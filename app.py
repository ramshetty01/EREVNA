"""EREVNA: inspectable evidence-backed research, powered by a shared pipeline."""

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

import streamlit as st

from agents.llm_backend import get_mode, mode_label, model_name
from agents.memory_agent import MemoryAgent
from agents.plan_schema import format_plan
from research.budgets import resolve_call_limit
from research.models import Document, ResearchResult
from research.pipeline import ResearchError, run_research
from tools.web_search import scrape_page

ROOT = Path(__file__).parent
st.set_page_config(page_title="EREVNA | Evidence-backed research", page_icon="◈", layout="wide")
st.markdown(
    """<style>
.stApp {background:#f6f3ec;color:#21352f}
h1,h2,h3 {font-family:Georgia,serif!important;letter-spacing:-.035em}
h1 {font-size:3.7rem!important;font-weight:500!important;line-height:1.08!important;max-width:850px}
.block-container {max-width:1180px;padding-top:2.5rem;padding-bottom:4rem}
[data-testid="stSidebar"] {background:#e9e8df;border-right:1px solid #d0d5ca}
[data-testid="stMetric"] {border-top:1px solid #b5c1b7;padding-top:1rem}
[data-testid="stMetricValue"] {font-family:Georgia,serif;font-size:1.8rem}
.stButton>button[kind="primary"] {background:#245b49;border:0;color:white}
[data-testid="stCaptionContainer"] {color:#52655d}
@media(max-width:650px){h1{font-size:2.6rem!important}.block-container{padding-top:1.5rem}}
</style>""",
    unsafe_allow_html=True,
)

