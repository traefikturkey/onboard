from __future__ import annotations

import sys
from typing import List

from ..utils.db import get_db, init_db
from ..services.interest_map import InterestMapService
from ..services.ranking import RankingEngine


def _print(s: str) -> None:
    print(f"[discover] {s}")


def run(limit: int = 10) -> int:
    """Print a concise summary of the ingested data and top recommendations.

    Returns number of recommendations printed.
    """
    init_db()
    db = get_db()

    # Basic counts
    total = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    embedded = db.execute(
        "SELECT COUNT(*) FROM items WHERE vec_id IS NOT NULL"
    ).fetchone()[0]
    _print(
        f"Items: total={total}, embedded={embedded}, pending={max(total - embedded, 0)}"
    )

    # Top sources
    rows = db.execute(
        "SELECT COALESCE(source, ''), COUNT(*) AS c FROM items GROUP BY source ORDER BY c DESC LIMIT 5"
    ).fetchall()
    if rows:
        parts = [f"{r[0] or 'unknown'}={r[1]}" for r in rows]
        _print("Top sources: " + ", ".join(parts))

    # Interest magnitudes and topics
    ims = InterestMapService(db=db)
    profiles = ims.compute_profiles()
    _print(
        f"Interest magnitudes: short={profiles.magnitudes['short']:.3f}, long={profiles.magnitudes['long']:.3f}"
    )
    topics = ims.get_topics(10)
    if topics:
        _print("Top topics (long_weight/short_weight):")
        for t, wl, ws in topics[:10]:
            _print(f"  - {t}: {wl:.2f}/{ws:.2f}")

    # Candidate recommendations (recent embedded)
    cand_rows = db.execute(
        """
        SELECT item_id FROM items
        WHERE vec_id IS NOT NULL
        ORDER BY COALESCE(last_embedded_at, 0) DESC, rowid DESC
        LIMIT 100
        """
    ).fetchall()
    item_ids: List[str] = [r[0] for r in cand_rows]
    if not item_ids:
        _print("No embedded items available for recommendations yet.")
        return 0

    engine = RankingEngine(db=db)
    scored = engine.score_items(item_ids)
    if not scored:
        _print("No recommendations scored.")
        return 0

    _print(f"Top {min(limit, len(scored))} recommendations:")
    for i, s in enumerate(scored[:limit], start=1):
        title = s.title or s.url
        src = s.source or ""
        _print(f"{i:2d}. {s.score:.3f}  [{src}] {title}  -> {s.url}")

    return min(limit, len(scored))


if __name__ == "__main__":
    n = run()
    # Exit 0 regardless; this is a report utility
    sys.exit(0)
