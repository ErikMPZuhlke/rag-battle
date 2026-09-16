"""Loads the frozen hidden question set (a compiled native module) and
verifies its integrity before handing questions to the evaluator.

The plaintext hidden_questions.json never ships in the repo; only the
compiled `_hidden_frozen` extension module under `assets/` does (see
tools/build_hidden.py). Every access here re-verifies the embedded sha256
so a tampered or stale binary is caught instead of silently scoring against
the wrong question set.
"""
import hashlib
import json
import sys
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


def _import_frozen():
    assets_str = str(ASSETS_DIR)
    if assets_str not in sys.path:
        sys.path.insert(0, assets_str)
    try:
        import _hidden_frozen  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Frozen hidden question module not found. Build it first with "
            "`python -m evaluation.tools.build_hidden` (organizer-only, requires the "
            "private hidden_questions.json)."
        ) from exc
    return _hidden_frozen


def _verify(frozen) -> None:
    canonical = json.dumps(frozen.QUESTIONS, sort_keys=True, separators=(",", ":")).encode("utf-8")
    actual = hashlib.sha256(canonical).hexdigest()
    if actual != frozen.QUESTIONS_SHA256:
        raise RuntimeError(
            "Hidden question set failed integrity verification: the frozen module's "
            "content does not match its embedded checksum. Rebuild it with "
            "`python -m evaluation.tools.build_hidden`."
        )


def load_hidden_questions() -> list:
    """Returns the hidden question list, verified against its embedded checksum."""
    frozen = _import_frozen()
    _verify(frozen)
    return frozen.QUESTIONS


def hidden_fingerprint() -> dict:
    """A tamper-evident summary safe to publish in results/reports (no question text)."""
    frozen = _import_frozen()
    _verify(frozen)
    return {"name": "hidden", "sha256": frozen.QUESTIONS_SHA256, "count": frozen.QUESTION_COUNT}
