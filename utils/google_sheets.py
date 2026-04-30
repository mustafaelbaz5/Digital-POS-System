"""
utils/google_sheets.py — Google Sheets export (3-sheet layout)
"""
import sys
import traceback
from pathlib import Path

import gspread

_CREDS_PATH  = Path(__file__).parent.parent / "credentials.json"
_SHEET_NAME  = "حسابات المحل"
_SHEET_NAMES = ["📊 الملخص", "👤 العملاء", "🏷️ المجموعات"]


# ── Sheets API request builders ──────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> dict:
    h = hex_color.lstrip("#")
    return {
        "red":   int(h[0:2], 16) / 255,
        "green": int(h[2:4], 16) / 255,
        "blue":  int(h[4:6], 16) / 255,
    }


def _fmt(sheet_id: int, r0: int, r1: int, c0: int, c1: int, *,
         bold: bool = False, bg: str = None, fg: str = None,
         align: str = None, num_fmt: str = None, font_size: int = None) -> dict:
    """Build a repeatCell formatting request covering rows [r0,r1) and cols [c0,c1)."""
    cell_fmt: dict = {}
    parts:    list  = []

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

    if align:
        cell_fmt["horizontalAlignment"] = align
        parts.append("horizontalAlignment")

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
            "range": {
                "sheetId":    sheet_id,
                "dimension":  "COLUMNS",
                "startIndex": col,
                "endIndex":   col + 1,
            },
            "properties": {"pixelSize": px},
            "fields":     "pixelSize",
        }
    }


def _row_height(sheet_id: int, row: int, px: int) -> dict:
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId":    sheet_id,
                "dimension":  "ROWS",
                "startIndex": row,
                "endIndex":   row + 1,
            },
            "properties": {"pixelSize": px},
            "fields":     "pixelSize",
        }
    }


def _merge(sheet_id: int, row: int, c0: int, c1: int) -> dict:
    return {
        "mergeCells": {
            "range": {
                "sheetId":          sheet_id,
                "startRowIndex":    row,
                "endRowIndex":      row + 1,
                "startColumnIndex": c0,
                "endColumnIndex":   c1,
            },
            "mergeType": "MERGE_ALL",
        }
    }


