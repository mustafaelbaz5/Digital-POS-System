"""
theme.py — Design System v2 (Radical Redesign)
===============================================
Key Changes:
- Color: Dark charcoal base (#0D1117) with deep teal accent (#0D9488)
- Typography: Cairo/Tajawal Arabic font, hierarchical scale
- Spacing: 4px base unit system (4, 8, 12, 16, 24, 32, 48)
- Border radius: Larger, more modern (8px default, 16px cards)
- Elevation: 3-level shadow system via QSS backgrounds
- All values defined here — zero inline styles in other files
"""

# ─── Color Palette ──────────────────────────────────────────────────
COLORS = {
    "bg_dark":        "#0D1117",
    "bg_card":        "#161B22",
    "bg_elevated":    "#1C2333",
    "bg_input":       "#212B3A",
    "bg_hover":       "#243040",
    "bg_selected":    "#1A3A4A",
    "border":         "#21262D",
    "border_light":   "#30363D",
    "border_focus":   "#0D9488",
    "teal_primary":   "#0D9488",
    "teal_light":     "#14B8A6",
    "teal_bright":    "#2DD4BF",
    "teal_dark":      "#0F766E",
    "teal_subtle":    "#0D948820",
    "teal_glow":      "#0D948840",
    "emerald":        "#10B981",
    "emerald_bg":     "#052E1C",
    "emerald_border": "#065F46",
    "text_primary":   "#E6EDF3",
    "text_secondary": "#8B949E",
    "text_muted":     "#484F58",
    "text_dim":       "#30363D",
    "green":          "#3FB950",
    "green_bg":       "#0A1F12",
    "green_border":   "#1A4428",
    "red":            "#F85149",
    "red_bg":         "#210B0B",
    "red_border":     "#6E1E1E",
    "yellow":         "#D29922",
    "yellow_bg":      "#221A00",
    "yellow_border":  "#5A4000",
    "blue":           "#58A6FF",
    "blue_bg":        "#0C1B35",
    "blue_border":    "#1A3A6E",
    "purple":         "#BC8CFF",
    "purple_bg":      "#180F2E",
    "cyan":           "#39C5CF",
    "cyan_bg":        "#061E26",
}

FONT = {
    "family": "'Cairo', 'Tajawal', 'Segoe UI', 'Tahoma', sans-serif",
    "xs":   "10px",
    "sm":   "11px",
    "md":   "13px",
    "lg":   "15px",
    "xl":   "18px",
    "2xl":  "22px",
    "3xl":  "28px",
}

SIDEBAR_WIDTH  = 220
HEADER_HEIGHT  = 60
ROW_HEIGHT     = 46
BTN_HEIGHT     = 38
INPUT_HEIGHT   = 40
BORDER_RADIUS  = "8px"
CARD_RADIUS    = "14px"

