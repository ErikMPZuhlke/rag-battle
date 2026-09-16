"""Fast local dev loop: score your own /ask endpoint against the PUBLIC
question set, without running the full multi-team organizer evaluation.

Usage:
    python -m evaluation.dev_eval
    python -m evaluation.dev_eval --base-url http://localhost:8000
    python -m evaluation.dev_eval --save evaluation/results/dev/baseline.json
    python -m evaluation.dev_eval --compare evaluation/results/dev/baseline.json

Requires GROQ_API_KEY (used by the LLM judge, same judge as the organizer
eval) and a running app (see the "Run API" task). Only the public question
set is accepted here -- per docs/PARTICIPANT_RULES.md the hidden set is
organizer-only.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from evaluation.evaluator import call_team
from evaluation.scoring import score_question

_METRICS = ["correctness", "retrieval", "groundedness", "citations", "latency", "weighted_total"]
DEFAULT_QUESTIONS = Path(__file__).parent / "public_questions.json"


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _assert_public(questions_path: str) -> None:
    """Refuse the hidden set -- it's organizer-only per the participant rules."""
    if "hidden" in Path(questions_path).name.lower():
        raise SystemExit(
            "Refusing to run against a hidden question set: only the public set "
            "(public_questions.json) is available to teams during the battle."
        )


def run(base_url: str, questions_path: str) -> dict:
    _assert_public(questions_path)
    questions = _load_json(questions_path)["questions"]

    per_question = []
    for q in questions:
        call = call_team(base_url, q["question"])
        if call["error"] is not None:
            scores = {m: 0.0 for m in _METRICS}
        else:
            scores = score_question(
                question=q["question"],
                gold_answer=q["gold_answer"],
                gold_sources=q["gold_sources"],
                candidate_answer=call["answer"],
                returned_sources=call["sources"],
                latency_seconds=call["latency"],
            )
        per_question.append(
            {
                "id": q["id"],
                "category": q.get("category", "uncategorized"),
                "question": q["question"],
                "candidate_answer": call["answer"],
                "error": call["error"],
                "scores": scores,
            }
        )

    average = {m: sum(r["scores"][m] for r in per_question) / len(per_question) for m in _METRICS}
    by_category: dict[str, list[dict]] = {}
    for r in per_question:
        by_category.setdefault(r["category"], []).append(r)
    category_avg = {
        category: {m: sum(r["scores"][m] for r in rows) / len(rows) for m in _METRICS}
        for category, rows in by_category.items()
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "questions_path": str(questions_path),
        "average": average,
        "by_category": category_avg,
        "per_question": per_question,
    }


def _print_table(title: str, rows: dict, baseline: dict | None = None) -> None:
    print(f"\n{title}")
    print(f"{'':<16}" + "".join(f"{m:>16}" for m in _METRICS))
    for key, scores in rows.items():
        cells = []
        for m in _METRICS:
            value = scores[m]
            if baseline and key in baseline:
                delta = value - baseline[key][m]
                sign = "+" if delta >= 0 else ""
                cells.append(f"{value:.2f} ({sign}{delta:.2f})")
            else:
                cells.append(f"{value:.2f}")
        print(f"{key:<16}" + "".join(f"{c:>16}" for c in cells))


def main():
    parser = argparse.ArgumentParser(description="Local dev loop: score your own /ask endpoint against the public question set.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    parser.add_argument("--save", default=None, help="Write this run's scores to a JSON snapshot for a future --compare")
    parser.add_argument("--compare", default=None, help="Path to a previous snapshot (from --save) to diff against")
    args = parser.parse_args()

    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY is not set -- required by the LLM judge (see .env.example).")

    result = run(args.base_url, args.questions)
    baseline = _load_json(args.compare) if args.compare else None

    print(f"\n\U0001F4CA Dev eval — {args.base_url} — {len(result['per_question'])} public questions")
    _print_table("Overall average", {"overall": result["average"]}, {"overall": baseline["average"]} if baseline else None)
    _print_table("By category", result["by_category"], baseline["by_category"] if baseline else None)

    failures = [r for r in result["per_question"] if r["scores"]["weighted_total"] < 0.5]
    if failures:
        print(f"\n\u26A0\uFE0F  {len(failures)} question(s) scored below 0.5 weighted_total:")
        for r in sorted(failures, key=lambda r: r["scores"]["weighted_total"])[:5]:
            print(f"  - [{r['scores']['weighted_total']:.2f}] {r['id']} ({r['category']}): {r['question']}")

    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\n\U0001F4BE Saved snapshot to {save_path}")


if __name__ == "__main__":
    main()
