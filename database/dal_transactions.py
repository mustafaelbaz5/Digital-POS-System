"""
Data Access Layer - Transactions
طبقة الوصول للبيانات - العمليات

كل عملية تستخدم Atomic Transaction (commit/rollback)
لضمان تكامل البيانات
"""

from database.schema import get_connection


# ══════════════════════════════════════════
#  إضافة العمليات  (Create Transactions)
# ══════════════════════════════════════════

def add_outbound_transaction(
    platform_id:    int,
    customer_id:    int,
    service_name:   str,
    amount_spent:   float,
    amount_required: float,
    payment_status: str,      # 'cash' | 'pending'
    reference_no:   str = "",
    is_card:        bool = False,
    notes:          str = ""
) -> int:
    """
    عملية شحن صادر (Outbound)
    ─────────────────────────
    - يخصم amount_spent من رصيد المنصة
    - إذا cash   → يضيف amount_required للخزينة النقدية
    - إذا pending → يضيف amount_required لمديونية العميل
    يرجع ID العملية
    """
    with get_connection() as conn:
        try:
            # 1. التحقق من رصيد المنصة
            row = conn.execute(
                "SELECT balance FROM platforms WHERE id = ?", (platform_id,)
            ).fetchone()

            if not row:
                raise ValueError("المنصة غير موجودة")

            if row["balance"] < amount_spent:
                raise ValueError(
                    f"رصيد غير كافٍ - الرصيد الحالي: {row['balance']:.2f} ج"
                )

            # 2. تسجيل العملية
            cursor = conn.execute("""
                INSERT INTO transactions
                    (operation_type, service_name, platform_id, customer_id,
                     amount_spent, amount_required, reference_no, is_card,
                     payment_status, notes)
                VALUES ('outbound', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                service_name, platform_id, customer_id,
                amount_spent, amount_required,
                reference_no, 1 if is_card else 0,
                payment_status, notes
            ))
            transaction_id = cursor.lastrowid

            # 3. خصم من رصيد المنصة
            conn.execute(
                "UPDATE platforms SET balance = balance - ? WHERE id = ?",
                (amount_spent, platform_id)
            )

            # 4. تحديث حسب حالة الدفع
            if payment_status == "cash":
                # إضافة للخزينة النقدية
                conn.execute(
                    "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                    (amount_required,)
                )
            elif payment_status == "pending" and customer_id:
                # إضافة لمديونية العميل
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                    (amount_required, customer_id)
                )

            conn.commit()
            return transaction_id

        except Exception:
            conn.rollback()
            raise


def add_inbound_transaction(
    wallet_id:        int,
    customer_id:      int,
    service_name:     str,
    amount_received:  float,    # المستلم في المحفظة
    amount_delivered: float,    # المسلم كاش للعميل
    reference_no:     str = "",
    notes:            str = ""
) -> int:
    """
    عملية استلام وارد (Inbound) - للمحافظ فقط
    ──────────────────────────────────────────
    - يضيف amount_received لرصيد المحفظة
    - يخصم amount_delivered من الخزينة النقدية
    - الربح = amount_received - amount_delivered
    يرجع ID العملية
    """
    with get_connection() as conn:
        try:
            # 1. التحقق من نوع المنصة
            row = conn.execute(
                "SELECT type, balance FROM platforms WHERE id = ?", (wallet_id,)
            ).fetchone()

            if not row:
                raise ValueError("المنصة غير موجودة")
            if row["type"] != "wallet":
                raise ValueError("عملية الاستلام متاحة للمحافظ فقط")

            # 2. التحقق من رصيد الخزينة
            budget = conn.execute(
                "SELECT cash_vault FROM budget WHERE id = 1"
            ).fetchone()

            if budget["cash_vault"] < amount_delivered:
                raise ValueError(
                    f"الكاش غير كافٍ - الكاش الحالي: {budget['cash_vault']:.2f} ج"
                )

            # 3. تسجيل العملية
            cursor = conn.execute("""
                INSERT INTO transactions
                    (operation_type, service_name, platform_id, customer_id,
                     amount_spent, amount_required, reference_no, payment_status, notes)
                VALUES ('inbound', ?, ?, ?, ?, ?, ?, 'cash', ?)
            """, (
                service_name, wallet_id, customer_id,
                amount_delivered,    # amount_spent = ما خرج من الكاش
                amount_received,     # amount_required = ما استلمناه
                reference_no, notes
            ))
            transaction_id = cursor.lastrowid

            # 4. تحديث رصيد المحفظة
            conn.execute(
                "UPDATE platforms SET balance = balance + ?, monthly_used = monthly_used + ? WHERE id = ?",
                (amount_received, amount_received, wallet_id)
            )

            # 5. خصم من الخزينة النقدية
            conn.execute(
                "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                (amount_delivered,)
            )

            conn.commit()
            return transaction_id

        except Exception:
            conn.rollback()
            raise


# ══════════════════════════════════════════
#  جلب العمليات  (Read Transactions)
# ══════════════════════════════════════════

def get_transactions(
    customer_id:    int  = None,
    platform_id:    int  = None,
    payment_status: str  = None,    # 'cash' | 'pending' | 'paid'
    date_from:      str  = None,    # 'YYYY-MM-DD'
    date_to:        str  = None,
    limit:          int  = 500
) -> list[dict]:
    """جلب العمليات مع فلترة مرنة"""
    with get_connection() as conn:
        conditions = []
        params     = []

        if customer_id:
            conditions.append("t.customer_id = ?")
            params.append(customer_id)

        if platform_id:
            conditions.append("t.platform_id = ?")
            params.append(platform_id)

        if payment_status:
            conditions.append("t.payment_status = ?")
            params.append(payment_status)

        if date_from:
            conditions.append("DATE(t.created_at) >= ?")
            params.append(date_from)

        if date_to:
            conditions.append("DATE(t.created_at) <= ?")
            params.append(date_to)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        rows = conn.execute(f"""
            SELECT
                t.id, t.created_at, t.operation_type, t.service_name,
                t.amount_spent, t.amount_required, t.profit,
                t.reference_no, t.is_card, t.payment_status, t.notes,
                p.name  AS platform_name, p.type AS platform_type,
                c.name  AS customer_name
            FROM transactions t
            JOIN platforms p ON p.id = t.platform_id
            LEFT JOIN customers c ON c.id = t.customer_id
            {where}
            ORDER BY t.created_at DESC
            LIMIT ?
        """, (*params, limit)).fetchall()

        return [dict(r) for r in rows]


def search_by_reference(reference_no: str) -> list[dict]:
    """البحث عن عملية برقم المرجع"""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                t.*, p.name AS platform_name, c.name AS customer_name
            FROM transactions t
            JOIN platforms p ON p.id = t.platform_id
            LEFT JOIN customers c ON c.id = t.customer_id
            WHERE t.reference_no LIKE ?
            ORDER BY t.created_at DESC
        """, (f"%{reference_no}%",)).fetchall()
        return [dict(r) for r in rows]


