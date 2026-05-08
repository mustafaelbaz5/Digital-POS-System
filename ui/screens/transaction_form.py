"""
transaction_form.py — شاشة إضافة العمليات (Compact Pro Zero-Scroll)
"""

import datetime

from PyQt6.QtCore import QLocale, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import BaseDialog, show_toast
from ui.styles.theme import COLORS, FONT
from utils.formatters import fmt_currency


class FocusSpinBox(QDoubleSpinBox):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        QTimer.singleShot(0, self.selectAll)


class CompactTransactionTab(QWidget):
    transaction_added = pyqtSignal()

    def __init__(
        self,
        platform: dict,
        is_inbound: bool = False,
        selected_date: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self.platform = platform
        self.is_inbound = is_inbound
        self.selected_date = (
            selected_date or __import__("datetime").date.today().isoformat()
        )
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)  # Highly condensed

        # ── Row 1: Client & Payment
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_c = QLabel("العميل:")
        lbl_c.setStyleSheet(f"color:{COLORS['text_secondary']};")
        row1.addWidget(lbl_c)

        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_combo.lineEdit().setPlaceholderText(
            "ابحث باسم العميل أو رقم التليفون..."
        )
        # Style the main line edit
        self.customer_combo.lineEdit().setStyleSheet("padding: 5px; font-size: 14px;")
        row1.addWidget(self.customer_combo, 2)

        if not self.is_inbound:
            lbl_p = QLabel("نوع الدفع:")
            lbl_p.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row1.addWidget(lbl_p)

            self.payment_combo = QComboBox()
            self.payment_combo.addItem("⏳ مؤجل", "pending")
            self.payment_combo.addItem(" مسدد", "paid")
            row1.addWidget(self.payment_combo, 1)
        else:
            lbl_d = QLabel("تسليم الكاش:")
            lbl_d.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row1.addWidget(lbl_d)

            self.delivery_combo = QComboBox()
            self.delivery_combo.addItem(" تم التسليم", True)
            self.delivery_combo.addItem("⏳ لم يُسلَّم", False)
            row1.addWidget(self.delivery_combo, 1)

        layout.addLayout(row1)

        # ── Row 2: Service & Amount
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_s = QLabel("الخدمة:")
        lbl_s.setStyleSheet(f"color:{COLORS['text_secondary']};")
        row2.addWidget(lbl_s)

        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("اسم الخدمة...")
        row2.addWidget(self.service_input, 2)

        self.amount_spent = FocusSpinBox()
        loc = QLocale(QLocale.Language.English)
        self.amount_spent.setLocale(loc)
        self.amount_spent.setGroupSeparatorShown(True)
        self.amount_spent.setRange(0, 999999)
        self.amount_spent.setDecimals(2)
        self.amount_spent.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.amount_spent.setStyleSheet(
            f"font-weight:bold; color:{COLORS['accent']}; font-size:18px; padding: 4px;"
        )
        self.amount_spent.valueChanged.connect(self._update_profit)

        if not self.is_inbound:
            lbl_a1 = QLabel("المصروف:")
            lbl_a1.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row2.addWidget(lbl_a1)
            row2.addWidget(self.amount_spent, 1)

            self.amount_req = FocusSpinBox()
            self.amount_req.setLocale(loc)
            self.amount_req.setGroupSeparatorShown(True)
            self.amount_req.setRange(0, 999999)
            self.amount_req.setDecimals(2)
            self.amount_req.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            self.amount_req.setStyleSheet(
                f"font-weight:bold; color:{COLORS['accent']}; font-size:18px; padding: 4px;"
            )
            self.amount_req.valueChanged.connect(self._update_profit)
            lbl_a2 = QLabel("المطلوب:")
            lbl_a2.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row2.addWidget(lbl_a2)
            row2.addWidget(self.amount_req, 1)
        else:
            self.amount_req = FocusSpinBox()  # used for received
            self.amount_req.setLocale(loc)
            self.amount_req.setGroupSeparatorShown(True)
            self.amount_req.setRange(0, 999999)
            self.amount_req.setDecimals(2)
            self.amount_req.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            self.amount_req.setStyleSheet(
                f"font-weight:bold; color:{COLORS['accent']}; font-size:18px; padding: 4px;"
            )
            self.amount_req.valueChanged.connect(self._update_profit)
            lbl_a1 = QLabel("المستلم:")
            lbl_a1.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row2.addWidget(lbl_a1)
            row2.addWidget(self.amount_req, 1)

            lbl_a2 = QLabel("المسلم:")
            lbl_a2.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row2.addWidget(lbl_a2)
            row2.addWidget(self.amount_spent, 1)  # used for delivered

        layout.addLayout(row2)

        # Real-time profit
        profit_layout = QHBoxLayout()
        profit_layout.addStretch()
        self.profit_lbl = QLabel("الربح المتوقع: 0.00 ج")
        self.profit_lbl.setStyleSheet(
            f"background:{COLORS['accent_dim']}; color:{COLORS['green']}; border-radius:6px; padding:4px 10px; font-weight:bold; font-size:13px;"
        )
        profit_layout.addWidget(self.profit_lbl)
        layout.addLayout(profit_layout)

        # ── Row 3: Reference & Notes
        row3 = QHBoxLayout()
        row3.setSpacing(8)

        lbl_r = QLabel("المرجع:")
        lbl_r.setStyleSheet(f"color:{COLORS['text_secondary']};")
        row3.addWidget(lbl_r)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("اختياري...")
        self.ref_input.setFixedWidth(120)
        row3.addWidget(self.ref_input)

        lbl_n = QLabel("ملاحظات:")
        lbl_n.setStyleSheet(f"color:{COLORS['text_secondary']};")
        row3.addWidget(lbl_n)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات إضافية...")
        row3.addWidget(self.notes_input)

        layout.addLayout(row3)

        # ── Row 4: Read-Only Date Display
        row4 = QHBoxLayout()
        row4.setContentsMargins(0, 15, 0, 15)
        row4.setSpacing(10)

        lbl_d = QLabel("تاريخ العملية:")
        lbl_d.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-weight:bold; font-size:14px;"
        )
        row4.addWidget(lbl_d)

        self.date_label = QLabel(self.selected_date)
        self.date_label.setStyleSheet(
            f"font-size: 15px; font-weight: bold; background: {COLORS['bg_hover']};"
            f"padding: 6px 16px; border-radius: 6px; color: {COLORS['accent']};"
        )
        row4.addWidget(self.date_label)

        row4.addStretch()
        layout.addLayout(row4)

        # ── Row 5: Add Button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("➕ إضافة العملية (Enter)")
        self.save_btn.setObjectName("btn_primary")
        self.save_btn.setMinimumHeight(44)
        self.save_btn.setMinimumWidth(180)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        self.setTabOrder(self.ref_input, self.notes_input)
        self.setTabOrder(self.notes_input, self.save_btn)

        # Enter-to-focus for rapid entry
        self.customer_combo.lineEdit().returnPressed.connect(
            self.service_input.setFocus
        )
        if not self.is_inbound:
            self.service_input.returnPressed.connect(self.amount_spent.setFocus)
        else:
            self.service_input.returnPressed.connect(self.amount_req.setFocus)

        # Adjust tab order for date
        self.setTabOrder(self.service_input, self.amount_spent)
        self.setTabOrder(self.amount_spent, self.amount_req)
        self.setTabOrder(self.amount_req, self.save_btn)

    def _update_profit(self):
        spent = self.amount_spent.value()
        req = self.amount_req.value()
        # Inbound: req = received, spent = delivered
        # Outbound: req = required, spent = spent
        profit = req - spent

        color = COLORS["green"] if profit >= 0 else COLORS["red"]
        self.profit_lbl.setStyleSheet(
            f"background:{COLORS['accent_dim']}; color:{color}; border-radius:6px; padding:4px 10px; font-weight:bold; font-size:13px;"
        )
        self.profit_lbl.setText(f"الربح المتوقع: {fmt_currency(profit)}")

    def load_data(self):
        self.customer_combo.clear()

        client_list = []
        for c in db.get_all_customers():
            lbl = c["name"] + (f" ({c['phone']})" if c.get("phone") else "")
            self.customer_combo.addItem(lbl, c["id"])
            client_list.append(lbl)

        # Non-interruptive Search Logic
        comp = QCompleter(client_list, self)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        # Style the Popup
        popup = comp.popup()
        popup.setStyleSheet(f"""
            QAbstractItemView {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['accent']};
                selection-color: white;
                border: 1px solid {COLORS['border']};
                font-size: 14px;
            }}
        """)

        self.customer_combo.setCompleter(comp)

        # Service completer
        services = db.get_unique_service_names()
        comp_s = QCompleter(services, self)
        comp_s.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_s.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        comp_s.popup().setStyleSheet(
            f"background-color: {COLORS['bg_input']}; color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['border']}; font-family: {FONT['family']}; font-size: 14px;"
        )
        self.service_input.setCompleter(comp_s)
        self.customer_combo.setCurrentIndex(-1)
        self.customer_combo.setEditText("")

    def _selected_customer_id(self):
        cid = self.customer_combo.currentData()
        if cid:
            return cid

        typed = self.customer_combo.currentText().strip()
        if not typed:
            return None
        for i in range(self.customer_combo.count()):
            if self.customer_combo.itemText(i) == typed:
                self.customer_combo.setCurrentIndex(i)
                return self.customer_combo.itemData(i)
        return None

    def _save(self):
        cid = self._selected_customer_id()
        service = self.service_input.text().strip()
        spent = self.amount_spent.value()
        req = self.amount_req.value()
        ref = self.ref_input.text().strip()
        notes = self.notes_input.text().strip()

        if not cid or cid <= 0:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار عميل من القائمة لإتمام العملية. العمليات بدون عميل غير مسموح بها حالياً.")
            self.customer_combo.lineEdit().setFocus()
            return
        if not service:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الخدمة")
            return
        if spent <= 0 and req <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل المبلغ")
            return

        pid = self.platform["id"]
        # Use selected date with current time
        from datetime import datetime

        now_time = datetime.now().strftime("%H:%M:%S")
        created_at = f"{self.selected_date} {now_time}"

        try:
            if not self.is_inbound:
                status = self.payment_combo.currentData()
                if not cid and status == "pending":
                    QMessageBox.warning(self, "تنبيه", "اختر العميل للعمليات المؤجلة")
                    return
                db.add_outbound_transaction(
                    platform_id=pid,
                    customer_id=cid,
                    service_name=service,
                    amount_spent=spent,
                    amount_required=req,
                    payment_status=status,
                    reference_no=ref,
                    is_card=False,
                    notes=notes,
                    created_at=created_at,
                )
            else:
                is_del = self.delivery_combo.currentData()
                if not cid and not is_del:
                    QMessageBox.warning(
                        self, "تنبيه", "اختر العميل للعمليات غير المسلمة"
                    )
                    return
                db.add_inbound_transaction(
                    wallet_id=pid,
                    customer_id=cid,
                    service_name=service,
                    amount_received=req,
                    amount_delivered=spent,
                    reference_no=ref,
                    notes=notes,
                    is_delivered=is_del,
                    created_at=created_at,
                )

            self.transaction_added.emit()
            show_toast(self, "تمت إضافة العملية بنجاح", type="success")

            # Reset Fields
            self.amount_spent.setValue(0)
            self.amount_req.setValue(0)
            self.ref_input.clear()
            self.notes_input.clear()

            # Reset Selections (as requested)
            self.service_input.clear()
            self.customer_combo.setCurrentIndex(-1)
            self.customer_combo.setEditText("")  # Clear search text

            # Return focus to Client Search for rapid next entry
            self.customer_combo.lineEdit().setFocus()

        except Exception as e:
            show_toast(self, f"خطأ: {str(e)}", type="danger")


