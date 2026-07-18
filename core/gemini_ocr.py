# -*- coding: utf-8 -*-
"""استخراج جدول سجل الصادر من صورة عبر Gemini (استخراج كامل + ثقة لكل خلية)."""
import urllib.request, urllib.parse, json, base64, time, io

MAX_SIDE = 2200      # صور الكاميرا الضخمة تُبطئ الرفع وتُسقط المهلة — التصغير لا يضر خط اليد


def prepare_image_bytes(img_path):
    """يصغّر الصور الأكبر من MAX_SIDE قبل الإرسال (JPEG جودة 88).
    صورة كاميرا 4000px/8MB ⟵ ~2200px/أقل من 1MB: رفع أسرع بكثير وبلا فقد قراءة."""
    raw = open(img_path, 'rb').read()
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw))
        if max(im.size) <= MAX_SIDE:
            return raw
        im = im.convert('RGB')
        ratio = MAX_SIDE / max(im.size)
        im = im.resize((round(im.width * ratio), round(im.height * ratio)),
                       Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=88)
        return buf.getvalue()
    except Exception:
        return raw           # أي فشل في التصغير = أرسل الأصل كما هو

ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'

PROMPT = '''هذه صورة جدول عربي مكتوب بخط اليد (سجل الصادر) اتجاهه من اليمين لليسار.
اقرأ عناوين الأعمدة من الصورة كما هي، ثم استخرج كل صف.
{vocab}تعليمات دقة:
- رقم الهاتف: رقم عراقي بالضبط 11 خانة يبدأ بـ 07 (077/078/079). تأمّل كل خانة على حدة بتأنٍّ وتأكّد أن الناتج 11 خانة.
- الاسم: اقرأ الاسم الثلاثي/الرباعي حرفاً حرفاً.
- علامة التكرار (قوس/مثله «») تعني: كرّر قيمة الخلية التي فوقها.
- لكل خلية أعطِ درجة ثقة: "high" إن كنت واثقاً، "low" إن كان الخط غامضاً.
أعِد JSON فقط بهذا الشكل بلا أي شرح:
{{"headers":["..."],"rows":[{{"cells":{{"<العنوان>":{{"v":"القيمة","c":"high"}}}}}}]}}'''

# قوائم مفردات المرجع تُحقن في الـ prompt — مُقاسة: ترفع قراءة الأسماء الخام من 5/10 إلى 9/10
VOCAB_TMPL = '''لديك قوائم مفردات معروفة من سجلات هذا المكتب — معظم ما في الصورة موجود فيها:
{lists}
- اقرأ خط اليد أولاً؛ إن طابقت قراءتك أحد عناصر القوائم بوضوح فاكتبه بصيغته من القائمة وثقة "high".
- إن لم تجد تطابقاً واضحاً في القائمة فاكتب ما تراه حرفياً بثقة "low" — لا تخترع تطابقاً.
'''

MAX_VOCAB_ITEMS = 1500   # سقف حجم القوائم الكلي حتى لا يتضخم الـ prompt


def build_prompt(vocab=None):
    """vocab: dict عنوان⟵قائمة قيم (مثل {'أسماء معروفة': [...], ...}) أو None."""
    if not vocab:
        return PROMPT.format(vocab='')
    lines, budget = [], MAX_VOCAB_ITEMS
    for title, items in vocab.items():
        items = [str(x).strip() for x in items if x and str(x).strip()][:budget]
        if not items:
            continue
        budget -= len(items)
        lines.append('- %s: %s' % (title, ' | '.join(items)))
        if budget <= 0:
            break
    if not lines:
        return PROMPT.format(vocab='')
    return PROMPT.format(vocab=VOCAB_TMPL.format(lists='\n'.join(lines)))


TEXT_PROMPT = '''اكتب كل النص المكتوب في هذه الصورة كما هو تماماً، سطراً بسطر بنفس ترتيب الورقة.
- حافظ على فواصل الأسطر الأصلية.
- إن وجدت جدولاً فاكتب كل صف من صفوفه في سطر واحد مع فاصل « | » بين الخلايا.
- لا تضف أي شرح أو عنوان أو ترجمة أو تعليق من عندك — النص الموجود في الصورة فقط.'''


