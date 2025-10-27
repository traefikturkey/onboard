from __future__ import annotations

import json
import math
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.db import get_db
from .vector_store import VectorStore


def decay_weight(delta_seconds: float, half_life_seconds: float) -> float:
    if half_life_seconds <= 0:
        return 1.0
    return math.exp(-math.log(2.0) * (delta_seconds / half_life_seconds))


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n == 0:
        return v
    return (v / n).astype(np.float32)


@dataclass
class InterestProfiles:
    short_vec: np.ndarray
    long_vec: np.ndarray
    magnitudes: Dict[str, float]


class InterestMapService:
    def __init__(
        self,
        db: Optional[sqlite3.Connection] = None,
        vector_store: Optional[VectorStore] = None,
        params: Optional[Dict] = None,
    ):
        self.db = db or get_db()
        self.vs = vector_store or VectorStore()
        self.params = params or {}

    # Config with defaults
    @property
    def half_short(self) -> float:
        # seconds
        return float(self.params.get("half_life_short_days", 7)) * 86400.0

    @property
    def half_long(self) -> float:
        return float(self.params.get("half_life_long_days", 90)) * 86400.0

    @property
    def base_click_wt(self) -> float:
        return float(self.params.get("base_click_wt", 0.5))

    @property
    def bookmark_wt(self) -> float:
        return float(self.params.get("bookmark_wt", 0.8))

    def _load_model_params(self) -> Dict[str, str]:
        cur = self.db.execute("SELECT key, val FROM model_params")
        return {row[0]: row[1] for row in cur.fetchall()}

    def compute_profiles(self, now: Optional[int] = None) -> InterestProfiles:
        """
        Recompute short/long centroids from click_events with exponential decay.
        Seed long-term with bookmark vectors.
        """
        now = now or int(time.time())

        # Fetch recent clicks (limit window to 1 year for performance)
        year_ago = now - int(86400 * 365)
        clicks = self.db.execute(
            "SELECT item_id, clicked_at FROM click_events WHERE clicked_at >= ? ORDER BY clicked_at DESC",
            (year_ago,),
        ).fetchall()

        # Map item_id -> vec (fetch in batches via Chroma)
        item_ids = [row[0] for row in clicks]
        short = np.zeros(384, dtype=np.float32)
        long = np.zeros(384, dtype=np.float32)

        # Chunk ids to avoid large payloads
        B = 200
        for i in range(0, len(item_ids), B):
            chunk = item_ids[i : i + B]
            vecs = self.vs.get_vectors_for_items(chunk)
            for j, iid in enumerate(chunk):
                v = vecs.get(iid)
                if v is None or v.size == 0:
                    continue
                dt = now - int(clicks[i + j][1])
                a_s = self.base_click_wt * decay_weight(dt, self.half_short)
                a_l = self.base_click_wt * decay_weight(dt, self.half_long)
                short = _normalize(short * (1 - a_s) + v * a_s)
                long = _normalize(long * (1 - a_l) + v * a_l)

        # Seed long-term from bookmarks (items.source='bookmark')
        bookmarks = self.db.execute(
            "SELECT item_id FROM items WHERE source = 'bookmark' AND vec_id IS NOT NULL"
        ).fetchall()
        if bookmarks:
            ids = [r[0] for r in bookmarks]
            vecs = self.vs.get_vectors_for_items(ids)
            for iid in ids:
                v = vecs.get(iid)
                if v is None or v.size == 0:
                    continue
                long = _normalize(long * (1 - self.bookmark_wt) + v * self.bookmark_wt)

        mags = {
            "short": float(np.linalg.norm(short)),
            "long": float(np.linalg.norm(long)),
        }
        return InterestProfiles(short_vec=short, long_vec=long, magnitudes=mags)

    def get_topics(self, top_k: int = 20) -> List[Tuple[str, float, float]]:
        cur = self.db.execute(
            "SELECT token, wt_long, wt_short FROM topics ORDER BY (wt_long + wt_short) DESC LIMIT ?",
            (top_k,),
        )
        return [(r[0], float(r[1]), float(r[2])) for r in cur.fetchall()]
