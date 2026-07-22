# -*- coding: utf-8 -*-
"""جلب فهرس الأقران وتنزيل الملفات + تفادي الطمس + تخزين آخر فهرس."""
import json, os, urllib.parse, urllib.request

_AR = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')


def unique_path(dest_dir, filename):
    """يتفادى الطمس: لو وُجد الاسم يُضاف (٢)، (٣)…"""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_dir, filename)
    n = 2
    while os.path.exists(candidate):
        suffix = str(n).translate(_AR)
        candidate = os.path.join(dest_dir, f'{base} ({suffix}){ext}')
        n += 1
    return candidate


def fetch_index(ip, port, timeout=4):
    url = f'http://{ip}:{port}/index'
    with urllib.request.urlopen(url, timeout=timeout) as r:
        data = json.loads(r.read().decode('utf-8'))
    return data.get('files', [])


def download(ip, port, fid, filename, dest_dir, by='', timeout=30, progress=None):
    """يجلب /file/<id>?by=<اسمي> ويحفظ باسم فريد. يرجع المسار المحفوظ."""
    os.makedirs(dest_dir, exist_ok=True)
    q = urllib.parse.urlencode({'by': by})
    url = f'http://{ip}:{port}/file/{fid}?{q}'
    saved = unique_path(dest_dir, filename)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        total = int(r.headers.get('Content-Length') or 0)
        done = 0
        with open(saved, 'wb') as fh:
            while True:
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                fh.write(chunk); done += len(chunk)
                if progress and total:
                    progress(done, total)
    return saved


class IndexCache:
    """يخزّن آخر فهرس معروف لكل قرين على القرص (بقاء القائمة بين الجلسات)."""
    def __init__(self, path):
        self.path = path
        self.data = {}           # peer_id -> {name, files}
        if os.path.exists(path):
            try:
                self.data = json.load(open(path, encoding='utf-8'))
            except Exception:
                self.data = {}

    def put(self, peer_id, name, files):
        self.data[peer_id] = {'name': name, 'files': files}
        self._save()

    def get(self, peer_id):
        return self.data.get(peer_id)

    def all(self):
        return self.data

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or '.', exist_ok=True)
        json.dump(self.data, open(self.path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
