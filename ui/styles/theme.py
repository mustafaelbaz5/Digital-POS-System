# ──────────────────────────────────────────────────
# COLOR SYSTEM — Dual Theme (Dark + Light)
# ──────────────────────────────────────────────────

DARK_COLORS = {
    # SURFACES
    "bg_dark": "#0D1117",
    "bg_card": "#0D1117",
    "bg_elevated": "#161B22",
    "bg_input": "#090C10",
    "bg_hover": "#21262D",
    "bg_button": "#21262D",
    # BORDERS
    "border": "#30363D",
    "border_light": "#424B57",
    # ACCENT
    "accent": "#059669",
    "accent_hover": "#10B981",
    "accent_dim": "#064E3B",
    # TYPOGRAPHY
    "text_primary": "#E6EDF3",
    "text_secondary": "#8B949E",
    "text_muted": "#484F58",
    # SEMANTIC
    "green": "#10B981",
    "green_bg": "#064E3B20",
    "green_border": "#064E3B",
    "red": "#F85149",
    "red_bg": "#490E0E20",
    "red_border": "#490E0E",
    "yellow": "#D29922",
    "yellow_bg": "#35210020",
    "yellow_border": "#352100",
    # COMPATIBILITY ALIASES
    "teal_primary": "#10B981",
    "teal_light": "#34D399",
    "teal_bright": "#6EE7B7",
    "teal_dark": "#059669",
    "teal_subtle": "#064E3B",
    "teal_glow": "#064E3B",
    "blue": "#58A6FF",
    "blue_bg": "#0C2D6B20",
    "blue_border": "#0C2D6B",
    "purple": "#BC8CFF",
    "purple_bg": "#3B256B20",
    "cyan": "#39C5BB",
    "cyan_bg": "#1A3B3920",
    "emerald": "#10B981",
    "emerald_bg": "#064E3B20",
    "emerald_border": "#064E3B",
    "bg_selected": "#161B22",
    "border_focus": "#10B981",
    "text_dim": "#484F58",
    # SIDEBAR
    "sidebar_bg": "#0D1117",
    "sidebar_active_bg": "#064E3B",
    "sidebar_active_color": "#059669",
    "sidebar_border": "#30363D",
}

LIGHT_COLORS = {
    # SURFACES
    "bg_dark": "#F6F8FA",
    "bg_card": "#FFFFFF",
    "bg_elevated": "#F6F8FA",
    "bg_input": "#FFFFFF",
    "bg_hover": "#F3F4F6",
    "bg_button": "#F3F4F6",
    # BORDERS
    "border": "#E5E7EB",
    "border_light": "#D1D5DB",
    # ACCENT
    "accent": "#059669",
    "accent_hover": "#047857",
    "accent_dim": "#ECFDF5",
    # TYPOGRAPHY
    "text_primary": "#111827",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    # SEMANTIC
    "green": "#059669",
    "green_bg": "#ECFDF5",
    "green_border": "#A7F3D0",
    "red": "#DC2626",
    "red_bg": "#FEF2F2",
    "red_border": "#FECACA",
    "yellow": "#D97706",
    "yellow_bg": "#FFFBEB",
    "yellow_border": "#FDE68A",
    # COMPATIBILITY ALIASES
    "teal_primary": "#059669",
    "teal_light": "#34D399",
    "teal_bright": "#6EE7B7",
    "teal_dark": "#047857",
    "teal_subtle": "#ECFDF5",
    "teal_glow": "#ECFDF5",
    "blue": "#2563EB",
    "blue_bg": "#EFF6FF",
    "blue_border": "#BFDBFE",
    "purple": "#7C3AED",
    "purple_bg": "#F5F3FF",
    "cyan": "#0891B2",
    "cyan_bg": "#ECFEFF",
    "emerald": "#059669",
    "emerald_bg": "#ECFDF5",
    "emerald_border": "#A7F3D0",
    "bg_selected": "#F3F4F6",
    "border_focus": "#059669",
    "text_dim": "#9CA3AF",
    # SIDEBAR
    "sidebar_bg": "#F9FAFB",
    "sidebar_active_bg": "#ECFDF5",
    "sidebar_active_color": "#059669",
    "sidebar_border": "#E5E7EB",
}

# Mutable active colors dict — updated in-place on theme switch
COLORS: dict = dict(DARK_COLORS)

