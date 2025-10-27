from __future__ import annotations

import hashlib
import time
import os
import sqlite3
from typing import Optional
from datetime import datetime
from pathlib import Path

from ..utils.db import get_db, init_db
from ..utils.url_tools import canonicalize_url


def _item_id_for(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _resolve_tracking_db_path() -> str:
    # Allow override, else default to app/configs/tracking.db
    env_path = os.environ.get("TRACKING_DB_PATH")
    if env_path:
        return env_path
    # repo_root/app/configs/tracking.db
    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    return str(repo_root / "app" / "configs" / "tracking.db")


def _parse_timestamp(ts_val: object) -> Optional[int]:
    try:
        if isinstance(ts_val, (int, float)):
            return int(ts_val)
        s = str(ts_val)
        # Expect ISO-8601 without tz from LinkTracker; handle basic cases
        return int(datetime.fromisoformat(s).timestamp())
    except Exception:
        return None


def run(limit: Optional[int] = None) -> int:
    """Sync app CLICK_EVENTS into personalization click_events.

    Maps columns:
      CLICK_EVENTS.TIMESTAMP -> click_events.clicked_at
      CLICK_EVENTS.WIDGET_ID -> click_events.source_id
      CLICK_EVENTS.LINK      -> click_events.url (canonicalized)
      LINK_ID is not used (we derive item_id from URL)
    """
    init_db()
    db = get_db()

    # Read from the app tracking database (CLICK_EVENTS)
    src_path = _resolve_tracking_db_path()
    try:
        src = sqlite3.connect(src_path)
    except Exception:
        return 0
    try:
        cur = src.execute(
            "SELECT TIMESTAMP, WIDGET_ID, LINK FROM CLICK_EVENTS ORDER BY TIMESTAMP DESC"
        )
        rows = cur.fetchall()
    except Exception:
        rows = []
    finally:
        try:
            src.close()
        except Exception:
            pass
    if not rows:
        return 0
    n = 0
    for r in rows[: (limit or len(rows))]:
        ts = _parse_timestamp(r[0])
        if ts is None:
            continue
        widget_id, raw_url = str(r[1]), str(r[2])
        url = canonicalize_url(raw_url)
        if not url:
            continue
        iid = _item_id_for(url)
        # Try to look up a title from items
        title_row = db.execute(
            "SELECT COALESCE(title, '') FROM items WHERE item_id = ?",
            (iid,),
        ).fetchone()
        title = title_row[0] if title_row else ""
        # Insert IGNORE semantics via unique (id,ts,url) tuples not present; we use timestamp granularity to avoid dup spam
        db.execute(
            """
            INSERT OR IGNORE INTO click_events(user_id, source_id, item_id, url, title, clicked_at)
            VALUES(?,?,?,?,?,?)
            """,
            ("default", widget_id, iid, url, title, ts),
        )
        n += 1
    db.commit()
    return n


if __name__ == "__main__":
    print(f"Synced {run()} events")
