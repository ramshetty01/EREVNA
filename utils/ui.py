"""UI helpers — ChatGPT-inspired minimal dark theme."""

import html

import streamlit as st

QUICK_ACTIONS = [
    ("compare", "Compare tools", "Compare LangGraph vs CrewAI for production use"),
    ("deepdive", "Deep dive a topic", "What are the top AI agent frameworks in 2025?"),
    ("lookup", "Look something up", "Latest breakthroughs in quantum computing"),
    ("report", "Write a report", "How is RAG evolving for enterprise search?"),
]


def inject_styles() -> None:
    st.markdown(
        """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Söhne-style,Inter,system-ui,sans-serif');

        /* ── Base ── */
        .stApp {
            background-color: #000000 !important;
        }
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: #ececec;
        }
        #MainMenu, footer, header[data-testid="stHeader"] {
            visibility: hidden;
            height: 0;
        }
        .block-container {
            padding: 0 1rem 6rem 1rem;
            max-width: 768px;
        }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background-color: #0d0d0d !important;
            border-right: 1px solid #2a2a2a;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }
        section[data-testid="stSidebar"] hr {
            border-color: #2a2a2a;
            margin: 0.75rem 0;
        }

        /* ── Greeting ── */
        .greeting-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 42vh;
            text-align: center;
            padding: 2rem 1rem 1rem;
        }
        .greeting-text {
            font-size: 1.75rem;
            font-weight: 400;
            color: #ececec;
            letter-spacing: -0.02em;
            margin: 0;
            line-height: 1.3;
        }
        .greeting-sub {
            font-size: 0.85rem;
            color: #6b6b6b;
            margin-top: 0.6rem;
        }

        /* ── Mode badge (top-right feel) ── */
        .mode-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 999px;
            padding: 0.3rem 0.75rem;
            font-size: 0.72rem;
            color: #888;
            margin-bottom: 0.5rem;
        }
        .mode-dot {
            width: 6px; height: 6px;
            border-radius: 50%;
            background: #22c55e;
        }
        .mode-dot.demo { background: #eab308; }

        /* ── Quick-action chips ── */
        .chips-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            justify-content: center;
            margin: 0 auto 1.25rem;
            max-width: 640px;
        }
        div[data-testid="column"] button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid #3a3a3a !important;
            border-radius: 999px !important;
            color: #ececec !important;
            font-size: 0.82rem !important;
            padding: 0.45rem 1rem !important;
            transition: background 0.15s;
        }
        div[data-testid="column"] button[kind="secondary"]:hover {
            background: #1a1a1a !important;
            border-color: #555 !important;
        }

        /* ── Chat input bar ── */
        div[data-testid="stChatInput"] {
            max-width: 768px;
            margin: 0 auto;
        }
        div[data-testid="stChatInput"] textarea {
            background: #2f2f2f !important;
            border: 1px solid #444 !important;
            border-radius: 1.5rem !important;
            color: #ececec !important;
            font-size: 0.95rem !important;
            padding: 0.75rem 1.25rem !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.4) !important;
        }
        div[data-testid="stChatInput"] textarea:focus {
            border-color: #666 !important;
            box-shadow: 0 2px 16px rgba(0,0,0,0.5) !important;
        }
        div[data-testid="stChatInput"] textarea::placeholder {
            color: #888 !important;
        }

        /* ── User query bubble ── */
        .user-query {
            background: #2f2f2f;
            border-radius: 1.25rem;
            padding: 0.85rem 1.15rem;
            margin: 1.5rem 0 1rem;
            font-size: 0.95rem;
            color: #ececec;
            line-height: 1.5;
        }

        /* ── Pipeline status ── */
        .pipeline-status {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.6rem 0;
            color: #888;
            font-size: 0.82rem;
        }
        .pipeline-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: #666;
            animation: pulse 1.2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 1; }
        }
        .pipeline-steps-inline {
            display: flex;
            gap: 0.35rem;
            margin: 0.75rem 0 1.25rem;
        }
        .p-step {
            font-size: 0.72rem;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            border: 1px solid #333;
            color: #666;
        }
        .p-step.done {
            border-color: #444;
            color: #aaa;
            background: #1a1a1a;
        }
        .p-step.active {
            border-color: #666;
            color: #ececec;
            background: #2a2a2a;
        }

        /* ── Result sections ── */
        .result-block {
            margin-bottom: 1.5rem;
        }
        .result-label {
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #666;
            margin-bottom: 0.5rem;
        }
        .result-body {
            font-size: 0.92rem;
            line-height: 1.65;
            color: #d4d4d4;
        }
        .result-body h1, .result-body h2, .result-body h3 {
            color: #ececec;
            font-weight: 600;
        }

        /* ── Source cards ── */
        .source-card {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 0.75rem;
            padding: 0.85rem 1rem;
            margin-bottom: 0.5rem;
        }
        .source-card:hover { border-color: #444; }
        .source-title {
            font-weight: 500;
            color: #ececec;
            font-size: 0.85rem;
            margin-bottom: 0.2rem;
        }
        .source-url {
            font-size: 0.72rem;
            color: #666;
            word-break: break-all;
            margin-bottom: 0.35rem;
        }
        .source-snippet {
            font-size: 0.8rem;
            color: #888;
            line-height: 1.45;
        }

        /* ── Cache banner ── */
        .cache-banner {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 0.75rem;
            padding: 1rem 1.15rem;
            margin: 1rem 0;
            font-size: 0.88rem;
            color: #aaa;
        }

        /* ── Tabs (minimal) ── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background: transparent;
            border-bottom: 1px solid #2a2a2a;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: #666;
            font-size: 0.82rem;
            padding: 0.5rem 1rem;
            border-radius: 0;
        }
        .stTabs [aria-selected="true"] {
            color: #ececec !important;
            border-bottom: 2px solid #ececec;
        }

        /* ── Buttons ── */
        .stButton > button[kind="primary"] {
            background: #ececec !important;
            color: #000 !important;
            border-radius: 999px !important;
            border: none !important;
            font-weight: 500 !important;
        }
        .stButton > button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid #444 !important;
            color: #ececec !important;
            border-radius: 999px !important;
        }

        /* ── Sidebar history ── */
        .sidebar-title {
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #555;
            margin: 0.5rem 0;
        }
        section[data-testid="stSidebar"] button {
            background: transparent !important;
            border: none !important;
            color: #aaa !important;
            text-align: left !important;
            font-size: 0.82rem !important;
            padding: 0.5rem 0.65rem !important;
            border-radius: 0.5rem !important;
        }
        section[data-testid="stSidebar"] button:hover {
            background: #1a1a1a !important;
            color: #ececec !important;
        }

        /* ── Progress bar ── */
        .stProgress > div > div {
            background-color: #333 !important;
        }
        .stProgress > div > div > div {
            background-color: #ececec !important;
        }

        /* ── Alerts ── */
        div[data-testid="stAlert"] {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 0.75rem;
            color: #aaa;
        }

        /* ── Download ── */
        .stDownloadButton button {
            border-radius: 999px !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_greeting(has_results: bool) -> None:
    if has_results:
        return
    st.markdown(
        """
    <div class="greeting-wrap">
        <p class="greeting-text">Ready when you are.</p>
        <p class="greeting-sub">Multi-agent research · plan · search · analyze · report</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_mode_badge(mode: str, label: str) -> None:
    dot_class = "demo" if mode == "demo" else ""
    st.markdown(
        f"""
    <div style="text-align:center;">
        <span class="mode-badge">
            <span class="mode-dot {dot_class}"></span>
            {html.escape(label)}
        </span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_quick_actions() -> None:
    cols = st.columns(len(QUICK_ACTIONS))
    for i, (key, label, prompt) in enumerate(QUICK_ACTIONS):
        with cols[i]:
            if st.button(label, key=f"chip_{key}", use_container_width=True):
                st.session_state.auto_run_query = prompt
                st.rerun()


def render_pipeline_inline(active: str | None, completed: list[str]) -> None:
    steps = [("plan", "Plan"), ("search", "Search"), ("analyze", "Analyze"), ("report", "Report")]
    chips = ""
    for key, label in steps:
        if key in completed:
            state = "done"
        elif key == active:
            state = "active"
        else:
            state = ""
        chips += f'<span class="p-step {state}">{label}</span>'
    st.markdown(f'<div class="pipeline-steps-inline">{chips}</div>', unsafe_allow_html=True)


def render_user_query(query: str) -> None:
    st.markdown(f'<div class="user-query">{html.escape(query)}</div>', unsafe_allow_html=True)


def render_search_results(search_results: dict) -> None:
    results = search_results.get("web_results", [])
    if not results:
        st.caption("No web sources found.")
        return
    st.caption(f"{len(results)} sources")
    for r in results:
        title = html.escape(r.get("title") or "Untitled")
        url = html.escape(r.get("url", ""))
        raw = r.get("snippet", "")
        snippet = html.escape(raw[:220])
        st.markdown(
            f"""
        <div class="source-card">
            <div class="source-title">{title}</div>
            <div class="source-url">{url}</div>
            <div class="source-snippet">{snippet}{"…" if len(raw) > 220 else ""}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_cache_prompt(cached_task: str) -> None:
    safe = html.escape(cached_task)
    st.markdown(
        f"""
    <div class="cache-banner">
        Similar research found — <em>{safe}</em>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar(history: list, mode_label: str) -> None:
    with st.sidebar:
        if st.button("＋  New research", use_container_width=True):
            st.session_state.last_result = None
            st.session_state.view_history_idx = None
            st.session_state.pending_query = None
            st.session_state.cached_match = None
            st.session_state.query_input = ""
            st.rerun()

        st.markdown(
            f'<p class="sidebar-title">{html.escape(mode_label)}</p>', unsafe_allow_html=True
        )
        st.markdown("---")

        if not history:
            st.caption("No research yet.")
        else:
            st.markdown('<p class="sidebar-title">History</p>', unsafe_allow_html=True)
            for i, item in enumerate(reversed(history[-12:])):
                idx = len(history) - i
                query = item["query"]
                label = query[:42] + ("…" if len(query) > 42 else "")
                if st.button(label, key=f"hist_{idx}", use_container_width=True):
                    st.session_state.view_history_idx = len(history) - i - 1
                    st.session_state.last_result = None
                    st.rerun()

        st.markdown("---")
        st.caption("[GitHub](https://github.com/ramshetty01/EREVNA)")
