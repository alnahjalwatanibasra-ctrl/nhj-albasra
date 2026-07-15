# -*- coding: utf-8 -*-
"""حفظ الجلسة تلقائياً: بعد الاستخراج وكل تعديل — الاسترجاع عند فتح البرنامج."""
import json, os, time
from . import logic

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'session_autosave.json')


def save(path, result, images):
    data = {
        'time': time.strftime('%Y-%m-%d %H:%M'),
        'images': list(images),
        'result': {**{k: v for k, v in result.items() if k != 'colors'},
                   'colors': logic.colors_to_list(result.get('colors', {}))},
    }
    tmp = path + '.tmp'
    json.dump(data, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    os.replace(tmp, path)


def load(path):
    if not os.path.exists(path):
        return None
    try:
        data = json.load(open(path, encoding='utf-8'))
        data['result']['colors'] = logic.colors_from_list(data['result'].get('colors', []))
        return data
    except Exception:
        return None


def clear(path):
    try:
        os.remove(path)
    except OSError:
        pass
