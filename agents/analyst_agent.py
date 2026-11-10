import json

from langchain_core.prompts import ChatPromptTemplate

from agents.demo_agents import demo_analyst
from agents.llm_backend import get_llm, get_mode
from agents.plan_schema import ResearchPlan, format_plan

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert AI Research Analyst.
Analyze the research data and return a structured markdown report with:
## Summary
## Key Trends
## Critical Insights
## Data Gaps & Limitations
## Conclusion
Be precise, cite specific data points, avoid generic statements.
Use the research plan to stay focused on the objective and key questions.""",
        ),
        ("human", "Research plan:\n{plan}\n\nCollected data:\n\n{data}"),
    ]
)


def analyst_agent(
    data: dict | str,
    plan: ResearchPlan | None = None,
    task: str = "",
) -> str:
    """Analyze research data using plan context and a structured LangChain chain."""
    raw = (
        data.get("raw_content", json.dumps(data, indent=2)) if isinstance(data, dict) else str(data)
    )
    source_count = len(data.get("web_results", [])) if isinstance(data, dict) else 0
    query = task or (data.get("query", "") if isinstance(data, dict) else "")

    if get_mode() == "demo":
        return demo_analyst(query, plan, raw[:8000], source_count)

    plan_text = format_plan(plan) if plan else "No structured plan provided."
    chain = PROMPT | get_llm()
    return chain.invoke({"plan": plan_text, "data": raw[:8000]}).content