def _call(key, model, img_bytes, timeout=300, prompt=None, mime='application/json',
          thinking=None):
    b64 = base64.b64encode(img_bytes).decode()
    gen = {"temperature": 0}
    if mime:
        gen["responseMimeType"] = mime
    if thinking is not None:
        gen["thinkingConfig"] = {"thinkingBudget": thinking}   # 0 = بلا تفكير (أسرع بكثير)
    body = {
        "contents": [{"parts": [
            {"text": prompt or build_prompt()},
            {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
        ]}],
        "generationConfig": gen,
    }
    url = ENDPOINT.format(model=model, key=urllib.parse.quote(key))
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    txt = r['candidates'][0]['content']['parts'][0]['text']
    return json.loads(txt) if mime == 'application/json' else txt


# نماذج نفدت حصتها في هذه الجلسة — لا نعيد تجربتها مع كل صورة (كانت سبب بطء شديد)
_dead_models = set()


def reset_dead_models():
    _dead_models.clear()


def extract_image(key, img_path, models, vocab=None, progress=None):
    """يعيد dict {headers, rows} حيث كل خلية {v, c}. يتناوب النماذج:
    خطأ الحصة (429) ⟵ تحويل فوري للنموذج التالي بلا انتظار، ويُحفظ أنه ممتلئ للجلسة.
    أخطاء الخادم/الشبكة العابرة ⟵ محاولتان لكل نموذج بانتظار قصير."""
    data = prepare_image_bytes(img_path)
    prompt = build_prompt(vocab)
    last_err = None
    queue = ([m for m in models if m not in _dead_models]
             or list(models))          # إن امتلأ الجميع جرّبها كلها مجدداً
    for model in queue:
        quota_dead = False
        for attempt in range(2):
            try:
                out = _call(key, model, data, prompt=prompt)
                return {'headers': out.get('headers', []), 'rows': out.get('rows', []),
                        'model': model}
            except urllib.error.HTTPError as e:
                last_err = f'HTTP {e.code} ({model})'
                if e.code == 429:
                    _dead_models.add(model)
                    quota_dead = True
                    if progress:
                        progress('حصة النموذج %s ممتلئة — التحويل للاحتياطي' % model)
                    break              # فوراً للنموذج التالي — لا انتظار على حصة ممتلئة
                if e.code in (500, 503):
                    time.sleep(2); continue
                raise
            except (urllib.error.URLError, ConnectionResetError, OSError, TimeoutError) as e:
                last_err = str(e); time.sleep(2); continue
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                last_err = 'parse: ' + str(e); time.sleep(1); continue
        if not quota_dead and progress:
            progress('النموذج %s تعثّر — التحويل للتالي' % model)
    raise RuntimeError('فشل استخراج Gemini بعد عدة محاولات: ' + str(last_err))


def extract_text_image(key, img_path, models, progress=None):
    """يستخرج النص الخام من صورة (ميزة «استخراج النصوص») — نفس التناوب
    وذاكرة النماذج الممتلئة والتصغير، لكن الرد نص حر لا JSON."""
    data = prepare_image_bytes(img_path)
    last_err = None
    queue = ([m for m in models if m not in _dead_models] or list(models))
    for model in queue:
        quota_dead = False
        for attempt in range(2):
            try:
                # بلا تفكير: نسخ النص لا يحتاجه، والفرق هائل (مُقاس: 210ث ⟵ 12ث)
                txt = _call(key, model, data, prompt=TEXT_PROMPT, mime=None, thinking=0)
                return {'text': (txt or '').strip(), 'model': model}
            except urllib.error.HTTPError as e:
                last_err = f'HTTP {e.code} ({model})'
                if e.code == 429:
                    _dead_models.add(model)
                    quota_dead = True
                    if progress:
                        progress('حصة النموذج %s ممتلئة — التحويل للاحتياطي' % model)
                    break
                if e.code in (500, 503):
                    time.sleep(2); continue
                raise
            except (urllib.error.URLError, ConnectionResetError, OSError, TimeoutError) as e:
                last_err = str(e); time.sleep(2); continue
            except (KeyError, ValueError) as e:
                last_err = 'parse: ' + str(e); time.sleep(1); continue
        if not quota_dead and progress:
            progress('النموذج %s تعثّر — التحويل للتالي' % model)
    raise RuntimeError('فشل استخراج النص بعد عدة محاولات: ' + str(last_err))


def cell_value(cell):
    """يستخرج القيمة من خلية {v,c} أو قيمة مباشرة."""
    if isinstance(cell, dict):
        return str(cell.get('v', '') or '')
    return str(cell or '')


def cell_conf(cell):
    if isinstance(cell, dict):
        return (cell.get('c', 'high') or 'high').lower()
    return 'high'
