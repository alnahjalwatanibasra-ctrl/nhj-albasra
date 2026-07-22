# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.sharing_worker import DownloadWorker, RefreshWorker


def test_workers_construct():
    create_app([])
    rw = RefreshWorker(service=None)
    assert rw is not None
    dw = DownloadWorker(service=None, row={'name': 'x'})
    assert dw.row['name'] == 'x'
