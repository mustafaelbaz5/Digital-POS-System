"""
ui/components/table.py — DataTable
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
)

from ui.styles.theme import COLORS, GAP_MD, GAP_LG, ROW_HEIGHT

AlignCenter = Qt.AlignmentFlag.AlignCenter

_HEADER_BASE = """
    QHeaderView::section {{
        background-color: {bg};
        color: {fg};
        padding: 12px 14px;
        border: none;
        border-bottom: 2px solid {border};
        font-weight: bold;
        font-size: 13px;
        letter-spacing: 0;
    }}
"""


class DataTable(QTableWidget):
    """RTL table with action buttons, status badges, and column resizing."""

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self._init(columns)

    def _init(self, columns: list):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.horizontalHeader()
        header.setMinimumSectionSize(72)
        for i, col in enumerate(columns):
            label = col[0]
            w = col[1] if len(col) > 1 else -1
            if "إجراءات" in label:
                self.setColumnWidth(i, max(w, 140))
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            else:
                if w > 0:
                    self.setColumnWidth(i, w)
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.horizontalHeader().setStretchLastSection(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)

        self.horizontalHeader().setStyleSheet(
            _HEADER_BASE.format(
                bg=COLORS["bg_elevated"],
                fg=COLORS["text_primary"],
                border=COLORS["border"],
            )
        )

        self.setAlternatingRowColors(True)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                alternate-background-color: {COLORS['bg_alt_row']};
                border: none;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {COLORS['border_light']};
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item:hover {{
                background-color: {COLORS['bg_hover']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['accent_dim']};
                color: {COLORS['accent']};
            }}
        """)

    def set_section_color(self, color: str):
        """Apply a section-identity color to the header, preserving padding/style."""
        self.horizontalHeader().setStyleSheet(
            _HEADER_BASE.format(
                bg=color,
                fg=COLORS["text_on_dark"],
                border="rgba(0,0,0,0.18)",
            )
        )

    def set_cell(
        self,
        row: int,
        col: int,
        text: str,
        color: str = None,
        bold: bool = False,
        align=None,
        bg_color: str = None,
    ):
        item = QTableWidgetItem(str(text) if text is not None else "—")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if color:
            item.setForeground(QColor(color))
        if bg_color:
            item.setBackground(QColor(bg_color))
        if bold:
            f = item.font()
            f.setBold(True)
            item.setFont(f)
        item.setTextAlignment(align if align else AlignCenter)
        self.setItem(row, col, item)

    def add_action_button(self, row: int, col: int, text: str, callback, role="ghost"):
        return self.add_action_buttons(
            row, col, [{"text": text, "callback": callback, "role": role}]
        )[0]

    def add_action_buttons(self, row, col, buttons_data, spacing=GAP_MD):
        wrapper = QFrame()
        wrapper.setObjectName("cell_wrapper")
        wrapper.setStyleSheet(
            "#cell_wrapper { background: transparent; border: none; }"
        )
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(spacing)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btns = []
        for data in buttons_data:
            btn = QPushButton(data.get("text", ""))
            btn.setObjectName(f"btn_{data.get('role', 'ghost')}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(30)
            btn.setMinimumWidth(74)
            btn.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
            )
            if "callback" in data:
                btn.clicked.connect(data["callback"])
            layout.addWidget(btn)
            btns.append(btn)

        self.setCellWidget(row, col, wrapper)
        return btns

    def add_status_badge(
        self,
        row: int,
        col: int,
        status: str,
        operation_type: str = "outbound",
        is_delivered: int = 0,
    ):
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
