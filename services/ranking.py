from __future__ import annotations

import math
import os
import random
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from ..utils.db import get_db
from .interest_map import InterestMapService, decay_weight
from .vector_store import VectorStore


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None or a.size == 0 or b.size == 0:
        return 0.0
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def cosine_to_unit(c: float) -> float:
    return 0.5 * (c + 1.0)


@dataclass
class ScoredItem:
    item_id: str
    url: str
    title: str
    score: float
    source: Optional[str]
    published_at: Optional[int]


class RankingEngine:
    def __init__(
        self,
        db: Optional[sqlite3.Connection] = None,
        vector_store: Optional[VectorStore] = None,
        interest: Optional[InterestMapService] = None,
        params: Optional[Dict] = None,
    ):
        self.db = db or get_db()
        self.vs = vector_store or VectorStore()
        self.interest = interest or InterestMapService(self.db, self.vs, params)
        self.params = params or {}

    # Config with defaults
    @property
    def w_long(self) -> float:
        return float(self.params.get("w_long", 0.40))

    @property
    def w_short(self) -> float:
        return float(self.params.get("w_short", 0.45))

    @property
    def w_time(self) -> float:
        return float(self.params.get("w_time", 0.10))

    @property
    def w_src(self) -> float:
        return float(self.params.get("w_src", 0.07))

    @property
    def shown_penalty(self) -> float:
        return float(self.params.get("shown_penalty", -0.12))

    @property
    def half_fresh(self) -> float:
        return float(self.params.get("fresh_half_days", 3)) * 86400.0

    @property
    def epsilon(self) -> float:
        return float(self.params.get("epsilon", 0.05))

    def _source_prior(self) -> Dict[str, float]:
        cur = self.db.execute(
            "SELECT key, val FROM model_params WHERE key LIKE 'source:%'"
        )
        priors = {}
        for k, v in cur.fetchall():
            try:
                priors[k.split(":", 1)[1]] = float(v)
            except Exception:
                continue
        return priors

    def _shown_recently(self, item_id: str, now: int) -> bool:
        hour_ago = now - 3600 * 24
        cur = self.db.execute(
            "SELECT 1 FROM rec_logs WHERE item_id = ? AND served_at >= ? LIMIT 1",
            (item_id, hour_ago),
        )
        return cur.fetchone() is not None

    def score_items(
        self, item_ids: List[str], now: Optional[int] = None
    ) -> List[ScoredItem]:
        now = now or int(time.time())
        profiles = self.interest.compute_profiles(now)
        priors = self._source_prior()

        # Fetch metadata and vectors
        qmarks = ",".join(["?"] * len(item_ids)) or "?"
        cur = self.db.execute(
            f"SELECT item_id, url, title, source, published_at FROM items WHERE item_id IN ({qmarks})",
            item_ids if item_ids else [""],
        )
        meta = {r[0]: (r[1], r[2], r[3], r[4]) for r in cur.fetchall()}
        vecs = self.vs.get_vectors_for_items(item_ids)

        scored: List[ScoredItem] = []
        for iid in item_ids:
            v = vecs.get(iid)
            if v is None or v.size == 0:
                # Skip items without vectors
                continue
            url, title, source, published_at = meta.get(iid, ("", "", None, None))
            s_long = cosine_to_unit(cosine_sim(v, profiles.long_vec))
            s_short = cosine_to_unit(cosine_sim(v, profiles.short_vec))
            # freshness
            if published_at:
                s_time = decay_weight(now - int(published_at), self.half_fresh)
            else:
                s_time = 0.0
            s_src = priors.get(source or "", 0.0)
            shown = self._shown_recently(iid, now)
            score = (
                self.w_long * s_long
                + self.w_short * s_short
                + self.w_time * s_time
                + self.w_src * s_src
                + (self.shown_penalty if shown else 0.0)
            )
            scored.append(
                ScoredItem(iid, url, title, float(score), source, published_at)
            )

        # ε-greedy: with epsilon, promote a mid-ranked unseen item towards top third
        if scored and random.random() < self.epsilon:
            scored_sorted = sorted(scored, key=lambda x: x.score, reverse=True)
            mid = scored_sorted[len(scored_sorted) // 2 :]
            if mid:
                pick = random.choice(mid)
                # small boost
                pick.score += 0.01
                scored = scored_sorted

        return sorted(scored, key=lambda x: x.score, reverse=True)
