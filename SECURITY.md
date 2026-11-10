# Security and privacy

This is a local portfolio prototype, not an audited multi-user service.

- Credentials stay in local `.env` or hosting secrets. `.env*` is excluded from Docker and Git, except the empty example.
- NVIDIA uses a fixed NVIDIA host and its own credential variable; OpenAI credentials use the OpenAI host.
- Provider exception payloads are not returned to users. The pipeline exposes only safe failure categories.
- Source text is untrusted. Generation prompts forbid following embedded instructions. No generated tools or code are executed.
- Public-page fetching validates DNS results, blocks private/loopback/link-local/reserved addresses, pins the connection IP, validates TLS hostnames, and rechecks redirects.
- Fetches have timeout, redirect, content-type and response-size bounds. An egress firewall is still required for public service deployment.
- API request bodies, question/source sizes and concurrency are bounded. Configure a bearer token unless bound to localhost in explicit local mode.
- Streamlit does not supply identity/authentication. Session-scoped cache separation is not a substitute for accounts and access controls.
- Reports and exported runs may contain provided source content. Treat the SQLite database and downloaded JSON as private when using private documents.
- Quote validation is not semantic proof and cannot guarantee protection from hallucinations or prompt injection.

Report security issues privately to the repository owner. Do not attach credentials, personal data or private source documents to public issues.

Model-based claim review is an additional fallible filter, not a security boundary
or proof of factual truth. It uses the configured generation model in a fresh context;
source prompt injection and verdict/reason inconsistencies remain possible. Inspect
the claim audit and independently review consequential outputs.
