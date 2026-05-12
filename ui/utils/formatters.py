"""
Formatters & Utilities
أدوات التنسيق
"""

from datetime import datetime


def fmt_currency(amount: float, symbol: str = "ج") -> str:
    """تنسيق المبلغ المالي  →  1,234.50 ج"""
    if amount is None:
        return f"0.00 {symbol}"
    return f"{amount:,.2f} {symbol}"


def fmt_number(number: float) -> str:
    """تنسيق رقم عادي  →  1,234"""
    if number is None:
        return "0"
    return f"{number:,.0f}"


def fmt_datetime(dt_str: str) -> str:
    """تنسيق التاريخ والوقت  →  2024-01-15  10:30"""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d  %H:%M")
    except Exception:
        return dt_str


def fmt_date(dt_str: str) -> str:
    """تنسيق التاريخ فقط  →  2024-01-15"""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return dt_str


def profit_color(profit: float, colors: dict) -> str:
    """يرجع لون الربح (أخضر/أحمر/رمادي)"""
    if profit is None:
        return colors["text_muted"]
    if profit > 0:
        return colors["green"]
    if profit < 0:
        return colors["red"]
    return colors["text_secondary"]
