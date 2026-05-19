"""
settlement_dialog.py — نافذة التسديد السريع (محرك FIFO)
"""

from PyQt6.QtCore import QLocale, Qt, QTimer
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

import database as db
from ui.components.widgets import BaseDialog
from ui.styles.theme import COLORS, FONT, GAP_MD, GAP_SM
from ui.utils.formatters import fmt_currency

RTL = Qt.LayoutDirection.RightToLeft


class _FocusSpin(QDoubleSpinBox):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        QTimer.singleShot(0, self.selectAll)


class QuickSettleDialog(BaseDialog):
    """تسديد سريع — يسدد المستحقات بترتيب FIFO ويحدّث الخزينة فوراً"""

    def __init__(self, customer: dict, parent=None):
        super().__init__("💚  تسديد سريع", parent)
        self.customer = customer
        self.setMinimumWidth(700)
        self._pending_total = self._load_pending_total()
        self._build_ui()

    # ── helpers ────────────────────────────────────────────────────────

    def _load_pending_total(self) -> float:
        """الصافي المتبقي الفعلي = SUM(amount_required − amount_paid) للعمليات المعلقة."""
        return db.get_customer_net_pending_total(self.customer["id"])

    # ── UI build ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Customer + debt summary card ─────────────────────────────
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        name_lbl = QLabel(self.customer.get("name", "—"))
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:{FONT['xl']}; "
            f"font-weight:bold; background:transparent; border:none;"
        )
        cl.addWidget(name_lbl)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{COLORS['border']}; margin:2px 0;")
        cl.addWidget(sep)

        def _stat(label: str, value: str, color: str):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color:{COLORS['text_secondary']}; font-size:{FONT['sm']}; "
                f"background:transparent; border:none;"
            )
            val = QLabel(value)
            val.setStyleSheet(
                f"color:{color}; font-size:{FONT['md']}; font-weight:bold; "
                f"background:transparent; border:none;"
            )
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            cl.addLayout(row)

        _stat("الصافي النهائي المطلوب:", fmt_currency(self._pending_total), COLORS["red"])
        _stat("الرصيد الكلي:",           fmt_currency(float(self.customer.get("total_debt") or 0)), COLORS["yellow"])

        self.body.addWidget(card)

        # ── Warning if no pending ─────────────────────────────────────
        if self._pending_total <= 0:
            warn = QLabel("✅  لا توجد مبالغ مستحقة على هذا العميل")
            warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            warn.setStyleSheet(
                f"color:{COLORS['green']}; font-size:{FONT['md']}; font-weight:bold; "
                f"padding:16px 0; background:transparent;"
            )
            self.body.addWidget(warn)
            self.add_stretch()
            self.add_button("إغلاق", self.reject, role="secondary")
            return

        # ── Amount input ──────────────────────────────────────────────
        amt_frame = QFrame()
        amt_frame.setObjectName("card")
        al = QVBoxLayout(amt_frame)
        al.setContentsMargins(20, 14, 20, 14)
        al.setSpacing(GAP_SM)

        amt_lbl = QLabel("المبلغ المدفوع:")
        amt_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:{FONT['sm']}; "
            f"font-weight:bold; background:transparent; border:none;"
        )
        al.addWidget(amt_lbl)

        self.amount_input = _FocusSpin()
        self.amount_input.setLocale(QLocale(QLocale.Language.English))
        self.amount_input.setGroupSeparatorShown(True)
        self.amount_input.setRange(0.01, self._pending_total)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(self._pending_total)
        self.amount_input.setSuffix("  ج.م")
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.amount_input.setStyleSheet(
            f"font-size:{FONT['xl']}; font-weight:bold; color:{COLORS['accent']}; "
            f"padding:8px 14px;"
        )
        self.amount_input.setMinimumHeight(50)
        al.addWidget(self.amount_input)

        # Quick-fill hint
        hint = QLabel(
            f"الصافي المتبقي الفعلي: {fmt_currency(self._pending_total)}  "
            f"(بعد خصم المبالغ المسددة جزئياً)"
        )
        hint.setStyleSheet(
            f"color:{COLORS['text_muted']}; font-size:{FONT['xs']}; "
            f"background:transparent; border:none;"
        )
        al.addWidget(hint)
        self.body.addWidget(amt_frame)

        # ── Footer ────────────────────────────────────────────────────
        self.add_stretch()
        self.add_button("إلغاء", self.reject, role="secondary")

        confirm_btn = self.add_button("✓  تأكيد التسديد", self._confirm, role="success")
        confirm_btn.setMinimumHeight(42)
        confirm_btn.setMinimumWidth(160)

        QTimer.singleShot(50, self.amount_input.setFocus)

    # ── settlement ─────────────────────────────────────────────────────

    def _confirm(self):
        amount = self.amount_input.value()
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل مبلغاً أكبر من الصفر")
            return

        try:
            result = db.settle_customer_debt(self.customer["id"], amount)

            total   = result["total_settled"]
            count   = result["settled_count"]
            partial = result["partial_settled"]

            lines = [f"تم تسديد مبلغ  {fmt_currency(total)}"]

            if count > 0:
                lines.append(f"وتحديث {count} عملية بالكامل.")
            if partial:
                lines.append("مع تسديد جزئي للعملية الأخيرة.")

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("تم التسديد ✓")
            msg_box.setText("\n".join(lines))
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.exec()

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "تنبيه", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
