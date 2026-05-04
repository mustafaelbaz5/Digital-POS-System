"""
ui/components/date_widgets.py — DateRangeWidget + calendar helpers
الويدجت التقويمي لاختيار نطاق التواريخ (canonical, replaces date_range_widget.py)
"""

from PyQt6.QtCore import QDate, QLocale, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.styles.theme import COLORS


# ─── Module-level helpers ──────────────────────────────────────────────────────


def _arrow_btn(text: str) -> QPushButton:
    """زرار سهم صغير للتنقل بين التواريخ."""
    btn = QPushButton(text)
    btn.setFixedSize(32, 32)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            # background: transparent; border: none;
            color: {COLORS['text_secondary']};
            font-size: 16px; font-weight: bold; border-radius: 6px;
        }}
        QPushButton:hover {{
            background: {COLORS['bg_hover']};
            color: {COLORS['accent']};
        }}
    """)
    return btn


def _open_calendar_dialog(parent, current_date: QDate) -> QDate | None:
    """يفتح ديالوج التقويم ويرجع التاريخ المختار أو None."""
    dialog = QDialog(parent.window() if parent else None)
    dialog.setWindowTitle("اختر التاريخ")
    dialog.setFixedSize(320, 420)
    dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    dialog.setStyleSheet(f"""
        QDialog {{ background: {COLORS['bg_elevated']}; }}
        QCalendarWidget QAbstractItemView {{
            background: {COLORS['bg_dark']};
            color: {COLORS['text_primary']};
            selection-background-color: {COLORS['accent']};
            selection-color: white;
            border: 1px solid {COLORS['border_light']};
            border-radius: 8px;
        }}
    """)

    cal = QCalendarWidget()
    cal.setSelectedDate(current_date)
    cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
    cal.setGridVisible(False)
    cal.setNavigationBarVisible(False)

    nav_style = f"""
        QPushButton {{
            background: {COLORS['bg_elevated']}; border: 1px solid {COLORS['border_light']};
            color: {COLORS['text_primary']}; font-size: 16px; font-weight: bold;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background: {COLORS['bg_hover']}; border-color: {COLORS['accent']};
            color: {COLORS['accent']};
        }}
    """
    lbl_style = (
        f"color:{COLORS['text_primary']};font-size:14px;"
        f"font-weight:bold;background:transparent;"
    )

    # Year nav
    year_lbl = QLabel()
    year_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    year_lbl.setStyleSheet(lbl_style)

    btn_yp = QPushButton("‹")
    btn_yn = QPushButton("›")
    for b in (btn_yp, btn_yn):
        b.setFixedSize(36, 32)
        b.setStyleSheet(nav_style)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_yp.clicked.connect(lambda: cal.setSelectedDate(cal.selectedDate().addYears(-1)))
    btn_yn.clicked.connect(lambda: cal.setSelectedDate(cal.selectedDate().addYears(1)))

    year_row = QHBoxLayout()
    year_row.addWidget(btn_yp)
    year_row.addWidget(year_lbl, 1)
    year_row.addWidget(btn_yn)

    # Month nav
    month_lbl = QLabel()
    month_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    month_lbl.setStyleSheet(lbl_style)

    btn_mp = QPushButton("‹")
    btn_mn = QPushButton("›")
    for b in (btn_mp, btn_mn):
        b.setFixedSize(36, 32)
        b.setStyleSheet(nav_style)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_mp.clicked.connect(
        lambda: cal.setSelectedDate(cal.selectedDate().addMonths(-1))
    )
    btn_mn.clicked.connect(lambda: cal.setSelectedDate(cal.selectedDate().addMonths(1)))

    month_row = QHBoxLayout()
    month_row.addWidget(btn_mp)
    month_row.addWidget(month_lbl, 1)
    month_row.addWidget(btn_mn)

    def _sync():
        year_lbl.setText(str(cal.selectedDate().year()))
        month_lbl.setText(QLocale().monthName(cal.selectedDate().month()))

    cal.selectionChanged.connect(_sync)
    _sync()

    confirm = QPushButton("تأكيد ✓")
    confirm.setObjectName("btn_primary")
    confirm.setFixedHeight(40)
    confirm.clicked.connect(dialog.accept)

    dl = QVBoxLayout(dialog)
    dl.setContentsMargins(20, 20, 20, 20)
    dl.setSpacing(12)
    dl.addLayout(year_row)
    dl.addLayout(month_row)
    dl.addWidget(cal)
    dl.addSpacing(4)
    dl.addWidget(confirm)

    if dialog.exec():
        return cal.selectedDate()
    return None


# ══════════════════════════════════════════
#  _SingleDateCell — خلية تاريخ واحد
# ══════════════════════════════════════════


class _SingleDateCell(QFrame):
    """خلية تاريخ واحدة مع أسهم للتنقل + ضغط لفتح تقويم."""

    changed = pyqtSignal()

    def __init__(self, date: QDate, label: str, parent=None):
        super().__init__(parent)
        self._date = date
        self._label = label
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_elevated']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
            }}
        """)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(0)

        self._btn_prev = _arrow_btn("‹")
        self._btn_prev.clicked.connect(self._go_prev)
        layout.addWidget(self._btn_prev)

        self._lbl = QLabel()
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lbl.setToolTip("اضغط لفتح التقويم")
        self._lbl.setStyleSheet(
            f"color:{COLORS['text_primary']};font-size:13px;"
            f"font-weight:bold;background:transparent;border:none;padding:0 6px;"
        )
        self._lbl.mousePressEvent = lambda e: self._open_cal()
        layout.addWidget(self._lbl, 1)

        self._btn_next = _arrow_btn("›")
        self._btn_next.clicked.connect(self._go_next)
        layout.addWidget(self._btn_next)

        self._update_label()

    def _update_label(self):
        today = QDate.currentDate()
        if self._date == today:
            date_str = "اليوم"
        elif self._date == today.addDays(-1):
            date_str = "أمس"
        else:
            date_str = self._date.toString("dd/MM/yyyy")
        self._lbl.setText(f"{self._label}: {date_str}")
        self._btn_next.setEnabled(self._date < today)

    def _go_prev(self):
        self._date = self._date.addDays(-1)
        self._update_label()
        self.changed.emit()

    def _go_next(self):
        if self._date < QDate.currentDate():
            self._date = self._date.addDays(1)
            self._update_label()
            self.changed.emit()

    def _open_cal(self):
        chosen = _open_calendar_dialog(self, self._date)
        if chosen:
            self._date = chosen
            self._update_label()
            self.changed.emit()

    def date(self) -> QDate:
        return self._date

    def setDate(self, d: QDate):
        self._date = d
        self._update_label()


