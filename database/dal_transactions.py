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

            # 3b. تحديث monthly_used للمحافظ فقط مع تطبيق الليمت
            platform_row = conn.execute(
                "SELECT type, monthly_used, monthly_limit FROM platforms WHERE id = ?",
                (platform_id,)
            ).fetchone()

            if platform_row["type"] in ("wallet", "instapay"):
                new_used = platform_row["monthly_used"] + amount_spent
                if new_used > platform_row["monthly_limit"]:
                    raise ValueError(
                        f"تجاوز الحد الشهري للمحفظة — "
                        f"المستخدم: {platform_row['monthly_used']:,.2f} / "
                        f"الحد: {platform_row['monthly_limit']:,.2f} ج"
                    )
                conn.execute(
                    "UPDATE platforms SET monthly_used = monthly_used + ? WHERE id = ?",
                    (amount_spent, platform_id)
                )

            # 4. تحديث حسب حالة الدفع
            if payment_status == "pending" and customer_id:
                # مؤجل → يضاف للمديونية
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                    (amount_required, customer_id)
                )
            # paid → تم السداد مباشرة، لا يضاف للمديونية ولا للكاش

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
    notes:            str = "",
    is_delivered:     bool = False,   # هل تم تسليم المبلغ للعميل؟
) -> int:
    """
    عملية استلام وارد (Inbound) - للمحافظ فقط
    ──────────────────────────────────────────
    - يضيف amount_received لرصيد المحفظة
    - يخصم amount_delivered من الخزينة النقدية
    - لو العميل محدد → يُسجَّل المبلغ في حسابه (له أو عليه حسب is_delivered)
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
            if row["type"] not in ("wallet", "instapay"):
                raise ValueError("عملية الاستلام متاحة للمحافظ وانستا باي فقط")

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
                     amount_spent, amount_required, reference_no, payment_status,
                     is_delivered, notes)
                VALUES ('inbound', ?, ?, ?, ?, ?, ?, 'cash', ?, ?)
            """, (
                service_name, wallet_id, customer_id,
                amount_delivered,    # amount_spent = ما خرج من الكاش
                amount_received,     # amount_required = ما استلمناه
                reference_no,
                1 if is_delivered else 0,
                notes
            ))
            transaction_id = cursor.lastrowid

            # 4. تحديث رصيد المحفظة
            conn.execute(
                "UPDATE platforms SET balance = balance + ? WHERE id = ?",
                (amount_received, wallet_id)
            )

            # 5. خصم من الخزينة النقدية
            conn.execute(
                "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                (amount_delivered,)
            )

            # 6. تسجيل في حساب العميل — المبلغ المسلم (له أو لم يُسلَّم بعد)
            if customer_id:
                if is_delivered:
                    # تم التسليم → ليس له شيء مستحق (صفر مديونية)
                    pass
                else:
                    # لم يُسلَّم بعد → مبلغ مستحق للعميل (نقص من مديونيته أو يصبح له)
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                        (amount_delivered, customer_id)
                    )

            conn.commit()
            return transaction_id

        except Exception:
            conn.rollback()
            raise


