import httpx
import pytest

from app.foundry import chat_completion


def test_chat_completion_wraps_http_status_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_ENDPOINT", "https://example.test/messages")

    def fake_post(*args, **kwargs):
        request = httpx.Request("POST", "https://example.test/messages")
        response = httpx.Response(401, request=request, text="unauthorized")
        raise httpx.HTTPStatusError("status error", request=request, response=response)

    monkeypatch.setattr("app.foundry.httpx.post", fake_post)

    with pytest.raises(RuntimeError, match="status=401"):
        chat_completion("hello")
