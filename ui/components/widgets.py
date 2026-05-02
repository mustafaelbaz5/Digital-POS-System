"""
widgets.py — Component Library v4 (Pro Dark Edition)
===================================================
Unified, professional components with modern emerald accents.
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFrame, QSizePolicy, QScrollArea,
    QDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor

from ui.styles.theme import (
    COLORS, FONT, CARD_RADIUS, BORDER_RADIUS,
    get_status_style, get_status_text,
    BTN_HEIGHT, INPUT_HEIGHT, ROW_HEIGHT,
    GAP_XS, GAP_SM, GAP_MD, GAP_LG, GAP_XL,
    MARGIN_CONTENT, MARGIN_CARD
)

RTL = Qt.LayoutDirection.RightToLeft
AlignLeft  = Qt.AlignmentFlag.AlignLeft  | Qt.AlignmentFlag.AlignVCenter
AlignCenter = Qt.AlignmentFlag.AlignCenter


# ══════════════════════════════════════════════════════
#  BaseDialog
# ══════════════════════════════════════════════════════

class BaseDialog(QDialog):
    """
    A professional base dialog with Header-Body-Footer structure.
    Ensures consistent spacing and visibility in dark mode.
    """
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self._build(title)

    def _build(self, title: str):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(1, 1, 1, 1) # Space for border
        self.root.setSpacing(0)

        # ─── Header
        header = QFrame()
        header.setObjectName("dialog_header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(GAP_MD, 0, GAP_MD, 0)
        
        title_lbl = QLabel(title)
        title_lbl.setObjectName("dialog_title")
        hl.addWidget(title_lbl)
        hl.addStretch()

        # Close button (top right in RTL)
        close_btn = QPushButton("✕")
        close_btn.setObjectName("dialog_close_btn")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        hl.addWidget(close_btn)

        self.root.addWidget(header)

        # ─── Body
        self.body_w = QWidget()
        self.body = QVBoxLayout(self.body_w)
        self.body.setContentsMargins(MARGIN_CARD, MARGIN_CARD, MARGIN_CARD, MARGIN_CARD)
        self.body.setSpacing(GAP_MD)
        self.root.addWidget(self.body_w, 1)

        # ─── Footer
        self.footer_w = QWidget()
        self.footer = QHBoxLayout(self.footer_w)
        self.footer.setContentsMargins(MARGIN_CARD, 0, MARGIN_CARD, MARGIN_CARD)
        self.footer.setSpacing(GAP_SM)
        self.root.addWidget(self.footer_w)

    def add_button(self, text: str, callback, role="primary") -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName(f"btn_{role}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        self.footer.addWidget(btn)
        return btn

    def add_stretch(self):
        self.footer.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            header = self.findChild(QFrame, "dialog_header")
            if header and header.geometry().contains(event.pos()):
                self._is_dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_is_dragging', False):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_is_dragging', False):
            self._is_dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


# ══════════════════════════════════════════════════════
#  ScreenShell
# ══════════════════════════════════════════════════════

class ScreenShell(QWidget):
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
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(MARGIN_CONTENT, 0, MARGIN_CONTENT, 0)
        hl.setSpacing(GAP_MD)

        title_block = QVBoxLayout()
        title_block.setSpacing(GAP_XS)

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

        self._actions = QHBoxLayout()
        self._actions.setSpacing(GAP_MD)
        hl.addLayout(self._actions)

        root.addWidget(self._header)

        # ─── Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content_w = QWidget()
        self._content_l = QVBoxLayout(self._content_w)
        self._content_l.setContentsMargins(MARGIN_CONTENT, GAP_LG, MARGIN_CONTENT, MARGIN_CONTENT)
        self._content_l.setSpacing(GAP_LG)
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
#  CardGroup
# ══════════════════════════════════════════════════════

class CardGroup(QFrame):
    """
    A container that groups items inside a styled card.
    Useful for separating logical sections of a screen.
    """
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(RTL)
        
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(MARGIN_CARD, MARGIN_CARD, MARGIN_CARD, MARGIN_CARD)
        self._layout.setSpacing(GAP_MD)
        
        if title:
            header = SectionTitle(title)
            self._layout.addWidget(header)
            self._layout.addWidget(make_divider())
            self._layout.addSpacing(GAP_XS)

    def add_widget(self, widget: QWidget):
        self._layout.addWidget(widget)
    
    def add_layout(self, layout: QVBoxLayout | QHBoxLayout):
        self._layout.addLayout(layout)

    def layout(self) -> QVBoxLayout:
        return self._layout


# ══════════════════════════════════════════════════════
#  StatCard
# ══════════════════════════════════════════════════════

class StatCard(QWidget):
    def __init__(self, title: str, value: str = "—",
                 accent_color: str = None, icon: str = "", parent=None):
        super().__init__(parent)
        self._accent = accent_color or COLORS["accent"]
        self._build(title, value, icon)

    def _build(self, title: str, value: str, icon: str):
        self.setObjectName("stat_card")
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(RTL)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Accent bar
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

        # Title
        title_lbl = QLabel(title)
        title_lbl.setObjectName("stat_label")
        title_lbl.setAlignment(AlignLeft)
        inner.addWidget(title_lbl)

        # Value
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
        self.setFixedWidth(240)
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(RTL)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(MARGIN_CARD, MARGIN_CARD, MARGIN_CARD, MARGIN_CARD)
        layout.setSpacing(GAP_MD)

        ptype = p.get("type", "machine")
        type_color, type_text = {
            "machine":  (COLORS["blue"],    "ماكينة"),
            "wallet":   (COLORS["purple"],  "محفظة"),
            "instapay": (COLORS["cyan"],    "انستا باي"),
        }.get(ptype, (COLORS["text_muted"], ptype))

        # ─ Header row
        hrow = QHBoxLayout()
        hrow.setSpacing(GAP_SM)

        name = QLabel(p["name"])
        name.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['md']}; font-weight:bold;"
        )
        name.setAlignment(AlignLeft)
        hrow.addWidget(name)
        hrow.addStretch()

        badge = QLabel(f" {type_text} ")
        badge.setStyleSheet(
            f"color:{type_color}; background:{type_color}20;"
            f"border-radius:5px; font-size:{FONT['xs']}; font-weight:bold; padding:2px 6px;"
        )
        hrow.addWidget(badge)
        layout.addLayout(hrow)

        layout.addSpacing(GAP_XS)

        # ─ Balance
        bal = p.get("balance", 0)
        bal_lbl = QLabel(f"{bal:,.0f} ج")
        bal_lbl.setStyleSheet(
            f"color:{COLORS['accent']}; font-size:{FONT['xl']}; font-weight:bold;"
        )
        bal_lbl.setAlignment(AlignLeft)
        layout.addWidget(bal_lbl)

        layout.addStretch()

        # ─ Deposit button
        dep = QPushButton("+ إيداع جديد")
        dep.setObjectName("btn_ghost")
        dep.setFixedHeight(32)
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

        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)

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

    def add_action_button(self, row: int, col: int, text: str, callback, role="ghost"):
        """
        Singular convenience method for add_action_buttons.
        """
        return self.add_action_buttons(row, col, [{'text': text, 'callback': callback, 'role': role}])[0]

    def add_action_buttons(self, row: int, col: int, buttons_data: list):
        """
        Adds multiple buttons to a table cell.
        buttons_data: list of dicts like {'text': '...', 'callback': ..., 'role': 'ghost'}
        """
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(GAP_SM)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btns = []
        for data in buttons_data:
            btn = QPushButton(data.get('text', ''))
            btn.setObjectName(f"btn_{data.get('role', 'ghost')}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(34)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btn.setStyleSheet(f"padding: 0 8px;") # Tighter padding to show all text
            if 'callback' in data:
                btn.clicked.connect(data['callback'])
            layout.addWidget(btn)
            btns.append(btn)
        
        self.setCellWidget(row, col, wrapper)
        return btns

    def add_status_badge(self, row: int, col: int, status: str,
                         operation_type: str = "outbound", is_delivered: int = 0):
        if operation_type == "inbound":
            if is_delivered:
                text, color = "تم التسليم ", COLORS["green"]
            else:
                text, color = "لم يُسلَّم ⏳", COLORS["yellow"]
        else:
            if status == "pending":
                text, color = "مؤجل ⏳", COLORS["yellow"]
            elif status == "paid":
                text, color = "مسدد ", COLORS["green"]
            else:
                text, color = status, COLORS["text_muted"]

        self.set_cell(row, col, text, color=color, bold=True)

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
        layout.setContentsMargins(0, GAP_XS, 0, GAP_XS)
        layout.setSpacing(GAP_XS)

        t = QLabel(title)
        t.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;")
        t.setAlignment(AlignLeft)
        layout.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:{FONT['sm']};")
            s.setAlignment(AlignLeft)
            layout.addWidget(s)


# ══════════════════════════════════════════════════════
#  GroupLabel
# ══════════════════════════════════════════════════════

class GroupLabel(QWidget):
    def __init__(self, text: str, color: str = None, parent=None):
        super().__init__(parent)
        color = color or COLORS["accent"]
        self.setLayoutDirection(RTL)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, GAP_MD, 0, GAP_XS)
        layout.setSpacing(GAP_SM + 2)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background:{color}; border-radius:4px;")
        layout.addWidget(dot)

        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{color}; font-size:{FONT['xs']}; font-weight:bold; text-transform:uppercase;")
        lbl.setAlignment(AlignLeft)
        layout.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background:{COLORS['border']}; max-height:1px; border:none;")
        layout.addWidget(line)


# ══════════════════════════════════════════════════════
#  InfoRow
# ══════════════════════════════════════════════════════

class InfoRow(QWidget):
    def __init__(self, label: str, value: str = "—",
                 value_color: str = None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, GAP_SM, 0, GAP_SM)
        layout.setSpacing(GAP_MD)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"color:{COLORS['text_secondary']};")
        self._lbl.setAlignment(AlignLeft)
        layout.addWidget(self._lbl)

        layout.addStretch()

        self._val = QLabel(value)
        v_style = f"color:{value_color or COLORS['text_primary']}; font-weight:bold;"
        self._val.setStyleSheet(v_style)
        self._val.setAlignment(AlignLeft)
        layout.addWidget(self._val)

    def set_value(self, value: str, color: str = None):
        self._val.setText(value)
        if color:
            self._val.setStyleSheet(f"color:{color}; font-weight:bold;")


# ══════════════════════════════════════════════════════
#  Utilities
# ══════════════════════════════════════════════════════

def make_divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background:{COLORS['border']}; max-height:1px; border:none;")
    return line


def make_section_header(title: str, btn_text: str = None,
                        btn_callback=None) -> QWidget:
    w = QWidget()
    w.setLayoutDirection(RTL)
    row = QHBoxLayout(w)
    row.setContentsMargins(0, GAP_SM, 0, GAP_SM)
    row.setSpacing(GAP_MD)

    lbl = QLabel(title)
    lbl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;")
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
