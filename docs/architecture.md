# Workflow architecture

Streamlit, FastAPI and the command-line entrypoint share `research.pipeline.run_research`.
The pipeline returns a typed `ResearchResult`; presentation code does not rewrite claims.

```mermaid
flowchart TD
    UI[Streamlit session] --> Cache{Fresh matching cache?}
    Cache -->|yes| Display[Render saved result]
    Cache -->|no| Pipeline[Shared research pipeline]
    API[FastAPI: bearer auth and two request slots] --> Pipeline
    CLI[CLI: offline default or explicit live mode] --> Pipeline
    Pipeline --> Plan[Plan: deterministic for supplied documents]
    Plan --> Collect[Provided corpus or bounded public web collection]
    Collect --> Retrieval[Chunk passages and rank evidence]
    Retrieval --> Generate[Structured findings]
    Generate --> Quotes[Validate IDs and literal quotes]
    Quotes -->|invalid quotes| Repair[At most one citation repair]
    Repair --> Review[Fresh-context claim support review]
    Quotes -->|valid quotes| Review
    Review --> Keep[Retain supported claims]
    Review --> Narrow[Partial claim: narrow and recheck once]
    Review --> Exclude[Withhold unsupported or unavailable judgments]
    Keep --> Result[Deterministic report and full run JSON]
    Narrow --> Result
    Exclude --> Result
    Result --> Display
    Result --> Save[UI only: scoped SQLite cache]
```

Every active model stage passes through `research.llm_io.invoke` with the same run
metrics and call ceiling. It checks the limit before invoking the provider. JSON
parsing permits one retry within that ceiling. Failure before generation surfaces a
safe error; failure during verification withholds affected claims. No background
agent, recursive planning loop or unbounded repair loop runs behind this workflow.
Demo mode extracts source text and labels semantic review as skipped.

The UI alone uses the SQLite cache. API and CLI runs execute directly. The cache
context includes session, pipeline version, source inputs, provider/model, retrieval,
review setting and call limit. Cache hits reuse the original run's metrics, not new
provider usage. Reloading a browser creates a new session namespace.

Public web fetching validates destination IPs, pins connections and revalidates
redirects. Prompt text remains untrusted even after network checks. Exact quotation
matching establishes traceability; model support judgments remain fallible and do
not independently establish truth. The support audit preserves excluded claims and
reasons so a reviewer can inspect failures.

The API semaphore and call ceilings are local process/run controls. They do not
provide account identity, per-user daily quotas, distributed concurrency limits or
a whole-run cancellation deadline. See [roadmap](roadmap.md) for remaining work.

Retrieval now uses a corpus-local index that precomputes lexical statistics and, for
dense/hybrid modes, passage vectors. Evaluation reuses it across questions. A normal
research run creates its own index; document vectors are not cached across sessions.
Only the fixed CPU embedding model is reused across requests, with synchronized first
load and a pinned revision. No document content is passed to a hosted embedding API.
