# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.main_window import MainWindow


def test_home_has_sharing_card_and_opens(qtbot=None):
    create_app([])
    w = MainWindow()
    assert hasattr(w.home_page, 'card_share')
    w._open_feature('share')
    assert w.stack.currentWidget() is w.sharing_page
    w.close()
