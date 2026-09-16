"""Runs the (public or hidden) question set against every team's /ask endpoint
and scores the responses. Organizer-only tool.

The hidden set is never read from disk as plaintext: it's compiled into a
frozen native module under assets/ (see tools/build_hidden.py and hidden.py)
and is selected with the literal value "hidden" (the default).

Usage:
    python -m evaluation.evaluator --questions hidden
    python -m evaluation.evaluator --questions evaluation/public_questions.json
"""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from evaluation.hidden import hidden_fingerprint, load_hidden_questions
from evaluation.leaderboard import print_failure_analysis, print_leaderboard, write_results
from evaluation.report import write_html_report
from evaluation.scoring import score_question

RESULTS_DIR = Path(__file__).resolve().parent / "results"
HIDDEN_SENTINEL = "hidden"


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve_questions(questions_arg: str) -> tuple[list, dict, bool]:
    """Returns (questions, question_set_fingerprint, redact) for --questions.

    `questions_arg` is either the literal "hidden" (loads the frozen,
    organizer-only set) or a path to a questions JSON file (e.g. the public set).
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
    written to disk or rendered -- scoring already happened, so this is safe."""
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
    except Exception as exc:  # noqa: BLE001 - a broken team submission must not crash the eval run
        latency = time.perf_counter() - start
        return {"answer": "", "sources": [], "latency": latency, "error": str(exc)}


def run_evaluation(questions: list, teams: list) -> dict:
    all_results = {}
    for team in teams:
        team_name, base_url = team["team"], team["base_url"]
        per_question = []
        for q in questions:
            call = call_team(base_url, q["question"])
            if call["error"] is not None:
                scores = {"correctness": 0.0, "retrieval": 0.0, "groundedness": 0.0, "citations": 0.0, "latency": 0.0, "weighted_total": 0.0}
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
        team_avg = {
            key: sum(r["scores"][key] for r in per_question) / len(per_question)
            for key in ["correctness", "retrieval", "groundedness", "citations", "latency", "weighted_total"]
        }
        by_category: dict[str, list[dict]] = {}
        for r in per_question:
            by_category.setdefault(r["category"] or "uncategorized", []).append(r)
        category_avg = {
            category: {
                key: sum(r["scores"][key] for r in rows) / len(rows)
                for key in ["correctness", "retrieval", "groundedness", "citations", "latency", "weighted_total"]
            }
            for category, rows in by_category.items()
        }
        all_results[team_name] = {
            "per_question": per_question,
            "average": team_avg,
            "by_category": category_avg,
            "final_score_pct": team_avg["weighted_total"] * 100,
        }

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Run the RAG Battle Royale evaluation.")
    parser.add_argument(
        "--questions",
        default=HIDDEN_SENTINEL,
        help='The literal "hidden" (default, frozen organizer-only set) or a path to a questions JSON file.',
    )
    parser.add_argument("--teams", default=str(Path(__file__).parent / "teams.json"))
    args = parser.parse_args()

    questions, question_set, redact = resolve_questions(args.questions)
    teams = load_json(args.teams)["teams"]

    results = run_evaluation(questions, teams)
    output_results = redact_results(results) if redact else results

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = RESULTS_DIR / run_id
    meta = {"run_id": run_id, "question_set": question_set}
    write_results(output_results, out_dir, meta)
    report_path = write_html_report(output_results, out_dir, meta)
    print_leaderboard(output_results)
    print_failure_analysis(output_results)
    print(f"\U0001F4C4 Emailable report: {report_path}")


if __name__ == "__main__":
    main()
