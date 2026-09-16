# RAG Battle Royale — Project Guidelines

## Architecture

FastAPI app (`app/main.py`, via `create_app()`) implementing a single `POST /ask`
contract: `{"question": ...}` → `{"answer": ..., "sources": [{"document", "section"}]}`.
Layout: `app/api/routes/` (FastAPI routers, e.g. `ask.py`, `health.py`) →
`app/services/` (`retrieval.py` vector search, `generation.py` prompts the Groq
LLM, `ingest.py` chunk + embed corpus into Chroma) → `app/core/` (`config.py`
`Settings`, `budget.py` budget guard) → `app/schemas/` (`ask.py` Pydantic
request/response schema). See [README.md](../README.md) for the full repo
layout and API contract.

## Per-question budget (hard constraint)

Every `/ask` request is metered by `app/core/budget.py` via a `Budget` object passed
into `retrieve()` and `generate_answer()`: max 3 LLM calls, 10 retrievals,
4,000 input tokens. Exceeding any limit raises `BudgetExceededError` → HTTP 429.
Any change to retrieval/generation must call `budget.use_retrieval()` /
`budget.use_llm_call()` accordingly — don't bypass the budget object.

## Rules (see [docs/PARTICIPANT_RULES.md](../docs/PARTICIPANT_RULES.md))

- Never modify files under `data/knowledge-base/` — that's the shared corpus.
- Never hard-code answers to specific questions or read the hidden eval set.
- Don't send the entire corpus to the LLM on every request.
- If the corpus doesn't contain the answer, return `settings.no_answer_text`
  ("The documentation does not specify this.") rather than inventing one —
  hallucinations are penalized heavily in scoring.
- Keep the `POST /ask` contract stable even if the internals are rewritten.

## Build and Test

- Ingest corpus (rebuild local vector index): `python -m app.services.ingest` (task: "Ingest corpus")
- Run API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (task: "Run API")
- Run tests: `pytest -q` (task: "Run tests")
- Requires `GROQ_API_KEY` set in `.env` (copy from `.env.example`).
