# -*- coding: utf-8 -*-
"""محاولات الوصول البديلة للمانيفست + تقرير الأخطاء (بدل رسالة عامة تُخفي السبب)."""
import io, json
import pytest
from core import updater

MF = {'version': '9.9', 'url': 'https://github.com/x/y/app.exe', 'notes': 'n'}


def test_first_attempt_success_reports_it(monkeypatch):
    monkeypatch.setattr(updater.urllib.request, 'urlopen',
                        lambda req, timeout=30: io.BytesIO(json.dumps(MF).encode()))
    data, report = updater.fetch_manifest_verbose('https://github.com/x/version.json')
    assert data['version'] == '9.9'
    assert 'نجح' in report


def test_falls_back_when_first_attempt_fails(monkeypatch):
    """فشل المسار العادي لا يُسقط التحديث: يُجرَّب مسار بلا بروكسي."""
    calls = {'n': 0}

    def flaky(req, timeout=30):
        calls['n'] += 1
        if calls['n'] == 1:
            raise OSError('proxy dead')
        return io.BytesIO(json.dumps(MF).encode())

    monkeypatch.setattr(updater.urllib.request, 'urlopen', flaky)

    class _Opener:
        def open(self, req, timeout=30):
            return io.BytesIO(json.dumps(MF).encode())

    monkeypatch.setattr(updater.urllib.request, 'build_opener', lambda *a: _Opener())
    data, report = updater.fetch_manifest_verbose('https://github.com/x/version.json')
    assert data['version'] == '9.9'
    assert 'OSError' in report          # المحاولة الأولى مسجّلة بسببها


def test_all_attempts_fail_raises_with_every_reason(monkeypatch):
    def dead(req, timeout=30):
        raise OSError('no route to host')

    monkeypatch.setattr(updater.urllib.request, 'urlopen', dead)

    class _Opener:
        def open(self, req, timeout=30):
            raise OSError('no route to host')

    monkeypatch.setattr(updater.urllib.request, 'build_opener', lambda *a: _Opener())
    with pytest.raises(RuntimeError) as e:
        updater.fetch_manifest_verbose('https://github.com/x/version.json')
    msg = str(e.value)
    assert 'OSError' in msg and 'no route to host' in msg
    for name in ('عادي', 'بلا بروكسي', 'ترويسة متصفّح'):
        assert name in msg              # تقرير كل محاولة موجود
