# -*- coding: utf-8 -*-
"""ميزة «استخراج النصوص» + الشاشة الرئيسية والتنقل."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.main_window import MainWindow
from ui.text_worker import join_pages, TextWorker
from core import gemini_ocr


def test_join_pages_single_and_multi():
    assert join_pages(['نص وحيد']) == 'نص وحيد'
    out = join_pages(['أول', 'ثانٍ', 'ثالث'])
    assert '——— الصفحة 2 ———' in out and '——— الصفحة 3 ———' in out
    assert out.startswith('أول') and out.endswith('ثالث')


def test_home_is_first_and_navigates():
    app = create_app([])
    win = MainWindow()
    assert win.stack.currentWidget() is win.home_page
    win.home_page.featureRequested.emit('text')
    assert win.stack.currentWidget() is win.text_page
    win._go_home()
    assert win.stack.currentWidget() is win.home_page
    win.home_page.featureRequested.emit('sadir')
    assert win.stack.currentWidget() is win.start_page


def test_home_button_visibility():
    app = create_app([])
    win = MainWindow()
    assert not win.btn_home.isVisibleTo(win)
    win._open_feature('text')
    assert win.btn_home.isVisibleTo(win)


def test_text_page_flow(tmp_path):
    app = create_app([])
    win = MainWindow()
    page = win.text_page
    assert not page.btn_go.isEnabled()
    img = tmp_path / 'a.jpg'; img.write_text('x')
    page.add_images([str(img)])
    assert page.btn_go.isEnabled()
    page._done('نص مستخرج')
    assert page.txt.toPlainText() == 'نص مستخرج'
    assert page.btn_copy.isEnabled()
    page._copy_all()
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == 'نص مستخرج'


def test_extract_text_image_plain(monkeypatch, tmp_path):
    gemini_ocr.reset_dead_models()
    img = tmp_path / 'a.jpg'; img.write_bytes(b'x')
    monkeypatch.setattr(gemini_ocr, '_call',
                        lambda k, m, d, timeout=300, prompt=None, mime='application/json',
                        thinking=None: 'سطر أول\nسطر ثانٍ')
    res = gemini_ocr.extract_text_image('k', str(img), ['m1'])
    assert res['text'] == 'سطر أول\nسطر ثانٍ'
    assert res['model'] == 'm1'


def test_text_worker_end_to_end(monkeypatch, tmp_path):
    app = create_app([])
    imgs = []
    for n in ('a.jpg', 'b.jpg'):
        p = tmp_path / n; p.write_bytes(b'x'); imgs.append(str(p))
    monkeypatch.setattr(gemini_ocr, 'extract_text_image',
                        lambda k, img, m, progress=None:
                        {'text': 'نص ' + os.path.basename(img), 'model': 'm'})
    w = TextWorker(imgs)
    got = {}
    w.finished_ok.connect(lambda t: got.setdefault('t', t))
    w.run()
    assert 'نص a.jpg' in got['t'] and 'نص b.jpg' in got['t']
    assert '——— الصفحة 2 ———' in got['t']
