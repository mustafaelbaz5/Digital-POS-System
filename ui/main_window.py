"""
Main Window — النافذة الرئيسية مع الـ Sidebar
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from ui.screens.customers_screen import CustomersScreen
from ui.screens.transaction_form import TransactionScreen
from ui.styles.theme import COLORS, MAIN_STYLE
from ui.screens.dashboard import DashboardScreen
from ui.screens.platforms_screen import PlatformsScreen


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة المدفوعات")
        self.setMinimumSize(1200, 750)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(MAIN_STYLE)

        self._screens = {}          # اسم الشاشة → QWidget
        self._nav_btns = {}         # اسم الشاشة → QPushButton

        self._build_ui()
        self._navigate("dashboard")

    # ─── بناء الواجهة ──────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── المحتوى (يمين)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # ── الـ Sidebar (يسار)
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # اللوجو / الاسم
        logo = QLabel("💳  POS System")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            f"color: {COLORS['blue_light']}; font-size: 16px; "
            f"font-weight: bold; padding: 8px 0 16px 0;"
        )
        layout.addWidget(logo)

        # خط فاصل
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {COLORS['border']}; margin-bottom: 8px;")
        layout.addWidget(line)

        # أزرار التنقل
        nav_items = [
            ("dashboard",  "📊  الداشبورد",        DashboardScreen),
            ("platforms",  "🏧  المنصات",           PlatformsScreen),
            ("customers",  "👥  العملاء",           CustomersScreen),
            ("transaction","➕  إضافة عملية",       TransactionScreen),
            ("reports",    "📑  التقارير والجرد",   None),   # قادم
        ]

        for key, label, ScreenClass in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setFixedHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key, S=ScreenClass: self._navigate(k, S))
            layout.addWidget(btn)
            self._nav_btns[key] = btn

        layout.addStretch()

        # Footer
        ver = QLabel("v1.0  —  المرحلة الثانية")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(ver)

        return sidebar

    # ─── التنقل ────────────────────────────────────────────────────

    def _navigate(self, key: str, ScreenClass=None):
        if key not in self._screens:
            if ScreenClass is None:
                self._show_coming_soon(key)
                return

        try:
            screen = ScreenClass()          # type: ignore # محاولة إنشاء الشاشة
            self._screens[key] = screen
            self.stack.addWidget(screen)
            print(f"✅ تم إنشاء شاشة: {key}")   # ← مهم للـ debug

        except Exception as e:
            print(f"❌ خطأ في إنشاء شاشة {key}: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()           # هيطبع الـ stack trace كامل
            self._show_coming_soon(key)
            return

    # تفعيل الشاشة
        self.stack.setCurrentWidget(self._screens[key])

    # تحديث حالة الأزرار
        for k, btn in self._nav_btns.items():
            btn.setProperty("active", "true" if k == key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # تحديث البيانات
        screen = self._screens.get(key)
        if screen and hasattr(screen, "refresh"):
            try:
                screen.refresh()
            except Exception as e:
                print(f"خطأ في refresh الشاشة {key}: {e}")

    def _show_coming_soon(self, key: str):
        """شاشة مؤقتة للشاشات القادمة"""
        if key in self._screens:
            return

        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel("🚧  هذه الشاشة قيد التطوير")
        lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 18px;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        self._screens[key] = placeholder
        self.stack.addWidget(placeholder)
        self.stack.setCurrentWidget(placeholder)

        for k, btn in self._nav_btns.items():
            btn.setProperty("active", "true" if k == key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
