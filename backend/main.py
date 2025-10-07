import os
import json
import uuid
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.models import AskRequest, AskResponse
from backend.agents.controller import ControllerAgent
from backend.agents.rag_pdf import PDFRAGAgent
from backend.utils.logging import get_logger, Tracer


def cleanup_old_uploads(uploads_dir: Path, max_age_hours: int = 24) -> None:
    # delete old PDFs to avoid filling up disk
    if not uploads_dir.exists():
        return
    cutoff = time.time() - (max_age_hours * 3600)
    count = 0
    for pdf_file in uploads_dir.glob("*.pdf"):
        try:
            if pdf_file.stat().st_mtime < cutoff:
                pdf_file.unlink()
                count += 1
        except Exception as e:
            logger.warn("cleanup.failed", file=str(pdf_file), error=str(e))
    if count > 0:
        logger.info("cleanup.completed", removed=count)

load_dotenv()

APP_ROOT = Path(__file__).resolve().parents[1]

# try to load .env if it exists
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=APP_ROOT / ".env", override=False)
except Exception:
    pass

FRONTEND_DIR = APP_ROOT / "frontend"
LOGS_DIR = APP_ROOT / "logs"
UPLOADS_DIR = APP_ROOT / "uploads"
SAMPLE_PDFS_DIR = APP_ROOT / "sample_pdfs"

app = FastAPI(title="Problem 2 — Multi-Agentic System")

# create dirs if needed
LOGS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_PDFS_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger()
tracer = Tracer(LOGS_DIR / "traces.json")

# agents get initialized in startup event
controller: Optional[ControllerAgent] = None
pdf_rag: Optional[PDFRAGAgent] = None


@app.on_event("startup")
async def on_startup():
    global controller, pdf_rag
    
    cleanup_old_uploads(UPLOADS_DIR)
    
    # setup RAG agent with sample PDFs
    pdf_rag = PDFRAGAgent(sample_dir=SAMPLE_PDFS_DIR)
    await pdf_rag.ensure_sample_pdfs()
    await pdf_rag.build_or_load_index()

    # setup controller
    controller = ControllerAgent(pdf_agent=pdf_rag, tracer=tracer)
    logger.info("app.startup", msg="Application started and agents initialized")

    # static files for the frontend
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>Frontend missing</h1>", status_code=200)
    return FileResponse(str(index_path))


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, request: Request):
    if controller is None:
        raise HTTPException(status_code=503, detail="Controller not ready")
    try:
        answer, agents_used, rationale, trace_id = await controller.handle_query(req.query, client_ip=request.client.host if request.client else "unknown")
        return AskResponse(answer=answer, agents_used=agents_used, rationale=rationale, trace_id=trace_id)
    except Exception as e:
        logger.error("ask.error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")


MAX_UPLOAD = 10 * 1024 * 1024  # 10MB


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type; only PDF allowed")

    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # save temporarily
    file_id = str(uuid.uuid4())
    dest = UPLOADS_DIR / f"{file_id}.pdf"
    with open(dest, "wb") as f:
        f.write(data)

    # ingest into RAG, then delete file
    try:
        if pdf_rag is None:
            raise HTTPException(status_code=503, detail="RAG not ready")
        await pdf_rag.ingest_pdf(dest)
    finally:
        try:
            dest.unlink(missing_ok=True)
        except Exception:
            pass

    return {"status": "ingested", "file_id": file_id}


@app.get("/logs")
async def get_logs():
    return tracer.read_all()


@app.get("/logs/{trace_id}")
async def get_log(trace_id: str):
    entry = tracer.read_one(trace_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    return entry
