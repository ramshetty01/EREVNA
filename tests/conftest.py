"""Unit tests never use a developer's local credentials or external models."""

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(autouse=True)
def isolated_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "demo")
    for key in (
        "OPENAI_API_KEY",
        "NVIDIA_API_KEY",
        "OLLAMA_MODEL",
        "INPUT_USD_PER_MILLION",
        "OUTPUT_USD_PER_MILLION",
    ):
        monkeypatch.delenv(key, raising=False)
