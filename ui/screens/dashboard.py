"""
dashboard.py — لوحة التحكم الرئيسية (Redesigned v3)
"""

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import BaseDialog, CardGroup, ScreenShell, StatCard
from ui.styles.theme import COLORS, FONT, GAP_LG, GAP_MD, GAP_SM
from ui.utils.formatters import fmt_currency


# ══════════════════════════════════════════
#  Export Success Dialog
# ══════════════════════════════════════════

class ExportSuccessDialog(BaseDialog):
    def __init__(self, url: str, parent=None):
        super().__init__("تم تصدير البيانات", parent)
        self.url = url
        self.setFixedWidth(420)
        self._build_content()

    def _build_content(self):
        self.body.setSpacing(GAP_MD)

        info_lbl = QLabel("تم تصدير كل البيانات إلى Google Sheets بنجاح.")
        info_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['md']};"
        )
        info_lbl.setWordWrap(True)
        self.body.addWidget(info_lbl)

        card = QFrame()
        card.setObjectName("card_highlight")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        url_lbl = QLabel(self.url)
        url_lbl.setStyleSheet(
            f"color:{COLORS['accent']}; font-size:{FONT['sm']}; font-family: 'Consolas', monospace;"
        )
        url_lbl.setWordWrap(True)
        cl.addWidget(url_lbl)
        self.body.addWidget(card)

        self.add_stretch()
        self.add_button("إغلاق", self.accept, role="primary")


# ══════════════════════════════════════════
#  Top Debtor Row
# ══════════════════════════════════════════

class _DebtorRow(QFrame):
    def __init__(self, name: str, debt: float, rank: int, on_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QFrame#card:hover {{
                border-color: {COLORS['accent']};
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(GAP_SM)

        rank_lbl = QLabel(f"#{rank}")
        rank_lbl.setFixedWidth(28)
        rank_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']}; font-size:{FONT['sm']}; font-weight:bold;"
        )
        layout.addWidget(rank_lbl)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['md']}; font-weight:bold;"
        )
        layout.addWidget(name_lbl, 1)

        debt_lbl = QLabel(fmt_currency(debt))
        debt_lbl.setStyleSheet(
            f"color:{COLORS['red']}; font-size:{FONT['md']}; font-weight:bold;"
            f"background:{COLORS['red_bg']}; border:1px solid {COLORS['red_border']};"
            f"border-radius:6px; padding:2px 10px;"
        )
        debt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(debt_lbl)

        if on_click:
            self.mousePressEvent = lambda _: on_click()


