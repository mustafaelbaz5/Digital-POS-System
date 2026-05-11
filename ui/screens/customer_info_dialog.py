"""
customer_info_dialog.py — نافذة معلومات العميل وإدارة أكواد الشحن
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import BaseDialog
from ui.styles.theme import COLORS, FONT, GAP_MD, GAP_SM
from utils.formatters import fmt_currency

RTL = Qt.LayoutDirection.RightToLeft


class CustomerInfoDialog(BaseDialog):
    """نافذة معلومات العميل الكاملة مع إدارة أكواد الشحن"""

    def __init__(self, customer: dict, parent=None):
        super().__init__(f"معلومات العميل  —  {customer['name']}", parent)
        self.customer = customer
        self.setMinimumWidth(540)
        self.setMinimumHeight(540)
        self.setModal(True)
        self._build_content()

    def _build_content(self):
        # ══ Section A: Basic Profile ════════════════════════════════════
        profile = QFrame()
        profile.setObjectName("card")
        pl = QVBoxLayout(profile)
        pl.setContentsMargins(20, 16, 20, 16)
        pl.setSpacing(10)

        def _info_row(label: str, value: str, val_color: str = None, bold: bool = False):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color:{COLORS['text_secondary']}; font-size:{FONT['sm']}; "
                f"background:transparent; border:none;"
            )
            lbl.setFixedWidth(90)
            val = QLabel(value)
            val.setStyleSheet(
                f"color:{val_color or COLORS['text_primary']}; "
                f"font-size:{FONT['md']}; "
                f"font-weight:{'bold' if bold else 'normal'}; "
                f"background:transparent; border:none;"
            )
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            pl.addLayout(row)

        _info_row("الاسم:", self.customer.get("name", "—"), bold=True)

        group = self.customer.get("group_name") or "بدون مجموعة"
        _info_row("المجموعة:", group, COLORS["text_muted"])

        phone = self.customer.get("phone") or "—"
        _info_row("التليفون:", phone, COLORS["text_secondary"])

        debt = float(self.customer.get("total_debt") or 0)
        if debt > 0:
            bal_text, bal_color = f"عليه  {fmt_currency(debt)}", COLORS["red"]
        elif debt < 0:
            bal_text, bal_color = f"له  {fmt_currency(abs(debt))}", COLORS["green"]
        else:
            bal_text, bal_color = "متسوي", COLORS["text_muted"]
        _info_row("الرصيد:", bal_text, bal_color, bold=True)

        self.body.addWidget(profile)

        # ══ Section B: Shipping Codes ════════════════════════════════════
        sec_hdr = QHBoxLayout()
        sec_title = QLabel("🔑  أكواد الشحن")
        sec_title.setStyleSheet(
            f"font-weight:bold; color:{COLORS['text_primary']}; font-size:{FONT['md']};"
        )
        sec_hdr.addWidget(sec_title)
        sec_hdr.addStretch()
        self.body.addLayout(sec_hdr)

        # Scrollable codes list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(180)
        scroll.setMaximumHeight(280)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._codes_widget = QWidget()
        self._codes_widget.setStyleSheet("background: transparent;")
        self._codes_vbox = QVBoxLayout(self._codes_widget)
        self._codes_vbox.setContentsMargins(0, 0, 6, 0)
        self._codes_vbox.setSpacing(5)

        scroll.setWidget(self._codes_widget)
        self.body.addWidget(scroll)

        # ── Add-code row
        add_row = QHBoxLayout()
        add_row.setSpacing(GAP_SM)

        self._new_code_input = QLineEdit()
        self._new_code_input.setPlaceholderText("أدخل الكود الجديد ثم اضغط إضافة...")
        self._new_code_input.setFixedHeight(40)
        self._new_code_input.returnPressed.connect(self._add_code)
        add_row.addWidget(self._new_code_input, 1)

        add_btn = QPushButton("➕  إضافة كود جديد")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(40)
        add_btn.clicked.connect(self._add_code)
        add_row.addWidget(add_btn)
        self.body.addLayout(add_row)

        # Footer
        self.add_stretch()
        self.add_button("إغلاق", self.reject, role="secondary")

        self._refresh_codes()

    # ── Codes list helpers ─────────────────────────────────────────────

    def _refresh_codes(self):
        while self._codes_vbox.count():
            item = self._codes_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        codes = db.get_shipping_codes(self.customer["id"])

        if not codes:
            empty = QLabel("لا يوجد أكواد مسجلة لهذا العميل")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color:{COLORS['text_muted']}; font-size:{FONT['sm']}; "
                f"padding:28px 0; background:transparent;"
            )
            self._codes_vbox.addWidget(empty)
        else:
            for code_dict in codes:
                self._codes_vbox.addWidget(self._make_code_row(code_dict))

        self._codes_vbox.addStretch()

    def _make_code_row(self, code_dict: dict) -> QWidget:
        row = QWidget()
        row.setFixedHeight(46)
        row.setLayoutDirection(RTL)
        row.setStyleSheet(
            f"background:{COLORS['bg_elevated']}; "
            f"border:1px solid {COLORS['border']}; border-radius:6px;"
        )
        hl = QHBoxLayout(row)
        hl.setContentsMargins(14, 0, 8, 0)
        hl.setSpacing(8)

        code_lbl = QLabel(f"🔑  {code_dict['code']}")
        code_lbl.setStyleSheet(
            f"color:{COLORS['accent']}; font-weight:bold; font-size:{FONT['md']}; "
            f"background:transparent; border:none;"
        )
        hl.addWidget(code_lbl, 1)

        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(34, 34)
        edit_btn.setToolTip("تعديل الكود")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet(
            f"background:{COLORS['bg_hover']}; color:{COLORS['blue']}; "
            f"border:2px solid {COLORS['border']}; border-radius:6px; font-size:14px;"
        )
        edit_btn.clicked.connect(lambda _, c=code_dict: self._edit_code(c))
        hl.addWidget(edit_btn)

        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(34, 34)
        del_btn.setToolTip("حذف الكود")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(
            f"background:{COLORS['red_bg']}; color:{COLORS['red']}; "
            f"border:2px solid {COLORS['red_border']}; border-radius:6px; font-size:14px;"
        )
        del_btn.clicked.connect(lambda _, c=code_dict: self._delete_code(c))
        hl.addWidget(del_btn)

        return row

    # ── CRUD actions ───────────────────────────────────────────────────

    def _add_code(self):
        code = self._new_code_input.text().strip()
        if not code:
            return
        try:
            db.add_shipping_code(self.customer["id"], code)
            self._new_code_input.clear()
            self._refresh_codes()
        except ValueError as e:
            QMessageBox.warning(self, "تنبيه", str(e))

    def _edit_code(self, code_dict: dict):
        new_code, ok = QInputDialog.getText(
            self,
            "تعديل الكود",
            "الكود الجديد:",
            text=code_dict["code"],
        )
        if ok and new_code.strip():
            try:
                db.update_shipping_code(code_dict["id"], new_code.strip())
                self._refresh_codes()
            except ValueError as e:
                QMessageBox.warning(self, "تنبيه", str(e))

    def _delete_code(self, code_dict: dict):
        if (
            QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل تريد حذف الكود «{code_dict['code']}»؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            db.delete_shipping_code(code_dict["id"])
            self._refresh_codes()