def get_customer_statement(customer_id: int) -> dict:
    """
    كشف حساب مفصل للعميل
    يرجع: بيانات العميل + قائمة العمليات + الإجماليات
    """
    with get_connection() as conn:
        customer = conn.execute("""
            SELECT c.*, g.name AS group_name
            FROM customers c
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE c.id = ?
        """, (customer_id,)).fetchone()

        if not customer:
            return {}

        transactions = conn.execute("""
            SELECT t.*, p.name AS platform_name
            FROM transactions t
            JOIN platforms p ON p.id = t.platform_id
            WHERE t.customer_id = ?
            ORDER BY t.created_at DESC
        """, (customer_id,)).fetchall()

        # الإجماليات
        totals = conn.execute("""
            SELECT
                SUM(CASE WHEN payment_status = 'pending' THEN amount_required ELSE 0 END) AS total_pending,
                SUM(CASE WHEN payment_status = 'paid'    THEN amount_required ELSE 0 END) AS total_paid,
                SUM(CASE WHEN payment_status = 'cash'    THEN amount_required ELSE 0 END) AS total_cash,
                SUM(profit) AS total_profit,
                COUNT(*) AS total_count
            FROM transactions
            WHERE customer_id = ?
        """, (customer_id,)).fetchone()

        return {
            "customer":     dict(customer),
            "transactions": [dict(t) for t in transactions],
            "totals":       dict(totals)
        }


