from __future__ import annotations

import time
from ..services.interest_map import decay_weight
from ..utils.db import get_db


def run():
    db = get_db()
    now = int(time.time())
    # Apply decay to topics since last_updated
    rows = db.execute(
        "SELECT token, wt_long, wt_short, COALESCE(last_updated, 0) FROM topics"
    ).fetchall()
    updated = 0
    for token, wl, ws, last in rows:
        last = int(last or 0)
        dt = max(0, now - last)
        w_long = decay_weight(dt, 90 * 86400)
        w_short = decay_weight(dt, 7 * 86400)
        wl2 = float(wl) * w_long
        ws2 = float(ws) * w_short
        db.execute(
            "UPDATE topics SET wt_long = ?, wt_short = ?, last_updated = ? WHERE token = ?",
            (wl2, ws2, now, token),
        )
        updated += 1
    db.commit()
    return updated


if __name__ == "__main__":
    n = run()
    print(f"Decayed {n} topic rows")
