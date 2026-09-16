"""Subprocess fixtures that boot a real API + Streamlit app for e2e tests.

Uses non-default ports so these tests don't collide with the "Run API" task
or a developer's already-running dev server.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
API_PORT = 8123
STREAMLIT_PORT = 8523
API_BASE_URL = f"http://127.0.0.1:{API_PORT}"
STREAMLIT_BASE_URL = f"http://127.0.0.1:{STREAMLIT_PORT}"


def _wait_for_http(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            httpx.get(url, timeout=2.0)
            return
        except httpx.HTTPError as exc:
            last_error = exc
            time.sleep(0.5)
    raise TimeoutError(f"{url} did not become ready in {timeout}s: {last_error}")


def _wait_for_port(host: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"{host}:{port} did not accept connections in {timeout}s")


@pytest.fixture(scope="session")
def api_server():
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(API_PORT)],
        cwd=REPO_ROOT,
    )
    try:
        _wait_for_http(f"{API_BASE_URL}/health")
        yield API_BASE_URL
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.fixture(scope="session")
def streamlit_server(api_server):
    env = {**os.environ, "API_BASE_URL": api_server}
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app/ui/streamlit_app.py",
            "--server.port",
            str(STREAMLIT_PORT),
            "--server.headless",
            "true",
            "--server.address",
            "127.0.0.1",
        ],
        cwd=REPO_ROOT,
        env=env,
    )
    try:
        _wait_for_port("127.0.0.1", STREAMLIT_PORT)
        _wait_for_http(STREAMLIT_BASE_URL)
        yield STREAMLIT_BASE_URL
    finally:
        process.terminate()
        process.wait(timeout=10)
