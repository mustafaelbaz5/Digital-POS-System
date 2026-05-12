"""
transaction_screen.py — شاشة عملية جديدة (Full Screen — Sidebar Item)

Flow:
  1. اختر نوع العملية: صادر / وارد
  2. اختر المنصة (visual cards مع الرصيد)
  3. أدخل بيانات العملية (form يظهر تلقائياً)
"""

import datetime

from PyQt6.QtCore import QLocale, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import ScreenShell, show_toast
from ui.styles.theme import COLORS, FONT, GAP_LG, GAP_MD, GAP_SM, CARD_RADIUS
from utils.formatters import fmt_currency


# ── helpers ────────────────────────────────────────────────────────────────

class _FocusSpin(QDoubleSpinBox):
    def focusInEvent(self, e):
        super().focusInEvent(e)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        QTimer.singleShot(0, self.selectAll)


def _spin(parent=None) -> _FocusSpin:
    sb = _FocusSpin(parent)
    sb.setLocale(QLocale(QLocale.Language.English))
    sb.setGroupSeparatorShown(True)
    sb.setRange(0, 9_999_999)
    sb.setDecimals(2)
    sb.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    sb.setStyleSheet(
        f"font-weight:bold; color:{COLORS['accent']}; font-size:20px; padding:6px;"
    )
    return sb


# ══════════════════════════════════════════════════════════════════════════
#  Platform Card Button
# ══════════════════════════════════════════════════════════════════════════

