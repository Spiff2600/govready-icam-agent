# GovReady ICAM Agent (Demo)

**Elevator pitch:** A small, showcase-ready agent that audits Microsoft Entra / Azure identity posture, explains recommendations in plain English mapped to federal guidance (NIST 800-53, SCuBA, M-21-31), and produces artifacts your stakeholders can act on.

This repo is built for quick demos **without** touching real tenant data. It includes:
- A pluggable agent loop with tool calling (FastAPI endpoint).
- Stubs for Graph/Kusto calls (swap in real connectors later).
- Policy-as-code guardrails.
- Synthetic data generator to demo queries safely.
- A short **6‑minute demo script** you can run on any laptop.

> ⚠️ Note: No USG data or credentials are required. This is a local demo. Replace the stubs with Azure Gov/AOAI/Graph clients when you’re ready.

---

## 1) Quickstart

```bash
# Python 3.11+
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# (Optional) create local env
cp config/settings.example.yaml config/settings.yaml

# seed synthetic data
python scripts/seed_synthetic.py

# run the API
uvicorn app.main:app --reload --port 8080
```

Test it:

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s -X POST http://127.0.0.1:8080/v1/ask -H "Content-Type: application/json" -d '{"question":"List permanent vs eligible role assignments and recommend least-privilege fixes."}' | jq .
```

---

## 2) What this agent does (MVP)

- **CA Policy Advisor:** Generates a baseline Conditional Access (CA) policy to require MFA *only* on admin portals (showcases guardrail logic).
- **Role Assignment Auditor:** Reads synthetic “role assignments” and shows **permanent vs. eligible** (demoing the view you’d want across 50+ subs).
- **CBA/PIV Mapping Explainer:** Walkthrough of X.509→Entra mapping steps (issuer/SKI rules) as an actionable checklist.
- **Compliance Explainer:** Each recommendation references relevant **M-21-31 / SCuBA / NIST 800-53** sections (for stakeholder trust).

> This is a scaffold. Replace the synthetic parts with real calls via MS Graph, Azure Resource Manager, Kusto/Sentinel, etc., when moving to tenant-connected PoC.

---

## 3) Architecture (at a glance)

```
+------------------+        +--------------------+
|  FastAPI / REST  |<------>|  Agent Orchestrator|
+------------------+        +--------------------+
          |                          |  calls tools with structured inputs
          v                          v
     Policy Guardrails        +------------------+
      (YAML rules)            |   Tools Layer    |
                              |  - entra.py      |
                              |  - kusto.py      |
                              +------------------+
                                      |
                               Synthetic/Real Data
```

---

## 4) 6‑Minute Demo Script

1. **Open** the Swagger UI: http://127.0.0.1:8080/docs
2. **Ask:** “Generate a CA policy to enforce MFA only for admin portals; explain user impact and rollback.”
3. **Ask:** “List permanent vs eligible role assignments; output CSV + top 3 least‑privilege fixes.”
4. **Ask:** “Give a checklist to implement PIV/CBA with issuer/SKI mapping in Entra.”
5. **Ask:** “Map those recommendations to M‑21‑31, SCuBA, NIST 800‑53 controls.”
6. **Show** that the response includes a **transparent tool‑trace** (what it executed) without exposing model internals.

---

## 5) Swap in real connectors (later)

- **Graph (directory roles & PIM):** Use `msal` + Graph SDK; for Azure resource roles + PIM eligible instances, use Azure Resource Manager roleEligibilityScheduleInstances APIs.
- **Kusto/Sentinel:** Use `azure-kusto-data` to run saved queries in a read‑only workspace. Pull policy‑relevant metrics only.
- **AOAI (Gov) or local models:** Make the LLM provider pluggable: env flag `PROVIDER=azure_openai|openai|local`.

---

## 6) Compliance & Guardrails

- No secrets in logs. Redact tokens/domains/UPNs by default.
- Minimal privileges for connectors; use Managed Identity when deployed.
- Private networking (VNet, Private Endpoints) for any cloud endpoints.
- Outputs include a justification + control mapping for auditability.
- See `app/policies/policy_pack.yaml` to extend guardrails as code.

---

## 7) Repo Layout

```
app/
  main.py                # FastAPI app
  agent_graph.py         # Orchestrator + tool routing
  tools/
    entra.py             # Entra/Graph/PIM stubs
    kusto.py             # Kusto/Sentinel stub
  policies/
    policy_pack.yaml     # Guardrails-as-code
config/
  settings.example.yaml  # Config template
scripts/
  seed_synthetic.py      # Generates fake role assignments & sign-ins
synthetic_data/
  role_assignments.csv
  signins.csv
tests/
  test_policies.py
requirements.txt
```

---

## 8) Roadmap Ideas

- Add export of **eligible** Azure Resource role assignments via PIM schedule instances.
- Add analyzer for **Conditional Access gaps** (break-glass, device state, service tags).
- Add **evidence pack** generator (PDF/CSV bundle) for auditors.
- Integrate **Defender XDR** & **Purview** signals for higher-context findings.
