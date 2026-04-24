"""
Transaction Form — شاشة إضافة العمليات (شحن صادر / استلام وارد)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit,
    QTabWidget, QCheckBox, QDoubleSpinBox,
    QMessageBox, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.styles.theme import COLORS
from ui.components.widgets import SectionTitle
from utils.formatters import fmt_currency

import database as db


# ══════════════════════════════════════════
#  Helper: حقل بعنوان
# ══════════════════════════════════════════

def labeled(label_text: str, widget: QWidget) -> QVBoxLayout:
    lbl = QLabel(label_text)
    lbl.setObjectName("label_field")
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
    box = QVBoxLayout()
    box.setSpacing(4)
    box.addWidget(lbl)
    box.addWidget(widget)
    return box


# ══════════════════════════════════════════
#  تاب الشحن الصادر (Outbound)
# ══════════════════════════════════════════

class OutboundTab(QWidget):
    """تاب إضافة عملية شحن صادر"""
    transaction_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ── الصف الأول: المنصة + الخدمة
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self.platform_combo = QComboBox()
        self.platform_combo.setFixedHeight(40)
        self.platform_combo.currentIndexChanged.connect(self._update_balance_label)
        row1.addLayout(labeled("المنصة *", self.platform_combo))

        self.service_input = QLineEdit()
        self.service_input.setFixedHeight(40)
        self.service_input.setPlaceholderText("مثال: شحن رصيد، تحويل...")
        row1.addLayout(labeled("اسم الخدمة *", self.service_input))

        layout.addLayout(row1)

        # رصيد المنصة الحالي
        self.balance_label = QLabel("")
        self.balance_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.balance_label)

        # ── الصف الثاني: المبالغ
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        self.amount_spent = QDoubleSpinBox()
        self.amount_spent.setFixedHeight(40)
        self.amount_spent.setRange(0.01, 9_999_999)
        self.amount_spent.setDecimals(2)
        self.amount_spent.setSuffix(" ج")
        self.amount_spent.valueChanged.connect(self._calc_profit)
        row2.addLayout(labeled("المبلغ المصروف (من المنصة) *", self.amount_spent))

        self.amount_required = QDoubleSpinBox()
        self.amount_required.setFixedHeight(40)
        self.amount_required.setRange(0.01, 9_999_999)
        self.amount_required.setDecimals(2)
        self.amount_required.setSuffix(" ج")
        self.amount_required.valueChanged.connect(self._calc_profit)
        row2.addLayout(labeled("المبلغ المطلوب (من العميل) *", self.amount_required))

        layout.addLayout(row2)

        # شريط الربح
        self.profit_bar = self._make_profit_bar()
        layout.addWidget(self.profit_bar)

        # ── الصف الثالث: العميل + حالة الدفع
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        # العميل مع بحث
        customer_box = QVBoxLayout()
        customer_box.setSpacing(4)
        customer_lbl = QLabel("العميل *")
        customer_lbl.setObjectName("label_field")
        customer_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        customer_box.addWidget(customer_lbl)

        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("🔍 ابحث عن عميل...")
        self.customer_search.setFixedHeight(36)
        self.customer_search.textChanged.connect(self._filter_customers)
        customer_box.addWidget(self.customer_search)

        self.customer_combo = QComboBox()
        self.customer_combo.setFixedHeight(40)
        customer_box.addWidget(self.customer_combo)
        row3.addLayout(customer_box)

        # حالة الدفع
        status_box = QVBoxLayout()
        status_box.setSpacing(4)
        status_lbl = QLabel("حالة الدفع *")
        status_lbl.setObjectName("label_field")
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_box.addWidget(status_lbl)

        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(40)
        self.status_combo.addItem("💵 نقدي",  "cash")
        self.status_combo.addItem("⏳ مؤجل",  "pending")
        status_box.addWidget(self.status_combo)

        status_box.addStretch()
        row3.addLayout(status_box)

        layout.addLayout(row3)

        # ── الصف الرابع: رقم العملية + كارت
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        self.ref_input = QLineEdit()
        self.ref_input.setFixedHeight(40)
        self.ref_input.setPlaceholderText("رقم المرجع / العملية")
        row4.addLayout(labeled("رقم المرجع", self.ref_input))

        card_box = QVBoxLayout()
        card_box.setSpacing(4)
        spacer_lbl = QLabel(" ")
        card_box.addWidget(spacer_lbl)
        self.is_card_check = QCheckBox("كارت (بدون رقم عملية)")
        self.is_card_check.stateChanged.connect(self._toggle_ref)
        card_box.addWidget(self.is_card_check)
        card_box.addStretch()
        row4.addLayout(card_box)

        layout.addLayout(row4)

        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        layout.addLayout(labeled("ملاحظات", self.notes_input))

        layout.addStretch()

        # زرار الحفظ
        save_btn = QPushButton("✅  حفظ العملية")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(44)
        save_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _make_profit_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(50)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)

        lbl = QLabel("الربح المتوقع:")
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(lbl)

        layout.addStretch()

        self.profit_label = QLabel("0.00 ج")
        self.profit_label.setStyleSheet(
            f"color: {COLORS['green']}; font-size: 16px; font-weight: bold;"
        )
        layout.addWidget(self.profit_label)

        return frame

    def load_data(self):
        """تحميل المنصات والعملاء"""
        # المنصات
        self.platform_combo.clear()
        for p in db.get_all_platforms():
            label = f"{'🏧' if p['type'] == 'machine' else '💳'} {p['name']}  ({fmt_currency(p['balance'])})"
            self.platform_combo.addItem(label, p["id"])

        self._all_customers = db.get_all_customers()
        self._fill_customers(self._all_customers)
        self._update_balance_label()

    def _fill_customers(self, customers: list):
        self.customer_combo.clear()
        for c in customers:
            label = f"{c['name']}"
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

    def _update_balance_label(self):
        pid = self.platform_combo.currentData()
        if pid:
            p = db.get_platform_by_id(pid)
            if p:
                self.balance_label.setText(
                    f"الرصيد الحالي: {fmt_currency(p['balance'])}"
                )

    def _calc_profit(self):
        profit = self.amount_required.value() - self.amount_spent.value()
        color  = COLORS["green"] if profit >= 0 else COLORS["red"]
        self.profit_label.setText(f"{profit:,.2f} ج")
        self.profit_label.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: bold;"
        )

    def _toggle_ref(self, state):
        self.ref_input.setEnabled(not bool(state))
        if state:
            self.ref_input.clear()

    def _save(self):
        platform_id  = self.platform_combo.currentData()
        customer_id  = self.customer_combo.currentData()
        service_name = self.service_input.text().strip()
        spent        = self.amount_spent.value()
        required     = self.amount_required.value()
        status       = self.status_combo.currentData()

        if not platform_id:
            QMessageBox.warning(self, "تنبيه", "اختر المنصة"); return
        if not customer_id:
            QMessageBox.warning(self, "تنبيه", "اختر العميل"); return
        if not service_name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الخدمة"); return
        if spent <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المصروف"); return
        if required <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المطلوب"); return

        try:
            db.add_outbound_transaction(
                platform_id    = platform_id,
                customer_id    = customer_id,
                service_name   = service_name,
                amount_spent   = spent,
                amount_required= required,
                payment_status = status,
                reference_no   = self.ref_input.text().strip(),
                is_card        = self.is_card_check.isChecked(),
                notes          = self.notes_input.toPlainText().strip()
            )
            QMessageBox.information(
                self, "تم ✅",
                f"تم تسجيل العملية بنجاح\nالربح: {fmt_currency(required - spent)}"
            )
            self._reset_form()
            self.transaction_added.emit()

        except ValueError as e:
            QMessageBox.warning(self, "تعذّر تنفيذ العملية", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _reset_form(self):
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
#  تاب الاستلام الوارد (Inbound)
# ══════════════════════════════════════════

class InboundTab(QWidget):
    """تاب إضافة عملية استلام وارد (محافظ فقط)"""
    transaction_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # إشعار
        note = QLabel("📌  عملية الاستلام متاحة للمحافظ الإلكترونية فقط")
        note.setStyleSheet(
            f"color: {COLORS['blue_light']}; background: {COLORS['bg_input']};"
            f"border-radius: 8px; padding: 8px 14px; font-size: 13px;"
        )
        note.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(note)

        # ── الصف الأول: المحفظة + الخدمة
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self.wallet_combo = QComboBox()
        self.wallet_combo.setFixedHeight(40)
        self.wallet_combo.currentIndexChanged.connect(self._update_wallet_info)
        row1.addLayout(labeled("المحفظة *", self.wallet_combo))

        self.service_input = QLineEdit()
        self.service_input.setFixedHeight(40)
        self.service_input.setPlaceholderText("مثال: استلام تحويل فودافون")
        row1.addLayout(labeled("اسم الخدمة *", self.service_input))

        layout.addLayout(row1)

        # معلومات المحفظة والكاش
        self.info_bar = self._make_info_bar()
        layout.addWidget(self.info_bar)

        # ── الصف الثاني: المبالغ
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        self.amount_received = QDoubleSpinBox()
        self.amount_received.setFixedHeight(40)
        self.amount_received.setRange(0.01, 9_999_999)
        self.amount_received.setDecimals(2)
        self.amount_received.setSuffix(" ج")
        self.amount_received.valueChanged.connect(self._calc_profit)
        row2.addLayout(labeled("المبلغ المستلم في المحفظة *", self.amount_received))

        self.amount_delivered = QDoubleSpinBox()
        self.amount_delivered.setFixedHeight(40)
        self.amount_delivered.setRange(0.01, 9_999_999)
        self.amount_delivered.setDecimals(2)
        self.amount_delivered.setSuffix(" ج")
        self.amount_delivered.valueChanged.connect(self._calc_profit)
        row2.addLayout(labeled("المبلغ المسلم كاش *", self.amount_delivered))

        layout.addLayout(row2)

        # شريط الربح
        self.profit_bar = self._make_profit_bar()
        layout.addWidget(self.profit_bar)

        # ── الصف الثالث: العميل + رقم المرجع
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        customer_box = QVBoxLayout()
        customer_box.setSpacing(4)
        c_lbl = QLabel("العميل")
        c_lbl.setObjectName("label_field")
        c_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        customer_box.addWidget(c_lbl)

        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("🔍 ابحث عن عميل...")
        self.customer_search.setFixedHeight(36)
        self.customer_search.textChanged.connect(self._filter_customers)
        customer_box.addWidget(self.customer_search)

        self.customer_combo = QComboBox()
        self.customer_combo.setFixedHeight(40)
        customer_box.addWidget(self.customer_combo)
        row3.addLayout(customer_box)

        self.ref_input = QLineEdit()
        self.ref_input.setFixedHeight(40)
        self.ref_input.setPlaceholderText("رقم المرجع")
        row3.addLayout(labeled("رقم المرجع", self.ref_input))

        layout.addLayout(row3)

        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        layout.addLayout(labeled("ملاحظات", self.notes_input))

        layout.addStretch()

        # زرار الحفظ
        save_btn = QPushButton("✅  حفظ العملية")
        save_btn.setObjectName("btn_success")
        save_btn.setFixedHeight(44)
        save_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _make_info_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(50)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)

        self.cash_label = QLabel("")
        self.cash_label.setStyleSheet(f"color: {COLORS['green']};")
        layout.addWidget(self.cash_label)

        layout.addStretch()

        self.limit_label = QLabel("")
        self.limit_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.limit_label)

        return frame

    def _make_profit_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(50)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)

        lbl = QLabel("الربح المتوقع:")
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(lbl)

        layout.addStretch()

        self.profit_label = QLabel("0.00 ج")
        self.profit_label.setStyleSheet(
            f"color: {COLORS['green']}; font-size: 16px; font-weight: bold;"
        )
        layout.addWidget(self.profit_label)

        return frame

    def load_data(self):
        """تحميل المحافظ والعملاء"""
        self.wallet_combo.clear()
        wallets = [p for p in db.get_all_platforms() if p["type"] == "wallet"]
        for w in wallets:
            pct   = int(w.get("monthly_used", 0) / w.get("monthly_limit", 200000) * 100)
            label = f"💳 {w['name']}  ({fmt_currency(w['balance'])})  — {pct}% شهري"
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
        wid = self.wallet_combo.currentData()
        budget = db.get_budget()
        self.cash_label.setText(f"الكاش المتاح: {fmt_currency(budget.get('cash_vault', 0))}")

        if wid:
            w = db.get_platform_by_id(wid)
            if w:
                used  = w.get("monthly_used", 0)
                limit = w.get("monthly_limit", 200000)
                remaining = limit - used
                color = COLORS["red"] if remaining < 10000 else COLORS["text_secondary"]
                self.limit_label.setText(
                    f"متبقي من الحد الشهري: {fmt_currency(remaining)}"
                )
                self.limit_label.setStyleSheet(f"color: {color};")

    def _calc_profit(self):
        profit = self.amount_received.value() - self.amount_delivered.value()
        color  = COLORS["green"] if profit >= 0 else COLORS["red"]
        self.profit_label.setText(f"{profit:,.2f} ج")
        self.profit_label.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: bold;"
        )

    def _save(self):
        wallet_id   = self.wallet_combo.currentData()
        customer_id = self.customer_combo.currentData()
        service     = self.service_input.text().strip()
        received    = self.amount_received.value()
        delivered   = self.amount_delivered.value()

        if not wallet_id:
            QMessageBox.warning(self, "تنبيه", "اختر المحفظة"); return
        if not service:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الخدمة"); return
        if received <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المستلم"); return
        if delivered <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المسلم"); return

        try:
            db.add_inbound_transaction(
                wallet_id        = wallet_id,
                customer_id      = customer_id,
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
            self._reset_form()
            self.transaction_added.emit()

        except ValueError as e:
            QMessageBox.warning(self, "تعذّر تنفيذ العملية", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _reset_form(self):
        self.service_input.clear()
        self.amount_received.setValue(0.01)
        self.amount_delivered.setValue(0.01)
        self.ref_input.clear()
        self.notes_input.clear()
        self.customer_search.clear()
        self.load_data()


# ══════════════════════════════════════════
#  الشاشة الرئيسية
# ══════════════════════════════════════════

class TransactionScreen(QWidget):
    """شاشة إضافة العمليات"""
    transaction_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(SectionTitle("➕ إضافة عملية", "شحن صادر أو استلام وارد"))

        self.tabs = QTabWidget()

        self.outbound_tab = OutboundTab()
        self.outbound_tab.transaction_added.connect(self._on_transaction_added)
        self.tabs.addTab(self.outbound_tab, "📤  شحن صادر")

        self.inbound_tab = InboundTab()
        self.inbound_tab.transaction_added.connect(self._on_transaction_added)
        self.tabs.addTab(self.inbound_tab, "📥  استلام وارد")

        layout.addWidget(self.tabs)

    def refresh(self):
        self.outbound_tab.load_data()
        self.inbound_tab.load_data()

    def _on_transaction_added(self):
        self.transaction_added.emit()
        self.refresh()