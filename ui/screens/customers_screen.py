"""
Customers Screen — شاشة إدارة العملاء والمجموعات
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit,
    QDialog, QFormLayout, QMessageBox, QTabWidget,
    QHeaderView, QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from ui.styles.theme import COLORS
from ui.components.widgets import SectionTitle, DataTable
from utils.formatters import fmt_currency

import database as db


# ══════════════════════════════════════════
#  ديالوج إضافة / تعديل عميل
# ══════════════════════════════════════════

class CustomerDialog(QDialog):
    """ديالوج إضافة أو تعديل بيانات عميل"""

    def __init__(self, parent=None, customer: dict = None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("تعديل عميل" if customer else "إضافة عميل جديد")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        if customer:
            self._fill_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("تعديل عميل" if self.customer else "➕ إضافة عميل جديد")
        title.setObjectName("label_title")
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # الاسم
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العميل *")
        form.addRow(QLabel("الاسم:"), self.name_input)

        # التليفون
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم التليفون")
        form.addRow(QLabel("التليفون:"), self.phone_input)

        # المجموعة
        self.group_combo = QComboBox()
        self.group_combo.addItem("بدون مجموعة", None)
        for g in db.get_all_groups():
            self.group_combo.addItem(g["name"], g["id"])
        form.addRow(QLabel("المجموعة:"), self.group_combo)

        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        form.addRow(QLabel("ملاحظات:"), self.notes_input)

        layout.addLayout(form)

        # الأزرار
        btns = QHBoxLayout()
        btns.setSpacing(8)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        save_btn = QPushButton("حفظ ✅")
        save_btn.setObjectName("btn_primary")
        save_btn.clicked.connect(self._save)
        btns.addWidget(save_btn)

        layout.addLayout(btns)

    def _fill_data(self):
        self.name_input.setText(self.customer.get("name", ""))
        self.phone_input.setText(self.customer.get("phone", ""))
        self.notes_input.setPlainText(self.customer.get("notes", ""))

        group_id = self.customer.get("group_id")
        if group_id:
            idx = self.group_combo.findData(group_id)
            if idx >= 0:
                self.group_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم العميل مطلوب")
            return

        phone    = self.phone_input.text().strip()
        group_id = self.group_combo.currentData()
        notes    = self.notes_input.toPlainText().strip()

        try:
            if self.customer:
                db.update_customer(self.customer["id"], name, phone, group_id, notes)
            else:
                db.add_customer(name, phone, group_id, notes)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════
#  ديالوج إضافة / تعديل مجموعة
# ══════════════════════════════════════════

class GroupDialog(QDialog):
    """ديالوج إضافة أو تعديل مجموعة"""

    def __init__(self, parent=None, group: dict = None):
        super().__init__(parent)
        self.group = group
        self.setWindowTitle("تعديل مجموعة" if group else "إضافة مجموعة جديدة")
        self.setMinimumWidth(380)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        if group:
            self._fill_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("تعديل مجموعة" if self.group else "➕ إضافة مجموعة جديدة")
        title.setObjectName("label_title")
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # الاسم
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المجموعة *")
        form.addRow(QLabel("الاسم:"), self.name_input)

        # القائد
        self.leader_combo = QComboBox()
        self.leader_combo.addItem("بدون قائد", None)
        for c in db.get_all_customers():
            self.leader_combo.addItem(c["name"], c["id"])
        form.addRow(QLabel("القائد:"), self.leader_combo)

        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)
        form.addRow(QLabel("ملاحظات:"), self.notes_input)

        layout.addLayout(form)

        # الأزرار
        btns = QHBoxLayout()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        save_btn = QPushButton("حفظ ✅")
        save_btn.setObjectName("btn_primary")
        save_btn.clicked.connect(self._save)
        btns.addWidget(save_btn)

        layout.addLayout(btns)

    def _fill_data(self):
        self.name_input.setText(self.group.get("name", ""))
        self.notes_input.setPlainText(self.group.get("notes", ""))
        leader_id = self.group.get("leader_id")
        if leader_id:
            idx = self.leader_combo.findData(leader_id)
            if idx >= 0:
                self.leader_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم المجموعة مطلوب")
            return

        leader_id = self.leader_combo.currentData()
        notes     = self.notes_input.toPlainText().strip()

        try:
            if self.group:
                db.update_group(self.group["id"], name, leader_id, notes)
            else:
                db.add_group(name, leader_id, notes)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════
#  تاب العملاء
# ══════════════════════════════════════════

class CustomersTab(QWidget):
    """تاب قائمة العملاء"""
    open_statement = pyqtSignal(int)   # يرسل customer_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        # شريط الأدوات
        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  بحث باسم أو تليفون...")
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input)

        self.group_filter = QComboBox()
        self.group_filter.setFixedHeight(36)
        self.group_filter.setMinimumWidth(160)
        self.group_filter.addItem("كل المجموعات", None)
        self.group_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.group_filter)

        add_btn = QPushButton("+ إضافة عميل")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_customer)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        # الجدول
        columns = [
            ("الاسم",       200),
            ("التليفون",    130),
            ("المجموعة",    130),
            ("المديونية",   120),
            ("ملاحظات",     -1),
            ("إجراءات",     130),
        ]
        self.table = DataTable(columns)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # الإجمالي
        self.total_label = QLabel("")
        self.total_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.total_label)

    def load_data(self):
        """تحميل/تحديث بيانات العملاء"""
        # تحديث قائمة المجموعات في الفلتر
        current_group = self.group_filter.currentData()
        self.group_filter.blockSignals(True)
        self.group_filter.clear()
        self.group_filter.addItem("كل المجموعات", None)
        for g in db.get_all_groups():
            self.group_filter.addItem(g["name"], g["id"])
        # استعادة الاختيار
        idx = self.group_filter.findData(current_group)
        self.group_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.group_filter.blockSignals(False)

        self._load_table()

    def _load_table(self):
        query      = self.search_input.text().strip()
        group_id   = self.group_filter.currentData()

        if query:
            customers = db.search_customers(query)
        elif group_id:
            customers = db.get_customers_by_group(group_id)
        else:
            customers = db.get_all_customers()

        self._customers = customers
        self.table.clear_rows()
        self.table.setRowCount(len(customers))

        total_debt = 0
        for row, c in enumerate(customers):
            self.table.set_cell(row, 0, c["name"], bold=True)
            self.table.set_cell(row, 1, c.get("phone") or "—")
            self.table.set_cell(row, 2, c.get("group_name") or "—",
                                color=COLORS["text_secondary"])
            debt = c.get("total_debt") or 0
            total_debt += debt
            debt_color = COLORS["red"] if debt > 0 else COLORS["text_muted"]
            self.table.set_cell(row, 3, fmt_currency(debt), color=debt_color, bold=debt > 0)
            self.table.set_cell(row, 4, c.get("notes") or "—",
                                color=COLORS["text_muted"])

            # زرار كشف الحساب
            stmt_btn = QPushButton("كشف حساب")
            stmt_btn.setObjectName("btn_secondary")
            stmt_btn.setFixedHeight(28)
            stmt_btn.clicked.connect(lambda _, cid=c["id"]: self.open_statement.emit(cid))
            self.table.setCellWidget(row, 5, stmt_btn)

        self.table.setRowHeight
        self.total_label.setText(
            f"إجمالي العملاء: {len(customers)}  |  "
            f"إجمالي المديونيات: {fmt_currency(total_debt)}"
        )

    def _on_search(self):
        self._load_table()

    def _add_customer(self):
        dlg = CustomerDialog(self)
        if dlg.exec():
            self.load_data()

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row >= len(self._customers):
            return

        customer = self._customers[row]
        menu = QMenu(self)

        edit_action   = QAction("✏️  تعديل", self)
        delete_action = QAction("🗑️  حذف",   self)
        stmt_action   = QAction("📋  كشف حساب", self)

        edit_action.triggered.connect(lambda: self._edit_customer(customer))
        delete_action.triggered.connect(lambda: self._delete_customer(customer))
        stmt_action.triggered.connect(lambda: self.open_statement.emit(customer["id"]))

        menu.addAction(stmt_action)
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _edit_customer(self, customer: dict):
        full = db.get_customer_by_id(customer["id"])
        dlg  = CustomerDialog(self, full)
        if dlg.exec():
            self.load_data()

    def _delete_customer(self, customer: dict):
        debt = customer.get("total_debt", 0)
        msg  = f"هل تريد حذف العميل [{customer['name']}]؟"
        if debt and debt > 0:
            msg += f"\n⚠️ لديه مديونية {fmt_currency(debt)} — سيُحذف بشكل مؤقت فقط."

        reply = QMessageBox.question(
            self, "تأكيد الحذف", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_customer(customer["id"])
            self.load_data()


# ══════════════════════════════════════════
#  تاب المجموعات
# ══════════════════════════════════════════

class GroupsTab(QWidget):
    """تاب قائمة المجموعات"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        # شريط الأدوات
        toolbar = QHBoxLayout()
        toolbar.addStretch()

        add_btn = QPushButton("+ إضافة مجموعة")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_group)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        # الجدول
        columns = [
            ("اسم المجموعة", 200),
            ("القائد",       180),
            ("ملاحظات",      -1),
            ("إجراءات",      130),
        ]
        self.table = DataTable(columns)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
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

            edit_btn = QPushButton("تعديل")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setFixedHeight(28)
            edit_btn.clicked.connect(lambda _, grp=g: self._edit_group(grp))
            self.table.setCellWidget(row, 3, edit_btn)

    def _add_group(self):
        dlg = GroupDialog(self)
        if dlg.exec():
            self.load_data()

    def _edit_group(self, group: dict):
        dlg = GroupDialog(self, group)
        if dlg.exec():
            self.load_data()

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row >= len(self._groups):
            return

        group = self._groups[row]
        menu  = QMenu(self)

        edit_action   = QAction("✏️  تعديل", self)
        delete_action = QAction("🗑️  حذف",   self)

        edit_action.triggered.connect(lambda: self._edit_group(group))
        delete_action.triggered.connect(lambda: self._delete_group(group))

        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _delete_group(self, group: dict):
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف المجموعة [{group['name']}]؟\n"
            f"العملاء المنتمون إليها سيبقون بدون مجموعة.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_group(group["id"])
            self.load_data()


# ══════════════════════════════════════════
#  الشاشة الرئيسية
# ══════════════════════════════════════════

class CustomersScreen(QWidget):
    """شاشة إدارة العملاء والمجموعات"""
    open_statement = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(SectionTitle("👥 إدارة العملاء", "العملاء والمجموعات"))

        # Tabs
        self.tabs = QTabWidget()

        self.customers_tab = CustomersTab()
        self.customers_tab.open_statement.connect(self.open_statement)
        self.tabs.addTab(self.customers_tab, "العملاء")

        self.groups_tab = GroupsTab()
        self.tabs.addTab(self.groups_tab, "المجموعات")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

    def refresh(self):
        self.customers_tab.load_data()
        self.groups_tab.load_data()

    def _on_tab_changed(self, index):
        if index == 0:
            self.customers_tab.load_data()
        else:
            self.groups_tab.load_data()