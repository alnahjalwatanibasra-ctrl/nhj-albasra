# -*- coding: utf-8 -*-
"""خيط المسح الضوئي — المسح يأخذ ثوانٍ فلا نجمّد الواجهة."""
from PySide6.QtCore import QThread, Signal
from core import scanner


class ScanWorker(QThread):
    progressed = Signal(str)
    scanned = Signal(str)      # مسار الصورة الممسوحة
    failed = Signal(str)       # رسالة عربية

    def run(self):
        try:
            path = scanner.scan_to_file(progress=self.progressed.emit)
            self.scanned.emit(path)
        except scanner.ScannerError as e:
            self.failed.emit(str(e))
        except Exception:
            self.failed.emit('حدث خطأ غير متوقع أثناء المسح — أعد المحاولة.')
