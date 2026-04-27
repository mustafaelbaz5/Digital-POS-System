# ──────────────────────────────────────────────────
# COLOR SYSTEM — CLEANER PROFESSIONAL DARK
# ──────────────────────────────────────────────────

COLORS = {

    # ─────────────────────────────────────────
    # SURFACES
    # More separation between layers
    # ─────────────────────────────────────────

    "bg_dark":      "#0B0F14",   # app background
    "bg_card":      "#121821",   # cards/sidebar
    "bg_elevated":  "#1A2330",   # hover/input/popup

    # interactive
    "bg_input":     "#1A2330",
    "bg_hover":     "#222D3D",

    # ─────────────────────────────────────────
    # BORDERS
    # softer + cleaner
    # ─────────────────────────────────────────

    "border":       "#263041",
    "border_light": "#313D4F",

    # ─────────────────────────────────────────
    # ACCENT
    # modern enterprise blue
    # ─────────────────────────────────────────

    "accent":       "#5B8CFF",
    "accent_hover": "#78A3FF",
    "accent_dim":   "#1A2A4A",

    # ─────────────────────────────────────────
    # TYPOGRAPHY
    # improved readability
    # ─────────────────────────────────────────

    "text_primary":   "#F4F7FB",
    "text_secondary": "#A8B3C2",
    "text_muted":     "#667085",

    # ─────────────────────────────────────────
    # SEMANTIC
    # muted professional tones
    # ─────────────────────────────────────────

    "green":         "#32C766",
    "green_bg":      "#102117",
    "green_border":  "#1F5132",

    "red":           "#FF6B6B",
    "red_bg":        "#2B1416",
    "red_border":    "#5C2529",

    "yellow":        "#E6B450",
    "yellow_bg":     "#2A2110",
    "yellow_border": "#5A4620",

    # ─────────────────────────────────────────
    # COMPATIBILITY ALIASES
    # keep old screens working
    # ─────────────────────────────────────────

    "teal_primary": "#5B8CFF",
    "teal_light":   "#78A3FF",
    "teal_bright":  "#A8C5FF",
    "teal_dark":    "#3E6FE0",
    "teal_subtle":  "#1A2A4A",
    "teal_glow":    "#1A2A4A",

    "blue":         "#5B8CFF",
    "blue_bg":      "#1A2A4A",
    "blue_border":  "#3E6FE0",

    "purple":       "#A78BFA",
    "purple_bg":    "#1A2330",

    "cyan":         "#4DD4E0",
    "cyan_bg":      "#1A2330",

    "emerald":         "#32C766",
    "emerald_bg":      "#102117",
    "emerald_border":  "#1F5132",

    "bg_selected":  "#1A2A4A",
    "border_focus": "#5B8CFF",
    "text_dim":     "#667085",
}

# ──────────────────────────────────────────────────
# TYPOGRAPHY
# ──────────────────────────────────────────────────

FONT = {
    "family": "'Cairo', 'Tajawal', 'Segoe UI', sans-serif",
    "xs":  "10px",
    "sm":  "12px",
    "md":  "14px",
    "lg":  "16px",
    "xl":  "20px",
    "2xl": "26px",
    "3xl": "32px",
}


# ──────────────────────────────────────────────────
# LAYOUT CONSTANTS
# ──────────────────────────────────────────────────

SIDEBAR_WIDTH  = 230
HEADER_HEIGHT  = 60
ROW_HEIGHT     = 48
BTN_HEIGHT     = 38
INPUT_HEIGHT   = 40
BORDER_RADIUS  = "8px"
CARD_RADIUS    = "12px"


# ──────────────────────────────────────────────────
# MAIN STYLESHEET
# ──────────────────────────────────────────────────

