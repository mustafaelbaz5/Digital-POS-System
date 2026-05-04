"""
platforms_screen.py — شاشة إدارة المنصات (Daily Financial Closing Model)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import database as db
from ui.components.widgets import BaseDialog, DataTable, SingleDateWidget, ScreenShell
from ui.styles.theme import COLORS, GAP_LG, GAP_MD, GAP_SM
from utils.formatters import fmt_currency


# ══════════════════════════════════════════
#  Platform More Dialog
# ══════════════════════════════════════════

class PlatformMoreDialog(BaseDialog):
    """نافذة المزيد — رؤية يومية مالية للمنصة"""

    refreshed = pyqtSignal()

    def __init__(self, platform: dict, date_str: str, parent=None):
        super().__init__(f"📊 المزيد — {platform['name']}", parent)
        self.platform = platform
        self.date_str = date_str
        self.setFixedSize(750, 700)
        self.setModal(False)
        self._setup_scroll()
        self._build_content()

    def _setup_scroll(self):
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.container)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(GAP_MD)

        scroll.setWidget(self.container)
        self.body.addWidget(scroll)

    def _build_content(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        p     = self.platform
        pid   = p["id"]
        d     = self.date_str
        p_type = p["type"]

        stats    = db.get_platform_day_stats(pid, d)
        opening  = db.get_opening_balance(pid, d)
        closing  = db.get_closing_balance(pid, d)
        after_ops = (
            opening
            + stats["total_deposits"]
            + stats["total_inbound"]
            - stats["total_outbound"]
        )

        # ── Date badge
        from datetime import datetime
        dt = datetime.strptime(d, "%Y-%m-%d")
        date_frame = QFrame()
        date_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_elevated']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 6px;
            }}
        """)
        dl = QHBoxLayout(date_frame)
        dl.setContentsMargins(12, 6, 12, 6)
        day_lbl = QLabel(dt.strftime("%d"))
        day_lbl.setStyleSheet(
            f"color:{COLORS['accent']}; font-size:22px; font-weight:bold; "
            f"background:transparent; border:none;"
        )
        my_lbl = QLabel(dt.strftime("%m / %Y"))
        my_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:11px; "
            f"background:transparent; border:none;"
        )
        dl.addWidget(day_lbl)
        dl.addWidget(my_lbl)
        dl.addStretch()
        self.scroll_layout.addWidget(date_frame)

        # ── Financial summary card
        info = QFrame()
        info.setObjectName("card")
        il = QVBoxLayout(info)
        il.setContentsMargins(18, 14, 18, 14)
        il.setSpacing(8)

        def _row(label, value, color=COLORS["text_primary"], bold=False, is_currency=True):
            r = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color:{COLORS['text_secondary']}; font-size:14px; "
                f"background:transparent; border:none;"
            )
            r.addWidget(lbl)
            r.addStretch()
            val_str = fmt_currency(value) if is_currency else str(value)
            val = QLabel(val_str)
            val.setStyleSheet(
                f"color:{color}; font-size:15px; "
                f"font-weight:{'bold' if bold else 'normal'}; "
                f"background:transparent; border:none;"
            )
            r.addWidget(val)
            il.addLayout(r)

        def _sep():
            s = QFrame()
            s.setFixedHeight(1)
            s.setStyleSheet(f"background:{COLORS['border']};")
            il.addWidget(s)

        _row("📂 رصيد البداية",              opening,                  COLORS["blue"],   True)
        _row("📊 عدد العمليات",              stats["txn_count"],       is_currency=False)
        _row("📤 إجمالي المصروف",            stats["total_outbound"],  COLORS["red"])
        _row("📥 إجمالي الوارد",             stats["total_inbound"],   COLORS["green"])
        _row("💰 إيداعات",                  stats["total_deposits"],   COLORS["purple"])
        _sep()
        _row("⚙️ الرصيد بعد العمليات",      after_ops,                COLORS["yellow"], True)
        _row("📊 إجمالي العمولات",           stats["total_commission"], COLORS["cyan"])
        _sep()
        _row("🏁 الرصيد النهائي",            closing,                  COLORS["accent"], True)
        self.scroll_layout.addWidget(info)

        # ── Commission (machines only)
        if p_type == "machine":
            cf = QFrame()
            cf.setObjectName("card")
            cl = QVBoxLayout(cf)
            cl.setContentsMargins(18, 14, 18, 14)
            cl.setSpacing(8)

            has_comm = stats["total_commission"] > 0

            t_lbl = QLabel("💵 تسجيل عمولة يدوية")
            t_lbl.setStyleSheet(
                f"background:transparent; border:none; "
                f"color:{COLORS['text_primary']};"
            )
            cl.addWidget(t_lbl)

            if has_comm:
                msg = QLabel("📌 تم إضافة عمولة هذا اليوم بالفعل")
                msg.setStyleSheet(
                    f"color:{COLORS['yellow']}; font-weight:bold; "
                    f"background:transparent; border:none;"
                )
                cl.addWidget(msg)

            cr = QHBoxLayout()
            self.comm_input = QDoubleSpinBox()
            self.comm_input.setRange(0, 999999)
            self.comm_input.setDecimals(2)
            self.comm_input.setSuffix("  ج")
            self.comm_input.setMinimumHeight(36)
            cr.addWidget(self.comm_input, 2)

            cb = QPushButton("✓ تسجيل")
            cb.setObjectName("btn_primary")
            cb.setMinimumHeight(36)
            cb.clicked.connect(self._save_commission)
            cr.addWidget(cb, 1)

            if has_comm:
                self.comm_input.setEnabled(False)
                cb.setEnabled(False)

            cl.addLayout(cr)
            self.scroll_layout.addWidget(cf)

        # ── Quick actions
        af = QFrame()
        af.setObjectName("card")
        al = QHBoxLayout(af)
        al.setContentsMargins(18, 10, 18, 10)
        al.setSpacing(8)

        dep = QPushButton("💰 إيداع")
        dep.setObjectName("btn_secondary")
        dep.setMinimumHeight(36)
        dep.clicked.connect(self._deposit)
        al.addWidget(dep)

        if p_type in ("wallet", "instapay"):
            lb = QPushButton("✏️ تعديل الحد")
            lb.setObjectName("btn_secondary")
            lb.setMinimumHeight(36)
            lb.clicked.connect(self._edit_limit)
            al.addWidget(lb)

        db_btn = QPushButton("🗑️ حذف")
        db_btn.setObjectName("btn_danger")
        db_btn.setMinimumHeight(36)
        db_btn.clicked.connect(self._delete)
        al.addWidget(db_btn)

        self.scroll_layout.addWidget(af)

        # ── Transactions table
        txns = db.get_platform_transactions_for_date(pid, d)
        if txns:
            lbl = QLabel(f"📋 عمليات اليوم ({len(txns)})")
            lbl.setStyleSheet(
                f"background:transparent; border:none; "
                f"color:{COLORS['text_primary']}; font-weight:bold;"
            )
            self.scroll_layout.addWidget(lbl)

            cols = [
                ("الوقت",   80),
                ("النوع",   85),
                ("الخدمة",  -1),
                ("العميل",  -1),
                ("المبلغ", 110),
                ("الحالة",  80),
            ]
            table = DataTable(cols)
            table.setRowCount(len(txns))
            table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

            op_map = {
                "outbound":          "📤 صادر",
                "inbound":           "📥 وارد",
                "manual_commission": "💵 عمولة",
            }
            for row, t in enumerate(txns):
                table.set_cell(row, 0, (t.get("created_at") or "")[-8:-3], color=COLORS["text_muted"])
                table.set_cell(row, 1, op_map.get(t.get("operation_type", ""), "—"))
                table.set_cell(row, 2, t.get("service_name") or "—")
                table.set_cell(row, 3, t.get("customer_name") or "—", color=COLORS["text_secondary"])
                table.set_cell(row, 4, fmt_currency(t.get("amount_spent", 0)), bold=True)
                st = t.get("payment_status", "")
                table.set_cell(
                    row, 5,
                    "مسدد" if st == "paid" else "مؤجل",
                    color=COLORS["green"] if st == "paid" else COLORS["yellow"],
                )

            row_h   = table.verticalHeader().defaultSectionSize()
            hdr_h   = table.horizontalHeader().height()
            total_h = hdr_h + (len(txns) * row_h) + 2
            table.setMinimumHeight(total_h)
            table.setMaximumHeight(total_h)
            self.scroll_layout.addWidget(table)

        self.scroll_layout.addStretch()

        # ── Footer
        while self.footer.count():
            item = self.footer.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.add_stretch()
        self.add_button("إغلاق", self.close, role="secondary")

    def refresh_data(self):
        self.refreshed.emit()
        new_p = db.get_platform_by_id(self.platform["id"])
        if new_p:
            self.platform = new_p
        self._build_content()

    def _save_commission(self):
        amount = self.comm_input.value()
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل مبلغ العمولة")
            return
        try:
            db.add_manual_commission(self.platform["id"], amount, self.date_str)
            self.refresh_data()
            self.comm_input.setValue(0.0)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _deposit(self):
        amount, ok = QInputDialog.getDouble(self, "إيداع", "المبلغ:", min=0.01, decimals=2)
        if ok and amount > 0:
            try:
                db.deposit_to_platform(self.platform["id"], amount)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_limit(self):
        current = self.platform.get("monthly_limit", 200000)
        amount, ok = QInputDialog.getDouble(
            self, "تعديل الحد", "الحد الشهري الجديد:", value=current, min=0, decimals=2
        )
        if ok:
            try:
                db.update_platform_limit(self.platform["id"], amount)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _delete(self):
        if (
            QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل تريد حذف [{self.platform['name']}]؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            db.delete_platform(self.platform["id"])
            self.refreshed.emit()
            self.close()


# ══════════════════════════════════════════
#  Platform List Tab
# ══════════════════════════════════════════

class PlatformListTab(QWidget):
    refreshed = pyqtSignal()

    def __init__(self, p_type: str, parent=None):
        super().__init__(parent)
        self.p_type = p_type
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._sort_mode = "default"
        self._sort_btns = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, GAP_MD, 0, 0)
        layout.setSpacing(GAP_MD)

        # ── Sort toolbar
        sb = QHBoxLayout()
        sb.setSpacing(GAP_SM)
        sb.setAlignment(Qt.AlignmentFlag.AlignLeft)

        sort_lbl = QLabel("ترتيب:")
        sort_lbl.setStyleSheet(f"color:{COLORS['text_muted']};font-size:12px;")
        sb.addWidget(sort_lbl)

        for mode, label in [("default", "الافتراضي"), ("balance_asc", "الرصيد ↑"), ("balance_desc", "الرصيد ↓")]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda _, m=mode: self._set_sort(m))
            self._sort_btns[mode] = btn
            sb.addWidget(btn)

        if self.p_type in ("wallet", "instapay"):
            for mode, label in [("limit_asc", "الحد المتبقي ↑"), ("limit_desc", "الحد المتبقي ↓")]:
                btn = QPushButton(label)
                btn.setFixedHeight(28)
                btn.clicked.connect(lambda _, m=mode: self._set_sort(m))
                self._sort_btns[mode] = btn
                sb.addWidget(btn)

        sb.addStretch()
        layout.addLayout(sb)
        self._apply_sort_styles()

        # ── Table
        cols = [
            ("اسم المنصة", -1),      # Name stretches
            ("الرصيد الحالي", 180),
            ("العمليات", 100),
            ("إجراءات", 200),        # Increased to fit buttons + 24px spacing
        ]
        if self.p_type in ("wallet", "instapay"):
            cols.insert(1, ("المتبقي من الحد", 190))

        self.table = DataTable(cols)
        self.table.setSortingEnabled(True)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addWidget(self.table)

    def _set_sort(self, mode: str):
        self._sort_mode = mode
        self._apply_sort_styles()
        if hasattr(self, "_platforms_data"):
            self.load(self._platforms_data)

    def _apply_sort_styles(self):
        for mode, btn in self._sort_btns.items():
            active = mode == self._sort_mode
            btn.setStyleSheet(
                f"background:{COLORS['blue_bg']};color:{COLORS['blue']};"
                f"border:1px solid {COLORS['blue']};border-radius:5px;"
                f"font-size:12px;padding:2px 8px;"
                if active else
                f"background:{COLORS['bg_input']};color:{COLORS['text_muted']};"
                f"border:1px solid {COLORS['border']};border-radius:5px;"
                f"font-size:12px;padding:2px 8px;"
            )

    def _sorted(self, platforms: list) -> list:
        if self._sort_mode == "balance_desc":
            return sorted(platforms, key=lambda p: p.get("balance", 0), reverse=True)
        if self._sort_mode == "balance_asc":
            return sorted(platforms, key=lambda p: p.get("balance", 0))
        if self._sort_mode == "limit_desc":
            return sorted(platforms, key=lambda p: p.get("monthly_limit", 0) - p.get("monthly_used", 0), reverse=True)
        if self._sort_mode == "limit_asc":
            return sorted(platforms, key=lambda p: p.get("monthly_limit", 0) - p.get("monthly_used", 0))
        return platforms

    def load(self, platforms: list):
        self._platforms_data = platforms
        platforms = self._sorted(platforms)

        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)

        for p in platforms:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.set_cell(row, 0, p["name"], bold=True)

            col = 1
            if self.p_type in ("wallet", "instapay"):
                rem = p.get("monthly_limit", 0) - p.get("monthly_used", 0)
                pct = int(p.get("monthly_used", 0) / max(p.get("monthly_limit", 1), 1) * 100)
                color = COLORS["red"] if pct > 90 else COLORS["yellow"] if pct > 70 else COLORS["blue"]
                self.table.set_cell(row, col, f"{fmt_currency(rem)} ({pct}%)", color=color)
                col += 1

            self.table.set_cell(row, col, fmt_currency(p.get("balance", 0)), color=COLORS["green"], bold=True)
            col += 1
            self.table.set_cell(row, col, str(p.get("transaction_count", 0)))
            col += 1

            self.table.add_action_buttons(row, col, [
                {"text": "اضافة  عملية", "callback": lambda _, pid=p["id"]: self._open_transaction_form(pid), "role": "primary"},
                {"text": " المزيد", "callback": lambda _, pid=p["id"]: self._open_more(pid), "role": "statement"},
            ])

        self.table.setSortingEnabled(True)
        self.table.setMinimumHeight(
            self.table.verticalHeader().length() + self.table.horizontalHeader().height() + 2
        )

    def _get_date(self) -> str:
        parent = self.parent()
        while parent:
            if hasattr(parent, "get_selected_date"):
                return parent.get_selected_date()
            parent = parent.parent()
        from datetime import date
        return date.today().isoformat()

    def _open_transaction_form(self, platform_id: int):
        from ui.screens.transaction_form import TransactionDialog
        TransactionDialog(platform_id=platform_id, selected_date=self._get_date(), parent=self).exec()
        self.refreshed.emit()

    def _open_more(self, platform_id: int):
        platform = db.get_platform_by_id(platform_id)
        if not platform:
            return
        if not hasattr(self, "_more_dialogs"):
            self._more_dialogs = {}
        if platform_id in self._more_dialogs:
            dlg = self._more_dialogs[platform_id]
            dlg.raise_()
            dlg.activateWindow()
            return
        dialog = PlatformMoreDialog(platform, self._get_date(), self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.destroyed.connect(lambda: self._more_dialogs.pop(platform_id, None))
        dialog.refreshed.connect(self.refreshed.emit)
        self._more_dialogs[platform_id] = dialog
        dialog.show()


# ══════════════════════════════════════════
#  Platforms Screen
# ══════════════════════════════════════════

class PlatformsScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__("المنصات", "الماكينات والمحافظ الإلكترونية")
        self._build_content()

    def get_selected_date(self) -> str:
        return self._date_widget.get_date()

    def _build_content(self):
        self._date_widget = SingleDateWidget()
        self._date_widget.changed.connect(self.refresh)
        self.add_action(self._date_widget)

        add_btn = QPushButton("＋  إضافة منصة")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_platform)
        self.add_action(add_btn)

        c = self.content()
        c.setContentsMargins(0, GAP_MD, 0, 0)
        c.setSpacing(GAP_LG)

        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._tab_machines  = PlatformListTab("machine")
        self._tab_wallets   = PlatformListTab("wallet")
        self._tab_instapay  = PlatformListTab("instapay")

        for tab in [self._tab_machines, self._tab_wallets, self._tab_instapay]:
            tab.refreshed.connect(self.refresh)

        self.tabs.addTab(self._tab_machines,  "🏧  الماكينات")
        self.tabs.addTab(self._tab_wallets,   "💳  المحافظ")
        self.tabs.addTab(self._tab_instapay,  "🔷  انستا باي")

        c.addWidget(self.tabs)

    def refresh(self):
        platforms = db.get_all_platforms()
        date_str = self.get_selected_date()
        for p in platforms:
            # We keep the real balance from p["balance"] as requested
            p["transaction_count"] = db.get_platform_day_stats(p["id"], date_str)["txn_count"]

        self._tab_machines.load( [p for p in platforms if p["type"] == "machine"])
        self._tab_wallets.load(  [p for p in platforms if p["type"] == "wallet"])
        self._tab_instapay.load( [p for p in platforms if p["type"] == "instapay"])

    def _add_platform(self):
        if AddPlatformDialog(self).exec():
            self.refresh()


