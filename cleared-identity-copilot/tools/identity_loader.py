"""
identity_loader.py
Loads and normalizes synthetic identity data from sample_data/.
Returns typed Python objects. No external dependencies except stdlib + pathlib.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "sample_data"
LOGGER = logging.getLogger(__name__)


def _load_json(filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
            LOGGER.warning("Sample data file %s did not contain a JSON object; using empty fallback.", path)
            return {}
    except FileNotFoundError:
        LOGGER.warning("Sample data file not found: %s", path)
        return {}
    except json.JSONDecodeError:
        LOGGER.warning("Sample data file is not valid JSON: %s", path)
        return {}
    except OSError as exc:
        LOGGER.warning("Unable to read sample data file %s: %s", path, exc)
        return {}


@lru_cache(maxsize=1)
def _azure_users() -> list[dict[str, Any]]:
    return _load_json("azure_users_roles.json").get("users", [])


@lru_cache(maxsize=1)
def _aws_users() -> list[dict[str, Any]]:
    return _load_json("aws_identity_center_permission_sets.json").get("users", [])


@lru_cache(maxsize=1)
def _access_reviews() -> dict[str, dict[str, Any]]:
    review_map: dict[str, dict[str, Any]] = {}
    for review in _load_json("privileged_access_reviews.json").get("reviews", []):
        review_map[review["user_id"]] = review
    return review_map


@lru_cache(maxsize=1)
def _personas_text() -> str:
    try:
        return (DATA_DIR / "personas.md").read_text(encoding="utf-8")
    except OSError as exc:
        LOGGER.warning("Unable to read personas file %s: %s", DATA_DIR / "personas.md", exc)
        return ""


@lru_cache(maxsize=1)
def load_all_users() -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for user in _azure_users():
        merged[user["user_id"]] = {
            **user,
            "clouds": ["azure"],
            "aws_permission_sets": [],
            "risk_indicators": list(user.get("risk_indicators", [])),
        }
    for user in _aws_users():
        existing = merged.setdefault(
            user["user_id"],
            {
                "user_id": user["user_id"],
                "name": user.get("name", user["user_id"]),
                "clouds": [],
                "azure_roles": [],
                "mfa_methods": [],
                "risk_indicators": [],
            },
        )
        existing.setdefault("clouds", [])
        if "aws" not in existing["clouds"]:
            existing["clouds"].append("aws")
        existing["aws_permission_sets"] = user.get("permission_sets", [])
        existing["aws_accounts"] = user.get("aws_accounts", [])
        existing["aws_last_console_login"] = user.get("last_console_login")
        existing["risk_indicators"] = sorted(set(existing.get("risk_indicators", []) + user.get("risk_indicators", [])))
    for user_id, review in _access_reviews().items():
        if user_id in merged:
            merged[user_id]["access_review"] = review
    for user in merged.values():
        persona = _extract_persona(user["user_id"])
        if persona:
            user["persona"] = persona
        user["clouds"] = sorted(set(user.get("clouds", []) + (["azure"] if user.get("azure_roles") else []) + (["aws"] if user.get("aws_permission_sets") else [])))
    return sorted(merged.values(), key=lambda item: item["user_id"])


def _extract_persona(user_id: str) -> str | None:
    marker = f"## {user_id} - "
    text = _personas_text()
    if marker not in text:
        return None
    segment = text.split(marker, 1)[1]
    lines = segment.splitlines()
    body_lines: list[str] = []
    for line in lines[1:]:
        if line.startswith("## "):
            break
        body_lines.append(line)
    return "\n".join(line for line in body_lines if line.strip()).strip() or None


def get_user(user_id: str) -> dict[str, Any] | None:
    return next((user for user in load_all_users() if user["user_id"] == user_id), None)


def get_users_with_role(role_name: str, cloud: str) -> list[dict[str, Any]]:
    role_name_lower = role_name.lower()
    cloud = cloud.lower()
    matches: list[dict[str, Any]] = []
    for user in load_all_users():
        azure_match = any(role_name_lower in role.get("role_name", "").lower() for role in user.get("azure_roles", []))
        aws_match = any(role_name_lower in role.get("permission_set", "").lower() for role in user.get("aws_permission_sets", []))
        if cloud == "azure" and azure_match:
            matches.append(user)
        elif cloud == "aws" and aws_match:
            matches.append(user)
        elif cloud == "both" and (azure_match or aws_match):
            matches.append(user)
    return matches


_CROSS_CLOUD_AZURE_ADMIN_ROLES = {"global administrator", "privileged role administrator"}
_CROSS_CLOUD_AWS_ADMIN_PERMISSION_SETS = {"administratoraccess"}


def get_cross_cloud_admins() -> list[dict[str, Any]]:
    admins: list[dict[str, Any]] = []
    for user in load_all_users():
        azure_admin = any(role.get("role_name", "").lower() in _CROSS_CLOUD_AZURE_ADMIN_ROLES for role in user.get("azure_roles", []))
        aws_admin = any(role.get("permission_set", "").lower() in _CROSS_CLOUD_AWS_ADMIN_PERMISSION_SETS for role in user.get("aws_permission_sets", []))
        if azure_admin and aws_admin:
            admins.append(user)
    return admins


def get_users_with_weak_mfa() -> list[dict[str, Any]]:
    weak = {"sms", "email_otp", "none"}
    return [user for user in load_all_users() if user.get("primary_mfa_method") in weak]


def get_service_accounts() -> list[dict[str, Any]]:
    return [user for user in load_all_users() if user.get("account_type") == "service"]


def get_contractor_accounts() -> list[dict[str, Any]]:
    return [user for user in load_all_users() if user.get("employment_type") == "contractor"]
