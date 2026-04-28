"""
widgets.py — Component Library v3 (Clean Professional Dark)
===========================================================
RTL-correct layouts. All text starts from right.
Minimal, consistent, professional.
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFrame, QSizePolicy, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.styles.theme import (
    COLORS, FONT, CARD_RADIUS, BORDER_RADIUS,
    get_status_style, get_status_text,
    BTN_HEIGHT, INPUT_HEIGHT
)

RTL = Qt.LayoutDirection.RightToLeft
AlignLeft  = Qt.AlignmentFlag.AlignLeft  | Qt.AlignmentFlag.AlignVCenter
AlignLeft   = Qt.AlignmentFlag.AlignLeft   | Qt.AlignmentFlag.AlignVCenter
AlignCenter = Qt.AlignmentFlag.AlignCenter


# ══════════════════════════════════════════════════════
#  ScreenShell
# ══════════════════════════════════════════════════════

class ScreenShell(QWidget):
    """
    Base screen wrapper.
    Header: [Title + subtitle] ←stretch→ [Action buttons]
    In RTL: title appears on right, buttons on left.
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)
        self._build(title, subtitle)

    def _build(self, title: str, subtitle: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── Header bar
        self._header = QWidget()
        self._header.setObjectName("screen_header")
        self._header.setLayoutDirection(RTL)
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.setSpacing(12)

        # Title block (right side in RTL)
        title_block = QVBoxLayout()
        title_block.setSpacing(2)

        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("screen_title")
        self._title_lbl.setAlignment(AlignLeft)
        title_block.addWidget(self._title_lbl)

        if subtitle:
            self._sub_lbl = QLabel(subtitle)
            self._sub_lbl.setObjectName("screen_subtitle")
            self._sub_lbl.setAlignment(AlignLeft)
            title_block.addWidget(self._sub_lbl)

        hl.addLayout(title_block)
        hl.addStretch()

        # Actions (left side in RTL)
        self._actions = QHBoxLayout()
        self._actions.setSpacing(8)
        hl.addLayout(self._actions)

        root.addWidget(self._header)

        # ─── Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content_w = QWidget()
        self._content_w.setLayoutDirection(RTL)
        self._content_l = QVBoxLayout(self._content_w)
        self._content_l.setContentsMargins(24, 20, 24, 20)
        self._content_l.setSpacing(16)
        scroll.setWidget(self._content_w)

        root.addWidget(scroll)

    def add_action(self, widget: QWidget):
        self._actions.addWidget(widget)

    def content(self) -> QVBoxLayout:
        return self._content_l

    def set_subtitle(self, text: str):
        if hasattr(self, "_sub_lbl"):
            self._sub_lbl.setText(text)


# ══════════════════════════════════════════════════════
#  StatCard
# ══════════════════════════════════════════════════════

class StatCard(QWidget):
    """
    Compact stat card — centered layout.
    Accent bar on right edge (RTL leading).
    """

    def __init__(self, title: str, value: str = "—",
                 accent_color: str = None, icon: str = "", parent=None):
        super().__init__(parent)
        self._accent = accent_color or COLORS["accent"]
        self._build(title, value, icon)

    def _build(self, title: str, value: str, icon: str):
        self.setObjectName("stat_card")
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(RTL)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Accent bar — RIGHT in RTL (leading edge)
        self._bar = QFrame()
        self._bar.setFixedWidth(4)
        self._bar.setStyleSheet(
            f"background:{self._accent};"
            f"border-top-right-radius:{CARD_RADIUS};"
            f"border-bottom-right-radius:{CARD_RADIUS};"
        )
        outer.addWidget(self._bar)

        # Content
        inner = QVBoxLayout()
        inner.setContentsMargins(16, 18, 16, 18)
        inner.setSpacing(8)
        inner.setAlignment(AlignCenter)

        # Icon + title row
        if icon:
            top = QHBoxLayout()
            top.setSpacing(6)

            icon_lbl = QLabel(icon)
            icon_lbl.setFixedSize(28, 28)
            icon_lbl.setAlignment(AlignCenter)
            icon_lbl.setStyleSheet(
                f"background:{self._accent}20; border-radius:8px; font-size:14px;"
            )
            top.addWidget(icon_lbl)
            top.addStretch()

            title_lbl = QLabel(title)
            title_lbl.setObjectName("stat_label")
            title_lbl.setAlignment(AlignLeft)
            top.addWidget(title_lbl)

            inner.addLayout(top)
        else:
            title_lbl = QLabel(title)
            title_lbl.setObjectName("stat_label")
            title_lbl.setAlignment(AlignCenter)
            inner.addWidget(title_lbl)

        # Value
        self._value = QLabel(value)
        self._value.setObjectName("stat_value")
        self._value.setAlignment(AlignCenter)
        self._value.setStyleSheet(
            f"color:{self._accent}; font-size:{FONT['2xl']}; font-weight:bold;"
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
        self._value.setStyleSheet(
            f"color:{color}; font-size:{FONT['2xl']}; font-weight:bold;"
        )


# ══════════════════════════════════════════════════════
#  PlatformCard
# ══════════════════════════════════════════════════════

class PlatformCard(QWidget):
    deposit_clicked = pyqtSignal(int)

    def __init__(self, platform: dict, parent=None):
        super().__init__(parent)
        self.platform_id = platform["id"]
        self._build(platform)

    def _build(self, p: dict):
        self.setObjectName("card")
        self.setFixedWidth(220)
        self.setMinimumHeight(155)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(RTL)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        ptype = p.get("type", "machine")
        type_color, type_text = {
            "machine":  (COLORS["accent"],  "ماكينة"),
            "wallet":   (COLORS["purple"],  "محفظة"),
            "instapay": (COLORS["cyan"],    "انستا باي"),
        }.get(ptype, (COLORS["text_muted"], ptype))

        # ─ Header row
        hrow = QHBoxLayout()
        hrow.setSpacing(6)

        name = QLabel(p["name"])
        name.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['md']}; font-weight:bold;"
        )
        name.setAlignment(AlignLeft)
        hrow.addWidget(name)
        hrow.addStretch()

        badge = QLabel(f" {type_text} ")
        badge.setStyleSheet(
            f"color:{type_color}; background:{type_color}18;"
            f"border:1px solid {type_color}40; border-radius:5px;"
            f"font-size:{FONT['xs']}; font-weight:bold; padding:1px 4px;"
        )
        hrow.addWidget(badge)
        layout.addLayout(hrow)

        # ─ Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{COLORS['border']}; background:{COLORS['border']}; max-height:1px;")
        layout.addWidget(div)

        # ─ Balance
        bal = p.get("balance", 0)
        bal_color = COLORS["green"] if bal > 0 else COLORS["text_secondary"]
        bal_lbl = QLabel(f"{bal:,.0f} ج")
        bal_lbl.setStyleSheet(
            f"color:{bal_color}; font-size:{FONT['xl']}; font-weight:bold;"
        )
        bal_lbl.setAlignment(AlignLeft)
        layout.addWidget(bal_lbl)

        # ─ Limit (wallets + instapay)
        if ptype in ("wallet", "instapay"):
            used      = p.get("monthly_used", 0)
            limit     = p.get("monthly_limit", 200_000)
            remaining = max(0, limit - used)
            pct       = min(100, int(used / limit * 100)) if limit else 0
            lim_color = (COLORS["red"]    if pct >= 90 else
                         COLORS["yellow"] if pct >= 70 else
                         COLORS["text_muted"])
            lim_lbl = QLabel(f"متبقي {remaining:,.0f} / {limit:,.0f} ج")
            lim_lbl.setStyleSheet(
                f"color:{lim_color}; font-size:{FONT['xs']};"
            )
            lim_lbl.setAlignment(AlignLeft)
            layout.addWidget(lim_lbl)

        # ─ Deposit button
        dep = QPushButton("+ إيداع")
        dep.setObjectName("btn_ghost")
        dep.setFixedHeight(28)
        dep.setCursor(Qt.CursorShape.PointingHandCursor)
        dep.clicked.connect(lambda: self.deposit_clicked.emit(self.platform_id))
        layout.addWidget(dep)


