"""
statement_screen.py — كشف حساب العميل (Ledger + Operations Dual-Tab)
"""

import os
from datetime import date as _date, timedelta

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import BaseDialog, DataTable
from ui.screens.settlement_dialog import QuickSettleDialog
from ui.styles.theme import COLORS, FONT, GAP_LG, GAP_MD, GAP_SM
from ui.utils.formatters import fmt_currency

RTL = Qt.LayoutDirection.RightToLeft


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
            f"color: {color or COLORS['text_primary']}; font-size: {FONT['xl']}; "
            f"font-weight: bold; background: transparent; border: none;"
        )
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.val_lbl)

        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT['sm']}; "
            f"background: transparent; border: none;"
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
                f"color: {COLORS['clients']}; font-size: 32px; "
                f"font-weight: 900; background: transparent; border: none;"
            )
        else:
            self.setStyleSheet("")

    def set_value(self, value: str):
        self.val_lbl.setText(value)


# ══════════════════════════════════════════
#  كشف حساب العميل — Dual-Tab Ledger View
# ══════════════════════════════════════════


class CustomerStatementDialog(QDialog):

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setLayoutDirection(RTL)
        self.setWindowTitle("كشف حساب العميل")
        
        # Default opening size (wider and taller for better data visibility)
        self.resize(1400, 900)
        # Allow resizing down to a reasonable minimum
        self.setMinimumSize(1100, 750)
        
        self.setObjectName("dialog")
        self._load_data()
        self._build_ui()

    # ── Data ──────────────────────────────────────────────────────

    def _load_data(self):
        self._data = db.get_customer_statement(self.customer_id)

    def _get_filter_dates(self) -> tuple[str | None, str | None]:
        """Return (date_from, date_to) as 'YYYY-MM-DD' strings, or (None, None) for all time."""
        if not hasattr(self, "period_combo"):
            return None, None
        idx = self.period_combo.currentIndex()
        today = _date.today()
        if idx == 0:
            return (today - timedelta(days=30)).isoformat(), today.isoformat()
        if idx == 1:
            return today.replace(day=1).isoformat(), today.isoformat()
        return None, None

    def _get_period_data(self) -> tuple[list, list, float]:
        """Return (filtered_txns, filtered_pmts, opening_balance) for the active period."""
        date_from, date_to = self._get_filter_dates()
        all_txns = self._data.get("transactions", [])
        all_pmts = self._data.get("payments", [])

        if date_from:
            opening_balance = (
                sum(float(t.get("amount_required") or 0)
                    for t in all_txns
                    if t.get("operation_type") == "outbound"
                    and (t.get("created_at") or "")[:10] < date_from)
                - sum(float(t.get("amount_spent") or 0)
                      for t in all_txns
                      if t.get("operation_type") == "inbound"
                      and (t.get("created_at") or "")[:10] < date_from)
                - sum(float(p.get("amount") or 0)
                      for p in all_pmts
                      if (p.get("created_at") or "")[:10] < date_from)
            )
            txns = [t for t in all_txns
                    if date_from <= (t.get("created_at") or "")[:10] <= date_to]
            pmts = [p for p in all_pmts
                    if date_from <= (p.get("created_at") or "")[:10] <= date_to]
        else:
            opening_balance = 0.0
            txns = all_txns
            pmts = all_pmts

        return txns, pmts, opening_balance

    def _compute_ledger(self) -> list[dict]:
        """Build running-balance ledger for the selected period with a rollover
        opening balance row when a date filter is active. Returned newest-first."""
        txns, pmts, opening_balance = self._get_period_data()
        date_from, _ = self._get_filter_dates()

        all_entries: list[dict] = []
        for t in txns:
            op = t.get("operation_type", "")
            if op == "outbound":
                all_entries.append({
                    "created_at":  t.get("created_at", ""),
                    "description": t.get("service_name") or "عملية شحن",
                    "debit":       float(t.get("amount_required") or 0),
                    "credit":      0.0,
                })
            elif op == "inbound":
                all_entries.append({
                    "created_at":  t.get("created_at", ""),
                    "description": "💰  دفعة من العميل",
                    "debit":       0.0,
                    "credit":      float(t.get("amount_spent") or 0),
                })
        for p in pmts:
            all_entries.append({
                "created_at":  p.get("created_at", ""),
                "description": "💳  تسديد سريع",
                "debit":       0.0,
                "credit":      float(p.get("amount") or 0),
            })

        all_entries.sort(key=lambda e: e["created_at"])

        rows: list[dict] = []
        balance = opening_balance
        for e in all_entries:
            balance += e["debit"] - e["credit"]
            rows.append({
                "date":        e["created_at"][:16].replace("T", " "),
                "description": e["description"],
                "debit":       e["debit"],
                "credit":      e["credit"],
                "balance":     balance,
                "is_rollover": False,
            })

        # Rollover row goes at the end so it appears at the bottom after reversal
        if date_from and abs(opening_balance) > 0.005:
            rows.append({
                "date":        date_from,
                "description": "رصيد سابق منقول من فترات سابقة",
                "debit":       opening_balance if opening_balance > 0 else 0.0,
                "credit":      abs(opening_balance) if opening_balance < 0 else 0.0,
                "balance":     opening_balance,
                "is_rollover": True,
            })

        rows.reverse()
        return rows

    # ── UI Build ──────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 24)
        root.setSpacing(GAP_LG)

        root.addLayout(self._make_header())

        body = QVBoxLayout()
        body.setContentsMargins(24, 0, 24, 0)
        body.setSpacing(GAP_LG)
        root.addLayout(body)

        body.addWidget(self._make_action_bar())
        body.addLayout(self._make_master_cards())

        # ── Dual-tab area ─────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(RTL)

        self.tabs.addTab(self._make_ledger_tab(),     "📒  سجل الحساب")
        self.tabs.addTab(self._make_operations_tab(), "📋  المعاملات")

        body.addWidget(self.tabs)

        self._fill_ledger()
        self._fill_table()

    # ── Header ────────────────────────────────────────────────────

    def _make_header(self) -> QVBoxLayout:
        wrap = QVBoxLayout()
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet(f"""
            background: {COLORS['clients']};
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
        """)
        hl = QHBoxLayout(frame)
        hl.setContentsMargins(24, 0, 24, 0)

        c = self._data["customer"]
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        name_lbl = QLabel(c.get("name", "—"))
        name_lbl.setStyleSheet(
            f"color: {COLORS['text_on_dark']}; font-size: {FONT['2xl']}; "
            f"font-weight: bold; background: transparent;"
        )
        info_col.addWidget(name_lbl)

        sub = QLabel(f"📞 {c.get('phone', '—')}  |  📂 {c.get('group_name', 'بدون مجموعة')}")
        sub.setStyleSheet(
            f"color: rgba(255,255,255,0.8); font-size: {FONT['md']}; background: transparent;"
        )
        info_col.addWidget(sub)

        hl.addLayout(info_col)
        hl.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet(f"""
            background: rgba(255,255,255,0.1); color: {COLORS['text_on_dark']};
            border-radius: 18px; font-weight: bold; font-size: 16px;
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        hl.addWidget(close_btn)

        wrap.addWidget(frame)
        return wrap

    # ── Action Bar ────────────────────────────────────────────────

    def _make_action_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("statement_action_bar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        self.print_btn = QPushButton("  طباعة")
        self.print_btn.setObjectName("statement_print_btn")
        self.print_btn.setFixedHeight(40)
        self.print_btn.setMinimumWidth(150)
        self.print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.print_btn.clicked.connect(self._print_report)
        layout.addWidget(self.print_btn)

        self.settle_btn = QPushButton("  تسديد سريع")
        self.settle_btn.setObjectName("statement_settle_btn")
        self.settle_btn.setFixedHeight(40)
        self.settle_btn.setMinimumWidth(180)
        self.settle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settle_btn.clicked.connect(self._quick_settle)
        layout.addWidget(self.settle_btn)

        s = self._compute_summary()
        self.settle_btn.setEnabled(s["net"] > 0.005)

        layout.addStretch()

        period_lbl = QLabel("الفترة الزمنية:")
        period_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; background: transparent; border: none;"
        )
        layout.addWidget(period_lbl)

        self.period_combo = QComboBox()
        self.period_combo.setLayoutDirection(RTL)
        self.period_combo.setFixedHeight(40)
        self.period_combo.setMinimumWidth(160)
        self.period_combo.addItems(["آخر 30 يوم", "الشهر الحالي", "كل الفترات"])
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        layout.addWidget(self.period_combo)

        self.print_status_lbl = QLabel("")
        self.print_status_lbl.setObjectName("statement_print_status")
        self.print_status_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.print_status_lbl)

        return bar

    # ── Master Cards ──────────────────────────────────────────────

    def _compute_summary(self) -> dict:
        """Derive card values from loaded data — no status flag dependency."""
        total_required = sum(
            float(t.get("amount_required") or 0)
            for t in self._data.get("transactions", [])
            if t.get("operation_type") == "outbound"
        )
        total_payments = sum(
            float(p.get("amount") or 0)
            for p in self._data.get("payments", [])
        )
        total_received = sum(
            float(t.get("amount_required") or 0)
            for t in self._data.get("transactions", [])
            if t.get("operation_type") == "inbound"
            and not t.get("is_delivered", 0)
        )
        return {
            "total_required": total_required,
            "total_payments": total_payments,
            "total_received": total_received,
            "net":            total_required - total_payments,
        }

    def _net_display(self, net: float) -> tuple[str, str]:
        """Return (display_text, color) for the net balance card."""
        if net > 0.005:
            return fmt_currency(net), COLORS["red"]
        elif net < -0.005:
            return f"{fmt_currency(abs(net))} — له", COLORS["green"]
        else:
            return "—", COLORS["text_muted"]

    def _make_master_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(GAP_MD)

        s = self._compute_summary()

        self.card_owed = SummaryCard(
            "إجمالي المطلوب",
            fmt_currency(s["total_required"]),
            COLORS["red"],
        )
        self.card_owned = SummaryCard(
            "إجمالي المسدد",
            fmt_currency(s["total_payments"]),
            COLORS["green"],
        )
        self.card_received = SummaryCard(
            "مبالغ الاستلام",
            fmt_currency(s["total_received"]),
            COLORS["purple"],
        )
        net_text, net_color = self._net_display(s["net"])
        self.card_net = SummaryCard("الصافي النهائي", net_text, net_color)
        self.card_net.set_featured(True)
        self.card_net.val_lbl.setStyleSheet(
            f"color: {net_color}; font-size: 32px; font-weight: 900; "
            f"background:transparent; border:none;"
        )

        layout.addWidget(self.card_owed)
        layout.addWidget(self.card_owned)
        layout.addWidget(self.card_received)
        layout.addWidget(self.card_net)
        return layout

    # ══════════════════════════════════════════
    #  Tab 1 — سجل الحساب (Accounting Ledger)
    # ══════════════════════════════════════════

    def _make_ledger_tab(self) -> QWidget:
        widget = QWidget()
        widget.setLayoutDirection(RTL)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_SM)

        cols = [
            ("التاريخ",      150),
            ("البيان",        -1),
            ("عليه (مدين)",  150),
            ("له (دائن)",    150),
            ("الرصيد",       150),
        ]
        self.ledger_table = DataTable(cols)
        self.ledger_table.set_section_color(COLORS["clients"])
        self.ledger_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.ledger_table)
        return widget

    def _fill_ledger(self):
        rows = self._compute_ledger()
        self.ledger_table.setSortingEnabled(False)
        self.ledger_table.clear_rows()
        self.ledger_table.setRowCount(len(rows))

        for i, r in enumerate(rows):
            is_rollover = r.get("is_rollover", False)
            is_debit    = r["debit"] > 0
            bg = COLORS.get("bg_hover") if is_rollover else None

            self.ledger_table.set_cell(
                i, 0, r["date"], color=COLORS["text_secondary"], bg_color=bg
            )
            desc = f"⟵  {r['description']}" if is_rollover else r["description"]
            self.ledger_table.set_cell(
                i, 1, desc,
                color=COLORS["accent"] if is_rollover else COLORS["text_primary"],
                bold=True, bg_color=bg,
            )

            if is_debit:
                self.ledger_table.set_cell(
                    i, 2, fmt_currency(r["debit"]), color=COLORS["red"], bold=True, bg_color=bg
                )
                self.ledger_table.set_cell(i, 3, "—", color=COLORS["text_muted"], bg_color=bg)
            else:
                self.ledger_table.set_cell(i, 2, "—", color=COLORS["text_muted"], bg_color=bg)
                self.ledger_table.set_cell(
                    i, 3, fmt_currency(r["credit"]), color=COLORS["green"], bold=True, bg_color=bg
                )

            bal = r["balance"]
            if bal > 0.005:
                bal_color, bal_text = COLORS["red"], fmt_currency(bal)
            elif bal < -0.005:
                bal_color, bal_text = COLORS["green"], fmt_currency(abs(bal))
            else:
                bal_color, bal_text = COLORS["text_muted"], "—"
            self.ledger_table.set_cell(i, 4, bal_text, color=bal_color, bold=True, bg_color=bg)

        self.ledger_table.setSortingEnabled(True)

    # ══════════════════════════════════════════
    #  Tab 2 — المعاملات (Operations)
    # ══════════════════════════════════════════

    def _make_operations_tab(self) -> QWidget:
        widget = QWidget()
        widget.setLayoutDirection(RTL)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_SM)

        cols = [
            ("التاريخ",    150),
            ("النوع",      150),
            ("الخدمة",      100),
            ("المنصة",      120),
            ("المصروف",    130),
            ("المطلوب",    130),
            ("المسدد",     130),
            ("الربح",       100),
            ("الحالة",     400),
            ("الإجراءات",  140),
        ]
        self.table = DataTable(cols)
        self.table.set_section_color(COLORS["clients"])
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        header = self.table.horizontalHeader()
        fixed_columns = {
            0: 150,
            1: 150,
            4: 130,
            5: 130,
            6: 130,
            7: 100,
            8: -1,
            9: 140,
        }
        for col, width in fixed_columns.items():
            self.table.setColumnWidth(col, width)
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        return widget

    def _fill_table(self):
        txns, _, _ = self._get_period_data()
        self.table.setSortingEnabled(False)
        self.table.clear_rows()
        self.table.setRowCount(len(txns))

        for row, t in enumerate(txns):
            op = t.get("operation_type", "")
            is_manual = op in ("manual_commission", "inbound")
            bg = COLORS["bg_hover"] if is_manual else None

            # Date
            self.table.set_cell(
                row, 0,
                (t.get("created_at") or "")[:16].replace("T", " "),
                color=COLORS["text_secondary"], bg_color=bg,
            )

            # Type
            is_out = op == "outbound"
            self.table.set_cell(
                row, 1,
                "📤 شحن صادر" if is_out else "📥 استلام",
                color=COLORS["blue"] if is_out else COLORS["purple"],
                bold=True, bg_color=bg,
            )

            # Service
            self.table.set_cell(
                row, 2, t.get("service_name") or "—",
                align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                bg_color=bg,
            )

            # Platform
            self.table.set_cell(
                row, 3, t.get("platform_name") or "—",
                color=COLORS["text_secondary"], bg_color=bg,
            )

            # Spent
            self.table.set_cell(
                row, 4, fmt_currency(t.get("amount_spent", 0)),
                color=COLORS["text_secondary"], bg_color=bg,
            )

            # Required — display-only, NEVER overwritten
            self.table.set_cell(
                row, 5, fmt_currency(t.get("amount_required", 0)),
                bold=True, bg_color=bg,
            )

            # Amount paid (col 6)
            amount_paid = float(t.get("amount_paid") or 0)
            if is_out and amount_paid > 0:
                self.table.set_cell(
                    row, 6, fmt_currency(amount_paid),
                    color=COLORS["green"], bold=True, bg_color=bg,
                )
            else:
                self.table.set_cell(row, 6, "—", color=COLORS["text_muted"], bg_color=bg)

            # Profit (col 7)
            profit = t.get("profit", 0)
            self.table.set_cell(
                row, 7,
                fmt_currency(profit) if not is_manual else "—",
                color=COLORS["cyan"] if (not is_manual and profit >= 0) else COLORS["red"]
                      if (not is_manual and profit < 0) else COLORS["text_secondary"],
                bg_color=bg,
            )

            # Status + progress widget (col 8) — derived purely from numeric values
            if is_out:
                required = float(t.get("amount_required") or 0)
                if required > 0 and amount_paid >= required - 0.005:
                    self.table.set_cell(row, 8, "مسدد ✓", color=COLORS["green"], bold=True, bg_color=bg)
                elif amount_paid > 0.005:
                    self.table.setCellWidget(row, 8, self._make_progress_widget(amount_paid, required, bg))
                else:
                    self.table.set_cell(row, 8, "مؤجل ⏳", color=COLORS["yellow"], bold=True, bg_color=bg)
            else:
                is_del  = bool(t.get("is_delivered", 0))
                st_text = "تم التسليم ✓" if is_del else "لم يسلم ⏳"
                st_color = COLORS["green"] if is_del else COLORS["yellow"]
                self.table.set_cell(row, 8, st_text, color=st_color, bold=True, bg_color=bg)

            # Actions (col 9)
            self._add_actions_button(row, 9, t)

        self.table.setSortingEnabled(True)

    # ── Payment Progress Widget ───────────────────────────────────

    def _make_progress_widget(self, paid: float, required: float, bg: str | None) -> QWidget:
        pct = min(100, int(paid / required * 100)) if required > 0 else 0
        remaining = required - paid

        wrap = QWidget()
        wrap.setStyleSheet(f"background: {bg or 'transparent'};")
        vlay = QVBoxLayout(wrap)
        vlay.setContentsMargins(8, 4, 8, 4)
        vlay.setSpacing(3)

        lbl = QLabel(
            f"جزئي ◑   مدفوع: {fmt_currency(paid)}   |   متبقي: {fmt_currency(remaining)}"
        )
        lbl.setStyleSheet(
            f"color:{COLORS['yellow']}; font-size:{FONT['sm']}; "
            f"font-weight:bold; background:transparent;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vlay.addWidget(lbl)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(pct)
        bar.setFixedHeight(5)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS.get('bg_secondary', '#2d333b')};
                border-radius: 2px; border: none;
            }}
            QProgressBar::chunk {{
                background: {COLORS['yellow']};
                border-radius: 2px;
            }}
        """)
        vlay.addWidget(bar)

        return wrap

    # ── Actions Menu ──────────────────────────────────────────────

    def _add_actions_button(self, row: int, col: int, t: dict):
        btn = QPushButton("⋮ إجراءات")
        btn.setObjectName("btn_ghost")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(26)

        wrap = QWidget()
        wrap.setObjectName("cell_wrapper_1")
        wrap.setStyleSheet("#cell_wrapper_1 { background: transparent; }")
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.addWidget(btn)

        def show_menu():
            menu = QMenu(self)
            if t["operation_type"] == "inbound" and not t.get("is_delivered", 0):
                tid = t["id"]
                a_net = QAction("💳 عمل مقاصة / خصم من المديونية", self)
                a_net.triggered.connect(lambda checked=False, _tid=tid: self._deliver_and_settle(_tid))
                menu.addAction(a_net)

                a_cash = QAction("💵 تأكيد تسليم المبلغ كاش للعميل", self)
                a_cash.triggered.connect(lambda checked=False, _tid=tid: self._deliver_cash(_tid))
                menu.addAction(a_cash)

                menu.addSeparator()
            a_del = QAction("🗑️ حذف العملية", self)
            a_del.triggered.connect(lambda: self._delete_txn(t["id"]))
            menu.addAction(a_del)
            menu.exec(btn.mapToGlobal(btn.rect().bottomRight()))

        btn.clicked.connect(show_menu)
        self.table.setCellWidget(row, col, wrap)

    # ── Mutating Actions ──────────────────────────────────────────

    def _deliver_and_settle(self, tid: int):
        try:
            result = db.deliver_and_settle(tid)
            total = result["total_settled"]
            count = result["settled_count"]
            lines = [f"تمت المقاصة — تم خصم {fmt_currency(total)} من مديونية الشحن"]
            if count > 0:
                lines.append(f"(تسديد {count} عملية بالكامل)")
            if result.get("partial_settled"):
                lines.append("مع تسديد جزئي للعملية الأخيرة.")
            QMessageBox.information(self, "تمت المقاصة ✓", "\n".join(lines))
            self._load_data()
            self._refresh_ui()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _deliver_cash(self, tid: int):
        if (
            QMessageBox.question(
                self,
                "تأكيد تسليم كاش",
                "هل تأكدت من تسليم المبلغ كاشاً للعميل؟\nسيتم خصمه من الخزينة.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            try:
                db.mark_as_delivered(tid)
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

    def _quick_settle(self):
        dlg = QuickSettleDialog(self._data["customer"], self)
        if dlg.exec():
            self._load_data()
            self._refresh_ui()

    def _on_period_changed(self):
        self._refresh_ui()

    def _print_report(self):
        self.print_btn.setEnabled(False)
        self.print_status_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; background:transparent; border:none;"
        )
        self.print_status_lbl.setText("جاري إنشاء الملف وإرساله للطابعة...")
        QApplication.processEvents()
        try:
            from ui.utils.pdf_generator import PDFGenerator
            pdf_txns, pdf_pmts, opening_balance = self._get_period_data()
            pdf_data = {
                "customer":     self._data["customer"],
                "transactions": pdf_txns,
                "payments":     pdf_pmts,
                "totals":       self._data.get("totals", {}),
            }
            period_label = self.period_combo.currentText()
            path = PDFGenerator(
                pdf_data,
                opening_balance=opening_balance,
                period_label=period_label,
            ).generate()
            path = os.path.abspath(os.path.normpath(path))
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            os.startfile(path)
            self.print_status_lbl.setStyleSheet(
                f"color:{COLORS['green']}; background:transparent; border:none;"
            )
            self.print_status_lbl.setText("تم إنشاء PDF وإرساله للطابعة.")
            QTimer.singleShot(4500, lambda: self.print_status_lbl.setText(""))
        except Exception as e:
            self.print_status_lbl.setStyleSheet(
                f"color:{COLORS['red']}; background:transparent; border:none;"
            )
            self.print_status_lbl.setText("تعذر إرسال الملف للطابعة.")
            QMessageBox.critical(self, "خطأ في توليد PDF", str(e))
        finally:
            self.print_btn.setEnabled(True)

    # ── Refresh ───────────────────────────────────────────────────

    def _refresh_ui(self):
        s = self._compute_summary()

        self.settle_btn.setEnabled(s["net"] > 0.005)

        self.card_owed.set_value(fmt_currency(s["total_required"]))
        self.card_owned.set_value(fmt_currency(s["total_payments"]))
        self.card_received.set_value(fmt_currency(s["total_received"]))

        net_text, net_color = self._net_display(s["net"])
        self.card_net.set_value(net_text)
        self.card_net.val_lbl.setStyleSheet(
            f"color: {net_color}; font-size: 32px; font-weight: 900; "
            f"background:transparent; border:none;"
        )

        self._fill_ledger()
        self._fill_table()


# ══════════════════════════════════════════
#  GroupReportDialog (unchanged)
# ══════════════════════════════════════════


class GroupReportDialog(BaseDialog):
    def __init__(self, group_id: int, parent=None):
        groups = db.get_all_groups()
        group = next((g for g in groups if g["id"] == group_id), {})
        super().__init__(f"تقرير مجموعة — {group.get('name', '—')}", parent)
        self.group_id = group_id
        self._group_name = group.get("name", "المجموعة")
        self.setMinimumSize(850, 600)
        self._build_content()

    def _build_content(self):
        from ui.utils.formatters import fmt_currency as _fc
        customers = db.get_customers_by_group(self.group_id)
        total_debt = sum(c.get("total_debt", 0) or 0 for c in customers)

        columns = [
            ("الاسم",      220),
            ("التليفون",   160),
            ("المديونية",  150),
            ("ملاحظات",     -1),
        ]
        self.table = DataTable(columns)
        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            debt = c.get("total_debt", 0) or 0
            self.table.set_cell(row, 0, c["name"], bold=True)
            self.table.set_cell(row, 1, c.get("phone") or "—", color=COLORS["text_secondary"])
            self.table.set_cell(
                row, 2, _fc(debt),
                color=(
                    COLORS["red"]   if debt > 0
                    else COLORS["green"] if debt < 0
                    else COLORS["text_muted"]
                ),
                bold=debt != 0,
            )
            self.table.set_cell(row, 3, c.get("notes") or "—", color=COLORS["text_muted"])

        self.body.addWidget(self.table)

        total_frame = QFrame()
        total_frame.setObjectName("card_highlight")
        tl = QHBoxLayout(total_frame)
        tl.setContentsMargins(16, 12, 16, 12)
        total_lbl = QLabel(f"إجمالي المجموعة: {_fc(total_debt)}")
        total_lbl.setStyleSheet(
            f"color:{COLORS['red'] if total_debt > 0 else COLORS['green']};"
            f"font-size:18px;font-weight:bold;"
        )
        tl.addStretch()
        tl.addWidget(total_lbl)
        self.body.addWidget(total_frame)

        self._print_status = QLabel("")
        self._print_status.setStyleSheet(
            "background: transparent; border: none; font-size: 12px;"
        )
        self._print_status.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.add_stretch()
        footer_row = QHBoxLayout()
        footer_row.setSpacing(12)

        self._print_btn = QPushButton("🖨️  طباعة PDF")
        self._print_btn.setObjectName("statement_print_btn")
        self._print_btn.setFixedHeight(40)
        self._print_btn.setMinimumWidth(160)
        self._print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._print_btn.clicked.connect(self._print_report)
        footer_row.addWidget(self._print_btn)
        footer_row.addWidget(self._print_status)
        footer_row.addStretch()
        self.body.addLayout(footer_row)

        self.add_button("إغلاق", self.accept, role="primary")

    def _print_report(self):
        self._print_btn.setEnabled(False)
        self._print_status.setStyleSheet(
            f"color:{COLORS['text_secondary']}; background:transparent; border:none;"
        )
        self._print_status.setText("جاري إنشاء الملف...")
        QApplication.processEvents()
        try:
            data = db.get_group_summary(self.group_id)
            if not data:
                raise ValueError("لم يتم العثور على بيانات المجموعة")
            from ui.utils.pdf_generator import GroupPDFGenerator
            path = GroupPDFGenerator(data).generate()
            path = os.path.abspath(os.path.normpath(path))
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            os.startfile(path)
            self._print_status.setStyleSheet(
                f"color:{COLORS['green']}; background:transparent; border:none;"
            )
            self._print_status.setText("✓ تم إنشاء PDF بنجاح")
            QTimer.singleShot(4500, lambda: self._print_status.setText(""))
        except Exception as e:
            self._print_status.setStyleSheet(
                f"color:{COLORS['red']}; background:transparent; border:none;"
            )
            self._print_status.setText("تعذّر إنشاء الملف")
            QMessageBox.critical(self, "خطأ في توليد PDF", str(e))
        finally:
            self._print_btn.setEnabled(True)