# Current theme state
_current_theme: str = "dark"


def get_current_theme() -> str:
    return _current_theme


def set_theme(mode: str) -> None:
    """Switch theme. Updates COLORS dict in-place. Returns new stylesheet via build_main_style()."""
    global _current_theme
    _current_theme = mode
    if mode == "light":
        COLORS.update(LIGHT_COLORS)
    else:
        COLORS.update(DARK_COLORS)


# ──────────────────────────────────────────────────
# TYPOGRAPHY
# ──────────────────────────────────────────────────

FONT = {
    "family": "'Cairo', 'Tajawal', 'Segoe UI', sans-serif",
    "xs": "10px",
    "sm": "12px",
    "md": "14px",
    "lg": "16px",
    "xl": "20px",
    "2xl": "26px",
    "3xl": "32px",
}


# ──────────────────────────────────────────────────
# LAYOUT CONSTANTS
# ──────────────────────────────────────────────────

SIDEBAR_WIDTH = 240
HEADER_HEIGHT = 70
ROW_HEIGHT = 60
BTN_HEIGHT = 42
INPUT_HEIGHT = 44
BORDER_RADIUS = "10px"
CARD_RADIUS = "14px"

# Standard Spacing (Gaps)
GAP_XS = 4
GAP_SM = 8
GAP_MD = 16
GAP_LG = 24
GAP_XL = 32

# Standard Margins
MARGIN_CONTENT = 20
MARGIN_CARD = 20


# ──────────────────────────────────────────────────
# MAIN STYLESHEET (dynamic — call build_main_style())
# ──────────────────────────────────────────────────