# ══════════════════════════════════════════════════════
#  DataTable
# ══════════════════════════════════════════════════════

class DataTable(QTableWidget):

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self._init(columns)

    def _init(self, columns: list):
        self.setLayoutDirection(RTL)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels([c[0] for c in columns])

        for i, col in enumerate(columns):
            w = col[1] if len(col) > 1 else -1
            if w == -1:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.setColumnWidth(i, w)
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setLayoutDirection(RTL)
        self.setStyleSheet(
            f"alternate-background-color: {COLORS['bg_elevated']};"
        )
        self.verticalHeader().setDefaultSectionSize(48)

    def set_cell(self, row: int, col: int, text: str,
                 color: str = None, bold: bool = False, align=None):
        item = QTableWidgetItem(str(text) if text is not None else "—")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if color:
            item.setForeground(QColor(color))
        if bold:
            f = item.font()
            f.setBold(True)
            item.setFont(f)
        item.setTextAlignment(align if align else AlignCenter)
        self.setItem(row, col, item)

    def add_status_badge(self, row: int, col: int, status: str,
                         operation_type: str = "outbound", is_delivered: int = 0):
        """
        outbound → مؤجل / مسدد
        inbound  → لم يُسلَّم / تم التسليم
        """
        if operation_type == "inbound":
            if is_delivered:
                text, color = "تم التسليم ", COLORS["green"]
            else:
                text, color = "لم يُسلَّم ⏳", COLORS["yellow"]
        else:
            # outbound
            if status == "pending":
                text, color = "مؤجل ⏳", COLORS["yellow"]
            elif status == "paid":
                text, color = "مسدد ", COLORS["green"]
            else:
                text, color = status, COLORS["text_muted"]

        self.set_cell(row, col, text, color=color)

    def clear_rows(self):
        self.setRowCount(0)


