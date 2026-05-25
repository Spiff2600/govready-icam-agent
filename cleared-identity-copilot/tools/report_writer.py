"""
report_writer.py
Generates executive brief and technical remediation content.
Uses Claude for prose generation, deterministic tools for data.
"""
from __future__ import annotations

from typing import Any

from tools.claude_client import analyze_identity_exposure
from tools.identity_loader import load_all_users
from tools.risk_scoring import get_risk_summary, score_all_users


def _top_users(limit: int = 10) -> list[dict[str, Any]]:
    users = load_all_users()
    return score_all_users(users)[:limit]


def generate_executive_brief(model: str = "claude-sonnet-4-5") -> dict[str, Any]:
    users = load_all_users()
    scored = score_all_users(users)
    summary = get_risk_summary(scored)
    prompt = (
        "Generate a concise executive brief for a federal CIO and CISO. Include a 3-4 sentence summary, "
        "CISO findings, and prioritize 30/60/90 day actions for cross-cloud identity risk."
    )
    analysis = analyze_identity_exposure(prompt, user_context={"risk_summary": summary, "top_users": scored[:5]}, model=model)
    cio_summary = (
        f"Orion Federal's synthetic identity posture is {summary['top_risks'][0]['risk_level']} with {summary['critical_count']} critical accounts and "
        f"{summary['high_count']} additional high-risk identities across Azure Gov and AWS GovCloud. The largest drivers are cross-cloud administrators, "
        "weak MFA on privileged users, stale access after role changes, and ungoverned service accounts. The environment is still recoverable within a quarter if privileged access is converted to just-in-time workflows and service-account ownership is enforced immediately."
    )
    plan = [
        {"Phase": "30 Days", "Actions": "Upgrade MFA for privileged users; deprovision CTR001; assign owners to SVC001/SVC002", "Owner": "Identity Ops + CISO", "Investment": "Low", "Risk Reduction": "High"},
        {"Phase": "60 Days", "Actions": "Convert permanent admin roles to PIM/JIT; remove Tamara Osei legacy roles; validate access reviews", "Owner": "Cloud Platform", "Investment": "Medium", "Risk Reduction": "High"},
        {"Phase": "90 Days", "Actions": "Operationalize quarterly cross-cloud reviews, SCP guardrails, and Security Lake telemetry", "Owner": "Enterprise Security", "Investment": "Medium", "Risk Reduction": "Medium-High"},
    ]
    ciso_findings = [
        "Cross-cloud admin concentration remains the fastest route to tenant-wide compromise.",
        "Weak or absent MFA is still present on privileged, analyst, and service identities.",
        "Lifecycle governance is failing on transfers, contractors, and service account ownership.",
        "Credential sharing between USR017 and SVC001 undermines attribution and auditability.",
    ]
    return {
        "cio_summary": cio_summary,
        "risk_posture": summary,
        "plan": plan,
        "ciso_findings": ciso_findings,
        "analysis": analysis,
        "token_usage": analysis.get("token_usage", {"input": 0, "output": 0, "cost_usd": 0.0}),
        "from_cache": analysis.get("from_cache", True),
    }


def build_technical_remediation_report(limit: int = 10) -> dict[str, Any]:
    users = load_all_users()
    scored = score_all_users(users)
    top = scored[:limit]
    user_reports = []
    for item in top:
        steps = []
        if item["breakdown"]["mfa_risk"] >= 60:
            steps.append("Move to phishing-resistant MFA and block SMS/email OTP.")
        if item["breakdown"]["privilege_risk"] >= 70:
            steps.append("Convert standing privilege to PIM/JIT and remove unnecessary admin roles.")
        if item["breakdown"]["access_staleness"] >= 70:
            steps.append("Complete an immediate access review and remediate stale entitlements.")
        if item["breakdown"]["cross_cloud_risk"] >= 90:
            steps.append("Separate duties across Azure Gov and AWS GovCloud to reduce blast radius.")
        user_reports.append({
            "user_id": item["user_id"],
            "name": item["name"],
            "risk_level": item["risk_level"],
            "risk_score": item["composite_score"],
            "risk_factors": item["factors"],
            "remediation_steps": steps or ["Maintain current controls and review on standard cadence."],
        })
    azure_recommendations = [
        "Require Conditional Access policies that block SMS and email OTP for admins and mission-critical analysts.",
        "Convert Global Administrator, Privileged Role Administrator, and Security Administrator assignments to approval-backed PIM eligibility.",
        "Roll out FIDO2 hardware keys to privileged users first, then to data science and mission analyst cohorts with weak MFA.",
        "Set quarterly access reviews for all privileged roles and monthly reviews for service accounts and contractors.",
    ]
    aws_recommendations = [
        "Reduce IAM Identity Center use of AdministratorAccess and PowerUserAccess by mapping users to narrower permission sets.",
        "Add service control policy guardrails to prevent unrestricted admin use outside approved break-glass workflows.",
        "Forward CloudTrail events into Security Lake and correlate with Azure sign-in events for cross-cloud investigations.",
    ]
    return {
        "top_users": user_reports,
        "azure_recommendations": azure_recommendations,
        "aws_recommendations": aws_recommendations,
    }
