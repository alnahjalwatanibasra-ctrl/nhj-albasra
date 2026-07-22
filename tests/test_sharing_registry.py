# -*- coding: utf-8 -*-
import os
from core.sharing.registry import Registry


def _make_file(tmp_path, name='doc.xlsx', data=b'hello'):
    p = tmp_path / name
    p.write_bytes(data)
    return str(p)


def test_add_creates_entry_with_metadata(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    f = _make_file(tmp_path)
    fid = reg.add(f)
    items = reg.list()
    assert len(items) == 1
    it = items[0]
    assert it['id'] == fid
    assert it['name'] == 'doc.xlsx'
    assert it['type'] == 'xlsx'
    assert it['size'] == 5
    assert it['downloaded_by'] == []


def test_add_persists_across_instances(tmp_path):
    path = str(tmp_path / 'reg.json')
    fid = Registry(path).add(_make_file(tmp_path))
    reg2 = Registry(path)
    assert reg2.path_of(fid).endswith('doc.xlsx')


def test_remove_deletes_entry(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    fid = reg.add(_make_file(tmp_path))
    reg.remove(fid)
    assert reg.list() == []


def test_list_sorted_newest_first(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    a = reg.add(_make_file(tmp_path, 'a.txt'))
    reg.items[a]['shared_at'] = 100
    b = reg.add(_make_file(tmp_path, 'b.txt'))
    reg.items[b]['shared_at'] = 200
    assert [x['id'] for x in reg.list()] == [b, a]


def test_index_reports_availability(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    f = _make_file(tmp_path)
    fid = reg.add(f)
    assert reg.index()[0]['available'] is True
    os.remove(f)
    assert reg.index()[0]['available'] is False
    assert 'path' not in reg.index()[0]


def test_resolve_missing_updates_path(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    fid = reg.add(_make_file(tmp_path, 'a.txt'))
    newp = _make_file(tmp_path, 'moved.txt', b'xx')
    reg.resolve_missing(fid, newp)
    assert reg.path_of(fid).endswith('moved.txt')
    assert reg.list()[0]['name'] == 'moved.txt'


def test_mark_downloaded_records_unique_names(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    fid = reg.add(_make_file(tmp_path))
    reg.mark_downloaded(fid, 'مكتب ب')
    reg.mark_downloaded(fid, 'مكتب ب')
    assert reg.list()[0]['downloaded_by'] == ['مكتب ب']
