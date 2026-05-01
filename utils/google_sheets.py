"""
utils/google_sheets.py — Professional Financial Export (Account Statements)
Optimized for Google Sheets API (Free Tier) & Mobile View.
"""
import sys
import traceback
from pathlib import Path
import gspread

# Configuration
_CREDS_PATH  = Path(__file__).parent.parent / "credentials.json"
_SHEET_NAME  = "الحسابات"
_SHEET_NAMES = ["📊 الملخص", "👤 العملاء", "🏷️ المجموعات"]

# ── API Formatting Helpers ───────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> dict:
    h = hex_color.lstrip("#")
    return {
        "red":   int(h[0:2], 16) / 255,
        "green": int(h[2:4], 16) / 255,
        "blue":  int(h[4:6], 16) / 255,
    }

def _fmt(sheet_id: int, r0: int, r1: int, c0: int, c1: int, *,
         bold: bool = False, bg: str = None, fg: str = None,
         align: str = "RIGHT", num_fmt: str = None, font_size: int = None) -> dict:
    cell_fmt: dict = {"verticalAlignment": "MIDDLE", "horizontalAlignment": align}
    parts:    list  = ["verticalAlignment", "horizontalAlignment"]

    if bold or fg or font_size:
        tf: dict = {}
        if bold:      tf["bold"]            = True
        if fg:        tf["foregroundColor"] = _hex_to_rgb(fg)
        if font_size: tf["fontSize"]        = font_size
        cell_fmt["textFormat"] = tf
        parts.append("textFormat")

    if bg:
        cell_fmt["backgroundColor"] = _hex_to_rgb(bg)
        parts.append("backgroundColor")

    if num_fmt:
        cell_fmt["numberFormat"] = {"type": "NUMBER", "pattern": num_fmt}
        parts.append("numberFormat")

    return {
        "repeatCell": {
            "range": {
                "sheetId":          sheet_id,
                "startRowIndex":    r0,
                "endRowIndex":      r1,
                "startColumnIndex": c0,
                "endColumnIndex":   c1,
            },
            "cell":   {"userEnteredFormat": cell_fmt},
            "fields": "userEnteredFormat(" + ",".join(parts) + ")",
        }
    }

def _col_width(sheet_id: int, col: int, px: int) -> dict:
    return {
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
            "properties": {"pixelSize": px}, "fields": "pixelSize"
        }
    }

def _row_height(sheet_id: int, row: int, px: int) -> dict:
    return {
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": row, "endIndex": row + 1},
            "properties": {"pixelSize": px}, "fields": "pixelSize"
        }
    }

