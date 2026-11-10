# Remaining roadmap

The engineering review is historical. This checklist reflects the current repository;
passing these steps does not make the application production-ready automatically.

## Completed

- [x] Full-passage retrieval, citation validation, bounded citation repair and inspectable exports.
- [x] Model-based support review, one narrowing/recheck pass and failure auditing.
- [x] Authored retrieval/support fixtures and transparent live results with known failures.
- [x] Local UI/API, session-scoped cache, container build, CI and dependency audit.
- [x] CLI with offline default, provided documents and explicit live usage.
- [x] Operator/request model-call ceilings and cache isolation by budget.
- [x] Deterministic API concurrency, overflow and failure-recovery tests.

## Next: evidence quality

- [ ] Investigate supported verdicts whose reasons describe contradiction. Preserve the existing failure cases; validate any fix on newly authored cases, not just the known evaluation set.
- [ ] Obtain independent human labels and adjudicate disagreements. The exported blind CSV supports this; assistant-authored labels do not satisfy this step.
- [ ] Evaluate narrowed claims separately and collect permissioned, diverse real documentation.
- [ ] Install and benchmark optional dense/hybrid retrieval; current numerical retrieval results cover BM25 only.

## Next: shared deployment

- [ ] Account identity, per-user authorization and quotas across workers.
- [ ] Persistent shared storage, explicit deletion and retention jobs.
- [ ] Enforced outbound-network policy and a total-run cancellation/deadline design.
- [ ] Choose a hosting account/region, configure secrets there and verify a public demo.
- [ ] Measure sustained HTTP load, p50/p95 latency and failure rates on the deployed topology. Unit concurrency checks are not a production load benchmark.

## Portfolio delivery

- [ ] Publish a demo video and a reproducible release after the next milestone is validated.
- [ ] Record an independently reviewed evaluation and deployment limitations alongside the demo.
