"""
Unit tests for the deterministic risk scoring engine in
``cleared-identity-copilot/tools/risk_scoring.py``.

The scoring functions are 100% deterministic - same input always produces
same output - so they are ideal for fast unit tests.  These tests pin down
the most important policy decisions encoded in the scoring rules.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "cleared-identity-copilot"))

from tools.risk_scoring import (  # noqa: E402
    get_risk_summary,
    score_access_staleness,
    score_all_users,
    score_cross_cloud_risk,
    score_mfa_risk,
    score_privilege_risk,
    score_user,
)


# ---------------------------------------------------------------------------
# MFA scoring
# ---------------------------------------------------------------------------
def test_sms_mfa_scores_high():
    assert score_mfa_risk({"primary_mfa_method": "sms"}) == 60


def test_fido2_scores_zero():
    assert score_mfa_risk({"primary_mfa_method": "fido2_hardware"}) == 0


def test_no_mfa_scores_max():
    assert score_mfa_risk({"primary_mfa_method": "none"}) == 100


def test_unknown_mfa_method_scores_conservative_default():
    # Unknown methods fall back to 25 (conservative, not zero).
    assert score_mfa_risk({"primary_mfa_method": "yubikey_otp"}) == 25


# ---------------------------------------------------------------------------
# Privilege scoring
# ---------------------------------------------------------------------------
def test_global_admin_scores_very_high():
    user = {"azure_roles": [{"role_name": "Global Administrator"}]}
    assert score_privilege_risk(user) >= 95


def test_aws_administrator_access_scores_max():
    user = {"aws_permission_sets": [{"permission_set": "AdministratorAccess"}]}
    assert score_privilege_risk(user) == 100


def test_reader_only_scores_low():
    user = {"azure_roles": [{"role_name": "Reader"}]}
    assert score_privilege_risk(user) <= 15


def test_permanent_admin_assignment_adds_premium():
    # Permanent assignment of an admin role bumps the score above the
    # eligible/JIT equivalent.
    eligible_user = {
        "azure_roles": [
            {"role_name": "Global Administrator", "assignment_type": "eligible"}
        ]
    }
    permanent_user = {
        "azure_roles": [
            {"role_name": "Global Administrator", "assignment_type": "permanent"}
        ]
    }
    assert score_privilege_risk(permanent_user) > score_privilege_risk(eligible_user)


# ---------------------------------------------------------------------------
# Access staleness scoring
# ---------------------------------------------------------------------------
def test_no_staleness_signals_scores_zero():
    assert score_access_staleness({}) == 0


def test_post_contract_access_is_max_staleness():
    user = {"risk_indicators": ["post_contract_access"]}
    assert score_access_staleness(user) == 100


def test_overdue_review_buckets_increase_monotonically():
    def s(days):
        return score_access_staleness({"access_review": {"days_overdue": days}})

    assert s(10) < s(45) < s(90) < s(150) < s(200)


# ---------------------------------------------------------------------------
# Cross-cloud blast radius
# ---------------------------------------------------------------------------
def test_no_cross_cloud_access_scores_zero():
    assert score_cross_cloud_risk({}) == 0


def test_global_admin_plus_aws_admin_is_max():
    user = {
        "azure_roles": [{"role_name": "Global Administrator"}],
        "aws_permission_sets": [{"permission_set": "AdministratorAccess"}],
    }
    assert score_cross_cloud_risk(user) == 100


def test_cross_cloud_service_account_scores_high():
    user = {
        "account_type": "service",
        "azure_roles": [{"role_name": "Contributor"}],
        "aws_permission_sets": [{"permission_set": "S3SQSFullLambda"}],
    }
    assert score_cross_cloud_risk(user) == 90


# ---------------------------------------------------------------------------
# Composite scoring + risk levels
# ---------------------------------------------------------------------------
def test_global_admin_is_critical_or_high():
    user = {
        "user_id": "USR_TEST",
        "name": "Test Admin",
        "azure_roles": [
            {"role_name": "Global Administrator", "assignment_type": "permanent"}
        ],
        "aws_permission_sets": [],
        "primary_mfa_method": "sms",
        "risk_indicators": [],
    }
    result = score_user(user)
    assert result["risk_level"] in ("CRITICAL", "HIGH")
    assert result["composite_score"] >= 55
    assert any("MFA" in factor or "mfa" in factor for factor in result["factors"])


def test_low_risk_user_is_low():
    user = {
        "user_id": "USR_LOW",
        "name": "Low Risk Reader",
        "azure_roles": [{"role_name": "Reader", "assignment_type": "eligible"}],
        "aws_permission_sets": [],
        "primary_mfa_method": "fido2_hardware",
        "risk_indicators": [],
    }
    result = score_user(user)
    assert result["risk_level"] == "LOW"
    assert result["composite_score"] < 35


def test_score_user_is_deterministic():
    user = {
        "user_id": "USR_DET",
        "name": "Deterministic",
        "azure_roles": [{"role_name": "Security Administrator"}],
        "aws_permission_sets": [{"permission_set": "PowerUserAccess"}],
        "primary_mfa_method": "authenticator_app",
        "risk_indicators": [],
    }
    assert score_user(user) == score_user(user)


def test_post_contract_access_indicator_forces_critical():
    user = {
        "user_id": "CTR_TEST",
        "name": "Expired Contractor",
        "azure_roles": [{"role_name": "Reader"}],
        "aws_permission_sets": [],
        "primary_mfa_method": "authenticator_app",
        "risk_indicators": ["post_contract_access"],
    }
    assert score_user(user)["risk_level"] == "CRITICAL"


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------
def test_score_all_users_is_sorted_desc_by_score():
    users = [
        {
            "user_id": "U1",
            "name": "Reader",
            "azure_roles": [{"role_name": "Reader"}],
            "primary_mfa_method": "fido2_hardware",
        },
        {
            "user_id": "U2",
            "name": "Global Admin",
            "azure_roles": [
                {"role_name": "Global Administrator", "assignment_type": "permanent"}
            ],
            "aws_permission_sets": [{"permission_set": "AdministratorAccess"}],
            "primary_mfa_method": "sms",
        },
    ]
    scored = score_all_users(users)
    assert scored[0]["user_id"] == "U2"
    assert scored[0]["composite_score"] >= scored[1]["composite_score"]


def test_get_risk_summary_counts_by_level():
    scored = [
        {"user_id": "a", "name": "a", "composite_score": 95, "risk_level": "CRITICAL"},
        {"user_id": "b", "name": "b", "composite_score": 70, "risk_level": "HIGH"},
        {"user_id": "c", "name": "c", "composite_score": 40, "risk_level": "MED"},
        {"user_id": "d", "name": "d", "composite_score": 10, "risk_level": "LOW"},
    ]
    summary = get_risk_summary(scored)
    assert summary == {
        "total_users": 4,
        "critical_count": 1,
        "high_count": 1,
        "medium_count": 1,
        "low_count": 1,
        "average_score": 53.8,
        "top_risks": [
            {"user_id": "a", "name": "a", "score": 95, "risk_level": "CRITICAL"},
            {"user_id": "b", "name": "b", "score": 70, "risk_level": "HIGH"},
            {"user_id": "c", "name": "c", "score": 40, "risk_level": "MED"},
            {"user_id": "d", "name": "d", "score": 10, "risk_level": "LOW"},
        ],
    }
