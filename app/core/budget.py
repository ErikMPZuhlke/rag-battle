"""Per-request resource budget guard (LLM calls / retrievals / input tokens).

Teams must stay within this budget; it exists to force engineering
trade-offs instead of brute-forcing quality with more tokens/calls.
"""
import tiktoken

from app.core.config import settings

_encoding = tiktoken.get_encoding("cl100k_base")


class BudgetExceededError(Exception):
    pass


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))


class Budget:
    """Tracks resource usage for a single /ask request."""

    def __init__(
        self,
        max_llm_calls: int = settings.max_llm_calls,
        max_retrievals: int = settings.max_retrievals,
        max_input_tokens: int = settings.max_input_tokens,
    ):
        self.max_llm_calls = max_llm_calls
        self.max_retrievals = max_retrievals
        self.max_input_tokens = max_input_tokens
        self.llm_calls = 0
        self.retrievals = 0
        self.input_tokens = 0

    def use_retrieval(self, count: int = 1) -> None:
        self.retrievals += count
        if self.retrievals > self.max_retrievals:
            raise BudgetExceededError(
                f"Retrieval budget exceeded: {self.retrievals} > {self.max_retrievals}"
            )

    def use_llm_call(self, prompt_text: str) -> None:
        self.llm_calls += 1
        self.input_tokens += count_tokens(prompt_text)
        if self.llm_calls > self.max_llm_calls:
            raise BudgetExceededError(
                f"LLM call budget exceeded: {self.llm_calls} > {self.max_llm_calls}"
            )
        if self.input_tokens > self.max_input_tokens:
            raise BudgetExceededError(
                f"Input token budget exceeded: {self.input_tokens} > {self.max_input_tokens}"
            )
