"""
utils/google_sheets.py — Professional Financial Export (Account Statements)
Optimized for Google Sheets API (Free Tier) & Mobile View.
"""

import sys
import traceback
from pathlib import Path

import gspread

# Configuration
_CREDS_PATH = Path(__file__).parent.parent / "credentials.json"
_SHEET_NAME = "الحسابات"
_SHEET_NAMES = ["📊 الملخص", "👤 العملاء", "🏷️ المجموعات"]

# ── API Formatting Helpers ───────────────────────────────────────────────────


def _hex_to_rgb(hex_color: str) -> dict:
    h = hex_color.lstrip("#")
    return {
        "red": int(h[0:2], 16) / 255,
        "green": int(h[2:4], 16) / 255,
        "blue": int(h[4:6], 16) / 255,
    }


def _contrast_text(bg_hex: str) -> str:
    h = bg_hex.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#111827" if luminance > 0.55 else "#F9FAFB"


def _fmt(
    sheet_id: int,
    r0: int,
    r1: int,
    c0: int,
    c1: int,
    *,
    bold: bool = False,
    bg: str = None,
    fg: str = None,
    align: str = "RIGHT",
    num_fmt: str = None,
    num_fmt_type: str = "NUMBER",
    font_size: int = None,
) -> dict:
    cell_fmt: dict = {"verticalAlignment": "MIDDLE", "horizontalAlignment": align}
    parts: list = ["verticalAlignment", "horizontalAlignment"]

    if bold or fg or font_size:
        tf: dict = {}
        if bold:
            tf["bold"] = True
        if fg:
            tf["foregroundColor"] = _hex_to_rgb(fg)
        if font_size:
            tf["fontSize"] = font_size
        cell_fmt["textFormat"] = tf
        parts.append("textFormat")

    if bg:
        cell_fmt["backgroundColor"] = _hex_to_rgb(bg)
        parts.append("backgroundColor")

    if num_fmt:
        cell_fmt["numberFormat"] = {"type": num_fmt_type, "pattern": num_fmt}
        parts.append("numberFormat")

    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r0,
                "endRowIndex": r1,
                "startColumnIndex": c0,
                "endColumnIndex": c1,
            },
            "cell": {"userEnteredFormat": cell_fmt},
            "fields": "userEnteredFormat(" + ",".join(parts) + ")",
        }
    }


def _col_width(sheet_id: int, col: int, px: int) -> dict:
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": col,
                "endIndex": col + 1,
            },
            "properties": {"pixelSize": px},
            "fields": "pixelSize",
        }
    }


def _auto_resize(sheet_id: int, c0: int, c1: int) -> dict:
    return {
        "autoResizeDimensions": {
            "dimensions": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": c0,
                "endIndex": c1,
            }
        }
    }


def _row_height(sheet_id: int, row: int, px: int) -> dict:
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": row,
                "endIndex": row + 1,
            },
            "properties": {"pixelSize": px},
            "fields": "pixelSize",
        }
    }


def _banded_rows(sheet_id: int, r0: int, r1: int, c0: int, c1: int) -> dict:
    return {
        "addBanding": {
            "bandedRange": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": r0,
                    "endRowIndex": r1,
                    "startColumnIndex": c0,
                    "endColumnIndex": c1,
                },
                "rowProperties": {
                    "headerColor": _hex_to_rgb("#415A77"),
                    "firstBandColor": _hex_to_rgb("#F8F9FA"),
                    "secondBandColor": _hex_to_rgb("#FFFFFF"),
                },
            }
        }
    }


def _status_rule(sheet_id: int, status: str, bg: str, r1: int, cols: int) -> dict:
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [
                    {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": r1,
                        "startColumnIndex": 0,
                        "endColumnIndex": cols,
                    }
                ],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": f'=$F1="{status}"'}],
                    },
                    "format": {
                        "backgroundColor": _hex_to_rgb(bg),
                        "textFormat": {"foregroundColor": _hex_to_rgb(_contrast_text(bg))},
                    },
                },
            },
            "index": 0,
        }
    }


def _merge(sheet_id: int, row: int, c0: int, c1: int) -> dict:
    return {
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row,
                "endRowIndex": row + 1,
                "startColumnIndex": c0,
                "endColumnIndex": c1,
            },
            "mergeType": "MERGE_ALL",
        }
    }


