# RAG Battle Royale — Acme Cloud Knowledge Assistant

Starter kit for the "RAG Battle Royale" hackathon. Each team gets a copy of this
repo containing the same corpus, the same mediocre baseline RAG API, and the
same public test questions. Your goal: improve retrieval, prompting, and
answer quality to score as high as possible on a **hidden** evaluation set.

## Workshop docs

- [docs/WORKSHOP_BRIEF.md](docs/WORKSHOP_BRIEF.md) — mission, goal, and agenda
- [docs/PARTICIPANT_RULES.md](docs/PARTICIPANT_RULES.md) — full rules, budget, and scoring breakdown
- [docs/SLIDES_OUTLINE.md](docs/SLIDES_OUTLINE.md) — intro slide outline

## Setup

This project runs in a **VS Code Dev Container**, so the only prerequisites
are on your host machine — the container itself provides the runtime:

- [VS Code](https://code.visualstudio.com/)
- The [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Docker Desktop (or another Docker-compatible container engine)
- A free Groq API key from https://console.groq.com

Steps:

1. Open this folder in VS Code and choose **Reopen in Container**.
2. Copy `.env.example` to `.env` and set `GROQ_API_KEY`.
3. Run the **"Ingest corpus"** task (or `python -m app.ingest`) to build the
   local vector index.
4. Run the **"Run API"** task (or `uvicorn app.main:app --reload --port 8000`).
5. Test it:

   ```bash
   curl -s localhost:8000/ask -H "content-type: application/json" \
     -d '{"question":"Who can approve production deployments?"}'
   ```

## Repo layout

```
app/            baseline RAG implementation (ingest, retrieval, generation, API)
data/           Acme Cloud knowledge base (~40 markdown docs)
.github/skills/rag-eval-report/scripts/evaluation/  public_questions.json + evaluator/scoring/leaderboard/report (organizer)
docs/           participant rules, workshop brief
tests/          smoke tests for the API contract
```

## API contract

`POST /ask`

```json
{ "question": "What is the SLA for P1 incidents?" }
```

```json
{
  "answer": "...",
  "sources": [{ "document": "sla.md", "section": "P1 incidents" }]
}
```

See [docs/openapi.yaml](docs/openapi.yaml) for the full OpenAPI spec, including
the `GET /health` endpoint and error responses.

## Rules

See [docs/PARTICIPANT_RULES.md](docs/PARTICIPANT_RULES.md) before you start —
there's a per-question budget (3 LLM calls / 10 retrievals / 4,000 input
tokens) and a short list of things you may not do (e.g. modifying the corpus
or hard-coding answers).

## What you can change

Chunking, embeddings, retrieval, top-k, metadata, filtering, hybrid search,
reranking, query rewriting, context compression, prompts, citation strategy,
caching — anything in `app/`, as long as you keep the `POST /ask` contract and
stay within budget.
