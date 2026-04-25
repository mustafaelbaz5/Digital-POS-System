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
    conn.execute("PRAGMA journal_mode = WAL")   # أداء أفضل
    conn.row_factory = sqlite3.Row              # النتائج كـ dict
    return conn


# ─── Schema Creation ──────────────────────────────────────────────
SCHEMA_SQL = """

-- ══════════════════════════════════════════
--  1. الإعدادات العامة  (Settings)
-- ══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS settings (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

-- ══════════════════════════════════════════
--  2. الميزانية الرئيسية  (Main Budget)
-- ══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS budget (
    id              INTEGER PRIMARY KEY CHECK (id = 1),  -- صف واحد فقط
    main_budget     REAL    NOT NULL DEFAULT 0,          -- رأس المال
    cash_vault      REAL    NOT NULL DEFAULT 0           -- الخزينة النقدية
);

-- إدراج صف الميزانية إذا لم يكن موجوداً
INSERT OR IGNORE INTO budget (id, main_budget, cash_vault) VALUES (1, 0, 0);

-- ══════════════════════════════════════════
--  3. المنصات الرقمية  (Platforms)
-- ══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS platforms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,             -- اسم المنصة
    type            TEXT    NOT NULL                     -- 'machine' | 'wallet'
                    CHECK (type IN ('machine', 'wallet')),
    balance         REAL    NOT NULL DEFAULT 0,          -- الرصيد الحالي
    monthly_limit   REAL    NOT NULL DEFAULT 200000,     -- حد المحفظة الشهري
    monthly_used    REAL    NOT NULL DEFAULT 0,          -- المستخدم من الحد
    last_reset_date TEXT    NOT NULL DEFAULT (strftime('%Y-%m', 'now')), -- آخر تصفير
    is_active       INTEGER NOT NULL DEFAULT 1           -- 0 = محذوف
);

-- ══════════════════════════════════════════
--  4. المجموعات  (Groups)
-- ══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS groups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,             -- اسم المجموعة
    leader_id       INTEGER,                             -- قائد المجموعة (customer.id)
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ══════════════════════════════════════════
--  5. العملاء  (Customers)
-- ══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    phone           TEXT,
    group_id        INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    total_debt      REAL    NOT NULL DEFAULT 0,          -- إجمالي المديونية
    notes           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- تحديث leader_id في groups بعد إنشاء جدول customers
-- (العلاقة الدائرية تُحل بعد الإنشاء)
CREATE INDEX IF NOT EXISTS idx_customers_group ON customers(group_id);

-- ══════════════════════════════════════════
--  6. سجل العمليات  (Transactions)
-- ══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,

    -- التوقيت
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    -- تصنيف العملية
    operation_type  TEXT    NOT NULL                     -- 'outbound' | 'inbound'
                    CHECK (operation_type IN ('outbound', 'inbound')),
    service_name    TEXT    NOT NULL,                    -- اسم الخدمة

    -- الأطراف
    platform_id     INTEGER NOT NULL REFERENCES platforms(id),
    customer_id     INTEGER REFERENCES customers(id) ON DELETE SET NULL,

    -- المبالغ
    amount_spent    REAL    NOT NULL DEFAULT 0,          -- المصروف من الرصيد
    amount_required REAL    NOT NULL DEFAULT 0,          -- المطلوب من العميل
    profit          REAL    GENERATED ALWAYS AS           -- الربح (محسوب تلقائياً)
                    (amount_required - amount_spent) VIRTUAL,

    -- التوثيق
    reference_no    TEXT,                                -- رقم العملية
    is_card         INTEGER NOT NULL DEFAULT 0,          -- 1 = كارت (بدون رقم)

    -- حالة الدفع
    payment_status  TEXT    NOT NULL DEFAULT 'pending'   -- 'cash' | 'pending' | 'paid'
                    CHECK (payment_status IN ('cash', 'pending', 'paid')),

    -- حالة التسليم (للعمليات الواردة فقط)
    is_delivered    INTEGER NOT NULL DEFAULT 0,          -- 1 = تم تسليم المبلغ للعميل

    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer  ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_platform  ON transactions(platform_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status    ON transactions(payment_status);
CREATE INDEX IF NOT EXISTS idx_transactions_created   ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_reference ON transactions(reference_no);

-- ══════════════════════════════════════════
--  7. سجل إيداعات الماكينات  (Machine Deposits)
-- ══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS machine_deposits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_id     INTEGER NOT NULL REFERENCES platforms(id),
    amount          REAL    NOT NULL,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

"""


def initialize_database() -> None:
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        # Migration: إضافة عمود is_delivered لو مش موجود
        try:
            conn.execute("ALTER TABLE transactions ADD COLUMN is_delivered INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        except Exception:
            pass  # العمود موجود بالفعل
    print(f"[DB] قاعدة البيانات جاهزة: {DB_PATH}")