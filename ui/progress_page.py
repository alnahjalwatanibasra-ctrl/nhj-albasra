# -*- coding: utf-8 -*-
"""صفحة التقدم: حالة نصية + شريط + زر إيقاف."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QProgressBar, QPushButton)
from PySide6.QtCore import Qt, Signal, QTimer


class ProgressPage(QWidget):
    cancelRequested = Signal()

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setAlignment(Qt.AlignCenter)
        self.lbl = QLabel('جاري التحضير...'); self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet('font-size:15px')
        self.lbl_time = QLabel(''); self.lbl_time.setAlignment(Qt.AlignCenter)
        self.lbl_time.setStyleSheet('color:#7d8587; font-size:12px')
        self.bar = QProgressBar(); self.bar.setRange(0, 0); self.bar.setFixedWidth(420)
        steps = QLabel('الصورة الواحدة تستغرق نحو دقيقة عادةً — ثم المطابقة والترقيم فوريان')
        steps.setStyleSheet('color:#7d8587; font-size:11px'); steps.setAlignment(Qt.AlignCenter)
        btn = QPushButton('إيقاف'); btn.setObjectName('ghost')
        btn.clicked.connect(self.cancelRequested.emit)
        h = QHBoxLayout(); h.addStretch(1); h.addWidget(btn); h.addStretch(1)
        for wdg in (self.lbl, self.lbl_time, self.bar, steps):
            v.addWidget(wdg, 0, Qt.AlignCenter)
        v.addLayout(h)
        self._secs = 0
        self._timer = QTimer(self); self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def start_clock(self):
        self._secs = 0
        self.lbl_time.setText('')
        self._timer.start()

    def stop_clock(self):
        self._timer.stop()

    def _tick(self):
        self._secs += 1
        m, s = divmod(self._secs, 60)
        self.lbl_time.setText(f'الوقت المنقضي: {m}:{s:02d}')

    def set_status(self, msg):
        self.lbl.setText(msg)
