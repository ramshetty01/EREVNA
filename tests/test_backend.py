import pytest

from agents.llm_backend import get_llm, get_mode


def test_nvidia_uses_own_host_and_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nvidia-credential")
    monkeypatch.setenv("OPENAI_API_KEY", "test-unrelated-credential")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://untrusted.example/v1")
    llm = get_llm()
    assert get_mode() == "nvidia"
    assert llm.max_retries == 0
    assert llm.openai_api_base == "https://integrate.api.nvidia.com/v1"
    assert llm.openai_api_key.get_secret_value() == "test-nvidia-credential"


def test_explicit_provider_never_silently_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    with pytest.raises(ValueError, match="Missing credential"):
        get_llm()


def test_unknown_provider_fails(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "typo")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        get_mode()
