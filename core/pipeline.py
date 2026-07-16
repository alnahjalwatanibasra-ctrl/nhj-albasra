# -*- coding: utf-8 -*-
"""المحرّك الكامل (قائم على الأدوار): صور → Gemini → أدوار الأعمدة → مطابقة المرجع → تصحيحات → ترقيم.
يعالج كل صورة بعناوينها هي ويربط كل عمود بدوره، فلا تختلّ المحاذاة مع اختلاف العناوين بين الصور."""
import json as _json, os as _os
from . import config, gemini_ocr, reference, corrections
from .reference import norm


class CancelledError(Exception):
    """أوقف المستخدم الاستخراج."""

# ترتيب الأعمدة (كالمرجع) وأسماؤها القياسية في المخرجات
ROLE_ORDER = ['num', 'name', 'subj', 'phone', 'date', 'dawira', 'moar', 'jiha']
CANON = {
    'num': 'رقم الكتاب', 'name': 'اسم صاحب الكتاب', 'subj': 'موضوع الكتاب',
    'phone': 'رقم الهاتف', 'date': 'تاريخ الكتاب', 'dawira': 'الدائرة',
    'moar': 'المعرف', 'jiha': 'الجهة المرسل اليها',
}


def detect_roles(headers):
    """يربط عناوين صورة بالأدوار (قائم على الكلمات المفتاحية، الهاتف قبل الرقم)."""
    roles = {}
    for h in headers:
        n = norm(h)
        if 'ملاحظ' in n:              # يُتجاهل
            continue
        if 'هاتف' in n or 'موبايل' in n or 'جوال' in n:
            roles.setdefault('phone', h)
        elif 'رقم' in n and 'كتاب' in n:
            roles.setdefault('num', h)
        elif n == norm('رقم'):
            roles.setdefault('num', h)
        elif 'اسم' in n:
            roles.setdefault('name', h)
        elif 'موضوع' in n:
            roles.setdefault('subj', h)
        elif 'تاريخ' in n:
            roles.setdefault('date', h)
        elif 'دائره' in n or 'دائرة' in n:
            roles.setdefault('dawira', h)
        elif 'معرف' in n:
            roles.setdefault('moar', h)
        elif 'جهه' in n or 'جهة' in n or 'مرسل' in n:
            roles.setdefault('jiha', h)
    return roles


def _extract(image_paths, key, models, progress, cache_path, vocab=None, cancel=None):
    """يعيد قائمة صفوف بالأدوار: كل صف {role: (value, conf)} + '_page' فهرس صفحته."""
    if cache_path and _os.path.exists(cache_path):
        if progress: progress('تحميل الاستخراج المخزّن')
        pages = _json.load(open(cache_path, encoding='utf-8'))
    else:
        # الصور تُستخرج بالتوازي — زمن الدفعة ≈ زمن أبطأ صورة لا مجموعها
        from concurrent.futures import ThreadPoolExecutor, as_completed
        pages = [None] * len(image_paths)
        if progress and len(image_paths) > 1:
            progress('استخراج %d صور بالتوازي...' % len(image_paths))

        def _work(idx, img):
            if cancel is not None and cancel.is_set():
                raise CancelledError()
            if progress: progress('استخراج الصورة %d/%d' % (idx + 1, len(image_paths)))
            return idx, gemini_ocr.extract_image(key, img, models, vocab=vocab,
                                                 progress=progress)
        with ThreadPoolExecutor(max_workers=min(3, max(1, len(image_paths)))) as ex:
            futs = [ex.submit(_work, i, img) for i, img in enumerate(image_paths)]
            done = 0
            for f in as_completed(futs):
                idx, res = f.result()
                pages[idx] = res
                done += 1
                if progress and len(image_paths) > 1:
                    progress('اكتملت %d من %d صور' % (done, len(image_paths)))
        if cancel is not None and cancel.is_set():
            raise CancelledError()
        if cache_path:
            _json.dump(pages, open(cache_path, 'w', encoding='utf-8'), ensure_ascii=False)

    rows = []
    for pi, res in enumerate(pages):
        roles = detect_roles(res.get('headers', []))
        for row in res.get('rows', []):
            cells = row.get('cells', {})
            rec = {}
            for role, header in roles.items():
                cell = cells.get(header, {})
                rec[role] = (gemini_ocr.cell_value(cell), gemini_ocr.cell_conf(cell))
            rec['_page'] = pi
            rec['_model'] = res.get('model', '')
            rows.append(rec)
    return rows


