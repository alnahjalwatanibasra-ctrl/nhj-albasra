# -*- coding: utf-8 -*-
"""المسح الضوئي عبر WIA على ويندوز — رمادي 300 نقطة/إنش (مثالي لقراءة النصوص).
معزول تماماً: يعتمد على pywin32 (win32com) المتاح داخل exe، ويفشل بلطف إن غاب."""
import os, tempfile, time

# ثوابت WIA
WIA_IMG_GRAYSCALE = 2
WIA_INTENT_TEXT = 0x00000002          # نية «نص» — رمادي عالي التباين
DPI = 300
# معرّفات خصائص WIA للعنصر (الأفقي/الرأسي دقة، نوع البيانات)
P_HORIZ_DPI, P_VERT_DPI = 6147, 6148
P_HORIZ_EXT, P_VERT_EXT = 6151, 6152
P_DATATYPE = 4103
WIA_FMT_JPEG = '{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}'


class ScannerError(Exception):
    """خطأ مسح برسالة عربية مفهومة للمستخدم."""


def _wia():
    try:
        import win32com.client
        return win32com.client.Dispatch('WIA.CommonDialog'), win32com.client.Dispatch('WIA.DeviceManager')
    except Exception:
        raise ScannerError('ميزة المسح تعمل في نسخة البرنامج المثبّتة (exe) على ويندوز فقط.')


def list_scanners():
    """أسماء الماسحات المتاحة الآن. قائمة فارغة إن لا يوجد."""
    try:
        _, dm = _wia()
    except ScannerError:
        return []
    out = []
    for info in dm.DeviceInfos:
        if info.Type == 1:              # 1 = ماسح ضوئي
            try:
                out.append(_prop(info.Properties, 'Name'))
            except Exception:
                out.append('ماسح')
    return out


def _prop(props, name):
    for p in props:
        if p.Name == name:
            return p.Value
    return None


def _set(props, pid, value):
    for p in props:
        if p.PropertyID == pid:
            p.Value = value
            return


def scan_to_file(progress=None):
    """يمسح صفحة واحدة رمادي 300dpi ويعيد مسار صورة JPEG مؤقتة.
    يرفع ScannerError برسالة عربية عند أي فشل."""
    _, dm = _wia()
    devices = [i for i in dm.DeviceInfos if i.Type == 1]
    if not devices:
        raise ScannerError('لم يُعثر على ماسح ضوئي — تأكد أن الجهاز مشغّل ومتصل.')
    if progress:
        progress('جاري الاتصال بالماسح...')
    try:
        device = devices[0].Connect()
    except Exception:
        raise ScannerError('تعذّر الاتصال بالماسح — قد يكون مشغولاً أو مطفأً. أعد المحاولة.')

    item = device.Items[1]
    try:
        _set(item.Properties, P_HORIZ_DPI, DPI)
        _set(item.Properties, P_VERT_DPI, DPI)
        _set(item.Properties, P_DATATYPE, WIA_IMG_GRAYSCALE)
    except Exception:
        pass                            # بعض الأجهزة لا تسمح بتغيير الخصائص — نمسح بالافتراضي

    if progress:
        progress('جاري المسح... (لا تحرّك الورقة)')
    try:
        image = item.Transfer(WIA_FMT_JPEG)
    except Exception as e:
        msg = str(e).lower()
        if 'paper' in msg or 'empty' in msg:
            raise ScannerError('لا توجد ورقة في الماسح — ضع الورقة وأعد المحاولة.')
        raise ScannerError('فشل المسح — تأكد من الجهاز والورقة ثم أعد المحاولة.')

    dest = os.path.join(tempfile.gettempdir(), 'nhj_scan_%d.jpg' % int(time.time() * 1000))
    try:
        if os.path.exists(dest):
            os.remove(dest)
        image.SaveFile(dest)
    except Exception:
        raise ScannerError('تعذّر حفظ الصورة الممسوحة.')
    return dest
