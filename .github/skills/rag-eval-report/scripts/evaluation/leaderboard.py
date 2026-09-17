"""Writes an evaluation run's results.json (the same payload submitted to the
leaderboard) to disk."""
import json
from pathlib import Path


def write_results(results: dict, out_dir: Path, meta: dict | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta or {}, "teams": results}
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