# ══════════════════════════════════════════
#  Add Platform Dialog
# ══════════════════════════════════════════

class AddPlatformDialog(BaseDialog):

    def __init__(self, parent=None):
        super().__init__("➕ إضافة منصة جديدة", parent)
        self.setMinimumWidth(440)
        self._build_form()

    def _build_form(self):
        form = QFormLayout()
        form.setSpacing(GAP_MD)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: فوري، أمان، فودافون كاش")
        form.addRow("اسم المنصة *:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItem("🏧  ماكينة",            "machine")
        self.type_combo.addItem("💳  محفظة إلكترونية",  "wallet")
        self.type_combo.addItem("🔷  انستا باي",          "instapay")
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("النوع:", self.type_combo)

        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(0, 10_000_000)
        self.balance_input.setDecimals(2)
        self.balance_input.setSuffix("  ج")
        form.addRow("الرصيد الابتدائي:", self.balance_input)

        self._limit_label = QLabel("الحد الشهري:")
        self.limit_input  = QDoubleSpinBox()
        self.limit_input.setRange(0, 10_000_000)
        self.limit_input.setDecimals(2)
        self.limit_input.setSuffix("  ج")
        self.limit_input.setValue(200000)
        form.addRow(self._limit_label, self.limit_input)

        self.body.addLayout(form)
        self.add_stretch()
        self.add_button("إلغاء",     self.reject, role="secondary")
        self.add_button("إضافة ✓",  self._save,  role="primary")
        self._on_type_changed(0)

    def _on_type_changed(self, _):
        p_type = self.type_combo.currentData()
        if p_type == "machine":
            self.limit_input.setEnabled(False)
            self.limit_input.setValue(0)
            self._limit_label.setStyleSheet(f"color:{COLORS['text_muted']};")
        elif p_type == "instapay":
            self.limit_input.setEnabled(True)
            self.limit_input.setValue(400000)
            self._limit_label.setStyleSheet("")
        else:
            self.limit_input.setEnabled(True)
            self.limit_input.setValue(200000)
            self._limit_label.setStyleSheet("")

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "اسم المنصة مطلوب")
            return
        try:
            db.add_platform(
                name,
                self.type_combo.currentData(),
                self.balance_input.value(),
                self.limit_input.value(),
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))