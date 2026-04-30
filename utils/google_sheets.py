"""
utils/google_sheets.py — Google Sheets export
"""
import sys
from pathlib import Path

import gspread

_SHEET_NAME     = "حسابات المحل"
_WORKSHEET_NAME = "الحسابات"
_CREDS_PATH     = Path(__file__).parent.parent / "credentials.json"


def _hex_rgb(hex_color: str) -> dict:
    h = hex_color.lstrip("#")
    return {
        "red":   int(h[0:2], 16) / 255,
        "green": int(h[2:4], 16) / 255,
        "blue":  int(h[4:6], 16) / 255,
    }


def _fmt(sheet_id: int, row: int, c0: int, c1: int, *,
         bold: bool = False, bg: str = None,
         fg: str = None, align: str = None, num_fmt: str = None) -> dict:
    cell_fmt: dict = {}
    parts:    list  = []

    if bold or fg:
        tf: dict = {}
        if bold:
            tf["bold"] = True
        if fg:
            tf["foregroundColor"] = _hex_rgb(fg)
        cell_fmt["textFormat"] = tf
        parts.append("textFormat")

    if bg:
        cell_fmt["backgroundColor"] = _hex_rgb(bg)
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
                "startRowIndex":    row,
                "endRowIndex":      row + 1,
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


def export_to_sheets(data: dict) -> str:
    """Exports data to Google Sheets. Returns the sheet URL."""
    try:
        gc          = gspread.service_account(filename=str(_CREDS_PATH))
        spreadsheet = gc.open(_SHEET_NAME)

        try:
            ws = spreadsheet.worksheet(_WORKSHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(_WORKSHEET_NAME, rows=2000, cols=4)

        ws.clear()

        rows:    list[list] = []
        formats: list[dict] = []
        sid = ws.id

        def _r(row_type: str, cells: list, *, member: bool = False) -> None:
            idx    = len(rows)
            padded = cells + [""] * (4 - len(cells))
            rows.append(padded)

            if row_type == "cust_name":
                formats.append(_fmt(sid, idx, 0, 4, bold=True, bg="#1C2333"))

            elif row_type == "col_header":
                formats.append(_fmt(sid, idx, 0, 4, bold=True, bg="#161B22", fg="#8B949E"))

            elif row_type == "txn":
                col = 3 if member else 2
                formats.append(_fmt(sid, idx, col, col + 1,
                                    align="RIGHT", num_fmt="#,##0.00"))

            elif row_type == "cust_total":
                col  = 2 if member else 1
                debt = cells[col] if col < len(cells) else 0
                fg   = "#F85149" if (debt or 0) > 0 else "#10B981"
                formats.append(_fmt(sid, idx, 0, 4, bold=True, fg=fg))
                formats.append(_fmt(sid, idx, col, col + 1,
                                    align="RIGHT", num_fmt="#,##0.00"))

            elif row_type == "group_header":
                formats.append(_fmt(sid, idx, 0, 4, bold=True, bg="#0D1117", fg="#39C5BB"))

            elif row_type == "group_total":
                debt = cells[1] if len(cells) > 1 else 0
                fg   = "#F85149" if (debt or 0) > 0 else "#10B981"
                formats.append(_fmt(sid, idx, 0, 4, bold=True, fg=fg))
                formats.append(_fmt(sid, idx, 1, 2,
                                    align="RIGHT", num_fmt="#,##0.00"))

        def _gap() -> None:
            rows.append(["", "", "", ""])
            rows.append(["", "", "", ""])

        first_block = True

        for cust in data.get("ungrouped", []):
            if not first_block:
                _gap()
            first_block = False

            _r("cust_name",  [f"اسم العميل: {cust['name']}", cust.get("phone", "")])
            _r("col_header", ["التاريخ", "الخدمة", "المبلغ"])
            for t in cust.get("transactions", []):
                _r("txn", [t["date"], t["service"], t["amount"]])
            _r("cust_total", ["الإجمالي عليه:", cust.get("total_debt", 0)])

        for group in data.get("groups", []):
            if not first_block:
                _gap()
            first_block = False

            _r("group_header", [f"مجموعة: {group['name']}"])

            for member in group.get("members", []):
                _r("cust_name",  ["", f"اسم العميل: {member['name']}", member.get("phone", "")],
                   member=True)
                _r("col_header", ["", "التاريخ", "الخدمة", "المبلغ"], member=True)
                for t in member.get("transactions", []):
                    _r("txn", ["", t["date"], t["service"], t["amount"]], member=True)
                _r("cust_total", ["", "الإجمالي عليه:", member.get("total_debt", 0)],
                   member=True)

            _r("group_total", ["إجمالي المجموعة:", group.get("total_debt", 0)])

        if rows:
            ws.update(values=rows, range_name="A1", value_input_option="USER_ENTERED")

        requests = [
            # clear all previous formatting first
            {"updateCells": {"range": {"sheetId": sid}, "fields": "userEnteredFormat"}},
            _col_width(sid, 0, 180),
            _col_width(sid, 1, 150),
            _col_width(sid, 2, 120),
            _col_width(sid, 3, 100),
            *formats,
        ]
        spreadsheet.batch_update({"requests": requests})

        return spreadsheet.url

    except Exception as exc:
        print(f"[google_sheets] export error: {exc}", file=sys.stderr)
        raise
