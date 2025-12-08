from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Optional

from ..utils.db import get_db, init_db
from ..utils.bookmarks import flatten_bookmarks
from ..utils.layout import extract_bookmark_widgets


# Repo root: /workspaces/onboard (two levels up from this file)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOOKMARKS = REPO_ROOT / "app" / "configs" / "bookmarks_bar.json"
DEFAULT_LAYOUT = REPO_ROOT / "app" / "configs" / "layout.yml"


def _load_sources(
    bookmarks_path: Optional[str] = None, layout_path: Optional[str] = None
) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    bp = Path(bookmarks_path) if bookmarks_path else DEFAULT_BOOKMARKS
    lp = Path(layout_path) if layout_path else DEFAULT_LAYOUT
    if bp.exists():
        items.extend(flatten_bookmarks(str(bp)))
    if lp.exists():
        items.extend(extract_bookmark_widgets(str(lp)))

    # Deduplicate by url
    seen = set()
    deduped: List[Dict[str, str]] = []
    for it in items:
        url = it.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        # normalize presence of fields
        deduped.append(
            {
                "url": it.get("url", ""),
                "title": it.get("title", ""),
                "source": it.get("source", "bookmark"),
                "item_id": it.get("item_id", ""),
            }
        )
    return deduped


def run(bookmarks_path: Optional[str] = None, layout_path: Optional[str] = None) -> int:
    """Ingest bookmarks and layout bookmark widgets into the items table."""
    # Ensure DB initialized
    init_db()
    db = get_db()
    items = _load_sources(bookmarks_path, layout_path)
    if not items:
        return 0

    inserted = 0
    for it in items:
        item_id = it["item_id"]
        url = it["url"]
        title = it.get("title", "")
        source = it.get("source", "bookmark")
        # 1) Insert if new
        db.execute(
            "INSERT OR IGNORE INTO items(item_id, url, title, source) VALUES(?,?,?,?)",
            (item_id, url, title, source),
        )
        # 2) If existing, update empty title/source
        db.execute(
            """
            UPDATE items
               SET title = CASE WHEN (title IS NULL OR title = '') THEN ? ELSE title END,
                   source = CASE WHEN (source IS NULL OR source = '') THEN ? ELSE source END
             WHERE item_id = ?
            """,
            (title, source, item_id),
        )
        inserted += 1
    db.commit()
    return inserted


if __name__ == "__main__":
    n = run()
    print(f"Ingested {n} bookmark items into SQLite 'items'")
