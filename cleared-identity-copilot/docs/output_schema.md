# Output Schema

Claude is instructed to emit a structured JSON object in the **Structured Output** section of every analysis response.

## Schema

```json
{
  "analysis_id": "string",
  "timestamp": "ISO8601",
  "model": "string",
  "findings": [
    {
      "finding_id": "string",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "string",
      "affected_users": ["user_id"],
      "evidence": ["string - tool call results"],
      "description": "string",
      "assumptions": ["string"],
      "nist_controls": ["string"]
    }
  ],
  "recommended_actions": [
    {
      "action_id": "string",
      "priority": 1,
      "action_type": "string",
      "target_users": ["user_id"],
      "description": "string",
      "approval_required": "none|IT_lead|CISO",
      "estimated_effort": "string",
      "risk_reduction": "string"
    }
  ],
  "risk_summary": {
    "overall_posture": "CRITICAL|HIGH|MEDIUM|LOW",
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0
  }
}
```

## Field guidance

- **analysis_id**: Unique identifier for traceability.
- **timestamp**: UTC timestamp of the analysis.
- **model**: Claude model used for the response.
- **findings**: Evidence-backed observations tied to users and NIST controls.
- **recommended_actions**: Ordered remediation steps that explicitly state required approval.
- **risk_summary**: Roll-up of overall posture and count by severity bucket.

## Safety expectations

- Findings must cite evidence from tool results.
- Assumptions must be isolated from facts.
- Recommended actions must not be treated as executed until a human approves them in the UI.
