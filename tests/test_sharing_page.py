# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.sharing_page import SharingPage
from core.sharing.service import ShareService


def test_page_builds_and_shares(tmp_path):
    create_app([])
    f = tmp_path / 'a.xlsx'; f.write_bytes(b'x')
    svc = ShareService(str(tmp_path), lambda: 'مكتب أ')
    page = SharingPage(svc)
    page.add_files([str(f)])
    assert svc.my_files()[0]['name'] == 'a.xlsx'
    assert page.mine_list.count() == 1
