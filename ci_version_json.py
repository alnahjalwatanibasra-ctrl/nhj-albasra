# -*- coding: utf-8 -*-
"""يولّد version.json للنشر التلقائي (GitHub Actions): يقرأ الإصدار والرابط من
core/version.py، والملاحظات من RELEASE_NOTES.txt إن وُجد. بلا مشاكل ترميز."""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.version import VERSION, EXE_URL

notes = ''
np = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RELEASE_NOTES.txt')
if os.path.exists(np):
    notes = open(np, encoding='utf-8').read().strip()

manifest = {'version': VERSION, 'url': EXE_URL, 'notes': notes}
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print('version.json:', json.dumps(manifest, ensure_ascii=False))
