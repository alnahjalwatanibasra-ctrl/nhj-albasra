# -*- coding: utf-8 -*-
"""عام: المفتاح + فحص الاتصال. متقدم (مطوي): الاستبدالات، النماذج، مفردات المرجع."""
import json, urllib.request, urllib.parse
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QGroupBox, QCheckBox, QPlainTextEdit, QInputDialog,
                               QMessageBox, QLineEdit)


def _key_display(settings):
    """يوضّح حالة المفتاح: يدوي، أو مضمّن ويعمل، أو مفقود."""
    from core import config
    if settings.get('gemini_key'):
        return settings['gemini_key'][:6] + '••••••••  (يدوي)'
    return 'مضمّن ويعمل ✓' if config.get_key(settings) else 'غير محدد'


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle('الإعدادات')
        self.resize(500, 480)
        self.settings = settings
        v = QVBoxLayout(self)

        g1 = QGroupBox('عام'); v1 = QVBoxLayout(g1)
        r = QHBoxLayout()
        self.lbl_key = QLabel('مفتاح Gemini: ' + _key_display(settings))
        b_key = QPushButton('تغيير'); b_key.setObjectName('ghost')
        b_key.clicked.connect(self._change_key)
        r.addWidget(self.lbl_key, 1); r.addWidget(b_key)
        v1.addLayout(r)
        b_check = QPushButton('فحص الاتصال الآن'); b_check.setObjectName('ghost')
        b_check.clicked.connect(self._check)
        v1.addWidget(b_check)

        r_dev = QHBoxLayout()
        r_dev.addWidget(QLabel('اسمك (يظهر لزملائك عند مشاركة ملف):'))
        self.txt_device = QLineEdit(settings.get('device_name', ''))
        self.txt_device.setPlaceholderText('اتركه فارغاً لاستخدام اسم الحاسوب')
        r_dev.addWidget(self.txt_device, 1)
        v1.addLayout(r_dev)
        v.addWidget(g1)

        from core.version import VERSION
        g_up = QGroupBox('التحديثات'); v_up = QVBoxLayout(g_up)
        r_up = QHBoxLayout()
        r_up.addWidget(QLabel(f'الإصدار الحالي: {VERSION}'), 1)
        b_up = QPushButton('فحص التحديثات الآن'); b_up.setObjectName('ghost')
        b_up.clicked.connect(self._check_updates)
        r_up.addWidget(b_up)
        v_up.addLayout(r_up)
        # إظهار مصدر التحديث الفعّال — يكشف فوراً أي رابط قديم يعطّل التحديث
        from core import config as _cfg
        lbl_src = QLabel('مصدر التحديث: ' + _cfg.manifest_url(settings))
        lbl_src.setWordWrap(True)
        lbl_src.setStyleSheet('color:#8a9294; font-size:10px')
        v_up.addWidget(lbl_src)
        v.addWidget(g_up)

        self.btn_reveal = QPushButton('⚙ إظهار الإعدادات المتقدمة')
        self.btn_reveal.setObjectName('ghost')
        self.btn_reveal.clicked.connect(self._reveal_advanced)
        v.addWidget(self.btn_reveal)

        self.adv = QGroupBox('متقدم (لا تغيّره إلا إذا كنت تعرف ما تفعل)')
        self.adv.setVisible(False)
        v2 = QVBoxLayout(self.adv)
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
        from core import config
        v2.addWidget(QLabel('رابط التحديثات (مدمج تلقائياً — اتركه فارغاً إلا لتجاوزه):'))
        self.txt_update = QLineEdit(settings.get('update_manifest_url', ''))
        self.txt_update.setPlaceholderText(config.manifest_url(settings))
        v2.addWidget(self.txt_update)
        v.addWidget(self.adv)
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
            self.lbl_key.setText('مفتاح Gemini: ' + txt.strip()[:6] + '••••••••  (يدوي)')

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

    def _reveal_advanced(self):
        self.adv.setVisible(True)
        self.btn_reveal.setVisible(False)

    def _save(self):
        from core import config
        models = [m.strip() for m in self.txt_models.toPlainText().split('\n') if m.strip()]
        if models:
            self.settings['gemini_models'] = models
        self.settings['vocab_in_prompt'] = self.chk_vocab.isChecked()
        self.settings['update_manifest_url'] = self.txt_update.text().strip()
        self.settings['device_name'] = self.txt_device.text().strip()
        config.save_settings(self.settings)
        self.accept()
