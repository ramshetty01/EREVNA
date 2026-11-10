from pydantic import BaseModel, Field


class ResearchPlan(BaseModel):
    """Structured research plan with Pydantic validation."""

    objective: str = Field(description="Clear research objective")
    steps: list[str] = Field(description="Ordered research steps")
    expected_sources: list[str] = Field(description="Types of sources to target")
    key_questions: list[str] = Field(description="Key questions to answer")


def format_plan(plan: ResearchPlan) -> str:
    """Render a ResearchPlan as markdown for the UI."""
    out = f"## 🎯 Objective\n{plan.objective}\n\n## 📋 Steps\n"
    for i, step in enumerate(plan.steps, 1):
        out += f"{i}. {step}\n"
    out += "\n## 🔍 Expected Sources\n"
    for source in plan.expected_sources:
        out += f"- {source}\n"
    out += "\n## ❓ Key Questions\n"
    for q in plan.key_questions:
        out += f"- {q}\n"
    return out
