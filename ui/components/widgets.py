"""
widgets.py — RTL-Corrected Components v2.1
==========================================
All layouts corrected for Arabic RTL direction:
- StatCard: accent bar on RIGHT (leading edge in RTL)
- ScreenShell: title on right, actions on left
- GroupLabel: dot on LEFT of text (trailing in RTL)
- PlatformCard: name right, badge left
- InfoRow: label right, value left
- All alignments and stretch positions corrected
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFrame, QSizePolicy, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor

from ui.styles.theme import COLORS, FONT, CARD_RADIUS, BORDER_RADIUS, get_status_style, get_status_text


# ══════════════════════════════════════════
#  Screen Shell
# ══════════════════════════════════════════

class ScreenShell(QWidget):
    """
    Unified screen wrapper with RTL-correct header:
    - Right: Title + subtitle
    - Left:  Action buttons
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_shell(title, subtitle)

    def _build_shell(self, title: str, subtitle: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header
        self._header_bar = QWidget()
        self._header_bar.setObjectName("screen_header")
        self._header_bar.setFixedHeight(60)
        header_layout = QHBoxLayout(self._header_bar)
        header_layout.setContentsMargins(28, 0, 28, 0)
        header_layout.setSpacing(10)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # RIGHT side: Title + subtitle (Arabic → right is the natural start)
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("screen_title")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_col.addWidget(self._title_lbl)

        if subtitle:
            self._sub_lbl = QLabel(subtitle)
            self._sub_lbl.setObjectName("screen_subtitle")
            self._sub_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            title_col.addWidget(self._sub_lbl)

        header_layout.addLayout(title_col)

        # STRETCH pushes actions to the left
        header_layout.addStretch()

        # LEFT side: Action buttons (in RTL, addWidget adds right-to-left,
        # so we use a sub-layout and reverse order naturally)
        self._actions_layout = QHBoxLayout()
        self._actions_layout.setSpacing(8)
        self._actions_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        header_layout.addLayout(self._actions_layout)

        root.addWidget(self._header_bar)

        # ── Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._content_widget = QWidget()
        self._content_widget.setObjectName("screen_content")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(28, 24, 28, 24)
        self._content_layout.setSpacing(20)

        scroll.setWidget(self._content_widget)
        root.addWidget(scroll)

    def add_action(self, widget: QWidget):
        self._actions_layout.addWidget(widget)

    def content(self) -> QVBoxLayout:
        return self._content_layout

    def set_subtitle(self, text: str):
        if hasattr(self, '_sub_lbl'):
            self._sub_lbl.setText(text)


# ══════════════════════════════════════════
#  Stat Card — RTL Corrected
# ══════════════════════════════════════════

class StatCard(QWidget):
    """
    RTL layout:
    - Accent bar on the RIGHT (the reading-start edge in Arabic)
    - Icon badge top-LEFT (trailing edge)
    - Label top-right, value bottom-right
    """

    def __init__(self, title: str, value: str = "—",
                 accent_color: str = None, parent=None):
        super().__init__(parent)
        self.accent = accent_color or COLORS["teal_primary"]
        self._build_ui(title, value)

    def _build_ui(self, title: str, value: str):
        self.setObjectName("stat_card")
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Accent bar
        accent_bar = QFrame()
        accent_bar.setFixedWidth(5)
        accent_bar.setStyleSheet(
            f"background-color: {self.accent}; border-top-right-radius: 12px; border-bottom-right-radius: 12px;"
        )
        outer.addWidget(accent_bar)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 24, 20, 24)
        content_layout.setSpacing(12)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("stat_label")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.title_lbl)

        # Value
        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("stat_value")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setStyleSheet(
            f"color: {self.accent}; font-size: {FONT['3xl']}; font-weight: bold;"
            f"font-family: {FONT['family']};"
        )
        content_layout.addWidget(self.value_lbl)

        outer.addWidget(content)
        self._accent_bar = accent_bar

    def set_value(self, value: str):
        self.value_lbl.setText(value)

    def set_accent(self, color: str):
        self.accent = color
        self.value_lbl.setStyleSheet(
            f"color: {color}; font-size: {FONT['3xl']}; font-weight: bold;"
            f"font-family: {FONT['family']};"
        )
        self._accent_bar.setStyleSheet(
            f"background-color: {color}; border-top-right-radius: 12px;"
            f"border-bottom-right-radius: 12px;"
        )


# ══════════════════════════════════════════
#  Platform Card — RTL Corrected
# ══════════════════════════════════════════