def _merge(sheet_id: int, row: int, c0: int, c1: int) -> dict:
    return {
        "mergeCells": {
            "range": {"sheetId": sheet_id, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": c0, "endColumnIndex": c1},
            "mergeType": "MERGE_ALL"
        }
    }

def _border(sheet_id: int, r0: int, r1: int, c0: int, c1: int) -> dict:
    style = {"style": "SOLID", "color": {"red": 0.4, "green": 0.4, "blue": 0.4}}
    return {
        "updateBorders": {
            "range": {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1, "startColumnIndex": c0, "endColumnIndex": c1},
            "top": style, "bottom": style, "left": style, "right": style,
            "innerHorizontal": style, "innerVertical": style
        }
    }

def _optimize_view(sheet_id: int) -> list:
    """Returns requests to set RTL, hide gridlines, and freeze headers."""
    return [
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "rightToLeft": True, "gridProperties": {"hideGridlines": True, "frozenRowCount": 1}},
                "fields": "rightToLeft,gridProperties.hideGridlines,gridProperties.frozenRowCount"
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
        
        rows.append([link, c.get("phone", ""), c.get("group_name", ""), c["total_debt"]])
        
        r = i + 1
        bg = "#F8F9FA" if i % 2 == 0 else "#FFFFFF"
        debt = float(c["total_debt"] or 0)
        fg = "#D0021B" if debt > 0 else ("#008000" if debt < 0 else "#000000")
        
        reqs.append(_fmt(sid, r, r + 1, 0, 4, bg=bg))
        reqs.append(_fmt(sid, r, r + 1, 3, 4, fg=fg, bold=True, num_fmt='#,##0.00 "ج"'))
        reqs.append(_row_height(sid, r, 32))

    # Header & Layout
    reqs.extend([
        _fmt(sid, 0, 1, 0, 4, bold=True, bg="#1B263B", fg="#FFFFFF", font_size=12, align="CENTER"),
        _row_height(sid, 0, 45),
        _col_width(sid, 0, 250), _col_width(sid, 1, 150), _col_width(sid, 2, 180), _col_width(sid, 3, 150),
        _border(sid, 0, len(rows), 0, 4)
    ])

    ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")
    spreadsheet.batch_update({"requests": reqs})


def _build_customers(spreadsheet, ws, data: dict) -> dict:
    sid = ws.id
    statements = data.get("individual_statements", [])
    rows = []
    reqs = _optimize_view(sid)
    customer_links = {}

    reqs.extend([
        _col_width(sid, 0, 160), _col_width(sid, 1, 280), _col_width(sid, 2, 120), _col_width(sid, 3, 120)
    ])

    for i, cust in enumerate(statements):
        if i > 0: rows.extend([[""]*4, [""]*4]) # Spacer rows
        
        block_start = len(rows)
        customer_links[cust["name"]] = block_start + 1
        
        # 1. Block Header
        hdr_idx = len(rows)
        rows.append([f"👤  كشف حساب: {cust['name']}  |  {cust.get('phone', '')}", "", "", ""])
        reqs.append(_merge(sid, hdr_idx, 0, 4))
        reqs.append(_fmt(sid, hdr_idx, hdr_idx + 1, 0, 4, bold=True, bg="#1B263B", fg="#FFFFFF", font_size=13, align="CENTER"))
        reqs.append(_row_height(sid, hdr_idx, 45))

        # 2. Table Header
        th_idx = len(rows)
        rows.append(["التاريخ", "البيان / الخدمة", "مدين (عليه)", "دائن (له)"])
        reqs.append(_fmt(sid, th_idx, th_idx + 1, 0, 4, bold=True, bg="#415A77", fg="#FFFFFF", align="CENTER"))
        reqs.append(_row_height(sid, th_idx, 35))

        # 3. Transaction Rows
        total_owed = 0.0
        total_credit = 0.0
        for j, t in enumerate(cust.get("transactions", [])):
            tx_idx = len(rows)
            amt = float(t["amount"] or 0)
            owed = amt if amt > 0 else 0
            credit = abs(amt) if amt < 0 else 0
            total_owed += owed
            total_credit += credit
            
            rows.append([t["date"], t["service"], owed if owed > 0 else "", credit if credit > 0 else ""])
            bg = "#F8F9FA" if j % 2 == 0 else "#FFFFFF"
            reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 0, 4, bg=bg))
            reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 2, 3, fg="#D0021B", num_fmt='#,##0.00 "ج"'))
            reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 3, 4, fg="#008000", num_fmt='#,##0.00 "ج"'))
            reqs.append(_row_height(sid, tx_idx, 30))

        # 4. Footer
        f_idx = len(rows)
        net = float(cust.get("total_debt", 0) or 0)
        status = "مستحق عليه" if net > 0 else "مستحق له"
        net_fg = "#D0021B" if net > 0 else "#008000"
        
        rows.append(["", "الإجماليات:", total_owed, total_credit])
        rows.append(["", f"الرصيد النهائي ({status}):", "", abs(net)])
        
        # Footer styling
        reqs.append(_fmt(sid, f_idx, f_idx + 1, 1, 2, bold=True, bg="#E0E1DD"))
        reqs.append(_fmt(sid, f_idx, f_idx + 1, 2, 3, bold=True, fg="#D0021B", num_fmt='#,##0.00 "ج"'))
        reqs.append(_fmt(sid, f_idx, f_idx + 1, 3, 4, bold=True, fg="#008000", num_fmt='#,##0.00 "ج"'))
        reqs.append(_row_height(sid, f_idx, 35))
        
        net_row = f_idx + 1
        reqs.append(_merge(sid, net_row, 1, 3))
        reqs.append(_fmt(sid, net_row, net_row + 1, 1, 4, bold=True, bg="#1B263B", fg="#FFFFFF", align="CENTER"))
        reqs.append(_fmt(sid, net_row, net_row + 1, 3, 4, bold=True, fg=net_fg, num_fmt='#,##0.00 "ج"', font_size=12))
        reqs.append(_row_height(sid, net_row, 40))
        
        # Block Border
        reqs.append(_border(sid, hdr_idx, len(rows), 0, 4))

    if rows:
        ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")
    spreadsheet.batch_update({"requests": reqs})
    return customer_links


