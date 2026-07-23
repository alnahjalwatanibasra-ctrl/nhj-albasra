# -*- coding: utf-8 -*-
"""رقم إصدار التطبيق — مصدر الحقيقة الوحيد. ارفعه مع كل بناء exe جديد."""
VERSION = '4.6'

# مستودع GitHub للتحديثات — الرابط الثابت «latest» يشير دائماً لأحدث إصدار
GITHUB_REPO = 'alnahjalwatanibasra-ctrl/nhj-albasra'
RELEASE_ASSET = 'NhjALBasra.exe'          # اسم الملف في الـ Release (بلا مسافات — رابط نظيف)


def latest_url(filename):
    return f'https://github.com/{GITHUB_REPO}/releases/latest/download/{filename}'


MANIFEST_URL = latest_url('version.json')
EXE_URL = latest_url(RELEASE_ASSET)
