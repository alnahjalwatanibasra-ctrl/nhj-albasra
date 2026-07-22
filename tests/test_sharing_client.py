# -*- coding: utf-8 -*-
import os
from core.sharing.registry import Registry
from core.sharing.server import FileShareServer
from core.sharing import client as C


def test_unique_path_avoids_overwrite(tmp_path):
    (tmp_path / 'a.txt').write_text('x')
    p2 = C.unique_path(str(tmp_path), 'a.txt')
    assert p2.endswith('a (٢).txt')
    (tmp_path / 'a (٢).txt').write_text('y')
    p3 = C.unique_path(str(tmp_path), 'a.txt')
    assert p3.endswith('a (٣).txt')


def test_index_cache_roundtrip(tmp_path):
    cache = C.IndexCache(str(tmp_path / 'cache.json'))
    cache.put('dev1', 'مكتب أ', [{'id': 'f1', 'name': 'x.txt'}])
    cache2 = C.IndexCache(str(tmp_path / 'cache.json'))
    entry = cache2.get('dev1')
    assert entry['name'] == 'مكتب أ'
    assert entry['files'][0]['id'] == 'f1'


def test_fetch_index_and_download_roundtrip(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    src = tmp_path / 'report.xlsx'; src.write_bytes(b'CONTENT-123')
    fid = reg.add(str(src))
    srv = FileShareServer(reg, port=0); srv.start()
    try:
        files = C.fetch_index('127.0.0.1', srv.port)
        assert files[0]['id'] == fid
        dest = tmp_path / 'in'; dest.mkdir()
        saved = C.download('127.0.0.1', srv.port, fid, 'report.xlsx',
                           str(dest), by='مكتب ب')
        assert open(saved, 'rb').read() == b'CONTENT-123'
        assert reg.list()[0]['downloaded_by'] == ['مكتب ب']
    finally:
        srv.stop()
