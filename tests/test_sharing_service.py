# -*- coding: utf-8 -*-
from core.sharing.service import ShareService


def test_share_and_list_my_files(tmp_path):
    f = tmp_path / 'a.xlsx'; f.write_bytes(b'x')
    svc = ShareService(str(tmp_path), lambda: 'مكتب أ')
    fid = svc.share(str(f))
    assert svc.my_files()[0]['id'] == fid
    svc.unshare(fid)
    assert svc.my_files() == []


def test_incoming_merges_cache_and_marks_offline(tmp_path):
    svc = ShareService(str(tmp_path), lambda: 'مكتب أ')
    svc.cache.put('devX', 'مكتب ب',
                  [{'id': 'f1', 'name': 'تقرير.xlsx', 'type': 'xlsx',
                    'size': 3, 'shared_at': 1.0, 'available': True}])
    rows = svc.incoming()
    assert len(rows) == 1
    assert rows[0]['peer_name'] == 'مكتب ب'
    assert rows[0]['peer_online'] is False
    assert rows[0]['name'] == 'تقرير.xlsx'


def test_two_services_discover_and_download(tmp_path):
    import time
    a_dir = tmp_path / 'A'; a_dir.mkdir()
    b_dir = tmp_path / 'B'; b_dir.mkdir()
    src = a_dir / 'report.xlsx'; src.write_bytes(b'HELLO-P2P')
    a = ShareService(str(a_dir), lambda: 'مكتب أ'); a.start()
    b = ShareService(str(b_dir), lambda: 'مكتب ب'); b.start()
    try:
        a.share(str(src))
        deadline = time.time() + 8
        while time.time() < deadline and not b.incoming():
            b.refresh(); time.sleep(0.5)
        rows = b.incoming()
        assert any(r['name'] == 'report.xlsx' for r in rows)
        row = [r for r in rows if r['name'] == 'report.xlsx'][0]
        saved = b.download(row)
        assert open(saved, 'rb').read() == b'HELLO-P2P'
    finally:
        a.stop(); b.stop()
