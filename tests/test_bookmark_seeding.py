import os
import sqlite3

import numpy as np

from onboard.services.interest_map import InterestMapService


class DummyVS:
    def get_vectors_for_items(self, ids):
        out = {}
        for i, iid in enumerate(ids):
            v = np.zeros(384, dtype=np.float32)
            v[i % 384] = 1.0
            out[iid] = v
        return out


def test_seed_from_bookmarks(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(str(db_path))
    con.executescript(
        """
        CREATE TABLE items (item_id TEXT PRIMARY KEY, url TEXT, title TEXT, source TEXT, published_at INTEGER, content_hash TEXT, vec_id TEXT, last_embedded_at INTEGER);
        CREATE TABLE click_events (id INTEGER PRIMARY KEY, user_id TEXT, source_id TEXT, item_id TEXT, url TEXT, title TEXT, clicked_at INTEGER);
        CREATE TABLE topics (token TEXT PRIMARY KEY, wt_long REAL NOT NULL DEFAULT 0.0, wt_short REAL NOT NULL DEFAULT 0.0, last_updated INTEGER);
        CREATE TABLE model_params (key TEXT PRIMARY KEY, val TEXT);
        CREATE TABLE rec_logs (rec_id TEXT, item_id TEXT, score REAL, served_at INTEGER, clicked INTEGER DEFAULT 0, PRIMARY KEY (rec_id, item_id));
        """
    )
    # Insert two bookmarks with vec_id present
    con.execute(
        "INSERT INTO items(item_id, url, title, source, vec_id) VALUES(?,?,?,?,?)",
        ("a", "https://a", "A", "bookmark", "a"),
    )
    con.execute(
        "INSERT INTO items(item_id, url, title, source, vec_id) VALUES(?,?,?,?,?)",
        ("b", "https://b", "B", "bookmark", "b"),
    )
    con.commit()

    ims = InterestMapService(db=con, vector_store=DummyVS())
    prof = ims.compute_profiles()
    assert np.linalg.norm(prof.long_vec) > 0.0
