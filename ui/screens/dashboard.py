"""
dashboard.py — لوحة التحكم الرئيسية (Pro Dark Edition)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QInputDialog, QMessageBox,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressDialog, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from datetime import datetime

from ui.styles.theme import (
    COLORS, FONT, CARD_RADIUS, BORDER_RADIUS, ROW_HEIGHT,
    GAP_XS, GAP_SM, GAP_MD, GAP_LG, GAP_XL, MARGIN_CONTENT
)
from ui.components.widgets import StatCard, SectionTitle, ScreenShell, CardGroup, make_divider
from utils.formatters import fmt_currency, fmt_datetime

import database as db


class DashboardScreen(ScreenShell):

    def __init__(self, parent=None):
        super().__init__("لوحة التحكم", self._today_str())
        self._build_content()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(30_000)

    @staticmethod
    def _today_str() -> str:
        days_ar = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        now = datetime.now()
        return f"{days_ar[now.weekday()]}  ·  {now.strftime('%Y-%m-%d')}"

    def _build_content(self):
        c = self.content()
        c.setSpacing(GAP_LG)

        # ── Section 1: Stat Cards
        stats_group = CardGroup("📊  نظرة عامة على الأموال")
        stats_group.add_layout(self._make_stats_grid())
        c.addWidget(stats_group)

        # ── Section 2: Recent Transactions
        ops_group = CardGroup("🕒  آخر العمليات")
        self._ops_table = self._make_ops_table()
        ops_group.add_widget(self._ops_table)
        c.addWidget(ops_group)

        # ── Section 3: Quick Actions
        actions_group = CardGroup("⚡  الإجراءات السريعة")
        actions_group.add_widget(self._make_actions_panel())
        c.addWidget(actions_group)

        c.addSpacing(GAP_MD)
        c.addStretch()

    def _make_stats_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(GAP_MD)
        grid.setContentsMargins(0, 0, 0, 0)

        self.card_budget   = StatCard("رأس المال",       accent_color=COLORS["text_secondary"])
        self.card_assets   = StatCard("إجمالي الأصول",    accent_color=COLORS["cyan"])
        self.card_cash     = StatCard("الخزينة النقدية",  accent_color=COLORS["green"])
        self.card_wallets  = StatCard("إجمالي المحافظ",    accent_color=COLORS["purple"])
        self.card_machines = StatCard("إجمالي الماكينات",   accent_color=COLORS["blue"])
        self.card_pending  = StatCard("إجمالي المؤجل",     accent_color=COLORS["red"])
        self.card_today    = StatCard("أرباح اليوم",       accent_color=COLORS["accent"])
        self.card_month    = StatCard("أرباح الشهر",       accent_color=COLORS["accent_hover"])
        self.card_ops      = StatCard("عمليات اليوم",      accent_color=COLORS["blue"])

        placement = [
            (self.card_budget, 0, 0), (self.card_assets, 0, 1), (self.card_cash, 0, 2),
            (self.card_wallets, 1, 0), (self.card_machines, 1, 1), (self.card_pending, 1, 2),
            (self.card_today, 2, 0),  (self.card_month, 2, 1),  (self.card_ops, 2, 2),
        ]
        for card, r, col in placement:
            grid.addWidget(card, r, col)
        return grid

    def _make_ops_table(self) -> QTableWidget:
        columns = ["التاريخ", "المرجع", "العميل", "الخدمة", "المنصة", "المطلوب", "المصروف", "الربح", "الحالة"]
        tbl = QTableWidget()
        tbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        tbl.setColumnCount(len(columns))
        tbl.setHorizontalHeaderLabels(columns)
        tbl.setMaximumHeight(350)
        tbl.setMinimumHeight(250)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        header = tbl.horizontalHeader()
        widths = [140, 90, -1, 130, 130, -1, 120, 120, -1]
        for i, w in enumerate(widths):
            if w == -1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                tbl.setColumnWidth(i, w)
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        tbl.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        return tbl

    def _fill_ops_table(self):
        txns = db.get_transactions(limit=15)
        self._ops_table.setRowCount(len(txns))
        
        for row, t in enumerate(txns):
            def cell(col, text, color=None, bold=False):
                item = QTableWidgetItem(str(text) if text else "—")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                if color: item.setForeground(QColor(color))
                if bold:  f = item.font(); f.setBold(True); item.setFont(f)
                self._ops_table.setItem(row, col, item)

            raw_date = t.get("created_at") or ""
            cell(0, raw_date[:16].replace("T", " "), color=COLORS["text_secondary"])
            
            # المرجع: يفضل رقم العملية إذا لم يوجد مرجع يدوي
            ref = t.get("reference_no") or f"#{t.get('id')}"
            cell(1, ref, color=COLORS["text_muted"])
            
            cell(2, t.get("customer_name") or "—", bold=True)
            cell(3, t.get("service_name") or "—")
            cell(4, t.get("platform_name") or "—", color=COLORS["text_secondary"])
            cell(5, fmt_currency(t.get("amount_required", 0) or 0), bold=True)
            cell(6, fmt_currency(t.get("amount_spent", 0) or 0), color=COLORS["text_secondary"])
            
            profit = t.get("profit", 0) or 0
            cell(7, fmt_currency(profit), color=COLORS["accent"] if profit >= 0 else COLORS["red"])
            
            st = t.get("payment_status", "")
            st_text = {"cash": "نقدي ", "pending": "مؤجل ⏳", "paid": "مسدد ✓"}.get(st, st)
            st_color = {"cash": COLORS["green"], "pending": COLORS["yellow"], "paid": COLORS["text_secondary"]}.get(st)
            cell(8, st_text, color=st_color, bold=True)

    def _make_actions_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        row = QHBoxLayout(frame)
        row.setContentsMargins(24, 20, 24, 20)
        row.setSpacing(16)

        actions = [
            ("⊕  إضافة عملية",           "btn_primary",   self._go_to_transaction),
            ("👤  إضافة عميل",           "btn_secondary", self._add_customer),
            ("💵  تعديل الكاش (الخزينة)", "btn_secondary", self._edit_cash),
        ]

        for label, obj, slot in actions:
            btn = QPushButton(label)
            btn.setObjectName(obj)
            btn.setMinimumHeight(48)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            row.addWidget(btn)

        self._btn_export = QPushButton("☁️  تصدير البيانات")
        self._btn_export.setObjectName("btn_secondary")
        self._btn_export.setMinimumHeight(48)
        self._btn_export.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_export.clicked.connect(self._export_to_sheets)
        row.addWidget(self._btn_export)

        return frame

    def refresh(self):
        stats = db.get_dashboard_stats()
        self.card_budget.set_value(fmt_currency(stats["main_budget"]))
        self.card_assets.set_value(fmt_currency(stats["total_assets"]))
        self.card_cash.set_value(fmt_currency(stats["cash_vault"]))
        self.card_wallets.set_value(fmt_currency(stats["total_wallets"]))
        self.card_machines.set_value(fmt_currency(stats["total_machines"]))
        self.card_pending.set_value(fmt_currency(stats["total_pending"]))
        self.card_today.set_value(fmt_currency(stats["today_profit"]))
        self.card_month.set_value(fmt_currency(stats["month_profit"]))
        
        try:
            from datetime import date
            today_str = date.today().isoformat()
            all_t = db.get_transactions(limit=500)
            ops_today = sum(1 for t in all_t if (t.get("created_at") or "").startswith(today_str))
            self.card_ops.set_value(str(ops_today))
        except Exception:
            self.card_ops.set_value("—")
        
        self._fill_ops_table()

    def _go_to_transaction(self):
        win = self.window()
        if hasattr(win, "navigate_to"): win.navigate_to("transaction")

    def _go_to_reports(self):
        win = self.window()
        if hasattr(win, "navigate_to"): win.navigate_to("reports")

    def _add_customer(self):
        from ui.screens.customers_screen import CustomerDialog
        dlg = CustomerDialog(self)
        if dlg.exec():
            self.refresh()
            QMessageBox.information(self, "تم ", "تم إضافة العميل بنجاح")

    def _edit_cash(self):
        current = db.get_budget()["cash_vault"]
        amount, ok = QInputDialog.getDouble(
            self, "تعديل الكاش",
            f"أدخل المبلغ النقدي الحالي:\n(الحالي: {fmt_currency(current)})",
            value=current, min=0, decimals=2
        )
        if ok:
            try:
                db.set_cash_vault(amount)
                self.refresh()
                QMessageBox.information(self, "تم ", f"تم تحديث الكاش إلى {fmt_currency(amount)}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _export_to_sheets(self):
        self._btn_export.setEnabled(False)
        self._btn_export.setText("جاري التصدير...")
        
        # Setup Progress Dialog
        progress = QProgressDialog("جاري تصدير البيانات إلى Google Sheets...", None, 0, 0, self)
        progress.setWindowTitle("يرجى الانتظار")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)
        progress.show()
        QApplication.processEvents()

        try:
            data = db.get_export_data()
            from utils.google_sheets import export_to_sheets
            url = export_to_sheets(data)
            
            progress.close()

            msg = QMessageBox(self)
            msg.setWindowTitle("تم التصدير")
            msg.setText(f"تم تصدير البيانات بنجاح\n\nرابط الشيت:\n{url}")
            msg.setIcon(QMessageBox.Icon.Information)
            copy_btn = msg.addButton("نسخ الرابط", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("إغلاق", QMessageBox.ButtonRole.AcceptRole)
            
            msg.exec()
            if msg.clickedButton() == copy_btn:
                QApplication.clipboard().setText(url)
                QMessageBox.information(self, "تم النسخ", "تم نسخ الرابط إلى الحافظة")
        except Exception as e:
            if progress: progress.close()
            QMessageBox.critical(self, "خطأ في التصدير", str(e))
        finally:
            self._btn_export.setEnabled(True)
            self._btn_export.setText("☁️  تصدير البيانات")
