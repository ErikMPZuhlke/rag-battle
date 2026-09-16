# 🏆 RAG Battle Royale — Participant Rules

**Duration:** 90 minutes build + 30 minutes evaluation/reveal

## You get

- The same Acme Cloud knowledge base (`data/knowledge-base/`) as every other team
- The same baseline RAG implementation (`app/`)
- The same `POST /ask` API contract
- The same per-question resource budget
- The same public training questions (`.github/skills/rag-eval-report/scripts/evaluation/public_questions.json`)

## You may modify

- Chunking, embeddings, retrieval, top-k, metadata, filtering
- Hybrid search, reranking, query rewriting, context compression
- Prompts, context formatting, answer generation, citation strategy
- Caching
- You may replace the baseline architecture entirely, as long as `POST /ask`
  still returns `{ "answer": ..., "sources": [...] }`.

## You may not

- Modify anything under `data/knowledge-base/`
- Access or attempt to guess the hidden evaluation questions
- Hard-code answers to specific questions
- Call an external service that directly answers the question (e.g. a general
  web search API used to just answer the question instead of using your RAG)
- Send the entire corpus to the LLM on every request
- Collaborate with other teams during the battle

## Per-question budget

Enforced by `app/budget.py` (`BudgetExceededError` → HTTP 429):

- Max **3 LLM calls** per question
- Max **10 retrieval operations** per question
- Max **4,000 input tokens** per question

If you change the budget enforcement itself, you're expected to still stay
within the spirit of these limits — the goal is to force real engineering
trade-offs, not to spend unlimited tokens.

## Unknown information

If the knowledge base does not contain the answer, say so explicitly (e.g.
"The documentation does not specify this."). Inventing an answer is scored
as a hallucination and penalized heavily.

## Scoring

| Category | Weight |
|---|---|
| Answer correctness | 50% |
| Retrieval quality | 20% |
| Groundedness | 15% |
| Citations | 10% |
| Latency | 5% |

## Winner

The team with the highest score on the hidden evaluation set.