MAIN_STYLE = f"""

/* ── Base ── */
QMainWindow, QWidget, QDialog {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    font-family: {FONT['family']};
    font-size: {FONT['md']};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border_light']};
    border-radius: 3px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent']};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['border_light']};
    border-radius: 3px;
    min-width: 32px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS['accent']};
}}

/* ── Sidebar ── */
#sidebar {{
    background: {COLORS['bg_card']};
    border-left: 1px solid {COLORS['border']};
}}

#sidebar_brand {{
    color: {COLORS['text_primary']};
    font-size: {FONT['lg']};
    font-weight: bold;
    padding: 0 8px;
}}

#sidebar_divider {{
    background: {COLORS['border']};
    max-height: 1px;
    border: none;
    margin: 2px 12px;
}}

#sidebar_version {{
    color: {COLORS['text_muted']};
    font-size: {FONT['xs']};
}}

/* ── Navigation ── */
#nav_btn {{
    background: transparent;
    color: {COLORS['text_secondary']};
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 10px 14px;
    text-align: left;
    font-size: {FONT['md']};
}}
#nav_btn:hover {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
}}
#nav_btn[active="true"] {{
    background: {COLORS['accent_dim']};
    color: {COLORS['accent']};
    font-weight: bold;
}}

/* ── Screen Header ── */
#screen_header {{
    background: {COLORS['bg_card']};
    border-bottom: 1px solid {COLORS['border']};
    min-height: {HEADER_HEIGHT}px;
    max-height: {HEADER_HEIGHT}px;
}}
#screen_title {{
    color: {COLORS['text_primary']};
    font-size: {FONT['lg']};
    font-weight: bold;
}}
#screen_subtitle {{
    color: {COLORS['text_muted']};
    font-size: {FONT['sm']};
}}

/* ── Cards ── */
#card {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
}}
#card:hover {{
    border-color: {COLORS['border_light']};
    background: {COLORS['bg_elevated']};
}}

#stat_card {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
}}
#stat_card:hover {{
    border-color: {COLORS['border_light']};
}}

#card_highlight {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['accent_dim']};
    border-radius: {CARD_RADIUS};
}}

#card_hero {{
    background: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {CARD_RADIUS};
}}

#stat_value {{
    color: {COLORS['text_primary']};
    font-size: {FONT['2xl']};
    font-weight: bold;
}}
#stat_label {{
    color: {COLORS['text_secondary']};
    font-size: {FONT['sm']};
}}
#label_title {{
    color: {COLORS['text_primary']};
    font-size: {FONT['md']};
    font-weight: bold;
}}
#label_subtitle {{
    color: {COLORS['text_muted']};
    font-size: {FONT['sm']};
}}
#label_muted {{
    color: {COLORS['text_secondary']};
    font-size: {FONT['sm']};
}}
#label_value {{
    color: {COLORS['text_primary']};
    font-size: {FONT['md']};
    font-weight: bold;
}}
#section_label {{
    color: {COLORS['text_muted']};
    font-size: {FONT['xs']};
    font-weight: bold;
    letter-spacing: 0.8px;
}}

/* ── Buttons ── */
#btn_primary {{
    background: {COLORS['accent']};
    color: #ffffff;
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 0 18px;
    min-height: {BTN_HEIGHT}px;
    font-weight: bold;
    font-size: {FONT['md']};
}}
#btn_primary:hover {{ background: {COLORS['accent_hover']}; }}
#btn_primary:pressed {{ background: {COLORS['teal_dark']}; }}
#btn_primary:disabled {{
    background: {COLORS['border']};
    color: {COLORS['text_muted']};
}}

#btn_secondary {{
    background: transparent;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {BORDER_RADIUS};
    padding: 0 16px;
    min-height: {BTN_HEIGHT}px;
    font-size: {FONT['md']};
}}
#btn_secondary:hover {{
    background: {COLORS['bg_elevated']};
    border-color: {COLORS['accent']};
    color: {COLORS['text_primary']};
}}

#btn_ghost {{
    background: transparent;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 3px 10px;
    min-height: 28px;
    font-size: {FONT['sm']};
}}
#btn_ghost:hover {{
    background: {COLORS['bg_elevated']};
    border-color: {COLORS['border_light']};
    color: {COLORS['text_primary']};
}}

#btn_danger {{
    background: transparent;
    color: {COLORS['red']};
    border: 1px solid {COLORS['red_border']};
    border-radius: {BORDER_RADIUS};
    min-height: {BTN_HEIGHT}px;
    padding: 0 16px;
}}
#btn_danger:hover {{
    background: {COLORS['red_bg']};
}}

#btn_success {{
    background: transparent;
    color: {COLORS['green']};
    border: 1px solid {COLORS['green_border']};
    border-radius: {BORDER_RADIUS};
    min-height: {BTN_HEIGHT}px;
    padding: 0 16px;
}}
#btn_success:hover {{
    background: {COLORS['green_bg']};
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
QComboBox, QDateEdit {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS};
    padding: 6px 12px;
    min-height: {INPUT_HEIGHT}px;
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {COLORS['accent']};
    background: {COLORS['bg_input']};
}}
QLineEdit::placeholder {{ color: {COLORS['text_muted']}; }}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {BORDER_RADIUS};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent_dim']};
    selection-color: {COLORS['accent']};
    padding: 4px;
}}

/* ── Table ── */
QTableWidget {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
    gridline-color: transparent;
    outline: none;
}}
QTableWidget::item {{
    padding: 10px 14px;
    border-bottom: 1px solid {COLORS['border']};
}}
QTableWidget::item:hover {{
    background: {COLORS['bg_elevated']};
}}
QTableWidget::item:selected {{
    background: {COLORS['accent_dim']};
    color: {COLORS['text_primary']};
}}
QHeaderView::section {{
    background: {COLORS['bg_dark']};
    color: {COLORS['text_muted']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 10px 14px;
    font-size: {FONT['xs']};
    font-weight: bold;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
QHeaderView::section:first {{ border-top-right-radius: {CARD_RADIUS}; }}
QHeaderView::section:last  {{ border-top-left-radius: {CARD_RADIUS}; }}

/* ── Tabs ── */
QTabWidget::pane {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {COLORS['text_muted']};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 20px;
    margin-right: 2px;
    font-size: {FONT['sm']};
    font-weight: bold;
}}
QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom-color: {COLORS['accent']};
}}
QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
}}

/* ── Dialogs & Popups ── */
QDialog {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {CARD_RADIUS};
}}

QToolTip {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: {FONT['sm']};
}}

QMenu {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 16px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}
QMenu::separator {{
    height: 1px;
    background: {COLORS['border']};
    margin: 4px 8px;
}}

QMessageBox {{
    background: {COLORS['bg_card']};
}}
QMessageBox QPushButton {{
    min-width: 80px;
    min-height: 32px;
    border-radius: {BORDER_RADIUS};
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    padding: 0 14px;
}}
QMessageBox QPushButton:hover {{
    background: {COLORS['accent']};
    border-color: {COLORS['accent']};
    color: white;
}}

QInputDialog {{
    background: {COLORS['bg_card']};
}}

"""


# ──────────────────────────────────────────────────
# STATUS HELPERS
# ──────────────────────────────────────────────────

def get_status_style(status: str) -> str:
    base = f"border-radius: 5px; padding: 2px 10px; font-size: 11px; font-weight: bold; font-family: {FONT['family']};"
    styles = {
        "cash":    f"color: {COLORS['green']}; background: {COLORS['green_bg']}; border: 1px solid {COLORS['green_border']}; {base}",
        "pending": f"color: {COLORS['yellow']}; background: {COLORS['yellow_bg']}; border: 1px solid {COLORS['yellow_border']}; {base}",
        "paid":    f"color: {COLORS['text_muted']}; background: {COLORS['bg_elevated']}; border: 1px solid {COLORS['border']}; {base}",
    }
    return styles.get(status, "")


def get_status_text(status: str) -> str:
    return {"cash": "نقدي ✓", "pending": "مؤجل", "paid": "مسدد ✓"}.get(status, status)
