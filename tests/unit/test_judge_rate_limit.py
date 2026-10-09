"""Judge throttling (Groq rate-limit headers, retry-after) and the on-disk score cache,
with the Groq client faked out."""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".github" / "skills" / "rag-eval-report" / "scripts"))

import httpx
import pytest
from openai import RateLimitError

from evaluation import judge


def _raw(score: str, remaining="8000", reset="1s"):
    headers = {"x-ratelimit-remaining-tokens": remaining, "x-ratelimit-reset-tokens": reset}
    parsed = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=score))])
    return SimpleNamespace(headers=headers, parse=lambda: parsed)


def _rate_limit_error(retry_after: str | None, message: str = "rate limited"):
    headers = {"retry-after": retry_after} if retry_after else {}
    response = httpx.Response(429, headers=headers, request=httpx.Request("POST", "http://x"))
    return RateLimitError(message, response=response, body=None)


_TPD_MESSAGE = (
    "Error code: 429 - Rate limit reached for model `openai/gpt-oss-20b` on tokens per day (TPD): "
    "Limit 200000, Used 198333, Requested 1970. Please try again in 2m10.896s."
)


class _FakeClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0
        create = self._create
        self.chat = SimpleNamespace(completions=SimpleNamespace(with_raw_response=SimpleNamespace(create=create)))

    def _create(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(judge, "_CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(judge, "_cache", None)
    monkeypatch.setattr(judge, "_cache_enabled", True)
    monkeypatch.setattr(judge, "_rate_state", {"remaining_tokens": None, "reset_at": 0.0})
    sleeps = []
    monkeypatch.setattr(judge.time, "sleep", sleeps.append)
    return sleeps


def _use_client(monkeypatch, client):
    monkeypatch.setattr(judge, "get_client", lambda: client)


def test_parse_duration_handles_groq_formats():
    assert judge._parse_duration("7.66s") == pytest.approx(7.66)
    assert judge._parse_duration("2m59.56s") == pytest.approx(179.56)
    assert judge._parse_duration("120ms") == pytest.approx(0.12)
    assert judge._parse_duration("12") == 12.0
    assert judge._parse_duration(None) is None


def test_429_honors_retry_after_header_then_succeeds(monkeypatch, _isolated):
    client = _FakeClient([_rate_limit_error("7"), _raw("1")])
    _use_client(monkeypatch, client)

    assert judge._judge_score("sys", "user") == 1.0
    assert client.calls == 2
    assert _isolated == [7.5]


def test_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr(judge, "_MAX_RATE_LIMIT_RETRIES", 2)
    client = _FakeClient([_rate_limit_error("1")] * 3)
    _use_client(monkeypatch, client)

    with pytest.raises(judge.RateLimitStop):
        judge._judge_score("sys", "user")

    assert client.calls == 3


def test_daily_quota_stops_immediately_without_waiting(monkeypatch, _isolated):
    client = _FakeClient([_rate_limit_error(None, _TPD_MESSAGE), _raw("1")])
    _use_client(monkeypatch, client)

    with pytest.raises(judge.RateLimitStop) as info:
        judge._judge_score("sys", "user")

    assert client.calls == 1
    assert _isolated == []
    assert "daily" in info.value.reason
    assert info.value.retry_after == pytest.approx(130.896)


def test_message_hint_with_minutes_is_parsed_fully(monkeypatch, _isolated):
    monkeypatch.setattr(judge, "_MAX_WAIT_SECONDS", 300.0)
    client = _FakeClient([_rate_limit_error(None, "Please try again in 1m2.5s."), _raw("1")])
    _use_client(monkeypatch, client)

    assert judge._judge_score("sys", "user") == 1.0
    assert _isolated == [pytest.approx(63.0)]


def test_waits_for_token_refill_when_headers_show_low_budget(monkeypatch, _isolated):
    clock = [100.0]
    monkeypatch.setattr(judge.time, "monotonic", lambda: clock[0])
    client = _FakeClient([_raw("1", remaining="10", reset="20s"), _raw("0.5")])
    _use_client(monkeypatch, client)

    judge._judge_score("sys", "first")
    judge._judge_score("sys", "second")

    assert _isolated == [pytest.approx(20.25)]


def test_no_wait_when_budget_is_sufficient(monkeypatch, _isolated):
    client = _FakeClient([_raw("1", remaining="8000", reset="20s"), _raw("1")])
    _use_client(monkeypatch, client)

    judge._judge_score("sys", "first")
    judge._judge_score("sys", "second")

    assert _isolated == []


def test_cache_hit_skips_the_client(monkeypatch):
    client = _FakeClient([_raw("0.5")])
    _use_client(monkeypatch, client)

    assert judge._judge_score("sys", "user") == 0.5
    assert judge._judge_score("sys", "user") == 0.5

    assert client.calls == 1
    assert judge._CACHE_PATH.exists()
    assert "user" not in judge._CACHE_PATH.read_text(encoding="utf-8")


def test_cache_can_be_disabled(monkeypatch):
    judge.set_cache_enabled(False)
    client = _FakeClient([_raw("1"), _raw("1")])
    _use_client(monkeypatch, client)

    judge._judge_score("sys", "user")
    judge._judge_score("sys", "user")

    assert client.calls == 2
    assert not judge._CACHE_PATH.exists()


def test_unparseable_reply_scores_zero_and_is_not_cached(monkeypatch):
    client = _FakeClient([_raw(""), _raw("1")])
    _use_client(monkeypatch, client)

    assert judge._judge_score("sys", "user") == 0.0
    assert judge._judge_score("sys", "user") == 1.0
    assert client.calls == 2
