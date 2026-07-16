# -*- coding: utf-8 -*-
"""الترقيم المرسّى: صف ساقط من القراءة = فجوة ظاهرة، لا انزياح لكل ما بعده."""
from core.corrections import sequential_numbers_anchored
from ui import logic


def test_normal_sequence_unchanged():
    ocr = ['489', '490', '491', '492']
    assert sequential_numbers_anchored(ocr, 489) == [489, 490, 491, 492]


def test_dropped_row_creates_gap_not_shift():
    # القارئ أسقط كتاب 491: الصفوف المقروءة 489,490,492,493
    ocr = ['489', '490', '492', '493']
    assert sequential_numbers_anchored(ocr, 489) == [489, 490, 492, 493]


def test_single_misread_ignored():
    # قراءة شاذة منفردة (712) لا يؤكدها ما بعدها — تُتجاهل
    ocr = ['489', '712', '491', '492']
    assert sequential_numbers_anchored(ocr, 489) == [489, 490, 491, 492]


def test_unreadable_numbers_follow_sequence():
    ocr = ['489', '', '', '492']
    assert sequential_numbers_anchored(ocr, 489) == [489, 490, 491, 492]


def test_systematic_misread_ignored():
    # قراءة خاطئة منهجية متتالية (٤٩٨,٤٩٩ قُرئتا ٤٩١,٤٩٢) — إزاحة سالبة كبيرة تُتجاهل
    ocr = ['498', '491', '492', '501']
    assert sequential_numbers_anchored(ocr, 498) == [498, 499, 500, 501]


def test_number_gaps_detected():
    rows = [{'رقم الكتاب': '٤٨٩'}, {'رقم الكتاب': '٤٩٠'}, {'رقم الكتاب': '٤٩٢'}]
    assert logic.number_gaps(rows) == [(490, 492)]
    assert logic.number_gaps([{'رقم الكتاب': '٤٨٩'}]) == []


def test_weak_models_used():
    res = {'primary_model': 'a', 'models_used': ['a', 'lite']}
    assert logic.weak_models_used(res) == ['lite']
    assert logic.weak_models_used({'primary_model': 'a', 'models_used': ['a']}) == []
