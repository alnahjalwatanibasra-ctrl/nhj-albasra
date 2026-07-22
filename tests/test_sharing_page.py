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
    assert page.files_list.count() == 1


def test_single_space_merges_mine_and_peers(tmp_path):
    """مساحة واحدة موحّدة: ملفاتي وملفات الزملاء في نفس القائمة، الأحدث أولاً."""
    create_app([])
    f = tmp_path / 'ملفي.xlsx'; f.write_bytes(b'x')
    svc = ShareService(str(tmp_path), lambda: 'مكتب أ')
    fid = svc.share(str(f))
    svc.registry.items[fid]['shared_at'] = 10
    svc.cache.put('devX', 'مكتب ب',
                  [{'id': 'f1', 'name': 'ملف_الزميل.pdf', 'type': 'pdf',
                    'size': 3, 'shared_at': 20, 'available': True}])
    page = SharingPage(svc)
    rows = page._rows()
    assert [r['kind'] for r in rows] == ['peer', 'mine']      # الأحدث أولاً
    assert page.files_list.count() == 2                       # الاثنان في مساحة واحدة
    assert not hasattr(page, 'tabs')                          # لا تبويبات بعد الآن


def test_refresh_skips_when_worker_still_running(tmp_path, monkeypatch):
    """حارس منع انهيار QThread: لا يُستبدل عامل التحديث بينما هو قيد التشغيل
    (سبب الإغلاق المتزامن بين الجهازين)."""
    create_app([])
    svc = ShareService(str(tmp_path), lambda: 'مكتب أ')
    page = SharingPage(svc)

    class _Running:
        def isRunning(self):
            return True

    sentinel = _Running()
    page._rw = sentinel
    # قرين متصل ⟵ لولا الحارس لأنشأ عاملاً جديداً واستبدل sentinel
    monkeypatch.setattr(svc, 'peers',
                        lambda: [{'id': 'x', 'name': 'ب', 'ip': '127.0.0.1', 'port': 1}])
    page._refresh_incoming()
    assert page._rw is sentinel   # لم يُستبدل العامل الجاري
