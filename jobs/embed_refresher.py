from __future__ import annotations

import time
from typing import Optional

import numpy as np

from ..services.embedding_service import EmbeddingService
from ..services.text_extractor import TextExtractor
from ..services.vector_store import VectorStore
from ..utils.db import get_db


def run(limit: Optional[int] = 100):
    """Embed items missing vectors or stale and upsert into vector store."""
    db = get_db()
    now = int(time.time())
    # Pick items without vec_id or never embedded
    cur = db.execute(
        """
        SELECT item_id, url, title FROM items
        WHERE vec_id IS NULL OR last_embedded_at IS NULL
        ORDER BY last_embedded_at IS NULL DESC, rowid DESC
        LIMIT ?
        """,
        (limit or 100,),
    )
    rows = cur.fetchall()
    if not rows:
        return 0

    extractor = TextExtractor()
    embedder = EmbeddingService()
    vs = VectorStore()

    payloads = []
    metas = []
    ids = []
    for r in rows:
        iid, url, title = r[0], r[1], r[2]
        ext = extractor.extract(url)
        text = (title or "") + "\n\n" + ext.text
        payloads.append(text)
        metas.append(
            {
                "item_id": iid,
                "url": url,
                "title": title or "",
                "content_hash": ext.content_hash,
            }
        )
        ids.append(iid)

    vecs = embedder.embed_texts(payloads)
    for i, iid in enumerate(ids):
        vec = vecs[i]
        vid = vs.upsert(iid, vec, metas[i])
        db.execute(
            "UPDATE items SET vec_id = ?, content_hash = ?, last_embedded_at = ? WHERE item_id = ?",
            (vid, metas[i]["content_hash"], now, iid),
        )
    db.commit()
    return len(ids)


if __name__ == "__main__":
    n = run()
    print(f"Embedded {n} items")
