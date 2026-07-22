# خطة تنفيذ ميزة «مشاركة الملفات» — Nhj AL-Basra

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** إضافة ميزة مشاركة ملفات نِدّ-لِنِدّ على الشبكة المحلية داخل التطبيق (بديل واتساب)، بلا جهاز مركزي ولا تكلفة.

**Architecture:** كل تطبيق يشغّل خادم HTTP محلياً يقدّم ملفاته المشارَكة، ويعلن عن نفسه عبر بثّ UDP فيكتشف الأقران تلقائياً. المشاركة تسجّل **مسار** الملف فقط (لا نسخ)؛ البايتات تُجلب عند الطلب. المنطق النقي (السجل، الترميز، التسمية، الدمج) معزول في `core/sharing/` وقابل للاختبار، والشبكة/الخيوط طبقة رقيقة فوقه. الواجهة صفحة PySide6 جديدة.

**Tech Stack:** Python 3، مكتبة `socket`/`http.server`/`urllib` القياسية (بلا اعتماديات خارجية — مهم لتغليف PyInstaller)، PySide6، pytest.

**المرجع:** التصميم المعتمد في [docs/superpowers/specs/2026-07-22-file-sharing-design.md](../specs/2026-07-22-file-sharing-design.md).

---

## بنية الملفات

**كود المحرّك (`core/sharing/`) — منطق نقي قابل للاختبار:**
- `core/sharing/__init__.py` — حزمة.
- `core/sharing/registry.py` — سجل ملفاتي المشاركة (add/remove/list/resolve_missing/mark_downloaded + index للأقران).
- `core/sharing/discovery.py` — ترميز/فكّ حزمة الإعلان + جدول الأقران + خيط البثّ/الاستماع.
- `core/sharing/server.py` — توجيه الطلبات (Router نقي) + خادم HTTP رقيق فوقه.
- `core/sharing/client.py` — جلب الفهرس، التنزيل، تفادي الطمس (unique_path)، تخزين آخر فهرس.
- `core/sharing/service.py` — منسّق يربط الثلاثة، واجهة بسيطة للواجهة الرسومية.

**الواجهة (`ui/`):**
- `ui/sharing_page.py` — صفحة المساحة (تبويبان + سحب/إفلات + صفوف + إجراءات).
- `ui/sharing_worker.py` — عمّال QThread لتحديث الفهرس والتنزيل (حتى لا تتجمّد الواجهة).
- تعديل `ui/home_page.py` — بطاقة ثالثة «مشاركة الملفات».
- تعديل `ui/main_window.py` — ربط الصفحة الجديدة وتشغيل/إيقاف الخدمة.
- تعديل `ui/dialogs/settings_dialog.py` — حقل «اسمك» + إعادة هيكلة الإعدادات المتقدمة.
- تعديل `core/config.py` — `device_name` + مسارات المشاركة.
- تعديل `core/version.py` + `RELEASE_NOTES.txt` — الإصدار 4.0 (في مهمة النشر).

**الاختبارات (`tests/`):** ملف اختبار لكل وحدة محرّك + اختبارات بناء الصفحات (نمط `test_app_builds`).

---

## Task 1: حزمة `core/sharing` وإعدادات المسارات

**Files:**
- Create: `core/sharing/__init__.py`
- Modify: `core/config.py`
- Test: `tests/test_sharing_config.py`

- [ ] **Step 1: أنشئ ملف الحزمة الفارغ**

Create `core/sharing/__init__.py`:

```python
# -*- coding: utf-8 -*-
"""ميزة مشاركة الملفات نِدّ-لِنِدّ على الشبكة المحلية."""
```

- [ ] **Step 2: اكتب اختبار مسارات المشاركة (يفشل)**

Create `tests/test_sharing_config.py`:

```python
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
```

- [ ] **Step 3: شغّل الاختبار وتأكد أنه يفشل**

Run: `python -m pytest tests/test_sharing_config.py -v`
Expected: FAIL (`AttributeError: module 'core.config' has no attribute 'device_name'`)

- [ ] **Step 4: أضف الإعداد والدوال**

In `core/config.py`, add `"device_name": ""` inside `DEFAULTS` (after `"gemini_key": "",`). Then add at end of file:

```python
def device_name(settings=None):
    """اسم الجهاز الظاهر للأقران عند المشاركة؛ الافتراضي = اسم حاسوب ويندوز."""
    settings = settings if settings is not None else load_settings()
    name = (settings.get('device_name') or '').strip()
    if name:
        return name
    import socket
    return socket.gethostname() or 'مستخدم'


def received_dir():
    """مجلد الملفات المستلمة (يُنشأ إن لم يوجد)."""
    d = os.path.join(APP_DIR, 'الملفات المستلمة')
    os.makedirs(d, exist_ok=True)
    return d


def sharing_registry_path():
    return os.path.join(APP_DIR, 'sharing_registry.json')


def sharing_index_cache_path():
    return os.path.join(APP_DIR, 'sharing_index_cache.json')
```

- [ ] **Step 5: شغّل الاختبار وتأكد أنه ينجح**

Run: `python -m pytest tests/test_sharing_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add core/sharing/__init__.py core/config.py tests/test_sharing_config.py
git commit -m "feat(sharing): حزمة المشاركة + إعدادات اسم الجهاز ومساراتها"
```

---

## Task 2: سجل الملفات المشارَكة (`registry.py`)

**Files:**
- Create: `core/sharing/registry.py`
- Test: `tests/test_sharing_registry.py`

- [ ] **Step 1: اكتب الاختبارات (تفشل)**

Create `tests/test_sharing_registry.py`:

