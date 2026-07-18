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


def download(url, progress=None, timeout=120):
    """ينزّل الـ exe الجديد إلى ملف مؤقت. progress(نسبة مئوية أو -1 إن مجهولة)."""
    req = urllib.request.Request(gdrive_direct(url),
                                 headers={'User-Agent': 'NhjALBasra-Updater'})
    resp = urllib.request.urlopen(req, timeout=timeout)
    total = int(resp.headers.get('Content-Length') or 0)
    fd, dest = tempfile.mkstemp(suffix='.exe', prefix='nhj_update_')
    done = 0
    with os.fdopen(fd, 'wb') as f:
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if progress:
                progress(int(done * 100 / total) if total else -1)
    if done < 1_000_000:        # أقل من ميغابايت = ليس exe (غالباً صفحة خطأ من درايف)
        os.remove(dest)
        raise RuntimeError('الملف المنزّل غير سليم — تحقق من رابط التنزيل في version.json')
    return dest


def apply_and_restart(new_exe_path):
    """يكتب سكربت استبدال ينتظر إغلاق التطبيق، يبدّل الـ exe، ويعيد تشغيله.
    المستدعي يجب أن يغلق التطبيق فور النداء."""
    if not getattr(sys, 'frozen', False):
        raise RuntimeError('الاستبدال الذاتي متاح في نسخة exe فقط')
    target = sys.executable
    pid = os.getpid()
    bat = os.path.join(tempfile.gettempdir(), 'nhj_update_%d.bat' % pid)
    with open(bat, 'w', encoding='utf-8') as f:
        f.write('@echo off\nchcp 65001 >NUL\n'
                ':wait\n'
                'tasklist /FI "PID eq {pid}" 2>NUL | find "{pid}" >NUL '
                '&& (timeout /t 1 /nobreak >NUL & goto wait)\n'
                'copy /y "{new}" "{target}" >NUL\n'
                'del /f /q "{new}" >NUL 2>&1\n'
                'start "" "{target}"\n'
                'del /f /q "%~f0"\n'.format(pid=pid, new=new_exe_path, target=target))
    subprocess.Popen(['cmd', '/c', bat],
                     creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
