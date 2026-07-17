# -*- coding: utf-8 -*-
"""عام: المفتاح + فحص الاتصال. متقدم (مطوي): الاستبدالات، النماذج، مفردات المرجع."""
import json, urllib.request, urllib.parse
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QGroupBox, QCheckBox, QPlainTextEdit, QInputDialog,
                               QMessageBox, QLineEdit)


def _mask(key):
    return (key[:6] + '••••••••') if key else 'غير محدد'


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle('الإعدادات')
        self.resize(500, 480)
        self.settings = settings
        v = QVBoxLayout(self)

        g1 = QGroupBox('عام'); v1 = QVBoxLayout(g1)
        r = QHBoxLayout()
        self.lbl_key = QLabel('مفتاح Gemini: ' + _mask(settings.get('gemini_key', '')))
        b_key = QPushButton('تغيير'); b_key.setObjectName('ghost')
        b_key.clicked.connect(self._change_key)
        r.addWidget(self.lbl_key, 1); r.addWidget(b_key)
        v1.addLayout(r)
        b_check = QPushButton('فحص الاتصال الآن'); b_check.setObjectName('ghost')
        b_check.clicked.connect(self._check)
        v1.addWidget(b_check)
        v.addWidget(g1)

        from core.version import VERSION
        g_up = QGroupBox('التحديثات'); v_up = QVBoxLayout(g_up)
        r_up = QHBoxLayout()
        r_up.addWidget(QLabel(f'الإصدار الحالي: {VERSION}'), 1)
        b_up = QPushButton('فحص التحديثات الآن'); b_up.setObjectName('ghost')
        b_up.clicked.connect(self._check_updates)
        r_up.addWidget(b_up)
        v_up.addLayout(r_up)
        v.addWidget(g_up)

        self.g2 = QGroupBox('متقدم (لا تغيّره إلا إذا كنت تعرف ما تفعل)')
        self.g2.setCheckable(True); self.g2.setChecked(False)
        v2 = QVBoxLayout(self.g2)
        b_rep = QPushButton('استبدالات المصطلحات...'); b_rep.setObjectName('ghost')
        b_rep.clicked.connect(self._edit_replacements)
        v2.addWidget(b_rep)
        v2.addWidget(QLabel('النماذج بالترتيب (سطر لكل نموذج):'))
        self.txt_models = QPlainTextEdit('\n'.join(settings.get('gemini_models', [])))
        self.txt_models.setFixedHeight(100)
        v2.addWidget(self.txt_models)
        self.chk_vocab = QCheckBox('إرشاد القراءة بمفردات المرجع (مُقاس: يحسّن الدقة)')
        self.chk_vocab.setChecked(settings.get('vocab_in_prompt', True))
        v2.addWidget(self.chk_vocab)
        v2.addWidget(QLabel('رابط التحديثات (version.json على درايف — يضبطه المسؤول):'))
        self.txt_update = QLineEdit(settings.get('update_manifest_url', ''))
        self.txt_update.setPlaceholderText('https://drive.google.com/file/d/...')
        v2.addWidget(self.txt_update)
        v.addWidget(self.g2)
        v.addStretch(1)

        h = QHBoxLayout(); h.addStretch(1)
        b_save = QPushButton('✓ حفظ')
        b_save.clicked.connect(self._save)
        b_cancel = QPushButton('إلغاء'); b_cancel.setObjectName('ghost')
        b_cancel.clicked.connect(self.reject)
        h.addWidget(b_save); h.addWidget(b_cancel)
        v.addLayout(h)

    def _change_key(self):
        txt, ok = QInputDialog.getText(self, 'مفتاح Gemini', 'ألصق المفتاح الجديد:',
                                       QLineEdit.Password)
        if ok and txt.strip():
            self.settings['gemini_key'] = txt.strip()
            self.lbl_key.setText('مفتاح Gemini: ' + _mask(txt.strip()))

    def _check(self):
        from core import config
        key = self.settings.get('gemini_key') or config.get_key()
        model = (self.settings.get('gemini_models') or ['gemini-3-flash-preview'])[0]
        try:
            body = json.dumps({'contents': [{'parts': [{'text': 'نعم'}]}],
                               'generationConfig': {'maxOutputTokens': 5}}).encode()
            url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
                   f'{model}:generateContent?key=' + urllib.parse.quote(key))
            urllib.request.urlopen(urllib.request.Request(
                url, data=body, headers={'Content-Type': 'application/json'}), timeout=30)
            QMessageBox.information(self, 'الفحص', f'✓ الاتصال يعمل ({model})')
        except Exception as e:
            msg = ('انتهت حصة اليوم لهذا النموذج — البرنامج سيتحول للاحتياطي تلقائياً'
                   if '429' in str(e) else f'فشل الاتصال: {type(e).__name__}')
            QMessageBox.warning(self, 'الفحص', msg)

    def _check_updates(self):
        # يُحفظ الرابط أولاً إن عدّله المسؤول للتو ثم يُفحص
        self.settings['update_manifest_url'] = self.txt_update.text().strip()
        from core import config
        config.save_settings(self.settings)
        from ..update_flow import manual_check
        manual_check(self)

    def _edit_replacements(self):
        from .replacements_dialog import ReplacementsDialog
        dlg = ReplacementsDialog(self.settings.get('subject_replacements', {}), self)
        if dlg.exec():
            self.settings['subject_replacements'] = dlg.values()

    def _save(self):
        from core import config
        models = [m.strip() for m in self.txt_models.toPlainText().split('\n') if m.strip()]
        if models:
            self.settings['gemini_models'] = models
        self.settings['vocab_in_prompt'] = self.chk_vocab.isChecked()
        self.settings['update_manifest_url'] = self.txt_update.text().strip()
        config.save_settings(self.settings)
        self.accept()