def mark_as_delivered(transaction_id: int) -> None:
    """
    تحويل عملية واردة من 'لم يُسلَّم' إلى 'تم التسليم'
    يُصفّر المبلغ المستحق للعميل
    """
    with get_connection() as conn:
        try:
            row = conn.execute("""
                SELECT customer_id, amount_spent, is_delivered, operation_type
                FROM transactions WHERE id = ?
            """, (transaction_id,)).fetchone()

            if not row:
                raise ValueError("العملية غير موجودة")
            if row["operation_type"] != "inbound":
                raise ValueError("هذه الوظيفة للعمليات الواردة فقط")
            if row["is_delivered"]:
                raise ValueError("تم التسليم مسبقاً")

            conn.execute(
                "UPDATE transactions SET is_delivered = 1 WHERE id = ?",
                (transaction_id,)
            )

            # إلغاء تأثير المبلغ على العميل (كان مسجلاً كـ "له")
            if row["customer_id"]:
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                    (row["amount_spent"], row["customer_id"])
                )

            conn.commit()
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
                t.reference_no, t.is_card, t.payment_status, t.is_delivered,
                t.notes, p.name AS platform_name, p.type AS platform_type,
                c.name AS customer_name, t.customer_id
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

        # مجموع انستا باي
        instapay = conn.execute("""
            SELECT COALESCE(SUM(balance), 0) AS total
            FROM platforms WHERE type = 'instapay' AND is_active = 1
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

        # إجمالي المؤجل
        pending = conn.execute("""
            SELECT COALESCE(SUM(amount_required), 0) AS total
            FROM transactions WHERE payment_status = 'pending'
        """).fetchone()

        total_assets = (
            (machines["total"]  or 0) +
            (wallets["total"]   or 0) +
            (instapay["total"]  or 0) +
            (budget["cash_vault"] or 0)
        )

        total_balances = total_assets

        return {
            "main_budget":     budget["main_budget"]  or 0,
            "cash_vault":      budget["cash_vault"]   or 0,
            "total_machines":  machines["total"]      or 0,
            "total_wallets":   (wallets["total"] or 0) + (instapay["total"] or 0),
            "total_instapay":  instapay["total"]      or 0,
            "total_debts":     debts["total"]         or 0,
            "today_profit":    today_profit["total"]  or 0,
            "month_profit":    month_profit["total"]  or 0,
            "total_balances":  total_balances,
            "total_assets":    total_assets,
            "net_position":    total_balances + (debts["total"] or 0) - (budget["main_budget"] or 0),
            "total_pending":   pending["total"] or 0,
        }

# ══════════════════════════════════════════
#  تعديل وحذف العمليات (Edit & Delete)
# ══════════════════════════════════════════

def update_transaction_status(transaction_id: int, new_status: str) -> None:
    """
    تغيير حالة الدفع (pending ↔ paid) أو تغيير is_delivered للوارد
    new_status: 'pending' | 'paid' | 'delivered' | 'not_delivered'
    """
    with get_connection() as conn:
        try:
            row = conn.execute("""
                SELECT customer_id, amount_required, amount_spent,
                       payment_status, is_delivered, operation_type
                FROM transactions WHERE id = ?
            """, (transaction_id,)).fetchone()

            if not row:
                raise ValueError("العملية غير موجودة")

            if new_status in ('pending', 'paid'):
                old = row["payment_status"]
                if old == new_status:
                    return

                if old == 'pending' and new_status == 'paid':
                    # pending → paid: خصم من مديونية العميل
                    conn.execute(
                        "UPDATE transactions SET payment_status = 'paid' WHERE id = ?",
                        (transaction_id,)
                    )
                    if row["customer_id"]:
                        conn.execute(
                            "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                            (row["amount_required"], row["customer_id"])
                        )

                elif old == 'paid' and new_status == 'pending':
                    # paid → pending: أعد المبلغ لمديونية العميل
                    conn.execute(
                        "UPDATE transactions SET payment_status = 'pending' WHERE id = ?",
                        (transaction_id,)
                    )
                    if row["customer_id"]:
                        conn.execute(
                            "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                            (row["amount_required"], row["customer_id"])
                        )
                else:
                    raise ValueError(f"لا يمكن التحويل من '{old}' إلى '{new_status}'")

            elif new_status == 'delivered':
                if row["operation_type"] != 'inbound':
                    raise ValueError("تغيير التسليم للعمليات الواردة فقط")
                if row["is_delivered"]:
                    return
                conn.execute("UPDATE transactions SET is_delivered = 1 WHERE id = ?", (transaction_id,))
                if row["customer_id"]:
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                        (row["amount_spent"], row["customer_id"])
                    )

            elif new_status == 'not_delivered':
                if row["operation_type"] != 'inbound':
                    raise ValueError("تغيير التسليم للعمليات الواردة فقط")
                if not row["is_delivered"]:
                    return
                conn.execute("UPDATE transactions SET is_delivered = 0 WHERE id = ?", (transaction_id,))
                if row["customer_id"]:
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                        (row["amount_spent"], row["customer_id"])
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise


def delete_transaction(transaction_id: int) -> None:
    """
    حذف عملية مع عكس تأثيرها المالي بالكامل
    """
    with get_connection() as conn:
        try:
            row = conn.execute("""
                SELECT t.*, p.type as platform_type
                FROM transactions t
                JOIN platforms p ON p.id = t.platform_id
                WHERE t.id = ?
            """, (transaction_id,)).fetchone()

            if not row:
                raise ValueError("العملية غير موجودة")

            op     = row["operation_type"]
            status = row["payment_status"]
            cid    = row["customer_id"]
            pid    = row["platform_id"]
            spent  = row["amount_spent"]
            req    = row["amount_required"]
            p_type = row["platform_type"]
            delivered = row["is_delivered"]

            if op == "outbound":
                # أعد الرصيد للمنصة
                conn.execute("UPDATE platforms SET balance = balance + ? WHERE id = ?", (spent, pid))
                # أعد monthly_used للمحافظ
                if p_type in ("wallet", "instapay"):
                    conn.execute(
                        "UPDATE platforms SET monthly_used = MAX(0, monthly_used - ?) WHERE id = ?",
                        (spent, pid)
                    )
                # عكس تأثير الدفع — فقط pending يؤثر على المديونية
                if status == "pending" and cid:
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?", (req, cid)
                    )
                # paid: تم السداد مباشرة، لا يوجد تأثير على المديونية يحتاج عكس

            elif op == "inbound":
                # أعد الخصم على المحفظة
                conn.execute("UPDATE platforms SET balance = balance - ? WHERE id = ?", (req, pid))
                # أعد الكاش
                conn.execute("UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1", (spent,))
                # عكس تأثير العميل
                if cid and not delivered:
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?", (spent, cid)
                    )

            # حذف العملية
            conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()

        except Exception:
            conn.rollback()
            raise
