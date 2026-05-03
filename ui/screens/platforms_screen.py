"""
platforms_screen.py — شاشة إدارة المنصات (UI جديد)
تابات (ماكينات / محافظ / انستا باي) + صفوف جدول بدل كروت
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QDoubleSpinBox, QFrame,
    QTabWidget, QInputDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.styles.theme import (
    COLORS, FONT, ROW_HEIGHT, 
    GAP_XS, GAP_SM, GAP_MD, GAP_LG, MARGIN_CARD
)
from ui.components.widgets import ScreenShell, make_divider, CardGroup, BaseDialog, DataTable
from utils.formatters import fmt_currency

import database as db


# ══════════════════════════════════════════
#  Platform Actions Dialog
# ══════════════════════════════════════════

class PlatformActionsDialog(BaseDialog):
    """ديالوج العمليات الخاصة بكل منصة (Pro Version)"""

    def __init__(self, platform: dict, parent=None):
        super().__init__(f"إجراءات — {platform['name']}", parent)
        self.platform       = platform
        self._result_action = None
        self.setFixedWidth(380)
        self._build_content()

    def _build_content(self):
        p      = self.platform
        p_type = p["type"]

        # ── Body (Info Card)
        info = QFrame()
        info.setObjectName("card")
        il = QVBoxLayout(info)
        il.setContentsMargins(18, 14, 18, 14)
        il.setSpacing(6)

        name_lbl = QLabel(p["name"])
        name_lbl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:16px; font-weight:bold;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        il.addWidget(name_lbl)

        bal_color = COLORS["green"] if p.get("balance", 0) > 0 else COLORS["text_muted"]
        bal_lbl   = QLabel(f"💰 الرصيد الحالي: {fmt_currency(p.get('balance', 0))}")
        bal_lbl.setStyleSheet(f"color:{bal_color}; font-size:14px; font-weight:bold;")
        bal_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        il.addWidget(bal_lbl)

        if p_type in ("wallet", "instapay"):
            used      = p.get("monthly_used", 0)
            limit     = p.get("monthly_limit", 200000)
            remaining = limit - used
            pct       = min(100, int(used / limit * 100)) if limit else 0
            lim_color = (COLORS["red"]    if pct >= 90 else
                         COLORS["yellow"] if pct >= 70 else
                         COLORS["text_secondary"])
            lim_lbl = QLabel(f"📉 متبقي من الحد: {fmt_currency(remaining)}  ({pct}%)")
            lim_lbl.setStyleSheet(f"color:{lim_color}; font-size:13px;")
            lim_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            il.addWidget(lim_lbl)

        self.body.addWidget(info)
        self.body.addSpacing(GAP_SM)

        # ── Body (Actions)
        for label, color, bg, handler in self._get_actions(p_type):
            btn = QPushButton(label)
            btn.setFixedHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Custom style for colorful action buttons
            btn.setStyleSheet(
                f"background:{bg}; color:{color}; border:1.5px solid {color}; border-radius:8px;"
                f"font-size:14px; font-weight:bold;"
            )
            btn.clicked.connect(handler)
            self.body.addWidget(btn)

        # ── Footer
        self.add_stretch()
        self.add_button("🗑️ حذف المنصة", self._delete, role="danger")
        self.add_button("إغلاق", self.reject, role="secondary")

    def _get_actions(self, p_type: str) -> list:
        actions = [
            ("💰  إيداع للمنصة",
             COLORS["green"], COLORS["green_bg"], self._deposit),
        ]
        if p_type == "machine":
            actions.append((
                "📊  تسجيل عمولة يومية",
                COLORS["yellow"], COLORS["yellow_bg"], self._commission
            ))
        if p_type in ("wallet", "instapay"):
            actions.append((
                "✏️  تعديل الحد الشهري",
                COLORS["blue"], COLORS["blue_bg"], self._edit_limit
            ))
        return actions

    def _deposit(self):
        p = self.platform
        amount, ok = QInputDialog.getDouble(
            self, "إيداع",
            f"المبلغ المراد إيداعه في [{p['name']}]:\n"
            f"الرصيد الحالي: {fmt_currency(p.get('balance', 0))}",
            min=0.01, decimals=2
        )
        if ok and amount > 0:
            try:
                db.deposit_to_platform(p["id"], amount)
                QMessageBox.information(self, "تم ", f"تم إيداع {fmt_currency(amount)}")
                self._result_action = "refresh"
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _commission(self):
        p = self.platform
        amount, ok = QInputDialog.getDouble(
            self, "العمولة اليومية",
            f"مبلغ العمولة لـ [{p['name']}]:\n"
            f"الرصيد الحالي: {fmt_currency(p.get('balance', 0))}",
            min=0.01, decimals=2
        )
        if ok and amount > 0:
            try:
                db.record_daily_commission(p["id"], amount)
                QMessageBox.information(
                    self, "تم ",
                    f"تم تسجيل العمولة: {fmt_currency(amount)}\n"
                    f"خُصمت من [{p['name']}] وأُضيفت للخزينة."
                )
                self._result_action = "refresh"
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_limit(self):
        p       = self.platform
        current = p.get("monthly_limit", 200000)
        amount, ok = QInputDialog.getDouble(
            self, "تعديل الحد الشهري",
            f"الحد الشهري الجديد لـ [{p['name']}]:",
            value=current, min=0, decimals=2
        )
        if ok:
            try:
                from database.schema import get_connection
                with get_connection() as conn:
                    conn.execute(
                        "UPDATE platforms SET monthly_limit = ? WHERE id = ?",
                        (amount, p["id"])
                    )
                    conn.commit()
                QMessageBox.information(self, "تم ", f"تم تحديث الحد إلى {fmt_currency(amount)}")
                self._result_action = "refresh"
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _delete(self):
        p = self.platform
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف [{p['name']}]؟\n"
            f"الرصيد الحالي: {fmt_currency(p.get('balance', 0))}\n\n"
            "⚠️ سيتم إخفاؤها من كل القوائم.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            db.delete_platform(p["id"])
            self._result_action = "refresh"
            self.accept()


# ══════════════════════════════════════════
#  Platform Row
# ══════════════════════════════════════════

class PlatformRow(QFrame):
    actions_clicked = pyqtSignal(int)
    add_transaction_clicked = pyqtSignal(int)

    def __init__(self, platform: dict, alternate: bool = False, parent=None):
        super().__init__(parent)
        self.platform_id = platform["id"]
        self.setObjectName("platform_row")
        self.setFixedHeight(ROW_HEIGHT)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        bg = COLORS["bg_card"] if not alternate else COLORS["bg_elevated"]
        self.setStyleSheet(
            f"QFrame#platform_row {{ background:{bg};"
            f"border-bottom:1px solid {COLORS['border']}; }}"
        )
        self._build(platform)

    def _build(self, p: dict):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)

        p_type = p["type"]

        # اسم المنصة (يمين)
        name_lbl = QLabel(p["name"])
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']};font-size:14px;font-weight:bold;"
            f"background:transparent;border:none;"
        )
        name_lbl.setFixedWidth(180)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(name_lbl)

        layout.addStretch()

        # الحد المتبقي (للمحافظ وانستا باي فقط)
        if p_type in ("wallet", "instapay"):
            used      = p.get("monthly_used", 0)
            limit     = p.get("monthly_limit", 200000)
            remaining = limit - used
            pct       = min(100, int(used / limit * 100)) if limit else 0
            lim_color = (COLORS["red"]    if pct >= 90 else
                         COLORS["yellow"] if pct >= 70 else
                         COLORS["text_secondary"])
            lim_lbl = QLabel(f"متبقي: {fmt_currency(remaining)}")
            lim_lbl.setStyleSheet(
                f"color:{lim_color};font-size:12px;"
                f"background:transparent;border:none;"
            )
            lim_lbl.setFixedWidth(190)
            lim_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(lim_lbl)
            layout.addStretch()

        # الرصيد (وسط)
        balance   = p.get("balance", 0)
        bal_color = COLORS["green"] if balance > 0 else COLORS["text_muted"]
        bal_lbl   = QLabel(fmt_currency(balance))
        bal_lbl.setStyleSheet(
            f"color:{bal_color};font-size:15px;font-weight:bold;"
            f"background:transparent;border:none;"
        )
        bal_lbl.setFixedWidth(140)
        bal_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(bal_lbl)

        # عدد العمليات
        count = p.get("transaction_count", 0)
        count_lbl = QLabel(f"🔢 {count}")
        count_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
        count_lbl.setFixedWidth(60)
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(count_lbl)

        # زرار إضافة عملية
        add_btn = QPushButton("➕ إضافة عملية")
        add_btn.setFixedHeight(30)
        add_btn.setFixedWidth(130)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            f"background:{COLORS['blue_bg']};color:{COLORS['blue']};"
            f"border:1px solid {COLORS['blue']};border-radius:6px;"
            f"font-size:13px;padding:2px 10px;font-weight:bold;"
        )
        add_btn.clicked.connect(lambda: self.add_transaction_clicked.emit(self.platform_id))
        layout.addWidget(add_btn)

        layout.addSpacing(8)

        # زرار الإجراءات (يسار)
        act_btn = QPushButton("⋮  إجراءات")
        act_btn.setFixedHeight(30)
        act_btn.setFixedWidth(100)
        act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        act_btn.setStyleSheet(
            f"background:{COLORS['bg_input']};color:{COLORS['text_secondary']};"
            f"border:1px solid {COLORS['border']};border-radius:6px;"
            f"font-size:13px;padding:2px 10px;"
        )
        act_btn.clicked.connect(lambda: self.actions_clicked.emit(self.platform_id))
        layout.addWidget(act_btn)


# ══════════════════════════════════════════
#  Platform List Tab
# ══════════════════════════════════════════

class PlatformListTab(QWidget):
    refreshed = pyqtSignal()

    def __init__(self, p_type: str, parent=None):
        super().__init__(parent)
        self.p_type = p_type
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_MD)

        # ── Toolbar
        sb = QHBoxLayout()
        sb.setSpacing(GAP_SM)
        sb.setAlignment(Qt.AlignmentFlag.AlignLeft)

        sort_lbl = QLabel("ترتيب:")
        sort_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
        sb.addWidget(sort_lbl)

        self._sort_mode = "default"
        self._sort_btns = {}
        
        # Sorting Buttons row
        self.btn_default = QPushButton("الافتراضي")
        self.btn_default.setFixedHeight(28)
        self.btn_default.clicked.connect(lambda: self._set_sort("default"))
        self._sort_btns["default"] = self.btn_default
        sb.addWidget(self.btn_default)

        self.btn_bal_asc = QPushButton("الرصيد ↑")
        self.btn_bal_asc.setFixedHeight(28)
        self.btn_bal_asc.clicked.connect(lambda: self._set_sort("balance_asc"))
        self._sort_btns["balance_asc"] = self.btn_bal_asc
        sb.addWidget(self.btn_bal_asc)

        self.btn_bal_desc = QPushButton("الرصيد ↓")
        self.btn_bal_desc.setFixedHeight(28)
        self.btn_bal_desc.clicked.connect(lambda: self._set_sort("balance_desc"))
        self._sort_btns["balance_desc"] = self.btn_bal_desc
        sb.addWidget(self.btn_bal_desc)

        if self.p_type in ("wallet", "instapay"):
            self.btn_lim_asc = QPushButton("الحد المتبقي ↑")
            self.btn_lim_asc.setFixedHeight(28)
            self.btn_lim_asc.clicked.connect(lambda: self._set_sort("limit_asc"))
            self._sort_btns["limit_asc"] = self.btn_lim_asc
            sb.addWidget(self.btn_lim_asc)

            self.btn_lim_desc = QPushButton("الحد المتبقي ↓")
            self.btn_lim_desc.setFixedHeight(28)
            self.btn_lim_desc.clicked.connect(lambda: self._set_sort("limit_desc"))
            self._sort_btns["limit_desc"] = self.btn_lim_desc
            sb.addWidget(self.btn_lim_desc)

        sb.addStretch()
        layout.addLayout(sb)
        self._apply_sort_styles()

        # ── Table Section

        cols = [
            ("اسم المنصة", -1), # Stretch
            ("الرصيد الحالي", 160),
            ("العمليات", 100),
            ("إجراءات", 200)
        ]
        if self.p_type in ("wallet", "instapay"):
            cols.insert(1, ("المتبقي من الحد", 190))

        self.table = DataTable(cols)
        self.table.setSortingEnabled(True)
        # Header Styling
        self.table.horizontalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_secondary']};
                padding: 10px;
                border: none;
                font-weight: bold;
                text-align: center;
            }}
        """)
        
        # Disable internal scroll for Full-Page Scroll
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        layout.addWidget(self.table)


    def _set_sort(self, mode: str):
        self._sort_mode = mode
        self._apply_sort_styles()
        if hasattr(self, "_platforms_data"):
            self.load(self._platforms_data)

    def _apply_sort_styles(self):
        for mode, btn in self._sort_btns.items():
            active = (mode == self._sort_mode)
            btn.setStyleSheet(
                f"background:{COLORS['blue_bg']};color:{COLORS['blue']};"
                f"border:1px solid {COLORS['blue']};border-radius:5px;"
                f"font-size:12px;padding:2px 8px;"
                if active else
                f"background:{COLORS['bg_input']};color:{COLORS['text_muted']};"
                f"border:1px solid {COLORS['border']};border-radius:5px;"
                f"font-size:12px;padding:2px 8px;"
            )

    def _toggle_balance_sort(self):
        self._balance_sort_asc = not self._balance_sort_asc
        mode = "balance_asc" if self._balance_sort_asc else "balance_desc"
        arrow = "↑" if self._balance_sort_asc else "↓"
        self.btn_bal.setText(f"💰 الرصيد {arrow}")
        self._set_sort(mode)

    def _sorted(self, platforms: list) -> list:
        if self._sort_mode == "default":
            return platforms
        elif self._sort_mode == "balance_desc":
            return sorted(platforms, key=lambda p: p.get("balance", 0), reverse=True)
        elif self._sort_mode == "balance_asc":
            return sorted(platforms, key=lambda p: p.get("balance", 0))
        elif self._sort_mode == "limit_desc":
            return sorted(platforms,
                key=lambda p: p.get("monthly_limit", 0) - p.get("monthly_used", 0),
                reverse=True)
        elif self._sort_mode == "limit_asc":
            return sorted(platforms,
                key=lambda p: p.get("monthly_limit", 0) - p.get("monthly_used", 0))
        return platforms

    def load(self, platforms: list):
        self._platforms_data = platforms
        platforms = self._sorted(platforms)

        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        
        for p in platforms:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Platform Name
            self.table.set_cell(row, 0, p["name"], bold=True)
            
            col = 1
            # Monthly Limit (if applicable)
            if self.p_type in ("wallet", "instapay"):
                rem = p.get("monthly_limit", 0) - p.get("monthly_used", 0)
                pct = int(p.get("monthly_used", 0) / p.get("monthly_limit", 1) * 100)
                color = COLORS["red"] if pct > 90 else COLORS["yellow"] if pct > 70 else COLORS["blue"]
                self.table.set_cell(row, col, f"{fmt_currency(rem)} ({pct}%)", color=color)
                col += 1
                
            # Current Balance
            self.table.set_cell(row, col, fmt_currency(p.get("balance", 0)), color=COLORS["green"], bold=True)
            col += 1
            
            # Transactions
            self.table.set_cell(row, col, str(p.get("transaction_count", 0)))
            col += 1
            
            # Actions
            self.table.add_action_buttons(row, col, [
                {'text': "➕ إضافة عملية", 'callback': lambda _, pid=p["id"]: self._open_transaction_form(pid), 'role': 'primary'},
                {'text': "⚙️ إعدادات", 'callback': lambda _, pid=p["id"]: self._open_actions(pid), 'role': 'secondary'}
            ])
            
        self.table.setSortingEnabled(True)
        # Update table height to fit all rows (Full-Page Scroll)
        self.table.setMinimumHeight(self.table.verticalHeader().length() + self.table.horizontalHeader().height() + 2)


    def _open_transaction_form(self, platform_id: int):
        from ui.screens.transaction_form import TransactionDialog
        dialog = TransactionDialog(platform_id=platform_id, parent=self)
        dialog.exec()
        self.refreshed.emit()

    def _open_actions(self, platform_id: int):
        platform = db.get_platform_by_id(platform_id)
        if not platform:
            return
        dialog = PlatformActionsDialog(platform, self)
        if dialog.exec() and dialog._result_action == "refresh":
            self.refreshed.emit()