```python
# -*- coding: utf-8 -*-
import os
from core.sharing.registry import Registry


def _make_file(tmp_path, name='doc.xlsx', data=b'hello'):
    p = tmp_path / name
    p.write_bytes(data)
    return str(p)


def test_add_creates_entry_with_metadata(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    f = _make_file(tmp_path)
    fid = reg.add(f)
    items = reg.list()
    assert len(items) == 1
    it = items[0]
    assert it['id'] == fid
    assert it['name'] == 'doc.xlsx'
    assert it['type'] == 'xlsx'
    assert it['size'] == 5
    assert it['downloaded_by'] == []


def test_add_persists_across_instances(tmp_path):
    path = str(tmp_path / 'reg.json')
    fid = Registry(path).add(_make_file(tmp_path))
    reg2 = Registry(path)
    assert reg2.path_of(fid).endswith('doc.xlsx')


def test_remove_deletes_entry(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    fid = reg.add(_make_file(tmp_path))
    reg.remove(fid)
    assert reg.list() == []


def test_list_sorted_newest_first(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    a = reg.add(_make_file(tmp_path, 'a.txt'))
    reg.items[a]['shared_at'] = 100
    b = reg.add(_make_file(tmp_path, 'b.txt'))
    reg.items[b]['shared_at'] = 200
    assert [x['id'] for x in reg.list()] == [b, a]


def test_index_reports_availability(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    f = _make_file(tmp_path)
    fid = reg.add(f)
    assert reg.index()[0]['available'] is True
    os.remove(f)
    assert reg.index()[0]['available'] is False
    # الفهرس لا يسرّب المسار المحلي
    assert 'path' not in reg.index()[0]


def test_resolve_missing_updates_path(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    fid = reg.add(_make_file(tmp_path, 'a.txt'))
    newp = _make_file(tmp_path, 'moved.txt', b'xx')
    reg.resolve_missing(fid, newp)
    assert reg.path_of(fid).endswith('moved.txt')
    assert reg.list()[0]['name'] == 'moved.txt'


def test_mark_downloaded_records_unique_names(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    fid = reg.add(_make_file(tmp_path))
    reg.mark_downloaded(fid, 'مكتب ب')
    reg.mark_downloaded(fid, 'مكتب ب')  # مكرر يُتجاهل
    assert reg.list()[0]['downloaded_by'] == ['مكتب ب']
```

- [ ] **Step 2: شغّل الاختبارات وتأكد أنها تفشل**

Run: `python -m pytest tests/test_sharing_registry.py -v`
Expected: FAIL (`ModuleNotFoundError: core.sharing.registry`)

- [ ] **Step 3: نفّذ `registry.py`**

Create `core/sharing/registry.py`:

```python
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
```

- [ ] **Step 4: شغّل الاختبارات وتأكد أنها تنجح**

Run: `python -m pytest tests/test_sharing_registry.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add core/sharing/registry.py tests/test_sharing_registry.py
git commit -m "feat(sharing): سجل الملفات المشارَكة (مسار فقط + فهرس التوفّر)"
```

---

## Task 3: التعارف التلقائي (`discovery.py`)

**Files:**
- Create: `core/sharing/discovery.py`
- Test: `tests/test_sharing_discovery.py`

- [ ] **Step 1: اكتب اختبارات الترميز وجدول الأقران (تفشل)**

Create `tests/test_sharing_discovery.py`:

```python
# -*- coding: utf-8 -*-
from core.sharing import discovery as D


def test_beacon_roundtrip():
    data = D.encode_beacon('dev1', 'مكتب أ', 48712)
    d = D.decode_beacon(data)
    assert d['id'] == 'dev1' and d['name'] == 'مكتب أ' and d['port'] == 48712


def test_decode_rejects_foreign_packet():
    assert D.decode_beacon(b'random junk') is None
    assert D.decode_beacon(b'{"magic":"OTHER","id":"x","port":1}') is None


def test_peer_table_marks_offline_after_timeout():
    t = D.PeerTable(timeout=10)
    t.update('dev1', 'مكتب أ', '192.168.1.5', 48712, now=100)
    assert len(t.online(now=105)) == 1
    assert len(t.online(now=120)) == 0     # تجاوز المهلة


def test_peer_table_update_refreshes_last_seen():
    t = D.PeerTable(timeout=10)
    t.update('dev1', 'مكتب أ', '192.168.1.5', 48712, now=100)
    t.update('dev1', 'مكتب أ', '192.168.1.5', 48712, now=118)
    assert len(t.online(now=120)) == 1     # حُدّث فبقي متصلاً
```

- [ ] **Step 2: شغّل الاختبارات وتأكد أنها تفشل**

Run: `python -m pytest tests/test_sharing_discovery.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: نفّذ `discovery.py`**

Create `core/sharing/discovery.py`:

```python
# -*- coding: utf-8 -*-
"""التعارف التلقائي عبر بثّ UDP على الشبكة المحلية. بلا مكتبات خارجية."""
import json, socket, threading, time

MAGIC = 'NHJ-BASRA-SHARE-1'
BROADCAST_PORT = 48711
BEACON_INTERVAL = 3.0
PEER_TIMEOUT = 10.0


def encode_beacon(device_id, name, http_port):
    return json.dumps({'magic': MAGIC, 'id': device_id,
                       'name': name, 'port': int(http_port)}).encode('utf-8')


def decode_beacon(data):
    try:
        d = json.loads(data.decode('utf-8'))
    except Exception:
        return None
    if d.get('magic') != MAGIC or not d.get('id') or not d.get('port'):
        return None
    return d


class PeerTable:
    def __init__(self, timeout=PEER_TIMEOUT):
        self.timeout = timeout
        self.peers = {}          # id -> {id,name,ip,port,last_seen}

    def update(self, pid, name, ip, port, now=None):
        now = time.time() if now is None else now
        self.peers[pid] = {'id': pid, 'name': name, 'ip': ip,
                           'port': int(port), 'last_seen': now}

    def online(self, now=None):
        now = time.time() if now is None else now
        return [p for p in self.peers.values()
                if now - p['last_seen'] <= self.timeout]


