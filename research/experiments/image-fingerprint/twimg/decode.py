"""Shared decode stage of the draft image profile (extraction-profile-image.md §3).

Bytes in, an RGB uint8 array out, or an Abstain with a closed reason code. Pillow is the only
decoder; its version and its bundled codec versions are checked against the profile by
twimg.profile.check_environment() before any run.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageOps

FORMATS = ("JPEG", "PNG")
MODES = ("1", "L", "LA", "P", "RGB", "RGBA", "CMYK", "YCbCr")
MIN_SIDE = 32
MAX_PIXELS = 50_000_000
MAX_BYTES = 64 * 1024 * 1024

ABSTAIN_CODES = (
    "input-too-large",
    "undecodable",
    "unsupported-format",
    "multi-frame",
    "unsupported-mode",
    "too-small",
    "too-many-pixels",
    "low-quality",
)


class Abstain(Exception):
    def __init__(self, code: str):
        assert code in ABSTAIN_CODES, code
        super().__init__(code)
        self.code = code


def fill_transparency(img: Image.Image) -> Image.Image:
    """iscc-sdk 0.9.7 image_fill_transparency (Apache-2.0), same Pillow calls: white background."""
    white = (255, 255, 255)
    if img.mode == "RGB":
        return img
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, white)
        bg.paste(img, mask=img.getchannel("A"))
        return bg
    if img.mode == "P":
        if "transparency" in img.info:
            rgba = img.convert("RGBA")
            bg = Image.new("RGB", img.size, white)
            bg.paste(rgba, mask=rgba.getchannel("A"))
            return bg
        return img.convert("RGB")
    return img.convert("RGB")


def decode(data: bytes) -> tuple[np.ndarray, dict]:
    """Return (rgb HxWx3 uint8, info). Raises Abstain."""
    if len(data) > MAX_BYTES:
        raise Abstain("input-too-large")
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
    except Exception:
        raise Abstain("undecodable")
    if fmt not in FORMATS:
        raise Abstain("unsupported-format")
    if getattr(img, "n_frames", 1) != 1:
        raise Abstain("multi-frame")
    w, h = img.size
    if w * h > MAX_PIXELS:
        raise Abstain("too-many-pixels")
    if img.mode not in MODES:
        raise Abstain("unsupported-mode")
    try:
        img.load()
    except Exception:
        raise Abstain("undecodable")
    exif_orientation = img.getexif().get(0x0112, 1)
    icc_present = "icc_profile" in img.info
    img = ImageOps.exif_transpose(img)
    img = fill_transparency(img)
    if img.mode != "RGB":  # defensive; fill_transparency always returns RGB
        img = img.convert("RGB")
    if min(img.size) < MIN_SIDE:
        raise Abstain("too-small")
    rgb = np.asarray(img, dtype=np.uint8)
    info = {
        "format": fmt,
        "sourceMode": Image.open(io.BytesIO(data)).mode,
        "width": rgb.shape[1],
        "height": rgb.shape[0],
        "exifOrientation": int(exif_orientation) if isinstance(exif_orientation, int) else 1,
        "iccPresent": icc_present,
    }
    return rgb, info
