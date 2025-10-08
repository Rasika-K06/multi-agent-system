
# Multi-Agent System


A FastAPI-based multi-agent system that routes user queries to specialized agents (PDF RAG, Web Search, ArXiv) through a hybrid Controller Agent powered by Google Gemini AI.

---

## Key Features

* **Intelligent Routing** — Rule-based + LLM decision-making with logged rationales.
* **PDF RAG** — Upload and query PDFs with timestamp-based prioritization (recent uploads rank higher).
* **Multi-Agent System** — PDF RAG, Web Search (SerpAPI with DuckDuckGo fallback), and ArXiv research.
* **Production-Ready** — Structured logging, error handling, security controls, and automated cleanup.
* **Domain Relevance** — Includes Solar Industries demo PDFs for contextual evaluation.
* **Transparency** — Shows which agents were used and why for every query.

---

## What’s Inside

* **Backend:** FastAPI with `/ask`, `/upload_pdf`, and `/logs` endpoints.
* **Agents:** Controller (Gemini), PDF RAG (PyMuPDF + FAISS), Web Search, ArXiv.
* **Frontend:** Minimal UI (search box, PDF upload, results panel).
* **Logging:** `structlog` JSON traces in `logs/traces.json`.
* **Deployment:** Dockerfile for Hugging Face Spaces / Render.
* **Tests:** `pytest` suite for endpoints, routing, and RAG.
* **Sample Data:** 5 PDFs (3 AI dialogs + 2 Solar Industries domain files).

Demo (Hugging Face Spaces)

* Placeholder: [https://huggingface.co/spaces/your-username/multi-agent-system](https://huggingface.co/spaces/your-username/multi-agent-system)

---

## Features and Requirements

* **Controller Agent** uses rules + Gemini LLM to decide which agent(s) to call and logs the rationale.
* **PDF RAG Agent** supports uploads with validation (<= 10MB), chunking (`chunk_size=1000`, `overlap=200`), and FAISS embeddings (`all-MiniLM-L6-v2`).
* **Web Search Agent** uses SerpAPI, falling back to DuckDuckGo Instant Answer if SerpAPI is unavailable.
* **ArXiv Agent** fetches top 3 results via the `arxiv` library and summarizes them with the LLM.
* **Logging** is exposed via `/logs` endpoint.
* **Security**: Temporary PDF storage with deletion after ingest and a 24-hour retention/cleanup policy.

---

## Project Structure

```
backend/
├── main.py                # FastAPI app entry
├── models.py              # Pydantic schemas
├── agents/
│   ├── controller.py
│   ├── rag_pdf.py
│   ├── web_search.py
│   └── arxiv_agent.py
├── utils/
│   └── logging.py
├── vectorstore/
│   └── faiss_store.py
frontend/
├── index.html
└── static/
    ├── main.js
    └── styles.css
logs/
└── traces.json
sample_pdfs/               # Auto-generated on startup if missing
scripts/
└── generate_pdfs.py
tests/
├── test_api.py
├── test_controller.py
└── test_rag.py
Dockerfile
requirements.txt
.env.example
.gitignore
REPORT.md
```

---

## Setup

1. **Python 3.10+**
2. (Optional) Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Environment variables (set in system or `.env`, do not commit secrets):

```bash
GOOGLE_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.5-flash  # optional (default)
SERPAPI_API_KEY=your_serpapi_key  # optional (fallback to DuckDuckGo)
```

---

## Run Locally

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 7860
```

Open [http://localhost:7860](http://localhost:7860) to access the UI.

---

## API Endpoints

* **POST /ask**

  * Body: `{"query": "..."}`
  * Response: `{ "answer": str, "agents_used": list, "rationale": str }`

* **POST /upload_pdf**

  * Form: file (application/pdf, <=10MB)
  * Response: `{ "status": "ingested", "file_id": str }`

* **GET /logs**

  * Returns list of trace JSON objects.

* **GET /logs/{id}**

  * Returns a specific trace by id if available.

---

## Testing

Run tests:

```bash
pytest -q
```

---

## Deployment to Hugging Face Spaces

1. Create a new Space (Docker type) and push this repo.
2. Add Secrets:

   * `GOOGLE_API_KEY` (required)
   * `GEMINI_MODEL` (optional)
   * `SERPAPI_API_KEY` (optional)
3. Dockerfile starts `uvicorn` on port `7860`.

See `DEPLOYMENT.md` for detailed instructions.

---

## Example Queries

**General AI:**

* "Summarize uploaded PDF"
* "Recent papers on multi-agent AI"
* "Latest news on AI developments"

**Solar Industries Context:**

* "What AI/ML applications does Solar Industries use?"
* "Tell me about Solar Industries' technology focus"
* "What are the challenges in explosives manufacturing?"

---

## Notes

* If `GOOGLE_API_KEY` is missing, the system returns graceful mock outputs to remain functional.
* SerpAPI falls back to DuckDuckGo Instant Answer when rate limited or missing key.
* 5 sample PDFs (3 AI + 2 Solar Industries) are generated programmatically on startup if missing.
* Recently uploaded PDFs are prioritized over sample files in search results.

---

## Sample PDFs Included

### AI Topics (NebulaByte Dialogs)

1. RAG benefits & performance
2. Multi-agent routing strategies
3. Controller design & LLM integration

### Solar Industries Context

4. Company overview (products, technology, industry)
5. AI/ML applications in explosives & defense manufacturing

---

## Why This Matters for Solar Industries

This system demonstrates how multi-agent AI can:

* Organize technical documentation (safety manuals, product specs)
* Track R&D developments (ArXiv papers on explosives, materials science)
* Monitor market intelligence (industry news, competitor analysis)
* Answer employee queries instantly from company knowledge base



---