class PlatformCardBtn(QPushButton):
    """Card button showing platform name, type badge, and balance."""

    def __init__(self, platform: dict, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.setObjectName("platform_card_btn")
        self.setFixedSize(160, 90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("selected", "false")
        self._update_text()

    def _update_text(self):
        p = self.platform
        type_map = {"machine": "ماكينة", "wallet": "محفظة", "instapay": "إنستاباي"}
        type_label = type_map.get(p.get("type", ""), p.get("type", ""))
        balance = fmt_currency(p.get("balance", 0))
        self.setText(f"{p['name']}\n{type_label}\n{balance}")

    def set_selected(self, selected: bool):
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def refresh_balance(self):
        updated = db.get_platform_by_id(self.platform["id"])
        if updated:
            self.platform = updated
            self._update_text()


# ══════════════════════════════════════════════════════════════════════════
#  Transaction Form Widget (appears after platform selection)
# ══════════════════════════════════════════════════════════════════════════

class _TransactionForm(QWidget):
    """Inline form — adapts to platform type and direction."""

    saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._platform: dict | None = None
        self._is_inbound: bool = False
        self._code_mode: bool = True
        self._resolved_cid: int | None = None
        self._build_ui()

    # ── build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, GAP_MD, 0, 0)
        root.setSpacing(GAP_MD)

        # ── Platform info bar ──────────────────────────────────────────────
        self._platform_bar = QFrame()
        self._platform_bar.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        pb_layout = QHBoxLayout(self._platform_bar)
        pb_layout.setContentsMargins(16, 10, 16, 10)
        self._platform_name_lbl = QLabel("—")
        self._platform_name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;"
        )
        pb_layout.addWidget(self._platform_name_lbl)
        self._platform_bal_lbl = QLabel("")
        self._platform_bal_lbl.setStyleSheet(
            f"color:{COLORS['green']}; font-size:{FONT['md']}; font-weight:bold;"
            f"background:{COLORS['green_bg']}; border:1px solid {COLORS['green_border']};"
            f"border-radius:8px; padding:2px 12px;"
        )
        pb_layout.addWidget(self._platform_bal_lbl)
        pb_layout.addStretch()
        root.addWidget(self._platform_bar)

        # ── Mode toggle: code vs name (for machines) ───────────────────────
        self._mode_frame = QFrame()
        mode_layout = QHBoxLayout(self._mode_frame)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(GAP_SM)

        self._code_btn = QPushButton("🔑  بالكود")
        self._code_btn.setObjectName("mode_btn_active")
        self._code_btn.setFixedHeight(36)
        self._code_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._code_btn.clicked.connect(lambda: self._switch_lookup_mode(True))
        mode_layout.addWidget(self._code_btn)

        self._name_btn = QPushButton("👤  بالاسم")
        self._name_btn.setObjectName("mode_btn_idle")
        self._name_btn.setFixedHeight(36)
        self._name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._name_btn.clicked.connect(lambda: self._switch_lookup_mode(False))
        mode_layout.addWidget(self._name_btn)
        mode_layout.addStretch()
        root.addWidget(self._mode_frame)

        # ── Code lookup panel ──────────────────────────────────────────────
        self._code_panel = QWidget()
        cp_layout = QHBoxLayout(self._code_panel)
        cp_layout.setContentsMargins(0, 0, 0, 0)
        cp_layout.setSpacing(GAP_SM)

        lbl_code = QLabel("كود الشحن:")
        lbl_code.setStyleSheet(f"color:{COLORS['text_secondary']}; font-weight:bold;")
        cp_layout.addWidget(lbl_code)

        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("ابحث أو أدخل الكود مباشرة...")
        self._code_input.setStyleSheet(
            f"font-size:15px; padding:5px; font-weight:bold; color:{COLORS['accent']};"
        )
        self._code_input.returnPressed.connect(self._on_code_enter)
        cp_layout.addWidget(self._code_input, 1)

        self._client_lbl = QLabel("—")
        self._client_lbl.setFixedHeight(32)
        self._client_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']}; font-size:12px; font-weight:bold;"
            f"background:{COLORS['bg_hover']}; border-radius:6px; padding:0 12px;"
        )
        cp_layout.addWidget(self._client_lbl)
        root.addWidget(self._code_panel)

        # ── Name lookup panel (wallet/instapay + name-mode) ────────────────
        self._name_panel = QWidget()
        np_layout = QHBoxLayout(self._name_panel)
        np_layout.setContentsMargins(0, 0, 0, 0)
        np_layout.setSpacing(GAP_SM)

        lbl_cust = QLabel("العميل:")
        lbl_cust.setStyleSheet(f"color:{COLORS['text_secondary']}; font-weight:bold;")
        np_layout.addWidget(lbl_cust)

        self._cust_combo = QComboBox()
        self._cust_combo.setEditable(True)
        self._cust_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._cust_combo.lineEdit().setPlaceholderText(
            "ابحث باسم العميل أو رقم التليفون..."
        )
        self._cust_combo.lineEdit().setStyleSheet("padding:8px; font-size:15px;")
        np_layout.addWidget(self._cust_combo, 1)
        root.addWidget(self._name_panel)

        # ── Amounts ───────────────────────────────────────────────────────
        amt_row = QHBoxLayout()
        amt_row.setSpacing(GAP_MD)

        self._lbl_spent = QLabel("المصروف:")
        self._lbl_spent.setStyleSheet(f"color:{COLORS['text_secondary']}; font-weight:bold;")
        amt_row.addWidget(self._lbl_spent)
        self._amount_spent = _spin()
        self._amount_spent.valueChanged.connect(self._update_profit)
        amt_row.addWidget(self._amount_spent, 1)

        self._lbl_req = QLabel("المطلوب:")
        self._lbl_req.setStyleSheet(f"color:{COLORS['text_secondary']}; font-weight:bold;")
        amt_row.addWidget(self._lbl_req)
        self._amount_req = _spin()
        self._amount_req.valueChanged.connect(self._update_profit)
        amt_row.addWidget(self._amount_req, 1)
        root.addLayout(amt_row)

        # ── Status + Profit ────────────────────────────────────────────────
        status_row = QHBoxLayout()
        status_row.setSpacing(GAP_MD)

        self._status_lbl = QLabel("نوع الدفع:")
        self._status_lbl.setStyleSheet(f"color:{COLORS['text_secondary']};")
        status_row.addWidget(self._status_lbl)

        self._payment_combo = QComboBox()
        self._payment_combo.addItem("⏳ مؤجل", "pending")
        self._payment_combo.addItem("✓ مسدد", "paid")
        self._payment_combo.setFixedWidth(140)
        status_row.addWidget(self._payment_combo)

        self._delivery_combo = QComboBox()
        self._delivery_combo.addItem("✓ تم التسليم", True)
        self._delivery_combo.addItem("⏳ لم يُسلَّم", False)
        self._delivery_combo.setFixedWidth(160)
        self._delivery_combo.setVisible(False)
        status_row.addWidget(self._delivery_combo)

        status_row.addStretch()

        self._profit_lbl = QLabel("الربح المتوقع: 0.00 ج")
        self._profit_lbl.setStyleSheet(
            f"background:{COLORS['accent_dim']}; color:{COLORS['green']};"
            f"border-radius:6px; padding:4px 14px; font-weight:bold; font-size:13px;"
        )
        status_row.addWidget(self._profit_lbl)
        root.addLayout(status_row)

        # ── Details (always visible — no "show more") ──────────────────────
        details_frame = QFrame()
        details_frame.setObjectName("card")
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(16, 14, 16, 14)
        details_layout.setSpacing(GAP_SM)

        det_row1 = QHBoxLayout()
        det_row1.setSpacing(GAP_MD)

        lbl_svc = QLabel("الخدمة:")
        lbl_svc.setStyleSheet(f"color:{COLORS['text_secondary']};")
        det_row1.addWidget(lbl_svc)
        self._service_input = QLineEdit()
        self._service_input.setPlaceholderText("اسم الخدمة (اختياري)...")
        det_row1.addWidget(self._service_input, 2)

        lbl_ref = QLabel("المرجع:")
        lbl_ref.setStyleSheet(f"color:{COLORS['text_secondary']};")
        det_row1.addWidget(lbl_ref)
        self._ref_input = QLineEdit()
        self._ref_input.setPlaceholderText("اختياري...")
        self._ref_input.setFixedWidth(150)
        det_row1.addWidget(self._ref_input)
        details_layout.addLayout(det_row1)

        det_row2 = QHBoxLayout()
        lbl_notes = QLabel("ملاحظات:")
        lbl_notes.setStyleSheet(f"color:{COLORS['text_secondary']};")
        det_row2.addWidget(lbl_notes)
        self._notes_input = QLineEdit()
        self._notes_input.setPlaceholderText("ملاحظات إضافية...")
        det_row2.addWidget(self._notes_input)
        details_layout.addLayout(det_row2)
        root.addWidget(details_frame)

        # ── Date + Save ────────────────────────────────────────────────────
        bottom_row = QHBoxLayout()

        date_lbl = QLabel("تاريخ العملية:")
        date_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-weight:bold;")
        bottom_row.addWidget(date_lbl)

        self._date_lbl = QLabel(datetime.date.today().isoformat())
        self._date_lbl.setStyleSheet(
            f"font-size:14px; font-weight:bold; background:{COLORS['bg_hover']};"
            f"padding:4px 16px; border-radius:6px; color:{COLORS['accent']};"
        )
        bottom_row.addWidget(self._date_lbl)
        bottom_row.addStretch()

        self._save_btn = QPushButton("✓  حفظ العملية  (Enter)")
        self._save_btn.setObjectName("btn_primary")
        self._save_btn.setMinimumHeight(48)
        self._save_btn.setMinimumWidth(220)
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.clicked.connect(self._save)
        bottom_row.addWidget(self._save_btn)
        root.addLayout(bottom_row)

        # Tab order
        self.setTabOrder(self._code_input, self._amount_spent)
        self.setTabOrder(self._cust_combo, self._amount_spent)
        self.setTabOrder(self._amount_spent, self._amount_req)
        self.setTabOrder(self._amount_req, self._save_btn)

    # ── setup ──────────────────────────────────────────────────────────────

    def setup(self, platform: dict, is_inbound: bool):
        self._platform = platform
        self._is_inbound = is_inbound

        # Update platform bar
        self._platform_name_lbl.setText(platform["name"])
        self._platform_bal_lbl.setText(f"الرصيد: {fmt_currency(platform.get('balance', 0))}")

        is_machine = platform.get("type") == "machine"

        # Mode toggle visible only for machines
        self._mode_frame.setVisible(is_machine)
        if is_machine:
            self._switch_lookup_mode(True)  # code mode for machines
        else:
            self._code_panel.setVisible(False)
            self._name_panel.setVisible(True)

        # Adapt labels for inbound
        if is_inbound:
            self._lbl_spent.setText("المسلَّم:")
            self._lbl_req.setText("المستلَم:")
            self._status_lbl.setText("تسليم الكاش:")
            self._payment_combo.setVisible(False)
            self._delivery_combo.setVisible(True)
        else:
            self._lbl_spent.setText("المصروف:")
            self._lbl_req.setText("المطلوب:")
            self._status_lbl.setText("نوع الدفع:")
            self._payment_combo.setVisible(True)
            self._delivery_combo.setVisible(False)

        self._load_completers()
        self.reset()

    def _load_completers(self):
        # Customer name completer
        self._cust_combo.clear()
        name_list = []
        for c in db.get_all_customers():
            label = c["name"] + (f" ({c['phone']})" if c.get("phone") else "")
            self._cust_combo.addItem(label, c["id"])
            name_list.append(label)
        comp = QCompleter(name_list, self)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        comp.popup().setStyleSheet(
            f"background:{COLORS['bg_elevated']}; color:{COLORS['text_primary']};"
            f"selection-background-color:{COLORS['accent']}; selection-color:white;"
            f"border:1px solid {COLORS['border']}; font-size:14px;"
        )
        self._cust_combo.setCompleter(comp)
        self._cust_combo.setCurrentIndex(-1)
        self._cust_combo.setEditText("")

        # Shipping code completer (machines)
        if self._platform and self._platform.get("type") == "machine":
            codes = [c["code"] for c in db.get_all_shipping_codes()]
            comp_c = QCompleter(codes, self)
            comp_c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            comp_c.setFilterMode(Qt.MatchFlag.MatchContains)
            comp_c.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            comp_c.popup().setStyleSheet(
                f"background:{COLORS['bg_elevated']}; color:{COLORS['text_primary']};"
                f"selection-background-color:{COLORS['accent']}; selection-color:white;"
                f"border:1px solid {COLORS['border']}; font-size:14px;"
            )
            comp_c.activated.connect(self._on_code_activated)
            self._code_input.setCompleter(comp_c)

        # Service name completer
        svcs = db.get_unique_service_names()
        comp_s = QCompleter(svcs, self)
        comp_s.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_s.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        comp_s.popup().setStyleSheet(
            f"background:{COLORS['bg_input']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; font-size:14px;"
        )
        self._service_input.setCompleter(comp_s)

    # ── mode helpers ───────────────────────────────────────────────────────

    def _switch_lookup_mode(self, code_mode: bool):
        self._code_mode = code_mode
        self._resolved_cid = None
        self._code_panel.setVisible(code_mode)
        self._name_panel.setVisible(not code_mode)
        self._code_btn.setObjectName("mode_btn_active" if code_mode else "mode_btn_idle")
        self._name_btn.setObjectName("mode_btn_active" if not code_mode else "mode_btn_idle")
        self._code_btn.style().unpolish(self._code_btn)
        self._code_btn.style().polish(self._code_btn)
        self._name_btn.style().unpolish(self._name_btn)
        self._name_btn.style().polish(self._name_btn)
        if code_mode:
            QTimer.singleShot(50, self._code_input.setFocus)
        else:
            QTimer.singleShot(50, lambda: self._cust_combo.lineEdit().setFocus())

    def _on_code_enter(self):
        self._resolve_code(self._code_input.text().strip())
        self._amount_spent.setFocus()

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
                f"color:{COLORS['green']}; font-size:12px; font-weight:bold;"
                f"background:{COLORS['green_bg']}; border-radius:6px; padding:0 12px;"
            )
        else:
            self._resolved_cid = None
            self._client_lbl.setText(f"⚠  كود غير موجود: {code}")
            self._client_lbl.setStyleSheet(
                f"color:{COLORS['yellow']}; font-size:12px; font-weight:bold;"
                f"background:{COLORS['yellow_bg']}; border-radius:6px; padding:0 12px;"
            )

    # ── profit ─────────────────────────────────────────────────────────────

    def _update_profit(self):
        profit = self._amount_req.value() - self._amount_spent.value()
        color = COLORS["green"] if profit >= 0 else COLORS["red"]
        self._profit_lbl.setStyleSheet(
            f"background:{COLORS['accent_dim']}; color:{color};"
            f"border-radius:6px; padding:4px 14px; font-weight:bold; font-size:13px;"
        )
        self._profit_lbl.setText(f"الربح المتوقع: {fmt_currency(profit)}")

    # ── customer id resolution ─────────────────────────────────────────────

    def _get_customer_id(self) -> int | None:
        is_machine = self._platform and self._platform.get("type") == "machine"
        if is_machine and self._code_mode:
            return self._resolved_cid
        cid = self._cust_combo.currentData()
        if cid:
            return cid
        typed = self._cust_combo.currentText().strip()
        for i in range(self._cust_combo.count()):
            if self._cust_combo.itemText(i) == typed:
                self._cust_combo.setCurrentIndex(i)
                return self._cust_combo.itemData(i)
        return None

    # ── save ───────────────────────────────────────────────────────────────

    def _save(self):
        if not self._platform:
            QMessageBox.warning(self, "تنبيه", "اختر منصة أولاً")
            return

        cid = self._get_customer_id()
        spent = self._amount_spent.value()
        req = self._amount_req.value()
        service = self._service_input.text().strip()
        ref = self._ref_input.text().strip()
        notes = self._notes_input.text().strip()

        is_machine = self._platform.get("type") == "machine"
        if not cid:
            msg = "يجب إدخال كود شحن صحيح" if (is_machine and self._code_mode) else "يجب اختيار عميل من القائمة"
            QMessageBox.warning(self, "تنبيه", msg)
            return

        if spent <= 0 and req <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل المبلغ")
            return

        pid = self._platform["id"]
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        created_at = f"{self._date_lbl.text()} {now_time}"

        try:
            if not self._is_inbound:
                default_svc = "شحن" if is_machine else "تحويل"
                db.add_outbound_transaction(
                    platform_id=pid,
                    customer_id=cid,
                    service_name=service or default_svc,
                    amount_spent=spent,
                    amount_required=req,
                    payment_status=self._payment_combo.currentData(),
                    reference_no=ref,
                    is_card=False,
                    notes=notes,
                    created_at=created_at,
                )
            else:
                db.add_inbound_transaction(
                    wallet_id=pid,
                    customer_id=cid,
                    service_name=service or "استلام",
                    amount_received=req,
                    amount_delivered=spent,
                    reference_no=ref,
                    notes=notes,
                    is_delivered=self._delivery_combo.currentData(),
                    created_at=created_at,
                )

            show_toast(self, "تمت إضافة العملية بنجاح ✓", type="success")
            self.saved.emit()
            self.reset()

        except Exception as e:
            show_toast(self, f"خطأ: {e}", type="danger")

    # ── reset ──────────────────────────────────────────────────────────────

    def reset(self):
        self._amount_spent.setValue(0)
        self._amount_req.setValue(0)
        self._service_input.clear()
        self._ref_input.clear()
        self._notes_input.clear()
        self._code_input.clear()
        self._resolved_cid = None
        self._client_lbl.setText("—")
        self._client_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']}; font-size:12px; font-weight:bold;"
            f"background:{COLORS['bg_hover']}; border-radius:6px; padding:0 12px;"
        )
        self._cust_combo.setCurrentIndex(-1)
        self._cust_combo.setEditText("")
        self._update_profit()
        self._date_lbl.setText(datetime.date.today().isoformat())
        QTimer.singleShot(80, self._focus_primary)

    def _focus_primary(self):
        is_machine = self._platform and self._platform.get("type") == "machine"
        if is_machine and self._code_mode:
            self._code_input.setFocus()
        else:
            self._cust_combo.lineEdit().setFocus()