class Discovery(threading.Thread):
    """يبثّ إعلاناً دورياً ويستمع لإعلانات الأقران على الشبكة المحلية."""
    daemon = True

    def __init__(self, device_id, name_getter, http_port,
                 port=BROADCAST_PORT, self_ids=None):
        super().__init__()
        self.device_id = device_id
        self.name_getter = name_getter      # دالة ترجع الاسم الحالي
        self.http_port = http_port
        self.port = port
        self.table = PeerTable()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        try:
            rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            rx.bind(('', self.port))
            rx.settimeout(0.5)
        except OSError:
            return
        tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        last_beacon = 0.0
        while not self._stop.is_set():
            now = time.time()
            if now - last_beacon >= BEACON_INTERVAL:
                try:
                    pkt = encode_beacon(self.device_id, self.name_getter(), self.http_port)
                    tx.sendto(pkt, ('255.255.255.255', self.port))
                except OSError:
                    pass
                last_beacon = now
            try:
                data, addr = rx.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            d = decode_beacon(data)
            if d and d['id'] != self.device_id:   # نتجاهل إعلان أنفسنا
                self.table.update(d['id'], d.get('name', ''), addr[0], d['port'])
        rx.close(); tx.close()
```

- [ ] **Step 4: شغّل الاختبارات وتأكد أنها تنجح**

Run: `python -m pytest tests/test_sharing_discovery.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add core/sharing/discovery.py tests/test_sharing_discovery.py
git commit -m "feat(sharing): تعارف تلقائي عبر بثّ UDP + جدول الأقران"
```

---

## Task 4: خادم الملفات (`server.py`)

**Files:**
- Create: `core/sharing/server.py`
- Test: `tests/test_sharing_server.py`

- [ ] **Step 1: اكتب اختبارات التوجيه (تفشل)**

Create `tests/test_sharing_server.py`:

```python
# -*- coding: utf-8 -*-
import json, os
from core.sharing.registry import Registry
from core.sharing.server import route


def _reg(tmp_path):
    reg = Registry(str(tmp_path / 'reg.json'))
    f = tmp_path / 'doc.xlsx'; f.write_bytes(b'hello')
    fid = reg.add(str(f))
    return reg, fid


def test_ping_ok(tmp_path):
    reg, _ = _reg(tmp_path)
    status, ctype, body = route(reg, '/ping', {})
    assert status == 200


def test_index_returns_files(tmp_path):
    reg, fid = _reg(tmp_path)
    status, ctype, body = route(reg, '/index', {})
    assert status == 200
    data = json.loads(body.decode('utf-8'))
    assert data['files'][0]['id'] == fid
    assert 'path' not in data['files'][0]


def test_file_returns_path_and_marks_downloaded(tmp_path):
    reg, fid = _reg(tmp_path)
    status, ctype, body = route(reg, '/file/' + fid, {'by': ['مكتب ب']})
    assert status == 200
    assert body[0] == 'FILE' and body[1].endswith('doc.xlsx')
    assert reg.list()[0]['downloaded_by'] == ['مكتب ب']


def test_unknown_id_is_404(tmp_path):
    reg, _ = _reg(tmp_path)
    status, _, _ = route(reg, '/file/deadbeef', {})
    assert status == 404


def test_path_traversal_blocked(tmp_path):
    reg, _ = _reg(tmp_path)
    # معرّف غير موجود مهما كان شكله ⟵ 404 (الوصول بالمعرّف لا بالمسار)
    status, _, _ = route(reg, '/file/..%2f..%2fsecret', {})
    assert status == 404


def test_missing_original_is_404(tmp_path):
    reg, fid = _reg(tmp_path)
    os.remove(reg.path_of(fid))
    status, _, _ = route(reg, '/file/' + fid, {})
    assert status == 404
```

- [ ] **Step 2: شغّل الاختبارات وتأكد أنها تفشل**

Run: `python -m pytest tests/test_sharing_server.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: نفّذ `server.py`**

Create `core/sharing/server.py`:

```python
# -*- coding: utf-8 -*-
"""خادم HTTP محلي يقدّم ملفات هذا الجهاز المشارَكة. الوصول بالمعرّف لا بالمسار
(يمنع اجتياز المسارات). التوجيه دالة نقية `route` قابلة للاختبار."""
import json, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs


def route(registry, path, query):
    """يرجع (status, content_type, body). body للملف = ('FILE', abs_path)."""
    if path == '/ping':
        return 200, 'application/json', b'{"ok":true}'
    if path == '/index':
        body = json.dumps({'files': registry.index()},
                          ensure_ascii=False).encode('utf-8')
        return 200, 'application/json; charset=utf-8', body
    if path.startswith('/file/'):
        fid = path[len('/file/'):]
        fpath = registry.path_of(fid)
        if not fpath or not os.path.exists(fpath):
            return 404, 'text/plain', b'not found'
        by = (query.get('by') or [''])[0]
        registry.mark_downloaded(fid, by)
        return 200, 'application/octet-stream', ('FILE', fpath)
    return 404, 'text/plain', b'not found'


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):          # صمت
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        status, ctype, body = route(self.server.registry,
                                    parsed.path, parse_qs(parsed.query))
        if isinstance(body, tuple) and body and body[0] == 'FILE':
            fpath = body[1]
            try:
                size = os.path.getsize(fpath)
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(size))
                self.end_headers()
                with open(fpath, 'rb') as fh:
                    while True:
                        chunk = fh.read(64 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (OSError, BrokenPipeError, ConnectionResetError):
                pass
            return
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


class FileShareServer:
    """خادم في خيط منفصل، يختار منفذاً حرّاً تلقائياً (port=0)."""
    def __init__(self, registry, port=0):
        self.registry = registry
        self._httpd = ThreadingHTTPServer(('0.0.0.0', port), _Handler)
        self._httpd.registry = registry
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._httpd.shutdown()
        self._httpd.server_close()
```

