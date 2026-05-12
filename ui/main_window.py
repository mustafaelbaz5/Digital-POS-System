"""
main_window.py — Main Window v3.0 (Dual Theme + Transaction Screen)
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.screens.customers_screen import CustomersScreen
from ui.screens.dashboard import DashboardScreen
from ui.screens.platforms_screen import PlatformsScreen
from ui.screens.Reports_screen import ReportsScreen
from ui.screens.transaction_screen import TransactionScreen
from ui.styles.theme import (
    MAIN_STYLE,
    SIDEBAR_WIDTH,
    build_main_style,
    get_current_theme,
    set_theme,
)

NAV_ITEMS = [
    ("dashboard", "لوحة التحكم", DashboardScreen),
    ("transaction", "عملية جديدة", TransactionScreen),
    ("platforms", "المنصات", PlatformsScreen),
    ("customers", "العملاء", CustomersScreen),
    ("reports", "التقارير والجرد", ReportsScreen),
]

NAV_SYMBOLS = {
    "dashboard": "◈",
    "transaction": "⊕",
    "platforms": "◉",
    "customers": "◎",
    "reports": "◑",
}


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة المدفوعات")
        self.setMinimumSize(1150, 720)
        self.resize(1350, 850)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(MAIN_STYLE)

        self._screens: dict[str, QWidget] = {}
        self._nav_btns: dict[str, QPushButton] = {}
        self._current_key: str = ""

        self._build_ui()
        self._navigate("dashboard")
        self.showMaximized()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

        from ui.styles.theme import COLORS
        self._sep = QFrame()
        self._sep.setFixedWidth(1)
        self._sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        main_layout.addWidget(self._sep)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.stack.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack, 1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 24, 12, 16)
        layout.setSpacing(4)

        # Brand
        brand = QLabel("نظام المدفوعات")
        brand.setObjectName("sidebar_brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(brand)

        div = QFrame()
        div.setObjectName("sidebar_divider")
        layout.addWidget(div)
        layout.addSpacing(12)

        # Navigation Buttons
        for key, label, _ in NAV_ITEMS:
            symbol = NAV_SYMBOLS.get(key, "·")
            btn = self._make_nav_btn(key, f"{symbol}  {label}")
            layout.addWidget(btn)
            self._nav_btns[key] = btn

        layout.addStretch()

        # Theme Toggle
        self._theme_btn = QPushButton("🌙  الوضع الليلي")
        self._theme_btn.setObjectName("theme_toggle_btn")
        self._theme_btn.setFixedHeight(38)
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self._theme_btn)

        return sidebar

    def _make_nav_btn(self, key: str, label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("nav_btn")
        btn.setFixedHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("active", "false")
        btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        screen_class = next((s[2] for s in NAV_ITEMS if s[0] == key), None)
        btn.clicked.connect(lambda _, k=key, S=screen_class: self._navigate(k, S))
        return btn

    def _navigate(self, key: str, ScreenClass=None):
        if key not in self._screens:
            if ScreenClass is None:
                ScreenClass = next((s[2] for s in NAV_ITEMS if s[0] == key), None)

            if ScreenClass is None:
                return

            try:
                screen = ScreenClass()
                self._screens[key] = screen
                self.stack.addWidget(screen)
            except Exception as e:
                import traceback
                print(f"[ERR] Failed to create screen {key}: {e}")
                traceback.print_exc()
                return

        self.stack.setCurrentWidget(self._screens[key])
        self._current_key = key

        for k, btn in self._nav_btns.items():
            active = "true" if k == key else "false"
            if btn.property("active") != active:
                btn.setProperty("active", active)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        screen = self._screens.get(key)
        if screen and hasattr(screen, "refresh"):
            try:
                screen.refresh()
            except Exception as e:
                print(f"[WARN] Refresh error in {key}: {e}")

    def _toggle_theme(self):
        current = get_current_theme()
        new_mode = "light" if current == "dark" else "dark"
        set_theme(new_mode)

        from ui.styles.theme import COLORS as C
        new_style = build_main_style()
        QApplication.instance().setStyleSheet(new_style)
        self.setStyleSheet(new_style)
        self._sep.setStyleSheet(f"background: {C['border']}; border: none;")

        # Update toggle button label
        if new_mode == "light":
            self._theme_btn.setText("☀️  الوضع النهاري")
        else:
            self._theme_btn.setText("🌙  الوضع الليلي")

        # Destroy all screens so they rebuild with new COLORS on next visit
        for key, screen in list(self._screens.items()):
            self.stack.removeWidget(screen)
            screen.deleteLater()
        self._screens.clear()

        # Recreate current screen
        self._navigate(self._current_key)

    def navigate_to(self, key: str):
        """Public API for navigation from any screen."""
        self._navigate(key)

    def open_transaction_for_platform(self, platform_id: int):
        """Navigate to transaction screen and pre-select a platform."""
        self._navigate("transaction")
        screen = self._screens.get("transaction")
        if screen and hasattr(screen, "select_platform"):
            screen.select_platform(platform_id)
