from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, collection: str = "onboard_items"):
        self.collection_name = collection
        self._client = None
        self._collection = None

    def _ensure_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            # Single source of truth: CHROMA_URL
            # If unset, default to repo_root/app/configs (local persistent directory)
            repo_root = Path(__file__).resolve().parents[2]
            chroma_url = os.environ.get("CHROMA_URL") or str(
                repo_root / "app" / "configs"
            )

            import chromadb  # type: ignore

            if chroma_url.startswith("http://") or chroma_url.startswith("https://"):
                # Remote server via HTTP
                host = chroma_url.split("://")[-1].split(":")[0]
                # Default port 8000 if not provided
                port = 8000
                if ":" in chroma_url.split("://")[-1]:
                    try:
                        port = int(chroma_url.split(":")[-1])
                    except Exception:
                        port = 8000
                self._client = chromadb.HttpClient(host=host, port=port)
            else:
                # Filesystem path persistence
                chroma_dir = Path(chroma_url)
                chroma_dir.mkdir(parents=True, exist_ok=True)

                # Try modern PersistentClient, fallback to legacy Settings
                client = None
                try:
                    from chromadb import PersistentClient  # type: ignore

                    client = PersistentClient(path=str(chroma_dir))
                except Exception:
                    try:
                        from chromadb.config import Settings  # type: ignore

                        client = chromadb.Client(
                            Settings(
                                chroma_db_impl="duckdb+parquet",
                                persist_directory=str(chroma_dir),
                            )
                        )
                    except Exception:
                        client = chromadb.Client()

                self._client = client
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
            return item_id
        vec_list = vector.tolist() if isinstance(vector, np.ndarray) else list(vector)
        try:
            col.upsert(ids=[item_id], embeddings=[vec_list], metadatas=[metadata])
        except Exception:
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
        # 'ids' is always present in the response; it should not be passed in include
        res = col.query(
            query_embeddings=[vec_list],
            n_results=top_k,
            include=["metadatas", "distances", "embeddings"],
        )
        items: List[Dict] = []
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
        # 'ids' is returned by default and is not a valid include value
        res = col.get(ids=item_ids, include=["embeddings", "metadatas"])  # type: ignore
        out: Dict[str, Optional[np.ndarray]] = {iid: None for iid in item_ids}
        ids = res.get("ids") or []
        embs = res.get("embeddings")
        if embs is None:
            embs = []
        for i, iid in enumerate(ids):
            emb = (
                np.array(embs[i], dtype=np.float32)
                if i < len(embs) and embs[i] is not None
                else None
            )
            out[iid] = emb
        return out
