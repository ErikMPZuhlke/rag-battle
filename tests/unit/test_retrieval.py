"""retrieve() chunk mapping and budget enforcement, with Chroma mocked out."""
import pytest

from app.services import retrieval
from app.core.budget import Budget, BudgetExceededError


class _FakeCollection:
    def __init__(self, result):
        self._result = result
        self.last_call = None

    def query(self, query_texts, n_results):
        self.last_call = (query_texts, n_results)
        return self._result


def test_retrieve_maps_chunks_and_falls_back_section_to_none(monkeypatch):
    fake_result = {
        "documents": [["chunk one", "chunk two"]],
        "metadatas": [[{"document": "a.md", "section": "Intro"}, {"document": "b.md", "section": ""}]],
        "distances": [[0.1, 0.2]],
    }
    fake_collection = _FakeCollection(fake_result)
    monkeypatch.setattr(retrieval, "get_collection", lambda: fake_collection)

    budget = Budget()
    chunks = retrieval.retrieve("what?", budget, top_k=2)

    assert chunks[0] == {"text": "chunk one", "document": "a.md", "section": "Intro", "distance": 0.1}
    assert chunks[1]["section"] is None
    assert budget.retrievals == 1
    assert fake_collection.last_call == (["what?"], 2)


def test_retrieve_raises_when_retrieval_budget_exhausted(monkeypatch):
    def _unexpected_call():
        raise AssertionError("should not query Chroma when the budget is already exhausted")

    monkeypatch.setattr(retrieval, "get_collection", _unexpected_call)
    budget = Budget(max_retrievals=0)

    with pytest.raises(BudgetExceededError):
        retrieval.retrieve("what?", budget)
