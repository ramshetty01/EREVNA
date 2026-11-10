> Historical pre-upgrade review. Several items below have since been implemented; see README and CHANGELOG for current status.

# EREVNA Engineering Review

Date: 2026-07-31
Repository: https://github.com/ramshetty01/EREVNA

## Overall Score

**31 / 100**

This repository is a demo Streamlit app, not yet a flagship AI engineering repository. It has a visible prototype loop, basic tests, and CI, but it lacks the product framing, evaluation discipline, reproducibility, safety controls, observability, deployment maturity, and documentation expected from a senior AI engineering portfolio project.

## Section Scores

| Category | Score |
|---|---:|
| Repository positioning | 18 / 100 |
| README | 35 / 100 |
| Repository structure | 52 / 100 |
| Code quality | 43 / 100 |
| AI engineering | 24 / 100 |
| Production readiness | 16 / 100 |
| Documentation | 12 / 100 |
| User experience | 48 / 100 |
| Research quality | 10 / 100 |
| Portfolio value | 22 / 100 |

## Critical Issues

1. Repo identity is inconsistent. The remote is `ramshetty01/EREVNA`, but README badges, clone commands, author links, and UI footer point to `Ramshetty02/Agentic_aiv2`.
2. GitHub repository metadata is empty: no description, homepage, or topics.
3. No reproducible environment: `requirements.txt` is unpinned, no lockfile, no Makefile, no setup script, and local tests fail in the current checkout because `pytest` is unavailable.
4. No evaluation harness for research quality, source grounding, hallucination rate, citation coverage, answer usefulness, or retrieval quality.
5. No citation contract. Reports can summarize scraped snippets without source-level attribution, evidence spans, or freshness metadata.
6. No production error model. Search, scraping, LLM calls, parsing, memory writes, and logging are mostly happy-path.
7. No security posture beyond `.gitignore`. There is no secret scanning, dependency scanning, SSRF mitigation for URL scraping, rate limiting, or data retention policy.
8. No observability. Logs only counts and character lengths, not request IDs, latency, model, token usage, costs, retrieval decisions, source failures, or trace context.
9. No deployment artifact. There is no Dockerfile, health check, deployment guide, release workflow, or live demo URL.
10. Generated Python bytecode is tracked in git under `agents/__pycache__`.

## High Issues

1. `app.py` owns UI, state, orchestration, memory, logging, and cache decision flow in one file.
2. `utils/ui.py` is a 438-line styling/rendering file with hidden coupling to session state and app behavior.
3. Prompt templates are hard-coded in agent modules with no versioning, tests, changelog, or prompt regression suite.
4. Structured outputs exist only for planning. Analysis and report generation return free-form markdown.
5. Search quality is weak: DuckDuckGo only, no source ranking, no canonicalization, no freshness controls, no domain allow/deny policy, and no content extraction quality checks.
6. Memory is not production-grade: local SQLite path, JSON embeddings, fixed threshold, no tenant/session isolation, no deletion, no migration, and no evals for false positives.
7. Model abstraction is minimal and environment-driven only; there is no provider interface, timeout policy, retry policy, token budget, or fallback strategy.
8. CI only runs tests. It does not run lint, format checks, type checks, coverage, security scans, dependency review, or build/deploy checks.
9. README claims OpenAI API key is required while also saying demo mode works without one.
10. No limitations section that honestly states demo/template behavior, search limitations, hallucination risk, and source coverage constraints.
11. No architecture docs beyond an ASCII pipeline in README.
12. No benchmark or baseline against simple web search, RAG, Perplexity-style citation output, or non-agentic pipeline.

## Medium Issues

1. Repository name `EREVNA` is short but not discoverable without a subtitle.
2. Branding is unclear: app title says "Research Assistant"; README says "Agentic AI Research Assistant v2"; repo is `EREVNA`.
3. Missing screenshots, GIF, video, sample reports, and hosted demo link.
4. Missing ADRs, API docs, developer docs, troubleshooting guide, FAQ, and contribution guide.
5. Missing docs for configuration, persistence paths, logs, model modes, and expected costs.
6. Missing type-checking discipline; function signatures are partial and many dict shapes are implicit.
7. Errors are swallowed in web search and scraping, making debugging and reliability measurement impossible.
8. No request/session IDs across UI, pipeline, logs, memory, and generated reports.
9. No user-facing "no sources found" fallback policy beyond generic demo text.
10. No dependency update automation.
11. No branch protection/ruleset documentation.
12. No release notes or versioning.
13. No license/citation framing beyond a basic MIT file.

