import sqlite3
import threading
from datetime import datetime, timezone

from core.paths import ROOT


_DB_PATH = ROOT / "velora.db"
_LOCK = threading.RLock()


def record(event_type, message, account=None, metadata=None):
    payload = "" if metadata is None else str(metadata)
    with _LOCK:
        connection = sqlite3.connect(_DB_PATH)
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    account TEXT,
                    message TEXT NOT NULL,
                    metadata TEXT
                )
                """
            )
            connection.execute(
                "INSERT INTO audit_events(created_at,event_type,account,message,metadata) VALUES(?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), str(event_type), account, str(message), payload),
            )
            connection.commit()
        finally:
            connection.close()


def recent(limit=100):
    with _LOCK:
        connection = sqlite3.connect(_DB_PATH)
        try:
            rows = connection.execute(
                "SELECT created_at,event_type,account,message,metadata "
                "FROM audit_events ORDER BY id DESC LIMIT ?",
                (max(1, int(limit)),),
            ).fetchall()
            return rows
        finally:
            connection.close()
