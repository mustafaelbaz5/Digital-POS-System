"""
Data Access Layer - Customers & Groups
طبقة الوصول للبيانات - العملاء والمجموعات
"""

from database.connection import get_connection


# ══════════════════════════════════════════
#  المجموعات  (Groups)
# ══════════════════════════════════════════

def get_all_groups() -> list[dict]:
    """جلب كل المجموعات مع اسم القائد"""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT g.id, g.name, g.notes, g.created_at,
                   c.name AS leader_name, g.leader_id
            FROM groups g
            LEFT JOIN customers c ON c.id = g.leader_id
            ORDER BY g.name
        """).fetchall()
        return [dict(r) for r in rows]


def add_group(name: str, leader_id: int = None, notes: str = "") -> int:
    """إضافة مجموعة جديدة - يرجع الـ ID"""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO groups (name, leader_id, notes) VALUES (?, ?, ?)",
            (name, leader_id, notes)
        )
        conn.commit()
        return cursor.lastrowid


def update_group(group_id: int, name: str, leader_id: int = None, notes: str = "") -> None:
    """تعديل بيانات مجموعة"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE groups SET name = ?, leader_id = ?, notes = ? WHERE id = ?",
            (name, leader_id, notes, group_id)
        )
        conn.commit()


def delete_group(group_id: int) -> None:
    """حذف مجموعة (يُبقي العملاء بدون مجموعة)"""
    with get_connection() as conn:
        conn.execute("UPDATE customers SET group_id = NULL WHERE group_id = ?", (group_id,))
        conn.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        conn.commit()


# ══════════════════════════════════════════
#  العملاء  (Customers)
# ══════════════════════════════════════════

def get_all_customers(include_inactive: bool = False) -> list[dict]:
    """جلب كل العملاء مع اسم المجموعة وصافي الرصيد حسب كشف الحساب"""
    with get_connection() as conn:
        where = "" if include_inactive else "WHERE c.is_active = 1"
        rows = conn.execute(f"""
            SELECT c.id, c.name, c.phone, c.total_debt,
                   COALESCE((SELECT SUM(amount_required) FROM transactions
                             WHERE customer_id = c.id AND operation_type = 'outbound'), 0)
                   - COALESCE((SELECT SUM(amount) FROM payments_history
                               WHERE customer_id = c.id), 0) AS net_balance,
                   c.notes, c.is_active, c.created_at,
                   g.name AS group_name, c.group_id
            FROM customers c
            LEFT JOIN groups g ON g.id = c.group_id
            {where}
            ORDER BY c.name
        """).fetchall()
        return [dict(r) for r in rows]


def get_customers_by_group(group_id: int) -> list[dict]:
    """جلب عملاء مجموعة معينة"""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT c.id, c.name, c.phone, c.total_debt,
                   COALESCE((SELECT SUM(amount_required) FROM transactions
                             WHERE customer_id = c.id AND operation_type = 'outbound'), 0)
                   - COALESCE((SELECT SUM(amount) FROM payments_history
                               WHERE customer_id = c.id), 0) AS net_balance,
                   c.notes, c.created_at
            FROM customers c
            WHERE c.group_id = ? AND c.is_active = 1
            ORDER BY c.name
        """, (group_id,)).fetchall()
        return [dict(r) for r in rows]


# ══════════════════════════════════════════
#  كودات الشحن  (Shipping Codes)
# ══════════════════════════════════════════

def get_shipping_codes(customer_id: int) -> list[dict]:
    """جلب كودات الشحن الخاصة بعميل معين"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, code, created_at FROM shipping_codes WHERE customer_id = ? ORDER BY code",
            (customer_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_shipping_codes() -> list[dict]:
    """جلب كل الكودات مع اسم العميل والمجموعة (للـ completer)"""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT sc.id, sc.code, c.id AS customer_id,
                   c.name AS customer_name, g.name AS group_name
            FROM shipping_codes sc
            JOIN customers c ON c.id = sc.customer_id
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE c.is_active = 1
            ORDER BY sc.code
        """).fetchall()
        return [dict(r) for r in rows]


def get_customer_by_shipping_code(code: str) -> dict | None:
    """البحث عن عميل بكود الشحن"""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT c.id, c.name, c.phone, c.total_debt,
                   g.name AS group_name
            FROM customers c
            JOIN shipping_codes sc ON sc.customer_id = c.id
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE sc.code = ? COLLATE NOCASE AND c.is_active = 1
        """, (code.strip(),)).fetchone()
        return dict(row) if row else None


