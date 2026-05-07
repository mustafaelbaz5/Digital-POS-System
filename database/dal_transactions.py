"""
dal_transactions.py — Transactions DAL
"""

from database.connection import get_connection


def add_outbound_transaction(
    platform_id: int,
    customer_id: int,
    service_name: str,
    amount_spent: float,
    amount_required: float,
    payment_status: str,
    reference_no: str = "",
    is_card: bool = False,
    notes: str = "",
    created_at: str = None,
) -> int:
    with get_connection() as conn:
        try:
            row = conn.execute(
                "SELECT balance FROM platforms WHERE id = ?", (platform_id,)
            ).fetchone()
            if not row:
                raise ValueError("المنصة غير موجودة")
            if row["balance"] < amount_spent:
                raise ValueError(
                    f"رصيد غير كافٍ - الرصيد الحالي: {row['balance']:.2f} ج"
                )

            sql = """
                INSERT INTO transactions
                    (operation_type, service_name, platform_id, customer_id,
                     amount_spent, amount_required, reference_no, is_card, payment_status, notes
                     {date_col})
                VALUES ('outbound', ?, ?, ?, ?, ?, ?, ?, ?, ? {date_val})
            """
            date_col = ", created_at" if created_at else ""
            date_val = ", ?" if created_at else ""
            params = [
                service_name,
                platform_id,
                customer_id,
                amount_spent,
                amount_required,
                reference_no,
                1 if is_card else 0,
                payment_status,
                notes,
            ]
            if created_at:
                params.append(created_at)

            cursor = conn.execute(
                sql.format(date_col=date_col, date_val=date_val), params
            )
            transaction_id = cursor.lastrowid

            conn.execute(
                "UPDATE platforms SET balance = balance - ? WHERE id = ?",
                (amount_spent, platform_id),
            )

            platform_row = conn.execute(
                "SELECT type, monthly_used, monthly_limit FROM platforms WHERE id = ?",
                (platform_id,),
            ).fetchone()
            if platform_row["type"] in ("wallet", "instapay"):
                new_used = platform_row["monthly_used"] + amount_spent
                if new_used > platform_row["monthly_limit"]:
                    raise ValueError(
                        f"تجاوز الحد الشهري — المستخدم: {platform_row['monthly_used']:,.0f} / "
                        f"الحد: {platform_row['monthly_limit']:,.0f} ج"
                    )
                conn.execute(
                    "UPDATE platforms SET monthly_used = monthly_used + ? WHERE id = ?",
                    (amount_spent, platform_id),
                )

            if payment_status == "paid":
                conn.execute(
                    "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                    (amount_required,),
                )
            elif payment_status == "pending" and customer_id:
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                    (amount_required, customer_id),
                )

            conn.commit()
            return transaction_id
        except Exception:
            conn.rollback()
            raise


def add_inbound_transaction(
    wallet_id: int,
    customer_id: int,
    service_name: str,
    amount_received: float,
    amount_delivered: float,
    reference_no: str = "",
    notes: str = "",
    is_delivered: bool = False,
    created_at: str = None,
) -> int:
    with get_connection() as conn:
        try:
            row = conn.execute(
                "SELECT type, balance FROM platforms WHERE id = ?", (wallet_id,)
            ).fetchone()
            if not row:
                raise ValueError("المنصة غير موجودة")
            if row["type"] not in ("wallet", "instapay"):
                raise ValueError("عملية الاستلام متاحة للمحافظ وانستا باي فقط")

            budget = conn.execute(
                "SELECT cash_vault FROM budget WHERE id = 1"
            ).fetchone()
            if budget["cash_vault"] < amount_delivered:
                raise ValueError(
                    f"الكاش غير كافٍ - الكاش الحالي: {budget['cash_vault']:.2f} ج"
                )

            sql = """
                INSERT INTO transactions
                    (operation_type, service_name, platform_id, customer_id,
                     amount_spent, amount_required, reference_no, payment_status, is_delivered, notes
                     {date_col})
                VALUES ('inbound', ?, ?, ?, ?, ?, ?, 'paid', ?, ? {date_val})
            """
            date_col = ", created_at" if created_at else ""
            date_val = ", ?" if created_at else ""
            params = [
                service_name,
                wallet_id,
                customer_id,
                amount_delivered,
                amount_received,
                reference_no,
                1 if is_delivered else 0,
                notes,
            ]
            if created_at:
                params.append(created_at)

            cursor = conn.execute(
                sql.format(date_col=date_col, date_val=date_val), params
            )
            transaction_id = cursor.lastrowid

            conn.execute(
                "UPDATE platforms SET balance = balance + ?, monthly_used = monthly_used + ? WHERE id = ?",
                (amount_received, amount_received, wallet_id),
            )

            if is_delivered:
                conn.execute(
                    "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                    (amount_delivered,),
                )
            elif customer_id:
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                    (amount_delivered, customer_id),
                )

            conn.commit()
            return transaction_id
        except Exception:
            conn.rollback()
            raise


