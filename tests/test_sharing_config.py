# -*- coding: utf-8 -*-
import os
from core import config


def test_default_device_name_is_hostname_when_unset():
    s = dict(config.DEFAULTS)
    assert 'device_name' in s
    assert config.device_name(s)  # غير فارغ (يرجع اسم الحاسوب عند الفراغ)


def test_device_name_uses_setting_when_present():
    assert config.device_name({'device_name': 'مكتب أ'}) == 'مكتب أ'


def test_sharing_dirs_under_app_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'APP_DIR', str(tmp_path))
    recv = config.received_dir()
    assert recv.endswith('الملفات المستلمة')
    assert os.path.isdir(recv)  # يُنشأ تلقائياً
