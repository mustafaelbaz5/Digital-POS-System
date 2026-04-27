"""
platforms_screen.py — شاشة إدارة المنصات
tasks: 4 (instapay), 5 (delete), 6 (daily commission), RTL fixes
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QDoubleSpinBox, QFrame,
    QScrollArea, QSizePolicy, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.styles.theme import COLORS, FONT, CARD_RADIUS
from ui.components.widgets import ScreenShell, SectionTitle, make_divider
from utils.formatters import fmt_currency

import database as db


# ══════════════════════════════════════════
#  Platform Card — with delete & commission
# ══════════════════════════════════════════

class PlatformCard(QWidget):
    deposit_clicked    = pyqtSignal(int)
    delete_clicked     = pyqtSignal(int)
    commission_clicked = pyqtSignal(int)

    def __init__(self, platform: dict, parent=None):
        super().__init__(parent)
        self.platform_id = platform["id"]
        self._build_ui(platform)

    def _build_ui(self, p: dict):
        self.setObjectName("card")
        self.setMinimumWidth(210)
        self.setMaximumWidth(260)
        self.setMinimumHeight(190)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        p_type = p["type"]
        if p_type == "machine":
            type_color = COLORS["blue"]
            type_text  = "ماكينة"
        elif p_type == "wallet":
            type_color = COLORS["purple"]
            type_text  = "محفظة"
        else:  # instapay
            type_color = COLORS["cyan"]
            type_text  = "انستا باي"

        # Header: name RIGHT, badge + delete LEFT
        header = QHBoxLayout()
        name_lbl = QLabel(p["name"])
        name_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: {FONT['lg']};"
            f"font-weight: bold; font-family: {FONT['family']};"
        )
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(name_lbl)
        header.addStretch()

        badge = QLabel(f"  {type_text}  ")
        badge.setStyleSheet(
            f"color: {type_color}; background: {type_color}22;"
            f"border: 1px solid {type_color}55; border-radius: 5px;"
            f"font-size: {FONT['xs']}; font-weight: bold;"
            f"font-family: {FONT['family']}; padding: 2px 0;"
        )
        header.addWidget(badge)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(22, 22)
        del_btn.setStyleSheet(
            f"background: {COLORS['red_bg']}; color: {COLORS['red']};"
            f"border: 1px solid {COLORS['red_border']}; border-radius: 4px;"
            f"font-size: 10px; font-weight: bold;"
        )
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.platform_id))
        header.addWidget(del_btn)
        layout.addLayout(header)

        # Divider
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(div)

        # Balance
        balance = p.get("balance", 0)
        bal_color = COLORS["green"] if balance > 0 else COLORS["text_muted"]
        balance_lbl = QLabel(f"{balance:,.2f} ج")
        balance_lbl.setStyleSheet(
            f"color: {bal_color}; font-size: {FONT['2xl']};"
            f"font-weight: bold; font-family: {FONT['family']};"
        )
        balance_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(balance_lbl)

        # Monthly limit for wallet / instapay
        if p_type in ("wallet", "instapay"):
            used      = p.get("monthly_used", 0)
            limit     = p.get("monthly_limit", 200000)
            remaining = limit - used
            pct       = min(100, int(used / limit * 100)) if limit else 0
            limit_color = (COLORS["red"] if pct >= 90 else
                           COLORS["yellow"] if pct >= 70 else COLORS["text_muted"])
            limit_lbl = QLabel(f"متبقي: {remaining:,.0f} / {limit:,.0f} ج")
            limit_lbl.setStyleSheet(f"color: {limit_color}; font-size: {FONT['xs']}; font-family: {FONT['family']};")
            limit_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(limit_lbl)

        layout.addStretch()

        # Action buttons
        btns = QHBoxLayout(); btns.setSpacing(6)

        dep_btn = QPushButton("إيداع +")
        dep_btn.setObjectName("btn_ghost")
        dep_btn.setFixedHeight(28)
        dep_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_btn.clicked.connect(lambda: self.deposit_clicked.emit(self.platform_id))
        btns.addWidget(dep_btn)

        # Daily commission — machines only (task 6)
        if p_type == "machine":
            comm_btn = QPushButton("عمولة يومية")
            comm_btn.setObjectName("btn_ghost")
            comm_btn.setFixedHeight(28)
            comm_btn.setStyleSheet(
                f"color: {COLORS['yellow']}; border-color: {COLORS['yellow_border']};"
                f"background: {COLORS['yellow_bg']};"
            )
            comm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            comm_btn.clicked.connect(lambda: self.commission_clicked.emit(self.platform_id))
            btns.addWidget(comm_btn)

        layout.addLayout(btns)


# ══════════════════════════════════════════
#  Card Scroll Row
# ══════════════════════════════════════════

class _CardScrollRow(QWidget):
    deposit_clicked    = pyqtSignal(int)
    delete_clicked     = pyqtSignal(int)
    commission_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(210)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._layout = QHBoxLayout(self._container)
        self._layout.setContentsMargins(0, 4, 0, 4)
        self._layout.setSpacing(12)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        scroll.setWidget(self._container)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    def load(self, platforms: list):
        for i in reversed(range(self._layout.count())):
            w = self._layout.itemAt(i).widget()
            if w: w.deleteLater()

        if not platforms:
            lbl = QLabel("لا توجد منصات في هذه الفئة")
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(lbl)
            return

        for p in platforms:
            card = PlatformCard(p)
            card.deposit_clicked.connect(self.deposit_clicked.emit)
            card.delete_clicked.connect(self.delete_clicked.emit)
            card.commission_clicked.connect(self.commission_clicked.emit)
            self._layout.addWidget(card)
        self._layout.addStretch()


# ══════════════════════════════════════════
#  Platforms Screen
# ══════════════════════════════════════════

class PlatformsScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__("المنصات", "الماكينات والمحافظ الإلكترونية")
        self._build_content()

    def _build_content(self):
        add_btn = QPushButton("+ إضافة منصة")
        add_btn.setObjectName("btn_primary")
        add_btn.clicked.connect(self._add_platform) # type: ignore
        self.add_action(add_btn)

        c = self.content()

        # ── Machines section
        machines_lbl = QLabel("⚙️  الماكينات")
        machines_lbl.setStyleSheet(
            f"color: {COLORS['blue']}; font-size: 13px; font-weight: bold;"
        )
        machines_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        c.addWidget(machines_lbl)

        self._machines_scroll = _CardScrollRow()
        self._machines_scroll.deposit_clicked.connect(self._deposit_to_platform)
        self._machines_scroll.delete_clicked.connect(self._delete_platform)
        self._machines_scroll.commission_clicked.connect(self._daily_commission)
        c.addWidget(self._machines_scroll)

        c.addWidget(make_divider())

        # ── Wallets section
        wallets_lbl = QLabel("💳  المحافظ الإلكترونية")
        wallets_lbl.setStyleSheet(
            f"color: {COLORS['purple']}; font-size: 13px; font-weight: bold;"
        )
        wallets_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        c.addWidget(wallets_lbl)

        self._wallets_scroll = _CardScrollRow()
        self._wallets_scroll.deposit_clicked.connect(self._deposit_to_platform)
        self._wallets_scroll.delete_clicked.connect(self._delete_platform)
        c.addWidget(self._wallets_scroll)

        c.addWidget(make_divider())

        # ── Instapay section (task 4)
        instapay_lbl = QLabel("🔷  انستا باي")
        instapay_lbl.setStyleSheet(
            f"color: {COLORS['cyan']}; font-size: 13px; font-weight: bold;"
        )
        instapay_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        c.addWidget(instapay_lbl)

        self._instapay_scroll = _CardScrollRow()
        self._instapay_scroll.deposit_clicked.connect(self._deposit_to_platform)
        self._instapay_scroll.delete_clicked.connect(self._delete_platform)
        c.addWidget(self._instapay_scroll)

        c.addStretch()

    def refresh(self):
        platforms = db.get_all_platforms()
        machines  = [p for p in platforms if p["type"] == "machine"]
        wallets   = [p for p in platforms if p["type"] == "wallet"]
        instapay  = [p for p in platforms if p["type"] == "instapay"]
        self._machines_scroll.load(machines)
        self._wallets_scroll.load(wallets)
        self._instapay_scroll.load(instapay)

    def _add_platform(self):
        if AddPlatformDialog(self).exec():
            self.refresh()

    def _deposit_to_platform(self, platform_id: int):
        platform = db.get_platform_by_id(platform_id)
        if not platform: return
        amount, ok = QInputDialog.getDouble(
            self, "إيداع",
            f"المبلغ المراد إيداعه في [{platform['name']}]:",
            min=0.01, decimals=2
        )
        if ok and amount > 0:
            try:
                db.deposit_to_platform(platform_id, amount)
                self.refresh()
                QMessageBox.information(self, "تم ✅", f"تم الإيداع  {fmt_currency(amount)}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _delete_platform(self, platform_id: int):
        """task 5: soft-delete with confirmation"""
        platform = db.get_platform_by_id(platform_id)
        if not platform: return
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف المنصة [{platform['name']}]؟\n"
            f"رصيدها الحالي: {fmt_currency(platform.get('balance', 0))}\n\n"
            "⚠️ سيتم إخفاؤها من كل القوائم.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            db.delete_platform(platform_id)
            self.refresh()

    def _daily_commission(self, platform_id: int):
        """task 6: daily commission for machines"""
        platform = db.get_platform_by_id(platform_id)
        if not platform: return
        amount, ok = QInputDialog.getDouble(
            self, "العمولة اليومية",
            f"أدخل مبلغ العمولة لـ [{platform['name']}]:\n"
            f"(رصيد الماكينة: {fmt_currency(platform.get('balance', 0))})",
            min=0.01, decimals=2
        )
        if ok and amount > 0:
            try:
                db.record_daily_commission(platform_id, amount)
                self.refresh()
                QMessageBox.information(
                    self, "تم ✅",
                    f"تم تسجيل العمولة اليومية: {fmt_currency(amount)}\n"
                    f"تم خصمها من [{platform['name']}] وإضافتها للخزينة."
                )
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════
#  Add Platform Dialog
# ══════════════════════════════════════════

class AddPlatformDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("إضافة منصة جديدة")
        self.setMinimumWidth(400)
        self.setMinimumHeight(320)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("➕  إضافة منصة جديدة")
        title.setObjectName("label_title")
        title.setStyleSheet(f"font-size: 15px; color: {COLORS['text_primary']};")
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: فوري، أمان، فودافون كاش")
        form.addRow("اسم المنصة *:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItem("ماكينة", "machine")
        self.type_combo.addItem("محفظة إلكترونية", "wallet")
        self.type_combo.addItem("انستا باي", "instapay")
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("النوع:", self.type_combo)

        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(0, 10_000_000)
        self.balance_input.setDecimals(2)
        self.balance_input.setSuffix("  ج")
        form.addRow("الرصيد الابتدائي:", self.balance_input)

        self.limit_input = QDoubleSpinBox()
        self.limit_input.setRange(0, 10_000_000)
        self.limit_input.setDecimals(2)
        self.limit_input.setSuffix("  ج")
        self.limit_input.setValue(200000)
        self._limit_row_label = QLabel("الحد الشهري:")
        form.addRow(self._limit_row_label, self.limit_input)

        layout.addLayout(form)
        layout.addStretch()

        btns = QHBoxLayout(); btns.setSpacing(8)
        cancel = QPushButton("إلغاء")
        cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        save = QPushButton("إضافة ✅")
        save.setObjectName("btn_primary")
        save.clicked.connect(self._save)
        btns.addWidget(save)
        layout.addLayout(btns)

        self._on_type_changed(0)

    def _on_type_changed(self, idx):
        p_type = self.type_combo.currentData()
        if p_type == "machine":
            self.limit_input.setEnabled(False)
            self.limit_input.setValue(0)
            self._limit_row_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        elif p_type == "instapay":
            self.limit_input.setEnabled(True)
            self.limit_input.setValue(400000)
            self._limit_row_label.setStyleSheet("")
        else:
            self.limit_input.setEnabled(True)
            self.limit_input.setValue(200000)
            self._limit_row_label.setStyleSheet("")

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم المنصة مطلوب")
            return
        p_type = self.type_combo.currentData()
        balance = self.balance_input.value()
        limit   = self.limit_input.value()
        try:
            db.add_platform(name, p_type, balance, limit)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
