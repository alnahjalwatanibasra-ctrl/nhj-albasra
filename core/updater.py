# -*- coding: utf-8 -*-
"""التحديث التلقائي عبر GitHub Releases:
version.json يحمل {version, url, notes} — التطبيق يقارن، ينزّل الـ exe الجديد،
ويستبدل نفسه بسكربت bat يعمل بعد إغلاقه ثم يعيد تشغيله.
(أُزيل دعم Google Drive نهائياً — GitHub هو المصدر الوحيد.)"""
import json, os, re, sys, tempfile, subprocess, urllib.request


def parse_ver(s):
    """'1.4' ⟵ (1,4,0) — مقارنة أرقام آمنة."""
    nums = [int(x) for x in re.findall(r'\d+', str(s or ''))][:3]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


def fetch_manifest(manifest_url, timeout=30):
    """يقرأ version.json — يعيد dict أو يرمي استثناء.
    يكسر التخزين المؤقت (طابع زمني) حتى يرى الفحص اليدوي أحدث إصدار فوراً."""
    import time as _t
    url = str(manifest_url or '').strip()
    url += ('&' if '?' in url else '?') + '_=%d' % int(_t.time())
    req = urllib.request.Request(url, headers={
        'User-Agent': 'NhjALBasra-Updater',
        'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})
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
    req = urllib.request.Request(str(url or '').strip(),
                                 headers={'User-Agent': 'Mozilla/5.0 NhjALBasra-Updater'})
    resp = urllib.request.urlopen(req, timeout=timeout)   # يتبع إعادة توجيه GitHub تلقائياً
    total = int(resp.headers.get('Content-Length') or 0)
    fd, dest = tempfile.mkstemp(suffix='.exe', prefix='nhj_update_')
    done = 0
    head = b''
    try:
        with os.fdopen(fd, 'wb') as f:
            while True:
                try:
                    chunk = resp.read(256 * 1024)
                except socket.timeout:
                    raise RuntimeError('توقّف التنزيل (الاتصال بطيء أو منقطع) — أعد المحاولة')
                if not chunk:
                    break
                if not head:
                    head = chunk[:2]
                f.write(chunk)
                done += len(chunk)
                if progress:
                    progress(int(done * 100 / total) if total else -1)
    except Exception:
        try: os.remove(dest)
        except OSError: pass
        raise

    def _bad(reason):
        try: os.remove(dest)
        except OSError: pass
        raise RuntimeError(reason)

    # فحوص سلامة صارمة — لا يُثبَّت ملف ناقص أو تالف مهما حدث
    if done < 1_000_000:
        _bad('الملف المنزّل غير سليم — تحقق من الرابط')
    if total and done != total:
        _bad('التنزيل غير مكتمل (%d من %d) — أعد المحاولة' % (done, total))
    if head != b'MZ':
        _bad('الملف المنزّل ليس برنامجاً صالحاً — أعد المحاولة')
    return dest


def apply_and_restart(new_exe_path):
    """يكتب سكربت استبدال يعيد محاولة نسخ الـ exe الجديد حتى يتحرّر قفل الملف
    (نسخة الملف الواحد تبقى قافلة نفسها ثانيةً بعد الإغلاق)، ثم يعيد التشغيل.
    المستدعي يجب أن يُنهي التطبيق فوراً (os._exit) بعد النداء."""
    if not getattr(sys, 'frozen', False):
        raise RuntimeError('الاستبدال الذاتي متاح في نسخة exe فقط')
    target = sys.executable
    bat = os.path.join(tempfile.gettempdir(), 'nhj_update.bat')
    # حلقة إعادة نسخ: تنجح فور تحرّر قفل الـ exe (حتى 90 محاولة/90 ثانية)،
    # ثم تأخير استقرار قبل التشغيل (يمنع خطأ «تعذّر تحميل Python DLL» عند إعادة
    # التشغيل الفورية — النظام/مكافح الفيروسات يحتاج ثوانيَ لإنهاء الملف الجديد).
    script = (
        '@echo off\r\n'
        'set /a tries=0\r\n'
        ':retry\r\n'
        'copy /y "{new}" "{target}" >NUL 2>&1\r\n'
        'if not errorlevel 1 goto settle\r\n'
        'set /a tries+=1\r\n'
        'if %tries% geq 90 goto giveup\r\n'
        'timeout /t 1 /nobreak >NUL\r\n'
        'goto retry\r\n'
        ':settle\r\n'
        'timeout /t 2 /nobreak >NUL\r\n'          # استقرار الملف قبل التشغيل
        'set "_MEIPASS2="\r\n'                     # تنظيف متغيّر التغليف المسرّب (سبب خطأ DLL)
        'set "_PYI_APPLICATION_HOME_DIR="\r\n'
        'set "_PYI_ARCHIVE_FILE="\r\n'
        'set "_PYI_PARENT_PROCESS_LEVEL="\r\n'
        'start "" "{target}"\r\n'
        ':giveup\r\n'
        'del /f /q "{new}" >NUL 2>&1\r\n'
        'del /f /q "%~f0" >NUL 2>&1\r\n'
    ).format(new=new_exe_path, target=target)
    with open(bat, 'w', encoding='utf-8') as f:
        f.write(script)
    # بيئة نظيفة: نزيل كل متغيّرات التغليف (_MEI*/_PYI*) حتى لا يرثها الـ exe الجديد
    clean_env = {k: v for k, v in os.environ.items()
                 if not (k.startswith('_MEI') or k.startswith('_PYI'))}
    subprocess.Popen(['cmd', '/c', bat], close_fds=True, env=clean_env,
                     creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