- [ ] **Step 4: شغّل الاختبارات وتأكد أنها تنجح**

Run: `python -m pytest tests/test_sharing_server.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add core/sharing/server.py tests/test_sharing_server.py
git commit -m "feat(sharing): خادم HTTP محلي (index/file/ping) بتوجيه نقي مختبَر"
```

---

## Task 5: عميل الجلب والتنزيل (`client.py`)

**Files:**
- Create: `core/sharing/client.py`
- Test: `tests/test_sharing_client.py`

- [ ] **Step 1: اكتب الاختبارات (تفشل)**

Create `tests/test_sharing_client.py`:

```python
# -*- coding: utf-8 -*-
import os
from core.sharing.registry import Registry
from core.sharing.server import FileShareServer
from core.sharing import client as C


def test_unique_path_avoids_overwrite(tmp_path):
    (tmp_path / 'a.txt').write_text('x')
    p2 = C.unique_path(str(tmp_path), 'a.txt')
    assert p2.endswith('a (٢).txt')
    (tmp_path / 'a (٢).txt').write_text('y')
    p3 = C.unique_path(str(tmp_path), 'a.txt')
    assert p3.endswith('a (٣).txt')


def test_index_cache_roundtrip(tmp_path):
    cache = C.IndexCache(str(tmp_path / 'cache.json'))
    cache.put('dev1', 'مكتب أ', [{'id': 'f1', 'name': 'x.txt'}])
    cache2 = C.IndexCache(str(tmp_path / 'cache.json'))
    entry = cache2.get('dev1')
    assert entry['name'] == 'مكتب أ'
    assert entry['files'][0]['id'] == 'f1'


def test_fetch_index_and_download_roundtrip(tmp_path):
    # خادم حقيقي على localhost
    reg = Registry(str(tmp_path / 'reg.json'))
    src = tmp_path / 'report.xlsx'; src.write_bytes(b'CONTENT-123')
    fid = reg.add(str(src))
    srv = FileShareServer(reg, port=0); srv.start()
    try:
        files = C.fetch_index('127.0.0.1', srv.port)
        assert files[0]['id'] == fid
        dest = tmp_path / 'in'; dest.mkdir()
        saved = C.download('127.0.0.1', srv.port, fid, 'report.xlsx',
                           str(dest), by='مكتب ب')
        assert open(saved, 'rb').read() == b'CONTENT-123'
        assert reg.list()[0]['downloaded_by'] == ['مكتب ب']
    finally:
        srv.stop()
```

- [ ] **Step 2: شغّل الاختبارات وتأكد أنها تفشل**

Run: `python -m pytest tests/test_sharing_client.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: نفّذ `client.py`**

Create `core/sharing/client.py`:

```python
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
```

- [ ] **Step 4: شغّل الاختبارات وتأكد أنها تنجح**

Run: `python -m pytest tests/test_sharing_client.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add core/sharing/client.py tests/test_sharing_client.py
git commit -m "feat(sharing): عميل الجلب والتنزيل + تفادي الطمس + تخزين الفهرس"
```

---

## Task 6: المنسّق (`service.py`)

**Files:**
- Create: `core/sharing/service.py`
- Test: `tests/test_sharing_service.py`

- [ ] **Step 1: اكتب الاختبارات (تفشل)**

Create `tests/test_sharing_service.py`:

```python
# -*- coding: utf-8 -*-
from core.sharing.service import ShareService


def test_share_and_list_my_files(tmp_path):
    f = tmp_path / 'a.xlsx'; f.write_bytes(b'x')
    svc = ShareService(str(tmp_path), lambda: 'مكتب أ')
    fid = svc.share(str(f))
    assert svc.my_files()[0]['id'] == fid
    svc.unshare(fid)
    assert svc.my_files() == []


def test_incoming_merges_cache_and_marks_offline(tmp_path):
    svc = ShareService(str(tmp_path), lambda: 'مكتب أ')
    # نحقن فهرساً مخزَّناً لقرين غير متصل الآن
    svc.cache.put('devX', 'مكتب ب',
                  [{'id': 'f1', 'name': 'تقرير.xlsx', 'type': 'xlsx',
                    'size': 3, 'shared_at': 1.0, 'available': True}])
    rows = svc.incoming()
    assert len(rows) == 1
    assert rows[0]['peer_name'] == 'مكتب ب'
    assert rows[0]['peer_online'] is False        # لا يوجد قرين حيّ
    assert rows[0]['name'] == 'تقرير.xlsx'


def test_two_services_discover_and_download(tmp_path):
    import time
    a_dir = tmp_path / 'A'; a_dir.mkdir()
    b_dir = tmp_path / 'B'; b_dir.mkdir()
    src = a_dir / 'report.xlsx'; src.write_bytes(b'HELLO-P2P')
    a = ShareService(str(a_dir), lambda: 'مكتب أ'); a.start()
    b = ShareService(str(b_dir), lambda: 'مكتب ب'); b.start()
    try:
        a.share(str(src))
        # ننتظر التعارف والفهرسة
        deadline = time.time() + 8
        while time.time() < deadline and not b.incoming():
            b.refresh(); time.sleep(0.5)
        rows = b.incoming()
        assert any(r['name'] == 'report.xlsx' for r in rows)
        row = [r for r in rows if r['name'] == 'report.xlsx'][0]
        saved = b.download(row)
        assert open(saved, 'rb').read() == b'HELLO-P2P'
    finally:
        a.stop(); b.stop()
```

> **ملاحظة للمنفّذ:** اختبار `test_two_services_discover_and_download` يعتمد على بثّ UDP على localhost وقد يكون بطيئاً أو محجوباً في بيئات CI المعزولة. إن فشل بسبب البيئة (لا بسبب الكود)، ضع عليه `@pytest.mark.skipif` عند غياب البثّ، لكن **يجب أن ينجح على جهاز ويندوز حقيقي**.

- [ ] **Step 2: شغّل الاختبارات وتأكد أنها تفشل**

Run: `python -m pytest tests/test_sharing_service.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: نفّذ `service.py`**

