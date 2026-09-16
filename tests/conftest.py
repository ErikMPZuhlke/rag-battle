"""Shared fixtures for the app test suite."""
import sys
from pathlib import Path

# Guarantee `app` is importable regardless of pytest's per-directory import-mode resolution.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
