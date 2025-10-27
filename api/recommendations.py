from __future__ import annotations

import time
from typing import List

from flask import Blueprint, jsonify, request

from ..services.ranking import RankingEngine
from ..utils.db import get_db


bp = Blueprint("recommendations", __name__)


@bp.get("/api/recommendations")
def get_recommendations():
    limit = int(request.args.get("limit", 20))
    now = int(time.time())
    db = get_db()
    # Candidate generation: recent items in last 7 days, with vectors
    week_ago = now - 7 * 86400
    cur = db.execute(
        """
        SELECT item_id FROM items
        WHERE (published_at IS NULL OR published_at >= ?)
          AND vec_id IS NOT NULL
        ORDER BY COALESCE(published_at, 0) DESC
        LIMIT 200
        """,
        (week_ago,),
    )
    candidates: List[str] = [r[0] for r in cur.fetchall()]
    engine = RankingEngine(db=db)
    scored = engine.score_items(candidates, now=now)[:limit]
    return jsonify(
        {
            "generated_at": now,
            "items": [
                {
                    "item_id": s.item_id,
                    "url": s.url,
                    "title": s.title,
                    "score": round(s.score, 6),
                    "source": s.source,
                    "published_at": s.published_at,
                }
                for s in scored
            ],
        }
    )
