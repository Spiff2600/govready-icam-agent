from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.identity_loader import (
    get_contractor_accounts,
    get_cross_cloud_admins,
    get_service_accounts,
    get_user,
    get_users_with_role as loader_get_users_with_role,
    get_users_with_weak_mfa,
)
from tools.risk_scoring import score_user

TOOLS = [
    {
        "name": "get_user_risk_score",
        "description": "Get the deterministic risk score for a specific user. Returns score breakdown, risk level (LOW/MED/HIGH/CRITICAL), and contributing factors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID (e.g., USR001, SVC001, CTR001)"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_users_with_role",
        "description": "Get all users with a specific role assignment in Azure or AWS.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role_name": {"type": "string"},
                "cloud": {"type": "string", "enum": ["azure", "aws", "both"]}
            },
            "required": ["role_name", "cloud"]
        }
    },
    {
        "name": "get_cross_cloud_admins",
        "description": "Get all users with administrative access in BOTH Azure Gov and AWS GovCloud - highest risk category.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_users_with_weak_mfa",
        "description": "Get all users with weak or missing MFA (SMS, email OTP, or no MFA).",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_persona",
        "description": "Get the detailed persona narrative for a user, including background, role history, and risk context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "propose_remediation",
        "description": "Generate a vendor-neutral remediation proposal for a specific user and action type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "action_type": {
                    "type": "string",
                    "enum": ["enable_pim", "upgrade_mfa", "revoke_role", "deprovision_account", "assign_owner", "conduct_access_review"]
                }
            },
            "required": ["user_id", "action_type"]
        }
    }
]

_PERSONAS_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "personas.md"


def _serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": user["user_id"],
        "name": user.get("name"),
        "account_type": user.get("account_type"),
        "primary_mfa_method": user.get("primary_mfa_method"),
        "azure_roles": [role.get("role_name") for role in user.get("azure_roles", [])],
        "aws_permission_sets": [role.get("permission_set") for role in user.get("aws_permission_sets", [])],
        "risk_indicators": user.get("risk_indicators", []),
    }


def handle_get_user_risk_score(user_id: str) -> dict[str, Any]:
    user = get_user(user_id)
    if not user:
        return {"error": f"User {user_id} not found"}
    return {**score_user(user), "user": _serialize_user(user)}


def handle_get_users_with_role(role_name: str, cloud: str) -> dict[str, Any]:
    matches = loader_get_users_with_role(role_name, cloud)
    return {"count": len(matches), "users": [_serialize_user(user) for user in matches]}


def handle_get_cross_cloud_admins() -> dict[str, Any]:
    admins = get_cross_cloud_admins()
    return {"count": len(admins), "users": [_serialize_user(user) for user in admins]}


def handle_get_users_with_weak_mfa() -> dict[str, Any]:
    weak = get_users_with_weak_mfa()
    return {"count": len(weak), "users": [_serialize_user(user) for user in weak]}


def handle_get_persona(user_id: str) -> dict[str, Any]:
    user = get_user(user_id)
    if not user:
        return {"error": f"User {user_id} not found"}
    return {"user_id": user_id, "name": user.get("name"), "persona": user.get("persona") or "No persona found."}


def handle_propose_remediation(user_id: str, action_type: str) -> dict[str, Any]:
    user = get_user(user_id)
    if not user:
        return {"error": f"User {user_id} not found"}
    score = score_user(user)
    approval = "CISO" if score["risk_level"] == "CRITICAL" else "IT_lead"
    catalog = {
        "enable_pim": {
            "description": "Convert standing privileged access to just-in-time elevation with documented approval.",
            "steps": [
                "Remove permanent admin role assignments where possible.",
                "Create approval-backed just-in-time elevation policy.",
                "Validate emergency access separately with quarterly attestation."
            ]
        },
        "upgrade_mfa": {
            "description": "Replace weak MFA with phishing-resistant authentication.",
            "steps": [
                "Enroll the identity in FIDO2 hardware key or certificate-based auth.",
                "Block SMS and email OTP for privileged and mission accounts.",
                "Run user validation and break-glass testing before cutover."
            ]
        },
        "revoke_role": {
            "description": "Remove excess role assignments that no longer match current duties.",
            "steps": [
                "Confirm current job function and required entitlements.",
                "Remove legacy Azure roles and AWS permission sets.",
                "Document compensating controls if temporary retention is needed."
            ]
        },
        "deprovision_account": {
            "description": "Disable active access and transition any remaining workload dependencies safely.",
            "steps": [
                "Disable interactive sign-in immediately.",
                "Preserve logs and mailbox or storage evidence per retention policy.",
                "Validate downstream systems for orphaned dependencies."
            ]
        },
        "assign_owner": {
            "description": "Assign accountable business and technical ownership to the service account.",
            "steps": [
                "Name a primary owner and alternate owner in the CMDB.",
                "Tie the account to a workload record and review schedule.",
                "Rotate credentials and document intended scope."
            ]
        },
        "conduct_access_review": {
            "description": "Run an immediate evidence-backed access review and close overdue findings.",
            "steps": [
                "Collect current role and sign-in evidence across Azure and AWS.",
                "Validate least privilege with the manager and system owner.",
                "Track remediation dates until closure."
            ]
        },
    }
    proposal = catalog[action_type]
    return {
        "user_id": user_id,
        "name": user.get("name"),
        "action_type": action_type,
        "approval_required": approval,
        "risk_level": score["risk_level"],
        "description": proposal["description"],
        "steps": proposal["steps"],
        "supporting_factors": score["factors"],
    }


def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    dispatcher = {
        "get_user_risk_score": lambda: handle_get_user_risk_score(tool_input["user_id"]),
        "get_users_with_role": lambda: handle_get_users_with_role(tool_input["role_name"], tool_input["cloud"]),
        "get_cross_cloud_admins": handle_get_cross_cloud_admins,
        "get_users_with_weak_mfa": handle_get_users_with_weak_mfa,
        "get_persona": lambda: handle_get_persona(tool_input["user_id"]),
        "propose_remediation": lambda: handle_propose_remediation(tool_input["user_id"], tool_input["action_type"]),
    }
    if tool_name not in dispatcher:
        return {"error": f"Unknown tool: {tool_name}"}
    result = dispatcher[tool_name]()
    try:
        json.dumps(result)
    except TypeError as exc:
        return {"error": f"Tool output is not JSON serializable: {exc}"}
    return result