def add_shipping_code(customer_id: int, code: str) -> int:
    """إضافة كود شحن جديد للعميل - يرجع الـ ID"""
    code = code.strip()
    if not code:
        raise ValueError("الكود لا يمكن أن يكون فارغاً")
    with get_connection() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO shipping_codes (customer_id, code) VALUES (?, ?)",
                (customer_id, code),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            raise ValueError(f"الكود '{code}' مستخدم بالفعل لعميل آخر")


def update_shipping_code(code_id: int, new_code: str) -> None:
    """تعديل كود شحن موجود"""
    new_code = new_code.strip()
    if not new_code:
        raise ValueError("الكود لا يمكن أن يكون فارغاً")
    with get_connection() as conn:
        try:
            conn.execute(
                "UPDATE shipping_codes SET code = ? WHERE id = ?",
                (new_code, code_id),
            )
            conn.commit()
        except Exception:
            raise ValueError(f"الكود '{new_code}' مستخدم بالفعل لعميل آخر")


def delete_shipping_code(code_id: int) -> None:
    """حذف كود شحن"""
    with get_connection() as conn:
        conn.execute("DELETE FROM shipping_codes WHERE id = ?", (code_id,))
        conn.commit()


def get_group_summary(group_id: int) -> dict:
    """جلب ملخص المجموعة مع أرصدة الأعضاء وتاريخ آخر نشاط"""
    with get_connection() as conn:
        group = conn.execute("""
            SELECT g.id, g.name, g.notes,
                   c.name AS leader_name
            FROM groups g
            LEFT JOIN customers c ON c.id = g.leader_id
            WHERE g.id = ?
        """, (group_id,)).fetchone()

        members = conn.execute("""
            SELECT c.id, c.name, c.phone,
                   COALESCE((SELECT SUM(amount_required) FROM transactions
                             WHERE customer_id = c.id AND operation_type = 'outbound'), 0)
                   - COALESCE((SELECT SUM(amount) FROM payments_history
                               WHERE customer_id = c.id), 0) AS net_balance,
                   strftime('%Y-%m-%d', MAX(t.created_at)) AS last_activity
            FROM customers c
            LEFT JOIN transactions t ON t.customer_id = c.id
            WHERE c.group_id = ? AND c.is_active = 1
            GROUP BY c.id
            ORDER BY ABS(net_balance) DESC
        """, (group_id,)).fetchall()

    if not group:
        return {}

    members_list = [dict(m) for m in members]
    total = sum(float(m["net_balance"] or 0) for m in members_list)

    return {
        "group": dict(group),
        "members": members_list,
        "total_balance": total,
    }


def get_customer_by_id(customer_id: int) -> dict | None:
    """جلب عميل بالـ ID"""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT c.*, g.name AS group_name
            FROM customers c
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE c.id = ?
        """, (customer_id,)).fetchone()
        return dict(row) if row else None


def add_customer(name: str, phone: str = "", group_id: int = None, notes: str = "") -> int:
    """إضافة عميل جديد - يرجع الـ ID"""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO customers (name, phone, group_id, notes) VALUES (?, ?, ?, ?)",
            (name, phone, group_id, notes)
        )
        conn.commit()
        return cursor.lastrowid


def update_customer(customer_id: int, name: str, phone: str = "",
                    group_id: int = None, notes: str = "") -> None:
    """تعديل بيانات عميل"""
    with get_connection() as conn:
        conn.execute(
            """UPDATE customers
               SET name = ?, phone = ?, group_id = ?, notes = ?
               WHERE id = ?""",
            (name, phone, group_id, notes, customer_id)
        )
        conn.commit()


def assign_customer_to_group(customer_id: int, group_id: int | None) -> None:
    """تغيير المجموعة لعميل معين"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE customers SET group_id = ? WHERE id = ?",
            (group_id, customer_id)
        )
        conn.commit()


def adjust_customer_debt(customer_id: int, delta: float, conn=None) -> None:
    """
    زيادة أو خصم من مديونية عميل
    يقبل connection خارجي لدعم الـ atomic transactions
    """
    close_after = False
    if conn is None:
        conn = get_connection().__enter__()
        close_after = True

    conn.execute(
        "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
        (delta, customer_id)
    )

    if close_after:
        conn.commit()


