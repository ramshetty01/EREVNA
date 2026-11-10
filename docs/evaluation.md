# Evaluation methodology

## Development fixture

`data/development_set.json` contains 50 authored questions about ten fictional Harbor
product documents. There are 40 answerable and ten unanswerable questions. Each answerable
question has an expected source URL. The corpus uses `example.org` identifiers, not claims
about real products. Repeated navigation text deliberately pushes relevant content past
500 characters, reproducing a known weakness in the old collector.

This is a development/regression fixture created alongside the implementation. It is not
held out, independent, diverse enough for generalisation claims, or a public benchmark.

## Retrieval comparison

Both variants use the same query, corpus, BM25 implementation and k=3. The baseline uses
only each document's first 500 characters; the new path chunks the complete supplied text
into 160-word passages with 35-word overlap. Top passages are mapped to unique source URLs.

- Source recall@3: fraction of labelled source URLs present among the selected passages.
- Reciprocal rank: inverse position of the first relevant source in the returned source list.
- Means exclude unanswerable questions because their relevant-source denominator is zero.
- Unanswerable retrieval rows are retained with null recall; retrieving something is not evidence that it answers the question.

See `evaluation-results.json` for dataset SHA-256, case-level rankings and measured results.
Do not compare the numbers with benchmarks having different corpora, passages or protocols.

## Live generation checks

`python -m research.evaluate --live --limit 3` explicitly calls the configured provider.
It selects the first two development questions and one unanswerable question. Each exported
run records provider/model, token counts, stage latency, source passages, structured findings
and quote-validation counts. `live-evaluation-summary.json` contains the recorded summary.

This run tests basic answerability/abstention and reference plumbing. It does NOT independently
score claim entailment or answer correctness. A bounded citation-repair pass can retry generation once when quote checks reject findings. Initial/final rejection counts and repair attempts are included in metrics.

Automatic quote matching verifies a verbatim
span occurs in the cited passage; it cannot prove the claim logically follows from the span.

## Recommended next evaluation

1. Freeze prompts/retrieval configuration before preparing an unseen test split.
2. Gather permissioned, real documentation covering several technologies and document versions.
3. Label answer spans, answerability and conflicting evidence, with a second human reviewing ambiguous cases.
4. Compare BM25, dense and hybrid retrieval using identical corpora and a held-out split.
5. Grade every factual claim as supported, unsupported or contradictory. Record citation completeness separately.
6. Measure abstention precision/recall, p50/p95 latency, usage and failure categories over enough runs.
7. Publish negative examples and retrieval/generation ablations, not just successful screenshots.

## Claim-support review (0.3)

The 0.2 generation checks above predate the semantic review gate. The separate
[claim-support evaluation](claim-support.md) measures original-claim acceptance,
retention and classification on 16 synthetic evaluation cases, with full label
provenance, a post-run annotation correction and known failures disclosed.
