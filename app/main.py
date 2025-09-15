from fastapi import FastAPI
from pydantic import BaseModel
from .agent_graph import run_agent

app = FastAPI(title="GovReady ICAM Agent", version="0.1.0")

class Ask(BaseModel):
    question: str

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/v1/ask")
def ask(payload: Ask):
    result = run_agent(payload.question)
    return result
