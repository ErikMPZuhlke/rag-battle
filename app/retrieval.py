"""Baseline retrieval: plain vector similarity search over the Chroma index."""
import chromadb

from app.budget import Budget
from app.config import CHROMA_COLLECTION, CHROMA_PERSIST_DIR, TOP_K

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _client.get_collection(CHROMA_COLLECTION)
    return _collection


def retrieve(question: str, budget: Budget, top_k: int = TOP_K) -> list[dict]:
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