def _border(sheet_id: int, r0: int, r1: int, c0: int, c1: int) -> dict:
    style = {"style": "SOLID", "color": {"red": 0.4, "green": 0.4, "blue": 0.4}}
    return {
        "updateBorders": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r0,
                "endRowIndex": r1,
                "startColumnIndex": c0,
                "endColumnIndex": c1,
            },
            "top": style,
            "bottom": style,
            "left": style,
            "right": style,
            "innerHorizontal": style,
            "innerVertical": style,
        }
    }


def _optimize_view(sheet_id: int) -> list:
    """Returns requests to set RTL, hide gridlines, and freeze headers."""
    return [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "rightToLeft": True,
                    "gridProperties": {"hideGridlines": True, "frozenRowCount": 1},
                },
                "fields": "rightToLeft,gridProperties.hideGridlines,gridProperties.frozenRowCount",
            }
        }
    ]


# ── Sheet Builders ───────────────────────────────────────────────────────────


def _build_summary(spreadsheet, ws, data: dict, customer_links: dict) -> None:
    sid = ws.id
    all_summary = data.get("all_summary", [])
    cust_gid = spreadsheet.worksheet(_SHEET_NAMES[1]).id

    rows = [["الاسم (اضغط للانتقال)", "التليفون", "المجموعة", "إجمالي المديونية"]]
    reqs = _optimize_view(sid)

    for i, c in enumerate(all_summary):
        name = c["name"]
        link = name
        if name in customer_links:
            row_idx = customer_links[name]
            link = f'=HYPERLINK("#gid={cust_gid}&range=A{row_idx}", "{name}")'

        rows.append(
            [link, c.get("phone", ""), c.get("group_name", ""), c["total_debt"]]
        )

        r = i + 1
        bg = "#F8F9FA" if i % 2 == 0 else "#FFFFFF"
        debt = float(c["total_debt"] or 0)
        fg = "#D0021B" if debt > 0 else ("#008000" if debt < 0 else "#000000")

        reqs.append(_fmt(sid, r, r + 1, 0, 4, bg=bg))
        reqs.append(_fmt(sid, r, r + 1, 3, 4, fg=fg, bold=True, num_fmt='#,##0.00 "ج.م"'))
        reqs.append(_row_height(sid, r, 32))

    # Header & Layout
    reqs.extend(
        [
            _fmt(
                sid,
                0,
                1,
                0,
                4,
                bold=True,
                bg="#1B263B",
                fg="#FFFFFF",
                font_size=12,
                align="CENTER",
            ),
            _row_height(sid, 0, 45),
            _col_width(sid, 0, 250),
            _col_width(sid, 1, 150),
            _col_width(sid, 2, 180),
            _col_width(sid, 3, 150),
            _border(sid, 0, len(rows), 0, 4),
        ]
    )

    ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")
    spreadsheet.batch_update({"requests": reqs})


