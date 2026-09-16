"""The POST /retrieve endpoint: vector search only, no LLM generation."""
from fastapi import APIRouter, HTTPException

from app.core.budget import Budget, BudgetExceededError
from app.core.config import settings
from app.schemas.retrieve import RetrieveRequest, RetrieveResponse
from app.services.retrieval import retrieve

router = APIRouter(tags=["retrieve"])


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_endpoint(request: RetrieveRequest):
    budget = Budget()
    top_k = request.top_k or settings.top_k
    try:
        chunks = retrieve(request.question, budget, top_k=top_k)
    except BudgetExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return RetrieveResponse(chunks=chunks)
