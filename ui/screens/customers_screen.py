"""
customers_screen.py — شاشة العملاء (Professional Rebuild v5)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit,
    QDialog, QFormLayout, QMessageBox, QTabWidget,
    QMenu, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from ui.styles.theme import (
    COLORS, FONT, ROW_HEIGHT,
    GAP_XS, GAP_SM, GAP_MD, GAP_LG, GAP_XL,
    MARGIN_CARD, MARGIN_CONTENT
)
from ui.components.widgets import (
    ScreenShell, DataTable, CardGroup, make_divider
)
from utils.formatters import fmt_currency

import database as db

RTL    = Qt.LayoutDirection.RightToLeft
ALeft  = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


# ══════════════════════════════════════════════════════
#  CustomersScreen
# ══════════════════════════════════════════════════════

class CustomersScreen(ScreenShell):
    open_statement = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("العملاء", "إدارة العملاء والمجموعات")
        self._build_content()

    def _build_content(self):
        c = self.content()
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(RTL)

        self.customers_tab = CustomersTab()
        self.customers_tab.open_statement.connect(self.open_statement)
        self.tabs.addTab(self.customers_tab, "👥  العملاء")

        self.groups_tab = GroupsTab()
        self.tabs.addTab(self.groups_tab, "📋  المجموعات")

        self.tabs.currentChanged.connect(self._on_tab)
        c.addWidget(self.tabs)

    def refresh(self):
        self._on_tab(self.tabs.currentIndex())

    def _on_tab(self, idx: int):
        if idx == 0: self.customers_tab.load_data()
        else:        self.groups_tab.load_data()


# ══════════════════════════════════════════════════════
#  CustomersTab
# ══════════════════════════════════════════════════════

class CustomersTab(QWidget):
    open_statement = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)
        self._customers = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_LG)

        # ── Toolbar card
        toolbar_card = CardGroup()
        tb = QHBoxLayout()
        tb.setSpacing(GAP_MD)

        add_btn = QPushButton("＋  إضافة عميل")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(38)
        add_btn.clicked.connect(self._add_customer)
        tb.addWidget(add_btn)

        tb.addStretch()

        self.group_filter = QComboBox()
        self.group_filter.setFixedHeight(38)
        self.group_filter.setMinimumWidth(160)
        self.group_filter.currentIndexChanged.connect(self.load_data)
        tb.addWidget(self.group_filter)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  بحث باسم أو تليفون...")
        self.search.setFixedHeight(38)
        self.search.setMinimumWidth(240)
        self.search.textChanged.connect(self._load_table)
        tb.addWidget(self.search)

        toolbar_card.add_layout(tb)
        layout.addWidget(toolbar_card)

        # ── Table card — task 7: clear space between toolbar and table
        layout.addSpacing(GAP_SM)

        table_card = CardGroup("👥  قائمة العملاء")

        cols = [
            ("الاسم",    200),
            ("التليفون", 130),
            ("المجموعة", 130),
            ("عليه 🔴",  120),
            ("له 🟢",    120),
            ("ملاحظات",   -1),
            ("الكشف",    150),
        ]
        self.table = DataTable(cols)
        # task 8: taller rows
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx_menu)
        table_card.add_widget(self.table)

        self.total_lbl = QLabel("")
        self.total_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']}; font-size:{FONT['xs']}; padding:{GAP_SM}px 0;"
        )
        self.total_lbl.setAlignment(ALeft)
        table_card.add_widget(self.total_lbl)

        layout.addWidget(table_card)

    def load_data(self):
        current = self.group_filter.currentData()
        self.group_filter.blockSignals(True)
        self.group_filter.clear()
        self.group_filter.addItem("كل المجموعات", None)
        for g in db.get_all_groups():
            self.group_filter.addItem(g["name"], g["id"])
        idx = self.group_filter.findData(current)
        self.group_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.group_filter.blockSignals(False)
        self._load_table()

    def _load_table(self):
        query    = self.search.text().strip()
        group_id = self.group_filter.currentData()
        if query:    customers = db.search_customers(query)
        elif group_id: customers = db.get_customers_by_group(group_id)
        else:          customers = db.get_all_customers()

        customers = sorted(customers, key=lambda c: -(c.get("total_debt") or 0))
        self._customers = customers
        self.table.clear_rows()
        self.table.setRowCount(len(customers))

        total_owed = total_due = 0

        for row, c in enumerate(customers):
            self.table.set_cell(row, 0, c["name"], bold=True)
            self.table.set_cell(row, 1, c.get("phone") or "—", COLORS["text_secondary"])
            self.table.set_cell(row, 2, c.get("group_name") or "—", COLORS["text_muted"])

            debt = c.get("total_debt") or 0
            if debt > 0:
                self.table.set_cell(row, 3, fmt_currency(debt), COLORS["red"], bold=True)
                self.table.set_cell(row, 4, "—", COLORS["text_muted"])
                total_owed += debt
            elif debt < 0:
                self.table.set_cell(row, 3, "—", COLORS["text_muted"])
                self.table.set_cell(row, 4, fmt_currency(abs(debt)), COLORS["green"], bold=True)
                total_due += abs(debt)
            else:
                self.table.set_cell(row, 3, "—", COLORS["text_muted"])
                self.table.set_cell(row, 4, "—", COLORS["text_muted"])

            self.table.set_cell(row, 5, c.get("notes") or "—", COLORS["text_muted"])

            # task 8: prominent statement button
            btn = QPushButton("📋  كشف الحساب")
            btn.setFixedHeight(36)
            btn.setStyleSheet(
                f"background:{COLORS['accent']}; color:#fff; border-radius:8px;"
                f"font-size:{FONT['sm']}; font-weight:bold; padding:0 10px;"
                f"border:none;"
            )
            btn.clicked.connect(lambda _, cid=c["id"]: self._open_statement(cid))

            wrap = QWidget(); wl = QHBoxLayout(wrap)
            wl.setContentsMargins(6, 4, 6, 4)
            wl.addWidget(btn)
            self.table.setCellWidget(row, 6, wrap)

        parts = [f"إجمالي: {len(customers)} عميل"]
        if total_owed: parts.append(f"عليهم: {fmt_currency(total_owed)}")
        if total_due:  parts.append(f"لهم: {fmt_currency(total_due)}")
        self.total_lbl.setText("  ·  ".join(parts))

    def _add_customer(self):
        if CustomerDialog(self).exec(): self.load_data()

    def _open_statement(self, cid: int):
        from ui.screens.statement_screen import CustomerStatementDialog
        CustomerStatementDialog(cid, self).exec()

    def _ctx_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row >= len(self._customers): return
        c   = self._customers[row]
        menu = QMenu(self)
        menu.addAction(QAction("📋  كشف حساب", self, triggered=lambda: self._open_statement(c["id"])))
        menu.addAction(QAction("✏️  تعديل",    self, triggered=lambda: self._edit(c)))
        menu.addSeparator()
        menu.addAction(QAction("🗑️  حذف",      self, triggered=lambda: self._delete(c)))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _edit(self, c: dict):
        full = db.get_customer_by_id(c["id"])
        if CustomerDialog(self, full).exec(): self.load_data()

    def _delete(self, c: dict):
        debt = c.get("total_debt", 0)
        msg  = f"هل تريد حذف العميل [{c['name']}]؟"
        if debt and debt > 0: msg += f"\n⚠️  لديه مديونية {fmt_currency(debt)}"
        if QMessageBox.question(self, "تأكيد الحذف", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            db.delete_customer(c["id"]); self.load_data()


# ══════════════════════════════════════════════════════
#  GroupsTab
# ══════════════════════════════════════════════════════

class GroupsTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)
        self._groups = []
        self._all_groups = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_LG)

        # ── Toolbar card — task 9: search for groups
        toolbar_card = CardGroup()
        tb = QHBoxLayout(); tb.setSpacing(GAP_MD)

        add_btn = QPushButton("＋  إضافة مجموعة")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(38)
        add_btn.clicked.connect(self._add_group)
        tb.addWidget(add_btn)

        tb.addStretch()

        self.group_search = QLineEdit()
        self.group_search.setPlaceholderText("🔍  بحث باسم المجموعة...")
        self.group_search.setFixedHeight(38)
        self.group_search.setMinimumWidth(240)
        self.group_search.textChanged.connect(self._filter)
        tb.addWidget(self.group_search)

        toolbar_card.add_layout(tb)
        layout.addWidget(toolbar_card)

        layout.addSpacing(GAP_SM)

        # ── Table card — task 10: bigger rows + visible buttons
        table_card = CardGroup("📋  قائمة المجموعات")

        cols = [
            ("اسم المجموعة", 200),
            ("القائد",        180),
            ("ملاحظات",        -1),
            ("إجراءات",       210),
        ]
        self.table = DataTable(cols)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx_menu)
        table_card.add_widget(self.table)
        layout.addWidget(table_card)

    def load_data(self):
        self._all_groups = db.get_all_groups()
        self._groups     = list(self._all_groups)
        self._render()

    def _filter(self, text: str):
        if not self._all_groups: return
        q = text.strip().lower()
        self._groups = (
            [g for g in self._all_groups if q in g["name"].lower()]
            if q else list(self._all_groups)
        )
        self._render()

    def _render(self):
        self.table.clear_rows()
        self.table.setRowCount(len(self._groups))

        for row, g in enumerate(self._groups):
            self.table.set_cell(row, 0, g["name"], bold=True)
            self.table.set_cell(row, 1, g.get("leader_name") or "—", COLORS["text_secondary"])
            self.table.set_cell(row, 2, g.get("notes") or "—", COLORS["text_muted"])

            # task 10: clear, well-spaced action buttons
            wrap = QWidget(); wrap.setLayoutDirection(RTL)
            wl   = QHBoxLayout(wrap)
            wl.setContentsMargins(GAP_SM, GAP_SM, GAP_SM, GAP_SM)
            wl.setSpacing(GAP_SM)

            edit_btn = QPushButton("✏️  تعديل")
            edit_btn.setObjectName("btn_ghost")
            edit_btn.setFixedHeight(34)
            edit_btn.setMinimumWidth(80)
            edit_btn.clicked.connect(lambda _, grp=g: self._edit_group(grp))
            wl.addWidget(edit_btn)

            report_btn = QPushButton("📊  تقرير")
            report_btn.setObjectName("btn_ghost")
            report_btn.setFixedHeight(34)
            report_btn.setMinimumWidth(80)
            report_btn.clicked.connect(lambda _, gid=g["id"]: self._show_report(gid))
            wl.addWidget(report_btn)

            self.table.setCellWidget(row, 3, wrap)

    def _add_group(self):
        if GroupDialog(self).exec(): self.load_data()

    def _edit_group(self, g: dict):
        if GroupDialog(self, g).exec(): self.load_data()

    def _show_report(self, gid: int):
        from ui.screens.statement_screen import GroupReportDialog
        GroupReportDialog(gid, self).exec()

    def _ctx_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row >= len(self._groups): return
        g   = self._groups[row]
        menu = QMenu(self)
        menu.addAction(QAction("📊  تقرير",  self, triggered=lambda: self._show_report(g["id"])))
        menu.addAction(QAction("✏️  تعديل", self, triggered=lambda: self._edit_group(g)))
        menu.addSeparator()
        menu.addAction(QAction("🗑️  حذف",   self, triggered=lambda: self._delete(g)))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _delete(self, g: dict):
        if QMessageBox.question(self, "تأكيد الحذف",
            f"هل تريد حذف المجموعة [{g['name']}]؟\nالعملاء سيبقون بدون مجموعة.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            db.delete_group(g["id"]); self.load_data()


# ══════════════════════════════════════════════════════
#  CustomerDialog
# ══════════════════════════════════════════════════════

class CustomerDialog(QDialog):

    def __init__(self, parent=None, customer: dict = None):
        super().__init__(parent)
        self.customer = customer
        self.setLayoutDirection(RTL)
        self.setWindowTitle("تعديل عميل" if customer else "إضافة عميل جديد")
        self.setMinimumWidth(440)
        self._build()
        if customer: self._fill()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(GAP_LG, GAP_LG, GAP_LG, GAP_LG)
        layout.setSpacing(GAP_MD)

        title = QLabel("تعديل عميل" if self.customer else "➕  إضافة عميل جديد")
        title.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;"
        )
        title.setAlignment(ALeft)
        layout.addWidget(title)
        layout.addWidget(_make_div())

        form = QFormLayout(); form.setSpacing(GAP_MD)
        form.setLabelAlignment(ALeft)

        self.name_input  = QLineEdit(); self.name_input.setPlaceholderText("اسم العميل *")
        self.phone_input = QLineEdit(); self.phone_input.setPlaceholderText("رقم التليفون")

        self.group_combo = QComboBox()
        self.group_combo.addItem("بدون مجموعة", None)
        for g in db.get_all_groups():
            self.group_combo.addItem(g["name"], g["id"])

        self.notes_input = QTextEdit(); self.notes_input.setMaximumHeight(72)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")

        form.addRow("الاسم *:", self.name_input)
        form.addRow("التليفون:", self.phone_input)
        form.addRow("المجموعة:", self.group_combo)
        form.addRow("ملاحظات:", self.notes_input)
        layout.addLayout(form)
        layout.addStretch()

        btns = QHBoxLayout(); btns.setSpacing(GAP_SM)
        cancel = QPushButton("إلغاء"); cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject); btns.addWidget(cancel)
        save = QPushButton("حفظ ✓"); save.setObjectName("btn_primary")
        save.clicked.connect(self._save); btns.addWidget(save)
        layout.addLayout(btns)

    def _fill(self):
        self.name_input.setText(self.customer.get("name", ""))
        self.phone_input.setText(self.customer.get("phone", ""))
        self.notes_input.setPlainText(self.customer.get("notes", ""))
        gid = self.customer.get("group_id")
        if gid:
            idx = self.group_combo.findData(gid)
            if idx >= 0: self.group_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم العميل مطلوب"); return
        try:
            db.update_customer(self.customer["id"], name,
                self.phone_input.text().strip(),
                self.group_combo.currentData(),
                self.notes_input.toPlainText().strip()
            ) if self.customer else db.add_customer(
                name,
                self.phone_input.text().strip(),
                self.group_combo.currentData(),
                self.notes_input.toPlainText().strip()
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════════════════
#  GroupDialog
# ══════════════════════════════════════════════════════

class GroupDialog(QDialog):

    def __init__(self, parent=None, group: dict = None):
        super().__init__(parent)
        self.group = group
        self.setLayoutDirection(RTL)
        self.setWindowTitle("تعديل مجموعة" if group else "إضافة مجموعة جديدة")
        self.setMinimumWidth(380)
        self._build()
        if group: self._fill()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(GAP_LG, GAP_LG, GAP_LG, GAP_LG)
        layout.setSpacing(GAP_MD)

        title = QLabel("تعديل مجموعة" if self.group else "➕  إضافة مجموعة جديدة")
        title.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['lg']}; font-weight:bold;"
        )
        title.setAlignment(ALeft)
        layout.addWidget(title)
        layout.addWidget(_make_div())

        form = QFormLayout(); form.setSpacing(GAP_MD)
        form.setLabelAlignment(ALeft)

        self.name_input   = QLineEdit(); self.name_input.setPlaceholderText("اسم المجموعة *")
        self.leader_combo = QComboBox()
        self.leader_combo.addItem("بدون قائد", None)
        for c in db.get_all_customers():
            self.leader_combo.addItem(c["name"], c["id"])
        self.notes_input = QTextEdit(); self.notes_input.setMaximumHeight(64)

        form.addRow("الاسم *:", self.name_input)
        form.addRow("القائد:", self.leader_combo)
        form.addRow("ملاحظات:", self.notes_input)
        layout.addLayout(form)
        layout.addStretch()

        btns = QHBoxLayout(); btns.setSpacing(GAP_SM)
        cancel = QPushButton("إلغاء"); cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject); btns.addWidget(cancel)
        save = QPushButton("حفظ ✓"); save.setObjectName("btn_primary")
        save.clicked.connect(self._save); btns.addWidget(save)
        layout.addLayout(btns)

    def _fill(self):
        self.name_input.setText(self.group.get("name", ""))
        self.notes_input.setPlainText(self.group.get("notes", ""))
        lid = self.group.get("leader_id")
        if lid:
            idx = self.leader_combo.findData(lid)
            if idx >= 0: self.leader_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم المجموعة مطلوب"); return
        try:
            lid   = self.leader_combo.currentData()
            notes = self.notes_input.toPlainText().strip()
            if self.group: db.update_group(self.group["id"], name, lid, notes)
            else:          db.add_group(name, lid, notes)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


# ── local helpers ──────────────────────────────────────

def _make_div() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background:{COLORS['border']}; max-height:1px; border:none;")
    return f
