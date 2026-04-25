"""
theme.py — Dark Theme with Blue Accent
نظام التصميم الموحد
"""

# ─── Color Palette ──────────────────────────────────────────────────
COLORS = {
    # Backgrounds — layered depth
    "bg_dark":       "#090E16",   # الخلفية الرئيسية (أعمق)
    "bg_card":       "#111827",   # خلفية الكروت
    "bg_elevated":   "#162032",   # عناصر مرتفعة
    "bg_input":      "#1A2540",   # خلفية الحقول
    "bg_hover":      "#1E2D47",   # hover
    "bg_selected":   "#1A3357",   # المحدد

    # Borders
    "border":        "#1E2D47",   # حدود عادية
    "border_light":  "#243352",   # حدود أفتح
    "border_focus":  "#2563EB",   # حدود عند التركيز

    # Blue Accent — richer palette
    "blue_primary":  "#2563EB",
    "blue_light":    "#3B82F6",
    "blue_bright":   "#60A5FA",
    "blue_dark":     "#1D4ED8",
    "blue_subtle":   "#1E3A5F",
    "blue_glow":     "#2563EB30",

    # Text
    "text_primary":  "#F0F6FF",
    "text_secondary":"#8BA3C7",
    "text_muted":    "#3D5275",
    "text_dim":      "#253349",

    # Status
    "green":         "#10B981",
    "green_bg":      "#052E1C",
    "green_border":  "#065F46",
    "red":           "#EF4444",
    "red_bg":        "#2D0A0A",
    "red_border":    "#7F1D1D",
    "yellow":        "#F59E0B",
    "yellow_bg":     "#2D1A00",
    "yellow_border": "#78350F",
    "purple":        "#A78BFA",
    "purple_bg":     "#1E1040",
    "cyan":          "#22D3EE",
    "cyan_bg":       "#061E26",
}

# ─── Spacing & Sizing ───────────────────────────────────────────────
SIDEBAR_WIDTH  = 230
HEADER_HEIGHT  = 56
ROW_HEIGHT     = 44
BTN_HEIGHT     = 38
INPUT_HEIGHT   = 38
BORDER_RADIUS  = "10px"
CARD_RADIUS    = "12px"

