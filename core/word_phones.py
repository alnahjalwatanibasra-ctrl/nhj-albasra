# -*- coding: utf-8 -*-
"""بحث الهواتف في ملفات Word (الطلبات): فهرس اسم←هاتف + اقتراح مرشّحين للتأكيد.
درس مُجرَّب: لا نملأ تلقائياً على تقاطع كلمات؛ نقترح ويؤكّد المستخدم."""
import zipfile, re, os, unicodedata, difflib

AR = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
BAD = ('الموظف', 'مقدم الطلب', 'التقدير', 'مدير', 'المحترم', 'م/', 'ارجو', 'مع ', 'السيد',
       'وزارة', 'مديرية', 'ت/')


def norm(s):
    s = '' if s is None else str(s)
    for a, b in [('أ','ا'),('إ','ا'),('آ','ا'),('ى','ي'),('ة','ه'),('ؤ','و'),('ئ','ي'),('ـ','')]:
        s = s.replace(a, b)
    return ' '.join(''.join(c for c in s if not unicodedata.combining(c)).split()).strip()


def _docx_lines(p):
    parts = []
    try:
        z = zipfile.ZipFile(p)
        for nm in z.namelist():
            if nm.endswith('.xml') and any(k in nm for k in ('document', 'header', 'footer')):
                xml = z.read(nm).decode('utf-8', 'ignore')
                xml = re.sub(r'</w:p>', '\n', xml)
                parts.append(re.sub(r'<[^>]+>', '', xml))
    except Exception:
        return []
    return [l.strip() for l in '\n'.join(parts).split('\n') if l.strip()]


def _phone(s):
    d = s.translate(AR)
    m = re.search(r'0?7[789]\d{8}', d)
    if m:
        return m.group() if len(m.group()) == 11 else '0' + m.group()
    return ''


def _looks_name(l):
    if not l or _phone(l) or any(b in l for b in BAD):
        return False
    if sum(c.isdigit() for c in l.translate(AR)) > 2:
        return False
    w = [x for x in norm(l).split() if len(x) >= 2]
    return 2 <= len(w) <= 4


def build_index(folder, progress=None):
    """يبني فهرس {norm_name: (display_name, phone, file)} من ملفات docx."""
    index = {}
    files = []
    for root, _, fs in os.walk(folder):
        for fn in fs:
            if fn.lower().endswith('.docx') and not fn.startswith('~$'):
                files.append(os.path.join(root, fn))
    for i, path in enumerate(files):
        if progress:
            progress(i + 1, len(files))
        lines = _docx_lines(path)
        for j, l in enumerate(lines):
            if 'الموظف' in l or 'مقدم الطلب' in l:
                nm, ph = '', ''
                for k in range(j + 1, min(j + 4, len(lines))):
                    if not nm and _looks_name(lines[k]):
                        nm = lines[k]
                    if not ph:
                        ph = _phone(lines[k])
                if nm and ph:
                    key = norm(nm)
                    index.setdefault(key, (nm.strip(), ph, os.path.basename(path)))
    return index


def suggest(index, name, th=0.82, ftok_th=0.5):
    """يقترح (اسم_المرجع, هاتف, ملف, نسبة) للمستخدم ليؤكّد — لا يملأ تلقائياً.
    يعيد None إن لم يوجد مرشّح قوي كامل الاسم."""
    q = norm(name)
    if len(q) < 5:
        return None
    best, bs = None, 0
    for nn, v in ((norm(v[0]), v) for v in index.values()):
        s = difflib.SequenceMatcher(None, q, nn).ratio()
        if s > bs:
            bs, best = s, v
    if not best:
        return None
    ft = difflib.SequenceMatcher(
        None, (q.split() or [''])[0], (norm(best[0]).split() or [''])[0]).ratio()
    if bs >= th and ft >= ftok_th:
        return {'name': best[0], 'phone': best[1], 'file': best[2], 'score': round(bs * 100)}
    return None
