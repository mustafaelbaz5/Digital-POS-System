"""
Reusable UI Components
مكونات الواجهة القابلة لإعادة الاستخدام
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.styles.theme import COLORS, get_status_style, get_status_text


# ══════════════════════════════════════════
#  كارت الإحصائية  (Stat Card)
# ══════════════════════════════════════════

class StatCard(QWidget):
    """كارت يعرض رقم إحصائي مع عنوان وأيقونة"""

    def __init__(self, title: str, value: str = "0",
                 icon: str = "", accent_color: str = None, parent=None):
        super().__init__(parent)
        self.accent = accent_color or COLORS["blue_primary"]
        self._build_ui(title, value, icon)

    def _build_ui(self, title: str, value: str, icon: str):
        self.setObjectName("stat_card")
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # الأيقونة + العنوان
        top_row = QHBoxLayout()

        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI Emoji", 20))
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            top_row.addWidget(icon_lbl)

        top_row.addStretch()

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("stat_label")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        top_row.addWidget(self.title_lbl)

        layout.addLayout(top_row)

        # القيمة
        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("stat_value")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.value_lbl.setStyleSheet(f"color: {self.accent};")
        layout.addWidget(self.value_lbl)

        # خط ملون أسفل الكارت
        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            f"stop:0 {self.accent}, stop:1 transparent);"
            f"border-radius: 2px;"
        )
        layout.addWidget(bar)

    def set_value(self, value: str):
        """تحديث القيمة"""
        self.value_lbl.setText(value)


# ══════════════════════════════════════════
#  كارت المنصة  (Platform Card)
# ══════════════════════════════════════════

class PlatformCard(QWidget):
    """كارت يعرض منصة (ماكينة أو محفظة) مع رصيدها"""
    deposit_clicked = pyqtSignal(int)   # يرسل platform_id

    def __init__(self, platform: dict, parent=None):
        super().__init__(parent)
        self.platform_id = platform["id"]
        self._build_ui(platform)

    def _build_ui(self, p: dict):
        self.setObjectName("card")
        self.setMinimumWidth(200)
        self.setMaximumWidth(260)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # النوع badge
        type_text = "🏧 ماكينة" if p["type"] == "machine" else "💳 محفظة"
        type_color = COLORS["blue_light"] if p["type"] == "machine" else COLORS["purple"]

        type_lbl = QLabel(type_text)
        type_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        type_lbl.setStyleSheet(
            f"color: {type_color}; font-size: 12px; font-weight: bold;"
        )
        layout.addWidget(type_lbl)

        # اسم المنصة
        name_lbl = QLabel(p["name"])
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: bold;"
        )
        layout.addWidget(name_lbl)

        # الرصيد
        balance = p.get("balance", 0)
        balance_lbl = QLabel(f"{balance:,.2f} ج")
        balance_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        color = COLORS["green"] if balance > 0 else COLORS["text_muted"]
        balance_lbl.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: bold;"
        )
        layout.addWidget(balance_lbl)

        # الحد الشهري للمحفظة
        if p["type"] == "wallet":
            used  = p.get("monthly_used", 0)
            limit = p.get("monthly_limit", 200000)
            pct   = min(100, int(used / limit * 100)) if limit else 0

            limit_lbl = QLabel(f"الحد الشهري: {used:,.0f} / {limit:,.0f} ج ({pct}%)")
            limit_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            limit_color = COLORS["red"] if pct >= 90 else COLORS["text_secondary"]
            limit_lbl.setStyleSheet(f"color: {limit_color}; font-size: 12px;")
            layout.addWidget(limit_lbl)

        # زرار الإيداع
        dep_btn = QPushButton("+ إيداع")
        dep_btn.setObjectName("btn_secondary")
        dep_btn.setFixedHeight(34)
        dep_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dep_btn.clicked.connect(lambda: self.deposit_clicked.emit(self.platform_id))
        layout.addWidget(dep_btn)

    def update_data(self, platform: dict):
        """تحديث بيانات الكارت"""
        # إعادة بناء الواجهة بالبيانات الجديدة
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().deleteLater()
        self._build_ui(platform)


# ══════════════════════════════════════════
#  جدول البيانات  (Data Table)
# ══════════════════════════════════════════

class DataTable(QTableWidget):
    """جدول بيانات موحد مع إعدادات ثابتة"""

    def __init__(self, columns: list[tuple], parent=None):
        """
        columns: قائمة tuples (اسم العمود, العرض)
        مثال: [("الاسم", 150), ("المبلغ", 100)]
        """
        super().__init__(parent)
        self._setup(columns)

    def _setup(self, columns: list[tuple]):
        self.setColumnCount(len(columns))
        headers = [c[0] for c in columns]
        self.setHorizontalHeaderLabels(headers)

        # العرض
        for i, (_, width) in enumerate(columns):
            if width == -1:
                self.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.Stretch
                )
            else:
                self.setColumnWidth(i, width)
                self.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.Fixed
                )

        # إعدادات عامة
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(
            f"alternate-background-color: {COLORS['bg_hover']};"
        )

        # RTL
        self.horizontalHeader().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def set_cell(self, row: int, col: int, text: str,
                 color: str = None, bold: bool = False, align=None):
        """إضافة خلية مع تنسيق"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        if color:
            item.setForeground(QColor(color))
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        if align:
            item.setTextAlignment(align)
        else:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

        self.setItem(row, col, item)

    def add_status_badge(self, row: int, col: int, status: str):
        """إضافة badge للحالة"""
        text = get_status_text(status)
        self.set_cell(row, col, text)

        colors_map = {
            "cash":    COLORS["green"],
            "pending": COLORS["yellow"],
            "paid":    COLORS["text_muted"],
        }
        color = colors_map.get(status, COLORS["text_secondary"])
        if self.item(row, col):
            self.item(row, col).setForeground(QColor(color))

    def clear_rows(self):
        """مسح كل الصفوف"""
        self.setRowCount(0)


# ══════════════════════════════════════════
#  فاصل أفقي  (Section Separator)
# ══════════════════════════════════════════

class SectionTitle(QWidget):
    """عنوان قسم مع خط فاصل"""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 4)
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

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(line)
