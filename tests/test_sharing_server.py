# -*- coding: utf-8 -*-
import json, os
from core.sharing.registry import Registry
from core.sharing.server import route


def _reg(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    f = tmp_path / 'doc.xlsx'; f.write_bytes(b'hello')
    fid = reg.add(str(f))
    return reg, fid


def test_ping_ok(tmp_path):
    reg, _ = _reg(tmp_path)
    status, ctype, body = route(reg, '/ping', {})
    assert status == 200


def test_index_returns_files(tmp_path):
    reg, fid = _reg(tmp_path)
    status, ctype, body = route(reg, '/index', {})
    assert status == 200
    data = json.loads(body.decode('utf-8'))
    assert data['files'][0]['id'] == fid
    assert 'path' not in data['files'][0]


def test_file_returns_path_and_marks_downloaded(tmp_path):
    reg, fid = _reg(tmp_path)
    status, ctype, body = route(reg, '/file/' + fid, {'by': ['مكتب ب']})
    assert status == 200
    assert body[0] == 'FILE' and body[1].endswith('doc.xlsx')
    assert reg.list()[0]['downloaded_by'] == ['مكتب ب']


def test_unknown_id_is_404(tmp_path):
    reg, _ = _reg(tmp_path)
    status, _, _ = route(reg, '/file/deadbeef', {})
    assert status == 404


def test_path_traversal_blocked(tmp_path):
    reg, _ = _reg(tmp_path)
    status, _, _ = route(reg, '/file/..%2f..%2fsecret', {})
    assert status == 404


def test_missing_original_is_404(tmp_path):
    reg, fid = _reg(tmp_path)
    os.remove(reg.path_of(fid))
    status, _, _ = route(reg, '/file/' + fid, {})
    assert status == 404