## Low Issues

1. Empty `__init__.py` files are harmless but add no API surface.
2. UI theme is dark-only and not documented or validated for accessibility.
3. Markdown formatting uses emoji in plan output, which is less professional for exported reports.
4. `AgentLogger` uses local time and default file encoding.
5. No issue templates, PR template, CODEOWNERS, funding, citation file, or security policy.

## Missing Features

- Live hosted demo with stable URL.
- Example research tasks and expected outputs.
- Export bundle with report, sources, plan, and trace metadata.
- Source cards with title, URL, retrieval query, timestamp, content excerpt, and confidence.
- User-selectable model/provider settings.
- Token/cost estimate and budget controls.
- Retry and timeout controls for search, scrape, and LLM calls.
- Cache invalidation and memory management.
- Evaluation command that can run offline.
- Structured JSON output mode for downstream use.
- CLI entrypoint for non-Streamlit usage.
- Health check endpoint or deployment smoke test.

## Missing Documents

- `docs/architecture.md`
- `docs/evaluation.md`
- `docs/security.md`
- `docs/observability.md`
- `docs/deployment.md`
- `docs/configuration.md`
- `docs/troubleshooting.md`
- `docs/examples.md`
- `docs/roadmap.md`
- `docs/adrs/0001-pipeline-architecture.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `CITATION.cff`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`

## Missing Benchmarks

- End-to-end latency by mode: demo, OpenAI, Ollama.
- Search latency and scrape success rate.
- Token usage and estimated cost per report.
- Memory lookup latency as sessions grow.
- Report generation latency by source count.
- Cold start time for Streamlit and embedding model load.

## Missing Evaluations

- Citation precision and recall.
- Claim support rate.
- Hallucination rate on source-constrained prompts.
- Source freshness accuracy.
- Search result relevance.
- Memory cache false-positive and false-negative rate.
- Planner usefulness versus raw-query search.
- Report quality rubric with golden examples.
- Regression suite for prompts and model upgrades.
- Baseline comparison against non-agentic single-pass search summarization.

## Missing Diagrams

- System architecture diagram.
- Runtime sequence diagram.
- Data flow diagram.
- Memory lifecycle diagram.
- Error handling and fallback flow.
- Deployment topology.
- Evaluation pipeline diagram.
- Observability trace diagram.

## Missing GitHub Features

- Repository description.
- Homepage URL.
- Topics: `ai-agents`, `research-assistant`, `langchain`, `streamlit`, `rag`, `llm`, `evaluation`.
- Correct badges for the actual repo.
- Issue templates.
- PR template.
- Dependabot.
- CodeQL.
- Security policy.
- Releases.
- Branch protection/ruleset documentation.
- Project board or milestone plan.

## Missing Automation

- Format check.
- Lint.
- Type check.
- Test coverage.
- Security scan.
- Dependency review.
- Secret scan.
- Build smoke test.
- Docker build check.
- Release workflow.
- README link checker.
- Scheduled dependency updates.

## Naming Issues

- Repo name `EREVNA` is not explained.
- README title uses `Agentic AI Research Assistant v2`.
- Streamlit page title uses `Research Assistant`.
- GitHub URLs use `Ramshetty02/Agentic_aiv2`.
- Author section points to the wrong account.
- UI footer points to the wrong repo.
- `demo_agents.py` is really a deterministic fallback implementation, not agents.
- `search_agent.py` mixes query expansion and retrieval orchestration.
- `web_search.py` performs both search and scraping.

## Architecture Issues

- UI and orchestration are coupled in `app.py`.
- Agent functions hide global backend selection through environment variables.
- No explicit pipeline object or typed pipeline result.
- Dict payloads flow between stages without schemas.
- Memory is instantiated from Streamlit state and writes directly to a local path.
- Search result objects are untyped.
- No cancellation, timeout, or retry boundary around pipeline steps.
- Prompt templates are not versioned or externally inspectable.

