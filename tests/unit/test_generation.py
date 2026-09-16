"""generate_answer() prompt formatting and budget enforcement, with Groq mocked out."""
from types import SimpleNamespace

import pytest

from app.services import generation
from app.core.budget import Budget, BudgetExceededError


def _fake_client(content: str):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response)))


def test_format_context_labels_sources_with_and_without_section():
    chunks = [
        {"document": "a.md", "section": "Intro", "text": "hello"},
        {"document": "b.md", "section": None, "text": "world"},
    ]
    context = generation._format_context(chunks)
    assert "[1] Source: a.md (Intro)" in context
    assert "[2] Source: b.md\n" in context


def test_generate_answer_returns_stripped_content_and_uses_budget(monkeypatch):
    monkeypatch.setattr(generation, "get_client", lambda: _fake_client("  the answer  "))
    budget = Budget()

    answer = generation.generate_answer("q?", [{"document": "a.md", "section": None, "text": "ctx"}], budget)

    assert answer == "the answer"
    assert budget.llm_calls == 1
    assert budget.input_tokens > 0


def test_generate_answer_raises_before_calling_llm_when_budget_exhausted(monkeypatch):
    calls = []
    monkeypatch.setattr(generation, "get_client", lambda: calls.append("called"))
    budget = Budget(max_llm_calls=0)

    with pytest.raises(BudgetExceededError):
        generation.generate_answer("q?", [], budget)

    assert calls == []
