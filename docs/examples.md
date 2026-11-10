# Reproducible examples

## Offline Python API

```python
import os
os.environ["LLM_PROVIDER"] = "demo"

from research.models import Document
from research.pipeline import run_research

result = run_research(
    "When does the cache expire?",
    documents=[Document(
        title="Cache policy", url="https://example.org/cache",
        text="Cache entries expire after 24 hours.",
    )],
)
print(result.report)
assert result.metrics.llm_calls == 0
```

Demo mode extracts text and labels support review as skipped. It is useful for checking
interfaces and export formats, not for measuring model reasoning.

## Command line and exports

```sh
python -m research "How does Harbor check citations?" --format markdown --output report.md
python -m research "How does Harbor check citations?" --output run.json
```

JSON includes passages, sources, judgments and usage, so inspect it before sharing.

## Explicit live run

Configure your intended provider in the local environment first. Then use:

```sh
python -m research "When does the cache expire?" --live \
  --documents documents.json --max-llm-calls 4 --output run.json
```

`documents.json` is an array of objects with `title`, public-form `url` and `text`.
The call ceiling includes retries and review. It does not guarantee an answer; exhausted
review budgets withhold affected claims. A real source URL is metadata for supplied text,
not evidence that the supplied text has been fetched or authenticated independently.

## Namespace-scoped cache deletion

```python
from agents.memory_agent import MemoryAgent
cache = MemoryAgent("database/memory.db", namespace="your-own-session")
deleted_rows = cache.clear()
```

The UI's Delete session history action supplies the active browser namespace automatically.
Other namespaces, exports and backups are not removed. This is logical deletion only.
