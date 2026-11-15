"""Visitor feedback ("Did this work for your hair?") stored in its own SQLite file.

Kept separate from haircare.db on purpose: haircare.db is rebuilt locally and pulled from
git, which would wipe votes collected on the live site. feedback.db is git-ignored.
Override the location with HAIRCARE_FEEDBACK_PATH.
"""
import os
import sqlite3
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(HERE, "feedback.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_url TEXT NOT NULL,      -- products.url (stable across rebuilds of haircare.db)
    vote        INTEGER NOT NULL,   -- 1 = worked, -1 = didn't
    label       TEXT,               -- what the site called it, e.g. 'Great match'
    profile     TEXT,               -- hair answers as a query string, e.g. 'curl_pattern=4C&porosity=high'
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feedback_product ON feedback(product_url);
"""
VOTES = {"up": 1, "down": -1}


def connect(path=None):
    conn = sqlite3.connect(path or os.environ.get("HAIRCARE_FEEDBACK_PATH", DEFAULT_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def record(conn, product_url, vote, label=None, profile=""):
    if vote not in VOTES:
        raise ValueError(f"vote must be one of {list(VOTES)}")
    with conn:
        conn.execute(
            "INSERT INTO feedback (product_url, vote, label, profile, created_at) VALUES (?, ?, ?, ?, ?)",
            (product_url[:512], VOTES[vote], (label or "")[:40], profile[:500],
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
