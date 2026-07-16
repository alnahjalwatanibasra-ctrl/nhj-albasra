# -*- coding: utf-8 -*-
"""جدول المراجعة الملوّن: تحرير مباشر، شريط الصفوف الغريبة، عرض الصورة، تصدير."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QTableWidget, QTableWidgetItem, QDialog, QScrollArea)
from PySide6.QtGui import QColor, QBrush, QPixmap
from PySide6.QtCore import Qt, Signal
from . import logic

CONF_QCOLORS = {'ref': '#C6EFCE', 'word': '#C6EFCE', 'agree': '#DDEBF7',
                'review': '#FFF2CC', 'phone_unconf': '#FCE4D6'}


def _chip(color, text):
    """مربع لون مرسوم (حاد) بدل الرموز التعبيرية النقطية المبكسلة."""
    return (f'<span style="background:{color}; border:1px solid #b9bfc1;">'
            f'&nbsp;&nbsp;&nbsp;&nbsp;</span> {text}')


LEGEND = ('  '.join([
    _chip('#C6EFCE', 'مؤكد من المرجع/Word'),
    _chip('#DDEBF7', 'ثقة عالية'),
    _chip('#FFF2CC', 'يحتاج مراجعة'),
    _chip('#FCE4D6', 'هاتف غير مؤكد'),
    _chip('#FFFFFF', 'عدّلته يدوياً'),
]))


class ReviewPage(QWidget):
    exportRequested = Signal()
    phonesRequested = Signal()
    backRequested = Signal()               # عودة لشاشة البداية (عملية جديدة)
    changed = Signal()                     # لأي تعديل — يستعمله الحفظ التلقائي

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(14, 10, 14, 10)

        bar = QHBoxLayout()
        self.btn_back = QPushButton('عملية جديدة'); self.btn_back.setObjectName('ghost')
        self.btn_back.clicked.connect(self.backRequested.emit)
        self.btn_phones = QPushButton('تأكيد الهواتف')
        self.btn_phones.clicked.connect(self.phonesRequested.emit)
        self.btn_image = QPushButton('عرض الصورة'); self.btn_image.setObjectName('ghost')
        self.btn_image.clicked.connect(self._show_image)
        bar.addWidget(self.btn_back)
        bar.addWidget(self.btn_phones); bar.addWidget(self.btn_image); bar.addStretch(1)
        self.btn_export = QPushButton('تصدير Excel'); self.btn_export.setObjectName('primary')
        self.btn_export.clicked.connect(self.exportRequested.emit)
        bar.addWidget(self.btn_export)
        v.addLayout(bar)

        self.lbl_quality = QLabel(); self.lbl_quality.setObjectName('warn')
        self.lbl_quality.hide()
        v.addWidget(self.lbl_quality)

        row = QHBoxLayout()
        self.lbl_unmatched = QLabel(); self.lbl_unmatched.setObjectName('warn')
        self.lbl_unmatched.hide()
        row.addWidget(self.lbl_unmatched, 1)
        self.btn_next_unmatched = QPushButton('التالي ⌄'); self.btn_next_unmatched.setObjectName('ghost')
        self.btn_next_unmatched.clicked.connect(self._jump_unmatched)
        self.btn_next_unmatched.hide()
        row.addWidget(self.btn_next_unmatched)
        v.addLayout(row)

        self.table = QTableWidget()
        self.table.itemChanged.connect(self._on_edit)
        v.addWidget(self.table, 1)
        legend = QLabel(LEGEND); legend.setStyleSheet('color:#41494B; font-size:11px')
        v.addWidget(legend)
        self.result, self.images, self._loading = None, [], False
        self._um, self._um_pos = [], -1

    def load_result(self, result, images):
        self.result, self.images, self._loading = result, list(images), True
        headers, rows = result['headers'], result['rows']
        self.table.setColumnCount(len(headers)); self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(headers)
        for i, r in enumerate(rows):
            for c, h in enumerate(headers):
                it = QTableWidgetItem(str(r.get(h, '')))
                key = result['colors'].get((i, h))
                if key in CONF_QCOLORS:
                    it.setBackground(QBrush(QColor(CONF_QCOLORS[key])))
                self.table.setItem(i, c, it)
        self.table.resizeColumnsToContents()
        um = logic.unmatched_rows(result.get('matched', []))
        if not result.get('ref_columns'):
            # لا ملف مرجعي أصلاً — رسالة مختلفة عن «صفوف لم تُطابَق»
            self.lbl_unmatched.setText(
                'لم يُستخدم ملف مرجعي — كل القيم من قراءة الصورة وحدها؛ راجعها بعناية')
            self.lbl_unmatched.show(); self.btn_next_unmatched.hide()
            self._um, self._um_pos = [], -1
        elif um:
            self.lbl_unmatched.setText(
                f'تنبيه: {len(um)} من الصفوف لم تُعثر في الملف المرجعي — دقّقها بعناية')
            self.lbl_unmatched.show(); self.btn_next_unmatched.show()
            self._um, self._um_pos = um, -1
        else:
            self.lbl_unmatched.hide(); self.btn_next_unmatched.hide()
            self._um, self._um_pos = [], -1
        n = len(result.get('phone_suggestions', []))
        self.btn_phones.setText(f'تأكيد الهواتف ({n})'); self.btn_phones.setEnabled(n > 0)
        # تنبيهات الجودة: نموذج احتياطي و/أو فجوات أرقام (صف ساقط من القراءة)
        notes = []
        weak = logic.weak_models_used(result)
        if weak:
            notes.append('استُخدم نموذج احتياطي أضعف (%s) لامتلاء حصة الرئيسي — راجع بدقة أعلى'
                         % '، '.join(weak))
        gaps = logic.number_gaps(rows)
        if gaps:
            notes.append('فجوات في الأرقام: ' + '، '.join(
                f'بين {a} و{b} (صف ساقط من القراءة؟ قارن بالصورة)' for a, b in gaps))
        if notes:
            self.lbl_quality.setText(' • '.join(notes)); self.lbl_quality.show()
        else:
            self.lbl_quality.hide()
        self._loading = False

    def current_rows(self):
        headers = self.result['headers']
        return [{h: (self.table.item(i, c).text() if self.table.item(i, c) else '')
                 for c, h in enumerate(headers)}
                for i in range(self.table.rowCount())]

    def set_cell(self, row, header, value, color_key=None):
        """يستعمله حوار الهواتف: تعبئة قيمة معتمدة + لونها."""
        c = self.result['headers'].index(header)
        self._loading = True
        it = self.table.item(row, c)
        if it is None:
            it = QTableWidgetItem()
            self.table.setItem(row, c, it)
        it.setText(value)
        if color_key:
            it.setBackground(QBrush(QColor(CONF_QCOLORS[color_key])))
            self.result['colors'][(row, header)] = color_key
        self._loading = False
        self.changed.emit()

    def _on_edit(self, item):
        if self._loading or self.result is None:
            return
        h = self.result['headers'][item.column()]
        self.result['colors'].pop((item.row(), h), None)
        item.setBackground(QBrush())            # قرار بشري — يزول اللون
        self.changed.emit()

    def _jump_unmatched(self):
        if not self._um:
            return
        self._um_pos = (self._um_pos + 1) % len(self._um)
        r = self._um[self._um_pos]
        self.table.selectRow(r)
        if self.table.item(r, 0):
            self.table.scrollToItem(self.table.item(r, 0))

    def _show_image(self):
        if not self.images:
            return
        r = max(self.table.currentRow(), 0)
        pages = self.result.get('row_pages') or [0] * self.table.rowCount()
        pg = min(pages[r] if r < len(pages) else 0, len(self.images) - 1)
        dlg = QDialog(self); dlg.setWindowTitle(f'صورة الصفحة {pg + 1}')
        dlg.resize(720, 820)
        v = QVBoxLayout(dlg)
        area = QScrollArea(); area.setWidgetResizable(True)
        lbl = QLabel()
        lbl.setPixmap(QPixmap(self.images[pg]).scaledToWidth(680, Qt.SmoothTransformation))
        area.setWidget(lbl); v.addWidget(area)
        dlg.exec()
