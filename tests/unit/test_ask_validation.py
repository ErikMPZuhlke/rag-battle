"""Request-schema validation for /ask -- no LLM/corpus dependency (fails before business logic runs)."""


def test_ask_rejects_empty_question(client):
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422
