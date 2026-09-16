"""Pydantic request/response schema behavior for the /ask contract."""
import pytest
from pydantic import ValidationError

from app.schemas.ask import AskRequest, AskResponse, Source


def test_ask_request_accepts_nonempty_question():
    assert AskRequest(question="hi").question == "hi"


def test_ask_request_rejects_empty_question():
    with pytest.raises(ValidationError):
        AskRequest(question="")


def test_source_defaults_section_to_none():
    assert Source(document="a.md").section is None


def test_ask_response_serializes_to_contract_shape():
    response = AskResponse(answer="hi", sources=[Source(document="a.md", section="Intro")])
    assert response.model_dump() == {"answer": "hi", "sources": [{"document": "a.md", "section": "Intro"}]}
