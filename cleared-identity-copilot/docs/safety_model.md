# Safety Model

Cleared Identity Co-Pilot follows a layered safety design aligned with Anthropic's emphasis on controllable tool use, human oversight, and transparent system boundaries.

## Synthetic data assurance

- Every record in `sample_data/` is fictional and marked as synthetic.
- The customer, mission, cloud tenants, account numbers, and identities are invented for demo use.
- The app banner and documentation repeatedly warn that no real federal data is present.

## Human approval gate architecture

- Claude can recommend actions, but it cannot execute them automatically.
- The UI only logs an action after a human explicitly selects **Approve**, **Reject**, or **Modify**.
- Approval levels are carried in the structured output so reviewers can distinguish routine changes from CISO-level decisions.

## Tool-use separation

- Deterministic Python functions load data, score users, and generate graph relationships.
- Claude receives only the approved `TOOLS` schema and must rely on returned evidence.
- The system prompt forbids invented facts and requires assumptions to be labeled explicitly.

## No real credentials policy

- The repository does not contain live credentials.
- `ANTHROPIC_API_KEY` is read only from the environment and is optional.
- If no API key is present, the app falls back to a cached synthetic response instead of attempting any external call.
- The demo never asks for customer secrets, tokens, or tenant-connected data.

## Prompt injection and tool misuse

Even with a small, read-only tool surface, the assistant has to be resilient to user input that tries to override the system prompt or coax it into producing harmful content. The design addresses this in three layers:

- **Bounded tool surface.** Claude can only call the functions declared in `tools/claude_tools.py:TOOLS`. There is no shell tool, no arbitrary HTTP fetch, and no way for the model to introduce a new tool at runtime. Adversarial strings inside `sample_data/` cannot escalate into code execution because the tools return structured Python dicts, not executable content.
- **Read-only deterministic tools.** Every approved tool is a pure read of the in-memory synthetic dataset (`identity_loader.py`, `risk_scoring.py`, `graph_builder.py`). There is no write, delete, or external-side-effect path the model can reach, so a successful injection still cannot mutate state or exfiltrate data outside the chat transcript.
- **Human approval gate on every recommendation.** The UI never auto-executes a recommended action. Even if the model were tricked into proposing something unsafe, a human has to click **Approve** before it is logged as taken — and the approval level (`none | IT_lead | CISO`) is part of the structured output so reviewers can spot escalation attempts.
- **Measured, not assumed.** The eval suite includes three intentional refusal prompts (`eval_016` insufficient evidence, `eval_017` direct prompt-injection override, `eval_018` request to draft a phishing email). They are scored on whether the response refuses, and the seeded results in `evals/results_cache.json` show a real behavior gap across model sizes — smaller models are more likely to partially comply with an injection wrapper, which is exactly the kind of signal the suite is designed to surface.

What this design does **not** claim: it does not prove the assistant is injection-proof. A determined adversary with control over tool *output* (for example, a future connector that returns attacker-controlled text from a real tenant) could still influence the model. The mitigation for that case is the same as for the synthetic demo: keep the tool surface small, keep tool output schema-validated, and keep a human in the loop before any action lands.