# ══════════════════════════════════════════
#  Platforms Screen
# ══════════════════════════════════════════

class PlatformsScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__("المنصات", "الماكينات والمحافظ الإلكترونية")
        self._build_content()

    def _build_content(self):
        add_btn = QPushButton("＋  إضافة منصة")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_platform)
        self.add_action(add_btn)

        c = self.content()
        c.setContentsMargins(0, GAP_MD, 0, 0)
        c.setSpacing(GAP_LG)

        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._tab_machines = PlatformListTab("machine")
        self._tab_machines.refreshed.connect(self.refresh)
        self.tabs.addTab(self._tab_machines, "🏧  الماكينات")

        self._tab_wallets = PlatformListTab("wallet")
        self._tab_wallets.refreshed.connect(self.refresh)
        self.tabs.addTab(self._tab_wallets, "💳  المحافظ")

        self._tab_instapay = PlatformListTab("instapay")
        self._tab_instapay.refreshed.connect(self.refresh)
        self.tabs.addTab(self._tab_instapay, "🔷  انستا باي")

        c.addWidget(self.tabs)

    def refresh(self):
        platforms = db.get_all_platforms()
        self._tab_machines.load([p for p in platforms if p["type"] == "machine"])
        self._tab_wallets.load( [p for p in platforms if p["type"] == "wallet"])
        self._tab_instapay.load([p for p in platforms if p["type"] == "instapay"])

    def _add_platform(self):
        if AddPlatformDialog(self).exec():
            self.refresh()


