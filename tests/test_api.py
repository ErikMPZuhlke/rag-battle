"""Smoke tests for the /ask API contract. Requires the app to be running
(ingest the corpus first) or use TestClient against the FastAPI app directly."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_returns_contract_shape():
    response = client.post("/ask", json={"question": "What is the production deployment approval policy?"})
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "sources" in body
    assert isinstance(body["sources"], list)
    for source in body["sources"]:
        assert "document" in source


def test_ask_rejects_empty_question():
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422