def _freeze(sheet_id: int, frozen_rows: int) -> dict:
    return {
        "updateSheetProperties": {
            "properties": {
                "sheetId":        sheet_id,
                "gridProperties": {"frozenRowCount": frozen_rows},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    }


def _right_align_all(sheet_id: int) -> dict:
    return {
        "repeatCell": {
            "range": {"sheetId": sheet_id},
            "cell":  {"userEnteredFormat": {"horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(horizontalAlignment)",
        }
    }


# ── Sheet builders ───────────────────────────────────────────────────────────

def _build_summary(spreadsheet, ws, data: dict) -> None:
    """Sheet 1 — 📊 الملخص : summary table sorted by debt descending."""
    sid           = ws.id
    all_customers = data.get("all_customers", [])

    rows = [["الاسم", "التليفون", "المجموعة", "المديونية"]]
    for c in all_customers:
        rows.append([c["name"], c.get("phone", ""), c.get("group_name", ""), c["total_debt"]])

    ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")

    reqs = [
        _right_align_all(sid),
        _col_width(sid, 0, 200),
        _col_width(sid, 1, 150),
        _col_width(sid, 2, 160),
        _col_width(sid, 3, 140),
        _row_height(sid, 0, 36),
        _freeze(sid, 1),
        _fmt(sid, 0, 1, 0, 4, bold=True, bg="#0D1117", fg="#39C5BB"),
    ]

    for i, c in enumerate(all_customers):
        r    = i + 1
        bg   = "#0D1117" if i % 2 == 0 else "#161B22"
        debt = float(c.get("total_debt", 0) or 0)
        reqs.append(_fmt(sid, r, r + 1, 0, 4, bg=bg))
        if debt > 0:
            reqs.append(_fmt(sid, r, r + 1, 3, 4, fg="#F85149", num_fmt='#,##0.00 "ج"'))
        elif debt < 0:
            reqs.append(_fmt(sid, r, r + 1, 3, 4, fg="#10B981", num_fmt='#,##0.00 "ج"'))
        else:
            reqs.append(_fmt(sid, r, r + 1, 3, 4, num_fmt='#,##0.00 "ج"'))

    spreadsheet.batch_update({"requests": reqs})


def _build_customers(spreadsheet, ws, data: dict) -> None:
    """Sheet 2 — 👤 العملاء : one block per ungrouped customer."""
    sid       = ws.id
    ungrouped = data.get("ungrouped", [])
    rows: list = []
    reqs: list = [
        _right_align_all(sid),
        _col_width(sid, 0, 160),
        _col_width(sid, 1, 200),
        _col_width(sid, 2, 140),
    ]

    for i, cust in enumerate(ungrouped):
        if i > 0:
            rows.append(["", "", ""])
            rows.append(["", "", ""])

        # ── block header (merged A:C) ─────────────────────────────────────
        hdr_idx = len(rows)
        rows.append([f"═══  {cust['name']}  |  {cust.get('phone', '')}  ═══", "", ""])
        reqs.append(_fmt(sid, hdr_idx, hdr_idx + 1, 0, 3,
                         bold=True, bg="#1C2333", fg="#E6EDF3", font_size=13))
        reqs.append(_merge(sid, hdr_idx, 0, 3))
        reqs.append(_row_height(sid, hdr_idx, 40))

        # ── column header row ─────────────────────────────────────────────
        ch_idx = len(rows)
        rows.append(["التاريخ", "الخدمة", "المبلغ"])
        reqs.append(_fmt(sid, ch_idx, ch_idx + 1, 0, 3,
                         bold=True, bg="#161B22", fg="#8B949E"))
        reqs.append(_row_height(sid, ch_idx, 32))

        # ── transaction rows ──────────────────────────────────────────────
        for j, t in enumerate(cust.get("transactions", [])):
            tx_idx = len(rows)
            rows.append([t["date"], t["service"], t["amount"]])
            bg = "#0D1117" if j % 2 == 0 else "#161B22"
            reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 0, 3, bg=bg, fg="#E6EDF3"))
            reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 2, 3, num_fmt='#,##0.00 "ج"'))

        # ── total row ─────────────────────────────────────────────────────
        tot_idx = len(rows)
        debt    = float(cust.get("total_debt", 0) or 0)
        debt_fg = "#F85149" if debt > 0 else "#10B981"
        rows.append(["", "الإجمالي عليه:", debt])
        reqs.append(_fmt(sid, tot_idx, tot_idx + 1, 0, 1, bold=True))
        reqs.append(_fmt(sid, tot_idx, tot_idx + 1, 1, 2, bold=True, fg="#8B949E"))
        reqs.append(_fmt(sid, tot_idx, tot_idx + 1, 2, 3,
                         bold=True, fg=debt_fg, num_fmt='#,##0.00 "ج"'))

    if rows:
        ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")

    spreadsheet.batch_update({"requests": reqs})


