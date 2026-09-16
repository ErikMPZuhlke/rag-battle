"""Full-stack smoke tests for the /ask API contract. Requires the corpus to be
ingested and GROQ_API_KEY set (see the "Ingest corpus" task and .env.example)."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_returns_contract_shape(client):
    response = client.post("/ask", json={"question": "What is the production deployment approval policy?"})
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "sources" in body
    assert isinstance(body["sources"], list)
    for source in body["sources"]:
        assert "document" in source
