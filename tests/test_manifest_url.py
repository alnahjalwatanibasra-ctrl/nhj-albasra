# -*- coding: utf-8 -*-
"""حماية رابط التحديث: رابط موروث غير صالح كان يعطّل التحديث بصمت على أجهزة المكتب."""
import json
from core import config
from core.version import MANIFEST_URL


def test_stale_drive_url_is_ignored():
    """رابط درايف حقيقي (بلا النقاط الحرفية) كان يمرّ ويُستعمل — يجب تجاهله الآن."""
    stale = 'https://drive.google.com/file/d/1AbCdEfGhIjK/view?usp=sharing'
    assert config.manifest_url({'update_manifest_url': stale}) == MANIFEST_URL


def test_empty_or_garbage_override_falls_back():
    for bad in ('', '   ', 'not-a-url', 'https://example.com/version.json'):
        assert config.manifest_url({'update_manifest_url': bad}) == MANIFEST_URL


def test_valid_github_override_is_honored():
    good = 'https://github.com/someone/repo/releases/latest/download/version.json'
    assert config.manifest_url({'update_manifest_url': good}) == good


def test_load_settings_self_heals_stale_url(tmp_path, monkeypatch):
    p = tmp_path / 'settings.json'
    p.write_text(json.dumps({
        'update_manifest_url': 'https://drive.google.com/file/d/1XyZ/view'
    }), encoding='utf-8')
    monkeypatch.setattr(config, 'SETTINGS_PATH', str(p))
    s = config.load_settings()
    assert s['update_manifest_url'] == ''          # نُظّف تلقائياً
    assert config.manifest_url(s) == MANIFEST_URL  # فيعود للرابط المدمج


def test_load_settings_keeps_valid_github_url(tmp_path, monkeypatch):
    good = 'https://github.com/x/y/releases/latest/download/version.json'
    p = tmp_path / 'settings.json'
    p.write_text(json.dumps({'update_manifest_url': good}), encoding='utf-8')
    monkeypatch.setattr(config, 'SETTINGS_PATH', str(p))
    assert config.load_settings()['update_manifest_url'] == good
