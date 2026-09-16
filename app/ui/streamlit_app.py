"""Streamlit chat UI for the Acme Cloud Knowledge Assistant `/ask` API."""
import os

import httpx
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 30.0


def query_api(question: str) -> dict:
    """POST the question to /ask and return the parsed {answer, sources} payload."""
    response = httpx.post(
        f"{API_BASE_URL}/ask", json={"question": question}, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for source in sources:
            label = source["document"]
            if source.get("section"):
                label += f" — {source['section']}"
            st.markdown(f"- {label}")


st.set_page_config(page_title="Acme Cloud Knowledge Assistant", page_icon="💬")
st.title("💬 Acme Cloud Knowledge Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []))

question = st.chat_input("Ask a question about Acme Cloud...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            payload = query_api(question)
            answer = payload["answer"]
            sources = payload.get("sources", [])
            st.markdown(answer)
            render_sources(sources)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                message = "Question budget exceeded for this request — please try again."
            else:
                message = f"API error ({exc.response.status_code}): {exc.response.text}"
            st.error(message)
            st.session_state.messages.append({"role": "assistant", "content": message})
        except httpx.HTTPError as exc:
            message = f"Could not reach the API at {API_BASE_URL}: {exc}"
            st.error(message)
            st.session_state.messages.append({"role": "assistant", "content": message})
