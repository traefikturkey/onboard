from __future__ import annotations

import os
import time

from ..utils.db import get_db
from ..services.topic_extractor import corpus_select_terms


def run(bump_long: float | None = None, bump_short: float | None = None) -> int:
    db = get_db()
    bump_long = float(os.environ.get("TOPIC_BUMP_LONG", bump_long or 0.05))
    bump_short = float(os.environ.get("TOPIC_BUMP_SHORT", bump_short or 0.02))
    now = int(time.time())
    rows = db.execute(
        "SELECT COALESCE(title, ''), item_id FROM items WHERE COALESCE(title, '') != ''"
    ).fetchall()
    titles = [r[0] for r in rows]
    selected_terms_per_doc = corpus_select_terms(
        titles,
        top_k_per_doc=int(os.environ.get("TOPIC_TOP_K_PER_TITLE", 5)),
        min_df=int(os.environ.get("TOPIC_MIN_DF", 2)),
        max_df_ratio=float(os.environ.get("TOPIC_MAX_DF_RATIO", 0.5)),
        use_bigrams=bool(int(os.environ.get("TOPIC_USE_BIGRAMS", 1))),
    )

    total = 0
    for terms in selected_terms_per_doc:
        if not terms:
            continue
        for tok in terms:
            db.execute(
                """
                INSERT INTO topics(token, wt_long, wt_short, last_updated)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(token) DO UPDATE SET
                  wt_long = wt_long + excluded.wt_long,
                  wt_short = wt_short + excluded.wt_short,
                  last_updated = ?
                """,
                (tok, bump_long, bump_short, now, now),
            )
            total += 1
    db.commit()
    return total


if __name__ == "__main__":
    n = run()
    print(f"Updated topics with {n} title tokens")
