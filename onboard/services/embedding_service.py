from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        logger.warning("SentenceTransformer not available: %s", e)
        return None


class EmbeddingService:
    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        model = _get_model()
        if model is None:
            raise RuntimeError(
                "SentenceTransformer model not available. Install 'sentence-transformers' to enable embeddings."
            )
        vectors = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=False,
        )
        arr = np.array(vectors, dtype=np.float32)
        if arr.ndim != 2:
            raise RuntimeError(f"Unexpected embedding shape: {arr.shape}")
        return arr
