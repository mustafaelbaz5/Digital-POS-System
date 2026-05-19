"""
Reports_screen.py — شاشة التقارير والجرد (Pro Dark Edition)
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import (
    BaseDialog,
    CardGroup,
    DataTable,
    DateRangeWidget,
    MiniStatCard,
    ScreenShell,
    Toast,
)
from ui.styles.theme import COLORS, FONT, GAP_LG, GAP_MD, ROW_HEIGHT
from ui.utils.formatters import fmt_currency

# ══════════════════════════════════════════
#  Tab 1: الجرد العام
# ══════════════════════════════════════════


class InventoryTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_LG)

        # ── Date range filter bar
        self.date_picker = DateRangeWidget()
        self.date_picker.changed.connect(self.run_inventory)
        layout.addWidget(self.date_picker)

        # ── Mini stat cards
        stats_group = CardGroup("📊  ملخص الفترة المالي", section_type="accent")
        self._cards_grid = QGridLayout()
        self._cards_grid.setSpacing(GAP_MD)

        self.card_cash = MiniStatCard("الخزينة النقدية", color=COLORS["green"])
        self.card_machines = MiniStatCard("إجمالي الماكينات", color=COLORS["machines"])
        self.card_wallets = MiniStatCard("إجمالي المحافظ", color=COLORS["wallets"])
        self.card_instapay = MiniStatCard("إجمالي انستا باي", color=COLORS["instapay"])
        self.card_debts = MiniStatCard("إجمالي الديون", color=COLORS["yellow"])
        self.card_profit = MiniStatCard("أرباح الفترة", color=COLORS["accent"])
        self.card_budget = MiniStatCard(
            "الميزانية الرئيسية", color=COLORS["text_primary"]
        )
        self.card_pending = MiniStatCard("إجمالي المؤجل", color=COLORS["red"])

        for i, card in enumerate(
            [
                self.card_cash,
                self.card_machines,
                self.card_wallets,
                self.card_instapay,
                self.card_debts,
                self.card_profit,
                self.card_budget,
                self.card_pending,
            ]
        ):
            self._cards_grid.addWidget(card, i // 4, i % 4)

        stats_group.add_layout(self._cards_grid)
        layout.addWidget(stats_group)

        # ── Match equation bar
        layout.addWidget(self._make_match_bar())

        # ── Platforms table
        platforms_group = CardGroup("🏢  تفاصيل أرصدة المنصات", section_type="accent")

        columns = [
            ("المنصة", 180),
            ("النوع", 120),
            ("الرصيد", -1),
            ("الحد الشهري", 130),
            ("المستخدم", -1),
            ("المتبقي", -1),
        ]
        self.platforms_table = DataTable(columns)
        self.platforms_table.set_section_color(COLORS["accent"])
        self.platforms_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        platforms_group.add_widget(self.platforms_table)
        layout.addWidget(platforms_group)

    def _make_match_bar(self) -> QFrame:
        frame = CardGroup("⚖️  معادلة المطابقة")

        header = QHBoxLayout()
        formula = QLabel("(أرصدة + كاش + ديون)  =  (ميزانية + أرباح كلية)")
        formula.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT['xs']};"
        )
        header.addStretch()
        header.addWidget(formula)
        frame.add_layout(header)

        row = QHBoxLayout()
        row.setSpacing(GAP_MD)

        # Right side
        self._match_right = QLabel("—")
        self._match_right.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: bold;"
        )
        self._match_right.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Result badge
        self._match_result = QLabel("—")
        self._match_result.setFixedWidth(180)
        self._match_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._match_result.setStyleSheet(
            f"border-radius: 8px; padding: 8px 12px;"
            f"background: {COLORS['bg_elevated']}; color: {COLORS['text_secondary']};"
            f"font-size: 13px; font-weight: bold; border: 1px solid {COLORS['border']};"
        )

        eq = QLabel("=")
        eq.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 20px;")

        # Left side
        self._match_left = QLabel("—")
        self._match_left.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: bold;"
        )
        self._match_left.setAlignment(Qt.AlignmentFlag.AlignCenter)

        row.addWidget(self._match_right)
        row.addWidget(eq)
        row.addWidget(self._match_result)
        row.addWidget(eq := QLabel("="))
        eq.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 20px;")
        row.addWidget(self._match_left)

        frame.add_layout(row)

        self._match_breakdown = QLabel("")
        self._match_breakdown.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT['xs']};"
        )
        self._match_breakdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame.add_widget(self._match_breakdown)

        return frame

    def run_inventory(self):
        date_from, date_to = self.date_picker.get_range()

        stats = db.get_dashboard_stats()
        platforms = db.get_all_platforms()

        period_txns = db.get_transactions(
            date_from=date_from, date_to=date_to, limit=5000
        )
        # احسب الربح من العمليات الفعلية فقط (استثني manual_commission و inbound)
        period_profit = sum(
            t.get("profit", 0) or 0
            for t in period_txns
            if t.get("payment_status") != "cash"
            and t.get("operation_type") not in ("manual_commission", "inbound")
        )

        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_machines.set_value(fmt_currency(stats["total_machines"]))
        self.card_wallets.set_value(fmt_currency(stats["total_wallets"]))
        self.card_instapay.set_value(fmt_currency(stats.get("total_instapay", 0)))
        self.card_debts.set_value(
            fmt_currency(stats["total_debts"]),
            color=COLORS["yellow"] if stats["total_debts"] > 0 else COLORS["green"],
        )
        self.card_profit.set_value(
            fmt_currency(period_profit),
            color=COLORS["accent"] if period_profit >= 0 else COLORS["red"],
        )
        self.card_budget.set_value(fmt_currency(stats["injected_capital"]))
        self.card_pending.set_value(
            fmt_currency(stats.get("total_pending", 0)),
            color=(
                COLORS["red"]
                if stats.get("total_pending", 0) > 0
                else COLORS["text_secondary"]
            ),
        )

        left_side = stats["total_assets"]
        right_side = stats["injected_capital"]
        diff = stats["asset_reconciliation"]

        self._match_left.setText(fmt_currency(left_side))
        self._match_right.setText(fmt_currency(right_side))

        breakdown = (
            f"الأصول = كاش [{fmt_currency(stats['cash_vault'])}] + "
            f"ماكينات [{fmt_currency(stats['total_machines'])}] + "
            f"محافظ [{fmt_currency(stats['total_wallets'])}] + "
            f"ديون [{fmt_currency(stats['total_debts'])}]"
        )
        if hasattr(self, "_match_breakdown"):
            self._match_breakdown.setText(breakdown)

        if abs(diff) < 0.01:
            self._match_result.setText("  متطابق")
            self._match_result.setStyleSheet(
                f"border-radius: 8px; padding: 8px 12px;"
                f"background: {COLORS['settle']}; color: {COLORS['text_on_dark']};"
                f"font-size: 13px; font-weight: bold;"
            )
        elif diff > 0:
            self._match_result.setText(f"📈 فائض\n{fmt_currency(diff)}")
            self._match_result.setStyleSheet(
                f"border-radius: 8px; padding: 8px 12px;"
                f"background: {COLORS['save']}; color: {COLORS['text_on_dark']};"
                f"font-size: 13px; font-weight: bold;"
            )
        else:
            self._match_result.setText(f"⚠️ عجز\n{fmt_currency(abs(diff))}")
            self._match_result.setStyleSheet(
                f"border-radius: 8px; padding: 8px 12px;"
                f"background: {COLORS['delete']}; color: {COLORS['text_on_dark']};"
                f"font-size: 13px; font-weight: bold;"
            )

        self.platforms_table.clear_rows()
        self.platforms_table.setRowCount(len(platforms))

        for row, p in enumerate(platforms):
            p_type = p["type"]
            if p_type == "machine":
                type_text, type_color = "🏧 ماكينة", COLORS["blue"]
            elif p_type == "wallet":
                type_text, type_color = "💳 محفظة", COLORS["purple"]
            else:
                type_text, type_color = "🔷 انستا باي", COLORS["cyan"]

            self.platforms_table.set_cell(row, 0, p["name"], bold=True)
            self.platforms_table.set_cell(row, 1, type_text, color=type_color)
            self.platforms_table.set_cell(
                row, 2, fmt_currency(p.get("balance", 0)), color=COLORS["accent"]
            )

            if p_type != "machine":
                limit = p.get("monthly_limit", 200000)
                used = p.get("monthly_used", 0)
                remaining = limit - used
                rem_color = (
                    COLORS["red"] if remaining < 10000 else COLORS["text_secondary"]
                )
                self.platforms_table.set_cell(row, 3, fmt_currency(limit))
                self.platforms_table.set_cell(
                    row, 4, fmt_currency(used), color=COLORS["yellow"]
                )
                self.platforms_table.set_cell(
                    row, 5, fmt_currency(remaining), color=rem_color
                )
            else:
                for col in [3, 4, 5]:
                    self.platforms_table.set_cell(
                        row, col, "—", color=COLORS["text_muted"]
                    )

        # Adjust table height to content (fixed look, scroll with page)
        h = (
            self.platforms_table.horizontalHeader().height()
            + (len(platforms) * ROW_HEIGHT)
            + 4
        )
        self.platforms_table.setMinimumHeight(h)
        self.platforms_table.setMaximumHeight(h)


# ══════════════════════════════════════════
#  Tab 2: سجل العمليات
# ══════════════════════════════════════════


class TransactionsLogTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_LG)

        # ── Date picker (first section)
        self.date_picker = DateRangeWidget()
        self.date_picker.changed.connect(self.load_data)
        layout.addWidget(self.date_picker)

        # ── Filters Card
        filters_group = CardGroup("🔍  فلترة العمليات")
        fl = QHBoxLayout()
        fl.setSpacing(GAP_MD)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("بحث برقم المرجع...")
        self.ref_input.setFixedHeight(34)
        self.ref_input.setFixedWidth(200)
        self.ref_input.textChanged.connect(self.load_data)
        fl.addWidget(self.ref_input)

        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(34)
        self.status_filter.setMinimumWidth(120)
        self.status_filter.addItem("كل الحالات", None)
        self.status_filter.addItem("⏳ مؤجل", "pending")
        self.status_filter.addItem(" تم السداد", "paid")
        self.status_filter.addItem("⏳ لم يسلم", "not_delivered")
        self.status_filter.addItem(" تم التسليم", "delivered")
        self.status_filter.currentIndexChanged.connect(self.load_data)
        fl.addWidget(self.status_filter)

        self.platform_filter = QComboBox()
        self.platform_filter.setFixedHeight(34)
        self.platform_filter.setMinimumWidth(140)
        self.platform_filter.currentIndexChanged.connect(self.load_data)
        fl.addWidget(self.platform_filter)

        fl.addStretch()
        filters_group.add_layout(fl)
        layout.addWidget(filters_group)

        # ── Table Card
        table_group = CardGroup("  سجل العمليات")

        columns = [
            ("التاريخ", 140),
            ("المرجع", 90),
            ("الخدمة", 130),
            ("المنصة", 110),
            ("العميل", -1),
            ("المطلوب", -1),
            ("المصروف", 90),
            ("الربح", 90),
            ("الحالة", -1),
            ("إجراءات", 150),
        ]
        self.table = DataTable(columns)
        self.table.set_section_color(COLORS["blue"])
        table_group.add_widget(self.table)

        self.summary_lbl = QLabel("")
        self.summary_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT['sm']};"
        )
        table_group.add_widget(self.summary_lbl)

        layout.addWidget(table_group)

    def load_platforms_filter(self):
        self.platform_filter.clear()
        self.platform_filter.addItem("كل المنصات", None)
        for p in db.get_all_platforms():
            self.platform_filter.addItem(p["name"], p["id"])

    def load_data(self):
        date_from, date_to = self.date_picker.get_range()
        status = self.status_filter.currentData()
        platform_id = self.platform_filter.currentData()
        ref = self.ref_input.text().strip()

        if ref:
            txns = db.search_by_reference(ref)
        else:
            is_del = None
            pay_st = status
            if status == "delivered":
                is_del = 1
                pay_st = None
            elif status == "not_delivered":
                is_del = 0
                pay_st = None

            txns = db.get_transactions(
                platform_id=platform_id,
                payment_status=pay_st,
                date_from=date_from,
                date_to=date_to,
                is_delivered=is_del,
                limit=1000,
            )
        self._render(txns)

    def _render(self, transactions: list):
        from ui.components.misc import make_txn_actions

        self.table.clear_rows()
        self.table.setRowCount(len(transactions))
        total_profit = total_required = 0

        for row, t in enumerate(transactions):
            op = t.get("operation_type")
            is_manual = op in ("manual_commission", "inbound")
            bg = COLORS["bg_hover"] if is_manual else None

            dt = (t.get("created_at") or "")[:16].replace("T", " ")
            self.table.set_cell(row, 0, dt, color=COLORS["text_secondary"], bg_color=bg)

            # المرجع
            ref = t.get("reference_no") or f"#{t.get('id')}"
            self.table.set_cell(row, 1, ref, color=COLORS["text_muted"], bg_color=bg)

            self.table.set_cell(row, 2, t.get("service_name") or "—", bg_color=bg)
            self.table.set_cell(
                row, 3, t.get("platform_name") or "—", color=COLORS["text_secondary"], bg_color=bg
            )
            self.table.set_cell(row, 4, t.get("customer_name") or "—", bold=True, bg_color=bg)

            required = t.get("amount_required", 0) or 0
            spent = t.get("amount_spent", 0) or 0
            profit = t.get("profit", 0) or 0

            self.table.set_cell(row, 5, fmt_currency(required), bold=True, bg_color=bg)
            self.table.set_cell(
                row, 6, fmt_currency(spent), color=COLORS["text_secondary"], bg_color=bg
            )
            profit_text = fmt_currency(profit) if not is_manual else "—"
            profit_color = COLORS["accent"] if profit >= 0 else COLORS["red"]
            if is_manual:
                profit_color = COLORS["text_secondary"]

            self.table.set_cell(
                row,
                7,
                profit_text,
                color=profit_color,
                bg_color=bg,
            )

            self.table.add_status_badge(
                row,
                8,
                t.get("payment_status", ""),
                operation_type=t.get("operation_type", "outbound"),
                is_delivered=t.get("is_delivered", 0),
            )

            actions = make_txn_actions(t, self._on_delete)
            self.table.setCellWidget(row, 9, actions)

            total_profit += profit
            total_required += required

        self.summary_lbl.setText(
            f"العمليات: {len(transactions)}  ·  إجمالي المطلوب: {fmt_currency(total_required)}  ·  إجمالي الربح: {fmt_currency(total_profit)}"
        )

    def _on_delete(self, tid: int):
        if (
            QMessageBox.question(
                self,
                "تأكيد الحذف",
                "⚠️ حذف العملية وعكس تأثيرها المالي؟ لا يمكن التراجع.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            try:
                db.delete_transaction(tid)
                self.load_data()
                QMessageBox.information(self, "تم ", "تم حذف العملية")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════
#  Reports Screen (main)
# ══════════════════════════════════════════


class ReportsScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__(
            "التقارير والجرد", "إدارة العمليات والجرد المالي"
        )
        self._build_content()

    def _build_content(self):
        c = self.content()
        c.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.inventory_tab = InventoryTab()
        self.tabs.addTab(self.inventory_tab, "📊  الجرد المالي")

        self.log_tab = TransactionsLogTab()
        self.tabs.addTab(self.log_tab, "  سجل العمليات")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        c.addWidget(self.tabs)

    def refresh(self):
        self._on_tab_changed(self.tabs.currentIndex())

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.inventory_tab.run_inventory()
        elif index == 1:
            self.log_tab.load_platforms_filter()
            self.log_tab.load_data()
