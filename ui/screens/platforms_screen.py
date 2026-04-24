"""
Platforms Screen — شاشة إدارة المنصات
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QScrollArea, QGridLayout,
    QDoubleSpinBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt

from ui.styles.theme import COLORS
from ui.components.widgets import SectionTitle, PlatformCard
from utils.formatters import fmt_currency

import database as db


# ══════════════════════════════════════════
#  شاشة المنصات
# ══════════════════════════════════════════

class PlatformsScreen(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # العنوان + زرار الإضافة
        header = QHBoxLayout()
        add_btn = QPushButton("＋  إضافة منصة")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(40)
        add_btn.clicked.connect(self._add_platform)
        header.addWidget(add_btn)
        header.addStretch()
        header.addWidget(SectionTitle("إدارة المنصات"))
        root.addLayout(header)

        # ── الماكينات
        root.addWidget(QLabel("🏧  الماكينات", styleSheet=f"color:{COLORS['blue_light']}; font-size:15px; font-weight:bold;"))
        self.machines_layout = QHBoxLayout()
        self.machines_layout.setSpacing(12)
        self.machines_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addLayout(self.machines_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {COLORS['border']};")
        root.addWidget(line)

        # ── المحافظ
        root.addWidget(QLabel("💳  المحافظ الإلكترونية", styleSheet=f"color:{COLORS['purple']}; font-size:15px; font-weight:bold;"))
        self.wallets_layout = QHBoxLayout()
        self.wallets_layout.setSpacing(12)
        self.wallets_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addLayout(self.wallets_layout)

        root.addStretch()

    def refresh(self):
        """تحديث عرض المنصات"""
        self._clear_layout(self.machines_layout)
        self._clear_layout(self.wallets_layout)

        platforms = db.get_all_platforms()

        machines = [p for p in platforms if p["type"] == "machine"]
        wallets  = [p for p in platforms if p["type"] == "wallet"]

        for p in machines:
            card = PlatformCard(p)
            card.deposit_clicked.connect(self._deposit_to_platform)
            self.machines_layout.addWidget(card)

        for p in wallets:
            card = PlatformCard(p)
            card.deposit_clicked.connect(self._deposit_to_platform)
            self.wallets_layout.addWidget(card)

        if not machines:
            self.machines_layout.addWidget(self._empty_label())
        if not wallets:
            self.wallets_layout.addWidget(self._empty_label())

        self.machines_layout.addStretch()
        self.wallets_layout.addStretch()

    def _clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w:
                w.deleteLater()

    def _empty_label(self) -> QLabel:
        lbl = QLabel("لا توجد منصات")
        lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
        return lbl

    def _add_platform(self):
        dialog = AddPlatformDialog(self)
        if dialog.exec():
            self.refresh()

    def _deposit_to_platform(self, platform_id: int):
        from PyQt6.QtWidgets import QInputDialog
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
                QMessageBox.information(self, "تم", f"تم الإيداع ✅  {fmt_currency(amount)}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════
#  ديالوج إضافة منصة
# ══════════════════════════════════════════

class AddPlatformDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("إضافة منصة جديدة")
        self.setFixedWidth(380)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(QLabel("➕  إضافة منصة جديدة", styleSheet=f"color:{COLORS['text_primary']}; font-size:16px; font-weight:bold;"))

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: فوري، أمان، فودافون كاش")
        form.addRow("اسم المنصة:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["ماكينة", "محفظة إلكترونية"])
        form.addRow("النوع:", self.type_combo)

        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(0, 10_000_000)
        self.balance_input.setDecimals(2)
        self.balance_input.setSuffix("  ج")
        form.addRow("الرصيد الابتدائي:", self.balance_input)

        layout.addLayout(form)

        # الأزرار
        btns = QHBoxLayout()
        cancel = QPushButton("إلغاء")
        cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject)

        save = QPushButton("حفظ")
        save.setObjectName("btn_primary")
        save.clicked.connect(self._save)

        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المنصة")
            return

        p_type   = "machine" if self.type_combo.currentIndex() == 0 else "wallet"
        balance  = self.balance_input.value()

        try:
            pid = db.add_platform(name, p_type)
            if balance > 0:
                db.deposit_to_platform(pid, balance, "رصيد ابتدائي")
            QMessageBox.information(self, "تم", f"تم إضافة [{name}] بنجاح ✅")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
