"""Pydantic models for the /ingest endpoint."""
from pydantic import BaseModel


class IngestResponse(BaseModel):
    chunks_indexed: int
    collection: str
    persist_dir: str
