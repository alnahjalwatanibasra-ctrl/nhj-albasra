# -*- coding: utf-8 -*-
from ui import session

RESULT = {'headers': ['رقم الكتاب'], 'rows': [{'رقم الكتاب': '٤٨٩'}],
          'colors': {(0, 'رقم الكتاب'): 'ref'}, 'matched': [True],
          'row_pages': [0]}


def test_roundtrip(tmp_path):
    p = tmp_path / 's.json'
    session.save(str(p), RESULT, images=['a.jpg'])
    loaded = session.load(str(p))
    assert loaded['result']['rows'] == RESULT['rows']
    assert loaded['result']['colors'] == RESULT['colors']
    assert loaded['images'] == ['a.jpg']


def test_load_missing_or_corrupt(tmp_path):
    assert session.load(str(tmp_path / 'none.json')) is None
    bad = tmp_path / 'bad.json'; bad.write_text('{{{', encoding='utf-8')
    assert session.load(str(bad)) is None


def test_clear(tmp_path):
    p = tmp_path / 's.json'
    session.save(str(p), RESULT, images=[])
    session.clear(str(p))
    assert session.load(str(p)) is None
