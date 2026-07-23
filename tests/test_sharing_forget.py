# -*- coding: utf-8 -*-
"""إزالة عنصر عالق من قائمة الوارد يدوياً (ملف حذفه صاحبه وهو غير متصل)."""
from core.sharing import client as C
from core.sharing.service import ShareService


def test_indexcache_forget_removes_one_file(tmp_path):
    cache = C.IndexCache(str(tmp_path / 'c.json'))
    cache.put('devX', 'ب', [{'id': 'f1', 'name': 'a.txt'},
                            {'id': 'f2', 'name': 'b.txt'}])
    assert cache.forget('devX', 'f1') is True
    assert [f['id'] for f in cache.get('devX')['files']] == ['f2']
    assert cache.forget('devX', 'nope') is False        # غير موجود


def test_indexcache_forget_drops_empty_peer(tmp_path):
    cache = C.IndexCache(str(tmp_path / 'c.json'))
    cache.put('devX', 'ب', [{'id': 'f1', 'name': 'a.txt'}])
    cache.forget('devX', 'f1')
    assert 'devX' not in cache.all()                    # أُزيل القرين الفارغ


def test_forget_persists_across_instances(tmp_path):
    p = str(tmp_path / 'c.json')
    c1 = C.IndexCache(p)
    c1.put('devX', 'ب', [{'id': 'f1'}, {'id': 'f2'}])
    c1.forget('devX', 'f1')
    c2 = C.IndexCache(p)
    assert [f['id'] for f in c2.get('devX')['files']] == ['f2']


def test_service_forget_incoming_removes_ghost(tmp_path):
    svc = ShareService(str(tmp_path), lambda: 'أ')
    svc.cache.put('devX', 'ب', [
        {'id': 'g1', 'name': 'شبح.xlsx', 'type': 'xlsx',
         'size': 1, 'shared_at': 1.0, 'available': True}])
    assert len(svc.incoming()) == 1
    svc.forget_incoming('devX', 'g1')
    assert svc.incoming() == []                          # اختفى الشبح
