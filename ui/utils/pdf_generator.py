"""
pdf_generator.py — توليد كشف حساب PDF للعميل
Professional Arabic financial statement.
  Primary path : WeasyPrint (requires GTK+ runtime on Windows)
  Fallback path: fpdf2  (pure-Python, no system dependencies)
"""

import os
import tempfile
from datetime import datetime

OWNER_NAME = "السعيد سيف"
OWNER_PHONE = "01098974588"
OWNER_ADDRESS = "منية سمنود - أجا"

_WINDOWS_FONTS = r"C:\Windows\Fonts"
_FONT_REGULAR = os.path.join(_WINDOWS_FONTS, "tahoma.ttf")
_FONT_BOLD = os.path.join(_WINDOWS_FONTS, "tahomabd.ttf")


# ── helpers ────────────────────────────────────────────────────────


def _fmt(amount) -> str:
    if amount is None:
        return "0.00"
    try:
        return f"{float(amount):,.2f}"
    except (TypeError, ValueError):
        return "0.00"


def _ar(text: str) -> str:
    """Reshape + bidi-reorder Arabic text for fpdf2 cells."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except ImportError:
        return str(text)


def _balance_box_props(balance: float) -> tuple[str, str, str, str, str]:
    """Return (label, bg, text_color, border_color, value_str) for balance box."""
    if balance > 0.005:
        return (
            "الرصيد الإجمالي — عليه",
            "#f8d7da", "#721c24", "#f5c6cb",
            f"{_fmt(balance)} ج",
        )
    if balance < -0.005:
        return (
            "الرصيد الإجمالي — له",
            "#d4edda", "#155724", "#c3e6cb",
            f"{_fmt(abs(balance))} ج",
        )
    return (
        "الرصيد الإجمالي — متوازن",
        "#e2e3e5", "#383d41", "#d6d8db",
        "0.00 ج",
    )


# ── Main class ─────────────────────────────────────────────────────


class PDFGenerator:
    def __init__(self, customer_data: dict):
        self.customer = customer_data.get("customer", {})
        self.transactions = sorted(
            customer_data.get("transactions", []),
            key=lambda t: t.get("created_at", ""),
        )
        self.payments = sorted(
            customer_data.get("payments", []),
            key=lambda p: p.get("created_at", ""),
        )
        self.totals = customer_data.get("totals", {})

    # ── public entry point ─────────────────────────────────────────

    def generate(self, output_path: str = None) -> str:
        try:
            from weasyprint import HTML as _WP
            return self._wp_generate(_WP, output_path)
        except (ImportError, OSError):
            return self._fpdf_generate(output_path)

    # ── shared ledger computation ──────────────────────────────────

    def _compute_ledger_rows(self) -> tuple[list[dict], float]:
        all_entries: list[dict] = []
        for t in self.transactions:
            op = t.get("operation_type", "")
            if op not in ("outbound", "inbound"):
                continue
            service  = t.get("service_name") or "—"
            platform = t.get("platform_name") or ""
            if op == "outbound":
                details = f"{service} ({platform})" if platform else service
                all_entries.append({
                    "created_at": t.get("created_at", ""),
                    "date":       (t.get("created_at") or "")[:10],
                    "details":    details,
                    "debit":      float(t.get("amount_required") or 0),
                    "credit":     0.0,
                })
            else:
                all_entries.append({
                    "created_at": t.get("created_at", ""),
                    "date":       (t.get("created_at") or "")[:10],
                    "details":    "دفعة من العميل",
                    "debit":      0.0,
                    "credit":     float(t.get("amount_spent") or 0),
                })

        for p in self.payments:
            all_entries.append({
                "created_at": p.get("created_at", ""),
                "date":       (p.get("created_at") or "")[:10],
                "details":    "تسديد سريع",
                "debit":      0.0,
                "credit":     float(p.get("amount") or 0),
            })

        all_entries.sort(key=lambda e: e["created_at"])

        rows: list[dict] = []
        balance = 0.0
        for e in all_entries:
            balance += e["debit"] - e["credit"]
            rows.append({
                "date":    e["date"],
                "details": e["details"],
                "debit":   e["debit"],
                "credit":  e["credit"],
                "balance": balance,
            })
        return rows, balance

    def _temp_path(self, ext: str = "pdf") -> str:
        safe_name = (self.customer.get("name") or "customer").replace(" ", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(tempfile.gettempdir(), f"كشف_حساب_{safe_name}_{ts}.{ext}")

    # ══════════════════════════════════════════════════════════════
    #  WeasyPrint path
    # ══════════════════════════════════════════════════════════════

    def _wp_generate(self, HTML, output_path: str) -> str:
        path = output_path or self._temp_path()
        HTML(string=self._build_html(), base_url=".").write_pdf(path)
        return path

    def _build_html(self) -> str:
        rows, final_balance = self._compute_ledger_rows()
        name = self.customer.get("name", "—")
        phone = self.customer.get("phone") or "—"
        group = self.customer.get("group_name") or "بدون مجموعة"
        now = datetime.now().strftime("%Y-%m-%d  %H:%M")
        total_debit = sum(r["debit"] for r in rows)
        total_credit = sum(r["credit"] for r in rows)
        rows_html = self._html_rows(rows)
        box_label, box_bg, box_color, box_border, box_value = _balance_box_props(final_balance)

        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>كشف حساب — {name}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

@page {{
  margin: 15mm;
  @bottom-center {{
    content: "صفحة " counter(page) " من " counter(pages);
    font-family: Cairo, 'Simplified Arabic', Arial, sans-serif;
    font-size: 8pt; color: #888;
  }}
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: Cairo, 'Simplified Arabic', 'Arabic Typesetting', Arial, sans-serif;
  font-size: 10pt; color: #2c3e50;
  direction: rtl; unicode-bidi: embed; background: #fff;
}}

.page-header {{
  width: 100%; border-bottom: 3px solid #2c3e50;
  padding-bottom: 12px; margin-bottom: 14px; overflow: hidden;
}}
.header-right {{ float: right; text-align: right; }}
.header-left  {{ float: left;  text-align: center; }}
.owner-name   {{ display: block; font-size: 15pt; font-weight: 900; color: #2c3e50; }}
.owner-detail {{ display: block; font-size: 9pt; color: #555; margin-top: 3px; }}
.logo-box {{
  width: 80px; height: 60px; background: #2c3e50; border-radius: 8px;
  color: white; font-size: 8.5pt; font-weight: bold;
  text-align: center; line-height: 1.5; padding: 8px 4px;
}}

.report-title {{
  text-align: center; font-size: 15pt; font-weight: 900;
  color: #2c3e50; margin: 12px 0 4px;
}}
.report-sub {{ text-align: center; font-size: 8.5pt; color: #777; margin-bottom: 12px; }}

.info-bar {{
  background: #f4f6f8; border: 1px solid #dee2e6; border-radius: 6px;
  padding: 9px 14px; margin-bottom: 14px; overflow: hidden;
}}
.info-item {{ float: right; margin-left: 28px; font-size: 9.5pt; color: #444; }}
.info-item strong {{ color: #2c3e50; }}

table {{ width: 100%; border-collapse: collapse; direction: rtl; unicode-bidi: embed; }}
thead tr {{ background: #2c3e50; color: white; }}
thead th {{
  padding: 10px 8px; font-size: 10.5pt; font-weight: bold;
  text-align: center; border: 1px solid #2c3e50;
}}
tbody td {{
  padding: 7px 8px; font-size: 10pt;
  border: 1px solid #ddd; text-align: center;
}}
tbody tr:nth-child(even) {{ background: #f9f9f9; }}

td.details-cell {{ text-align: right; padding-right: 10px; }}
td.amount {{ font-family: 'Courier New', monospace; font-size: 9.5pt; }}
.bal-debit  {{ color: #c0392b; font-weight: bold; }}
.bal-credit {{ color: #27ae60; font-weight: bold; }}

.totals-row {{ background: #eaf0fb !important; }}
.totals-row td {{ font-size: 10.5pt; font-weight: bold; color: #2c3e50; border-top: 2px solid #2c3e50; }}
.totals-label {{ text-align: right; padding-right: 10px; }}

.balance-box {{
  margin-top: 18px; padding: 14px 20px;
  background: {box_bg}; border: 2px solid {box_border};
  border-radius: 8px; overflow: hidden;
}}
.balance-label {{ float: right; font-size: 13pt; font-weight: 900; color: {box_color}; }}
.balance-value {{ float: left; font-size: 16pt; font-weight: 900; color: {box_color}; }}

.footer-note {{
  margin-top: 14px; text-align: center; font-size: 8pt; color: #aaa;
  border-top: 1px solid #eee; padding-top: 8px;
}}
</style>
</head>
<body>

<div class="page-header">
  <div class="header-right">
    <span class="owner-name">{OWNER_NAME}</span>
    <span class="owner-detail">📍 {OWNER_ADDRESS}</span>
    <span class="owner-detail">📞 {OWNER_PHONE}</span>
  </div>
  <div class="header-left">
    <div class="logo-box">نظام<br/>إدارة<br/>المدفوعات</div>
  </div>
</div>

<div class="report-title">كشف حساب: {name}</div>
<div class="report-sub">تاريخ التقرير: {now}</div>

<div class="info-bar">
  <span class="info-item"><strong>المجموعة:</strong> {group}</span>
  <span class="info-item"><strong>التليفون:</strong> {phone}</span>
  <span class="info-item"><strong>العميل:</strong> {name}</span>
</div>

<table>
  <thead>
    <tr>
      <th style="width:13%">التاريخ</th>
      <th style="width:36%">التفاصيل</th>
      <th style="width:17%">عليه (مدين)</th>
      <th style="width:17%">له (دائن)</th>
      <th style="width:17%">الرصيد</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
    <tr class="totals-row">
      <td colspan="2" class="totals-label">إجمالي العمليات</td>
      <td class="amount">{_fmt(total_debit)}</td>
      <td class="amount">{_fmt(total_credit)}</td>
      <td></td>
    </tr>
  </tbody>
</table>

<div class="balance-box">
  <span class="balance-label">{box_label}</span>
  <span class="balance-value">{box_value}</span>
</div>

<div class="footer-note">
  تم إنشاء هذا التقرير بواسطة نظام إدارة المدفوعات — {OWNER_NAME} — {OWNER_ADDRESS}
</div>

</body>
</html>"""

    def _html_rows(self, rows: list[dict]) -> str:
        if not rows:
            return (
                '<tr><td colspan="5" style="text-align:center;color:#888;padding:16px;">'
                "لا توجد عمليات</td></tr>"
            )
        html = ""
        for r in rows:
            d = _fmt(r["debit"]) if r["debit"] else "—"
            c = _fmt(r["credit"]) if r["credit"] else "—"
            b = r["balance"]
            if b > 0.005:
                b_class, b_str = "bal-debit", _fmt(b)
            elif b < -0.005:
                b_class, b_str = "bal-credit", f"({_fmt(abs(b))})"
            else:
                b_class, b_str = "", "0.00"
            html += f"""
    <tr>
      <td>{r['date']}</td>
      <td class="details-cell">{r['details']}</td>
      <td class="amount">{d}</td>
      <td class="amount">{c}</td>
      <td class="amount {b_class}">{b_str}</td>
    </tr>"""
        return html

    # ══════════════════════════════════════════════════════════════
    #  fpdf2 fallback path
    # ══════════════════════════════════════════════════════════════

    def _fpdf_generate(self, output_path: str) -> str:
        from fpdf import FPDF

        rows, final_balance = self._compute_ledger_rows()
        name = self.customer.get("name", "—")
        phone = self.customer.get("phone") or "—"
        group = self.customer.get("group_name") or "بدون مجموعة"
        now = datetime.now().strftime("%Y-%m-%d  %H:%M")
        total_debit = sum(r["debit"] for r in rows)
        total_credit = sum(r["credit"] for r in rows)
        box_label, box_bg_hex, box_color_hex, _, box_value = _balance_box_props(final_balance)

        # ── Parse CSS hex colours to RGB tuples ──
        def hex_rgb(h: str) -> tuple[int, int, int]:
            h = h.lstrip("#")
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        box_bg_rgb = hex_rgb(box_bg_hex)
        box_txt_rgb = hex_rgb(box_color_hex)

        # Column widths (portrait A4: 180mm usable)
        # Visual RTL order: التاريخ | التفاصيل | عليه | له | الرصيد
        # PDF LTR order  :  الرصيد  |   له    | عليه | التفاصيل | التاريخ
        CW = {
            "balance": 28,
            "credit":  28,
            "debit":   28,
            "details": 69,
            "date":    27,
        }  # total = 180 mm

        # ── Custom FPDF class with footer ──
        class _ArabicPDF(FPDF):
            def footer(self_inner):  # noqa: N805
                self_inner.set_y(-12)
                self_inner.set_font("Tahoma", "", 8)
                self_inner.set_text_color(150, 150, 150)
                pg = _ar("صفحة") + f"  {self_inner.page_no()}  " + _ar("من") + "  {nb}"
                self_inner.cell(0, 5, pg, align="C")

        pdf = _ArabicPDF(unit="mm", format="A4")
        pdf.alias_nb_pages("{nb}")
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.set_margins(15, 15, 15)

        # Register fonts (Tahoma has solid Arabic glyph coverage)
        pdf.add_font("Tahoma", "",  _FONT_REGULAR, uni=True)
        pdf.add_font("Tahoma", "B", _FONT_BOLD,    uni=True)

        pdf.add_page()

        # ── Dark header banner ──────────────────────────────────
        pdf.set_fill_color(44, 62, 80)
        pdf.rect(15, 10, 180, 20, style="F")
        pdf.set_text_color(255, 255, 255)

        pdf.set_font("Tahoma", "B", 11)
        pdf.set_xy(15, 12)
        pdf.cell(180, 7, _ar(f"نظام إدارة المدفوعات — {OWNER_NAME}"), align="C", ln=1)

        pdf.set_font("Tahoma", "", 8)
        pdf.set_xy(15, 20)
        pdf.cell(180, 6, _ar(f"{OWNER_ADDRESS}    |    {OWNER_PHONE}"), align="C", ln=1)

        pdf.set_text_color(0, 0, 0)

        # ── Report title ────────────────────────────────────────
        pdf.set_xy(15, 36)
        pdf.set_font("Tahoma", "B", 13)
        pdf.cell(180, 8, _ar(f"كشف حساب: {name}"), align="C", ln=1)

        pdf.set_font("Tahoma", "", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(180, 5, _ar(f"تاريخ التقرير: {now}"), align="C", ln=1)
        pdf.set_text_color(0, 0, 0)

        # ── Customer info bar ───────────────────────────────────
        bar_y = pdf.get_y() + 3
        pdf.set_fill_color(244, 246, 248)
        pdf.set_draw_color(222, 226, 230)
        pdf.rect(15, bar_y, 180, 9, style="FD")
        pdf.set_font("Tahoma", "", 9)
        info = _ar(f"المجموعة: {group}") + "    |    " + _ar(f"التليفون: {phone}") + "    |    " + _ar(f"العميل: {name}")
        pdf.set_xy(15, bar_y + 1.5)
        pdf.cell(180, 6, info, align="C")
        pdf.set_draw_color(0, 0, 0)

        # ── Table ───────────────────────────────────────────────
        pdf.set_xy(15, bar_y + 13)

        def draw_table_header():
            pdf.set_fill_color(44, 62, 80)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Tahoma", "B", 9.5)
            # RTL visual order drawn LTR in PDF coordinates
            for key, label in [
                ("balance", "الرصيد"),
                ("credit",  "له (دائن)"),
                ("debit",   "عليه (مدين)"),
                ("details", "التفاصيل"),
                ("date",    "التاريخ"),
            ]:
                pdf.cell(CW[key], 9, _ar(label), border=1, align="C", fill=True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0)

        draw_table_header()

        ROW_H = 7.5
        fill = False
        pdf.set_font("Tahoma", "", 9)

        for r in rows:
            if pdf.get_y() > pdf.h - 35:
                pdf.add_page()
                pdf.set_xy(15, 15)
                draw_table_header()
                pdf.set_font("Tahoma", "", 9)

            pdf.set_fill_color(249, 249, 249) if fill else pdf.set_fill_color(255, 255, 255)
            fill = not fill

            d = _fmt(r["debit"]) if r["debit"] else "—"
            c = _fmt(r["credit"]) if r["credit"] else "—"
            b = r["balance"]
            if b > 0.005:
                b_str = _fmt(b)
                pdf.set_text_color(192, 57, 43)
            elif b < -0.005:
                b_str = f"({_fmt(abs(b))})"
                pdf.set_text_color(39, 174, 96)
            else:
                b_str = "0.00"
                pdf.set_text_color(80, 80, 80)

            pdf.cell(CW["balance"], ROW_H, b_str, border=1, align="C", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(CW["credit"],  ROW_H, c,    border=1, align="C", fill=True)
            pdf.cell(CW["debit"],   ROW_H, d,    border=1, align="C", fill=True)
            pdf.cell(CW["details"], ROW_H, _ar(r["details"]), border=1, align="R", fill=True)
            pdf.cell(CW["date"],    ROW_H, r["date"],         border=1, align="C", fill=True)
            pdf.ln()

        # ── Totals row ──────────────────────────────────────────
        pdf.set_fill_color(234, 240, 251)
        pdf.set_text_color(44, 62, 80)
        pdf.set_font("Tahoma", "B", 9.5)
        pdf.cell(CW["balance"], ROW_H, "",               border=1, align="C", fill=True)
        pdf.cell(CW["credit"],  ROW_H, _fmt(total_credit), border=1, align="C", fill=True)
        pdf.cell(CW["debit"],   ROW_H, _fmt(total_debit),  border=1, align="C", fill=True)
        pdf.cell(CW["details"] + CW["date"], ROW_H, _ar("إجمالي العمليات"),
                 border=1, align="R", fill=True)
        pdf.ln()
        pdf.set_text_color(0, 0, 0)

        # ── Final balance box ────────────────────────────────────
        box_y = pdf.get_y() + 5
        if box_y > pdf.h - 35:
            pdf.add_page()
            box_y = 15

        pdf.set_fill_color(*box_bg_rgb)
        pdf.set_draw_color(*box_txt_rgb)
        pdf.rect(15, box_y, 180, 16, style="FD")

        pdf.set_text_color(*box_txt_rgb)
        pdf.set_font("Tahoma", "B", 11)
        pdf.set_xy(15, box_y + 3)
        pdf.cell(90, 10, _ar(box_label), align="R")

        pdf.set_font("Tahoma", "B", 13)
        pdf.set_xy(105, box_y + 3)
        pdf.cell(90, 10, box_value, align="L")

        pdf.set_draw_color(0, 0, 0)
        pdf.set_text_color(0, 0, 0)

        # ── Save ─────────────────────────────────────────────────
        path = output_path or self._temp_path()
        pdf.output(path)
        return path


# ══════════════════════════════════════════════════════════════════
#  GroupPDFGenerator — تقرير إجمالي المجموعة
# ══════════════════════════════════════════════════════════════════


class GroupPDFGenerator:
    """Generates a group summary PDF: all members + balances + grand total."""

    def __init__(self, group_data: dict):
        self.group = group_data.get("group", {})
        self.members = group_data.get("members", [])
        self.total_balance = float(group_data.get("total_balance", 0))

    # ── public entry point ─────────────────────────────────────────

    def generate(self, output_path: str = None) -> str:
        try:
            from weasyprint import HTML as _WP
            return self._wp_generate(_WP, output_path)
        except (ImportError, OSError):
            return self._fpdf_generate(output_path)

    def _temp_path(self, ext: str = "pdf") -> str:
        safe = (self.group.get("name") or "group").replace(" ", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(tempfile.gettempdir(), f"تقرير_مجموعة_{safe}_{ts}.{ext}")

    # ══════════════════════════════════════════════════════════════
    #  WeasyPrint path
    # ══════════════════════════════════════════════════════════════

    def _wp_generate(self, HTML, output_path: str) -> str:
        path = output_path or self._temp_path()
        HTML(string=self._build_html(), base_url=".").write_pdf(path)
        return path

    def _build_html(self) -> str:
        group_name = self.group.get("name", "—")
        now = datetime.now().strftime("%Y-%m-%d  %H:%M")
        rows_html = self._html_rows()
        box_label, box_bg, box_color, box_border, box_value = _balance_box_props(self.total_balance)
        member_count = len(self.members)

        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>تقرير مجموعة — {group_name}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

@page {{
  margin: 15mm;
  @bottom-center {{
    content: "صفحة " counter(page) " من " counter(pages);
    font-family: Cairo, 'Simplified Arabic', Arial, sans-serif;
    font-size: 8pt; color: #888;
  }}
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: Cairo, 'Simplified Arabic', 'Arabic Typesetting', Arial, sans-serif;
  font-size: 10pt; color: #2c3e50;
  direction: rtl; unicode-bidi: embed; background: #fff;
}}

.page-header {{
  width: 100%; border-bottom: 3px solid #2c3e50;
  padding-bottom: 12px; margin-bottom: 14px; overflow: hidden;
}}
.header-right {{ float: right; text-align: right; }}
.header-left  {{ float: left;  text-align: center; }}
.owner-name   {{ display: block; font-size: 15pt; font-weight: 900; color: #2c3e50; }}
.owner-detail {{ display: block; font-size: 9pt; color: #555; margin-top: 3px; }}
.logo-box {{
  width: 80px; height: 60px; background: #2c3e50; border-radius: 8px;
  color: white; font-size: 8.5pt; font-weight: bold;
  text-align: center; line-height: 1.5; padding: 8px 4px;
}}

.report-title {{
  text-align: center; font-size: 15pt; font-weight: 900;
  color: #1a56db; margin: 12px 0 4px;
}}
.report-sub {{ text-align: center; font-size: 8.5pt; color: #777; margin-bottom: 12px; }}

.info-bar {{
  background: #e8f0fe; border: 1px solid #c2d4f8; border-radius: 6px;
  padding: 9px 14px; margin-bottom: 14px; overflow: hidden;
}}
.info-item {{ float: right; margin-left: 28px; font-size: 9.5pt; color: #1a3a6e; }}
.info-item strong {{ color: #1a56db; }}

table {{ width: 100%; border-collapse: collapse; direction: rtl; unicode-bidi: embed; }}

thead tr {{ background: #e8f0fe; }}
thead th {{
  padding: 10px 10px; font-size: 10.5pt; font-weight: bold;
  text-align: center; border: 1px solid #c2d4f8; color: #1a56db;
}}

tbody td {{
  padding: 9px 10px; font-size: 10pt;
  border: 1px solid #e0e0e0; text-align: center;
}}
tbody tr:nth-child(even) {{ background: #f8f9fa; }}

td.name-cell {{ text-align: right; padding-right: 14px; font-weight: 600; }}
td.amount    {{ font-family: 'Courier New', monospace; font-size: 9.5pt; }}
td.type-owed  {{ color: #c0392b; font-weight: bold; }}
td.type-owned {{ color: #27ae60; font-weight: bold; }}
td.type-zero  {{ color: #888; }}

.totals-row {{ background: #eaf0fb !important; }}
.totals-row td {{
  font-size: 10.5pt; font-weight: bold;
  color: #2c3e50; border-top: 2px solid #1a56db;
}}

.balance-box {{
  margin-top: 18px; padding: 14px 20px;
  background: {box_bg}; border: 2px solid {box_border};
  border-radius: 8px; overflow: hidden;
}}
.balance-label {{ float: right; font-size: 13pt; font-weight: 900; color: {box_color}; }}
.balance-value {{ float: left; font-size: 16pt; font-weight: 900; color: {box_color}; }}

.footer-note {{
  margin-top: 14px; text-align: center; font-size: 8pt; color: #aaa;
  border-top: 1px solid #eee; padding-top: 8px;
}}
</style>
</head>
<body>

<div class="page-header">
  <div class="header-right">
    <span class="owner-name">{OWNER_NAME}</span>
    <span class="owner-detail">📍 {OWNER_ADDRESS}</span>
    <span class="owner-detail">📞 {OWNER_PHONE}</span>
  </div>
  <div class="header-left">
    <div class="logo-box">نظام<br/>إدارة<br/>المدفوعات</div>
  </div>
</div>

<div class="report-title">إجمالي المبالغ — {group_name}</div>
<div class="report-sub">تاريخ التقرير: {now}</div>

<div class="info-bar">
  <span class="info-item"><strong>عدد الأعضاء:</strong> {member_count} عضو</span>
  <span class="info-item"><strong>المجموعة:</strong> {group_name}</span>
</div>

<table>
  <thead>
    <tr>
      <th style="width:35%">اسم الحساب</th>
      <th style="width:22%">الرصيد</th>
      <th style="width:15%">نوع الحساب</th>
      <th style="width:28%">التاريخ</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
    <tr class="totals-row">
      <td colspan="3" style="text-align:right;padding-right:14px;">إجمالي المجموعة</td>
      <td class="amount">{_fmt(abs(self.total_balance))} ج</td>
    </tr>
  </tbody>
</table>

<div class="balance-box">
  <span class="balance-label">{box_label}</span>
  <span class="balance-value">{box_value}</span>
</div>

<div class="footer-note">
  تم إنشاء هذا التقرير بواسطة نظام إدارة المدفوعات — {OWNER_NAME} — {OWNER_ADDRESS}
</div>

</body>
</html>"""

    def _html_rows(self) -> str:
        if not self.members:
            return (
                '<tr><td colspan="4" style="text-align:center;color:#888;padding:16px;">'
                "لا يوجد أعضاء في هذه المجموعة</td></tr>"
            )
        html = ""
        for m in self.members:
            debt = float(m.get("total_debt") or 0)
            balance_str = f"{_fmt(abs(debt))} ج"
            last = m.get("last_activity") or "—"

            if debt > 0.005:
                type_class = "type-owed"
                type_label = "عليه"
            elif debt < -0.005:
                type_class = "type-owned"
                type_label = "له"
            else:
                type_class = "type-zero"
                type_label = "صفر"
                balance_str = "—"

            html += f"""
    <tr>
      <td class="name-cell">{m.get('name', '—')}</td>
      <td class="amount">{balance_str}</td>
      <td class="{type_class}">{type_label}</td>
      <td>{last}</td>
    </tr>"""
        return html

    # ══════════════════════════════════════════════════════════════
    #  fpdf2 fallback path
    # ══════════════════════════════════════════════════════════════

    def _fpdf_generate(self, output_path: str) -> str:
        from fpdf import FPDF

        group_name = self.group.get("name", "—")
        now = datetime.now().strftime("%Y-%m-%d  %H:%M")
        box_label, box_bg_hex, box_color_hex, _, box_value = _balance_box_props(self.total_balance)

        def hex_rgb(h: str) -> tuple[int, int, int]:
            h = h.lstrip("#")
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        box_bg_rgb = hex_rgb(box_bg_hex)
        box_txt_rgb = hex_rgb(box_color_hex)

        # Column widths — portrait A4 (180mm usable)
        # RTL visual: اسم الحساب | الرصيد | نوع الحساب | التاريخ
        # PDF LTR   : التاريخ   | نوع الحساب | الرصيد | اسم الحساب
        CW = {"date": 35, "acct_type": 22, "balance": 38, "name": 85}  # 180mm

        class _ArabicPDF(FPDF):
            def footer(self_inner):  # noqa: N805
                self_inner.set_y(-12)
                self_inner.set_font("Tahoma", "", 8)
                self_inner.set_text_color(150, 150, 150)
                pg = _ar("صفحة") + f"  {self_inner.page_no()}  " + _ar("من") + "  {nb}"
                self_inner.cell(0, 5, pg, align="C")

        pdf = _ArabicPDF(unit="mm", format="A4")
        pdf.alias_nb_pages("{nb}")
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.set_margins(15, 15, 15)
        pdf.add_font("Tahoma", "",  _FONT_REGULAR, uni=True)
        pdf.add_font("Tahoma", "B", _FONT_BOLD,    uni=True)
        pdf.add_page()

        # ── Dark header banner ──
        pdf.set_fill_color(44, 62, 80)
        pdf.rect(15, 10, 180, 20, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Tahoma", "B", 11)
        pdf.set_xy(15, 12)
        pdf.cell(180, 7, _ar(f"نظام إدارة المدفوعات — {OWNER_NAME}"), align="C", ln=1)
        pdf.set_font("Tahoma", "", 8)
        pdf.set_xy(15, 20)
        pdf.cell(180, 6, _ar(f"{OWNER_ADDRESS}    |    {OWNER_PHONE}"), align="C", ln=1)
        pdf.set_text_color(0, 0, 0)

        # ── Report title (blue) ──
        pdf.set_xy(15, 36)
        pdf.set_font("Tahoma", "B", 13)
        pdf.set_text_color(26, 86, 219)
        pdf.cell(180, 8, _ar(f"إجمالي المبالغ — {group_name}"), align="C", ln=1)
        pdf.set_font("Tahoma", "", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(180, 5, _ar(f"تاريخ التقرير: {now}"), align="C", ln=1)
        pdf.set_text_color(0, 0, 0)

        # ── Info bar (light blue) ──
        bar_y = pdf.get_y() + 3
        pdf.set_fill_color(232, 240, 254)
        pdf.set_draw_color(194, 212, 248)
        pdf.rect(15, bar_y, 180, 9, style="FD")
        pdf.set_font("Tahoma", "", 9)
        pdf.set_text_color(26, 58, 110)
        info = _ar(f"عدد الأعضاء: {len(self.members)} عضو") + "    |    " + _ar(f"المجموعة: {group_name}")
        pdf.set_xy(15, bar_y + 1.5)
        pdf.cell(180, 6, info, align="C")
        pdf.set_draw_color(0, 0, 0)
        pdf.set_text_color(0, 0, 0)

        # ── Table ──
        pdf.set_xy(15, bar_y + 13)

        def draw_header():
            pdf.set_fill_color(232, 240, 254)
            pdf.set_text_color(26, 86, 219)
            pdf.set_font("Tahoma", "B", 9.5)
            for key, label in [
                ("date",      "التاريخ"),
                ("acct_type", "نوع الحساب"),
                ("balance",   "الرصيد"),
                ("name",      "اسم الحساب"),
            ]:
                pdf.cell(CW[key], 9, _ar(label), border=1, align="C", fill=True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0)

        draw_header()

        ROW_H = 8.0
        fill = False
        pdf.set_font("Tahoma", "", 9)

        for m in self.members:
            if pdf.get_y() > pdf.h - 35:
                pdf.add_page()
                pdf.set_xy(15, 15)
                draw_header()
                pdf.set_font("Tahoma", "", 9)

            pdf.set_fill_color(248, 249, 250) if fill else pdf.set_fill_color(255, 255, 255)
            fill = not fill

            debt = float(m.get("total_debt") or 0)
            last = m.get("last_activity") or "—"
            name_str = m.get("name", "—")

            if debt > 0.005:
                bal_str = f"{_fmt(debt)} ج"
                type_str = _ar("عليه")
                pdf.set_text_color(192, 57, 43)
            elif debt < -0.005:
                bal_str = f"{_fmt(abs(debt))} ج"
                type_str = _ar("له")
                pdf.set_text_color(39, 174, 96)
            else:
                bal_str = "—"
                type_str = _ar("صفر")
                pdf.set_text_color(150, 150, 150)

            pdf.cell(CW["date"],      ROW_H, last,     border=1, align="C", fill=True)
            pdf.set_text_color(0, 0, 0) if debt == 0 else None

            # Draw type cell with colored text
            type_color = (192, 57, 43) if debt > 0.005 else (39, 174, 96) if debt < -0.005 else (150, 150, 150)
            pdf.set_text_color(*type_color)
            pdf.cell(CW["acct_type"], ROW_H, type_str,  border=1, align="C", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(CW["balance"],   ROW_H, bal_str,   border=1, align="C", fill=True)
            pdf.set_font("Tahoma", "B", 9)
            pdf.cell(CW["name"],      ROW_H, _ar(name_str), border=1, align="R", fill=True)
            pdf.set_font("Tahoma", "", 9)
            pdf.ln()

        # ── Totals row ──
        pdf.set_fill_color(234, 240, 251)
        pdf.set_text_color(44, 62, 80)
        pdf.set_font("Tahoma", "B", 9.5)
        pdf.cell(CW["date"] + CW["acct_type"], ROW_H,
                 _fmt(abs(self.total_balance)) + " ج", border=1, align="C", fill=True)
        pdf.cell(CW["balance"], ROW_H, "", border=1, fill=True)
        pdf.cell(CW["name"], ROW_H, _ar("إجمالي المجموعة"), border=1, align="R", fill=True)
        pdf.ln()
        pdf.set_text_color(0, 0, 0)

        # ── Final balance box ──
        box_y = pdf.get_y() + 5
        if box_y > pdf.h - 35:
            pdf.add_page()
            box_y = 15

        pdf.set_fill_color(*box_bg_rgb)
        pdf.set_draw_color(*box_txt_rgb)
        pdf.rect(15, box_y, 180, 16, style="FD")
        pdf.set_text_color(*box_txt_rgb)
        pdf.set_font("Tahoma", "B", 11)
        pdf.set_xy(15, box_y + 3)
        pdf.cell(90, 10, _ar(box_label), align="R")
        pdf.set_font("Tahoma", "B", 13)
        pdf.set_xy(105, box_y + 3)
        pdf.cell(90, 10, box_value, align="L")
        pdf.set_draw_color(0, 0, 0)
        pdf.set_text_color(0, 0, 0)

        path = output_path or self._temp_path()
        pdf.output(path)
        return path
