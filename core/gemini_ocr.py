# -*- coding: utf-8 -*-
"""استخراج جدول سجل الصادر من صورة عبر Gemini (استخراج كامل + ثقة لكل خلية)."""
import urllib.request, urllib.parse, json, base64, time

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


def _call(key, model, img_bytes, timeout=120, prompt=None):
    b64 = base64.b64encode(img_bytes).decode()
    body = {
        "contents": [{"parts": [
            {"text": prompt or build_prompt()},
            {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
        ]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    url = ENDPOINT.format(model=model, key=urllib.parse.quote(key))
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    txt = r['candidates'][0]['content']['parts'][0]['text']
    return json.loads(txt)


def extract_image(key, img_path, models, vocab=None):
    """يعيد dict {headers, rows} حيث كل خلية {v, c}. يعيد المحاولة ويتناوب النماذج.
    vocab: قوائم مفردات المرجع تُحقن في الـ prompt لترشيد قراءة خط اليد."""
    data = open(img_path, 'rb').read()
    prompt = build_prompt(vocab)
    last_err = None
    for attempt in range(6):
        model = models[min(attempt, len(models) - 1)]
        try:
            out = _call(key, model, data, prompt=prompt)
            return {'headers': out.get('headers', []), 'rows': out.get('rows', []), 'model': model}
        except urllib.error.HTTPError as e:
            last_err = f'HTTP {e.code}'
            if e.code in (429, 500, 503):
                time.sleep(3 + attempt * 3); continue
            raise
        except (urllib.error.URLError, ConnectionResetError, OSError, TimeoutError) as e:
            last_err = str(e); time.sleep(3 + attempt * 3); continue
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            last_err = 'parse: ' + str(e); time.sleep(2); continue
    raise RuntimeError('فشل استخراج Gemini بعد عدة محاولات: ' + str(last_err))


def cell_value(cell):
    """يستخرج القيمة من خلية {v,c} أو قيمة مباشرة."""
    if isinstance(cell, dict):
        return str(cell.get('v', '') or '')
    return str(cell or '')


def cell_conf(cell):
    if isinstance(cell, dict):
        return (cell.get('c', 'high') or 'high').lower()
    return 'high'
