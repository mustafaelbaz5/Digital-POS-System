"""
platforms_screen.py — شاشة إدارة المنصات (UI جديد)
تابات (ماكينات / محافظ / انستا باي) + صفوف جدول بدل كروت
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QDoubleSpinBox, QFrame,
    QTabWidget, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.styles.theme import (
    COLORS, FONT, ROW_HEIGHT, 
    GAP_XS, GAP_SM, GAP_MD, GAP_LG, MARGIN_CARD
)
from ui.components.widgets import ScreenShell, make_divider, CardGroup, BaseDialog
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
        bal_lbl.setFixedWidth(160)
        bal_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(bal_lbl)

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
        layout.setContentsMargins(GAP_MD, GAP_MD, GAP_MD, GAP_MD)
        layout.setSpacing(GAP_MD)

        # ── Toolbar Card
        sort_group = CardGroup()
        sb = QHBoxLayout()
        sb.setSpacing(GAP_SM)
        sb.setAlignment(Qt.AlignmentFlag.AlignLeft)

        sort_lbl = QLabel("ترتيب:")
        sort_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
        sb.addWidget(sort_lbl)

        self._sort_mode = "default"   # default | balance_desc | limit_asc | limit_desc

        sort_options = [
            ("الافتراضي",        "default"),
            ("الرصيد ↓",         "balance_desc"),
            ("الحد المتبقي ↓",   "limit_desc"),
            ("الحد المتبقي ↑",   "limit_asc"),
        ]
        self._sort_btns = {}
        for label, mode in sort_options:
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, m=mode: self._set_sort(m))
            self._sort_btns[mode] = btn
            sb.addWidget(btn)

        sb.addStretch()
        sort_group.add_layout(sb)
        layout.addWidget(sort_group)
        self._apply_sort_styles()

        # ── List Card
        list_group = CardGroup()
        list_layout = QVBoxLayout()
        list_layout.setSpacing(0)
        list_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet(
            f"background:{COLORS['bg_elevated']};"
            f"border-bottom:1px solid {COLORS['border']};"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(0)

        def hdr(text, width=None, align=Qt.AlignmentFlag.AlignLeft):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{COLORS['text_secondary']};font-size:11px;"
                f"font-weight:bold;background:transparent;border:none;"
                f"text-transform: uppercase;"
            )
            lbl.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
            if width:
                lbl.setFixedWidth(width)
            return lbl

        hl.addWidget(hdr("اسم المنصة", 180))
        hl.addStretch()

        if self.p_type in ("wallet", "instapay"):
            hl.addWidget(hdr("المتبقي من الحد", 190))
            hl.addStretch()

        hl.addWidget(hdr("الرصيد الحالي", 160, Qt.AlignmentFlag.AlignLeft))
        hl.addWidget(hdr("العمليات", 110))
        hl.addSpacing(8)
        hl.addWidget(hdr("إجراءات", 100))
        list_layout.addWidget(header)

        # منطقه الصفوف
        self._rows_widget = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)

        list_layout.addWidget(self._rows_widget)
        list_group.add_layout(list_layout)
        layout.addWidget(list_group)
        
        layout.addStretch()

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

    def _sorted(self, platforms: list) -> list:
        if self._sort_mode == "balance_desc":
            return sorted(platforms, key=lambda p: p.get("balance", 0), reverse=True)
        elif self._sort_mode == "limit_desc":
            return sorted(platforms,
                key=lambda p: p.get("monthly_limit", 0) - p.get("monthly_used", 0),
                reverse=True)
        elif self._sort_mode == "limit_asc":
            return sorted(platforms,
                key=lambda p: p.get("monthly_limit", 0) - p.get("monthly_used", 0))
        return platforms

    def load(self, platforms: list):
        self._platforms_data = platforms          # حفظ للـ re-sort
        platforms = self._sorted(platforms)

        # مسح القديم
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not platforms:
            empty = QLabel("لا توجد منصات في هذه الفئة")
            empty.setStyleSheet(
                f"color:{COLORS['text_muted']};font-size:13px;padding:28px;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._rows_layout.addWidget(empty)
            return

        for i, p in enumerate(platforms):
            row = PlatformRow(p, alternate=(i % 2 == 1))
            row.actions_clicked.connect(self._open_actions)
            row.add_transaction_clicked.connect(self._open_transaction_form)
            self._rows_layout.addWidget(row)

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
