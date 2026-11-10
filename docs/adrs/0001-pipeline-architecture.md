# ADR 0001: Shared typed pipeline with deterministic report rendering

Status: accepted in the local prototype.

## Context

The original UI mixed orchestration and presentation, and free-form reports could
introduce statements whose source could not be inspected. Separate UI/API/CLI logic
would make validation and failure behavior inconsistent.

## Decision

Use one synchronous `run_research` function returning validated `ResearchResult` data.
Generate structured findings with exact evidence quotes, validate their references,
review support in a fresh model context and render the report deterministically.
Keep original judgments in an audit. Apply one shared per-run call budget across all
model stages. Make source collection and external model calls bounded; keep a local
extractive demo that does not silently pretend to be live model output.

The UI owns session/cache presentation; the API and CLI call the same pipeline directly.
Use BM25 by default because it needs no download and performed well on the authored
fixture. Optional dense/hybrid indexes are corpus-local; only model weights are shared.

## Consequences

Behavior is testable without a browser, exports are inspectable, and the report cannot
silently add generated prose outside the findings. Extra support-review calls add cost
and latency. Both generator and reviewer use the configured model, so correlated errors
remain possible. Quote checks establish traceability, not truth. The synchronous process
and local SQLite cache are insufficient for distributed jobs, account identity, shared
quotas or a public multi-tenant service. Those require separate design and validation.
