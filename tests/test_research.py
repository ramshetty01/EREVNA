import json
from types import SimpleNamespace

import pytest

from research.citations import check_answer
from research.models import Document, Evidence, Finding, GroundedAnswer
from research.pipeline import ResearchError, run_research
from research.retrieval import chunk_documents, retrieve


def corpus():
    return [
        Document(
            title="Retries",
            url="https://example.org/retries",
            text="Retry failed requests with exponential backoff and jitter. Never retry a payment without an idempotency key.",
        ),
        Document(
            title="Caching",
            url="https://example.org/cache",
            text="Cache entries expire after twenty minutes. Namespaces isolate cached reports between users.",
        ),
    ]


def test_retrieves_answer_beyond_original_500_character_cutoff():
    docs = [
        Document(
            title="Manual",
            url="https://example.org/manual",
            text=("Navigation links introduction " * 100)
            + "The zephyr widget operates at precisely seventeen volts.",
        )
    ]
    passages = retrieve("zephyr widget volts", chunk_documents(docs), k=1)
    assert "seventeen volts" in passages[0].text
    assert passages[0].id != "S1-P1"


def test_bm25_ranking_and_no_match():
    passages = chunk_documents(corpus())
    assert retrieve("retry requests", passages, k=1)[0].source_id == "S1"
    assert retrieve("zebras migration", passages) == []


def test_chunk_dedup_and_overlap_validation():
    assert len(chunk_documents([corpus()[0], corpus()[0]])) == 1
    with pytest.raises(ValueError):
        chunk_documents(corpus(), size=20, overlap=20)


def test_citation_rejects_fabricated_ids_and_quotes():
    passages = chunk_documents(corpus())
    valid = Finding(
        claim="Use backoff.",
        evidence=[Evidence(passage_id="S1-P1", quote="exponential backoff and jitter")],
    )
    bad_id = Finding(
        claim="Unsupported.",
        evidence=[Evidence(passage_id="S99-P1", quote="exponential backoff and jitter")],
    )
    bad_quote = Finding(
        claim="Unsupported.",
        evidence=[Evidence(passage_id="S1-P1", quote="invented source statement entirely")],
    )
    answer, rejected = check_answer(GroundedAnswer(findings=[valid, bad_id, bad_quote]), passages)
    assert rejected == 2
    assert answer.findings == [valid]


def test_pipeline_no_evidence_abstains_without_calling_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")

    class NeverCall:
        def invoke(self, _):
            pytest.fail("No evidence should not call the model")

    result = run_research("zebras", documents=corpus(), llm=NeverCall())
    assert result.answer.insufficient_evidence
    assert result.metrics.llm_calls == 0


def test_live_pipeline_contract_usage_and_citations(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")

    class Model:
        def invoke(self, messages):
            assert "UNTRUSTED DATA" in str(messages)
            return SimpleNamespace(
                content=json.dumps(
                    {
                        "findings": [
                            {
                                "claim": "Use exponential backoff with jitter.",
                                "evidence": [
                                    {
                                        "passage_id": "S1-P1",
                                        "quote": "Retry failed requests with exponential backoff and jitter.",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                usage_metadata={"input_tokens": 100, "output_tokens": 50},
            )

    result = run_research("retry requests", documents=corpus(), llm=Model())
    assert result.metrics.accepted_findings == 1
    assert result.metrics.input_tokens == 100
    assert result.metrics.estimated_cost_usd is None
    assert "[S1-P1](https://example.org/retries)" in result.report


def test_parser_retries_once_and_does_not_leak_raw_errors(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")

    class Model:
        calls = 0

        def invoke(self, _):
            self.calls += 1
            return SimpleNamespace(content="secret arbitrary bad model output", usage_metadata={})

    model = Model()
    with pytest.raises(ResearchError, match="invalid structured output twice") as exc:
        run_research("retry", documents=corpus(), llm=model)
    assert model.calls == 2
    assert "secret" not in str(exc.value)


def test_demo_pipeline_exports_typed_result():
    result = run_research("retry requests", documents=corpus())
    assert result.metrics.provider == "demo"
    assert result.metrics.llm_calls == 0
    assert "Extractive demo" in result.report
    assert json.loads(result.model_dump_json())["passages"]


def test_provider_exception_is_redacted(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")

    class Model:
        def invoke(self, _):
            raise RuntimeError("Bearer secret-credential-here")

    with pytest.raises(ResearchError) as exc:
        run_research("retry", documents=corpus(), llm=Model())
    assert "secret-credential" not in str(exc.value)
