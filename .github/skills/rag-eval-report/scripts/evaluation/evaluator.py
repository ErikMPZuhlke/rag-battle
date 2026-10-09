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
    python -m evaluation.evaluator --resume <run_id>        # continue an interrupted run
    python -m evaluation.evaluator --debug                  # show full tracebacks on failure

Groq's per-minute token limit is shared by the app and the judge; see the
"Rate limits & resuming" section of the skill's SKILL.md. Exit codes: 0 ok,
75 stopped on a rate limit (resume later), 1 any other failure.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx

from evaluation.hidden import hidden_fingerprint, load_hidden_questions
from evaluation.judge import RateLimitStop, set_cache_enabled
from evaluation.leaderboard import write_results
from evaluation.report import write_html_report
from evaluation.scoring import score_question
from evaluation.submit import SubmissionError, submit_results

RESULTS_DIR = Path(__file__).resolve().parent / "results"
HIDDEN_SENTINEL = "hidden"
_METRICS = ["correctness", "retrieval", "groundedness", "citations", "latency", "weighted_total"]
_REDACTED = "<redacted: hidden question set>"
_RETRYABLE_STATUS = {502, 503, 504}
_MAX_ASK_WAIT_SECONDS = 60.0
_RUN_ID_RE = re.compile(r"[\w-]+")
EXIT_RATE_LIMITED = 75  # EX_TEMPFAIL: try again later


