"""Tests for the frozen hidden question set: integrity checks, and that the
evaluator actually sources hidden runs from the frozen module (not JSON) and
redacts question text from anything written to disk.

Run from scripts/: `pytest evaluation/tests/test_frozen_hidden.py -q`
"""
import hashlib
import json
import pathlib
from pathlib import Path

import pytest

from evaluation import evaluator, hidden
from evaluation.leaderboard import write_results


def test_no_plaintext_hidden_questions_committed():
    """The plaintext hidden question set must never live outside the gitignored private/ dir."""
    tracked_root = Path(__file__).resolve().parents[1]
    leaked = [p for p in tracked_root.rglob("hidden_questions.json") if "private" not in p.parts]
    assert leaked == [], f"Plaintext hidden questions found outside private/: {leaked}"


def test_integrity_check_rejects_tampered_module(monkeypatch):
    class _Tampered:
        QUESTIONS = [{"id": "x", "question": "q", "gold_answer": "a", "gold_sources": []}]
        QUESTIONS_SHA256 = "0" * 64
        QUESTION_COUNT = 1

    monkeypatch.setattr(hidden, "_import_frozen", lambda: _Tampered)
    with pytest.raises(RuntimeError, match="integrity"):
        hidden.load_hidden_questions()


def _frozen_available() -> bool:
    try:
        hidden.load_hidden_questions()
        return True
    except RuntimeError:
        return False


requires_frozen_module = pytest.mark.skipif(
    not _frozen_available(),
    reason="frozen hidden module not built; run `python -m evaluation.tools.build_hidden`",
)


@requires_frozen_module
def test_hidden_fingerprint_matches_loaded_questions():
    questions = hidden.load_hidden_questions()
    fingerprint = hidden.hidden_fingerprint()
    assert fingerprint["count"] == len(questions)
    canonical = json.dumps(questions, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert fingerprint["sha256"] == hashlib.sha256(canonical).hexdigest()


@requires_frozen_module
def test_resolve_questions_hidden_never_reads_a_json_file(monkeypatch):
    """`--questions hidden` must come from the frozen module, never from a path read."""
    monkeypatch.setattr(pathlib.Path, "read_bytes", lambda self: (_ for _ in ()).throw(AssertionError("must not read a file for the hidden set")))
    questions, fingerprint, redact = evaluator.resolve_questions("hidden")
    assert redact is True
    assert fingerprint == hidden.hidden_fingerprint()
    assert len(questions) == fingerprint["count"]


def test_redact_results_masks_question_and_gold_answer_only():
    results = {
        "team-a": {
            "per_question": [
                {"id": "hid-01", "question": "secret?", "gold_answer": "secret answer", "candidate_answer": "kept"}
            ],
            "average": {},
            "by_category": {},
            "final_score_pct": 0.0,
        }
    }
    redacted = evaluator.redact_results(results)
    row = redacted["team-a"]["per_question"][0]
    assert row["question"] != "secret?"
    assert row["gold_answer"] != "secret answer"
    assert row["candidate_answer"] == "kept"
    assert row["id"] == "hid-01"


@requires_frozen_module
def test_hidden_run_output_is_fingerprinted_and_redacted(tmp_path):
    """End-to-end: the fingerprint stamped in results.json is the one that verifies
    the questions actually used, while the questions themselves never reach disk."""
    questions, fingerprint, redact = evaluator.resolve_questions("hidden")
    fake_scores = {"correctness": 0.0, "retrieval": 0.0, "groundedness": 0.0, "citations": 0.0, "latency": 0.0, "weighted_total": 0.0}
    results = {
        "team-a": {
            "per_question": [
                {"id": q["id"], "category": q.get("category"), "question": q["question"], "gold_answer": q["gold_answer"], "scores": fake_scores}
                for q in questions
            ],
            "average": fake_scores,
            "by_category": {},
            "final_score_pct": 0.0,
        }
    }
    write_results(evaluator.redact_results(results) if redact else results, tmp_path, {"run_id": "test", "question_set": fingerprint})

    payload = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert payload["meta"]["question_set"] == hidden.hidden_fingerprint()
    for row in payload["teams"]["team-a"]["per_question"]:
        assert "secret" not in row["question"].lower()
        assert row["question"] == "<redacted: hidden question set>"
        assert row["gold_answer"] == "<redacted: hidden question set>"
