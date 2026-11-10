from agents.demo_agents import demo_analyst, demo_planner, demo_report
from agents.llm_backend import get_mode, is_demo_mode


def test_demo_mode_is_default_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    assert get_mode() == "demo"
    assert is_demo_mode()


def test_demo_planner_returns_structured_plan():
    plan = demo_planner("AI agent frameworks")
    assert plan.objective
    assert len(plan.steps) >= 3
    assert len(plan.key_questions) >= 3


def test_demo_analyst_includes_source_count():
    analysis = demo_analyst(
        "AI agents",
        demo_planner("AI agents"),
        raw_content="Sample scraped content from the web.",
        source_count=3,
    )
    assert "3 web sources" in analysis
    assert "## Summary" in analysis


def test_demo_report_wraps_analysis():
    task = "Quantum computing trends"
    plan = demo_planner(task)
    analysis = demo_analyst(task, plan, "", 0)
    report = demo_report(task, plan, analysis)
    assert f"# Research Report: {task}" in report
    assert "Demo Mode" in report
