from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.interest_map import InterestMapService
from ..utils.db import get_db

bp = Blueprint("feedback", __name__)


@bp.post("/api/feedback")
def post_feedback():
    try:
        data = request.get_json(silent=True) or {}
        item_id = (data.get("item_id") or "").strip()
        signal = (data.get("signal") or "").strip().lower()
        if not item_id or signal not in {"up", "down"}:
            return jsonify({"ok": False, "error": "invalid payload"}), 400

        ims = InterestMapService(db=get_db())
        updated = ims.apply_feedback(item_id, signal)
        return jsonify({"ok": True, "updated": updated})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
