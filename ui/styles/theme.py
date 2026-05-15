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
    "bg_alt_row": "#161B22",
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
    "text_on_dark": "#FFFFFF",
    "save": "#1565C0",
    "settle": "#2E7D32",
    "delete": "#C62828",
    "ledger": "#FFB020",
    "machines": "#3F51B5",
    "wallets": "#2E7D32",
    "instapay": "#6A1B9A",
    "clients": "#00695C",
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
    # SUCCESS — Settle/Pay Action
    "success": "#32D74B",
    "success_hover": "#28A745",
    "success_dim": "#1A3A2A",
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
    "bg_dark": "#F0F2F5",           # Core Background (Light Grey)
    "bg_card": "#FFFFFF",            # Body of the card
    "bg_elevated": "#FFFFFF",        # White body
    "bg_input": "#FFFFFF",           # Input background
    "bg_hover": "#F0F2F5",           # Subtle hover
    "bg_button": "#F0F2F5",          # Secondary button background
    "bg_alt_row": "#F8F9FA",         # Default alternate row
    # BORDERS
    "border": "#E0E4E7",
    "border_light": "#F1F3F4",
    # ACCENT — Primary Action
    "accent": "#1565C0",             # Bold Blue
    "accent_hover": "#0D47A1",
    "accent_dim": "#E3F2FD",
    # TYPOGRAPHY
    "text_primary": "#212121",       # Dark Charcoal for light backgrounds
    "text_secondary": "#424242",
    "text_muted": "#757575",
    "text_on_dark": "#FFFFFF",       # Pure White for dark backgrounds
    # SEMANTIC / BUTTONS
    "save": "#1565C0",               # Bold Blue
    "settle": "#2E7D32",             # Vivid Emerald
    "delete": "#C62828",             # Crimson Red
    "ledger": "#FF8F00",             # Deep Amber (Black text logic)
    # SECTION IDENTITIES (Dark & Rich)
    "machines": "#3F51B5",           # Deep Indigo
    "wallets": "#2E7D32",            # Forest Green
    "instapay": "#6A1B9A",           # Royal Purple
    "clients": "#00695C",            # Dark Teal
    # SEMANTIC STATUS (Restored for compatibility)
    "green": "#2E7D32",
    "green_bg": "#E8F5E9",
    "green_border": "#C8E6C9",
    "red": "#C62828",
    "red_bg": "#FFEBEE",
    "red_border": "#FFCDD2",
    "yellow": "#F57C00",
    "yellow_bg": "#FFF3E0",
    "yellow_border": "#FFE0B2",
    "blue": "#1976D2",
    "blue_bg": "#E3F2FD",
    "blue_border": "#BBDEFB",
    "purple": "#7B1FA2",
    "purple_bg": "#F3E5F5",
    "cyan": "#0097A7",
    "cyan_bg": "#E0F7FA",
    # Sidebar styling
    "sidebar_bg": "#F0F4F8",
    "sidebar_active_bg": "#DCEEFB",
    "sidebar_active_color": "#1565C0",
    "sidebar_border": "#D1D9E0",
}

# Mapping platform types to their color identity
COLOR_MAPPER = {
    "machine": "machines",
    "wallet": "wallets",
    "instapay": "instapay",
    "customer": "clients",
    "group": "clients",
}

# Mutable active colors dict — updated in-place on theme switch
COLORS: dict = dict(LIGHT_COLORS)

# Current theme state
_current_theme: str = "light"

def get_section_color(stype: str) -> str:
    key = COLOR_MAPPER.get(stype, "accent")
    return COLORS.get(key, COLORS["accent"])

def get_current_theme() -> str:
    return _current_theme

def text_for_background(hex_color: str) -> str:
    """Return high-contrast text color for a solid hex background."""
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return COLORS.get("text_primary", "#212121")
    r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#FFFFFF" if luminance < 0.55 else "#212121"

def set_theme(mode: str) -> None:
    """Switch theme. Updates COLORS dict in-place."""
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
    "family": "Tajawal, Cairo, Segoe UI, sans-serif",
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
CARD_RADIUS = "15px"

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

QWidget {{
    direction: rtl;
}}

/* ── Card Containers ── */
#card {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 15px;
}}

#stat_card {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 15px;
}}

#card_highlight {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 15px;
}}

/* Section Header styling within CardGroup */
#card_header {{
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
    padding: 8px 16px;
    min-height: 36px;
    max-height: 36px;
}}
#card_header_title {{
    color: {C['text_on_dark']};
    font-size: {FONT['md']};
    font-weight: bold;
}}

/* ── Buttons (High-Visibility Deep Palette) ── */
QPushButton {{
    font-family: {FONT['family']};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
}}

#btn_primary {{
    background: {C['save']};
    color: {C['text_on_dark']};
}}
#btn_primary:hover {{ background: {C['accent_hover']}; }}

#btn_success {{
    background: {C['settle']};
    color: {C['text_on_dark']};
}}

