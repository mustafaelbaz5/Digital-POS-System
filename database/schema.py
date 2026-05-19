"""
Database Schema & Connection Manager
نظام إدارة قاعدة البيانات
"""

import sqlite3

from database.connection import DB_DIR, DB_PATH, get_connection  # re-exported for compat


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

CREATE INDEX IF NOT EXISTS idx_deposits_platform ON machine_deposits(platform_id);
CREATE INDEX IF NOT EXISTS idx_deposits_created  ON machine_deposits(created_at);
CREATE INDEX IF NOT EXISTS idx_deposits_platform ON machine_deposits(platform_id);
CREATE INDEX IF NOT EXISTS idx_deposits_created  ON machine_deposits(created_at);

CREATE TABLE IF NOT EXISTS daily_commissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_id     INTEGER NOT NULL,
    amount          REAL    NOT NULL,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS capital_movements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type     TEXT    NOT NULL CHECK (target_type IN ('platform', 'cash')),
    target_id       INTEGER,
    amount          REAL    NOT NULL,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_capital_movements_target ON capital_movements(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_capital_movements_created ON capital_movements(created_at);
"""


def initialize_database() -> None:
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)

        # ── Platforms table: إنشاء أو migration آمن ──────────────────
        try:
            info = conn.execute("PRAGMA table_info(platforms)").fetchall()

            if not info:
                # الجدول مش موجود خالص → إنشاء جديد
                conn.execute("""
                    CREATE TABLE platforms (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        name            TEXT    NOT NULL UNIQUE,
                        type            TEXT    NOT NULL,
                        balance         REAL    NOT NULL DEFAULT 0,
                        initial_balance REAL    NOT NULL DEFAULT 0,
                        monthly_limit   REAL    NOT NULL DEFAULT 200000,
                        monthly_used    REAL    NOT NULL DEFAULT 0,
                        last_reset_date TEXT    NOT NULL DEFAULT (strftime('%Y-%m', 'now')),
                        is_active       INTEGER NOT NULL DEFAULT 1
                    )
                """)
                conn.commit()
                print("[DB] platforms table created fresh")
            else:
                # الجدول موجود → تحقق إن instapay مسموح بيه
                # الطريقة الآمنة: نجرب INSERT حقيقي بدون executescript
                conn.execute("SAVEPOINT check_instapay")
                try:
                    conn.execute(
                        "INSERT INTO platforms (name, type, balance) VALUES ('__test__', 'instapay', 0)"
                    )
                    conn.execute("DELETE FROM platforms WHERE name = '__test__'")
                    conn.execute("RELEASE SAVEPOINT check_instapay")
                    # instapay مسموح → مفيش مشكلة
                except Exception:
                    # الـ CHECK constraint قديم → lazim نعمل migration
                    conn.execute("ROLLBACK TO SAVEPOINT check_instapay")
                    conn.execute("RELEASE SAVEPOINT check_instapay")

                    print("[DB] Migrating platforms table to support instapay...")

                    # خطوة 1: إيقاف foreign keys مؤقتاً
                    conn.execute("PRAGMA foreign_keys = OFF")

                    # خطوة 2: إنشاء الجدول الجديد
                    conn.execute("""
                        CREATE TABLE platforms_new (
                            id              INTEGER PRIMARY KEY AUTOINCREMENT,
                            name            TEXT    NOT NULL UNIQUE,
                            type            TEXT    NOT NULL,
                            balance         REAL    NOT NULL DEFAULT 0,
                            monthly_limit   REAL    NOT NULL DEFAULT 200000,
                            monthly_used    REAL    NOT NULL DEFAULT 0,
                            last_reset_date TEXT    NOT NULL DEFAULT (strftime('%Y-%m', 'now')),
                            is_active       INTEGER NOT NULL DEFAULT 1
                        )
                    """)

                    # خطوة 3: نسخ البيانات القديمة
                    conn.execute("""
                        INSERT INTO platforms_new
                            (id, name, type, balance, monthly_limit,
                             monthly_used, last_reset_date, is_active)
                        SELECT
                            id, name, type, balance,
                            COALESCE(monthly_limit,   200000),
                            COALESCE(monthly_used,    0),
                            COALESCE(last_reset_date, strftime('%Y-%m', 'now')),
                            COALESCE(is_active,       1)
                        FROM platforms
                    """)

                    # خطوة 4: حذف القديم وإعادة التسمية
                    conn.execute("DROP TABLE platforms")
                    conn.execute("ALTER TABLE platforms_new RENAME TO platforms")

                    # خطوة 5: إعادة تفعيل foreign keys
                    conn.execute("PRAGMA foreign_keys = ON")

                    conn.commit()
                    print("[DB] platforms migration done ")

        except Exception as e:
            print(f"[DB] Platform setup error: {e}")

        # Transactions table migrations
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                    operation_type  TEXT    NOT NULL
                                    CHECK (operation_type IN ('outbound', 'inbound', 'commission', 'manual_commission')),
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
                CREATE INDEX IF NOT EXISTS idx_transactions_platform  ON transactions(platform_id);
            """)
            conn.commit()
        except Exception:
            pass

        # Migration: expand operation_type CHECK to include manual_commission
        try:
            conn.execute("INSERT INTO transactions (operation_type, service_name, platform_id, amount_spent, amount_required, payment_status) VALUES ('manual_commission', '__migration_test__', 1, 0, 0, 'paid')")
            conn.execute("DELETE FROM transactions WHERE service_name = '__migration_test__'")
            conn.commit()
        except Exception:
            # CHECK constraint is old, need to rebuild table
            try:
                conn.execute("PRAGMA foreign_keys = OFF")
                conn.executescript("""
                    CREATE TABLE transactions_new (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                        operation_type  TEXT    NOT NULL
                                        CHECK (operation_type IN ('outbound', 'inbound', 'commission', 'manual_commission')),
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
                    INSERT INTO transactions_new (id, created_at, operation_type, service_name, platform_id, customer_id, amount_spent, amount_required, reference_no, is_card, payment_status, is_delivered, notes)
                        SELECT id, created_at, operation_type, service_name, platform_id, customer_id, amount_spent, amount_required, reference_no, is_card, payment_status, is_delivered, notes FROM transactions;
                    DROP TABLE transactions;
                    ALTER TABLE transactions_new RENAME TO transactions;
                """)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                print("[DB] transactions table migrated for manual_commission support")
            except Exception as e:
                print(f"[DB] transactions migration error: {e}")

        # Column migrations
        for sql in [
            "ALTER TABLE transactions ADD COLUMN is_delivered INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE platforms ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE platforms ADD COLUMN initial_balance REAL NOT NULL DEFAULT 0",
        ]:
            try:
                conn.execute(sql)
                conn.commit()
            except Exception:
                pass

        # Shipping codes table (1-to-Many: customer → codes)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS shipping_codes (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
                    code        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                );
                CREATE INDEX IF NOT EXISTS idx_shipping_codes_customer ON shipping_codes(customer_id);
                CREATE INDEX IF NOT EXISTS idx_shipping_codes_code     ON shipping_codes(code);
            """)
            conn.commit()
        except Exception:
            pass

        # Seed the capital ledger for existing installations once. Platform deposits
        # already represent central-budget injections; initial platform balances were
        # historically stored only on platforms.
        try:
            seeded = conn.execute(
                "SELECT value FROM settings WHERE key = 'capital_movements_seeded'"
            ).fetchone()
            if not seeded:
                conn.execute("""
                    INSERT INTO machine_deposits (platform_id, amount, notes, created_at)
                    SELECT id, initial_balance, 'historical initial platform balance', '1970-01-01 00:00:00'
                    FROM platforms
                    WHERE COALESCE(initial_balance, 0) > 0
                      AND NOT EXISTS (
                          SELECT 1 FROM machine_deposits md
                          WHERE md.platform_id = platforms.id
                            AND md.notes = 'historical initial platform balance'
                      )
                """)
                conn.execute("""
                    INSERT INTO capital_movements (target_type, target_id, amount, notes, created_at)
                    SELECT 'platform', platform_id, amount, COALESCE(notes, 'historical platform injection'), created_at
                    FROM machine_deposits
                    WHERE amount != 0
                """)
                conn.execute("""
                    INSERT INTO capital_movements (target_type, target_id, amount, notes, created_at)
                    SELECT 'cash', NULL, cash_vault, 'historical cash injection', '1970-01-01 00:00:00'
                    FROM budget
                    WHERE id = 1 AND COALESCE(cash_vault, 0) > 0
                """)
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES ('capital_movements_seeded', '1')"
                )
                conn.commit()
        except Exception as e:
            print(f"[DB] capital movements seed skipped: {e}")

        # amount_paid column — non-destructive partial payment tracking
        try:
            conn.execute(
                "ALTER TABLE transactions ADD COLUMN amount_paid REAL NOT NULL DEFAULT 0"
            )
            conn.commit()
        except Exception:
            pass  # column already exists

        # is_netted — marks inbound transactions that were settled via مقاصة (FIFO netting)
        # instead of cash delivery; prevents double-counting in the ledger.
        try:
            conn.execute(
                "ALTER TABLE transactions ADD COLUMN is_netted INTEGER NOT NULL DEFAULT 0"
            )
            conn.commit()
        except Exception:
            pass  # column already exists

        # payments_history — audit trail for settle_customer_debt entries
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS payments_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL REFERENCES customers(id),
                    amount      REAL    NOT NULL,
                    notes       TEXT,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                );
                CREATE INDEX IF NOT EXISTS idx_payments_history_customer ON payments_history(customer_id);
                CREATE INDEX IF NOT EXISTS idx_payments_history_created  ON payments_history(created_at);
            """)
            conn.commit()
        except Exception as e:
            print(f"[DB] payments_history setup: {e}")

    print(f"[DB] Database ready: {DB_PATH}")
