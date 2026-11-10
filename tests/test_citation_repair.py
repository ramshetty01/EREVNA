import json
from types import SimpleNamespace

from research.models import Document
from research.pipeline import run_research


def test_one_repair_recovers_exact_evidence(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")

    class Model:
        calls = 0

        def invoke(self, _):
            self.calls += 1
            quote = (
                "An invented and unsupported sentence."
                if self.calls == 1
                else "Cache entries expire after 24 hours."
            )
            return SimpleNamespace(
                content=json.dumps(
                    {
                        "findings": [
                            {
                                "claim": "The cache expires after 24 hours.",
                                "evidence": [{"passage_id": "S1-P1", "quote": quote}],
                            }
                        ]
                    }
                ),
                usage_metadata={"input_tokens": 10, "output_tokens": 5},
            )

    model = Model()
    result = run_research(
        "cache expiry",
        documents=[
            Document(
                title="Cache",
                url="https://example.org/cache",
                text="Cache entries expire after 24 hours.",
            )
        ],
        llm=model,
        verify_support=False,
    )
    assert model.calls == 2
    assert result.metrics.initial_rejected_findings == 1
    assert result.metrics.rejected_findings == 0
    assert result.metrics.citation_repair_attempts == 1
    assert len(result.answer.findings) == 1
    assert result.metrics.input_tokens == 20


def test_invalid_repair_still_abstains(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")

    class Model:
        calls = 0

        def invoke(self, _):
            self.calls += 1
            return SimpleNamespace(
                content=json.dumps(
                    {
                        "findings": [
                            {
                                "claim": "Wrong.",
                                "evidence": [
                                    {"passage_id": "S99", "quote": "Entirely fabricated quotation."}
                                ],
                            }
                        ]
                    }
                ),
                usage_metadata={},
            )

    model = Model()
    result = run_research(
        "cache expiry",
        documents=[
            Document(
                title="Cache",
                url="https://example.org/cache",
                text="Cache entries expire after 24 hours.",
            )
        ],
        llm=model,
        verify_support=False,
    )
    assert model.calls == 2
    assert result.answer.insufficient_evidence
    assert result.metrics.accepted_findings == 0
