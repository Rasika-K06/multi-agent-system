import asyncio
import fitz  # PyMuPDF
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from backend.vectorstore.faiss_store import FAISSStore, Document
from backend.utils.logging import get_logger


LOGGER = get_logger()


class PDFRAGAgent:
    def __init__(self, sample_dir: Path):
        self.sample_dir = Path(sample_dir)
        self.embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.dim = self.embed_model.get_sentence_embedding_dimension()
        self.store = FAISSStore(dim=self.dim)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    async def ensure_sample_pdfs(self) -> None:
        # Generate 5 small PDFs with fictional dialogs if missing
        topics = [
            ("dialog1.pdf", "RAG benefits", [
                "A: What are the benefits of RAG?",
                "B: It grounds LLMs with retrieval, improving factuality.",
                "A: How about performance?",
                "B: With FAISS and MiniLM embeddings, it's fast and lightweight.",
            ]),
            ("dialog2.pdf", "Multi-agent routing", [
                "A: How to route queries in a multi-agent setup?",
                "B: Combine rule-based hints with an LLM controller.",
            ]),
            ("dialog3.pdf", "Controller design", [
                "A: What rules should the controller have?",
                "B: PDF summarize -> RAG; recent papers -> ArXiv; latest news -> Web.",
            ]),
            ("dialog4.pdf", "ArXiv scanning strategies", [
                "A: How to find recent papers efficiently?",
                "B: Use the arxiv API with query filters and summarize abstracts.",
            ]),
            ("dialog5.pdf", "Web search vs. curated corpora", [
                "A: When to use web search?",
                "B: For latest developments; curated corpora for depth and reliability.",
            ]),
        ]
        self.sample_dir.mkdir(parents=True, exist_ok=True)
        for filename, title, lines in topics:
            path = self.sample_dir / filename
            if path.exists():
                continue
            doc = fitz.open()
            page = doc.new_page()
            content = f"NebulaByte Dialog — {title}\n\n" + "\n".join(lines)
            # Draw text
            page.insert_text((72, 72), content, fontsize=12)
            doc.save(str(path))
            doc.close()
            LOGGER.info("pdf.generated", file=str(path))

    async def build_or_load_index(self) -> None:
        # For simplicity, always rebuild on startup
        pdf_files = sorted(self.sample_dir.glob("*.pdf"))
        all_chunks: List[str] = []
        all_metas: List[Dict[str, Any]] = []
        for pdf in pdf_files:
            texts = self._extract_pdf_text(pdf)
            chunks = self.splitter.split_text(texts)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metas.append({"source": pdf.name, "chunk": i})
        if all_chunks:
            emb = self._embed(all_chunks)
            docs = [Document(text=t, metadata=m) for t, m in zip(all_chunks, all_metas)]
            self.store.add(emb, docs)
            LOGGER.info("rag.index_built", num_chunks=len(all_chunks))
        else:
            LOGGER.warn("rag.no_pdfs_found")

    def _extract_pdf_text(self, path: Path) -> str:
        try:
            with fitz.open(str(path)) as doc:
                texts = []
                for page_num, page in enumerate(doc):
                    t = page.get_text()
                    texts.append(f"[Page {page_num+1} of {path.name}]\n{t}")
                return "\n\n".join(texts)
        except Exception as e:
            LOGGER.error("pdf.extract_error", file=str(path), error=str(e))
            return ""

    def _embed(self, texts: List[str]) -> np.ndarray:
        vecs = self.embed_model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
        return vecs.astype(np.float32)

    async def ingest_pdf(self, path: Path) -> None:
        text = self._extract_pdf_text(path)
        if not text.strip():
            return
        chunks = self.splitter.split_text(text)
        embeddings = self._embed(chunks)
        docs = [Document(text=c, metadata={"source": Path(path).name}) for c in chunks]
        self.store.add(embeddings, docs)
        LOGGER.info("rag.pdf_ingested", file=str(path), chunks=len(chunks))

    async def retrieve(self, query: str, k: int = 5) -> List[Tuple[float, Document]]:
        q_emb = self._embed([query])[0]
        return self.store.search(q_emb, k=k)
