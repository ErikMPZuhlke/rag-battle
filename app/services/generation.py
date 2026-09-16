"""Baseline generation: naive context-stuffing prompt + Groq chat completion."""
from openai import OpenAI

from app.core.budget import Budget
from app.core.config import settings

_client = None

_SYSTEM_PROMPT = (
    "You are an internal knowledge assistant for Acme Cloud. Answer the "
    "question using ONLY the provided context. If the context does not "
    f"contain the answer, respond exactly with: \"{settings.no_answer_text}\". "
    "Do not invent information. Be concise."
)


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
    return _client


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

    response = get_client().chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()
