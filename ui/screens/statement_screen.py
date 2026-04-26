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

        customer_stmt_btn = QPushButton("👤  كشف العميل")
        customer_stmt_btn.setObjectName("btn_success"); customer_stmt_btn.setFixedHeight(32)
        customer_stmt_btn.clicked.connect(self._open_customer_facing)
        row.addWidget(customer_stmt_btn)

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

    def _open_customer_facing(self):
        """فتح كشف الحساب المخصص للعميل (بدون أرباح)"""
        dlg = CustomerFacingStatementDialog(self.customer_id, self)
        dlg.exec()

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

    def _open_customer_facing(self):
        """فتح كشف الحساب المخصص للعميل (بدون أرباح)"""
        dlg = CustomerFacingStatementDialog(self.customer_id, self)
        dlg.exec()

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", "تقرير_المجموعة.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ✅", f"تم حفظ الصورة:\n{path}")


# ══════════════════════════════════════════
#  تقرير العميل (للطباعة / التصدير)
#  بدون أرباح — فقط ما عليه وما له
# ══════════════════════════════════════════

class ClientReportDialog(QDialog):
    """
    كشف حساب مبسط للعميل:
    - المبالغ المؤجلة عليه  (ما يجب أن يدفعه)
    - المبالغ المستحقة له   (ما سيستلمه)
    - الصافي النهائي
    بدون أي أرباح أو تفاصيل داخلية
    """

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("تقرير العميل")
        self.setMinimumSize(700, 580)
        self._data = db.get_customer_statement(customer_id)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(16)

        c    = self._data["customer"]
        txns = self._data.get("transactions", [])

        # ── Header أزرار
        btn_row = QHBoxLayout()
        save_img_btn = QPushButton("🖼️  حفظ كصورة")
        save_img_btn.setObjectName("btn_secondary")
        save_img_btn.setFixedHeight(34)
        save_img_btn.clicked.connect(self._export_image)
        btn_row.addWidget(save_img_btn)

        save_pdf_btn = QPushButton("📄  حفظ PDF")
        save_pdf_btn.setObjectName("btn_secondary")
        save_pdf_btn.setFixedHeight(34)
        save_pdf_btn.clicked.connect(self._export_pdf)
        btn_row.addWidget(save_pdf_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── هوية العميل
        id_frame = QFrame(); id_frame.setObjectName("card")
        id_layout = QHBoxLayout(id_frame)
        id_layout.setContentsMargins(18, 14, 18, 14)

        name_col = QVBoxLayout(); name_col.setSpacing(4)
        name_lbl = QLabel(c.get("name", "—"))
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']};font-size:20px;font-weight:bold;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_col.addWidget(name_lbl)
        if c.get("phone"):
            ph = QLabel(f"📞  {c['phone']}")
            ph.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:13px;")
            ph.setAlignment(Qt.AlignmentFlag.AlignRight)
            name_col.addWidget(ph)
        id_layout.addLayout(name_col)
        id_layout.addStretch()

        from datetime import datetime
        date_lbl = QLabel(f"📅  {datetime.now().strftime('%Y-%m-%d')}")
        date_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
        id_layout.addWidget(date_lbl)

        layout.addWidget(id_frame)

        # ── تحليل العمليات
        pending_txns  = [t for t in txns if t.get("payment_status") == "pending"]
        due_txns      = [t for t in txns
                         if t.get("operation_type") == "inbound"
                         and not t.get("is_delivered", 0)
                         and t.get("customer_id") == self.customer_id]

        total_pending = sum(t.get("amount_required", 0) or 0 for t in pending_txns)
        total_due     = sum(t.get("amount_spent", 0) or 0 for t in due_txns)
        net           = total_pending - total_due

        # ── قسم "عليه" (ما يجب أن يدفعه)
        if pending_txns:
            layout.addWidget(self._section_title("🔴  مبالغ مستحقة عليك", COLORS["red"]))
            layout.addWidget(self._make_txn_table(pending_txns, mode="owed"))

        # ── قسم "له" (ما سيستلمه)
        if due_txns:
            layout.addWidget(self._section_title("🟢  مبالغ مستحقة لك", COLORS["green"]))
            layout.addWidget(self._make_txn_table(due_txns, mode="due"))

        # ── لا توجد عمليات
        if not pending_txns and not due_txns:
            empty = QLabel("✅  لا توجد مبالغ مستحقة عليك أو لك")
            empty.setStyleSheet(
                f"color:{COLORS['green']};font-size:14px;"
                f"background:{COLORS['green_bg']};border-radius:8px;padding:12px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)

        layout.addStretch()

        # ── بطاقة الصافي
        layout.addWidget(self._make_net_card(total_pending, total_due, net))

    def _section_title(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{color};font-size:13px;font-weight:bold;"
            f"border-right:3px solid {color};padding-right:8px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        return lbl

    def _make_txn_table(self, txns: list, mode: str) -> QFrame:
        """
        mode='owed': جدول المبالغ عليه
        mode='due':  جدول المبالغ له
        """
        frame = QFrame(); frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(0)

        # Header row
        header = QHBoxLayout()
        for text, width in [("التاريخ", 110), ("البيان", 0), ("المبلغ", 110)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{COLORS['text_muted']};font-size:11px;font-weight:bold;"
                f"border-bottom:1px solid {COLORS['border']};padding-bottom:4px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            if width:
                lbl.setFixedWidth(width)
            else:
                lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            header.addWidget(lbl)
        layout.addLayout(header)

        # Rows
        total = 0
        for t in txns:
            row = QHBoxLayout()
            row.setContentsMargins(0, 6, 0, 6)

            # التاريخ
            date_lbl = QLabel((t.get("created_at") or "")[:10])
            date_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
            date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            date_lbl.setFixedWidth(110)
            row.addWidget(date_lbl)

            # البيان
            service = t.get("service_name") or "—"
            svc_lbl = QLabel(service)
            svc_lbl.setStyleSheet(f"color:{COLORS['text_primary']};font-size:13px;")
            svc_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            svc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row.addWidget(svc_lbl)

            # المبلغ
            if mode == "owed":
                amount = t.get("amount_required", 0) or 0
                color  = COLORS["red"]
            else:
                amount = t.get("amount_spent", 0) or 0
                color  = COLORS["green"]
            total += amount

            amt_lbl = QLabel(fmt_currency(amount))
            amt_lbl.setStyleSheet(f"color:{color};font-size:13px;font-weight:bold;")
            amt_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            amt_lbl.setFixedWidth(110)
            row.addWidget(amt_lbl)

            layout.addLayout(row)

            # فاصل خفيف
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color:{COLORS['border']};")
            layout.addWidget(sep)

        # إجمالي القسم
        total_row = QHBoxLayout()
        total_lbl = QLabel("الإجمالي:")
        total_lbl.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:12px;font-weight:bold;")
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_row.addStretch()
        total_row.addWidget(total_lbl)

        color = COLORS["red"] if mode == "owed" else COLORS["green"]
        total_val = QLabel(fmt_currency(total))
        total_val.setStyleSheet(f"color:{color};font-size:14px;font-weight:bold;")
        total_val.setFixedWidth(110)
        total_val.setAlignment(Qt.AlignmentFlag.AlignLeft)
        total_row.addWidget(total_val)
        layout.addLayout(total_row)

        return frame

    def _make_net_card(self, total_owed: float, total_due: float, net: float) -> QFrame:
        """بطاقة الصافي النهائي"""
        frame = QFrame()
        frame.setObjectName("card")

        if net > 0:
            bg    = COLORS["red_bg"]
            border= COLORS["red"]
            color = COLORS["red"]
            label = "إجمالي المبلغ المطلوب منك"
            icon  = "💳"
        elif net < 0:
            bg    = COLORS["green_bg"]
            border= COLORS["green"]
            color = COLORS["green"]
            label = "إجمالي المبلغ المستحق لك"
            icon  = "💰"
        else:
            bg    = COLORS["bg_input"]
            border= COLORS["border"]
            color = COLORS["text_secondary"]
            label = "الحساب متساوٍ"
            icon  = "✅"

        frame.setStyleSheet(
            f"QFrame#card {{ background:{bg}; border:2px solid {border}; border-radius:12px; }}"
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 18, 24, 18)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size:28px;")
        layout.addWidget(icon_lbl)

        layout.addStretch()

        text_col = QVBoxLayout(); text_col.setSpacing(4)

        amt_lbl = QLabel(fmt_currency(abs(net)))
        amt_lbl.setStyleSheet(f"color:{color};font-size:26px;font-weight:bold;")
        amt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_col.addWidget(amt_lbl)

        desc_lbl = QLabel(label)
        desc_lbl.setStyleSheet(f"color:{color};font-size:13px;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_col.addWidget(desc_lbl)

        if total_owed > 0 and total_due > 0:
            breakdown = QLabel(
                f"عليك: {fmt_currency(total_owed)}  —  لك: {fmt_currency(total_due)}"
            )
            breakdown.setStyleSheet(f"color:{COLORS['text_muted']};font-size:11px;")
            breakdown.setAlignment(Qt.AlignmentFlag.AlignRight)
            text_col.addWidget(breakdown)

        layout.addLayout(text_col)
        return frame

    def _open_customer_facing(self):
        """فتح كشف الحساب المخصص للعميل (بدون أرباح)"""
        dlg = CustomerFacingStatementDialog(self.customer_id, self)
        dlg.exec()

    def _export_image(self):
        name = self._data["customer"]["name"]
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", f"تقرير_{name}.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ✅", f"تم الحفظ:\n{path}")

    def _export_pdf(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter
        name = self._data["customer"]["name"]
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ PDF", f"تقرير_{name}.pdf", "PDF (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            painter = QPainter(printer)
            self.render(painter); painter.end()
            QMessageBox.information(self, "تم ✅", f"تم الحفظ:\n{path}")


# ══════════════════════════════════════════
#  كشف حساب للعميل (نسخة العميل — بدون أرباح)
# ══════════════════════════════════════════

class CustomerFacingStatementDialog(QDialog):
    """
    كشف حساب مُصمَّم للعميل — يعرض فقط:
    - المبالغ المطلوبة منه (مؤجل)
    - المبالغ المستحقة له (وارد لم يُسلَّم)
    - الصافي: هيدفع كام / هياخد كام
    بدون أي أرقام ربح أو تفاصيل داخلية
    """

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("كشف حساب العميل")
        self.setMinimumSize(750, 620)
        self._load_data()
        self._build_ui()

    def _load_data(self):
        self._data = db.get_customer_statement(self.customer_id)
        txns = self._data.get("transactions", [])

        # ما عليه: عمليات صادرة مؤجلة غير مسددة
        self._owed = [t for t in txns
                      if t.get("payment_status") == "pending"
                      and t.get("operation_type") == "outbound"]

        # ما له: عمليات واردة لم يُسلَّم فيها الكاش بعد
        self._due = [t for t in txns
                     if t.get("operation_type") == "inbound"
                     and not t.get("is_delivered", 0)]

        self._total_owed = sum(t.get("amount_required", 0) or 0 for t in self._owed)
        self._total_due  = sum(t.get("amount_spent",    0) or 0 for t in self._due)
        self._net        = self._total_owed - self._total_due

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(16)

        layout.addWidget(self._make_header())
        layout.addWidget(self._make_net_card())

        if self._owed:
            layout.addWidget(self._section_label("📋  المبالغ المطلوبة منك"))
            layout.addWidget(self._make_owed_table())

        if self._due:
            layout.addWidget(self._section_label("💰  المبالغ المستحقة لك"))
            layout.addWidget(self._make_due_table())

        if not self._owed and not self._due:
            empty = QLabel("✅  لا توجد مبالغ معلقة — حسابك صافي")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color:{COLORS['green']};font-size:16px;font-weight:bold;"
                f"padding:30px;"
            )
            layout.addWidget(empty)

        layout.addStretch()
        layout.addWidget(self._make_footer_btns())

    # ── Header: اسم العميل + تاريخ الكشف
    def _make_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)

        from datetime import datetime
        date_lbl = QLabel(datetime.now().strftime("%Y-%m-%d"))
        date_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
        layout.addWidget(date_lbl)

        layout.addStretch()

        c = self._data.get("customer", {})
        name_lbl = QLabel(c.get("name", "—"))
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']};font-size:20px;font-weight:bold;"
        )
        layout.addWidget(name_lbl)

        if c.get("phone"):
            ph = QLabel(f"📞  {c['phone']}")
            ph.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:13px;margin-right:12px;")
            layout.addWidget(ph)

        return frame

    # ── Net Card: الصافي الواضح
    def _make_net_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # صف الإجماليات
        totals_row = QHBoxLayout()
        totals_row.setSpacing(12)

        for label, amount, color in [
            ("إجمالي عليك",  self._total_owed, COLORS["red"]),
            ("إجمالي لك",    self._total_due,  COLORS["green"]),
        ]:
            box = QFrame()
            box.setStyleSheet(
                f"background:{COLORS['bg_input']};border-radius:10px;"
                f"border:1px solid {COLORS['border']};"
            )
            bl = QVBoxLayout(box)
            bl.setContentsMargins(16, 12, 16, 12)
            bl.setSpacing(4)

            amt_lbl = QLabel(fmt_currency(amount))
            amt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            amt_lbl.setStyleSheet(f"color:{color};font-size:20px;font-weight:bold;border:none;")
            bl.addWidget(amt_lbl)

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;border:none;")
            bl.addWidget(lbl)

            totals_row.addWidget(box)

        layout.addLayout(totals_row)

        # فاصل
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color:{COLORS['border']};")
        layout.addWidget(line)

        # الصافي — أوضح حاجة في الكشف
        net_row = QHBoxLayout()

        if self._net > 0:
            net_text  = f"المطلوب منك: {fmt_currency(self._net)}"
            net_color = COLORS["red"]
            net_bg    = COLORS["red_bg"]
            net_icon  = "💳"
        elif self._net < 0:
            net_text  = f"المستحق لك: {fmt_currency(abs(self._net))}"
            net_color = COLORS["green"]
            net_bg    = COLORS["green_bg"]
            net_icon  = "💰"
        else:
            net_text  = "الحساب صافي ✅"
            net_color = COLORS["text_secondary"]
            net_bg    = COLORS["bg_input"]
            net_icon  = "✅"

        net_frame = QFrame()
        net_frame.setStyleSheet(
            f"background:{net_bg};border-radius:10px;"
            f"border:1.5px solid {net_color};"
        )
        nfl = QHBoxLayout(net_frame)
        nfl.setContentsMargins(20, 12, 20, 12)

        icon_lbl = QLabel(net_icon)
        icon_lbl.setStyleSheet(f"font-size:22px;border:none;")
        nfl.addWidget(icon_lbl)

        nfl.addStretch()

        net_lbl = QLabel(net_text)
        net_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        net_lbl.setStyleSheet(
            f"color:{net_color};font-size:22px;font-weight:bold;border:none;"
        )
        nfl.addWidget(net_lbl)

        net_row.addWidget(net_frame)
        layout.addLayout(net_row)

        return frame

    # ── جدول ما عليه
    def _make_owed_table(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        columns = [
            ("التاريخ",    120),
            ("البيان",     220),
            ("المبلغ",     130),
        ]
        table = DataTable(columns)
        table.setMaximumHeight(180)
        table.setRowCount(len(self._owed))

        for row, t in enumerate(self._owed):
            table.set_cell(row, 0, (t.get("created_at") or "")[:10],
                           color=COLORS["text_muted"])
            table.set_cell(row, 1, t.get("service_name") or "—")
            table.set_cell(row, 2, fmt_currency(t.get("amount_required", 0) or 0),
                           color=COLORS["red"], bold=True)

        layout.addWidget(table)

        # إجمالي
        total_row = QHBoxLayout()
        total_row.setContentsMargins(16, 8, 16, 8)
        total_lbl = QLabel(f"الإجمالي: {fmt_currency(self._total_owed)}")
        total_lbl.setStyleSheet(
            f"color:{COLORS['red']};font-size:14px;font-weight:bold;"
        )
        total_row.addStretch()
        total_row.addWidget(total_lbl)
        layout.addLayout(total_row)

        return frame

    # ── جدول ما له
    def _make_due_table(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        columns = [
            ("التاريخ",    120),
            ("البيان",     220),
            ("المبلغ",     130),
        ]
        table = DataTable(columns)
        table.setMaximumHeight(180)
        table.setRowCount(len(self._due))

        for row, t in enumerate(self._due):
            table.set_cell(row, 0, (t.get("created_at") or "")[:10],
                           color=COLORS["text_muted"])
            table.set_cell(row, 1, t.get("service_name") or "—")
            table.set_cell(row, 2, fmt_currency(t.get("amount_spent", 0) or 0),
                           color=COLORS["green"], bold=True)

        layout.addWidget(table)

        total_row = QHBoxLayout()
        total_row.setContentsMargins(16, 8, 16, 8)
        total_lbl = QLabel(f"الإجمالي: {fmt_currency(self._total_due)}")
        total_lbl.setStyleSheet(
            f"color:{COLORS['green']};font-size:14px;font-weight:bold;"
        )
        total_row.addStretch()
        total_row.addWidget(total_lbl)
        layout.addLayout(total_row)

        return frame

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']};font-size:13px;font-weight:bold;"
        )
        return lbl

    # ── أزرار الأسفل
    def _make_footer_btns(self) -> QHBoxLayout:
        row = QHBoxLayout()

        img_btn = QPushButton("🖼️  حفظ كصورة")
        img_btn.setObjectName("btn_secondary")
        img_btn.setFixedHeight(38)
        img_btn.clicked.connect(self._export_image)
        row.addWidget(img_btn)

        pdf_btn = QPushButton("📄  تصدير PDF")
        pdf_btn.setObjectName("btn_secondary")
        pdf_btn.setFixedHeight(38)
        pdf_btn.clicked.connect(self._export_pdf)
        row.addWidget(pdf_btn)

        row.addStretch()

        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("btn_primary")
        close_btn.setFixedHeight(38)
        close_btn.clicked.connect(self.accept)
        row.addWidget(close_btn)

        # تحويل HBoxLayout لـ QWidget عشان addWidget يقبله
        container = QWidget()
        container.setLayout(row)
        return container

    def _open_customer_facing(self):
        """فتح كشف الحساب المخصص للعميل (بدون أرباح)"""
        dlg = CustomerFacingStatementDialog(self.customer_id, self)
        dlg.exec()

    def _export_image(self):
        c = self._data.get("customer", {})
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة",
            f"كشف_عميل_{c.get('name','')}.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ✅", f"تم حفظ الصورة:\n{path}")

    def _export_pdf(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter
        c = self._data.get("customer", {})
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كـ PDF",
            f"كشف_عميل_{c.get('name','')}.pdf", "PDF (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            painter = QPainter(printer)
            self.render(painter)
            painter.end()
            QMessageBox.information(self, "تم ✅", f"تم حفظ PDF:\n{path}")