Create `core/sharing/service.py`:

```python
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
```

- [ ] **Step 4: شغّل الاختبارات وتأكد أنها تنجح**

Run: `python -m pytest tests/test_sharing_service.py -v`
Expected: PASS (3 passed) — قد يأخذ اختبار التعارف عدة ثوانٍ.

- [ ] **Step 5: Commit**

```bash
git add core/sharing/service.py tests/test_sharing_service.py
git commit -m "feat(sharing): منسّق الخدمة (تعارف+خادم+تنزيل) بواجهة موحّدة"
```

---

## Task 7: عمّال الواجهة (`sharing_worker.py`)

**Files:**
- Create: `ui/sharing_worker.py`
- Test: `tests/test_sharing_worker.py`

- [ ] **Step 1: اكتب اختبار البناء (يفشل)**

Create `tests/test_sharing_worker.py`:

```python
# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.sharing_worker import DownloadWorker, RefreshWorker


def test_workers_construct():
    create_app([])
    rw = RefreshWorker(service=None)
    assert rw is not None
    dw = DownloadWorker(service=None, row={'name': 'x'})
    assert dw.row['name'] == 'x'
```

- [ ] **Step 2: شغّل الاختبار وتأكد أنه يفشل**

Run: `python -m pytest tests/test_sharing_worker.py -v`
Expected: FAIL (`ModuleNotFoundError: ui.sharing_worker`)

- [ ] **Step 3: نفّذ `sharing_worker.py`**

Create `ui/sharing_worker.py`:

```python
# -*- coding: utf-8 -*-
"""عمّال QThread للمشاركة: تحديث الفهرس والتنزيل بلا تجميد الواجهة."""
from PySide6.QtCore import QThread, Signal


class RefreshWorker(QThread):
    done = Signal()

    def __init__(self, service):
        super().__init__()
        self.service = service

    def run(self):
        try:
            self.service.refresh()
        except Exception:
            pass
        self.done.emit()


class DownloadWorker(QThread):
    progressed = Signal(int, int)      # (done, total)
    finished_ok = Signal(str)          # المسار المحفوظ
    failed = Signal(str)

    def __init__(self, service, row):
        super().__init__()
        self.service = service
        self.row = row

    def run(self):
        try:
            saved = self.service.download(
                self.row, progress=lambda d, t: self.progressed.emit(d, t))
            self.finished_ok.emit(saved)
        except Exception as e:
            self.failed.emit(type(e).__name__)
```

- [ ] **Step 4: شغّل الاختبار وتأكد أنه ينجح**

Run: `python -m pytest tests/test_sharing_worker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/sharing_worker.py tests/test_sharing_worker.py
git commit -m "feat(sharing): عمّال QThread لتحديث الفهرس والتنزيل"
```

---

## Task 8: صفحة المشاركة (`sharing_page.py`)

**Files:**
- Create: `ui/sharing_page.py`
- Test: `tests/test_sharing_page.py`

- [ ] **Step 1: اكتب اختبار البناء والمشاركة (يفشل)**

Create `tests/test_sharing_page.py`:

```python
# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.sharing_page import SharingPage
from core.sharing.service import ShareService


def test_page_builds_and_shares(tmp_path):
    create_app([])
    f = tmp_path / 'a.xlsx'; f.write_bytes(b'x')
    svc = ShareService(str(tmp_path), lambda: 'مكتب أ')
    page = SharingPage(svc)
    page.add_files([str(f)])
    # ظهر في تبويب «ملفاتي المشاركة»
    assert svc.my_files()[0]['name'] == 'a.xlsx'
    assert page.mine_list.count() == 1
```

- [ ] **Step 2: شغّل الاختبار وتأكد أنه يفشل**

Run: `python -m pytest tests/test_sharing_page.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: نفّذ `sharing_page.py`**

Create `ui/sharing_page.py`:

```python
# -*- coding: utf-8 -*-
"""صفحة «مشاركة الملفات»: تبويبان (الوارد/الصادر مني) + منطقة سحب وإفلات.
تعتمد على ShareService (P2P على الشبكة المحلية)."""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QTabWidget, QListWidget, QListWidgetItem, QFileDialog,
                               QMessageBox, QFrame, QProgressDialog)
from PySide6.QtCore import Qt, QTimer
from .start_page import DropList
from .sharing_worker import RefreshWorker, DownloadWorker

_ICONS = {'xlsx': '📊', 'xls': '📊', 'docx': '📝', 'doc': '📝', 'pdf': '📕',
          'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️'}


def _icon(t):
    return _ICONS.get((t or '').lower(), '📄')


