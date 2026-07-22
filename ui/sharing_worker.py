# -*- coding: utf-8 -*-
"""عمّال QThread للمشاركة: تحديث الفهرس والتنزيل بلا تجميد الواجهة."""
from PySide6.QtCore import QThread, Signal


class RefreshWorker(QThread):
    done = Signal()

    def __init__(self, service):
        super().__init__()
        self.service = service

    def run(self):
        try:
            self.service.refresh()
        except Exception:
            pass
        self.done.emit()


class DownloadWorker(QThread):
    progressed = Signal(int, int)      # (done, total)
    finished_ok = Signal(str)          # المسار المحفوظ
    failed = Signal(str)

    def __init__(self, service, row):
        super().__init__()
        self.service = service
        self.row = row

    def run(self):
        try:
            saved = self.service.download(
                self.row, progress=lambda d, t: self.progressed.emit(d, t))
            self.finished_ok.emit(saved)
        except Exception as e:
            self.failed.emit(type(e).__name__)
