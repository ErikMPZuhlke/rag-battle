"""Pure logic: Budget counters and limit enforcement (no network/index needed)."""
import pytest

from app.core.budget import Budget, BudgetExceededError, count_tokens
from app.core.config import settings


def test_count_tokens_counts_nonzero_tokens_for_text():
    assert count_tokens("") == 0
    assert count_tokens("hello world") > 0


def test_budget_defaults_match_config():
    budget = Budget()
    assert budget.max_llm_calls == settings.max_llm_calls
    assert budget.max_retrievals == settings.max_retrievals
    assert budget.max_input_tokens == settings.max_input_tokens


def test_use_retrieval_allows_up_to_the_limit():
    budget = Budget(max_retrievals=2)
    budget.use_retrieval()
    budget.use_retrieval()
    assert budget.retrievals == 2


def test_use_retrieval_raises_once_over_the_limit():
    budget = Budget(max_retrievals=1)
    budget.use_retrieval()
    with pytest.raises(BudgetExceededError):
        budget.use_retrieval()


def test_use_llm_call_tracks_calls_and_tokens():
    budget = Budget(max_llm_calls=5, max_input_tokens=1000)
    budget.use_llm_call("hello world")
    assert budget.llm_calls == 1
    assert budget.input_tokens == count_tokens("hello world")


def test_use_llm_call_raises_when_call_count_exceeded():
    budget = Budget(max_llm_calls=1, max_input_tokens=1000)
    budget.use_llm_call("hello")
    with pytest.raises(BudgetExceededError):
        budget.use_llm_call("hello")


def test_use_llm_call_raises_when_token_budget_exceeded():
    budget = Budget(max_llm_calls=5, max_input_tokens=1)
    with pytest.raises(BudgetExceededError):
        budget.use_llm_call("this prompt certainly has more than one token")