MAIN_STYLE = f"""

/* ══ Base ══ */
QMainWindow, QWidget, QDialog {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: {FONT['family']};
    font-size: {FONT['md']};
}}

/* ══ Scrollbar ══ */
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border_light']};
    border-radius: 3px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['teal_primary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['border_light']};
    border-radius: 3px;
    min-width: 32px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS['teal_primary']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ══ Sidebar ══ */
#sidebar {{
    border-left: 1px solid {COLORS['border']};
}}
#sidebar_brand {{
    color: {COLORS['text_primary']};
    font-size: {FONT['lg']};
    text-align: center;
    font-weight: bold;
    padding: 0 4px;
    font-family: {FONT['family']};
}}

#sidebar_divider {{
    background: {COLORS['border']};
    max-height: 1px;
    border: none;
    margin: 0 12px;
}}

/* ══ Nav Buttons ══ */
#nav_btn {{
    background: transparent;
    color: {COLORS['text_secondary']};
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 10px 14px;
    text-align: left;
    font-size: {FONT['md']};
    font-weight: normal;
    font-family: {FONT['family']};
}}
#nav_btn:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}
#nav_btn[active="true"] {{
    background-color: {COLORS['teal_subtle']};
    color: {COLORS['teal_bright']};
    font-weight: bold;
    border: 1px solid {COLORS['teal_dark']};
}}
#sidebar_version {{
    color: {COLORS['text_muted']};
    font-size: {FONT['xs']};
    font-family: {FONT['family']};
}}

/* ══ Screen Header ══ */
#screen_header {{
    background-color: {COLORS['bg_card']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 0 28px;
    min-height: {HEADER_HEIGHT}px;
    max-height: {HEADER_HEIGHT}px;
}}
#screen_title {{
    color: {COLORS['text_primary']};
    font-size: {FONT['xl']};
    font-weight: bold;
    font-family: {FONT['family']};
}}
#screen_subtitle {{
    color: {COLORS['text_muted']};
    font-size: {FONT['sm']};
    font-family: {FONT['family']};
}}

/* ══ Cards ══ */
#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
}}
#card:hover {{
    border-color: {COLORS['border_light']};
    background-color: {COLORS['bg_elevated']};
}}
#card_highlight {{
    background-color: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['teal_primary']};
    border-radius: {CARD_RADIUS};
}}
#card_hero {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['teal_dark']};
    border-radius: {CARD_RADIUS};
}}

/* ══ Stat Cards ══ */
#stat_card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
}}
#stat_card:hover {{
    border-color: {COLORS['teal_primary']};
    background-color: {COLORS['bg_elevated']};
}}
#stat_value {{
    font-size: {FONT['2xl']};
    font-weight: bold;
    color: {COLORS['text_primary']};
    font-family: {FONT['family']};
}}
#stat_label {{
    font-size: {FONT['lg']};
    color: {COLORS['text_primary']};
    font-family: {FONT['family']};
}}
#section_label {{
    color: {COLORS['text_secondary']};
    font-size: {FONT['sm']};
    font-weight: bold;
    font-family: {FONT['family']};
    letter-spacing: 0.5px;
}}

/* ══ Primary Button ══ */
#btn_primary {{
    background-color: {COLORS['teal_primary']};
    color: white;
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 0 20px;
    font-size: {FONT['md']};
    font-weight: bold;
    font-family: {FONT['family']};
    min-height: {BTN_HEIGHT}px;
}}
#btn_primary:hover {{
    background-color: {COLORS['teal_light']};
}}
#btn_primary:pressed {{
    background-color: {COLORS['teal_dark']};
}}
#btn_primary:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}

/* ══ Secondary Button ══ */
#btn_secondary {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {BORDER_RADIUS};
    padding: 0 16px;
    font-size: {FONT['md']};
    font-family: {FONT['family']};
    min-height: {BTN_HEIGHT}px;
}}
#btn_secondary:hover {{
    border-color: {COLORS['teal_primary']};
    color: {COLORS['teal_bright']};
    background-color: {COLORS['teal_subtle']};
}}
#btn_secondary:pressed {{
    background-color: {COLORS['bg_selected']};
}}

/* ══ Ghost Button ══ */
#btn_ghost {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 2px 12px;
    font-size: {FONT['sm']};
    font-family: {FONT['family']};
    min-height: 28px;
}}
#btn_ghost:hover {{
    border-color: {COLORS['teal_primary']};
    color: {COLORS['teal_bright']};
    background-color: {COLORS['teal_subtle']};
}}

/* ══ Danger Button ══ */
#btn_danger {{
    background-color: {COLORS['red_bg']};
    color: {COLORS['red']};
    border: 1px solid {COLORS['red_border']};
    border-radius: {BORDER_RADIUS};
    padding: 0 16px;
    font-family: {FONT['family']};
    min-height: {BTN_HEIGHT}px;
}}
#btn_danger:hover {{
    background-color: {COLORS['red']};
    color: white;
    border-color: {COLORS['red']};
}}

/* ══ Success Button ══ */
#btn_success {{
    background-color: {COLORS['green_bg']};
    color: {COLORS['green']};
    border: 1px solid {COLORS['green_border']};
    border-radius: {BORDER_RADIUS};
    padding: 0 16px;
    font-family: {FONT['family']};
    min-height: {BTN_HEIGHT}px;
}}
#btn_success:hover {{
    background-color: {COLORS['green']};
    color: white;
    border-color: {COLORS['green']};
}}

/* ══ Input Fields ══ */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {BORDER_RADIUS};
    padding: 6px 14px;
    font-size: {FONT['md']};
    font-family: {FONT['family']};
    min-height: {INPUT_HEIGHT}px;
    selection-background-color: {COLORS['teal_primary']};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {COLORS['teal_primary']};
    background-color: {COLORS['bg_elevated']};
    outline: none;
}}
QLineEdit::placeholder {{
    color: {COLORS['text_dim']};
}}
QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}
QTextEdit {{
    min-height: unset;
    padding: 10px 14px;
}}

/* ══ SpinBox ══ */
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {COLORS['border_light']};
    border: none;
    width: 20px;
    border-radius: 4px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {COLORS['teal_primary']};
}}

/* ══ ComboBox ══ */
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS['text_muted']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {BORDER_RADIUS};
    selection-background-color: {COLORS['bg_selected']};
    padding: 4px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 8px 14px;
    min-height: 34px;
    font-family: {FONT['family']};
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

/* ══ DateEdit ══ */
QDateEdit::drop-down {{
    border: none;
    width: 24px;
}}
QCalendarWidget {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {CARD_RADIUS};
}}
QCalendarWidget QToolButton {{
    background: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
}}
QCalendarWidget QAbstractItemView {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['teal_primary']};
}}

/* ══ Labels ══ */
#label_field {{
    color: {COLORS['text_secondary']};
    font-size: {FONT['sm']};
    font-weight: bold;
    font-family: {FONT['family']};
    letter-spacing: 0.3px;
}}
#label_title {{
    color: {COLORS['text_primary']};
    font-size: {FONT['xl']};
    font-weight: bold;
    font-family: {FONT['family']};
}}
#label_subtitle {{
    color: {COLORS['text_secondary']};
    font-size: {FONT['sm']};
    font-family: {FONT['family']};
}}
#label_value {{
    color: {COLORS['text_primary']};
    font-size: {FONT['md']};
    font-weight: bold;
    font-family: {FONT['family']};
}}
#label_muted {{
    color: {COLORS['text_muted']};
    font-size: {FONT['sm']};
    font-family: {FONT['family']};
}}

/* ══ Table ══ */
QTableWidget {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
    gridline-color: transparent;
    font-size: {FONT['md']};
    font-family: {FONT['family']};
    outline: none;
}}
QTableWidget::item {{
    padding: 10px 16px;
    border-bottom: 1px solid {COLORS['border']};
}}
QTableWidget::item:selected {{
    background-color: {COLORS['bg_selected']};
    color: {COLORS['text_primary']};
}}
QTableWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
}}
QHeaderView::section {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    border: none;
    border-bottom: 1px solid {COLORS['border_light']};
    padding: 10px 16px;
    font-weight: bold;
    font-size: {FONT['sm']};
    font-family: {FONT['family']};
    letter-spacing: 0.3px;
}}
QHeaderView::section:first {{
    border-top-right-radius: {CARD_RADIUS};
}}
QHeaderView::section:last {{
    border-top-left-radius: {CARD_RADIUS};
}}

/* ══ Tab Widget ══ */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
    background: {COLORS['bg_card']};
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
    font-family: {FONT['family']};
}}
QTabBar::tab:selected {{
    color: {COLORS['teal_bright']};
    border-bottom: 2px solid {COLORS['teal_primary']};
}}
QTabBar::tab:hover:!selected {{
    color: {COLORS['text_secondary']};
    border-bottom: 2px solid {COLORS['border_light']};
}}
QTabWidget::tab-bar {{
    background: {COLORS['bg_dark']};
    border-bottom: 1px solid {COLORS['border']};
}}

/* ══ Separator ══ */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    background-color: {COLORS['border']};
    max-height: 1px;
    border: none;
}}

/* ══ ToolTip ══ */
QToolTip {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: {FONT['sm']};
    font-family: {FONT['family']};
}}

/* ══ MessageBox ══ */
QMessageBox {{
    background-color: {COLORS['bg_card']};
}}
QMessageBox QLabel {{
    color: {COLORS['text_primary']};
    font-size: {FONT['md']};
    font-family: {FONT['family']};
}}
QMessageBox QPushButton {{
    background-color: {COLORS['teal_primary']};
    color: white;
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 8px 24px;
    min-width: 90px;
    font-weight: bold;
    font-family: {FONT['family']};
}}
QMessageBox QPushButton:hover {{
    background-color: {COLORS['teal_light']};
}}

/* ══ CheckBox ══ */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 8px;
    font-size: {FONT['md']};
    font-family: {FONT['family']};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_light']};
    border-radius: 5px;
    background: {COLORS['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['teal_primary']};
    border-color: {COLORS['teal_primary']};
}}
QCheckBox::indicator:hover {{
    border-color: {COLORS['teal_primary']};
}}

/* ══ RadioButton ══ */
QRadioButton {{
    color: {COLORS['text_primary']};
    spacing: 8px;
    font-family: {FONT['family']};
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_light']};
    border-radius: 9px;
    background: {COLORS['bg_input']};
}}
QRadioButton::indicator:checked {{
    background-color: {COLORS['teal_primary']};
    border-color: {COLORS['teal_primary']};
}}

/* ══ Splitter ══ */
QSplitter::handle {{
    background-color: {COLORS['border']};
    width: 1px;
}}

/* ══ InputDialog ══ */
QInputDialog {{
    background-color: {COLORS['bg_card']};
}}
QInputDialog QLabel {{
    color: {COLORS['text_primary']};
    font-family: {FONT['family']};
}}
QInputDialog QLineEdit, QInputDialog QDoubleSpinBox {{
    min-height: 38px;
}}
QInputDialog QPushButton {{
    background-color: {COLORS['teal_primary']};
    color: white;
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 6px 20px;
    font-weight: bold;
    font-family: {FONT['family']};
}}
QInputDialog QPushButton:hover {{
    background-color: {COLORS['teal_light']};
}}

/* ══ Menu ══ */
QMenu {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {CARD_RADIUS};
    padding: 6px;
    font-family: {FONT['family']};
}}
QMenu::item {{
    padding: 8px 18px;
    border-radius: 6px;
    font-size: {FONT['md']};
}}
QMenu::item:selected {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}
QMenu::separator {{
    height: 1px;
    background: {COLORS['border']};
    margin: 4px 8px;
}}

/* ══ Scroll Area ══ */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
"""


def get_status_style(status: str) -> str:
    styles = {
        "cash":    f"color: {COLORS['green']}; background: {COLORS['green_bg']}; border: 1px solid {COLORS['green_border']}; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: bold; font-family: {FONT['family']};",
        "pending": f"color: {COLORS['yellow']}; background: {COLORS['yellow_bg']}; border: 1px solid {COLORS['yellow_border']}; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: bold; font-family: {FONT['family']};",
        "paid":    f"color: {COLORS['text_muted']}; background: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-family: {FONT['family']};",
    }
    return styles.get(status, "")


def get_status_text(status: str) -> str:
    return {"cash": "نقدي", "pending": "مؤجل", "paid": "مسدد"}.get(status, status)
