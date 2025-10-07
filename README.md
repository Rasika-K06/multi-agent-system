# Multi-Agentic System with Dynamic Decision Making

**Built for Solar Industries India Limited AIML Assessment**

A FastAPI project that routes user queries to specialized agents (PDF RAG, Web Search, ArXiv) using a hybrid Controller Agent powered by Google Gemini AI.

## Key Features

- **Intelligent Routing**: Hybrid rule-based + LLM decision-making with detailed rationales
- **PDF RAG**: Upload & query PDFs with timestamp-based prioritization (recent uploads rank higher)
- **Multi-Agent System**: PDF RAG, Web Search (SerpAPI + DuckDuckGo fallback), ArXiv research
- **Production-Ready**: Complete logging, error handling, security measures, automated cleanup
- **Solar Industries Context**: Includes company-specific demo PDFs for domain relevance
- **Transparent**: Shows which agents were used and WHY for every query

## What's Inside

- Backend: FastAPI with /ask, /upload_pdf, /logs endpoints
- Agents: Controller (Gemini), PDF RAG (PyMuPDF + FAISS), Web Search, ArXiv
- Frontend: Minimalist UI (search box, PDF upload, results)
- Logging: structlog JSON traces (logs/traces.json)
- Deployment: Dockerfile for HF Spaces/Render
- Tests: pytest suite for endpoints, routing, RAG
- Sample Data: 5 PDFs (3 AI dialogs + 2 Solar Industries context)

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

- Set GOOGLE_API_KEY and (optionally) SERPAPI_API_KEY in environment or a .env file (do not commit secrets):

```bash
GOOGLE_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.5-flash  # optional, this is default
SERPAPI_API_KEY=your_serpapi_key  # optional, falls back to DuckDuckGo
```

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
- Add Secrets: GOOGLE_API_KEY (required), GEMINI_MODEL (optional), SERPAPI_API_KEY (optional)
- The Dockerfile will start uvicorn on port 7860
- See DEPLOYMENT.md for detailed instructions

Example Queries

**General AI:**
- "Summarize uploaded PDF"
- "Recent papers on multi-agent AI"
- "Latest news on AI developments"

**Solar Industries Context:**
- "What AI/ML applications does Solar Industries use?"
- "Tell me about Solar Industries' technology focus"
- "What are the challenges in explosives manufacturing?"

Notes

- If GOOGLE_API_KEY is missing, the system returns graceful mock outputs to remain functional
- SerpAPI falls back to DuckDuckGo Instant Answer if rate limited or missing key
- 5 sample PDFs (3 AI + 2 Solar Industries) are generated programmatically on startup if missing
- Recently uploaded PDFs are automatically prioritized over sample files in search results

## Sample PDFs Included

**AI Topics (NebulaByte Dialogs):**
1. RAG benefits & performance
2. Multi-agent routing strategies
3. Controller design & LLM integration

**Solar Industries Context:**
4. Company overview (products, technology, industry)
5. AI/ML applications in explosives & defense manufacturing

## Why This Matters for Solar Industries

This system demonstrates how multi-agent AI can:
- **Organize technical documentation** (safety manuals, product specs)
- **Track R&D developments** (ArXiv papers on explosives, materials science)
- **Monitor market intelligence** (industry news, competitor analysis)
- **Answer employee queries** instantly from company knowledge base

The included Solar Industries PDFs show domain research and relevance to your business.

---

**Built for Solar Industries India Limited AIML Assessment | January 2025**
