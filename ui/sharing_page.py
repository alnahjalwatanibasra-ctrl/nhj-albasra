# -*- coding: utf-8 -*-
"""صفحة «مشاركة الملفات»: تبويبان (الوارد/الصادر مني) + منطقة سحب وإفلات.
تعتمد على ShareService (P2P على الشبكة المحلية)."""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QTabWidget, QListWidget, QListWidgetItem, QFileDialog,
                               QMessageBox, QFrame, QProgressDialog)
from PySide6.QtCore import Qt, QTimer
from .start_page import DropList
from .sharing_worker import RefreshWorker, DownloadWorker

_ICONS = {'xlsx': '📊', 'xls': '📊', 'docx': '📝', 'doc': '📝', 'pdf': '📕',
          'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️'}


def _icon(t):
    return _ICONS.get((t or '').lower(), '📄')


class SharingPage(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        v = QVBoxLayout(self); v.setContentsMargins(28, 18, 28, 14); v.setSpacing(10)

        hint = QLabel('شارك الملفات مباشرةً مع أجهزة المكتب على نفس الشبكة. '
                      'أول مرة قد يسألك ويندوز عن السماح بالاتصال — اضغط «سماح».')
        hint.setWordWrap(True); hint.setStyleSheet('color:#7d8587')
        v.addWidget(hint)

        card = QFrame(); card.setProperty('class', 'card')
        c = QVBoxLayout(card)
        self.drop = DropList()
        self.drop.setFixedHeight(90)
        self.drop.filesDropped.connect(self.add_files)
        c.addWidget(QLabel('اسحب ملفات هنا لمشاركتها (يمكن عدّة ملفات معاً):'))
        row = QHBoxLayout()
        b_pick = QPushButton('اختيار ملفات...'); b_pick.setObjectName('ghost')
        b_pick.clicked.connect(self._pick)
        row.addWidget(self.drop, 1)
        c.addLayout(row); c.addWidget(b_pick)
        v.addWidget(card)

        self.tabs = QTabWidget()
        self.incoming_list = QListWidget()
        self.incoming_list.itemDoubleClicked.connect(self._download_selected)
        self.mine_list = QListWidget()
        self.tabs.addTab(self.incoming_list, 'المشتركة من الآخرين')
        self.tabs.addTab(self.mine_list, 'ملفاتي المشاركة')
        v.addWidget(self.tabs, 1)

        bar = QHBoxLayout()
        b_dl = QPushButton('تنزيل المحدد'); b_dl.setObjectName('primary')
        b_dl.clicked.connect(self._download_selected)
        b_open = QPushButton('فتح مجلد المستلمات'); b_open.setObjectName('ghost')
        b_open.clicked.connect(lambda: os.startfile(self.service.received)
                               if os.path.isdir(self.service.received) else None)
        b_rm = QPushButton('إزالة من المشاركة'); b_rm.setObjectName('danger')
        b_rm.clicked.connect(self._remove_mine)
        bar.addWidget(b_dl); bar.addWidget(b_open); bar.addStretch(1); bar.addWidget(b_rm)
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
        paths, _ = QFileDialog.getOpenFileNames(self, 'اختر ملفات للمشاركة', '', 'كل الملفات (*.*)')
        self.add_files(paths)

    def _remove_mine(self):
        it = self.mine_list.currentItem()
        if not it:
            return
        fid = it.data(Qt.UserRole)
        if QMessageBox.question(self, 'إزالة',
                                'إزالة هذا الملف من المشاركة؟ (لن يُحذف الأصل من جهازك)'
                                ) == QMessageBox.StandardButton.Yes:
            self.service.unshare(fid)
            self.refresh()

    # -- التنزيل --
    def _download_selected(self, *args):
        it = self.incoming_list.currentItem()
        if not it:
            return
        row = it.data(Qt.UserRole)
        if not row.get('peer_online') or not row.get('available'):
            QMessageBox.information(self, 'غير متاح',
                                    'هذا الملف غير متاح الآن (جهاز صاحبه مطفأ). حاول لاحقاً.')
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
        if self.service.peers():
            self._rw = RefreshWorker(self.service)
            self._rw.done.connect(self.refresh)
            self._rw.start()
        else:
            self.refresh()

    def refresh(self):
        cur = self.incoming_list.currentRow()
        self.incoming_list.clear()
        for r in self.service.incoming():
            if r['peer_online'] and r['available']:
                state = 'متاح'
            elif not r['peer_online']:
                state = 'غير متاح الآن'
            else:
                state = 'الأصل مفقود عند صاحبه'
            it = QListWidgetItem(
                f"{_icon(r['type'])}  {r['name']}   —   من: {r['peer_name']}   [{state}]")
            it.setData(Qt.UserRole, r)
            self.incoming_list.addItem(it)
        self.incoming_list.setCurrentRow(cur)
        self.mine_list.clear()
        for f in self.service.my_files():
            avail = os.path.exists(f['path'])
            dl = f.get('downloaded_by') or []
            note = '' if avail else '  ⚠️ الأصل مفقود'
            recv = f'   ✔ نزّله: {"، ".join(dl)}' if dl else ''
            it = QListWidgetItem(f"{_icon(f['type'])}  {f['name']}{recv}{note}")
            it.setData(Qt.UserRole, f['id'])
            self.mine_list.addItem(it)
