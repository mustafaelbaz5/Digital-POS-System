"""
statement_screen.py — كشف حساب العميل (Professional Rebuild v5)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFileDialog, QMessageBox,
    QWidget, QScrollArea, QSizePolicy, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

from datetime import datetime

import database as db
from ui.styles.theme import (
    COLORS, FONT, CARD_RADIUS, BORDER_RADIUS,
    GAP_XS, GAP_SM, GAP_MD, GAP_LG, GAP_XL,
    MARGIN_CARD, ROW_HEIGHT
)
from utils.formatters import fmt_currency

RTL    = Qt.LayoutDirection.RightToLeft
ALeft  = Qt.AlignmentFlag.AlignLeft  | Qt.AlignmentFlag.AlignVCenter
ARight = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
ACenter= Qt.AlignmentFlag.AlignCenter


# ──────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────

def _card(parent=None) -> QFrame:
    f = QFrame(parent)
    f.setObjectName("card")
    return f

def _label(text: str, size: str = "md", color: str = None,
           bold: bool = False, align=None) -> QLabel:
    lbl = QLabel(text)
    style = f"font-size:{FONT[size]}; color:{color or COLORS['text_primary']};"
    if bold: style += "font-weight:bold;"
    lbl.setStyleSheet(style)
    if align: lbl.setAlignment(align)
    return lbl

def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background:{COLORS['border']}; max-height:1px; border:none;")
    return f

def _fmt_dt(raw: str) -> str:
    """Format: 2024-01-15 14:30"""
    if not raw: return "—"
    return raw[:16].replace("T", " ")

def _status_text_color(status: str, op: str = "outbound", delivered: int = 0):
    if op == "inbound":
        return ("تم التسليم ✓", COLORS["green"]) if delivered else ("لم يُسلَّم ⏳", COLORS["yellow"])
    return {
        "pending": ("مؤجل ⏳",  COLORS["yellow"]),
        "paid":    ("مسدد ✓",  COLORS["green"]),
        "cash":    ("نقدي ✓",  COLORS["accent"]),
    }.get(status, (status, COLORS["text_muted"]))


# ──────────────────────────────────────────────────────────
#  SummaryPill  — واحدة من 5 كروت الإحصائيات
# ──────────────────────────────────────────────────────────

class SummaryPill(QFrame):
    def __init__(self, label: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayoutDirection(RTL)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(MARGIN_CARD, GAP_SM + 4, MARGIN_CARD, GAP_SM + 4)
        layout.setSpacing(GAP_XS)

        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color:{color}; font-size:{FONT['xl']}; font-weight:bold;"
        )
        self._val.setAlignment(ALeft)
        layout.addWidget(self._val)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:{FONT['xs']};")
        lbl.setAlignment(ALeft)
        layout.addWidget(lbl)

        # accent bottom border
        self.setStyleSheet(
            f"QFrame#card {{ border-bottom: 3px solid {color}; }}"
        )

    def set_value(self, v: str): self._val.setText(v)


# ──────────────────────────────────────────────────────────
#  TransactionTable  — جدول العمليات مع إجراءات
# ──────────────────────────────────────────────────────────

COLS = [
    ("التاريخ والوقت", 145),
    ("النوع",          70),
    ("الخدمة",        155),
    ("المنصة",        120),
    ("المصروف",       100),
    ("المطلوب",       100),
    ("الربح",          85),
    ("الحالة",         110),
    ("إجراءات",        120),
]

class TransactionTable(QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup()

    def _setup(self):
        self.setLayoutDirection(RTL)
        self.setColumnCount(len(COLS))
        self.setHorizontalHeaderLabels([c[0] for c in COLS])
        for i, (_, w) in enumerate(COLS):
            if w == -1:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.setColumnWidth(i, w)
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.horizontalHeader().setHighlightSections(False)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            f"alternate-background-color:{COLORS['bg_elevated']};"
        )
        self.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)

    def _cell(self, row: int, col: int, text: str,
               color: str = None, bold: bool = False):
        item = QTableWidgetItem(str(text) if text else "—")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setTextAlignment(ACenter)
        if color: item.setForeground(QColor(color))
        if bold:
            f = item.font(); f.setBold(True); item.setFont(f)
        self.setItem(row, col, item)

    def load(self, txns: list, on_status_change, on_delete):
        self.setRowCount(len(txns))
        for row, t in enumerate(txns):
            op        = t.get("operation_type", "outbound")
            status    = t.get("payment_status", "")
            delivered = t.get("is_delivered", 0)

            self._cell(row, 0, _fmt_dt(t.get("created_at")), COLORS["text_secondary"])

            op_text  = "📤 صادر" if op == "outbound" else "📥 وارد"
            op_color = COLORS["blue"] if op == "outbound" else COLORS["purple"]
            self._cell(row, 1, op_text, op_color)

            self._cell(row, 2, t.get("service_name") or "—", bold=True)
            self._cell(row, 3, t.get("platform_name") or "—", COLORS["text_secondary"])
            self._cell(row, 4, fmt_currency(t.get("amount_spent", 0) or 0))
            self._cell(row, 5, fmt_currency(t.get("amount_required", 0) or 0), bold=True)

            profit = t.get("profit", 0) or 0
            self._cell(row, 6, fmt_currency(profit),
                       COLORS["accent"] if profit >= 0 else COLORS["red"])

            st_text, st_color = _status_text_color(status, op, delivered)
            self._cell(row, 7, st_text, st_color, bold=True)

            # ── Action button
            btn = QPushButton("⋮  إجراءات")
            btn.setObjectName("btn_ghost")
            btn.setFixedHeight(32)
            btn.clicked.connect(
                lambda _, tid=t["id"], _t=t: self._open_action(tid, _t, on_status_change, on_delete)
            )
            wrap = QWidget()
            wl   = QHBoxLayout(wrap)
            wl.setContentsMargins(6, 4, 6, 4)
            wl.addWidget(btn)
            self.setCellWidget(row, 8, wrap)

    def _open_action(self, tid, t, on_status_change, on_delete):
        dlg = _ActionDialog(t, on_status_change, on_delete, self.window())
        dlg.exec()


# ──────────────────────────────────────────────────────────
#  _ActionDialog  — ديالوج الإجراءات
# ──────────────────────────────────────────────────────────

class _ActionDialog(QDialog):
    def __init__(self, t: dict, on_sc, on_del, parent=None):
        super().__init__(parent)
        self._t   = t
        self._on_sc  = on_sc
        self._on_del = on_del
        self.setLayoutDirection(RTL)
        self.setWindowTitle("إجراءات العملية")
        self.setFixedWidth(340)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(GAP_LG, GAP_LG, GAP_LG, GAP_LG)
        layout.setSpacing(GAP_MD)

        op        = self._t.get("operation_type", "")
        status    = self._t.get("payment_status", "")
        delivered = bool(self._t.get("is_delivered", 0))
        tid       = self._t["id"]

        # ── Info card
        info = _card()
        il   = QVBoxLayout(info)
        il.setContentsMargins(MARGIN_CARD, GAP_MD, MARGIN_CARD, GAP_MD)
        il.setSpacing(GAP_XS)
        il.addWidget(_label(self._t.get("service_name") or "—", "lg", bold=True, align=ALeft))
        il.addWidget(_label(
            fmt_currency(self._t.get("amount_required", 0)),
            "md", COLORS["accent"], align=ALeft
        ))
        il.addWidget(_label(
            _fmt_dt(self._t.get("created_at")),
            "sm", COLORS["text_muted"], align=ALeft
        ))
        layout.addWidget(info)

        layout.addWidget(_label("تغيير الحالة", "sm", COLORS["text_secondary"], align=ALeft))

        # ── Status buttons
        if op == "outbound":
            self._status_btn(layout, tid, "مؤجل ⏳",  "pending",       status == "pending", COLORS["yellow"])
            self._status_btn(layout, tid, "مسدد ✓",  "paid",           status == "paid",    COLORS["green"])
        elif op == "inbound":
            self._status_btn(layout, tid, "لم يُسلَّم ⏳", "not_delivered", not delivered,   COLORS["yellow"])
            self._status_btn(layout, tid, "تم التسليم ✓", "delivered",    delivered,         COLORS["accent"])

        layout.addWidget(_divider())

        # ── Delete
        del_btn = QPushButton("🗑️  حذف العملية نهائياً")
        del_btn.setObjectName("btn_danger")
        del_btn.setFixedHeight(40)
        del_btn.clicked.connect(lambda: self._do_delete(tid))
        layout.addWidget(del_btn)

        close = QPushButton("إغلاق")
        close.setObjectName("btn_secondary")
        close.setFixedHeight(38)
        close.clicked.connect(self.reject)
        layout.addWidget(close)

    def _status_btn(self, layout, tid, label, new_status, is_active, color):
        btn = QPushButton(label)
        btn.setFixedHeight(42)
        if is_active:
            btn.setStyleSheet(
                f"background:{color}18; color:{color};"
                f"border:2px solid {color}; border-radius:{BORDER_RADIUS};"
                f"font-size:{FONT['md']}; font-weight:bold;"
            )
        else:
            btn.setStyleSheet(
                f"background:{COLORS['bg_elevated']}; color:{COLORS['text_secondary']};"
                f"border:1px solid {COLORS['border']}; border-radius:{BORDER_RADIUS};"
                f"font-size:{FONT['md']};"
            )
        btn.clicked.connect(lambda: self._do_change(tid, new_status))
        layout.addWidget(btn)

    def _do_change(self, tid, ns):
        self.accept()
        self._on_sc(tid, ns)

    def _do_delete(self, tid):
        self.accept()
        self._on_del(tid)


# ──────────────────────────────────────────────────────────
#  CustomerStatementDialog  — الشاشة الرئيسية
# ──────────────────────────────────────────────────────────

class CustomerStatementDialog(QDialog):

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setLayoutDirection(RTL)
        self.setWindowTitle("كشف حساب")
        self.setMinimumSize(1140, 780)
        self.resize(1200, 840)
        self._filter = "all"
        self._load()
        self._build()

    # ── Data ────────────────────────────────────────────

    def _load(self):
        self._data = db.get_customer_statement(self.customer_id)

    # ── Build ────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # fixed top bar (not scrollable)
        outer.addWidget(self._make_topbar())

        # scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body.setLayoutDirection(RTL)
        self._body_l = QVBoxLayout(body)
        self._body_l.setContentsMargins(GAP_LG, GAP_LG, GAP_LG, GAP_LG)
        self._body_l.setSpacing(GAP_MD)

        self._body_l.addWidget(self._make_identity())
        self._body_l.addLayout(self._make_pills_row())
        self._body_l.addWidget(self._make_table_section())   # table first
        self._body_l.addLayout(self._make_filter_bar())      # filter after
        self._body_l.addWidget(self._make_footer_bar())

        scroll.setWidget(body)
        outer.addWidget(scroll)

    # ── Top Bar ─────────────────────────────────────────

    def _make_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("screen_header")
        bar.setLayoutDirection(RTL)
        bar.setFixedHeight(60)
        hl  = QHBoxLayout(bar)
        hl.setContentsMargins(GAP_LG, 0, GAP_LG, 0)
        hl.setSpacing(GAP_MD)

        c    = self._data.get("customer", {})
        name = c.get("name", "—")

        # RIGHT: customer name + meta
        meta_col = QVBoxLayout()
        meta_col.setSpacing(2)
        meta_col.addWidget(_label(f"كشف حساب — {name}", "lg", bold=True, align=ALeft))
        phone = c.get("phone") or ""
        group = c.get("group_name") or ""
        meta  = "  ·  ".join(filter(None, [phone, group]))
        if meta:
            meta_col.addWidget(_label(meta, "xs", COLORS["text_muted"], align=ALeft))
        hl.addLayout(meta_col)
        hl.addStretch()

        # LEFT: export buttons + customer facing
        for lbl, obj, slot in [
            ("👤 كشف العميل", "btn_secondary", self._open_customer_facing),
            ("📄 PDF",        "btn_secondary", self._export_pdf),
            ("🖼️ صورة",      "btn_secondary", self._export_image),
        ]:
            b = QPushButton(lbl); b.setObjectName(obj); b.setFixedHeight(34)
            b.clicked.connect(slot); hl.addWidget(b)

        return bar

    # ── Identity Card ────────────────────────────────────

    def _make_identity(self) -> QFrame:
        c     = self._data.get("customer", {})
        txns  = self._data.get("transactions", [])
        debt  = c.get("total_debt", 0) or 0

        frame = _card()
        frame.setLayoutDirection(RTL)
        hl    = QHBoxLayout(frame)
        hl.setContentsMargins(GAP_LG, GAP_MD, GAP_LG, GAP_MD)
        hl.setSpacing(GAP_XL)

        # ── block helper
        def block(title: str, value: str, color: str = None):
            w  = QWidget(); w.setLayoutDirection(RTL)
            vl = QVBoxLayout(w); vl.setContentsMargins(0,0,0,0); vl.setSpacing(3)
            vl.addWidget(_label(value, "lg", color or COLORS["text_primary"], bold=True, align=ALeft))
            vl.addWidget(_label(title, "xs", COLORS["text_muted"], align=ALeft))
            return w

        if debt > 0:
            status_text, status_color = "عليه", COLORS["red"]
        elif debt < 0:
            status_text, status_color = "له",   COLORS["green"]
        else:
            status_text, status_color = "صافر", COLORS["text_muted"]

        hl.addWidget(block("الاسم",       c.get("name", "—")))
        hl.addWidget(_vdiv())
        hl.addWidget(block("التليفون",    c.get("phone") or "—"))
        hl.addWidget(_vdiv())
        hl.addWidget(block("المجموعة",    c.get("group_name") or "—", COLORS["blue"]))
        hl.addWidget(_vdiv())
        hl.addWidget(block(f"الرصيد ({status_text})",
                           fmt_currency(abs(debt)), status_color))
        hl.addWidget(_vdiv())
        hl.addWidget(block("عدد العمليات", str(len(txns)), COLORS["accent"]))
        if txns:
            last = _fmt_dt(txns[0].get("created_at", ""))
            hl.addWidget(_vdiv())
            hl.addWidget(block("آخر تعامل", last, COLORS["text_secondary"]))
        hl.addStretch()
        return frame

    # ── Pills Row ────────────────────────────────────────

    def _make_pills_row(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(GAP_SM)
        t   = self._data.get("totals", {})
        c   = self._data.get("customer", {})
        debt = c.get("total_debt", 0) or 0

        data = [
            ("المديونية",    debt,                           COLORS["red"] if debt > 0 else COLORS["green"]),
            ("مؤجل",        t.get("total_pending", 0) or 0, COLORS["yellow"]),
            ("مسدد",        t.get("total_paid",    0) or 0, COLORS["green"]),
            ("نقدي",        t.get("total_cash",    0) or 0, COLORS["accent"]),
            ("صافي أرباح",  t.get("total_profit",  0) or 0, COLORS["purple"]),
        ]
        self._pills = []
        for label, val, color in data:
            p = SummaryPill(label, fmt_currency(val), color)
            self._pills.append((p, color))
            row.addWidget(p)
        return row

    def _refresh_pills(self):
        t    = self._data.get("totals", {})
        c    = self._data.get("customer", {})
        debt = c.get("total_debt", 0) or 0
        vals = [
            (debt,                          COLORS["red"] if debt > 0 else COLORS["green"]),
            (t.get("total_pending", 0) or 0, COLORS["yellow"]),
            (t.get("total_paid",    0) or 0, COLORS["green"]),
            (t.get("total_cash",    0) or 0, COLORS["accent"]),
            (t.get("total_profit",  0) or 0, COLORS["purple"]),
        ]
        for (pill, _), (v, _) in zip(self._pills, vals):
            pill.set_value(fmt_currency(v))

    # ── Filter Bar ───────────────────────────────────────

    def _make_filter_bar(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(GAP_SM)

        filters = [
            ("all",     "الكل",    COLORS["text_secondary"]),
            ("pending", "مؤجل ⏳", COLORS["yellow"]),
            ("paid",    "مسدد ✓",  COLORS["green"]),
            ("cash",    "نقدي ✓",  COLORS["accent"]),
            ("inbound", "وارد 📥", COLORS["purple"]),
        ]
        self._filter_btns = {}
        for key, label, color in filters:
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.setMinimumWidth(90)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._apply_filter(k))
            self._filter_btns[key] = (btn, color)
            row.addWidget(btn)

        row.addStretch()

        cleanup = QPushButton("🗑️  حذف المنتهية")
        cleanup.setObjectName("btn_danger")
        cleanup.setFixedHeight(32)
        cleanup.clicked.connect(self._cleanup)
        row.addWidget(cleanup)

        # Google Sheets sync hook
        sync_btn = QPushButton("☁️  مزامنة")
        sync_btn.setObjectName("btn_secondary")
        sync_btn.setFixedHeight(32)
        sync_btn.clicked.connect(self._sync_to_sheets)
        row.addWidget(sync_btn)

        self._apply_filter("all")
        return row

    def _apply_filter(self, key: str):
        self._filter = key
        for k, (btn, color) in self._filter_btns.items():
            if k == key:
                btn.setStyleSheet(
                    f"background:{color}18; color:{color};"
                    f"border:1.5px solid {color}; border-radius:8px;"
                    f"font-weight:bold; font-size:{FONT['sm']};"
                )
            else:
                btn.setStyleSheet(
                    f"background:{COLORS['bg_elevated']}; color:{COLORS['text_muted']};"
                    f"border:1px solid {COLORS['border']}; border-radius:8px;"
                    f"font-size:{FONT['sm']};"
                )
        self._reload_table()

    # ── Table Section ────────────────────────────────────

    def _make_table_section(self) -> QWidget:
        wrap = QWidget(); wrap.setLayoutDirection(RTL)
        vl   = QVBoxLayout(wrap)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(GAP_SM)

        self._table = TransactionTable()
        self._table.setMinimumHeight(320)
        vl.addWidget(self._table)

        self._count_lbl = _label("", "sm", COLORS["text_muted"], align=ALeft)
        vl.addWidget(self._count_lbl)
        return wrap

    def _reload_table(self):
        txns = self._data.get("transactions", [])
        if self._filter == "pending": txns = [t for t in txns if t.get("payment_status") == "pending"]
        elif self._filter == "paid":  txns = [t for t in txns if t.get("payment_status") == "paid"]
        elif self._filter == "cash":  txns = [t for t in txns if t.get("payment_status") == "cash"]
        elif self._filter == "inbound": txns = [t for t in txns if t.get("operation_type") == "inbound"]

        self._table.load(txns, self._on_status_change, self._on_delete)

        total = sum(t.get("amount_required", 0) or 0 for t in txns)
        self._count_lbl.setText(
            f"عرض {len(txns)} عملية  ·  إجمالي المطلوب: {fmt_currency(total)}"
        )

    # ── Footer Bar ───────────────────────────────────────

    def _make_footer_bar(self) -> QFrame:
        bar = _card()
        bar.setLayoutDirection(RTL)
        bar.setFixedHeight(46)
        hl  = QHBoxLayout(bar)
        hl.setContentsMargins(GAP_LG, 0, GAP_LG, 0)

        t    = self._data.get("totals", {})
        c    = self._data.get("customer", {})
        debt = c.get("total_debt", 0) or 0
        pending = t.get("total_pending", 0) or 0

        if debt > 0:
            balance_text  = f"عليه:  {fmt_currency(debt)}"
            balance_color = COLORS["red"]
        elif debt < 0:
            balance_text  = f"له:  {fmt_currency(abs(debt))}"
            balance_color = COLORS["green"]
        else:
            balance_text  = "صافر"
            balance_color = COLORS["text_muted"]

        self._footer_balance = _label(balance_text, "lg", balance_color, bold=True, align=ALeft)
        hl.addWidget(self._footer_balance)

        hl.addWidget(_vdiv())

        self._footer_pending = _label(
            f"مؤجل:  {fmt_currency(pending)}", "md", COLORS["yellow"], align=ALeft
        )
        hl.addWidget(self._footer_pending)
        hl.addStretch()

        date_lbl = _label(
            f"وقت الطباعة:  {datetime.now().strftime('%Y-%m-%d  %H:%M')}",
            "xs", COLORS["text_muted"], align=ALeft
        )
        hl.addWidget(date_lbl)
        return bar

    def _refresh_footer(self):
        t    = self._data.get("totals", {})
        c    = self._data.get("customer", {})
        debt = c.get("total_debt", 0) or 0
        pending = t.get("total_pending", 0) or 0

        if debt > 0:
            self._footer_balance.setText(f"عليه:  {fmt_currency(debt)}")
            self._footer_balance.setStyleSheet(
                f"color:{COLORS['red']}; font-size:{FONT['lg']}; font-weight:bold;"
            )
        elif debt < 0:
            self._footer_balance.setText(f"له:  {fmt_currency(abs(debt))}")
            self._footer_balance.setStyleSheet(
                f"color:{COLORS['green']}; font-size:{FONT['lg']}; font-weight:bold;"
            )
        else:
            self._footer_balance.setText("صافر")

        self._footer_pending.setText(f"مؤجل:  {fmt_currency(pending)}")

    # ── Actions ──────────────────────────────────────────

    def _on_status_change(self, tid: int, new_status: str):
        try:
            db.update_transaction_status(tid, new_status)
            self._load(); self._reload_table()
            self._refresh_pills(); self._refresh_footer()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _on_delete(self, tid: int):
        if QMessageBox.question(self, "تأكيد الحذف",
            "⚠️  حذف العملية سيعكس تأثيرها المالي.\nهل أنت متأكد؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            try:
                db.delete_transaction(tid)
                self._load(); self._reload_table()
                self._refresh_pills(); self._refresh_footer()
                QMessageBox.information(self, "تم ✓", "تم حذف العملية.")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _cleanup(self):
        n = db.count_finished_transactions(self.customer_id)
        if n == 0:
            QMessageBox.information(self, "لا يوجد", "لا توجد عمليات منتهية للحذف.")
            return
        if QMessageBox.question(self, "تنظيف",
            f"حذف {n} عملية منتهية (مسددة/مسلمة)؟\n⚠️  لا يمكن التراجع.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            deleted = db.cleanup_paid_transactions(self.customer_id)
            self._load(); self._reload_table()
            self._refresh_pills(); self._refresh_footer()
            QMessageBox.information(self, "تم ✓", f"تم حذف {deleted} عملية.")

    def _sync_to_sheets(self):
        """Google Sheets sync hook — يكتمل لما يتوفر backend"""
        # TODO: implement when google_sheets_service.py is ready
        # sync_to_google_sheets(self.customer_id, self._data)
        QMessageBox.information(
            self, "قريباً",
            "ميزة المزامنة مع Google Sheets قيد الإعداد.\n"
            "سيتم تفعيلها في التحديث القادم."
        )

    def _export_image(self):
        name = self._data.get("customer", {}).get("name", "عميل")
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", f"كشف_{name}.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG")
            QMessageBox.information(self, "تم ✓", f"تم الحفظ:\n{path}")

    def _export_pdf(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter
        name = self._data.get("customer", {}).get("name", "عميل")
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ PDF", f"كشف_{name}.pdf", "PDF (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            p = QPainter(printer); self.render(p); p.end()
            QMessageBox.information(self, "تم ✓", f"تم الحفظ:\n{path}")

    def _open_customer_facing(self):
        CustomerFacingDialog(self.customer_id, self).exec()


# ──────────────────────────────────────────────────────────
#  Vertical divider helper
# ──────────────────────────────────────────────────────────

def _vdiv() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setStyleSheet(
        f"background:{COLORS['border']}; max-width:1px; border:none;"
    )
    f.setFixedWidth(1)
    return f


# ──────────────────────────────────────────────────────────
#  CustomerFacingDialog  — كشف مبسط للعميل (بدون أرباح)
# ──────────────────────────────────────────────────────────

class CustomerFacingDialog(QDialog):

    def __init__(self, customer_id: int, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)
        self.setWindowTitle("كشف العميل")
        self.setMinimumSize(680, 560)
        self.resize(720, 620)
        self._data = db.get_customer_statement(customer_id)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(GAP_LG, GAP_LG, GAP_LG, GAP_LG)
        layout.setSpacing(GAP_MD)

        c    = self._data.get("customer", {})
        txns = self._data.get("transactions", [])

        # Header
        header_row = QHBoxLayout()
        save_btn = QPushButton("🖼️  حفظ كصورة")
        save_btn.setObjectName("btn_secondary"); save_btn.setFixedHeight(34)
        save_btn.clicked.connect(self._export_image)
        header_row.addWidget(save_btn)
        header_row.addStretch()
        header_row.addWidget(_label(
            f"كشف حساب — {c.get('name', '—')}",
            "lg", bold=True, align=ALLeft if False else ALeft
        ))
        layout.addLayout(header_row)

        # Customer info
        info = _card(); info.setLayoutDirection(RTL)
        il   = QHBoxLayout(info)
        il.setContentsMargins(GAP_LG, GAP_MD, GAP_LG, GAP_MD)
        il.setSpacing(GAP_LG)
        il.addWidget(_label(c.get("name", "—"), "xl", bold=True, align=ALeft))
        if c.get("phone"):
            il.addWidget(_label(f"📞 {c['phone']}", "md", COLORS["text_secondary"], align=ALeft))
        il.addStretch()
        il.addWidget(_label(
            datetime.now().strftime("📅  %Y-%m-%d"), "sm", COLORS["text_muted"], align=ALeft
        ))
        layout.addWidget(info)

        # Pending / Due
        pending_txns = [t for t in txns if t.get("payment_status") == "pending"]
        due_txns     = [t for t in txns if t.get("operation_type") == "inbound" and not t.get("is_delivered", 0)]
        total_pending = sum(t.get("amount_required", 0) or 0 for t in pending_txns)
        total_due     = sum(t.get("amount_spent",    0) or 0 for t in due_txns)
        net           = total_pending - total_due

        if pending_txns:
            layout.addWidget(_label("🔴  مبالغ عليك", "md", COLORS["red"], bold=True, align=ALeft))
            layout.addWidget(self._simple_table(pending_txns, "owed"))

        if due_txns:
            layout.addWidget(_label("🟢  مبالغ لك", "md", COLORS["green"], bold=True, align=ALeft))
            layout.addWidget(self._simple_table(due_txns, "due"))

        if not pending_txns and not due_txns:
            ok = _label("✓  لا توجد مبالغ مستحقة", "md", COLORS["green"], align=ACenter)
            ok.setStyleSheet(
                f"color:{COLORS['green']}; font-size:{FONT['md']};"
                f"background:{COLORS['green_bg']}; border-radius:8px; padding:12px;"
            )
            layout.addWidget(ok)

        layout.addStretch()

        # Net balance
        net_card = _card(); net_card.setLayoutDirection(RTL)
        nl = QHBoxLayout(net_card)
        nl.setContentsMargins(GAP_LG, GAP_MD, GAP_LG, GAP_MD)
        if net > 0:   color, label = COLORS["red"],   f"إجمالي المطلوب منك:  {fmt_currency(net)}"
        elif net < 0: color, label = COLORS["green"],  f"إجمالي المستحق لك:  {fmt_currency(abs(net))}"
        else:          color, label = COLORS["text_muted"], "صافر — لا شيء عليك"
        nl.addStretch()
        nl.addWidget(_label(label, "lg", color, bold=True, align=ALeft))
        layout.addWidget(net_card)

    def _simple_table(self, txns: list, mode: str) -> QFrame:
        frame = _card(); frame.setLayoutDirection(RTL)
        vl    = QVBoxLayout(frame)
        vl.setContentsMargins(GAP_MD, GAP_MD, GAP_MD, GAP_MD)
        vl.setSpacing(0)

        # header
        hrow = QHBoxLayout(); hrow.setSpacing(0)
        for text, flex in [("التاريخ", 0), ("البيان", 1), ("المبلغ", 0)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{COLORS['text_muted']}; font-size:{FONT['xs']}; font-weight:bold;"
                f"border-bottom:1px solid {COLORS['border']}; padding-bottom:4px;"
            )
            lbl.setAlignment(ALeft)
            if flex == 0: lbl.setFixedWidth(120)
            else: lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            hrow.addWidget(lbl)
        vl.addLayout(hrow)

        color = COLORS["red"] if mode == "owed" else COLORS["green"]
        for t in txns:
            rw  = QHBoxLayout()
            amt = (t.get("amount_required", 0) if mode == "owed" else t.get("amount_spent", 0)) or 0

            dl = QLabel((t.get("created_at") or "")[:10])
            dl.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:{FONT['sm']}; padding:6px 0;")
            dl.setFixedWidth(120); dl.setAlignment(ALeft)
            rw.addWidget(dl)

            sl = QLabel(t.get("service_name") or "—")
            sl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:{FONT['sm']}; padding:6px 0;")
            sl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            sl.setAlignment(ALeft)
            rw.addWidget(sl)

            al = QLabel(fmt_currency(amt))
            al.setStyleSheet(f"color:{color}; font-size:{FONT['sm']}; font-weight:bold; padding:6px 0;")
            al.setFixedWidth(120); al.setAlignment(ALLeft if False else ALeft)
            rw.addWidget(al)

            vl.addLayout(rw)
            vl.addWidget(_divider())

        return frame

    def _export_image(self):
        name = self._data.get("customer", {}).get("name", "عميل")
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", f"كشف_{name}.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG"); QMessageBox.information(self, "تم ✓", path)


# ──────────────────────────────────────────────────────────
#  GroupReportDialog
# ──────────────────────────────────────────────────────────

class GroupReportDialog(QDialog):

    def __init__(self, group_id: int, parent=None):
        super().__init__(parent)
        self.group_id = group_id
        self.setLayoutDirection(RTL)
        self.setWindowTitle("تقرير المجموعة")
        self.setMinimumSize(760, 520)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(GAP_LG, GAP_LG, GAP_LG, GAP_LG)
        layout.setSpacing(GAP_MD)

        groups    = db.get_all_groups()
        group     = next((g for g in groups if g["id"] == self.group_id), {})
        customers = db.get_customers_by_group(self.group_id)
        total     = sum(c.get("total_debt", 0) or 0 for c in customers)

        # Header
        hrow = QHBoxLayout()
        exp = QPushButton("🖼️ حفظ كصورة")
        exp.setObjectName("btn_secondary"); exp.setFixedHeight(34)
        exp.clicked.connect(self._export_image)
        hrow.addWidget(exp); hrow.addStretch()
        hrow.addWidget(_label(
            f"تقرير مجموعة — {group.get('name', '—')}", "lg", bold=True, align=ALeft
        ))
        layout.addLayout(hrow)

        # Members table
        from ui.components.widgets import DataTable
        tbl = DataTable([
            ("الاسم", 200), ("التليفون", 140), ("الرصيد", 150), ("ملاحظات", -1)
        ])
        tbl.setRowCount(len(customers))
        for row, c in enumerate(customers):
            d = c.get("total_debt", 0) or 0
            tbl.set_cell(row, 0, c["name"], bold=True)
            tbl.set_cell(row, 1, c.get("phone") or "—", COLORS["text_secondary"])
            tbl.set_cell(row, 2, fmt_currency(d),
                         COLORS["red"] if d > 0 else (COLORS["green"] if d < 0 else COLORS["text_muted"]))
            tbl.set_cell(row, 3, c.get("notes") or "—", COLORS["text_muted"])
        layout.addWidget(tbl)

        # Total footer
        foot = _card(); foot.setObjectName("card_highlight"); foot.setLayoutDirection(RTL)
        fl   = QHBoxLayout(foot); fl.setContentsMargins(GAP_LG, GAP_MD, GAP_LG, GAP_MD)
        color = COLORS["red"] if total > 0 else COLORS["green"]
        fl.addStretch()
        fl.addWidget(_label(f"إجمالي المجموعة:  {fmt_currency(total)}", "lg", color, bold=True))
        layout.addWidget(foot)

    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كصورة", "تقرير_المجموعة.png", "PNG (*.png)")
        if path:
            self.grab().save(path, "PNG"); QMessageBox.information(self, "تم ✓", path)