def sort_pages_by_numbers(ext):
    """يعيد ترتيب الصفحات حسب وسيط أرقام كتبها المقروءة — يحمي من رفع الصور
    بترتيب خاطئ (الترقيم التسلسلي يتوزع بالموضع، فالترتيب الخاطئ = أرقام خاطئة).
    صفحة بلا أرقام مقروءة تبقى في موضعها النسبي بعد الصفحات المعروفة."""
    import statistics
    from collections import defaultdict
    pages = defaultdict(list)
    for rec in ext:
        pages[rec.get('_page', 0)].append(rec)
    keys = {}
    for pi, recs in pages.items():
        nums = []
        for rec in recs:
            d = corrections.to_western_digits(rec.get('num', ('', ''))[0])
            if d.isdigit() and 2 <= len(d) <= 5:
                nums.append(int(d))
        keys[pi] = statistics.median(nums) if nums else None
    known = sorted([pi for pi in pages if keys[pi] is not None], key=lambda pi: keys[pi])
    unknown = sorted(pi for pi in pages if keys[pi] is None)
    out = []
    for pi in known + unknown:
        out.extend(pages[pi])
    return out


_DIGITS = set('٠١٢٣٤٥٦٧٨٩0123456789 /')

def _is_numeric(s):
    s = (s or '').strip()
    return bool(s) and set(s) <= set('٠١٢٣٤٥٦٧٨٩0123456789') and s != ''

def _looks_date(s):
    s = (s or '').strip()
    return ('/' in s) or ('-' in s)

def cleanup_ditto(ext):
    """يصحّح خلايا التكرار المشوّشة حتمياً: يكرّر آخر قيمة صحيحة نزولاً،
    ويكشف الأخطاء (تاريخ بلا «/»، جهة/موضوع رقمي، معرف = الاسم)."""
    last = {}
    for rec in ext:
        name = (rec.get('name', ('', ''))[0] or '').strip()
        for role in ('subj', 'date', 'jiha', 'moar', 'dawira'):
            v, cf = rec.get(role, ('', 'high'))
            vs = (v or '').strip()
            bad = False
            if role == 'date':
                bad = bool(vs) and not _looks_date(vs)          # تاريخ بلا فاصل = خطأ (رقم كتاب)
            elif role in ('jiha', 'subj'):
                bad = _is_numeric(vs)                             # قيمة رقمية بحتة = خطأ
            elif role == 'moar':
                bad = bool(vs) and name and norm(vs) == norm(name)  # المعرف = الاسم = خطأ
            if (not vs) or bad:
                if role in last:
                    rec[role] = (last[role], cf)
            else:
                last[role] = vs
    return ext


