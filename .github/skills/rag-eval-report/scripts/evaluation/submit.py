"""Submits a hidden-run results.json to the Leaderboard's public /submit channel.

Reads LEADERBOARD_SUBMIT_URL and LEADERBOARD_SUBMIT_TOKEN from the environment
(.env). The request body is posted byte-for-byte from results.json, so the
redaction already applied by evaluator.redact_results travels with it --
question/gold-answer text for hidden questions never leaves this machine.

Usage:
    python -m evaluation.submit --results evaluation/results/<run_id>/results.json
    python -m evaluation.submit --results ... --dry-run
"""
import argparse
import json
import os
import time
from pathlib import Path

import httpx

_MAX_ATTEMPTS = 3
_DEFAULT_RETRY_AFTER = 5.0


class SubmissionError(RuntimeError):
    """Raised when the leaderboard rejects a submission or retries are exhausted."""


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise SystemExit(f"{name} is not set -- required to submit to the leaderboard (see .env.example).")
    return value


def _extract_reason(response: httpx.Response) -> str:
    try:
        return response.json().get("reason", response.text)
    except ValueError:
        return response.text


def submit_results(results_path: Path, *, dry_run: bool = False) -> dict | None:
    """POSTs results_path's raw bytes to the leaderboard. Returns the parsed
    response on success (202), or None for a dry run. Raises SubmissionError on
    a non-retryable rejection (400/401/413) or once retries are exhausted."""
    body = Path(results_path).read_bytes()

    if dry_run:
        print(f"[dry-run] Would POST {len(body)} bytes to <LEADERBOARD_SUBMIT_URL>/submit:")
        print(json.dumps(json.loads(body), indent=2))
        return None

    url = _require_env("LEADERBOARD_SUBMIT_URL").rstrip("/") + "/submit"
    token = _require_env("LEADERBOARD_SUBMIT_TOKEN")
    headers = {"Content-Type": "application/json", "X-Submit-Token": token}

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = httpx.post(url, content=body, headers=headers, timeout=15.0)
        except httpx.HTTPError as exc:
            if attempt >= _MAX_ATTEMPTS:
                raise SubmissionError(f"Network error submitting to leaderboard: {exc}") from exc
            time.sleep(_DEFAULT_RETRY_AFTER)
            continue

        if response.status_code == 202:
            print(f"\u2705 Submitted to leaderboard ({url}) -- accepted.")
            return response.json()

        if response.status_code in (429, 503) and attempt < _MAX_ATTEMPTS:
            retry_after = float(response.headers.get("Retry-After", _DEFAULT_RETRY_AFTER))
            print(f"\u23F3 Leaderboard returned {response.status_code}; retrying in {retry_after:.0f}s "
                  f"(attempt {attempt}/{_MAX_ATTEMPTS})...")
            time.sleep(retry_after)
            continue

        raise SubmissionError(f"Leaderboard rejected submission: HTTP {response.status_code} ({_extract_reason(response)})")

    raise SubmissionError("Leaderboard submission failed after all retries.")


def main():
    parser = argparse.ArgumentParser(description="Submit a results.json to the leaderboard's /submit endpoint.")
    parser.add_argument("--results", required=True, help="Path to a results.json file to submit")
    parser.add_argument("--dry-run", action="store_true", help="Print the request instead of sending it")
    args = parser.parse_args()
    submit_results(Path(args.results), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
