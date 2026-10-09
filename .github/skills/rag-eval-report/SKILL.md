---
name: rag-eval-report
description: 'Score your RAG app''s /ask endpoint against the public or hidden question set, render a self-contained HTML report, and (for hidden runs) submit your scores to the RAG Battle Royale leaderboard. Use when asked to run the evaluation, score your app, generate a report, or submit results to the leaderboard.'
argument-hint: '[--questions public|hidden] [--base-url URL] [--no-submit] [--dry-run]'
---

# RAG Battle Royale — Evaluate, Report & Submit

Scores your team's `/ask` endpoint against a question set and renders the
results as a self-contained HTML report (inline styles, inline SVG bars, no
JS/CSS/CDN — safe to email or paste). Hidden-set runs also submit your scores
to the leaderboard's public `/submit` channel.

## Prerequisites

- Your app is running and reachable (see the **Run API** task, default
  `http://localhost:8000`).
- `.env` has:
  - `GROQ_API_KEY` — used by the LLM judge in
    [scripts/evaluation/judge.py](./scripts/evaluation/judge.py).
  - `TEAM_NAME` — your team's identity on the leaderboard.
  - `LEADERBOARD_SUBMIT_URL` / `LEADERBOARD_SUBMIT_TOKEN` — given to you by the
    organizers at the start of the event (only needed for hidden/submitted
    runs; see [leaderboard/participant/README.md](../../../../leaderboard/participant/README.md)
    in the sibling `leaderboard` project for the full submission contract).
- The hidden question set is never checked into this repo as plaintext. It's
  compiled into a frozen, importable native module under
  [assets/](./assets/) (`_hidden_frozen*.so`), shipped to you so you can score
  against it without ever seeing the questions — see
  [scripts/evaluation/hidden.py](./scripts/evaluation/hidden.py).

## Procedure

1. `cd` into the skill's `scripts/` folder so `evaluation` resolves as a package:
   ```bash
   cd .github/skills/rag-eval-report/scripts
   ```
2. Run the evaluator against the hidden (default, submitted) or public
   (self-test, never submitted) set:
   ```bash
   # scores against the hidden set, writes a report, and submits to the leaderboard:
   python -m evaluation.evaluator
   # self-test against the public set -- local report only, never submitted:
   python -m evaluation.evaluator --questions evaluation/public_questions.json
   ```
3. This writes a timestamped run under `evaluation/results/<run_id>/`:
   - `results.json` — `{"meta": {"run_id", "question_set": {"name","sha256","count"}, "issued_at"}, "teams": {...}}`.
     This is exactly the body submitted to the leaderboard for hidden runs.
     For hidden runs, `question` and `gold_answer` are redacted per-question
     (scoring already happened before redaction, so scores are unaffected);
     `question_set` is a tamper-evident fingerprint (sha256 + count), not the
     question text, so you can verify which set produced a given report
     without ever exposing it.
   - `report.html` — self-contained HTML report, ready to email; the footer
     shows the same `question_set` fingerprint as `results.json`.
4. To regenerate the HTML report from an existing run (no re-evaluation)
   see [scripts/evaluation/report.py](./scripts/evaluation/report.py):
   ```bash
   python -m evaluation.report --results evaluation/results/<run_id>/results.json
   ```

## Submitting to the leaderboard

Every hidden run auto-submits at the end, unless you pass a safety flag:

```bash
python -m evaluation.evaluator --no-submit   # score + report, skip submission
python -m evaluation.evaluator --dry-run     # print the exact request body, send nothing
```

To (re-)submit an existing run without re-evaluating, see
[scripts/evaluation/submit.py](./scripts/evaluation/submit.py):
```bash
python -m evaluation.submit --results evaluation/results/<run_id>/results.json
```

Submission posts `results.json` byte-for-byte to `$LEADERBOARD_SUBMIT_URL/submit`
with the `X-Submit-Token` header. It retries on `429`/`503` (honoring
`Retry-After`) and raises on any other non-`202` response. Resubmitting the
same run is harmless — the leaderboard dedupes on `(run_id, question_set.sha256)`.
Only your own team's scores are affected; submitting never touches other
teams' standings.

## Verifying the hidden set that produced a report

