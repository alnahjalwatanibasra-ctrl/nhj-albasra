# -*- coding: utf-8 -*-
"""تهيئة الصورة قبل الإرسال: دوران EXIF، تعديل الميلان الواضح، وتنبيه الدقّة المنخفضة."""
import io
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PIL import Image
from core.gemini_ocr import (prepare_image_bytes, detect_skew, low_res_images,
                             DESKEW_MIN_ANGLE, LOW_RES_SIDE)


def _ruled_page(w=900, h=1200, angle=0.0):
    """صفحة بيضاء بخطوط أفقية (تحاكي جدول السجل) مع ميلان اختياري."""
    im = Image.new('RGB', (w, h), (255, 255, 255))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    for y in range(120, h - 60, 60):
        d.line([(40, y), (w - 40, y)], fill=(0, 0, 0), width=4)
    if angle:
        im = im.rotate(-angle, resample=Image.BICUBIC, expand=False,
                       fillcolor=(255, 255, 255))
    return im


def test_upright_image_is_sent_untouched(tmp_path):
    """الصورة السليمة تُرسل كما هي بلا إعادة ترميز (حفاظاً على السلوك المُتحقَّق منه)."""
    p = tmp_path / 'clean.jpg'
    _ruled_page().save(p, 'JPEG', quality=92)
    assert prepare_image_bytes(str(p)) == open(p, 'rb').read()


def test_exif_rotated_image_is_straightened(tmp_path):
    """صورة بعلامة دوران EXIF تُصحَّح قبل الإرسال (كانت تُرسل مقلوبة)."""
    p = tmp_path / 'rot.jpg'
    im = _ruled_page(w=900, h=1200)
    exif = im.getexif()
    exif[274] = 8                      # Orientation = تدوير 90° عكس عقارب الساعة
    im.save(p, 'JPEG', quality=92, exif=exif)
    out = prepare_image_bytes(str(p))
    assert out != open(p, 'rb').read()          # عُدّلت فعلاً
    fixed = Image.open(io.BytesIO(out))
    assert fixed.width > fixed.height           # صارت أفقية بعد التصحيح


def test_detect_skew_finds_clear_tilt():
    assert abs(detect_skew(_ruled_page(angle=4.0)) - 4.0) <= 1.5


def test_detect_skew_near_zero_for_straight_page():
    assert abs(detect_skew(_ruled_page())) < DESKEW_MIN_ANGLE


def test_slightly_tilted_image_untouched(tmp_path):
    """ميلان أقل من العتبة لا يُلمس — صور المستخدم الحالية ميلانها ≤ 1°."""
    p = tmp_path / 'tiny_tilt.jpg'
    _ruled_page(angle=0.5).save(p, 'JPEG', quality=92)
    assert prepare_image_bytes(str(p)) == open(p, 'rb').read()


def test_low_res_images_flags_whatsapp_sizes(tmp_path):
    small = tmp_path / 'wa.jpg'; Image.new('RGB', (1280, 960)).save(small, 'JPEG')
    big = tmp_path / 'cam.jpg'; Image.new('RGB', (3000, 2000)).save(big, 'JPEG')
    flagged = low_res_images([str(small), str(big)])
    assert [n for n, w, h in flagged] == ['wa.jpg']
    assert LOW_RES_SIDE > 1280
