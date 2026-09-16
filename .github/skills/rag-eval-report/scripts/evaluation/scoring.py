"""Per-question scoring: correctness, retrieval, groundedness, citations, latency.

Weights (see docs/PARTICIPANT_RULES.md): correctness 50%, retrieval 20%,
groundedness 15%, citations 10%, latency 5%.
"""
import re
from pathlib import Path

from evaluation.judge import judge_correctness, judge_groundedness


def _find_kb_dir(start: Path) -> Path:
    """Walk upward from this file to locate data/knowledge-base regardless of nesting depth."""
    for parent in (start, *start.parents):
        candidate = parent / "data" / "knowledge-base"
        if candidate.is_dir():
            return candidate
    return start.parent.parent / "data" / "knowledge-base"


KB_DIR = _find_kb_dir(Path(__file__).resolve().parent)

_NO_ANSWER_PHRASES = re.compile(
    r"does not specify|not specified|no information|cannot find|couldn't find|"
    r"not mentioned|unable to find|not documented|not covered",
    re.IGNORECASE,
)

_LATENCY_TIERS = [
    (1.0, 5),
    (2.0, 4),
    (3.0, 3),
    (5.0, 2),
]


def _read_source_text(document: str, max_chars: int = 2000) -> str:
    path = KB_DIR / document
    try:
        return path.read_text(encoding="utf-8")[:max_chars]
    except OSError:
        return ""


def score_correctness(question: str, gold_answer: str, candidate_answer: str, gold_sources: list[str]) -> float:
    """Deterministic backstop for no-answer questions; LLM judge otherwise."""
    is_no_answer_question = len(gold_sources) == 0
    if is_no_answer_question:
        return 1.0 if _NO_ANSWER_PHRASES.search(candidate_answer) else 0.0
    return judge_correctness(question, gold_answer, candidate_answer)


def score_retrieval(returned_documents: list[str], gold_sources: list[str]) -> float:
    """Recall@k of gold source documents among the returned sources."""
    if not gold_sources:
        # No-answer question: correct behavior is to return no sources at all.
        return 1.0 if not returned_documents else 0.0
    gold_set = set(gold_sources)
    hit = len(gold_set & set(returned_documents))
    return hit / len(gold_set)


def score_groundedness(question: str, candidate_answer: str, returned_documents: list[str]) -> float:
    if not returned_documents:
        # No context returned; only "grounded" if the answer itself declines to answer.
        return 1.0 if _NO_ANSWER_PHRASES.search(candidate_answer) else 0.0
    context = "\n\n".join(_read_source_text(doc) for doc in returned_documents)
    if not context.strip():
        return 0.0
    return judge_groundedness(question, candidate_answer, context)


def score_citations(returned_documents: list[str], gold_sources: list[str]) -> float:
    """F1 between returned and gold source documents (document-level)."""
    if not gold_sources:
        return 1.0 if not returned_documents else 0.0
    if not returned_documents:
        return 0.0
    gold_set, returned_set = set(gold_sources), set(returned_documents)
    tp = len(gold_set & returned_set)
    precision = tp / len(returned_set) if returned_set else 0.0
    recall = tp / len(gold_set) if gold_set else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score_latency(latency_seconds: float) -> float:
    """Tiered latency score, normalized to 0-1 (5 = best, per the spec's 0-5 scale)."""
    for threshold, tier_score in _LATENCY_TIERS:
        if latency_seconds < threshold:
            return tier_score / 5.0
    return 0.0


def score_question(
    question: str,
    gold_answer: str,
    gold_sources: list[str],
    candidate_answer: str,
    returned_documents: list[str],
    latency_seconds: float,
) -> dict:
    correctness = score_correctness(question, gold_answer, candidate_answer, gold_sources)
    retrieval = score_retrieval(returned_documents, gold_sources)
    groundedness = score_groundedness(question, candidate_answer, returned_documents)
    citations = score_citations(returned_documents, gold_sources)
    latency = score_latency(latency_seconds)

    weighted_total = (
        0.50 * correctness
        + 0.20 * retrieval
        + 0.15 * groundedness
        + 0.10 * citations
        + 0.05 * latency
    )

    return {
        "correctness": correctness,
        "retrieval": retrieval,
        "groundedness": groundedness,
        "citations": citations,
        "latency": latency,
        "weighted_total": weighted_total,
    }
