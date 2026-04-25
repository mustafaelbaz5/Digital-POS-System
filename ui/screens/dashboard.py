"""
dashboard.py — الداشبورد الرئيسي
Refactored: ScreenShell, responsive grid, clean layout
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QInputDialog, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime

from ui.styles.theme import COLORS
from ui.components.widgets import (
    StatCard, PlatformsRow, SectionTitle, ScreenShell, InfoRow, make_divider
)
from utils.formatters import fmt_currency

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
        days_ar = ["الإثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
        now = datetime.now()
        day = days_ar[now.weekday()]
        return f"{day}  ·  {now.strftime('%Y-%m-%d')}"

    # ─── Build Content ────────────────────────────────────────────

    def _build_content(self):
        c = self.content()

        # Quick actions in header
        self._add_header_actions()

        # ── Stat Cards Grid
        self._stats_grid = QGridLayout()
        self._stats_grid.setSpacing(12)
        c.addLayout(self._stats_grid)
        self._build_stat_cards()

        # ── Match bar
        self._match_bar = self._make_match_bar()
        c.addWidget(self._match_bar)

        # ── Platforms
        platforms_header = QHBoxLayout()
        sec = SectionTitle("المنصات", "الماكينات والمحافظ الإلكترونية")
        platforms_header.addWidget(sec)
        platforms_header.addStretch()
        add_btn = QPushButton("+ إضافة منصة")
        add_btn.setObjectName("btn_secondary")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._add_platform)
        platforms_header.addWidget(add_btn)
        c.addLayout(platforms_header)

        self._platforms_row = PlatformsRow()
        self._platforms_row.deposit_clicked.connect(self._on_deposit_clicked)
        c.addWidget(self._platforms_row)

        c.addStretch()

    def _add_header_actions(self):
        budget_btn = QPushButton("⚙️  الميزانية")
        budget_btn.setObjectName("btn_secondary")
        budget_btn.setFixedHeight(32)
        budget_btn.clicked.connect(self._edit_budget)
        self.add_action(budget_btn)

        cash_btn = QPushButton("💵  تعديل الكاش")
        cash_btn.setObjectName("btn_secondary")
        cash_btn.setFixedHeight(32)
        cash_btn.clicked.connect(self._edit_cash)
        self.add_action(cash_btn)

        deposit_btn = QPushButton("💰  إيداع سريع")
        deposit_btn.setObjectName("btn_primary")
        deposit_btn.setFixedHeight(32)
        deposit_btn.clicked.connect(self._deposit_quick)
        self.add_action(deposit_btn)

    def _build_stat_cards(self):
        self.card_budget   = StatCard("الميزانية الأصلية",    icon="🏦", accent_color=COLORS["blue_primary"])
        self.card_assets   = StatCard("إجمالي الأصول",        icon="💰", accent_color=COLORS["cyan"])
        self.card_cash     = StatCard("الخزينة النقدية",      icon="💵", accent_color=COLORS["green"])
        self.card_machines = StatCard("إجمالي الماكينات",     icon="🏧", accent_color=COLORS["blue_bright"])
        self.card_wallets  = StatCard("إجمالي المحافظ",       icon="💳", accent_color=COLORS["purple"])
        self.card_debts    = StatCard("إجمالي المديونيات",    icon="📋", accent_color=COLORS["yellow"])
        self.card_today    = StatCard("أرباح اليوم",          icon="📈", accent_color=COLORS["green"])
        self.card_month    = StatCard("أرباح الشهر",          icon="🗓️", accent_color=COLORS["blue_primary"])
        self.card_pending  = StatCard("إجمالي المؤجل",       icon="⏳", accent_color=COLORS["yellow"])

        cards = [
            self.card_budget,   self.card_assets,   self.card_cash,
            self.card_machines, self.card_wallets,  self.card_debts,
            self.card_today,    self.card_month,    self.card_pending,
        ]
        for i, card in enumerate(cards):
            self._stats_grid.addWidget(card, i // 3, i % 3)

    def _make_match_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card_highlight")
        frame.setFixedHeight(60)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        self._match_icon  = QLabel("⚖️")
        self._match_icon.setStyleSheet("font-size: 20px;")
        layout.addWidget(self._match_icon)

        self._match_detail = QLabel("معادلة المطابقة")
        self._match_detail.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        layout.addWidget(self._match_detail)

        layout.addStretch()

        self._match_value = QLabel("—")
        self._match_value.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: bold;"
        )
        layout.addWidget(self._match_value)

        return frame

    # ─── Refresh ──────────────────────────────────────────────────

    def refresh(self):
        stats = db.get_dashboard_stats()

        self.card_budget.set_value(fmt_currency(stats["main_budget"]))
        self.card_assets.set_value(fmt_currency(stats["total_assets"]))
        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_machines.set_value(fmt_currency(stats["total_machines"]))
        self.card_wallets.set_value(fmt_currency(stats["total_wallets"]))
        self.card_debts.set_value(fmt_currency(stats["total_debts"]))
        self.card_today.set_value(fmt_currency(stats["today_profit"]))
        self.card_month.set_value(fmt_currency(stats["month_profit"]))
        self.card_pending.set_value(fmt_currency(stats.get("total_pending", 0)))

        # Match formula
        net = stats["net_position"]
        if abs(net) < 0.01:
            self._match_icon.setText("✅")
            self._match_value.setText("الحسابات متطابقة")
            self._match_value.setStyleSheet(
                f"color: {COLORS['green']}; font-size: 14px; font-weight: bold;"
            )
        elif net > 0:
            self._match_icon.setText("📈")
            self._match_value.setText(f"فائض  {fmt_currency(net)}")
            self._match_value.setStyleSheet(
                f"color: {COLORS['blue_bright']}; font-size: 14px; font-weight: bold;"
            )
        else:
            self._match_icon.setText("⚠️")
            self._match_value.setText(f"عجز  {fmt_currency(abs(net))}")
            self._match_value.setStyleSheet(
                f"color: {COLORS['red']}; font-size: 14px; font-weight: bold;"
            )

        self._match_detail.setText(
            f"ميزانية: {fmt_currency(stats['main_budget'])}  ·  "
            f"أرصدة: {fmt_currency(stats['total_balances'])}  ·  "
            f"ديون: {fmt_currency(stats['total_debts'])}"
        )

        # Platforms
        self._platforms_row.load(db.get_all_platforms())

    # ─── Actions ──────────────────────────────────────────────────

    def _on_deposit_clicked(self, platform_id: int):
        platform = db.get_platform_by_id(platform_id)
        if not platform:
            return
        amount, ok = QInputDialog.getDouble(
            self, "إيداع",
            f"المبلغ المراد إيداعه في [{platform['name']}]:",
            min=0.01, decimals=2
        )
        if ok and amount > 0:
            try:
                db.deposit_to_platform(platform_id, amount)
                self.refresh()
                QMessageBox.information(
                    self, "تم ✅",
                    f"تم إيداع {fmt_currency(amount)} في {platform['name']}"
                )
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_cash(self):
        current = db.get_budget()["cash_vault"]
        amount, ok = QInputDialog.getDouble(
            self, "تعديل الكاش",
            f"أدخل المبلغ النقدي الحالي في يدك:\n(الحالي: {fmt_currency(current)})",
            value=current, min=0, decimals=2
        )
        if ok:
            try:
                db.set_cash_vault(amount)
                self.refresh()
                QMessageBox.information(
                    self, "تم ✅",
                    f"تم تحديث الكاش إلى {fmt_currency(amount)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_budget(self):
        current = db.get_budget()["main_budget"]
        amount, ok = QInputDialog.getDouble(
            self, "تعديل الميزانية الرئيسية",
            "أدخل رأس المال الجديد:",
            value=current, min=0, decimals=2
        )
        if ok:
            try:
                db.update_main_budget(amount)
                self.refresh()
                QMessageBox.information(
                    self, "تم ✅",
                    f"تم تحديث الميزانية إلى {fmt_currency(amount)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _add_platform(self):
        from ui.screens.platforms_screen import AddPlatformDialog
        dialog = AddPlatformDialog(self)
        if dialog.exec():
            self.refresh()

    def _deposit_quick(self):
        platforms = db.get_all_platforms("machine")
        if not platforms:
            QMessageBox.information(self, "تنبيه", "لا توجد ماكينات مضافة")
            return
        names = [p["name"] for p in platforms]
        name, ok = QInputDialog.getItem(
            self, "إيداع للماكينة", "اختر الماكينة:", names, editable=False
        )
        if ok:
            platform = next(p for p in platforms if p["name"] == name)
            self._on_deposit_clicked(platform["id"])