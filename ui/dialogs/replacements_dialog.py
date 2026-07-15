# -*- coding: utf-8 -*-
"""جدول (ما يُقرأ خطأً ← الصواب) — يضيفه الموظف بنفسه مع الوقت."""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QTableWidget, QTableWidgetItem)


class ReplacementsDialog(QDialog):
    def __init__(self, replacements, parent=None):
        super().__init__(parent)
        self.setWindowTitle('استبدالات المصطلحات')
        self.resize(440, 400)
        v = QVBoxLayout(self)
        v.addWidget(QLabel('عندما يقرأ البرنامج الكلمة اليمنى في «الموضوع»، '
                           'يستبدلها باليسرى تلقائياً:'))
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['ما يقرؤه خطأً', 'الصواب'])
        self.table.horizontalHeader().setStretchLastSection(True)
        for a, b in replacements.items():
            self.add_row(a, b)
        v.addWidget(self.table, 1)
        h = QHBoxLayout()
        b_add = QPushButton('+ إضافة'); b_add.setObjectName('ghost')
        b_add.clicked.connect(lambda: self.add_row('', ''))
        b_del = QPushButton('حذف المحدد'); b_del.setObjectName('danger')
        b_del.clicked.connect(lambda: self.table.removeRow(self.table.currentRow()))
        b_ok = QPushButton('✓ حفظ')
        b_ok.clicked.connect(self.accept)
        for b in (b_add, b_del, b_ok):
            h.addWidget(b)
        v.addLayout(h)

    def add_row(self, a, b):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(a))
        self.table.setItem(r, 1, QTableWidgetItem(b))

    def values(self):
        out = {}
        for r in range(self.table.rowCount()):
            a = (self.table.item(r, 0).text() if self.table.item(r, 0) else '').strip()
            b = (self.table.item(r, 1).text() if self.table.item(r, 1) else '').strip()
            if a and b:
                out[a] = b
        return out