def _fmt_duration(seconds: float) -> str:
    seconds = int(round(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m{secs:02d}s" if minutes else f"{secs}s"


def _one_line(text: str, limit: int = 300) -> str:
    lines = (text or "").strip().splitlines()
    first = lines[0] if lines else ""
    return first if len(first) <= limit else first[: limit - 1] + "\u2026"


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
    return {
        team: {**data, "per_question": [_redact_record(q) for q in data["per_question"]]}
        for team, data in results.items()
    }


def _redact_record(record: dict) -> dict:
    return {**record, "question": _REDACTED, "gold_answer": _REDACTED}


def _retry_wait_seconds(response: httpx.Response, attempt: int) -> float:
    try:
        wait = float(response.headers.get("retry-after", ""))
    except ValueError:
        wait = 5.0 * attempt
    return min(wait + 0.5, _MAX_ASK_WAIT_SECONDS)


def _is_retryable(response: httpx.Response) -> bool:
    # A bare 429 is the app's deterministic budget-exceeded error; only a 429 with
    # Retry-After means a transient upstream rate limit worth waiting out.
    return response.status_code in _RETRYABLE_STATUS or (
        response.status_code == 429 and "retry-after" in response.headers
    )


def call_team(base_url: str, question: str, timeout: float = 30.0, max_retries: int = 4) -> dict:
    """Calls /ask, retrying transient 429/502/503/504 responses; latency covers the successful attempt only.

    Raises RateLimitStop if /ask is still transiently failing after `max_retries`, so the run
    stops (and can be resumed) instead of recording a zero score.
    """
    attempts = 0
    while True:
        attempts += 1
        start = time.perf_counter()
        try:
            response = httpx.post(f"{base_url}/ask", json={"question": question}, timeout=timeout)
            latency = time.perf_counter() - start
            if _is_retryable(response):
                try:
                    hint = float(response.headers.get("retry-after", ""))
                except ValueError:
                    hint = None
                if hint is not None and hint > _MAX_ASK_WAIT_SECONDS:
                    raise RateLimitStop(
                        f"/ask returned {response.status_code} asking to wait longer than "
                        f"{_MAX_ASK_WAIT_SECONDS:.0f}s (the app is likely out of Groq quota)",
                        hint,
                    )
                if attempts > max_retries:
                    raise RateLimitStop(
                        f"/ask still returned {response.status_code} after {max_retries} retries "
                        "(the app is likely rate-limited by Groq)",
                        hint,
                    )
                wait = _retry_wait_seconds(response, attempts)
                print(
                    f"  \u23F3 /ask returned {response.status_code}, retrying in {wait:.0f}s "
                    f"(attempt {attempts}/{max_retries})",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(wait)
                continue
            response.raise_for_status()
            body = response.json()
            sources = [{"document": s["document"], "section": s.get("section")} for s in body.get("sources", [])]
            return {
                "answer": body.get("answer", ""),
                "sources": sources,
                "latency": latency,
                "error": None,
                "attempts": attempts,
            }
        except RateLimitStop:
            raise
        except Exception as exc:  # noqa: BLE001 - a broken app must not crash the eval run
            latency = time.perf_counter() - start
            return {"answer": "", "sources": [], "latency": latency, "error": str(exc), "attempts": attempts}


def load_checkpoint(path: Path) -> dict[str, dict]:
    """Finished per-question records keyed by id; errored records are dropped so a resume retries them."""
    records: dict[str, dict] = {}
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            records[record["id"]] = record
    return {qid: r for qid, r in records.items() if r.get("error") is None}


def run_evaluation(
    questions: list,
    team_name: str,
    base_url: str,
    *,
    ask_timeout: float = 30.0,
    ask_retries: int = 4,
    pace: float = 0.0,
    done: dict[str, dict] | None = None,
    on_result: Callable[[dict], None] | None = None,
) -> dict:
    done = done or {}
    per_question = []
    total = len(questions)
    for index, q in enumerate(questions, start=1):
        if q["id"] in done:
            per_question.append(done[q["id"]])
            continue
        call = call_team(base_url, q["question"], timeout=ask_timeout, max_retries=ask_retries)
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
        record = {
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
        per_question.append(record)
        if on_result is not None:
            on_result(record)
        # Id only, never question text: progress lines must stay safe for hidden runs.
        outcome = f"ERROR: {_one_line(call['error'], 120)}" if call["error"] else f"{scores['weighted_total']:.2f}"
        print(f"[{index}/{total}] {q['id']} -> {outcome} ({call['latency']:.1f}s)", flush=True)
        if pace > 0:
            time.sleep(pace)

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
    parser.add_argument("--resume", default=None, metavar="RUN_ID", help="Continue an interrupted run, skipping finished questions")
    parser.add_argument("--ask-retries", type=int, default=4, help="Retries per /ask call on transient 429/502/503/504")
    parser.add_argument("--ask-timeout", type=float, default=30.0, help="Seconds to wait for each /ask response")
    parser.add_argument("--pace", type=float, default=0.0, help="Seconds to pause between questions")
    parser.add_argument("--no-judge-cache", action="store_true", help="Ignore and don't write the on-disk judge score cache")
    parser.add_argument("--debug", action="store_true", help="Print full tracebacks on unexpected failures")
    args = parser.parse_args()

    if not args.team:
        raise SystemExit("Team name is required: pass --team or set TEAM_NAME in .env.")
    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY is not set -- required by the LLM judge (see .env.example).")

    questions, question_set, is_hidden = resolve_questions(args.questions)
    if args.no_judge_cache:
        set_cache_enabled(False)

    if args.resume:
        run_id = args.resume
        if not _RUN_ID_RE.fullmatch(run_id):
            raise SystemExit(f"Invalid run id: {run_id!r}")
        out_dir = RESULTS_DIR / run_id
        state_path = out_dir / "run_state.json"
        if not state_path.exists():
            raise SystemExit(f"Nothing to resume: {state_path} not found.")
        saved_sha = json.loads(state_path.read_text(encoding="utf-8"))["question_set"]["sha256"]
        if saved_sha != question_set["sha256"]:
            raise SystemExit("Refusing to resume: the question set differs from the one this run started with.")
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        out_dir = RESULTS_DIR / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "run_state.json").write_text(
            json.dumps({"run_id": run_id, "question_set": question_set}), encoding="utf-8"
        )

    checkpoint_path = out_dir / "checkpoint.jsonl"
    done = load_checkpoint(checkpoint_path)
    if done:
        print(f"Resuming {run_id}: {len(done)}/{len(questions)} questions already scored.")

    def _checkpoint(record: dict) -> None:
        # Hidden-set question/gold text never touches disk, not even in the checkpoint.
        saved = _redact_record(record) if is_hidden else record
        with checkpoint_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(saved) + "\n")

    resume_cmd = f"python -m evaluation.evaluator --questions {args.questions} --resume {run_id}"
    try:
        results = run_evaluation(
            questions,
            args.team,
            args.base_url,
            ask_timeout=args.ask_timeout,
            ask_retries=args.ask_retries,
            pace=args.pace,
            done=done,
            on_result=_checkpoint,
        )
    except KeyboardInterrupt:
        raise SystemExit(f"\nInterrupted. Finished questions are saved; continue with:\n  {resume_cmd}") from None
    except RateLimitStop as exc:
        when = f" Try again in ~{_fmt_duration(exc.retry_after)}." if exc.retry_after else ""
        saved = len(load_checkpoint(checkpoint_path))
        print(
            f"\n\u23F8\uFE0F  Stopped: {exc.reason}.{when}\n"
            f"   {saved}/{len(questions)} questions saved; continue with:\n  {resume_cmd}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_RATE_LIMITED) from None
    except Exception as exc:  # noqa: BLE001 - report cleanly; --debug shows the traceback
        if args.debug:
            traceback.print_exc()
        print(
            f"\n\u274C Run failed: {type(exc).__name__}: {_one_line(str(exc))}\n"
            f"   Finished questions are saved; continue with:\n  {resume_cmd}"
            + ("" if args.debug else "\n   (rerun with --debug for the full traceback)"),
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    output_results = redact_results(results) if is_hidden else results

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

    errored_ids = [r["id"] for r in output_results[args.team]["per_question"] if r["error"]]
    if errored_ids:
        print(
            f"\n\u26A0\uFE0F  {len(errored_ids)} question(s) errored and scored 0: {', '.join(errored_ids)}",
            file=sys.stderr,
        )

    if not is_hidden:
        print("\u2139\uFE0F  Public run \u2014 not submitted (only hidden runs count toward the leaderboard).")
    elif args.no_submit:
        print("\u23ED\uFE0F  Skipped submission (--no-submit).")
    elif errored_ids and not args.dry_run:
        print(
            f"\u274C Not submitting a run with errored questions. Fix the app, then retry them with:\n  {resume_cmd}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    else:
        try:
            submit_results(out_dir / "results.json", dry_run=args.dry_run)
        except SubmissionError as exc:
            raise SystemExit(f"\u274C {exc}") from exc


if __name__ == "__main__":
    main()
