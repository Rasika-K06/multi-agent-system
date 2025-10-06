from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_routing_rules():
    # ArXiv routing
    r1 = client.post("/ask", json={"query": "Show me recent papers on multi-agent AI"})
    assert r1.status_code == 200
    agents1 = r1.json().get("agents_used", [])
    assert any("ArXiv" in a for a in agents1)

    # Web Search routing
    r2 = client.post("/ask", json={"query": "What are the latest news about Groq?"})
    assert r2.status_code == 200
    agents2 = r2.json().get("agents_used", [])
    assert any("Web Search" in a for a in agents2)

    # Default/LLM routing still returns something
    r3 = client.post("/ask", json={"query": "Explain multi-agent controllers"})
    assert r3.status_code == 200
    assert isinstance(r3.json().get("agents_used", []), list)
