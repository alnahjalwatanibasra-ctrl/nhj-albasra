# -*- coding: utf-8 -*-
"""صفحة التقدم: حالة نصية + شريط + زر إيقاف."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QProgressBar, QPushButton)
from PySide6.QtCore import Qt, Signal


class ProgressPage(QWidget):
    cancelRequested = Signal()

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setAlignment(Qt.AlignCenter)
        self.lbl = QLabel('جاري التحضير...'); self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet('font-size:15px')
        self.bar = QProgressBar(); self.bar.setRange(0, 0); self.bar.setFixedWidth(420)
        steps = QLabel('ثم: مطابقة الملف المرجعي ← الترقيم ← جدول المراجعة')
        steps.setStyleSheet('color:#7d8587; font-size:11px'); steps.setAlignment(Qt.AlignCenter)
        btn = QPushButton('إيقاف'); btn.setObjectName('ghost')
        btn.clicked.connect(self.cancelRequested.emit)
        h = QHBoxLayout(); h.addStretch(1); h.addWidget(btn); h.addStretch(1)
        for wdg in (self.lbl, self.bar, steps):
            v.addWidget(wdg, 0, Qt.AlignCenter)
        v.addLayout(h)

    def set_status(self, msg):
        self.lbl.setText(msg)
