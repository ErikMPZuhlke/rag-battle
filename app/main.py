"""FastAPI application factory exposing the RAG API."""
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api import api_router

DESCRIPTION = (
    "Acme Cloud internal knowledge assistant. Ask natural-language questions "
    "against the knowledge base (`/ask`), inspect raw retrieval results "
    "(`/retrieve`), or rebuild the vector index (`/ingest`)."
)

TAGS_METADATA = [
    {"name": "ask", "description": "Retrieve context and generate a grounded answer."},
    {"name": "retrieve", "description": "Vector search only — returns matching chunks without calling the LLM."},
    {"name": "ingest", "description": "Rebuild the Chroma index from the knowledge base corpus."},
    {"name": "health", "description": "Liveness probe."},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Acme Cloud Knowledge Assistant",
        description=DESCRIPTION,
        version="1.0.0",
        openapi_tags=TAGS_METADATA,
    )
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
