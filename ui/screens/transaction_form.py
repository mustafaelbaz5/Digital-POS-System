"""
transaction_form.py — شاشة إضافة العمليات
Refactored: ScreenShell, cleaner form layout, better field grouping
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit,
    QTabWidget, QCheckBox, QDoubleSpinBox,
    QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.styles.theme import COLORS
from ui.components.widgets import ScreenShell, make_divider
from utils.formatters import fmt_currency

import database as db


# ══════════════════════════════════════════
#  Helper: Field with label
# ══════════════════════════════════════════

def field(label_text: str, widget: QWidget) -> QVBoxLayout:
    lbl = QLabel(label_text)
    lbl.setObjectName("label_field")
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
    box = QVBoxLayout()
    box.setSpacing(5)
    box.addWidget(lbl)
    box.addWidget(widget)
    return box


# ══════════════════════════════════════════
#  Outbound Tab
# ══════════════════════════════════════════

class OutboundTab(QWidget):
    transaction_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._all_customers = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # ── Row 1: Platform + Service
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self.platform_combo = QComboBox()
        self.platform_combo.setMinimumWidth(200)
        self.platform_combo.currentIndexChanged.connect(self._update_balance)
        row1.addLayout(field("المنصة *", self.platform_combo))

        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("مثال: شحن رصيد، تحويل...")
        row1.addLayout(field("اسم الخدمة *", self.service_input))

        layout.addLayout(row1)

        # Balance hint
        self.balance_lbl = QLabel("")
        self.balance_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; margin-right: 2px;"
        )
        self.balance_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.balance_lbl)

        # ── Row 2: Amounts
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        self.amount_spent = QDoubleSpinBox()
        self.amount_spent.setRange(0.01, 9_999_999)
        self.amount_spent.setDecimals(2)
        self.amount_spent.setSuffix(" ج")
        self.amount_spent.valueChanged.connect(self._calc_profit)
        row2.addLayout(field("المبلغ المصروف (من المنصة) *", self.amount_spent))

        self.amount_required = QDoubleSpinBox()
        self.amount_required.setRange(0.01, 9_999_999)
        self.amount_required.setDecimals(2)
        self.amount_required.setSuffix(" ج")
        self.amount_required.valueChanged.connect(self._calc_profit)
        row2.addLayout(field("المبلغ المطلوب (من العميل) *", self.amount_required))

        layout.addLayout(row2)

        # Profit bar
        layout.addWidget(self._make_profit_bar())

        # ── Row 3: Customer + Payment status
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        # Customer with inline search
        cust_box = QVBoxLayout()
        cust_box.setSpacing(5)
        cust_box.addWidget(self._field_lbl("العميل *"))

        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("🔍 ابحث باسم أو تليفون...")
        self.customer_search.setFixedHeight(34)
        self.customer_search.textChanged.connect(self._filter_customers)
        cust_box.addWidget(self.customer_search)

        self.customer_combo = QComboBox()
        cust_box.addWidget(self.customer_combo)
        row3.addLayout(cust_box)

        # Payment status
        self.status_combo = QComboBox()
        self.status_combo.addItem("💵  نقدي",  "cash")
        self.status_combo.addItem("⏳  مؤجل",  "pending")
        row3.addLayout(field("حالة الدفع *", self.status_combo))

        layout.addLayout(row3)

        # ── Row 4: Reference + Card checkbox
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("رقم المرجع / العملية")
        row4.addLayout(field("رقم المرجع", self.ref_input))

        card_col = QVBoxLayout()
        card_col.setSpacing(5)
        card_col.addWidget(self._field_lbl(" "))
        self.is_card_check = QCheckBox("كارت (بدون رقم عملية)")
        self.is_card_check.stateChanged.connect(
            lambda s: self.ref_input.setEnabled(not bool(s))
        )
        card_col.addWidget(self.is_card_check)
        card_col.addStretch()
        row4.addLayout(card_col)

        layout.addLayout(row4)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(64)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        layout.addLayout(field("ملاحظات", self.notes_input))

        layout.addStretch()

        # Save button
        save_btn = QPushButton("✅  حفظ العملية الصادرة")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(44)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _field_lbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("label_field")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        return lbl

    def _make_profit_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(48)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)

        lbl = QLabel("الربح المتوقع:")
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(lbl)
        layout.addStretch()

        self.profit_label = QLabel("0.00 ج")
        self.profit_label.setStyleSheet(
            f"color: {COLORS['green']}; font-size: 15px; font-weight: bold;"
        )
        layout.addWidget(self.profit_label)
        return frame

    def load_data(self):
        self.platform_combo.clear()
        for p in db.get_all_platforms():
            icon  = "🏧" if p["type"] == "machine" else "💳"
            label = f"{icon} {p['name']}  ({fmt_currency(p['balance'])})"
            self.platform_combo.addItem(label, p["id"])

        self._all_customers = db.get_all_customers()
        self._fill_customers(self._all_customers)
        self._update_balance()

    def _fill_customers(self, customers: list):
        self.customer_combo.clear()
        for c in customers:
            label = c["name"]
            if c.get("phone"):
                label += f"  ({c['phone']})"
            self.customer_combo.addItem(label, c["id"])

    def _filter_customers(self, text: str):
        if not text.strip():
            self._fill_customers(self._all_customers)
            return
        filtered = [c for c in self._all_customers
                    if text in c["name"] or text in (c.get("phone") or "")]
        self._fill_customers(filtered)

    def _update_balance(self):
        pid = self.platform_combo.currentData()
        if pid:
            p = db.get_platform_by_id(pid)
            if p:
                self.balance_lbl.setText(f"الرصيد الحالي: {fmt_currency(p['balance'])}")

    def _calc_profit(self):
        profit = self.amount_required.value() - self.amount_spent.value()
        color  = COLORS["green"] if profit >= 0 else COLORS["red"]
        self.profit_label.setText(f"{profit:,.2f} ج")
        self.profit_label.setStyleSheet(
            f"color: {color}; font-size: 15px; font-weight: bold;"
        )

    def _save(self):
        pid     = self.platform_combo.currentData()
        cid     = self.customer_combo.currentData()
        service = self.service_input.text().strip()
        spent   = self.amount_spent.value()
        req     = self.amount_required.value()
        status  = self.status_combo.currentData()

        if not pid:   QMessageBox.warning(self, "تنبيه", "اختر المنصة");      return
        if not cid:   QMessageBox.warning(self, "تنبيه", "اختر العميل");      return
        if not service: QMessageBox.warning(self, "تنبيه", "أدخل اسم الخدمة"); return
        if spent <= 0:  QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المصروف"); return
        if req <= 0:    QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المطلوب"); return

        try:
            db.add_outbound_transaction(
                platform_id     = pid,
                customer_id     = cid,
                service_name    = service,
                amount_spent    = spent,
                amount_required = req,
                payment_status  = status,
                reference_no    = self.ref_input.text().strip(),
                is_card         = self.is_card_check.isChecked(),
                notes           = self.notes_input.toPlainText().strip()
            )
            QMessageBox.information(
                self, "تم ✅",
                f"تم تسجيل العملية بنجاح\nالربح: {fmt_currency(req - spent)}"
            )
            self._reset()
            self.transaction_added.emit()
        except ValueError as e:
            QMessageBox.warning(self, "تعذّر تنفيذ العملية", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _reset(self):
        self.service_input.clear()
        self.amount_spent.setValue(0.01)
        self.amount_required.setValue(0.01)
        self.ref_input.clear()
        self.is_card_check.setChecked(False)
        self.notes_input.clear()
        self.customer_search.clear()
        self.status_combo.setCurrentIndex(0)
        self.load_data()


# ══════════════════════════════════════════
#  Inbound Tab
# ══════════════════════════════════════════

class InboundTab(QWidget):
    transaction_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._all_customers = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Info note
        note = QLabel("📌  عملية الاستلام متاحة للمحافظ الإلكترونية فقط")
        note.setStyleSheet(
            f"color: {COLORS['blue_bright']}; background: {COLORS['blue_subtle']};"
            f"border: 1px solid {COLORS['border_light']};"
            f"border-radius: 8px; padding: 8px 14px; font-size: 12px;"
        )
        note.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(note)

        # ── Row 1: Wallet + Service
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self.wallet_combo = QComboBox()
        self.wallet_combo.setMinimumWidth(200)
        self.wallet_combo.currentIndexChanged.connect(self._update_wallet_info)
        row1.addLayout(field("المحفظة *", self.wallet_combo))

        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("مثال: استلام تحويل فودافون")
        row1.addLayout(field("اسم الخدمة *", self.service_input))

        layout.addLayout(row1)

        # Info bar
        layout.addWidget(self._make_info_bar())

        # ── Row 2: Amounts
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        self.amount_received = QDoubleSpinBox()
        self.amount_received.setRange(0.01, 9_999_999)
        self.amount_received.setDecimals(2)
        self.amount_received.setSuffix(" ج")
        self.amount_received.valueChanged.connect(self._calc_profit)
        row2.addLayout(field("المبلغ المستلم في المحفظة *", self.amount_received))

        self.amount_delivered = QDoubleSpinBox()
        self.amount_delivered.setRange(0.01, 9_999_999)
        self.amount_delivered.setDecimals(2)
        self.amount_delivered.setSuffix(" ج")
        self.amount_delivered.valueChanged.connect(self._calc_profit)
        row2.addLayout(field("المبلغ المسلم كاش *", self.amount_delivered))

        layout.addLayout(row2)

        # Profit bar
        layout.addWidget(self._make_profit_bar())

        # ── Row 3: Customer + Reference
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        cust_col = QVBoxLayout()
        cust_col.setSpacing(5)
        lbl = QLabel("العميل")
        lbl.setObjectName("label_field")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        cust_col.addWidget(lbl)

        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("🔍 ابحث باسم أو تليفون...")
        self.customer_search.setFixedHeight(34)
        self.customer_search.textChanged.connect(self._filter_customers)
        cust_col.addWidget(self.customer_search)

        self.customer_combo = QComboBox()
        cust_col.addWidget(self.customer_combo)
        row3.addLayout(cust_col)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("رقم المرجع")
        row3.addLayout(field("رقم المرجع", self.ref_input))

        layout.addLayout(row3)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(64)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        layout.addLayout(field("ملاحظات", self.notes_input))

        layout.addStretch()

        save_btn = QPushButton("✅  حفظ العملية الواردة")
        save_btn.setObjectName("btn_success")
        save_btn.setFixedHeight(44)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _make_info_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(46)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)

        self.cash_lbl  = QLabel("")
        self.cash_lbl.setStyleSheet(f"color: {COLORS['green']}; font-size: 12px;")
        layout.addWidget(self.cash_lbl)

        layout.addStretch()

        self.limit_lbl = QLabel("")
        self.limit_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.limit_lbl)

        return frame

    def _make_profit_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(48)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)

        lbl = QLabel("الربح المتوقع:")
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(lbl)
        layout.addStretch()

        self.profit_label = QLabel("0.00 ج")
        self.profit_label.setStyleSheet(
            f"color: {COLORS['green']}; font-size: 15px; font-weight: bold;"
        )
        layout.addWidget(self.profit_label)
        return frame

    def load_data(self):
        self.wallet_combo.clear()
        for w in db.get_all_platforms():
            if w["type"] != "wallet":
                continue
            pct   = int(w.get("monthly_used", 0) / max(w.get("monthly_limit", 200000), 1) * 100)
            label = f"💳 {w['name']}  ({fmt_currency(w['balance'])})  — {pct}%"
            self.wallet_combo.addItem(label, w["id"])

        self._all_customers = db.get_all_customers()
        self._fill_customers(self._all_customers)
        self._update_wallet_info()

    def _fill_customers(self, customers: list):
        self.customer_combo.clear()
        self.customer_combo.addItem("بدون عميل محدد", None)
        for c in customers:
            label = c["name"]
            if c.get("phone"):
                label += f"  ({c['phone']})"
            self.customer_combo.addItem(label, c["id"])

    def _filter_customers(self, text: str):
        if not text.strip():
            self._fill_customers(self._all_customers)
            return
        filtered = [c for c in self._all_customers
                    if text in c["name"] or text in (c.get("phone") or "")]
        self._fill_customers(filtered)

    def _update_wallet_info(self):
        budget = db.get_budget()
        self.cash_lbl.setText(f"الكاش المتاح: {fmt_currency(budget.get('cash_vault', 0))}")

        wid = self.wallet_combo.currentData()
        if wid:
            w = db.get_platform_by_id(wid)
            if w:
                remaining = w.get("monthly_limit", 200000) - w.get("monthly_used", 0)
                color = COLORS["red"] if remaining < 10000 else COLORS["text_secondary"]
                self.limit_lbl.setText(f"متبقي من الحد الشهري: {fmt_currency(remaining)}")
                self.limit_lbl.setStyleSheet(f"color: {color}; font-size: 12px;")

    def _calc_profit(self):
        profit = self.amount_received.value() - self.amount_delivered.value()
        color  = COLORS["green"] if profit >= 0 else COLORS["red"]
        self.profit_label.setText(f"{profit:,.2f} ج")
        self.profit_label.setStyleSheet(
            f"color: {color}; font-size: 15px; font-weight: bold;"
        )

    def _save(self):
        wid       = self.wallet_combo.currentData()
        cid       = self.customer_combo.currentData()
        service   = self.service_input.text().strip()
        received  = self.amount_received.value()
        delivered = self.amount_delivered.value()

        if not wid:     QMessageBox.warning(self, "تنبيه", "اختر المحفظة");        return
        if not service: QMessageBox.warning(self, "تنبيه", "أدخل اسم الخدمة");    return
        if received <= 0:  QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المستلم"); return
        if delivered <= 0: QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المسلم");  return

        try:
            db.add_inbound_transaction(
                wallet_id        = wid,
                customer_id      = cid,
                service_name     = service,
                amount_received  = received,
                amount_delivered = delivered,
                reference_no     = self.ref_input.text().strip(),
                notes            = self.notes_input.toPlainText().strip()
            )
            QMessageBox.information(
                self, "تم ✅",
                f"تم تسجيل الاستلام بنجاح\nالربح: {fmt_currency(received - delivered)}"
            )
            self._reset()
            self.transaction_added.emit()
        except ValueError as e:
            QMessageBox.warning(self, "تعذّر تنفيذ العملية", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _reset(self):
        self.service_input.clear()
        self.amount_received.setValue(0.01)
        self.amount_delivered.setValue(0.01)
        self.ref_input.clear()
        self.notes_input.clear()
        self.customer_search.clear()
        self.load_data()


# ══════════════════════════════════════════
#  Transaction Screen
# ══════════════════════════════════════════

class TransactionScreen(ScreenShell):
    transaction_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("إضافة عملية", "شحن صادر أو استلام وارد")
        self._build_content()

    def _build_content(self):
        c = self.content()
        c.setContentsMargins(0, 0, 0, 0)  # tabs handle their own margins

        self.tabs = QTabWidget()

        self.outbound_tab = OutboundTab()
        self.outbound_tab.transaction_added.connect(self._on_added)
        self.tabs.addTab(self.outbound_tab, "📤  شحن صادر")

        self.inbound_tab = InboundTab()
        self.inbound_tab.transaction_added.connect(self._on_added)
        self.tabs.addTab(self.inbound_tab, "📥  استلام وارد")

        c.addWidget(self.tabs)

    def refresh(self):
        self.outbound_tab.load_data()
        self.inbound_tab.load_data()

    def _on_added(self):
        self.transaction_added.emit()
        self.refresh()