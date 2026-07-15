# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.dialogs.phones_dialog import PhonesDialog

SUG = [{'row': 1, 'name': 'عبد المختار جبار', 'phone': '07710887993',
        'file': 'ص122.docx', 'score': 95}]


def test_accept_emits_row_and_phone():
    app = create_app([])
    dlg = PhonesDialog(SUG, word_folder='.')
    got = []
    dlg.accepted_one.connect(lambda row, phone: got.append((row, phone)))
    dlg._accept(0)
    assert got == [(1, '07710887993')]


def test_reject_disables_row():
    app = create_app([])
    dlg = PhonesDialog(SUG, word_folder='.')
    dlg._reject(0)
    assert not dlg._rows[0][0].isEnabled()
