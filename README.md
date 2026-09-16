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
3. Run the **"Ingest corpus"** task (or `python -m app.services.ingest`) to build the
   local vector index.
4. Run the **"Run API"** task (or `uvicorn app.main:app --reload --port 8000`) — this
   also opens the Swagger UI at `/docs` in VS Code's integrated browser once the
   server is up.
5. Test it — either through the Swagger UI, or:

   ```bash
   curl -s localhost:8000/ask -H "content-type: application/json" \
     -d '{"question":"Who can approve production deployments?"}'
   ```

## VS Code tasks

Available via **Terminal > Run Task...** (or `Tasks: Run Task` in the command palette):

| Task | Command | Purpose |
| --- | --- | --- |
| **Run API** | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | Starts the API, then opens the Swagger UI (`/docs`) in the integrated browser once it's ready. |
| **Ingest corpus** | `python -m app.services.ingest` | (Re)builds the local Chroma vector index from `data/knowledge-base/`. |
| **Run unit tests** | `pytest tests/unit -q` | Runs only the unit test suite (no running API required). |
| **Run integration tests** | `pytest tests/integration -q` | Runs only the integration suite against the `/ask` API contract. |
| **Run tests** | runs the two tasks above in sequence | Default test task (`Tasks: Run Test Task`) — the full suite. |

## API contract

The API surface is documented as an interactive Swagger UI at `GET /` (which
redirects to `/docs`; ReDoc is also available at `/redoc`).

`POST /ask` — retrieve context and generate a grounded answer:

```json
{ "question": "What is the SLA for P1 incidents?" }
```

```json
{
  "answer": "...",
  "sources": [{ "document": "sla.md", "section": "P1 incidents" }]
}
```

`POST /retrieve` — vector search only, no LLM call (useful for debugging
retrieval quality in isolation); accepts an optional `top_k` override and
returns the matching chunks with their similarity distance.

`POST /ingest` — rebuilds the Chroma index from the corpus, equivalent to
running `python -m app.services.ingest`.

`GET /health` — liveness probe.

The full OpenAPI spec (including error responses) is generated live from the
code — see it at `/docs` (Swagger UI), `/redoc`, or the raw `/openapi.json`.

## Configuration

Settings are loaded from environment variables (`.env` in local dev) via
`app/core/config.py`. See [.env.example](.env.example) for the full list,
including the Groq model/API key, Chroma persistence directory, retrieval
`TOP_K`, and the per-question budget limits below.

## Rules

See [docs/PARTICIPANT_RULES.md](docs/PARTICIPANT_RULES.md) before you start —
there's a per-question budget (3 LLM calls / 10 retrievals / 4,000 input
tokens) enforced by `app/core/budget.py`, and a short list of things you may
not do (e.g. modifying the corpus or hard-coding answers).

## What you can change

Chunking, embeddings, retrieval, top-k, metadata, filtering, hybrid search,
reranking, query rewriting, context compression, prompts, citation strategy,
caching — anything in `app/`, as long as you keep the `POST /ask` contract and
stay within budget.

