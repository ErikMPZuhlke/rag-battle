"""Thin wrapper around a Groq chat model used as an LLM judge for scoring.

Groq enforces a per-minute token limit shared by every caller on the same key
and model (including the app under test), so the judge reads Groq's
`x-ratelimit-*` headers and waits *before* hitting the limit, honors
`retry-after` when it does, and caches scores on disk so unchanged answers
are never re-judged.
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()

_JUDGE_API_KEY = os.getenv("GROQ_API_KEY", "")
_JUDGE_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
_JUDGE_MODEL = os.getenv("GROQ_JUDGE_MODEL", os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"))

_client = None

_VALID_SCORES = {"0": 0.0, "0.5": 0.5, "1": 1.0}
_MAX_RATE_LIMIT_RETRIES = int(os.getenv("JUDGE_MAX_RETRIES", "8"))
_MAX_WAIT_SECONDS = float(os.getenv("JUDGE_MAX_WAIT_S", "90"))
# Reasoning models spend hidden output tokens; reserve room for them in the pre-call estimate.
_OUTPUT_TOKEN_ESTIMATE = int(os.getenv("JUDGE_OUTPUT_TOKEN_ESTIMATE", "600"))
_RETRY_AFTER_RE = re.compile(r"try again in ((?:\d+(?:\.\d+)?(?:ms|h|m|s))+)", re.IGNORECASE)
_DAILY_LIMIT_RE = re.compile(r"per day \((?:TPD|RPD)\)", re.IGNORECASE)
_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")
_ANNOUNCE_WAIT_SECONDS = 5.0
_UNIT_SECONDS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}

_CACHE_PATH = Path(__file__).resolve().parent / "results" / ".judge_cache.json"
_cache: dict[str, float] | None = None
_cache_enabled = True

# Last-seen Groq token bucket: tokens left, and the monotonic time it refills.
_rate_state: dict[str, float | None] = {"remaining_tokens": None, "reset_at": 0.0}


class RateLimitStop(RuntimeError):
    """Rate limited past what's worth waiting out in-process; the run should stop and be resumed later."""

    def __init__(self, reason: str, retry_after: float | None = None):
        super().__init__(reason)
        self.reason = reason
        self.retry_after = retry_after


def get_client() -> OpenAI:
    global _client
    if _client is None:
        # max_retries=0: all waiting happens in _judge_score so it can honor the headers.
        _client = OpenAI(api_key=_JUDGE_API_KEY, base_url=_JUDGE_BASE_URL, max_retries=0)
    return _client


def set_cache_enabled(enabled: bool) -> None:
    global _cache_enabled
    _cache_enabled = enabled


def _cache_key(system_prompt: str, user_prompt: str) -> str:
    return hashlib.sha256(f"{_JUDGE_MODEL}\0{system_prompt}\0{user_prompt}".encode("utf-8")).hexdigest()


def _load_cache() -> dict[str, float]:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _cache_put(key: str, score: float) -> None:
    cache = _load_cache()
    cache[key] = score
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache), encoding="utf-8")
    tmp.replace(_CACHE_PATH)


def _parse_duration(value: str | None) -> float | None:
    """Parses Groq durations like '7.66s', '2m59.56s', '120ms', or a bare number of seconds."""
    if not value:
        return None
    parts = _DURATION_RE.findall(value)
    if parts:
        return sum(float(n) * _UNIT_SECONDS[unit] for n, unit in parts)
    try:
        return float(value)
    except ValueError:
        return None


def _record_rate_headers(headers) -> None:
    remaining = headers.get("x-ratelimit-remaining-tokens")
    reset = _parse_duration(headers.get("x-ratelimit-reset-tokens"))
    if remaining is None or reset is None:
        return
    try:
        _rate_state["remaining_tokens"] = float(remaining)
    except ValueError:
        return
    _rate_state["reset_at"] = time.monotonic() + reset


def _wait_for_token_budget(estimated_tokens: int) -> None:
    remaining = _rate_state["remaining_tokens"]
    if remaining is None:
        return
    now = time.monotonic()
    reset_at = _rate_state["reset_at"] or 0.0
    if now < reset_at and remaining < estimated_tokens:
        wait = min(reset_at - now + 0.25, _MAX_WAIT_SECONDS)
        if wait >= _ANNOUNCE_WAIT_SECONDS:
            print(f"  \u23F3 judge pacing for Groq token refill, waiting {wait:.0f}s", file=sys.stderr, flush=True)
        time.sleep(wait)
    # Either we waited for the refill or the snapshot is stale; don't trust it again.
    if now >= reset_at or remaining < estimated_tokens:
        _rate_state["remaining_tokens"] = None