def _build_customers(spreadsheet, ws, data: dict) -> dict:
    sid = ws.id
    statements = data.get("individual_statements", [])
    rows = []
    reqs = _optimize_view(sid)
    customer_links = {}
    col_count = 6

    reqs.extend(
        [
            _col_width(sid, 0, 160),
            _col_width(sid, 1, 280),
            _col_width(sid, 2, 120),
            _col_width(sid, 3, 120),
            _col_width(sid, 4, 130),
            _col_width(sid, 5, 130),
        ]
    )

    for i, cust in enumerate(statements):
        if i > 0:
            rows.extend([[""] * col_count, [""] * col_count])  # Spacer rows

        block_start = len(rows)
        customer_links[cust["name"]] = block_start + 1

        # 1. Block Header
        hdr_idx = len(rows)
        rows.append(
            [f"👤  كشف حساب: {cust['name']}  |  {cust.get('phone', '')}", "", "", "", "", ""]
        )
        reqs.append(_merge(sid, hdr_idx, 0, col_count))
        reqs.append(
            _fmt(
                sid,
                hdr_idx,
                hdr_idx + 1,
                0,
                col_count,
                bold=True,
                bg="#1B263B",
                fg="#FFFFFF",
                font_size=13,
                align="CENTER",
            )
        )
        reqs.append(_row_height(sid, hdr_idx, 45))

        # 2. Table Header
        th_idx = len(rows)
        rows.append(["التاريخ", "البيان / الخدمة", "مدين (عليه)", "دائن (له)", "الرصيد", "حالة العملية"])
        reqs.append(
            _fmt(
                sid,
                th_idx,
                th_idx + 1,
                0,
                col_count,
                bold=True,
                bg="#415A77",
                fg="#FFFFFF",
                align="CENTER",
            )
        )
        reqs.append(_row_height(sid, th_idx, 35))

        # 3. Transaction Rows
        total_owed = 0.0
        total_credit = 0.0
        running_balance = 0.0
        for j, t in enumerate(cust.get("transactions", [])):
            tx_idx = len(rows)
            amt = float(t["amount"] or 0)
            effective = float(t.get("effective_amount", amt) or 0)
            status = t.get("status") or "قيد الانتظار"
            owed = amt if amt > 0 else 0
            credit = abs(amt) if amt < 0 else 0
            eff_owed = effective if effective > 0 else 0
            eff_credit = abs(effective) if effective < 0 else 0
            total_owed += eff_owed
            total_credit += eff_credit
            running_balance += effective

            rows.append(
                [
                    t["date"],
                    t["service"],
                    owed if owed > 0 else "",
                    credit if credit > 0 else "",
                    running_balance,
                    status,
                ]
            )
            reqs.append(
                _fmt(
                    sid,
                    tx_idx,
                    tx_idx + 1,
                    0,
                    1,
                    align="CENTER",
                    num_fmt="yyyy-mm-dd",
                    num_fmt_type="DATE",
                )
            )
            reqs.append(
                _fmt(
                    sid, tx_idx, tx_idx + 1, 2, 3, fg="#D0021B", num_fmt='#,##0.00 "ج.م"'
                )
            )
            reqs.append(
                _fmt(
                    sid, tx_idx, tx_idx + 1, 3, 4, fg="#008000", num_fmt='#,##0.00 "ج.م"'
                )
            )
            balance_fg = "#D0021B" if running_balance > 0 else ("#008000" if running_balance < 0 else "#000000")
            reqs.append(
                _fmt(
                    sid,
                    tx_idx,
                    tx_idx + 1,
                    4,
                    5,
                    fg=balance_fg,
                    bold=True,
                    num_fmt='#,##0.00 "ج.م"',
                    align="CENTER",
                )
            )
            reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 5, 6, bold=True, align="CENTER"))
            reqs.append(_row_height(sid, tx_idx, 30))

        # 4. Footer
        f_idx = len(rows)
        net = float(cust.get("total_debt", 0) or 0)
        status = "مستحق عليه" if net > 0 else "مستحق له"
        net_fg = "#D0021B" if net > 0 else "#008000"

        rows.append(["", "الإجماليات:", total_owed, total_credit, total_owed - total_credit, ""])
        rows.append(["", f"الرصيد النهائي ({status}):", "", "", abs(net), ""])

        # Footer styling
        reqs.append(_fmt(sid, f_idx, f_idx + 1, 1, 2, bold=True, bg="#E0E1DD"))
        reqs.append(
            _fmt(
                sid,
                f_idx,
                f_idx + 1,
                2,
                3,
                bold=True,
                fg="#D0021B",
                num_fmt='#,##0.00 "ج.م"',
            )
        )
        reqs.append(
            _fmt(
                sid,
                f_idx,
                f_idx + 1,
                3,
                4,
                bold=True,
                fg="#008000",
                num_fmt='#,##0.00 "ج.م"',
            )
        )
        reqs.append(
            _fmt(
                sid,
                f_idx,
                f_idx + 1,
                4,
                5,
                bold=True,
                num_fmt='#,##0.00 "ج.م"',
                align="CENTER",
            )
        )
        reqs.append(_row_height(sid, f_idx, 35))

        net_row = f_idx + 1
        reqs.append(_merge(sid, net_row, 1, 4))
        reqs.append(
            _fmt(
                sid,
                net_row,
                net_row + 1,
                1,
                5,
                bold=True,
                bg="#1B263B",
                fg="#FFFFFF",
                align="CENTER",
            )
        )
        reqs.append(
            _fmt(
                sid,
                net_row,
                net_row + 1,
                4,
                5,
                bold=True,
                fg=net_fg,
                num_fmt='#,##0.00 "ج.م"',
                font_size=12,
            )
        )
        reqs.append(_row_height(sid, net_row, 40))

        # Block Border
        reqs.append(_border(sid, hdr_idx, len(rows), 0, col_count))

    if rows:
        ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")
        reqs.insert(1, _banded_rows(sid, 0, max(len(rows), 10000), 0, col_count))
        reqs.extend(
            [
                _status_rule(sid, "مسدد", "#E8F5E9", max(len(rows), 10000), col_count),
                _status_rule(sid, "تم التسليم", "#E3F2FD", max(len(rows), 10000), col_count),
                _auto_resize(sid, 0, col_count),
            ]
        )
    spreadsheet.batch_update({"requests": reqs})
    return customer_links


