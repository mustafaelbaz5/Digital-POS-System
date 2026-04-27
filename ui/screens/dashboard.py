"""
dashboard.py — لوحة التحكم الرئيسية (v3 - Full Rebuild)
=========================================================
Layout (top → bottom):
  1. Stat Cards Grid  (3 × 3 – capital / distribution / profits)
  2. Match Equation   (معادلة المطابقة — detailed rich card)
  3. Recent Ops Table (آخر العمليات — last 15 rows, read-only)
  4. Action Buttons   (الإجراءات السريعة — 5 key actions)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QInputDialog, QMessageBox,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from datetime import datetime

from ui.styles.theme import COLORS, FONT, CARD_RADIUS, BORDER_RADIUS
from ui.components.widgets import StatCard, SectionTitle, ScreenShell
from utils.formatters import fmt_currency, fmt_datetime

import database as db


# ══════════════════════════════════════════════════════════════
#  DashboardScreen
# ══════════════════════════════════════════════════════════════

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

    # ─── Build ────────────────────────────────────────────────

    def _build_content(self):
        c = self.content()
        c.setSpacing(20)

        # ── Section 1: Stat Cards ──────────────────────────
        c.addWidget(self._make_section_header("📊  نظرة عامة على الأموال"))
        c.addLayout(self._make_stats_grid())

        # ── Section 2: Match Equation ─────────────────────
        c.addWidget(self._make_section_header("⚖️  معادلة المطابقة"))
        self._match_card = self._make_match_card()
        c.addWidget(self._match_card)

        # ── Section 3: Recent Transactions ────────────────
        c.addWidget(self._make_section_header("🕒  آخر العمليات"))
        self._ops_table = self._make_ops_table()
        c.addWidget(self._ops_table)

        # ── Section 4: Quick Actions ──────────────────────
        c.addWidget(self._make_section_header("⚡  الإجراءات السريعة"))
        c.addWidget(self._make_actions_panel())

        c.addSpacing(40)  # Spacing at the bottom for better scrolling
        c.addStretch()

    # ─── Section Header Helper ────────────────────────────────

    @staticmethod
    def _make_section_header(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT['sm']};"
            f"font-weight: bold; font-family: {FONT['family']};"
            f"letter-spacing: 0.5px; padding-bottom: 2px;"
            f"border-bottom: 1px solid {COLORS['border']};"
            f"text-align: left;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        return lbl

    # ─── Stats Grid (3 rows × 3 cols) ─────────────────────────

    def _make_stats_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        # Row 0: Capital
        self.card_budget = StatCard("الميزانية الأصلية", accent_color=COLORS["teal_primary"])
        self.card_assets = StatCard("إجمالي الأصول",    accent_color=COLORS["cyan"])
        self.card_cash   = StatCard("الخزينة النقدية",  accent_color=COLORS["green"])

        # Row 1: Distribution
        self.card_wallets  = StatCard("إجمالي المحافظ",    accent_color=COLORS["purple"])
        self.card_debts    = StatCard("إجمالي المديونيات", accent_color=COLORS["yellow"])
        self.card_pending  = StatCard("إجمالي المؤجل",     accent_color=COLORS["red"])

        # Row 2: Profits
        self.card_today  = StatCard("أرباح اليوم", accent_color=COLORS["green"])
        self.card_month  = StatCard("أرباح الشهر", accent_color=COLORS["teal_bright"])
        self.card_ops    = StatCard("عمليات اليوم", accent_color=COLORS["blue"])

        placement = [
            (self.card_budget, 0, 0), (self.card_assets, 0, 1), (self.card_cash, 0, 2),
            (self.card_wallets, 1, 0), (self.card_debts, 1, 1), (self.card_pending, 1, 2),
            (self.card_today, 2, 0),   (self.card_month, 2, 1), (self.card_ops, 2, 2),
        ]
        for card, r, col in placement:
            grid.addWidget(card, r, col)

        return grid

    # ─── Match Equation Card ──────────────────────────────────

    def _make_match_card(self) -> QFrame:
        """Detailed مطابقة card with formula breakdown + status badge."""
        frame = QFrame()
        frame.setObjectName("card")
        frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        frame.setMinimumHeight(130)

        root = QVBoxLayout(frame)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # ── Top row: icon + title + STATUS badge (right-aligned) ──
        top_row = QHBoxLayout()

        self._match_icon = QLabel("⚖")
        self._match_icon.setStyleSheet(
            f"font-size: 28px; color: {COLORS['teal_primary']};"
            f"background: {COLORS['bg_input']}; border-radius: 10px; padding: 5px;"
        )
        top_row.addWidget(self._match_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        eq_title = QLabel("معادلة المطابقة")
        eq_title.setStyleSheet(
            f"font-size: {FONT['md']}; font-weight: bold;"
            f"color: {COLORS['text_primary']}; font-family: {FONT['family']};"
        )
        eq_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        eq_sub = QLabel("ميزانية  =  أصول + مديونيات")
        eq_sub.setStyleSheet(
            f"font-size: {FONT['xs']}; color: {COLORS['text_muted']};"
            f"font-family: {FONT['family']};"
        )
        eq_sub.setAlignment(Qt.AlignmentFlag.AlignRight)
        title_col.addWidget(eq_title)
        title_col.addWidget(eq_sub)
        top_row.addLayout(title_col)

        top_row.addStretch()

        self._match_badge = QLabel("جاري...")
        self._match_badge.setFixedHeight(26)
        self._match_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._match_badge.setStyleSheet(
            f"background: {COLORS['bg_input']}; color: {COLORS['text_muted']};"
            f"border-radius: 13px; padding: 0 14px; font-size: {FONT['xs']};"
            f"font-weight: bold; font-family: {FONT['family']};"
        )
        top_row.addWidget(self._match_badge)
        root.addLayout(top_row)

        # ── Divider ──
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {COLORS['border']};")
        root.addWidget(div)

        # ── Bottom: formula breakdown columns ──
        formula_row = QHBoxLayout()
        formula_row.setSpacing(0)

        self._pill_budget  = self._make_formula_pill("الميزانية",     "—", COLORS["teal_primary"])
        self._pill_eq      = self._make_eq_sign("=")
        self._pill_assets  = self._make_formula_pill("الأصول",       "—", COLORS["cyan"])
        self._pill_plus    = self._make_eq_sign("+")
        self._pill_debts   = self._make_formula_pill("المديونيات",   "—", COLORS["yellow"])
        self._pill_eq2     = self._make_eq_sign("=")
        self._pill_net     = self._make_formula_pill("الفرق",         "—", COLORS["green"])

        for w in [self._pill_budget, self._pill_eq,
                  self._pill_assets,  self._pill_plus,
                  self._pill_debts,   self._pill_eq2,
                  self._pill_net]:
            formula_row.addWidget(w)

        root.addLayout(formula_row)
        return frame

    @staticmethod
    def _make_formula_pill(label: str, value: str, color: str) -> QFrame:
        """A pill-shaped breakdown cell used inside the match card."""
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {color}15; border: 1px solid {color}30;"
            f"border-radius: 8px;"
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)

        val_lbl = QLabel(value)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_lbl.setStyleSheet(
            f"color: {color}; font-size: {FONT['lg']}; font-weight: bold;"
            f"font-family: {FONT['family']}; background: transparent; border: none;"
        )
        lay.addWidget(val_lbl)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: {FONT['xs']};"
            f"font-family: {FONT['family']}; background: transparent; border: none;"
        )
        lay.addWidget(lbl)

        # Store reference for update
        frame._val_lbl = val_lbl
        frame._color   = color
        return frame

    @staticmethod
    def _make_eq_sign(sign: str) -> QLabel:
        lbl = QLabel(sign)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFixedWidth(28)
        lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 18px; font-weight: bold;"
        )
        return lbl

    # ─── Recent Ops Table ─────────────────────────────────────

    def _make_ops_table(self) -> QTableWidget:
        columns = ["التاريخ", "العميل", "الخدمة", "المنصة", "المطلوب", "الربح", "الحالة"]
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

        # Column widths
        header = tbl.horizontalHeader()
        widths = [130, 120, 160, 100, 100, 85, 70]
        for i, w in enumerate(widths):
            if w == -1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                tbl.setColumnWidth(i, w)
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        # Let "الخدمة" stretch
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        tbl.verticalHeader().setDefaultSectionSize(48)
        tbl.setStyleSheet(
            f"QTableWidget {{ background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']};"
            f"border-radius: {CARD_RADIUS}; gridline-color: transparent; }}"
            f"QTableWidget::item {{ padding: 8px 16px; border-bottom: 1px solid {COLORS['border']}; }}"
            f"QTableWidget::item:selected {{ background: {COLORS['bg_selected']}; }}"
            f"QTableWidget::item:hover {{ background: {COLORS['bg_hover']}; }}"
            f"QHeaderView::section {{ background: {COLORS['bg_dark']}; color: {COLORS['text_secondary']};"
            f"border: none; border-bottom: 2px solid {COLORS['border']};"
            f"padding: 10px 16px; font-weight: bold; font-size: {FONT['sm']}; }}"
            f"alternate-background-color: {COLORS['bg_elevated']};"
        )
        return tbl

    def _fill_ops_table(self):
        txns = db.get_transactions(limit=15)
        self._ops_table.setRowCount(len(txns))

        status_colors = {
            "cash":    COLORS["green"],
            "pending": COLORS["yellow"],
            "paid":    COLORS["text_muted"],
        }
        status_text = {"cash": "نقدي", "pending": "مؤجل", "paid": "مسدد"}

        for row, t in enumerate(txns):
            def cell(col, text, color=None, bold=False):
                item = QTableWidgetItem(str(text) if text else "—")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if color:
                    item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                self._ops_table.setItem(row, col, item)

            cell(0, (t.get("created_at") or "")[:16],   color=COLORS["text_muted"])
            cell(1, t.get("customer_name") or "—",      color=COLORS["text_secondary"])
            cell(2, t.get("service_name") or "—")
            cell(3, t.get("platform_name") or "—",      color=COLORS["text_muted"])
            cell(4, fmt_currency(t.get("amount_required", 0) or 0), bold=True)

            profit = t.get("profit", 0) or 0
            cell(5, fmt_currency(profit),
                 color=COLORS["green"] if profit >= 0 else COLORS["red"])

            st = t.get("payment_status", "")
            cell(6, status_text.get(st, st), color=status_colors.get(st))

    # ─── Actions Panel ────────────────────────────────────────

    def _make_actions_panel(self) -> QFrame:
        """Row of 5 prominent action buttons."""
        frame = QFrame()
        frame.setObjectName("card")
        frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        row = QHBoxLayout(frame)
        row.setContentsMargins(20, 16, 20, 16)
        row.setSpacing(12)

        actions = [
            ("⊕  إضافة عملية",     "btn_primary",   self._go_to_transaction),
            ("👤  إضافة عميل",     "btn_secondary", self._add_customer),
            ("💵  تعديل الميزانية","btn_secondary", self._edit_budget),
            ("💰  تعديل الكاش",    "btn_secondary", self._edit_cash),
            ("📊  التقارير",       "btn_secondary", self._go_to_reports),
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

    # ─── Refresh ──────────────────────────────────────────────

    def refresh(self):
        stats = db.get_dashboard_stats()

        # Stat cards
        self.card_budget.set_value(fmt_currency(stats["main_budget"]))
        self.card_assets.set_value(fmt_currency(stats["total_assets"]))
        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_wallets.set_value(fmt_currency(stats["total_wallets"]))
        self.card_debts.set_value(fmt_currency(stats["total_debts"]))
        self.card_pending.set_value(fmt_currency(stats["total_pending"]))
        self.card_today.set_value(fmt_currency(stats["today_profit"]))
        self.card_month.set_value(fmt_currency(stats["month_profit"]))

        # Today ops count
        try:
            ops_count = len(db.get_transactions(limit=500))
            # filter today roughly
            from datetime import date
            today_str = date.today().isoformat()
            all_t = db.get_transactions(limit=500)
            ops_today = sum(1 for t in all_t if (t.get("created_at") or "").startswith(today_str))
            self.card_ops.set_value(str(ops_today))
        except Exception:
            self.card_ops.set_value("—")

        # Match equation
        net = stats["net_position"]
        budget  = stats["main_budget"]
        assets  = stats["total_assets"]
        debts   = stats["total_debts"]

        self._pill_budget._val_lbl.setText(fmt_currency(budget))
        self._pill_assets._val_lbl.setText(fmt_currency(assets))
        self._pill_debts._val_lbl.setText(fmt_currency(debts))

        diff_color = COLORS["green"] if abs(net) < 0.01 else (
            COLORS["teal_bright"] if net > 0 else COLORS["red"]
        )
        self._pill_net._val_lbl.setText(fmt_currency(abs(net)))
        self._pill_net._val_lbl.setStyleSheet(
            f"color: {diff_color}; font-size: {FONT['lg']}; font-weight: bold;"
            f"font-family: {FONT['family']}; background: transparent; border: none;"
        )
        self._pill_net.setStyleSheet(
            f"background: {diff_color}15; border: 1px solid {diff_color}30; border-radius: 8px;"
        )

        if abs(net) < 0.01:
            self._match_icon.setText("✓")
            badge_text   = "✅  متطابق"
            badge_style  = (f"background: {COLORS['green_bg']}; color: {COLORS['green']};"
                            f"border: 1px solid {COLORS['green_border']}; border-radius: 13px;"
                            f"padding: 0 14px; font-size: {FONT['xs']}; font-weight: bold;"
                            f"font-family: {FONT['family']};")
        elif net > 0:
            self._match_icon.setText("↑")
            badge_text  = f"↑  فائض  {fmt_currency(net)}"
            badge_style = (f"background: {COLORS['cyan_bg']}; color: {COLORS['teal_bright']};"
                           f"border: 1px solid {COLORS['teal_dark']}; border-radius: 13px;"
                           f"padding: 0 14px; font-size: {FONT['xs']}; font-weight: bold;"
                           f"font-family: {FONT['family']};")
        else:
            self._match_icon.setText("!")
            badge_text  = f"⚠  عجز  {fmt_currency(abs(net))}"
            badge_style = (f"background: {COLORS['red_bg']}; color: {COLORS['red']};"
                           f"border: 1px solid {COLORS['red_border']}; border-radius: 13px;"
                           f"padding: 0 14px; font-size: {FONT['xs']}; font-weight: bold;"
                           f"font-family: {FONT['family']};")

        self._match_badge.setText(badge_text)
        self._match_badge.setStyleSheet(badge_style)

        # Recent transactions
        self._fill_ops_table()

    # ─── Actions ──────────────────────────────────────────────

    def _go_to_transaction(self):
        win = self.window()
        if hasattr(win, "navigate_to"):
            win.navigate_to("transaction")

    def _go_to_reports(self):
        win = self.window()
        if hasattr(win, "navigate_to"):
            win.navigate_to("reports")

    def _add_customer(self):
        name, ok = QInputDialog.getText(self, "إضافة عميل", "أدخل اسم العميل:")
        if ok and name.strip():
            try:
                db.add_customer(name.strip(), 1)
                self.refresh()
                QMessageBox.information(self, "تم ✅", f"تم إضافة العميل: {name}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_budget(self):
        current = db.get_budget()["main_budget"]
        amount, ok = QInputDialog.getDouble(
            self, "تعديل الميزانية",
            "أدخل رأس المال الجديد:",
            value=current, min=0, decimals=2
        )
        if ok:
            try:
                db.update_main_budget(amount)
                self.refresh()
                QMessageBox.information(self, "تم ✅", f"تم تحديث الميزانية إلى {fmt_currency(amount)}")
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
                QMessageBox.information(self, "تم ✅", f"تم تحديث الكاش إلى {fmt_currency(amount)}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))
