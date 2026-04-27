"""
Database Schema & Connection Manager
نظام إدارة قاعدة البيانات
"""

import sqlite3
import os
from pathlib import Path


# ─── Database Path ────────────────────────────────────────────────
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


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS budget (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    main_budget     REAL    NOT NULL DEFAULT 0,
    cash_vault      REAL    NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO budget (id, main_budget, cash_vault) VALUES (1, 0, 0);

CREATE TABLE IF NOT EXISTS groups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    leader_id       INTEGER,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    phone           TEXT,
    group_id        INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    total_debt      REAL    NOT NULL DEFAULT 0,
    notes           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_customers_group ON customers(group_id);

CREATE TABLE IF NOT EXISTS machine_deposits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_id     INTEGER NOT NULL,
    amount          REAL    NOT NULL,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS daily_commissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_id     INTEGER NOT NULL,
    amount          REAL    NOT NULL,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


def initialize_database() -> None:
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)

        # Migrate platforms — recreate to allow instapay type
        try:
            # Check if platforms table exists with old constraint
            info = conn.execute("PRAGMA table_info(platforms)").fetchall()
            if not info:
                # Create fresh
                conn.executescript("""
                    CREATE TABLE platforms (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        name            TEXT    NOT NULL UNIQUE,
                        type            TEXT    NOT NULL
                                        CHECK (type IN ('machine', 'wallet', 'instapay')),
                        balance         REAL    NOT NULL DEFAULT 0,
                        monthly_limit   REAL    NOT NULL DEFAULT 200000,
                        monthly_used    REAL    NOT NULL DEFAULT 0,
                        last_reset_date TEXT    NOT NULL DEFAULT (strftime('%Y-%m', 'now')),
                        is_active       INTEGER NOT NULL DEFAULT 1
                    );
                """)
            else:
                # Try inserting instapay to check constraint
                try:
                    conn.execute("INSERT OR IGNORE INTO platforms (name, type) VALUES ('__ip_test__', 'instapay')")
                    conn.execute("DELETE FROM platforms WHERE name = '__ip_test__'")
                    conn.commit()
                except Exception:
                    # Old constraint — recreate table
                    conn.executescript("""
                        PRAGMA foreign_keys = OFF;
                        CREATE TABLE platforms_v2 (
                            id              INTEGER PRIMARY KEY AUTOINCREMENT,
                            name            TEXT    NOT NULL UNIQUE,
                            type            TEXT    NOT NULL
                                            CHECK (type IN ('machine', 'wallet', 'instapay')),
                            balance         REAL    NOT NULL DEFAULT 0,
                            monthly_limit   REAL    NOT NULL DEFAULT 200000,
                            monthly_used    REAL    NOT NULL DEFAULT 0,
                            last_reset_date TEXT    NOT NULL DEFAULT (strftime('%Y-%m', 'now')),
                            is_active       INTEGER NOT NULL DEFAULT 1
                        );
                        INSERT OR IGNORE INTO platforms_v2
                            SELECT id, name, type, balance, monthly_limit, monthly_used, last_reset_date,
                                   COALESCE(is_active, 1)
                            FROM platforms;
                        DROP TABLE platforms;
                        ALTER TABLE platforms_v2 RENAME TO platforms;
                        PRAGMA foreign_keys = ON;
                    """)
                    conn.commit()
        except Exception as e:
            print(f"[DB] Platform migration note: {e}")

        # Transactions table migrations
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                    operation_type  TEXT    NOT NULL
                                    CHECK (operation_type IN ('outbound', 'inbound')),
                    service_name    TEXT    NOT NULL,
                    platform_id     INTEGER NOT NULL REFERENCES platforms(id),
                    customer_id     INTEGER REFERENCES customers(id) ON DELETE SET NULL,
                    amount_spent    REAL    NOT NULL DEFAULT 0,
                    amount_required REAL    NOT NULL DEFAULT 0,
                    profit          REAL    GENERATED ALWAYS AS (amount_required - amount_spent) VIRTUAL,
                    reference_no    TEXT,
                    is_card         INTEGER NOT NULL DEFAULT 0,
                    payment_status  TEXT    NOT NULL DEFAULT 'pending'
                                    CHECK (payment_status IN ('cash', 'pending', 'paid')),
                    is_delivered    INTEGER NOT NULL DEFAULT 0,
                    notes           TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_transactions_customer  ON transactions(customer_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_platform  ON transactions(platform_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_status    ON transactions(payment_status);
                CREATE INDEX IF NOT EXISTS idx_transactions_created   ON transactions(created_at);
                CREATE INDEX IF NOT EXISTS idx_transactions_reference ON transactions(reference_no);
            """)
            conn.commit()
        except Exception:
            pass

        # Column migrations
        for sql in [
            "ALTER TABLE transactions ADD COLUMN is_delivered INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE platforms ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1",
        ]:
            try:
                conn.execute(sql)
                conn.commit()
            except Exception:
                pass

    print(f"[DB] Database ready: {DB_PATH}")
