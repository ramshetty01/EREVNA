import numpy as np

from agents.memory_agent import MemoryAgent
from agents.plan_schema import ResearchPlan, format_plan
from agents.search_agent import _search_queries


def test_format_plan_renders_all_sections():
    plan = ResearchPlan(
        objective="Understand AI agent frameworks",
        steps=["Survey docs", "Compare features"],
        expected_sources=["Official docs", "GitHub repos"],
        key_questions=["Which are open source?", "Which support tool use?"],
    )
    rendered = format_plan(plan)
    assert "Understand AI agent frameworks" in rendered
    assert "Survey docs" in rendered
    assert "Official docs" in rendered
    assert "Which are open source?" in rendered


def test_search_queries_uses_plan_questions():
    plan = ResearchPlan(
        objective="Test objective",
        steps=["Step 1"],
        expected_sources=["Web"],
        key_questions=["What is LangGraph?", "What is CrewAI?", "What is AutoGen?"],
    )
    queries = _search_queries("AI agent frameworks 2025", plan)
    assert queries[0] == "AI agent frameworks 2025"
    assert "What is LangGraph?" in queries
    assert len(queries) <= 4


def test_search_queries_deduplicates():
    plan = ResearchPlan(
        objective="Test",
        steps=["Step"],
        expected_sources=["Web"],
        key_questions=["AI agents", "AI Agents"],
    )
    queries = _search_queries("AI agents", plan)
    assert len(queries) == 1


def test_memory_agent_finds_similar_task(tmp_path):
    db_path = tmp_path / "test_memory.db"

    class Encoder:
        def encode(self, text):
            return np.array([1.0, 0.0])

    memory = MemoryAgent(db_path=str(db_path), encoder=Encoder())

    memory.save(
        "Latest trends in AI agent frameworks",
        "# Report\nLangGraph and CrewAI lead the space.",
    )
    match = memory.get_similar("What are the top AI agent frameworks right now?")
    assert match is not None
    assert "LangGraph" in match["report"]


def test_memory_agent_returns_none_for_unrelated_query(tmp_path):
    db_path = tmp_path / "test_memory.db"
    memory = MemoryAgent(db_path=str(db_path))

    memory.save("Best pizza recipes in Naples", "# Report\nMargherita is classic.")
    match = memory.get_similar("Quantum computing error correction codes")
    assert match is None
