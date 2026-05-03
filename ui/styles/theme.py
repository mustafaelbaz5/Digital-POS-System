# ──────────────────────────────────────────────────
# COLOR SYSTEM — PRO DARK AESTHETIC
# ──────────────────────────────────────────────────

COLORS = {

    # ─────────────────────────────────────────
    # SURFACES
    # Deep, GitHub-inspired charcoal/gray tones
    # ─────────────────────────────────────────

    "bg_dark":      "#0D1117",   # main app background
    "bg_card":      "#0D1117",   # cards/sidebar/containers
    "bg_elevated":  "#161B22",   # elevated surfaces (lighter than bg_dark)

    "bg_input":     "#090C10",   # inputs (darker for depth)
    "bg_hover":     "#21262D",
    "bg_button":    "#21262D",   # distinct button background

    # ─────────────────────────────────────────
    # BORDERS
    # Subtle separation
    # ─────────────────────────────────────────

    "border":       "#30363D",
    "border_light": "#424B57",

    # ─────────────────────────────────────────
    # ACCENT
    # Modern Dark Green (Professional and clear for confirmations)
    # ─────────────────────────────────────────

    "accent":       "#059669",   # Darker Emerald
    "accent_hover": "#10B981",   # Vibrant Emerald on hover
    "accent_dim":   "#064E3B",   # Very dark green

    # ─────────────────────────────────────────
    # TYPOGRAPHY
    # Optimized for readability on dark backgrounds
    # ─────────────────────────────────────────

    "text_primary":   "#E6EDF3",   # High contrast
    "text_secondary": "#8B949E",   # Soft contrast
    "text_muted":     "#484F58",   # Low contrast

    # ─────────────────────────────────────────
    # SEMANTIC
    # Unified with accent and industry standards
    # ─────────────────────────────────────────

    "green":         "#10B981",
    "green_bg":      "#064E3B20",
    "green_border":  "#064E3B",

    "red":           "#F85149",
    "red_bg":        "#490E0E20",
    "red_border":    "#490E0E",

    "yellow":        "#D29922",
    "yellow_bg":     "#35210020",
    "yellow_border": "#352100",

    # ─────────────────────────────────────────
    # COMPATIBILITY ALIASES
    # Supporting existing components
    # ─────────────────────────────────────────

    "teal_primary": "#10B981",
    "teal_light":   "#34D399",
    "teal_bright":  "#6EE7B7",
    "teal_dark":    "#059669",
    "teal_subtle":  "#064E3B",
    "teal_glow":    "#064E3B",

    "blue":         "#58A6FF",
    "blue_bg":      "#0C2D6B20",
    "blue_border":  "#0C2D6B",

    "purple":       "#BC8CFF",
    "purple_bg":    "#3B256B20",

    "cyan":         "#39C5BB",
    "cyan_bg":      "#1A3B3920",

    "emerald":         "#10B981",
    "emerald_bg":      "#064E3B20",
    "emerald_border":  "#064E3B",

    "bg_selected":  "#161B22",
    "border_focus": "#10B981",
    "text_dim":     "#484F58",
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

SIDEBAR_WIDTH  = 240
HEADER_HEIGHT  = 70
ROW_HEIGHT     = 60
BTN_HEIGHT     = 42
INPUT_HEIGHT   = 44
BORDER_RADIUS  = "10px"
CARD_RADIUS    = "14px"

# Standard Spacing (Gaps)
GAP_XS = 4
GAP_SM = 8
GAP_MD = 16
GAP_LG = 24
GAP_XL = 32

# Standard Margins
MARGIN_CONTENT = 20
MARGIN_CARD    = 20


# ──────────────────────────────────────────────────
# MAIN STYLESHEET
# ──────────────────────────────────────────────────

MAIN_STYLE = f"""

/* ── Base ── */
QMainWindow, QWidget, QDialog {{
    background: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
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
    background: {COLORS['border']};
    border-radius: 3px;
    min-height: 40px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
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
    background: {COLORS['border']};
    border-radius: 3px;
    min-width: 40px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['border']};
    border-radius: 3px;
    min-width: 40px;
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
    padding: 0 10px;
}}

#sidebar_divider {{
    background: {COLORS['border']};
    max-height: 1px;
    border: none;
    margin: {GAP_SM}px {GAP_MD}px;
}}

/* ── Navigation ── */
#nav_btn {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS};
    padding: 12px 18px;
    text-align: left;
    font-size: {FONT['md']};
    margin: 2px 8px;
}}
#nav_btn[active="true"] {{
    background: {COLORS['accent_dim']};
    color: {COLORS['accent']};
    font-weight: bold;
    border: 1px solid {COLORS['accent']};
    border-right: 4px solid {COLORS['accent']};
}}

/* ── Screen Header ── */
#screen_header {{
    background: {COLORS['bg_dark']};
    border-bottom: 1px solid {COLORS['border']};
    min-height: {HEADER_HEIGHT}px;
    max-height: {HEADER_HEIGHT}px;
}}
#screen_title {{
    color: {COLORS['text_primary']};
    font-size: {FONT['xl']};
    font-weight: bold;
}}
#screen_subtitle {{
    color: {COLORS['text_secondary']};
    font-size: {FONT['sm']};
}}

/* ── Cards ── */
#card {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
}}

#stat_card {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
}}

#card_highlight {{
    background: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['accent_dim']};
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

/* ── Buttons ── */
QPushButton {{
    font-family: {FONT['family']};
    border-radius: {BORDER_RADIUS};
    padding: 8px 16px;
    border: 1px solid transparent; /* Defined in specific IDs */
}}

#btn_primary {{
    background: {COLORS['accent']};
    color: #ffffff;
    border: 1px solid {COLORS['accent_hover']};
    border-radius: {BORDER_RADIUS};
    padding: 0 24px;
    min-height: {BTN_HEIGHT}px;
    font-weight: bold;
    font-size: {FONT['md']};
}}
#btn_primary:hover {{
    background: {COLORS['accent_hover']};
}}
#btn_primary:pressed {{
    background: {COLORS['accent_dim']};
}}
#btn_primary:disabled {{
    background: {COLORS['border']};
    color: {COLORS['text_muted']};
    border: none;
}}

#btn_secondary {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS};
    padding: 0 20px;
    min-height: {BTN_HEIGHT}px;
    font-size: {FONT['md']};
}}
#btn_secondary:hover {{
    background: {COLORS['bg_hover']};
    border-color: {COLORS['border_light']};
}}
#btn_secondary:pressed {{
    background: {COLORS['bg_dark']};
}}

#btn_ghost {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px 12px;
    font-size: {FONT['sm']};
}}
#btn_ghost:hover {{
    background: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}

#btn_danger {{
    background: {COLORS['red_bg']};
    color: {COLORS['red']};
    border: 1px solid {COLORS['red_border']};
    border-radius: {BORDER_RADIUS};
    min-height: {BTN_HEIGHT}px;
    font-weight: bold;
}}

#btn_statement {{
    background: #0969DA; /* Professional Blue */
    color: #ffffff;
    border: 1px solid #0969DA;
    border-radius: 6px;
    font-weight: bold;
    font-size: {FONT['sm']};
}}
#btn_statement:hover {{
    background: #0550AE;
    border-color: #0550AE;
}}
#btn_statement:pressed {{
    background: #0A3069;
}}

/* ── In-Table Buttons (Static & Highlighted) ── */
QTableWidget QPushButton,
QTableWidget #btn_ghost, QTableWidget #btn_ghost:hover, QTableWidget #btn_ghost:pressed,
QTableWidget #btn_primary, QTableWidget #btn_primary:hover, QTableWidget #btn_primary:pressed,
QTableWidget #btn_secondary, QTableWidget #btn_secondary:hover, QTableWidget #btn_secondary:pressed,
QTableWidget #btn_statement, QTableWidget #btn_statement:hover, QTableWidget #btn_statement:pressed {{
    border: 2px solid {COLORS['accent']};
    border-radius: 6px;
    padding: 5px 10px;
    background-color: {COLORS['green_bg']};
    color: {COLORS['text_primary']};
    font-weight: bold;
    font-size: {FONT['sm']};
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
QComboBox, QDateEdit {{
    background: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS};
    padding: 8px 14px;
    min-height: {INPUT_HEIGHT}px;
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {COLORS['accent']};
}}

QComboBox::drop-down {{
    background: {COLORS['bg_hover']};
    border-left: 1px solid {COLORS['border']};
    width: 32px;
    border-top-right-radius: {BORDER_RADIUS};
    border-bottom-right-radius: {BORDER_RADIUS};
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
    margin-top: 2px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {BORDER_RADIUS};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['bg_hover']};
    selection-color: {COLORS['accent']};
    outline: none;
    padding: 4px;
}}

/* ── Table ── */
QTableWidget {{
    background: {COLORS['bg_dark']};
    border: none;
    border-radius: {CARD_RADIUS};
    gridline-color: transparent;
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 20px;
    border-bottom: 1px solid {COLORS['border']};
}}
QTableWidget::item:selected {{
    background: {COLORS['bg_hover']};
    color: {COLORS['accent']};
}}
QHeaderView {{
    background: {COLORS['bg_elevated']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
}}
QHeaderView::section {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_secondary']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
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
    color: {COLORS['text_secondary']};
    padding: 12px 24px;
    font-weight: bold;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom: 2px solid {COLORS['accent']};
}}

/* ── Dialogs ── */
QDialog {{
    background: {COLORS['bg_dark']};
    border: 1px solid {COLORS['border']};
}}

#dialog_header {{
    background: {COLORS['bg_elevated']};
    border-bottom: 1px solid {COLORS['border']};
    min-height: 50px;
}}

#dialog_title {{
    color: {COLORS['text_primary']};
    font-size: {FONT['lg']};
    font-weight: bold;
}}

#dialog_close_btn {{
    background: transparent;
    color: {COLORS['text_secondary']};
    border: none;
    font-size: 14px;
    font-weight: bold;
    border-radius: 15px;
    padding: 0;
    margin: 0;
}}

QMessageBox {{
    background: {COLORS['bg_dark']};
}}
QMessageBox QLabel {{
    color: {COLORS['text_primary']};
    font-size: {FONT['md']};
}}
QMessageBox QPushButton {{
    min-width: 100px;
    min-height: 36px;
}}

QMenu {{
    background: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 10px;
    padding: 5px;
}}
QMenu::item {{
    padding: 10px 20px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: {COLORS['bg_hover']};
    color: {COLORS['accent']};
}}

"""


# ──────────────────────────────────────────────────
# STATUS HELPERS
# ──────────────────────────────────────────────────

def get_status_style(status: str) -> str:
    base = f"border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: bold;"
    styles = {
        "pending": f"color: {COLORS['yellow']}; background: {COLORS['yellow_bg']}; border: 1px solid {COLORS['yellow_border']}; {base}",
        "paid":    f"color: {COLORS['green']}; background: {COLORS['green_bg']}; border: 1px solid {COLORS['green_border']}; {base}",
    }
    return styles.get(status, "")


def get_status_text(status: str) -> str:
    return {"pending": "مؤجل ⏳", "paid": "تم السداد ✓"}.get(status, status)
