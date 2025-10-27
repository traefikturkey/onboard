from __future__ import annotations

import time
from flask import Blueprint, jsonify

from ..services.interest_map import InterestMapService
from ..utils.db import get_db


bp = Blueprint("interest_map", __name__)


@bp.get("/api/interest_map")
def get_interest_map():
    now = int(time.time())
    svc = InterestMapService(db=get_db())
    profiles = svc.compute_profiles(now)
    topics = svc.get_topics(20)
    return jsonify(
        {
            "generated_at": now,
            "magnitudes": profiles.magnitudes,
            "top_topics": [
                {"token": t, "wt_long": wl, "wt_short": ws} for (t, wl, ws) in topics
            ],
            "params": {
                "half_life_short_days": 7,
                "half_life_long_days": 90,
                "base_click_wt": 0.5,
                "bookmark_wt": 0.8,
            },
        }
    )
