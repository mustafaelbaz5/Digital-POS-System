"""
customers_screen.py — شاشة العملاء (Professional Rebuild v5)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import BaseDialog, DataTable, ScreenShell
from ui.styles.theme import COLORS, FONT, GAP_MD, GAP_SM, GAP_XS, ROW_HEIGHT
from ui.utils.formatters import fmt_currency

RTL = Qt.LayoutDirection.RightToLeft
ALeft = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


# ══════════════════════════════════════════════════════
#  CustomersScreen
# ══════════════════════════════════════════════════════


class CustomersScreen(ScreenShell):
    open_statement = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("إدارة العملاء والمجموعات", "")
        self._build_content()

    def _build_content(self):
        c = self.content()
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(RTL)

        self.customers_tab = CustomersTab()
        self.customers_tab.open_statement.connect(self.open_statement)
        self.tabs.addTab(self.customers_tab, "👥  العملاء")

        self.groups_tab = GroupsTab()
        self.tabs.addTab(self.groups_tab, "📂  المجموعات")

        self.tabs.currentChanged.connect(self._on_tab)
        c.addWidget(self.tabs)

    def refresh(self):
        self._on_tab(self.tabs.currentIndex())

    def _on_tab(self, idx: int):
        if idx == 0:
            self.customers_tab.load_data()
        else:
            self.groups_tab.load_data()


class CustomersTab(QWidget):
    open_statement = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(RTL)
        self._customers = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, GAP_XS, 0, 0)
        layout.setSpacing(GAP_MD)

        # ── Middle Layer: Add Button & Search
        tb_row = QHBoxLayout()
        tb_row.setContentsMargins(0, 0, 0, 0)
        tb_row.setSpacing(GAP_MD)

        add_btn = QPushButton("➕ إضافة عميل")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(42)
        add_btn.setMinimumWidth(160)
        add_btn.clicked.connect(self._add_customer)
        tb_row.addWidget(add_btn)

        tb_row.addStretch()

        self.group_filter = QComboBox()
        self.group_filter.setFixedHeight(42)
        self.group_filter.setMinimumWidth(200)  # Expanded width
        self.group_filter.setStyleSheet(
            f"background: {COLORS['bg_hover']}; font-weight: bold; font-size: 14px;"
        )
        self.group_filter.currentIndexChanged.connect(self.load_data)
        tb_row.addWidget(self.group_filter)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  بحث باسم أو تليفون...")
        self.search.setFixedHeight(42)
        self.search.setMinimumWidth(320)
        self.search.textChanged.connect(self._load_table)
        tb_row.addWidget(self.search)

        layout.addLayout(tb_row)
        layout.addSpacing(GAP_SM)

        # # ── Bottom Layer: Table Section
        # from ui.components.widgets import SectionTitle
        # self.table_title = SectionTitle("👥  قائمة العملاء")
        # layout.addWidget(self.table_title)
        # layout.addSpacing(GAP_SM)

        cols = [
            ("الاسم", -1),
            ("التليفون", 120),
            ("المجموعة", 120),
            ("عليه 🔴", 110),
            ("له 🟢", 110),
            ("الإجراءات", 280),
        ]
        self.table = DataTable(cols)
        self.table.horizontalHeader().setVisible(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx_menu)

        # Disable internal scroll
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        layout.addWidget(self.table)

        self.total_lbl = QLabel("")
        self.total_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']}; font-size:{FONT['xs']}; padding:{GAP_SM}px {GAP_MD}px;"
        )
        self.total_lbl.setAlignment(ALeft)
        layout.addWidget(self.total_lbl)

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
        query = self.search.text().strip()
        group_id = self.group_filter.currentData()
        if query:
            customers = db.search_customers(query)
        elif group_id:
            customers = db.get_customers_by_group(group_id)
        else:
            customers = db.get_all_customers()

        customers = sorted(customers, key=lambda c: -(c.get("total_debt") or 0))
        self._customers = customers
        self.table.clear_rows()
        self.table.setRowCount(len(customers))

        total_owed = total_due = 0

        for row, c in enumerate(customers):
            self.table.set_cell(row, 0, c["name"], bold=True)
            self.table.set_cell(row, 1, c.get("phone") or "—", COLORS["text_secondary"])
            self.table.set_cell(
                row, 2, c.get("group_name") or "—", COLORS["text_muted"]
            )

            debt = c.get("total_debt") or 0
            if debt > 0:
                self.table.set_cell(
                    row, 3, fmt_currency(debt), COLORS["red"], bold=True
                )
                self.table.set_cell(row, 4, "—", COLORS["text_muted"])
                total_owed += debt
            elif debt < 0:
                self.table.set_cell(row, 3, "—", COLORS["text_muted"])
                self.table.set_cell(
                    row, 4, fmt_currency(abs(debt)), COLORS["green"], bold=True
                )
                total_due += abs(debt)
            else:
                self.table.set_cell(row, 3, "—", COLORS["text_muted"])
                self.table.set_cell(row, 4, "—", COLORS["text_muted"])

            actions = [
                {
                    "text": "📊 كشف الحساب",
                    "callback": lambda _, cid=c["id"]: self._open_statement(cid),
                    "role": "statement",
                },
                {
                    "text": "المزيد",
                    "callback": lambda _, cid=c["id"]: self._open_more(cid),
                    "role": "secondary",
                },
            ]
            self.table.add_action_buttons(row, 5, actions, spacing=6)

        parts = [f"إجمالي: {len(customers)} عميل"]
        if total_owed:
            parts.append(f"عليهم: {fmt_currency(total_owed)}")
        if total_due:
            parts.append(f"لهم: {fmt_currency(total_due)}")
        self.total_lbl.setText("  ·  ".join(parts))

        # Update table height to fit all rows (Full-Page Scroll)
        self.table.setMinimumHeight(
            self.table.verticalHeader().length()
            + self.table.horizontalHeader().height()
            + 2
        )

    def _add_customer(self):
        if CustomerDialog(self).exec():
            self.load_data()

    def _open_statement(self, cid: int):
        from ui.screens.statement_screen import CustomerStatementDialog
        CustomerStatementDialog(cid, self).exec()

    def _open_more(self, cid: int):
        from ui.screens.customer_info_dialog import CustomerInfoDialog
        customer = db.get_customer_by_id(cid)
        if customer:
            CustomerInfoDialog(customer, self).exec()

    def _ctx_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row >= len(self._customers):
            return
        c = self._customers[row]
        menu = QMenu(self)
        menu.addAction(
            QAction("📊  كشف حساب", self, triggered=lambda: self._open_statement(c["id"]))
        )
        menu.addAction(QAction("ℹ️  المزيد", self, triggered=lambda: self._open_more(c["id"])))
        menu.addAction(QAction("✏️  تعديل", self, triggered=lambda: self._edit(c)))
        menu.addSeparator()
        menu.addAction(QAction("🗑️  حذف", self, triggered=lambda: self._delete(c)))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _edit(self, c: dict):
        full = db.get_customer_by_id(c["id"])
        if CustomerDialog(self, full).exec():
            self.load_data()

    def _delete(self, c: dict):
        debt = c.get("total_debt", 0)
        msg = f"هل تريد حذف العميل [{c['name']}]؟"
        if debt and debt > 0:
            msg += f"\n⚠️  لديه مديونية {fmt_currency(debt)}"
        if (
            QMessageBox.question(
                self,
                "تأكيد الحذف",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            db.delete_customer(c["id"])
            self.load_data()


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
        layout.setContentsMargins(0, GAP_XS, 0, 0)
        layout.setSpacing(GAP_MD)

        # ── Middle Layer: Add & Search
        tb_row = QHBoxLayout()
        tb_row.setContentsMargins(0, 0, 0, 0)
        tb_row.setSpacing(GAP_MD)

        add_btn = QPushButton("➕ إضافة مجموعة")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(42)
        add_btn.setMinimumWidth(180)
        add_btn.clicked.connect(self._add_group)
        tb_row.addWidget(add_btn)

        tb_row.addStretch()

        self.group_search = QLineEdit()
        self.group_search.setPlaceholderText("🔍  بحث باسم المجموعة...")
        self.group_search.setFixedHeight(42)
        self.group_search.setMinimumWidth(320)
        self.group_search.textChanged.connect(self._filter)
        tb_row.addWidget(self.group_search)

        layout.addLayout(tb_row)
        layout.addSpacing(GAP_SM)

        cols = [
            ("اسم المجموعة", -1),  # Stretch
            ("القائد", 180),
            ("ملاحظات", 200),
            ("إجراءات", 310),
        ]
        self.table = DataTable(cols)
        self.table.horizontalHeader().setVisible(True)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx_menu)

        # Full page scroll logic
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        layout.addWidget(self.table)

    def load_data(self):
        self._all_groups = db.get_all_groups()
        self._groups = list(self._all_groups)
        self._render()

    def _filter(self, text: str):
        if not self._all_groups:
            return
        q = text.strip().lower()
        self._groups = (
            [g for g in self._all_groups if q in g["name"].lower()]
            if q
            else list(self._all_groups)
        )
        self._render()

    def _render(self):
        self.table.clear_rows()
        self.table.setRowCount(len(self._groups))

        for row, g in enumerate(self._groups):
            self.table.set_cell(row, 0, g["name"], bold=True)
            self.table.set_cell(
                row, 1, g.get("leader_name") or "—", COLORS["text_secondary"]
            )
            self.table.set_cell(row, 2, g.get("notes") or "—", COLORS["text_muted"])

            self.table.add_action_buttons(
                row,
                3,
                [
                    {
                        "text": "✏️ تعديل",
                        "callback": lambda _, g=g: self._edit_group(g),
                        "role": "secondary",
                    },
                    {
                        "text": "📊 تقرير",
                        "callback": lambda _, gid=g["id"]: self._show_report(gid),
                        "role": "statement",
                    },
                    {
                        "text": "🖨️ طباعة",
                        "callback": lambda _, gid=g["id"], gname=g["name"]: self._print_group_report(gid, gname),
                        "role": "secondary",
                    },
                ],
            )

        # Update table height to fit all rows (Full-Page Scroll)
        self.table.setMinimumHeight(
            self.table.verticalHeader().length()
            + self.table.horizontalHeader().height()
            + 2
        )

    def _add_group(self):
        if GroupDialog(self).exec():
            self.load_data()

    def _edit_group(self, g: dict):
        if GroupDialog(self, g).exec():
            self.load_data()

    def _show_report(self, gid: int):
        from ui.screens.statement_screen import GroupReportDialog

        GroupReportDialog(gid, self).exec()

    def _print_group_report(self, gid: int, group_name: str):
        import os
        try:
            data = db.get_group_summary(gid)
            if not data:
                QMessageBox.warning(self, "تنبيه", "لم يتم العثور على بيانات المجموعة")
                return
            from ui.utils.pdf_generator import GroupPDFGenerator
            path = GroupPDFGenerator(data).generate()
            os.startfile(path)
        except Exception as e:
            QMessageBox.critical(self, "خطأ في توليد PDF", str(e))

    def _ctx_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row >= len(self._groups):
            return
        g = self._groups[row]
        menu = QMenu(self)
        menu.addAction(
            QAction("📊  تقرير", self, triggered=lambda: self._show_report(g["id"]))
        )
        menu.addAction(
            QAction("🖨️  طباعة PDF", self,
                    triggered=lambda: self._print_group_report(g["id"], g["name"]))
        )
        menu.addAction(
            QAction("✏️  تعديل", self, triggered=lambda: self._edit_group(g))
        )
        menu.addSeparator()
        menu.addAction(QAction("🗑️  حذف", self, triggered=lambda: self._delete(g)))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _delete(self, g: dict):
        if (
            QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل تريد حذف المجموعة [{g['name']}]؟\nالعملاء سيبقون بدون مجموعة.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            db.delete_group(g["id"])
            self.load_data()


# ══════════════════════════════════════════════════════
#  CustomerDialog
# ══════════════════════════════════════════════════════


class CustomerDialog(BaseDialog):

    def __init__(self, parent=None, customer: dict = None):
        title = "تعديل عميل" if customer else "➕ إضافة عميل جديد"
        super().__init__(title, parent)
        self.customer = customer
        self.setMinimumWidth(700)
        self._existing_codes: list[dict] = []   # {"id", "code"} loaded from DB
        self._pending_new: list[str] = []        # codes to add on save
        self._pending_del: list[int] = []        # code IDs to delete on save
        self._build_form()
        if customer:
            self._fill()

    def _build_form(self):
        form = QFormLayout()
        form.setSpacing(GAP_MD)
        form.setLabelAlignment(ALeft)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العميل *")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم التليفون")

        self.group_combo = QComboBox()
        self.group_combo.addItem("بدون مجموعة", None)
        for g in db.get_all_groups():
            self.group_combo.addItem(g["name"], g["id"])

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(72)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")

        form.addRow("الاسم *:", self.name_input)
        form.addRow("التليفون:", self.phone_input)
        form.addRow("المجموعة:", self.group_combo)
        form.addRow("ملاحظات:", self.notes_input)

        self.body.addLayout(form)

        # ── Shipping Codes Section ──────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{COLORS['border']}; margin-top:4px;")
        self.body.addWidget(sep)

        codes_hdr = QHBoxLayout()
        codes_title = QLabel("🔑 كودات الشحن")
        codes_title.setStyleSheet(
            f"font-weight:bold; color:{COLORS['text_primary']}; font-size:{FONT['md']};"
        )
        codes_hdr.addWidget(codes_title)
        codes_hdr.addStretch()
        self.body.addLayout(codes_hdr)

        # Dynamic list of code chips
        self._codes_vbox = QVBoxLayout()
        self._codes_vbox.setSpacing(4)
        self.body.addLayout(self._codes_vbox)

        # Add-code row
        add_row = QHBoxLayout()
        add_row.setSpacing(GAP_SM)
        self._new_code_input = QLineEdit()
        self._new_code_input.setPlaceholderText("أدخل كود جديد ثم اضغط ➕ ...")
        self._new_code_input.setFixedHeight(36)
        self._new_code_input.returnPressed.connect(self._add_pending_code)
        add_row.addWidget(self._new_code_input, 1)

        add_code_btn = QPushButton("➕ إضافة")
        add_code_btn.setObjectName("btn_secondary")
        add_code_btn.setFixedHeight(36)
        add_code_btn.setFixedWidth(90)
        add_code_btn.clicked.connect(self._add_pending_code)
        add_row.addWidget(add_code_btn)
        self.body.addLayout(add_row)

        # Footer
        self.add_stretch()
        self.add_button("إلغاء", self.reject, role="secondary")
        self.add_button("حفظ ✓", self._save, role="primary")

        self._render_codes()

    # ── code chip helpers ───────────────────────────────────────

    def _render_codes(self):
        while self._codes_vbox.count():
            item = self._codes_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        shown = [c for c in self._existing_codes if c["id"] not in self._pending_del]
        all_items = [(c["code"], c["id"], False) for c in shown] + \
                    [(code, None, True) for code in self._pending_new]

        if not all_items:
            empty = QLabel("لا توجد كودات مضافة")
            empty.setStyleSheet(f"color:{COLORS['text_muted']}; padding:4px 2px; font-size:{FONT['xs']};")
            self._codes_vbox.addWidget(empty)
            return

        for code_text, code_id, is_new in all_items:
            chip = self._make_chip(code_text, code_id, is_new)
            self._codes_vbox.addWidget(chip)

    def _make_chip(self, code_text: str, code_id: int | None, is_new: bool) -> QWidget:
        chip = QWidget()
        chip.setFixedHeight(32)
        chip.setStyleSheet(
            f"background:{COLORS['bg_hover']}; border:1px solid {COLORS['border']};"
            f"border-radius:6px;"
        )
        row = QHBoxLayout(chip)
        row.setContentsMargins(10, 0, 6, 0)
        row.setSpacing(6)

        icon_color = COLORS["yellow"] if is_new else COLORS["accent"]
        lbl = QLabel(f"🔑  {code_text}")
        lbl.setStyleSheet(f"color:{icon_color}; font-weight:bold; font-size:{FONT['sm']};")
        row.addWidget(lbl)

        if is_new:
            badge = QLabel("جديد")
            badge.setStyleSheet(
                f"color:{COLORS['yellow']}; font-size:{FONT['xs']};"
                f"background:{COLORS['yellow_bg']}; border-radius:4px; padding:1px 6px;"
            )
            row.addWidget(badge)

        row.addStretch()

        del_btn = QPushButton("✕")
        del_btn.setObjectName("btn_danger")
        del_btn.setFixedSize(24, 24)
        if is_new:
            del_btn.clicked.connect(lambda _, c=code_text: self._remove_pending(c))
        else:
            del_btn.clicked.connect(lambda _, cid=code_id: self._mark_delete(cid))
        row.addWidget(del_btn)
        return chip

    def _add_pending_code(self):
        code = self._new_code_input.text().strip()
        if not code:
            return
        existing_codes = {c["code"].lower() for c in self._existing_codes
                          if c["id"] not in self._pending_del}
        if code.lower() in existing_codes or code.lower() in [c.lower() for c in self._pending_new]:
            QMessageBox.warning(self, "تنبيه", f"الكود '{code}' موجود بالفعل")
            return
        self._pending_new.append(code)
        self._new_code_input.clear()
        self._render_codes()

    def _remove_pending(self, code: str):
        self._pending_new = [c for c in self._pending_new if c != code]
        self._render_codes()

    def _mark_delete(self, code_id: int):
        self._pending_del.append(code_id)
        self._render_codes()

    # ── fill / save ─────────────────────────────────────────────

    def _fill(self):
        self.name_input.setText(self.customer.get("name", ""))
        self.phone_input.setText(self.customer.get("phone", ""))
        self.notes_input.setPlainText(self.customer.get("notes", ""))
        gid = self.customer.get("group_id")
        if gid:
            idx = self.group_combo.findData(gid)
            if idx >= 0:
                self.group_combo.setCurrentIndex(idx)
        self._existing_codes = db.get_shipping_codes(self.customer["id"])
        self._render_codes()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم العميل مطلوب")
            return
        try:
            phone = self.phone_input.text().strip()
            gid = self.group_combo.currentData()
            notes = self.notes_input.toPlainText().strip()

            if self.customer:
                db.update_customer(self.customer["id"], name, phone, gid, notes)
                cid = self.customer["id"]
            else:
                cid = db.add_customer(name, phone, gid, notes)

            for code_id in self._pending_del:
                try:
                    db.delete_shipping_code(code_id)
                except Exception:
                    pass

            code_errors = []
            for code in self._pending_new:
                try:
                    db.add_shipping_code(cid, code)
                except ValueError as e:
                    code_errors.append(str(e))

            if code_errors:
                QMessageBox.warning(self, "تعارض في الكودات", "\n".join(code_errors))
                # Reload so user sees what actually got saved
                self._existing_codes = db.get_shipping_codes(cid)
                self._pending_new = []
                self._pending_del = []
                self._render_codes()
                return

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════════════════
#  GroupDialog
# ══════════════════════════════════════════════════════


class GroupDialog(BaseDialog):

    def __init__(self, parent=None, group: dict = None):
        title = "تعديل مجموعة" if group else "➕ إضافة مجموعة جديدة"
        super().__init__(title, parent)
        self.group = group
        self.setMinimumWidth(400)
        self._build_form()
        if group:
            self._fill()

    def _build_form(self):
        form = QFormLayout()
        form.setSpacing(GAP_MD)
        form.setLabelAlignment(ALeft)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المجموعة *")

        self.leader_combo = QComboBox()
        self.leader_combo.addItem("بدون قائد", None)
        for c in db.get_all_customers():
            self.leader_combo.addItem(c["name"], c["id"])

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")

        form.addRow("الاسم *:", self.name_input)
        form.addRow("القائد:", self.leader_combo)
        form.addRow("ملاحظات:", self.notes_input)

        self.body.addLayout(form)

        # Footer buttons
        self.add_stretch()
        self.add_button("إلغاء", self.reject, role="secondary")
        self.add_button("حفظ ✓", self._save, role="primary")

    def _fill(self):
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
            lid = self.leader_combo.currentData()
            notes = self.notes_input.toPlainText().strip()
            if self.group:
                db.update_group(self.group["id"], name, lid, notes)
            else:
                db.add_group(name, lid, notes)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