def run(image_paths, reference_path, prev_register_path=None,
        settings=None, progress=None, cache_path=None, cancel=None):
    settings = settings or config.load_settings()
    key = config.get_key(settings)
    models = settings['gemini_models']
    ref = reference.Reference(reference_path) if reference_path else None

    vocab = ref.vocab() if (ref and settings.get('vocab_in_prompt', True)) else None
    ext = _extract(image_paths, key, models, progress, cache_path, vocab=vocab, cancel=cancel)
    ext = sort_pages_by_numbers(ext)   # قبل معالجة الديتو — التكرار يتبع الترتيب الحقيقي
    ext = cleanup_ditto(ext)

    def rv(rec, role): return rec.get(role, ('', 'high'))[0]
    def rc(rec, role): return rec.get(role, ('', 'high'))[1]

    th = settings.get('match_threshold', 0.82)
    ftok = settings.get('first_token_threshold', 0.55)
    rare = settings.get('rare_referrer_max', 4)
    pull = settings.get('reference_pull_fields', [])
    repl = settings.get('subject_replacements', {})
    arabic = settings.get('arabic_numerals', True)

    # مطابقة المرجع (محاذاة تسلسلية: السجل غالباً مقطع متتالٍ من صفوف المرجع)
    if ref:
        signals = [{'name': rv(rec, 'name'), 'moar': rv(rec, 'moar'), 'subj': rv(rec, 'subj')}
                   for rec in ext]
        hits = ref.align(signals, th=th, ftok_th=ftok, rare_max=rare)
    else:
        hits = [None] * len(ext)
    # إزالة التكرار المتتالي (نفس صف المرجع نفسه على صفّين = تسرّب ديتو)
    for i in range(1, len(hits)):
        if hits[i] is not None and hits[i] is hits[i - 1]:
            hits[i] = None

    # ترقيم متسلسل مرسّى بأرقام OCR (صف ساقط من القراءة = فجوة ظاهرة لا انزياح شامل)
    ocr_nums = [corrections.to_western_digits(rv(rec, 'num')) for rec in ext]
    start = None
    if prev_register_path:
        last = corrections.last_book_number(prev_register_path)
        if last is not None:
            start = last + 1
    if start is None:
        start = corrections.infer_start_number(ocr_nums)
    seq = corrections.sequential_numbers_anchored(ocr_nums, start) if start is not None else None

    # الأعمدة الظاهرة = الأدوار المكتشفة في أي صورة + الدائرة إن طُلب سحبها
    present = set()
    for rec in ext: present |= (set(rec.keys()) - {'_page', '_model'})
    if 'دائرة' in pull: present.add('dawira')
    out_roles = [r for r in ROLE_ORDER if r in present]
    headers = [CANON[r] for r in out_roles]

    rows, colors = [], {}
    for i, rec in enumerate(ext):
        hit = hits[i]
        out = {}
        # القيم من الاستخراج
        for r in out_roles:
            out[CANON[r]] = rv(rec, r)
        # الموضوع: تصحيح المصطلحات
        if 'subj' in out_roles:
            out[CANON['subj']] = corrections.apply_replacements(out[CANON['subj']], repl)
        # رقم الكتاب: ترقيم متسلسل
        if 'num' in out_roles:
            v = seq[i] if seq else corrections.to_western_digits(rv(rec, 'num'))
            out[CANON['num']] = corrections.to_arabic(v) if (arabic and str(v)) else v
        # الهاتف المستخرج: توحيد (٠٧ + ١١ خانة) بأرقام عربية
        if 'phone' in out_roles:
            pv = corrections.format_phone(out[CANON['phone']], arabic=arabic)
            out[CANON['phone']] = pv if pv else out[CANON['phone']]

        if hit:
            def _pull(role, value):
                out[CANON[role]] = value; colors[(i, CANON[role])] = 'ref'
            _pull('name', hit.get('name', out.get(CANON['name'], '')))
            if 'هاتف' in pull and 'phone' in hit:
                ph = corrections.format_phone(hit.get('phone'), arabic=arabic)
                # مرجع بلا خانات (فارغ أو «لا يوجد») = لا هاتف لهذا الشخص فعلاً
                _pull('phone', ph if ph else 'لا يوجد')
            if 'معرف' in pull and hit.get('moar'):
                _pull('moar', hit['moar'])
            if 'دائرة' in pull and hit.get('dawira') and 'dawira' in present:
                _pull('dawira', hit['dawira'])
            if 'موضوع' in pull and hit.get('subj') and 'subj' in out_roles:
                _pull('subj', corrections.apply_replacements(str(hit['subj']), repl))
            if 'جهة' in pull and hit.get('jiha') and 'jiha' in out_roles:
                _pull('jiha', hit['jiha'])
            if 'تاريخ' in pull and hit.get('date') and 'date' in out_roles:
                dt = corrections.format_ref_date(hit['date'], arabic=arabic)
                if dt:
                    _pull('date', dt)
        # الدائرة من المعرف (كل معرف تابع لدائرة معروفة) — إن بقيت الخلية فارغة
        if ref and 'دائرة' in pull and 'dawira' in present:
            if not str(out.get(CANON['dawira'], '') or '').strip():
                dm = ref.dawira_for_moar(out.get(CANON['moar'], ''))
                if dm:
                    dawira, decisive = dm
                    out[CANON['dawira']] = dawira
                    colors[(i, CANON['dawira'])] = 'ref' if decisive else 'review'
        else:
            # ثقة Gemini
            if rc(rec, 'name') == 'low':
                colors[(i, CANON['name'])] = 'review'
            pv = corrections.to_western_digits(rv(rec, 'phone'))
            if pv and (len(pv) != 11 or pv[:2] != '07' or rc(rec, 'phone') == 'low'):
                if CANON['phone'] in out:
                    colors[(i, CANON['phone'])] = 'phone_unconf'
        rows.append(out)

    return {
        'headers': headers,
        'rows': rows,
        'colors': colors,
        'ref_columns': ref.detected_columns() if ref else {},
        'names': [rv(rec, 'name') for rec in ext],
        'matched': [bool(h) for h in hits],
        'row_pages': [rec.get('_page', 0) for rec in ext],
        'models_used': sorted({rec.get('_model', '') for rec in ext} - {''}),
        'primary_model': (models[0] if models else ''),
    }
