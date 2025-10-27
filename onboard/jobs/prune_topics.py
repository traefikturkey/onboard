from __future__ import annotations

import os
from typing import Dict, Set

from ..utils.db import get_db
from ..services.topic_extractor import _DEFAULT_STOPWORDS, extract_tokens


def run(max_df_ratio: float | None = None, dry_run: bool | None = None) -> int:
    """Prune low-signal topics.

    Rules:
    - Remove tokens that are in the stopword list
    - Remove tokens that appear in more than max_df_ratio of titles (too generic)
    """
    db = get_db()
    max_df_ratio = float(
        os.environ.get("TOPIC_PRUNE_MAX_DF_RATIO", max_df_ratio or 0.6)
    )
    dry_run = bool(
        int(
            os.environ.get(
                "TOPIC_PRUNE_DRY_RUN", 0 if dry_run is None else int(dry_run)
            )
        )
    )

    rows = db.execute(
        "SELECT COALESCE(title, '') FROM items WHERE COALESCE(title, '') != ''"
    ).fetchall()
    titles = [r[0] for r in rows]
    N = len(titles) or 1

    # Build document frequency over titles
    df: Dict[str, int] = {}
    for t in titles:
        toks = set(extract_tokens(t, max_tokens=200))
        for tok in toks:
            df[tok] = df.get(tok, 0) + 1

    # Candidates to prune
    to_prune: Set[str] = set()
    for tok, d in df.items():
        if tok in _DEFAULT_STOPWORDS:
            to_prune.add(tok)
            continue
        if d / N > max_df_ratio:
            to_prune.add(tok)

    # Also include any pure stopwords that may have slipped into topics
    to_prune.update(_DEFAULT_STOPWORDS)

    if not to_prune:
        return 0

    # Delete from topics
    pruned = 0
    if dry_run:
        return len(to_prune)

    # SQLite has a limit on variables; delete in batches
    toks = list(to_prune)
    B = 500
    for i in range(0, len(toks), B):
        batch = toks[i : i + B]
        q = f"DELETE FROM topics WHERE token IN ({','.join(['?'] * len(batch))})"
        cur = db.execute(q, batch)
        pruned += cur.rowcount if cur.rowcount is not None else 0
    db.commit()
    return pruned


if __name__ == "__main__":
    n = run()
    print(f"Pruned {n} generic/stopword topics")
