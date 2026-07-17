# -*- coding: utf-8 -*-
"""① صور السجل  ② الملفات الثلاثة  ③ زر ابدأ — بخطوات مرقّمة تذكيرية."""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QListWidget, QListWidgetItem, QFileDialog, QFrame)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, Signal
from . import logic

HINT = 'الصور الأوضح تعطي نتائج أدق — أرسلها من واتساب كملف لا كصورة'
IMG_EXTS = ('.jpg', '.jpeg', '.png')


def _step_label(n, text):
    lbl = QLabel(f' {n}  {text} ')
    lbl.setStyleSheet('font-weight:700; color:#0F7D7A; font-size:14px;'
                      'background:#DFF1F0; border-radius:8px; padding:4px 12px;')
    return lbl


class DropList(QListWidget):
    """قائمة مصغّرات تقبل إفلات الصور من المستكشف وإعادة الترتيب داخلياً."""
    filesDropped = Signal(list)
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(96, 96))
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setFixedHeight(150)
        self.model().rowsMoved.connect(lambda *a: self.changed.emit())

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in e.mimeData().urls()
                     if u.toLocalFile().lower().endswith(IMG_EXTS)]
            if paths:
                self.filesDropped.emit(paths)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)
            self.changed.emit()


class StartPage(QWidget):
    startRequested = Signal(list, dict)     # (صور، مسارات)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        v = QVBoxLayout(self); v.setContentsMargins(28, 18, 28, 18); v.setSpacing(12)

        v.addWidget(_step_label('①', 'صور السجل'), 0, Qt.AlignLeft)
        card1 = QFrame(); card1.setProperty('class', 'card')
        c1 = QVBoxLayout(card1)
        self.images_list = DropList()
        self.images_list.filesDropped.connect(self.add_images)
        self.images_list.changed.connect(self._refresh)
        btn_pick = QPushButton('اختيار صور...'); btn_pick.setObjectName('ghost')
        btn_pick.clicked.connect(self._pick_images)
        btn_del = QPushButton('حذف المحددة'); btn_del.setObjectName('danger')
        btn_del.clicked.connect(self._remove_selected)
        row = QHBoxLayout(); row.addWidget(btn_pick); row.addWidget(btn_del); row.addStretch(1)
        hint = QLabel(HINT); hint.setStyleSheet('color:#8a9294; font-size:11px')
        c1.addWidget(self.images_list); c1.addLayout(row); c1.addWidget(hint)
        v.addWidget(card1)

        v.addWidget(_step_label('②', 'الملفات'), 0, Qt.AlignLeft)
        card2 = QFrame(); card2.setProperty('class', 'card')
        c2 = QVBoxLayout(card2)
        self.lbl_reference = QLabel(); self.lbl_prev = QLabel(); self.lbl_word = QLabel()
        for key, lbl, title, isdir in (
                ('reference_path', self.lbl_reference, 'الملف المرجعي (اختياري — يُنصح به بشدة)', False),
                ('prev_register_path', self.lbl_prev, 'السجل السابق (اختياري)', False),
                ('word_folder', self.lbl_word, 'مجلد طلبات Word (اختياري)', True)):
            r = QHBoxLayout()
            t = QLabel(title + ':')
            t.setMinimumWidth(240)          # عرض طبيعي بلا قصّ لأطول العناوين
            r.addWidget(t)
            r.addWidget(lbl, 1)
            b = QPushButton('تغيير'); b.setObjectName('ghost')
            b.clicked.connect(lambda _, k=key, d=isdir: self._change_path(k, d))
            r.addWidget(b)
            c2.addLayout(r)
        v.addWidget(card2)

        h = QHBoxLayout(); h.addStretch(1)
        step3 = _step_label('③', '')
        h.addWidget(step3)
        self.btn_start = QPushButton('ابدأ الاستخراج'); self.btn_start.setObjectName('primary')
        self.btn_start.clicked.connect(self._emit_start)
        h.addWidget(self.btn_start); h.addStretch(1)
        v.addLayout(h)
        self.lbl_reason = QLabel(); self.lbl_reason.setAlignment(Qt.AlignCenter)
        self.lbl_reason.setStyleSheet('color:#8a9294')
        v.addWidget(self.lbl_reason)
        v.addStretch(1)
        self._refresh()

    # -- الصور --
    def images(self):
        return [self.images_list.item(i).data(Qt.UserRole)
                for i in range(self.images_list.count())]

    def add_images(self, paths):
        from PySide6.QtGui import QPixmap
        for p in paths:
            if p and p not in self.images():
                # مصغّر يُبنى مرة واحدة — تحميل الصورة الكاملة عند كل رسم كان سبب الثقل
                pix = QPixmap(p)
                icon = QIcon(pix.scaled(96, 96, Qt.KeepAspectRatio,
                                        Qt.SmoothTransformation)) if not pix.isNull() else QIcon()
                it = QListWidgetItem(icon, os.path.basename(p)[:16])
                it.setData(Qt.UserRole, p)
                self.images_list.addItem(it)
        self._refresh()

    def remove_image(self, idx):
        self.images_list.takeItem(idx); self._refresh()

    def _remove_selected(self):
        for it in self.images_list.selectedItems():
            self.images_list.takeItem(self.images_list.row(it))
        self._refresh()

    def _pick_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'اختر صور السجل', '',
                                                'صور (*.jpg *.jpeg *.png)')
        self.add_images(paths)

    # -- المسارات --
    def set_reference(self, path):
        self.settings['reference_path'] = path; self._refresh()

    def _change_path(self, key, isdir):
        if isdir:
            p = QFileDialog.getExistingDirectory(self, 'اختر المجلد')
        else:
            p, _ = QFileDialog.getOpenFileName(self, 'اختر الملف', '', 'Excel (*.xlsx)')
        if p:
            self.settings[key] = p
            from core import config
            config.save_settings(self.settings)
            self._refresh()

    def _path_text(self, key):
        p = self.settings.get(key, '')
        if not p:
            return '<span style="color:#8a9294">لم يُحدد</span>'
        name = os.path.basename(p)
        if not os.path.exists(p):
            return f'<span style="color:#A32D2D">⚠ {name} — غير موجود</span>'
        return name

    def _refresh(self):
        self.lbl_reference.setText(self._path_text('reference_path'))
        self.lbl_prev.setText(self._path_text('prev_register_path'))
        self.lbl_word.setText(self._path_text('word_folder'))
        ok, why = logic.can_start(self.images(), self.settings.get('reference_path', ''))
        self.btn_start.setEnabled(ok)
        self.lbl_reason.setText(why)

    def _emit_start(self):
        if not self.settings.get('reference_path', ''):
            from PySide6.QtWidgets import QMessageBox
            btn = QMessageBox.question(
                self, 'بدون ملف مرجعي',
                'لم تحدد الملف المرجعي — لن تُصحَّح الأسماء والهواتف والمواضيع تلقائياً،\n'
                'وستعتمد النتيجة على قراءة الصورة وحدها (دقة أقل بكثير).\n\nالمتابعة على أي حال؟')
            if btn != QMessageBox.StandardButton.Yes:
                return
        self.startRequested.emit(self.images(), {
            'reference': self.settings.get('reference_path', ''),
            'prev_register': self.settings.get('prev_register_path', '') or None,
            'word_folder': self.settings.get('word_folder', '') or None,
        })
