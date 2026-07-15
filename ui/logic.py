# -*- coding: utf-8 -*-
"""منطق الواجهة الخالص (بلا Qt) — قابل للاختبار مباشرة."""
import os
from core.corrections import to_western_digits

NUM_H, PHONE_H = 'رقم الكتاب', 'رقم الهاتف'


def can_start(images, reference_path):
    """هل يجوز تفعيل زر «ابدأ الاستخراج»؟ يعيد (نعم/لا، سبب التعطيل)."""
    if not images:
        return False, 'أضف صور السجل أولاً'
    if not reference_path:
        return False, 'اختر الملف المرجعي'
    if not os.path.exists(reference_path):
        return False, 'الملف المرجعي غير موجود'
    return True, ''


def export_filename(rows):
    """سجل_الصادر_<أول رقم>-<آخر رقم>.xlsx"""
    nums = [to_western_digits(r.get(NUM_H, '')) for r in rows]
    nums = [n for n in nums if n.isdigit()]
    if not nums:
        return 'سجل_الصادر.xlsx'
    return f'سجل_الصادر_{nums[0]}-{nums[-1]}.xlsx'


def colors_to_list(colors):
    return [[i, h, k] for (i, h), k in colors.items()]


def colors_from_list(ser):
    return {(i, h): k for i, h, k in ser}


def unmatched_rows(matched):
    return [i for i, m in enumerate(matched) if not m]


def missing_phone_rows(rows, matched):
    """صفوف بلا هاتف موثوق: فارغ، أو «لا يوجد» في صف غير مطابَق للمرجع."""
    out = []
    for i, r in enumerate(rows):
        v = str(r.get(PHONE_H, '') or '').strip()
        if not to_western_digits(v):
            if v == 'لا يوجد' and matched[i]:
                continue      # المرجع يؤكد أن لا هاتف له — ليست ناقصة
            out.append(i)
    return out
