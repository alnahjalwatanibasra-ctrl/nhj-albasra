# -*- coding: utf-8 -*-
"""نقطة تشغيل التطبيق: QApplication + الثيم + RTL + الأيقونة."""
import os, sys, glob
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFontDatabase, QFont
from PySide6.QtCore import Qt, QLocale

# الموارد (الشعار، الخطوط): داخل exe تكون في مجلد التفريغ _MEIPASS؛ تطويراً في جذر المشروع
if getattr(sys, 'frozen', False):
    APP_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_brand_fonts():
    """يحمّل خط «نور» (هوية النهج) من ملفات البرنامج — يعمل حتى على جهاز لم يثبّته."""
    for f in glob.glob(os.path.join(APP_DIR, 'assets', 'fonts', '*.ttf')):
        QFontDatabase.addApplicationFont(f)


def create_app(argv=None):
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    QLocale.setDefault(QLocale(QLocale.Arabic, QLocale.Iraq))
    app.setWindowIcon(QIcon(os.path.join(APP_DIR, 'assets', 'logo.png')))
    _load_brand_fonts()
    # خط نور محوَّل قديم — بلا تنعيم يظهر مبكسلاً؛ نفرض التنعيم ونلغي الـ hinting
    f = QFont('Noor')
    f.setPixelSize(15)
    f.setStyleStrategy(QFont.PreferAntialias)
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(f)
    qss = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'theme.qss')
    app.setStyleSheet(open(qss, encoding='utf-8').read())
    return app


def main():
    app = create_app()
    from .main_window import MainWindow
    win = MainWindow()
    win.show()
    return app.exec()
