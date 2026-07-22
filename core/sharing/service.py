# -*- coding: utf-8 -*-
"""منسّق المشاركة: يربط السجل + الخادم + التعارف + العميل، ويعرض واجهة بسيطة
للواجهة الرسومية. كل الشبكة تُدار هنا؛ المنطق النقي في الوحدات الأخرى."""
import os, uuid
from .registry import Registry
from .server import FileShareServer
from .discovery import Discovery
from . import client as C


class ShareService:
    def __init__(self, app_dir, name_getter):
        self.app_dir = app_dir
        self.name_getter = name_getter          # دالة ترجع اسم هذا الجهاز
        self.device_id = uuid.uuid4().hex[:12]
        self.registry = Registry(os.path.join(app_dir, 'sharing_registry.json'))
        self.cache = C.IndexCache(os.path.join(app_dir, 'sharing_index_cache.json'))
        self.received = os.path.join(app_dir, 'الملفات المستلمة')
        self.server = None
        self.discovery = None

    # -- دورة الحياة --
    def start(self):
        self.server = FileShareServer(self.registry, port=0)
        self.server.start()
        self.discovery = Discovery(self.device_id, self.name_getter, self.server.port)
        self.discovery.start()

    def stop(self):
        if self.discovery:
            self.discovery.stop()
        if self.server:
            self.server.stop()

    # -- ملفاتي المشاركة --
    def share(self, path):
        return self.registry.add(path)

    def unshare(self, fid):
        self.registry.remove(fid)

    def resolve_missing(self, fid, new_path):
        self.registry.resolve_missing(fid, new_path)

    def my_files(self):
        return self.registry.list()

    # -- المشتركة من الآخرين --
    def peers(self):
        return self.discovery.table.online() if self.discovery else []

    def refresh(self):
        """يستعلم عن فهرس كل قرين متصل ويحدّث الكاش."""
        for p in self.peers():
            try:
                files = C.fetch_index(p['ip'], p['port'])
                self.cache.put(p['id'], p['name'], files)
            except Exception:
                pass

    def incoming(self):
        """قائمة مسطّحة من كل الأقران (متصلين ومخزَّنين)، الأحدث أولاً."""
        online = {p['id']: p for p in self.peers()}
        rows = []
        for pid, entry in self.cache.all().items():
            p = online.get(pid)
            for f in entry.get('files', []):
                rows.append({
                    'peer_id': pid,
                    'peer_name': (p['name'] if p else entry.get('name', '')),
                    'peer_online': p is not None,
                    'peer_ip': p['ip'] if p else None,
                    'peer_port': p['port'] if p else None,
                    'id': f['id'], 'name': f['name'], 'type': f.get('type', ''),
                    'size': f.get('size', 0), 'shared_at': f.get('shared_at', 0),
                    'available': bool(p) and f.get('available', True),
                })
        return sorted(rows, key=lambda x: x['shared_at'], reverse=True)

    def download(self, row, progress=None):
        """ينزّل صفّاً من incoming(). يتطلب أن يكون القرين متصلاً."""
        if not row.get('peer_online'):
            raise ConnectionError('القرين غير متصل')
        return C.download(row['peer_ip'], row['peer_port'], row['id'],
                          row['name'], self.received, by=self.name_getter(),
                          progress=progress)
