# Running and deployment

## Local environment

Use Python 3.12 and `requirements.lock` for the tested default environment. The local app
is `streamlit run app.py --server.address=127.0.0.1 --server.port=8501`.
The `scripts/run_local.sh` shortcut uses the repository's `.venv`.

Keep provider credentials in `.env` (ignored by Git and Docker) or your hosting secret store.
NVIDIA configuration uses `LLM_PROVIDER=nvidia`, `NVIDIA_API_KEY`, and `NVIDIA_MODEL`.
A retired model returns HTTP 410: choose an available model in NVIDIA's catalogue rather
than repeatedly retrying. No credentials are needed for `LLM_PROVIDER=demo`.

## Container

```sh
docker build -t erevna:local .
docker run --rm -p 127.0.0.1:8501:8501 --env-file .env erevna:local
```

The container uses Python 3.12 and exposes a Streamlit health check. Docker build/run was
not part of the local validation on this workstation; CI has a Docker build job.

## API

Bind to `127.0.0.1:8000` for local use. `/health` and the schema are public. `/research`
requires a bearer token unless `EREVNA_API_LOCAL=1` is explicitly enabled. Never combine
local-only mode with a public bind address or a public reverse proxy.

For sharing, set `EREVNA_API_TOKEN` in the hosting secret store and put the service behind
TLS, request quotas, authentication and an egress firewall. The two-request semaphore is
per process, not a distributed rate limiter. The Streamlit interface does not provide user
authentication and must not be publicly exposed with an unrestricted API credential.

## Persistence and retention

SQLite reports are scoped by browser session and a context hash including provider, model,
retrieval method and supplied corpus/URLs. Entries older than 24 hours are excluded from cache
lookup. Records older than 30 days are purged on the next write. Reloading the browser creates
a new namespace; there is no cross-device account history. A JSON export contains source text.

Use a private persistent volume for a local deployment. Before multi-user hosting, add identity,
access controls, deletion requests and a retention job. Local JSON artifacts and screenshots
are excluded from Git unless explicitly copied into public documentation.

## Operational checks

- `/health`: API process health; not a check of model/search availability.
- `/_stcore/health`: Streamlit health.
- `make test`, `make evaluate`: offline regression checks; no provider requests.
- `make live-evaluate`: three explicit provider requests, subject to parser retries.
- Unknown pricing stays unknown. Set both input/output USD-per-million prices only for your model.
