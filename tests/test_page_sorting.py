# -*- coding: utf-8 -*-
"""ترتيب الصفحات تلقائياً حسب أرقام الكتب — يحمي من رفع الصور بترتيب خاطئ."""
from core import pipeline


def _rec(page, num, name):
    return {'_page': page, 'num': (num, 'high'), 'name': (name, 'high')}


def test_shuffled_pages_get_sorted_by_book_numbers():
    # رُفعت الصفحات معكوسة: صفحة الأرقام ٥٠٧+ أولاً ثم ٤٩٩+ ثم ٤٨٩+
    ext = ([_rec(0, '٥٠٧', 'ج١'), _rec(0, '٥٠٨', 'ج٢')] +
           [_rec(1, '٤٩٩', 'ب١'), _rec(1, '٥٠٠', 'ب٢')] +
           [_rec(2, '٤٨٩', 'أ١'), _rec(2, '٤٩٠', 'أ٢')])
    out = pipeline.sort_pages_by_numbers(ext)
    assert [r['name'][0] for r in out] == ['أ١', 'أ٢', 'ب١', 'ب٢', 'ج١', 'ج٢']
    # فهرس الصورة الأصلي محفوظ لكل صف (لعرض الصورة الصحيحة)
    assert [r['_page'] for r in out] == [2, 2, 1, 1, 0, 0]


def test_page_without_numbers_keeps_relative_position():
    ext = ([_rec(0, '٥٠٠', 'ب')] + [_rec(1, '', 'مجهول')] + [_rec(2, '٤٨٩', 'أ')])
    out = pipeline.sort_pages_by_numbers(ext)
    assert [r['name'][0] for r in out] == ['أ', 'ب', 'مجهول']


def test_correct_order_unchanged():
    ext = [_rec(0, '٤٨٩', 'أ'), _rec(1, '٤٩٩', 'ب'), _rec(2, '٥٠٧', 'ج')]
    out = pipeline.sort_pages_by_numbers(ext)
    assert [r['name'][0] for r in out] == ['أ', 'ب', 'ج']