def mark_as_delivered(transaction_id: int) -> None:
    with get_connection() as conn:
        try:
            row = conn.execute(
                "SELECT customer_id, amount_spent, is_delivered, operation_type FROM transactions WHERE id = ?",
                (transaction_id,),
            ).fetchone()
            if not row:
                raise ValueError("العملية غير موجودة")
            if row["operation_type"] != "inbound":
                raise ValueError("هذه الوظيفة للعمليات الواردة فقط")
            if row["is_delivered"]:
                raise ValueError("تم التسليم مسبقاً")
            conn.execute(
                "UPDATE transactions SET is_delivered = 1 WHERE id = ?",
                (transaction_id,),
            )

            # Deduct from cash vault
            conn.execute(
                "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                (row["amount_spent"],),
            )

            if row["customer_id"]:
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                    (row["amount_spent"], row["customer_id"]),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def mark_as_paid(transaction_id: int) -> None:
    with get_connection() as conn:
        try:
            row = conn.execute(
                "SELECT customer_id, amount_required, payment_status FROM transactions WHERE id = ?",
                (transaction_id,),
            ).fetchone()
            if not row:
                raise ValueError("العملية غير موجودة")
            if row["payment_status"] != "pending":
                raise ValueError("العملية ليست في حالة مؤجل")
            conn.execute(
                "UPDATE transactions SET payment_status = 'paid' WHERE id = ?",
                (transaction_id,),
            )

            # Add to cash vault
            conn.execute(
                "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                (row["amount_required"],),
            )

            if row["customer_id"]:
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                    (row["amount_required"], row["customer_id"]),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def update_transaction_status(transaction_id: int, new_val) -> None:
    """
    تغيير حالة عملية (صادرة: pending/paid | واردة: 0/1 للـ is_delivered)
    مع تصحيح التأثيرات المالية
    """
    with get_connection() as conn:
        try:
            row = conn.execute(
                """
                SELECT customer_id, amount_spent, amount_required, payment_status, is_delivered, operation_type 
                FROM transactions WHERE id = ?
            """,
                (transaction_id,),
            ).fetchone()

            if not row:
                raise ValueError("العملية غير موجودة")

            op_type = row["operation_type"]
            cid = row["customer_id"]

            if op_type == "outbound":
                if new_val not in ("pending", "paid"):
                    raise ValueError("الحالة يجب أن تكون pending أو paid")

                old_status = row["payment_status"]
                if old_status == new_val:
                    return

                amt = row["amount_required"]

                # تحديث الحالة
                conn.execute(
                    "UPDATE transactions SET payment_status = ? WHERE id = ?",
                    (new_val, transaction_id),
                )

                if old_status == "pending" and new_val == "paid":
                    # مديونية -> كاش
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                        (amt,),
                    )
                    if cid:
                        conn.execute(
                            "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                            (amt, cid),
                        )
                elif old_status == "paid" and new_val == "pending":
                    # كاش -> مديونية
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                        (amt,),
                    )
                    if cid:
                        conn.execute(
                            "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                            (amt, cid),
                        )

            elif op_type == "inbound":
                new_is_del = int(new_val)
                old_is_del = int(row["is_delivered"])

                if old_is_del == new_is_del:
                    return

                amt = row["amount_spent"]  # المبلغ الذي يُسلم للعميل

                # تحديث الحالة
                conn.execute(
                    "UPDATE transactions SET is_delivered = ? WHERE id = ?",
                    (new_is_del, transaction_id),
                )

                if old_is_del == 0 and new_is_del == 1:
                    # لم يُسلم -> تم التسليم (خصم من الكاش)
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                        (amt,),
                    )
                    if cid:
                        conn.execute(
                            "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                            (amt, cid),
                        )
                elif old_is_del == 1 and new_is_del == 0:
                    # تم التسليم -> تراجع للم تُسلم (إضافة للكاش)
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                        (amt,),
                    )
                    if cid:
                        conn.execute(
                            "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                            (amt, cid),
                        )

            conn.commit()
        except Exception:
            conn.rollback()
            raise