# ══════════════════════════════════════════════════════════════════
#  MachineTransactionTab — واجهة ماكينات متخصصة (كود الشحن)
# ══════════════════════════════════════════════════════════════════


class MachineTransactionTab(QWidget):
    """
    Machine outbound tab with:
    • Primary mode : shipping-code lookup with QCompleter + live client label
    • Toggle mode  : classic client-name combo
    • Progressive disclosure for service / reference / notes
    """

    transaction_added = pyqtSignal()

    _BTN_ACTIVE = "background:#059669;color:white;border:1px solid #059669;border-radius:4px;font-weight:bold;padding:4px 12px;"
    _BTN_IDLE   = "background:#21262D;color:#8B949E;border:1px solid #30363D;border-radius:4px;padding:4px 12px;"

    def __init__(self, platform: dict, selected_date: str = None, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.selected_date = selected_date or datetime.date.today().isoformat()
        self._code_mode = True
        self._resolved_cid: int | None = None
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_data()

    # ── UI construction ────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ── 0. Mode toggle ─────────────────────────────────────────
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(0)

        self._code_btn = QPushButton("🔑  بالكود")
        self._code_btn.setFixedHeight(30)
        self._code_btn.setStyleSheet(self._BTN_ACTIVE)
        self._code_btn.clicked.connect(lambda: self._switch_mode(True))
        toggle_row.addWidget(self._code_btn)

        self._name_btn = QPushButton("👤  بالاسم")
        self._name_btn.setFixedHeight(30)
        self._name_btn.setStyleSheet(self._BTN_IDLE)
        self._name_btn.clicked.connect(lambda: self._switch_mode(False))
        toggle_row.addWidget(self._name_btn)

        toggle_row.addStretch()
        root.addLayout(toggle_row)

        # ── 1a. Code-lookup panel ──────────────────────────────────
        self._code_panel = QWidget()
        cp = QVBoxLayout(self._code_panel)
        cp.setContentsMargins(0, 0, 0, 0)
        cp.setSpacing(5)

        cr = QHBoxLayout()
        lc = QLabel("كود الشحن:")
        lc.setStyleSheet(f"color:{COLORS['text_secondary']};font-weight:bold;")
        cr.addWidget(lc)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("ابحث أو أدخل الكود مباشرة...")
        self.code_input.setStyleSheet(
            f"font-size:15px;padding:5px;font-weight:bold;color:{COLORS['accent']};"
        )
        self.code_input.returnPressed.connect(self._on_code_enter)
        cr.addWidget(self.code_input, 1)
        cp.addLayout(cr)

        self._client_lbl = QLabel("—")
        self._client_lbl.setFixedHeight(30)
        self._client_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};font-size:12px;font-weight:bold;"
            f"background:{COLORS['bg_hover']};border-radius:6px;padding:0 12px;"
        )
        cp.addWidget(self._client_lbl)
        root.addWidget(self._code_panel)

        # ── 1b. Name-selection panel (hidden by default) ───────────
        self._name_panel = QWidget()
        self._name_panel.setVisible(False)
        np = QHBoxLayout(self._name_panel)
        np.setContentsMargins(0, 0, 0, 0)

        ln = QLabel("العميل:")
        ln.setStyleSheet(f"color:{COLORS['text_secondary']};font-weight:bold;")
        np.addWidget(ln)

        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_combo.lineEdit().setPlaceholderText("ابحث بالاسم أو التليفون...")
        self.customer_combo.lineEdit().setStyleSheet("padding:5px;font-size:14px;")
        np.addWidget(self.customer_combo, 1)
        root.addWidget(self._name_panel)

        # ── 2. Amounts ─────────────────────────────────────────────
        amt_row = QHBoxLayout()
        amt_row.setSpacing(8)
        loc = QLocale(QLocale.Language.English)

        for attr, label in [("amount_spent", "المصروف:"), ("amount_req", "المطلوب:")]:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{COLORS['text_secondary']};")
            amt_row.addWidget(lbl)
            sb = FocusSpinBox()
            sb.setLocale(loc)
            sb.setGroupSeparatorShown(True)
            sb.setRange(0, 9_999_999)
            sb.setDecimals(2)
            sb.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            sb.setStyleSheet(
                f"font-weight:bold;color:{COLORS['accent']};font-size:18px;padding:4px;"
            )
            sb.valueChanged.connect(self._update_profit)
            setattr(self, attr, sb)
            amt_row.addWidget(sb, 1)
        root.addLayout(amt_row)

        # Profit badge
        pr = QHBoxLayout()
        pr.addStretch()
        self._profit_lbl = QLabel("الربح المتوقع: 0.00 ج")
        self._profit_lbl.setStyleSheet(
            f"background:{COLORS['accent_dim']};color:{COLORS['green']};"
            f"border-radius:6px;padding:4px 10px;font-weight:bold;font-size:13px;"
        )
        pr.addWidget(self._profit_lbl)
        root.addLayout(pr)

        # ── 3. Payment status + date ───────────────────────────────
        pd_row = QHBoxLayout()
        pd_row.setSpacing(12)

        lp = QLabel("نوع الدفع:")
        lp.setStyleSheet(f"color:{COLORS['text_secondary']};")
        pd_row.addWidget(lp)

        self.payment_combo = QComboBox()
        self.payment_combo.addItem("⏳ مؤجل", "pending")
        self.payment_combo.addItem("✓ مسدد", "paid")
        pd_row.addWidget(self.payment_combo)

        pd_row.addStretch()

        ld = QLabel("تاريخ العملية:")
        ld.setStyleSheet(f"color:{COLORS['text_secondary']};font-weight:bold;")
        pd_row.addWidget(ld)

        self._date_lbl = QLabel(self.selected_date)
        self._date_lbl.setStyleSheet(
            f"font-size:14px;font-weight:bold;background:{COLORS['bg_hover']};"
            f"padding:4px 14px;border-radius:6px;color:{COLORS['accent']};"
        )
        pd_row.addWidget(self._date_lbl)
        root.addLayout(pd_row)

        # ── 4. "Show More" toggle ──────────────────────────────────
        more_row = QHBoxLayout()
        self._more_btn = QPushButton("▼  عرض المزيد")
        self._more_btn.setObjectName("btn_ghost")
        self._more_btn.setFixedHeight(26)
        self._more_btn.clicked.connect(self._toggle_more)
        more_row.addWidget(self._more_btn)
        more_row.addStretch()
        root.addLayout(more_row)

        # ── 4b. Extras panel (hidden) ──────────────────────────────
        self._extras = QWidget()
        self._extras.setVisible(False)
        ex = QVBoxLayout(self._extras)
        ex.setContentsMargins(0, 0, 0, 0)
        ex.setSpacing(6)

        ex_row1 = QHBoxLayout()
        ex_row1.setSpacing(8)

        ls = QLabel("الخدمة:")
        ls.setStyleSheet(f"color:{COLORS['text_secondary']};")
        ex_row1.addWidget(ls)
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("اسم الخدمة (افتراضي: شحن)...")
        ex_row1.addWidget(self.service_input, 2)

        lr = QLabel("المرجع:")
        lr.setStyleSheet(f"color:{COLORS['text_secondary']};")
        ex_row1.addWidget(lr)
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("اختياري...")
        self.ref_input.setFixedWidth(120)
        ex_row1.addWidget(self.ref_input)
        ex.addLayout(ex_row1)

        ex_row2 = QHBoxLayout()
        ln2 = QLabel("ملاحظات:")
        ln2.setStyleSheet(f"color:{COLORS['text_secondary']};")
        ex_row2.addWidget(ln2)
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات إضافية...")
        ex_row2.addWidget(self.notes_input)
        ex.addLayout(ex_row2)

        root.addWidget(self._extras)

        # ── 5. Add button ──────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("➕  إضافة العملية  (Enter)")
        self.save_btn.setObjectName("btn_primary")
        self.save_btn.setMinimumHeight(44)
        self.save_btn.setMinimumWidth(200)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

        self.setTabOrder(self.code_input, self.amount_spent)
        self.setTabOrder(self.amount_spent, self.amount_req)
        self.setTabOrder(self.amount_req, self.save_btn)

    # ── mode helpers ───────────────────────────────────────────────

    def _switch_mode(self, code_mode: bool):
        self._code_mode = code_mode
        self._resolved_cid = None
        self._code_panel.setVisible(code_mode)
        self._name_panel.setVisible(not code_mode)
        self._code_btn.setStyleSheet(self._BTN_ACTIVE if code_mode else self._BTN_IDLE)
        self._name_btn.setStyleSheet(self._BTN_ACTIVE if not code_mode else self._BTN_IDLE)
        if code_mode:
            QTimer.singleShot(50, self.code_input.setFocus)
        else:
            QTimer.singleShot(50, lambda: self.customer_combo.lineEdit().setFocus())

    def _toggle_more(self):
        visible = self._extras.isVisible()
        self._extras.setVisible(not visible)
        self._more_btn.setText("▲  إخفاء" if not visible else "▼  عرض المزيد")

    # ── code resolution ────────────────────────────────────────────

    def _on_code_enter(self):
        self._resolve_code(self.code_input.text().strip())
        self.amount_spent.setFocus()

    def _on_code_activated(self, code_text: str):
        self._resolve_code(code_text)

    def _resolve_code(self, code: str):
        if not code:
            return
        result = db.get_customer_by_shipping_code(code)
        if result:
            self._resolved_cid = result["id"]
            group = result.get("group_name") or "بدون مجموعة"
            self._client_lbl.setText(f"✓  {result['name']}  |  {group}")
            self._client_lbl.setStyleSheet(
                f"color:{COLORS['green']};font-size:12px;font-weight:bold;"
                f"background:{COLORS['green_bg']};border-radius:6px;padding:0 12px;"
            )
        else:
            self._resolved_cid = None
            self._client_lbl.setText(f"⚠  كود غير موجود: {code}")
            self._client_lbl.setStyleSheet(
                f"color:{COLORS['yellow']};font-size:12px;font-weight:bold;"
                f"background:{COLORS['yellow_bg']};border-radius:6px;padding:0 12px;"
            )

    # ── data loading ───────────────────────────────────────────────

    def load_data(self):
        # Shipping codes completer
        all_codes = db.get_all_shipping_codes()
        code_strings = [c["code"] for c in all_codes]

        comp_c = QCompleter(code_strings, self)
        comp_c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_c.setFilterMode(Qt.MatchFlag.MatchContains)
        comp_c.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        comp_c.popup().setStyleSheet(
            f"background:{COLORS['bg_elevated']};color:{COLORS['text_primary']};"
            f"selection-background-color:{COLORS['accent']};selection-color:white;"
            f"border:1px solid {COLORS['border']};font-size:14px;"
        )
        comp_c.activated.connect(self._on_code_activated)
        self.code_input.setCompleter(comp_c)

        # Customer name completer (name mode)
        self.customer_combo.clear()
        name_list = []
        for c in db.get_all_customers():
            label = c["name"] + (f" ({c['phone']})" if c.get("phone") else "")
            self.customer_combo.addItem(label, c["id"])
            name_list.append(label)

        comp_n = QCompleter(name_list, self)
        comp_n.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_n.setFilterMode(Qt.MatchFlag.MatchContains)
        comp_n.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        comp_n.popup().setStyleSheet(
            f"background:{COLORS['bg_elevated']};color:{COLORS['text_primary']};"
            f"selection-background-color:{COLORS['accent']};selection-color:white;"
            f"border:1px solid {COLORS['border']};font-size:14px;"
        )
        self.customer_combo.setCompleter(comp_n)
        self.customer_combo.setCurrentIndex(-1)
        self.customer_combo.setEditText("")

        # Service name completer
        svc = db.get_unique_service_names()
        comp_s = QCompleter(svc, self)
        comp_s.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_s.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        comp_s.popup().setStyleSheet(
            f"background:{COLORS['bg_input']};color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']};font-size:14px;"
        )
        self.service_input.setCompleter(comp_s)

    # ── profit ─────────────────────────────────────────────────────

    def _update_profit(self):
        profit = self.amount_req.value() - self.amount_spent.value()
        color = COLORS["green"] if profit >= 0 else COLORS["red"]
        self._profit_lbl.setStyleSheet(
            f"background:{COLORS['accent_dim']};color:{color};"
            f"border-radius:6px;padding:4px 10px;font-weight:bold;font-size:13px;"
        )
        self._profit_lbl.setText(f"الربح المتوقع: {fmt_currency(profit)}")

    # ── customer resolution ────────────────────────────────────────

    def _get_customer_id(self) -> int | None:
        if self._code_mode:
            return self._resolved_cid
        cid = self.customer_combo.currentData()
        if cid:
            return cid
        typed = self.customer_combo.currentText().strip()
        for i in range(self.customer_combo.count()):
            if self.customer_combo.itemText(i) == typed:
                self.customer_combo.setCurrentIndex(i)
                return self.customer_combo.itemData(i)
        return None

    # ── save ───────────────────────────────────────────────────────

    def _save(self):
        cid = self._get_customer_id()
        service = self.service_input.text().strip() or "شحن"
        spent = self.amount_spent.value()
        req = self.amount_req.value()
        status = self.payment_combo.currentData()
        ref = self.ref_input.text().strip()
        notes = self.notes_input.text().strip()

        if not cid:
            msg = ("يجب إدخال كود شحن صحيح" if self._code_mode
                   else "يجب اختيار عميل من القائمة")
            QMessageBox.warning(self, "تنبيه", msg)
            QTimer.singleShot(50, self.code_input.setFocus if self._code_mode
                              else self.customer_combo.lineEdit().setFocus)
            return
        if spent <= 0 and req <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل المبلغ")
            return

        created_at = f"{self.selected_date} {datetime.datetime.now().strftime('%H:%M:%S')}"
        try:
            db.add_outbound_transaction(
                platform_id=self.platform["id"],
                customer_id=cid,
                service_name=service,
                amount_spent=spent,
                amount_required=req,
                payment_status=status,
                reference_no=ref,
                is_card=False,
                notes=notes,
                created_at=created_at,
            )
            self.transaction_added.emit()
            show_toast(self, "تمت إضافة العملية بنجاح ✓", type="success")
            self._reset()
        except Exception as e:
            show_toast(self, f"خطأ: {e}", type="danger")

    def _reset(self):
        self.code_input.clear()
        self._resolved_cid = None
        self._client_lbl.setText("—")
        self._client_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};font-size:12px;font-weight:bold;"
            f"background:{COLORS['bg_hover']};border-radius:6px;padding:0 12px;"
        )
        self.customer_combo.setCurrentIndex(-1)
        self.customer_combo.setEditText("")
        self.amount_spent.setValue(0)
        self.amount_req.setValue(0)
        self.service_input.clear()
        self.ref_input.clear()
        self.notes_input.clear()
        QTimer.singleShot(80, self._focus_primary)

    def _focus_primary(self):
        if self._code_mode:
            self.code_input.setFocus()
        else:
            self.customer_combo.lineEdit().setFocus()


