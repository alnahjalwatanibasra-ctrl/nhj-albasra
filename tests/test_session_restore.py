# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QMessageBox
from ui.app import create_app
from ui import session
from ui.main_window import MainWindow

RESULT = {'headers': ['رقم الكتاب'], 'rows': [{'رقم الكتاب': '٤٨٩'}],
          'colors': {}, 'matched': [True], 'row_pages': [0], 'phone_suggestions': []}


def test_restore_offered_and_loads(monkeypatch):
    app = create_app([])
    session.save(session.DEFAULT_PATH, RESULT, images=[])
    monkeypatch.setattr(QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    win = MainWindow()
    assert win.stack.currentWidget() is win.review_page
    assert win.review_page.table.rowCount() == 1
    session.clear(session.DEFAULT_PATH)


def test_restore_declined_clears(monkeypatch):
    app = create_app([])
    session.save(session.DEFAULT_PATH, RESULT, images=[])
    monkeypatch.setattr(QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QMessageBox.StandardButton.No))
    win = MainWindow()
    assert win.stack.currentWidget() is win.start_page
    assert session.load(session.DEFAULT_PATH) is None
