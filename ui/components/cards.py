"""
ui/components/cards.py — Card components: CardGroup, StatCard, MiniStatCard, PlatformCard
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.styles.theme import (
    CARD_RADIUS,
    COLORS,
    FONT,
    GAP_MD,
    GAP_SM,
    GAP_XS,
    MARGIN_CARD,
)
from ui.styles import theme

AlignLeft = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


# ══════════════════════════════════════════
#  CardGroup
# ══════════════════════════════════════════


class CardGroup(QFrame):
    """حاوية تجمع عناصر داخل بطاقة منسقة مع عنوان ملون."""

    def __init__(self, title: str = "", section_type: str = "accent", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, MARGIN_CARD)
        self._layout.setSpacing(GAP_MD)

        if title:
            # Create a colored header
            header_color = theme.get_section_color(section_type)
            self.header = QFrame()
            self.header.setObjectName("card_header")
            self.header.setStyleSheet(f"background: {header_color};")
            
            hl = QHBoxLayout(self.header)
            hl.setContentsMargins(16, 0, 16, 0)
            
            self.title_lbl = QLabel(title)
            self.title_lbl.setObjectName("card_header_title")
            hl.addWidget(self.title_lbl)
            hl.addStretch()
            
            self._layout.addWidget(self.header)
            
        # Body container for content
        self.body_layout = QVBoxLayout()
        self.body_layout.setContentsMargins(20, 10, 20, 10)
        self.body_layout.setSpacing(GAP_MD)
        self._layout.addLayout(self.body_layout)

    def add_widget(self, widget: QWidget):
        self.body_layout.addWidget(widget)

    def add_layout(self, layout):
        self.body_layout.addLayout(layout)

    def layout(self) -> QVBoxLayout:
        return self.body_layout


# ══════════════════════════════════════════
#  StatCard
# ══════════════════════════════════════════


class StatCard(QWidget):
    """بطاقة إحصائية مع شريط لوني جانبي."""

    def __init__(
        self,
        title: str,
        value: str = "—",
        accent_color: str = None,
        icon: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._accent = accent_color or COLORS["accent"]
        self._build(title, value, icon)

    def _build(self, title: str, value: str, icon: str):
        self.setObjectName("stat_card")
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._bar = QFrame()
        self._bar.setFixedWidth(5)
        self._bar.setStyleSheet(
            f"background:{self._accent};"
            f"border-top-right-radius:{CARD_RADIUS};"
            f"border-bottom-right-radius:{CARD_RADIUS};"
        )
        outer.addWidget(self._bar)

        inner = QVBoxLayout()
        inner.setContentsMargins(MARGIN_CARD, MARGIN_CARD, MARGIN_CARD, MARGIN_CARD)
        inner.setSpacing(GAP_SM)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("stat_label")
        title_lbl.setAlignment(AlignLeft)
        inner.addWidget(title_lbl)

        self._value = QLabel(value)
        self._value.setObjectName("stat_value")
        self._value.setAlignment(AlignLeft)
        self._value.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['2xl']}; font-weight:bold;"
        )
        inner.addWidget(self._value)

        outer.addLayout(inner)

    def set_value(self, value: str):
        self._value.setText(value)

    def set_accent(self, color: str):
        self._accent = color
        self._bar.setStyleSheet(
            f"background:{color};"
            f"border-top-right-radius:{CARD_RADIUS};"
            f"border-bottom-right-radius:{CARD_RADIUS};"
        )


# ══════════════════════════════════════════
#  MiniStatCard
# ══════════════════════════════════════════


class MiniStatCard(QFrame):
    """بطاقة إحصائية صغيرة."""

    def __init__(self, title: str, value: str = "—", color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(160)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._val_lbl = QLabel(value)
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val_lbl.setStyleSheet(
            f"color: {color or COLORS['text_primary']}; font-size: 20px; font-weight: 900; background: transparent; border:none;"
        )
        layout.addWidget(self._val_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT['xs']}; font-weight: bold; background: transparent; border:none;"
        )
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

    def set_value(self, value: str, color: str = None):
        self._val_lbl.setText(value)
        if color:
            self._val_lbl.setStyleSheet(
                f"color: {color}; font-size: 20px; font-weight: 900; background: transparent; border:none;"
            )


# ══════════════════════════════════════════
#  PlatformCard
# ══════════════════════════════════════════


class PlatformCard(QWidget):
    """بطاقة عرض منصة مع زرار إيداع."""

    deposit_clicked = pyqtSignal(int)

    def __init__(self, platform: dict, parent=None):
        super().__init__(parent)
        self.platform_id = platform["id"]
        self._build(platform)

    def _build(self, p: dict):
        self.setObjectName("card")
        self.setFixedWidth(240)
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(MARGIN_CARD, MARGIN_CARD, MARGIN_CARD, MARGIN_CARD)
        layout.setSpacing(GAP_MD)

        ptype = p.get("type", "machine")
        type_color, type_text = {
            "machine": (COLORS["blue"], "ماكينة"),
            "wallet": (COLORS["purple"], "محفظة"),
            "instapay": (COLORS["cyan"], "انستا باي"),
        }.get(ptype, (COLORS["text_muted"], ptype))

        hrow = QHBoxLayout()
        hrow.setSpacing(GAP_SM)

        name = QLabel(p["name"])
        name.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['md']}; font-weight:bold; background:transparent; border:none;"
        )
        name.setAlignment(AlignLeft)
        hrow.addWidget(name)
        hrow.addStretch()

        badge = QLabel(f" {type_text} ")
        badge.setStyleSheet(
            f"color:{type_color}; background:{type_color}20;"
            f"border-radius:5px; font-size:{FONT['xs']}; font-weight:bold; padding:2px 6px; border:none;"
        )
        hrow.addWidget(badge)
        layout.addLayout(hrow)

        layout.addSpacing(GAP_XS)

        bal = p.get("balance", 0)
        bal_lbl = QLabel(f"{bal:,.0f} ج")
        bal_lbl.setStyleSheet(
            f"color:{COLORS['accent']}; font-size:{FONT['xl']}; font-weight:bold; background:transparent; border:none;"
        )
        bal_lbl.setAlignment(AlignLeft)
        layout.addWidget(bal_lbl)

        layout.addStretch()

        dep = QPushButton("+ إيداع جديد")
        dep.setObjectName("btn_ghost")
        dep.setFixedHeight(32)
        dep.setCursor(Qt.CursorShape.PointingHandCursor)
        dep.clicked.connect(lambda: self.deposit_clicked.emit(self.platform_id))
        layout.addWidget(dep)
