"""End-to-end browser test: real API + real Streamlit app + real LLM call.

Requires the corpus to be ingested and GROQ_API_KEY set (see the "Ingest
corpus" task and .env.example), same as tests/integration/test_ask_api.py.
Run `playwright install chromium` once before executing this suite.
"""
from playwright.sync_api import Page, expect


def test_chat_question_returns_answer(streamlit_server: str, page: Page):
    page.goto(streamlit_server)

    chat_input = page.get_by_placeholder("Ask a question about Acme Cloud...")
    expect(chat_input).to_be_visible(timeout=15000)
    chat_input.fill("What is the production deployment approval policy?")
    chat_input.press("Enter")

    answer = page.locator('[data-testid="stChatMessage"]').last
    expect(answer).to_be_visible(timeout=30000)
    expect(answer).not_to_contain_text("Could not reach the API")
