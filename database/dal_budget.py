"""
Data Access Layer - Budget & Platforms
طبقة الوصول للبيانات - الميزانية والمنصات
"""

from database.schema import get_connection


# ══════════════════════════════════════════
#  الميزانية والخزينة  (Budget & Cash)
# ══════════════════════════════════════════

def get_budget() -> dict:
    """جلب الميزانية الرئيسية والخزينة النقدية"""
    with get_connection() as conn:
        row = conn.execute("SELECT main_budget, cash_vault FROM budget WHERE id = 1").fetchone()
        return dict(row)


def update_main_budget(amount: float) -> None:
    """تعديل الميزانية الرئيسية يدوياً"""
    with get_connection() as conn:
        conn.execute("UPDATE budget SET main_budget = ? WHERE id = 1", (amount,))
        conn.commit()


def adjust_cash(delta: float) -> None:
    """زيادة أو خصم من الخزينة النقدية (delta يمكن أن يكون سالب)"""
    with get_connection() as conn:
        conn.execute("UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1", (delta,))
        conn.commit()


# ══════════════════════════════════════════
#  المنصات  (Platforms)
# ══════════════════════════════════════════

def get_all_platforms(platform_type: str = None) -> list[dict]: # pyright: ignore[reportArgumentType]
    """
    جلب كل المنصات النشطة
    platform_type: 'machine' | 'wallet' | None (الكل)
    """
    with get_connection() as conn:
        if platform_type:
            rows = conn.execute(
                "SELECT * FROM platforms WHERE is_active = 1 AND type = ? ORDER BY name",
                (platform_type,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM platforms WHERE is_active = 1 ORDER BY type, name"
            ).fetchall()
        return [dict(r) for r in rows]


def get_platform_by_id(platform_id: int) -> dict | None:
    """جلب منصة بالـ ID"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM platforms WHERE id = ?", (platform_id,)
        ).fetchone()
        return dict(row) if row else None


def add_platform(name: str, platform_type: str) -> int:
    """إضافة منصة جديدة - يرجع الـ ID"""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO platforms (name, type) VALUES (?, ?)",
            (name, platform_type)
        )
        conn.commit()
        return cursor.lastrowid # pyright: ignore[reportReturnType]


def update_platform_balance(platform_id: int, delta: float, conn=None) -> None:
    """
    تعديل رصيد منصة (delta يمكن أن يكون سالب)
    يقبل connection خارجي لدعم الـ atomic transactions
    """
    close_after = False
    if conn is None:
        conn = get_connection().__enter__()
        close_after = True

    conn.execute(
        "UPDATE platforms SET balance = balance + ? WHERE id = ?",
        (delta, platform_id)
    )

    if close_after:
        conn.commit()


def update_wallet_monthly_used(wallet_id: int, delta: float, conn=None) -> None:
    """تحديث المستخدم من الحد الشهري للمحفظة"""
    close_after = False
    if conn is None:
        conn = get_connection().__enter__()
        close_after = True

    conn.execute(
        "UPDATE platforms SET monthly_used = monthly_used + ? WHERE id = ?",
        (delta, wallet_id)
    )

    if close_after:
        conn.commit()


def deposit_to_platform(platform_id: int, amount: float, notes: str = "") -> None:
    """إيداع مبلغ لماكينة وتسجيله في سجل الإيداعات"""
    with get_connection() as conn:
        try:
            conn.execute(
                "UPDATE platforms SET balance = balance + ? WHERE id = ?",
                (amount, platform_id)
            )
            conn.execute(
                "INSERT INTO machine_deposits (platform_id, amount, notes) VALUES (?, ?, ?)",
                (platform_id, amount, notes)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def reset_wallet_limit_if_needed(wallet_id: int) -> bool:
    """
    تصفير الحد الشهري للمحفظة إذا تغير الشهر
    يرجع True إذا تم التصفير
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT last_reset_date FROM platforms WHERE id = ?", (wallet_id,)
        ).fetchone()

        if not row:
            return False

        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")

        if row["last_reset_date"] != current_month:
            conn.execute(
                """UPDATE platforms
                   SET monthly_used = 0, last_reset_date = ?
                   WHERE id = ?""",
                (current_month, wallet_id)
            )
            conn.commit()
            return True

        return False


def delete_platform(platform_id: int) -> None:
    """حذف منصة (Soft Delete)"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE platforms SET is_active = 0 WHERE id = ?", (platform_id,)
        )
        conn.commit()
