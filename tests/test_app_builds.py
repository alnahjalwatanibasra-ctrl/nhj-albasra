# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt
from ui.app import create_app
from ui.main_window import MainWindow


def test_main_window_builds():
    app = create_app([])
    win = MainWindow()
    assert 'سجلات النهج' in win.windowTitle()
    assert app.layoutDirection() == Qt.RightToLeft
