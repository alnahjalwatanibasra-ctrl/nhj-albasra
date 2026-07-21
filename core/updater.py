# -*- coding: utf-8 -*-
"""التحديث التلقائي عبر Google Drive:
version.json على درايف يحمل {version, url, notes} — التطبيق يقارن، ينزّل الـ exe الجديد،
ويستبدل نفسه بسكربت bat يعمل بعد إغلاقه ثم يعيد تشغيله."""
import json, os, re, sys, tempfile, subprocess, urllib.request


def parse_ver(s):
    """'1.4' ⟵ (1,4,0) — مقارنة أرقام آمنة."""
    nums = [int(x) for x in re.findall(r'\d+', str(s or ''))][:3]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


def gdrive_direct(url):
    """يحوّل رابط المشاركة إلى رابط تنزيل مباشر.
    روابط GitHub Releases مباشرة أصلاً فتمرّ كما هي؛ روابط درايف تُحوَّل."""
    url = str(url or '').strip()
    if 'github.com' in url or 'githubusercontent.com' in url:
        return url          # GitHub: رابط تنزيل نظيف مباشر
    m = (re.search(r'drive\.google\.com/file/d/([\w-]+)', url)
         or re.search(r'[?&]id=([\w-]+)', url))
    if m:
        return ('https://drive.usercontent.google.com/download?id=%s'
                '&export=download&confirm=t' % m.group(1))
    return url          # رابط مباشر أصلاً (خادم آخر)


def fetch_manifest(manifest_url, timeout=30):
    """يقرأ version.json — يعيد dict أو يرمي استثناء."""
    req = urllib.request.Request(gdrive_direct(manifest_url),
                                 headers={'User-Agent': 'NhjALBasra-Updater'})
    raw = urllib.request.urlopen(req, timeout=timeout).read()
    return json.loads(raw.decode('utf-8-sig'))


def check(manifest_url, current_version):
    """يعيد {'version','url','notes'} إن وجد إصدار أحدث، وإلا None."""
    mf = fetch_manifest(manifest_url)
    if parse_ver(mf.get('version')) > parse_ver(current_version):
        return {'version': str(mf.get('version')),
                'url': str(mf.get('url', '')),
                'notes': str(mf.get('notes', ''))}
    return None


def download(url, progress=None, timeout=60):
    """ينزّل الـ exe الجديد إلى ملف مؤقت. progress(نسبة مئوية أو -1 إن مجهولة).
    مهلة على مستوى المقبس: إن توقّف التدفّق يفشل برسالة بدل التعليق للأبد."""
    import socket
    req = urllib.request.Request(gdrive_direct(url),
                                 headers={'User-Agent': 'Mozilla/5.0 NhjALBasra-Updater'})
    resp = urllib.request.urlopen(req, timeout=timeout)   # يتبع إعادة توجيه GitHub تلقائياً
    total = int(resp.headers.get('Content-Length') or 0)
    fd, dest = tempfile.mkstemp(suffix='.exe', prefix='nhj_update_')
    done = 0
    try:
        with os.fdopen(fd, 'wb') as f:
            while True:
                try:
                    chunk = resp.read(256 * 1024)
                except socket.timeout:
                    raise RuntimeError('توقّف التنزيل (الاتصال بطيء أو منقطع) — أعد المحاولة')
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress:
                    progress(int(done * 100 / total) if total else -1)
    except Exception:
        try: os.remove(dest)
        except OSError: pass
        raise
    if done < 1_000_000:        # أقل من ميغابايت = ليس exe (غالباً صفحة خطأ)
        os.remove(dest)
        raise RuntimeError('الملف المنزّل غير سليم — تحقق من الرابط')
    return dest


def apply_and_restart(new_exe_path):
    """يكتب سكربت استبدال يعيد محاولة نسخ الـ exe الجديد حتى يتحرّر قفل الملف
    (نسخة الملف الواحد تبقى قافلة نفسها ثانيةً بعد الإغلاق)، ثم يعيد التشغيل.
    المستدعي يجب أن يُنهي التطبيق فوراً (os._exit) بعد النداء."""
    if not getattr(sys, 'frozen', False):
        raise RuntimeError('الاستبدال الذاتي متاح في نسخة exe فقط')
    target = sys.executable
    bat = os.path.join(tempfile.gettempdir(), 'nhj_update.bat')
    # حلقة إعادة نسخ: تنجح فور تحرّر قفل الـ exe (حتى 90 محاولة/90 ثانية)
    script = (
        '@echo off\r\n'
        'set /a tries=0\r\n'
        ':retry\r\n'
        'copy /y "{new}" "{target}" >NUL 2>&1\r\n'
        'if not errorlevel 1 goto done\r\n'
        'set /a tries+=1\r\n'
        'if %tries% geq 90 goto giveup\r\n'
        'timeout /t 1 /nobreak >NUL\r\n'
        'goto retry\r\n'
        ':done\r\n'
        'start "" "{target}"\r\n'
        ':giveup\r\n'
        'del /f /q "{new}" >NUL 2>&1\r\n'
        'del /f /q "%~f0" >NUL 2>&1\r\n'
    ).format(new=new_exe_path, target=target)
    with open(bat, 'w', encoding='utf-8') as f:
        f.write(script)
    subprocess.Popen(['cmd', '/c', bat], close_fds=True,
                     creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
