"""Explicit provider selection; NVIDIA credentials never reach another provider."""

import os

from dotenv import load_dotenv

load_dotenv()
MODES = ("demo", "nvidia", "openai", "ollama")


def get_mode() -> str:
    requested = os.getenv("LLM_PROVIDER", "").strip().lower()
    if requested:
        if requested not in MODES:
            raise ValueError(f"LLM_PROVIDER must be one of {MODES}")
        return requested
    if os.getenv("NVIDIA_API_KEY", "").strip():
        return "nvidia"
    if os.getenv("OPENAI_API_KEY", "").strip() not in ("", "your_key_here", "sk-your-key-here"):
        return "openai"
    if os.getenv("OLLAMA_MODEL", "").strip():
        return "ollama"
    return "demo"


def is_demo_mode() -> bool:
    return get_mode() == "demo"


def model_name() -> str:
    return {
        "nvidia": os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"),
        "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "ollama": os.getenv("OLLAMA_MODEL", "llama3.2"),
        "demo": "extractive-demo",
    }[get_mode()]


def get_llm():
    mode = get_mode()
    if mode in ("nvidia", "openai"):
        from langchain_openai import ChatOpenAI
        from pydantic import SecretStr

        key = os.getenv("NVIDIA_API_KEY" if mode == "nvidia" else "OPENAI_API_KEY", "")
        if not key or key == "your_key_here":
            raise ValueError(f"Missing credential for {mode}; configure the local .env file.")
        base = (
            "https://integrate.api.nvidia.com/v1"
            if mode == "nvidia"
            else "https://api.openai.com/v1"
        )
        return ChatOpenAI(
            model=model_name(),
            api_key=SecretStr(key),
            base_url=base,
            temperature=0,
            max_tokens=2400,
            timeout=60,
            max_retries=1,
        )
    if mode == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model_name(),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
            num_predict=2400,
            client_kwargs={"timeout": 60},
        )
    raise RuntimeError("Demo mode uses source extracts, not an LLM.")


def mode_label() -> str:
    return f"{get_mode().title()} · {model_name()}"
