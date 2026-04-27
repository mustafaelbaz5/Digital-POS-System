"""
main_window.py — Main Window v2.1 (Improved Sidebar + Better UX)
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt

from ui.styles.theme import COLORS, MAIN_STYLE, SIDEBAR_WIDTH
from ui.screens.dashboard import DashboardScreen
from ui.screens.platforms_screen import PlatformsScreen
from ui.screens.customers_screen import CustomersScreen
from ui.screens.transaction_form import TransactionScreen
from ui.screens.Reports_screen import ReportsScreen   # تأكد من اسم الملف Reports_screen.py


NAV_ITEMS = [
    ("dashboard",   "لوحة التحكم",      DashboardScreen),
    ("platforms",   "المنصات",           PlatformsScreen),
    ("customers",   "العملاء",           CustomersScreen),
    ("transaction", "إضافة عملية",       TransactionScreen),
    ("reports",     "التقارير والجرد",   ReportsScreen),
]

NAV_SYMBOLS = {
    "dashboard":   "◈",
    "platforms":   "◉",
    "customers":   "◎",
    "transaction": "⊕",
    "reports":     "◑",
}


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة المدفوعات", )
        self.setMinimumSize(1150, 720)
        self.resize(1350, 850)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(MAIN_STYLE)

        self._screens: dict[str, QWidget] = {}
        self._nav_btns: dict[str, QPushButton] = {}
        self._current_key: str = ""

        self._build_ui()
        self._navigate("dashboard")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar (يسار في RTL)
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

        # Main Content
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.stack, 1)   # stretch = 1

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(6)

        # Brand Block
        brand = QLabel("نظام المدفوعات")
        brand.setObjectName("sidebar_brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)

        # Divider
        div = QFrame()
        div.setObjectName("sidebar_divider")
        layout.addWidget(div)
        layout.addSpacing(16)

        # Navigation Buttons
        for key, label, _ in NAV_ITEMS:
            btn = self._make_nav_btn(key, label)
            layout.addWidget(btn)
            self._nav_btns[key] = btn

        layout.addStretch()
        return sidebar

    def _make_nav_btn(self, key: str, label: str) -> QPushButton:
        btn_text = f"{label}"

        btn = QPushButton(btn_text)
        btn.setObjectName("nav_btn")
        btn.setFixedHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("active", "false")
        btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)   # مهم جداً

        # ربط الزر بالتنقل
        screen_class = next((s[2] for s in NAV_ITEMS if s[0] == key), None)
        btn.clicked.connect(lambda _, k=key, S=screen_class: self._navigate(k, S))

        return btn

    def _navigate(self, key: str, ScreenClass=None):
        if key not in self._screens:
            if ScreenClass is None:
                ScreenClass = next((s[2] for s in NAV_ITEMS if s[0] == key), None)

            if ScreenClass is None:
                self._show_placeholder(key)
                return

            try:
                screen = ScreenClass()
                self._screens[key] = screen
                self.stack.addWidget(screen)
                print(f"[OK] Screen created: {key}")
            except Exception as e:
                import traceback
                print(f"[ERR] Failed to create screen {key}: {e}")
                traceback.print_exc()
                self._show_placeholder(key)
                return

        self.stack.setCurrentWidget(self._screens[key])
        self._current_key = key

        # تحديث حالة الأزرار
        for k, btn in self._nav_btns.items():
            active = "true" if k == key else "false"
            if btn.property("active") != active:
                btn.setProperty("active", active)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        # Refresh الشاشة إذا كان فيها دالة refresh
        screen = self._screens.get(key)
        if screen and hasattr(screen, "refresh"):
            try:
                screen.refresh()
            except Exception as e:
                print(f"[WARN] Refresh error in {key}: {e}")

    def _show_placeholder(self, key: str):
        # ... (نفس الكود السابق أو يمكن تبسيطه)
        pass   # يمكنك الاحتفاظ بالنسخة القديمة أو تحسينها

    def navigate_to(self, key: str):
        """API عام للتنقل من أي مكان"""
        self._navigate(key)