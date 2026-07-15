# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.review_page import ReviewPage

RESULT = {
    'headers': ['رقم الكتاب', 'اسم صاحب الكتاب'],
    'rows': [{'رقم الكتاب': '٤٨٩', 'اسم صاحب الكتاب': 'رقية علي محسن'},
             {'رقم الكتاب': '٤٩٠', 'اسم صاحب الكتاب': 'غريب عن المرجع'}],
    'colors': {(0, 'اسم صاحب الكتاب'): 'ref'},
    'matched': [True, False], 'row_pages': [0, 0], 'phone_suggestions': [],
}


def _fresh():
    return {**RESULT, 'colors': dict(RESULT['colors'])}


def test_fill_table_and_colors():
    app = create_app([])
    page = ReviewPage()
    page.load_result(_fresh(), images=[])
    assert page.table.rowCount() == 2
    assert page.table.item(0, 1).background().color().name().upper() == '#C6EFCE'
    assert '1' in page.lbl_unmatched.text() or '١' in page.lbl_unmatched.text()
    assert page.lbl_unmatched.isVisibleTo(page)


def test_manual_edit_clears_color():
    app = create_app([])
    page = ReviewPage()
    page.load_result(_fresh(), images=[])
    page.table.item(0, 1).setText('تعديل يدوي')
    assert (0, 'اسم صاحب الكتاب') not in page.result['colors']


def test_current_rows_reflect_edits():
    app = create_app([])
    page = ReviewPage()
    page.load_result(_fresh(), images=[])
    page.table.item(1, 1).setText('اسم مصحح')
    assert page.current_rows()[1]['اسم صاحب الكتاب'] == 'اسم مصحح'


def test_set_cell_colors_and_keeps_result():
    app = create_app([])
    page = ReviewPage()
    page.load_result(_fresh(), images=[])
    page.set_cell(1, 'اسم صاحب الكتاب', 'من وورد', color_key='word')
    assert page.result['colors'][(1, 'اسم صاحب الكتاب')] == 'word'
    assert page.current_rows()[1]['اسم صاحب الكتاب'] == 'من وورد'
