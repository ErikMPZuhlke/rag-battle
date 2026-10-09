"""Evaluator resilience: /ask retries, checkpoint loading, and hidden-set redaction in checkpoints."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".github" / "skills" / "rag-eval-report" / "scripts"))

import httpx
import pytest

from evaluation import evaluator

_OK_BODY = {"answer": "a", "sources": [{"document": "d.md", "section": "S"}]}


def _response(status: int, headers: dict | None = None, body: dict | None = None) -> httpx.Response:
    return httpx.Response(status, headers=headers or {}, json=body or {}, request=httpx.Request("POST", "http://x/ask"))


@pytest.fixture
def sleeps(monkeypatch):
    recorded = []
    monkeypatch.setattr(evaluator.time, "sleep", recorded.append)
    return recorded


def _script_posts(monkeypatch, responses):
    queue = list(responses)
    monkeypatch.setattr(evaluator.httpx, "post", lambda *a, **k: queue.pop(0))


def test_call_team_retries_503_honoring_retry_after(monkeypatch, sleeps):
    _script_posts(monkeypatch, [_response(503, {"retry-after": "3"}), _response(200, body=_OK_BODY)])

    result = evaluator.call_team("http://x", "q?")

    assert result["error"] is None
    assert result["answer"] == "a"
    assert result["attempts"] == 2
    assert sleeps == [3.5]


def test_call_team_does_not_retry_bare_429_budget_error(monkeypatch, sleeps):
    _script_posts(monkeypatch, [_response(429)])

    result = evaluator.call_team("http://x", "q?")

    assert result["error"] is not None
    assert result["attempts"] == 1
    assert sleeps == []


def test_call_team_retries_429_with_retry_after(monkeypatch, sleeps):
    _script_posts(monkeypatch, [_response(429, {"retry-after": "1"}), _response(200, body=_OK_BODY)])

    assert evaluator.call_team("http://x", "q?")["attempts"] == 2


def test_call_team_gives_up_after_max_retries(monkeypatch, sleeps):
    _script_posts(monkeypatch, [_response(503, {"retry-after": "1"})] * 3)

    result = evaluator.call_team("http://x", "q?", max_retries=2)

    assert result["error"] is not None
    assert result["attempts"] == 3


def test_load_checkpoint_drops_errored_and_keeps_latest(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    lines = [
        {"id": "a", "error": "boom", "scores": {}},
        {"id": "a", "error": None, "scores": {"weighted_total": 1.0}},
        {"id": "b", "error": "boom", "scores": {}},
    ]
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")

    done = evaluator.load_checkpoint(path)

    assert set(done) == {"a"}
    assert done["a"]["scores"]["weighted_total"] == 1.0


def test_load_checkpoint_missing_file_is_empty(tmp_path):
    assert evaluator.load_checkpoint(tmp_path / "nope.jsonl") == {}


def test_run_evaluation_skips_done_questions_and_emits_new_results(monkeypatch):
    questions = [
        {"id": "a", "question": "qa", "gold_answer": "ga", "gold_sources": []},
        {"id": "b", "question": "qb", "gold_answer": "gb", "gold_sources": []},
    ]
    asked = []

    def _fake_call(base_url, question, timeout, max_retries):
        asked.append(question)
        return {"answer": "x", "sources": [], "latency": 0.1, "error": None, "attempts": 1}

    monkeypatch.setattr(evaluator, "call_team", _fake_call)
    monkeypatch.setattr(
        evaluator, "score_question", lambda **kw: {m: 1.0 for m in evaluator._METRICS}
    )
    done_record = {
        "id": "a", "category": None, "question": "qa", "gold_answer": "ga", "candidate_answer": "x",
        "returned_documents": [], "latency_seconds": 0.1, "error": None,
        "scores": {m: 0.5 for m in evaluator._METRICS},
    }
    emitted = []

    results = evaluator.run_evaluation(
        questions, "team", "http://x", done={"a": done_record}, on_result=emitted.append
    )

    assert asked == ["qb"]
    assert [r["id"] for r in emitted] == ["b"]
    assert [r["id"] for r in results["team"]["per_question"]] == ["a", "b"]
    assert results["team"]["average"]["weighted_total"] == pytest.approx(0.75)


def test_redact_record_strips_question_and_gold():
    redacted = evaluator._redact_record({"id": "a", "question": "secret?", "gold_answer": "secret!", "scores": {}})

    assert "secret" not in json.dumps(redacted)
    assert redacted["id"] == "a"
