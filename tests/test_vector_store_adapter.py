import numpy as np

from onboard.services.vector_store import VectorStore


def test_vector_store_no_chroma_graceful():
    vs = VectorStore()
    q = vs.query(np.zeros(384, dtype=np.float32), top_k=5)
    assert isinstance(q, list)