def _build_groups(spreadsheet, ws, data: dict) -> None:
    """Sheet 3 — 🏷️ المجموعات : Detailed Group Accounting Ledger."""
    sid = ws.id
    groups = data.get("groups", [])
    rows = []
    reqs = _optimize_view(sid)

    # Column Widths: Name, Phone, Debit, Credit, Net
    reqs.extend(
        [
            _col_width(sid, 0, 180),  # Member Name
            _col_width(sid, 1, 140),  # Phone
            _col_width(sid, 2, 110),  # Debit (عليه)
            _col_width(sid, 3, 110),  # Credit (له)
            _col_width(sid, 4, 130),  # Net (الصافي)
        ]
    )

    for g_i, group in enumerate(groups):
        if g_i > 0:
            rows.extend([[""] * 5, [""] * 5])  # Block Spacing

        g_start = len(rows)
        # 1. Group Header (Merged A:E)
        rows.append([f"🏷️  مجموعة: {group['name']}", "", "", "", ""])
        reqs.append(_merge(sid, g_start, 0, 5))
        reqs.append(
            _fmt(
                sid,
                g_start,
                g_start + 1,
                0,
                5,
                bold=True,
                bg="#1B263B",
                fg="#FFFFFF",
                font_size=14,
                align="CENTER",
            )
        )
        reqs.append(_row_height(sid, g_start, 50))

        # 2. Table Header
        th_idx = len(rows)
        rows.append(["اسم العضو", "التليفون", "مدين (عليه)", "دائن (له)", "صافي العضو"])
        reqs.append(
            _fmt(
                sid,
                th_idx,
                th_idx + 1,
                0,
                5,
                bold=True,
                bg="#415A77",
                fg="#FFFFFF",
                align="CENTER",
            )
        )
        reqs.append(_row_height(sid, th_idx, 35))

        group_total_owed = 0.0
        group_total_credit = 0.0

        # 3. Member Rows
        for m_i, member in enumerate(group.get("members", [])):
            m_row_idx = len(rows)

            # Calculate member totals from their transactions
            m_owed = 0.0
            m_credit = 0.0
            for t in member.get("transactions", []):
                amt = float(t.get("effective_amount", t.get("amount", 0)) or 0)
                if amt > 0:
                    m_owed += amt
                else:
                    m_credit += abs(amt)

            m_net = m_owed - m_credit
            group_total_owed += m_owed
            group_total_credit += m_credit

            rows.append(
                [
                    member["name"],
                    member.get("phone", ""),
                    m_owed if m_owed > 0 else "",
                    m_credit if m_credit > 0 else "",
                    m_net,
                ]
            )

            bg = "#F8F9FA" if m_i % 2 == 0 else "#FFFFFF"
            reqs.append(_fmt(sid, m_row_idx, m_row_idx + 1, 0, 5, bg=bg))
            reqs.append(
                _fmt(
                    sid,
                    m_row_idx,
                    m_row_idx + 1,
                    2,
                    3,
                    fg="#D0021B",
                    num_fmt='#,##0.00 "ج.م"',
                )
            )
            reqs.append(
                _fmt(
                    sid,
                    m_row_idx,
                    m_row_idx + 1,
                    3,
                    4,
                    fg="#008000",
                    num_fmt='#,##0.00 "ج.م"',
                )
            )

            # Member Net Balance Color
            m_net_fg = (
                "#D0021B" if m_net > 0 else ("#008000" if m_net < 0 else "#000000")
            )
            reqs.append(
                _fmt(
                    sid,
                    m_row_idx,
                    m_row_idx + 1,
                    4,
                    5,
                    fg=m_net_fg,
                    bold=True,
                    num_fmt='#,##0.00 "ج.م"',
                )
            )
            reqs.append(_row_height(sid, m_row_idx, 30))

        # 4. Group Footer (Summary)
        f_idx = len(rows)
        group_net = group_total_owed - group_total_credit
        status = "مستحق على المجموعة" if group_net > 0 else "مستحق للمجموعة"
        net_fg = "#D0021B" if group_net > 0 else "#008000"

        rows.append(["", "إجمالي مبالغ المجموعة (عليه):", group_total_owed, "", ""])
        rows.append(["", "إجمالي مدفوعات المجموعة (له):", "", group_total_credit, ""])
        rows.append(["", f"الصافي النهائي للمجموعة ({status}):", "", "", group_net])

        # Footer Styling
        reqs.append(_fmt(sid, f_idx, f_idx + 2, 1, 2, bold=True, bg="#E0E1DD"))
        reqs.append(
            _fmt(
                sid,
                f_idx,
                f_idx + 1,
                2,
                3,
                bold=True,
                fg="#D0021B",
                num_fmt='#,##0.00 "ج.م"',
            )
        )
        reqs.append(
            _fmt(
                sid,
                f_idx + 1,
                f_idx + 2,
                3,
                4,
                bold=True,
                fg="#008000",
                num_fmt='#,##0.00 "ج.م"',
            )
        )
        reqs.append(_row_height(sid, f_idx, 35))
        reqs.append(_row_height(sid, f_idx + 1, 35))

        # Net Summary Row
        net_row = f_idx + 2
        reqs.append(_merge(sid, net_row, 1, 4))
        reqs.append(
            _fmt(
                sid,
                net_row,
                net_row + 1,
                1,
                5,
                bold=True,
                bg="#1B263B",
                fg="#FFFFFF",
                align="CENTER",
            )
        )
        reqs.append(
            _fmt(
                sid,
                net_row,
                net_row + 1,
                4,
                5,
                bold=True,
                fg=net_fg,
                num_fmt='#,##0.00 "ج.م"',
                font_size=12,
            )
        )
        reqs.append(_row_height(sid, net_row, 45))

        # Border for the entire group block
        reqs.append(_border(sid, g_start, len(rows), 0, 5))

    if rows:
        ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")
    spreadsheet.batch_update({"requests": reqs})