# ══════════════════════════════════════════
#  DashboardScreen
# ══════════════════════════════════════════

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
        c.setSpacing(GAP_LG)

        # ── Row 1: 6 Stat Cards ────────────────────────────────────────────
        stats_group = CardGroup("نظرة عامة")
        stats_group.add_layout(self._make_stats_grid())
        c.addWidget(stats_group)

        # ── Row 2: Quick search + top debts + quick actions ────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(GAP_MD)

        search_group = CardGroup("بحث سريع عن عميل", section_type="customer")
        search_group.add_widget(self._make_search_panel())
        row2.addWidget(search_group, 1)

        debtors_group = CardGroup("أعلى المديونيات", section_type="customer")
        self._debtors_container = QVBoxLayout()
        self._debtors_container.setSpacing(GAP_SM)
        debtors_group.add_layout(self._debtors_container)
        row2.addWidget(debtors_group, 1)

        actions_group = CardGroup("الإجراءات السريعة")
        actions_group.add_widget(self._make_actions_panel())
        row2.addWidget(actions_group, 1)

        row2_widget = QWidget()
        row2_widget.setLayout(row2)
        c.addWidget(row2_widget)

        c.addStretch()

    # ── Stats Grid (6 cards) ───────────────────────────────────────────────

    def _make_stats_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(GAP_MD)
        grid.setContentsMargins(0, 0, 0, 0)

        self.card_budget = StatCard("رأس المال", accent_color=COLORS["text_secondary"])
        self.card_cash = StatCard("الخزينة النقدية", accent_color=COLORS["green"])
        self.card_assets = StatCard("إجمالي الأصول", accent_color=COLORS["cyan"])
        self.card_pending = StatCard("إجمالي المؤجل", accent_color=COLORS["red"])
        self.card_today = StatCard("أرباح اليوم", accent_color=COLORS["accent"])
        self.card_month = StatCard("أرباح الشهر", accent_color=COLORS["accent_hover"])

        cards = [
            (self.card_budget, 0, 0),
            (self.card_cash, 0, 1),
            (self.card_assets, 0, 2),
            (self.card_pending, 1, 0),
            (self.card_today, 1, 1),
            (self.card_month, 1, 2),
        ]
        for card, r, col in cards:
            grid.addWidget(card, r, col)
        return grid

    # ── Quick Customer Search ──────────────────────────────────────────────

    def _make_search_panel(self) -> QWidget:
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(GAP_SM)

        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("ابحث باسم العميل أو التليفون...")
        self._search_input.setMinimumHeight(44)
        self._search_input.textChanged.connect(self._on_search)
        search_row.addWidget(self._search_input, 1)

        layout.addLayout(search_row)

        # Results area
        self._search_results = QVBoxLayout()
        self._search_results.setSpacing(4)
        layout.addLayout(self._search_results)
        layout.addStretch()
        return frame

    def _on_search(self, text: str):
        # Clear old results
        while self._search_results.count():
            item = self._search_results.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if len(text.strip()) < 2:
            return

        customers = db.search_customers(text.strip())
        for cust in customers[:5]:
            row = QFrame()
            row.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_elevated']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                }}
                QFrame:hover {{ border-color: {COLORS['accent']}; }}
            """)
            row.setCursor(Qt.CursorShape.PointingHandCursor)

            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 10, 8)

            name_lbl = QLabel(cust["name"])
            name_lbl.setStyleSheet(
                f"color:{COLORS['text_primary']}; font-weight:bold; font-size:{FONT['md']};"
            )
            rl.addWidget(name_lbl, 1)

            if cust.get("phone"):
                phone_lbl = QLabel(cust["phone"])
                phone_lbl.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:{FONT['sm']};")
                rl.addWidget(phone_lbl)

            net = cust.get("net_balance", 0) or 0
            if net > 0:
                debt_lbl = QLabel(fmt_currency(net))
                debt_lbl.setStyleSheet(
                    f"color:{COLORS['red']}; font-weight:bold; font-size:{FONT['sm']};"
                    f"background:{COLORS['red_bg']}; border-radius:4px; padding:2px 8px;"
                )
                rl.addWidget(debt_lbl)

            stmt_btn = QPushButton("كشف")
            stmt_btn.setObjectName("btn_statement")
            stmt_btn.setFixedHeight(28)
            stmt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cid = cust["id"]
            stmt_btn.clicked.connect(lambda _, c=cid: self._open_statement(c))
            rl.addWidget(stmt_btn)

            self._search_results.addWidget(row)

    def _open_statement(self, customer_id: int):
        from ui.screens.statement_screen import CustomerStatementDialog
        dlg = CustomerStatementDialog(customer_id, self)
        dlg.statement_changed.connect(self.refresh)
        dlg.exec()

    # ── Actions Panel ──────────────────────────────────────────────────────

    def _make_actions_panel(self) -> QWidget:
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(GAP_SM)

        actions = [
            ("💰  إدارة الميزانية", self._manage_budget),
            ("💵  تعديل الخزينة النقدية", self._edit_cash),
            ("☁️  تصدير البيانات", self._export_to_sheets),
        ]

        for label, slot in actions:
            btn = QPushButton(label)
            btn.setObjectName("btn_secondary")
            btn.setMinimumHeight(46)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            if label.startswith("☁️"):
                self._btn_export = btn
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    # ── Top Debtors ────────────────────────────────────────────────────────

    def _fill_debtors(self):
        while self._debtors_container.count():
            item = self._debtors_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            customers = db.get_all_customers()
            debtors = sorted(
                [c for c in customers if (c.get("net_balance") or 0) > 0],
                key=lambda c: c.get("net_balance", 0),
                reverse=True,
            )[:5]

            if not debtors:
                no_debt = QLabel("لا توجد مديونيات حالية")
                no_debt.setStyleSheet(
                    f"color:{COLORS['text_muted']}; font-size:{FONT['sm']};"
                )
                no_debt.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._debtors_container.addWidget(no_debt)
                return

            for i, cust in enumerate(debtors):
                cid = cust["id"]
                row = _DebtorRow(
                    cust["name"],
                    cust.get("net_balance", 0),
                    i + 1,
                    on_click=lambda c=cid: self._open_statement(c),
                )
                self._debtors_container.addWidget(row)

        except Exception:
            pass

        self._debtors_container.addStretch()

    # ── Refresh ────────────────────────────────────────────────────────────

    def refresh(self):
        stats = db.get_dashboard_stats()
        self.card_budget.set_value(fmt_currency(stats["main_budget"]))
        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_assets.set_value(fmt_currency(stats["total_assets"]))
        self.card_pending.set_value(fmt_currency(stats["total_pending"]))
        self.card_today.set_value(fmt_currency(stats["today_profit"]))
        self.card_month.set_value(fmt_currency(stats["month_profit"]))

        budget_str = fmt_currency(stats["main_budget"])
        self.set_subtitle(f"{self._today_str()}   |   الميزانية: {budget_str}")

        self._fill_debtors()

    # ── Actions ────────────────────────────────────────────────────────────

    def _manage_budget(self):
        current = db.get_budget()["main_budget"]
        amount, ok = QInputDialog.getDouble(
            self,
            "إدارة الميزانية المركزية",
            f"أدخل رصيد الميزانية المركزية الكلي:\n(الحالي: {fmt_currency(current)})",
            value=current,
            min=0,
            max=100_000_000,
            decimals=2,
        )
        if ok:
            try:
                db.update_main_budget(amount)
                self.refresh()
                QMessageBox.information(
                    self, "تم", f"تم تحديث الميزانية إلى {fmt_currency(amount)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_cash(self):
        current = db.get_budget()["cash_vault"]
        amount, ok = QInputDialog.getDouble(
            self,
            "تعديل الخزينة النقدية",
            f"أدخل المبلغ النقدي الحالي:\n(الحالي: {fmt_currency(current)})",
            value=current,
            min=0,
            decimals=2,
        )
        if ok:
            try:
                db.set_cash_vault(amount)
                self.refresh()
                QMessageBox.information(self, "تم", f"تم تحديث الخزينة إلى {fmt_currency(amount)}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _export_to_sheets(self):
        self._btn_export.setEnabled(False)
        self._btn_export.setText("جاري التصدير...")

        progress = QProgressDialog(
            "جاري تصدير البيانات إلى Google Sheets...", None, 0, 0, self
        )
        progress.setWindowTitle("يرجى الانتظار")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)
        progress.show()
        QApplication.processEvents()

        try:
            data = db.get_export_data()
            from ui.utils.google_sheets import export_to_sheets
            url = export_to_sheets(data)
            progress.close()
            ExportSuccessDialog(url, self).exec()
        except Exception as e:
            if progress:
                progress.close()
            QMessageBox.critical(self, "خطأ في التصدير", str(e))
        finally:
            self._btn_export.setEnabled(True)
            self._btn_export.setText("☁️  تصدير البيانات")
