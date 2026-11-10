# EREVNA — Evidence-backed research assistant

Repository: https://github.com/ramshetty01/EREVNA

## Purpose and status

Turn a question and source documents into findings whose quotations and model-based
support judgments can be inspected. This is a tested local portfolio application with
UI, API and CLI, not a certified or deployed multi-user production service. The 0.3
claim-review work is merged; runtime-budget and retrieval follow-ups are in PRs #37
and #38 respectively at the time of this brief. Confirm their current state on GitHub.

## Actual technology stack

Python 3.12; Streamlit UI; FastAPI/Uvicorn API; Pydantic data contracts; LangChain model
adapters; NVIDIA NIM (recorded live provider), optional OpenAI/Ollama and extractive demo;
NumPy/BM25; optional Sentence Transformers/PyTorch CPU embeddings; requests/BeautifulSoup
and DuckDuckGo search; SQLite cache; Docker; pytest, Ruff, mypy and GitHub Actions.
There is no production vector database, account system or distributed task queue.

## Components and architecture

UI, API and CLI call `research.pipeline.run_research`. It plans, collects source text,
chunks passages, retrieves evidence, asks for structured findings, validates quotes,
reviews semantic support and renders Markdown deterministically. Pydantic schemas
validate the exported run. A shared invocation wrapper applies model-call limits and
tracks usage. The API adds bearer auth, request/body limits and a two-request semaphore.
The UI caches completed runs by browser session and context; the CLI defaults to offline.

Retrieval indexes keep corpus text/vectors local. BM25 is the default. Dense and hybrid
modes reuse a pinned CPU encoder, with safetensors weights and remote model code disabled.
Hybrid combines BM25 and dense ranks using reciprocal-rank fusion. This is a bounded
pipeline with multiple model passes, not an autonomous team of independent agents.

## End-to-end workflow

1. Enter a question and choose bundled documents, public URLs or live web search.
2. Collect and deduplicate sources; chunk full text rather than only the first 500 characters.
3. Rank passages with BM25 or optional dense/hybrid retrieval.
4. Generate findings with passage IDs and exact quotes; reject invalid references/quotes.
5. Optionally perform one citation-repair attempt within the shared call budget.
6. In live mode, review each claim as supported, partial, contradicted or insufficient.
7. Partial claims may be narrowed and rechecked once; failed review withholds affected claims.
8. Inspect report, evidence, claim audit, plan and metrics; export Markdown or full JSON.

## Data and operational boundaries

Sources and reports may contain private information; full JSON includes source text.
Local SQLite records expire for lookup after 24 hours and are purged after 30 days on
writes. Reloading the browser creates a new namespace. There is no cross-device identity.
Provider secrets stay outside Git/Docker. Public fetches validate destination addresses
and redirects, but production network policy still requires infrastructure enforcement.

The call ceiling is 1–10 model invocations per run, including failed calls and format
retries. It is not a monetary budget, total-run deadline or distributed quota. SDK
transport retries are disabled for OpenAI-compatible providers to preserve accounting.

## Verification and measured results

- 83 tests pass, plus Ruff/mypy and optional-environment dependency audit.
- Live NVIDIA CLI generation and support review completed within two model calls.
- Fresh-process browser flow covers evidence/audit inspection, downloads and mobile layout;
  hybrid mode has also been exercised with the real local embedding model.
- On 40 answerable authored retrieval questions, source recall@3/MRR: BM25 1.00/.9875,
  dense .95/.8917, hybrid 1.00/.9625. The ten unanswerable questions retrieve text in every
  method; retrieval alone does not establish answerability.
- On 16 synthetic support cases, unsupported originals retained fell from 12/12 under
  quote-only acceptance to 1/12 with model review. Supported originals retained: 3/4.
  Two narrowed claims and one unavailable decision were recorded. Label correction and
  false acceptance are disclosed; the set is not independently human reviewed.

## Run and inspect

```sh
make setup PYTHON=.venv/bin/python
make lint typecheck test evaluate support-evaluate PYTHON=.venv/bin/python
.venv/bin/python -m research "How does Harbor check citations?" --format markdown
# Explicit optional model installation and benchmark:
make setup-semantic semantic-evaluate PYTHON=.venv/bin/python
```

See README for creating the virtual environment and configuring live NVIDIA access.
`docs/architecture.md` contains workflow, sequence, cache, evaluation and deployment
diagrams. `docs/configuration.md` and `docs/troubleshooting.md` explain operational behavior.

## Honest resume bullets

- Built a Python research application with shared Streamlit, FastAPI and CLI entrypoints,
  structured citations, bounded model usage and inspectable support-review exports.
- Implemented BM25/dense/hybrid retrieval and reproducible per-case evaluation; preserved
  prior BM25 rankings while reusing corpus embeddings across evaluation questions.
- Added regression tests for citation failures, budget exhaustion, API concurrency,
  cache isolation and model-review failures, alongside CI and dependency auditing.

Use the synthetic evaluation scope whenever quoting its numbers. Do not claim zero
hallucinations, independent factual verification, public production traffic or trained
foundation models. These contributions demonstrate applied AI/RAG/LLM engineering work;
job eligibility also depends on your understanding and the employer's requirements.

## Interview topics to prepare

Explain why exact quotes do not prove entailment; how a same-model reviewer can fail;
how call budgets interact with retries and verification; why BM25 remains the default;
how reciprocal-rank fusion works; why source recall differs from answer-span recall;
and what must change for account isolation, cancellation and distributed deployment.

## Remaining blockers

Verdict/reason inconsistencies; independently reviewed evaluation on diverse sources;
account identity and authorization; per-user/shared quotas; persistence and deletion;
public hosting/TLS/egress policy; sustained deployed-load and failure-recovery testing.
See docs/roadmap.md and GitHub issues rather than treating test passage as completion.