## Production Issues

- No Dockerfile.
- No deployment guide.
- No health check.
- No runtime configuration validation.
- No operational runbook.
- No tracing or metrics.
- No cost controls.
- No rate limiting.
- No failure recovery.
- No data retention policy.
- No upgrade/migration strategy for memory DB.

## README Issues

- Wrong repo URLs and badge targets.
- No clear EREVNA positioning.
- No hero image or screenshot.
- No demo URL.
- No quick result example.
- No limitations.
- No benchmarks.
- No evaluation section.
- No security section.
- No troubleshooting.
- No contributing guide.
- No citation.
- Environment variable table contradicts demo mode.

## UI Issues

- No screenshot-backed quality proof.
- No source trust/freshness UI.
- No visible latency/cost/debug trace.
- No clear error recovery states.
- No accessibility evidence.
- No mobile QA evidence.
- Dark-only theme may hurt readability.

## Testing Gaps

- No app-level pipeline test.
- No LLM failure tests.
- No parser failure tests.
- No scrape failure detail tests.
- No memory corruption/migration tests.
- No citation tests.
- No prompt regression tests.
- No CI coverage output.
- No deterministic offline eval dataset.

## Deployment Gaps

- No Streamlit Cloud app URL.
- No Docker image.
- No container smoke test.
- No deployment environment documentation.
- No production secret setup documentation.
- No rollback guidance.

## Observability Gaps

- No request ID.
- No step latency.
- No model name in logs.
- No token usage.
- No estimated cost.
- No source URLs in trace logs.
- No error reason taxonomy.
- No retrieval score.
- No cache hit score.

## Security Issues

- URL scraping has no SSRF protection.
- No allowlist or blocklist for local/private IP ranges.
- No dependency or secret scanning in CI.
- No security policy.
- No privacy/data retention policy for saved reports.
- No guidance for handling sensitive user queries.
- Web search exceptions can expose raw exception messages as result bodies.

## Prioritized Roadmap: 0-100

### 0-10: Correct the Public Surface

- Rename/position the repo consistently as EREVNA.
- Fix README badges, clone URL, author link, and UI footer.
- Add GitHub description, homepage, and topics.
- Remove tracked `__pycache__`.

### 10-20: Make Setup Reproducible

- Pin dependencies or add a lockfile.
- Add `make setup`, `make test`, and `make run` or equivalent.
- Document Python version and environment creation.
- Ensure tests run from a fresh checkout.

### 20-30: Split the Pipeline Cleanly

- Move pipeline orchestration out of Streamlit UI.
- Add typed request/result objects for plan, search, analysis, report, memory, and trace.
- Keep Streamlit as a thin presentation layer.

### 30-40: Add Source Grounding

- Define source schema with URL, title, query, timestamp, excerpt, and retrieval status.
- Require report claims to cite source IDs.
- Add unsupported-claim handling.

### 40-50: Add Reliability Controls

- Add timeouts, retries, and clear errors for search, scraping, parsing, LLM calls, memory, and logging.
- Add request IDs and structured exceptions.
- Add UI recovery states.

### 50-60: Add Observability

- Log pipeline step latency, model, token usage, source count, source failures, cache score, and request ID.
- Add trace export.
- Document logs and debugging.

### 60-70: Add Evaluation

- Create a small golden dataset.
- Add offline eval command.
- Score citation support, hallucination rate, source relevance, and report quality.
- Add baseline comparison.

### 70-80: Harden CI and Security

- Add lint, typecheck, coverage, secret scan, dependency review, and CodeQL.
- Add SSRF protections for scraping.
- Add `SECURITY.md` and data retention docs.

### 80-90: Ship Deployment

- Add Dockerfile and container smoke test.
- Add deployment guide and Streamlit Cloud/VPS path.
- Add release workflow and versioned changelog.

### 90-100: Make It Portfolio-Grade

- Add screenshots, demo video/GIF, architecture diagrams, evaluation report, benchmarks, examples, ADRs, and polished README.
- Add GitHub milestones and project board.
- Publish a stable demo and tag a release.

