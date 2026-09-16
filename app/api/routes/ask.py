"""The POST /ask endpoint: retrieve -> generate -> deduplicate sources."""
from fastapi import APIRouter, HTTPException

from app.core.budget import Budget, BudgetExceededError
from app.schemas.ask import AskRequest, AskResponse, Source
from app.services.generation import generate_answer
from app.services.retrieval import retrieve

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
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
