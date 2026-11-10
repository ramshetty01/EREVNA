# Changelog

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
