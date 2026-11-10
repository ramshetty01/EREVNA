"""Research from a terminal; defaults to an offline bundled demo."""

import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from research.models import Document
from research.pipeline import ResearchError, run_research

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Research question (up to 1,500 characters)")
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument(
        "--documents", type=Path, help="JSON document array or object with documents"
    )
    sources.add_argument("--web", action="store_true", help="Explicitly search the live web")
    parser.add_argument(
        "--live", action="store_true", help="Use the configured model; may spend provider usage"
    )
    parser.add_argument("--retrieval", choices=["bm25", "dense", "hybrid"], default="bm25")
    parser.add_argument(
        "--max-llm-calls", type=int, help="Lower the operator's per-run call limit (1–10)"
    )
    parser.add_argument(
        "--no-support-review", action="store_true", help="Explicitly disable semantic claim review"
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", type=Path, help="Write to this file instead of standard output")
    args = parser.parse_args(argv)
    original_mode = os.environ.get("LLM_PROVIDER")
    if not args.live:
        os.environ["LLM_PROVIDER"] = "demo"
    try:
        documents = None
        if not args.web:
            path = args.documents or ROOT / "data/development_set.json"
            # Bound reads as well as validated document input.
            with path.open("rb") as handle:
                raw = handle.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError("Document JSON must be at most 2 MB.")
            data = json.loads(raw)
            rows = data.get("documents") if isinstance(data, dict) else data
            if not isinstance(rows, list):
                raise ValueError(
                    "Document input must be an array or an object with a documents array."
                )
            documents = [Document.model_validate(row) for row in rows]
        result = run_research(
            args.query,
            documents=documents,
            retrieval=args.retrieval,
            verify_support=not args.no_support_review,
            max_llm_calls=args.max_llm_calls,
        )
        output = result.model_dump_json(indent=2) if args.format == "json" else result.report
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0
    except (ValidationError, json.JSONDecodeError, UnicodeError):
        print("Invalid document input. Check the JSON document schema.", file=sys.stderr)
    except OSError:
        print(
            "Cannot read the input or write the output file. Check paths and permissions.",
            file=sys.stderr,
        )
    except (ValueError, ResearchError) as exc:
        print(str(exc), file=sys.stderr)
    finally:
        if original_mode is None:
            os.environ.pop("LLM_PROVIDER", None)
        else:
            os.environ["LLM_PROVIDER"] = original_mode
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
