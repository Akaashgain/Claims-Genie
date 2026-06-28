from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agents.supervisor import run_agent
from tools.search_tool import build_faiss_index


app = FastAPI(
    title="Agentic Document Assistant",
    description="LangGraph document assistant for salary slips, bank statements, and offer letters.",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    question: str
    document_type: str
    answer: str
    sources: list[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/index")
def index_documents():
    try:
        return build_faiss_index()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        result = run_agent(request.question)
        return AskResponse(question=request.question, **result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
