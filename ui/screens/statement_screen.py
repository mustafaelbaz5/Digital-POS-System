"""
statement_screen.py — كشف حساب العميل (Master-Detail View)
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import BaseDialog, DataTable
from ui.screens.settlement_dialog import QuickSettleDialog
from ui.styles.theme import CARD_RADIUS, COLORS, FONT, GAP_LG, GAP_MD
from ui.utils.formatters import fmt_currency

# ══════════════════════════════════════════
#  Summary Card Component
# ══════════════════════════════════════════


class SummaryCard(QFrame):
    def __init__(self, label: str, value: str, color: str = None):
        super().__init__()
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(
            f"color: {color or COLORS['text_primary']}; font-size: {FONT['xl']}; font-weight: bold; background: transparent; border: none;"
        )
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.val_lbl)

        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT['sm']}; background: transparent; border: none;"
        )
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl)

    def set_featured(self, is_featured: bool):
        if is_featured:
            self.setStyleSheet(f"""
                QFrame#card {{
                    background: {COLORS['bg_card']};
                    border: 2px solid {COLORS['clients']};
                    border-radius: 15px;
                }}
            """)
            self.val_lbl.setStyleSheet(
                f"color: {COLORS['clients']}; font-size: 32px; font-weight: 900; background: transparent; border: none;"
            )
        else:
            self.setStyleSheet("")
    def set_value(self, value: str):
        self.val_lbl.setText(value)


# ══════════════════════════════════════════
#  كشف حساب العميل (Master-Detail)
# ══════════════════════════════════════════


class CustomerStatementDialog(QDialog):

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("كشف حساب العميل")
        self.setMinimumSize(1300, 850)
        self.setObjectName("dialog")

        self._load_data()
        self._build_ui()

    def _load_data(self):
        self._data = db.get_customer_statement(self.customer_id)

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 24)
        self.main_layout.setSpacing(GAP_LG)

        # 1. Header (Identity) - Themed as Section Header
        self.main_layout.addLayout(self._make_header())

        # Body container for content with margins
        self.body_container = QVBoxLayout()
        self.body_container.setContentsMargins(24, 0, 24, 0)
        self.body_container.setSpacing(GAP_LG)
        self.main_layout.addLayout(self.body_container)

        # 2. Master Section (Summary Cards)
        self.body_container.addLayout(self._make_master_cards())

        # 3. Detail Section (Table)
        self.body_container.addLayout(self._make_detail_table())

        # Initial fill
        self._fill_table()

    def _make_header(self) -> QVBoxLayout:
        # Wrapper for colored header
        header_wrap = QVBoxLayout()
        
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet(f"""
            background: {COLORS['clients']};
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
        """)
        hl = QHBoxLayout(header_frame)
        hl.setContentsMargins(24, 0, 24, 0)

        c = self._data["customer"]
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        name_lbl = QLabel(c.get("name", "—"))
        name_lbl.setStyleSheet(
            f"color: {COLORS['text_on_dark']}; font-size: {FONT['2xl']}; font-weight: bold; background: transparent;"
        )
        info_col.addWidget(name_lbl)

        sub_info = QLabel(
            f"📞 {c.get('phone', '—')}  |  📂 {c.get('group_name', 'بدون مجموعة')}"
        )
        sub_info.setStyleSheet(
            f"color: rgba(255,255,255,0.8); font-size: {FONT['md']}; background: transparent;"
        )
        info_col.addWidget(sub_info)

        hl.addLayout(info_col)
        hl.addStretch()

        self.settle_btn = QPushButton("💚 تسديد سريع")
        self.settle_btn.setObjectName("btn_success")
        self.settle_btn.setFixedWidth(150)
        self.settle_btn.clicked.connect(self._quick_settle)
        hl.addWidget(self.settle_btn)

        # Show settle button only if there is debt
        t = self._data.get("totals", {})
        self.settle_btn.setVisible((t.get("total_pending") or 0) > 0)

        print_btn = QPushButton("🖨️ طباعة")
        print_btn.setObjectName("btn_primary")
        print_btn.setFixedWidth(120)
        print_btn.clicked.connect(self._print_report)
        hl.addWidget(print_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet(f"""
            background: rgba(255,255,255,0.1); color: {COLORS['text_on_dark']};
            border-radius: 18px; font-weight: bold; font-size: 16px;
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        hl.addWidget(close_btn)

        header_wrap.addWidget(header_frame)
        return header_wrap

    def _make_master_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(GAP_MD)

        t = self._data.get("totals", {})
        net = (t.get("total_pending") or 0) - (t.get("total_due") or 0)

        self.card_owed = SummaryCard(
            "إجمالي المطلوب منه", fmt_currency(t.get("total_pending", 0)), COLORS["red"]
        )
        self.card_owned = SummaryCard(
            "إجمالي مبالغ العميل", fmt_currency(t.get("total_due", 0)), COLORS["green"]
        )
        self.card_net = SummaryCard(
            "الصافي النهائي (المطلوب)",
            fmt_currency(net),
            COLORS['clients'] if net >= 0 else COLORS["red"],
        )
        self.card_net.set_featured(True)
        
        self.card_count = SummaryCard(
            "عدد العمليات", str(t.get("total_count", 0)), COLORS["accent"]
        )

        layout.addWidget(self.card_owed)
        layout.addWidget(self.card_owned)
        layout.addWidget(self.card_net)
        layout.addWidget(self.card_count)

        return layout

    def _make_detail_table(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(GAP_MD)

        title_row = QHBoxLayout()
        title = QLabel("📋 سجل المعاملات التفصيلي")
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: {FONT['lg']}; font-weight: bold;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        cleanup_btn = QPushButton("🗑️ تنظيف المسدد")
        cleanup_btn.setObjectName("btn_danger")
        cleanup_btn.setFixedHeight(32)
        cleanup_btn.clicked.connect(self._cleanup)
        title_row.addWidget(cleanup_btn)

        layout.addLayout(title_row)

        cols = [
            ("التاريخ", -1),
            ("النوع", -1),
            ("الخدمة", -1),
            ("المنصة", -1),
            ("المرجع", -1),
            ("المصروف", -1),
            ("المطلوب", -1),
            ("الربح", -1),
            ("الحالة", -1),
            ("الإجراءات", 150),
        ]
        self.table = DataTable(cols)
        self.table.set_section_color(COLORS["clients"])
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.table)

        return layout

    def _fill_table(self):
        txns = self._data.get("transactions", [])
        self.table.clear_rows()
        self.table.setRowCount(len(txns))

        for row, t in enumerate(txns):
            op = t.get("operation_type", "")
            is_manual = op in ("manual_commission", "inbound")
            bg = COLORS["bg_hover"] if is_manual else None

            # Date
            self.table.set_cell(
                row,
                0,
                (t.get("created_at") or "")[:16].replace("T", " "),
                color=COLORS["text_secondary"],
                bg_color=bg,
            )

            # Type
            op = t.get("operation_type", "")
            is_out = op == "outbound"
            type_text = "📤 شحن صادر" if is_out else "📥 استلام"
            type_color = COLORS["blue"] if is_out else COLORS["purple"]
            self.table.set_cell(row, 1, type_text, color=type_color, bold=True, bg_color=bg)

            # Service
            self.table.set_cell(
                row,
                2,
                t.get("service_name") or "—",
                align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                bg_color=bg,
            )

            # Platform
            self.table.set_cell(
                row, 3, t.get("platform_name") or "—", color=COLORS["text_secondary"], bg_color=bg
            )

            # Reference
            ref = "🃏 كارت" if t.get("is_card") else (t.get("reference_no") or "—")
            self.table.set_cell(row, 4, ref, color=COLORS["text_muted"], bg_color=bg)

            # Spent (المصروف)
            spent = t.get("amount_spent", 0)
            self.table.set_cell(row, 5, fmt_currency(spent), color=COLORS["text_secondary"], bg_color=bg)

            # Required (المطلوب)
            req = t.get("amount_required", 0)
            self.table.set_cell(row, 6, fmt_currency(req), bold=True, bg_color=bg)

            # Profit (الربح)
            profit = t.get("profit", 0)
            profit_text = fmt_currency(profit) if not is_manual else "—"
            profit_color = COLORS["cyan"] if profit >= 0 else COLORS["red"]
            if is_manual:
                profit_color = COLORS["text_secondary"]
            self.table.set_cell(row, 7, profit_text, color=profit_color, bg_color=bg)

            # Status
            if is_out:
                status = t.get("payment_status", "pending")
                st_text = "مؤجل ⏳" if status == "pending" else "تم السداد ✓"
                st_color = COLORS["yellow"] if status == "pending" else COLORS["green"]
            else:
                is_del = bool(t.get("is_delivered", 0))
                st_text = "تم التسليم ✓" if is_del else "لم يسلم ⏳"
                st_color = COLORS["green"] if is_del else COLORS["yellow"]

            self.table.set_cell(row, 8, st_text, color=st_color, bold=True, bg_color=bg)

            # Actions
            self._add_actions_button(row, 9, t)

    def _add_actions_button(self, row: int, col: int, t: dict):
        btn = QPushButton("⋮ إجراءات")
        btn.setObjectName("btn_ghost")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(26)

        # Wrap button in layout for padding
        wrap = QWidget()
        wrap.setObjectName("cell_wrapper_1")
        wrap.setStyleSheet("#cell_wrapper_1 { background: transparent; }")
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.addWidget(btn)

        def show_menu():
            menu = QMenu(self)

            if t["operation_type"] == "outbound":
                if t["payment_status"] == "pending":
                    act_pay = QAction(" تحديد كمسدد", self)
                    act_pay.triggered.connect(
                        lambda: self._update_status(t["id"], "paid")
                    )
                    menu.addAction(act_pay)
                else:
                    act_unpay = QAction("⏳ تحديد كمؤجل", self)
                    act_unpay.triggered.connect(
                        lambda: self._update_status(t["id"], "pending")
                    )
                    menu.addAction(act_unpay)
            else:  # inbound
                if not t.get("is_delivered", 0):
                    act_del = QAction("🤝 تحديد كتم التسليم", self)
                    act_del.triggered.connect(lambda: self._update_status(t["id"], 1))
                    menu.addAction(act_del)
                else:
                    act_undel = QAction("⏳ تحديد كـ لم يُسلّم", self)
                    act_undel.triggered.connect(lambda: self._update_status(t["id"], 0))
                    menu.addAction(act_undel)

            menu.addSeparator()
            act_del = QAction("🗑️ حذف العملية", self)
            act_del.triggered.connect(lambda: self._delete_txn(t["id"]))
            menu.addAction(act_del)

            menu.exec(btn.mapToGlobal(btn.rect().bottomRight()))

        btn.clicked.connect(show_menu)
        self.table.setCellWidget(row, col, wrap)

    def _update_status(self, tid: int, val):
        try:
            db.update_transaction_status(tid, val)
            self._load_data()
            self._refresh_ui()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _delete_txn(self, tid: int):
        if (
            QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف هذه العملية؟")
            == QMessageBox.StandardButton.Yes
        ):
            try:
                db.delete_transaction(tid)
                self._load_data()
                self._refresh_ui()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _cleanup(self):
        if (
            QMessageBox.question(
                self, "تنظيف", "هل تريد حذف جميع العمليات المسددة والمسلمة؟"
            )
            == QMessageBox.StandardButton.Yes
        ):
            db.cleanup_paid_transactions(self.customer_id)
            self._load_data()
            self._refresh_ui()

    def _quick_settle(self):
        dlg = QuickSettleDialog(self._data["customer"], self)
        if dlg.exec():
            self._load_data()
            self._refresh_ui()

    def _print_report(self):
        QMessageBox.information(self, "طباعة", "ميزة الطباعة قريباً.")

    def _refresh_ui(self):
        t = self._data.get("totals", {})
        net = (t.get("total_pending") or 0) - (t.get("total_due") or 0)

        # Update settle button visibility
        self.settle_btn.setVisible((t.get("total_pending") or 0) > 0)

        self.card_owed.set_value(fmt_currency(t.get("total_pending", 0)))
        self.card_owned.set_value(fmt_currency(t.get("total_due", 0)))
        self.card_net.set_value(fmt_currency(net))
        # Keep it special and larger than other cards
        self.card_net.val_lbl.setStyleSheet(
            f"color: {COLORS['accent'] if net >= 0 else COLORS['red']}; font-size: 32px; font-weight: 900;"
        )
        self.card_count.set_value(str(t.get("total_count", 0)))

        self._fill_table()


