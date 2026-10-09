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


def test_call_team_stops_run_after_max_retries(monkeypatch, sleeps):
    _script_posts(monkeypatch, [_response(503, {"retry-after": "7"})] * 3)

    with pytest.raises(evaluator.RateLimitStop) as info:
        evaluator.call_team("http://x", "q?", max_retries=2)

    assert len(sleeps) == 2
    assert "503" in info.value.reason
    assert info.value.retry_after == 7.0


def test_call_team_stops_immediately_when_retry_after_exceeds_cap(monkeypatch, sleeps):
    _script_posts(monkeypatch, [_response(503, {"retry-after": "437"})])

    with pytest.raises(evaluator.RateLimitStop) as info:
        evaluator.call_team("http://x", "q?")

    assert sleeps == []
    assert info.value.retry_after == 437.0


def test_call_team_records_non_transient_errors(monkeypatch, sleeps):
    _script_posts(monkeypatch, [_response(500)])

    result = evaluator.call_team("http://x", "q?")

    assert result["error"] is not None
    assert sleeps == []


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


_QUESTIONS = [{"id": "a", "question": "qa", "gold_answer": "ga", "gold_sources": []}]


@pytest.fixture
def cli(monkeypatch, tmp_path):
    """Runs evaluator.main() as a hidden run in tmp_path; returns a callable taking extra argv."""
    monkeypatch.setenv("GROQ_API_KEY", "test")
    monkeypatch.setattr(evaluator, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        evaluator, "resolve_questions", lambda arg: (_QUESTIONS, {"name": "hidden", "sha256": "x", "count": 1}, True)
    )

    def _run(*argv):
        monkeypatch.setattr(sys, "argv", ["evaluator", "--team", "t", *argv])
        evaluator.main()

    return _run


def _raise(exc):
    def _fn(*a, **k):
        raise exc
    return _fn


def test_main_rate_limit_exits_75_without_traceback(monkeypatch, cli, capsys):
    monkeypatch.setattr(evaluator, "run_evaluation", _raise(evaluator.RateLimitStop("Groq daily token quota reached", 131)))

    with pytest.raises(SystemExit) as info:
        cli()

    assert info.value.code == evaluator.EXIT_RATE_LIMITED
    err = capsys.readouterr().err
    assert "Groq daily token quota reached. Try again in ~2m11s." in err
    assert "--resume" in err
    assert "Traceback" not in err


def test_main_unexpected_error_exits_1_without_traceback(monkeypatch, cli, capsys):
    monkeypatch.setattr(evaluator, "run_evaluation", _raise(ValueError("boom\nmore detail")))

    with pytest.raises(SystemExit) as info:
        cli()

    assert info.value.code == 1
    err = capsys.readouterr().err
    assert "Run failed: ValueError: boom" in err
    assert "more detail" not in err
    assert "Traceback" not in err


def test_main_debug_prints_traceback(monkeypatch, cli, capsys):
    monkeypatch.setattr(evaluator, "run_evaluation", _raise(ValueError("boom")))

    with pytest.raises(SystemExit):
        cli("--debug")

    assert "Traceback" in capsys.readouterr().err


def test_main_does_not_submit_hidden_run_with_errored_questions(monkeypatch, cli, capsys):
    record = {
        "id": "a", "category": None, "question": "qa", "gold_answer": "ga", "candidate_answer": "",
        "returned_documents": [], "latency_seconds": 0.1, "error": "500 Server Error",
        "scores": {m: 0.0 for m in evaluator._METRICS},
    }
    results = {"t": {"per_question": [record], "average": record["scores"], "by_category": {}, "final_score_pct": 0.0}}
    monkeypatch.setattr(evaluator, "run_evaluation", lambda *a, **k: results)
    monkeypatch.setattr(evaluator, "write_results", lambda *a, **k: None)
    monkeypatch.setattr(evaluator, "write_html_report", lambda *a, **k: "report.html")
    submitted = []
    monkeypatch.setattr(evaluator, "submit_results", lambda *a, **k: submitted.append(a))

    with pytest.raises(SystemExit) as info:
        cli()

    assert info.value.code == 1
    assert submitted == []
    assert "Not submitting" in capsys.readouterr().err
