# -*- coding: utf-8 -*-
"""تصغير صور الكاميرا الضخمة قبل الإرسال — رفع أسرع وبلا سقوط مهلة."""
import io
from PIL import Image
from core.gemini_ocr import prepare_image_bytes, MAX_SIDE


def _make_jpg(tmp_path, w, h):
    p = tmp_path / 'img.jpg'
    Image.new('RGB', (w, h), (200, 200, 200)).save(p, 'JPEG')
    return str(p)


def test_small_image_untouched(tmp_path):
    p = _make_jpg(tmp_path, 1280, 960)
    assert prepare_image_bytes(p) == open(p, 'rb').read()


def test_huge_image_downscaled(tmp_path):
    p = _make_jpg(tmp_path, 4000, 3000)
    out = prepare_image_bytes(p)
    im = Image.open(io.BytesIO(out))
    assert max(im.size) == MAX_SIDE
    assert len(out) < len(open(p, 'rb').read()) * 2   # ليس أكبر من الأصل عبثاً
