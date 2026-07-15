# -*- coding: utf-8 -*-
"""النافذة الرئيسية: شريط علوي بهوية النهج + ثلاث صفحات (بداية/تقدم/مراجعة)."""
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QToolButton, QStackedWidget)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from .app import APP_DIR

TITLE = 'سجل الصادر — تحالف النهج الوطني'


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITLE)
        self.resize(1100, 750)
        root = QWidget(); self.setCentralWidget(root)
        lay = QVBoxLayout(root); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        lay.addWidget(self._topbar())
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self._build_pages()

    def _topbar(self):
        bar = QWidget(); bar.setObjectName('topbar'); bar.setFixedHeight(52)
        h = QHBoxLayout(bar); h.setContentsMargins(14, 6, 14, 6)
        logo = QLabel()
        pix = QPixmap(os.path.join(APP_DIR, 'assets', 'logo.jpg'))
        if not pix.isNull():
            logo.setPixmap(pix.scaledToHeight(38, Qt.SmoothTransformation))
        h.addWidget(logo)
        h.addWidget(QLabel(TITLE))
        h.addStretch(1)
        self.btn_settings = QToolButton(); self.btn_settings.setText('⚙  الإعدادات')
        h.addWidget(self.btn_settings)
        return bar

    def _build_pages(self):
        pass
