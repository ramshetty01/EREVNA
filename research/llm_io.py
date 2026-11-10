"""Bounded structured calls and safe errors shared by generation and verification."""

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser

from research.models import RunMetrics


class ResearchError(Exception):
    """Safe user-facing failure without provider payloads or credentials."""


class BudgetExceeded(ResearchError):
    """No additional model call is allowed for this run."""


def invoke(llm, messages: list, metrics: RunMetrics) -> str:
    if metrics.llm_calls >= metrics.max_llm_calls:
        metrics.call_budget_exhausted = True
        raise BudgetExceeded(
            "Model-call budget exhausted. Increase the run limit or simplify the request."
        )
    metrics.llm_calls += 1
    try:
        response = llm.invoke(messages)
    except Exception:
        metrics.usage_complete = False
        raise
    usage = getattr(response, "usage_metadata", None)
    if usage:
        metrics.input_tokens += int(usage.get("input_tokens", 0))
        metrics.output_tokens += int(usage.get("output_tokens", 0))
    else:
        metrics.usage_complete = False
    if not isinstance(response.content, str):
        raise ResearchError("The model returned an unsupported response format.")
    return response.content


def structured(llm, messages: list, schema, metrics: RunMetrics):
    parser = PydanticOutputParser(pydantic_object=schema)
    prompt = messages + [("human", parser.get_format_instructions())]
    for attempt in range(2):
        text = invoke(llm, prompt, metrics)
        try:
            return parser.parse(text)
        except OutputParserException:
            if attempt:
                raise ResearchError(
                    "The model returned invalid structured output twice. Please retry."
                ) from None
            # Do not include raw errors or failed output (could contain source instructions).
            prompt = messages + [
                (
                    "human",
                    "Your prior output was invalid. Return JSON only. "
                    + parser.get_format_instructions(),
                )
            ]
