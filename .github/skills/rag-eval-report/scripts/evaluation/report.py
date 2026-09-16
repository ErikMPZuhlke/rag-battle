"""Renders evaluation results into a single self-contained, emailable HTML report.

No JavaScript, external CSS, fonts, or CDNs — everything (styles, bar charts as
inline SVG) is embedded so the file can be attached to or pasted into an email
and render correctly in restrictive email clients.

Usage:
    python -m evaluation.report --results evaluation/results/<run_id>/results.json
"""
import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

_METRICS = ["correctness", "retrieval", "groundedness", "citations", "latency"]
_MEDALS = ["\U0001F947", "\U0001F948", "\U0001F949"]

_BODY_STYLE = "font-family:Arial,Helvetica,sans-serif;background:#f4f5f7;margin:0;padding:24px;color:#1f2430;"
_CARD_STYLE = "background:#ffffff;border:1px solid #e2e5eb;border-radius:8px;padding:20px 24px;margin-bottom:20px;"
_TABLE_STYLE = "border-collapse:collapse;width:100%;font-size:14px;"
_TH_STYLE = "text-align:left;padding:8px 10px;border-bottom:2px solid #d7dbe3;color:#555;font-size:12px;text-transform:uppercase;"
_TD_STYLE = "padding:8px 10px;border-bottom:1px solid #edeff3;vertical-align:top;"


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


def _bar_svg(value: float, width: int = 140, height: int = 12, color: str = "#2563eb") -> str:
    """Static inline SVG bar for a 0..1 score — no JS/CSS animation, email-safe."""
    pct = max(0.0, min(1.0, value))
    fill_w = round(width * pct, 1)
    return (
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" '
        f'style="vertical-align:middle;">'
        f'<rect width="{width}" height="{height}" rx="3" fill="#e5e8ee"/>'
        f'<rect width="{fill_w}" height="{height}" rx="3" fill="{color}"/>'
        f"</svg>"
    )


def _metric_row(label: str, value: float) -> str:
    return (
        f'<tr><td style="{_TD_STYLE}width:110px;">{_esc(label)}</td>'
        f'<td style="{_TD_STYLE}width:150px;">{_bar_svg(value)}</td>'
        f'<td style="{_TD_STYLE}">{value:.2f}</td></tr>'
    )


def _leaderboard_table(results: dict) -> str:
    ranked = sorted(results.items(), key=lambda kv: kv[1]["final_score_pct"], reverse=True)
    rows = []
    for i, (team, data) in enumerate(ranked):
        medal = _MEDALS[i] if i < len(_MEDALS) else ""
        rows.append(
            f'<tr><td style="{_TD_STYLE}">{medal} {_esc(team)}</td>'
            f'<td style="{_TD_STYLE}"><strong>{data["final_score_pct"]:.1f}</strong></td>'
            f'<td style="{_TD_STYLE}">{_bar_svg(data["final_score_pct"] / 100, color="#16a34a")}</td></tr>'
        )
    return (
        f'<table style="{_TABLE_STYLE}"><thead><tr>'
        f'<th style="{_TH_STYLE}">Team</th><th style="{_TH_STYLE}">Score</th><th style="{_TH_STYLE}"></th>'
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _team_detail_section(team: str, data: dict) -> str:
    metric_rows = "".join(_metric_row(m, data["average"][m]) for m in _METRICS)
    return (
        f'<div style="{_CARD_STYLE}">'
        f'<h3 style="margin:0 0 12px;">{_esc(team)} — {data["final_score_pct"]:.1f}%</h3>'
        f'<table style="{_TABLE_STYLE}"><tbody>{metric_rows}</tbody></table>'
        f"</div>"
    )


def _failure_analysis_section(results: dict, worst_n: int = 5) -> str:
    rows = []
    for team, data in results.items():
        for q in data["per_question"]:
            rows.append((q["scores"]["weighted_total"], team, q))
    rows.sort(key=lambda r: r[0])

    items = []
    for score, team, q in rows[:worst_n]:
        items.append(
            f'<tr><td style="{_TD_STYLE}">{score:.2f}</td>'
            f'<td style="{_TD_STYLE}">{_esc(team)}</td>'
            f'<td style="{_TD_STYLE}">{_esc(q["question"])}</td>'
            f'<td style="{_TD_STYLE}">{_esc(q["gold_answer"])}</td>'
            f'<td style="{_TD_STYLE}">{_esc(q["candidate_answer"][:300])}</td></tr>'
        )
    return (
        f'<div style="{_CARD_STYLE}"><h2 style="margin:0 0 12px;">Lowest-scoring answers</h2>'
        f'<table style="{_TABLE_STYLE}"><thead><tr>'
        f'<th style="{_TH_STYLE}">Score</th><th style="{_TH_STYLE}">Team</th>'
        f'<th style="{_TH_STYLE}">Question</th><th style="{_TH_STYLE}">Gold answer</th>'
        f'<th style="{_TH_STYLE}">Candidate answer</th>'
        f"</tr></thead><tbody>{''.join(items)}</tbody></table></div>"
    )


def render_html(results: dict, meta: dict | None = None) -> str:
    meta = meta or {}
    generated_at = meta.get("generated_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    run_id = meta.get("run_id", "")
    questions_path = meta.get("questions_path", "")

    detail_sections = "".join(_team_detail_section(team, data) for team, data in results.items())

    return (
        "<!DOCTYPE html>"
        f'<html><head><meta charset="utf-8"><title>RAG Battle Royale — Results</title></head>'
        f'<body style="{_BODY_STYLE}">'
        f'<div style="{_CARD_STYLE}">'
        f'<h1 style="margin:0 0 4px;">\U0001F3C6 RAG Battle Royale — Leaderboard</h1>'
        f'<p style="margin:0;color:#666;font-size:13px;">Run {_esc(run_id)} &middot; generated {_esc(generated_at)}'
        + (f" &middot; questions: {_esc(questions_path)}" if questions_path else "")
        + "</p></div>"
        f'<div style="{_CARD_STYLE}"><h2 style="margin:0 0 12px;">Leaderboard</h2>{_leaderboard_table(results)}</div>'
        f"{detail_sections}"
        f"{_failure_analysis_section(results)}"
        "</body></html>"
    )


def write_html_report(results: dict, out_dir: Path, meta: dict | None = None) -> Path:
    meta = {**(meta or {}), "run_id": meta.get("run_id", out_dir.name) if meta else out_dir.name}
    out_path = out_dir / "report.html"
    out_path.write_text(render_html(results, meta), encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Render a results.json into a self-contained HTML report.")
    parser.add_argument("--results", required=True, help="Path to a results.json file")
    parser.add_argument("--out", default=None, help="Output HTML path (default: report.html next to results.json)")
    args = parser.parse_args()

    results_path = Path(args.results)
    results = json.loads(results_path.read_text(encoding="utf-8"))
    out_path = Path(args.out) if args.out else results_path.parent / "report.html"
    out_path.write_text(render_html(results, {"run_id": results_path.parent.name}), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
