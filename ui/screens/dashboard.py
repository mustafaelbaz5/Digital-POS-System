"""
dashboard.py — لوحة التحكم الرئيسية
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QInputDialog, QMessageBox,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from datetime import datetime

from ui.styles.theme import COLORS, FONT, CARD_RADIUS, BORDER_RADIUS
from ui.components.widgets import StatCard, SectionTitle, ScreenShell
from utils.formatters import fmt_currency, fmt_datetime

import database as db


class DashboardScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__("لوحة التحكم", self._today_str())
        self._build_content()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(30_000)

    @staticmethod
    def _today_str() -> str:
        days_ar = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        now = datetime.now()
        return f"{days_ar[now.weekday()]}  ·  {now.strftime('%Y-%m-%d')}"

    def _build_content(self):
        c = self.content()
        c.setSpacing(20)

        # ── Section 1: Stat Cards
        c.addWidget(self._make_section_header("📊  نظرة عامة على الأموال"))
        c.addLayout(self._make_stats_grid())

        # ── Section 2: Recent Transactions (no match equation — task 1)
        c.addWidget(self._make_section_header("🕒  آخر العمليات"))
        self._ops_table = self._make_ops_table()
        c.addWidget(self._ops_table)

        # ── Section 3: Quick Actions
        c.addWidget(self._make_section_header("⚡  الإجراءات السريعة"))
        c.addWidget(self._make_actions_panel())

        c.addSpacing(40)
        c.addStretch()

    @staticmethod
    def _make_section_header(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT['sm']};"
            f"font-weight: bold; font-family: {FONT['family']};"
            f"letter-spacing: 0.5px; padding-bottom: 2px;"
            f"border-bottom: 1px solid {COLORS['border']};"
            f"text-align: right;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)  # task 2: RTL titles
        return lbl

    def _make_stats_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        self.card_budget  = StatCard("الميزانية الأصلية", accent_color=COLORS["teal_primary"])
        self.card_assets  = StatCard("إجمالي الأصول",    accent_color=COLORS["cyan"])
        self.card_cash    = StatCard("الخزينة النقدية",  accent_color=COLORS["green"])
        self.card_wallets = StatCard("إجمالي المحافظ",    accent_color=COLORS["purple"])
        self.card_debts   = StatCard("إجمالي المديونيات", accent_color=COLORS["yellow"])
        self.card_pending = StatCard("إجمالي المؤجل",     accent_color=COLORS["red"])
        self.card_today   = StatCard("أرباح اليوم",       accent_color=COLORS["green"])
        self.card_month   = StatCard("أرباح الشهر",       accent_color=COLORS["teal_bright"])
        self.card_ops     = StatCard("عمليات اليوم",      accent_color=COLORS["blue"])

        placement = [
            (self.card_budget, 0, 0), (self.card_assets, 0, 1), (self.card_cash, 0, 2),
            (self.card_wallets, 1, 0), (self.card_debts, 1, 1), (self.card_pending, 1, 2),
            (self.card_today, 2, 0),  (self.card_month, 2, 1),  (self.card_ops, 2, 2),
        ]
        for card, r, col in placement:
            grid.addWidget(card, r, col)
        return grid

    def _make_ops_table(self) -> QTableWidget:
        columns = ["التاريخ والوقت", "العميل", "الخدمة", "المنصة", "المطلوب", "الربح", "الحالة"]
        tbl = QTableWidget()
        tbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        tbl.setColumnCount(len(columns))
        tbl.setHorizontalHeaderLabels(columns)
        tbl.setMaximumHeight(320)
        tbl.setMinimumHeight(220)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setAlternatingRowColors(True)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.horizontalHeader().setHighlightSections(False)
        tbl.horizontalHeader().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        header = tbl.horizontalHeader()
        widths = [200, 150, 150, 150, 100, 85,-1]
        for i, w in enumerate(widths):
            if w == -1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                tbl.setColumnWidth(i, w)
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        tbl.verticalHeader().setDefaultSectionSize(50)
        tbl.setStyleSheet(
            f"QTableWidget {{ background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']};"
            f"border-radius: {CARD_RADIUS}; gridline-color: transparent; }}"
            f"QTableWidget::item {{background: {COLORS['bg_elevated']}; padding: 8px 16px; border-bottom: 1px solid {COLORS['border']}; }}"
            f"QTableWidget::item:selected {{ background: {COLORS['teal_subtle']}; }}"
            f"QHeaderView::section {{ background: {COLORS['bg_dark']}; color: {COLORS['text_secondary']};"
            f"border: none; border-bottom: 2px solid {COLORS['border']};"
            f"padding: 10px 16px; font-weight: bold; font-size: {FONT['sm']}; }}"
            f"alternate-background-color: {COLORS['bg_elevated']};"
        )
        return tbl

    def _fill_ops_table(self):
        txns = db.get_transactions(limit=15)
        self._ops_table.setRowCount(len(txns))
        status_colors = {"cash": COLORS["green"], "pending": COLORS["yellow"], "paid": COLORS["text_muted"]}
        status_text   = {"cash": "نقدي", "pending": "مؤجل", "paid": "مسدد"}
        for row, t in enumerate(txns):
            def cell(col, text, color=None, bold=False):
                item = QTableWidgetItem(str(text) if text else "—")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                if color: item.setForeground(QColor(color))
                if bold:  f = item.font(); f.setBold(True); item.setFont(f)
                self._ops_table.setItem(row, col, item)
            # task 16: full timestamp
            raw_date = t.get("created_at") or ""
            cell(0, raw_date[:16].replace("T", "  "), color=COLORS["text_muted"])
            cell(1, t.get("customer_name") or "—", color=COLORS["text_secondary"])
            cell(2, t.get("service_name") or "—")
            cell(3, t.get("platform_name") or "—", color=COLORS["text_muted"])
            cell(4, fmt_currency(t.get("amount_required", 0) or 0), bold=True)
            profit = t.get("profit", 0) or 0
            cell(5, fmt_currency(profit), color=COLORS["green"] if profit >= 0 else COLORS["red"])
            st = t.get("payment_status", "")
            cell(6, status_text.get(st, st), color=status_colors.get(st))

    def _make_actions_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        row = QHBoxLayout(frame)
        row.setContentsMargins(20, 16, 20, 16)
        row.setSpacing(12)
        actions = [
            ("⊕  إضافة عملية",      "btn_primary",   self._go_to_transaction),
            ("👤  إضافة عميل",      "btn_secondary", self._add_customer),
            ("💵  تعديل الميزانية", "btn_secondary", self._edit_budget),
            ("💰  تعديل الكاش",    "btn_secondary", self._edit_cash),
            ("📊  التقارير",        "btn_secondary", self._go_to_reports),
        ]
        for label, obj, slot in actions:
            btn = QPushButton(label)
            btn.setObjectName(obj)
            btn.setMinimumHeight(44)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        return frame

    def refresh(self):
        stats = db.get_dashboard_stats()
        self.card_budget.set_value(fmt_currency(stats["main_budget"]))
        self.card_assets.set_value(fmt_currency(stats["total_assets"]))
        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_wallets.set_value(fmt_currency(stats["total_wallets"]))
        self.card_debts.set_value(fmt_currency(stats["total_debts"]))
        self.card_pending.set_value(fmt_currency(stats["total_pending"]))
        self.card_today.set_value(fmt_currency(stats["today_profit"]))
        self.card_month.set_value(fmt_currency(stats["month_profit"]))
        try:
            from datetime import date
            today_str = date.today().isoformat()
            all_t = db.get_transactions(limit=500)
            ops_today = sum(1 for t in all_t if (t.get("created_at") or "").startswith(today_str))
            self.card_ops.set_value(str(ops_today))
        except Exception:
            self.card_ops.set_value("—")
        self._fill_ops_table()

    def _go_to_transaction(self):
        win = self.window()
        if hasattr(win, "navigate_to"): win.navigate_to("transaction")

    def _go_to_reports(self):
        win = self.window()
        if hasattr(win, "navigate_to"): win.navigate_to("reports")

    def _add_customer(self):
        """task 3: use exact same CustomerDialog as customers screen"""
        from ui.screens.customers_screen import CustomerDialog
        dlg = CustomerDialog(self)
        if dlg.exec():
            self.refresh()
            QMessageBox.information(self, "تم ", "تم إضافة العميل بنجاح")

    def _edit_budget(self):
        current = db.get_budget()["main_budget"]
        amount, ok = QInputDialog.getDouble(
            self, "تعديل الميزانية", "أدخل رأس المال الجديد:",
            value=current, min=0, decimals=2
        )
        if ok:
            try:
                db.update_main_budget(amount)
                self.refresh()
                QMessageBox.information(self, "تم ", f"تم تحديث الميزانية إلى {fmt_currency(amount)}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_cash(self):
        current = db.get_budget()["cash_vault"]
        amount, ok = QInputDialog.getDouble(
            self, "تعديل الكاش",
            f"أدخل المبلغ النقدي الحالي:\n(الحالي: {fmt_currency(current)})",
            value=current, min=0, decimals=2
        )
        if ok:
            try:
                db.set_cash_vault(amount)
                self.refresh()
                QMessageBox.information(self, "تم ", f"تم تحديث الكاش إلى {fmt_currency(amount)}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))
