"""
widgets.py — Reusable UI Components
مكونات الواجهة القابلة لإعادة الاستخدام
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFrame, QSizePolicy, QScrollArea,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor

from ui.styles.theme import COLORS, get_status_style, get_status_text


# ══════════════════════════════════════════
#  Screen Shell — غلاف الشاشة الموحد
# ══════════════════════════════════════════

class ScreenShell(QWidget):
    """
    غلاف موحد لكل الشاشات:
    - هيدر ثابت (عنوان + subtitle + actions)
    - منطقة محتوى قابلة للتمرير
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_shell(title, subtitle)

    def _build_shell(self, title: str, subtitle: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar
        self._header_bar = QWidget()
        self._header_bar.setObjectName("screen_header")
        self._header_bar.setFixedHeight(56)
        header_layout = QHBoxLayout(self._header_bar)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(8)

        # Action buttons slot (left side in RTL = right visually)
        self._actions_layout = QHBoxLayout()
        self._actions_layout.setSpacing(8)
        header_layout.addLayout(self._actions_layout)

        header_layout.addStretch()

        # Title + subtitle (right side in RTL = left visually)
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("screen_title")
        title_col.addWidget(self._title_lbl)

        if subtitle:
            self._sub_lbl = QLabel(subtitle)
            self._sub_lbl.setObjectName("screen_subtitle")
            title_col.addWidget(self._sub_lbl)

        header_layout.addLayout(title_col)
        root.addWidget(self._header_bar)

        # ── Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._content_widget = QWidget()
        self._content_widget.setObjectName("screen_content")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(24, 20, 24, 20)
        self._content_layout.setSpacing(16)

        scroll.setWidget(self._content_widget)
        root.addWidget(scroll)

    def add_action(self, widget: QWidget):
        """إضافة زرار أو widget لمنطقة الإجراءات في الهيدر"""
        self._actions_layout.addWidget(widget)

    def content(self) -> QVBoxLayout:
        """يرجع layout المحتوى لإضافة عناصر"""
        return self._content_layout

    def set_subtitle(self, text: str):
        if hasattr(self, '_sub_lbl'):
            self._sub_lbl.setText(text)


# ══════════════════════════════════════════
#  Stat Card
# ══════════════════════════════════════════

class StatCard(QWidget):
    """كارت إحصائية بتصميم محسّن"""

    def __init__(self, title: str, value: str = "—",
                 icon: str = "", accent_color: str = None, parent=None):
        super().__init__(parent)
        self.accent = accent_color or COLORS["blue_primary"]
        self._build_ui(title, value, icon)

    def _build_ui(self, title: str, value: str, icon: str):
        self.setObjectName("stat_card")
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        # Top row: title + icon
        top = QHBoxLayout()
        top.setSpacing(6)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("stat_label")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self.title_lbl)

        top.addStretch()

        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setObjectName("stat_icon")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            top.addWidget(icon_lbl)

        layout.addLayout(top)

        # Value
        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("stat_value")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.value_lbl.setStyleSheet(f"color: {self.accent}; font-size: 22px; font-weight: bold;")
        layout.addWidget(self.value_lbl)

        # Bottom accent line
        bar = QFrame()
        bar.setFixedHeight(2)
        bar.setStyleSheet(
            f"background: qlineargradient(x1:1, y1:0, x2:0, y2:0,"
            f"stop:0 {self.accent}, stop:1 transparent);"
            f"border-radius: 1px; border: none;"
        )
        layout.addWidget(bar)

    def set_value(self, value: str):
        self.value_lbl.setText(value)

    def set_accent(self, color: str):
        self.accent = color
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")


# ══════════════════════════════════════════
#  Platform Card
# ══════════════════════════════════════════

