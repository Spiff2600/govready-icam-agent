from fastapi.testclient import TestClient

from app.main import app


def test_chat_endpoint_returns_foundry_response(monkeypatch):
    def fake_chat_completion(message: str, system: str | None = None):
        assert message == "hello"
        assert system == "you are helpful"
        return {"model": "claude-sonnet-4-5", "message": "hi"}

    monkeypatch.setattr("app.main.chat_completion", fake_chat_completion)
    client = TestClient(app)

    response = client.post("/chat", json={"message": "hello", "system": "you are helpful"})

    assert response.status_code == 200
    assert response.json() == {"model": "claude-sonnet-4-5", "message": "hi"}


def test_chat_endpoint_returns_error_when_not_configured(monkeypatch):
    def fake_chat_completion(message: str, system: str | None = None):
        raise RuntimeError("ANTHROPIC_FOUNDRY_ENDPOINT is not configured")

    monkeypatch.setattr("app.main.chat_completion", fake_chat_completion)
    client = TestClient(app)

    response = client.post("/chat", json={"message": "hello"})

    assert response.status_code == 500
    assert response.json()["detail"] == "ANTHROPIC_FOUNDRY_ENDPOINT is not configured"
