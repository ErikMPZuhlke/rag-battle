"""Pydantic request/response models for the /ask API contract."""
from typing import Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class Source(BaseModel):
    document: str
    section: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
