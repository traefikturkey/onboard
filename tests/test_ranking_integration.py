import sqlite3
import time

import numpy as np

from onboard.services.ranking import RankingEngine


class DummyVS:
    def __init__(self, vecs):
        self.vecs = vecs

    def get_vectors_for_items(self, ids):
        return {iid: self.vecs.get(iid) for iid in ids}


def test_ranking_orders_by_similarity(tmp_path):
    now = int(time.time())
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

    # Create three items with simple one-hot vectors
    vecs = {
        "i1": np.array([1] + [0] * 383, dtype=np.float32),
        "i2": np.array([0, 1] + [0] * 382, dtype=np.float32),
        "i3": np.array([0, 0, 1] + [0] * 381, dtype=np.float32),
    }
    for i, iid in enumerate(["i1", "i2", "i3"], start=1):
        con.execute(
            "INSERT INTO items(item_id, url, title, source, published_at, vec_id) VALUES(?,?,?,?,?,?)",
            (iid, f"https://x/{iid}", iid.upper(), "feed", now - i, iid),
        )
    # Seed one click on i1 very recent to bias short_vec toward i1
    con.execute(
        "INSERT INTO click_events(user_id, source_id, item_id, url, title, clicked_at) VALUES(?,?,?,?,?,?)",
        ("default", "feed", "i1", "https://x/i1", "I1", now - 10),
    )
    con.commit()

    engine = RankingEngine(db=con, vector_store=DummyVS(vecs), params={"epsilon": 0.0})
    scored = engine.score_items(["i1", "i2", "i3"], now=now)
    # Expect i1 to rank first given click on i1
    assert [s.item_id for s in scored][:1] == ["i1"]