# ── Public API ───────────────────────────────────────────────────────────────


def export_to_sheets(data: dict) -> str:
    """Exports data to Google Sheets. Optimized for minimal API calls."""
    try:
        gc = gspread.service_account(filename=str(_CREDS_PATH))
        spreadsheet = gc.open(_SHEET_NAME)

        # 1. Clear & Prepare Worksheets (Minimal API calls)
        existing = spreadsheet.worksheets()
        to_delete = [ws for ws in existing if ws.title in _SHEET_NAMES + ["Sheet1"]]
        remaining = [ws for ws in existing if ws.title not in _SHEET_NAMES + ["Sheet1"]]

        temp = None
        if not remaining:
            temp = spreadsheet.add_worksheet("_tmp_", rows=1, cols=1)
        for ws in to_delete:
            spreadsheet.del_worksheet(ws)

        ws_summary = spreadsheet.add_worksheet(_SHEET_NAMES[0], rows=2000, cols=4)
        ws_customers = spreadsheet.add_worksheet(_SHEET_NAMES[1], rows=10000, cols=6)
        ws_groups = spreadsheet.add_worksheet(_SHEET_NAMES[2], rows=10000, cols=5)
        if temp:
            spreadsheet.del_worksheet(temp)

        # 2. Build Sheets (Each builder uses 1 update + 1 batch_update)
        customer_links = _build_customers(spreadsheet, ws_customers, data)
        _build_summary(spreadsheet, ws_summary, data, customer_links)
        _build_groups(spreadsheet, ws_groups, data)

        return spreadsheet.url

    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        raise