class PlatformCard(QWidget):
    deposit_clicked = pyqtSignal(int)

    def __init__(self, platform: dict, parent=None):
        super().__init__(parent)
        self.platform_id = platform["id"]
        self._build_ui(platform)

    def _build_ui(self, p: dict):
        self.setObjectName("card")
        self.setMinimumWidth(200)
        self.setMaximumWidth(250)
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        is_machine = p["type"] == "machine"
        type_color = COLORS["blue"] if is_machine else COLORS["purple"]
        type_text  = "ماكينة" if is_machine else "محفظة"

        # Header: name RIGHT, badge LEFT
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

        layout.addLayout(header)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(div)

        # Balance — right aligned
        balance = p.get("balance", 0)
        bal_color = COLORS["green"] if balance > 0 else COLORS["text_muted"]
        balance_lbl = QLabel(f"{balance:,.2f} ج")
        balance_lbl.setStyleSheet(
            f"color: {bal_color}; font-size: {FONT['2xl']};"
            f"font-weight: bold; font-family: {FONT['family']};"
        )
        balance_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(balance_lbl)

        # Wallet monthly limit
        if p["type"] == "wallet":
            used      = p.get("monthly_used", 0)
            limit     = p.get("monthly_limit", 200000)
            remaining = limit - used
            pct       = min(100, int(used / limit * 100)) if limit else 0
            limit_color = (COLORS["red"] if pct >= 90 else
                           COLORS["yellow"] if pct >= 70 else COLORS["text_muted"])
            limit_lbl = QLabel(f"متبقي: {remaining:,.0f} / {limit:,.0f} ج")
            limit_lbl.setStyleSheet(
                f"color: {limit_color}; font-size: {FONT['xs']};"
                f"font-family: {FONT['family']};"
            )
            limit_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(limit_lbl)

        # Deposit button — full width
        dep_btn = QPushButton("إيداع +")
        dep_btn.setObjectName("btn_ghost")
        dep_btn.setFixedHeight(28)
        dep_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_btn.clicked.connect(lambda: self.deposit_clicked.emit(self.platform_id))
        layout.addWidget(dep_btn)


# ══════════════════════════════════════════
#  Data Table — RTL Corrected
# ══════════════════════════════════════════

class DataTable(QTableWidget):

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self._setup(columns)

    def _setup(self, columns: list):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels([c[0] for c in columns])

        for i, col in enumerate(columns):
            width = col[1] if len(col) > 1 else -1
            if width == -1:
                self.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.Stretch)
            else:
                self.setColumnWidth(i, width)
                self.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.Fixed)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(
            f"alternate-background-color: {COLORS['bg_elevated']};"
        )
        self.verticalHeader().setDefaultSectionSize(46)

    def set_cell(self, row: int, col: int, text: str,
                 color: str = None, bold: bool = False, align=None):
        item = QTableWidgetItem(str(text) if text is not None else "—")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if color:
            item.setForeground(QColor(color))
        if bold:
            f = item.font(); f.setBold(True); item.setFont(f)
        item.setTextAlignment(
            align if align else
            (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        )
        self.setItem(row, col, item)

    def add_status_badge(self, row: int, col: int, status: str):
        text = get_status_text(status)
        color_map = {
            "cash":    COLORS["green"],
            "pending": COLORS["yellow"],
            "paid":    COLORS["text_muted"],
        }
        self.set_cell(row, col, text, color=color_map.get(status, COLORS["text_secondary"]))

    def clear_rows(self):
        self.setRowCount(0)


# ══════════════════════════════════════════
#  Section Title
# ══════════════════════════════════════════

class SectionTitle(QWidget):

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 2)
        layout.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("label_title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setObjectName("label_subtitle")
            sub_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(sub_lbl)


# ══════════════════════════════════════════
#  Group Label — RTL Corrected
#  Layout: [text] [dot•]  — right to left
# ══════════════════════════════════════════

class GroupLabel(QWidget):
    """Section separator. RTL: dot on right of text (leading indicator)."""

    def __init__(self, text: str, color: str = None, parent=None):
        super().__init__(parent)
        color = color or COLORS["teal_primary"]
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 4)
        layout.setSpacing(8)

        # Dot — rightmost (leading in RTL)
        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        layout.addWidget(dot)

        # Label text — right after dot
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color}; font-size: {FONT['sm']}; font-weight: bold;"
            f"font-family: {FONT['family']}; letter-spacing: 0.5px;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)

        # Separator line to the left
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(line)


# ══════════════════════════════════════════
#  Info Row — RTL Corrected
#  [value (left)] [stretch] [label (right)]
# ══════════════════════════════════════════

class InfoRow(QWidget):

    def __init__(self, label: str, value: str = "—",
                 value_color: str = None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        # Label on right (natural reading position)
        lbl = QLabel(label)
        lbl.setObjectName("label_muted")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)

        layout.addStretch()

        # Value on left (number/result on trailing side)
        val_lbl = QLabel(value)
        val_lbl.setObjectName("label_value")
        if value_color:
            val_lbl.setStyleSheet(
                f"color: {value_color}; font-size: {FONT['md']};"
                f"font-weight: bold; font-family: {FONT['family']};"
            )
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(val_lbl)

        self.value_lbl = val_lbl

    def set_value(self, value: str, color: str = None):
        self.value_lbl.setText(value)
        if color:
            self.value_lbl.setStyleSheet(
                f"color: {color}; font-size: {FONT['md']};"
                f"font-weight: bold; font-family: {FONT['family']};"
            )


# ══════════════════════════════════════════
#  Platforms Scroll Row — RTL Corrected
# ══════════════════════════════════════════

class PlatformsRow(QWidget):
    deposit_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(186)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._container = QWidget()
        self._container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._layout = QHBoxLayout(self._container)
        self._layout.setContentsMargins(0, 4, 0, 4)
        self._layout.setSpacing(14)
        # Cards start from the right in RTL
        self._layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        scroll.setWidget(self._container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def load(self, platforms: list):
        for i in reversed(range(self._layout.count())):
            w = self._layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not platforms:
            empty = QLabel("لا توجد منصات مضافة")
            empty.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: {FONT['md']};"
                f"font-family: {FONT['family']};"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(empty)
            return

        for p in platforms:
            card = PlatformCard(p)
            card.deposit_clicked.connect(self.deposit_clicked.emit)
            self._layout.addWidget(card)

        self._layout.addStretch()


# ══════════════════════════════════════════
#  Divider
# ══════════════════════════════════════════

def make_divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    return line
