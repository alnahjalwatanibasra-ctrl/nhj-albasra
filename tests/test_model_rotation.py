# -*- coding: utf-8 -*-
"""تناوب النماذج: 429 = تحويل فوري + تذكُّر النموذج الممتلئ للجلسة."""
import json, urllib.error, pytest
from core import gemini_ocr


class _Resp429(urllib.error.HTTPError):
    def __init__(self):
        super().__init__('u', 429, 'quota', {}, None)


def test_429_switches_immediately_and_remembers(monkeypatch, tmp_path):
    gemini_ocr.reset_dead_models()
    img = tmp_path / 'a.jpg'; img.write_bytes(b'x')
    calls = []

    def fake_call(key, model, data, timeout=120, prompt=None, mime='application/json', thinking=None):
        calls.append(model)
        if model == 'dead-model':
            raise _Resp429()
        return {'headers': ['ح'], 'rows': []}

    monkeypatch.setattr(gemini_ocr, '_call', fake_call)
    monkeypatch.setattr(gemini_ocr.time, 'sleep',
                        lambda s: (_ for _ in ()).throw(AssertionError('لا انتظار على 429!')))
    models = ['dead-model', 'live-model']
    r1 = gemini_ocr.extract_image('k', str(img), models)
    assert r1['model'] == 'live-model'
    assert calls == ['dead-model', 'live-model']
    # الصورة الثانية: لا يعيد تجربة الممتلئ إطلاقاً
    calls.clear()
    r2 = gemini_ocr.extract_image('k', str(img), models)
    assert calls == ['live-model']
    gemini_ocr.reset_dead_models()
