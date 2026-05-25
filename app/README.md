# `app/` — Legacy FastAPI ICAM agent

> **This is NOT the main demo.** It is kept for historical context.

The primary, interview-ready demo for this repository is the Streamlit
**Cleared Identity Co-Pilot** in [`../cleared-identity-copilot/`](../cleared-identity-copilot/).
That app uses real Anthropic Claude tool-use, an approval gate, deterministic
risk scoring, and an evals harness.

## What lives here

`app/` is an earlier FastAPI prototype of the same problem domain. It uses a
simple keyword-dispatch graph (`agent_graph.py`) and stub tools, and only
optionally calls Claude via the `/chat` endpoint when
`ANTHROPIC_FOUNDRY_ENDPOINT` is configured. It does **not** demonstrate the
tool-use loop, approval gate, or evals story that the Streamlit app shows.

## Running the legacy app (optional)

```bash
make run-legacy   # uvicorn app.main:app --reload --port 8080
```

## Running the actual demo

```bash
streamlit run cleared-identity-copilot/app.py
# or:
make run
```
