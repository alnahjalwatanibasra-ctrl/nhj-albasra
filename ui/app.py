# -*- coding: utf-8 -*-
"""نقطة تشغيل التطبيق: QApplication + الثيم + RTL + الأيقونة."""
import os, sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QLocale

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(argv=None):
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    QLocale.setDefault(QLocale(QLocale.Arabic, QLocale.Iraq))
    app.setWindowIcon(QIcon(os.path.join(APP_DIR, 'assets', 'logo.jpg')))
    qss = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'theme.qss')
    app.setStyleSheet(open(qss, encoding='utf-8').read())
    return app


def main():
    app = create_app()
    from .main_window import MainWindow
    win = MainWindow()
    win.show()
    return app.exec()
