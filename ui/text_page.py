# -*- coding: utf-8 -*-
"""شاشة «استخراج النصوص»: صور ⟵ نص خام قابل للنسخ. لا مرجع، لا إعدادات، لا جلسات."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFileDialog, QFrame, QPlainTextEdit, QApplication,
                               QMessageBox, QListWidgetItem)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QTimer
from .start_page import DropList
import os


class TextPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(28, 18, 28, 14); v.setSpacing(10)

        card = QFrame(); card.setProperty('class', 'card')
        c = QVBoxLayout(card)
        self.images_list = DropList()
        self.images_list.filesDropped.connect(self.add_images)
        row = QHBoxLayout()
        b_pick = QPushButton('اختيار صور...'); b_pick.setObjectName('ghost')
        b_pick.clicked.connect(self._pick)
        b_del = QPushButton('حذف المحددة'); b_del.setObjectName('danger')
        b_del.clicked.connect(self._remove_selected)
        row.addWidget(b_pick); row.addWidget(b_del); row.addStretch(1)
        c.addWidget(self.images_list); c.addLayout(row)
        v.addWidget(card)

        h = QHBoxLayout(); h.addStretch(1)
        self.btn_go = QPushButton('استخراج النصوص'); self.btn_go.setObjectName('primary')
        self.btn_go.clicked.connect(self._start)
        h.addWidget(self.btn_go)
        self.btn_clear = QPushButton('صور جديدة'); self.btn_clear.setObjectName('ghost')
        self.btn_clear.clicked.connect(self._reset)
        h.addWidget(self.btn_clear); h.addStretch(1)
        v.addLayout(h)

        self.lbl_status = QLabel(''); self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet('color:#7d8587')
        v.addWidget(self.lbl_status)

        bar = QHBoxLayout()
        self.btn_copy = QPushButton('نسخ الكل')
        self.btn_copy.clicked.connect(self._copy_all)
        self.btn_copy.setEnabled(False)
        bar.addWidget(self.btn_copy); bar.addStretch(1)
        v.addLayout(bar)
        self.txt = QPlainTextEdit(); self.txt.setReadOnly(True)
        self.txt.setPlaceholderText('النص المستخرج سيظهر هنا — حدد ما تريد بالمؤشر أو انسخ الكل')
        v.addWidget(self.txt, 1)

        self.worker = None
        self._secs = 0
        self._timer = QTimer(self); self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._refresh()

    # -- الصور --
    def images(self):
        return [self.images_list.item(i).data(Qt.UserRole)
                for i in range(self.images_list.count())]

    def add_images(self, paths):
        for p in paths:
            if p and p not in self.images():
                pix = QPixmap(p)
                icon = QIcon(pix.scaled(96, 96, Qt.KeepAspectRatio,
                                        Qt.SmoothTransformation)) if not pix.isNull() else QIcon()
                item = QListWidgetItem(icon, os.path.basename(p)[:16])
                item.setData(Qt.UserRole, p)
                self.images_list.addItem(item)
        self._refresh()

    def _pick(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'اختر الصور', '',
                                                'صور (*.jpg *.jpeg *.png)')
        self.add_images(paths)

    def _remove_selected(self):
        for it in self.images_list.selectedItems():
            self.images_list.takeItem(self.images_list.row(it))
        self._refresh()

    def _reset(self):
        self.images_list.clear()
        self.txt.clear()
        self.lbl_status.setText('')
        self._refresh()

    def _refresh(self):
        busy = self.worker is not None and self.worker.isRunning()
        self.btn_go.setEnabled(bool(self.images()) and not busy)
        self.btn_copy.setEnabled(bool(self.txt.toPlainText()))

    # -- الاستخراج --
    def _start(self):
        from .text_worker import TextWorker
        self.txt.clear()
        self.worker = TextWorker(self.images())
        self.worker.progressed.connect(self.lbl_status.setText)
        self.worker.finished_ok.connect(self._done)
        self.worker.failed.connect(self._failed)
        self._secs = 0; self._timer.start()
        self.btn_go.setEnabled(False)
        self.lbl_status.setText('جاري التحضير...')
        self.worker.start()

    def _tick(self):
        self._secs += 1
        m, s = divmod(self._secs, 60)
        cur = self.lbl_status.text().split('  —  ')[0]
        self.lbl_status.setText(f'{cur}  —  الوقت المنقضي: {m}:{s:02d}')

    def _done(self, text):
        self._timer.stop()
        self.txt.setPlainText(text)
        self.lbl_status.setText('اكتمل الاستخراج ✓')
        self._refresh()

    def _failed(self, err):
        self._timer.stop()
        self._refresh()
        if err == 'CANCELLED':
            self.lbl_status.setText(''); return
        msg = 'تعذر الاستخراج الآن — أعد المحاولة لاحقاً.'
        if '429' in err:
            msg = 'انتهت حصة اليوم لكل النماذج — أعد المحاولة غداً.'
        if 'URLError' in err or 'getaddrinfo' in err or 'ConnectionReset' in err:
            msg = 'لا يوجد اتصال بالإنترنت — تحقق من الشبكة ثم أعد المحاولة.'
        self.lbl_status.setText('')
        QMessageBox.warning(self, 'خطأ', msg)

    def _copy_all(self):
        QApplication.clipboard().setText(self.txt.toPlainText())
        self.lbl_status.setText('نُسخ النص كاملاً إلى الحافظة ✓')

    def busy(self):
        return self.worker is not None and self.worker.isRunning()
