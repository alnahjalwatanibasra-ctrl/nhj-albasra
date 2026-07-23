# -*- coding: utf-8 -*-
"""صفحة «مشاركة الملفات»: مساحة واحدة موحّدة تعرض كل الملفات (ملفاتي + ملفات
الزملاء) كأيقونات بالاسم تحتها، وتستقبل السحب والإفلات مباشرةً.
تعتمد على ShareService (P2P على الشبكة المحلية)."""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QListWidget, QListView, QListWidgetItem, QFileDialog,
                               QMessageBox, QProgressDialog)
from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QIcon
from .sharing_worker import RefreshWorker, DownloadWorker

_EXT_LABEL = {'xlsx': 'XLS', 'xls': 'XLS', 'docx': 'DOC', 'doc': 'DOC', 'pdf': 'PDF',
              'jpg': 'IMG', 'jpeg': 'IMG', 'png': 'IMG', 'txt': 'TXT'}


def _type_label(t):
    t = (t or '').lower()
    return _EXT_LABEL.get(t, (t[:4].upper() or 'FILE'))


def _file_icon(t, faded=False):
    """أيقونة نوع الملف: بطاقة تركوازية مدوّرة باختصار الامتداد (بأسلوب هوية النهج)."""
    S = 2
    pm = QPixmap(64 * S, 64 * S)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor('#9DC3C0' if faded else '#13908C'))
    m = 9 * S
    p.drawRoundedRect(m, m, 64 * S - 2 * m, 64 * S - 2 * m, 11 * S, 11 * S)
    f = QFont('Segoe UI'); f.setPixelSize(15 * S); f.setBold(True)
    p.setFont(f)
    p.setPen(QColor('#FFFFFF'))
    p.drawText(pm.rect(), Qt.AlignCenter, _type_label(t))
    p.end()
    return QIcon(pm)


class ShareGrid(QListWidget):
    """المساحة الموحّدة: أيقونات بالاسم تحتها، وتقبل إفلات أي نوع ملف."""
    filesDropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setViewMode(QListView.IconMode)
        self.setIconSize(QSize(58, 58))
        self.setGridSize(QSize(126, 124))
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setWordWrap(True)
        self.setSpacing(10)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)
        self.setStyleSheet(
            'QListWidget { background:#CDEBE1; border:2px dashed #6FBFB4;'
            ' border-radius:12px; padding:8px; }'
            ' QListWidget::item { color:#0A5A54; }'
            ' QListWidget::item:selected { background:#A2D8CA;'
            ' border-radius:8px; color:#083F3A; }')

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
            paths = [u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile()]
            if paths:
                self.filesDropped.emit(paths)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)


