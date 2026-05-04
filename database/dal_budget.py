"""
Data Access Layer - Budget & Platforms
طبقة الوصول للبيانات - الميزانية والمنصات
"""

from database.connection import get_connection


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


def adjust_main_budget(delta: float) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE budget SET main_budget = main_budget + ? WHERE id = 1", (delta,))
        conn.commit()


def has_sufficient_budget(amount: float) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT main_budget FROM budget WHERE id = 1").fetchone()
        return (row["main_budget"] if row else 0) >= amount


def set_cash_vault(new_amount: float) -> None:
    if new_amount < 0:
        raise ValueError("قيمة الكاش لا يمكن أن تكون سالبة")
    
    with get_connection() as conn:
        try:
            budget = conn.execute("SELECT main_budget, cash_vault FROM budget WHERE id = 1").fetchone()
            current_cash = budget["cash_vault"]
            diff = new_amount - current_cash

            if diff > 0:
                if budget["main_budget"] < diff:
                    raise ValueError(f"الميزانية غير كافية لزيادة الكاش — المتاح: {budget['main_budget']:,.2f} ج")
                # Deduct from main_budget
                conn.execute("UPDATE budget SET main_budget = main_budget - ? WHERE id = 1", (diff,))
            elif diff < 0:
                # Return to main_budget if reduced
                conn.execute("UPDATE budget SET main_budget = main_budget + ? WHERE id = 1", (abs(diff),))
            
            conn.execute(
                "UPDATE budget SET cash_vault = ? WHERE id = 1",
                (new_amount,)
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
    جلب كل المنصات النشطة مع عدد العمليات
    platform_type: 'machine' | 'wallet' | 'instapay' | None (الكل)
    """
    with get_connection() as conn:
        query = """
            SELECT p.*, COUNT(t.id) as transaction_count
            FROM platforms p
            LEFT JOIN transactions t ON t.platform_id = p.id
            WHERE p.is_active = 1
        """
        params = []
        if platform_type:
            query += " AND p.type = ?"
            params.append(platform_type)
        
        query += " GROUP BY p.id ORDER BY p.name"
        
        rows = conn.execute(query, params).fetchall()
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
        try:
            if initial_balance > 0:
                budget = conn.execute("SELECT main_budget FROM budget WHERE id = 1").fetchone()
                if budget["main_budget"] < initial_balance:
                    raise ValueError(f"الميزانية غير كافية للرصيد الابتدائي — المتاح: {budget['main_budget']:,.2f} ج")
                
                # Deduct from main budget
                conn.execute("UPDATE budget SET main_budget = main_budget - ? WHERE id = 1", (initial_balance,))

            cursor = conn.execute(
                "INSERT INTO platforms (name, type, balance, monthly_limit) VALUES (?, ?, ?, ?)",
                (name, platform_type, initial_balance, monthly_limit)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise


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
    - يخصم من الخزينة النقدية (الكاش)
    - يزيد رصيد المنصة
    """
    if amount <= 0:
        raise ValueError("مبلغ الإيداع يجب أن يكون أكبر من الصفر")

    with get_connection() as conn:
        try:
            budget = conn.execute("SELECT main_budget FROM budget WHERE id = 1").fetchone()
            if budget["main_budget"] < amount:
                raise ValueError(
                    f"الميزانية المركزية غير كافية — المتاح: {budget['main_budget']:,.2f} ج  |  "
                    f"المطلوب: {amount:,.2f} ج"
                )

            platform = conn.execute(
                "SELECT id FROM platforms WHERE id = ? AND is_active = 1", (platform_id,)
            ).fetchone()
            if not platform:
                raise ValueError("المنصة غير موجودة أو محذوفة")

            # خصم من الميزانية المركزية وليس الكاش
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


def update_platform_limit(platform_id: int, new_limit: float) -> None:
    """تحديث الحد الشهري لمنصة محفظة أو انستا باي."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE platforms SET monthly_limit = ? WHERE id = ?", (new_limit, platform_id)
        )
        conn.commit()


def delete_platform(platform_id: int) -> None:
    """حذف منصة (Soft Delete)"""
    with get_connection() as conn:
        conn.execute("UPDATE platforms SET is_active = 0 WHERE id = ?", (platform_id,))
        conn.commit()
