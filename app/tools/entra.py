import csv, os
from typing import Dict, Any, List

SYNTHETIC_ROLES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "synthetic_data", "role_assignments.csv")

def _load_roles() -> List[Dict[str, str]]:
    rows = []
    if os.path.exists(SYNTHETIC_ROLES):
        with open(SYNTHETIC_ROLES, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows

def audit_roles(question: str) -> Dict[str, Any]:
    rows = _load_roles()
    permanent = [r for r in rows if r.get("assignment_type") == "permanent"]
    eligible = [r for r in rows if r.get("assignment_type") == "eligible"]

    recs = []
    if permanent:
        recs.append("Convert permanent high-privilege roles (e.g., Owner, User Access Administrator) to PIM-eligible with approval + JIT activation.")
    if eligible:
        recs.append("Tighten PIM: reduce max activation duration to 2-4h; require MFA + ticket ID justification; enable notifications.")

    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "synthetic_data", "role_assignments.csv"))
    return {
        "summary": {
            "total": len(rows),
            "permanent": len(permanent),
            "eligible": len(eligible),
            "top_findings": [
                "Excess permanent assignments increase standing privilege risk (AC-6).",
                "Ensure break-glass accounts are monitored and excluded from PIM rotations.",
            ],
        },
        "recommendations": recs,
        "artifacts": {"role_assignments_csv": csv_path},
        "notes": "In a real deployment, replace with Graph/ARM APIs for directory and Azure resource roles, including PIM schedule instances for 'eligible'.",
    }

def advise_ca_policy(question: str) -> Dict[str, Any]:
    baseline = {
        "name": "Require MFA for admin portals",
        "conditions": {
            "user_risk": "low+",
            "client_apps": ["browser", "modern_auth"],
            "cloud_apps": ["Azure portal", "Microsoft Admin Portals"],
            "device_platforms": ["Any"],
            "locations": ["Any"],
        },
        "grant_controls": ["Require MFA"],
        "session_controls": ["Sign-in frequency 12h (admins)"],
        "exclusions": ["Break-glass accounts (2)"],
        "rollout": ["Report-only 7 days", "Then On for 'Admins' group", "Stage to broader admin sets"],
        "rollback_plan": ["Disable policy", "Use emergency access account", "Publish comms to affected admins"],
        "justification": "Limits MFA prompts to high-risk surfaces while minimizing user friction; aligns with least-privilege and strong auth for privileged operations (IA-2, IA-11).",
        "references": ["CISA SCuBA Entra CA Baseline", "NIST 800-53 IA-2", "M-21-31"],
    }
    return {"policy": baseline}
