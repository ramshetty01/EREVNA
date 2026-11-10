from streamlit.testing.v1 import AppTest


def test_bundled_flow_cache_history_and_validation(tmp_path, monkeypatch):
    # Use a temporary cache so the browser test does not touch developer history.
    from agents.memory_agent import MemoryAgent

    monkeypatch.setattr(
        "agents.memory_agent.MemoryAgent",
        lambda *a, **k: MemoryAgent(
            str(tmp_path / "cache.db"), namespace=k.get("namespace", "test")
        ),
    )
    app = AppTest.from_file(
        str(__import__("pathlib").Path(__file__).resolve().parents[1] / "app.py"),
        default_timeout=20,
    ).run()
    assert not app.exception
    app.button(key="FormSubmitter:research_form-Start research").click().run()
    assert not app.exception
    assert len(app.tabs) == 4
    assert "Findings" in app.session_state.selected_run["report"]
    assert app.session_state.selected_run["metrics"]["provider"] == "demo"
    app.button(key="FormSubmitter:research_form-Start research").click().run()
    assert not app.exception
    assert app.session_state.cache_notice is True
    assert len(app.session_state.runs) == 1
    app.text_input[0].set_value(" ")
    app.button(key="FormSubmitter:research_form-Start research").click().run()
    assert not app.exception
    assert app.session_state.selected_run is None
