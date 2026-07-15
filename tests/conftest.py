# -*- coding: utf-8 -*-
"""عزل الاختبارات: جلسة مؤقتة لكل اختبار حتى لا تتداخل مع جلسة المستخدم الحقيقية
(جلسة حقيقية موجودة كانت تجعل نافذة «استكمال الجلسة؟» تعلّق الاختبارات بلا نهاية)."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest


@pytest.fixture(autouse=True)
def isolated_session(tmp_path, monkeypatch):
    from ui import session
    monkeypatch.setattr(session, 'DEFAULT_PATH', str(tmp_path / 'session_autosave.json'))
