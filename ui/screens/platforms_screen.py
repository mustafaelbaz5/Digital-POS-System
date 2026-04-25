"""
platforms_screen.py — شاشة إدارة المنصات
Refactored: ScreenShell, grouped display, improved dialog
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QDoubleSpinBox, QFrame,
    QScrollArea, QSizePolicy, QInputDialog
)
from PyQt6.QtCore import Qt

from ui.styles.theme import COLORS
from ui.components.widgets import ScreenShell, SectionTitle, PlatformCard, make_divider
from utils.formatters import fmt_currency

import database as db


class PlatformsScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__("المنصات", "الماكينات والمحافظ الإلكترونية")
        self._build_content()

    def _build_content(self):
        # Header actions
        add_btn = QPushButton("＋  إضافة منصة")
        add_btn.setObjectName("btn_primary")
        add_btn.clicked.connect(self._add_platform)
        self.add_action(add_btn)

        c = self.content()

        # ── Machines section
        machines_hdr = QHBoxLayout()
        machines_lbl = QLabel("🏧  الماكينات")
        machines_lbl.setStyleSheet(
            f"color: {COLORS['blue_bright']}; font-size: 13px; font-weight: bold;"
        )
        machines_hdr.addWidget(machines_lbl)
        machines_hdr.addStretch()
        c.addLayout(machines_hdr)

        self._machines_scroll = _CardScrollRow()
        self._machines_scroll.deposit_clicked.connect(self._deposit_to_platform)
        c.addWidget(self._machines_scroll)

        c.addWidget(make_divider())

        # ── Wallets section
        wallets_hdr = QHBoxLayout()
        wallets_lbl = QLabel("💳  المحافظ الإلكترونية")
        wallets_lbl.setStyleSheet(
            f"color: {COLORS['purple']}; font-size: 13px; font-weight: bold;"
        )
        wallets_hdr.addWidget(wallets_lbl)
        wallets_hdr.addStretch()
        c.addLayout(wallets_hdr)

        self._wallets_scroll = _CardScrollRow()
        self._wallets_scroll.deposit_clicked.connect(self._deposit_to_platform)
        c.addWidget(self._wallets_scroll)

        c.addStretch()

    def refresh(self):
        platforms = db.get_all_platforms()
        machines = [p for p in platforms if p["type"] == "machine"]
        wallets  = [p for p in platforms if p["type"] == "wallet"]
        self._machines_scroll.load(machines)
        self._wallets_scroll.load(wallets)

    def _add_platform(self):
        dialog = AddPlatformDialog(self)
        if dialog.exec():
            self.refresh()

    def _deposit_to_platform(self, platform_id: int):
        platform = db.get_platform_by_id(platform_id)
        if not platform:
            return
        amount, ok = QInputDialog.getDouble(
            self, "إيداع",
            f"المبلغ المراد إيداعه في [{platform['name']}]:",
            min=0.01, decimals=2
        )
        if ok and amount > 0:
            try:
                db.deposit_to_platform(platform_id, amount)
                self.refresh()
                QMessageBox.information(
                    self, "تم ✅", f"تم الإيداع  {fmt_currency(amount)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════
#  Internal: Horizontal card scroll row
# ══════════════════════════════════════════

from PyQt6.QtCore import pyqtSignal

class _CardScrollRow(QWidget):
    deposit_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(180)
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
            if w:
                w.deleteLater()

        if not platforms:
            lbl = QLabel("لا توجد منصات في هذه الفئة")
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(lbl)
            return

        for p in platforms:
            card = PlatformCard(p)
            card.deposit_clicked.connect(self.deposit_clicked.emit)
            self._layout.addWidget(card)
        self._layout.addStretch()


# ══════════════════════════════════════════
#  Add Platform Dialog
# ══════════════════════════════════════════

class AddPlatformDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("إضافة منصة جديدة")
        self.setMinimumWidth(380)
        self.setMinimumHeight(280)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("➕  إضافة منصة جديدة")
        title.setObjectName("label_title")
        title.setStyleSheet(f"font-size: 15px; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: فوري، أمان، فودافون كاش")
        form.addRow("اسم المنصة *:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItem("🏧  ماكينة", "machine")
        self.type_combo.addItem("💳  محفظة إلكترونية", "wallet")
        form.addRow("النوع:", self.type_combo)

        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(0, 10_000_000)
        self.balance_input.setDecimals(2)
        self.balance_input.setSuffix("  ج")
        form.addRow("الرصيد الابتدائي:", self.balance_input)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(8)

        cancel = QPushButton("إلغاء")
        cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        save = QPushButton("حفظ")
        save.setObjectName("btn_primary")
        save.clicked.connect(self._save)
        btns.addWidget(save)

        layout.addLayout(btns)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المنصة")
            return

        p_type  = self.type_combo.currentData()
        balance = self.balance_input.value()

        try:
            pid = db.add_platform(name, p_type)
            if balance > 0:
                db.deposit_to_platform(pid, balance, "رصيد ابتدائي")
            QMessageBox.information(self, "تم ✅", f"تم إضافة [{name}] بنجاح")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))