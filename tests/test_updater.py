# -*- coding: utf-8 -*-
"""آلية التحديث التلقائي عبر GitHub Releases: مقارنة الإصدارات والفحص."""
import io, json
import pytest
from core import updater


def test_parse_ver():
    assert updater.parse_ver('1.4') == (1, 4, 0)
    assert updater.parse_ver('2.0.3') == (2, 0, 3)
    assert updater.parse_ver('') == (0, 0, 0)
    assert updater.parse_ver('1.10') > updater.parse_ver('1.9')


def test_no_drive_legacy_remains():
    """GitHub هو المصدر الوحيد — لا تُعِد أي تحويل لروابط درايف."""
    assert not hasattr(updater, 'gdrive_direct')
    assert 'drive.google' not in open(updater.__file__, encoding='utf-8').read()


def _mock_manifest(monkeypatch, payload):
    monkeypatch.setattr(updater.urllib.request, 'urlopen',
                        lambda req, timeout=30: io.BytesIO(json.dumps(payload).encode()))


def test_check_newer_found(monkeypatch):
    _mock_manifest(monkeypatch, {'version': '9.9', 'url': 'http://x/app.exe', 'notes': 'جديد'})
    info = updater.check('http://x/version.json', '1.4')
    assert info['version'] == '9.9' and info['notes'] == 'جديد'


def test_check_same_or_older_none(monkeypatch):
    _mock_manifest(monkeypatch, {'version': '1.4', 'url': 'http://x/app.exe'})
    assert updater.check('http://x/version.json', '1.4') is None
    _mock_manifest(monkeypatch, {'version': '1.3', 'url': 'http://x/app.exe'})
    assert updater.check('http://x/version.json', '1.4') is None


def test_apply_refuses_outside_frozen(tmp_path):
    with pytest.raises(RuntimeError):
        updater.apply_and_restart(str(tmp_path / 'new.exe'))
