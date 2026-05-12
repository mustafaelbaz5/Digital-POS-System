"""
dashboard.py — لوحة التحكم الرئيسية (Redesigned v3)
"""

from datetime import date, datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import BaseDialog, CardGroup, ScreenShell, StatCard
from ui.styles.theme import COLORS, FONT, GAP_LG, GAP_MD, GAP_SM, ROW_HEIGHT, CARD_RADIUS
from utils.formatters import fmt_currency


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

        # ── Row 2: Quick search + Quick actions ────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(GAP_MD)

        search_group = CardGroup("بحث سريع عن عميل")
        search_group.add_widget(self._make_search_panel())
        row2.addWidget(search_group, 1)

        actions_group = CardGroup("الإجراءات السريعة")
        actions_group.add_widget(self._make_actions_panel())
        row2.addWidget(actions_group, 1)

        row2_widget = QWidget()
        row2_widget.setLayout(row2)
        c.addWidget(row2_widget)

        # ── Row 3: Top Debtors + Recent Transactions ───────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(GAP_MD)

        debtors_group = CardGroup("أعلى المديونيات")
        self._debtors_container = QVBoxLayout()
        self._debtors_container.setSpacing(GAP_SM)
        debtors_group.add_layout(self._debtors_container)
        row3.addWidget(debtors_group, 1)

        ops_group = CardGroup("آخر العمليات")
        self._ops_table = self._make_ops_table()
        ops_group.add_widget(self._ops_table)
        row3.addWidget(ops_group, 2)

        row3_widget = QWidget()
        row3_widget.setLayout(row3)
        c.addWidget(row3_widget)

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

            debt = cust.get("total_debt", 0) or 0
            if debt > 0:
                debt_lbl = QLabel(fmt_currency(debt))
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

    # ── Ops Table ──────────────────────────────────────────────────────────

    def _make_ops_table(self) -> QTableWidget:
        columns = ["التاريخ", "العميل", "الخدمة", "المنصة", "المطلوب", "الربح", "الحالة"]
        tbl = QTableWidget()
        tbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        tbl.setColumnCount(len(columns))
        tbl.setHorizontalHeaderLabels(columns)
        tbl.setMaximumHeight(340)
        tbl.setMinimumHeight(220)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = tbl.horizontalHeader()
        widths = [140, -1, 130, 120, -1, 100, -1]
        for i, w in enumerate(widths):
            if w == -1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                tbl.setColumnWidth(i, w)
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        tbl.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        return tbl

    def _fill_ops_table(self):
        txns = db.get_transactions(limit=12)
        self._ops_table.setRowCount(len(txns))

        for row, t in enumerate(txns):
            op_type = t.get("operation_type")
            is_manual = op_type in ("manual_commission", "inbound")
            bg_color = COLORS["bg_hover"] if is_manual else None

            def cell(col, text, color=None, bold=False, bg=bg_color):
                item = QTableWidgetItem(str(text) if text else "—")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if color:
                    item.setForeground(QColor(color))
                if bg:
                    item.setBackground(QColor(bg))
                if bold:
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                self._ops_table.setItem(row, col, item)

            raw_date = t.get("created_at") or ""
            cell(0, raw_date[:16].replace("T", " "), color=COLORS["text_secondary"])
            cell(1, t.get("customer_name") or "—", bold=True)
            cell(2, t.get("service_name") or "—")
            cell(3, t.get("platform_name") or "—", color=COLORS["text_secondary"])
            cell(4, fmt_currency(t.get("amount_required", 0) or 0), bold=True)

            profit = t.get("profit", 0) or 0
            profit_text = fmt_currency(profit) if not is_manual else "—"
            profit_color = COLORS["accent"] if profit >= 0 else COLORS["red"]
            if is_manual:
                profit_color = COLORS["text_secondary"]
            cell(5, profit_text, color=profit_color)

            st = t.get("payment_status", "")
            if op_type == "inbound":
                is_del = bool(t.get("is_delivered", 0))
                st_text = "تم التسليم ✓" if is_del else "لم يسلم ⏳"
                st_color = COLORS["green"] if is_del else COLORS["yellow"]
            else:
                st_text = "مؤجل ⏳" if st == "pending" else "تم السداد ✓"
                st_color = COLORS["yellow"] if st == "pending" else COLORS["green"]
            cell(6, st_text, color=st_color, bold=True)

    # ── Top Debtors ────────────────────────────────────────────────────────

    def _fill_debtors(self):
        while self._debtors_container.count():
            item = self._debtors_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            customers = db.get_all_customers()
            debtors = sorted(
                [c for c in customers if (c.get("total_debt") or 0) > 0],
                key=lambda c: c.get("total_debt", 0),
                reverse=True,
            )[:6]

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
                    cust.get("total_debt", 0),
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

        self._fill_ops_table()
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
            from utils.google_sheets import export_to_sheets
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
