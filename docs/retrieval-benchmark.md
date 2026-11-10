# Dense, hybrid and BM25 retrieval comparison

This comparison uses the existing 50-question fictional Harbor development fixture:
40 questions with labelled source URLs and ten unanswerable questions. It was authored
alongside the application, not collected independently. Navigation prefixes deliberately
exercise the old 500-character truncation. Results cannot establish general retrieval
quality, answer correctness or a production hallucination rate.

## Frozen protocol

- Same documents, 160-word chunks, 35-word overlap and k=3 for every full-text method.
- The truncation baseline uses the first 500 characters of each document and BM25.
- Return the top three passages, then deduplicate source URLs for source-level recall
  and reciprocal rank. This is not retrieval of three distinct sources and does not
  test whether the answer span appears in the selected passage.
- BM25 indexes titles plus text. Dense embeddings encode text only, preserving the
  existing retrieval protocol. Hybrid uses reciprocal-rank fusion with constant 60;
  only positive-score contributions count, with ties resolved by passage ID.
- The local CPU encoder is `sentence-transformers/all-MiniLM-L6-v2`, pinned to revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Remote model code is disabled and safetensors
  weights are required. [Model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
  and [loader configuration](https://sbert.net/docs/package_reference/sentence_transformer/model.html).
- Corpus vectors are computed once per method's index. Query p50/p95 includes query
  encoding/ranking but excludes model loading and corpus indexing, reported separately.
  Methods run sequentially, in fixed order, once on a local machine. These are descriptive
  timings, not a statistically controlled speed comparison or deployment benchmark.
- Unanswerable rows are excluded from recall/MRR denominators and retained in the output.
  The count that retrieves any passage is reported separately; retrieving text does not
  establish answerability. There is no calibrated semantic abstention threshold.

## Implementation boundaries

The model is loaded once per process, including concurrent first use. A reusable
`RetrievalIndex` snapshots its own passages, lexical statistics and optional vectors.
The evaluation reuses an index across its questions. A regular UI/API/CLI research run
constructs a fresh index. Only the fixed model is shared across requests; user corpus
text/vectors are not stored in a global cache. Warm evaluation query times therefore
do not represent end-to-end application latency for a new corpus.

The model's token limit is separate from the word chunk size. The export records how
many passages exceed that limit and would be truncated by the encoder. Query inputs
may also be truncated by the encoder. No chunk-size or fusion-weight tuning was made
to improve this fixture's scores.

The BM25 refactor preserves all 100 per-case source rankings in the original baseline
and full-text reports. Tests check single corpus encoding, isolated passage snapshots,
invalid embeddings, stable hybrid ties and concurrent model initialization.

## Reproduce

```sh
# Optional dependencies; the default installation does not download embeddings:
make setup-semantic PYTHON=.venv/bin/python
make semantic-evaluate PYTHON=.venv/bin/python
```

The optional lock records the measured Python 3.12 macOS ARM environment. Other
platforms may need additional platform-specific PyTorch dependencies and are not
validated by this local measurement. The first run downloads the pinned public model;
subsequent runs can use its local cache. No hosted LLM or embedding API is called by
this benchmark. The normal CI suite tests retrieval contracts with fixed embeddings
and runs BM25; it does not download the optional model.

## Recorded local results

| Method | Source recall@3 | MRR | Query p50 (ms) | Query p95 (ms) |
|---|---:|---:|---:|---:|
| first_500_chars_bm25 | 0.5500 | 0.5333 | 0.024 | 0.043 |
| bm25 | 1.0000 | 0.9875 | 0.033 | 0.052 |
| dense | 0.9500 | 0.8917 | 6.096 | 7.427 |
| hybrid | 1.0000 | 0.9625 | 6.679 | 7.177 |

BM25 remains the default: this fixture gives no quality reason to replace it. Dense misses two of the 40 labelled sources within three passages; hybrid recovers recall but has lower MRR than BM25. All methods retrieve some text for all ten unanswerable questions, reinforcing the need for downstream abstention and support review.

The corpus contains 13 passages; 0 exceed the model’s 256-token limit. See [full per-case results and environment metadata](semantic-retrieval-results.json). First-use model loading/download took 113.78 seconds in this run; that includes environment/cache effects and is not a guaranteed cold-start measurement.
