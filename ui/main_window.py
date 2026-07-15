# -*- coding: utf-8 -*-
"""النافذة الرئيسية: شريط علوي بهوية النهج + ثلاث صفحات (بداية/تقدم/مراجعة)."""
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QToolButton, QStackedWidget)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from .app import APP_DIR

TITLE = 'سجلات النهج — تحالف النهج الوطني'


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
        self.btn_settings.clicked.connect(self._open_settings)
        self._maybe_restore_session()

    def _open_settings(self):
        from .dialogs.settings_dialog import SettingsDialog
        SettingsDialog(self.settings, self).exec()
        self.start_page._refresh()

    def _maybe_restore_session(self):
        from PySide6.QtWidgets import QMessageBox
        from . import session
        data = session.load(session.DEFAULT_PATH)
        if not data:
            return
        n = len(data['result'].get('rows', []))
        btn = QMessageBox.question(
            self, 'جلسة سابقة',
            f'لديك جلسة لم تُصدَّر ({n} صفاً) من {data.get("time", "")} — استكمالها؟')
        if btn == QMessageBox.StandardButton.Yes:
            self._last_images = [p for p in data.get('images', []) if os.path.exists(p)]
            self.review_page.load_result(data['result'], self._last_images)
            self.stack.setCurrentWidget(self.review_page)
        else:
            session.clear(session.DEFAULT_PATH)

    def closeEvent(self, event):
        from PySide6.QtWidgets import QMessageBox
        from . import session
        if (self.stack.currentWidget() is self.review_page
                and session.load(session.DEFAULT_PATH) is not None):
            btn = QMessageBox.question(
                self, 'إغلاق',
                'المراجعة غير مصدَّرة (محفوظة تلقائياً وستُعرض عند الفتح القادم) — إغلاق؟')
            if btn != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()

    def _topbar(self):
        bar = QWidget(); bar.setObjectName('topbar'); bar.setFixedHeight(52)
        h = QHBoxLayout(bar); h.setContentsMargins(14, 6, 14, 6)
        logo = QLabel()
        pix = QPixmap(os.path.join(APP_DIR, 'assets', 'logo.png'))
        if not pix.isNull():
            logo.setPixmap(pix.scaledToHeight(38, Qt.SmoothTransformation))
        h.addWidget(logo)
        h.addWidget(QLabel(TITLE))
        h.addStretch(1)
        self.btn_settings = QToolButton(); self.btn_settings.setText('الإعدادات')
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
        from .review_page import ReviewPage
        self.review_page = ReviewPage()
        self.stack.addWidget(self.review_page)
        self.start_page.startRequested.connect(self._start_extract)
        self.progress_page.cancelRequested.connect(self._cancel_extract)
        self.review_page.changed.connect(self._autosave)
        self.review_page.phonesRequested.connect(self._open_phones)
        self.review_page.exportRequested.connect(self._do_export)
        self.worker = None
        self._last_images = []

    def _do_export(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from core.excel_export import export
        from core.corrections import to_western_digits
        from . import logic, session
        rows = self.review_page.current_rows()
        res = self.review_page.result
        # اقتراحات هواتف لم تُراجع: صفّها ما زال بلا خانات هاتف
        left = [s for s in res.get('phone_suggestions', [])
                if not to_western_digits(rows[s['row']].get('رقم الهاتف', ''))]
        if left:
            btn = QMessageBox.question(
                self, 'تنبيه',
                f'توجد {len(left)} اقتراحات هواتف لم تُؤكد — تصدير على أي حال؟')
            if btn != QMessageBox.StandardButton.Yes:
                return
        path, _ = QFileDialog.getSaveFileName(self, 'حفظ السجل',
                                              logic.export_filename(rows),
                                              'Excel (*.xlsx)')
        if not path:
            return
        try:
            export(path, res['headers'], rows, colors=res['colors'], source_col=False)
        except PermissionError:
            QMessageBox.warning(self, 'الملف مفتوح',
                                'أغلق الملف في Excel ثم أعد المحاولة.')
            return
        session.clear(session.DEFAULT_PATH)
        box = QMessageBox(self)
        box.setWindowTitle('تم التصدير')
        box.setText('تم حفظ السجل بنجاح.')
        b_file = box.addButton('فتح الملف', QMessageBox.ButtonRole.AcceptRole)
        b_dir = box.addButton('فتح المجلد', QMessageBox.ButtonRole.ActionRole)
        box.addButton('إغلاق', QMessageBox.ButtonRole.RejectRole)
        box.exec()
        import subprocess
        if box.clickedButton() is b_file:
            os.startfile(path)
        elif box.clickedButton() is b_dir:
            subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])

    def _open_phones(self):
        from .dialogs.phones_dialog import PhonesDialog
        sugs = self.review_page.result.get('phone_suggestions', [])
        dlg = PhonesDialog(sugs, self.settings.get('word_folder'), self)
        dlg.accepted_one.connect(
            lambda row, phone: self.review_page.set_cell(row, 'رقم الهاتف',
                                                         phone, color_key='word'))
        dlg.exec()

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
        self.review_page.load_result(res, self._last_images)
        self.stack.setCurrentWidget(self.review_page)
        self._autosave()

    def _autosave(self):
        from . import session
        if self.review_page.result is None:
            return
        res = dict(self.review_page.result)
        res['rows'] = self.review_page.current_rows()
        session.save(session.DEFAULT_PATH, res, self._last_images)

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
