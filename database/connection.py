"""
connection.py — Database connection factory
مصنع الاتصال بقاعدة البيانات
"""

import sqlite3
from pathlib import Path

DB_DIR  = Path.home() / "POSSystem"
DB_PATH = DB_DIR / "pos_data.db"


def get_connection() -> sqlite3.Connection:
    """إنشاء اتصال بقاعدة البيانات مع تفعيل Foreign Keys"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn
