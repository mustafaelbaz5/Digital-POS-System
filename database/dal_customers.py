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
    """جلب كل العملاء مع اسم المجموعة"""
    with get_connection() as conn:
        where = "" if include_inactive else "WHERE c.is_active = 1"
        rows = conn.execute(f"""
            SELECT c.id, c.name, c.phone, c.total_debt,
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
            SELECT id, name, phone, total_debt, notes, created_at
            FROM customers
            WHERE group_id = ? AND is_active = 1
            ORDER BY name
        """, (group_id,)).fetchall()
        return [dict(r) for r in rows]


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
            SELECT c.id, c.name, c.phone, c.total_debt, g.name AS group_name
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