# ══════════════════════════════════════════
#  Add Platform Dialog
# ══════════════════════════════════════════

class AddPlatformDialog(BaseDialog):

    def __init__(self, parent=None):
        super().__init__("➕ إضافة منصة جديدة", parent)
        self.setMinimumWidth(440)
        self._build_form()

    def _build_form(self):
        form = QFormLayout()
        form.setSpacing(GAP_MD)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: فوري، أمان، فودافون كاش")
        form.addRow("اسم المنصة *:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItem("🏧  ماكينة",           "machine")
        self.type_combo.addItem("💳  محفظة إلكترونية", "wallet")
        self.type_combo.addItem("🔷  انستا باي",         "instapay")
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("النوع:", self.type_combo)

        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(0, 10_000_000)
        self.balance_input.setDecimals(2)
        self.balance_input.setSuffix("  ج")
        form.addRow("الرصيد الابتدائي:", self.balance_input)

        self._limit_label = QLabel("الحد الشهري:")
        self.limit_input  = QDoubleSpinBox()
        self.limit_input.setRange(0, 10_000_000)
        self.limit_input.setDecimals(2)
        self.limit_input.setSuffix("  ج")
        self.limit_input.setValue(200000)
        form.addRow(self._limit_label, self.limit_input)

        self.body.addLayout(form)

        # Footer
        self.add_stretch()
        self.add_button("إلغاء", self.reject, role="secondary")
        self.add_button("إضافة ✓", self._save, role="primary")

        self._on_type_changed(0)

    def _on_type_changed(self, _):
        p_type = self.type_combo.currentData()
        if p_type == "machine":
            self.limit_input.setEnabled(False)
            self.limit_input.setValue(0)
            self._limit_label.setStyleSheet(f"color:{COLORS['text_muted']};")
        elif p_type == "instapay":
            self.limit_input.setEnabled(True)
            self.limit_input.setValue(400000)
            self._limit_label.setStyleSheet("")
        else:
            self.limit_input.setEnabled(True)
            self.limit_input.setValue(200000)
            self._limit_label.setStyleSheet("")

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم المنصة مطلوب")
            return
        try:
            db.add_platform(
                name,
                self.type_combo.currentData(),
                self.balance_input.value(),
                self.limit_input.value()
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
