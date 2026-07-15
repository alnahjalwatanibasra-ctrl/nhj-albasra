# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.start_page import StartPage


def test_button_disabled_until_ready(tmp_path):
    app = create_app([])
    page = StartPage(settings={})
    assert not page.btn_start.isEnabled()
    ref = tmp_path / 'ref.xlsx'; ref.write_text('x')
    img = tmp_path / 'a.jpg'; img.write_text('x')
    page.set_reference(str(ref))
    page.add_images([str(img)])
    assert page.btn_start.isEnabled()
    page.remove_image(0)
    assert not page.btn_start.isEnabled()


def test_missing_saved_path_marked(tmp_path):
    app = create_app([])
    page = StartPage(settings={'reference_path': str(tmp_path / 'gone.xlsx')})
    assert 'غير موجود' in page.lbl_reference.text()


def test_start_signal_payload(tmp_path):
    app = create_app([])
    ref = tmp_path / 'ref.xlsx'; ref.write_text('x')
    img = tmp_path / 'a.jpg'; img.write_text('x')
    page = StartPage(settings={'reference_path': str(ref)})
    page.add_images([str(img)])
    got = {}
    page.startRequested.connect(lambda imgs, paths: got.update(imgs=imgs, paths=paths))
    page._emit_start()
    assert got['imgs'] == [str(img)]
    assert got['paths']['reference'] == str(ref)
    assert got['paths']['prev_register'] is None
