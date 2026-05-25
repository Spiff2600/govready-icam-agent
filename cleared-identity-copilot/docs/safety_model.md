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