#btn_danger {{
    background: {C['delete']};
    color: {C['text_on_dark']};
}}

#btn_secondary {{
    background: {C['ledger']};
    color: #FFFFFF;
}}

#btn_statement {{
    background: {C['clients']};
    color: {C['text_on_dark']};
}}

#statement_action_bar {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 15px;
}}

#statement_print_btn {{
    background: #3F51B5;
    color: #FFFFFF;
    border: 2px solid #303F9F;
    border-radius: 10px;
    min-height: 40px;
    padding: 0 18px;
    font-family: "Font Awesome 6 Free", "Font Awesome 5 Free", {FONT['family']};
    font-weight: 900;
}}
#statement_print_btn:hover {{
    background: #303F9F;
}}
#statement_print_btn:disabled {{
    background: #9FA8DA;
    border-color: #9FA8DA;
}}

#statement_settle_btn {{
    background: #2E7D32;
    color: #FFFFFF;
    border: 2px solid #1B5E20;
    border-radius: 10px;
    min-height: 40px;
    padding: 0 18px;
    font-family: "Font Awesome 6 Free", "Font Awesome 5 Free", {FONT['family']};
    font-weight: 900;
}}
#statement_settle_btn:hover {{
    background: #1B5E20;
}}
#statement_settle_btn:disabled {{
    background: #A5D6A7;
    border-color: #A5D6A7;
}}

#statement_print_status {{
    color: {C['text_secondary']};
    font-size: {FONT['sm']};
    font-weight: bold;
    background: transparent;
    border: none;
}}

#btn_ghost {{
    background: {C['bg_button']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
}}

/* ── Tables (Section Identity Headers) ── */
QTableWidget {{
    background: {C['bg_card']};
    gridline-color: transparent;
    border: none;
    alternate-background-color: {C['bg_alt_row']};
}}
QHeaderView::section {{
    background: {C['accent']};
    color: {C['text_on_dark']};
    padding: 14px 18px;
    font-weight: bold;
    border: none;
}}
QTableWidget::item {{
    padding: 12px 16px;
    border-bottom: 1px solid {C['border_light']};
}}

/* ── Inputs (Thick Border & Focus) ── */
QLineEdit, QTextEdit, QPlainTextEdit, QDoubleSpinBox, QSpinBox, QComboBox, QDateEdit {{
    background: {C['bg_input']};
    color: {C['text_primary']};
    border: 2px solid {C['border']};
    border-radius: 10px;
    padding: 8px 14px;
    min-height: 44px;
}}
QTextEdit, QPlainTextEdit {{
    min-height: 80px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {C['accent']};
}}

QTabWidget::pane {{
    border: none;
    background: transparent;
    margin-top: 12px;
}}
QTabBar::tab {{
    background: {C['bg_button']};
    color: {C['text_secondary']};
    border: 1px solid {C['border']};
    border-radius: 10px;
    padding: 10px 18px;
    margin-left: 6px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    background: {C['accent']};
    color: {C['text_on_dark']};
    border-color: {C['accent']};
}}

#dialog_header {{
    background: {C['accent']};
    border-top-left-radius: 15px;
    border-top-right-radius: 15px;
}}
QLabel#dialogTitleLabel,
QLabel#dialog_title {{
    background-color: transparent;
    color: #FFFFFF;
    font-size: 18px;
    font-weight: bold;
    border: none;
    qproperty-alignment: 'AlignRight | AlignVCenter';
}}
#dialog_close_btn {{
    background: rgba(255, 255, 255, 0.14);
    color: {C['text_on_dark']};
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 16px;
    padding: 0;
}}
#dialog_close_btn:hover {{
    background: rgba(255, 255, 255, 0.24);
}}

/* Scrollbars & Sidebar (kept minimal) */
QScrollBar:vertical {{ background: transparent; width: 6px; }}
QScrollBar::handle:vertical {{ background: {C['border']}; border-radius: 3px; }}
#sidebar {{ background: {C['sidebar_bg']}; border-left: 1px solid {C['sidebar_border']}; }}
#sidebar_brand {{
    color: {C['accent']};
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 12px;
}}
#sidebar_divider {{
    height: 1px;
    background: {C['border']};
    margin: 12px 0;
}}
#nav_btn {{
    text-align: left;
    background: transparent;
    color: {C['text_primary']};
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: {FONT['md']};
}}
#nav_btn:hover {{
    background: {C['bg_hover']};
}}
#nav_btn[active="true"] {{
    background: {C['sidebar_active_bg']};
    color: {C['sidebar_active_color']};
    border: 1px solid {C['accent']};
}}
#nav_btn[active="true"]:hover {{
    background: {C['sidebar_active_bg']};
}}
#theme_toggle_btn {{
    background: {C['bg_button']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 10px;
}}
#theme_toggle_btn:hover {{
    background: {C['bg_hover']};
}}

"""


# Backward-compat: pre-built light stylesheet
MAIN_STYLE: str = build_main_style(LIGHT_COLORS)


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