class PlatformCard(QWidget):
    """كارت منصة بتصميم محسّن"""
    deposit_clicked = pyqtSignal(int)

    def __init__(self, platform: dict, parent=None):
        super().__init__(parent)
        self.platform_id = platform["id"]
        self._build_ui(platform)

    def _build_ui(self, p: dict):
        self.setObjectName("card")
        self.setMinimumWidth(190)
        self.setMaximumWidth(240)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Type badge row
        is_machine = p["type"] == "machine"
        type_text  = "🏧 ماكينة" if is_machine else "💳 محفظة"
        type_color = COLORS["blue_bright"] if is_machine else COLORS["purple"]

        type_lbl = QLabel(type_text)
        type_lbl.setStyleSheet(
            f"color: {type_color}; font-size: 11px; font-weight: bold; "
            f"letter-spacing: 0.3px;"
        )
        type_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(type_lbl)

        # Name
        name_lbl = QLabel(p["name"])
        name_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: bold;"
        )
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(name_lbl)

        # Balance
        balance = p.get("balance", 0)
        bal_color = COLORS["green"] if balance > 0 else COLORS["text_muted"]
        balance_lbl = QLabel(f"{balance:,.2f} ج")
        balance_lbl.setStyleSheet(
            f"color: {bal_color}; font-size: 20px; font-weight: bold; letter-spacing: -0.5px;"
        )
        balance_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(balance_lbl)

        # Monthly limit bar (wallets only)
        if p["type"] == "wallet":
            used  = p.get("monthly_used", 0)
            limit = p.get("monthly_limit", 200000)
            pct   = min(100, int(used / limit * 100)) if limit else 0
            limit_color = COLORS["red"] if pct >= 90 else (
                COLORS["yellow"] if pct >= 70 else COLORS["text_muted"]
            )
            limit_lbl = QLabel(f"{pct}% من الحد الشهري")
            limit_lbl.setStyleSheet(f"color: {limit_color}; font-size: 11px;")
            limit_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(limit_lbl)

        # Deposit button
        dep_btn = QPushButton("+ إيداع")
        dep_btn.setObjectName("btn_ghost")
        dep_btn.setFixedHeight(28)
        dep_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_btn.clicked.connect(lambda: self.deposit_clicked.emit(self.platform_id))
        layout.addWidget(dep_btn)


# ══════════════════════════════════════════
#  Data Table
# ══════════════════════════════════════════

class DataTable(QTableWidget):
    """جدول بيانات موحد"""

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self._setup(columns)

    def _setup(self, columns: list):
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
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            f"alternate-background-color: {COLORS['bg_elevated']};"
        )

        self.horizontalHeader().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.verticalHeader().setDefaultSectionSize(40)

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
#  Section Header
# ══════════════════════════════════════════

class SectionTitle(QWidget):
    """عنوان قسم بسيط"""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
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
#  Info Row — صف معلومات بـ label + value
# ══════════════════════════════════════════

class InfoRow(QWidget):
    """صف label + value للحقول الثابتة"""

    def __init__(self, label: str, value: str = "—",
                 value_color: str = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("label_value")
        if value_color:
            val_lbl.setStyleSheet(f"color: {value_color}; font-size: 13px; font-weight: bold;")
        layout.addWidget(val_lbl)

        layout.addStretch()

        lbl = QLabel(label)
        lbl.setObjectName("label_muted")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)

        self.value_lbl = val_lbl

    def set_value(self, value: str, color: str = None):
        self.value_lbl.setText(value)
        if color:
            self.value_lbl.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")


# ══════════════════════════════════════════
#  Platforms Scroll Row
# ══════════════════════════════════════════

class PlatformsRow(QWidget):
    """صف أفقي قابل للتمرير لعرض كروت المنصات"""
    deposit_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(174)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._layout = QHBoxLayout(self._container)
        self._layout.setContentsMargins(0, 4, 0, 4)
        self._layout.setSpacing(12)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        scroll.setWidget(self._container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def load(self, platforms: list):
        # Clear existing
        for i in reversed(range(self._layout.count())):
            w = self._layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not platforms:
            empty = QLabel("لا توجد منصات مضافة")
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
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