Every `results.json` and `report.html` carries `question_set` (name, sha256,
count). To confirm a given report was produced by the current frozen hidden
set:
```bash
cd .github/skills/rag-eval-report/scripts
python -c "from evaluation.hidden import hidden_fingerprint; print(hidden_fingerprint())"
```
and compare against the `question_set` recorded in that run's `results.json`
`meta`. `evaluation/hidden.py` also re-verifies the frozen module's embedded
sha256 on every load, so a tampered or stale `.so` fails loudly instead of
silently scoring against the wrong questions. See
[tests/unit/test_frozen_hidden.py](../../../tests/unit/test_frozen_hidden.py)
for the automated checks (tamper rejection, no-plaintext-in-repo, and that
the hidden set never falls back to reading a JSON file).

## Report contents

The HTML report ([scripts/evaluation/report.py](./scripts/evaluation/report.py)) includes:
- Overall score and a score bar
- Metric breakdown (correctness, retrieval, groundedness, citations, latency), plus a per-category table
- Lowest-scoring answers for the post-run failure-analysis discussion

## Scoring semantics (scripts/evaluation/scoring.py)

All 5 rule-mandated metrics are computed and weighted exactly as in
`docs/PARTICIPANT_RULES.md` (correctness 50%, retrieval 20%, groundedness
15%, citations 10%, latency 5%). Retrieval and citations both grade against
`gold_sources` but are intentionally distinct, not a duplicate check:

- **Retrieval (20%)** is rank-aware (nDCG): rewards gold documents/sections
  appearing early in `sources`.
- **Citations (10%)** is precision-weighted (F-beta, beta=0.5): penalizes
  citing extra, irrelevant documents rather than a clean, minimal list.
- Both are **section-aware**: `gold_sources` entries may be a plain document
  path (`"engineering/deployments.md"`) or `{"document": ..., "sections":
  [...]}"` for partial credit when the right document is cited but the wrong
  section. `public_questions.json` uses the object form; `hidden_questions.json`
  may use either.

## Rate limits & resuming

Groq limits `openai/gpt-oss-20b` per minute (roughly 8K tokens / 30 requests on
the free tier), and the app's `/ask` and the judge share that budget. One
question costs several thousand tokens, so a full run takes on the order of a
minute per question. The harness is built to wait rather than fail:

- **Judge throttling** ([judge.py](./scripts/evaluation/judge.py)): reads Groq's
  `x-ratelimit-remaining-tokens` / `-reset-tokens` headers and waits before the
  limit is hit; on a 429 it honors `retry-after`.
- **Judge cache**: scores are cached in `evaluation/results/.judge_cache.json`
  (hashes and scores only, no question text), so re-running with unchanged
  answers costs no judge tokens. Disable with `--no-judge-cache`.
- **`/ask` retries**: the evaluator retries 502/503/504 and any 429 carrying
  `Retry-After` (`--ask-retries`, `--ask-timeout`). The app waits out short Groq
  429s itself and otherwise answers `503` + `Retry-After`.
- **Checkpoint / resume**: each finished question is appended to
  `results/<run_id>/checkpoint.jsonl` (hidden runs store it redacted). If a run
  is interrupted or fails, it prints the command to continue:
  ```bash
  python -m evaluation.evaluator --resume <run_id>              # hidden
  python -m evaluation.evaluator --questions evaluation/public_questions.json --resume <run_id>
  ```
  Resume refuses if the question-set fingerprint changed.
- `--pace SECONDS` adds a fixed pause between questions if you still see 429s.
- **Progress & exits**: each question prints `[i/N] <id> -> score (latency)`, and
  every rate-limit wait is announced. A run stops cleanly (no traceback) with exit
  code `75` when rate-limited past the retry window, or `1` on any other failure;
  both print the resume command. Add `--debug` for the full traceback.
- **Daily quota (TPD)**: the judge stops immediately instead of retrying, printing
  Groq's wait hint. The free tier's 200K tokens/day refill gradually (~8.3K/hour).
- **Errored questions**: if `/ask` keeps returning 502/503/504 the run stops rather
  than recording a zero; other `/ask` errors score 0 and a hidden run containing
  them is **not submitted** -- fix the app and `--resume` to retry just those.

The daily token quota is not worked around: use the public set for iteration
and the cache/resume to avoid repeating spent work.

## Measuring the impact of a change

Use `--save`/`--compare` to see per-metric, per-category deltas after a change
to `app/` (typically against the public set, which has no submission cost):
```bash
python -m evaluation.evaluator --questions evaluation/public_questions.json --save evaluation/results/dev/baseline.json
# ...make a change to app/...
python -m evaluation.evaluator --questions evaluation/public_questions.json --compare evaluation/results/dev/baseline.json
```
Or via the **Evaluate app (local)** VS Code task.

It has no external dependencies (fonts, scripts, stylesheets) so it renders
correctly when attached to or pasted into an email.

