# Runtime configuration

Use the ignored `.env` or environment variables. Shell environment variables take
precedence over `.env`. Never place keys in command arguments, screenshots or Git.

| Setting | Default | Effect |
|---|---|---|
| `LLM_PROVIDER` | Auto-detect if unset | Explicit `demo`, `nvidia`, `openai` or `ollama` is preferred |
| `NVIDIA_API_KEY` / `NVIDIA_MODEL` | See `.env.example` | NVIDIA credentials and model |
| `EREVNA_MAX_LLM_CALLS` | 10 | Operator ceiling, integer 1–10 |
| `EREVNA_API_TOKEN` | Unset | Shared bearer token required for API research unless local mode is explicit |
| `EREVNA_API_LOCAL` | Unset | `1` permits unauthenticated localhost-only API use |
| `INPUT_USD_PER_MILLION`, `OUTPUT_USD_PER_MILLION` | Unknown | Optional pricing for estimates only; no dollar-budget enforcement |

A request's `max_llm_calls` must be within the operator ceiling; omitted means use
the ceiling. Invalid configuration is rejected before a model call. The UI exposes
the same limit and includes it in the cache context. Old exported metrics default
to a ceiling of 10 when read; this does not retroactively establish historical limits.

Every active-pipeline `invoke` checks and increments a shared run counter before
calling the model. Failed invocations consume a slot. JSON format retries, planning,
citation repair and verification all share that counter. Built-in OpenAI-compatible
SDK retries are disabled; there are no additional retries for transport errors.
Custom injected model adapters may implement their own retries and must be configured
accordingly. The limit applies to `run_research` and its UI/API/CLI entrypoints, not
legacy standalone agent helpers or aggregate usage across evaluation cases.

If the budget runs out before generation completes, the API returns 422 and the CLI
exits 1 with a safe message. If generation succeeded but support review cannot run,
the result records `call_budget_exhausted: true`, a warning and withheld findings.
Already supported findings can survive an unavailable narrowing recheck. A run that
uses its final permitted call successfully is not marked exhausted unless another
call is actually blocked. JSON/Markdown output can legitimately contain no findings.

A ceiling bounds application calls, not monetary spend, input tokens, total duration,
concurrent users or daily traffic. Output caps and provider timeouts are separately
configured in `agents/llm_backend.py`; they are not a total-run deadline. API concurrency
is limited to two active requests per process; excess requests receive 429 with a
`Retry-After: 5` header. This is not a distributed rate limiter or per-user quota.