# ══════════════════════════════════════════
#  تعديل العمليات  (Update Transactions)
# ══════════════════════════════════════════

def mark_as_paid(transaction_id: int) -> None:
    """
    تحويل عملية من 'مؤجل' إلى 'تم السداد'
    يخصم المبلغ من مديونية العميل
    """
    with get_connection() as conn:
        try:
            row = conn.execute("""
                SELECT customer_id, amount_required, payment_status
                FROM transactions WHERE id = ?
            """, (transaction_id,)).fetchone()

            if not row:
                raise ValueError("العملية غير موجودة")
            if row["payment_status"] != "pending":
                raise ValueError("العملية ليست في حالة مؤجل")

            # تحديث حالة العملية
            conn.execute(
                "UPDATE transactions SET payment_status = 'paid' WHERE id = ?",
                (transaction_id,)
            )

            # خصم من المديونية
            if row["customer_id"]:
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                    (row["amount_required"], row["customer_id"])
                )

            conn.commit()

        except Exception:
            conn.rollback()
            raise


# ══════════════════════════════════════════
#  التنظيف  (Cleanup)
# ══════════════════════════════════════════

def cleanup_paid_transactions(customer_id: int = None) -> int:
    """
    حذف العمليات المسددة (paid)
    customer_id: إذا None يحذف الكل، وإلا يحذف لعميل معين
    يرجع عدد الصفوف المحذوفة
    """
    with get_connection() as conn:
        if customer_id:
            cursor = conn.execute(
                "DELETE FROM transactions WHERE payment_status = 'paid' AND customer_id = ?",
                (customer_id,)
            )
        else:
            cursor = conn.execute(
                "DELETE FROM transactions WHERE payment_status = 'paid'"
            )
        conn.commit()
        return cursor.rowcount


# ══════════════════════════════════════════
#  إحصائيات الداشبورد  (Dashboard Stats)
# ══════════════════════════════════════════

def get_dashboard_stats() -> dict:
    """جلب كل إحصائيات الداشبورد دفعة واحدة"""
    with get_connection() as conn:
        # الميزانية والكاش
        budget = conn.execute(
            "SELECT main_budget, cash_vault FROM budget WHERE id = 1"
        ).fetchone()

        # مجموع الماكينات
        machines = conn.execute("""
            SELECT COALESCE(SUM(balance), 0) AS total
            FROM platforms WHERE type = 'machine' AND is_active = 1
        """).fetchone()

        # مجموع المحافظ
        wallets = conn.execute("""
            SELECT COALESCE(SUM(balance), 0) AS total
            FROM platforms WHERE type = 'wallet' AND is_active = 1
        """).fetchone()

        # إجمالي المديونيات
        debts = conn.execute("""
            SELECT COALESCE(SUM(total_debt), 0) AS total
            FROM customers WHERE is_active = 1
        """).fetchone()

        # أرباح اليوم
        today_profit = conn.execute("""
            SELECT COALESCE(SUM(profit), 0) AS total
            FROM transactions
            WHERE DATE(created_at) = DATE('now', 'localtime')
        """).fetchone()

        # أرباح الشهر
        month_profit = conn.execute("""
            SELECT COALESCE(SUM(profit), 0) AS total
            FROM transactions
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')
        """).fetchone()

        total_balances = (
            (machines["total"] or 0) +
            (wallets["total"]  or 0) +
            (budget["cash_vault"] or 0)
        )

        return {
            "main_budget":    budget["main_budget"]  or 0,
            "cash_vault":     budget["cash_vault"]   or 0,
            "total_machines": machines["total"]      or 0,
            "total_wallets":  wallets["total"]       or 0,
            "total_debts":    debts["total"]         or 0,
            "today_profit":   today_profit["total"]  or 0,
            "month_profit":   month_profit["total"]  or 0,
            "total_balances": total_balances,
            # معادلة المطابقة: (أرصدة + ديون) vs (ميزانية + أرباح كلية)
            "net_position":   total_balances + (debts["total"] or 0) - (budget["main_budget"] or 0),
        }
