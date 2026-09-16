---
name: rag-eval-report
description: 'Kick off the RAG Battle Royale evaluation chain (score every team''s /ask endpoint against the public or hidden question set) and produce a self-contained, emailable HTML leaderboard report. Use when asked to run the evaluation, score teams, generate the leaderboard, or produce an evaluation/results report.'
argument-hint: '[--questions public|hidden] [--teams path]'
---

# RAG Battle Royale — Evaluation & Report

Runs the organizer-only evaluation chain against each team's `/ask` endpoint and
renders the results as a leaderboard, CSV, and a self-contained HTML report
suitable for emailing (inline styles, inline SVG bars, no JS/CSS/CDN).

## Prerequisites

- Each team's API is running and reachable (see `docker-compose.eval.yml` for
  the organizer multi-team setup, or run a single team locally via the
  **Run API** task).
- `.env` has `GROQ_API_KEY` set (used by the LLM judge in
  [scripts/evaluation/judge.py](./scripts/evaluation/judge.py)).
- [scripts/evaluation/teams.json](./scripts/evaluation/teams.json) lists every team name and
  its reachable `base_url`.

## Procedure

1. `cd` into the skill's `scripts/` folder so `evaluation` resolves as a package:
   ```bash
   cd .github/skills/rag-eval-report/scripts
   ```
2. Run the evaluator against the public (self-test) or hidden (organizer) set:
   ```bash
   python -m evaluation.evaluator --questions evaluation/public_questions.json --teams evaluation/teams.json
   # organizer-only:
   python -m evaluation.evaluator --questions evaluation/hidden_questions.json --teams evaluation/teams.json
   ```
3. This writes a timestamped run under `evaluation/results/<run_id>/`:
   - `results.json` — full per-question, per-team scores
   - `leaderboard.csv` — summary table
   - `report.html` — self-contained HTML leaderboard report, ready to email
4. To regenerate the HTML report from an existing run (no re-evaluation)
   see [scripts/evaluation/report.py](./scripts/evaluation/report.py):
   ```bash
   python -m evaluation.report --results evaluation/results/<run_id>/results.json
   ```

## Report contents

The HTML report ([scripts/evaluation/report.py](./scripts/evaluation/report.py)) includes:
- Ranked leaderboard with medals and a score bar per team
- Per-team metric breakdown (correctness, retrieval, groundedness, citations, latency)
- Lowest-scoring answers across all teams (gold vs. candidate) for the post-battle discussion

It has no external dependencies (fonts, scripts, stylesheets) so it renders
correctly when attached to or pasted into an email.
