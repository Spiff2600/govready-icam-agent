import httpx
import pytest

from app.foundry import chat_completion


def test_chat_completion_uses_configurable_tokens_and_timeout(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_ENDPOINT", "https://example.test/messages")
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_MAX_TOKENS", "42")
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_TIMEOUT_SECONDS", "9.5")

    def fake_post(url, headers, json, timeout):
        assert timeout == 9.5
        assert json["max_tokens"] == 42
        request = httpx.Request("POST", url)
        return httpx.Response(200, request=request, json={"model": "claude-sonnet-4-5", "content": [{"type": "text", "text": "ok"}]})

    monkeypatch.setattr("app.foundry.httpx.post", fake_post)

    result = chat_completion("hello")

    assert result == {"model": "claude-sonnet-4-5", "message": "ok"}


def test_chat_completion_wraps_http_status_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_ENDPOINT", "https://example.test/messages")

    def fake_post(*args, **kwargs):
        request = httpx.Request("POST", "https://example.test/messages")
        response = httpx.Response(401, request=request, text="unauthorized")
        raise httpx.HTTPStatusError("status error", request=request, response=response)

    monkeypatch.setattr("app.foundry.httpx.post", fake_post)

    with pytest.raises(RuntimeError, match="status=401"):
        chat_completion("hello")