# ══════════════════════════════════════════════════════
#  SectionTitle
# ══════════════════════════════════════════════════════

class SectionTitle(QWidget):

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(2)

        t = QLabel(title)
        t.setObjectName("label_title")
        t.setAlignment(AlignLeft)
        layout.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("label_subtitle")
            s.setAlignment(AlignLeft)
            layout.addWidget(s)


# ══════════════════════════════════════════════════════
#  GroupLabel  (section divider)
# ══════════════════════════════════════════════════════

class GroupLabel(QWidget):
    """RTL section divider: ● Title ─────────────"""

    def __init__(self, text: str, color: str = None, parent=None):
        super().__init__(parent)
        color = color or COLORS["accent"]
        self.setLayoutDirection(RTL)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 2)
        layout.setSpacing(8)

        dot = QFrame()
        dot.setFixedSize(7, 7)
        dot.setStyleSheet(
            f"background:{color}; border-radius:4px; border:none;"
        )
        layout.addWidget(dot)

        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{color}; font-size:{FONT['xs']}; font-weight:bold;"
            f"letter-spacing:0.8px; background:transparent;"
        )
        lbl.setAlignment(AlignLeft)
        layout.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(
            f"color:{COLORS['border']}; background:{COLORS['border']}; max-height:1px; border:none;"
        )
        layout.addWidget(line)


# ══════════════════════════════════════════════════════
#  InfoRow
# ══════════════════════════════════════════════════════

class InfoRow(QWidget):
    """Label: ─────── Value   (RTL: label right, value left)"""

    def __init__(self, label: str, value: str = "—",
                 value_color: str = None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(8)

        self._lbl = QLabel(label)
        self._lbl.setObjectName("label_muted")
        self._lbl.setAlignment(AlignLeft)
        layout.addWidget(self._lbl)

        layout.addStretch()

        self._val = QLabel(value)
        self._val.setObjectName("label_value")
        if value_color:
            self._val.setStyleSheet(
                f"color:{value_color}; font-size:{FONT['md']}; font-weight:bold;"
            )
        self._val.setAlignment(AlignLeft)
        layout.addWidget(self._val)

    def set_value(self, value: str, color: str = None):
        self._val.setText(value)
        if color:
            self._val.setStyleSheet(
                f"color:{color}; font-size:{FONT['md']}; font-weight:bold;"
            )


# ══════════════════════════════════════════════════════
#  PlatformsRow  (horizontal scroll of PlatformCards)
# ══════════════════════════════════════════════════════

class PlatformsRow(QWidget):
    deposit_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(180)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setLayoutDirection(RTL)

        self._inner = QWidget()
        self._inner.setLayoutDirection(RTL)
        self._layout = QHBoxLayout(self._inner)
        self._layout.setContentsMargins(0, 4, 0, 4)
        self._layout.setSpacing(12)
        self._layout.setAlignment(AlignLeft)

        scroll.setWidget(self._inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def load(self, platforms: list):
        # Clear
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not platforms:
            empty = QLabel("لا توجد منصات مضافة")
            empty.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:{FONT['md']};")
            empty.setAlignment(AlignCenter)
            self._layout.addWidget(empty)
            return

        for p in platforms:
            card = PlatformCard(p)
            card.deposit_clicked.connect(self.deposit_clicked.emit)
            self._layout.addWidget(card)

        self._layout.addStretch()


# ══════════════════════════════════════════════════════
#  Utilities
# ══════════════════════════════════════════════════════

def make_divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(
        f"color:{COLORS['border']}; background:{COLORS['border']}; max-height:1px; border:none;"
    )
    return line


def make_section_header(title: str, btn_text: str = None,
                        btn_callback=None) -> QWidget:
    """Section header row with optional action button."""
    w = QWidget()
    w.setLayoutDirection(RTL)
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 4, 0, 4)
    row.setSpacing(12)

    lbl = QLabel(title)
    lbl.setObjectName("label_title")
    lbl.setAlignment(AlignLeft)
    row.addWidget(lbl)
    row.addStretch()

    if btn_text and btn_callback:
        btn = QPushButton(btn_text)
        btn.setObjectName("btn_secondary")
        btn.setFixedHeight(34)
        btn.clicked.connect(btn_callback)
        row.addWidget(btn)

    return w
