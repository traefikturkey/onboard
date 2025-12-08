from __future__ import annotations

import time

from ..utils.db import get_db
from . import embed_refresher


def run(embed: bool = True) -> int:
    db = get_db()
    # Insert items for clicked URLs that are not yet in items
    rows = db.execute(
        """
        SELECT DISTINCT ce.item_id, ce.url, COALESCE(ce.title, '')
        FROM click_events ce
        LEFT JOIN items i ON i.item_id = ce.item_id
        WHERE i.item_id IS NULL
        """
    ).fetchall()
    if not rows:
        return 0
    now = int(time.time())
    for iid, url, title in rows:
        db.execute(
            """
            INSERT OR IGNORE INTO items(item_id, url, title, source, published_at)
            VALUES(?, ?, ?, 'click', NULL)
            """,
            (iid, url, title),
        )
    db.commit()
    if embed:
        # Immediately embed newly added items
        embed_refresher.run(limit=None)
    return len(rows)


if __name__ == "__main__":
    n = run(embed=True)
    print(f"Hydrated {n} clicked items into items table and embedded vectors")
