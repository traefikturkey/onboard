from __future__ import annotations

from ..services.interest_map import InterestMapService
from ..utils.db import get_db


def run() -> int:
    db = get_db()
    svc = InterestMapService(db=db)
    rows = db.execute("SELECT item_id FROM items WHERE source = 'bookmark'").fetchall()
    cnt = 0
    for (iid,) in rows:
        before = cnt
        svc.seed_from_bookmark(iid)
        # seed_from_bookmark does not return count; assume at least attempted
        cnt = before + 1
    return cnt


if __name__ == "__main__":
    n = run()
    print(f"Seeded topics from {n} bookmark items")
