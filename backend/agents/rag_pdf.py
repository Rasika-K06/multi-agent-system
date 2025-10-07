import asyncio
import fitz  # PyMuPDF
import os
import time
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
        # TODO: maybe move this to a separate script?
        # create sample PDFs if they don't exist yet
        topics = [
            # NebulaByte AI Dialogs (3 PDFs)
            ("dialog1.pdf", "RAG benefits", [
                "A: What are the benefits of RAG?",
                "B: It grounds LLMs with retrieval, improving factuality.",
                "A: How about performance?",
                "B: With FAISS and MiniLM embeddings, it's fast and lightweight.",
            ]),
            ("dialog2.pdf", "Multi-agent routing", [
                "A: How to route queries in a multi-agent setup?",
                "B: Combine rule-based hints with an LLM controller.",
                "A: Why use multiple agents?",
                "B: Specialization enables better accuracy per domain: PDFs, research papers, real-time news.",
            ]),
            ("dialog3.pdf", "Controller design", [
                "A: What rules should the controller have?",
                "B: PDF summarize -> RAG; recent papers -> ArXiv; latest news -> Web.",
                "A: How does the LLM help?",
                "B: It handles ambiguous queries and can call multiple agents in parallel.",
            ]),
            
            # Solar Industries India Limited Context (2 PDFs)
            ("solar_overview.pdf", "Solar Industries Overview", [
                "Company: Solar Industries India Limited",
                "Founded: 1995 | HQ: Nagpur, Maharashtra",
                "Business: India's largest private sector manufacturer of industrial explosives and propellants.",
                "",
                "Product Lines:",
                "- Bulk explosives (ANFO, emulsions, SME)",
                "- Packaged explosives (cartridges, detonators, boosters)",
                "- Initiating systems (electronic, non-electric detonators)",
                "- Defense products (propellants, warheads, ammunition)",
                "",
                "Technology Focus:",
                "- Advanced blasting solutions for mining, infrastructure, defense",
                "- R&D in energetic materials, precision munitions",
                "- Automation in manufacturing for safety and efficiency",
                "",
                "Industry: Explosives manufacturing requires extreme safety, regulatory compliance,",
                "and continuous innovation in chemistry and materials science.",
            ]),
            ("solar_ai_applications.pdf", "AI/ML at Solar Industries", [
                "AI/ML Applications in Explosives & Defense Manufacturing:",
                "",
                "1. Predictive Maintenance:",
                "   - ML models monitor equipment health (mixers, conveyor systems)",
                "   - Reduces downtime, prevents hazardous failures",
                "",
                "2. Quality Control:",
                "   - Computer vision inspects detonator assembly, cartridge consistency",
                "   - Anomaly detection in chemical composition via spectroscopy data",
                "",
                "3. Supply Chain Optimization:",
                "   - Demand forecasting for explosives (mining seasonality, infrastructure projects)",
                "   - Route optimization for safe transport of hazardous materials",
                "",
                "4. R&D Acceleration:",
                "   - NLP for patent/research paper analysis (energetic materials, propellants)",
                "   - Molecular simulation for new explosive formulations",
                "",
                "5. Safety & Compliance:",
                "   - Document management systems for regulatory filings",
                "   - Real-time monitoring of safety protocols via IoT + AI",
                "",
                "Potential: Multi-agent systems could unify technical docs, track industry research,",
                "and provide instant answers to engineers across manufacturing sites.",
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
            page.insert_text((72, 72), content, fontsize=12)
            doc.save(str(path))
            doc.close()
            LOGGER.info("pdf.generated", file=str(path))

    async def build_or_load_index(self) -> None:
        # just rebuild everything on startup (simpler than persistence)
        pdf_files = sorted(self.sample_dir.glob("*.pdf"))
        all_chunks: List[str] = []
        all_metas: List[Dict[str, Any]] = []
        for pdf in pdf_files:
            texts = self._extract_pdf_text(pdf)
            chunks = self.splitter.split_text(texts)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metas.append({
                    "source": pdf.name,
                    "chunk": i,
                    "timestamp": 0,  # sample files get low priority
                    "is_sample": True,
                })
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
        upload_time = time.time()
        docs = [
            Document(
                text=c,
                metadata={
                    "source": Path(path).name,
                    "chunk": i,
                    "timestamp": upload_time,
                    "is_sample": False,
                },
            )
            for i, c in enumerate(chunks)
        ]
        self.store.add(embeddings, docs)
        LOGGER.info("rag.pdf_ingested", file=str(path), chunks=len(chunks))

    async def retrieve(self, query: str, k: int = 5) -> List[Tuple[float, Document]]:
        q_emb = self._embed([query])[0]
        # get 3x candidates so we can re-rank them
        candidates = self.store.search(q_emb, k=k * 3)
        # boost user uploads over sample files
        reranked = []
        for score, doc in candidates:
            boost = 0.0
            # user uploads get a big boost
            if not doc.metadata.get("is_sample", False):
                boost += 0.3
            # newer uploads get higher score
            ts = doc.metadata.get("timestamp", 0)
            if ts > 0:
                age_hours = (time.time() - ts) / 3600
                recency_boost = max(0, 0.2 * (1.0 - age_hours / 168))  # decays over ~1 week
                boost += recency_boost
            adjusted_score = score + boost
            reranked.append((adjusted_score, doc))
        # sort and return top k
        reranked.sort(key=lambda x: x[0], reverse=True)
        return reranked[:k]