defaults: dict[str, Any] = {
    "session_id": uuid.uuid4().hex,
    "runs": [],
    "selected_run": None,
    "cache_notice": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

with st.sidebar:
    st.markdown("### EREVNA")
    st.caption("A research notebook with evidence you can inspect.")
    st.divider()
    source_mode = st.radio("Research sources", ["Bundled example", "Live web", "Specific URLs"])
    st.caption(
        "The bundled example uses fictional Harbor product documentation. It is a reproducible development fixture."
    )
    method = st.selectbox("Retrieval method", ["bm25", "dense", "hybrid"])
    if method != "bm25":
        st.caption("Dense and hybrid retrieval require the optional local embedding model.")
    fresh = st.checkbox("Run fresh — bypass saved results", value=False)
    verify_support = st.checkbox("Review claim support", value=True)
    st.caption(
        "Uses extra model calls to check each claim against its evidence. Model judgments can still be wrong."
    )
    try:
        call_ceiling = resolve_call_limit()
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    max_llm_calls = st.number_input(
        "Maximum model calls", min_value=1, max_value=call_ceiling, value=call_ceiling, step=1
    )
    st.caption("Includes generation, retries and claim review. A low limit can leave no verified findings.")
    st.divider()
    st.caption(mode_label())
    st.caption("Saved results expire after 24 hours and are isolated to this browser session.")
    if st.button("New research", use_container_width=True):
        st.session_state.selected_run = None
        st.session_state.cache_notice = False
    if st.session_state.runs:
        if st.button("Delete session history", key="delete_session_history", use_container_width=True):
            try:
                MemoryAgent(
                    os.getenv("EREVNA_CACHE_DB", str(ROOT / "database/memory.db")),
                    namespace=st.session_state.session_id,
                ).clear()
                st.session_state.runs = []
                st.session_state.selected_run = None
                st.session_state.cache_notice = False
                st.success("This session’s saved history was deleted.")
            except Exception:
                st.error("History could not be deleted. Check local cache access and retry.")
        st.markdown("#### Recent research")
        for item in reversed(st.session_state.runs[-10:]):
            if st.button(
                item["query"][:48], key=f"history-{item['run_id']}", use_container_width=True
            ):
                st.session_state.selected_run = item
                st.session_state.cache_notice = False
    st.link_button("View source on GitHub", "https://github.com/ramshetty01/EREVNA")

st.caption("RESEARCH / EVIDENCE / ACCOUNTABILITY")
st.title("Evidence, before answers.")
st.write("Ask a question. Read the findings. Follow each citation back to the exact passage.")
with st.form("research_form"):
    default = (
        "How does Harbor check citations, and what do those checks not prove?"
        if source_mode == "Bundled example"
        else ""
    )
    question = st.text_input(
        "Research question",
        value=default,
        placeholder="What would you like to understand?",
        max_chars=1500,
    )
    urls_text = (
        st.text_area(
            "Source URLs — one per line, up to six", placeholder="https://docs.example.com/guide"
        )
        if source_mode == "Specific URLs"
        else ""
    )
    submitted = st.form_submit_button("Start research", type="primary")

if submitted:
    st.session_state.cache_notice = False
    st.session_state.selected_run = None
    if not question.strip():
        st.warning("Enter a research question first.")
    else:
        try:
            documents = None
            if source_mode == "Bundled example":
                data = json.loads((ROOT / "data/development_set.json").read_text())
                documents = [Document(**d) for d in data["documents"]]
            context = hashlib.sha256(
                json.dumps(
                    [
                        "pipeline-v0.5-retrieval-index",
                        max_llm_calls,
                        verify_support,
                        source_mode,
                        urls_text,
                        method,
                        get_mode(),
                        model_name(),
                        [d.model_dump(exclude={"fetched_at"}) for d in documents]
                        if documents is not None
                        else None,
                    ],
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            memory = MemoryAgent(
                os.getenv("EREVNA_CACHE_DB", str(ROOT / "database/memory.db")), namespace=st.session_state.session_id
            )
            cached = None if fresh else memory.get_similar(question, context=context)
            if cached and cached.get("payload"):
                result = ResearchResult.model_validate(cached["payload"])
                st.session_state.cache_notice = True
            else:
                with st.status("Research in progress", expanded=True) as status:
                    if source_mode == "Specific URLs":
                        urls = list(
                            dict.fromkeys(u.strip() for u in urls_text.splitlines() if u.strip())
                        )
                        if not 1 <= len(urls) <= 6:
                            raise ValueError("Provide between one and six source URLs.")
                        documents = []
                        for url in urls:
                            text = scrape_page(url)
                            if text:
                                documents.append(
                                    Document(title=url, url=url, text=text, status="page")
                                )
                            else:
                                st.warning(f"Could not read this source: {url}")
                    result = run_research(
                        question,
                        documents=documents,
                        retrieval=method,
                        verify_support=verify_support,
                        max_llm_calls=max_llm_calls,
                        progress=lambda stage: st.write(stage),
                    )
                    status.update(label="Research complete", state="complete", expanded=False)
                memory.save(question, result.report, context=context, payload=result.model_dump())
            st.session_state.selected_run = result.model_dump()
            if not any(r["run_id"] == result.run_id for r in st.session_state.runs):
                st.session_state.runs.append(result.model_dump())
        except (ValueError, ResearchError) as exc:
            st.error(str(exc))
        except Exception:
            st.error(
                "The run could not be saved or completed. Please retry. Your API credential was not logged."
            )

if st.session_state.selected_run:
    result = ResearchResult.model_validate(st.session_state.selected_run)
    if st.session_state.cache_notice:
        st.info(
            "Loaded a saved result from this session. Enable Run fresh to collect new evidence."
        )
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sources", result.metrics.source_count)
    c2.metric("Evidence passages", result.metrics.passage_count)
    c3.metric("Run time", f"{result.metrics.step_seconds.get('total', 0):.1f}s")
    cost = result.metrics.estimated_cost_usd
    c4.metric("Estimated cost", f"${cost:.5f}" if cost is not None else "Not configured")
    report_tab, evidence_tab, review_tab, plan_tab, run_tab = st.tabs(
        ["Report", "Evidence", "Claim review", "Research plan", "Run details"]
    )
    with report_tab:
        for warning in result.warnings:
            st.warning(warning)
        st.markdown(result.report)
        st.download_button(
            "Download report",
            result.report,
            file_name=f"erevna-{result.run_id[:8]}.md",
            mime="text/markdown",
        )
    with evidence_tab:
        st.caption(
            "These are the passages provided to the model. Quote checks verify text matches; they do not certify factual correctness."
        )
        for p in result.passages:
            with st.expander(f"{p.id} · {p.title}", expanded=True):
                st.write(p.text)
                st.link_button("Open source", p.url)
                st.caption(f"Retrieval score: {p.score:.4f}")
        st.markdown("#### Source acquisition")
        for doc in result.documents:
            st.write(f"{doc.title} — {doc.status}")
            st.caption(f"Acquired: {doc.fetched_at}")
    with review_tab:
        review = result.support_review
        st.caption(f"Review status: {review.status}. {review.note}")
        if not review.claims:
            st.info(
                "No claim judgments are available for this run. Demo and review-disabled runs do not perform semantic verification."
            )
        for item in review.claims:
            label = item.decision.verdict if item.decision else "unavailable"
            with st.expander(
                f"Finding {item.finding_id + 1} · {label} · {item.disposition}", expanded=True
            ):
                st.write("Original claim:", item.original.claim)
                if item.decision:
                    st.write("Reason:", item.decision.reason)
                    st.write("Evidence IDs:", ", ".join(item.decision.evidence_ids))
                if item.final_claim and item.disposition == "narrowed":
                    st.write("Narrowed claim:", item.final_claim)
                if item.recheck:
                    st.write("Recheck:", item.recheck.verdict, "—", item.recheck.reason)
                if item.error:
                    st.warning(item.error)
    with plan_tab:
        st.markdown(format_plan(result.plan))
        st.caption(
            "A deterministic plan is used for provided documents; live-web mode can use model-generated planning."
        )
    with run_tab:
        st.write(f"Run ID: {result.run_id}")
        st.json(result.metrics.model_dump())
        st.caption(
            "Token counts reflect provider-reported usage. Dollar estimates require explicit model pricing. A JSON export includes the source text used in this run."
        )
        st.download_button(
            "Download full run JSON",
            result.model_dump_json(indent=2),
            file_name=f"erevna-{result.run_id[:8]}.json",
            mime="application/json",
        )
else:
    st.divider()
    left, right = st.columns([2, 1])
    with left:
        st.markdown("### Every finding has a trail.")
        st.write(
            "EREVNA retains source passages, asks for supporting quotations, and removes findings with invalid references or quotes that do not match. When evidence is insufficient, it says so."
        )
    with right:
        st.markdown("### Start with an example")
        st.write(
            "Use the bundled documentation to explore retrieval, citations and exports without relying on live search."
        )
    st.caption(
        "Citation checks establish traceability, not truth. Review the evidence before relying on a report."
    )
