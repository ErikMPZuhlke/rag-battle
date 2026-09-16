"""Per-question scoring: correctness, retrieval, groundedness, citations, latency.

Weights (see docs/PARTICIPANT_RULES.md): correctness 50%, retrieval 20%,
groundedness 15%, citations 10%, latency 5%.

Retrieval and citations both grade against `gold_sources`, but they measure
different things so they don't collapse into one redundant document-set
check:
  - retrieval (20%) is rank-aware (nDCG): did gold material show up, and how
    high in the returned list?
  - citations (10%) is precision-weighted (F-beta, beta=0.5): are the sources
    actually cited clean, or is the answer citing everything to be safe?
Both are section-aware when gold data specifies a section: citing the right
document but wrong section earns partial (not full) credit.
"""
import math
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


def _normalize_gold(gold_sources: list) -> dict[str, list[str] | None]:
    """Map gold document -> list of acceptable sections, or None if gold is document-level only.

    Accepts either plain document-path strings (back-compat) or
    {"document": ..., "sections": [...]} objects for section-aware grading.
    """
    gold_by_doc: dict[str, list[str] | None] = {}
    for item in gold_sources:
        if isinstance(item, str):
            gold_by_doc.setdefault(item, None)
        else:
            gold_by_doc.setdefault(item["document"], item.get("sections") or None)
    return gold_by_doc


def _gain(source: dict, gold_by_doc: dict[str, list[str] | None]) -> float:
    """Graded relevance of one returned {document, section} source: 1.0 full match,
    0.5 right document/wrong section (only possible when gold specifies sections), 0 otherwise."""
    document = source.get("document")
    if document not in gold_by_doc:
        return 0.0
    gold_sections = gold_by_doc[document]
    if not gold_sections:
        return 1.0
    return 1.0 if source.get("section") in gold_sections else 0.5


def score_correctness(question: str, gold_answer: str, candidate_answer: str, gold_sources: list) -> float:
    """Deterministic backstop for no-answer questions; LLM judge otherwise."""
    is_no_answer_question = len(gold_sources) == 0
    if is_no_answer_question:
        return 1.0 if _NO_ANSWER_PHRASES.search(candidate_answer) else 0.0
    return judge_correctness(question, gold_answer, candidate_answer)


def score_retrieval(returned_sources: list[dict], gold_sources: list) -> float:
    """Rank- and section-aware nDCG: rewards gold documents/sections appearing early in the list."""
    gold_by_doc = _normalize_gold(gold_sources)
    if not gold_by_doc:
        # No-answer question: correct behavior is to return no sources at all.
        return 1.0 if not returned_sources else 0.0
    dcg = sum(_gain(src, gold_by_doc) / math.log2(i + 2) for i, src in enumerate(returned_sources))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(len(gold_by_doc)))
    return dcg / idcg if idcg else 0.0


def score_groundedness(question: str, candidate_answer: str, returned_sources: list[dict]) -> float:
    if not returned_sources:
        # No context returned; only "grounded" if the answer itself declines to answer.
        return 1.0 if _NO_ANSWER_PHRASES.search(candidate_answer) else 0.0
    documents = dict.fromkeys(src["document"] for src in returned_sources)
    context = "\n\n".join(_read_source_text(doc) for doc in documents)
    if not context.strip():
        return 0.0
    return judge_groundedness(question, candidate_answer, context)


def score_citations(returned_sources: list[dict], gold_sources: list) -> float:
    """Precision-weighted F-beta (beta=0.5) over cited sources, graded by document+section accuracy.

    Distinct from retrieval: this rewards a clean citation list (not padding
    `sources` with extra documents to inflate recall) rather than ranking.
    """
    gold_by_doc = _normalize_gold(gold_sources)
    if not gold_by_doc:
        return 1.0 if not returned_sources else 0.0
    if not returned_sources:
        return 0.0
    gains = [_gain(src, gold_by_doc) for src in returned_sources]
    precision = sum(gains) / len(returned_sources)
    covered_docs = {src["document"] for src, g in zip(returned_sources, gains) if g > 0}
    recall = len(covered_docs) / len(gold_by_doc)
    if precision + recall == 0:
        return 0.0
    beta_sq = 0.25  # beta=0.5: weight precision more heavily than recall
    return (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)


def score_latency(latency_seconds: float) -> float:
    """Tiered latency score, normalized to 0-1 (5 = best, per the spec's 0-5 scale)."""
    for threshold, tier_score in _LATENCY_TIERS:
        if latency_seconds < threshold:
            return tier_score / 5.0
    return 0.0


def score_question(
    question: str,
    gold_answer: str,
    gold_sources: list,
    candidate_answer: str,
    returned_sources: list[dict],
    latency_seconds: float,
) -> dict:
    correctness = score_correctness(question, gold_answer, candidate_answer, gold_sources)
    retrieval = score_retrieval(returned_sources, gold_sources)
    groundedness = score_groundedness(question, candidate_answer, returned_sources)
    citations = score_citations(returned_sources, gold_sources)
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
