from typing import Dict, Any
from .tools.entra import advise_ca_policy, audit_roles
from .tools.kusto import summarize_signins

def classify_intent(q: str) -> str:
    qs = q.lower()
    if "conditional access" in qs or "mfa" in qs or "admin portal" in qs:
        return "ca_policy"
    if "role" in qs and ("eligible" in qs or "permanent" in qs or "pim" in qs):
        return "roles_audit"
    if "signin" in qs or "sign-in" in qs:
        return "signin_summary"
    return "general"

def run_agent(question: str) -> Dict[str, Any]:
    intent = classify_intent(question)
    trace = []
    answer: Dict[str, Any] = {}

    if intent == "ca_policy":
        res = advise_ca_policy(question)
        trace.append({"tool": "advise_ca_policy", "ok": True})
        answer = res
    elif intent == "roles_audit":
        res = audit_roles(question)
        trace.append({"tool": "audit_roles", "ok": True})
        answer = res
    elif intent == "signin_summary":
        res = summarize_signins(question)
        trace.append({"tool": "summarize_signins", "ok": True})
        answer = res
    else:
        # default helpful response
        answer = {
            "message": "I can help with CA policy baselines, role assignment audits (eligible vs permanent), and sign-in summaries using synthetic data. Try asking for a CA policy for admin portals only, or to list permanent vs eligible roles."
        }
        trace.append({"tool": "none", "ok": True})

    # Always include a transparent tool-trace (no model internals)
    answer["trace"] = trace
    answer["intent"] = intent
    answer["references"] = [
        "NIST SP 800-53 (AC, IA, AU)",
        "CISA SCuBA baselines",
        "OMB M-21-31"
    ]
    return answer
