import sqlite3
from datetime import datetime

import pandas as pd
from app.models.utils import calculate_sha1_hash, pwd


class LinkTracker:
  conn: sqlite3.Connection
  cursor: sqlite3.Cursor

  def __init__(self):
    file_path = pwd.joinpath("configs", "tracking.db")
    self.connection = sqlite3.connect(file_path, check_same_thread=False)
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
    timestamp = datetime.now()
    event_id = calculate_sha1_hash(f"{widget_id}_{link_id}_{str(timestamp)}")

    self.cursor.execute(
        """
    INSERT INTO CLICK_EVENTS (ID, TIMESTAMP, WIDGET_ID, LINK_ID, LINK) VALUES (?, ?, ?, ?, ?)
    """,
        (event_id, timestamp, widget_id, link_id, link),
    )
    self.connection.commit()

  def get_click_events(self):
    self.cursor.execute("SELECT TIMESTAMP, LINK FROM CLICK_EVENTS")
    rows = self.cursor.fetchall()
    df = pd.DataFrame(rows, columns=["TIMESTAMP", "LINK"])
    df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])
    return df

  def __del__(self):
    self.connection.close()


link_tracker = LinkTracker()
