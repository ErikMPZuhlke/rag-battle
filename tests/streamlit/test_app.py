"""Streamlit AppTest coverage for app/ui/streamlit_app.py, with the API mocked out.

AppTest execs the script under sys.modules["__main__"] on every run, a
different module object than the one `import streamlit_app` gives us, so
patching "streamlit_app.query_api" would silently miss the real call. We
patch `httpx.post` instead, since `httpx` is a single shared module object.
"""
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")

FAKE_RESPONSE = {
    "answer": "Employees get 20 days of PTO per year.",
    "sources": [{"document": "people/time-off.md", "section": "Annual leave"}],
}


def test_chat_renders_answer_and_sources():
    at = AppTest.from_file(APP_PATH)
    at.run()

    fake_response = Mock(spec=httpx.Response)
    fake_response.raise_for_status = Mock()
    fake_response.json.return_value = FAKE_RESPONSE
    with patch("httpx.post", return_value=fake_response):
        at.chat_input[0].set_value("How much PTO do I get?").run()

    assert at.error == []
    markdown_text = "\n".join(md.value for md in at.markdown)
    assert FAKE_RESPONSE["answer"] in markdown_text
    assert "time-off.md" in markdown_text


def test_chat_shows_error_on_api_failure():
    at = AppTest.from_file(APP_PATH)
    at.run()

    with patch("httpx.post", side_effect=httpx.ConnectError("boom")):
        at.chat_input[0].set_value("Anything?").run()

    assert at.exception == []
    assert len(at.error) == 1
    assert "boom" in at.error[0].value
