"""
statement_screen.py — كشف حساب العميل (واجهة محسّنة)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFileDialog, QMessageBox,
    QWidget, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database as db
from ui.components.widgets import DataTable
from ui.styles.theme import COLORS
from utils.formatters import fmt_currency


# ══════════════════════════════════════════
#  Mini Info Pill
# ══════════════════════════════════════════

def info_pill(label: str, value: str, color: str = None) -> QFrame:
    """خانة معلومة صغيرة (label + value)"""
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 10, 14, 10)
    layout.setSpacing(3)

    val_lbl = QLabel(value)
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
    val_lbl.setStyleSheet(
        f"color:{color or COLORS['text_primary']};font-size:17px;font-weight:bold;"
    )
    layout.addWidget(val_lbl)

    lbl = QLabel(label)
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
    lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:11px;")
    layout.addWidget(lbl)

    return frame


# ══════════════════════════════════════════
#  كشف حساب العميل
# ══════════════════════════════════════════

class CustomerStatementDialog(QDialog):

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("كشف حساب")
        self.setMinimumSize(1050, 700)
        self._filter = "all"
        self._load_data()
        self._build_ui()

    def _load_data(self):
        self._data = db.get_customer_statement(self.customer_id)

    # ─── بناء الواجهة ──────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        layout.addLayout(self._make_header())
        layout.addWidget(self._make_identity_card())
        layout.addLayout(self._make_stats_row())
        layout.addWidget(self._make_table())        # الجدول أولاً
        layout.addLayout(self._make_filter_bar())   # ثم الفلتر (يستدعي _fill_table)
        layout.addWidget(self._make_summary_bar())

    # ── Header
    def _make_header(self) -> QHBoxLayout:
        row = QHBoxLayout()

        export_img = QPushButton("🖼️ صورة")
        export_img.setObjectName("btn_secondary"); export_img.setFixedHeight(32)
        export_img.clicked.connect(self._export_image)
        row.addWidget(export_img)

        export_pdf = QPushButton("📄 PDF")
        export_pdf.setObjectName("btn_secondary"); export_pdf.setFixedHeight(32)
        export_pdf.clicked.connect(self._export_pdf)
        row.addWidget(export_pdf)

        row.addStretch()

        c = self._data["customer"]
        title = QLabel(f"📋  كشف حساب  —  {c['name']}")
        title.setStyleSheet(f"color:{COLORS['text_primary']};font-size:16px;font-weight:bold;")
        row.addWidget(title)
        return row

    # ── Identity card (اسم + تليفون + مجموعة + آخر تعامل)
    def _make_identity_card(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 12, 18, 12); layout.setSpacing(0)

        c    = self._data["customer"]
        txns = self._data.get("transactions", [])

        # Name + phone + group (right side)
        info = QVBoxLayout(); info.setSpacing(4)
        name_lbl = QLabel(c.get("name", "—"))
        name_lbl.setStyleSheet(f"color:{COLORS['text_primary']};font-size:18px;font-weight:bold;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        info.addWidget(name_lbl)

        sub_row = QHBoxLayout(); sub_row.setSpacing(16)
        sub_row.addStretch()
        if c.get("phone"):
            ph = QLabel(f"📞  {c['phone']}")
            ph.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:13px;")
            sub_row.addWidget(ph)
        if c.get("group_name"):
            gr = QLabel(f"👥  {c['group_name']}")
            gr.setStyleSheet(f"color:{COLORS['blue_bright']};font-size:13px;")
            sub_row.addWidget(gr)
        info.addLayout(sub_row)

        if c.get("notes"):
            notes_lbl = QLabel(f"📝  {c['notes']}")
            notes_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
            notes_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            info.addWidget(notes_lbl)

        layout.addLayout(info)
        layout.addStretch()

        # Last transaction + count (left side)
        meta = QVBoxLayout(); meta.setSpacing(4); meta.setAlignment(Qt.AlignmentFlag.AlignLeft)
        count_lbl = QLabel(f"إجمالي العمليات: {len(txns)}")
        count_lbl.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:12px;")
        meta.addWidget(count_lbl)
        if txns:
            last_dt = (txns[0].get("created_at") or "")[:10]
            last_lbl = QLabel(f"آخر تعامل: {last_dt}")
            last_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
            meta.addWidget(last_lbl)
        layout.addLayout(meta)

        return frame

    # ── Stats row (4 أرقام رئيسية)
    def _make_stats_row(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(10)
        t = self._data.get("totals", {})
        c = self._data["customer"]

        debt = c.get("total_debt", 0) or 0
        debt_color = COLORS["red"] if debt > 0 else COLORS["green"]

        for label, value, color in [
            ("المديونية الحالية",  debt,                              debt_color),
            ("إجمالي المؤجل",    t.get("total_pending", 0) or 0,    COLORS["yellow"]),
            ("إجمالي المسدد",    t.get("total_paid",    0) or 0,    COLORS["green"]),
            ("إجمالي النقدي",    t.get("total_cash",    0) or 0,    COLORS["blue_bright"]),
            ("صافي الأرباح",     t.get("total_profit",  0) or 0,    COLORS["purple"]),
        ]:
            row.addWidget(info_pill(label, fmt_currency(value), color))

        return row

    # ── Filter bar
    def _make_filter_bar(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(8)
        row.addStretch()

        self._filter_btns = {}
        filters = [
            ("all",     "الكل 📋",   COLORS["text_secondary"]),
            ("pending", "مؤجل ⏳",   COLORS["yellow"]),
            ("paid",    "مسدد ✅",   COLORS["green"]),
            ("cash",    "نقدي 💵",   COLORS["blue_bright"]),
            ("inbound", "وارد 📥",   COLORS["purple"]),
        ]
        for key, label, color in filters:
            btn = QPushButton(label)
            btn.setFixedHeight(30); btn.setMinimumWidth(90)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._apply_filter(k))
            self._filter_btns[key] = (btn, color)
            row.addWidget(btn)

        row.addStretch()

        cleanup_btn = QPushButton("🗑️  تنظيف المسدد")
        cleanup_btn.setObjectName("btn_danger"); cleanup_btn.setFixedHeight(30)
        cleanup_btn.clicked.connect(self._cleanup)
        row.addWidget(cleanup_btn)

        self._apply_filter("all")
        return row

    def _apply_filter(self, key: str):
        self._filter = key
        for k, (btn, color) in self._filter_btns.items():
            if k == key:
                btn.setStyleSheet(
                    f"background:{COLORS['bg_selected']};color:{color};"
                    f"border:1.5px solid {color};border-radius:7px;"
                    f"font-weight:bold;font-size:12px;padding:2px 10px;"
                )
            else:
                btn.setStyleSheet(
                    f"background:{COLORS['bg_input']};color:{COLORS['text_muted']};"
                    f"border:1px solid {COLORS['border']};border-radius:7px;"
                    f"font-size:12px;padding:2px 10px;"
                )
        self._fill_table()

    # ── Table
    def _make_table(self) -> QWidget:
        columns = [
            ("التاريخ",  120), ("النوع",    75), ("الخدمة",  155),
            ("المنصة",   110), ("المصروف", 100), ("المطلوب", 100),
            ("الربح",     85), ("تسليم",    75), ("المرجع",  105),
            ("الحالة",    85), ("إجراء",   100),
        ]
        self.table = DataTable(columns)
        self.table.setMinimumHeight(300)
        return self.table

    def _fill_table(self):
        txns = self._data.get("transactions", [])

        # فلترة
        if self._filter == "pending":
            txns = [t for t in txns if t.get("payment_status") == "pending"]
        elif self._filter == "paid":
            txns = [t for t in txns if t.get("payment_status") == "paid"]
        elif self._filter == "cash":
            txns = [t for t in txns if t.get("payment_status") == "cash"]
        elif self._filter == "inbound":
            txns = [t for t in txns if t.get("operation_type") == "inbound"]

        self.table.clear_rows()
        self.table.setRowCount(len(txns))

        for row, t in enumerate(txns):
            # التاريخ
            self.table.set_cell(row, 0, (t.get("created_at") or "")[:16],
                                color=COLORS["text_muted"])

            # النوع
            op = t.get("operation_type", "")
            self.table.set_cell(row, 1,
                "📤 صادر" if op == "outbound" else "📥 وارد",
                color=COLORS["blue_bright"] if op == "outbound" else COLORS["purple"])

            self.table.set_cell(row, 2, t.get("service_name") or "—")
            self.table.set_cell(row, 3, t.get("platform_name") or "—",
                                color=COLORS["text_secondary"])
            self.table.set_cell(row, 4, fmt_currency(t.get("amount_spent",    0) or 0))
            self.table.set_cell(row, 5, fmt_currency(t.get("amount_required", 0) or 0), bold=True)

            profit = t.get("profit", 0) or 0
            self.table.set_cell(row, 6, fmt_currency(profit),
                                color=COLORS["green"] if profit >= 0 else COLORS["red"])

            # عمود تسليم الكاش (خاص بالوارد فقط)
            if op == "inbound":
                delivered = bool(t.get("is_delivered", 0))
                dlv_text  = "✅ تم" if delivered else "⏳ لا"
                dlv_color = COLORS["green"] if delivered else COLORS["yellow"]
                self.table.set_cell(row, 7, dlv_text, color=dlv_color)
            else:
                self.table.set_cell(row, 7, "—", color=COLORS["text_muted"])

            ref = "🃏 كارت" if t.get("is_card") else (t.get("reference_no") or "—")
            self.table.set_cell(row, 8, ref, color=COLORS["text_muted"])
            self.table.add_status_badge(row, 9, t.get("payment_status", ""))

            # زرار سداد
            if t.get("payment_status") == "pending":
                btn = QPushButton("✅ سداد")
                btn.setObjectName("btn_ghost"); btn.setFixedHeight(26)
                btn.clicked.connect(lambda _, tid=t["id"]: self._mark_paid(tid))
                cont = QWidget(); bl = QHBoxLayout(cont)
                bl.setContentsMargins(4, 2, 4, 2); bl.addWidget(btn)
                self.table.setCellWidget(row, 10, cont)
            else:
                self.table.set_cell(row, 10, "—", color=COLORS["text_muted"])

        if hasattr(self, "_summary_lbl"):
            total = sum(t.get("amount_required", 0) or 0 for t in txns)
            self._summary_lbl.setText(f"عرض: {len(txns)} عملية  |  إجمالي المطلوب: {fmt_currency(total)}")

    # ── Summary bar
    def _make_summary_bar(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("card"); frame.setFixedHeight(38)
        layout = QHBoxLayout(frame); layout.setContentsMargins(14, 0, 14, 0)
        self._summary_lbl = QLabel("")
        self._summary_lbl.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:11px;")
        layout.addStretch(); layout.addWidget(self._summary_lbl)
        self._fill_table()   # trigger summary update
        return frame

    # ── Actions
    def _mark_paid(self, tid: int):
        if QMessageBox.question(self, "تأكيد",
            "هل تريد تحويل هذه العملية إلى 'تم السداد'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            try:
                db.mark_as_paid(tid)
                self._load_data()
                self._fill_table()
                QMessageBox.information(self, "تم ✅", "تم تحويل العملية إلى مسددة")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _cleanup(self):
        if QMessageBox.question(self, "تنظيف المسدد",
            "هل تريد حذف كل العمليات المسددة لهذا العميل؟\n⚠️ لا يمكن التراجع.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            deleted = db.cleanup_paid_transactions(self.customer_id)
            self._load_data(); self._fill_table()
            QMessageBox.information(self, "تم ✅", f"تم حذف {deleted} عملية مسددة")

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", f"كشف_{self._data['customer']['name']}.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ✅", f"تم حفظ الصورة:\n{path}")

    def _export_pdf(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كـ PDF", f"كشف_{self._data['customer']['name']}.pdf", "PDF (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            painter = QPainter(printer)
            self.render(painter); painter.end()
            QMessageBox.information(self, "تم ✅", f"تم حفظ PDF:\n{path}")


# ══════════════════════════════════════════
#  تقرير المجموعة (unchanged)
# ══════════════════════════════════════════

class GroupReportDialog(QDialog):

    def __init__(self, group_id: int, parent=None):
        super().__init__(parent)
        self.group_id = group_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("تقرير المجموعة")
        self.setMinimumSize(750, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        export_btn = QPushButton("🖼️ حفظ كصورة")
        export_btn.setObjectName("btn_secondary")
        export_btn.clicked.connect(self._export_image)
        header.addWidget(export_btn)
        header.addStretch()

        groups = db.get_all_groups()
        group  = next((g for g in groups if g["id"] == self.group_id), {})
        title  = QLabel(f"تقرير مجموعة — {group.get('name', '—')}")
        title.setStyleSheet(f"color:{COLORS['text_primary']};font-size:16px;font-weight:bold;")
        header.addWidget(title)
        layout.addLayout(header)

        customers  = db.get_customers_by_group(self.group_id)
        total_debt = sum(c.get("total_debt", 0) or 0 for c in customers)

        columns = [("الاسم", 200), ("التليفون", 140), ("المديونية", 150), ("ملاحظات", -1)]
        self.table = DataTable(columns)
        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            debt = c.get("total_debt", 0) or 0
            self.table.set_cell(row, 0, c["name"], bold=True)
            self.table.set_cell(row, 1, c.get("phone") or "—", color=COLORS["text_secondary"])
            self.table.set_cell(row, 2, fmt_currency(debt),
                                color=COLORS["red"] if debt > 0 else COLORS["text_muted"], bold=debt > 0)
            self.table.set_cell(row, 3, c.get("notes") or "—", color=COLORS["text_muted"])
        layout.addWidget(self.table)

        total_frame = QFrame(); total_frame.setObjectName("card_highlight")
        tl = QHBoxLayout(total_frame); tl.setContentsMargins(16, 10, 16, 10)
        total_lbl = QLabel(f"إجمالي المجموعة: {fmt_currency(total_debt)}")
        total_lbl.setStyleSheet(
            f"color:{COLORS['red'] if total_debt > 0 else COLORS['green']};"
            f"font-size:16px;font-weight:bold;")
        tl.addStretch(); tl.addWidget(total_lbl)
        layout.addWidget(total_frame)

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", "تقرير_المجموعة.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ✅", f"تم حفظ الصورة:\n{path}")