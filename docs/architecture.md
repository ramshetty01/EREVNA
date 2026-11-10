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

## Runtime sequence

```mermaid
sequenceDiagram
    participant Client
    participant Pipeline
    participant Model
    participant Validator
    Client->>Pipeline: Query, source inputs, review setting, call limit
    Pipeline->>Pipeline: Plan, collect and retrieve passages
    Pipeline->>Model: Structured findings, if live and budget permits
    Model-->>Pipeline: Findings and reported usage
    Pipeline->>Validator: Check passage IDs and exact quotes
    Validator-->>Pipeline: Retained findings and rejection count
    opt Citation repair needed and budget available
      Pipeline->>Model: One bounded repair attempt
    end
    opt Live support review enabled
      Pipeline->>Model: Fresh-context claim-support decisions
      opt Partial claims and budget available
        Pipeline->>Model: One narrowing recheck batch
      end
    end
    Pipeline-->>Client: Deterministic report, evidence, audit and metrics
```

## Cache lifecycle

```mermaid
flowchart LR
    Session[New browser session namespace] --> Key[Question plus context hash]
    Key --> Lookup[SQLite lookup]
    Lookup --> Fresh{Matching record under 24 hours old?}
    Fresh -->|yes| Saved[Render saved result and original metrics]
    Fresh -->|no| Run[Execute pipeline]
    Run --> Write[Save result]
    Write --> Purge[Remove records older than 30 days on writes]
```

## Evaluation flow

```mermaid
flowchart LR
    Fixture[Authored fixture plus provenance] --> Offline[Offline retrieval or quote baseline]
    Fixture --> OptIn[Explicit live evaluation]
    OptIn --> Review[Configured model with bounded calls]
    Offline --> Scores[Per-case results and metrics]
    Review --> Scores
    Scores --> Limits[Record failures, denominators and limitations]
    Fixture --> Blind[Blind CSV for independent human labels]
```

## Current deployment topology

```mermaid
flowchart TD
    Browser[Local browser] --> UI[Streamlit on localhost]
    Client[CLI or authenticated API client] --> API[FastAPI on localhost]
    UI --> Pipeline[Shared pipeline]
    API --> Pipeline
    UI --> SQLite[Local SQLite cache]
    Pipeline --> Web[Validated public web destinations]
    Pipeline --> Provider[Configured model provider]
    Pipeline --> Encoder[Optional local CPU embedding model]
```

Docker packages the app, but this diagram describes the tested local topology. A
public deployment still needs TLS, identity/authorization, shared quotas/persistence,
retention/deletion, network egress controls and deployed load testing.