def delete_transaction(transaction_id: int) -> None:
    """
    حذف عملية مع عكس كل التأثيرات المالية
    """
    with get_connection() as conn:
        try:
            row = conn.execute(
                """
                SELECT t.*, p.type as p_type FROM transactions t
                JOIN platforms p ON p.id = t.platform_id
                WHERE t.id = ?
            """,
                (transaction_id,),
            ).fetchone()
            if not row:
                raise ValueError("العملية غير موجودة")

            op = row["operation_type"]
            status = row["payment_status"]
            cid = row["customer_id"]
            pid = row["platform_id"]
            spent = row["amount_spent"]
            req = row["amount_required"]

            if op == "outbound":
                # استرجاع رصيد المنصة
                conn.execute(
                    "UPDATE platforms SET balance = balance + ? WHERE id = ?",
                    (spent, pid),
                )
                # استرجاع monthly_used للمحافظ
                if row["p_type"] in ("wallet", "instapay"):
                    conn.execute(
                        "UPDATE platforms SET monthly_used = MAX(0, monthly_used - ?) WHERE id = ?",
                        (spent, pid),
                    )
                # عكس تأثير الدفع
                if status in ("cash", "paid"):
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                        (req,),
                    )
                elif status == "pending" and cid:
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                        (req, cid),
                    )

            elif op == "inbound":
                # استرجاع رصيد المحفظة (الذي تم استلامه)
                conn.execute(
                    "UPDATE platforms SET balance = balance - ? WHERE id = ?",
                    (req, pid),
                )
                conn.execute(
                    "UPDATE platforms SET monthly_used = MAX(0, monthly_used - ?) WHERE id = ?",
                    (req, pid),
                )

                if row["is_delivered"]:
                    # استرداد الكاش للخزنة
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                        (spent,),
                    )
                elif cid:
                    # عكس تأثير الرصيد للعميل
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                        (spent, cid),
                    )

            elif op == "commission":
                # استرجاع رصيد الماكينة وخصم الكاش
                conn.execute(
                    "UPDATE platforms SET balance = balance + ? WHERE id = ?",
                    (spent, pid),
                )
                conn.execute(
                    "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                    (spent,),
                )

            conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def get_transactions(
    customer_id: int = None,
    platform_id: int = None,
    payment_status: str = None,
    date_from: str = None,
    date_to: str = None,
    is_delivered: int = None,
    limit: int = 500,
) -> list[dict]:
    with get_connection() as conn:
        conditions, params = [], []
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
        if is_delivered is not None:
            # The above code snippet is adding a condition to a list called `conditions` and a
            # corresponding parameter to a list called `params`. The condition being added is
            # `"t.is_delivered = ?"`, where `?` is a placeholder for a parameter value that will be
            # provided later. This is a common technique used in SQL queries to dynamically build
            # query conditions based on certain criteria.
            conditions.append("t.is_delivered = ?")
            params.append(is_delivered)
            if is_delivered == 0:  # Usually we want not delivered inbounds
                conditions.append("t.operation_type = 'inbound'")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.execute(
            f"""
            SELECT t.id, t.created_at, t.operation_type, t.service_name,
                   t.amount_spent, t.amount_required, t.profit,
                   t.reference_no, t.is_card, t.payment_status, t.is_delivered, t.notes,
                   p.name AS platform_name, p.type AS platform_type,
                   c.name AS customer_name
            FROM transactions t
            JOIN platforms p ON p.id = t.platform_id
            LEFT JOIN customers c ON c.id = t.customer_id
            {where}
            ORDER BY t.created_at DESC
            LIMIT ?
        """,
            (*params, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_customer_statement(customer_id: int) -> dict:
    with get_connection() as conn:
        customer = conn.execute(
            """
            SELECT c.*, g.name AS group_name
            FROM customers c
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE c.id = ?
        """,
            (customer_id,),
        ).fetchone()
        if not customer:
            return {}

        transactions = conn.execute(
            """
            SELECT t.*, p.name AS platform_name
            FROM transactions t
            JOIN platforms p ON p.id = t.platform_id
            WHERE t.customer_id = ?
            ORDER BY t.created_at DESC
        """,
            (customer_id,),
        ).fetchall()

        totals = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN payment_status='pending' AND operation_type='outbound' THEN amount_required ELSE 0 END), 0) AS total_pending,
                COALESCE(SUM(CASE WHEN payment_status='paid'    AND operation_type='outbound' THEN amount_required ELSE 0 END), 0) AS total_paid,
                COALESCE(SUM(CASE WHEN operation_type='inbound' AND is_delivered=0 THEN amount_spent ELSE 0 END), 0) AS total_due,
                COALESCE(SUM(CASE WHEN payment_status IN ('pending', 'paid') THEN profit ELSE 0 END), 0) AS total_profit,
                COUNT(*) AS total_count
            FROM transactions WHERE customer_id = ?
        """,
            (customer_id,),
        ).fetchone()

        return {
            "customer": dict(customer),
            "transactions": [dict(t) for t in transactions],
            "totals": dict(totals),
        }


def cleanup_paid_transactions(customer_id: int = None) -> int:
    with get_connection() as conn:
        finished_sql = """
            (operation_type='outbound' AND payment_status='paid') 
            OR 
            (operation_type='inbound' AND is_delivered=1)
        """
        if customer_id:
            cursor = conn.execute(
                f"DELETE FROM transactions WHERE customer_id=? AND ({finished_sql})",
                (customer_id,),
            )
        else:
            cursor = conn.execute(f"DELETE FROM transactions WHERE {finished_sql}")
        conn.commit()
        return cursor.rowcount


def cleanup_transactions_before(cutoff_date: str) -> int:
    """حذف العمليات المسددة والمسلمة حتى تاريخ معين"""
    with get_connection() as conn:
        finished_sql = """
            ((operation_type='outbound' AND payment_status='paid') 
            OR 
            (operation_type='inbound' AND is_delivered=1))
            AND DATE(created_at) <= ?
        """
        cursor = conn.execute(
            f"DELETE FROM transactions WHERE {finished_sql}", (cutoff_date,)
        )
        conn.commit()
        return cursor.rowcount


# ══════════════════════════════════════════
#  Daily Financial Closing Model
# ══════════════════════════════════════════


def get_platform_day_stats(platform_id: int, date_str: str) -> dict:
    """
    إحصائيات يوم معين لمنصة (تتبع نموذج Chain Balance):
    - Net Inward: (Deposits + Inbounds)
    - Net Outward: (Outbounds)
    - Daily Commission: (manual_commission)
    """
    with get_connection() as conn:
        # Transactions on this date
        row = conn.execute(
            """
            SELECT 
                COUNT(*) AS txn_count,
                COALESCE(SUM(CASE WHEN operation_type='outbound' THEN amount_spent ELSE 0 END), 0) AS total_outbound,
                COALESCE(SUM(CASE WHEN operation_type='inbound' THEN amount_required ELSE 0 END), 0) AS total_inbound,
                COALESCE(SUM(CASE WHEN operation_type='manual_commission' THEN amount_spent ELSE 0 END), 0) AS total_commission
            FROM transactions
            WHERE platform_id = ? AND DATE(created_at) = ?
        """,
            (platform_id, date_str),
        ).fetchone()

        # Deposits on this date
        dep_row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_deposits
            FROM machine_deposits
            WHERE platform_id = ? AND DATE(created_at) = ?
        """,
            (platform_id, date_str),
        ).fetchone()

        # Legacy commissions (fallback)
        legacy_row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_legacy
            FROM daily_commissions
            WHERE platform_id = ? AND DATE(created_at) = ?
        """,
            (platform_id, date_str),
        ).fetchone()

        return {
            "txn_count": row["txn_count"] if row else 0,
            "total_outbound": row["total_outbound"] if row else 0,
            "total_inbound": row["total_inbound"] if row else 0,
            "total_deposits": dep_row["total_deposits"] if dep_row else 0,
            "total_commission": (row["total_commission"] if row else 0) + (legacy_row["total_legacy"] if legacy_row else 0),
        }


def get_opening_balance(platform_id: int, date_str: str) -> float:
    """
    Dynamic Opening Balance (The Snapshot):
    Cumulative sum of ALL transactions from the beginning of time up until Date(X-1).
    """
    with get_connection() as conn:
        # 1. Start with initial_balance
        plat = conn.execute(
            "SELECT initial_balance FROM platforms WHERE id = ?", (platform_id,)
        ).fetchone()
        initial = plat["initial_balance"] if plat else 0.0

        # 2. SUM(Deposits) before date_str
        deps = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM machine_deposits
            WHERE platform_id = ? AND DATE(created_at) < ?
        """, (platform_id, date_str)).fetchone()["total"]

        # 3. SUM(Inbound + Commission - Outbound) before date_str
        txns = conn.execute("""
            SELECT 
                COALESCE(SUM(CASE 
                    WHEN operation_type = 'inbound' THEN amount_required
                    WHEN operation_type = 'manual_commission' THEN amount_spent
                    ELSE 0 END), 0) AS total_in,
                COALESCE(SUM(CASE 
                    WHEN operation_type = 'outbound' THEN amount_spent
                    ELSE 0 END), 0) AS total_out
            FROM transactions
            WHERE platform_id = ? AND DATE(created_at) < ?
        """, (platform_id, date_str)).fetchone()

        # 4. Legacy commissions
        legacy = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM daily_commissions
            WHERE platform_id = ? AND DATE(created_at) < ?
        """, (platform_id, date_str)).fetchone()["total"]

        return initial + deps + txns["total_in"] + legacy - txns["total_out"]


def get_closing_balance(platform_id: int, date_str: str) -> float:
    """
    الرصيد النهائي (تتبع نموذج Chain Balance):
    E = (A + B) + D
    حيث:
    A = Opening Balance
    B = Net Change (Inbound + Deposits - Outbound)
    D = Daily Commission
    """
    opening = get_opening_balance(platform_id, date_str)
    stats = get_platform_day_stats(platform_id, date_str)
    
    # Net Change B (Daily Inward - Daily Outward)
    inward = stats["total_deposits"] + stats["total_inbound"]
    outward = stats["total_outbound"]
    net_change = inward - outward
    
    # Balance After Operations C
    after_ops = opening + net_change
    
    # Final Closing Balance E
    closing = after_ops + stats["total_commission"]
    return closing


def add_manual_commission(
    platform_id: int, amount: float, date_str: str, notes: str = ""
) -> int:
    """تسجيل عمولة يدوية لماكينة — تُخصم من رصيد الماكينة وتُضاف للخزينة"""
    if amount <= 0:
        raise ValueError("مبلغ العمولة يجب أن يكون أكبر من الصفر")

    with get_connection() as conn:
        try:
            platform = conn.execute(
                "SELECT id, type, balance FROM platforms WHERE id = ? AND is_active = 1",
                (platform_id,),
            ).fetchone()

            if not platform:
                raise ValueError("المنصة غير موجودة")
            if platform["type"] != "machine":
                raise ValueError("العمولة اليدوية متاحة للماكينات فقط")

            # Enforce single daily commission
            existing = conn.execute(
                """
                SELECT id FROM transactions 
                WHERE platform_id = ? AND DATE(created_at) = ? AND operation_type = 'manual_commission'
                LIMIT 1
            """,
                (platform_id, date_str),
            ).fetchone()

            if existing:
                raise ValueError("تم إضافة عمولة لهذه الماكينة بالفعل في هذا التاريخ.")

            from datetime import datetime

            now_time = datetime.now().strftime("%H:%M:%S")
            created_at = f"{date_str} {now_time}"

            cursor = conn.execute(
                """
                INSERT INTO transactions
                    (operation_type, service_name, platform_id, customer_id,
                     amount_spent, amount_required, payment_status, notes, created_at)
                VALUES ('manual_commission', 'عمولة يدوية', ?, NULL, ?, 0, 'paid', ?, ?)
            """,
                (platform_id, amount, notes, created_at),
            )

            # Add to machine balance (Commission is now treated as an addition)
            conn.execute(
                "UPDATE platforms SET balance = balance + ? WHERE id = ?",
                (amount, platform_id),
            )
            # Optional: If commission is "earned profit" that stays in the machine, we don't necessarily add to cash vault here
            # unless the user wants to track it as cash on hand. But typically, adding to machine is enough.
            # conn.execute("UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1", (amount,))

            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise


def get_platform_transactions_for_date(platform_id: int, date_str: str) -> list[dict]:
    """جلب كل عمليات منصة في يوم معين"""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t.id, t.created_at, t.operation_type, t.service_name,
                   t.amount_spent, t.amount_required, t.profit,
                   t.reference_no, t.payment_status, t.is_delivered, t.notes,
                   c.name AS customer_name
            FROM transactions t
            LEFT JOIN customers c ON c.id = t.customer_id
            WHERE t.platform_id = ? AND DATE(t.created_at) = ?
            ORDER BY t.created_at DESC
        """,
            (platform_id, date_str),
        ).fetchall()
        return [dict(r) for r in rows]


