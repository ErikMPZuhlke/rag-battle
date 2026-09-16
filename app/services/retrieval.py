"""Baseline retrieval: plain vector similarity search over the Chroma index."""
import chromadb

from app.core.budget import Budget
from app.core.config import settings

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        _collection = _client.get_collection(settings.chroma_collection)
    return _collection


def reset_collection_cache() -> None:
    """Drop the cached client/collection so the next call reopens the index."""
    global _client, _collection
    _client = None
    _collection = None


def retrieve(question: str, budget: Budget, top_k: int = settings.top_k) -> list[dict]:
    """Return the top-k most similar chunks for the question."""
    budget.use_retrieval(1)
    collection = get_collection()
    result = collection.query(query_texts=[question], n_results=top_k)

    chunks = []
    for text, meta, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        chunks.append(
            {
                "text": text,
                "document": meta["document"],
                "section": meta.get("section") or None,
                "distance": distance,
            }
        )
    return chunks
