"""Baseline generation: naive context-stuffing prompt + Groq chat completion."""
import time

from openai import OpenAI, RateLimitError

from app.core.budget import Budget
from app.core.config import settings

_client = None


class LLMRateLimitedError(RuntimeError):
    """Groq kept rate-limiting us past the bounded retry window; callers may retry later."""

    def __init__(self, retry_after: float):
        super().__init__(f"LLM rate limited; retry after {retry_after:.0f}s")
        self.retry_after = retry_after

_SYSTEM_PROMPT = (
    "You are an internal knowledge assistant for Acme Cloud. Answer the "
    "question using ONLY the provided context. If the context does not "
    f"contain the answer, respond exactly with: \"{settings.no_answer_text}\". "
    "Do not invent information. Be concise."
)


def get_client() -> OpenAI:
    global _client
    if _client is None:
        # max_retries=0: generate_answer owns the retry timing so it stays within the wait cap.
        _client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url, max_retries=0)
    return _client


def _retry_after_seconds(exc: RateLimitError, attempt: int) -> float:
    response = getattr(exc, "response", None)
    try:
        return float(response.headers.get("retry-after", "")) + 0.5
    except (AttributeError, ValueError):
        return float(min(2 ** attempt, 8))


def _format_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        label = c["document"] + (f" ({c['section']})" if c.get("section") else "")
        parts.append(f"[{i}] Source: {label}\n{c['text']}")
    return "\n\n".join(parts)


def generate_answer(question: str, chunks: list[dict], budget: Budget) -> str:
    context = _format_context(chunks)
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    budget.use_llm_call(_SYSTEM_PROMPT + user_prompt)

    # A 429 produced no tokens, so retries of the same logical call stay one budget charge.
    waited = 0.0
    for attempt in range(settings.groq_max_retries + 1):
        try:
            response = get_client().chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            break
        except RateLimitError as exc:
            wait = _retry_after_seconds(exc, attempt)
            if attempt == settings.groq_max_retries or waited + wait > settings.groq_max_retry_wait_s:
                raise LLMRateLimitedError(wait) from exc
            time.sleep(wait)
            waited += wait
    return response.choices[0].message.content.strip()
