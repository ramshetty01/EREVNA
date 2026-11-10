"""Reproducible retrieval checks; optional, explicit live answer evaluation."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from research.models import Document
from research.pipeline import run_research
from research.retrieval import chunk_documents, retrieve

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data/development_set.json"


def evaluate(path: Path = DEFAULT_DATA, method: str = "bm25", k: int = 3) -> dict:
    raw = path.read_bytes()
    dataset = json.loads(raw)
    documents = [Document(**d) for d in dataset["documents"]]
    full = chunk_documents(documents)
    truncated = chunk_documents([d.model_copy(update={"text": d.text[:500]}) for d in documents])
    report = {
        "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "dataset_description": dataset["description"],
        "k": k,
        "metric": "Source-level recall@k and reciprocal rank; NOT answer correctness or factual support.",
        "methods": {},
    }
    for label, passages, retrieval in [
        ("first_500_chars_bm25", truncated, "bm25"),
        (method, full, method),
    ]:
        rows = []
        start = time.perf_counter()
        for case in dataset["cases"]:
            selected = retrieve(case["query"], passages, method=retrieval, k=k)
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
                    "recall_at_k": recall,
                    "reciprocal_rank": reciprocal,
                }
            )
        answerable = [r for r in rows if r["answerable"]]
        report["methods"][label] = {
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
    parser.add_argument("--method", choices=["bm25", "dense", "hybrid"], default="bm25")
    parser.add_argument("--output", type=Path, default=Path("artifacts/retrieval-evaluation.json"))
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly call the configured provider on a bounded case subset.",
    )
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
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
