# Problem 2 — Multi-Agentic System with Dynamic Decision Making

A complete, production-grade FastAPI project that routes user queries to a dynamic set of agents (PDF RAG, Web Search, ArXiv) using a Controller Agent powered by Groq (llama3-70b-8192). Includes:

- Backend (FastAPI) with endpoints: /ask, /upload_pdf, /logs
- Agents: Controller, PDF RAG (PyMuPDF + FAISS + Sentence-Transformers), Web Search (SerpAPI -> DuckDuckGo fallback), ArXiv (arxiv lib)
- Frontend: Minimal HTML/JS (search box, PDF upload, results)
- Logging: structlog JSON traces persisted to logs/traces.json
- Deployment: Dockerfile for Hugging Face Spaces
- Tests: pytest for endpoints, routing, and RAG ingest
- Report: REPORT.md (export to PDF)
- Sample data: Generated NebulaByte PDFs on startup if missing

Demo (Hugging Face Spaces)

- Placeholder: https://huggingface.co/spaces/your-username/problem-2-multi-agentic

Features and Requirements

- Controller Agent uses rules + Groq LLM to decide which agent(s) to call, logs rationale
- PDF RAG Agent supports uploads with validation and size limit (10MB), chunks (1000, overlap 200), FAISS embeddings (all-MiniLM-L6-v2)
- Web Search via SerpAPI (fallback to DuckDuckGo Instant Answer if rate limited/missing key)
- ArXiv Agent fetches top 3 with arxiv library and summarizes via LLM
- Logs exposed via /logs endpoint
- Security: Temporary PDF storage, deletion post-ingest, retention policy (24h cleanup)

Project Structure

- backend/
  - main.py (FastAPI app, routes)
  - models.py (Pydantic schemas)
  - agents/
    - controller.py
    - rag_pdf.py
    - web_search.py
    - arxiv_agent.py
  - utils/
    - logging.py
  - vectorstore/
    - faiss_store.py
- frontend/
  - index.html
  - static/
    - main.js
    - styles.css
- logs/
  - traces.json
- sample_pdfs/
  - Generated on startup if missing
- scripts/
  - generate_pdfs.py
- tests/
  - test_api.py
  - test_controller.py
  - test_rag.py
- Dockerfile
- requirements.txt
- .env.example
- .gitignore
- REPORT.md

Setup

1) Python 3.10+
2) Create and activate a virtualenv (optional)
3) Install dependencies

- pip install -r requirements.txt

4) Environment variables

- Set GROQ_API_KEY and (optionally) SERPAPI_API_KEY in environment or a .env file (do not commit secrets):

- GROQ_API_KEY=your_key_here
- SERPAPI_API_KEY=your_key_here

Run locally

- uvicorn backend.main:app --host 0.0.0.0 --port 7860

Open http://localhost:7860 to access the minimal UI.

API Endpoints

- POST /ask
  - Body: {"query": "..."}
  - Response: {"answer": str, "agents_used": list, "rationale": str}
- POST /upload_pdf
  - Form: file (application/pdf, <=10MB)
  - Response: {"status": "ingested", "file_id": str}
- GET /logs
  - Returns list of trace JSON objects
- GET /logs/{id}
  - Returns a specific trace by id (if available)

Testing

- pytest -q

Deployment to Hugging Face Spaces

- Create a new Space (Docker type) and push this repo
- Add Secrets: GROQ_API_KEY, SERPAPI_API_KEY
- The Dockerfile will start uvicorn on port 7860

Example Queries

- "Summarize uploaded PDF"
- "Recent papers on multi-agent AI"
- "Latest news on Groq"

Notes

- If GROQ_API_KEY is missing, the system returns graceful mock outputs to remain functional
- SerpAPI falls back to DuckDuckGo Instant Answer if rate limited or missing key
- PDFs are generated programmatically if not found in sample_pdfs/ on startup
