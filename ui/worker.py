# -*- coding: utf-8 -*-
"""خيط الاستخراج: المحرّك كاملاً ثم اقتراحات هواتف Word — الواجهة لا تتجمد."""
import threading, traceback
from PySide6.QtCore import QThread, Signal
from core import pipeline, config, word_phones
from . import logic


class ExtractWorker(QThread):
    progressed = Signal(str)
    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, images, reference, prev_register=None, word_folder=None):
        super().__init__()
        self.images, self.reference = list(images), reference
        self.prev_register, self.word_folder = prev_register, word_folder
        self.cancel = threading.Event()

    def stop(self):
        self.cancel.set()

    def run(self):
        try:
            settings = config.load_settings()
            res = pipeline.run(self.images, self.reference,
                               prev_register_path=self.prev_register,
                               settings=settings,
                               progress=self.progressed.emit,
                               cache_path=None,
                               cancel=self.cancel)
            res['phone_suggestions'] = self._suggest_phones(res)
            self.finished_ok.emit(res)
        except pipeline.CancelledError:
            self.failed.emit('CANCELLED')
        except Exception:
            self.failed.emit(traceback.format_exc(limit=2))

    def _suggest_phones(self, res):
        """[{row, name, phone, file, score}] للصفوف الناقصة — تأكيد بشري لاحقاً."""
        if not self.word_folder:
            return []
        missing = logic.missing_phone_rows(res['rows'], res['matched'])
        if not missing:
            return []
        self.progressed.emit('بحث الهواتف في ملفات Word...')
        idx = word_phones.build_index(
            self.word_folder,
            progress=lambda i, n: self.progressed.emit(f'فهرسة ملفات Word {i}/{n}')
            if i % 100 == 0 else None)
        out = []
        name_h = 'اسم صاحب الكتاب'
        for i in missing:
            if self.cancel.is_set():
                break
            s = word_phones.suggest(idx, res['rows'][i].get(name_h, ''))
            if s:
                out.append({'row': i, **s})
        return out
