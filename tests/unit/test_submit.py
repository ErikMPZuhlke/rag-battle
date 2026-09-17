"""Tests for the leaderboard submission client: env validation, dry-run,
retry-on-transient-failure, and non-retryable rejection handling.

Run from the repo root: `pytest tests/unit/test_submit.py -q`
"""
import json
import sys
from pathlib import Path

# The `evaluation` package lives in the rag-eval-report skill, not under `app`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".github" / "skills" / "rag-eval-report" / "scripts"))

import httpx
import pytest

from evaluation import submit


@pytest.fixture
def results_path(tmp_path) -> Path:
    path = tmp_path / "results.json"
    path.write_text(json.dumps({"meta": {"run_id": "r1"}, "teams": {"team-a": {}}}), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Retries would otherwise slow the suite down for no reason."""
    monkeypatch.setattr(submit.time, "sleep", lambda _seconds: None)


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("LEADERBOARD_SUBMIT_URL", "https://leaderboard.example")
    monkeypatch.setenv("LEADERBOARD_SUBMIT_TOKEN", "secret-token")


def test_missing_url_env_raises(results_path, monkeypatch):
    monkeypatch.delenv("LEADERBOARD_SUBMIT_URL", raising=False)
    monkeypatch.delenv("LEADERBOARD_SUBMIT_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="LEADERBOARD_SUBMIT_URL"):
        submit.submit_results(results_path)


def test_dry_run_never_touches_the_network(results_path, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise AssertionError("dry-run must not perform a network request")

    monkeypatch.setattr(httpx, "post", _boom)
    assert submit.submit_results(results_path, dry_run=True) is None


def test_202_returns_parsed_response(results_path, env, monkeypatch):
    monkeypatch.setattr(
        httpx, "post", lambda *a, **k: httpx.Response(202, json={"status": "accepted"})
    )
    result = submit.submit_results(results_path)
    assert result == {"status": "accepted"}


def test_posts_expected_url_headers_and_body(results_path, env, monkeypatch):
    captured = {}

    def _fake_post(url, content, headers, timeout):
        captured.update(url=url, content=content, headers=headers, timeout=timeout)
        return httpx.Response(202, json={"status": "accepted"})

    monkeypatch.setattr(httpx, "post", _fake_post)
    submit.submit_results(results_path)

    assert captured["url"] == "https://leaderboard.example/submit"
    assert captured["headers"]["X-Submit-Token"] == "secret-token"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert json.loads(captured["content"]) == json.loads(results_path.read_text(encoding="utf-8"))


def test_retries_on_429_then_succeeds(results_path, env, monkeypatch):
    responses = iter([
        httpx.Response(429, json={"reason": "rate_limited"}, headers={"Retry-After": "1"}),
        httpx.Response(202, json={"status": "accepted"}),
    ])
    calls = []

    def _fake_post(*_a, **_k):
        calls.append(1)
        return next(responses)

    monkeypatch.setattr(httpx, "post", _fake_post)
    result = submit.submit_results(results_path)
    assert result == {"status": "accepted"}
    assert len(calls) == 2


def test_exhausts_retries_on_persistent_503(results_path, env, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(503))
    with pytest.raises(submit.SubmissionError, match="503"):
        submit.submit_results(results_path)


def test_400_rejection_raises_immediately_without_retry(results_path, env, monkeypatch):
    calls = []

    def _fake_post(*_a, **_k):
        calls.append(1)
        return httpx.Response(400, json={"reason": "invalid_payload"})

    monkeypatch.setattr(httpx, "post", _fake_post)
    with pytest.raises(submit.SubmissionError, match="invalid_payload"):
        submit.submit_results(results_path)
    assert len(calls) == 1


def test_401_rejection_raises_without_retry(results_path, env, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(401, json={"reason": "unauthorized"}))
    with pytest.raises(submit.SubmissionError, match="unauthorized"):
        submit.submit_results(results_path)
