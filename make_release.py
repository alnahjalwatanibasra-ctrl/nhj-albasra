# -*- coding: utf-8 -*-
"""يجهّز إصداراً للتوزيع عبر GitHub Releases:
يبني الـ exe، ينسخه باسم الأصل النظيف، ويولّد version.json الجاهز للرفع.
الاستخدام: python make_release.py "وصف الجديد في هذا الإصدار"

بعد التشغيل ارفع الملفين في Release جديد على GitHub:
  dist/NhjALBasra.exe   و   dist/version.json
والرابط الثابت latest يتكفّل بالباقي — كل الأجهزة تتحدّث وحدها."""
import json, os, shutil, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
from core.version import VERSION, RELEASE_ASSET, EXE_URL

notes = sys.argv[1] if len(sys.argv) > 1 else ''
print(f'>> بناء الإصدار {VERSION} ...')
r = subprocess.run([sys.executable, '-m', 'PyInstaller', 'run_app.py',
                    '--name', 'Nhj AL-Basra', '--onefile', '--windowed',
                    '--icon', 'assets/logo.ico', '--splash', 'assets/splash.png',
                    '--add-data', 'assets;assets', '--add-data', 'ui/theme.qss;ui',
                    '--noconfirm', '--log-level', 'ERROR'], cwd=HERE)
if r.returncode:
    sys.exit('فشل البناء')

dist = os.path.join(HERE, 'dist')
built = os.path.join(dist, 'Nhj AL-Basra.exe')
asset = os.path.join(dist, RELEASE_ASSET)          # نسخة بلا مسافات لأصل الـ Release
shutil.copy2(built, asset)

manifest = {'version': VERSION, 'url': EXE_URL, 'notes': notes}
mp = os.path.join(dist, 'version.json')
json.dump(manifest, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

print('\n>> جاهز. أنشئ Release جديداً على GitHub وارفع فيه هذين الملفين:')
print('   1)', asset)
print('   2)', mp)
print('   محتوى version.json:', json.dumps(manifest, ensure_ascii=False))
print('\n   (سطح المكتب: انسخ "Nhj AL-Basra.exe" الأصلي — بالمسافة — للاستخدام المحلي)')
