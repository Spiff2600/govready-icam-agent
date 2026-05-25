"""
eval_runner.py
Runs the eval prompt suite against multiple Claude models.
Reports pass rate, latency, cost per model.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.claude_client import run_single_eval

BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_PROMPTS_PATH = BASE_DIR / "evals" / "prompts.jsonl"
RESULTS_CACHE_PATH = BASE_DIR / "evals" / "results_cache.json"
DEFAULT_MODELS = ["claude-haiku-4-5", "claude-sonnet-4-5", "claude-opus-4-7"]


def load_eval_prompts(path: str = "evals/prompts.jsonl") -> list[dict[str, Any]]:
    file_path = BASE_DIR / path if not Path(path).is_absolute() else Path(path)
    prompts: list[dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            prompts.append(json.loads(line))
    return prompts


def check_pass_criteria(response: str, criteria: dict[str, Any]) -> bool:
    response_lower = response.lower()
    criteria_type = criteria.get("type")
    values = criteria.get("values", [])
    if criteria_type == "contains_all":
        return all(value.lower() in response_lower for value in values)
    if criteria_type == "contains_any":
        return any(value.lower() in response_lower for value in values)
    if criteria_type == "regex":
        pattern = criteria.get("pattern", "")
        return bool(re.search(pattern, response, flags=re.IGNORECASE | re.DOTALL))
    if criteria_type == "function":
        function_name = criteria.get("name")
        if function_name == "mentions_user_ids":
            return any(token.startswith(("USR", "SVC", "CTR")) for token in response.split())
        return False
    return False


def evaluate_single(prompt_obj: dict[str, Any], model: str) -> dict[str, Any]:
    eval_result = run_single_eval(prompt_obj["prompt"], model)
    response_text = eval_result.get("analysis", "")
    passed = check_pass_criteria(response_text, prompt_obj.get("pass_criteria", {}))
    return {
        "id": prompt_obj["id"],
        "prompt": prompt_obj["prompt"],
        "model": model,
        "difficulty": prompt_obj.get("difficulty"),
        "mission_relevance": prompt_obj.get("mission_relevance"),
        "category": prompt_obj.get("category"),
        "passed": passed,
        "latency_ms": eval_result.get("latency_ms", 0),
        "cost_usd": eval_result.get("token_usage", {}).get("cost_usd", 0.0),
        "from_cache": eval_result.get("from_cache", False),
        "response": response_text,
        "tool_calls": eval_result.get("tool_calls", []),
    }


def run_full_eval_suite(models: list[str] | None = None) -> dict[str, Any]:
    selected_models = models or DEFAULT_MODELS
    prompts = load_eval_prompts()
    all_results: list[dict[str, Any]] = []
    model_summary: list[dict[str, Any]] = []
    for model in selected_models:
        model_results = [evaluate_single(prompt, model) for prompt in prompts]
        all_results.extend(model_results)
        passes = sum(1 for result in model_results if result["passed"])
        avg_latency = round(sum(result["latency_ms"] for result in model_results) / len(model_results), 1) if model_results else 0.0
        total_cost = round(sum(result["cost_usd"] for result in model_results), 4)
        model_summary.append({
            "model": model,
            "pass_rate": round((passes / len(model_results)) * 100, 1) if model_results else 0.0,
            "avg_latency_ms": avg_latency,
            "total_cost_usd": total_cost,
            "cached": all(result["from_cache"] for result in model_results) if model_results else True,
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": selected_models,
        "summary": model_summary,
        "results": all_results,
    }
    RESULTS_CACHE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
