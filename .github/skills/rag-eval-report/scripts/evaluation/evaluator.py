"""Runs the RAG Battle Royale evaluation for THIS team's /ask endpoint, writes a
local HTML report, and -- for hidden runs only -- submits the redacted scores
to the leaderboard's public /submit channel.

The hidden set is never read from disk as plaintext: it's compiled into a
frozen native module under assets/ (see hidden.py and tools/build_hidden.py,
organizer-only) and is selected with the literal value "hidden" (the default).
Only hidden runs are submitted -- per docs/PARTICIPANT_RULES.md the public set
is your own dev loop and never counts toward the leaderboard.

Usage:
    python -m evaluation.evaluator                        # hidden set, scores + reports + submits
    python -m evaluation.evaluator --questions evaluation/public_questions.json
    python -m evaluation.evaluator --no-submit             # score hidden, skip submission
    python -m evaluation.evaluator --dry-run               # print the submission body, send nothing
    python -m evaluation.evaluator --save snap.json
    python -m evaluation.evaluator --compare snap.json      # diff against a prior snapshot
"""
import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from evaluation.hidden import hidden_fingerprint, load_hidden_questions
from evaluation.leaderboard import write_results
from evaluation.report import write_html_report
from evaluation.scoring import score_question
from evaluation.submit import SubmissionError, submit_results

RESULTS_DIR = Path(__file__).resolve().parent / "results"
HIDDEN_SENTINEL = "hidden"
_METRICS = ["correctness", "retrieval", "groundedness", "citations", "latency", "weighted_total"]


def resolve_questions(questions_arg: str) -> tuple[list, dict, bool]:
    """Returns (questions, question_set_fingerprint, is_hidden) for --questions.

    `questions_arg` is either the literal "hidden" (loads the frozen,
    integrity-checked set) or a path to a questions JSON file (the public set).
    """
    if questions_arg == HIDDEN_SENTINEL:
        return load_hidden_questions(), hidden_fingerprint(), True
    path = Path(questions_arg)
    raw = path.read_bytes()
    questions = json.loads(raw)["questions"]
    fingerprint = {"name": path.stem, "sha256": hashlib.sha256(raw).hexdigest(), "count": len(questions)}
    return questions, fingerprint, False


def redact_results(results: dict) -> dict:
    """Strips hidden question text/gold answers from a results dict before it's
    written to disk, rendered, or submitted -- scoring already happened, so this is safe."""
    redacted = {}
    for team, data in results.items():
        per_question = [
            {**q, "question": "<redacted: hidden question set>", "gold_answer": "<redacted: hidden question set>"}
            for q in data["per_question"]
        ]
        redacted[team] = {**data, "per_question": per_question}
    return redacted


def call_team(base_url: str, question: str, timeout: float = 15.0) -> dict:
    start = time.perf_counter()
    try:
        response = httpx.post(f"{base_url}/ask", json={"question": question}, timeout=timeout)
        latency = time.perf_counter() - start
        response.raise_for_status()
        body = response.json()
        sources = [{"document": s["document"], "section": s.get("section")} for s in body.get("sources", [])]
        return {"answer": body.get("answer", ""), "sources": sources, "latency": latency, "error": None}
    except Exception as exc:  # noqa: BLE001 - a broken app must not crash the eval run
        latency = time.perf_counter() - start
        return {"answer": "", "sources": [], "latency": latency, "error": str(exc)}


def run_evaluation(questions: list, team_name: str, base_url: str) -> dict:
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
                "category": q.get("category"),
                "question": q["question"],
                "gold_answer": q["gold_answer"],
                "candidate_answer": call["answer"],
                "returned_documents": [s["document"] for s in call["sources"]],
                "latency_seconds": call["latency"],
                "error": call["error"],
                "scores": scores,
            }
        )

    average = {m: sum(r["scores"][m] for r in per_question) / len(per_question) for m in _METRICS}
    by_category: dict[str, list[dict]] = {}
    for r in per_question:
        by_category.setdefault(r["category"] or "uncategorized", []).append(r)
    category_avg = {
        category: {m: sum(r["scores"][m] for r in rows) / len(rows) for m in _METRICS}
        for category, rows in by_category.items()
    }

    return {
        team_name: {
            "per_question": per_question,
            "average": average,
            "by_category": category_avg,
            "final_score_pct": average["weighted_total"] * 100,
        }
    }


