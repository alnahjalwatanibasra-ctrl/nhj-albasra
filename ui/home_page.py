# -*- coding: utf-8 -*-
"""الشاشة الرئيسية: خلفية تركوازية + مخطوطة بيضاء + بطاقتا ميزتين (أيقونة + اسم).
جمالياً: بطاقات بيضاء عائمة بحافة ليمونية سفلية تتوهج، ترتفع قليلاً عند المرور."""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QGraphicsDropShadowEffect)
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtCore import Qt, Signal
from .app import APP_DIR


def _asset(name):
    return os.path.join(APP_DIR, 'assets', name)


class FeatureCard(QFrame):
    """بطاقة ميزة قابلة للنقر: أيقونة فوق الاسم، حافة ليمونية، ارتفاع عند المرور."""
    clicked = Signal()

    def __init__(self, icon_file, name):
        super().__init__()
        self.setObjectName('featcard')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(268, 200)
        self._base_shadow()
        v = QVBoxLayout(self); v.setAlignment(Qt.AlignCenter); v.setSpacing(16)
        icon = QLabel(); icon.setAlignment(Qt.AlignCenter)
        pm = QPixmap(_asset(icon_file))
        if not pm.isNull():
            icon.setPixmap(pm.scaledToWidth(60, Qt.SmoothTransformation))
        icon.setStyleSheet('background: transparent;')
        lbl = QLabel(name); lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet('background: transparent; color: #0B6663;'
                          ' font-size: 20px; font-weight: 700;')
        v.addWidget(icon); v.addWidget(lbl)
        self._apply(False)

    def _base_shadow(self):
        self._sh = QGraphicsDropShadowEffect(self)
        self._sh.setColor(QColor(6, 60, 58, 60))
        self.setGraphicsEffect(self._sh)

    def _apply(self, hover):
        accent = '#E6EC26' if hover else '#19BBBD'
        self.setStyleSheet(
            '#featcard { background: #FFFFFF; border: 1px solid #D3E3E2;'
            f' border-bottom: 4px solid {accent}; border-radius: 16px; }}')
        self._sh.setBlurRadius(38 if hover else 24)
        self._sh.setOffset(0, 12 if hover else 7)

    def enterEvent(self, e):
        self._apply(True); super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply(False); super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


class HomePage(QWidget):
    featureRequested = Signal(str)      # 'sadir' أو 'text'

    def __init__(self):
        super().__init__()
        self.setObjectName('homebg')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            '#homebg { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
            ' stop:0 #159390, stop:1 #0C7370); }')

        v = QVBoxLayout(self); v.setAlignment(Qt.AlignCenter)
        v.setContentsMargins(40, 24, 40, 40); v.setSpacing(0)

        calli = QLabel(); calli.setAlignment(Qt.AlignCenter)
        calli.setStyleSheet('background: transparent;')
        pix = QPixmap(_asset('calligraphy.png'))
        if not pix.isNull():
            calli.setPixmap(pix.scaledToWidth(430, Qt.SmoothTransformation))
        v.addWidget(calli)
        v.addSpacing(14)

        rule = QFrame(); rule.setFixedSize(430, 3)   # بعرض المخطوطة (بطول العبارة)
        rule.setStyleSheet('background: #E6EC26; border: none; border-radius: 2px;')
        v.addWidget(rule, 0, Qt.AlignHCenter)
        v.addSpacing(14)

        title = QLabel('ماذا تريد أن تفعل اليوم؟')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('background: transparent; color: #FFFFFF;'
                            ' font-size: 22px; font-weight: 700;')
        v.addWidget(title)
        v.addSpacing(30)

        row = QHBoxLayout(); row.setSpacing(34); row.setAlignment(Qt.AlignCenter)
        self.card_sadir = FeatureCard('ic_sadir.png', 'سجل الصادر')
        self.card_text = FeatureCard('ic_text.png', 'استخراج النصوص')
        self.card_sadir.clicked.connect(lambda: self.featureRequested.emit('sadir'))
        self.card_text.clicked.connect(lambda: self.featureRequested.emit('text'))
        row.addWidget(self.card_sadir); row.addWidget(self.card_text)
        v.addLayout(row)

        foot = QLabel('تحالف النهج الوطني')
        foot.setAlignment(Qt.AlignCenter)
        foot.setStyleSheet('background: transparent; color: #AEDEDC;'
                           ' font-size: 12px; font-weight: 600;')
        foot_city = QLabel('البصرة')
        foot_city.setAlignment(Qt.AlignCenter)
        foot_city.setStyleSheet('background: transparent; color: #AEDEDC;'
                                ' font-size: 12px; font-weight: 600;')
        v.addSpacing(30)
        v.addWidget(foot)
        v.addWidget(foot_city)
