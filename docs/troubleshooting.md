# Troubleshooting

| Symptom | Check and action |
|---|---|
| CLI does not call the model | Offline demo is the default. Add `--live` and configure the intended provider. |
| No findings after a successful response | Inspect limitations and Claim review. Retrieval, quotes or support judgments may have rejected the answer. Do not remove validation to manufacture a result. |
| Model-call budget exhausted | Inspect `llm_calls`, `max_llm_calls` and `call_budget_exhausted`. Reduce scope or raise the request limit within the operator ceiling. |
| API 401 | Send the configured bearer token without logging it. |
| API 503 | Configure a bearer token, or explicitly enable local mode while bound only to localhost. |
| API 429 | Two runs are active in that process. Respect Retry-After; a fleet needs shared quotas. |
| API 422 | Check request schema; a pre-generation exhausted model-call budget also uses 422. |
| Missing dense/hybrid dependencies | Install the optional semantic lock in the interpreter running the app. Restart that process. |
| Slow first semantic request | It may download/load the pinned public model. Use recorded setup time separately from query latency. |
| Provider errors or retired model | Verify access/model configuration in the provider account; do not repeatedly retry a retired model. Provider failures do not fall back silently. |
| Edits visible but research fails | Restart Streamlit and the API to clear stale imported modules; test a fresh browser session. |
| Empty live-web sources | Search may be blocked/rate-limited or pages may require JS/PDF parsing. Use supported public pages or supplied documents and inspect warnings. |
| History disappears on reload | Cache namespaces are browser-session scoped, not persistent accounts. Export JSON for a durable local record. |

For bug reports include the commit, entrypoint, provider/model name, safe error category
and a minimal non-sensitive fixture. Exclude keys, authorization headers and private
source text. Exported runs include source text; review them before sharing.