def get_dashboard_stats() -> dict:
    with get_connection() as conn:
        budget = conn.execute(
            "SELECT main_budget, cash_vault FROM budget WHERE id=1"
        ).fetchone()
        machines = conn.execute(
            "SELECT COALESCE(SUM(balance),0) AS total FROM platforms WHERE type='machine' AND is_active=1"
        ).fetchone()
        wallets = conn.execute(
            "SELECT COALESCE(SUM(balance),0) AS total FROM platforms WHERE type IN ('wallet','instapay') AND is_active=1"
        ).fetchone()
        debts = conn.execute(
            "SELECT COALESCE(SUM(total_debt),0) AS total FROM customers WHERE is_active=1"
        ).fetchone()
        today_p = conn.execute("""
            SELECT COALESCE(SUM(profit),0) AS total FROM transactions 
            WHERE DATE(created_at)=DATE('now','localtime') 
            AND payment_status IN ('pending', 'paid')
        """).fetchone()
        month_p = conn.execute("""
            SELECT COALESCE(SUM(profit),0) AS total FROM transactions 
            WHERE strftime('%Y-%m',created_at)=strftime('%Y-%m','now','localtime') 
            AND payment_status IN ('pending', 'paid')
        """).fetchone()
        pending = conn.execute(
            "SELECT COALESCE(SUM(amount_required),0) AS total FROM transactions WHERE payment_status='pending' AND operation_type='outbound'"
        ).fetchone()

        total_assets = (
            (machines["total"] or 0)
            + (wallets["total"] or 0)
            + (budget["cash_vault"] or 0)
        )
        return {
            "main_budget": budget["main_budget"] or 0,
            "cash_vault": budget["cash_vault"] or 0,
            "total_machines": machines["total"] or 0,
            "total_wallets": wallets["total"] or 0,
            "total_debts": debts["total"] or 0,
            "today_profit": today_p["total"] or 0,
            "month_profit": month_p["total"] or 0,
            "total_assets": total_assets,
            "total_balances": total_assets,
            "net_position": total_assets
            + (debts["total"] or 0)
            - (budget["main_budget"] or 0),
            "total_pending": pending["total"] or 0,
        }