def _build_groups(spreadsheet, ws, data: dict) -> None:
    """Sheet 3 — 🏷️ المجموعات : one block per group with member sub-blocks."""
    sid      = ws.id
    groups   = data.get("groups", [])
    rows: list = []
    reqs: list = [
        _right_align_all(sid),
        _col_width(sid, 0, 180),
        _col_width(sid, 1, 150),
        _col_width(sid, 2, 200),
        _col_width(sid, 3, 140),
    ]

    for g_i, group in enumerate(groups):
        if g_i > 0:
            rows.extend([["", "", "", ""], ["", "", "", ""], ["", "", "", ""]])

        # ── group header (merged A:D) ──────────────────────────────────────
        gh_idx = len(rows)
        rows.append([f"══════  مجموعة: {group['name']}  ══════", "", "", ""])
        reqs.append(_fmt(sid, gh_idx, gh_idx + 1, 0, 4,
                         bold=True, bg="#0D1117", fg="#39C5BB", font_size=14))
        reqs.append(_merge(sid, gh_idx, 0, 4))
        reqs.append(_row_height(sid, gh_idx, 44))

        # ── column headers ────────────────────────────────────────────────
        ch_idx = len(rows)
        rows.append(["الاسم", "التليفون", "الخدمة", "المبلغ"])
        reqs.append(_fmt(sid, ch_idx, ch_idx + 1, 0, 4,
                         bold=True, bg="#161B22", fg="#8B949E"))

        # ── member sub-blocks ─────────────────────────────────────────────
        for m_i, member in enumerate(group.get("members", [])):
            if m_i > 0:
                rows.append(["", "", "", ""])  # 1 empty row between members

            # member name row (C:D merged)
            mn_idx = len(rows)
            rows.append([member["name"], member.get("phone", ""), "", ""])
            reqs.append(_fmt(sid, mn_idx, mn_idx + 1, 0, 4,
                             bold=True, bg="#1C2333", fg="#E6EDF3"))
            reqs.append(_merge(sid, mn_idx, 2, 4))

            # per-member transaction header (indented to C:D)
            th_idx = len(rows)
            rows.append(["", "", "الخدمة", "المبلغ"])
            reqs.append(_fmt(sid, th_idx, th_idx + 1, 2, 4, bold=True, fg="#8B949E"))

            # transaction rows
            for t in member.get("transactions", []):
                tx_idx = len(rows)
                rows.append(["", "", t["service"], t["amount"]])
                reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 0, 4, bg="#0D1117"))
                reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 2, 4, fg="#8B949E"))
                reqs.append(_fmt(sid, tx_idx, tx_idx + 1, 3, 4, num_fmt='#,##0.00 "ج"'))

            # member total row
            mt_idx    = len(rows)
            m_debt    = float(member.get("total_debt", 0) or 0)
            m_debt_fg = "#F85149" if m_debt > 0 else "#10B981"
            rows.append(["", "", "إجمالي العضو:", m_debt])
            reqs.append(_fmt(sid, mt_idx, mt_idx + 1, 0, 2, bold=True))
            reqs.append(_fmt(sid, mt_idx, mt_idx + 1, 2, 3, bold=True, fg="#8B949E"))
            reqs.append(_fmt(sid, mt_idx, mt_idx + 1, 3, 4,
                             bold=True, fg=m_debt_fg, num_fmt='#,##0.00 "ج"'))

        # ── group total row ────────────────────────────────────────────────
        gt_idx = len(rows)
        g_debt = float(group.get("total_debt", 0) or 0)
        rows.append(["", "", "إجمالي المجموعة:", g_debt])
        reqs.append(_fmt(sid, gt_idx, gt_idx + 1, 0, 2, bold=True, bg="#161B22"))
        reqs.append(_fmt(sid, gt_idx, gt_idx + 1, 2, 3, bold=True, bg="#161B22", fg="#8B949E"))
        reqs.append(_fmt(sid, gt_idx, gt_idx + 1, 3, 4,
                         bold=True, bg="#161B22", fg="#39C5BB", num_fmt='#,##0.00 "ج"'))

    if rows:
        ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")

    spreadsheet.batch_update({"requests": reqs})


# ── Public API ───────────────────────────────────────────────────────────────

def export_to_sheets(data: dict) -> str:
    """Exports data to Google Sheets. Returns the sheet URL."""
    try:
        gc          = gspread.service_account(filename=str(_CREDS_PATH))
        spreadsheet = gc.open(_SHEET_NAME)

        # Delete all target sheets + Sheet1, recreate fresh in order
        existing  = spreadsheet.worksheets()
        to_delete = [ws for ws in existing if ws.title in _SHEET_NAMES + ["Sheet1"]]
        remaining = [ws for ws in existing if ws.title not in _SHEET_NAMES + ["Sheet1"]]

        # Google Sheets requires at least one worksheet at all times
        temp = None
        if not remaining:
            temp = spreadsheet.add_worksheet("_tmp_", rows=1, cols=1)

        for ws in to_delete:
            spreadsheet.del_worksheet(ws)

        ws_summary   = spreadsheet.add_worksheet(_SHEET_NAMES[0], rows=2000, cols=4)
        ws_customers = spreadsheet.add_worksheet(_SHEET_NAMES[1], rows=5000, cols=3)
        ws_groups    = spreadsheet.add_worksheet(_SHEET_NAMES[2], rows=5000, cols=4)

        if temp:
            spreadsheet.del_worksheet(temp)

        _build_summary(spreadsheet,   ws_summary,   data)
        _build_customers(spreadsheet, ws_customers, data)
        _build_groups(spreadsheet,    ws_groups,    data)

        return spreadsheet.url

    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        raise
