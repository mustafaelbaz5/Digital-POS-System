"""
transaction_form.py — شاشة إضافة العمليات
tasks: 11 (spacing), 12 (remove profit frame), instapay support, RTL
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit,
    QTabWidget, QCheckBox, QDoubleSpinBox,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.styles.theme import (
    COLORS, FONT, GAP_XS, GAP_SM, GAP_MD, GAP_LG, MARGIN_CARD
)
from ui.components.widgets import ScreenShell, make_divider, CardGroup
from utils.formatters import fmt_currency

import database as db


def field(label_text: str, widget: QWidget) -> QVBoxLayout:
    lbl = QLabel(label_text)
    lbl.setObjectName("label_field")
    lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    box = QVBoxLayout()
    box.setSpacing(GAP_XS + 2)
    box.addWidget(lbl)
    box.addWidget(widget)
    return box


# ══════════════════════════════════════════
#  Payment Status Selector
# ══════════════════════════════════════════

class PaymentStatusSelector(QFrame):
    status_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(44)
        self._current = "pending"
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        self._btn_pending = self._make_btn("⏳  مؤجل",    "pending")
        self._btn_paid    = self._make_btn("  تم السداد", "paid")
        layout.addWidget(self._btn_pending)
        layout.addWidget(self._btn_paid)
        self._apply("pending")

    def _make_btn(self, text, val):
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._apply(val))
        return btn

    def _apply(self, val):
        self._current = val
        active_pending = (val == "pending")
        self._btn_pending.setStyleSheet(
            f"background:{COLORS['yellow_bg']};color:{COLORS['yellow']};"
            f"border:1.5px solid {COLORS['yellow']};border-radius:8px;"
            f"font-weight:bold;font-size:13px;padding:2px 14px;"
            if active_pending else
            f"background:{COLORS['bg_input']};color:{COLORS['text_muted']};"
            f"border:1px solid {COLORS['border']};border-radius:8px;"
            f"font-size:13px;padding:2px 14px;"
        )
        self._btn_paid.setStyleSheet(
            f"background:{COLORS['green_bg']};color:{COLORS['green']};"
            f"border:1.5px solid {COLORS['green']};border-radius:8px;"
            f"font-weight:bold;font-size:13px;padding:2px 14px;"
            if not active_pending else
            f"background:{COLORS['bg_input']};color:{COLORS['text_muted']};"
            f"border:1px solid {COLORS['border']};border-radius:8px;"
            f"font-size:13px;padding:2px 14px;"
        )
        self.status_changed.emit(val)

    def value(self) -> str: return self._current
    def set_value(self, val: str): self._apply(val)


# ══════════════════════════════════════════
#  Delivery Status Selector
# ══════════════════════════════════════════

class DeliveryStatusSelector(QFrame):

    def __init__(self, effect_label: QLabel, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(46)
        self._delivered = True
        self._effect_lbl = effect_label
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        title = QLabel("تسليم الكاش للعميل:")
        title.setObjectName("label_field")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)
        layout.addStretch()
        self._btn_no  = self._make_btn("⏳  لم يُسلَّم بعد", False)
        self._btn_yes = self._make_btn("  تم التسليم",    True)
        layout.addWidget(self._btn_no)
        layout.addWidget(self._btn_yes)
        self._apply(False)

    def _make_btn(self, text, val):
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._apply(val))
        return btn

    def _apply(self, delivered: bool):
        self._delivered = delivered
        self._btn_yes.setStyleSheet(
            f"background:{COLORS['green_bg']};color:{COLORS['green']};"
            f"border:1.5px solid {COLORS['green']};border-radius:8px;"
            f"font-weight:bold;font-size:12px;padding:2px 10px;"
            if delivered else
            f"background:{COLORS['bg_input']};color:{COLORS['text_muted']};"
            f"border:1px solid {COLORS['border']};border-radius:8px;"
            f"font-size:12px;padding:2px 10px;"
        )
        self._btn_no.setStyleSheet(
            f"background:{COLORS['yellow_bg']};color:{COLORS['yellow']};"
            f"border:1.5px solid {COLORS['yellow']};border-radius:8px;"
            f"font-weight:bold;font-size:12px;padding:2px 10px;"
            if not delivered else
            f"background:{COLORS['bg_input']};color:{COLORS['text_muted']};"
            f"border:1px solid {COLORS['border']};border-radius:8px;"
            f"font-size:12px;padding:2px 10px;"
        )
        if self._effect_lbl:
            if delivered:
                self._effect_lbl.setText(" المبلغ تم تسليمه للعميل")
                self._effect_lbl.setStyleSheet(f"color:{COLORS['green']};font-size:11px;")
            else:
                self._effect_lbl.setText("⏳ المبلغ المسلم يُسجَّل كمستحق للعميل (يُخصم من مديونيته)")
                self._effect_lbl.setStyleSheet(f"color:{COLORS['yellow']};font-size:11px;")

    def value(self) -> bool: return self._delivered
    def reset(self): self._apply(True)


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
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_LG)

        # ── Section 1: Platform & Service
        info_group = CardGroup("🏢  بيانات الخدمة")
        
        row1 = QHBoxLayout(); row1.setSpacing(GAP_MD)
        self.platform_combo = QComboBox()
        self.platform_combo.setMinimumWidth(300)
        self.platform_combo.currentIndexChanged.connect(self._update_balance)
        row1.addLayout(field("المنصة *", self.platform_combo))
        
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("مثال: شحن رصيد، تحويل...")
        row1.addLayout(field("اسم الخدمة *", self.service_input))
        info_group.add_layout(row1)

        self.balance_lbl = QLabel("")
        self.balance_lbl.setStyleSheet(
            f"color:{COLORS['teal_bright']};font-size:12px;"
            f"background:{COLORS['bg_input']};border-radius:6px;padding:6px 12px;"
        )
        self.balance_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_group.add_widget(self.balance_lbl)
        layout.addWidget(info_group)

        # ── Section 2: Amounts & Customer
        financial_group = CardGroup("💰  المبالغ والعملاء")
        
        row2 = QHBoxLayout(); row2.setSpacing(GAP_MD)
        self.amount_spent = QDoubleSpinBox()
        self.amount_spent.setRange(0.01, 9_999_999); self.amount_spent.setDecimals(2)
        self.amount_spent.setSuffix(" ج"); self.amount_spent.valueChanged.connect(self._calc_profit)
        row2.addLayout(field("المبلغ المصروف (من المنصة) *", self.amount_spent))
        
        self.amount_required = QDoubleSpinBox()
        self.amount_required.setRange(0.01, 9_999_999); self.amount_required.setDecimals(2)
        self.amount_required.setSuffix(" ج"); self.amount_required.valueChanged.connect(self._calc_profit)
        row2.addLayout(field("المبلغ المطلوب (من العميل) *", self.amount_required))
        financial_group.add_layout(row2)

        profit_row = QHBoxLayout()
        profit_lbl_title = QLabel("الربح المتوقع:")
        profit_lbl_title.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:12px;")
        profit_row.addWidget(profit_lbl_title)
        profit_row.addStretch()
        self.profit_label = QLabel("0.00 ج")
        self.profit_label.setStyleSheet(f"color:{COLORS['green']};font-size:16px;font-weight:bold;")
        profit_row.addWidget(self.profit_label)
        financial_group.add_layout(profit_row)

        financial_group.add_widget(make_divider())

        # Customer selection
        cust_search_row = QHBoxLayout(); cust_search_row.setSpacing(GAP_SM)
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("🔍 ابحث باسم أو تليفون...")
        self.customer_search.setFixedHeight(38)
        self.customer_search.textChanged.connect(self._filter_customers)
        cust_search_row.addLayout(field("ابحث عن عميل", self.customer_search))
        
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(200)
        cust_search_row.addLayout(field("اختر العميل *", self.customer_combo))
        financial_group.add_layout(cust_search_row)
        layout.addWidget(financial_group)

        # ── Section 3: Status & Notes
        status_group = CardGroup("  الحالة والملاحظات")
        
        status_layout = QVBoxLayout(); status_layout.setSpacing(GAP_SM)
        self.status_selector = PaymentStatusSelector()
        status_layout.addLayout(field("حالة الدفع *", self.status_selector))
        status_group.add_layout(status_layout)

        row4 = QHBoxLayout(); row4.setSpacing(GAP_MD)
        self.ref_input = QLineEdit(); self.ref_input.setPlaceholderText("رقم المرجع / العملية")
        row4.addLayout(field("رقم المرجع", self.ref_input))
        
        self.is_card_check = QCheckBox("كارت (بدون رقم عملية)")
        self.is_card_check.stateChanged.connect(lambda s: self.ref_input.setEnabled(not bool(s)))
        row4.addLayout(field("إضافي", self.is_card_check))
        status_group.add_layout(row4)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        status_group.add_layout(field("ملاحظات", self.notes_input))
        layout.addWidget(status_group)

        layout.addStretch()

        save_btn = QPushButton("  حفظ العملية الصادرة")
        save_btn.setObjectName("btn_primary"); save_btn.setFixedHeight(46)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def load_data(self):
        self.platform_combo.clear()
        for p in db.get_all_platforms():
            if p["type"] == "machine":   icon = "🏧"
            elif p["type"] == "wallet":  icon = "💳"
            else:                         icon = "🔷"
            self.platform_combo.addItem(
                f"{icon} {p['name']}  ({fmt_currency(p['balance'])})", p["id"]
            )
        self._all_customers = db.get_all_customers()
        self._fill_customers(self._all_customers)
        self._update_balance()

    def _fill_customers(self, customers):
        self.customer_combo.clear()
        for c in customers:
            lbl = c["name"] + (f"  ({c['phone']})" if c.get("phone") else "")
            self.customer_combo.addItem(lbl, c["id"])

    def _filter_customers(self, text):
        if not text.strip():
            self._fill_customers(self._all_customers); return
        self._fill_customers([c for c in self._all_customers
                               if text in c["name"] or text in (c.get("phone") or "")])

    def _update_balance(self):
        pid = self.platform_combo.currentData()
        if pid:
            p = db.get_platform_by_id(pid)
            if p:
                self.balance_lbl.setText(f"الرصيد الحالي:  {fmt_currency(p['balance'])}")

    def _calc_profit(self):
        profit = self.amount_required.value() - self.amount_spent.value()
        color  = COLORS["green"] if profit >= 0 else COLORS["red"]
        self.profit_label.setText(f"{profit:,.2f} ج")
        self.profit_label.setStyleSheet(f"color:{color};font-size:16px;font-weight:bold;")

    def _save(self):
        pid = self.platform_combo.currentData(); cid = self.customer_combo.currentData()
        service = self.service_input.text().strip()
        spent = self.amount_spent.value(); req = self.amount_required.value()
        status = self.status_selector.value()
        if not pid:     QMessageBox.warning(self, "تنبيه", "اختر المنصة");       return
        if not cid:     QMessageBox.warning(self, "تنبيه", "اختر العميل");       return
        if not service: QMessageBox.warning(self, "تنبيه", "أدخل اسم الخدمة");  return
        if spent <= 0:  QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المصروف"); return
        if req <= 0:    QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المطلوب"); return
        try:
            db.add_outbound_transaction(
                platform_id=pid, customer_id=cid, service_name=service,
                amount_spent=spent, amount_required=req, payment_status=status,
                reference_no=self.ref_input.text().strip(),
                is_card=self.is_card_check.isChecked(),
                notes=self.notes_input.toPlainText().strip()
            )
            QMessageBox.information(self, "تم ",
                f"تم تسجيل العملية\nالربح: {fmt_currency(req - spent)}\n"
                f"الحالة: {'مؤجل ⏳' if status == 'pending' else 'تم السداد '}")
            self._reset(); self.transaction_added.emit()
        except ValueError as e:
            QMessageBox.warning(self, "تعذّر تنفيذ العملية", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _reset(self):
        self.service_input.clear(); self.amount_spent.setValue(0.01)
        self.amount_required.setValue(0.01); self.ref_input.clear()
        self.is_card_check.setChecked(False); self.notes_input.clear()
        self.customer_search.clear(); self.status_selector.set_value("pending")
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
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_LG)

        note = QLabel("📌  عملية الاستلام متاحة للمحافظ الإلكترونية وانستا باي فقط")
        note.setStyleSheet(
            f"color:{COLORS['cyan']};background:{COLORS['cyan_bg']};"
            f"border:1px solid {COLORS['border_light']};"
            f"border-radius:8px;padding:10px 16px;font-size:12px;")
        note.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(note)

        # ── Section 1: Wallet & Service
        info_group = CardGroup("🏢  بيانات الاستلام")
        
        row1 = QHBoxLayout(); row1.setSpacing(GAP_MD)
        self.wallet_combo = QComboBox(); self.wallet_combo.setMinimumWidth(200)
        self.wallet_combo.currentIndexChanged.connect(self._update_wallet_info)
        row1.addLayout(field("المحفظة / انستا باي *", self.wallet_combo))
        
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("مثال: استلام تحويل فودافون")
        row1.addLayout(field("اسم الخدمة *", self.service_input))
        info_group.add_layout(row1)

        info_group.add_widget(self._make_info_bar())
        layout.addWidget(info_group)

        # ── Section 2: Amounts & Customer
        financial_group = CardGroup("💰  المبالغ والعملاء")
        
        row2 = QHBoxLayout(); row2.setSpacing(GAP_MD)
        self.amount_received = QDoubleSpinBox()
        self.amount_received.setRange(0.01, 9_999_999); self.amount_received.setDecimals(2)
        self.amount_received.setSuffix(" ج"); self.amount_received.valueChanged.connect(self._calc_profit)
        row2.addLayout(field("المبلغ المستلم في المحفظة *", self.amount_received))
        
        self.amount_delivered = QDoubleSpinBox()
        self.amount_delivered.setRange(0.01, 9_999_999); self.amount_delivered.setDecimals(2)
        self.amount_delivered.setSuffix(" ج"); self.amount_delivered.valueChanged.connect(self._calc_profit)
        row2.addLayout(field("المبلغ المسلم كاش *", self.amount_delivered))
        financial_group.add_layout(row2)

        profit_row = QHBoxLayout()
        p_title = QLabel("الربح المتوقع:")
        p_title.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:12px;")
        profit_row.addWidget(p_title); profit_row.addStretch()
        self.profit_label = QLabel("0.00 ج")
        self.profit_label.setStyleSheet(f"color:{COLORS['green']};font-size:16px;font-weight:bold;")
        profit_row.addWidget(self.profit_label)
        financial_group.add_layout(profit_row)

        financial_group.add_widget(make_divider())

        # Customer selection
        cust_row = QHBoxLayout(); cust_row.setSpacing(GAP_SM)
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("🔍 ابحث باسم أو تليفون...")
        self.customer_search.setFixedHeight(38)
        self.customer_search.textChanged.connect(self._filter_customers)
        cust_row.addLayout(field("العميل (مُحوِّل المبلغ)", self.customer_search))
        
        self.customer_combo = QComboBox(); self.customer_combo.setMinimumWidth(200)
        cust_row.addLayout(field("اختر العميل", self.customer_combo))
        financial_group.add_layout(cust_row)
        layout.addWidget(financial_group)

        # ── Section 3: Status & Notes
        status_group = CardGroup("  الحالة والملاحظات")
        
        self.ref_input = QLineEdit(); self.ref_input.setPlaceholderText("رقم المرجع")
        status_group.add_layout(field("رقم المرجع", self.ref_input))

        self._effect_lbl = QLabel("")
        self._effect_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.delivery_selector = DeliveryStatusSelector(self._effect_lbl)
        status_group.add_layout(field("تسليم الكاش للعميل", self.delivery_selector))
        status_group.add_widget(self._effect_lbl)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        status_group.add_layout(field("ملاحظات", self.notes_input))
        layout.addWidget(status_group)

        layout.addStretch()

        save_btn = QPushButton("  حفظ العملية الواردة")
        save_btn.setObjectName("btn_primary"); save_btn.setFixedHeight(46)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _make_info_bar(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("card"); frame.setFixedHeight(46)
        layout = QHBoxLayout(frame); layout.setContentsMargins(16, 0, 16, 0); layout.setSpacing(20)
        self.cash_lbl = QLabel("")
        self.cash_lbl.setStyleSheet(f"color:{COLORS['green']};font-size:12px;")
        layout.addWidget(self.cash_lbl); layout.addStretch()
        self.limit_lbl = QLabel("")
        self.limit_lbl.setStyleSheet(f"color:{COLORS['text_secondary']};font-size:12px;")
        layout.addWidget(self.limit_lbl)
        return frame

    def load_data(self):
        self.wallet_combo.clear()
        for w in db.get_all_platforms():
            if w["type"] not in ("wallet", "instapay"): continue
            icon = "💳" if w["type"] == "wallet" else "🔷"
            pct = int(w.get("monthly_used", 0) / max(w.get("monthly_limit", 1), 1) * 100)
            self.wallet_combo.addItem(f"{icon} {w['name']}  ({fmt_currency(w['balance'])})  — {pct}%", w["id"])
        self._all_customers = db.get_all_customers()
        self._fill_customers(self._all_customers)
        self._update_wallet_info()

    def _fill_customers(self, customers):
        self.customer_combo.clear()
        self.customer_combo.addItem("بدون عميل محدد", None)
        for c in customers:
            lbl = c["name"] + (f"  ({c['phone']})" if c.get("phone") else "")
            self.customer_combo.addItem(lbl, c["id"])

    def _filter_customers(self, text):
        if not text.strip():
            self._fill_customers(self._all_customers); return
        self._fill_customers([c for c in self._all_customers
                               if text in c["name"] or text in (c.get("phone") or "")])

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
                self.limit_lbl.setStyleSheet(f"color:{color};font-size:12px;")

    def _calc_profit(self):
        profit = self.amount_received.value() - self.amount_delivered.value()
        color  = COLORS["green"] if profit >= 0 else COLORS["red"]
        self.profit_label.setText(f"{profit:,.2f} ج")
        self.profit_label.setStyleSheet(f"color:{color};font-size:16px;font-weight:bold;")

    def _save(self):
        wid = self.wallet_combo.currentData(); cid = self.customer_combo.currentData()
        service = self.service_input.text().strip()
        received = self.amount_received.value(); delivered = self.amount_delivered.value()
        is_delivered = self.delivery_selector.value()
        if not wid:       QMessageBox.warning(self, "تنبيه", "اختر المحفظة");         return
        if not service:   QMessageBox.warning(self, "تنبيه", "أدخل اسم الخدمة");     return
        if received <= 0: QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المستلم"); return
        if delivered <= 0: QMessageBox.warning(self, "تنبيه", "أدخل المبلغ المسلم"); return
        try:
            db.add_inbound_transaction(
                wallet_id=wid, customer_id=cid, service_name=service,
                amount_received=received, amount_delivered=delivered,
                reference_no=self.ref_input.text().strip(),
                notes=self.notes_input.toPlainText().strip(),
                is_delivered=is_delivered
            )
            extra = ""
            if cid:
                extra = "\n تم تسليم الكاش للعميل" if is_delivered else \
                        f"\n⏳ {fmt_currency(delivered)} مسجلة كمستحقة للعميل"
            QMessageBox.information(self, "تم ",
                f"تم تسجيل الاستلام\nالربح: {fmt_currency(received - delivered)}{extra}")
            self._reset(); self.transaction_added.emit()
        except ValueError as e:
            QMessageBox.warning(self, "تعذّر تنفيذ العملية", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _reset(self):
        self.service_input.clear(); self.amount_received.setValue(0.01)
        self.amount_delivered.setValue(0.01); self.ref_input.clear()
        self.notes_input.clear(); self.customer_search.clear()
        self.delivery_selector.reset(); self.load_data()


# ══════════════════════════════════════════
#  Transaction Screen
# ══════════════════════════════════════════

class TransactionScreen(ScreenShell):
    transaction_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("إضافة عملية", "شحن صادر أو استلام وارد")
        self._build_content()

    def _build_content(self):
        c = self.content(); c.setContentsMargins(0, 0, 0, 0)
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