# ══════════════════════════════════════════════════════════════════════════
#  TransactionScreen — the main sidebar screen
# ══════════════════════════════════════════════════════════════════════════

class TransactionScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__("عملية جديدة", "اختر المنصة لبدء العملية")
        self._platforms: list[dict] = []
        self._selected_pid: int | None = None
        self._is_inbound: bool = False
        self._platform_btns: dict[int, PlatformCardBtn] = {}
        self._build_content()

    # ── layout ─────────────────────────────────────────────────────────────

    def _build_content(self):
        c = self.content()
        c.setSpacing(GAP_LG)

        # ── Direction toggle ───────────────────────────────────────────────
        dir_frame = QFrame()
        dir_frame.setObjectName("card")
        dir_layout = QHBoxLayout(dir_frame)
        dir_layout.setContentsMargins(20, 16, 20, 16)
        dir_layout.setSpacing(GAP_SM)

        dir_lbl = QLabel("نوع العملية:")
        dir_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-weight:bold; font-size:{FONT['md']};"
        )
        dir_layout.addWidget(dir_lbl)

        self._outbound_btn = QPushButton("📤  صادر (شحن)")
        self._outbound_btn.setObjectName("mode_btn_active")
        self._outbound_btn.setFixedHeight(42)
        self._outbound_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._outbound_btn.clicked.connect(lambda: self._set_direction(False))
        dir_layout.addWidget(self._outbound_btn)

        self._inbound_btn = QPushButton("📥  وارد (استلام)")
        self._inbound_btn.setObjectName("mode_btn_idle")
        self._inbound_btn.setFixedHeight(42)
        self._inbound_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._inbound_btn.clicked.connect(lambda: self._set_direction(True))
        dir_layout.addWidget(self._inbound_btn)

        dir_layout.addStretch()
        c.addWidget(dir_frame)

        # ── Platform selection grid ────────────────────────────────────────
        plat_label = QLabel("اختر المنصة:")
        plat_label.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;"
        )
        c.addWidget(plat_label)

        self._platforms_grid_widget = QWidget()
        self._platforms_grid = QGridLayout(self._platforms_grid_widget)
        self._platforms_grid.setSpacing(GAP_MD)
        self._platforms_grid.setContentsMargins(0, 0, 0, 0)
        c.addWidget(self._platforms_grid_widget)

        # ── Transaction form (shown after platform selection) ──────────────
        self._form_wrapper = QFrame()
        self._form_wrapper.setObjectName("card")
        fw_layout = QVBoxLayout(self._form_wrapper)
        fw_layout.setContentsMargins(24, 20, 24, 24)

        form_title = QLabel("بيانات العملية")
        form_title.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;"
        )
        fw_layout.addWidget(form_title)

        self._form = _TransactionForm()
        self._form.saved.connect(self._on_saved)
        fw_layout.addWidget(self._form)

        self._form_wrapper.setVisible(False)
        c.addWidget(self._form_wrapper)

        c.addStretch()

    # ── direction ──────────────────────────────────────────────────────────

    def _set_direction(self, is_inbound: bool):
        self._is_inbound = is_inbound
        self._outbound_btn.setObjectName("mode_btn_idle" if is_inbound else "mode_btn_active")
        self._inbound_btn.setObjectName("mode_btn_active" if is_inbound else "mode_btn_idle")
        for btn in [self._outbound_btn, self._inbound_btn]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Reload form if a platform is already selected
        if self._selected_pid is not None:
            p = next((p for p in self._platforms if p["id"] == self._selected_pid), None)
            if p:
                self._form.setup(p, is_inbound)

    # ── platform selection ─────────────────────────────────────────────────

    def _build_platform_grid(self):
        # Clear existing buttons
        while self._platforms_grid.count():
            item = self._platforms_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._platform_btns.clear()

        cols = 5
        for i, p in enumerate(self._platforms):
            btn = PlatformCardBtn(p)
            btn.clicked.connect(lambda _, pid=p["id"]: self._select_platform(pid))
            self._platforms_grid.addWidget(btn, i // cols, i % cols)
            self._platform_btns[p["id"]] = btn

        # Re-select previously selected platform
        if self._selected_pid and self._selected_pid in self._platform_btns:
            self._platform_btns[self._selected_pid].set_selected(True)

    def _select_platform(self, pid: int):
        # Update visual selection
        for p_id, btn in self._platform_btns.items():
            btn.set_selected(p_id == pid)

        self._selected_pid = pid
        p = next((p for p in self._platforms if p["id"] == pid), None)
        if not p:
            return

        # Wallets/instapay can't do outbound if direction is inbound already;
        # but we allow the user to set direction freely — just show the form.
        self._form.setup(p, self._is_inbound)
        self._form_wrapper.setVisible(True)

    def select_platform(self, platform_id: int):
        """Public API — called from main window when navigating from platforms screen."""
        if platform_id in self._platform_btns:
            self._select_platform(platform_id)

    # ── refresh ────────────────────────────────────────────────────────────

    def refresh(self):
        self._platforms = [p for p in db.get_all_platforms() if p.get("is_active", 1)]
        self._build_platform_grid()

        # Update balance in form bar if platform still selected
        if self._selected_pid and self._form_wrapper.isVisible():
            p = next((p for p in self._platforms if p["id"] == self._selected_pid), None)
            if p:
                self._form.setup(p, self._is_inbound)

    def _on_saved(self):
        # Refresh platform balances after save
        self._platforms = [p for p in db.get_all_platforms() if p.get("is_active", 1)]
        for p in self._platforms:
            btn = self._platform_btns.get(p["id"])
            if btn:
                btn.platform = p
                btn._update_text()
