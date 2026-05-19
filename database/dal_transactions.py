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

            # ── Receiving capacity check ──────────────────────────────────
            from datetime import date as _date
            _month_start = _date.today().replace(day=1).isoformat()

            _cap_row = conn.execute(
                "SELECT monthly_limit FROM platforms WHERE id = ?", (wallet_id,)
            ).fetchone()
            _total_limit = (_cap_row["monthly_limit"] or 0) if _cap_row else 0

            _deps = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM machine_deposits
                WHERE platform_id = ?
                  AND datetime(created_at) < datetime(?, 'start of day')
            """, (wallet_id, _month_start)).fetchone()["total"]

            _txns = conn.execute("""
                SELECT
                    COALESCE(SUM(CASE
                        WHEN operation_type = 'inbound' THEN amount_required
                        WHEN operation_type = 'manual_commission' THEN amount_spent
                        ELSE 0 END), 0) AS total_in,
                    COALESCE(SUM(CASE
                        WHEN operation_type = 'outbound' THEN amount_spent
                        ELSE 0 END), 0) AS total_out
                FROM transactions
                WHERE platform_id = ?
                  AND datetime(created_at) < datetime(?, 'start of day')
            """, (wallet_id, _month_start)).fetchone()

            _legacy = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM daily_commissions
                WHERE platform_id = ?
                  AND datetime(created_at) < datetime(?, 'start of day')
            """, (wallet_id, _month_start)).fetchone()["total"]

            _opening = _deps + _txns["total_in"] + _legacy - _txns["total_out"]

            _monthly_inward = conn.execute("""
                SELECT COALESCE(SUM(amount_required), 0) AS total
                FROM transactions
                WHERE platform_id = ? AND operation_type = 'inbound'
                  AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')
            """, (wallet_id,)).fetchone()["total"]

            _remaining = _total_limit - (_opening + _monthly_inward)
            if amount_received > _remaining:
                raise ValueError(
                    f"تنبيه: هذه العملية ستتخطى الحد الشهري المسموح للاستقبال — "
                    f"السعة المتبقية: {_remaining:,.0f} ج"
                )
            # ─────────────────────────────────────────────────────────────

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
                "UPDATE platforms SET balance = balance + ? WHERE id = ?",
                (amount_received, wallet_id),
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
                SELECT customer_id, amount_spent, amount_required, amount_paid,
                       payment_status, is_delivered, operation_type
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

                required   = float(row["amount_required"])
                paid_so_far = float(row["amount_paid"] or 0)

                if old_status == "pending" and new_val == "paid":
                    # Settle the unpaid remainder only
                    unpaid = required - paid_so_far
                    conn.execute(
                        "UPDATE transactions SET payment_status = 'paid', amount_paid = amount_required WHERE id = ?",
                        (transaction_id,),
                    )
                    if unpaid > 0:
                        conn.execute(
                            "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                            (unpaid,),
                        )
                        if cid:
                            conn.execute(
                                "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                                (unpaid, cid),
                            )
                elif old_status == "paid" and new_val == "pending":
                    # Full reversal — reset amount_paid to zero
                    conn.execute(
                        "UPDATE transactions SET payment_status = 'pending', amount_paid = 0 WHERE id = ?",
                        (transaction_id,),
                    )
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault - ? WHERE id = 1",
                        (required,),
                    )
                    if cid:
                        conn.execute(
                            "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                            (required, cid),
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

            elif op == "manual_commission":
                conn.execute(
                    "UPDATE platforms SET balance = balance - ? WHERE id = ?",
                    (spent, pid),
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

        payments = conn.execute(
            """
            SELECT id, amount, created_at, notes
            FROM payments_history
            WHERE customer_id = ?
            ORDER BY created_at DESC
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

        isolated = conn.execute(
            """
            SELECT t.*, p.name AS platform_name
            FROM transactions t
            JOIN platforms p ON p.id = t.platform_id
            WHERE t.customer_id = ?
              AND t.operation_type = 'inbound'
              AND t.is_netted = 0
            ORDER BY t.created_at ASC
            """,
            (customer_id,),
        ).fetchall()

        return {
            "customer":              dict(customer),
            "transactions":          [dict(t) for t in transactions],
            "isolated_transactions": [dict(t) for t in isolated],
            "totals":                dict(totals),
            "payments":              [dict(p) for p in payments],
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


def get_daily_manual_commission(platform_id: int, date_str: str) -> float:
    """Return the existing manual commission for a platform/day, including legacy rows."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COALESCE((
                    SELECT SUM(amount_spent)
                    FROM transactions
                    WHERE platform_id = ?
                      AND DATE(created_at) = ?
                      AND operation_type = 'manual_commission'
                ), 0)
                +
                COALESCE((
                    SELECT SUM(amount)
                    FROM daily_commissions
                    WHERE platform_id = ?
                      AND DATE(created_at) = ?
                ), 0) AS amount
            """,
            (platform_id, date_str, platform_id, date_str),
        ).fetchone()
        return row["amount"] if row else 0.0


def get_opening_balance(platform_id: int, date_str: str) -> float:
    """
    Dynamic Opening Balance (The Snapshot):
    Cumulative sum from the beginning of history up to the previous day.
    """
    with get_connection() as conn:
        deps = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM machine_deposits
            WHERE platform_id = ?
              AND datetime(created_at) < datetime(?, 'start of day')
        """, (platform_id, date_str)).fetchone()["total"]

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
            WHERE platform_id = ?
              AND datetime(created_at) < datetime(?, 'start of day')
        """, (platform_id, date_str)).fetchone()

        legacy = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM daily_commissions
            WHERE platform_id = ?
              AND datetime(created_at) < datetime(?, 'start of day')
        """, (platform_id, date_str)).fetchone()["total"]

        return deps + txns["total_in"] + legacy - txns["total_out"]


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
                SELECT 1
                WHERE EXISTS (
                    SELECT 1 FROM transactions
                    WHERE platform_id = ?
                      AND DATE(created_at) = ?
                      AND operation_type = 'manual_commission'
                      AND amount_spent > 0
                )
                OR EXISTS (
                    SELECT 1 FROM daily_commissions
                    WHERE platform_id = ?
                      AND DATE(created_at) = ?
                      AND amount > 0
                )
                LIMIT 1
            """,
                (platform_id, date_str, platform_id, date_str),
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
            "SELECT COALESCE(SUM(balance),0) AS total FROM platforms WHERE type='wallet' AND is_active=1"
        ).fetchone()
        instapay = conn.execute(
            "SELECT COALESCE(SUM(balance),0) AS total FROM platforms WHERE type='instapay' AND is_active=1"
        ).fetchone()
        debts = conn.execute(
            """
            SELECT COALESCE(SUM(
                COALESCE((SELECT SUM(amount_required) FROM transactions
                          WHERE customer_id = c.id AND operation_type = 'outbound'), 0)
                - COALESCE((SELECT SUM(amount) FROM payments_history
                            WHERE customer_id = c.id), 0)
            ), 0) AS total
            FROM customers c
            WHERE c.is_active = 1
            """
        ).fetchone()
        # احسب أرباح اليوم: استثني manual_commission التي ليست عمليات بيع
        today_p = conn.execute("""
            SELECT COALESCE(SUM(profit),0) AS total FROM transactions 
            WHERE DATE(created_at)=DATE('now','localtime') 
            AND payment_status IN ('pending', 'paid')
            AND operation_type != 'manual_commission'
        """).fetchone()
        # احسب أرباح الشهر: استثني manual_commission التي ليست عمليات بيع
        month_p = conn.execute("""
            SELECT COALESCE(SUM(profit),0) AS total FROM transactions 
            WHERE strftime('%Y-%m',created_at)=strftime('%Y-%m','now','localtime') 
            AND payment_status IN ('pending', 'paid')
            AND operation_type != 'manual_commission'
        """).fetchone()
        pending = conn.execute(
            "SELECT COALESCE(SUM(amount_required),0) AS total FROM transactions WHERE payment_status='pending' AND operation_type='outbound'"
        ).fetchone()
        injected = conn.execute(
            "SELECT COALESCE(SUM(amount),0) AS total FROM capital_movements"
        ).fetchone()
        # احسب إجمالي الكاش المطلوب تسليمه للعملاء
        pending_cash = conn.execute(
            "SELECT COALESCE(SUM(amount_spent),0) AS total FROM transactions WHERE operation_type='inbound' AND is_delivered=0"
        ).fetchone()

        total_platform_balances = (
            (machines["total"] or 0)
            + (wallets["total"] or 0)
            + (instapay["total"] or 0)
        )
        total_assets = (
            total_platform_balances
            + (budget["cash_vault"] or 0)
        )
        injected_capital = injected["total"] or 0
        reconciliation = total_assets - injected_capital

        return {
            "main_budget": budget["main_budget"] or 0,
            "cash_vault": budget["cash_vault"] or 0,
            "total_machines": machines["total"] or 0,
            "total_wallets": wallets["total"] or 0,
            "total_instapay": instapay["total"] or 0,
            "total_debts": debts["total"] or 0,
            "today_profit": today_p["total"] or 0,
            "month_profit": month_p["total"] or 0,
            "total_assets": total_assets,
            "total_platform_balances": total_platform_balances,
            "total_balances": total_assets,
            "injected_capital": injected_capital,
            "asset_reconciliation": reconciliation,
            "net_position": reconciliation,
            "total_pending": pending["total"] or 0,
            "pending_cash_liability": pending_cash["total"] or 0,
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


def settle_customer_debt(customer_id: int, payment_amount: float) -> dict:
    """
    تسديد سريع — محرك FIFO غير مُدمِّر
    يسدد المستحقات المعلقة بترتيب التاريخ (الأقدم أولاً).
    - لا يُعدِّل amount_required أبداً.
    - تسديد كامل: amount_paid = amount_required → payment_status = 'paid'.
    - تسديد جزئي: amount_paid += المبلغ المتاح، الحالة تبقى pending.
    يرجع: {"settled_count", "partial_settled", "total_settled", "overpaid"}
    """
    if payment_amount <= 0:
        raise ValueError("المبلغ يجب أن يكون أكبر من الصفر")

    with get_connection() as conn:
        try:
            pending = conn.execute("""
                SELECT id, amount_required, amount_paid
                FROM transactions
                WHERE customer_id = ?
                  AND operation_type = 'outbound'
                  AND payment_status = 'pending'
                ORDER BY datetime(created_at) ASC, id ASC
            """, (customer_id,)).fetchall()

            if not pending:
                raise ValueError("لا توجد مبالغ مستحقة على هذا العميل")

            remaining       = payment_amount
            settled_count   = 0
            partial_settled = False
            total_settled   = 0.0

            for txn in pending:
                if remaining <= 0:
                    break

                txn_id     = txn["id"]
                still_owed = float(txn["amount_required"]) - float(txn["amount_paid"] or 0)
                if still_owed <= 0:
                    continue

                if remaining >= still_owed:
                    # ── Full coverage — mark paid, never touch amount_required ──
                    conn.execute(
                        "UPDATE transactions SET amount_paid = amount_required, payment_status = 'paid' WHERE id = ?",
                        (txn_id,)
                    )
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                        (still_owed,)
                    )
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                        (still_owed, customer_id)
                    )
                    remaining     -= still_owed
                    total_settled += still_owed
                    settled_count += 1
                else:
                    # ── Partial coverage — accumulate into amount_paid only ────
                    conn.execute(
                        "UPDATE transactions SET amount_paid = amount_paid + ? WHERE id = ?",
                        (remaining, txn_id)
                    )
                    conn.execute(
                        "UPDATE budget SET cash_vault = cash_vault + ? WHERE id = 1",
                        (remaining,)
                    )
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                        (remaining, customer_id)
                    )
                    total_settled  += remaining
                    remaining       = 0
                    partial_settled = True

            if total_settled > 0:
                conn.execute(
                    "INSERT INTO payments_history (customer_id, amount) VALUES (?, ?)",
                    (customer_id, total_settled),
                )

            conn.commit()
            return {
                "settled_count":  settled_count,
                "partial_settled": partial_settled,
                "total_settled":  total_settled,
                "overpaid":       max(0.0, remaining),
            }
        except Exception:
            conn.rollback()
            raise


def deliver_and_settle(transaction_id: int) -> dict:
    """
    مقاصة ذرية: تحديد عملية الاستلام كـ'تم التسليم' ثم خصم مبلغها (amount_spent)
    من مديونية شحن العميل بنظام FIFO — بدون تغيير في الخزينة (لا يُسلَّم كاش).
    """
    with get_connection() as conn:
        try:
            txn = conn.execute(
                "SELECT id, customer_id, amount_spent, is_delivered FROM transactions "
                "WHERE id = ? AND operation_type = 'inbound'",
                (transaction_id,),
            ).fetchone()
            if not txn:
                raise ValueError("لم يتم العثور على عملية الاستلام")
            if txn["is_delivered"]:
                raise ValueError("هذه العملية تم تسليمها بالفعل")

            customer_id   = txn["customer_id"]
            settle_amount = float(txn["amount_spent"] or 0)
            if settle_amount <= 0:
                raise ValueError("لا يوجد مبلغ للمقاصة")

            # Mark as delivered AND flag as netted so the ledger knows to skip the
            # inbound credit (payments_history entry is the single canonical record).
            conn.execute(
                "UPDATE transactions SET is_delivered = 1, is_netted = 1 WHERE id = ?",
                (transaction_id,),
            )

            # FIFO loop — reduce shipping debt oldest-first
            pending = conn.execute(
                """
                SELECT id, amount_required, amount_paid
                FROM transactions
                WHERE customer_id = ?
                  AND operation_type = 'outbound'
                  AND payment_status = 'pending'
                ORDER BY datetime(created_at) ASC, id ASC
                """,
                (customer_id,),
            ).fetchall()

            remaining       = settle_amount
            settled_count   = 0
            partial_settled = False
            total_settled   = 0.0

            for pt in pending:
                if remaining <= 0:
                    break
                still_owed = float(pt["amount_required"]) - float(pt["amount_paid"] or 0)
                if still_owed <= 0:
                    continue
                if remaining >= still_owed:
                    conn.execute(
                        "UPDATE transactions SET amount_paid = amount_required, "
                        "payment_status = 'paid' WHERE id = ?",
                        (pt["id"],),
                    )
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                        (still_owed, customer_id),
                    )
                    remaining     -= still_owed
                    total_settled += still_owed
                    settled_count += 1
                else:
                    conn.execute(
                        "UPDATE transactions SET amount_paid = amount_paid + ? WHERE id = ?",
                        (remaining, pt["id"]),
                    )
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                        (remaining, customer_id),
                    )
                    total_settled  += remaining
                    remaining       = 0
                    partial_settled = True

            # Always record the full inbound amount as a payments_history credit.
            # settle_amount = the full cash received; total_settled = portion applied to
            # pending outbounds. Any surplus (remaining > 0) means the customer is now
            # in credit — push total_debt negative so net_balance shows "له".
            conn.execute(
                "INSERT INTO payments_history (customer_id, amount, notes) VALUES (?, ?, ?)",
                (customer_id, settle_amount,
                 f"مقاصة تلقائية — دفعة واردة #{transaction_id}"),
            )

            surplus = max(0.0, remaining)
            if surplus > 0:
                # Debt already reduced to 0 by FIFO loop; push it negative by surplus.
                conn.execute(
                    "UPDATE customers SET total_debt = total_debt - ? WHERE id = ?",
                    (surplus, customer_id),
                )

            conn.commit()
            return {
                "settled_count":   settled_count,
                "partial_settled": partial_settled,
                "total_settled":   total_settled,
                "surplus":         surplus,
            }
        except Exception:
            conn.rollback()
            raise


def get_customer_net_pending_total(customer_id: int) -> float:
    """إجمالي الصافي المتبقي = SUM(amount_required − amount_paid) للعمليات الصادرة المعلقة.
    يستخدم كقيمة افتراضية لحقل الإدخال في التسديد السريع."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT COALESCE(
                SUM(amount_required - COALESCE(amount_paid, 0)), 0
            ) AS net_total
            FROM transactions
            WHERE customer_id = ?
              AND operation_type = 'outbound'
              AND payment_status = 'pending'
        """, (customer_id,)).fetchone()
        return float(row["net_total"] if row else 0)


def get_pending_cash_liability() -> float:
    """
    احسب إجمالي الكاش المطلوب تسليمه للعملاء
    (العمليات الواردة التي لم يتم تسليمها بعد)
    المسؤولية: المبلغ المطلوب تسليمه (amount_spent) للعمليات الواردة حيث is_delivered=0
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount_spent), 0) AS total
            FROM transactions
            WHERE operation_type = 'inbound' AND is_delivered = 0
        """
        ).fetchone()
        return row["total"] if row else 0


def calculate_wallet_capacity(wallet_id: int) -> dict:
    """
    حساب السعة المتبقية للاستقبال (نموذج الطاقة الاستيعابية الواردة):
      المستخدم  = إجمالي الواردات الشهرية + الإيداعات الشهرية
      المتبقي   = الحد الشهري - المستخدم
    """
    from datetime import date as _date
    current_month = _date.today().strftime("%Y-%m")

    with get_connection() as conn:
        cap_row = conn.execute(
            "SELECT monthly_limit FROM platforms WHERE id = ?", (wallet_id,)
        ).fetchone()
        if not cap_row:
            return {"total_limit": 0, "monthly_inward": 0, "monthly_deposits": 0, "used": 0, "remaining": 0}

        total_limit = cap_row["monthly_limit"] or 0

        # 1. إجمالي العمليات الواردة في الشهر الحالي
        monthly_inward = conn.execute("""
            SELECT COALESCE(SUM(amount_required), 0) AS total
            FROM transactions
            WHERE platform_id = ? AND operation_type = 'inbound'
              AND strftime('%Y-%m', created_at) = ?
        """, (wallet_id, current_month)).fetchone()["total"]

        # 2. إجمالي الإيداعات في الشهر الحالي (بما في ذلك الرصيد الابتدائي إذا كان في نفس الشهر)
        monthly_deposits = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM machine_deposits
            WHERE platform_id = ?
              AND strftime('%Y-%m', created_at) = ?
        """, (wallet_id, current_month)).fetchone()["total"]

    used = monthly_inward + monthly_deposits
    remaining = total_limit - used

    return {
        "total_limit": total_limit,
        "monthly_inward": monthly_inward,
        "monthly_deposits": monthly_deposits,
        "used": used,
        "remaining": remaining,
    }
