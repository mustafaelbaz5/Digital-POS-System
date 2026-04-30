# Google Sheets Export — Updated Layout & Formatting

## Context
This is an update to the existing `utils/google_sheets.py` and `database/dal_customers.py`
already implemented in this project. Read both files fully before changing anything.
The export is triggered from `ui/screens/dashboard.py` via `_export_to_sheets()`.
`credentials.json` is in the project root. The Google Sheet is named "حسابات المحل".

---

## Task: Replace the single-sheet layout with a clean 3-sheet structure

### Sheet 1 — "📊 الملخص"
A single table listing every customer who has `total_debt != 0` OR has pending transactions.
Sorted descending by `total_debt` (highest debt first).

**Columns:** الاسم | التليفون | المجموعة | المديونية

**Formatting:**
- Row 1 (header): bold, background `#0D1117`, text `#39C5BB`, height 36px
- Debt > 0 rows: `total_debt` cell text color `#F85149`
- Debt < 0 rows: `total_debt` cell text color `#10B981`
- Alternating row background: odd `#0D1117`, even `#161B22`
- Column widths: A=200, B=150, C=160, D=140
- Freeze row 1
- Number format on column D: `#,##0.00 "ج"`

---

### Sheet 2 — "👤 العملاء"
One block per ungrouped customer (customers with `group_id IS NULL` or not in any group).
Blocks are separated by 2 empty rows.

**Each customer block layout:**
```
Row 1  : [═══ {name} | {phone} ═══]   ← merged A:C, bold
Row 2  : [التاريخ] [الخدمة] [المبلغ]  ← header row
Row 3+ : one row per pending transaction
Last   : [] [الإجمالي عليه:] [{total_debt}]
```

**Formatting:**
- Block header row (name): merged A:C, bold, background `#1C2333`, text `#E6EDF3`, font size 13, height 40px
- Column header row: bold, background `#161B22`, text `#8B949E`, height 32px
- Transaction rows: alternating background `#0D1117` / `#161B22`, text `#E6EDF3`
- Total row: bold, column B text `#8B949E`, column C text `#F85149` if debt > 0 else `#10B981`
- Column widths: A=160, B=200, C=140
- Number format on column C: `#,##0.00 "ج"`
- All text right-aligned

---

### Sheet 3 — "🏷️ المجموعات"
One block per group. Within each group block, one sub-block per member.
Group blocks separated by 3 empty rows. Member sub-blocks separated by 1 empty row.

**Each group block layout:**
```
Row 1    : [══════ مجموعة: {group_name} ══════]  ← merged A:D
Row 2    : [الاسم] [التليفون] [الخدمة] [المبلغ]  ← column headers

  ── member sub-block ──
  Row N  : [{member_name}] [{phone}] [] []         ← member name row, merged C:D
  Row N+1: [] [] [الخدمة] [المبلغ]                ← transaction header (indented)
  Row N+2+: [] [] [{service}] [{amount}]           ← transactions (indented)
  Row last: [] [] [إجمالي العضو:] [{member_debt}]

Group last row: [] [] [إجمالي المجموعة:] [{group_total}]
```

**Formatting:**
- Group header row: merged A:D, bold, background `#0D1117`, text `#39C5BB`, font size 14, height 44px
- Column header row: bold, background `#161B22`, text `#8B949E`
- Member name rows: bold, background `#1C2333`, text `#E6EDF3`
- Transaction rows: background `#0D1117`, text `#8B949E` for indented cells
- Member total rows: bold, column C text `#8B949E`, column D `#F85149` if > 0 else `#10B981`
- Group total row: bold, background `#161B22`, column C text `#8B949E`, column D `#39C5BB`
- Column widths: A=180, B=150, C=200, D=140
- Number format on column D: `#,##0.00 "ج"`
- All text right-aligned

---

## Implementation Rules

### Sheet management
- On every export: delete all 3 worksheets if they exist, then recreate them in order:
  `["📊 الملخص", "👤 العملاء", "🏷️ المجموعات"]`
- Never append to existing data — always full overwrite
- Delete the default "Sheet1" if it exists

### API efficiency
- Write all cell values with a single `worksheet.update(values, range)` call per sheet
- Collect ALL formatting requests into one list and send via a single `spreadsheet.batch_update()` call per sheet
- Do not loop over individual cells for formatting

### `get_export_data()` changes (in `dal_customers.py`)
Update the function to return:
```python
{
  "ungrouped": [
    {
      "id": int, "name": str, "phone": str, "total_debt": float,
      "transactions": [{"date": str, "service": str, "amount": float}]
    }
  ],
  "groups": [
    {
      "id": int, "name": str, "total_debt": float,
      "members": [
        {
          "name": str, "phone": str, "total_debt": float,
          "transactions": [{"date": str, "service": str, "amount": float}]
        }
      ]
    }
  ],
  "all_customers": [
    {"name": str, "phone": str, "group_name": str, "total_debt": float}
  ]
}
```
- `transactions` = only `payment_status = 'pending'` rows
- `all_customers` = everyone with `total_debt != 0`, sorted by `total_debt DESC`
- Only include groups that have at least one member with debt or pending transactions
- `date` field format: `YYYY-MM-DD HH:MM`

### Helper: hex_to_sheets_color
Add this helper inside `google_sheets.py`:
```python
def _hex_to_rgb(hex_color: str) -> dict:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return {"red": r/255, "green": g/255, "blue": b/255}
```

### Error handling
- Wrap the entire export in try/except
- On any gspread or google-auth exception: `print(traceback.format_exc(), file=sys.stderr)` then re-raise
- The UI (`_export_to_sheets` in `dashboard.py`) already handles showing the error to the user — don't add QMessageBox here

### Return value
`export_to_sheets(data)` must return the full spreadsheet URL as a string.

---

## Constraints
- No PyQt6 imports in `utils/google_sheets.py`
- No SQL in any UI file
- No hardcoded paths — resolve `credentials.json` via `Path(__file__).parent.parent / "credentials.json"`
- Do not modify any existing DAL function signatures other than `get_export_data()`
- Do not add new keys to `COLORS` in `theme.py` — the hex values above are used directly in `google_sheets.py` only
- All identifiers English, all string literals Arabic
