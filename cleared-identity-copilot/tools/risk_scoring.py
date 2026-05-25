"""
risk_scoring.py
Deterministic risk scoring for identity exposure.
Each rule is documented with NIST 800-53 control mapping.
No ML, no randomness - same input always produces same output.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

AS_OF_DATE = date(2025, 3, 1)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _days_since(value: str | None) -> int:
    parsed = _parse_date(value)
    if not parsed:
        return 0
    return max((AS_OF_DATE - parsed).days, 0)


def _has_azure_role(user: dict[str, Any], *role_names: str) -> bool:
    names = {role.lower() for role in role_names}
    return any(role.get("role_name", "").lower() in names for role in user.get("azure_roles", []))


def _has_aws_permission(user: dict[str, Any], *permission_sets: str) -> bool:
    names = {name.lower() for name in permission_sets}
    return any(permission.get("permission_set", "").lower() in names for permission in user.get("aws_permission_sets", []))


def _factor(user: dict[str, Any], text: str, factors: list[str]) -> None:
    if text not in factors:
        factors.append(text)


def score_mfa_risk(user: dict[str, Any]) -> int:
    """Map MFA strength to deterministic risk (IA-2, IA-5)."""
    mapping = {
        "fido2_hardware": 0,
        "authenticator_app": 10,
        "sms": 60,
        "email_otp": 70,
        "none": 100,
    }
    return mapping.get(user.get("primary_mfa_method", "authenticator_app"), 25)


def score_privilege_risk(user: dict[str, Any]) -> int:
    """Score privilege concentration and standing access (AC-6, AC-5)."""
    score = 0
    if _has_azure_role(user, "Global Administrator"):
        score = max(score, 95)
    elif _has_azure_role(user, "Privileged Role Administrator"):
        score = max(score, 85)
    elif _has_azure_role(user, "Security Administrator"):
        score = max(score, 70)
    elif _has_azure_role(user, "Application Administrator", "Exchange Administrator"):
        score = max(score, 55)
    elif _has_azure_role(user, "Contributor"):
        score = max(score, 28)
    elif _has_azure_role(user, "Reader"):
        score = max(score, 10)
    if _has_azure_role(user, "Security Reader"):
        score = max(score, 48)
    if _has_azure_role(user, "Threat Intelligence Contributor"):
        score = max(score, 72)
    if _has_aws_permission(user, "AdministratorAccess"):
        score = max(score, 100)
    elif _has_aws_permission(user, "PowerUserAccess"):
        score = max(score, 70)
    elif _has_aws_permission(user, "S3SQSFullLambda"):
        score = max(score, 88)
    elif _has_aws_permission(user, "BedrockS3Access", "S3SageMakerAccess"):
        score = max(score, 35)
    elif _has_aws_permission(user, "ReadOnlyAccess", "S3ReadAccess", "S3PutObject"):
        score = max(score, 12)

    if user.get("account_type") == "service" and "overscoped_service_account" in user.get("risk_indicators", []):
        score = max(score, 95)
    if any(role.get("assignment_type") == "permanent" for role in user.get("azure_roles", [])) and any(
        "administrator" in role.get("role_name", "").lower() or "privileged role" in role.get("role_name", "").lower()
        for role in user.get("azure_roles", [])
    ):
        score = min(100, score + 5)
    return min(score, 100)


def score_access_staleness(user: dict[str, Any]) -> int:
    """Score stale review cycles, transfer drift, and offboarding failures (AC-2, PS-4)."""
    score = 0
    review = user.get("access_review", {})
    overdue_days = int(review.get("days_overdue", 0) or 0)
    if overdue_days >= 180:
        score = max(score, 85)
    elif overdue_days >= 120:
        score = max(score, 70)
    elif overdue_days >= 60:
        score = max(score, 55)
    elif overdue_days >= 30:
        score = max(score, 35)
    elif overdue_days > 0:
        score = max(score, 20)

    indicators = set(user.get("risk_indicators", []))
    if "transferred_employee" in indicators or "retained_legacy_roles" in indicators:
        score = max(score, 90)
    if "post_contract_access" in indicators or "deprovisioning_failure" in indicators:
        score = max(score, 100)
    if "emergency_access_stale" in indicators:
        score = max(score, 90)
    if "credential_sharing_confirmed" in indicators:
        score = max(score, 95)
    if user.get("account_type") == "service" and (not user.get("service_account_owner") or user.get("service_account_owner") == "Departed Employee"):
        score = max(score, 80)
    contract_end = _parse_date(user.get("contract_end_date"))
    if contract_end and contract_end < AS_OF_DATE and user.get("last_login"):
        score = max(score, 100)
    if _days_since(user.get("last_review_date")) > 180:
        score = max(score, 70)
    return min(score, 100)


def score_cross_cloud_risk(user: dict[str, Any]) -> int:
    """Score Azure/AWS combined blast radius (CA-7, AC-6)."""
    azure_tier0 = any(
        role.get("role_name", "").lower() in {"global administrator", "privileged role administrator"}
        for role in user.get("azure_roles", [])
    )
    azure_admin = any(
        any(keyword in role.get("role_name", "").lower() for keyword in ["administrator", "privileged role", "security administrator"])
        for role in user.get("azure_roles", [])
    )
    aws_admin = any(permission.get("permission_set", "").lower() == "administratoraccess" for permission in user.get("aws_permission_sets", []))
    aws_power = any(permission.get("permission_set", "").lower() in {"poweruseraccess", "s3sqsfulllambda"} for permission in user.get("aws_permission_sets", []))
    if user.get("azure_roles") and user.get("aws_permission_sets") and user.get("account_type") == "service":
        return 90
    if azure_tier0 and aws_admin:
        return 100
    if azure_admin and aws_power:
        return 70
    if azure_admin or aws_admin or aws_power:
        return 65
    if user.get("azure_roles") and user.get("aws_permission_sets"):
        if _has_azure_role(user, "Contributor") and _has_aws_permission(user, "BedrockS3Access", "S3SageMakerAccess"):
            return 38
        return 15
    return 0


def score_user(user: dict[str, Any]) -> dict[str, Any]:
    mfa = score_mfa_risk(user)
    privilege = score_privilege_risk(user)
    stale = score_access_staleness(user)
    cross_cloud = score_cross_cloud_risk(user)
    composite = round((mfa * 0.25) + (privilege * 0.35) + (stale * 0.25) + (cross_cloud * 0.15))

    factors: list[str] = []
    if mfa >= 60:
        _factor(user, f"Weak MFA method detected: {user.get('primary_mfa_method')}", factors)
    if privilege >= 80:
        _factor(user, "Highly privileged access assignment present.", factors)
    if stale >= 80:
        _factor(user, "Access review or lifecycle governance issue detected.", factors)
    if cross_cloud >= 90:
        _factor(user, "Administrative or sensitive access spans Azure Gov and AWS GovCloud.", factors)
    for indicator in user.get("risk_indicators", []):
        if indicator == "retained_legacy_roles":
            _factor(user, "Transferred employee retained legacy cyber roles after reassignment.", factors)
        if indicator == "credential_sharing_confirmed":
            _factor(user, "Confirmed credential sharing violates unique accountability requirements.", factors)
        if indicator == "unowned_service_account":
            _factor(user, "Service account lacks an assigned owner.", factors)
        if indicator == "post_contract_access":
            _factor(user, "Contractor account remained active after contract end.", factors)
        if indicator == "emergency_access_stale":
            _factor(user, "Temporary emergency access was never removed.", factors)

    indicators = set(user.get("risk_indicators", []))
    if (
        composite >= 85
        or {"post_contract_access", "credential_sharing_confirmed", "overscoped_service_account"} & indicators
        or (privilege >= 95 and mfa >= 60)
        or (privilege >= 95 and "emergency_access_stale" in indicators)
    ):
        risk_level = "CRITICAL"
    elif composite >= 65 or "retained_legacy_roles" in indicators:
        risk_level = "HIGH"
    elif composite >= 35:
        risk_level = "MED"
    else:
        risk_level = "LOW"

    return {
        "user_id": user["user_id"],
        "name": user.get("name", user["user_id"]),
        "composite_score": composite,
        "risk_level": risk_level,
        "breakdown": {
            "mfa_risk": mfa,
            "privilege_risk": privilege,
            "access_staleness": stale,
            "cross_cloud_risk": cross_cloud,
        },
        "factors": factors,
    }


def score_all_users(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((score_user(user) for user in users), key=lambda item: (-item["composite_score"], item["user_id"]))


def get_risk_summary(scored_users: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(scored_users)
    counts = {level: 0 for level in ["CRITICAL", "HIGH", "MED", "LOW"]}
    for user in scored_users:
        counts[user["risk_level"]] += 1
    avg_score = round(sum(user["composite_score"] for user in scored_users) / total, 1) if total else 0.0
    top = scored_users[:5]
    return {
        "total_users": total,
        "critical_count": counts["CRITICAL"],
        "high_count": counts["HIGH"],
        "medium_count": counts["MED"],
        "low_count": counts["LOW"],
        "average_score": avg_score,
        "top_risks": [{"user_id": user["user_id"], "name": user["name"], "score": user["composite_score"], "risk_level": user["risk_level"]} for user in top],
    }
