# -*- coding: utf-8 -*-
"""اقتراحات هواتف Word — تأكيد بشري لكل سطر، مع فتح ملف المصدر للتحقق."""
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QScrollArea, QWidget)
from PySide6.QtCore import Signal


class PhonesDialog(QDialog):
    accepted_one = Signal(int, str)          # (رقم الصف، الهاتف)

    def __init__(self, suggestions, word_folder, parent=None):
        super().__init__(parent)
        self.setWindowTitle('تأكيد الهواتف من ملفات الطلبات')
        self.resize(680, 420)
        self.word_folder = word_folder
        v = QVBoxLayout(self)
        v.addWidget(QLabel(f'وُجدت {len(suggestions)} اقتراحات — '
                           'تحقق من ملف المصدر قبل الاعتماد:'))
        area = QScrollArea(); area.setWidgetResizable(True)
        inner = QWidget(); iv = QVBoxLayout(inner)
        self._rows = []
        for i, s in enumerate(suggestions):
            f = QFrame(); f.setProperty('class', 'card')
            h = QHBoxLayout(f)
            h.addWidget(QLabel(
                f"<b>{s['name']}</b> ← {s['phone']} "
                f"<span style='color:#8a9294;font-size:11px'>({s['file']} — تشابه {s['score']}%)</span>"), 1)
            b_ok = QPushButton('✓ اعتماد')
            b_ok.clicked.connect(lambda _, k=i: self._accept(k))
            b_open = QPushButton('فتح الملف'); b_open.setObjectName('ghost')
            b_open.clicked.connect(lambda _, k=i: self._open(k))
            b_no = QPushButton('✗'); b_no.setObjectName('danger')
            b_no.clicked.connect(lambda _, k=i: self._reject(k))
            for b in (b_ok, b_open, b_no):
                h.addWidget(b)
            iv.addWidget(f)
            self._rows.append((f, s))
        iv.addStretch(1)
        area.setWidget(inner)
        v.addWidget(area, 1)
        close = QPushButton('إغلاق'); close.setObjectName('ghost')
        close.clicked.connect(self.accept)
        v.addWidget(close)

    def _accept(self, k):
        f, s = self._rows[k]
        self.accepted_one.emit(s['row'], s['phone'])
        f.setDisabled(True)

    def _reject(self, k):
        self._rows[k][0].setDisabled(True)

    def _open(self, k):
        _, s = self._rows[k]
        for root, _, files in os.walk(self.word_folder or '.'):
            if s['file'] in files:
                os.startfile(os.path.join(root, s['file']))
                return
