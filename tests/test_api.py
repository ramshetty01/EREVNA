from fastapi.testclient import TestClient

from research.api import app

client = TestClient(app)


def test_health_and_default_auth(monkeypatch):
    monkeypatch.delenv("EREVNA_API_TOKEN", raising=False)
    monkeypatch.delenv("EREVNA_API_LOCAL", raising=False)
    assert client.get("/health").json()["status"] == "ok"
    assert client.post("/research", json={"query": "test", "documents": []}).status_code == 503


def test_api_research_and_validation(monkeypatch):
    monkeypatch.setenv("EREVNA_API_TOKEN", "unit-test-token")
    headers = {"Authorization": "Bearer unit-test-token"}
    assert client.post("/research", json={"query": "test"}).status_code == 401
    result = client.post(
        "/research",
        headers=headers,
        json={
            "query": "Retries",
            "documents": [
                {
                    "url": "https://example.org/retry",
                    "title": "Retries",
                    "text": "Retries use exponential backoff and jitter.",
                }
            ],
        },
    )
    assert result.status_code == 200
    assert result.json()["metrics"]["accepted_findings"] == 1
    assert client.post("/research", headers=headers, json={"query": " "}).status_code == 400
    assert (
        client.post("/research", headers=headers, json={"query": "test", "k": 99}).status_code
        == 422
    )


def test_oversize_body_is_rejected():
    assert client.post("/research", content=b"x" * 400_001).status_code == 413


def test_api_enforces_operator_budget(monkeypatch):
    monkeypatch.setenv("EREVNA_API_LOCAL", "1")
    monkeypatch.delenv("EREVNA_API_TOKEN", raising=False)
    monkeypatch.setenv("EREVNA_MAX_LLM_CALLS", "2")
    assert (
        client.post(
            "/research", json={"query": "test", "documents": [], "max_llm_calls": 3}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/research", json={"query": "test", "documents": [], "max_llm_calls": True}
        ).status_code
        == 422
    )
    response = client.post("/research", json={"query": "test", "documents": []})
    assert response.json()["metrics"]["max_llm_calls"] == 2


def test_api_concurrency_rejects_overflow_and_recovers(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Event

    from research.pipeline import ResearchError

    monkeypatch.setenv("EREVNA_API_LOCAL", "1")
    monkeypatch.delenv("EREVNA_API_TOKEN", raising=False)
    entered = Barrier(3)
    release = Event()

    def blocked_run(*args, **kwargs):
        entered.wait(timeout=10)
        assert release.wait(timeout=10)
        raise ResearchError("Simulated failure")

    import research.api as api

    original = api.run_research
    monkeypatch.setattr(api, "run_research", blocked_run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(client.post, "/research", json={"query": "test", "documents": []})
            for _ in range(2)
        ]
        try:
            entered.wait(timeout=10)
            overflow = client.post("/research", json={"query": "test", "documents": []})
            assert overflow.status_code == 429
            assert overflow.headers["Retry-After"] == "5"
            assert client.get("/health").status_code == 200
        finally:
            release.set()
        assert [future.result().status_code for future in futures] == [502, 502]
    monkeypatch.setattr(api, "run_research", original)
    assert client.post("/research", json={"query": "test", "documents": []}).status_code == 200
