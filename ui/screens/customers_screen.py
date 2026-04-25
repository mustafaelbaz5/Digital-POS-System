"""
customers_screen.py — شاشة إدارة العملاء والمجموعات
Refactored: ScreenShell, cleaner dialogs, better table layout
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit,
    QDialog, QFormLayout, QMessageBox, QTabWidget,
    QMenu, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from ui.styles.theme import COLORS
from ui.components.widgets import ScreenShell, DataTable, make_divider
from utils.formatters import fmt_currency

import database as db


class CustomersScreen(ScreenShell):
    open_statement = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("العملاء", "إدارة العملاء والمجموعات")
        self._build_content()

    def _build_content(self):
        c = self.content()

        # Tabs
        self.tabs = QTabWidget()

        self.customers_tab = CustomersTab()
        self.customers_tab.open_statement.connect(self.open_statement)
        self.tabs.addTab(self.customers_tab, "العملاء")

        self.groups_tab = GroupsTab()
        self.tabs.addTab(self.groups_tab, "المجموعات")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        c.addWidget(self.tabs)

    def refresh(self):
        idx = self.tabs.currentIndex()
        self._on_tab_changed(idx)

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.customers_tab.load_data()
        else:
            self.groups_tab.load_data()


# ══════════════════════════════════════════
#  Customers Tab
# ══════════════════════════════════════════

class CustomersTab(QWidget):
    open_statement = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._customers = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        add_btn = QPushButton("＋  إضافة عميل")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_customer)
        toolbar.addWidget(add_btn)

        toolbar.addStretch()

        self.group_filter = QComboBox()
        self.group_filter.setFixedHeight(36)
        self.group_filter.setMinimumWidth(160)
        self.group_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.group_filter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  بحث باسم أو تليفون...")
        self.search_input.setFixedHeight(36)
        self.search_input.setMinimumWidth(220)
        self.search_input.textChanged.connect(self._load_table)
        toolbar.addWidget(self.search_input)

        layout.addLayout(toolbar)

        # Table
        columns = [
            ("الاسم",       200),
            ("التليفون",    130),
            ("المجموعة",    130),
            ("عليه 🔴",     115),
            ("له 🟢",       115),
            ("ملاحظات",      -1),
            ("إجراءات",     115),
        ]
        self.table = DataTable(columns)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.table)

        # Footer summary
        self.total_label = QLabel("")
        self.total_label.setObjectName("label_muted")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.total_label)

    def load_data(self):
        # Refresh group filter
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
        query    = self.search_input.text().strip()
        group_id = self.group_filter.currentData()

        if query:
            customers = db.search_customers(query)
        elif group_id:
            customers = db.get_customers_by_group(group_id)
        else:
            customers = db.get_all_customers()

        # ترتيب: الأعلى مديونية أولاً، ثم اللي له رصيد، ثم الصفر
        customers = sorted(
            customers,
            key=lambda c: (-(c.get("total_debt") or 0))
        )
        self._customers = customers
        self.table.clear_rows()
        self.table.setRowCount(len(customers))

        total_owed = 0   # إجمالي ما عليهم
        total_due  = 0   # إجمالي ما لهم

        for row, c in enumerate(customers):
            self.table.set_cell(row, 0, c["name"], bold=True)
            self.table.set_cell(row, 1, c.get("phone") or "—",
                                color=COLORS["text_secondary"])
            self.table.set_cell(row, 2, c.get("group_name") or "—",
                                color=COLORS["text_muted"])

            debt = c.get("total_debt") or 0
            if debt > 0:
                # عليه (مدين)
                self.table.set_cell(row, 3, fmt_currency(debt),
                                    color=COLORS["red"], bold=True)
                self.table.set_cell(row, 4, "—", color=COLORS["text_muted"])
                total_owed += debt
            elif debt < 0:
                # له (دائن) — القيمة سالبة يعني احنا بندين له
                self.table.set_cell(row, 3, "—", color=COLORS["text_muted"])
                self.table.set_cell(row, 4, fmt_currency(abs(debt)),
                                    color=COLORS["green"], bold=True)
                total_due += abs(debt)
            else:
                self.table.set_cell(row, 3, "—", color=COLORS["text_muted"])
                self.table.set_cell(row, 4, "—", color=COLORS["text_muted"])

            self.table.set_cell(row, 5, c.get("notes") or "—",
                                color=COLORS["text_muted"])

            stmt_btn = QPushButton("كشف")
            stmt_btn.setObjectName("btn_ghost")
            stmt_btn.setFixedHeight(26)
            stmt_btn.clicked.connect(
                lambda _, cid=c["id"]: self._open_statement(cid)
            )
            self.table.setCellWidget(row, 6, stmt_btn)

        summary_parts = [f"إجمالي العملاء: {len(customers)}"]
        if total_owed > 0:
            summary_parts.append(f"عليهم: {fmt_currency(total_owed)}")
        if total_due > 0:
            summary_parts.append(f"لهم: {fmt_currency(total_due)}")
        self.total_label.setText("  ·  ".join(summary_parts))

    def _add_customer(self):
        if CustomerDialog(self).exec():
            self.load_data()

    def _open_statement(self, customer_id: int):
        from ui.screens.statement_screen import CustomerStatementDialog
        dialog = CustomerStatementDialog(customer_id, self)
        dialog.exec()

    def _context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row >= len(self._customers):
            return

        customer = self._customers[row]
        menu = QMenu(self)

        menu.addAction(QAction("📋  كشف حساب", self,
            triggered=lambda: self.open_statement.emit(customer["id"])))
        menu.addAction(QAction("✏️  تعديل", self,
            triggered=lambda: self._edit_customer(customer)))
        menu.addSeparator()
        menu.addAction(QAction("🗑️  حذف", self,
            triggered=lambda: self._delete_customer(customer)))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _edit_customer(self, customer: dict):
        full = db.get_customer_by_id(customer["id"])
        if CustomerDialog(self, full).exec():
            self.load_data()

    def _delete_customer(self, customer: dict):
        debt = customer.get("total_debt", 0)
        msg  = f"هل تريد حذف العميل [{customer['name']}]؟"
        if debt and debt > 0:
            msg += f"\n⚠️ لديه مديونية {fmt_currency(debt)}"

        if QMessageBox.question(
            self, "تأكيد الحذف", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            db.delete_customer(customer["id"])
            self.load_data()


# ══════════════════════════════════════════
#  Groups Tab
# ══════════════════════════════════════════

class GroupsTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._groups = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("＋  إضافة مجموعة")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_group)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        columns = [
            ("اسم المجموعة", 200),
            ("القائد",        180),
            ("ملاحظات",        -1),
            ("إجراءات",       130),
        ]
        self.table = DataTable(columns)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.table)

    def load_data(self):
        groups = db.get_all_groups()
        self._groups = groups
        self.table.clear_rows()
        self.table.setRowCount(len(groups))

        for row, g in enumerate(groups):
            self.table.set_cell(row, 0, g["name"], bold=True)
            self.table.set_cell(row, 1, g.get("leader_name") or "—",
                                color=COLORS["text_secondary"])
            self.table.set_cell(row, 2, g.get("notes") or "—",
                                color=COLORS["text_muted"])

            row_btns = QHBoxLayout()
            row_btns.setContentsMargins(6, 2, 6, 2)
            row_btns.setSpacing(4)

            edit_btn = QPushButton("تعديل")
            edit_btn.setObjectName("btn_ghost")
            edit_btn.setFixedHeight(26)
            edit_btn.clicked.connect(lambda _, grp=g: self._edit_group(grp))
            row_btns.addWidget(edit_btn)

            report_btn = QPushButton("تقرير")
            report_btn.setObjectName("btn_ghost")
            report_btn.setFixedHeight(26)
            report_btn.clicked.connect(lambda _, grp=g: self._show_group_report(grp["id"]))
            row_btns.addWidget(report_btn)

            container = QWidget()
            container.setLayout(row_btns)
            self.table.setCellWidget(row, 3, container)

    def _add_group(self):
        if GroupDialog(self).exec():
            self.load_data()

    def _edit_group(self, group: dict):
        if GroupDialog(self, group).exec():
            self.load_data()

    def _show_group_report(self, group_id: int):
        from ui.screens.statement_screen import GroupReportDialog
        GroupReportDialog(group_id, self).exec()

    def _context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row >= len(self._groups):
            return

        group = self._groups[row]
        menu = QMenu(self)
        menu.addAction(QAction("✏️  تعديل", self,
            triggered=lambda: self._edit_group(group)))
        menu.addSeparator()
        menu.addAction(QAction("🗑️  حذف", self,
            triggered=lambda: self._delete_group(group)))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _delete_group(self, group: dict):
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف المجموعة [{group['name']}]؟\n"
            "العملاء سيبقون بدون مجموعة.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            db.delete_group(group["id"])
            self.load_data()


# ══════════════════════════════════════════
#  Customer Dialog
# ══════════════════════════════════════════

class CustomerDialog(QDialog):

    def __init__(self, parent=None, customer: dict = None):
        super().__init__(parent)
        self.customer = customer
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("تعديل عميل" if customer else "إضافة عميل جديد")
        self.setMinimumWidth(420)
        self.setMinimumHeight(340)
        self._build_ui()
        if customer:
            self._fill_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("تعديل عميل" if self.customer else "➕  إضافة عميل جديد")
        title.setObjectName("label_title")
        title.setStyleSheet(f"font-size: 15px; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العميل *")
        form.addRow("الاسم:", self.name_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم التليفون")
        form.addRow("التليفون:", self.phone_input)

        self.group_combo = QComboBox()
        self.group_combo.addItem("بدون مجموعة", None)
        for g in db.get_all_groups():
            self.group_combo.addItem(g["name"], g["id"])
        form.addRow("المجموعة:", self.group_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(72)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        form.addRow("ملاحظات:", self.notes_input)

        layout.addLayout(form)
        layout.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(8)
        cancel = QPushButton("إلغاء")
        cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        save = QPushButton("حفظ ✅")
        save.setObjectName("btn_primary")
        save.clicked.connect(self._save)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _fill_data(self):
        self.name_input.setText(self.customer.get("name", ""))
        self.phone_input.setText(self.customer.get("phone", ""))
        self.notes_input.setPlainText(self.customer.get("notes", ""))
        gid = self.customer.get("group_id")
        if gid:
            idx = self.group_combo.findData(gid)
            if idx >= 0:
                self.group_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم العميل مطلوب")
            return
        try:
            phone    = self.phone_input.text().strip()
            group_id = self.group_combo.currentData()
            notes    = self.notes_input.toPlainText().strip()
            if self.customer:
                db.update_customer(self.customer["id"], name, phone, group_id, notes)
            else:
                db.add_customer(name, phone, group_id, notes)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════
#  Group Dialog
# ══════════════════════════════════════════

class GroupDialog(QDialog):

    def __init__(self, parent=None, group: dict = None):
        super().__init__(parent)
        self.group = group
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("تعديل مجموعة" if group else "إضافة مجموعة جديدة")
        self.setMinimumWidth(380)
        self.setMinimumHeight(300)
        self._build_ui()
        if group:
            self._fill_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("تعديل مجموعة" if self.group else "➕  إضافة مجموعة جديدة")
        title.setObjectName("label_title")
        title.setStyleSheet(f"font-size: 15px; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المجموعة *")
        form.addRow("الاسم:", self.name_input)

        self.leader_combo = QComboBox()
        self.leader_combo.addItem("بدون قائد", None)
        for c in db.get_all_customers():
            self.leader_combo.addItem(c["name"], c["id"])
        form.addRow("القائد:", self.leader_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(64)
        form.addRow("ملاحظات:", self.notes_input)

        layout.addLayout(form)
        layout.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(8)
        cancel = QPushButton("إلغاء")
        cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        save = QPushButton("حفظ ✅")
        save.setObjectName("btn_primary")
        save.clicked.connect(self._save)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _fill_data(self):
        self.name_input.setText(self.group.get("name", ""))
        self.notes_input.setPlainText(self.group.get("notes", ""))
        lid = self.group.get("leader_id")
        if lid:
            idx = self.leader_combo.findData(lid)
            if idx >= 0:
                self.leader_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم المجموعة مطلوب")
            return
        try:
            lid   = self.leader_combo.currentData()
            notes = self.notes_input.toPlainText().strip()
            if self.group:
                db.update_group(self.group["id"], name, lid, notes)
            else:
                db.add_group(name, lid, notes)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))