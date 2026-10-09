"""generate_answer() prompt formatting and budget enforcement, with Groq mocked out."""
from types import SimpleNamespace

import httpx
import pytest
from openai import RateLimitError

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


def _rate_limit_error(retry_after: str):
    response = httpx.Response(429, headers={"retry-after": retry_after}, request=httpx.Request("POST", "http://x"))
    return RateLimitError("rate limited", response=response, body=None)


def _scripted_client(outcomes):
    queue = list(outcomes)
    ok = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])

    def _create(**kwargs):
        outcome = queue.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return ok

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))


def test_generate_answer_retries_429_and_charges_budget_once(monkeypatch):
    sleeps = []
    monkeypatch.setattr(generation.time, "sleep", sleeps.append)
    client = _scripted_client([_rate_limit_error("2"), None])
    monkeypatch.setattr(generation, "get_client", lambda: client)
    budget = Budget()

    assert generation.generate_answer("q?", [], budget) == "ok"

    assert budget.llm_calls == 1
    assert sleeps == [2.5]


def test_generate_answer_raises_when_retry_wait_exceeds_cap(monkeypatch):
    monkeypatch.setattr(generation.time, "sleep", lambda _s: None)
    client = _scripted_client([_rate_limit_error("30")])
    monkeypatch.setattr(generation, "get_client", lambda: client)

    with pytest.raises(generation.LLMRateLimitedError) as exc_info:
        generation.generate_answer("q?", [], Budget())

    assert exc_info.value.retry_after == 30.5


def test_generate_answer_raises_after_max_retries(monkeypatch):
    monkeypatch.setattr(generation.time, "sleep", lambda _s: None)
    monkeypatch.setattr(generation.settings, "groq_max_retries", 1)
    client = _scripted_client([_rate_limit_error("1")] * 2)
    monkeypatch.setattr(generation, "get_client", lambda: client)

    with pytest.raises(generation.LLMRateLimitedError):
        generation.generate_answer("q?", [], Budget())
