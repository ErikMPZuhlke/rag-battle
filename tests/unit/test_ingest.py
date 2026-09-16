"""Chunking + document loading are pure/local I/O; the Chroma client is mocked
out for build_index so this suite never touches a real vector index."""
import pytest

from app.services import ingest


def test_chunk_text_tracks_the_last_header_seen():
    text = "# Intro\nline one\n" + ("x" * 20 + "\n") * 3 + "## Details\nmore text\n"
    chunks = ingest._chunk_text(text, chunk_size=30)
    assert chunks[0][1] == "Intro"
    assert any(section == "Details" for _, section in chunks)


def test_chunk_text_with_no_header_yields_empty_section():
    chunks = ingest._chunk_text("just a paragraph with no headers at all", chunk_size=1000)
    assert len(chunks) == 1
    text, section = chunks[0]
    assert section == ""
    assert "paragraph" in text


def test_load_documents_walks_markdown_files_recursively(tmp_path):
    (tmp_path / "a.md").write_text("# Title\nSome content here.\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.md").write_text("# Other\nMore content.\n", encoding="utf-8")

    records = ingest.load_documents(str(tmp_path))

    documents = {r["document"] for r in records}
    assert documents == {"a.md", "sub/b.md"}
    assert all(r["id"].startswith(r["document"] + "::") for r in records)


def test_build_index_raises_when_no_documents_found(tmp_path, monkeypatch):
    class _FakeClient:
        def list_collections(self):
            return []

        def create_collection(self, name):
            return object()

        def delete_collection(self, name):
            pass

    monkeypatch.setattr(ingest.chromadb, "PersistentClient", lambda path: _FakeClient())

    with pytest.raises(RuntimeError):
        ingest.build_index(kb_dir=str(tmp_path), persist_dir=str(tmp_path / ".chroma"))


def test_build_index_adds_every_chunk_to_the_collection(tmp_path, monkeypatch):
    (tmp_path / "a.md").write_text("# Title\nSome content here.\n", encoding="utf-8")
    added = {}

    class _FakeCollection:
        def add(self, ids, documents, metadatas):
            added["ids"] = ids
            added["documents"] = documents
            added["metadatas"] = metadatas

    class _FakeClient:
        def list_collections(self):
            return []

        def create_collection(self, name):
            return _FakeCollection()

        def delete_collection(self, name):
            pass

    monkeypatch.setattr(ingest.chromadb, "PersistentClient", lambda path: _FakeClient())

    count = ingest.build_index(kb_dir=str(tmp_path), persist_dir=str(tmp_path / ".chroma"))

    assert count == len(added["ids"]) == len(added["documents"]) == len(added["metadatas"])
