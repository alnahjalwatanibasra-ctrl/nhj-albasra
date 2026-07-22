# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.dialogs.replacements_dialog import ReplacementsDialog
from ui.dialogs.settings_dialog import SettingsDialog


def test_replacements_roundtrip():
    app = create_app([])
    dlg = ReplacementsDialog({'رضخي': 'وظيفي'})
    assert dlg.values() == {'رضخي': 'وظيفي'}
    dlg.add_row('تخديم', 'تخصيص')
    assert dlg.values()['تخديم'] == 'تخصيص'


def test_settings_dialog_masks_key():
    app = create_app([])
    dlg = SettingsDialog({'gemini_key': 'AQ.Ab8SECRET', 'gemini_models': ['m1'],
                          'vocab_in_prompt': True, 'subject_replacements': {}})
    assert 'SECRET' not in dlg.lbl_key.text()


def test_settings_has_device_name_field():
    app = create_app([])
    dlg = SettingsDialog({'device_name': 'مكتب أ', 'gemini_models': ['m1'],
                          'vocab_in_prompt': True, 'subject_replacements': {}})
    assert dlg.txt_device.text() == 'مكتب أ'


def test_advanced_hidden_until_revealed():
    app = create_app([])
    dlg = SettingsDialog({'gemini_models': ['m1'], 'vocab_in_prompt': True,
                          'subject_replacements': {}})
    dlg.show()  # isVisible() يتطلب أن يكون النافذة الأعلى معروضة، وإلا فهو False دائماً
    assert dlg.adv.isVisible() is False
    dlg._reveal_advanced()
    assert dlg.adv.isVisible() is True
