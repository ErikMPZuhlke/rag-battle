"""Baseline ingestion: naive fixed-size chunking + Chroma (local embeddings).

Intentionally coarse — chunk boundaries ignore markdown structure. This is a
starting point for teams to improve (respect headers, add overlap, add
metadata, switch chunking strategy, etc.).
"""
import re
from pathlib import Path

import chromadb

from app.core.config import settings

_HEADER_RE = re.compile(r"^#{1,6}\s+(.*)$")


def _chunk_text(text: str, chunk_size: int) -> list[tuple[str, str]]:
    """Split text into fixed-size chunks, each tagged with the last markdown
    header seen before it started (best-effort "section" label)."""
    lines = text.splitlines()
    chunks: list[tuple[str, str]] = []
    current_section = ""
    buffer: list[str] = []
    buffer_len = 0

    def flush():
        if buffer:
            chunks.append(("\n".join(buffer).strip(), current_section))

    for line in lines:
        header_match = _HEADER_RE.match(line.strip())
        if header_match:
            current_section = header_match.group(1).strip()
        buffer.append(line)
        buffer_len += len(line) + 1
        if buffer_len >= chunk_size:
            flush()
            buffer = []
            buffer_len = 0
    flush()

    return [(c, s) for c, s in chunks if c]


def load_documents(kb_dir: str = settings.knowledge_base_dir) -> list[dict]:
    """Walk the knowledge base directory and return chunk records."""
    records = []
    base = Path(kb_dir)
    for path in sorted(base.rglob("*.md")):
        relative = path.relative_to(base).as_posix()
        text = path.read_text(encoding="utf-8")
        for i, (chunk, section) in enumerate(_chunk_text(text, settings.chunk_size_chars)):
            records.append(
                {
                    "id": f"{relative}::{i}",
                    "text": chunk,
                    "document": relative,
                    "section": section,
                }
            )
    return records


def build_index(kb_dir: str = settings.knowledge_base_dir, persist_dir: str = settings.chroma_persist_dir) -> int:
    """Ingest the knowledge base into a persistent Chroma collection."""
    client = chromadb.PersistentClient(path=persist_dir)
    client.delete_collection(settings.chroma_collection) if settings.chroma_collection in [
        c.name for c in client.list_collections()
    ] else None
    collection = client.create_collection(settings.chroma_collection)

    records = load_documents(kb_dir)
    if not records:
        raise RuntimeError(f"No documents found under {kb_dir}")

    collection.add(
        ids=[r["id"] for r in records],
        documents=[r["text"] for r in records],
        metadatas=[{"document": r["document"], "section": r["section"]} for r in records],
    )
    return len(records)


if __name__ == "__main__":
    count = build_index()
    print(f"Ingested {count} chunks into Chroma collection '{settings.chroma_collection}' at {settings.chroma_persist_dir}")
