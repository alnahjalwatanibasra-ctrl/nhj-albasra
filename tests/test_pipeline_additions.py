# -*- coding: utf-8 -*-
import threading, pytest
from core import pipeline


def test_cancelled_error_exists():
    assert issubclass(pipeline.CancelledError, Exception)


def test_extract_honors_cancel_event(monkeypatch):
    calls = []
    monkeypatch.setattr(pipeline.gemini_ocr, 'extract_image',
        lambda k, img, m, vocab=None, progress=None: calls.append(img) or {'headers': [], 'rows': []})
    ev = threading.Event(); ev.set()
    with pytest.raises(pipeline.CancelledError):
        pipeline._extract(['a.jpg', 'b.jpg'], 'k', ['m'], None, None, cancel=ev)
    assert calls == []          # أُلغي قبل أول صورة


def test_rows_carry_page_index(monkeypatch):
    pages = {'p1.jpg': {'headers': ['اسم صاحب الكتاب'],
                        'rows': [{'cells': {'اسم صاحب الكتاب': {'v': 'x', 'c': 'high'}}}] * 2},
             'p2.jpg': {'headers': ['اسم صاحب الكتاب'],
                        'rows': [{'cells': {'اسم صاحب الكتاب': {'v': 'y', 'c': 'high'}}}]}}
    monkeypatch.setattr(pipeline.gemini_ocr, 'extract_image',
                        lambda k, img, m, vocab=None, progress=None: pages[img])
    rows = pipeline._extract(['p1.jpg', 'p2.jpg'], 'k', ['m'], None, None)
    assert [r['_page'] for r in rows] == [0, 0, 1]