def _print_summary(team_name: str, data: dict, baseline: dict | None = None) -> None:
    print(f"\n\U0001F4CA {team_name} \u2014 {data['final_score_pct']:.1f}% ({len(data['per_question'])} questions)")
    print(f"{'':<16}" + "".join(f"{m:>16}" for m in _METRICS))
    for label, scores in [("overall", data["average"]), *sorted(data["by_category"].items())]:
        cells = []
        for m in _METRICS:
            value = scores[m]
            if baseline and label in baseline:
                delta = value - baseline[label][m]
                sign = "+" if delta >= 0 else ""
                cells.append(f"{value:.2f} ({sign}{delta:.2f})")
            else:
                cells.append(f"{value:.2f}")
        print(f"{label:<16}" + "".join(f"{c:>16}" for c in cells))

    failures = [r for r in data["per_question"] if r["scores"]["weighted_total"] < 0.5]
    failures.sort(key=lambda r: r["scores"]["weighted_total"])
    if failures:
        print(f"\n\u26A0\uFE0F  {len(failures)} question(s) scored below 0.5 weighted_total:")
        for r in failures[:5]:
            print(f"  - [{r['scores']['weighted_total']:.2f}] {r['id']} ({r['category']}): {r['question']}")


def _load_snapshot(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"overall": payload["average"], **payload["by_category"]}


def main():
    parser = argparse.ArgumentParser(description="Run the RAG Battle Royale evaluation for your team's app.")
    parser.add_argument(
        "--questions",
        default=HIDDEN_SENTINEL,
        help='The literal "hidden" (default, submitted set) or a path to a questions JSON file '
        "(e.g. the public set, dev-loop only, never submitted).",
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="Your running app's base URL.")
    parser.add_argument("--team", default=os.environ.get("TEAM_NAME"), help="Team name; defaults to $TEAM_NAME.")
    parser.add_argument("--save", default=None, help="Write this run's scores to a JSON snapshot for a future --compare")
    parser.add_argument("--compare", default=None, help="Path to a previous snapshot (from --save) to diff against")
    parser.add_argument("--no-submit", action="store_true", help="Score and report but never submit, even for a hidden run")
    parser.add_argument("--dry-run", action="store_true", help="Print the submission body instead of sending it")
    args = parser.parse_args()

    if not args.team:
        raise SystemExit("Team name is required: pass --team or set TEAM_NAME in .env.")
    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY is not set -- required by the LLM judge (see .env.example).")

    questions, question_set, is_hidden = resolve_questions(args.questions)
    results = run_evaluation(questions, args.team, args.base_url)
    output_results = redact_results(results) if is_hidden else results

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = RESULTS_DIR / run_id
    meta = {
        "run_id": run_id,
        "question_set": question_set,
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    write_results(output_results, out_dir, meta)
    report_path = write_html_report(output_results, out_dir, meta)

    baseline = _load_snapshot(args.compare) if args.compare else None
    _print_summary(args.team, output_results[args.team], baseline)
    print(f"\n\U0001F4C4 Report: {report_path}")

    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(output_results[args.team], indent=2), encoding="utf-8")
        print(f"\U0001F4BE Saved snapshot to {save_path}")

    if not is_hidden:
        print("\u2139\uFE0F  Public run \u2014 not submitted (only hidden runs count toward the leaderboard).")
    elif args.no_submit:
        print("\u23ED\uFE0F  Skipped submission (--no-submit).")
    else:
        try:
            submit_results(out_dir / "results.json", dry_run=args.dry_run)
        except SubmissionError as exc:
            raise SystemExit(f"\u274C {exc}") from exc


if __name__ == "__main__":
    main()