class SharingPage(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        v = QVBoxLayout(self); v.setContentsMargins(28, 18, 28, 14); v.setSpacing(10)

        hint = QLabel('شارك الملفات مباشرةً مع أجهزة المكتب على نفس الشبكة. '
                      'أول مرة قد يسألك ويندوز عن السماح بالاتصال — اضغط «سماح».')
        hint.setWordWrap(True); hint.setStyleSheet('color:#7d8587')
        v.addWidget(hint)

        # منطقة السحب والإفلات للمشاركة
        card = QFrame(); card.setProperty('class', 'card')
        c = QVBoxLayout(card)
        self.drop = DropList()
        self.drop.setFixedHeight(90)
        self.drop.filesDropped.connect(self.add_files)
        c.addWidget(QLabel('اسحب ملفات هنا لمشاركتها (يمكن عدّة ملفات معاً):'))
        row = QHBoxLayout()
        b_pick = QPushButton('اختيار ملفات...'); b_pick.setObjectName('ghost')
        b_pick.clicked.connect(self._pick)
        row.addWidget(self.drop, 1)
        c.addLayout(row); c.addWidget(b_pick)
        v.addWidget(card)

        self.tabs = QTabWidget()
        self.incoming_list = QListWidget()
        self.incoming_list.itemDoubleClicked.connect(self._download_selected)
        self.mine_list = QListWidget()
        self.tabs.addTab(self.incoming_list, 'المشتركة من الآخرين')
        self.tabs.addTab(self.mine_list, 'ملفاتي المشاركة')
        v.addWidget(self.tabs, 1)

        bar = QHBoxLayout()
        b_dl = QPushButton('تنزيل المحدد'); b_dl.setObjectName('primary')
        b_dl.clicked.connect(self._download_selected)
        b_open = QPushButton('فتح مجلد المستلمات'); b_open.setObjectName('ghost')
        b_open.clicked.connect(lambda: os.startfile(self.service.received)
                               if os.path.isdir(self.service.received) else None)
        b_rm = QPushButton('إزالة من المشاركة'); b_rm.setObjectName('danger')
        b_rm.clicked.connect(self._remove_mine)
        bar.addWidget(b_dl); bar.addWidget(b_open); bar.addStretch(1); bar.addWidget(b_rm)
        v.addLayout(bar)

        self._timer = QTimer(self); self._timer.setInterval(4000)
        self._timer.timeout.connect(self._refresh_incoming)
        self._timer.start()
        self.refresh()

    # -- المشاركة --
    def add_files(self, paths):
        for p in paths:
            if p and os.path.isfile(p):
                self.service.share(p)
        self.refresh()

    def _pick(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'اختر ملفات للمشاركة', '', 'كل الملفات (*.*)')
        self.add_files(paths)

    def _remove_mine(self):
        it = self.mine_list.currentItem()
        if not it:
            return
        fid = it.data(Qt.UserRole)
        if QMessageBox.question(self, 'إزالة',
                                'إزالة هذا الملف من المشاركة؟ (لن يُحذف الأصل من جهازك)'
                                ) == QMessageBox.StandardButton.Yes:
            self.service.unshare(fid)
            self.refresh()

    # -- التنزيل --
    def _download_selected(self, *args):
        it = self.incoming_list.currentItem()
        if not it:
            return
        row = it.data(Qt.UserRole)
        if not row.get('peer_online') or not row.get('available'):
            QMessageBox.information(self, 'غير متاح',
                                    'هذا الملف غير متاح الآن (جهاز صاحبه مطفأ). حاول لاحقاً.')
            return
        dlg = QProgressDialog('جاري التنزيل...', 'إلغاء', 0, 100, self)
        dlg.setWindowModality(Qt.WindowModal)
        self._dw = DownloadWorker(self.service, row)
        self._dw.progressed.connect(
            lambda d, t: dlg.setValue(int(d * 100 / t)) if t else None)
        self._dw.finished_ok.connect(lambda p: (dlg.close(), self._downloaded(p)))
        self._dw.failed.connect(lambda e: (dlg.close(), QMessageBox.warning(
            self, 'تعذّر التنزيل', 'انقطع الاتصال، حاول لاحقاً.')))
        self._dw.start()

    def _downloaded(self, path):
        box = QMessageBox(self); box.setWindowTitle('اكتمل التنزيل')
        box.setText(f'تم حفظ «{os.path.basename(path)}».')
        b_open = box.addButton('فتح', QMessageBox.ButtonRole.AcceptRole)
        box.addButton('إغلاق', QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is b_open:
            os.startfile(path)

    # -- التحديث --
    def _refresh_incoming(self):
        if self.service.peers():
            self._rw = RefreshWorker(self.service)
            self._rw.done.connect(self.refresh)
            self._rw.start()
        else:
            self.refresh()

    def refresh(self):
        # الوارد
        cur = self.incoming_list.currentRow()
        self.incoming_list.clear()
        for r in self.service.incoming():
            if r['peer_online'] and r['available']:
                state = 'متاح'
            elif not r['peer_online']:
                state = 'غير متاح الآن'
            else:
                state = 'الأصل مفقود عند صاحبه'
            it = QListWidgetItem(
                f"{_icon(r['type'])}  {r['name']}   —   من: {r['peer_name']}   [{state}]")
            it.setData(Qt.UserRole, r)
            self.incoming_list.addItem(it)
        self.incoming_list.setCurrentRow(cur)
        # ملفاتي
        self.mine_list.clear()
        for f in self.service.my_files():
            avail = os.path.exists(f['path'])
            dl = f.get('downloaded_by') or []
            note = '' if avail else '  ⚠️ الأصل مفقود'
            recv = f'   ✔ نزّله: {"، ".join(dl)}' if dl else ''
            it = QListWidgetItem(f"{_icon(f['type'])}  {f['name']}{recv}{note}")
            it.setData(Qt.UserRole, f['id'])
            self.mine_list.addItem(it)
```

- [ ] **Step 4: شغّل الاختبار وتأكد أنه ينجح**

Run: `python -m pytest tests/test_sharing_page.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/sharing_page.py tests/test_sharing_page.py
git commit -m "feat(sharing): صفحة المشاركة (تبويبان + سحب/إفلات + تنزيل + إشعار استلام)"
```

---

## Task 9: بطاقة الصفحة الرئيسية وربط النافذة

**Files:**
- Modify: `ui/home_page.py`
- Modify: `ui/main_window.py`
- Test: `tests/test_sharing_integration.py`

- [ ] **Step 1: اكتب اختبار التكامل (يفشل)**

Create `tests/test_sharing_integration.py`:

```python
# -*- coding: utf-8 -*-
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from ui.app import create_app
from ui.main_window import MainWindow


def test_home_has_sharing_card_and_opens(qtbot=None):
    create_app([])
    w = MainWindow()
    assert hasattr(w.home_page, 'card_share')
    # فتح الميزة يبدّل الصفحة إلى صفحة المشاركة
    w._open_feature('share')
    assert w.stack.currentWidget() is w.sharing_page
    w.close()
```

- [ ] **Step 2: شغّل الاختبار وتأكد أنه يفشل**

Run: `python -m pytest tests/test_sharing_integration.py -v`
Expected: FAIL (`AttributeError: 'HomePage' object has no attribute 'card_share'`)

- [ ] **Step 3: أضف البطاقة في `home_page.py`**

In `ui/home_page.py`, change the signal comment and add a third card. Replace the block from `row = QHBoxLayout()` through `v.addLayout(row)` (lines ~98-104) with:

```python
        row = QHBoxLayout(); row.setSpacing(34); row.setAlignment(Qt.AlignCenter)
        self.card_sadir = FeatureCard('ic_sadir.png', 'سجل الصادر')
        self.card_text = FeatureCard('ic_text.png', 'استخراج النصوص')
        self.card_share = FeatureCard('ic_share.png', 'مشاركة الملفات')
        self.card_sadir.clicked.connect(lambda: self.featureRequested.emit('sadir'))
        self.card_text.clicked.connect(lambda: self.featureRequested.emit('text'))
        self.card_share.clicked.connect(lambda: self.featureRequested.emit('share'))
        row.addWidget(self.card_sadir); row.addWidget(self.card_text)
        row.addWidget(self.card_share)
        v.addLayout(row)
```

> **ملاحظة أيقونة:** إن لم توجد `assets/ic_share.png` فالبطاقة تظهر بلا صورة (الكود يتحمّل `QPixmap` الفارغ). أضف أيقونة لاحقاً بنفس نمط `ic_sadir.png`/`ic_text.png` (٦٠px، بهوية النهج). هذا لا يعطّل البناء.

- [ ] **Step 4: اربط الصفحة في `main_window.py`**

In `ui/main_window.py` `_build_pages`, after `self.text_page = TextPage()` add:

```python
        from .sharing_page import SharingPage
        from core.sharing.service import ShareService
        from core import config
        self.share_service = ShareService(config.APP_DIR,
                                          lambda: config.device_name(self.settings))
        try:
            self.share_service.start()
        except Exception:
            pass
        self.sharing_page = SharingPage(self.share_service)
```

Then after `self.stack.addWidget(self.text_page)` add:

```python
        self.stack.addWidget(self.sharing_page)
```

Change `_open_feature` to:

```python
    def _open_feature(self, name):
        page = {'sadir': self.start_page, 'text': self.text_page,
                'share': self.sharing_page}.get(name, self.start_page)
        self.stack.setCurrentWidget(page)
```

Add service shutdown in `closeEvent` (at the start of the method, before the existing logic):

```python
        if getattr(self, 'share_service', None):
            self.share_service.stop()
```

- [ ] **Step 5: شغّل الاختبار وتأكد أنه ينجح**

Run: `python -m pytest tests/test_sharing_integration.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add ui/home_page.py ui/main_window.py tests/test_sharing_integration.py
git commit -m "feat(sharing): بطاقة الرئيسية + ربط الخدمة بالنافذة"
```

---

## Task 10: حقل اسم الجهاز + إعادة هيكلة الإعدادات المتقدمة

**Files:**
- Modify: `ui/dialogs/settings_dialog.py`
- Test: `tests/test_settings_dialog.py` (إضافة)

- [ ] **Step 1: اكتب الاختبارات (تفشل)**

Append to `tests/test_settings_dialog.py`:

```python
def test_settings_has_device_name_field():
    app = create_app([])
    dlg = SettingsDialog({'device_name': 'مكتب أ', 'gemini_models': ['m1'],
                          'vocab_in_prompt': True, 'subject_replacements': {}})
    assert dlg.txt_device.text() == 'مكتب أ'


def test_advanced_hidden_until_revealed():
    app = create_app([])
    dlg = SettingsDialog({'gemini_models': ['m1'], 'vocab_in_prompt': True,
                          'subject_replacements': {}})
    assert dlg.adv.isVisible() is False
    dlg._reveal_advanced()
    assert dlg.adv.isVisible() is True
```

- [ ] **Step 2: شغّل الاختبارات وتأكد أنها تفشل**

Run: `python -m pytest tests/test_settings_dialog.py -v`
Expected: FAIL (`AttributeError: ... 'txt_device'`)

- [ ] **Step 3: عدّل `settings_dialog.py`**

Import `QLineEdit` is already imported. In `__init__`, inside the `g1` (عام) group after the check button (`v1.addWidget(b_check)`), add a device-name row:

```python
        r_dev = QHBoxLayout()
        r_dev.addWidget(QLabel('اسمك (يظهر لزملائك عند مشاركة ملف):'))
        self.txt_device = QLineEdit(settings.get('device_name', ''))
        self.txt_device.setPlaceholderText('اتركه فارغاً لاستخدام اسم الحاسوب')
        r_dev.addWidget(self.txt_device, 1)
        v1.addLayout(r_dev)
```

Replace the advanced group creation. Change:

```python
        self.g2 = QGroupBox('متقدم (لا تغيّره إلا إذا كنت تعرف ما تفعل)')
        self.g2.setCheckable(True); self.g2.setChecked(False)
        v2 = QVBoxLayout(self.g2)
```

to (a plain hidden container revealed by a button):

```python
        self.btn_reveal = QPushButton('⚙ إظهار الإعدادات المتقدمة')
        self.btn_reveal.setObjectName('ghost')
        self.btn_reveal.clicked.connect(self._reveal_advanced)
        v.addWidget(self.btn_reveal)

        self.adv = QGroupBox('متقدم (لا تغيّره إلا إذا كنت تعرف ما تفعل)')
        self.adv.setVisible(False)
        v2 = QVBoxLayout(self.adv)
```

Then change the two later references from `self.g2` to `self.adv`: the line `v.addWidget(self.g2)` becomes `v.addWidget(self.adv)`. Add the reveal method (e.g. after `_edit_replacements`):

```python
    def _reveal_advanced(self):
        self.adv.setVisible(True)
        self.btn_reveal.setVisible(False)
```

In `_save`, persist the device name — add before `config.save_settings(self.settings)`:

```python
        self.settings['device_name'] = self.txt_device.text().strip()
```

- [ ] **Step 4: شغّل كل اختبارات الإعدادات وتأكد أنها تنجح**

Run: `python -m pytest tests/test_settings_dialog.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add ui/dialogs/settings_dialog.py tests/test_settings_dialog.py
git commit -m "feat(sharing): حقل اسم الجهاز + كشف الإعدادات المتقدمة بزر بدل التعطيل"
```

---

## Task 11: التحقق الشامل

**Files:** لا ملفات جديدة — تشغيل وتحقق.

- [ ] **Step 1: كل الاختبارات تمرّ**

Run: `python -m pytest tests/ -v`
Expected: كل الاختبارات القديمة (٥٧) + الجديدة تمرّ. إن فشل اختبار التعارف بسبب حجب UDP في البيئة فقط، وثّقه.

- [ ] **Step 2: المحرّك القديم لم ينكسر**

Run: `python run_engine.py`
Expected: يبقى بدقّة 100% مقابل الذهبي (الميزة الجديدة معزولة).

- [ ] **Step 3: فحص يدوي حقيقي على جهازين (قائمة تحقق)**

نفّذ يدوياً وسجّل النتيجة:
1. افتح التطبيق على الجهازين على نفس الشبكة → صفحة «مشاركة الملفات» تُظهر الطرف الآخر خلال ثوانٍ.
2. اسحب ملف إكسل على الجهاز أ → يظهر في «المشتركة من الآخرين» على الجهاز ب.
3. اضغط عليه على ب → ينزّل ويُفتح؛ وعلى أ يظهر «✔ نزّله <اسم ب>».
4. اسحب عدّة ملفات دفعة واحدة → كلها تُشارك.
5. نزّل ملفاً باسم موجود → يُحفظ بلاحقة (٢) بلا طمس.
6. أطفئ التطبيق على أ → ملفاته تبقى ظاهرة على ب بوسم «غير متاح الآن».
7. أعد فتح ب بعد إغلاقه → القائمة تبقى (كاش) بوسم «غير متاح» حتى يعود أ.
8. احذف ملفاً من «ملفاتي المشاركة» على أ → يختفي من ب؛ والنسخة المنزَّلة على ب تبقى.
9. الإعدادات: اسم الجهاز يُحفظ ويظهر كصاحب الملف؛ زر «إظهار الإعدادات المتقدمة» يكشفها.

- [ ] **Step 4: Commit أي إصلاحات نتجت عن الفحص اليدوي**

```bash
git add -A
git commit -m "fix(sharing): إصلاحات الفحص اليدوي على جهازين"
```

---

## Task 12: النشر (الإصدار 4.0)

**Files:**
- Modify: `core/version.py`
- Modify: `RELEASE_NOTES.txt`

- [ ] **Step 1: ارفع رقم الإصدار**

In `core/version.py` change `VERSION = '3.7'` to `VERSION = '4.0'`.

- [ ] **Step 2: حدّث ملاحظات الإصدار**

Replace `RELEASE_NOTES.txt` content with:

```
الإصدار 4.0 — ميزة جديدة: مشاركة الملفات بين أجهزة المكتب على نفس الشبكة
مباشرةً من داخل التطبيق (بديل واتساب)، مع اسم لكل جهاز وإشعار استلام.
وتحسين: الإعدادات المتقدمة تُكشف بزر بدل ظهورها معطّلة.
```

- [ ] **Step 3: تأكد أن كل الاختبارات تمرّ قبل النشر**

Run: `python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 4: Commit + push + tag (النشر التلقائي)**

```bash
git add core/version.py RELEASE_NOTES.txt
git commit -m "release: الإصدار 4.0 — ميزة مشاركة الملفات"
git push origin main
git tag v4.0
git push origin v4.0
```

- [ ] **Step 5: تحقق من النشر التلقائي**

انتظر GitHub Actions حتى يكتمل، ثم اجلب المانيفست وتأكد أن الإصدار 4.0:
`https://github.com/alnahjalwatanibasra-ctrl/nhj-albasra/releases/latest/download/version.json`
Expected: `"version": "4.0"`.

---

## Self-Review (أُجريت)

- **تغطية المواصفة:** كل بنود التصميم ممثَّلة بمهمة — التعارف (T3)، الخادم/الفهرس/التوفّر (T2،T4)، التنزيل وتفادي الطمس وبقاء القائمة (T5)، إشعار الاستلام (T2،T4،T8)، التبويبان والسحب المتعدد والحذف (T8)، اسم الجهاز والإعدادات المتقدمة (T10)، الربط (T9)، النشر 4.0 (T12).
- **بلا عناصر نائبة:** كل خطوة تحوي كوداً كاملاً وأمراً وناتجاً متوقّعاً.
- **اتساق الأنواع:** `ShareService` تُستخدم بنفس التواقيع في T7/T8/T9؛ `route` ترجع `(status, ctype, body)` وتُختبر وتُستهلك بنفس الشكل؛ `incoming()`/`download(row)` متسقتان بين الخدمة والصفحة والعامل؛ مفاتيح الصفوف (`peer_online`, `available`, `id`, `name`, `type`, `peer_ip`, `peer_port`) موحّدة.
- **الأمان:** الوصول بالمعرّف لا بالمسار (يمنع الاجتياز، مُختبَر)، ترويسة سحرية للتعارف، لا انكشاف على الإنترنت.
