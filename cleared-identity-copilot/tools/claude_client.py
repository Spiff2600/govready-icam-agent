"""
claude_client.py
Anthropic Claude integration with tool use, streaming, and token telemetry.
Graceful fallback to cached example output when API key is missing.
"""
from __future__ import annotations

import copy
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from tools.claude_tools import TOOLS, execute_tool

try:
    from anthropic import Anthropic
except Exception:  # pragma: no cover - optional import safety
    Anthropic = None  # type: ignore[assignment]

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = Path(__file__).resolve().parent / "cached_example_output.json"
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
PRICING = {
    "claude-haiku-4-5": {"input_per_million": 0.80, "output_per_million": 4.00},
    "claude-sonnet-4-5": {"input_per_million": 3.00, "output_per_million": 15.00},
    "claude-opus-4-7": {"input_per_million": 15.00, "output_per_million": 75.00},
}
SYSTEM_PROMPT = """You are a federal identity security analyst AI assistant for Orion Federal Analytics Agency.
You have access to deterministic tools that query synthetic identity data.
ALL DATA IS SYNTHETIC AND FICTIONAL for demonstration purposes.

Rules:
1. Only use data from tool calls. Do not invent facts.
2. Separate evidence (tool call results) from inference (your analysis).
3. Cite which tool call produced each evidence item.
4. Flag assumptions explicitly with "ASSUMPTION:" prefix.
5. Mark every recommendation with required approval level: [APPROVAL: none | IT_lead | CISO]
6. Output structured JSON conforming to the documented schema.
7. Be specific about cross-cloud identity risks - Azure Gov and AWS GovCloud together.
8. When analyzing personas, weave the narrative context into your evidence.

Format your response as:
## Evidence Summary
[List each finding with tool call citation]

## Analysis
[Detailed reasoning]

## Assumptions
[Explicit list]

## Structured Output
```json
[JSON conforming to schema]
```
"""


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING.get(model, PRICING[DEFAULT_MODEL])
    return round((input_tokens / 1_000_000) * pricing["input_per_million"] + (output_tokens / 1_000_000) * pricing["output_per_million"], 6)


def _load_cached_output(model: str | None = None) -> dict[str, Any]:
    payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    payload = copy.deepcopy(payload)
    if model:
        payload["model"] = model
        if isinstance(payload.get("structured_output"), dict):
            payload["structured_output"]["model"] = model
    payload["from_cache"] = True
    return payload


def _content_block_to_dict(block: Any) -> dict[str, Any]:
    block_type = getattr(block, "type", None)
    if block_type == "text":
        return {"type": "text", "text": getattr(block, "text", "")}
    if block_type == "tool_use":
        return {
            "type": "tool_use",
            "id": getattr(block, "id", ""),
            "name": getattr(block, "name", ""),
            "input": getattr(block, "input", {}),
        }
    return {"type": block_type or "unknown", "text": getattr(block, "text", "")}


def _extract_text(response: Any) -> str:
    texts = [getattr(block, "text", "") for block in getattr(response, "content", []) if getattr(block, "type", "") == "text"]
    return "\n".join(texts).strip()


def _extract_structured_output(text: str, model: str) -> dict[str, Any]:
    match = re.search(r"## Structured Output\s*```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not match:
        match = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {
        "analysis_id": f"fallback-{uuid.uuid4().hex[:8]}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": model,
        "findings": [],
        "recommended_actions": [],
        "risk_summary": {"overall_posture": "MEDIUM", "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0},
    }


def _prepare_user_prompt(question: str, user_context: dict[str, Any] | None) -> str:
    context_blob = json.dumps(user_context or {}, indent=2)
    schema = {
        "analysis_id": "string",
        "timestamp": "ISO8601",
        "model": "string",
        "findings": [{
            "finding_id": "string",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "category": "string",
            "affected_users": ["user_id"],
            "evidence": ["string - tool call results"],
            "description": "string",
            "assumptions": ["string"],
            "nist_controls": ["string"]
        }],
        "recommended_actions": [{
            "action_id": "string",
            "priority": 1,
            "action_type": "string",
            "target_users": ["user_id"],
            "description": "string",
            "approval_required": "none|IT_lead|CISO",
            "estimated_effort": "string",
            "risk_reduction": "string"
        }],
        "risk_summary": {
            "overall_posture": "CRITICAL|HIGH|MEDIUM|LOW",
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0
        }
    }
    return (
        f"Question: {question}\n\n"
        f"User context (synthetic):\n{context_blob}\n\n"
        "Return JSON matching this schema in the Structured Output section:\n"
        f"{json.dumps(schema, indent=2)}"
    )


def analyze_identity_exposure(question: str, user_context: dict[str, Any] | None = None, model: str | None = None) -> dict[str, Any]:
    selected_model = model or DEFAULT_MODEL
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or Anthropic is None:
        return _load_cached_output(selected_model)

    try:
        client = Anthropic(api_key=api_key)
        messages: list[dict[str, Any]] = [{"role": "user", "content": _prepare_user_prompt(question, user_context)}]
        tool_calls: list[dict[str, Any]] = []
        total_input = 0
        total_output = 0
        final_text = ""

        for _ in range(6):
            response = client.messages.create(
                model=selected_model,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
                max_tokens=2200,
                temperature=0,
            )
            usage = getattr(response, "usage", None)
            total_input += int(getattr(usage, "input_tokens", 0) or 0)
            total_output += int(getattr(usage, "output_tokens", 0) or 0)
            blocks = getattr(response, "content", [])
            if any(getattr(block, "type", "") == "tool_use" for block in blocks):
                assistant_content = [_content_block_to_dict(block) for block in blocks]
                messages.append({"role": "assistant", "content": assistant_content})
                tool_results: list[dict[str, Any]] = []
                for block in blocks:
                    if getattr(block, "type", "") != "tool_use":
                        continue
                    start = time.perf_counter()
                    result = execute_tool(block.name, block.input)
                    duration_ms = int((time.perf_counter() - start) * 1000)
                    tool_calls.append({"tool": block.name, "args": block.input, "result": result, "duration_ms": duration_ms})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, indent=2),
                    })
                messages.append({"role": "user", "content": tool_results})
                continue
            final_text = _extract_text(response)
            break

        structured_output = _extract_structured_output(final_text, selected_model)
        return {
            "tool_calls": tool_calls,
            "analysis": final_text,
            "structured_output": structured_output,
            "token_usage": {
                "input": total_input,
                "output": total_output,
                "cost_usd": _estimate_cost(selected_model, total_input, total_output),
            },
            "model": selected_model,
            "from_cache": False,
        }
    except Exception as exc:  # pragma: no cover - external API path
        payload = _load_cached_output(selected_model)
        payload["analysis"] = f"No live Claude response available because the API call failed: {exc}.\n\n" + payload["analysis"]
        payload["from_cache"] = True
        return payload


def run_single_eval(prompt: str, model: str) -> dict[str, Any]:
    started = time.perf_counter()
    result = analyze_identity_exposure(prompt, user_context={"mode": "eval"}, model=model)
    latency_ms = int((time.perf_counter() - started) * 1000)
    text = result.get("analysis", "")
    return {
        "prompt": prompt,
        "analysis": text,
        "structured_output": result.get("structured_output", {}),
        "tool_calls": result.get("tool_calls", []),
        "token_usage": result.get("token_usage", {}),
        "model": result.get("model", model),
        "from_cache": result.get("from_cache", False),
        "latency_ms": latency_ms,
    }