def _retry_hint_seconds(exc: RateLimitError) -> float | None:
    """Groq's own wait hint: `retry-after` header, else 'try again in 2m10.9s' in the message."""
    response = getattr(exc, "response", None)
    header_wait = _parse_duration(response.headers.get("retry-after")) if response is not None else None
    if header_wait is not None:
        return header_wait
    match = _RETRY_AFTER_RE.search(str(exc))
    return _parse_duration(match.group(1)) if match else None


def _is_daily_limit(exc: RateLimitError) -> bool:
    return bool(_DAILY_LIMIT_RE.search(str(exc)))


def _rate_limit_wait_seconds(exc: RateLimitError, attempt: int) -> float:
    """Wait time for a 429: Groq's hint (plus a small safety margin), else backoff."""
    hint = _retry_hint_seconds(exc)
    if hint is not None:
        return min(max(hint, 0.5) + 0.5, _MAX_WAIT_SECONDS)
    return min(2 ** attempt, 30)


def _judge_score(system_prompt: str, user_prompt: str) -> float:
    """Call the judge model and parse a 0 / 0.5 / 1 score from its reply."""
    key = _cache_key(system_prompt, user_prompt)
    if _cache_enabled:
        cached = _load_cache().get(key)
        if cached is not None:
            return cached

    estimated_tokens = (len(system_prompt) + len(user_prompt)) // 4 + _OUTPUT_TOKEN_ESTIMATE
    for attempt in range(_MAX_RATE_LIMIT_RETRIES + 1):
        _wait_for_token_budget(estimated_tokens)
        try:
            raw = get_client().chat.completions.with_raw_response.create(
                model=_JUDGE_MODEL,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            break
        except RateLimitError as exc:
            _rate_state["remaining_tokens"] = None
            if _is_daily_limit(exc):
                # Daily quota refills slowly; waiting in-process just stalls the run.
                raise RateLimitStop("Groq daily token quota reached", _retry_hint_seconds(exc)) from exc
            wait = _rate_limit_wait_seconds(exc, attempt)
            if attempt == _MAX_RATE_LIMIT_RETRIES:
                raise RateLimitStop(
                    f"Groq rate limit persisted after {_MAX_RATE_LIMIT_RETRIES} judge retries", wait
                ) from exc
            print(
                f"  \u23F3 judge rate-limited, waiting {wait:.0f}s (retry {attempt + 1}/{_MAX_RATE_LIMIT_RETRIES})",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(wait)
    _record_rate_headers(raw.headers)
    text = (raw.parse().choices[0].message.content or "").strip()
    match = re.search(r"\b(0\.5|0|1)\b", text)
    if not match:
        # Unparseable reply (e.g. reasoning ate the output budget): score 0 but don't cache it.
        return 0.0
    score = _VALID_SCORES[match.group(1)]
    if _cache_enabled:
        _cache_put(key, score)
    return score


def judge_correctness(question: str, gold_answer: str, candidate_answer: str) -> float:
    system = (
        "You are grading answer correctness for a RAG evaluation. Compare the "
        "CANDIDATE answer to the GOLD answer for the given QUESTION. Reply with "
        "exactly one token: 0 (wrong), 0.5 (partially correct), or 1 (correct). "
        "No explanation."
    )
    user = f"QUESTION: {question}\n\nGOLD ANSWER: {gold_answer}\n\nCANDIDATE ANSWER: {candidate_answer}"
    return _judge_score(system, user)


def judge_groundedness(question: str, candidate_answer: str, context: str) -> float:
    system = (
        "You are grading groundedness for a RAG evaluation. Given the QUESTION, "
        "the retrieved CONTEXT, and the CANDIDATE answer, judge whether the "
        "candidate answer is supported by the context (not hallucinated). Reply "
        "with exactly one token: 0 (unsupported/contradicts context), "
        "0.5 (partially supported), or 1 (fully supported). No explanation."
    )
    user = f"QUESTION: {question}\n\nCONTEXT:\n{context}\n\nCANDIDATE ANSWER: {candidate_answer}"
    return _judge_score(system, user)
