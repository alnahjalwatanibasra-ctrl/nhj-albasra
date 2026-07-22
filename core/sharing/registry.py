# -*- coding: utf-8 -*-
"""سجل الملفات التي يشاركها هذا الجهاز. نخزّن المسار فقط (لا نسخ — الخيار أ).
يُحفظ JSON في مجلد بيانات التطبيق."""
import json, os, time, uuid


class Registry:
    def __init__(self, path):
        self.path = path
        self.items = {}          # id -> dict
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                self.items = json.load(open(self.path, encoding='utf-8'))
            except Exception:
                self.items = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or '.', exist_ok=True)
        json.dump(self.items, open(self.path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)

    def add(self, path):
        fid = uuid.uuid4().hex[:12]
        self.items[fid] = {
            'id': fid,
            'path': path,
            'name': os.path.basename(path),
            'size': os.path.getsize(path) if os.path.exists(path) else 0,
            'type': os.path.splitext(path)[1].lower().lstrip('.'),
            'shared_at': time.time(),
            'downloaded_by': [],
        }
        self._save()
        return fid

    def remove(self, fid):
        if fid in self.items:
            del self.items[fid]
            self._save()

    def list(self):
        return sorted(self.items.values(),
                      key=lambda x: x.get('shared_at', 0), reverse=True)

    def path_of(self, fid):
        it = self.items.get(fid)
        return it['path'] if it else None

    def resolve_missing(self, fid, new_path):
        it = self.items.get(fid)
        if it:
            it['path'] = new_path
            it['name'] = os.path.basename(new_path)
            it['size'] = os.path.getsize(new_path) if os.path.exists(new_path) else 0
            self._save()

    def mark_downloaded(self, fid, by):
        it = self.items.get(fid)
        if it and by and by not in it['downloaded_by']:
            it['downloaded_by'].append(by)
            self._save()

    def index(self):
        """التمثيل المقدَّم للأقران عبر /index — بلا المسار المحلي."""
        return [{
            'id': it['id'], 'name': it['name'], 'size': it['size'],
            'type': it['type'], 'shared_at': it['shared_at'],
            'available': os.path.exists(it['path']),
        } for it in self.list()]
