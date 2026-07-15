# -*- coding: utf-8 -*-
from ui import logic


def test_can_start_requires_images_and_reference(tmp_path):
    ref = tmp_path / 'ref.xlsx'; ref.write_text('x')
    img = tmp_path / 'a.jpg'; img.write_text('x')
    ok, why = logic.can_start([], str(ref));         assert not ok and 'صور' in why
    ok, why = logic.can_start([str(img)], '');       assert not ok and 'المرجعي' in why
    ok, why = logic.can_start([str(img)], str(tmp_path / 'gone.xlsx')); assert not ok
    ok, why = logic.can_start([str(img)], str(ref)); assert ok and why == ''


def test_export_filename_from_numbers():
    rows = [{'رقم الكتاب': '٤٨٩'}, {'رقم الكتاب': '٥١٥'}]
    assert logic.export_filename(rows) == 'سجل_الصادر_489-515.xlsx'
    assert logic.export_filename([]) == 'سجل_الصادر.xlsx'


def test_colors_roundtrip():
    colors = {(0, 'اسم صاحب الكتاب'): 'ref', (3, 'رقم الهاتف'): 'phone_unconf'}
    ser = logic.colors_to_list(colors)
    assert logic.colors_from_list(ser) == colors


def test_unmatched_rows():
    assert logic.unmatched_rows([True, False, True, False]) == [1, 3]


def test_missing_phone_rows():
    rows = [{'رقم الهاتف': '٠٧٨٠٢١٧٨٧٣٦'}, {'رقم الهاتف': ''}, {'رقم الهاتف': 'لا يوجد'}]
    matched = [True, False, False]
    assert logic.missing_phone_rows(rows, matched) == [1, 2]
