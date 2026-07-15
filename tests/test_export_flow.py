# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import openpyxl
from ui.app import create_app
from ui.main_window import MainWindow
from ui import session

RESULT = {'headers': ['رقم الكتاب', 'اسم صاحب الكتاب'],
          'rows': [{'رقم الكتاب': '٤٨٩', 'اسم صاحب الكتاب': 'رقية علي محسن'}],
          'colors': {(0, 'اسم صاحب الكتاب'): 'ref'},
          'matched': [True], 'row_pages': [0], 'phone_suggestions': []}


def test_export_writes_file_and_clears_session(tmp_path, monkeypatch):
    app = create_app([])
    win = MainWindow()
    win._last_images = []
    win.review_page.load_result({**RESULT, 'colors': dict(RESULT['colors'])}, [])
    out = str(tmp_path / 'خرج.xlsx')
    monkeypatch.setattr('PySide6.QtWidgets.QFileDialog.getSaveFileName',
                        staticmethod(lambda *a, **k: (out, '')))
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.exec',
                        lambda self, *a, **k: None)
    win._autosave()
    win._do_export()
    wb = openpyxl.load_workbook(out)
    assert wb.active.cell(2, 2).value == 'رقية علي محسن'
    assert session.load(session.DEFAULT_PATH) is None
