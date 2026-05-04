"""
ui/components/base.py — ScreenShell & BaseDialog
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.styles.theme import GAP_LG, GAP_MD, GAP_SM, GAP_XS, MARGIN_CARD, MARGIN_CONTENT

RTL = Qt.LayoutDirection.RightToLeft
AlignLeft = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


class BaseDialog(QDialog):
    """Header-Body-Footer dialog: draggable, frameless, RTL."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self._build(title)

    def _build(self, title: str):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(1, 1, 1, 1)
        self.root.setSpacing(0)

        # ─── Header
        header = QFrame()
        header.setObjectName("dialog_header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(GAP_MD, GAP_MD, GAP_MD, GAP_MD)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("dialog_title")
        hl.addWidget(title_lbl)
        hl.addStretch()

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
                self._drag_pos = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_is_dragging", False):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, "_is_dragging", False):
            self._is_dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Re-map Enter/Return to Tab for focus switching."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextChild()
            event.accept()
        else:
            super().keyPressEvent(event)


class ScreenShell(QWidget):
    """Screen container: sticky header/filters area + scrollable content."""

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

        # Sticky area (fixed between header and scroll content)
        self._sticky_w = QWidget()
        self._sticky_l = QVBoxLayout(self._sticky_w)
        self._sticky_l.setContentsMargins(MARGIN_CONTENT, 0, MARGIN_CONTENT, 0)
        self._sticky_l.setSpacing(0)
        root.addWidget(self._sticky_w)

        # ─── Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content_w = QWidget()
        self._content_l = QVBoxLayout(self._content_w)
        self._content_l.setContentsMargins(
            MARGIN_CONTENT, GAP_LG, MARGIN_CONTENT, MARGIN_CONTENT
        )
        self._content_l.setSpacing(GAP_LG)
        scroll.setWidget(self._content_w)

        root.addWidget(scroll)

    def add_action(self, widget: QWidget):
        self._actions.addWidget(widget)

    def content(self) -> QVBoxLayout:
        return self._content_l

    def sticky(self) -> QVBoxLayout:
        return self._sticky_l

    def set_subtitle(self, text: str):
        if hasattr(self, "_sub_lbl"):
            self._sub_lbl.setText(text)
