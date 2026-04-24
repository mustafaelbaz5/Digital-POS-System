"""
Dashboard Screen — الشاشة الرئيسية
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QGridLayout, QFrame,
    QSpacerItem, QSizePolicy, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from ui.styles.theme import COLORS
from ui.components.widgets import StatCard, PlatformCard, SectionTitle
from utils.formatters import fmt_currency, fmt_number

import database as db


class DashboardScreen(QWidget):
    """الداشبورد الرئيسي"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.refresh()

        # تحديث تلقائي كل 30 ثانية
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(30_000)

    # ─── بناء الواجهة ──────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)

        # ── العنوان
        header = self._make_header()
        root.addLayout(header)

        # ── كروت الإحصائيات
        root.addWidget(SectionTitle("نظرة عامة", "إجماليات اليوم"))
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(12)
        root.addLayout(self.stats_grid)
        self._build_stat_cards()

        # ── معادلة المطابقة
        self.match_bar = self._make_match_bar()
        root.addWidget(self.match_bar)

        # ── المنصات
        root.addWidget(SectionTitle("المنصات", "الماكينات والمحافظ الإلكترونية"))

        platforms_scroll = QScrollArea()
        platforms_scroll.setWidgetResizable(True)
        platforms_scroll.setFixedHeight(200)
        platforms_scroll.setStyleSheet("border: none; background: transparent;")
        platforms_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        platforms_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.platforms_container = QWidget()
        self.platforms_layout    = QHBoxLayout(self.platforms_container)
        self.platforms_layout.setContentsMargins(0, 0, 0, 0)
        self.platforms_layout.setSpacing(12)
        self.platforms_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        platforms_scroll.setWidget(self.platforms_container)
        root.addWidget(platforms_scroll)

        # ── أزرار سريعة
        root.addWidget(SectionTitle("إجراءات سريعة"))
        root.addLayout(self._make_quick_actions())

        root.addStretch()

    def _make_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        # التاريخ والوقت
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%A  |  %Y-%m-%d")

        date_lbl = QLabel(date_str)
        date_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(date_lbl)

        layout.addStretch()

        # العنوان
        title = QLabel("📊  لوحة التحكم")
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 22px; font-weight: bold;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title)

        return layout

    def _build_stat_cards(self):
        """إنشاء كروت الإحصائيات"""
        self.card_cash     = StatCard("الخزينة النقدية",   icon="💵", accent_color=COLORS["green"])
        self.card_machines = StatCard("إجمالي الماكينات",  icon="🏧", accent_color=COLORS["blue_light"])
        self.card_wallets  = StatCard("إجمالي المحافظ",    icon="💳", accent_color=COLORS["purple"])
        self.card_debts    = StatCard("إجمالي المديونيات", icon="📋", accent_color=COLORS["yellow"])
        self.card_today    = StatCard("أرباح اليوم",       icon="📈", accent_color=COLORS["green"])
        self.card_month    = StatCard("أرباح الشهر",       icon="🗓️", accent_color=COLORS["blue_primary"])

        cards = [
            self.card_cash, self.card_machines, self.card_wallets,
            self.card_debts, self.card_today, self.card_month
        ]

        for i, card in enumerate(cards):
            row, col = divmod(i, 3)
            self.stats_grid.addWidget(card, row, col)

    def _make_match_bar(self) -> QFrame:
        """شريط معادلة المطابقة"""
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(64)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 12, 20, 12)

        self.match_icon  = QLabel("✅")
        self.match_icon.setFont(QFont("Segoe UI Emoji", 18))
        layout.addWidget(self.match_icon)

        layout.addStretch()

        self.match_label = QLabel("معادلة المطابقة")
        self.match_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px;"
        )
        layout.addWidget(self.match_label)

        self.match_value = QLabel("")
        self.match_value.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: bold;"
        )
        layout.addWidget(self.match_value)

        # زرار تعديل الميزانية
        budget_btn = QPushButton("⚙️  تعديل الميزانية")
        budget_btn.setObjectName("btn_secondary")
        budget_btn.setFixedHeight(36)
        budget_btn.clicked.connect(self._edit_budget)
        layout.addWidget(budget_btn)

        return frame

    def _make_quick_actions(self) -> QHBoxLayout:
        """أزرار الإجراءات السريعة"""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        actions = [
            ("➕  إضافة منصة",      "btn_secondary", self._add_platform_quick),
            ("💰  إيداع للماكينة",  "btn_secondary", self._deposit_quick),
        ]

        for text, obj_name, handler in actions:
            btn = QPushButton(text)
            btn.setObjectName(obj_name)
            btn.setFixedHeight(40)
            btn.setMinimumWidth(160)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        layout.addStretch()
        return layout

    # ─── تحديث البيانات ────────────────────────────────────────────

    def refresh(self):
        """تحديث كل بيانات الداشبورد"""
        stats = db.get_dashboard_stats()

        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_machines.set_value(fmt_currency(stats["total_machines"]))
        self.card_wallets.set_value(fmt_currency(stats["total_wallets"]))
        self.card_debts.set_value(fmt_currency(stats["total_debts"]))
        self.card_today.set_value(fmt_currency(stats["today_profit"]))
        self.card_month.set_value(fmt_currency(stats["month_profit"]))

        # معادلة المطابقة
        net = stats["net_position"]
        if abs(net) < 0.01:
            self.match_icon.setText("✅")
            self.match_value.setText("الحسابات متطابقة")
            self.match_value.setStyleSheet(f"color: {COLORS['green']}; font-size: 15px; font-weight: bold;")
        elif net > 0:
            self.match_icon.setText("📈")
            self.match_value.setText(f"فائض  {fmt_currency(net)}")
            self.match_value.setStyleSheet(f"color: {COLORS['blue_light']}; font-size: 15px; font-weight: bold;")
        else:
            self.match_icon.setText("⚠️")
            self.match_value.setText(f"عجز  {fmt_currency(abs(net))}")
            self.match_value.setStyleSheet(f"color: {COLORS['red']}; font-size: 15px; font-weight: bold;")

        self.match_label.setText(
            f"ميزانية: {fmt_currency(stats['main_budget'])}   |   "
            f"إجمالي الأرصدة: {fmt_currency(stats['total_balances'])}   |   "
            f"الديون: {fmt_currency(stats['total_debts'])}"
        )

        # تحديث كروت المنصات
        self._refresh_platforms()

    def _refresh_platforms(self):
        """تحديث كروت المنصات"""
        # مسح القديم
        for i in reversed(range(self.platforms_layout.count())):
            w = self.platforms_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        platforms = db.get_all_platforms()

        if not platforms:
            empty = QLabel("لا توجد منصات مضافة بعد")
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.platforms_layout.addWidget(empty)
            return

        for p in platforms:
            card = PlatformCard(p)
            card.deposit_clicked.connect(self._on_deposit_clicked)
            self.platforms_layout.addWidget(card)

        self.platforms_layout.addStretch()

    # ─── الإجراءات ──────────────────────────────────────────────────

    def _on_deposit_clicked(self, platform_id: int):
        """إيداع لمنصة من كارتها"""
        platform = db.get_platform_by_id(platform_id)
        if not platform:
            return

        amount, ok = QInputDialog.getDouble(
            self, "إيداع",
            f"أدخل المبلغ المراد إيداعه في [{platform['name']}]:",
            min=0.01, decimals=2
        )
        if ok and amount > 0:
            try:
                db.deposit_to_platform(platform_id, amount)
                self.refresh()
                QMessageBox.information(
                    self, "تم",
                    f"تم إيداع {fmt_currency(amount)} في {platform['name']} ✅"
                )
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_budget(self):
        """تعديل الميزانية الرئيسية"""
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
                    self, "تم",
                    f"تم تحديث الميزانية إلى {fmt_currency(amount)} ✅"
                )
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _add_platform_quick(self):
        """إضافة منصة سريعة"""
        from ui.screens.platforms_screen import AddPlatformDialog
        dialog = AddPlatformDialog(self)
        if dialog.exec():
            self.refresh()

    def _deposit_quick(self):
        """إيداع سريع — يختار المستخدم المنصة"""
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
