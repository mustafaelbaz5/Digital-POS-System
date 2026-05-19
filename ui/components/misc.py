"""
ui/components/misc.py — Utility widgets, small helpers, and shared dialogs
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.components.base import BaseDialog
from ui.styles.theme import COLORS, FONT, GAP_MD, GAP_SM, GAP_XS
from ui.utils.formatters import fmt_currency

AlignLeft = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


# ══════════════════════════════════════════
#  SectionTitle
# ══════════════════════════════════════════


class SectionTitle(QWidget):
    """عنوان قسم مع عنوان فرعي اختياري."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, GAP_XS, 0, GAP_XS)
        layout.setSpacing(GAP_XS)

        t = QLabel(title)
        t.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;"
        )
        t.setAlignment(AlignLeft)
        layout.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(
                f"color:{COLORS['text_secondary']}; font-size:{FONT['sm']};"
            )
            s.setAlignment(AlignLeft)
            layout.addWidget(s)


# ══════════════════════════════════════════
#  GroupLabel
# ══════════════════════════════════════════


class GroupLabel(QWidget):
    """تسمية مجموعة مع نقطة لونية وخط فاصل."""

    def __init__(self, text: str, color: str = None, parent=None):
        super().__init__(parent)
        color = color or COLORS["accent"]
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, GAP_MD, 0, GAP_XS)
        layout.setSpacing(GAP_SM + 2)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background:{color}; border-radius:4px;")
        layout.addWidget(dot)

        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{color}; font-size:{FONT['xs']}; font-weight:bold;"
        )
        lbl.setAlignment(AlignLeft)
        layout.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(
            f"background:{COLORS['border']}; max-height:1px; border:none;"
        )
        layout.addWidget(line)


# ══════════════════════════════════════════
#  InfoRow
# ══════════════════════════════════════════


class InfoRow(QWidget):
    """صف معلومات بتسمية وقيمة."""

    def __init__(
        self, label: str, value: str = "—", value_color: str = None, parent=None
    ):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, GAP_SM, 0, GAP_SM)
        layout.setSpacing(GAP_MD)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"color:{COLORS['text_secondary']};")
        self._lbl.setAlignment(AlignLeft)
        layout.addWidget(self._lbl)

        layout.addStretch()

        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color:{value_color or COLORS['text_primary']}; font-weight:bold;"
        )
        self._val.setAlignment(AlignLeft)
        layout.addWidget(self._val)

    def set_value(self, value: str, color: str = None):
        self._val.setText(value)
        if color:
            self._val.setStyleSheet(f"color:{color}; font-weight:bold;")


# ══════════════════════════════════════════
#  Utility helpers
# ══════════════════════════════════════════


def make_divider() -> QFrame:
    """يرجع خطًا أفقيًا للفصل بين العناصر."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background:{COLORS['border']}; max-height:1px; border:none;")
    return line


def make_section_header(title: str, btn_text: str = None, btn_callback=None) -> QWidget:
    """يرجع شريط عنوان قسم مع زرار اختياري."""
    w = QWidget()
    w.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    row = QHBoxLayout(w)
    row.setContentsMargins(0, GAP_SM, 0, GAP_SM)
    row.setSpacing(GAP_MD)

    lbl = QLabel(title)
    lbl.setStyleSheet(
        f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;"
    )
    lbl.setAlignment(AlignLeft)
    row.addWidget(lbl)
    row.addStretch()

    if btn_text and btn_callback:
        btn = QPushButton(btn_text)
        btn.setObjectName("btn_secondary")
        btn.setFixedHeight(36)
        btn.clicked.connect(btn_callback)
        row.addWidget(btn)

    return w


# ══════════════════════════════════════════
#  Toast
# ══════════════════════════════════════════


class Toast(QLabel):
    """إشعار مؤقت يُغلق تلقائيًا بعد ثانيتين."""

    def __init__(self, parent, message: str, type: str = "success"):
        super().__init__(parent.window())
        self.setText(message)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bg = COLORS.get(type, COLORS["accent"])
        if type == "success":
            bg = COLORS["green"]
        if type in ("danger", "error"):
            bg = COLORS["red"]

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: white;
                border-radius: 20px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }}
        """)

        self.adjustSize()
        self.show()
        self._position()

        QTimer.singleShot(2000, self.deleteLater)

    def _position(self):
        parent = self.parent()
        if parent:
            rect = parent.rect()
            x = (rect.width() - self.width()) // 2
            y = rect.height() - self.height() - 40
            self.move(x, y)


def show_toast(parent, message: str, type: str = "success"):
    """اختصار لإنشاء Toast."""
    Toast(parent, message, type)


# ══════════════════════════════════════════
#  make_txn_actions / _ActionDialog
# ══════════════════════════════════════════


def make_txn_actions(t: dict, on_delete) -> QWidget:
    """يرجع QWidget فيه زرار إجراءات يفتح _ActionDialog."""
    btn = QPushButton("⋮ إجراءات")
    btn.setObjectName("btn_ghost")
    btn.setFixedHeight(26)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"font-size: {FONT['sm']}; padding: 0 12px;")

    def _open():
        parent_widget = btn.window()
        dlg = _ActionDialog(t, on_delete, parent_widget)
        dlg.exec()

    btn.clicked.connect(_open)

    wrap = QWidget()
    wrap.setObjectName("cell_wrapper_2")
    wrap.setStyleSheet("#cell_wrapper_2 { background: transparent; border: none; }")
    wl = QHBoxLayout(wrap)
    wl.setContentsMargins(2, 4, 2, 4)
    wl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    wl.addWidget(btn)
    return wrap


class _ActionDialog(BaseDialog):
    """حوار صغير يعرض تفاصيل العملية مع خيار الحذف فقط."""

    def __init__(self, t: dict, on_delete, parent=None):
        super().__init__("إجراءات العملية", parent)
        self._t = t
        self._on_delete = on_delete
        self.setMinimumWidth(380)
        self._build_content()

    def _build_content(self):
        t = self._t

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)

        service_lbl = QLabel(f"🛠️ {t.get('service_name', 'عملية بدون اسم')}")
        service_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:15px; font-weight:bold;"
        )
        cl.addWidget(service_lbl)

        amt_lbl = QLabel(
            f"💰 المبلغ المطلوب: {fmt_currency(t.get('amount_required', 0))}"
        )
        amt_lbl.setStyleSheet(f"color:{COLORS['accent']}; font-weight:bold;")
        cl.addWidget(amt_lbl)

        self.body.addWidget(card)
        self.body.addSpacing(GAP_SM)

        self.add_stretch()
        self.add_button("🗑️ حذف العملية", self._do_delete, role="danger")
        self.add_button("إغلاق", self.reject, role="secondary")

    def _do_delete(self):
        if (
            QMessageBox.question(
                self,
                "تأكيد الحذف",
                "⚠️ حذف العملية وعكس تأثيرها المالي؟ لا يمكن التراجع.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.accept()
            self._on_delete(self._t["id"])
