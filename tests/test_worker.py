# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from ui.app import create_app
from ui import worker


def test_worker_emits_finished(monkeypatch):
    app = create_app([])
    fake = {'headers': ['رقم الكتاب'], 'rows': [], 'colors': {}, 'matched': [],
            'row_pages': [], 'names': []}
    def fake_run(*a, **k):
        cb = k.get('progress')
        if cb:
            cb('تجريب')
        return fake
    monkeypatch.setattr(worker.pipeline, 'run', fake_run)
    w = worker.ExtractWorker(images=['x.jpg'], reference='r.xlsx',
                             prev_register=None, word_folder=None)
    done = {}
    w.finished_ok.connect(lambda res: done.setdefault('res', res))
    w.run()          # تشغيل متزامن في الاختبار (بلا خيط)
    assert done['res']['headers'] == ['رقم الكتاب']
    assert done['res']['phone_suggestions'] == []


def test_worker_emits_cancelled(monkeypatch):
    app = create_app([])
    def boom(*a, **k):
        raise worker.pipeline.CancelledError()
    monkeypatch.setattr(worker.pipeline, 'run', boom)
    w = worker.ExtractWorker(images=['x.jpg'], reference='r.xlsx')
    got = []
    w.failed.connect(got.append)
    w.run()
    assert got == ['CANCELLED']
