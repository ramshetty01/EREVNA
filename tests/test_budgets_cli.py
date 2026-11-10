import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from research.__main__ import main
from research.budgets import resolve_call_limit
from research.llm_io import BudgetExceeded, invoke, structured
from research.models import Document, Evidence, Finding, GroundedAnswer, RunMetrics
from research.pipeline import run_research


def test_budget_counts_failed_requests_and_blocks_next_call():
    metrics = RunMetrics(provider="test", model="test", max_llm_calls=1)
    model = Mock()
    model.invoke.side_effect = RuntimeError("private")
    with pytest.raises(RuntimeError):
        invoke(model, [], metrics)
    with pytest.raises(BudgetExceeded):
        invoke(model, [], metrics)
    assert model.invoke.call_count == 1
    assert metrics.llm_calls == 1 and metrics.call_budget_exhausted
    assert not metrics.usage_complete


def test_format_retry_cannot_exceed_budget():
    model = Mock()
    model.invoke.return_value = SimpleNamespace(content="not json", usage_metadata=None)
    metrics = RunMetrics(provider="test", model="test", max_llm_calls=1)
    with pytest.raises(BudgetExceeded):
        structured(model, [], GroundedAnswer, metrics)
    assert model.invoke.call_count == 1


def test_budget_exhaustion_withholds_unreviewed_findings(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    quote = "The service encrypts data in transit."
    answer = GroundedAnswer(
        findings=[Finding(claim=quote, evidence=[Evidence(passage_id="S1-P1", quote=quote)])]
    )
    model = Mock()
    model.invoke.return_value = SimpleNamespace(
        content=answer.model_dump_json(), usage_metadata={"input_tokens": 12, "output_tokens": 24}
    )
    result = run_research(
        "encrypts data",
        documents=[Document(title="Security", url="https://example.org", text=quote)],
        llm=model,
        max_llm_calls=1,
    )
    assert not result.answer.findings
    assert result.support_review.status == "failed"
    assert result.metrics.call_budget_exhausted
    assert result.metrics.llm_calls == model.invoke.call_count == 1
    assert "budget exhausted" in result.warnings[0]


def test_operator_ceiling_cannot_be_raised_by_caller(monkeypatch):
    monkeypatch.setenv("EREVNA_MAX_LLM_CALLS", "3")
    assert resolve_call_limit() == 3
    assert resolve_call_limit(2) == 2
    for value in (4, 0, True, 2.5):
        with pytest.raises(ValueError):
            resolve_call_limit(value)
    monkeypatch.setenv("EREVNA_MAX_LLM_CALLS", "secret-invalid-setting")
    with pytest.raises(ValueError, match="must be an integer") as exc:
        resolve_call_limit()
    assert "secret-invalid" not in str(exc.value)


def test_cli_defaults_to_offline_demo_and_restores_provider(monkeypatch, capsys):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setattr(
        "research.pipeline.get_llm", Mock(side_effect=AssertionError("No model allowed"))
    )
    assert main(["How does Harbor check citations?"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["metrics"]["provider"] == "demo"
    assert result["metrics"]["llm_calls"] == 0
    import os

    assert os.environ["LLM_PROVIDER"] == "nvidia"


def test_cli_documents_markdown_and_bad_input(tmp_path, capsys):
    source = tmp_path / "docs.json"
    output = tmp_path / "report.md"
    source.write_text(
        json.dumps(
            [
                {
                    "title": "Cache",
                    "url": "https://example.org/cache",
                    "text": "Cache entries expire after 24 hours.",
                }
            ]
        )
    )
    assert (
        main(
            [
                "Cache expiry",
                "--documents",
                str(source),
                "--format",
                "markdown",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert "24 hours" in output.read_text()
    source.write_text('{"documents": [{"private": "do-not-print"}]}')
    assert main(["Cache expiry", "--documents", str(source)]) == 1
    assert "do-not-print" not in capsys.readouterr().err
    source.write_text('"do-not-print"')
    assert main(["Cache expiry", "--documents", str(source)]) == 1


def test_cli_live_forwards_settings(monkeypatch, capsys):
    result = Mock()
    result.model_dump_json.return_value = '{"ok": true}'
    runner = Mock(return_value=result)
    monkeypatch.setattr("research.__main__.run_research", runner)
    assert main(["question", "--live", "--web", "--max-llm-calls", "3", "--no-support-review"]) == 0
    assert runner.call_args.kwargs["documents"] is None
    assert runner.call_args.kwargs["max_llm_calls"] == 3
    assert runner.call_args.kwargs["verify_support"] is False
