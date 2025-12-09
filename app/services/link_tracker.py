import sqlite3
from datetime import datetime

import pandas as pd

from app.models.utils import calculate_sha1_hash, pwd


class LinkTracker:
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, db_path=None):
        # Allow injection of db_path for testing (use ":memory:" for in-memory DB)
        if db_path is None:
            db_path = pwd.joinpath("configs", "tracking.db")
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute(
            """
    SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='CLICK_EVENTS'
    """
        )
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(
                """
    CREATE TABLE CLICK_EVENTS (
    ID TEXT PRIMARY KEY,
    TIMESTAMP DATETIME,
    WIDGET_ID TEXT,
    LINK_ID TEXT,
    LINK TEXT
    )
    """
            )
            self.connection.commit()

    def track_click_event(self, widget_id, link_id, link):
        # Store timestamp as ISO-formatted string to avoid passing a datetime
        # object directly to sqlite3 (the default datetime adapter is
        # deprecated in Python 3.12). Converting to ISO string is simple and
        # plays nicely with pandas.to_datetime on read.
        timestamp = datetime.now()
        timestamp_str = timestamp.isoformat()
        event_id = calculate_sha1_hash(f"{widget_id}_{link_id}_{str(timestamp)}")

        self.cursor.execute(
            """
    INSERT INTO CLICK_EVENTS (ID, TIMESTAMP, WIDGET_ID, LINK_ID, LINK) VALUES (?, ?, ?, ?, ?)
    """,
            (event_id, timestamp_str, widget_id, link_id, link),
        )
        self.connection.commit()

    def get_click_events(self):
        self.cursor.execute("SELECT TIMESTAMP, LINK FROM CLICK_EVENTS")
        rows = self.cursor.fetchall()
        df = pd.DataFrame(rows, columns=["TIMESTAMP", "LINK"])
        # If there are no rows, return the empty dataframe immediately
        if df.empty:
            return df

        # Parse timestamps with mixed format support. Timestamps may be stored
        # in different formats:
        # - ISO8601: 2025-08-15T16:02:33.206513
        # - Space-separated: 2025-08-15 16:02:33.206513
        # Use format='mixed' to handle both formats and coerce unparsable
        # values to NaT instead of raising an error.
        df["TIMESTAMP"] = pd.to_datetime(
            df["TIMESTAMP"], format="mixed", errors="coerce"
        )
        return df

    def __del__(self):
        self.connection.close()


link_tracker = LinkTracker()
