# -*- coding: utf-8 -*-
"""النافذة الرئيسية: شريط علوي بهوية النهج + ثلاث صفحات (بداية/تقدم/مراجعة)."""
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QToolButton, QStackedWidget)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from .app import APP_DIR

TITLE = 'سجل الصادر — تحالف النهج الوطني'


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITLE)
        self.resize(1100, 750)
        root = QWidget(); self.setCentralWidget(root)
        lay = QVBoxLayout(root); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        lay.addWidget(self._topbar())
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self._build_pages()

    def _topbar(self):
        bar = QWidget(); bar.setObjectName('topbar'); bar.setFixedHeight(52)
        h = QHBoxLayout(bar); h.setContentsMargins(14, 6, 14, 6)
        logo = QLabel()
        pix = QPixmap(os.path.join(APP_DIR, 'assets', 'logo.jpg'))
        if not pix.isNull():
            logo.setPixmap(pix.scaledToHeight(38, Qt.SmoothTransformation))
        h.addWidget(logo)
        h.addWidget(QLabel(TITLE))
        h.addStretch(1)
        self.btn_settings = QToolButton(); self.btn_settings.setText('⚙  الإعدادات')
        h.addWidget(self.btn_settings)
        return bar

    def _build_pages(self):
        from core import config
        self.settings = config.load_settings()
        from .start_page import StartPage
        from .progress_page import ProgressPage
        self.start_page = StartPage(self.settings)
        self.progress_page = ProgressPage()
        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.progress_page)
        self.start_page.startRequested.connect(self._start_extract)
        self.progress_page.cancelRequested.connect(self._cancel_extract)
        self.worker = None
        self._last_images = []

    def _start_extract(self, images, paths):
        from .worker import ExtractWorker
        self.worker = ExtractWorker(images, paths['reference'],
                                    paths['prev_register'], paths['word_folder'])
        self.worker.progressed.connect(self.progress_page.set_status)
        self.worker.finished_ok.connect(self._extract_done)
        self.worker.failed.connect(self._extract_failed)
        self.progress_page.set_status('جاري التحضير...')
        self.stack.setCurrentWidget(self.progress_page)
        self.worker.start()

    def _cancel_extract(self):
        if self.worker:
            self.worker.stop()
            self.progress_page.set_status('جاري الإيقاف...')

    def _extract_done(self, res):
        self._last_images = list(self.worker.images)
        self.stack.setCurrentWidget(self.start_page)   # تُستبدل بصفحة المراجعة في المهمة 7

    def _extract_failed(self, err):
        from PySide6.QtWidgets import QMessageBox
        self.stack.setCurrentWidget(self.start_page)
        if err == 'CANCELLED':
            return
        msg = 'تعذر الاستخراج الآن — أعد المحاولة لاحقاً.'
        if '429' in err:
            msg = 'انتهت حصة اليوم لكل النماذج — أعد المحاولة غداً.'
        if 'URLError' in err or 'ConnectionReset' in err or 'getaddrinfo' in err:
            msg = 'لا يوجد اتصال بالإنترنت — تحقق من الشبكة ثم أعد المحاولة.'
        QMessageBox.warning(self, 'خطأ', msg)
