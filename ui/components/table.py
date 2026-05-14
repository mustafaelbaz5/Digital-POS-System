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

from ui.styles.theme import COLORS, GAP_LG

AlignCenter = Qt.AlignmentFlag.AlignCenter


class DataTable(QTableWidget):
    """RTL table with action buttons, status badges, and column resizing."""

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self._init(columns)

    def _init(self, columns: list):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels([c[0] for c in columns])

        for i, col in enumerate(columns):
            w = col[1] if len(col) > 1 else -1
            if w == -1:
                self.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.Stretch
                )
            else:
                self.setColumnWidth(i, w)
                self.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.Interactive
                )

        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setDefaultSectionSize(70)

        self.horizontalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                padding: 14px 16px;
                border: none;
                border-bottom: 2px solid {COLORS['border']};
                font-weight: bold;
                font-size: 12px;
            }}
        """)

        self.setAlternatingRowColors(True)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                alternate-background-color: {COLORS['bg_alt_row']};
                border: none;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 12px 16px;
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
        """Convenience wrapper around add_action_buttons for a single button."""
        return self.add_action_buttons(
            row, col, [{"text": text, "callback": callback, "role": role}]
        )[0]

    def add_action_buttons(self, row, col, buttons_data, spacing=GAP_LG):
        """Add action buttons to a cell with configurable spacing."""
        wrapper = QFrame()
        wrapper.setObjectName("cell_wrapper")
        wrapper.setStyleSheet(
            "#cell_wrapper { background: transparent; border: none; }"
        )
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(spacing)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        btns = []
        for data in buttons_data:
            btn = QPushButton(data.get("text", ""))
            btn.setObjectName(f"btn_{data.get('role', 'ghost')}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(22)
            btn.setMinimumWidth(120)
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
