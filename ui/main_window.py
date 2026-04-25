"""
main_window.py — النافذة الرئيسية
Fixed: navigation caching, active state, refresh logic
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.styles.theme import COLORS, MAIN_STYLE, SIDEBAR_WIDTH
from ui.screens.dashboard import DashboardScreen
from ui.screens.platforms_screen import PlatformsScreen
from ui.screens.customers_screen import CustomersScreen
from ui.screens.transaction_form import TransactionScreen
from ui.screens.Reports_screen import ReportsScreen


# Navigation items definition
NAV_ITEMS = [
    ("dashboard",    "📊",  "الداشبورد",         DashboardScreen),
    ("platforms",    "🏧",  "المنصات",            PlatformsScreen),
    ("customers",    "👥",  "العملاء",            CustomersScreen),
    ("transaction",  "➕",  "إضافة عملية",        TransactionScreen),
    ("reports",      "📑",  "التقارير والجرد",    ReportsScreen),
]


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة المدفوعات")
        self.setMinimumSize(1100, 680)
        self.resize(1280, 780)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(MAIN_STYLE)

        self._screens:  dict[str, QWidget]     = {}
        self._nav_btns: dict[str, QPushButton] = {}
        self._current_key: str = ""

        self._build_ui()
        self._navigate("dashboard")

    # ─── Build UI ─────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content stack (right in RTL = left visually)
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        main_layout.addWidget(self.stack)

        # Sidebar (left in RTL = right visually)
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(2)

        # Logo
        logo = QLabel("💳  POS System")
        logo.setObjectName("sidebar_logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        # Divider
        div = QFrame()
        div.setObjectName("sidebar_divider")
        div.setFixedHeight(1)
        layout.addWidget(div)
        layout.addSpacing(8)

        # Nav buttons
        for key, icon, label, _ in NAV_ITEMS:
            btn = self._make_nav_btn(key, icon, label)
            layout.addWidget(btn)
            self._nav_btns[key] = btn

        layout.addStretch()

        # Footer
        ver = QLabel("v1.0  —  المرحلة الثانية")
        ver.setObjectName("sidebar_version")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        return sidebar

    def _make_nav_btn(self, key: str, icon: str, label: str) -> QPushButton:
        btn = QPushButton(f"{icon}  {label}")
        btn.setObjectName("nav_btn")
        btn.setFixedHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("active", "false")

        screen_class = next(s[3] for s in NAV_ITEMS if s[0] == key)
        btn.clicked.connect(lambda _, k=key, S=screen_class: self._navigate(k, S))
        return btn

    # ─── Navigation ───────────────────────────────────────────────

    def _navigate(self, key: str, ScreenClass=None):
        """Navigate to a screen — create once, reuse after"""

        # Create screen if not cached
        if key not in self._screens:
            if ScreenClass is None:
                # Find class from NAV_ITEMS
                match = next((s[3] for s in NAV_ITEMS if s[0] == key), None)
                if match:
                    ScreenClass = match
                else:
                    self._show_placeholder(key)
                    return

            try:
                screen = ScreenClass()
                self._screens[key] = screen
                self.stack.addWidget(screen)
            except Exception as e:
                import traceback
                print(f"❌ Error creating screen [{key}]: {e}")
                traceback.print_exc()
                self._show_placeholder(key)
                return

        # Activate screen
        self.stack.setCurrentWidget(self._screens[key])
        self._current_key = key

        # Update nav button states
        for k, btn in self._nav_btns.items():
            active = "true" if k == key else "false"
            if btn.property("active") != active:
                btn.setProperty("active", active)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        # Refresh data
        screen = self._screens[key]
        if hasattr(screen, "refresh"):
            try:
                screen.refresh()
            except Exception as e:
                print(f"⚠️ Refresh error [{key}]: {e}")

    def _show_placeholder(self, key: str):
        """Placeholder for screens that failed to load"""
        if key in self._screens:
            self.stack.setCurrentWidget(self._screens[key])
            return

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("🚧")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        lbl = QLabel("هذه الشاشة قيد التطوير")
        lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 16px; margin-top: 12px;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        self._screens[key] = widget
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

        for k, btn in self._nav_btns.items():
            active = "true" if k == key else "false"
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ─── Public API ───────────────────────────────────────────────

    def navigate_to(self, key: str):
        """Public method for cross-screen navigation"""
        self._navigate(key)