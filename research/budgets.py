"""Per-run application-call limits, also capped by the operator's configuration."""

import os

DEFAULT_MAX_LLM_CALLS = 10


def resolve_call_limit(requested: int | None = None) -> int:
    raw = os.getenv("EREVNA_MAX_LLM_CALLS", str(DEFAULT_MAX_LLM_CALLS))
    try:
        ceiling = int(raw)
    except ValueError:
        raise ValueError("EREVNA_MAX_LLM_CALLS must be an integer from 1 to 10.") from None
    if not 1 <= ceiling <= DEFAULT_MAX_LLM_CALLS:
        raise ValueError("EREVNA_MAX_LLM_CALLS must be an integer from 1 to 10.")
    if requested is not None and (type(requested) is not int or not 1 <= requested <= ceiling):
        raise ValueError(f"max_llm_calls must be an integer from 1 to {ceiling}.")
    return ceiling if requested is None else requested
