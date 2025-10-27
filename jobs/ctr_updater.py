from __future__ import annotations

import time
from collections import Counter

from ..utils.db import get_db


def run(days: int = 30):
    """Compute simple per-source priors based on click counts in last N days.

    Stores values in model_params as key='source:<name>' with small normalized weights [-0.1, 0.1].
    """
    db = get_db()
    now = int(time.time())
    since = now - days * 86400
    rows = db.execute(
        "SELECT source_id FROM click_events WHERE clicked_at >= ?",
        (since,),
    ).fetchall()
    counts = Counter([r[0] for r in rows])
    if not counts:
        return 0
    total = sum(counts.values())
    for src, c in counts.items():
        # naive normalization
        prior = (c / total) * 0.2 - 0.1
        db.execute(
            "INSERT INTO model_params(key, val) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET val=excluded.val",
            (f"source:{src}", str(prior)),
        )
    db.commit()
    return len(counts)


if __name__ == "__main__":
    n = run()
    print(f"Updated priors for {n} sources")
