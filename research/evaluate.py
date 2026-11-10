"""Reproducible retrieval checks; optional, explicit live answer evaluation."""

import argparse
import hashlib
import json
import platform
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

from research.models import Document
from research.pipeline import run_research
from research.retrieval import (
    MODEL_ID,
    MODEL_REVISION,
    RetrievalIndex,
    chunk_documents,
    get_dense_encoder,
)

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data/development_set.json"


def evaluate(path: Path = DEFAULT_DATA, method: str = "bm25", k: int = 3, encoder=None) -> dict:
    if method not in ("bm25", "dense", "hybrid", "all") or not 1 <= k <= 12:
        raise ValueError("Choose bm25, dense, hybrid or all and k between 1 and 12.")
    raw = path.read_bytes()
    dataset = json.loads(raw)
    documents = [Document(**d) for d in dataset["documents"]]
    full = chunk_documents(documents)
    truncated = chunk_documents([d.model_copy(update={"text": d.text[:500]}) for d in documents])
    if not dataset["cases"] or not any(c["answerable"] for c in dataset["cases"]):
        raise ValueError("Evaluation requires at least one answerable case.")
    if any(bool(c["relevant_urls"]) != c["answerable"] for c in dataset["cases"]):
        raise ValueError("Answerability labels must agree with relevant URLs.")
    packages: dict[str, str | None] = {}
    for package in ("numpy", "sentence-transformers", "transformers", "torch"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = None
    report = {
        "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "dataset_description": dataset["description"],
        "k": k,
        "implementation_sha256": hashlib.sha256(
            Path(__file__).with_name("retrieval.py").read_bytes()
        ).hexdigest(),
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
            "packages": packages,
        },
        "protocol": "Top-k passages, then deduplicated source URLs. Query latency excludes model loading and corpus indexing. Fixed query order; single local run, not production load.",
        "passage_count": len(full),
        "metric": "Source-level recall@k and reciprocal rank; NOT answer correctness or factual support.",
        "methods": {},
    }
    methods = ["bm25", "dense", "hybrid"] if method == "all" else [method]
    if any(m != "bm25" for m in methods):
        start = time.perf_counter()
        supplied_encoder = encoder is not None
        encoder = encoder if supplied_encoder else get_dense_encoder()
        report["embedding"] = {
            "model": "injected-test-encoder" if supplied_encoder else MODEL_ID,
            "revision": None if supplied_encoder else MODEL_REVISION,
            "device": "injected" if supplied_encoder else "cpu",
            "model_load_seconds": round(time.perf_counter() - start, 6),
            "note": "Model load may use cached files; download is not separately timed. Text only is embedded; BM25 includes titles.",
        }
        if not supplied_encoder:
            lengths = [
                len(ids)
                for ids in encoder.tokenizer([p.text for p in full], truncation=False)["input_ids"]
            ]
            report["embedding"]["max_sequence_tokens"] = encoder.max_seq_length
            report["embedding"]["passages_over_token_limit"] = sum(
                n > encoder.max_seq_length for n in lengths
            )
    for label, passages, retrieval in [
        ("first_500_chars_bm25", truncated, "bm25"),
        *((m, full, m) for m in methods),
    ]:
        setup_start = time.perf_counter()
        index = RetrievalIndex(passages, method=retrieval, encoder=encoder)
        index_seconds = time.perf_counter() - setup_start
        rows = []
        start = time.perf_counter()
        for case in dataset["cases"]:
            query_start = time.perf_counter()
            selected = index.search(case["query"], k=k)
            query_ms = (time.perf_counter() - query_start) * 1000
            ranked = list(dict.fromkeys(p.url for p in selected))
            gold = set(case["relevant_urls"])
            recall = len(gold.intersection(ranked)) / len(gold) if gold else None
            reciprocal = (
                next((1 / (i + 1) for i, u in enumerate(ranked) if u in gold), 0) if gold else None
            )
            rows.append(
                {
                    "id": case["id"],
                    "query": case["query"],
                    "answerable": case["answerable"],
                    "retrieved_urls": ranked,
                    "retrieved_passage_ids": [p.id for p in selected],
                    "query_ms": round(query_ms, 6),
                    "recall_at_k": recall,
                    "reciprocal_rank": reciprocal,
                }
            )
        answerable = [r for r in rows if r["answerable"]]
        query_times = [r["query_ms"] for r in rows]
        unanswerable = [r for r in rows if not r["answerable"]]
        report["methods"][label] = {
            "index_build_seconds": round(index_seconds, 6),
            "query_p50_ms": round(float(np.percentile(query_times, 50)), 6),
            "query_p95_ms": round(float(np.percentile(query_times, 95)), 6),
            "unanswerable_with_results": sum(bool(r["retrieved_urls"]) for r in unanswerable),
            "source_recall_at_k": round(
                sum(r["recall_at_k"] for r in answerable) / len(answerable), 4
            ),
            "mean_reciprocal_rank": round(
                sum(r["reciprocal_rank"] for r in answerable) / len(answerable), 4
            ),
            "answerable_cases": len(answerable),
            "unanswerable_cases": len(rows) - len(answerable),
            "seconds": round(time.perf_counter() - start, 3),
            "cases": rows,
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--method", choices=["bm25", "dense", "hybrid", "all"], default="bm25")
    parser.add_argument("--output", type=Path, default=Path("artifacts/retrieval-evaluation.json"))
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly call the configured provider on a bounded case subset.",
    )
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    if args.live and args.method == "all":
        parser.error("Live evaluation requires a single method; --method all is retrieval only.")
    report = evaluate(args.dataset, args.method)
    if args.live:
        if not 1 <= args.limit <= 50:
            parser.error("--limit must be 1–50")
        dataset = json.loads(args.dataset.read_text())
        documents = [Document(**d) for d in dataset["documents"]]
        # Include an unanswerable question in every live evaluation with >=2 cases.
        selected = dataset["cases"][: args.limit]
        if args.limit >= 2:
            selected[-1] = next(c for c in dataset["cases"] if not c["answerable"])
        runs = []
        for case in selected:
            result = run_research(case["query"], documents=documents, retrieval=args.method)
            runs.append(
                {
                    "case_id": case["id"],
                    "expected_answerable": case["answerable"],
                    "abstention_correct": result.answer.insufficient_evidence
                    == (not case["answerable"]),
                    "run": result.model_dump(),
                }
            )
        report["live_runs"] = runs
        report["live_note"] = (
            "Abstention and reference/quote checks are measured. Human claim-support and answer-correctness grading are still required."
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(
        json.dumps(
            {
                name: {k: v for k, v in metrics.items() if k != "cases"}
                for name, metrics in report["methods"].items()
            },
            indent=2,
        )
    )
    if args.live:
        print("Live abstention checks:", [r["abstention_correct"] for r in report["live_runs"]])
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
