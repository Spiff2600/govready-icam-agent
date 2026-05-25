from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .agent_graph import run_agent
from .foundry import chat_completion

app = FastAPI(title="GovReady ICAM Agent", version="0.1.0")

class Ask(BaseModel):
    question: str


class Chat(BaseModel):
    message: str
    system: str | None = None


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/v1/ask")
def ask(payload: Ask):
    result = run_agent(payload.question)
    return result


@app.post("/chat")
def chat(payload: Chat):
    try:
        return chat_completion(payload.message, payload.system)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
