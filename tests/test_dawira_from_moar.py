# -*- coding: utf-8 -*-
"""استنتاج الدائرة من المعرف (كل معرف تابع لدائرة معروفة غالباً)."""
from core.reference import Reference


class _FakeRef(Reference):
    def __init__(self, rows):
        # نبني الحد الأدنى يدوياً دون فتح ملف Excel
        self.rows = rows
        from collections import Counter
        from core.reference import norm
        self.moar_freq = Counter(norm(x.get('moar', '')) for x in rows if x.get('moar'))
        pairs = {}
        for x in rows:
            m = norm(str(x.get('moar') or ''))
            d = str(x.get('dawira') or '').strip()
            if m and d:
                pairs.setdefault(m, Counter())[d] += 1
        self.moar_dawira = {}
        for m, c in pairs.items():
            top, n = c.most_common(1)[0]
            self.moar_dawira[m] = (top, n / sum(c.values()))


REF = _FakeRef([
    {'moar': 'مكتب الصادق', 'dawira': 'الدائرة الخامسة'},
    {'moar': 'مكتب الصادق', 'dawira': 'الدائرة الخامسة'},
    {'moar': 'محمد الاسدي', 'dawira': 'الدائرة الثالثة'},
    {'moar': 'محمد الاسدي', 'dawira': 'الدائرة الثالثة'},
    {'moar': 'محمد الاسدي', 'dawira': 'الدائرة الخامسة'},
])


def test_decisive_moar():
    d, decisive = REF.dawira_for_moar('مكتب الصادق')
    assert d == 'الدائرة الخامسة' and decisive


def test_ambiguous_moar_flagged():
    d, decisive = REF.dawira_for_moar('محمد الاسدي')
    assert d == 'الدائرة الثالثة' and not decisive     # 2/3 أقل من 80%


def test_fuzzy_spelling():
    d, _ = REF.dawira_for_moar('مكتب صادق')            # إملاء مختلف قليلاً
    assert d == 'الدائرة الخامسة'


def test_unknown_moar():
    assert REF.dawira_for_moar('معرف غريب تماماً') is None
    assert REF.dawira_for_moar('') is None