# ─── Main Stylesheet ────────────────────────────────────────────────
MAIN_STYLE = f"""

/* ══ Base ══ */
QMainWindow, QWidget, QDialog {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Cairo', 'Tahoma', sans-serif;
    font-size: 13px;
}}

/* ══ Scrollbar ══ */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border_light']};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['blue_primary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['border_light']};
    border-radius: 3px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS['blue_primary']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ══ Sidebar ══ */
#sidebar {{
    background-color: {COLORS['bg_card']};
    border-left: 1px solid {COLORS['border']};
}}

#sidebar_logo {{
    color: {COLORS['blue_bright']};
    font-size: 15px;
    font-weight: bold;
    padding: 4px 0 12px 0;
    letter-spacing: 0.5px;
}}

#sidebar_divider {{
    background: {COLORS['border']};
    max-height: 1px;
    border: none;
    margin: 4px 8px;
}}

/* ══ Nav Buttons ══ */
#nav_btn {{
    background: transparent;
    color: {COLORS['text_secondary']};
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 10px 14px;
    text-align: right;
    font-size: 13px;
    font-weight: normal;
}}
#nav_btn:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}
#nav_btn[active="true"] {{
    background-color: {COLORS['blue_subtle']};
    color: {COLORS['blue_bright']};
    border-right: 2px solid {COLORS['blue_primary']};
    font-weight: bold;
}}

#sidebar_version {{
    color: {COLORS['text_muted']};
    font-size: 10px;
}}

/* ══ Screen Header ══ */
#screen_header {{
    background-color: {COLORS['bg_card']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 0 24px;
    min-height: {HEADER_HEIGHT}px;
    max-height: {HEADER_HEIGHT}px;
}}

#screen_title {{
    color: {COLORS['text_primary']};
    font-size: 16px;
    font-weight: bold;
}}

#screen_subtitle {{
    color: {COLORS['text_muted']};
    font-size: 11px;
}}

/* ══ Cards ══ */
#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
}}
#card:hover {{
    border-color: {COLORS['border_light']};
}}

#card_highlight {{
    background-color: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {CARD_RADIUS};
}}

/* ══ Stat Card ══ */
#stat_card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
}}
#stat_card:hover {{
    border-color: {COLORS['border_light']};
    background-color: {COLORS['bg_elevated']};
}}
#stat_value {{
    font-size: 22px;
    font-weight: bold;
    color: {COLORS['text_primary']};
    letter-spacing: -0.5px;
}}
#stat_label {{
    font-size: 11px;
    color: {COLORS['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
#stat_icon {{
    font-size: 18px;
}}

/* ══ Primary Button ══ */
#btn_primary {{
    background-color: {COLORS['blue_primary']};
    color: white;
    border: none;
    border-radius: {BORDER_RADIUS};
    padding: 0 18px;
    font-size: 13px;
    font-weight: bold;
    min-height: {BTN_HEIGHT}px;
}}
#btn_primary:hover {{
    background-color: {COLORS['blue_light']};
}}
#btn_primary:pressed {{
    background-color: {COLORS['blue_dark']};
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
    font-size: 13px;
    min-height: {BTN_HEIGHT}px;
}}
#btn_secondary:hover {{
    border-color: {COLORS['blue_primary']};
    color: {COLORS['blue_bright']};
    background-color: {COLORS['blue_subtle']};
}}
#btn_secondary:pressed {{
    background-color: {COLORS['bg_selected']};
}}

/* ══ Ghost Button (tiny) ══ */
#btn_ghost {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 12px;
    min-height: 26px;
}}
#btn_ghost:hover {{
    border-color: {COLORS['blue_primary']};
    color: {COLORS['blue_bright']};
}}

/* ══ Danger Button ══ */
#btn_danger {{
    background-color: {COLORS['red_bg']};
    color: {COLORS['red']};
    border: 1px solid {COLORS['red_border']};
    border-radius: {BORDER_RADIUS};
    padding: 0 16px;
    font-size: 13px;
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
    font-size: 13px;
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
    padding: 6px 12px;
    font-size: 13px;
    min-height: {INPUT_HEIGHT}px;
    selection-background-color: {COLORS['blue_primary']};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {COLORS['blue_primary']};
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
    padding: 8px 12px;
}}

/* ══ SpinBox buttons ══ */
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {COLORS['border_light']};
    border: none;
    width: 18px;
    border-radius: 4px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {COLORS['blue_primary']};
}}

/* ══ ComboBox ══ */
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS['text_muted']};
    margin-right: 6px;
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
    padding: 6px 12px;
    min-height: 32px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

/* ══ DateEdit ══ */
QDateEdit::drop-down {{
    border: none;
    width: 22px;
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
    selection-background-color: {COLORS['blue_primary']};
}}

/* ══ Labels ══ */
#label_field {{
    color: {COLORS['text_muted']};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
#label_title {{
    color: {COLORS['text_primary']};
    font-size: 18px;
    font-weight: bold;
    letter-spacing: -0.3px;
}}
#label_subtitle {{
    color: {COLORS['text_secondary']};
    font-size: 12px;
}}
#label_value {{
    color: {COLORS['text_primary']};
    font-size: 13px;
    font-weight: bold;
}}
#label_muted {{
    color: {COLORS['text_muted']};
    font-size: 12px;
}}

/* ══ Table ══ */
QTableWidget {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {CARD_RADIUS};
    gridline-color: transparent;
    font-size: 12px;
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 14px;
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
    color: {COLORS['text_muted']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 8px 14px;
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:first {{
    border-top-right-radius: {CARD_RADIUS};
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
    padding: 10px 18px;
    margin-left: 2px;
    font-size: 12px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    color: {COLORS['blue_bright']};
    border-bottom: 2px solid {COLORS['blue_primary']};
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
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ══ MessageBox ══ */
QMessageBox {{
    background-color: {COLORS['bg_card']};
}}
QMessageBox QLabel {{
    color: {COLORS['text_primary']};
    font-size: 13px;
}}
QMessageBox QPushButton {{
    background-color: {COLORS['blue_primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    min-width: 80px;
    font-weight: bold;
}}
QMessageBox QPushButton:hover {{
    background-color: {COLORS['blue_light']};
}}

/* ══ CheckBox ══ */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 8px;
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    background: {COLORS['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['blue_primary']};
    border-color: {COLORS['blue_primary']};
}}
QCheckBox::indicator:hover {{
    border-color: {COLORS['blue_primary']};
}}

/* ══ RadioButton ══ */
QRadioButton {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    background: {COLORS['bg_input']};
}}
QRadioButton::indicator:checked {{
    background-color: {COLORS['blue_primary']};
    border-color: {COLORS['blue_primary']};
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
}}
QInputDialog QLineEdit, QInputDialog QDoubleSpinBox {{
    min-height: 36px;
}}
QInputDialog QPushButton {{
    background-color: {COLORS['blue_primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 6px 16px;
    font-weight: bold;
}}
QInputDialog QPushButton:hover {{
    background-color: {COLORS['blue_light']};
}}

/* ══ Menu (Context Menu) ══ */
QMenu {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {CARD_RADIUS};
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 12px;
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
        "cash":    f"color: {COLORS['green']}; background: {COLORS['green_bg']}; border: 1px solid {COLORS['green_border']}; border-radius: 5px; padding: 2px 8px; font-size: 11px; font-weight: bold;",
        "pending": f"color: {COLORS['yellow']}; background: {COLORS['yellow_bg']}; border: 1px solid {COLORS['yellow_border']}; border-radius: 5px; padding: 2px 8px; font-size: 11px; font-weight: bold;",
        "paid":    f"color: {COLORS['text_muted']}; background: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; border-radius: 5px; padding: 2px 8px; font-size: 11px;",
    }
    return styles.get(status, "")


def get_status_text(status: str) -> str:
    return {"cash": "نقدي", "pending": "مؤجل", "paid": "مسدد"}.get(status, status)