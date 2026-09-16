"""Runs the (public or hidden) question set against every team's /ask endpoint
and scores the responses. Organizer-only tool.

Usage:
    python -m evaluation.evaluator --questions evaluation/hidden_questions.json
    python -m evaluation.evaluator --questions evaluation/public_questions.json
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from evaluation.leaderboard import print_failure_analysis, print_leaderboard, write_results
from evaluation.report import write_html_report
from evaluation.scoring import score_question

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def run_evaluation(questions_path: str, teams_path: str) -> dict:
    questions = load_json(questions_path)["questions"]
    teams = load_json(teams_path)["teams"]

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
        all_results[team_name] = {"per_question": per_question, "average": team_avg, "final_score_pct": team_avg["weighted_total"] * 100}

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Run the RAG Battle Royale evaluation.")
    parser.add_argument("--questions", default=str(Path(__file__).parent / "hidden_questions.json"))
    parser.add_argument("--teams", default=str(Path(__file__).parent / "teams.json"))
    args = parser.parse_args()

    results = run_evaluation(args.questions, args.teams)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = RESULTS_DIR / run_id
    write_results(results, out_dir)
    report_path = write_html_report(results, out_dir, {"run_id": run_id, "questions_path": args.questions})
    print_leaderboard(results)
    print_failure_analysis(results)
    print(f"\U0001F4C4 Emailable report: {report_path}")


if __name__ == "__main__":
    main()
