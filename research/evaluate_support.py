"""Compare quote-only acceptance with model support review on authored cases."""

import argparse
import csv
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from agents.llm_backend import get_llm, get_mode, model_name
from research.citations import check_answer
from research.models import Finding, GroundedAnswer, Passage, RunMetrics
from research.verification import PROMPT_VERSION, verify_answer

DATASET = Path(__file__).resolve().parents[1] / "data/claim_support_set.json"
LABELS = ("supported", "partially_supported", "contradicted", "insufficient")


def load_dataset(path: Path = DATASET) -> dict:
    data = json.loads(path.read_text())
    seen = set()
    for case in data["cases"]:
        if case["id"] in seen or case["expected_verdict"] not in LABELS:
            raise ValueError("Invalid or duplicate labelled case.")
        seen.add(case["id"])
        finding = Finding.model_validate(case["finding"])
        passages = [Passage.model_validate(p) for p in case["passages"]]
        checked, rejected = check_answer(GroundedAnswer(findings=[finding]), passages)
        if rejected or not checked.findings:
            raise ValueError(f"Case {case['id']} is not a valid quote-matching fixture.")
    return data


def score(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("No evaluation rows.")
    matrix = {label: dict.fromkeys((*LABELS, "unavailable"), 0) for label in LABELS}
    supported = sum(r["expected"] == "supported" for r in rows)
    unsupported = len(rows) - supported
    for row in rows:
        matrix[row["expected"]][row["predicted"]] += 1
    true_retained = sum(
        r["expected"] == "supported" and r["disposition"] == "retained" for r in rows
    )
    false_retained = sum(
        r["expected"] != "supported" and r["disposition"] == "retained" for r in rows
    )
    return {
        "cases": len(rows),
        "classification_accuracy": sum(r["predicted"] == r["expected"] for r in rows) / len(rows),
        "supported_original_retention": true_retained / supported if supported else None,
        "unsupported_original_acceptance": false_retained / unsupported if unsupported else None,
        "retained_original_precision": true_retained / (true_retained + false_retained)
        if true_retained + false_retained
        else None,
        "narrowed_claims_emitted": sum(r["disposition"] == "narrowed" for r in rows),
        "unavailable_decisions": sum(r["predicted"] == "unavailable" for r in rows),
        "confusion_matrix": matrix,
        "note": "Narrowed claims are not counted as acceptance of the original claim. Their semantic quality still needs independent human grading. Failures remain in the denominator.",
    }


def evaluate_case(case: dict, llm=None) -> dict:
    metrics = RunMetrics(provider=get_mode(), model=model_name())
    answer = GroundedAnswer(findings=[Finding.model_validate(case["finding"])])
    passages = [Passage.model_validate(p) for p in case["passages"]]
    start = time.perf_counter()
    final, review = verify_answer(answer, passages, llm if llm is not None else get_llm(), metrics)
    item = review.claims[0]
    return {
        "id": case["id"],
        "category": case["category"],
        "expected": case["expected_verdict"],
        "predicted": item.decision.verdict if item.decision else "unavailable",
        "disposition": item.disposition,
        "seconds": round(time.perf_counter() - start, 3),
        "answer": final.model_dump(),
        "review": review.model_dump(),
        "metrics": metrics.model_dump(
            include={
                "provider",
                "model",
                "llm_calls",
                "input_tokens",
                "output_tokens",
                "usage_complete",
            }
        ),
    }


def export_review_template(cases: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "claim",
                "evidence_json",
                "reviewer_verdict",
                "reviewer_rationale",
                "reviewer_name",
                "reviewed_at",
            ],
        )
        writer.writeheader()
        for case in cases:
            # Neither reference labels nor model predictions are shown to the human annotator.
            writer.writerow(
                {
                    "case_id": case["id"],
                    "claim": case["finding"]["claim"],
                    "evidence_json": json.dumps(
                        {"citations": case["finding"]["evidence"], "passages": case["passages"]}
                    ),
                }
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument(
        "--split", choices=["development", "evaluation", "all"], default="evaluation"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly spend configured provider usage on verification.",
    )
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--workers", type=int, choices=[1, 2], default=1)
    parser.add_argument("--output", type=Path, default=Path("artifacts/support-evaluation.json"))
    parser.add_argument("--review-template", type=Path)
    args = parser.parse_args()
    if not 1 <= args.limit <= 32:
        parser.error("--limit must be between 1 and 32")
    dataset = load_dataset(args.dataset)
    cases = [c for c in dataset["cases"] if args.split == "all" or c["split"] == args.split][
        : args.limit
    ]
    baseline = [
        {
            "id": c["id"],
            "expected": c["expected_verdict"],
            "predicted": "supported",
            "disposition": "retained",
        }
        for c in cases
    ]
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "prompt_sha256": hashlib.sha256(
            Path(__file__).with_name("verification.py").read_bytes()
        ).hexdigest(),
        "prompt_version": PROMPT_VERSION,
        "split": args.split,
        "label_provenance": dataset["label_provenance"],
        "dataset_description": dataset["description"],
        "quote_only_baseline": score(baseline),
        "baseline_rows": baseline,
        "support_verifier": None,
        "cases": [],
    }
    if args.live:
        if get_mode() == "demo":
            parser.error(
                "Live support evaluation requires a configured model provider, not demo mode."
            )
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            rows = list(pool.map(evaluate_case, cases))
        report["cases"] = rows
        report["support_verifier"] = score(rows)
    if args.review_template:
        export_review_template(cases, args.review_template)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(
        json.dumps(
            {
                k: report[k]
                for k in ("label_provenance", "split", "quote_only_baseline", "support_verifier")
            },
            indent=2,
        )
    )
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