class SharingPage(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        v = QVBoxLayout(self); v.setContentsMargins(28, 18, 28, 14); v.setSpacing(10)

        hint = QLabel('اسحب ملفات إلى المساحة لمشاركتها مع أجهزة المكتب على نفس الشبكة '
                      '(يمكن عدّة ملفات معاً). أول مرة قد يسألك ويندوز عن السماح '
                      'بالاتصال — اضغط «سماح».')
        hint.setWordWrap(True); hint.setStyleSheet('color:#7d8587')
        v.addWidget(hint)

        self.files_list = ShareGrid()
        self.files_list.filesDropped.connect(self.add_files)
        self.files_list.itemDoubleClicked.connect(self._activate)
        self.files_list.itemSelectionChanged.connect(self._sync_buttons)
        v.addWidget(self.files_list, 1)

        self.lbl_empty = QLabel('لا توجد ملفات مشاركة بعد — اسحب ملفاتك هنا.')
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.lbl_empty.setStyleSheet('color:#8aa3a1')
        v.addWidget(self.lbl_empty)

        bar = QHBoxLayout()
        self.btn_go = QPushButton('تنزيل / فتح المحدد'); self.btn_go.setObjectName('primary')
        self.btn_go.clicked.connect(self._activate)
        b_pick = QPushButton('اختيار ملفات...'); b_pick.setObjectName('ghost')
        b_pick.clicked.connect(self._pick)
        b_open = QPushButton('فتح مجلد المستلمات'); b_open.setObjectName('ghost')
        b_open.clicked.connect(self._open_received)
        self.btn_rm = QPushButton('إزالة من المشاركة'); self.btn_rm.setObjectName('danger')
        self.btn_rm.clicked.connect(self._remove_mine)
        bar.addWidget(self.btn_go); bar.addWidget(b_pick); bar.addWidget(b_open)
        bar.addStretch(1); bar.addWidget(self.btn_rm)
        v.addLayout(bar)

        self._timer = QTimer(self); self._timer.setInterval(4000)
        self._timer.timeout.connect(self._refresh_incoming)
        self._timer.start()
        self.refresh()

    # -- المشاركة --
    def add_files(self, paths):
        for p in paths:
            if p and os.path.isfile(p):
                self.service.share(p)
        self.refresh()

    def _pick(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'اختر ملفات للمشاركة', '',
                                                'كل الملفات (*.*)')
        self.add_files(paths)

    def _open_received(self):
        if os.path.isdir(self.service.received):
            os.startfile(self.service.received)

    # -- التحديد والإجراءات --
    def _current(self):
        it = self.files_list.currentItem()
        return it.data(Qt.UserRole) if it else None

    def _sync_buttons(self):
        d = self._current()
        self.btn_go.setEnabled(d is not None)
        self.btn_rm.setEnabled(bool(d) and d['kind'] == 'mine')

    def _activate(self, *args):
        """ملف زميل ⟵ تنزيل، وملفي ⟵ فتحه من مكانه."""
        d = self._current()
        if not d:
            return
        if d['kind'] == 'mine':
            if os.path.exists(d['path']):
                os.startfile(d['path'])
            else:
                QMessageBox.information(self, 'الملف مفقود',
                                        'الأصل لم يعد موجوداً في مكانه على جهازك.')
            return
        self._download(d['row'])

    def _remove_mine(self):
        d = self._current()
        if not d or d['kind'] != 'mine':
            return
        if QMessageBox.question(self, 'إزالة',
                                'إزالة هذا الملف من المشاركة؟ (لن يُحذف الأصل من جهازك)'
                                ) == QMessageBox.StandardButton.Yes:
            self.service.unshare(d['id'])
            self.refresh()

    # -- التنزيل --
    def _download(self, row):
        if not row.get('peer_online') or not row.get('available'):
            QMessageBox.information(self, 'غير متاح',
                                    'هذا الملف غير متاح الآن (جهاز صاحبه مطفأ). حاول لاحقاً.')
            return
        # لا تبدأ تنزيلاً وآخر ما زال جارياً (حماية QThread)
        if getattr(self, '_dw', None) is not None and self._dw.isRunning():
            return
        dlg = QProgressDialog('جاري التنزيل...', 'إلغاء', 0, 100, self)
        dlg.setWindowModality(Qt.WindowModal)
        self._dw = DownloadWorker(self.service, row)
        self._dw.progressed.connect(
            lambda d, t: dlg.setValue(int(d * 100 / t)) if t else None)
        self._dw.finished_ok.connect(lambda p: (dlg.close(), self._downloaded(p)))
        self._dw.failed.connect(lambda e: (dlg.close(), QMessageBox.warning(
            self, 'تعذّر التنزيل', 'انقطع الاتصال، حاول لاحقاً.')))
        self._dw.start()

    def _downloaded(self, path):
        box = QMessageBox(self); box.setWindowTitle('اكتمل التنزيل')
        box.setText(f'تم حفظ «{os.path.basename(path)}».')
        b_open = box.addButton('فتح', QMessageBox.ButtonRole.AcceptRole)
        box.addButton('إغلاق', QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is b_open:
            os.startfile(path)

    # -- التحديث --
    def _refresh_incoming(self):
        # لا تُنشئ عاملاً جديداً وآخر ما زال يعمل: استبدال self._rw بينما الخيط يعمل
        # يُتلف QThread أثناء تشغيله فينهار التطبيق — ويحدث ذلك حين يتجمّد الجلب من
        # قرين أُغلق للتوّ (جدار الحماية يُسقط الحزم) حتى المهلة. (إصلاح الإغلاق المتزامن.)
        if getattr(self, '_rw', None) is not None and self._rw.isRunning():
            return
        if self.service.peers():
            self._rw = RefreshWorker(self.service)
            self._rw.done.connect(self.refresh)
            self._rw.start()
        else:
            self.refresh()

    def _rows(self):
        """كل الملفات في مساحة واحدة: ملفاتي + ملفات الزملاء، الأحدث أولاً."""
        rows = []
        for f in self.service.my_files():
            avail = os.path.exists(f['path'])
            dl = f.get('downloaded_by') or []
            sub = ('✔ نزّله: ' + '، '.join(dl)) if dl else (
                'منك' if avail else '⚠️ الأصل مفقود')
            rows.append({'kind': 'mine', 'sort': f.get('shared_at', 0),
                         'name': f['name'], 'type': f['type'], 'sub': sub,
                         'faded': not avail, 'id': f['id'], 'path': f['path']})
        for r in self.service.incoming():
            if r['peer_online'] and r['available']:
                sub, faded = f"من: {r['peer_name']}", False
            elif not r['peer_online']:
                sub, faded = f"من: {r['peer_name']} — غير متاح الآن", True
            else:
                sub, faded = f"من: {r['peer_name']} — الأصل مفقود", True
            rows.append({'kind': 'peer', 'sort': r.get('shared_at', 0),
                         'name': r['name'], 'type': r['type'], 'sub': sub,
                         'faded': faded, 'row': r})
        rows.sort(key=lambda x: x['sort'], reverse=True)
        return rows

    def refresh(self):
        cur = self.files_list.currentRow()
        self.files_list.clear()
        for d in self._rows():
            it = QListWidgetItem(_file_icon(d['type'], d['faded']),
                                 f"{d['name']}\n{d['sub']}")
            it.setToolTip(f"{d['name']} — {d['sub']}")
            it.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            it.setData(Qt.UserRole, d)
            self.files_list.addItem(it)
        self.files_list.setCurrentRow(cur)
        self.lbl_empty.setVisible(self.files_list.count() == 0)
        self._sync_buttons()