# ══════════════════════════════════════════
#  Remaining Dialogs (GroupReport, etc.)
# ══════════════════════════════════════════


class GroupReportDialog(BaseDialog):
    def __init__(self, group_id: int, parent=None):
        groups = db.get_all_groups()
        group = next((g for g in groups if g["id"] == group_id), {})
        super().__init__(f"تقرير مجموعة — {group.get('name', '—')}", parent)
        self.group_id = group_id
        self.setMinimumSize(850, 600)
        self._build_content()

    def _build_content(self):
        customers = db.get_customers_by_group(self.group_id)
        total_debt = sum(c.get("total_debt", 0) or 0 for c in customers)

        columns = [
            ("الاسم", 220),
            ("التليفون", 160),
            ("المديونية", 150),
            ("ملاحظات", -1),
        ]
        self.table = DataTable(columns)
        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            debt = c.get("total_debt", 0) or 0
            self.table.set_cell(row, 0, c["name"], bold=True)
            self.table.set_cell(
                row, 1, c.get("phone") or "—", color=COLORS["text_secondary"]
            )
            self.table.set_cell(
                row,
                2,
                fmt_currency(debt),
                color=(
                    COLORS["red"]
                    if debt > 0
                    else COLORS["green"] if debt < 0 else COLORS["text_muted"]
                ),
                bold=debt != 0,
            )
            self.table.set_cell(
                row, 3, c.get("notes") or "—", color=COLORS["text_muted"]
            )

        self.body.addWidget(self.table)

        total_frame = QFrame()
        total_frame.setObjectName("card_highlight")
        tl = QHBoxLayout(total_frame)
        tl.setContentsMargins(16, 12, 16, 12)
        total_lbl = QLabel(f"إجمالي المجموعة: {fmt_currency(total_debt)}")
        total_lbl.setStyleSheet(
            f"color:{COLORS['red'] if total_debt > 0 else COLORS['green']};"
            f"font-size:18px;font-weight:bold;"
        )
        tl.addStretch()
        tl.addWidget(total_lbl)
        self.body.addWidget(total_frame)

        # Footer
        self.add_stretch()
        self.add_button("إغلاق", self.accept, role="primary")
