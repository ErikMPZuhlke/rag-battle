"""The POST /ingest endpoint: (re)build the Chroma index from the corpus."""
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.ingest import IngestResponse
from app.services.ingest import build_index
from app.services.retrieval import reset_collection_cache

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
def ingest_endpoint():
    try:
        count = build_index()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    reset_collection_cache()  # drop the stale handle to the recreated collection
    return IngestResponse(
        chunks_indexed=count,
        collection=settings.chroma_collection,
        persist_dir=settings.chroma_persist_dir,
    )
