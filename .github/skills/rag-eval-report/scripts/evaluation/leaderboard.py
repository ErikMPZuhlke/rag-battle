"""Formats evaluation results into a leaderboard, CSV/JSON output, and a
failure-analysis dump for the post-battle teaching moment."""
import csv
import json
from pathlib import Path

_MEDALS = ["🥇", "🥈", "🥉"]


def write_results(results: dict, out_dir: Path, meta: dict | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta or {}, "teams": results}
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with (out_dir / "leaderboard.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["team", "final_score_pct", "correctness", "retrieval", "groundedness", "citations", "latency"])
        for team, data in sorted(results.items(), key=lambda kv: kv[1]["final_score_pct"], reverse=True):
            avg = data["average"]
            writer.writerow(
                [team, f"{data['final_score_pct']:.1f}", avg["correctness"], avg["retrieval"], avg["groundedness"], avg["citations"], avg["latency"]]
            )

    with (out_dir / "leaderboard_by_category.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["team", "category", "correctness", "retrieval", "groundedness", "citations", "latency", "weighted_total"])
        for team, data in sorted(results.items(), key=lambda kv: kv[1]["final_score_pct"], reverse=True):
            for category, scores in sorted(data.get("by_category", {}).items()):
                writer.writerow(
                    [team, category, scores["correctness"], scores["retrieval"], scores["groundedness"], scores["citations"], scores["latency"], scores["weighted_total"]]
                )


def print_leaderboard(results: dict) -> None:
    ranked = sorted(results.items(), key=lambda kv: kv[1]["final_score_pct"], reverse=True)
    print("\n🏆 RAG BATTLE ROYALE — LEADERBOARD\n")
    print(f"{'Rank':<6}{'Team':<20}{'Score':<8}")
    for i, (team, data) in enumerate(ranked):
        medal = _MEDALS[i] if i < len(_MEDALS) else "  "
        print(f"{medal:<6}{team:<20}{data['final_score_pct']:.1f}")
    print()


def print_failure_analysis(results: dict, worst_n: int = 5) -> None:
    """Print the lowest-scoring (team, question) pairs across all teams."""
    rows = []
    for team, data in results.items():
        for q in data["per_question"]:
            rows.append((q["scores"]["weighted_total"], team, q))
    rows.sort(key=lambda r: r[0])

    print(f"📉 Lowest-scoring answers (top {worst_n}) — good candidates for the failure-analysis discussion:\n")
    for score, team, q in rows[:worst_n]:
        print(f"- [{score:.2f}] {team} | {q['id']} ({q['category']}): {q['question']}")
        print(f"    gold: {q['gold_answer']}")
        print(f"    got:  {q['candidate_answer'][:200]}")
    print()
