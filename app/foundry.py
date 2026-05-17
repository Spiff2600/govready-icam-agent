import os
from typing import Any, Dict

import httpx

DEFAULT_MAX_TOKENS = 512
DEFAULT_TIMEOUT_SECONDS = 30.0


def _extract_text(payload: Dict[str, Any]) -> str:
    content = payload.get("content", [])
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
        return "".join(parts).strip()
    return ""


def chat_completion(message: str, system: str | None = None) -> Dict[str, Any]:
    endpoint = os.getenv("ANTHROPIC_FOUNDRY_ENDPOINT")
    if not endpoint:
        raise RuntimeError("ANTHROPIC_FOUNDRY_ENDPOINT is not configured")

    api_key = os.getenv("ANTHROPIC_FOUNDRY_API_KEY")
    model = os.getenv("ANTHROPIC_FOUNDRY_MODEL", "claude-sonnet-4-5")
    max_tokens = int(os.getenv("ANTHROPIC_FOUNDRY_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
    timeout_seconds = float(os.getenv("ANTHROPIC_FOUNDRY_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["api-key"] = api_key

    body: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": message}],
    }
    if system:
        body["system"] = system

    try:
        response = httpx.post(endpoint, headers=headers, json=body, timeout=timeout_seconds)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Foundry request failed: status={exc.response.status_code} body={exc.response.text}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Foundry request failed: {exc}") from exc
    payload = response.json()
    return {
        "model": payload.get("model", model),
        "message": _extract_text(payload),
    }