class TransactionDialog(BaseDialog):
    def __init__(self, platform_id: int, selected_date: str = None, parent=None):
        self.platform_id = platform_id
        self.platform = db.get_platform_by_id(platform_id)
        self.selected_date = (
            selected_date or __import__("datetime").date.today().isoformat()
        )

        title = "إضافة عملية"
        super().__init__(title, parent)

        screen = QGuiApplication.primaryScreen().availableGeometry()
        w = int(screen.width() * 0.7)
        h = int(screen.height() * 0.65)
        self.resize(w, h)

        x = (screen.width() - w) // 2
        y = (screen.height() - h) // 2
        self.move(x, y)

        # Hide default footer as we have our own save button in the tab
        while self.footer.count():
            item = self.footer.takeAt(0)
            if item.widget():
                item.widget().hide()

        self._build_content()
        self._update_header()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            if hasattr(self, "machine_tab"):
                self.machine_tab.code_input.setFocus()
            elif hasattr(self, "out_tab"):
                self.out_tab.customer_combo.lineEdit().setFocus()
            elif hasattr(self, "in_tab"):
                self.in_tab.customer_combo.lineEdit().setFocus()
        except Exception:
            pass

    def _build_content(self):
        if self.platform and self.platform["type"] in ("wallet", "instapay"):
            self.tabs = QTabWidget()
            self.out_tab = CompactTransactionTab(
                self.platform, is_inbound=False, selected_date=self.selected_date
            )
            self.out_tab.transaction_added.connect(self._on_added)
            self.tabs.addTab(self.out_tab, "📤 شحن صادر")

            self.in_tab = CompactTransactionTab(
                self.platform, is_inbound=True, selected_date=self.selected_date
            )
            self.in_tab.transaction_added.connect(self._on_added)
            self.tabs.addTab(self.in_tab, "📥 استلام وارد")

            self.body.addWidget(self.tabs)
        else:
            # Machine: new code-lookup tab
            self.machine_tab = MachineTransactionTab(
                self.platform, selected_date=self.selected_date
            )
            self.machine_tab.transaction_added.connect(self._on_added)
            self.body.addWidget(self.machine_tab)

    def _on_added(self):
        # Continuous Flow: do not close
        self._update_header(pulse=True)

    def _update_header(self, pulse=False):
        p = db.get_platform_by_id(self.platform_id)
        if not p:
            return
        self.platform = p

        header_frame = self.findChild(QFrame, "dialog_header")
        if not header_frame:
            return
        hl = header_frame.layout()

        # Clear existing
        while hl.count():
            item = hl.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        # Platform Name
        name_lbl = QLabel(p["name"])
        name_lbl.setObjectName("header_name")
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:18px; font-weight:bold;"
        )
        hl.addWidget(name_lbl)
        hl.addSpacing(20)

        # Balance Badge
        bal_badge = QLabel(f" رصيد: {fmt_currency(p.get('balance',0))} ")
        bal_badge.setObjectName("header_bal")
        bal_badge.setStyleSheet(f"""
            background: {COLORS['green_bg']}; color: {COLORS['green']}; 
            border: 1px solid {COLORS['green']}; border-radius: 12px;
            padding: 2px 12px; font-weight: bold; font-size: 13px;
        """)
        hl.addWidget(bal_badge)

        # Limit Badge
        if p["type"] in ("wallet", "instapay"):
            hl.addSpacing(10)
            used = p.get("monthly_used", 0)
            limit = p.get("monthly_limit", 200000)
            rem = limit - used
            pct = int(used / limit * 100) if limit else 0
            lim_color = (
                COLORS["red"]
                if pct > 90
                else COLORS["yellow"] if pct > 70 else COLORS["blue"]
            )
            lim_bg = (
                COLORS["red_bg"]
                if pct > 90
                else COLORS["yellow_bg"] if pct > 70 else COLORS["blue_bg"]
            )

            lim_badge = QLabel(f" المتبقي: {fmt_currency(rem)} ({pct}%) ")
            lim_badge.setObjectName("header_limit")
            lim_badge.setStyleSheet(f"""
                background: {lim_bg}; color: {lim_color}; 
                border: 1px solid {lim_color}; border-radius: 12px;
                padding: 2px 12px; font-weight: bold; font-size: 13px;
            """)
            hl.addWidget(lim_badge)

        hl.addStretch()

        if pulse:
            name_lbl.setStyleSheet(
                f"color:{COLORS['green']}; font-size:18px; font-weight:bold;"
            )
            QTimer.singleShot(
                600,
                lambda: name_lbl.setStyleSheet(
                    f"color:{COLORS['text_primary']}; font-size:18px; font-weight:bold;"
                ),
            )

        # Redundant Close Button logic removed to fix double 'X' glitch.
        # Since we clear the layout, we re-add it only once.
        close_btn = QPushButton("✕")
        close_btn.setObjectName("dialog_close_btn")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        hl.addWidget(close_btn)
