"""FastAPI app exposing the POST /ask contract."""
from fastapi import FastAPI, HTTPException

from app.budget import Budget, BudgetExceededError
from app.generation import generate_answer
from app.models import AskRequest, AskResponse, Source
from app.retrieval import retrieve

app = FastAPI(title="Acme Cloud Knowledge Assistant")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    budget = Budget()
    try:
        chunks = retrieve(request.question, budget)
        answer = generate_answer(request.question, chunks, budget)
    except BudgetExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    seen_documents = set()
    sources = []
    for chunk in chunks:
        if chunk["document"] in seen_documents:
            continue
        seen_documents.add(chunk["document"])
        sources.append(Source(document=chunk["document"], section=chunk["section"]))

    return AskResponse(answer=answer, sources=sources)
