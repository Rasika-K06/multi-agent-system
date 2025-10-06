from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import faiss  # type: ignore
import numpy as np


@dataclass
class Document:
    text: str
    metadata: Dict[str, Any]


class FAISSStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self._texts: List[str] = []
        self._metas: List[Dict[str, Any]] = []
        self._norm = True  # cosine via normalized dot-product

    @staticmethod
    def _normalize(x: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(x, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return x / norms

    def add(self, embeddings: np.ndarray, docs: List[Document]) -> None:
        if embeddings.ndim != 2 or embeddings.shape[1] != self.dim:
            raise ValueError("Embedding dimension mismatch")
        vecs = self._normalize(embeddings.astype(np.float32)) if self._norm else embeddings.astype(np.float32)
        self.index.add(vecs)
        for d in docs:
            self._texts.append(d.text)
            self._metas.append(d.metadata)

    def search(self, query_emb: np.ndarray, k: int = 5) -> List[Tuple[float, Document]]:
        q = query_emb.astype(np.float32)
        if q.ndim == 1:
            q = q[None, :]
        qn = self._normalize(q) if self._norm else q
        scores, idxs = self.index.search(qn, k)
        results: List[Tuple[float, Document]] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append((float(score), Document(text=self._texts[idx], metadata=self._metas[idx])))
        return results
