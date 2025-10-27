import os
import sqlite3
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = os.environ.get(
    "ONBOARD_DB_PATH",
    os.path.join(Path(__file__).resolve().parents[2], "data", "onboard.db"),
)
SCHEMA_PATH = os.path.join(Path(__file__).resolve().parents[2], "data", "schema.sql")


def init_db(db_path: Optional[str] = None, schema_path: Optional[str] = None) -> str:
    db_file = db_path or DEFAULT_DB_PATH
    schema_file = schema_path or SCHEMA_PATH

    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    con = sqlite3.connect(db_file)
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            con.executescript(f.read())
        con.commit()
    finally:
        con.close()
    return db_file


def get_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    db_file = db_path or DEFAULT_DB_PATH
    con = sqlite3.connect(db_file)
    con.row_factory = sqlite3.Row
    return con
