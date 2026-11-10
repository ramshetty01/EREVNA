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


class SupportDecision(BaseModel):
    """A model judgment, not a guarantee of truth."""

    model_config = {"extra": "forbid"}
    finding_id: int = Field(ge=0, le=7)
    verdict: Literal["supported", "partially_supported", "contradicted", "insufficient"]
    reason: str = Field(min_length=1, max_length=1500)
    evidence_ids: list[str] = Field(max_length=12)
    narrowed_claim: str | None = Field(default=None, max_length=2000)


class SupportBatch(BaseModel):
    model_config = {"extra": "forbid"}
    decisions: list[SupportDecision] = Field(max_length=8)


class ClaimReview(BaseModel):
    finding_id: int
    original: Finding
    decision: SupportDecision | None = None
    recheck: SupportDecision | None = None
    disposition: Literal["retained", "narrowed", "excluded"] = "excluded"
    final_claim: str | None = None
    error: str | None = None


class SupportReview(BaseModel):
    status: Literal["completed", "failed", "partial_failure", "disabled", "demo", "no_findings"] = (
        "disabled"
    )
    prompt_version: str = "claim-support-v1"
    provider: str = ""
    model: str = ""
    claims: list[ClaimReview] = Field(default_factory=list)
    note: str = "Model judgments can be wrong; human review is still required."


class RunMetrics(BaseModel):
    provider: str
    model: str
    step_seconds: dict[str, float] = Field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    usage_complete: bool = True
    llm_calls: int = 0
    max_llm_calls: int = Field(default=10, ge=1, le=10)
    call_budget_exhausted: bool = False
    estimated_cost_usd: float | None = None
    source_count: int = 0
    passage_count: int = 0
    candidate_findings: int = 0
    accepted_findings: int = 0
    rejected_findings: int = 0
    initial_rejected_findings: int = 0
    citation_repair_attempts: int = 0
    citation_references_valid: bool = True
    support_assessment: str = (
        "Exact quote matching only; claim entailment is not independently verified."
    )
    quote_valid_findings: int = 0
    support_verification_requested: bool = False
    support_review_status: str = "disabled"
    support_excluded_findings: int = 0
    support_narrowed_findings: int = 0
    support_llm_calls: int = 0


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
    support_review: SupportReview = Field(default_factory=SupportReview)
