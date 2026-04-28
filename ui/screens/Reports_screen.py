"""
Reports_screen.py — شاشة التقارير والجرد
Refactored: ScreenShell, fixed heavy query in inventory, cleaner layout
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QDateEdit,
    QComboBox, QMessageBox, QGridLayout, QSizePolicy,
    QLineEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ui.styles.theme import COLORS
from ui.components.widgets import ScreenShell, DataTable, SectionTitle, make_divider
from utils.formatters import fmt_currency

import database as db


# ══════════════════════════════════════════
#  Mini Stat Card (local)
# ══════════════════════════════════════════

class MiniStatCard(QFrame):
    def __init__(self, title: str, value: str = "—", color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(150)
        self.setMinimumHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        self._val_lbl = QLabel(value)
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._val_lbl.setStyleSheet(
            f"color: {color or COLORS['text_primary']}; font-size: 18px; font-weight: bold;"
        )
        layout.addWidget(self._val_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_lbl.setObjectName("label_muted")
        layout.addWidget(title_lbl)

    def set_value(self, value: str, color: str = None):
        self._val_lbl.setText(value)
        if color:
            self._val_lbl.setStyleSheet(
                f"color: {color}; font-size: 18px; font-weight: bold;"
            )


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
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(14)

        # ── Date range filter bar
        filter_bar = QFrame()
        filter_bar.setObjectName("card")
        fb_layout = QHBoxLayout(filter_bar)
        fb_layout.setContentsMargins(16, 10, 16, 10)
        fb_layout.setSpacing(10)

        run_btn = QPushButton("🔍  تشغيل الجرد")
        run_btn.setObjectName("btn_primary")
        run_btn.setFixedHeight(36)
        run_btn.clicked.connect(self.run_inventory)
        fb_layout.addWidget(run_btn)

        fb_layout.addStretch()

        for lbl_text, attr, days_offset in [
            ("إلى:", "date_to", 0),
            ("من:",  "date_from", -30),
        ]:
            lbl = QLabel(lbl_text)
            lbl.setObjectName("label_muted")
            fb_layout.addWidget(lbl)

            de = QDateEdit(QDate.currentDate().addDays(days_offset))
            de.setCalendarPopup(True)
            de.setFixedHeight(34)
            de.setFixedWidth(120)
            setattr(self, attr, de)
            fb_layout.addWidget(de)

        layout.addWidget(filter_bar)

        # ── Mini stat cards
        self._cards_grid = QGridLayout()
        self._cards_grid.setSpacing(10)
        layout.addLayout(self._cards_grid)

        self.card_cash     = MiniStatCard("الخزينة النقدية",    color=COLORS["green"])
        self.card_machines = MiniStatCard("إجمالي الماكينات",  color=COLORS["blue"])
        self.card_wallets  = MiniStatCard("إجمالي المحافظ",    color=COLORS["purple"])
        self.card_instapay = MiniStatCard("إجمالي انستا باي",  color=COLORS["cyan"])
        self.card_debts    = MiniStatCard("إجمالي الديون",     color=COLORS["yellow"])
        self.card_profit   = MiniStatCard("أرباح الفترة",      color=COLORS["green"])
        self.card_budget   = MiniStatCard("الميزانية الرئيسية",color=COLORS["text_primary"])
        self.card_pending  = MiniStatCard("إجمالي المؤجل",     color=COLORS["yellow"])

        for i, card in enumerate([
            self.card_cash, self.card_machines, self.card_wallets, self.card_instapay,
            self.card_debts, self.card_profit, self.card_budget, self.card_pending,
        ]):
            self._cards_grid.addWidget(card, i // 4, i % 4)

        # ── Match equation bar
        layout.addWidget(self._make_match_bar())

        # ── Platforms table
        sec_lbl = QLabel("تفاصيل المنصات")
        sec_lbl.setObjectName("label_subtitle")
        sec_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: bold;"
            f"text-transform: uppercase; letter-spacing: 0.5px;"
        )
        layout.addWidget(sec_lbl)

        columns = [
            ("المنصة",       180),
            ("النوع",          120),
            ("الرصيد",        -1),
            ("الحد الشهري",   130),
            ("المستخدم",      -1),
            ("المتبقي",       -1),
        ]
        self.platforms_table = DataTable(columns)
        self.platforms_table.setMaximumHeight(200)
        layout.addWidget(self.platforms_table)
        layout.addStretch()

    def _make_match_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card_highlight")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("⚖️  معادلة المطابقة")
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: bold;"
        )
        header.addWidget(title)
        header.addStretch()
        formula = QLabel("(أرصدة + كاش + ديون)  =  (ميزانية + أرباح كلية)")
        formula.setObjectName("label_muted")
        header.addWidget(formula)
        layout.addLayout(header)

        row = QHBoxLayout()
        row.setSpacing(12)

        # Left side (أرصدة+كاش+ديون)
        self._match_left = QLabel("—")
        self._match_left.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: bold;"
        )
        self._match_left.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Result badge
        self._match_result = QLabel("—")
        self._match_result.setFixedWidth(160)
        self._match_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._match_result.setStyleSheet(
            f"border-radius: 8px; padding: 6px 10px;"
            f"background: {COLORS['bg_input']}; color: {COLORS['text_muted']};"
            f"font-size: 12px; font-weight: bold;"
        )

        eq = QLabel("=")
        eq.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px;")
        eq.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Right side (ميزانية+أرباح)
        self._match_right = QLabel("—")
        self._match_right.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: bold;"
        )
        self._match_right.setAlignment(Qt.AlignmentFlag.AlignCenter)

        row.addWidget(self._match_right)
        row.addWidget(eq)
        row.addWidget(self._match_result)
        row.addWidget(eq := QLabel("="))
        eq.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px;")
        eq.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self._match_left)

        layout.addLayout(row)

        # سطر تفاصيل التوزيع
        self._match_breakdown = QLabel("")
        self._match_breakdown.setObjectName("label_muted")
        self._match_breakdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._match_breakdown)

        return frame

    def run_inventory(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to   = self.date_to.date().toString("yyyy-MM-dd")

        if self.date_from.date() > self.date_to.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return

        # Fetch data — use dashboard stats for current snapshot
        stats     = db.get_dashboard_stats()
        budget    = db.get_budget()
        platforms = db.get_all_platforms()

        # Period profit — use reasonable limit not 100k
        period_txns   = db.get_transactions(date_from=date_from, date_to=date_to, limit=5000)
        period_profit = sum(t.get("profit", 0) or 0 for t in period_txns)

        # Update mini cards
        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_machines.set_value(fmt_currency(stats["total_machines"]))
        self.card_wallets.set_value(fmt_currency(stats["total_wallets"]))
        self.card_instapay.set_value(fmt_currency(stats.get("total_instapay", 0)))
        self.card_debts.set_value(
            fmt_currency(stats["total_debts"]),
            color=COLORS["yellow"] if stats["total_debts"] > 0 else COLORS["green"]
        )
        self.card_profit.set_value(
            fmt_currency(period_profit),
            color=COLORS["green"] if period_profit >= 0 else COLORS["red"]
        )
        self.card_budget.set_value(fmt_currency(budget["main_budget"]))
        self.card_pending.set_value(
            fmt_currency(stats.get("total_pending", 0)),
            color=COLORS["yellow"] if stats.get("total_pending", 0) > 0 else COLORS["text_muted"]
        )

        # Match equation — use stats for total profit (single efficient query)
        all_txns      = db.get_transactions(limit=5000)
        total_profit  = sum(t.get("profit", 0) or 0 for t in all_txns)
        left_side     = stats["total_balances"] + stats["total_debts"]
        right_side    = budget["main_budget"] + total_profit
        diff          = left_side - right_side

        self._match_left.setText(fmt_currency(left_side))
        self._match_right.setText(fmt_currency(right_side))

        # تفاصيل التوزيع: الميزانية = كاش + ماكينات + محافظ
        breakdown = (
            f"الميزانية = كاش [{fmt_currency(stats['cash_vault'])}] + "
            f"ماكينات [{fmt_currency(stats['total_machines'])}] + "
            f"محافظ [{fmt_currency(stats['total_wallets'])}]"
        )
        if hasattr(self, "_match_breakdown"):
            self._match_breakdown.setText(breakdown)

        if abs(diff) < 0.01:
            self._match_result.setText("✅  متطابق")
            self._match_result.setStyleSheet(
                f"border-radius: 8px; padding: 6px 10px;"
                f"background: {COLORS['green_bg']}; color: {COLORS['green']};"
                f"font-size: 12px; font-weight: bold; border: 1px solid {COLORS['green_border']};"
            )
        elif diff > 0:
            self._match_result.setText(f"📈 فائض\n{fmt_currency(diff)}")
            self._match_result.setStyleSheet(
                f"border-radius: 8px; padding: 6px 10px;"
                f"background: {COLORS['blue_bg']}; color: {COLORS['blue']};"
                f"font-size: 12px; font-weight: bold;"
            )
        else:
            self._match_result.setText(f"⚠️ عجز\n{fmt_currency(abs(diff))}")
            self._match_result.setStyleSheet(
                f"border-radius: 8px; padding: 6px 10px;"
                f"background: {COLORS['red_bg']}; color: {COLORS['red']};"
                f"font-size: 12px; font-weight: bold; border: 1px solid {COLORS['red_border']};"
            )

        # Platforms table
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
            is_machine = (p_type == "machine")

            self.platforms_table.set_cell(row, 0, p["name"], bold=True)
            self.platforms_table.set_cell(row, 1, type_text, color=type_color)
            self.platforms_table.set_cell(row, 2, fmt_currency(p.get("balance", 0)),
                                          color=COLORS["green"])

            if not is_machine:
                limit     = p.get("monthly_limit", 200000)
                used      = p.get("monthly_used", 0)
                remaining = limit - used
                rem_color = COLORS["red"] if remaining < 10000 else COLORS["text_secondary"]
                self.platforms_table.set_cell(row, 3, fmt_currency(limit))
                self.platforms_table.set_cell(row, 4, fmt_currency(used), color=COLORS["yellow"])
                self.platforms_table.set_cell(row, 5, fmt_currency(remaining), color=rem_color)
            else:
                for col in [3, 4, 5]:
                    self.platforms_table.set_cell(row, col, "—", color=COLORS["text_muted"])


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
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)

        # ── شريط البحث بالمرجع
        ref_frame = QFrame()
        ref_frame.setObjectName("card")
        rl = QHBoxLayout(ref_frame)
        rl.setContentsMargins(14, 8, 14, 8)
        rl.setSpacing(8)

        ref_search_btn = QPushButton("🔍  بحث بالمرجع")
        ref_search_btn.setObjectName("btn_secondary")
        ref_search_btn.setFixedHeight(32)
        ref_search_btn.clicked.connect(self._search_by_ref)
        rl.addWidget(ref_search_btn)

        clear_btn = QPushButton("✕  مسح")
        clear_btn.setObjectName("btn_secondary")
        clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self._clear_ref_search)
        rl.addWidget(clear_btn)

        rl.addStretch()

        ref_lbl = QLabel("رقم المرجع / رقم العملية:")
        ref_lbl.setObjectName("label_muted")
        rl.addWidget(ref_lbl)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("ابحث برقم المرجع أو رقم العملية...")
        self.ref_input.setFixedHeight(100)
        self.ref_input.setFixedWidth(280)
        self.ref_input.returnPressed.connect(self._search_by_ref)
        rl.addWidget(self.ref_input)

        layout.addWidget(ref_frame)

        # ── Filter bar
        filter_frame = QFrame()
        filter_frame.setObjectName("card")
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(14, 8, 14, 8)
        fl.setSpacing(8)

        search_btn = QPushButton("🔍  بحث")
        search_btn.setObjectName("btn_primary")
        search_btn.setFixedHeight(32)
        search_btn.clicked.connect(self.load_data)
        fl.addWidget(search_btn)

        fl.addStretch()

        # Status
        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(100)
        self.status_filter.setMinimumWidth(110)
        self.status_filter.addItem("كل الحالات", None)
        self.status_filter.addItem("⏳ مؤجل",    "pending")
        self.status_filter.addItem("مسدد",    "paid")
        fl.addWidget(self.status_filter)

        # Type
        self.type_filter = QComboBox()
        self.type_filter.setFixedHeight(100)
        self.type_filter.setMinimumWidth(120)
        self.type_filter.addItem("كل الأنواع",  None)
        self.type_filter.addItem("📤 صادر",     "outbound")
        self.type_filter.addItem("📥 وارد",     "inbound")
        fl.addWidget(self.type_filter)

        # Platform
        self.platform_filter = QComboBox()
        self.platform_filter.setFixedHeight(100)
        self.platform_filter.setMinimumWidth(130)
        fl.addWidget(self.platform_filter)

        # Dates
        for lbl_text, attr, days in [("إلى:", "date_to", 0), ("من:", "date_from", -30)]:
            lbl = QLabel(lbl_text)
            lbl.setObjectName("label_muted")
            fl.addWidget(lbl)
            de = QDateEdit(QDate.currentDate().addDays(days))
            de.setCalendarPopup(True)
            de.setFixedHeight(100)
            de.setFixedWidth(115)
            setattr(self, attr, de)
            fl.addWidget(de)

        layout.addWidget(filter_frame)

        # ── Table
        columns = [
            ("التاريخ والوقت", 150),
            ("النوع",           75),
            ("الخدمة",         150),
            ("المنصة",         110),
            ("العميل",         -1),
            ("المصروف",        100),
            ("المطلوب",        100),
            ("الربح",           -1),
            ("المرجع",         -1),
            ("الحالة",          120),
            ("إجراءات",       200),
        ]
        self.table = DataTable(columns)
        self.table.verticalHeader().setDefaultSectionSize(80)
        layout.addWidget(self.table)

        # Summary
        self.summary_lbl = QLabel("")
        self.summary_lbl.setObjectName("label_muted")
        self.summary_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.summary_lbl)

    def load_platforms_filter(self):
        current = self.platform_filter.currentData()
        self.platform_filter.blockSignals(True)
        self.platform_filter.clear()
        self.platform_filter.addItem("كل المنصات", None)
        for p in db.get_all_platforms():
            icon = "🏧" if p["type"] == "machine" else "💳"
            self.platform_filter.addItem(f"{icon} {p['name']}", p["id"])
        idx = self.platform_filter.findData(current)
        self.platform_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.platform_filter.blockSignals(False)

    def load_data(self):
        date_from   = self.date_from.date().toString("yyyy-MM-dd") # type: ignore
        date_to     = self.date_to.date().toString("yyyy-MM-dd")
        status      = self.status_filter.currentData()
        platform_id = self.platform_filter.currentData()

        txns = db.get_transactions(
            platform_id    = platform_id,
            payment_status = status,
            date_from      = date_from,
            date_to        = date_to,
            limit          = 1000
        )

        op_type = self.type_filter.currentData()
        if op_type:
            txns = [t for t in txns if t["operation_type"] == op_type]

        self._render(txns)

    def _render(self, transactions: list):
        from ui.screens.statement_screen import make_txn_actions
        self.table.clear_rows()
        self.table.setRowCount(len(transactions))
        total_profit = total_spent = total_required = 0
        for row, t in enumerate(transactions):
            dt = (t.get("created_at") or "")[:16]
            self.table.set_cell(row, 0, dt, color=COLORS["text_muted"])
            op = t.get("operation_type", "")
            self.table.set_cell(row, 1, "📤 صادر" if op == "outbound" else "📥 وارد",
                color=COLORS["blue"] if op == "outbound" else COLORS["purple"])
            self.table.set_cell(row, 2, t.get("service_name") or "—")
            self.table.set_cell(row, 3, t.get("platform_name") or "—", color=COLORS["text_secondary"])
            self.table.set_cell(row, 4, t.get("customer_name") or "—", color=COLORS["text_secondary"])
            spent    = t.get("amount_spent", 0) or 0
            required = t.get("amount_required", 0) or 0
            profit   = t.get("profit", 0) or 0
            self.table.set_cell(row, 5, fmt_currency(spent))
            self.table.set_cell(row, 6, fmt_currency(required), bold=True)
            self.table.set_cell(row, 7, fmt_currency(profit),
                color=COLORS["green"] if profit >= 0 else COLORS["red"])
            ref = "🃏 كارت" if t.get("is_card") else (t.get("reference_no") or "—")
            self.table.set_cell(row, 8, ref, color=COLORS["text_muted"])
            self.table.add_status_badge(
                row, 9,
                t.get("payment_status", ""),
                operation_type=t.get("operation_type", "outbound"),
                is_delivered=t.get("is_delivered", 0)
            )
            actions = make_txn_actions(t, self._on_status_change, self._on_delete)
            self.table.setCellWidget(row, 10, actions)
            total_profit   += profit
            total_spent    += spent
            total_required += required
        p_color = COLORS["green"] if total_profit > 0 else (COLORS["red"] if total_profit < 0 else COLORS["text_muted"])
        self.summary_lbl.setText(
            f"العمليات: {len(transactions)}  ·  مصروف: {fmt_currency(total_spent)}  ·  "
            f"مطلوب: {fmt_currency(total_required)}  ·  ربح: {fmt_currency(total_profit)}"
        )
        self.summary_lbl.setStyleSheet(f"color: {p_color}; font-size: 11px;")

    def _search_by_ref(self):
        ref = self.ref_input.text().strip()
        if not ref:
            return
        txns = db.search_by_reference(ref)
        self._render(txns)

    def _clear_ref_search(self):
        self.ref_input.clear()
        self.load_data()

    def _on_status_change(self, tid: int, new_status: str):
        # الديالوج خلاص سأل المستخدم — ننفذ مباشرة بدون سؤال تاني
        try:
            db.update_transaction_status(tid, new_status)
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _on_delete(self, tid: int):
        if QMessageBox.question(self, "تأكيد الحذف",
            "⚠️ حذف العملية وعكس تأثيرها المالي؟ لا يمكن التراجع.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            try:
                db.delete_transaction(tid)
                self.load_data()
                QMessageBox.information(self, "تم ✅", "تم حذف العملية")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))


class CleanupTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(14)

        # ── Paid stats bar
        stat_frame = QFrame()
        stat_frame.setObjectName("card")
        stat_layout = QHBoxLayout(stat_frame)
        stat_layout.setContentsMargins(16, 10, 16, 10)

        refresh_btn = QPushButton("🔄  تحديث الإحصائية")
        refresh_btn.setObjectName("btn_secondary")
        refresh_btn.setFixedHeight(34)
        refresh_btn.clicked.connect(self._refresh_stat)
        stat_layout.addWidget(refresh_btn)
        stat_layout.addStretch()

        self.stat_label = QLabel("اضغط تحديث لعرض عدد العمليات المسددة")
        self.stat_label.setObjectName("label_muted")
        self.stat_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        stat_layout.addWidget(self.stat_label)
        layout.addWidget(stat_frame)

        # ── Single customer cleanup
        single_frame = QFrame()
        single_frame.setObjectName("card")
        sl = QVBoxLayout(single_frame)
        sl.setContentsMargins(18, 14, 18, 14)
        sl.setSpacing(10)

        sh = QHBoxLayout()
        s_title = QLabel("🧹  تنظيف عميل واحد")
        s_title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: bold;"
        )
        sh.addWidget(s_title)
        sh.addStretch()
        sl.addLayout(sh)

        s_desc = QLabel("حذف العمليات المسددة (paid) لعميل محدد فقط. العمليات المؤجلة لا تُمس.")
        s_desc.setObjectName("label_muted")
        s_desc.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sl.addWidget(s_desc)

        s_row = QHBoxLayout()
        s_row.setSpacing(10)

        clean_s_btn = QPushButton("تنظيف العميل المحدد")
        clean_s_btn.setObjectName("btn_danger")
        clean_s_btn.setFixedHeight(36)
        clean_s_btn.clicked.connect(self._cleanup_single)
        s_row.addWidget(clean_s_btn)

        s_row.addStretch()

        self.customer_combo = QComboBox()
        self.customer_combo.setFixedHeight(36)
        self.customer_combo.setMinimumWidth(200)
        s_row.addWidget(self.customer_combo)

        c_lbl = QLabel("اختر العميل:")
        c_lbl.setObjectName("label_muted")
        s_row.addWidget(c_lbl)

        sl.addLayout(s_row)
        layout.addWidget(single_frame)

        # ── Global cleanup
        all_frame = QFrame()
        all_frame.setObjectName("card")
        al = QVBoxLayout(all_frame)
        al.setContentsMargins(18, 14, 18, 14)
        al.setSpacing(10)

        a_title = QLabel("🗑️  تنظيف شامل")
        a_title.setStyleSheet(
            f"color: {COLORS['red']}; font-size: 13px; font-weight: bold;"
        )
        a_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        al.addWidget(a_title)

        a_desc = QLabel(
            "حذف كل العمليات المسددة لجميع العملاء.\n"
            "⚠️  لا يمكن التراجع عن هذا الإجراء."
        )
        a_desc.setObjectName("label_muted")
        a_desc.setAlignment(Qt.AlignmentFlag.AlignLeft)
        al.addWidget(a_desc)

        a_row = QHBoxLayout()
        clean_a_btn = QPushButton("🗑️  تنظيف شامل لكل العملاء")
        clean_a_btn.setObjectName("btn_danger")
        clean_a_btn.setFixedHeight(36)
        clean_a_btn.clicked.connect(self._cleanup_all)
        a_row.addWidget(clean_a_btn)
        a_row.addStretch()
        al.addLayout(a_row)

        layout.addWidget(all_frame)
        layout.addStretch()

    def load_data(self):
        self.customer_combo.clear()
        for c in db.get_all_customers():
            self.customer_combo.addItem(c["name"], c["id"])

    def _refresh_stat(self):
        txns = db.get_transactions(payment_status="paid", limit=5000)
        self.stat_label.setText(f"العمليات المسددة القابلة للحذف: {len(txns)} عملية")

    def _cleanup_single(self):
        cid = self.customer_combo.currentData()
        if not cid:
            QMessageBox.warning(self, "تنبيه", "اختر عميلاً أولاً")
            return
        name = self.customer_combo.currentText()
        if QMessageBox.question(
            self, "تأكيد التنظيف",
            f"هل تريد حذف العمليات المسددة للعميل [{name}]؟\n"
            "لا يمكن التراجع.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            deleted = db.cleanup_paid_transactions(cid)
            QMessageBox.information(self, "تم ✅", f"تم حذف {deleted} عملية مسددة")
            self._refresh_stat()

    def _cleanup_all(self):
        if QMessageBox.question(
            self, "⚠️  تأكيد التنظيف الشامل",
            "هل أنت متأكد من حذف كل العمليات المسددة لجميع العملاء؟\n"
            "هذا الإجراء نهائي.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            if QMessageBox.warning(
                self, "تأكيد أخير",
                "سيتم الحذف النهائي. هل تريد المتابعة؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                deleted = db.cleanup_paid_transactions()
                QMessageBox.information(self, "تم ✅", f"تم حذف {deleted} عملية مسددة")
                self._refresh_stat()


# ══════════════════════════════════════════
#  Reports Screen (main)
# ══════════════════════════════════════════

class ReportsScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__("التقارير والجرد", "جرد المنصات، سجل العمليات، تنظيف البيانات")
        self._build_content()

    def _build_content(self):
        c = self.content()
        c.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        self.inventory_tab = InventoryTab()
        self.tabs.addTab(self.inventory_tab, "📊  الجرد العام")

        self.log_tab = TransactionsLogTab()
        self.tabs.addTab(self.log_tab, "📋  سجل العمليات")

        self.cleanup_tab = CleanupTab()
        self.tabs.addTab(self.cleanup_tab, "🗑️  تنظيف البيانات")

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
        elif index == 2:
            self.cleanup_tab.load_data()