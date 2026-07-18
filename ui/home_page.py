# -*- coding: utf-8 -*-
"""الشاشة الرئيسية: بطاقات الميزات — أسماء فقط بلا شرح (قرار المستخدم).
جمالياً: هرمية عنوان + بطاقات بيضاء بظل ناعم وشريط سفلي تركوازي يتوهج ليمونياً عند المرور."""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QGraphicsDropShadowEffect)
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtCore import Qt, Signal
from .app import APP_DIR

CARD_QSS = ('QPushButton { background: #FFFFFF; color: #0F7D7A;'
            ' border: 1px solid #DCE7E6; border-bottom: 4px solid #19BBBD;'
            ' border-radius: 14px; font-size: 21px; font-weight: 700;'
            ' min-width: 240px; min-height: 150px; }'
            'QPushButton:hover { background: #FBFEF2; border-bottom-color: #E6EC26;'
            ' color: #0B6663; }'
            'QPushButton:pressed { background: #F2F8F1; }')


def _soft_shadow(w):
    e = QGraphicsDropShadowEffect(w)
    e.setBlurRadius(28)
    e.setOffset(0, 6)
    e.setColor(QColor(15, 125, 122, 42))
    w.setGraphicsEffect(e)


class HomePage(QWidget):
    featureRequested = Signal(str)      # 'sadir' أو 'text'

    def __init__(self):
        super().__init__()
        # خلفية تركوازية متدرّجة للشاشة الرئيسية (المخطوطة البيضاء تظهر عليها)
        self.setObjectName('homebg')
        self.setStyleSheet(
            '#homebg { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
            ' stop:0 #159390, stop:1 #0E7B78); }')
        v = QVBoxLayout(self); v.setAlignment(Qt.AlignCenter); v.setSpacing(10)
        calli = QLabel(); calli.setAlignment(Qt.AlignCenter)
        pix = QPixmap(os.path.join(APP_DIR, 'assets', 'calligraphy.png'))
        if not pix.isNull():
            calli.setPixmap(pix.scaledToWidth(440, Qt.SmoothTransformation))
        v.addWidget(calli)
        v.addSpacing(6)
        kicker = QLabel('تحالف النهج الوطني — البصرة')
        kicker.setAlignment(Qt.AlignCenter)
        kicker.setStyleSheet('font-size: 12px; color: #B9E6E4; font-weight: 600;'
                             ' background: transparent;')
        title = QLabel('ماذا تريد أن تفعل اليوم؟')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size: 23px; color: #FFFFFF; font-weight: 700;'
                            ' background: transparent;')
        v.addWidget(kicker)
        v.addWidget(title)
        v.addSpacing(22)
        h = QHBoxLayout(); h.setSpacing(28); h.setAlignment(Qt.AlignCenter)
        self.btn_sadir = QPushButton('سجل الصادر')
        self.btn_text = QPushButton('استخراج النصوص')
        for name, btn in (('sadir', self.btn_sadir), ('text', self.btn_text)):
            btn.setStyleSheet(CARD_QSS)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self.featureRequested.emit(n))
            _soft_shadow(btn)
            h.addWidget(btn)
        v.addLayout(h)