def build_main_style(colors: dict = None) -> str:
    """Generate QSS stylesheet from the given colors dict (defaults to current COLORS)."""
    C = colors if colors is not None else COLORS
    return f"""

/* ── Base ── */
QMainWindow, QWidget, QDialog {{
    background: {C['bg_dark']};
    color: {C['text_primary']};
    font-family: {FONT['family']};
    font-size: {FONT['md']};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C['border']};
    border-radius: 3px;
    min-height: 40px;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: {C['border']};
    border-radius: 3px;
    min-width: 40px;
}}

/* ── Sidebar ── */
#sidebar {{
    background: {C['sidebar_bg']};
    border-left: 1px solid {C['sidebar_border']};
}}

#sidebar_brand {{
    color: {C['text_primary']};
    font-size: {FONT['lg']};
    font-weight: bold;
    padding: 0 10px;
}}

#sidebar_divider {{
    background: {C['border']};
    max-height: 1px;
    border: none;
    margin: {GAP_SM}px {GAP_MD}px;
}}

#theme_toggle_btn {{
    background: {C['bg_elevated']};
    color: {C['text_secondary']};
    border: 1px solid {C['border']};
    border-radius: {BORDER_RADIUS};
    padding: 8px 12px;
    font-size: {FONT['sm']};
    margin: 2px 8px;
    text-align: left;
}}
#theme_toggle_btn:hover {{
    background: {C['bg_hover']};
    color: {C['text_primary']};
}}

/* ── Navigation ── */
#nav_btn {{
    background: transparent;
    color: {C['text_secondary']};
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 12px 18px;
    text-align: left;
    font-size: {FONT['md']};
    margin: 2px 4px;
}}
#nav_btn:hover {{
    background: {C['bg_hover']};
    color: {C['text_primary']};
}}
#nav_btn[active="true"] {{
    background: {C['sidebar_active_bg']};
    color: {C['sidebar_active_color']};
    font-weight: bold;
    border-right: 3px solid {C['accent']};
}}

/* ── Screen Header ── */
#screen_header {{
    background: {C['bg_dark']};
    border-bottom: 1px solid {C['border']};
    min-height: {HEADER_HEIGHT}px;
    max-height: {HEADER_HEIGHT}px;
}}
#screen_title {{
    color: {C['text_primary']};
    font-size: {FONT['xl']};
    font-weight: bold;
}}
#screen_subtitle {{
    color: {C['text_secondary']};
    font-size: {FONT['sm']};
}}

/* ── Cards ── */
#card {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: {CARD_RADIUS};
}}

#stat_card {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: {CARD_RADIUS};
}}

#card_highlight {{
    background: {C['bg_elevated']};
    border: 1px solid {C['accent_dim']};
    border-radius: {CARD_RADIUS};
}}

#stat_value {{
    color: {C['text_primary']};
    font-size: {FONT['2xl']};
    font-weight: bold;
}}
#stat_label {{
    color: {C['text_secondary']};
    font-size: {FONT['sm']};
}}

/* ── Platform Selection Cards ── */
#platform_card_btn {{
    background: {C['bg_card']};
    color: {C['text_primary']};
    border: 2px solid {C['border']};
    border-radius: {CARD_RADIUS};
    padding: 12px;
    text-align: center;
    font-size: {FONT['sm']};
}}
#platform_card_btn:hover {{
    border-color: {C['accent']};
    background: {C['bg_hover']};
}}
#platform_card_btn[selected="true"] {{
    border-color: {C['accent']};
    background: {C['accent_dim']};
    color: {C['accent']};
}}

/* ── Buttons ── */
QPushButton {{
    font-family: {FONT['family']};
    border-radius: 6px;
    padding: 8px 16px;
    border: 2px solid transparent;
}}

#btn_primary {{
    background: {C['accent']};
    color: #ffffff;
    border: 2px solid {C['accent']};
    border-radius: 6px;
    padding: 0 24px;
    min-height: {BTN_HEIGHT}px;
    font-weight: bold;
    font-size: {FONT['md']};
}}
#btn_primary:hover {{
    background: {C['accent_hover']};
    border-color: {C['accent_hover']};
}}
#btn_primary:pressed {{
    background: {C['accent_dim']};
}}
#btn_primary:disabled {{
    background: {C['border']};
    color: {C['text_muted']};
    border: none;
}}

#btn_secondary {{
    background: {C['bg_elevated']};
    color: {C['text_primary']};
    border: 2px solid {C['border']};
    border-radius: 6px;
    padding: 0 20px;
    min-height: {BTN_HEIGHT}px;
    font-size: {FONT['md']};
}}
#btn_secondary:hover {{
    background: {C['bg_hover']};
    border-color: {C['border_light']};
}}
#btn_secondary:pressed {{
    background: {C['bg_dark']};
}}

#btn_ghost {{
    background: {C['bg_elevated']};
    color: {C['text_secondary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 4px 12px;
    font-size: {FONT['sm']};
}}
#btn_ghost:hover {{
    background: {C['bg_hover']};
    color: {C['text_primary']};
}}

#btn_danger {{
    background: {C['red_bg']};
    color: {C['red']};
    border: 2px solid {C['red_border']};
    border-radius: 6px;
    min-height: {BTN_HEIGHT}px;
    font-weight: bold;
}}
#btn_danger:hover {{
    background: {C['red_bg']};
    border-color: {C['red']};
}}

#btn_statement {{
    background: #0969DA;
    color: #ffffff;
    border: 2px solid #0969DA;
    border-radius: 6px;
    font-weight: bold;
    font-size: {FONT['sm']};
}}
#btn_statement:hover {{
    background: #0550AE;
}}

/* ── Mode Toggle Buttons ── */
#mode_btn_active {{
    background: {C['accent']};
    color: #ffffff;
    border: 2px solid {C['accent']};
    border-radius: 8px;
    font-weight: bold;
    padding: 8px 20px;
}}
#mode_btn_idle {{
    background: {C['bg_elevated']};
    color: {C['text_secondary']};
    border: 2px solid {C['border']};
    border-radius: 8px;
    padding: 8px 20px;
}}
#mode_btn_idle:hover {{
    background: {C['bg_hover']};
    color: {C['text_primary']};
}}

/* ── In-Table Buttons ── */
QTableWidget QPushButton {{
    border-radius: 6px;
    padding: 2px 10px;
    font-weight: bold;
    font-size: 10px;
    min-height: 22px;
    border: 2px solid {C['border_light']};
    background-color: {C['bg_hover']};
    color: {C['text_primary']};
}}

QTableWidget QPushButton:hover {{
    background-color: {C['bg_hover']};
    border: 2px solid {C['border_light']};
}}

QTableWidget #btn_ghost, QTableWidget #btn_ghost:hover, QTableWidget #btn_ghost:pressed {{
    border: 1px solid {C['border_light']};
    background-color: {C['bg_hover']};
    color: {C['text_primary']};
}}

QTableWidget #btn_secondary, QTableWidget #btn_secondary:hover, QTableWidget #btn_secondary:pressed {{
    border: 1px solid {C['border_light']};
    background-color: {C['bg_elevated']};
    color: {C['text_primary']};
}}

QTableWidget #btn_statement, QTableWidget #btn_statement:hover, QTableWidget #btn_statement:pressed {{
    border: 1px solid #0969DA;
    background-color: #0969DA;
    color: #ffffff;
}}

QTableWidget #btn_primary, QTableWidget #btn_primary:hover, QTableWidget #btn_primary:pressed {{
    border: 1px solid {C['accent']};
    background-color: {C['accent']};
    color: #ffffff;
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
QComboBox, QDateEdit {{
    background: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: {BORDER_RADIUS};
    padding: 8px 14px;
    min-height: {INPUT_HEIGHT}px;
    selection-background-color: {C['accent']};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {C['accent']};
}}

QComboBox::drop-down {{
    background: {C['bg_hover']};
    border-left: 1px solid {C['border']};
    width: 32px;
    border-top-right-radius: {BORDER_RADIUS};
    border-bottom-right-radius: {BORDER_RADIUS};
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {C['text_secondary']};
    margin-top: 2px;
}}
QComboBox QAbstractItemView {{
    background: {C['bg_elevated']};
    border: 1px solid {C['border_light']};
    border-radius: {BORDER_RADIUS};
    color: {C['text_primary']};
    selection-background-color: {C['bg_hover']};
    selection-color: {C['accent']};
    outline: none;
    padding: 4px;
}}

/* ── Table ── */
QTableWidget {{
    background: {C['bg_dark']};
    border: none;
    border-radius: {CARD_RADIUS};
    gridline-color: transparent;
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 20px;
    border-bottom: 1px solid {C['border']};
}}
QTableWidget::item:selected {{
    background: {C['bg_hover']};
    color: {C['accent']};
}}
QHeaderView {{
    background: {C['bg_elevated']};
    border: none;
    border-bottom: 1px solid {C['border']};
}}
QHeaderView::section {{
    background: {C['bg_elevated']};
    color: {C['text_secondary']};
    border: none;
    border-bottom: 1px solid {C['border']};
    padding: 16px 18px;
    font-size: {FONT['sm']};
    font-weight: 800;
}}
QHeaderView::section:last {{
    border-left: none;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    background: transparent;
    border: none;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {C['text_secondary']};
    padding: 12px 24px;
    font-weight: bold;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {C['accent']};
    border-bottom: 2px solid {C['accent']};
}}

/* ── Dialogs ── */
QDialog {{
    background: {C['bg_dark']};
    border: 1px solid {C['border']};
}}

#dialog_header {{
    background: {C['bg_elevated']};
    border-bottom: 1px solid {C['border']};
    min-height: 50px;
}}

#dialog_title {{
    color: {C['text_primary']};
    font-size: {FONT['lg']};
    font-weight: bold;
}}

#dialog_close_btn {{
    background: transparent;
    color: {C['text_secondary']};
    border: none;
    font-size: 14px;
    font-weight: bold;
    border-radius: 15px;
    padding: 0;
    margin: 0;
}}

QMessageBox {{
    background: {C['bg_dark']};
}}
QMessageBox QLabel {{
    color: {C['text_primary']};
    font-size: {FONT['md']};
}}
QMessageBox QPushButton {{
    min-width: 100px;
    min-height: 36px;
}}

QMenu {{
    background: {C['bg_elevated']};
    border: 1px solid {C['border_light']};
    border-radius: 10px;
    padding: 5px;
}}
QMenu::item {{
    padding: 10px 20px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: {C['bg_hover']};
    color: {C['accent']};
}}

"""


# Backward-compat: pre-built dark stylesheet
MAIN_STYLE: str = build_main_style(DARK_COLORS)


# ──────────────────────────────────────────────────
# STATUS HELPERS
# ──────────────────────────────────────────────────


def get_status_style(status: str) -> str:
    C = COLORS
    base = "border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: bold;"
    styles = {
        "pending": f"color: {C['yellow']}; background: {C['yellow_bg']}; border: 1px solid {C['yellow_border']}; {base}",
        "paid": f"color: {C['green']}; background: {C['green_bg']}; border: 1px solid {C['green_border']}; {base}",
    }
    return styles.get(status, "")


def get_status_text(status: str) -> str:
    return {"pending": "مؤجل ⏳", "paid": "تم السداد ✓"}.get(status, status)
