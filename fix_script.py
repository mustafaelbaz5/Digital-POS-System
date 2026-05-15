filepath = r"d:\WORK\pos_system\ui\screens\statement_screen.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_content = "".join(lines[:471])  # Up to the start of the corruption

# Now we append the correct content
correct_code = """                    else COLORS["green"] if debt < 0 else COLORS["text_muted"]
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

        # ── Status label for print feedback
        self._print_status = QLabel("")
        self._print_status.setStyleSheet(
            "background: transparent; border: none; font-size: 12px;"
        )
        self._print_status.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Footer — Print button + status + Close
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
"""

# Wait, lines[:471] ends at line 471 (0-indexed 470), which is:
# "if debt > 0"
# So the appended text must start with the next line.
with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)
    f.write(correct_code)

print("File fixed successfully!")
