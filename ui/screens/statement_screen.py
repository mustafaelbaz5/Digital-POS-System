"""
statement_screen.py — كشف حساب العميل (واجهة محسّنة)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFileDialog, QMessageBox,
    QWidget, QScrollArea, QGridLayout, QSizePolicy,
    QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database as db
from ui.components.widgets import DataTable, BaseDialog, CardGroup, make_divider
from ui.styles.theme import COLORS, FONT, GAP_SM, GAP_MD
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
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    val_lbl.setStyleSheet(
        f"color:{color or COLORS['text_primary']};font-size:17px;font-weight:bold;"
    )
    layout.addWidget(val_lbl)

    lbl = QLabel(label)
    lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
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
        self._make_table()                          # إنشاء self.table أولاً قبل أي استدعاء _fill_table
        layout.addLayout(self._make_filter_bar())   # يستدعي _fill_table داخلياً
        layout.addWidget(self.table)
        layout.addWidget(self._make_summary_bar())

    # ── Header
    def _make_header(self) -> QHBoxLayout:
        row = QHBoxLayout()

        export_img = QPushButton("🖼️ حفظ كصورة")
        export_img.setObjectName("btn_secondary"); export_img.setFixedHeight(32)
        export_img.clicked.connect(self._export_image)
        row.addWidget(export_img)

        customer_stmt_btn = QPushButton("👤  كشف العميل")
        customer_stmt_btn.setObjectName("btn_ghost"); customer_stmt_btn.setFixedHeight(32)
        customer_stmt_btn.clicked.connect(self._open_customer_facing)
        row.addWidget(customer_stmt_btn)

        row.addStretch()

        c = self._data["customer"]
        title = QLabel(f"  كشف حساب  —  {c['name']}")
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
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info.addWidget(name_lbl)

        sub_row = QHBoxLayout(); sub_row.setSpacing(16)
        sub_row.addStretch()
        if c.get("phone"):
            ph = QLabel(f"📞  {c['phone']}")
            ph.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:13px;")
            sub_row.addWidget(ph)
        if c.get("group_name"):
            gr = QLabel(f"👥  {c['group_name']}")
            gr.setStyleSheet(f"color:{COLORS['blue']};font-size:13px;")
            sub_row.addWidget(gr)
        info.addLayout(sub_row)

        if c.get("notes"):
            notes_lbl = QLabel(f"📝  {c['notes']}")
            notes_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
            notes_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
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
            ("إجمالي النقدي",    t.get("total_cash",    0) or 0,    COLORS["blue"]),
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
            ("all",     "الكل ",   COLORS["text_secondary"]),
            ("pending", "مؤجل ⏳",   COLORS["yellow"]),
            ("paid",    "مسدد ",   COLORS["green"]),
            ("cash",    "نقدي 💵",   COLORS["blue"]),
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
                color=COLORS["blue"] if op == "outbound" else COLORS["purple"])

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
                dlv_text  = " تم" if delivered else "⏳ لا"
                dlv_color = COLORS["green"] if delivered else COLORS["yellow"]
                self.table.set_cell(row, 7, dlv_text, color=dlv_color)
            else:
                self.table.set_cell(row, 7, "—", color=COLORS["text_muted"])

            ref = "🃏 كارت" if t.get("is_card") else (t.get("reference_no") or "—")
            self.table.set_cell(row, 8, ref, color=COLORS["text_muted"])
            self.table.add_status_badge(row, 9, t.get("payment_status", ""))

            # زرار سداد
            if t.get("payment_status") == "pending":
                self.table.add_action_button(
                    row, 10, " سداد", 
                    lambda _, tid=t["id"]: self._mark_paid(tid), 
                    role="ghost"
                )
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
                QMessageBox.information(self, "تم ", "تم تحويل العملية إلى مسددة")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _cleanup(self):
        if QMessageBox.question(self, "تنظيف المسدد",
            "هل تريد حذف كل العمليات المسددة لهذا العميل؟\n⚠️ لا يمكن التراجع.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            deleted = db.cleanup_paid_transactions(self.customer_id)
            self._load_data(); self._fill_table()
            QMessageBox.information(self, "تم ", f"تم حذف {deleted} عملية مسددة")

    def _open_customer_facing(self):
        """فتح كشف الحساب المخصص للعميل (بدون أرباح)"""
        dlg = CustomerFacingStatementDialog(self.customer_id, self)
        dlg.exec()

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", f"كشف_{self._data['customer']['name']}.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ", f"تم حفظ الصورة:\n{path}")

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
            QMessageBox.information(self, "تم ", f"تم حفظ PDF:\n{path}")


# ══════════════════════════════════════════
#  تقرير المجموعة
# ══════════════════════════════════════════

class GroupReportDialog(BaseDialog):

    def __init__(self, group_id: int, parent=None):
        groups = db.get_all_groups()
        group  = next((g for g in groups if g["id"] == group_id), {})
        super().__init__(f"تقرير مجموعة — {group.get('name', '—')}", parent)
        self.group_id = group_id
        self.setMinimumSize(850, 600)
        self._build_content()

    def _build_content(self):
        customers  = db.get_customers_by_group(self.group_id)
        total_debt = sum(c.get("total_debt", 0) or 0 for c in customers)

        columns = [("الاسم", 220), ("التليفون", 160), ("المديونية", 150), ("ملاحظات", -1)]
        self.table = DataTable(columns)
        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            debt = c.get("total_debt", 0) or 0
            self.table.set_cell(row, 0, c["name"], bold=True)
            self.table.set_cell(row, 1, c.get("phone") or "—", color=COLORS["text_secondary"])
            self.table.set_cell(row, 2, fmt_currency(debt),
                                color=COLORS["red"] if debt > 0 else COLORS["green"] if debt < 0 else COLORS["text_muted"], bold=debt != 0)
            self.table.set_cell(row, 3, c.get("notes") or "—", color=COLORS["text_muted"])
        
        self.body.addWidget(self.table)

        total_frame = QFrame(); total_frame.setObjectName("card_highlight")
        tl = QHBoxLayout(total_frame); tl.setContentsMargins(16, 12, 16, 12)
        total_lbl = QLabel(f"إجمالي المجموعة: {fmt_currency(total_debt)}")
        total_lbl.setStyleSheet(
            f"color:{COLORS['red'] if total_debt > 0 else COLORS['green']};"
            f"font-size:18px;font-weight:bold;")
        tl.addStretch(); tl.addWidget(total_lbl)
        self.body.addWidget(total_frame)

        # Footer
        self.add_stretch()
        self.add_button("🖼️ حفظ كصورة", self._export_image, role="secondary")
        self.add_button("إغلاق", self.accept, role="primary")

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", "تقرير_المجموعة.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ", f"تم حفظ الصورة:\n{path}")


# ══════════════════════════════════════════
#  تقرير العميل (للطباعة / التصدير)
#  بدون أرباح — فقط ما عليه وما له
# ══════════════════════════════════════════

class ClientReportDialog(BaseDialog):
    def __init__(self, customer_id: int, parent=None):
        super().__init__("تقرير العميل المالي", parent)
        self.customer_id = customer_id
        self.setMinimumSize(750, 650)
        self._data = db.get_customer_statement(customer_id)
        self._build_content()

    def _build_content(self):
        c    = self._data["customer"]
        txns = self._data.get("transactions", [])

        # ── هوية العميل
        id_frame = QFrame(); id_frame.setObjectName("card")
        id_layout = QHBoxLayout(id_frame)
        id_layout.setContentsMargins(18, 14, 18, 14)

        name_col = QVBoxLayout(); name_col.setSpacing(4)
        name_lbl = QLabel(c.get("name", "—"))
        name_lbl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:20px; font-weight:bold;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        name_col.addWidget(name_lbl)
        
        if c.get("phone"):
            ph = QLabel(f"📞  {c['phone']}")
            ph.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:13px;")
            ph.setAlignment(Qt.AlignmentFlag.AlignLeft)
            name_col.addWidget(ph)
        id_layout.addLayout(name_col)
        id_layout.addStretch()

        from datetime import datetime
        date_lbl = QLabel(f"📅  {datetime.now().strftime('%Y-%m-%d')}")
        date_lbl.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:12px;")
        id_layout.addWidget(date_lbl)
        self.body.addWidget(id_frame)

        # Analysis
        pending_txns  = [t for t in txns if t.get("payment_status") == "pending"]
        due_txns      = [t for t in txns
                         if t.get("operation_type") == "inbound"
                         and not t.get("is_delivered", 0)
                         and t.get("customer_id") == self.customer_id]

        total_pending = sum(t.get("amount_required", 0) or 0 for t in pending_txns)
        total_due     = sum(t.get("amount_spent", 0) or 0 for t in due_txns)
        net           = total_pending - total_due

        if pending_txns:
            self.body.addWidget(self._section_title("🔴  مبالغ مستحقة عليك", COLORS["red"]))
            self.body.addWidget(self._make_txn_table(pending_txns, mode="owed"))

        if due_txns:
            self.body.addWidget(self._section_title("🟢  مبالغ مستحقة لك", COLORS["green"]))
            self.body.addWidget(self._make_txn_table(due_txns, mode="due"))

        if not pending_txns and not due_txns:
            empty = QLabel("  لا توجد مبالغ مستحقة حالياً")
            empty.setStyleSheet(f"color:{COLORS['green']}; background:{COLORS['green_bg']}; border-radius:8px; padding:20px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.body.addWidget(empty)

        self.body.addStretch()
        self.body.addWidget(self._make_net_card(total_pending, total_due, net))

        # Footer
        self.add_stretch()
        self.add_button("🖼️ حفظ كصورة", self._export_image, role="secondary")
        self.add_button("📄 حفظ PDF", self._export_pdf, role="secondary")
        self.add_button("إغلاق", self.accept, role="primary")

    def _section_title(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{color}; font-size:14px; font-weight:bold; border-right:3px solid {color}; padding-right:10px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        return lbl

    def _make_txn_table(self, txns: list, mode: str) -> QFrame:
        frame = QFrame(); frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(0)

        # Header row
        header = QHBoxLayout()
        for text, width in [("التاريخ", 110), ("البيان", 0), ("المبلغ", 110)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:11px; font-weight:bold; border-bottom:1px solid {COLORS['border']}; padding-bottom:4px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            if width: lbl.setFixedWidth(width)
            else: lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            header.addWidget(lbl)
        layout.addLayout(header)

        total = 0
        for t in txns:
            row = QHBoxLayout(); row.setContentsMargins(0, 6, 0, 6)
            date_lbl = QLabel((t.get("created_at") or "")[:10])
            date_lbl.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:12px;")
            date_lbl.setFixedWidth(110); row.addWidget(date_lbl)

            service = t.get("service_name") or "—"
            svc_lbl = QLabel(service)
            svc_lbl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:13px;")
            svc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred); row.addWidget(svc_lbl)

            amount = t.get("amount_required", 0) if mode == "owed" else t.get("amount_spent", 0)
            color  = COLORS["red"] if mode == "owed" else COLORS["green"]
            total += amount

            amt_lbl = QLabel(fmt_currency(amount))
            amt_lbl.setStyleSheet(f"color:{color}; font-size:13px; font-weight:bold;")
            amt_lbl.setFixedWidth(110); row.addWidget(amt_lbl)
            layout.addLayout(row)
            
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet(f"color:{COLORS['border']};"); layout.addWidget(sep)

        return frame

    def _make_net_card(self, total_owed: float, total_due: float, net: float) -> QFrame:
        frame = QFrame(); frame.setObjectName("card")
        if net > 0:
            bg, border, color, label, icon = COLORS["red_bg"], COLORS["red"], COLORS["red"], "إجمالي المبلغ المطلوب منك", "💳"
        elif net < 0:
            bg, border, color, label, icon = COLORS["green_bg"], COLORS["green"], COLORS["green"], "إجمالي المبلغ المستحق لك", "💰"
        else:
            bg, border, color, label, icon = COLORS["bg_input"], COLORS["border"], COLORS["text_secondary"], "الحساب متساوٍ", ""

        frame.setStyleSheet(f"QFrame#card {{ background:{bg}; border:2px solid {border}; border-radius:12px; }}")
        layout = QHBoxLayout(frame); layout.setContentsMargins(24, 18, 24, 18)
        
        icon_lbl = QLabel(icon); icon_lbl.setStyleSheet("font-size:28px;"); layout.addWidget(icon_lbl)
        layout.addStretch()

        text_col = QVBoxLayout(); text_col.setSpacing(4)
        amt_lbl = QLabel(fmt_currency(abs(net))); amt_lbl.setStyleSheet(f"color:{color}; font-size:26px; font-weight:bold;")
        text_col.addWidget(amt_lbl)
        desc_lbl = QLabel(label); desc_lbl.setStyleSheet(f"color:{color}; font-size:13px;")
        text_col.addWidget(desc_lbl)
        layout.addLayout(text_col)
        return frame

    def _export_image(self):
        name = self._data["customer"]["name"]
        path, _ = QFileDialog.getSaveFileName(self, "حفظ كصورة", f"تقرير_{name}.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ", f"تم الحفظ:\n{path}")

    def _export_pdf(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter
        name = self._data["customer"]["name"]
        path, _ = QFileDialog.getSaveFileName(self, "حفظ PDF", f"تقرير_{name}.pdf", "PDF (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            painter = QPainter(printer)
            self.render(painter); painter.end()
            QMessageBox.information(self, "تم ", f"تم الحفظ:\n{path}")


# ══════════════════════════════════════════
#  كشف حساب للعميل (نسخة العميل — بدون أرباح)
# ══════════════════════════════════════════

class CustomerFacingStatementDialog(BaseDialog):
    def __init__(self, customer_id: int, parent=None):
        super().__init__("كشف حساب العميل", parent)
        self.customer_id = customer_id
        self.setMinimumSize(800, 650)
        self._load_data()
        self._build_content()

    def _load_data(self):
        self._data = db.get_customer_statement(self.customer_id)
        txns = self._data.get("transactions", [])
        self._owed = [t for t in txns if t.get("payment_status") == "pending" and t.get("operation_type") == "outbound"]
        self._due = [t for t in txns if t.get("operation_type") == "inbound" and not t.get("is_delivered", 0)]
        self._total_owed = sum(t.get("amount_required", 0) or 0 for t in self._owed)
        self._total_due  = sum(t.get("amount_spent",    0) or 0 for t in self._due)
        self._net        = self._total_owed - self._total_due

    def _build_content(self):
        self.body.addWidget(self._make_client_info())
        self.body.addWidget(self._make_net_summary())

        if self._owed:
            self.body.addWidget(self._section_label("📋 المبالغ المطلوبة منك"))
            self.body.addWidget(self._make_mini_table(self._owed, "owed"))

        if self._due:
            self.body.addWidget(self._section_label("💰 المبالغ المستحقة لك"))
            self.body.addWidget(self._make_mini_table(self._due, "due"))

        if not self._owed and not self._due:
            empty = QLabel("لا توجد مبالغ معلقة — حسابك صافي")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{COLORS['green']}; font-size:18px; font-weight:bold; padding:40px;")
            self.body.addWidget(empty)

        self.body.addStretch()
        
        # Footer
        self.add_stretch()
        self.add_button("🖼️ حفظ كصورة", self._export_image, role="secondary")
        self.add_button("📄 تصدير PDF", self._export_pdf, role="secondary")
        self.add_button("إغلاق", self.accept, role="primary")

    def _make_client_info(self) -> QFrame:
        f = QFrame(); f.setObjectName("card")
        l = QHBoxLayout(f); l.setContentsMargins(18, 14, 18, 14)
        c = self._data.get("customer", {})
        l.addWidget(QLabel(f"👤 {c.get('name')}"))
        l.addStretch()
        l.addWidget(QLabel(f"📞 {c.get('phone', '—')}"))
        return f

    def _make_net_summary(self) -> QFrame:
        f = QFrame(); f.setObjectName("card_highlight")
        l = QVBoxLayout(f); l.setContentsMargins(20, 16, 20, 16); l.setSpacing(10)
        
        net_text = f"المطلوب منك: {fmt_currency(self._net)}" if self._net > 0 else f"المستحق لك: {fmt_currency(abs(self._net))}" if self._net < 0 else "الحساب صافي"
        color = COLORS["red"] if self._net > 0 else COLORS["green"] if self._net < 0 else COLORS["text_secondary"]
        
        lbl = QLabel(net_text)
        lbl.setStyleSheet(f"color:{color}; font-size:24px; font-weight:bold; border:none;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl)
        return f

    def _make_mini_table(self, txns, mode) -> DataTable:
        cols = [("التاريخ", 120), ("البيان", -1), ("المبلغ", 130)]
        t = DataTable(cols); t.setMaximumHeight(200); t.setRowCount(len(txns))
        color = COLORS["red"] if mode == "owed" else COLORS["green"]
        for row, tx in enumerate(txns):
            t.set_cell(row, 0, (tx.get("created_at") or "")[:10], color=COLORS["text_muted"])
            t.set_cell(row, 1, tx.get("service_name") or "—")
            amt = tx.get("amount_required") if mode == "owed" else tx.get("amount_spent")
            t.set_cell(row, 2, fmt_currency(amt), color=color, bold=True)
        return t

    def _section_label(self, text):
        l = QLabel(text); l.setStyleSheet(f"color:{COLORS['text_secondary']}; font-weight:bold; font-size:14px;")
        return l

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "حفظ كصورة", "كشف_حساب.png", "PNG (*.png)")
        if path: self.grab().save(path, "PNG"); QMessageBox.information(self, "تم ", "تم حفظ الصورة")

    def _export_pdf(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter
        path, _ = QFileDialog.getSaveFileName(self, "حفظ كـ PDF", "كشف_حساب.pdf", "PDF (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            painter = QPainter(printer); self.render(painter); painter.end()
            QMessageBox.information(self, "تم ", "تم حفظ PDF")


# ──────────────────────────────────────────────────────────
#  make_txn_actions — helper مشترك للتقارير وكشف الحساب
# ──────────────────────────────────────────────────────────

def make_txn_actions(t: dict, on_status_change, on_delete) -> QWidget:
    """
    يرجع QWidget فيه زرار "إجراءات" يفتح _ActionDialog.
    """
    btn = QPushButton("⋮ إجراءات")
    btn.setObjectName("btn_ghost")
    btn.setFixedHeight(30)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"font-size: {FONT['sm']}; padding: 0 12px;")

    def _open():
        parent_widget = btn.window()
        dlg = _ActionDialog(t, on_status_change, on_delete, parent_widget)
        dlg.exec()

    btn.clicked.connect(_open)

    wrap = QWidget()
    wrap.setStyleSheet("background: transparent; border: none;")
    wl   = QHBoxLayout(wrap)
    wl.setContentsMargins(8, 2, 8, 2)
    wl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    wl.addWidget(btn)
    return wrap


class _ActionDialog(BaseDialog):
    """
    حوار صغير يعرض خيارات تعديل أو حذف العملية.
    """

    def __init__(self, t: dict, on_status_change, on_delete, parent=None):
        super().__init__("إجراءات العملية", parent)
        self._t               = t
        self._on_status_change = on_status_change
        self._on_delete        = on_delete
        self.setMinimumWidth(380)
        self._build_content()

    def _build_content(self):
        t = self._t
        op_type = t.get("operation_type", "outbound")
        
        # Info Card
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        
        service_lbl = QLabel(f"🛠️ {t.get('service_name', 'عملية بدون اسم')}")
        service_lbl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:15px; font-weight:bold;")
        cl.addWidget(service_lbl)
        
        amt_lbl = QLabel(f"💰 المبلغ المطلوب: {fmt_currency(t.get('amount_required', 0))}")
        amt_lbl.setStyleSheet(f"color:{COLORS['accent']}; font-weight:bold;")
        cl.addWidget(amt_lbl)
        
        self.body.addWidget(card)
        self.body.addSpacing(GAP_SM)

        # Status Toggle Button
        if op_type == "outbound":
            curr_status = t.get("payment_status", "pending")
            btn_text = "✅ تحديد كمسدد" if curr_status == "pending" else "⏳ تحديد كمؤجل"
            new_status = "paid" if curr_status == "pending" else "pending"
            role = "primary" if curr_status == "pending" else "secondary"
            
            s_btn = QPushButton(btn_text)
            s_btn.setObjectName(f"btn_{role}")
            s_btn.setFixedHeight(44)
            s_btn.clicked.connect(lambda: self._do_status(new_status))
            self.body.addWidget(s_btn)
            
        else: # inbound
            is_del = t.get("is_delivered", 0)
            btn_text = "🤝 تحديد كتم التسليم" if not is_del else "⏳ تحديد كـ لم يُسلّم"
            new_val = 1 if not is_del else 0
            role = "primary" if not is_del else "secondary"
            
            d_btn = QPushButton(btn_text)
            d_btn.setObjectName(f"btn_{role}")
            d_btn.setFixedHeight(44)
            d_btn.clicked.connect(lambda: self._do_status(new_val))
            self.body.addWidget(d_btn)

        # Footer
        self.add_stretch()
        self.add_button("🗑️ حذف العملية", self._do_delete, role="danger")
        self.add_button("إغلاق", self.reject, role="secondary")

    def _do_status(self, val):
        self.accept()
        self._on_status_change(self._t["id"], val)

    def _do_delete(self):
        if QMessageBox.question(self, "تأكيد الحذف",
            "⚠️ حذف العملية وعكس تأثيرها المالي؟ لا يمكن التراجع.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.accept()
            self._on_delete(self._t["id"])
