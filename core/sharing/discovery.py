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
