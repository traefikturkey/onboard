from __future__ import annotations

from ..services.interest_map import InterestMapService
from ..utils.db import get_db


def run() -> int:
    db = get_db()
    svc = InterestMapService(db=db)
    rows = db.execute(
        "SELECT item_id, clicked_at FROM click_events ORDER BY clicked_at ASC"
    ).fetchall()
    cnt = 0
    for iid, ts in rows:
        cnt += svc.update_from_click(iid, ts)
    return cnt


if __name__ == "__main__":
    updated = run()
    print(f"Updated tokens: {updated}")
