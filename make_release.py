# -*- coding: utf-8 -*-
"""يجهّز إصداراً للتوزيع: يبني الـ exe ويولّد dist/version.json.
الاستخدام: python make_release.py "وصف الجديد في هذا الإصدار"
ثم ارفع الملفين على درايف بخاصية «إدارة الإصدارات» (نفس الرابطين يبقيان)."""
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
from core.version import VERSION
from core.config import load_settings

notes = sys.argv[1] if len(sys.argv) > 1 else ''
print(f'>> بناء الإصدار {VERSION} ...')
r = subprocess.run([sys.executable, '-m', 'PyInstaller', 'run_app.py',
                    '--name', 'Nhj AL-Basra', '--onefile', '--windowed',
                    '--icon', 'assets/logo.ico',
                    '--add-data', 'assets;assets', '--add-data', 'ui/theme.qss;ui',
                    '--noconfirm', '--log-level', 'ERROR'], cwd=HERE)
if r.returncode:
    sys.exit('فشل البناء')

# رابط تنزيل الـ exe: يقرأه من الإعدادات إن ضُبط (exe_download_url) وإلا يترك تذكيراً
exe_url = load_settings().get('exe_download_url', 'ضع هنا رابط مشاركة الـ exe من درايف')
manifest = {'version': VERSION, 'url': exe_url, 'notes': notes}
mp = os.path.join(HERE, 'dist', 'version.json')
json.dump(manifest, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('>> جاهز للرفع على درايف (استبدال بنفس الملفين عبر «إدارة الإصدارات»):')
print('   1)', os.path.join(HERE, 'dist', 'Nhj AL-Basra.exe'))
print('   2)', mp, '\n      محتواه:', json.dumps(manifest, ensure_ascii=False))
