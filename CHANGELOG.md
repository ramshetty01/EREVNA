# Changelog

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
