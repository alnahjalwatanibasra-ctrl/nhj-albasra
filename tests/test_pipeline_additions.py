# -*- coding: utf-8 -*-
import threading, pytest
from core import pipeline


def test_cancelled_error_exists():
    assert issubclass(pipeline.CancelledError, Exception)


def test_extract_honors_cancel_event(monkeypatch):
    calls = []
    monkeypatch.setattr(pipeline.gemini_ocr, 'extract_image',
        lambda k, img, m, vocab=None: calls.append(img) or {'headers': [], 'rows': []})
    ev = threading.Event(); ev.set()
    with pytest.raises(pipeline.CancelledError):
        pipeline._extract(['a.jpg', 'b.jpg'], 'k', ['m'], None, None, cancel=ev)
    assert calls == []          # أُلغي قبل أول صورة


def test_rows_carry_page_index(monkeypatch):
    pages = [{'headers': ['اسم صاحب الكتاب'], 'rows': [{'cells': {'اسم صاحب الكتاب': {'v': 'x', 'c': 'high'}}}] * 2},
             {'headers': ['اسم صاحب الكتاب'], 'rows': [{'cells': {'اسم صاحب الكتاب': {'v': 'y', 'c': 'high'}}}]}]
    it = iter(pages)
    monkeypatch.setattr(pipeline.gemini_ocr, 'extract_image', lambda k, img, m, vocab=None: next(it))
    rows = pipeline._extract(['p1.jpg', 'p2.jpg'], 'k', ['m'], None, None)
    assert [r['_page'] for r in rows] == [0, 0, 1]
