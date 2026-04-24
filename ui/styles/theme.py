"""
Theme & Global Styles
الثيم الداكن مع اللون الأزرق
"""

# ─── Color Palette ─────────────────────────────────────────────────
COLORS = {
    # Backgrounds
    "bg_dark":       "#0D1117",   # الخلفية الرئيسية
    "bg_card":       "#161B22",   # خلفية الكروت
    "bg_input":      "#1C2128",   # خلفية الحقول
    "bg_hover":      "#21262D",   # hover
    "bg_selected":   "#1F3A5F",   # المحدد

    # Borders
    "border":        "#30363D",   # حدود عادية
    "border_focus":  "#1F6FEB",   # حدود عند التركيز

    # Blue Accent
    "blue_primary":  "#1F6FEB",   # الأزرق الرئيسي
    "blue_light":    "#388BFD",   # أزرق فاتح
    "blue_dark":     "#0D4F9E",   # أزرق داكن
    "blue_glow":     "#1F6FEB40", # أزرق شفاف للـ glow

    # Text
    "text_primary":  "#E6EDF3",   # النص الرئيسي
    "text_secondary":"#8B949E",   # النص الثانوي
    "text_muted":    "#484F58",   # نص خافت

    # Status Colors
    "green":         "#3FB950",   # إيجابي / نقدي
    "green_bg":      "#1A3A2A",
    "red":           "#F85149",   # سالب / خطأ
    "red_bg":        "#3A1A1A",
    "yellow":        "#D29922",   # تحذير / مؤجل
    "yellow_bg":     "#3A2A0A",
    "purple":        "#BC8CFF",   # معلومات إضافية
}

# ─── Main Stylesheet ────────────────────────────────────────────────
MAIN_STYLE = f"""
/* ══ القاعدة ══ */
QMainWindow, QWidget, QDialog {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Cairo', 'Tahoma', sans-serif;
    font-size: 14px;
}}

/* ══ Scrollbar ══ */
QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['blue_primary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: {COLORS['bg_dark']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['border']};
    border-radius: 4px;
}}

/* ══ Sidebar ══ */
#sidebar {{
    background-color: {COLORS['bg_card']};
    border-left: 1px solid {COLORS['border']};
    min-width: 220px;
    max-width: 220px;
}}

/* ══ Nav Buttons ══ */
#nav_btn {{
    background: transparent;
    color: {COLORS['text_secondary']};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: right;
    font-size: 14px;
}}
#nav_btn:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}
#nav_btn[active="true"] {{
    background-color: {COLORS['bg_selected']};
    color: {COLORS['blue_light']};
    border-right: 3px solid {COLORS['blue_primary']};
    font-weight: bold;
}}

/* ══ Cards ══ */
#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px;
}}
#card:hover {{
    border-color: {COLORS['blue_primary']};
}}

/* ══ Stat Card ══ */
#stat_card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 20px;
}}
#stat_value {{
    font-size: 28px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}
#stat_label {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
}}

/* ══ Primary Button ══ */
#btn_primary {{
    background-color: {COLORS['blue_primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
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
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
}}
#btn_secondary:hover {{
    border-color: {COLORS['blue_primary']};
    color: {COLORS['blue_light']};
}}

/* ══ Danger Button ══ */
#btn_danger {{
    background-color: {COLORS['red_bg']};
    color: {COLORS['red']};
    border: 1px solid {COLORS['red']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
}}
#btn_danger:hover {{
    background-color: {COLORS['red']};
    color: white;
}}

/* ══ Success Button ══ */
#btn_success {{
    background-color: {COLORS['green_bg']};
    color: {COLORS['green']};
    border: 1px solid {COLORS['green']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
}}
#btn_success:hover {{
    background-color: {COLORS['green']};
    color: white;
}}

/* ══ Input Fields ══ */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    selection-background-color: {COLORS['blue_primary']};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {COLORS['blue_primary']};
    background-color: {COLORS['bg_card']};
}}
QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['text_muted']};
}}

/* ══ ComboBox Dropdown ══ */
QComboBox::drop-down {{
    border: none;
    padding-left: 8px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    selection-background-color: {COLORS['bg_selected']};
    padding: 4px;
}}

/* ══ Labels ══ */
#label_field {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
    font-weight: bold;
}}
#label_title {{
    color: {COLORS['text_primary']};
    font-size: 20px;
    font-weight: bold;
}}
#label_subtitle {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
}}

/* ══ Table ══ */
QTableWidget {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 10px 12px;
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
    border-bottom: 1px solid {COLORS['border']};
    padding: 10px 12px;
    font-weight: bold;
    font-size: 13px;
}}

/* ══ Tab Widget ══ */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background: {COLORS['bg_card']};
    top: -1px;
}}
QTabBar::tab {{
    background: {COLORS['bg_input']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
    margin-left: 2px;
    font-size: 13px;
}}
QTabBar::tab:selected {{
    background: {COLORS['bg_card']};
    color: {COLORS['blue_light']};
    border-color: {COLORS['blue_primary']};
    font-weight: bold;
}}
QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
}}

/* ══ Separator ══ */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {COLORS['border']};
}}

/* ══ ToolTip ══ */
QToolTip {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}

/* ══ MessageBox ══ */
QMessageBox {{
    background-color: {COLORS['bg_card']};
}}
QMessageBox QPushButton {{
    background-color: {COLORS['blue_primary']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    min-width: 80px;
}}
QMessageBox QPushButton:hover {{
    background-color: {COLORS['blue_light']};
}}

/* ══ CheckBox ══ */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border']};
    border-radius: 4px;
    background: {COLORS['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['blue_primary']};
    border-color: {COLORS['blue_primary']};
}}

/* ══ RadioButton ══ */
QRadioButton {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border']};
    border-radius: 9px;
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
"""


def get_status_style(status: str) -> str:
    """يرجع style الـ badge حسب الحالة"""
    styles = {
        "cash":    f"color: {COLORS['green']}; background: {COLORS['green_bg']}; border-radius: 6px; padding: 3px 10px;",
        "pending": f"color: {COLORS['yellow']}; background: {COLORS['yellow_bg']}; border-radius: 6px; padding: 3px 10px;",
        "paid":    f"color: {COLORS['text_muted']}; background: {COLORS['bg_input']}; border-radius: 6px; padding: 3px 10px;",
    }
    return styles.get(status, "")


def get_status_text(status: str) -> str:
    """يرجع النص العربي للحالة"""
    texts = {
        "cash":    "نقدي",
        "pending": "مؤجل",
        "paid":    "مسدد",
    }
    return texts.get(status, status)
