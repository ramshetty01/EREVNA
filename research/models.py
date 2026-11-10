"""Typed, exportable contracts shared by UI, API and evaluation."""

from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator

from agents.plan_schema import ResearchPlan


class Document(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(max_length=2048)
    text: str = Field(min_length=1, max_length=100_000)
    fetched_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: Literal["page", "snippet", "provided"] = "provided"

    @field_validator("url")
    @classmethod
    def public_link(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
            raise ValueError("Source URL must be an HTTP(S) URL without credentials")
        return value


class Passage(BaseModel):
    id: str
    source_id: str
    title: str
    url: str
    text: str
    score: float = 0


class Evidence(BaseModel):
    passage_id: str
    quote: str = Field(min_length=15, max_length=1500)


class Finding(BaseModel):
    claim: str = Field(min_length=1, max_length=2000)
    evidence: list[Evidence] = Field(min_length=1, max_length=4)


class GroundedAnswer(BaseModel):
    findings: list[Finding] = Field(default_factory=list, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=10)
    insufficient_evidence: bool = False


class RunMetrics(BaseModel):
    provider: str
    model: str
    step_seconds: dict[str, float] = Field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    usage_complete: bool = True
    llm_calls: int = 0
    estimated_cost_usd: float | None = None
    source_count: int = 0
    passage_count: int = 0
    candidate_findings: int = 0
    accepted_findings: int = 0
    rejected_findings: int = 0
    citation_references_valid: bool = True
    support_assessment: str = (
        "Exact quote matching only; claim entailment is not independently verified."
    )


class ResearchResult(BaseModel):
    run_id: str
    created_at: str
    query: str
    plan: ResearchPlan
    documents: list[Document]
    passages: list[Passage]
    answer: GroundedAnswer
    report: str
    metrics: RunMetrics
    warnings: list[str] = Field(default_factory=list)
