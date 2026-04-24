"""
Reports Screen — شاشة التقارير والجرد
تحتوي على 3 تابات:
  1. الجرد العام (بفترة زمنية + معادلة المطابقة)
  2. سجل العمليات (مع فلترة)
  3. تنظيف البيانات (Cleanup)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QDateEdit,
    QComboBox, QMessageBox, QGridLayout, QScrollArea,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ui.styles.theme import COLORS
from ui.components.widgets import SectionTitle, DataTable
from utils.formatters import fmt_currency

import database as db


# ══════════════════════════════════════════
#  Helper: كارت رقم بسيط
# ══════════════════════════════════════════

class MiniStatCard(QFrame):
    def __init__(self, title: str, value: str = "—",
                 color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        self._val_lbl = QLabel(value)
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._val_lbl.setStyleSheet(
            f"color: {color or COLORS['text_primary']};"
            f"font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(self._val_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        title_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        layout.addWidget(title_lbl)

    def set_value(self, value: str, color: str = None):
        self._val_lbl.setText(value)
        if color:
            self._val_lbl.setStyleSheet(
                f"color: {color}; font-size: 20px; font-weight: bold;"
            )


# ══════════════════════════════════════════
#  تاب 1: الجرد العام
# ══════════════════════════════════════════

class InventoryTab(QWidget):
    """جرد بفترة زمنية + معادلة المطابقة"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(16)

        # ── شريط اختيار الفترة
        period_frame = QFrame()
        period_frame.setObjectName("card")
        period_layout = QHBoxLayout(period_frame)
        period_layout.setContentsMargins(16, 12, 16, 12)
        period_layout.setSpacing(12)

        run_btn = QPushButton("🔍  تشغيل الجرد")
        run_btn.setObjectName("btn_primary")
        run_btn.setFixedHeight(38)
        run_btn.clicked.connect(self.run_inventory)
        period_layout.addWidget(run_btn)

        period_layout.addStretch()

        to_lbl = QLabel("إلى:")
        to_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        period_layout.addWidget(to_lbl)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setFixedHeight(36)
        self.date_to.setFixedWidth(130)
        period_layout.addWidget(self.date_to)

        from_lbl = QLabel("من:")
        from_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        period_layout.addWidget(from_lbl)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setFixedHeight(36)
        self.date_from.setFixedWidth(130)
        period_layout.addWidget(self.date_from)

        layout.addWidget(period_frame)

        # ── كروت الإجماليات
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(12)
        layout.addLayout(self.cards_layout)

        self.card_cash     = MiniStatCard("الخزينة النقدية",    color=COLORS["green"])
        self.card_machines = MiniStatCard("إجمالي الماكينات",   color=COLORS["blue_light"])
        self.card_wallets  = MiniStatCard("إجمالي المحافظ",     color=COLORS["purple"])
        self.card_debts    = MiniStatCard("إجمالي الديون",      color=COLORS["yellow"])
        self.card_profit   = MiniStatCard("صافي الأرباح (الفترة)", color=COLORS["green"])
        self.card_budget   = MiniStatCard("الميزانية الرئيسية", color=COLORS["text_primary"])

        for i, card in enumerate([
            self.card_cash, self.card_machines, self.card_wallets,
            self.card_debts, self.card_profit, self.card_budget
        ]):
            self.cards_layout.addWidget(card, i // 3, i % 3)

        # ── معادلة المطابقة
        self.match_frame = self._build_match_frame()
        layout.addWidget(self.match_frame)

        # ── جدول المنصات
        layout.addWidget(QLabel(
            "تفاصيل المنصات",
            styleSheet=f"color:{COLORS['text_secondary']}; font-size:13px; font-weight:bold;"
        ))

        columns = [
            ("المنصة",    180),
            ("النوع",      90),
            ("الرصيد",    140),
            ("الحد الشهري", 130),
            ("المستخدم",  130),
            ("المتبقي",   130),
        ]
        self.platforms_table = DataTable(columns)
        self.platforms_table.setMaximumHeight(220)
        layout.addWidget(self.platforms_table)

        layout.addStretch()

    def _build_match_frame(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        title = QLabel("⚖️  معادلة المطابقة")
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: bold;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title)

        formula = QLabel("(أرصدة المنصات + الكاش + الديون)  =  (الميزانية + إجمالي الأرباح الكلية)")
        formula.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        formula.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(formula)

        row = QHBoxLayout()

        self.match_left  = QLabel("—")
        self.match_right = QLabel("—")
        self.match_result = QLabel("—")

        for lbl in [self.match_left, self.match_right]:
            lbl.setStyleSheet(
                f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: bold;"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.match_result.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.match_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_result.setFixedWidth(180)
        self.match_result.setStyleSheet(
            f"border-radius: 8px; padding: 6px 12px;"
            f"background: {COLORS['bg_input']}; color: {COLORS['text_muted']};"
        )

        eq_lbl = QLabel("=")
        eq_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 18px;")
        eq_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.left_label  = QLabel("(أرصدة + كاش + ديون)")
        self.right_label = QLabel("(ميزانية + أرباح)")
        for l in [self.left_label, self.right_label]:
            l.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_box = QVBoxLayout()
        left_box.addWidget(self.match_left)
        left_box.addWidget(self.left_label)

        right_box = QVBoxLayout()
        right_box.addWidget(self.match_right)
        right_box.addWidget(self.right_label)

        row.addLayout(right_box)
        row.addWidget(eq_lbl)
        row.addWidget(self.match_result)
        row.addWidget(eq_lbl)  # لن نضيفه مرتين — نستخدم stretch
        row.addStretch()
        row.addLayout(left_box)

        layout.addLayout(row)
        return frame

    def run_inventory(self):
        """تشغيل الجرد"""
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to   = self.date_to.date().toString("yyyy-MM-dd")

        if self.date_from.date() > self.date_to.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return

        # بيانات لحظية
        stats    = db.get_dashboard_stats()
        budget   = db.get_budget()
        platforms = db.get_all_platforms()

        # أرباح الفترة فقط
        period_txns = db.get_transactions(date_from=date_from, date_to=date_to, limit=10000)
        period_profit = sum(t.get("profit", 0) or 0 for t in period_txns)

        # تحديث الكروت
        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_machines.set_value(fmt_currency(stats["total_machines"]))
        self.card_wallets.set_value(fmt_currency(stats["total_wallets"]))
        self.card_debts.set_value(fmt_currency(stats["total_debts"]),
                                  color=COLORS["yellow"] if stats["total_debts"] > 0 else COLORS["green"])
        self.card_profit.set_value(
            fmt_currency(period_profit),
            color=COLORS["green"] if period_profit >= 0 else COLORS["red"]
        )
        self.card_budget.set_value(fmt_currency(budget["main_budget"]))

        # معادلة المطابقة
        left_side  = stats["total_balances"] + stats["total_debts"]
        # إجمالي الأرباح الكلية
        all_txns   = db.get_transactions(limit=100000)
        total_profit_all = sum(t.get("profit", 0) or 0 for t in all_txns)
        right_side = budget["main_budget"] + total_profit_all
        diff       = left_side - right_side

        self.match_left.setText(fmt_currency(left_side))
        self.match_right.setText(fmt_currency(right_side))

        if abs(diff) < 0.01:
            self.match_result.setText("✅  متطابق")
            self.match_result.setStyleSheet(
                f"border-radius: 8px; padding: 6px 12px;"
                f"background: {COLORS['green_bg']}; color: {COLORS['green']};"
                f"font-size: 14px; font-weight: bold;"
            )
        elif diff > 0:
            self.match_result.setText(f"📈 فائض\n{fmt_currency(diff)}")
            self.match_result.setStyleSheet(
                f"border-radius: 8px; padding: 6px 12px;"
                f"background: {COLORS['bg_input']}; color: {COLORS['blue_light']};"
                f"font-size: 13px; font-weight: bold;"
            )
        else:
            self.match_result.setText(f"⚠️ عجز\n{fmt_currency(abs(diff))}")
            self.match_result.setStyleSheet(
                f"border-radius: 8px; padding: 6px 12px;"
                f"background: {COLORS['red_bg']}; color: {COLORS['red']};"
                f"font-size: 13px; font-weight: bold;"
            )

        # جدول المنصات
        self.platforms_table.clear_rows()
        self.platforms_table.setRowCount(len(platforms))

        for row, p in enumerate(platforms):
            type_text  = "🏧 ماكينة" if p["type"] == "machine" else "💳 محفظة"
            type_color = COLORS["blue_light"] if p["type"] == "machine" else COLORS["purple"]

            self.platforms_table.set_cell(row, 0, p["name"], bold=True)
            self.platforms_table.set_cell(row, 1, type_text, color=type_color)
            self.platforms_table.set_cell(row, 2, fmt_currency(p.get("balance", 0)),
                                          color=COLORS["green"])

            if p["type"] == "wallet":
                limit     = p.get("monthly_limit", 200000)
                used      = p.get("monthly_used", 0)
                remaining = limit - used
                rem_color = COLORS["red"] if remaining < 10000 else COLORS["text_secondary"]

                self.platforms_table.set_cell(row, 3, fmt_currency(limit))
                self.platforms_table.set_cell(row, 4, fmt_currency(used),
                                              color=COLORS["yellow"])
                self.platforms_table.set_cell(row, 5, fmt_currency(remaining),
                                              color=rem_color)
            else:
                for col in [3, 4, 5]:
                    self.platforms_table.set_cell(row, col, "—",
                                                  color=COLORS["text_muted"])


# ══════════════════════════════════════════
#  تاب 2: سجل العمليات
# ══════════════════════════════════════════

class TransactionsLogTab(QWidget):
    """سجل كل العمليات مع فلترة"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        # ── شريط الفلترة
        filter_frame = QFrame()
        filter_frame.setObjectName("card")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 10, 16, 10)
        filter_layout.setSpacing(10)

        search_btn = QPushButton("🔍  بحث")
        search_btn.setObjectName("btn_primary")
        search_btn.setFixedHeight(36)
        search_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(search_btn)

        filter_layout.addStretch()

        # حالة الدفع
        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(36)
        self.status_filter.setMinimumWidth(120)
        self.status_filter.addItem("كل الحالات", None)
        self.status_filter.addItem("💵 نقدي",    "cash")
        self.status_filter.addItem("⏳ مؤجل",    "pending")
        self.status_filter.addItem("✅ مسدد",    "paid")
        filter_layout.addWidget(self.status_filter)

        # نوع العملية
        self.type_filter = QComboBox()
        self.type_filter.setFixedHeight(36)
        self.type_filter.setMinimumWidth(130)
        self.type_filter.addItem("كل الأنواع",    None)
        self.type_filter.addItem("📤 صادر",       "outbound")
        self.type_filter.addItem("📥 وارد",       "inbound")
        filter_layout.addWidget(self.type_filter)

        # المنصة
        self.platform_filter = QComboBox()
        self.platform_filter.setFixedHeight(36)
        self.platform_filter.setMinimumWidth(140)
        filter_layout.addWidget(self.platform_filter)

        # التواريخ
        to_lbl = QLabel("إلى:")
        to_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        filter_layout.addWidget(to_lbl)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setFixedHeight(36)
        self.date_to.setFixedWidth(120)
        filter_layout.addWidget(self.date_to)

        from_lbl = QLabel("من:")
        from_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        filter_layout.addWidget(from_lbl)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setFixedHeight(36)
        self.date_from.setFixedWidth(120)
        filter_layout.addWidget(self.date_from)

        layout.addWidget(filter_frame)

        # ── الجدول
        columns = [
            ("التاريخ",    130),
            ("النوع",       80),
            ("الخدمة",     160),
            ("المنصة",     120),
            ("العميل",     130),
            ("المصروف",    110),
            ("المطلوب",    110),
            ("الربح",       90),
            ("المرجع",     110),
            ("الحالة",      90),
        ]
        self.table = DataTable(columns)
        layout.addWidget(self.table)

        # ملخص
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 12px;"
        )
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.summary_label)

    def load_platforms_filter(self):
        self.platform_filter.clear()
        self.platform_filter.addItem("كل المنصات", None)
        for p in db.get_all_platforms():
            icon = "🏧" if p["type"] == "machine" else "💳"
            self.platform_filter.addItem(f"{icon} {p['name']}", p["id"])

    def load_data(self):
        date_from   = self.date_from.date().toString("yyyy-MM-dd")
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

        # فلتر النوع (client-side لأن get_transactions لا يدعمه مباشرة)
        op_type = self.type_filter.currentData()
        if op_type:
            txns = [t for t in txns if t["operation_type"] == op_type]

        self._render(txns)

    def _render(self, transactions: list):
        self.table.clear_rows()
        self.table.setRowCount(len(transactions))

        total_profit  = 0
        total_spent   = 0
        total_required = 0

        for row, t in enumerate(transactions):
            created = t.get("created_at", "")[:16].replace("T", "  ")
            self.table.set_cell(row, 0, created, color=COLORS["text_muted"])

            op = t.get("operation_type", "")
            self.table.set_cell(
                row, 1,
                "📤 صادر" if op == "outbound" else "📥 وارد",
                color=COLORS["blue_light"] if op == "outbound" else COLORS["purple"]
            )

            self.table.set_cell(row, 2, t.get("service_name", "—"))
            self.table.set_cell(row, 3, t.get("platform_name", "—"),
                                color=COLORS["text_secondary"])
            self.table.set_cell(row, 4, t.get("customer_name") or "—",
                                color=COLORS["text_secondary"])

            spent    = t.get("amount_spent", 0) or 0
            required = t.get("amount_required", 0) or 0
            profit   = t.get("profit", 0) or 0

            self.table.set_cell(row, 5, fmt_currency(spent))
            self.table.set_cell(row, 6, fmt_currency(required), bold=True)
            self.table.set_cell(
                row, 7, fmt_currency(profit),
                color=COLORS["green"] if profit >= 0 else COLORS["red"]
            )

            ref = "🃏 كارت" if t.get("is_card") else (t.get("reference_no") or "—")
            self.table.set_cell(row, 8, ref, color=COLORS["text_muted"])
            self.table.add_status_badge(row, 9, t.get("payment_status", ""))

            total_profit   += profit
            total_spent    += spent
            total_required += required

        p_color = COLORS["green"] if total_profit >= 0 else COLORS["red"]
        self.summary_label.setText(
            f"العمليات: {len(transactions)}  |  "
            f"إجمالي المصروف: {fmt_currency(total_spent)}  |  "
            f"إجمالي المطلوب: {fmt_currency(total_required)}  |  "
            f"صافي الأرباح: {fmt_currency(total_profit)}"
        )
        self.summary_label.setStyleSheet(
            f"color: {p_color if total_profit != 0 else COLORS['text_muted']}; font-size: 12px;"
        )


# ══════════════════════════════════════════
#  تاب 3: تنظيف البيانات
# ══════════════════════════════════════════

class CleanupTab(QWidget):
    """تنظيف العمليات المسددة"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(20)

        # ── تنظيف عميل واحد
        single_frame = QFrame()
        single_frame.setObjectName("card")
        single_layout = QVBoxLayout(single_frame)
        single_layout.setContentsMargins(20, 16, 20, 16)
        single_layout.setSpacing(12)

        single_title = QLabel("🧹  تنظيف عميل واحد")
        single_title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: bold;"
        )
        single_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        single_layout.addWidget(single_title)

        single_desc = QLabel(
            "حذف العمليات المسددة (paid) لعميل معين فقط.\n"
            "المديونيات الحالية والعمليات المؤجلة لا تُمس."
        )
        single_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        single_desc.setAlignment(Qt.AlignmentFlag.AlignRight)
        single_layout.addWidget(single_desc)

        row = QHBoxLayout()
        row.setSpacing(10)

        clean_single_btn = QPushButton("تنظيف العميل المحدد")
        clean_single_btn.setObjectName("btn_danger")
        clean_single_btn.setFixedHeight(38)
        clean_single_btn.clicked.connect(self._cleanup_single)
        row.addWidget(clean_single_btn)

        row.addStretch()

        self.customer_combo = QComboBox()
        self.customer_combo.setFixedHeight(38)
        self.customer_combo.setMinimumWidth(220)
        row.addWidget(self.customer_combo)

        cust_lbl = QLabel("اختر العميل:")
        cust_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        row.addWidget(cust_lbl)

        single_layout.addLayout(row)
        layout.addWidget(single_frame)

        # ── تنظيف شامل
        all_frame = QFrame()
        all_frame.setObjectName("card")
        all_layout = QVBoxLayout(all_frame)
        all_layout.setContentsMargins(20, 16, 20, 16)
        all_layout.setSpacing(12)

        all_title = QLabel("🗑️  تنظيف شامل")
        all_title.setStyleSheet(
            f"color: {COLORS['red']}; font-size: 15px; font-weight: bold;"
        )
        all_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        all_layout.addWidget(all_title)

        all_desc = QLabel(
            "حذف كل العمليات المسددة (paid) لجميع العملاء.\n"
            "⚠️  لا يمكن التراجع عن هذا الإجراء."
        )
        all_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        all_desc.setAlignment(Qt.AlignmentFlag.AlignRight)
        all_layout.addWidget(all_desc)

        all_row = QHBoxLayout()
        clean_all_btn = QPushButton("🗑️  تنظيف شامل لكل العملاء")
        clean_all_btn.setObjectName("btn_danger")
        clean_all_btn.setFixedHeight(38)
        clean_all_btn.clicked.connect(self._cleanup_all)
        all_row.addWidget(clean_all_btn)
        all_row.addStretch()
        all_layout.addLayout(all_row)

        layout.addWidget(all_frame)

        # ── إحصائية المسدد
        stat_frame = QFrame()
        stat_frame.setObjectName("card")
        stat_layout = QHBoxLayout(stat_frame)
        stat_layout.setContentsMargins(20, 14, 20, 14)

        refresh_btn = QPushButton("🔄  تحديث")
        refresh_btn.setObjectName("btn_secondary")
        refresh_btn.setFixedHeight(34)
        refresh_btn.clicked.connect(self._refresh_stat)
        stat_layout.addWidget(refresh_btn)

        stat_layout.addStretch()

        self.stat_label = QLabel("اضغط تحديث لعرض عدد العمليات المسددة")
        self.stat_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        self.stat_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        stat_layout.addWidget(self.stat_label)

        layout.addWidget(stat_frame)
        layout.addStretch()

    def load_data(self):
        self.customer_combo.clear()
        for c in db.get_all_customers():
            self.customer_combo.addItem(c["name"], c["id"])

    def _refresh_stat(self):
        txns = db.get_transactions(payment_status="paid", limit=100000)
        self.stat_label.setText(
            f"العمليات المسددة القابلة للحذف: {len(txns)} عملية"
        )

    def _cleanup_single(self):
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            QMessageBox.warning(self, "تنبيه", "اختر عميلاً أولاً")
            return

        name = self.customer_combo.currentText()
        reply = QMessageBox.question(
            self, "تأكيد التنظيف",
            f"هل تريد حذف العمليات المسددة للعميل [{name}]؟\n"
            "لا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            deleted = db.cleanup_paid_transactions(customer_id)
            QMessageBox.information(self, "تم ✅", f"تم حذف {deleted} عملية مسددة")
            self._refresh_stat()

    def _cleanup_all(self):
        reply = QMessageBox.question(
            self, "⚠️  تأكيد التنظيف الشامل",
            "هل أنت متأكد من حذف كل العمليات المسددة لجميع العملاء؟\n"
            "⚠️  هذا الإجراء نهائي ولا يمكن التراجع عنه.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # تأكيد ثاني للأمان
            reply2 = QMessageBox.warning(
                self, "تأكيد أخير",
                "سيتم حذف جميع سجلات المسدد نهائياً. هل تريد المتابعة؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply2 == QMessageBox.StandardButton.Yes:
                deleted = db.cleanup_paid_transactions()
                QMessageBox.information(self, "تم ✅", f"تم حذف {deleted} عملية مسددة")
                self._refresh_stat()


# ══════════════════════════════════════════
#  الشاشة الرئيسية
# ══════════════════════════════════════════

class ReportsScreen(QWidget):
    """شاشة التقارير والجرد"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(SectionTitle("📑 التقارير والجرد", "جرد المنصات، سجل العمليات، تنظيف البيانات"))

        self.tabs = QTabWidget()

        self.inventory_tab = InventoryTab()
        self.tabs.addTab(self.inventory_tab, "📊  الجرد العام")

        self.log_tab = TransactionsLogTab()
        self.tabs.addTab(self.log_tab, "📋  سجل العمليات")

        self.cleanup_tab = CleanupTab()
        self.tabs.addTab(self.cleanup_tab, "🗑️  تنظيف البيانات")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

    def refresh(self):
        """يُستدعى عند الانتقال للشاشة"""
        current = self.tabs.currentIndex()
        self._on_tab_changed(current)

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.inventory_tab.run_inventory()
        elif index == 1:
            self.log_tab.load_platforms_filter()
            self.log_tab.load_data()
        elif index == 2:
            self.cleanup_tab.load_data()