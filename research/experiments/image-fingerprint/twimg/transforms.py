"""The 12 frozen edits of image-experiment-protocol.md §4.

Each edit takes the decoded original (RGB uint8 array) and returns the bytes of the edited
file. Queries are then decoded through the profile decode stage like any other input.
Encoders: Pillow 13.0.0 with its bundled libjpeg-turbo 3.2.0 and zlib-ng 1.3.1. No metadata
(EXIF, ICC, text chunks) is written.
"""
from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image

SCREENSHOT_BORDER = 40
SCREENSHOT_GREY = (240, 240, 240)
SCREENSHOT_SCALE_NUM, SCREENSHOT_SCALE_DEN = 4, 5

TRANSFORMS = (
    "jpeg90",
    "jpeg75",
    "jpeg50",
    "jpeg30",
    "resize50",
    "resize25",
    "crop90",
    "crop75",
    "crop50",
    "flip",
    "png",
    "screenshot",
)


def encode_png(img: Image.Image, level: int = 6) -> bytes:
    b = io.BytesIO()
    img.save(b, format="PNG", compress_level=level, optimize=False)
    return b.getvalue()


def encode_jpeg(img: Image.Image, quality: int) -> bytes:
    b = io.BytesIO()
    img.save(b, format="JPEG", quality=quality, subsampling=2, optimize=False, progressive=False)
    return b.getvalue()


def encode_original(rgb: np.ndarray) -> bytes:
    """Catalogue originals are enrolled from these bytes: PNG, compress_level 6."""
    return encode_png(Image.fromarray(rgb, "RGB"), 6)


def _resize_roundtrip(img: Image.Image, den: int) -> Image.Image:
    w, h = img.size
    small = img.resize((w // den, h // den), Image.Resampling.LANCZOS)
    return small.resize((w, h), Image.Resampling.BICUBIC)


def _centre_crop(img: Image.Image, area: float) -> Image.Image:
    w, h = img.size
    s = math.sqrt(area)
    cw, ch = int(w * s + 0.5), int(h * s + 0.5)
    left, top = (w - cw) // 2, (h - ch) // 2
    return img.crop((left, top, left + cw, top + ch))


def _screenshot(img: Image.Image) -> Image.Image:
    w, h = img.size
    b = SCREENSHOT_BORDER
    canvas = Image.new("RGB", (w + 2 * b, h + 2 * b), SCREENSHOT_GREY)
    canvas.paste(img, (b, b))
    cw, ch = canvas.size
    nw = (cw * SCREENSHOT_SCALE_NUM * 2 + SCREENSHOT_SCALE_DEN) // (2 * SCREENSHOT_SCALE_DEN)
    nh = (ch * SCREENSHOT_SCALE_NUM * 2 + SCREENSHOT_SCALE_DEN) // (2 * SCREENSHOT_SCALE_DEN)
    return canvas.resize((nw, nh), Image.Resampling.BICUBIC)


def apply(name: str, rgb: np.ndarray) -> bytes:
    img = Image.fromarray(rgb, "RGB")
    if name.startswith("jpeg"):
        return encode_jpeg(img, int(name[4:]))
    if name == "resize50":
        return encode_png(_resize_roundtrip(img, 2))
    if name == "resize25":
        return encode_png(_resize_roundtrip(img, 4))
    if name.startswith("crop"):
        return encode_png(_centre_crop(img, int(name[4:]) / 100.0))
    if name == "flip":
        return encode_png(img.transpose(Image.Transpose.FLIP_LEFT_RIGHT))
    if name == "png":
        return encode_png(img, 1)
    if name == "screenshot":
        return encode_png(_screenshot(img))
    raise KeyError(name)
