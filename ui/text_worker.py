# -*- coding: utf-8 -*-
"""خيط ميزة «استخراج النصوص»: الصور بالتوازي ⟵ نص واحد بفواصل صفحات."""
import threading, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QThread, Signal
from core import gemini_ocr, config, pipeline


def join_pages(texts):
    """يجمع نصوص الصفحات بفاصل واضح — صفحة واحدة تُعاد كما هي بلا فاصل."""
    if len(texts) == 1:
        return texts[0]
    parts = []
    for i, t in enumerate(texts):
        if i:
            parts.append(f'\n——— الصفحة {i + 1} ———\n')
        parts.append(t)
    return '\n'.join(parts).strip()


class TextWorker(QThread):
    progressed = Signal(str)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, images):
        super().__init__()
        self.images = list(images)
        self.cancel = threading.Event()

    def stop(self):
        self.cancel.set()

    def run(self):
        try:
            settings = config.load_settings()
            key = config.get_key(settings)
            models = settings['gemini_models']
            texts = [None] * len(self.images)
            if len(self.images) > 1:
                self.progressed.emit('استخراج %d صور بالتوازي...' % len(self.images))

            def work(i, img):
                if self.cancel.is_set():
                    raise pipeline.CancelledError()
                self.progressed.emit('استخراج الصورة %d/%d' % (i + 1, len(self.images)))
                return i, gemini_ocr.extract_text_image(key, img, models,
                                                        progress=self.progressed.emit)
            with ThreadPoolExecutor(max_workers=min(3, max(1, len(self.images)))) as ex:
                futs = [ex.submit(work, i, img) for i, img in enumerate(self.images)]
                done = 0
                for f in as_completed(futs):
                    i, res = f.result()
                    texts[i] = res['text']
                    done += 1
                    if len(self.images) > 1:
                        self.progressed.emit('اكتملت %d من %d صور' % (done, len(self.images)))
            if self.cancel.is_set():
                self.failed.emit('CANCELLED'); return
            self.finished_ok.emit(join_pages(texts))
        except pipeline.CancelledError:
            self.failed.emit('CANCELLED')
        except Exception:
            self.failed.emit(traceback.format_exc(limit=2))
