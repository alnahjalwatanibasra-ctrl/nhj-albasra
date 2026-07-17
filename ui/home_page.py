# -*- coding: utf-8 -*-
"""الشاشة الرئيسية: بطاقات الميزات — أسماء فقط بلا شرح (قرار المستخدم)."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

CARD_QSS = ('QPushButton { background: #FCFEFE; color: #13908C; border: 2px solid #19BBBD;'
            ' border-radius: 14px; font-size: 20px; font-weight: 600;'
            ' min-width: 220px; min-height: 130px; }'
            'QPushButton:hover { background: #F4FBFB; border-color: #13908C; }')


class HomePage(QWidget):
    featureRequested = Signal(str)      # 'sadir' أو 'text'

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setAlignment(Qt.AlignCenter); v.setSpacing(26)
        title = QLabel('ماذا تريد أن تفعل اليوم؟')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size:17px; color:#41494B')
        v.addWidget(title)
        h = QHBoxLayout(); h.setSpacing(24); h.setAlignment(Qt.AlignCenter)
        self.btn_sadir = QPushButton('سجل الصادر')
        self.btn_text = QPushButton('استخراج النصوص')
        for name, btn in (('sadir', self.btn_sadir), ('text', self.btn_text)):
            btn.setStyleSheet(CARD_QSS)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self.featureRequested.emit(n))
            h.addWidget(btn)
        v.addLayout(h)
