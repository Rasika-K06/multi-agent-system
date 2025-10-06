import io
from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from backend.main import app, SAMPLE_PDFS_DIR

client = TestClient(app)


def test_root_serves_frontend():
    r = client.get("/")
    assert r.status_code == 200


def test_ask_basic_query():
    r = client.post("/ask", json={"query": "What are the recent developments in Groq?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert isinstance(data.get("agents_used", []), list)
    assert isinstance(data.get("rationale", ""), str)


def test_upload_pdf_and_ask_summary():
    # Generate a small in-memory PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72,72), "Test PDF: Summarize this content about multi-agent systems.")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    r = client.post("/upload_pdf", files=files)
    assert r.status_code == 200

    # Now ask to summarize
    r2 = client.post("/ask", json={"query": "Summarize this"})
    assert r2.status_code == 200


def test_logs_endpoint():
    r = client.get("/logs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
