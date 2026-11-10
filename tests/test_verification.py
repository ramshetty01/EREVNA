import json
from types import SimpleNamespace

import pytest

from research.models import Evidence, Finding, GroundedAnswer, Passage, RunMetrics
from research.pipeline import run_research
from research.verification import verify_answer

TEXT = "The service encrypts data in transit. No security audit has been completed."


def fixture(claim="The service is fully secure."):
    passage = Passage(
        id="S1-P1", source_id="S1", title="Security", url="https://example.org/security", text=TEXT
    )
    finding = Finding(claim=claim, evidence=[Evidence(passage_id=passage.id, quote=TEXT)])
    return (
        GroundedAnswer(findings=[finding]),
        [passage],
        RunMetrics(provider="nvidia", model="test"),
    )


def decision(verdict, *, narrowed=None, finding_id=0, evidence_ids=None):
    return {
        "finding_id": finding_id,
        "verdict": verdict,
        "reason": "Evidence establishes encryption only.",
        "evidence_ids": ["S1-P1"] if evidence_ids is None else evidence_ids,
        "narrowed_claim": narrowed,
    }


class Model:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.prompts = []

    def invoke(self, messages):
        self.prompts.append(messages)
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return SimpleNamespace(
            content=json.dumps(value), usage_metadata={"input_tokens": 20, "output_tokens": 10}
        )


@pytest.mark.parametrize("verdict", ["insufficient", "contradicted"])
def test_real_quote_does_not_allow_unsupported_claim(verdict):
    answer, passages, metrics = fixture()
    model = Model({"decisions": [decision(verdict)]})
    final, review = verify_answer(answer, passages, model, metrics)
    assert final.insufficient_evidence and not final.findings
    assert review.claims[0].disposition == "excluded"
    assert review.claims[0].original.claim == answer.findings[0].claim
    assert "generator" not in json.loads(model.prompts[0][1][1])


def test_supported_claim_retained_and_usage_counted():
    answer, passages, metrics = fixture("The service encrypts data in transit.")
    final, review = verify_answer(
        answer, passages, Model({"decisions": [decision("supported")]}), metrics
    )
    assert final.findings == answer.findings
    assert review.status == "completed"
    assert metrics.input_tokens == 20


def test_partial_claim_requires_fresh_recheck():
    answer, passages, metrics = fixture("The service encrypts data and passed a security audit.")
    narrow = "The service encrypts data in transit."
    model = Model(
        {"decisions": [decision("partially_supported", narrowed=narrow)]},
        {"decisions": [decision("supported")]},
    )
    final, review = verify_answer(answer, passages, model, metrics)
    assert final.findings[0].claim == narrow
    assert review.claims[0].disposition == "narrowed"
    assert review.claims[0].recheck.verdict == "supported"
    # The rechecker sees the new claim and sources, not prior verdicts/reasons.
    payload = json.loads(model.prompts[1][1][1])
    assert payload["findings"][0]["claim"] == narrow
    assert "partially_supported" not in model.prompts[1][1][1]
    assert len(model.prompts) == 2


def test_partial_recheck_cannot_start_another_narrowing_loop():
    answer, passages, metrics = fixture()
    response = {
        "decisions": [decision("partially_supported", narrowed="The service encrypts data.")]
    }
    model = Model(response, response)
    final, review = verify_answer(answer, passages, model, metrics)
    assert final.insufficient_evidence
    assert len(model.prompts) == 2
    assert review.claims[0].disposition == "excluded"


@pytest.mark.parametrize(
    "decisions",
    [
        [],
        [decision("supported"), decision("supported")],
        [decision("supported", finding_id=1)],
        [decision("supported", evidence_ids=["S99"])],
        [decision("supported", evidence_ids=[])],
        [decision("supported", narrowed="Changed claim")],
    ],
)
def test_invalid_verdict_contract_fails_closed(decisions):
    answer, passages, metrics = fixture()
    final, review = verify_answer(answer, passages, Model({"decisions": decisions}), metrics)
    assert review.status == "failed"
    assert final.insufficient_evidence


def test_support_failure_does_not_leak_provider_details():
    answer, passages, metrics = fixture()
    final, review = verify_answer(
        answer, passages, Model(RuntimeError("Bearer secret-private")), metrics
    )
    assert review.status == "failed"
    assert "secret-private" not in final.model_dump_json() + review.model_dump_json()
    assert metrics.usage_complete is False
    assert metrics.llm_calls == 1


def test_failed_recheck_preserves_other_supported_findings():
    answer, passages, metrics = fixture("The service encrypts data in transit.")
    answer.findings.append(
        Finding(
            claim="It encrypts data and meets every compliance standard.",
            evidence=answer.findings[0].evidence,
        )
    )
    model = Model(
        {
            "decisions": [
                decision("supported"),
                decision("partially_supported", finding_id=1, narrowed="It encrypts data."),
            ]
        },
        RuntimeError("unavailable"),
    )
    final, review = verify_answer(answer, passages, model, metrics)
    assert len(final.findings) == 1
    assert review.status == "partial_failure"
    assert review.claims[1].error


def test_pipeline_verifies_by_default(monkeypatch):
    from research.models import Document

    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    answer, _, _ = fixture()
    model = Model(answer.model_dump(), {"decisions": [decision("insufficient")]})
    result = run_research(
        "service security",
        documents=[Document(title="Security", url="https://example.org/security", text=TEXT)],
        llm=model,
    )
    assert result.metrics.quote_valid_findings == 1
    assert result.metrics.accepted_findings == 0
    assert result.metrics.support_excluded_findings == 1
    assert result.metrics.support_llm_calls == 1
    assert result.support_review.status == "completed"
    assert "insufficient / excluded" in result.report


def test_legacy_result_has_safe_default_review():
    from research.models import SupportReview

    assert SupportReview().status == "disabled"
