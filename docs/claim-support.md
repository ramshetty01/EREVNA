# Claim support review

Live research now validates references and literal quotes, then asks the configured
model to assess each complete claim against the retrieved passages. A fresh context
contains only claims and source evidence, never the generator's reasoning. Source
instructions are explicitly treated as untrusted. This is a separate review pass
using the same model, not independent verification of real-world truth.

Decisions are supported, partially_supported, contradicted or insufficient.
Supported claims remain; partial claims may be narrowed using the same citations,
then pass one fresh-context recheck. No recursive rewriting occurs. Other claims
are excluded. Invalid IDs, malformed decisions and provider failures withhold the
affected findings. Already-supported findings survive a failed narrowing recheck.
Each structured batch allows one format retry. Review adds up to four model calls
(two batches, two attempts each), beyond generation/citation repair/planning.

The UI's Claim review tab, API `support_review`, Markdown and full JSON exports retain
original claims, reasons, proposed revisions, dispositions and safe error messages.
Metrics include additional calls, tokens, timing and exclusion/narrowing counts.
`verify_support` defaults to true in the API; the sidebar offers an explicit opt-out.
Demo runs are labelled as skipping semantic review. Cache contexts include the
pipeline version and review setting; legacy cached JSON remains readable.

## Evaluation and provenance

`data/claim_support_set.json` contains 32 synthetic cases authored by the implementation
assistant alongside this feature. Sixteen development cases and sixteen evaluation
cases cover different topics. All citations deliberately match their passages, so
quote matching alone accepts even semantically invalid claims. This targeted stress
fixture is not representative of real research and is not independently human labelled.
Every human-review status is pending. Labels and rationales are never sent to the judge.

The recorded NVIDIA run used `nvidia/nemotron-3.5-lightning-30b-a3b`, 20 calls and
21,682 reported tokens. Raw per-case decisions, hashes and metrics are retained in
[support-evaluation-results.json](support-evaluation-results.json).

| Measure (16 evaluation cases) | Quote-only acceptance | Model review |
|---|---:|---:|
| Unsupported original claims retained | 12/12 | 1/12 |
| Supported original claims retained | 4/4 | 3/4 |
| Retained original precision | 25% | 75% |
| Four-class accuracy | 25% | 62.5% |
| Narrowed claims emitted | 0 | 2 |
| Unavailable decisions | 0 | 1 |

One label was corrected after the first run: support-028's universal language-support
claim is contradicted by the explicit absence of Spanish support, rather than merely
insufficient. The initial result was 9/16; the corrected result is 10/16 using identical
predictions and prompt. Both metrics, original hash, rationale and correction are
preserved in the result JSON. This correction is not independent human review.

Known failures remain visible: support-023 received a supported verdict even though
its reason describes a contradiction, retaining an unsupported authentication claim.
Support-026 failed the decision contract and was withheld. Support-029's accurate
attribution of conflicting reports was excluded. Revised claims have not been
independently graded. Errors remain in metric denominators; narrowed claims do not
count as acceptance of the original claim. These results cannot establish a production
hallucination rate, safety guarantee, or model superiority.

## Reproduce and review

```sh
# No API calls; validate quote integrity and report the baseline:
python -m research.evaluate_support
# Explicit live usage, bounded to 16 cases and two workers:
python -m research.evaluate_support --live --limit 16 --workers 2 \
  --output artifacts/support-live-evaluation.json \
  --review-template artifacts/support-human-review.csv
```

The blind CSV omits reference labels and predictions. Have independent reviewers
annotate it, adjudicate disagreements, and separately grade narrowed claims before
making broader quality claims. Next work should address verdict/reason inconsistency
and evaluate on newly authored, independently reviewed cases without tuning on this
recorded evaluation split.
