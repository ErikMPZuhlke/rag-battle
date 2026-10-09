"""/ask endpoint logic (source de-duplication, budget-error mapping) with
retrieval and generation mocked out -- no LLM/corpus dependency."""
import app.api.routes.ask as ask_route
from app.core.budget import BudgetExceededError
from app.services.generation import LLMRateLimitedError


def test_ask_deduplicates_sources_by_document_keeping_first_section(client, monkeypatch):
    chunks = [
        {"document": "a.md", "section": "Intro", "text": "x"},
        {"document": "a.md", "section": "Later", "text": "y"},
        {"document": "b.md", "section": None, "text": "z"},
    ]
    monkeypatch.setattr(ask_route, "retrieve", lambda question, budget: chunks)
    monkeypatch.setattr(ask_route, "generate_answer", lambda question, chunks, budget: "an answer")

    response = client.post("/ask", json={"question": "anything"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "an answer"
    assert [s["document"] for s in body["sources"]] == ["a.md", "b.md"]
    assert body["sources"][0]["section"] == "Intro"


def test_ask_returns_429_when_budget_exceeded(client, monkeypatch):
    def _boom(question, budget):
        raise BudgetExceededError("nope")

    monkeypatch.setattr(ask_route, "retrieve", _boom)

    response = client.post("/ask", json={"question": "anything"})

    assert response.status_code == 429


def test_ask_returns_503_with_retry_after_when_llm_rate_limited(client, monkeypatch):
    def _limited(question, chunks, budget):
        raise LLMRateLimitedError(12.4)

    monkeypatch.setattr(ask_route, "retrieve", lambda question, budget: [])
    monkeypatch.setattr(ask_route, "generate_answer", _limited)

    response = client.post("/ask", json={"question": "anything"})

    assert response.status_code == 503
    assert response.headers["retry-after"] == "13"