def _build_groups(spreadsheet, ws, data: dict) -> None:
    sid = ws.id
    groups = data.get("groups", [])
    rows = []
    reqs = _optimize_view(sid)
    reqs.extend([
        _col_width(sid, 0, 180), _col_width(sid, 1, 250), _col_width(sid, 2, 120), _col_width(sid, 3, 120)
    ])

    for g_i, group in enumerate(groups):
        if g_i > 0: rows.extend([[""]*4, [""]*4])
        
        g_start = len(rows)
        rows.append([f"🏷️  مجموعة: {group['name']}", "", "", ""])
        reqs.append(_merge(sid, g_start, 0, 4))
        reqs.append(_fmt(sid, g_start, g_start + 1, 0, 4, bold=True, bg="#1B263B", fg="#FFFFFF", font_size=14, align="CENTER"))
        reqs.append(_row_height(sid, g_start, 50))

        group_owed = 0.0
        group_credit = 0.0

        for m_i, member in enumerate(group.get("members", [])):
            if m_i > 0: rows.append([""]*4)
            m_idx = len(rows)
            rows.append([f"👤 {member['name']}", "البيان / الخدمة", "مدين", "دائن"])
            reqs.append(_fmt(sid, m_idx, m_idx + 1, 0, 1, bold=True, bg="#E0E1DD"))
            reqs.append(_fmt(sid, m_idx, m_idx + 1, 1, 4, bold=True, bg="#415A77", fg="#FFFFFF"))
            reqs.append(_row_height(sid, m_idx, 35))

            for t in member.get("transactions", []):
                tx_idx = len(rows)
                amt = float(t["amount"] or 0)
                o, c = (amt, 0) if amt > 0 else (0, abs(amt))
                group_owed += o; group_credit += c
                rows.append(["", t["service"], o if o > 0 else "", c if c > 0 else ""])
                reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 0, 4, bg="#FFFFFF"))
                reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 2, 3, fg="#D0021B", num_fmt='#,##0.00 "ج"'))
                reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 3, 4, fg="#008000", num_fmt='#,##0.00 "ج"'))
                reqs.append(_row_height(sid, tx_idx, 30))

        # Group Footer
        f_idx = len(rows)
        net = group_owed - group_credit
        status = "مستحق على المجموعة" if net > 0 else "مستحق للمجموعة"
        net_fg = "#D0021B" if net > 0 else "#008000"
        
        rows.append(["", "إجمالي المجموعة (مدين):", group_owed, ""])
        rows.append(["", "إجمالي المجموعة (دائن):", "", group_credit])
        rows.append(["", f"صافي المجموعة ({status}):", "", abs(net)])
        
        reqs.append(_fmt(sid, f_idx, f_idx + 3, 1, 2, bold=True))
        reqs.append(_fmt(sid, f_idx, f_idx + 1, 2, 3, bold=True, fg="#D0021B", num_fmt='#,##0.00 "ج"'))
        reqs.append(_fmt(sid, f_idx + 1, f_idx + 2, 3, 4, bold=True, fg="#008000", num_fmt='#,##0.00 "ج"'))
        
        net_idx = f_idx + 2
        reqs.append(_merge(sid, net_idx, 1, 3))
        reqs.append(_fmt(sid, net_idx, net_idx + 1, 1, 4, bold=True, bg="#1B263B", fg="#FFFFFF", align="CENTER"))
        reqs.append(_fmt(sid, net_idx, net_idx + 1, 3, 4, bold=True, fg=net_fg, num_fmt='#,##0.00 "ج"'))
        
        reqs.append(_border(sid, g_start, len(rows), 0, 4))

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
        if not remaining: temp = spreadsheet.add_worksheet("_tmp_", rows=1, cols=1)
        for ws in to_delete: spreadsheet.del_worksheet(ws)

        ws_summary   = spreadsheet.add_worksheet(_SHEET_NAMES[0], rows=2000, cols=4)
        ws_customers = spreadsheet.add_worksheet(_SHEET_NAMES[1], rows=10000, cols=4)
        ws_groups    = spreadsheet.add_worksheet(_SHEET_NAMES[2], rows=10000, cols=4)
        if temp: spreadsheet.del_worksheet(temp)

        # 2. Build Sheets (Each builder uses 1 update + 1 batch_update)
        customer_links = _build_customers(spreadsheet, ws_customers, data)
        _build_summary(spreadsheet, ws_summary, data, customer_links)
        _build_groups(spreadsheet, ws_groups, data)

        return spreadsheet.url

    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        raise
