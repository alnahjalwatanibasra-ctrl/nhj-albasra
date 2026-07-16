# -*- coding: utf-8 -*-
"""الإعدادات: المفتاح المشترك، قوائم الاستبدال، تنسيقات — تُحفظ في settings.json."""
import json, os, sys

# داخل exe المجمّد: الملفات القابلة للكتابة (الإعدادات، الجلسة، الكاش) في AppData
# حتى يبقى ملف exe وحيداً نظيفاً على سطح المكتب بلا ملفات متناثرة حوله
if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
    _roaming = os.environ.get('APPDATA', EXE_DIR)
    APP_DIR = os.path.join(_roaming, 'Nhj-AL-Basra')
    _old = os.path.join(_roaming, 'سجلات النهج')
    try:
        if os.path.isdir(_old) and not os.path.isdir(APP_DIR):
            os.rename(_old, APP_DIR)      # ترحيل بيانات الاسم القديم
        os.makedirs(APP_DIR, exist_ok=True)
    except OSError:
        APP_DIR = EXE_DIR
else:
    EXE_DIR = APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(APP_DIR, 'settings.json')

DEFAULTS = {
    "gemini_key": "",
    "gemini_models": ["gemini-3-flash-preview", "gemini-3.5-flash", "gemini-flash-latest",
                      "gemini-3.1-flash-lite", "gemini-flash-lite-latest"],
    "arabic_numerals": True,          # مخرجات بالأرقام العربية ٠١٢
    # استبدالات مصطلحات الموضوع (تُطبّق تلقائياً)
    "subject_replacements": {
        "رضخي": "وظيفي",
        "أجهزة": "أعمدة",
        "اجهزة": "اعمدة",
        "أجرة": "ظفيرة",
        "اجرة": "ظفيرة",
        "تخديم": "تخصيص",
    },
    # الحقول التي تُسحب من المرجع عند مطابقة الاسم
    "reference_pull_fields": ["هاتف", "معرف", "دائرة", "موضوع", "جهة", "تاريخ"],
    "vocab_in_prompt": True,          # حقن مفردات المرجع في prompt الاستخراج (يرشد قراءة خط اليد)
    "match_threshold": 0.82,          # عتبة تشابه الاسم
    "first_token_threshold": 0.55,    # حارس الاسم الأول
    "rare_referrer_max": 4,           # المعرّف النادر يؤكّد الهوية
}


def load_settings():
    s = dict(DEFAULTS)
    if os.path.exists(SETTINGS_PATH):
        try:
            s.update(json.load(open(SETTINGS_PATH, encoding='utf-8')))
        except Exception:
            pass
    return s


def save_settings(s):
    json.dump(s, open(SETTINGS_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def get_key(settings=None):
    """المفتاح: من settings أو من ملف gemini_key.txt بجانب البرنامج."""
    settings = settings or load_settings()
    if settings.get('gemini_key'):
        return settings['gemini_key'].strip()
    # الأولوية: مفتاح الإعدادات ⟵ ملف بجانب exe (تجاوز اختياري) ⟵ المفتاح المضمّن داخل البرنامج
    embedded = os.path.join(getattr(sys, '_MEIPASS', APP_DIR), 'assets', 'keys', 'gemini_key.txt')
    for p in (os.path.join(EXE_DIR, 'gemini_key.txt'),
              os.path.join(APP_DIR, 'gemini_key.txt'),
              embedded,
              r'C:\Users\ABR ALSHARQ\Desktop\ser\gemini_key.txt'):
        if os.path.exists(p):
            return open(p, encoding='utf-8').read().strip()
    return ""
