"""
transaction_form.py — شاشة إضافة العمليات (Compact Pro Zero-Scroll)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox,
    QTabWidget, QDoubleSpinBox, QMessageBox, QFrame, QCompleter, QDialog,
    QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QLocale, QDate
from PyQt6.QtGui import QGuiApplication

from ui.styles.theme import COLORS, FONT, CARD_RADIUS
from ui.components.widgets import BaseDialog, make_divider, show_toast
from utils.formatters import fmt_currency

import database as db

class FocusSpinBox(QDoubleSpinBox):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        QTimer.singleShot(0, self.selectAll)

class CompactTransactionTab(QWidget):
    transaction_added = pyqtSignal()
    
    def __init__(self, platform: dict, is_inbound: bool = False, selected_date: str = None, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.is_inbound = is_inbound
        self.selected_date = selected_date or __import__('datetime').date.today().isoformat()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_data()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8) # Highly condensed
        
        # ── Row 1: Client & Payment
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        
        lbl_c = QLabel("العميل:")
        lbl_c.setStyleSheet(f"color:{COLORS['text_secondary']};")
        row1.addWidget(lbl_c)
        
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_combo.lineEdit().setPlaceholderText("ابحث باسم العميل أو رقم التليفون...")
        # Style the main line edit
        self.customer_combo.lineEdit().setStyleSheet(f"padding: 5px; font-size: 14px;")
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
        self.amount_spent.setStyleSheet(f"font-weight:bold; color:{COLORS['accent']}; font-size:18px; padding: 4px;")
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
            self.amount_req.setStyleSheet(f"font-weight:bold; color:{COLORS['accent']}; font-size:18px; padding: 4px;")
            self.amount_req.valueChanged.connect(self._update_profit)
            lbl_a2 = QLabel("المطلوب:")
            lbl_a2.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row2.addWidget(lbl_a2)
            row2.addWidget(self.amount_req, 1)
        else:
            self.amount_req = FocusSpinBox() # used for received
            self.amount_req.setLocale(loc)
            self.amount_req.setGroupSeparatorShown(True)
            self.amount_req.setRange(0, 999999)
            self.amount_req.setDecimals(2)
            self.amount_req.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            self.amount_req.setStyleSheet(f"font-weight:bold; color:{COLORS['accent']}; font-size:18px; padding: 4px;")
            self.amount_req.valueChanged.connect(self._update_profit)
            lbl_a1 = QLabel("المستلم:")
            lbl_a1.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row2.addWidget(lbl_a1)
            row2.addWidget(self.amount_req, 1)
            
            lbl_a2 = QLabel("المسلم:")
            lbl_a2.setStyleSheet(f"color:{COLORS['text_secondary']};")
            row2.addWidget(lbl_a2)
            row2.addWidget(self.amount_spent, 1) # used for delivered
            
        layout.addLayout(row2)
        
        # Real-time profit
        profit_layout = QHBoxLayout()
        profit_layout.addStretch()
        self.profit_lbl = QLabel("الربح المتوقع: 0.00 ج")
        self.profit_lbl.setStyleSheet(f"background:{COLORS['accent_dim']}; color:{COLORS['green']}; border-radius:6px; padding:4px 10px; font-weight:bold; font-size:13px;")
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
        lbl_d.setStyleSheet(f"color:{COLORS['text_secondary']}; font-weight:bold; font-size:14px;")
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
        self.customer_combo.lineEdit().returnPressed.connect(self.service_input.setFocus)
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
        self.profit_lbl.setStyleSheet(f"background:{COLORS['accent_dim']}; color:{color}; border-radius:6px; padding:4px 10px; font-weight:bold; font-size:13px;")
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

    def _save(self):
        cid = self.customer_combo.currentData()
        service = self.service_input.text().strip()
        spent = self.amount_spent.value()
        req = self.amount_req.value()
        ref = self.ref_input.text().strip()
        notes = self.notes_input.text().strip()
        
        if not cid: QMessageBox.warning(self, "تنبيه", "يجب اختيار العميل لإتمام العملية."); return
        if not service: QMessageBox.warning(self, "تنبيه", "أدخل اسم الخدمة"); return
        if spent <= 0 and req <= 0: QMessageBox.warning(self, "تنبيه", "أدخل المبلغ"); return
        
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
                    platform_id=pid, customer_id=cid, service_name=service,
                    amount_spent=spent, amount_required=req, payment_status=status,
                    reference_no=ref, is_card=False, notes=notes,
                    created_at=created_at
                )
            else:
                is_del = self.delivery_combo.currentData()
                if not cid and not is_del:
                    QMessageBox.warning(self, "تنبيه", "اختر العميل للعمليات غير المسلمة")
                    return
                db.add_inbound_transaction(
                    wallet_id=pid, customer_id=cid, service_name=service,
                    amount_received=req, amount_delivered=spent,
                    reference_no=ref, notes=notes, is_delivered=is_del,
                    created_at=created_at
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
            self.customer_combo.setCurrentIndex(0) # Back to "بدون عميل محدد"
            self.customer_combo.setEditText("")    # Clear search text
            
            # Return focus to Client Search for rapid next entry
            self.customer_combo.setFocus()
                
        except Exception as e:
            show_toast(self, f"خطأ: {str(e)}", type="danger")


class TransactionDialog(BaseDialog):
    def __init__(self, platform_id: int, selected_date: str = None, parent=None):
        self.platform_id = platform_id
        self.platform = db.get_platform_by_id(platform_id)
        self.selected_date = selected_date or __import__('datetime').date.today().isoformat()
        
        title = f"إضافة عملية"
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
        # Auto-focus first input field (Customer Search)
        try:
            if hasattr(self, "out_tab"):
                self.out_tab.customer_combo.setFocus()
            elif hasattr(self, "in_tab"):
                self.in_tab.customer_combo.setFocus()
        except: pass
        
    def _build_content(self):
        if self.platform and self.platform["type"] in ("wallet", "instapay"):
            self.tabs = QTabWidget()
            self.out_tab = CompactTransactionTab(self.platform, is_inbound=False, selected_date=self.selected_date)
            self.out_tab.transaction_added.connect(self._on_added)
            self.tabs.addTab(self.out_tab, "📤 شحن صادر")
            
            self.in_tab = CompactTransactionTab(self.platform, is_inbound=True, selected_date=self.selected_date)
            self.in_tab.transaction_added.connect(self._on_added)
            self.tabs.addTab(self.in_tab, "📥 استلام وارد")
            
            self.body.addWidget(self.tabs)
        else:
            self.out_tab = CompactTransactionTab(self.platform, is_inbound=False, selected_date=self.selected_date)
            self.out_tab.transaction_added.connect(self._on_added)
            self.body.addWidget(self.out_tab)
            
    def _on_added(self):
        # Continuous Flow: do not close
        self._update_header(pulse=True)

    def _update_header(self, pulse=False):
        p = db.get_platform_by_id(self.platform_id)
        if not p: return
        self.platform = p
        
        header_frame = self.findChild(QFrame, "dialog_header")
        if not header_frame: return
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
        name_lbl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:18px; font-weight:bold;")
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
            lim_color = COLORS["red"] if pct > 90 else COLORS["yellow"] if pct > 70 else COLORS["blue"]
            lim_bg = COLORS["red_bg"] if pct > 90 else COLORS["yellow_bg"] if pct > 70 else COLORS["blue_bg"]
            
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
            name_lbl.setStyleSheet(f"color:{COLORS['green']}; font-size:18px; font-weight:bold;")
            QTimer.singleShot(600, lambda: name_lbl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:18px; font-weight:bold;"))

        # Redundant Close Button logic removed to fix double 'X' glitch.
        # Since we clear the layout, we re-add it only once.
        close_btn = QPushButton("✕")
        close_btn.setObjectName("dialog_close_btn")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        hl.addWidget(close_btn)