def delete_customer(customer_id: int) -> None:
    """حذف عميل (Soft Delete)"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE customers SET is_active = 0 WHERE id = ?", (customer_id,)
        )
        conn.commit()


def search_customers(query: str) -> list[dict]:
    """البحث عن عميل بالاسم أو رقم التليفون"""
    with get_connection() as conn:
        pattern = f"%{query}%"
        rows = conn.execute("""
            SELECT c.id, c.name, c.phone, c.total_debt,
                   COALESCE((SELECT SUM(amount_required) FROM transactions
                             WHERE customer_id = c.id AND operation_type = 'outbound'), 0)
                   - COALESCE((SELECT SUM(amount) FROM payments_history
                               WHERE customer_id = c.id), 0) AS net_balance,
                   g.name AS group_name
            FROM customers c
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE c.is_active = 1
              AND (c.name LIKE ? OR c.phone LIKE ?)
            ORDER BY c.name
        """, (pattern, pattern)).fetchall()
        return [dict(r) for r in rows]


def get_export_data() -> dict:
    """جلب بيانات التصدير: العملاء والمجموعات وملخص المديونيات"""
    with get_connection() as conn:
        # 1. Fetch ALL active customers who have any balance or any transactions
        customers = conn.execute("""
            SELECT c.id, c.name, c.phone, c.total_debt, c.group_id,
                   g.name AS group_name
            FROM customers c
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE c.is_active = 1
              AND (
                ABS(c.total_debt) > 0.01
                OR EXISTS (SELECT 1 FROM transactions t WHERE t.customer_id = c.id)
              )
            ORDER BY c.name
        """).fetchall()

        # 2. Summary rows (same as customers but sorted by debt)
        summary_rows = sorted(customers, key=lambda x: x["total_debt"], reverse=True)

        # 3. Fetch detailed customer ledger rows. Status/effective_amount are
        # used by the Sheets exporter so paid/delivered rows can be displayed
        # without inflating outstanding debt totals.
        customer_ids = [r["id"] for r in customers]
        txn_rows = []
        if customer_ids:
            placeholders = ",".join("?" * len(customer_ids))
            txn_rows = conn.execute(f"""
                SELECT t.customer_id,
                       strftime('%Y-%m-%d', t.created_at)       AS date,
                       t.service_name                            AS service,
                       t.amount_required                         AS amount,
                       t.amount_spent                            AS amount_spent,
                       t.operation_type,
                       t.payment_status,
                       t.is_delivered
                FROM transactions t
                WHERE t.customer_id IN ({placeholders})
                  AND t.operation_type IN ('outbound', 'inbound')
                ORDER BY t.created_at ASC
            """, customer_ids).fetchall()

    txn_by_customer: dict = {}
    for t in txn_rows:
        amount = float(t["amount"] or 0)
        effective_amount = 0.0
        service = t["service"]
        status = "قيد الانتظار"

        if t["operation_type"] == "inbound":
            service = f"📥 دفع: {service}"
            delivered = int(t["is_delivered"] or 0) == 1
            status = "تم التسليم" if delivered else "قيد الانتظار"
            amount = -(float(t["amount_spent"] or 0))
            effective_amount = 0.0 if delivered else amount
        elif t["payment_status"] == "paid":
            status = "مسدد"
            effective_amount = 0.0
        else:
            effective_amount = amount

        txn_by_customer.setdefault(t["customer_id"], []).append({
            "date":             t["date"],
            "service":          service,
            "amount":           amount,
            "effective_amount": effective_amount,
            "status":           status,
        })

    # Prepare data for sheets
    all_individual_statements = []
    groups_dict = {}

    for r in customers:
        cust = {
            "id":           r["id"],
            "name":         r["name"],
            "phone":        r["phone"] or "",
            "total_debt":   float(r["total_debt"] or 0),
            "transactions": txn_by_customer.get(r["id"], []),
            "group_name":   r["group_name"]
        }
        
        # Add to main individual list
        all_individual_statements.append(cust)

        # Also add to group data if applicable
        if r["group_id"] is not None:
            gid = r["group_id"]
            if gid not in groups_dict:
                groups_dict[gid] = {
                    "id":         gid,
                    "name":       r["group_name"] or "",
                    "total_debt": 0.0,
                    "members":    [],
                }
            groups_dict[gid]["total_debt"] += cust["total_debt"]
            groups_dict[gid]["members"].append(cust)

    return {
        "individual_statements": all_individual_statements,
        "groups":               list(groups_dict.values()),
        "all_summary": [
            {
                "name":       r["name"],
                "phone":      r["phone"] or "",
                "group_name": r["group_name"] or "",
                "total_debt": float(r["total_debt"] or 0),
            }
            for r in summary_rows
        ],
    }