def count_finished_transactions(customer_id: int = None) -> int:
    """عدد العمليات المسددة أو المسلمة القابلة للحذف"""
    with get_connection() as conn:
        finished_sql = """
            (operation_type='outbound' AND payment_status='paid') 
            OR 
            (operation_type='inbound' AND is_delivered=1)
        """
        if customer_id:
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM transactions WHERE customer_id=? AND ({finished_sql})",
                (customer_id,),
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM transactions WHERE {finished_sql}"
            ).fetchone()
        return row["n"] if row else 0


def search_by_reference(reference_no: str) -> list[dict]:
    """البحث عن عمليات برقم المرجع"""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t.id, t.created_at, t.operation_type, t.service_name,
                   t.amount_spent, t.amount_required, t.profit,
                   t.reference_no, t.is_card, t.payment_status, t.is_delivered, t.notes,
                   p.name AS platform_name, p.type AS platform_type,
                   c.name AS customer_name
            FROM transactions t
            JOIN platforms p ON p.id = t.platform_id
            LEFT JOIN customers c ON c.id = t.customer_id
            WHERE t.reference_no LIKE ?
            ORDER BY t.created_at DESC
            LIMIT 200
        """,
            (f"%{reference_no}%",),
        ).fetchall()
        return [dict(r) for r in rows]


def get_unique_service_names() -> list[str]:
    """استرجاع قائمة بأسماء الخدمات الفريدة لاستخدامها في الإكمال التلقائي"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT service_name FROM transactions WHERE service_name IS NOT NULL AND service_name != ''"
        ).fetchall()
        return [r["service_name"] for r in rows]
