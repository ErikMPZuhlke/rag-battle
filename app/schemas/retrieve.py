"""Pydantic models for the /retrieve endpoint."""
from typing import Optional

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, description="Overrides the configured default top-k.")


class Chunk(BaseModel):
    text: str
    document: str
    section: Optional[str] = None
    distance: float


class RetrieveResponse(BaseModel):
    chunks: list[Chunk]
