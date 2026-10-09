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
_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)(ms|s)", re.IGNORECASE)
_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")
_UNIT_SECONDS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}

_CACHE_PATH = Path(__file__).resolve().parent / "results" / ".judge_cache.json"
_cache: dict[str, float] | None = None
_cache_enabled = True

# Last-seen Groq token bucket: tokens left, and the monotonic time it refills.
_rate_state: dict[str, float | None] = {"remaining_tokens": None, "reset_at": 0.0}


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
        time.sleep(min(reset_at - now + 0.25, _MAX_WAIT_SECONDS))
    # Either we waited for the refill or the snapshot is stale; don't trust it again.
    if now >= reset_at or remaining < estimated_tokens:
        _rate_state["remaining_tokens"] = None


def _rate_limit_wait_seconds(exc: RateLimitError, attempt: int) -> float:
    """Wait time for a 429: `retry-after` header, else Groq's message hint, else backoff."""
    response = getattr(exc, "response", None)
    header_wait = _parse_duration(response.headers.get("retry-after")) if response is not None else None
    if header_wait is not None:
        return min(header_wait + 0.5, _MAX_WAIT_SECONDS)
    match = _RETRY_AFTER_RE.search(str(exc))
    if match:
        value, unit = match.groups()
        seconds = float(value) / 1000 if unit.lower() == "ms" else float(value)
        return min(max(seconds, 0.5) + 0.5, _MAX_WAIT_SECONDS)  # small safety margin
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
            if attempt == _MAX_RATE_LIMIT_RETRIES:
                raise
            time.sleep(_rate_limit_wait_seconds(exc, attempt))
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
