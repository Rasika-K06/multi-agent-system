import fitz
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_rag_retrieval_after_sample_generation():
    # Ensure sample PDFs exist via startup; ask something that likely hits RAG
    r = client.post("/ask", json={"query": "What are the benefits of RAG?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert isinstance(data.get("agents_used", []), list)
