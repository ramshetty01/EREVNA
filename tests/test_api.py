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