# ══════════════════════════════════════════
#  SingleDateWidget — تاريخ واحد
# ══════════════════════════════════════════


class SingleDateWidget(QFrame):
    """Widget لاختيار يوم واحد مع أسهم تنقل وزر تقويم."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date = QDate.currentDate()
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_elevated']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
            }}
        """)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(0)

        self._btn_prev = _arrow_btn("‹")
        self._btn_prev.clicked.connect(self._go_prev)
        layout.addWidget(self._btn_prev)

        self._lbl = QLabel()
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lbl.setToolTip("اضغط لفتح التقويم")
        self._lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:13px;"
            f"font-weight:bold; background:transparent; border:none; padding:0 10px;"
        )
        self._lbl.mousePressEvent = lambda e: self._open_cal()
        layout.addWidget(self._lbl, 1)

        self._btn_next = _arrow_btn("›")
        self._btn_next.clicked.connect(self._go_next)
        layout.addWidget(self._btn_next)

        self._update_label()

    def _update_label(self):
        today = QDate.currentDate()
        if self._date == today:
            text = "اليوم"
        elif self._date == today.addDays(-1):
            text = "أمس"
        else:
            text = self._date.toString("dd / MM / yyyy")
        self._lbl.setText(text)
        self._btn_next.setEnabled(self._date < today)

    def _go_prev(self):
        self._date = self._date.addDays(-1)
        self._update_label()
        self.changed.emit()

    def _go_next(self):
        if self._date < QDate.currentDate():
            self._date = self._date.addDays(1)
            self._update_label()
            self.changed.emit()

    def _open_cal(self):
        chosen = _open_calendar_dialog(self, self._date)
        if chosen:
            self._date = chosen
            self._update_label()
            self.changed.emit()

    def get_date(self) -> str:
        return self._date.toString("yyyy-MM-dd")

    def date(self) -> QDate:
        return self._date


# ══════════════════════════════════════════
#  DateRangeWidget — نطاق تاريخين
# ══════════════════════════════════════════


class DateRangeWidget(QWidget):
    """
    Widget بتاريخين (من / إلى) مع زرار "الكل" يرجع للـ 30 يوم الماضية.
    get_range() → tuple[str, str]  بصيغة "yyyy-MM-dd"
    """

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._all_btn = QPushButton("الكل")
        self._all_btn.setFixedHeight(44)
        self._all_btn.setFixedWidth(70)
        self._all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._all_btn.clicked.connect(self._reset_to_all)
        layout.addWidget(self._all_btn)

        sep = QLabel("—")
        sep.setStyleSheet(f"color:{COLORS['text_muted']};background:transparent;")
        sep.setFixedWidth(16)
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._from_cell = _SingleDateCell(QDate.currentDate().addDays(-30), "من")
        self._from_cell.changed.connect(self._on_changed)
        layout.addWidget(self._from_cell)

        layout.addWidget(sep)

        self._to_cell = _SingleDateCell(QDate.currentDate(), "إلى")
        self._to_cell.changed.connect(self._on_changed)
        layout.addWidget(self._to_cell)

        layout.addStretch()
        self._update_all_btn_style(False)

    def _on_changed(self):
        self._update_all_btn_style(False)
        self.changed.emit()

    def _reset_to_all(self):
        """يرجع للفترة الافتراضية (30 يوم)."""
        self._from_cell.setDate(QDate.currentDate().addDays(-30))
        self._to_cell.setDate(QDate.currentDate())
        self._update_all_btn_style(True)
        self.changed.emit()

    def _update_all_btn_style(self, active: bool):
        if active:
            self._all_btn.setStyleSheet(
                f"background:{COLORS['blue_bg']};color:{COLORS['blue']};"
                f"border:1.5px solid {COLORS['blue']};border-radius:8px;"
                f"font-size:13px;font-weight:bold;"
            )
        else:
            self._all_btn.setStyleSheet(
                f"background:{COLORS['bg_elevated']};color:{COLORS['text_secondary']};"
                f"border:1px solid {COLORS['border_light']};border-radius:8px;"
                f"font-size:13px;font-weight:bold;"
            )

    def get_range(self) -> tuple[str, str]:
        """يرجع (date_from, date_to) بصيغة 'yyyy-MM-dd'. يُصحح الترتيب تلقائياً."""
        d_from = self._from_cell.date()
        d_to = self._to_cell.date()
        if d_from > d_to:
            d_from, d_to = d_to, d_from
        return d_from.toString("yyyy-MM-dd"), d_to.toString("yyyy-MM-dd")
