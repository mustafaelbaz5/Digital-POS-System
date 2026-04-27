"""
Data Access Layer - Budget & Platforms
طبقة الوصول للبيانات - الميزانية والمنصات
"""

from database.schema import get_connection


# ══════════════════════════════════════════
#  الميزانية والخزينة
# ══════════════════════════════════════════

def get_budget() -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT main_budget, cash_vault FROM budget WHERE id = 1").fetchone()
        return dict(row)


def update_main_budget(amount: float) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE budget SET main_budget = ? WHERE id = 1", (amount,))
        conn.commit()


def set_cash_vault(new_amount: float) -> None:
    if new_amount < 0:
        raise ValueError("قيمة الكاش لا يمكن أن تكون سالبة")
    with get_connection() as conn:
        try:
            current = conn.execute("SELECT cash_vault FROM budget WHERE id = 1").fetchone()["cash_vault"]
            delta = new_amount - (current or 0)
            conn.execute(
                "UPDATE budget SET cash_vault = ?, main_budget = main_budget - ? WHERE id = 1",
                (new_amount, delta)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def adjust_cash(delta: float) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1", (delta,))
        conn.commit()


# ══════════════════════════════════════════
#  المنصات  (Platforms)
# ══════════════════════════════════════════

def get_all_platforms(platform_type: str = None) -> list[dict]:
    """
    جلب كل المنصات النشطة
    platform_type: 'machine' | 'wallet' | 'instapay' | None (الكل)
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
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM platforms WHERE id = ?", (platform_id,)).fetchone()
        return dict(row) if row else None


def add_platform(name: str, platform_type: str, initial_balance: float = 0,
                 monthly_limit: float = None) -> int:
    """إضافة منصة جديدة — يرجع الـ ID"""
    # Default monthly limit: instapay=400000, wallet=200000, machine=0
    if monthly_limit is None:
        if platform_type == 'instapay':
            monthly_limit = 400000
        elif platform_type == 'wallet':
            monthly_limit = 200000
        else:
            monthly_limit = 0

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO platforms (name, type, balance, monthly_limit) VALUES (?, ?, ?, ?)",
            (name, platform_type, initial_balance, monthly_limit)
        )
        conn.commit()
        return cursor.lastrowid


def update_platform_balance(platform_id: int, delta: float, conn=None) -> None:
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
    """
    إيداع مبلغ لمنصة (ماكينة أو محفظة أو انستا باي)
    - يخصم من main_budget
    - يزيد رصيد المنصة
    """
    if amount <= 0:
        raise ValueError("مبلغ الإيداع يجب أن يكون أكبر من الصفر")

    with get_connection() as conn:
        try:
            budget = conn.execute("SELECT main_budget FROM budget WHERE id = 1").fetchone()
            if budget["main_budget"] < amount:
                raise ValueError(
                    f"الميزانية غير كافية — المتاح: {budget['main_budget']:,.2f} ج  |  "
                    f"المطلوب: {amount:,.2f} ج"
                )

            platform = conn.execute(
                "SELECT id FROM platforms WHERE id = ? AND is_active = 1", (platform_id,)
            ).fetchone()
            if not platform:
                raise ValueError("المنصة غير موجودة أو محذوفة")

            conn.execute("UPDATE budget SET main_budget = main_budget - ? WHERE id = 1", (amount,))
            conn.execute("UPDATE platforms SET balance = balance + ? WHERE id = ?", (amount, platform_id))
            conn.execute(
                "INSERT INTO machine_deposits (platform_id, amount, notes) VALUES (?, ?, ?)",
                (platform_id, amount, notes)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def record_daily_commission(platform_id: int, amount: float, notes: str = "") -> None:
    """
    تسجيل عمولة يومية لماكينة
    - يخصم amount من رصيد الماكينة
    - يضيف amount لـ cash_vault
    """
    if amount <= 0:
        raise ValueError("مبلغ العمولة يجب أن يكون أكبر من الصفر")

    with get_connection() as conn:
        try:
            platform = conn.execute(
                "SELECT id, type, balance FROM platforms WHERE id = ? AND is_active = 1", (platform_id,)
            ).fetchone()

            if not platform:
                raise ValueError("المنصة غير موجودة")
            if platform["type"] != "machine":
                raise ValueError("العمولة اليومية متاحة للماكينات فقط")
            if platform["balance"] < amount:
                raise ValueError(
                    f"رصيد الماكينة غير كافٍ — الرصيد: {platform['balance']:,.2f} ج"
                )

            # خصم من الماكينة
            conn.execute("UPDATE platforms SET balance = balance - ? WHERE id = ?", (amount, platform_id))
            # إضافة للخزينة
            conn.execute("UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1", (amount,))
            # تسجيل في سجل العمولات
            conn.execute(
                "INSERT INTO daily_commissions (platform_id, amount, notes) VALUES (?, ?, ?)",
                (platform_id, amount, notes)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def reset_wallet_limit_if_needed(wallet_id: int) -> bool:
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
                "UPDATE platforms SET monthly_used = 0, last_reset_date = ? WHERE id = ?",
                (current_month, wallet_id)
            )
            conn.commit()
            return True
        return False


def delete_platform(platform_id: int) -> None:
    """حذف منصة (Soft Delete)"""
    with get_connection() as conn:
        conn.execute("UPDATE platforms SET is_active = 0 WHERE id = ?", (platform_id,))
        conn.commit()
