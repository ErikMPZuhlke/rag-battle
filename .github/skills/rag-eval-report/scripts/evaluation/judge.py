"""Thin wrapper around a Groq chat model used as an LLM judge for scoring."""
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()

_JUDGE_API_KEY = os.getenv("GROQ_API_KEY", "")
_JUDGE_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
_JUDGE_MODEL = os.getenv("GROQ_JUDGE_MODEL", os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"))

_client = None

_VALID_SCORES = {"0": 0.0, "0.5": 0.5, "1": 1.0}
_MAX_RATE_LIMIT_RETRIES = 5
_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)(ms|s)", re.IGNORECASE)


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=_JUDGE_API_KEY, base_url=_JUDGE_BASE_URL)
    return _client


def _rate_limit_wait_seconds(exc: RateLimitError, attempt: int) -> float:
    """Parse Groq's suggested wait time from the error message, else back off."""
    match = _RETRY_AFTER_RE.search(str(exc))
    if match:
        value, unit = match.groups()
        seconds = float(value) / 1000 if unit.lower() == "ms" else float(value)
        return max(seconds, 0.5) + 0.5  # small safety margin
    return min(2 ** attempt, 30)


def _judge_score(system_prompt: str, user_prompt: str) -> float:
    """Call the judge model and parse a 0 / 0.5 / 1 score from its reply."""
    for attempt in range(_MAX_RATE_LIMIT_RETRIES + 1):
        try:
            response = get_client().chat.completions.create(
                model=_JUDGE_MODEL,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            break
        except RateLimitError as exc:
            if attempt == _MAX_RATE_LIMIT_RETRIES:
                raise
            time.sleep(_rate_limit_wait_seconds(exc, attempt))
    text = response.choices[0].message.content.strip()
    match = re.search(r"\b(0\.5|0|1)\b", text)
    if not match:
        return 0.0
    return _VALID_SCORES[match.group(1)]


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
