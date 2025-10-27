from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB adapter. Uses HTTP client if CHROMA_URL provided; else tries local client.

    Collection name: 'onboard_items'
    """

    def __init__(self, collection: str = "onboard_items"):
        self.collection_name = collection
        self._client = None
        self._collection = None

    def _ensure_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            chroma_url = os.environ.get("CHROMA_URL")
            if chroma_url:
                import chromadb  # type: ignore

                self._client = chromadb.HttpClient(
                    host=chroma_url.split("://")[-1].split(":")[0],
                    port=int(chroma_url.split(":")[-1]),
                )
            else:
                import chromadb  # type: ignore

                self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                self.collection_name, metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.warning("ChromaDB not available: %s", e)
            self._collection = None
        return self._collection

    def upsert(self, item_id: str, vector: np.ndarray, metadata: Dict) -> str:
        col = self._ensure_collection()
        if col is None:
            # No-op fallback: pretend success and return item_id
            return item_id
        vec_list = vector.tolist() if isinstance(vector, np.ndarray) else list(vector)
        try:
            col.upsert(ids=[item_id], embeddings=[vec_list], metadatas=[metadata])
        except Exception:
            # Some clients require 'documents' param; still best-effort
            col.upsert(
                ids=[item_id],
                embeddings=[vec_list],
                metadatas=[metadata],
                documents=[metadata.get("title", "")],
            )
        return item_id

    def query(self, vector: np.ndarray, top_k: int = 10) -> List[Dict]:
        col = self._ensure_collection()
        if col is None:
            return []
        vec_list = vector.tolist() if isinstance(vector, np.ndarray) else list(vector)
        res = col.query(
            query_embeddings=[vec_list],
            n_results=top_k,
            include=["metadatas", "distances", "embeddings", "ids"],
        )
        items: List[Dict] = []
        # distances for cosine space are 1 - cosine_similarity; convert to similarity
        ids = (res.get("ids") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        for i, vid in enumerate(ids):
            dist = dists[i] if i < len(dists) else None
            sim = 1.0 - float(dist) if dist is not None else 0.0
            md = metas[i] if i < len(metas) else {}
            items.append({"item_id": vid, "score": sim, "metadata": md})
        return items

    def get_vectors_for_items(
        self, item_ids: List[str]
    ) -> Dict[str, Optional[np.ndarray]]:
        col = self._ensure_collection()
        if col is None:
            return {iid: None for iid in item_ids}
        res = col.get(ids=item_ids, include=["embeddings", "metadatas", "ids"])  # type: ignore
        out: Dict[str, Optional[np.ndarray]] = {iid: None for iid in item_ids}
        ids = res.get("ids") or []
        embs = res.get("embeddings") or []
        for i, iid in enumerate(ids):
            emb = (
                np.array(embs[i], dtype=np.float32)
                if i < len(embs) and embs[i] is not None
                else None
            )
            out[iid] = emb
        return out
