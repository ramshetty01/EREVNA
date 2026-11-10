# Changelog

## 0.5.0 — Reusable retrieval and semantic benchmark

- Add session-scoped history deletion, configurable cache storage and serialized schema migration/version checks.

- Reuse corpus statistics and embeddings across evaluation questions; reuse a pinned CPU encoder across requests without sharing document indexes.
- Compare BM25, dense and reciprocal-rank hybrid retrieval with dataset/model/code provenance, setup/query timing and unanswerable retrieval counts.
- Validate embedding dimensions and finite values; make hybrid score ties deterministic by passage ID.
- Add optional semantic dependency pins and document measured quality and limitations.

## 0.4.0 — Runtime limits and CLI

- Enforce a per-run model-call ceiling across planning, generation, format retries, citation repair and support review; callers can lower the operator limit.
- Disable hidden OpenAI-compatible SDK retries so application call accounting is not bypassed.
- Add an offline-by-default command-line interface with document input, live opt-in and JSON/Markdown output.
- Expose call limits in the UI/API, isolate cached runs by limit, and test concurrent API overflow and recovery.

## 0.3.0 — Claim support review

- Add default fresh-context support judgments after quote validation, with bounded narrowing and recheck.
- Withhold findings when review fails; expose decisions, reasons and usage in UI/API/Markdown exports.
- Separate cache entries by verification settings and preserve legacy result compatibility.
- Add 32 synthetic reference-labelled cases, blind human-review export and recorded NVIDIA comparison with disclosed annotation correction and failure cases.

## 0.2.0 — Grounded research prototype

- Add NVIDIA NIM support and test an available Nemotron model.
- Replace truncated snippets in the active pipeline with full-text passage retrieval.
- Generate structured findings with exact quotes and validate references before deterministic report rendering.
- Add explicit abstention, token/latency metadata and optional configured cost estimation.
- Separate orchestration from the browser and expose a bounded REST API.
- Introduce an evidence-first UI with source inspection and full run exports.
- Scope cache entries by session/context, enforce freshness and preserve run evidence.
- Add DNS-pinned public fetching, redirect checks and safe provider error handling.
- Add a 50-case fictional development fixture, retrieval comparison and explicit bounded live evaluation.
- Update Python/dependencies, test isolation, CI and deployment documentation.
