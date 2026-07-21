# -*- coding: utf-8 -*-
"""تدفق التحديث في الواجهة: فحص بالخلفية ⟵ سؤال ⟵ تنزيل بتقدم ⟵ استبدال وإعادة تشغيل."""
import sys
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from core import updater, config
from core.version import VERSION


class CheckWorker(QThread):
    found = Signal(dict)
    none_found = Signal()
    failed = Signal(str)

    def __init__(self, manifest_url):
        super().__init__()
        self.manifest_url = manifest_url

    def run(self):
        try:
            info = updater.check(self.manifest_url, VERSION)
            if info:
                self.found.emit(info)
            else:
                self.none_found.emit()
        except Exception as e:
            self.failed.emit(str(e))


class DownloadWorker(QThread):
    progressed = Signal(int)
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            self.done.emit(updater.download(self.url, progress=self.progressed.emit))
        except Exception as e:
            self.failed.emit(str(e))


def offer_update(parent, info):
    """يعرض التحديث ويقوده حتى إعادة التشغيل. يعيد True إن بدأ التثبيت."""
    notes = ('\n\nالجديد:\n' + info['notes']) if info.get('notes') else ''
    btn = QMessageBox.question(
        parent, 'تحديث متوفر',
        f'يتوفر إصدار أحدث ({info["version"]}) — إصدارك الحالي {VERSION}.{notes}\n\n'
        'تنزيل التحديث وتثبيته الآن؟ (سيُغلق التطبيق ويُعاد فتحه وحده)')
    if btn != QMessageBox.StandardButton.Yes:
        return False
    dlg = QProgressDialog('جاري تنزيل التحديث...', None, 0, 100, parent)
    dlg.setWindowTitle('التحديث'); dlg.setCancelButton(None)
    dlg.setMinimumDuration(0); dlg.setAutoClose(False)
    w = DownloadWorker(info['url'])
    state = {}
    w.progressed.connect(lambda p: dlg.setValue(p if p >= 0 else 0))
    w.done.connect(lambda path: state.setdefault('path', path) or dlg.close())
    w.failed.connect(lambda e: state.setdefault('err', e) or dlg.close())
    w.start()
    dlg.exec()
    w.wait()
    if 'err' in state:
        QMessageBox.warning(parent, 'التحديث',
                            'تعذر تنزيل التحديث — تحقق من الإنترنت وحاول لاحقاً.\n' + state['err'][:120])
        return False
    if not getattr(sys, 'frozen', False):
        QMessageBox.information(parent, 'التحديث',
                                'نُزّل الملف الجديد:\n%s\n(الاستبدال الذاتي يعمل في نسخة exe فقط)'
                                % state['path'])
        return False
    try:
        updater.apply_and_restart(state['path'])
    except Exception as e:
        QMessageBox.warning(parent, 'التحديث', 'تعذر تثبيت التحديث: ' + str(e)[:150])
        return False
    # إنهاء فوري ليتحرّر قفل ملف الـ exe فينجح الاستبدال (quit وحده قد لا يُنهي العملية)
    import os
    os._exit(0)


def manual_check(parent):
    """زر «فحص التحديثات الآن» في الإعدادات — بنتيجة معلنة دائماً."""
    url = config.manifest_url()      # رابط GitHub المدمج دائماً (لا يعتمد على قيمة محفوظة)
    if not url:
        QMessageBox.information(parent, 'التحديثات', 'رابط التحديثات غير متاح.')
        return
    w = CheckWorker(url)
    state = {}
    w.found.connect(lambda i: state.setdefault('info', i))
    w.none_found.connect(lambda: state.setdefault('none', True))
    w.failed.connect(lambda e: state.setdefault('err', e))
    w.start(); w.wait(30000)
    if 'info' in state:
        offer_update(parent, state['info'])
    elif 'none' in state:
        QMessageBox.information(parent, 'التحديثات',
                                f'أنت على أحدث إصدار ({VERSION}) ✓')
    else:
        QMessageBox.warning(parent, 'التحديثات',
                            'تعذر الفحص — تحقق من الإنترنت أو من رابط التحديثات.')
