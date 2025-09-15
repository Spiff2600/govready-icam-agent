import csv, os
from typing import Dict, Any, List
SYNTHETIC_SIGNINS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "synthetic_data", "signins.csv")

def _load_signins() -> List[Dict[str, str]]:
    rows = []
    if os.path.exists(SYNTHETIC_SIGNINS):
        with open(SYNTHETIC_SIGNINS, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows

def summarize_signins(question: str) -> Dict[str, Any]:
    rows = _load_signins()
    total = len(rows)
    by_status = {}
    for r in rows:
        s = r.get("status", "Unknown")
        by_status[s] = by_status.get(s, 0) + 1
    anomalies = [r for r in rows if r.get("risk") in ("high", "medium")]
    return {
        "summary": {
            "total_signins": total,
            "status_breakdown": by_status,
            "anomalies": len(anomalies),
        },
        "recommendations": [
            "Enable sign-in risk-based CA controls for medium+ risk.",
            "Add sign-in frequency for privileged roles.",
            "Investigate repeat failures by IP/app — consider blocking legacy protocols."
        ],
        "notes": "Replace with real KQL via azure-kusto-data in connected mode."
    }
