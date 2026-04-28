"""
statement_screen.py — كشف حساب العميل
tasks: 13 (edit/delete), 14 (size), 15 (UI polish), 16 (timestamps), 17 (customer info), 21 (scroll)
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
from ui.components.widgets import DataTable
from ui.styles.theme import COLORS, FONT, CARD_RADIUS
from utils.formatters import fmt_currency


# ══════════════════════════════════════════
#  Info Pill
# ══════════════════════════════════════════

def info_pill(label: str, value: str, color: str = None) -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 10, 14, 10)
    layout.setSpacing(3)
    val_lbl = QLabel(value)
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    val_lbl.setStyleSheet(f"color:{color or COLORS['text_primary']};font-size:17px;font-weight:bold;")
    layout.addWidget(val_lbl)
    lbl = QLabel(label)
    lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:11px;")
    layout.addWidget(lbl)
    return frame


# ══════════════════════════════════════════
#  Transaction Action Dialog
# ══════════════════════════════════════════

class TransactionActionDialog(QDialog):
    """
    ديالوج موحد لإجراءات العملية:
    - outbound → مؤجل / تم السداد
    - inbound  → لم يُسلَّم / تم التسليم
    + حذف العملية
    """

    def __init__(self, t: dict, on_status_change, on_delete, parent=None):
        super().__init__(parent)
        self.t               = t
        self.on_status_change = on_status_change
        self.on_delete        = on_delete
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("إجراءات العملية")
        self.setFixedWidth(360)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        op        = self.t.get("operation_type", "")
        status    = self.t.get("payment_status", "")
        delivered = bool(self.t.get("is_delivered", 0))
        tid       = self.t["id"]

        # ── معلومات العملية ──────────────────
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(14, 10, 14, 10)
        info_layout.setSpacing(4)

        svc_lbl = QLabel(self.t.get("service_name") or "—")
        svc_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']};font-size:15px;font-weight:bold;"
        )
        svc_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(svc_lbl)

        op_text  = "📤 صادر (تحويل)" if op == "outbound" else "📥 وارد (استلام)"
        op_color = COLORS["blue"] if op == "outbound" else COLORS["purple"]
        op_lbl   = QLabel(op_text)
        op_lbl.setStyleSheet(f"color:{op_color};font-size:12px;")
        op_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(op_lbl)

        layout.addWidget(info_frame)

        # ── عنوان قسم تعديل الحالة ──────────
        status_title = QLabel("تعديل الحالة")
        status_title.setStyleSheet(
            f"color:{COLORS['text_secondary']};font-size:12px;font-weight:bold;"
        )
        status_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(status_title)

        # ── أزرار الحالة حسب نوع العملية ────
        if op == "outbound":
            # الخيارات: مؤجل أو تم السداد
            self._add_status_btn(
                layout,
                label   = "⏳  مؤجل",
                active  = (status == "pending"),
                color   = COLORS["yellow"],
                bg      = COLORS["yellow_bg"],
                handler = lambda: self._change_status(tid, "pending"),
            )
            self._add_status_btn(
                layout,
                label   = "✅  تم السداد",
                active  = (status == "paid"),
                color   = COLORS["green"],
                bg      = COLORS["green_bg"],
                handler = lambda: self._change_status(tid, "paid"),
            )

        elif op == "inbound":
            # الخيارات: لم يُسلَّم أو تم التسليم
            self._add_status_btn(
                layout,
                label   = "⏳  لم يُسلَّم بعد",
                active  = (not delivered),
                color   = COLORS["yellow"],
                bg      = COLORS["yellow_bg"],
                handler = lambda: self._change_status(tid, "not_delivered"),
            )
            self._add_status_btn(
                layout,
                label   = "✅  تم التسليم",
                active  = delivered,
                color   = COLORS["green"],
                bg      = COLORS["green_bg"],
                handler = lambda: self._change_status(tid, "delivered"),
            )

        # ── فاصل ────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color:{COLORS['border']};")
        layout.addWidget(line)

        # ── زرار الحذف ──────────────────────
        del_btn = QPushButton("🗑️  حذف العملية")
        del_btn.setObjectName("btn_danger")
        del_btn.setFixedHeight(38)
        del_btn.clicked.connect(lambda: self._delete(tid))
        layout.addWidget(del_btn)

        # ── إغلاق ───────────────────────────
        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("btn_secondary")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def _add_status_btn(self, layout, label, active, color, bg, handler):
        btn = QPushButton(label)
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if active:
            btn.setStyleSheet(
                f"background:{bg};color:{color};"
                f"border:2px solid {color};border-radius:8px;"
                f"font-size:14px;font-weight:bold;padding:4px 16px;"
            )
        else:
            btn.setStyleSheet(
                f"background:{COLORS['bg_input']};color:{COLORS['text_muted']};"
                f"border:1px solid {COLORS['border']};border-radius:8px;"
                f"font-size:14px;padding:4px 16px;"
            )
        btn.clicked.connect(handler)
        layout.addWidget(btn)

    def _change_status(self, tid: int, new_status: str):
        self.accept()
        self.on_status_change(tid, new_status)

    def _delete(self, tid: int):
        self.accept()
        self.on_delete(tid)


# ══════════════════════════════════════════
#  زرار الإجراءات الموحد (زرار واحد ⋮)
# ══════════════════════════════════════════

def make_txn_actions(t: dict, on_status_change, on_delete) -> QWidget:
    """زرار واحد ⋮ يفتح TransactionActionDialog — نفس شكل زرار المنصات"""
    cont   = QWidget()
    layout = QHBoxLayout(cont)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    btn = QPushButton("⋮  إجراءات")
    btn.setFixedHeight(30)
    btn.setFixedWidth(100)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"background:{COLORS['bg_input']};color:{COLORS['text_secondary']};"
        f"border:1px solid {COLORS['border']};border-radius:6px;"
        f"font-size:13px;padding:2px 10px;"
    )

    def _open():
        dialog = TransactionActionDialog(t, on_status_change, on_delete, cont.window())
        dialog.exec()

    btn.clicked.connect(_open)
    layout.addWidget(btn)
    return cont


# ══════════════════════════════════════════
#  كشف حساب العميل
# ══════════════════════════════════════════

class CustomerStatementDialog(QDialog):

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("كشف حساب")
        # task 14: always open large enough
        self.setMinimumSize(1100, 750)
        self.resize(1150, 800)
        self._filter = "all"
        self._load_data()
        self._build_ui()

    def _load_data(self):
        self._data = db.get_customer_statement(self.customer_id)

    def _build_ui(self):
        # task 21: wrap everything in scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        layout.addLayout(self._make_header())
        layout.addWidget(self._make_identity_card())
        layout.addLayout(self._make_stats_row())
        layout.addWidget(self._make_table())            # must be created BEFORE filter bar
        layout.addLayout(self._make_filter_bar())       # calls _fill_table internally
        layout.addWidget(self._make_summary_bar())

        scroll.setWidget(content_widget)
        outer.addWidget(scroll)

    # ── Header
    def _make_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        for label, slot, obj in [
            ("🖼️ صورة", self._export_image, "btn_secondary"),
            ("📄 PDF",   self._export_pdf,   "btn_secondary"),
            ("👤  كشف العميل", self._open_customer_facing, "btn_success"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName(obj); btn.setFixedHeight(32)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        row.addStretch()
        c = self._data["customer"]
        title = QLabel(f"📋  كشف حساب  —  {c['name']}")
        title.setStyleSheet(f"color:{COLORS['text_primary']};font-size:16px;font-weight:bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        row.addWidget(title)
        return row

    # ── Identity card — task 17: clean, readable, organized
    def _make_identity_card(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        c    = self._data["customer"]
        txns = self._data.get("transactions", [])

        # Name row
        name_lbl = QLabel(c.get("name", "—"))
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']};font-size:20px;font-weight:bold;"
        )
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(name_lbl)

        # Divider
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{COLORS['border']};")
        layout.addWidget(div)

        # Fields grid
        grid = QGridLayout(); grid.setSpacing(10); grid.setColumnStretch(1, 1)

        def add_field(row, lbl_text, val_text, val_color=None):
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            val = QLabel(val_text or "—")
            val.setStyleSheet(
                f"color:{val_color or COLORS['text_primary']};font-size:13px;font-weight:bold;"
            )
            val.setAlignment(Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)

        add_field(0, "📞  التليفون:", c.get("phone") or "—")
        add_field(1, "👥  المجموعة:", c.get("group_name") or "—", COLORS["blue"])
        add_field(2, "📝  ملاحظات:", c.get("notes") or "—")

        debt  = c.get("total_debt", 0) or 0
        dc    = COLORS["red"] if debt > 0 else (COLORS["green"] if debt < 0 else COLORS["text_muted"])
        label = "عليه" if debt > 0 else ("له" if debt < 0 else "صافر")
        add_field(3, f"💰  الرصيد ({label}):", fmt_currency(abs(debt)), dc)

        if txns:
            last_dt = (txns[0].get("created_at") or "")[:16]
            add_field(4, "🕒  آخر تعامل:", last_dt, COLORS["text_secondary"])
        add_field(5 if txns else 4, "📊  إجمالي العمليات:", str(len(txns)), COLORS["teal_bright"])

        layout.addLayout(grid)
        return frame

    # ── Stats row
    def _make_stats_row(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(10)
        t = self._data.get("totals", {})
        c = self._data["customer"]
        debt = c.get("total_debt", 0) or 0
        debt_color = COLORS["red"] if debt > 0 else COLORS["green"]
        self._stats_pills = []   # ← حفظ reference للتحديث لاحقاً
        for label, value, color in [
            ("المديونية الحالية", debt,                          debt_color),
            ("إجمالي المؤجل",   t.get("total_pending", 0) or 0, COLORS["yellow"]),
            ("إجمالي المسدد",   t.get("total_paid",    0) or 0, COLORS["green"]),
            ("إجمالي النقدي",   t.get("total_cash",    0) or 0, COLORS["blue"]),
            ("صافي الأرباح",    t.get("total_profit",  0) or 0, COLORS["purple"]),
        ]:
            pill = info_pill(label, fmt_currency(value), color)
            self._stats_pills.append(pill)
            row.addWidget(pill)
        return row

    # ── Filter bar
    def _make_filter_bar(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(8)
        row.addStretch()
        self._filter_btns = {}
        for key, label, color in [
            ("all",     "الكل 📋",  COLORS["text_secondary"]),
            ("pending", "مؤجل ⏳",  COLORS["yellow"]),
            ("paid",    "مسدد ✅",  COLORS["green"]),
            ("cash",    "نقدي 💵",  COLORS["blue"]),
            ("inbound", "وارد 📥",  COLORS["purple"]),
        ]:
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
                    f"background:{COLORS['teal_subtle']};color:{color};"
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

    # ── Table — task 13, 16
    def _make_table(self) -> QWidget:
        columns = [
            ("التاريخ والوقت", 150), ("النوع", 75), ("الخدمة", 155),
            ("المنصة", 110), ("المصروف", 100), ("المطلوب", 100),
            ("الربح", 85), ("تسليم", 75), ("المرجع", 105),
            ("الحالة", 85), ("إجراءات", 120),
        ]
        self.table = DataTable(columns)
        self.table.verticalHeader().setDefaultSectionSize(52)
        self.table.setMinimumHeight(300)
        return self.table

    def _fill_table(self):
        txns = self._data.get("transactions", [])
        if self._filter == "pending": txns = [t for t in txns if t.get("payment_status") == "pending"]
        elif self._filter == "paid":  txns = [t for t in txns if t.get("payment_status") == "paid"]
        elif self._filter == "cash":  txns = [t for t in txns if t.get("payment_status") == "cash"]
        elif self._filter == "inbound": txns = [t for t in txns if t.get("operation_type") == "inbound"]

        self.table.clear_rows()
        self.table.setRowCount(len(txns))

        for row, t in enumerate(txns):
            # task 16: full timestamp
            raw = t.get("created_at") or ""
            self.table.set_cell(row, 0, raw[:16], color=COLORS["text_muted"])

            op = t.get("operation_type", "")
            self.table.set_cell(row, 1,
                "📤 صادر" if op == "outbound" else "📥 وارد",
                color=COLORS["blue"] if op == "outbound" else COLORS["purple"])

            self.table.set_cell(row, 2, t.get("service_name") or "—")
            self.table.set_cell(row, 3, t.get("platform_name") or "—", color=COLORS["text_secondary"])
            self.table.set_cell(row, 4, fmt_currency(t.get("amount_spent",    0) or 0))
            self.table.set_cell(row, 5, fmt_currency(t.get("amount_required", 0) or 0), bold=True)
            profit = t.get("profit", 0) or 0
            self.table.set_cell(row, 6, fmt_currency(profit),
                                color=COLORS["green"] if profit >= 0 else COLORS["red"])

            if op == "inbound":
                delivered = bool(t.get("is_delivered", 0))
                self.table.set_cell(row, 7, "✅ تم" if delivered else "⏳ لا",
                                    color=COLORS["green"] if delivered else COLORS["yellow"])
            else:
                self.table.set_cell(row, 7, "—", color=COLORS["text_muted"])

            ref = "🃏 كارت" if t.get("is_card") else (t.get("reference_no") or "—")
            self.table.set_cell(row, 8, ref, color=COLORS["text_muted"])
            self.table.add_status_badge(
                row, 9,
                t.get("payment_status", ""),
                operation_type=t.get("operation_type", "outbound"),
                is_delivered=t.get("is_delivered", 0)
            )

            # task 13: action buttons
            actions = make_txn_actions(t, self._on_status_change, self._on_delete)
            self.table.setCellWidget(row, 10, actions)

        if hasattr(self, "_summary_lbl"):
            total = sum(t.get("amount_required", 0) or 0 for t in txns)
            self._summary_lbl.setText(f"عرض: {len(txns)} عملية  |  إجمالي المطلوب: {fmt_currency(total)}")

    # ── Summary bar
    def _make_summary_bar(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("card"); frame.setFixedHeight(38)
        layout = QHBoxLayout(frame); layout.setContentsMargins(14, 0, 14, 0)
        self._summary_lbl = QLabel("")
        self._summary_lbl.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:11px;")
        self._summary_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(); layout.addWidget(self._summary_lbl)
        self._fill_table()
        return frame

    # ── Task 13: Status change
    def _on_status_change(self, tid: int, new_status: str):
        # الديالوج خلاص سأل المستخدم — ننفذ مباشرة بدون سؤال تاني
        try:
            db.update_transaction_status(tid, new_status)
            self._refresh_all()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _refresh_all(self):
        """إعادة تحميل البيانات وتحديث كل عناصر الواجهة"""
        self._load_data()
        self._fill_table()

        # تحديث بطاقات الإحصائيات إذا كانت موجودة
        if hasattr(self, "_stats_pills"):
            t = self._data.get("totals", {})
            c = self._data["customer"]
            debt = c.get("total_debt", 0) or 0
            debt_color = COLORS["red"] if debt > 0 else COLORS["green"]
            new_vals = [
                (debt,                          debt_color),
                (t.get("total_pending", 0) or 0, COLORS["yellow"]),
                (t.get("total_paid",    0) or 0, COLORS["green"]),
                (t.get("total_cash",    0) or 0, COLORS["blue"]),
                (t.get("total_profit",  0) or 0, COLORS["purple"]),
            ]
            for pill, (val, color) in zip(self._stats_pills, new_vals):
                # pill هو QFrame — نحدث الـ QLabel الأول جوه
                for child in pill.findChildren(QLabel):
                    if child.text().startswith("ج") or "," in child.text() or child.text() == "0.00 ج":
                        child.setText(fmt_currency(val))
                        child.setStyleSheet(
                            f"color:{color};font-size:17px;font-weight:bold;"
                        )
                        break

    # ── Task 13: Delete
    def _on_delete(self, tid: int):
        if QMessageBox.question(self, "تأكيد الحذف",
            "⚠️ هل تريد حذف هذه العملية؟\nسيتم عكس جميع التأثيرات المالية.\nلا يمكن التراجع.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            try:
                db.delete_transaction(tid)
                self._refresh_all()
                QMessageBox.information(self, "تم ✅", "تم حذف العملية وعكس تأثيرها المالي")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _mark_paid(self, tid: int):
        self._on_status_change(tid, "paid")

    def _cleanup(self):
        if QMessageBox.question(self, "تنظيف المسدد",
            "هل تريد حذف كل العمليات المسددة لهذا العميل؟\n⚠️ لا يمكن التراجع.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            deleted = db.cleanup_paid_transactions(self.customer_id)
            self._refresh_all()
            QMessageBox.information(self, "تم ✅", f"تم حذف {deleted} عملية مسددة")

    def _open_customer_facing(self):
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
#  Customer Facing Statement (without profits)
# ══════════════════════════════════════════

class CustomerFacingStatementDialog(QDialog):
    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("كشف العميل")
        self.setMinimumSize(700, 580)
        self._data = db.get_customer_statement(customer_id)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(16)

        c    = self._data["customer"]
        txns = self._data.get("transactions", [])

        btn_row = QHBoxLayout()
        save_img_btn = QPushButton("🖼️  حفظ كصورة")
        save_img_btn.setObjectName("btn_secondary"); save_img_btn.setFixedHeight(34)
        save_img_btn.clicked.connect(self._export_image)
        btn_row.addWidget(save_img_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        id_frame = QFrame(); id_frame.setObjectName("card")
        id_layout = QHBoxLayout(id_frame); id_layout.setContentsMargins(18, 14, 18, 14)
        name_col = QVBoxLayout(); name_col.setSpacing(4)
        name_lbl = QLabel(c.get("name", "—"))
        name_lbl.setStyleSheet(f"color:{COLORS['text_primary']};font-size:20px;font-weight:bold;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        name_col.addWidget(name_lbl)
        if c.get("phone"):
            ph = QLabel(f"📞  {c['phone']}")
            ph.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:13px;")
            ph.setAlignment(Qt.AlignmentFlag.AlignLeft)
            name_col.addWidget(ph)
        id_layout.addLayout(name_col)
        id_layout.addStretch()
        from datetime import datetime
        date_lbl = QLabel(f"📅  {datetime.now().strftime('%Y-%m-%d')}")
        date_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
        id_layout.addWidget(date_lbl)
        layout.addWidget(id_frame)

        pending_txns = [t for t in txns if t.get("payment_status") == "pending"]
        due_txns     = [t for t in txns if t.get("operation_type") == "inbound" and not t.get("is_delivered", 0)]

        total_pending = sum(t.get("amount_required", 0) or 0 for t in pending_txns)
        total_due     = sum(t.get("amount_spent",    0) or 0 for t in due_txns)
        net           = total_pending - total_due

        if pending_txns:
            sec = QLabel("🔴  مبالغ مستحقة عليك")
            sec.setStyleSheet(f"color:{COLORS['red']};font-size:13px;font-weight:bold;border-right:3px solid {COLORS['red']};padding-right:8px;")
            sec.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(sec)
            layout.addWidget(self._make_txn_table(pending_txns, "owed"))

        if due_txns:
            sec = QLabel("🟢  مبالغ مستحقة لك")
            sec.setStyleSheet(f"color:{COLORS['green']};font-size:13px;font-weight:bold;border-right:3px solid {COLORS['green']};padding-right:8px;")
            sec.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(sec)
            layout.addWidget(self._make_txn_table(due_txns, "due"))

        if not pending_txns and not due_txns:
            empty = QLabel("✅  لا توجد مبالغ مستحقة عليك أو لك")
            empty.setStyleSheet(f"color:{COLORS['green']};font-size:14px;background:{COLORS['green_bg']};border-radius:8px;padding:12px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)

        layout.addStretch()

        net_frame = QFrame(); net_frame.setObjectName("card")
        nl = QHBoxLayout(net_frame); nl.setContentsMargins(18, 12, 18, 12)
        if net > 0:
            color, label = COLORS["red"], "إجمالي المطلوب منك"
        elif net < 0:
            color, label = COLORS["green"], "إجمالي المستحق لك"
        else:
            color, label = COLORS["text_muted"], "صافر (لا شيء عليك)"
        nl.addStretch()
        net_lbl = QLabel(f"{label}:  {fmt_currency(abs(net))}")
        net_lbl.setStyleSheet(f"color:{color};font-size:18px;font-weight:bold;")
        net_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        nl.addWidget(net_lbl)
        layout.addWidget(net_frame)

    def _make_txn_table(self, txns: list, mode: str) -> QFrame:
        frame = QFrame(); frame.setObjectName("card")
        layout = QVBoxLayout(frame); layout.setContentsMargins(14, 10, 14, 10); layout.setSpacing(0)
        header = QHBoxLayout()
        for text, width in [("التاريخ", 120), ("البيان", 0), ("المبلغ", 110)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:11px;font-weight:bold;border-bottom:1px solid {COLORS['border']};padding-bottom:4px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            if width: lbl.setFixedWidth(width)
            else: lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            header.addWidget(lbl)
        layout.addLayout(header)
        total = 0
        for t in txns:
            row = QHBoxLayout(); row.setContentsMargins(0, 6, 0, 6)
            date_lbl = QLabel((t.get("created_at") or "")[:10])
            date_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
            date_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft); date_lbl.setFixedWidth(120)
            row.addWidget(date_lbl)
            svc_lbl = QLabel(t.get("service_name") or "—")
            svc_lbl.setStyleSheet(f"color:{COLORS['text_primary']};font-size:13px;")
            svc_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            svc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row.addWidget(svc_lbl)
            amount = (t.get("amount_required", 0) if mode == "owed" else t.get("amount_spent", 0)) or 0
            total += amount
            color = COLORS["red"] if mode == "owed" else COLORS["green"]
            amt_lbl = QLabel(fmt_currency(amount))
            amt_lbl.setStyleSheet(f"color:{color};font-size:13px;font-weight:bold;")
            amt_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft); amt_lbl.setFixedWidth(110)
            row.addWidget(amt_lbl)
            layout.addLayout(row)
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color:{COLORS['border']};"); layout.addWidget(sep)
        total_row = QHBoxLayout()
        total_lbl = QLabel("الإجمالي:")
        total_lbl.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:12px;font-weight:bold;")
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        total_row.addStretch(); total_row.addWidget(total_lbl)
        color = COLORS["red"] if mode == "owed" else COLORS["green"]
        total_val = QLabel(fmt_currency(total))
        total_val.setStyleSheet(f"color:{color};font-size:14px;font-weight:bold;")
        total_val.setFixedWidth(110); total_val.setAlignment(Qt.AlignmentFlag.AlignLeft)
        total_row.addWidget(total_val)
        layout.addLayout(total_row)
        return frame

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", f"كشف_{self._data['customer']['name']}.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ✅", f"تم حفظ الصورة:\n{path}")


# ══════════════════════════════════════════
#  تقرير المجموعة
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
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
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
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tl.addStretch(); tl.addWidget(total_lbl)
        layout.addWidget(total_frame)

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", "تقرير_المجموعة.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ✅", f"تم حفظ الصورة:\n{path}")