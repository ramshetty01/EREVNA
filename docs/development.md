# Development guide

Use Python 3.12, a virtual environment and `requirements.lock`. Create `.env` from
`.env.example`; use `LLM_PROVIDER=demo` for offline development. No key is required.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
make lint typecheck test evaluate support-evaluate smoke PYTHON=.venv/bin/python
make security PYTHON=.venv/bin/python
```

The optional embedding environment is installed with `make setup-semantic`. Its
recorded lock and benchmark were validated on macOS ARM; the default Linux Docker/CI
path remains BM25. Model downloads are not part of the normal unit tests.

## Working on an issue

1. Reproduce the failure and record the affected entrypoint and acceptance criteria.
2. Create a feature branch and add a regression test for changed behavior.
3. Change the shared pipeline/schema for behavior common to UI, API and CLI.
4. Run the checks above and the relevant browser/optional-model check if affected.
5. Commit a coherent change and open a PR linking the issue, evidence and limitations.
6. Keep issues open until all acceptance criteria are met and the fix is merged.

Tests isolate provider configuration and never spend API usage. Live evaluation and
browser smoke tests are explicit commands and can call the configured provider. Use
bounded call limits. Never commit `.env`, local cache files or raw private documents.
Do not imply mocked tests establish live-provider quality or production readiness.

## Key contracts

- `research/models.py`: source, finding, evidence, support-decision and exported-run schemas.
- `research/pipeline.py`: planning, collection, retrieval, generation, validation and rendering.
- `research/llm_io.py`: safe structured responses and the per-run call gate.
- `research/retrieval.py`: local corpus indexes and optional pinned model.
- `research/api.py`: bearer authentication, input/body/concurrency boundaries.
- `agents/memory_agent.py`: session/context cache with expiry.

Prompt changes should preserve prior fixtures/results, declare which cases were used
for development, and record new results on fresh cases. The semantic-review prompt
has an explicit version; model and source-code hashes are recorded in evaluations.
Restart the local app/API after changes to imported modules, dependency versions or
configuration; hot reload is not a substitute for a fresh-process verification.
