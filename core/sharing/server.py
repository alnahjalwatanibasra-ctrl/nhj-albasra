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
