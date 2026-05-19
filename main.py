"""
main.py — نقطة البداية
"""

import os
import sys

# إضافة مسار المشروع لـ Python path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from database.schema import initialize_database
from ui.main_window import MainWindow


def main():
    # تهيئة DB
    initialize_database()

    # تشغيل التطبيق
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setApplicationName("نظام إدارة المدفوعات")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
# C:\Users\Mustafa\POSSystem
# rmdir /s /q build
# rmdir /s /q dist
# del *.spec