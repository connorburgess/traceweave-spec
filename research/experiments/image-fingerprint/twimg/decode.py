"""Shared decode stage of the draft image profile (extraction-profile-image.md §3).

Bytes in, an RGB uint8 array out, or an Abstain with a closed reason code. Pillow 13.0.0 is the
only decoder. Every conversion after decoding is written out here as an integer formula or a
table lookup, so it does not depend on Pillow's convert() or paste() semantics.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

FORMATS = ("JPEG", "PNG")
MODES = ("L", "LA", "P", "RGB", "RGBA")
MIN_SIDE = 32
MAX_PIXELS = 50_000_000
MAX_BYTES = 64 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

ABSTAIN_CODES = (
    "input-too-large",
    "undecodable",
    "unsupported-format",
    "unsupported-bit-depth",
    "multi-frame",
    "unsupported-mode",
    "too-small",
    "too-many-pixels",
    "low-quality",
)

# EXIF orientation value -> Pillow transpose (EXIF 2.32 orientation semantics; same table as
# PIL.ImageOps.exif_transpose). Values outside 2..8 are treated as 1 (identity).
_ORIENT = {
    2: Image.Transpose.FLIP_LEFT_RIGHT,
    3: Image.Transpose.ROTATE_180,
    4: Image.Transpose.FLIP_TOP_BOTTOM,
    5: Image.Transpose.TRANSPOSE,
    6: Image.Transpose.ROTATE_270,
    7: Image.Transpose.TRANSVERSE,
    8: Image.Transpose.ROTATE_90,
}


class Abstain(Exception):
    def __init__(self, code: str):
        assert code in ABSTAIN_CODES, code
        super().__init__(code)
        self.code = code


def png_ihdr(data: bytes) -> tuple[int, int] | None:
    """(bit depth, colour type) from the PNG IHDR chunk, or None if the bytes are not PNG."""
    if not data.startswith(PNG_SIGNATURE) or len(data) < 29 or data[12:16] != b"IHDR":
        return None
    return data[24], data[25]


def png_bit_depth_ok(depth: int, colour_type: int) -> bool:
    """Draft-1 accepts 8 bits per sample, and palette images (type 3) with 1, 2, 4 or 8-bit
    indices (the index depth does not change any colour)."""
    if colour_type == 3:
        return depth in (1, 2, 4, 8)
    return depth == 8


def flatten_white(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """out = (c*a + 255*(255 - a) + 127) // 255 per channel (white background)."""
    c = rgb.astype(np.int64)
    a = alpha.astype(np.int64)[..., None]
    return ((c * a + 255 * (255 - a) + 127) // 255).astype(np.uint8)


def to_rgb(img: Image.Image) -> np.ndarray:
    """Mode-specific, explicit conversion to RGB uint8 (profile §3 step 10)."""
    mode = img.mode
    if mode == "RGB":
        return np.asarray(img, dtype=np.uint8)
    if mode == "RGBA":
        a = np.asarray(img, dtype=np.uint8)
        return flatten_white(a[..., :3], a[..., 3])
    if mode == "L":
        g = np.asarray(img, dtype=np.uint8)
        return np.repeat(g[..., None], 3, axis=2)
    if mode == "LA":
        a = np.asarray(img, dtype=np.uint8)
        g = np.repeat(a[..., :1], 3, axis=2)
        return flatten_white(g, a[..., 1])
    if mode == "P":
        idx = np.asarray(img, dtype=np.uint8)
        pal = img.getpalette("RGB") or []
        table = np.zeros((256, 3), np.uint8)
        n = len(pal) // 3
        table[:n] = np.array(pal[: 3 * n], dtype=np.uint8).reshape(n, 3)
        rgb = table[idx]
        trns = img.info.get("transparency")
        if trns is None:
            return rgb
        alpha_table = np.full(256, 255, np.uint8)
        if isinstance(trns, (bytes, bytearray)):
            alpha_table[: len(trns)] = np.frombuffer(bytes(trns), dtype=np.uint8)
        else:
            alpha_table[int(trns)] = 0
        return flatten_white(rgb, alpha_table[idx])
    raise Abstain("unsupported-mode")


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
    if fmt == "PNG":
        ihdr = png_ihdr(data)
        if ihdr is None:
            raise Abstain("undecodable")
        if not png_bit_depth_ok(*ihdr):
            raise Abstain("unsupported-bit-depth")
    if getattr(img, "n_frames", 1) != 1:
        raise Abstain("multi-frame")
    w, h = img.size
    if w * h > MAX_PIXELS:
        raise Abstain("too-many-pixels")
    source_mode = img.mode
    if source_mode not in MODES:
        raise Abstain("unsupported-mode")
    try:
        img.load()
    except Exception:
        raise Abstain("undecodable")
    orientation = 1
    if fmt == "JPEG":
        try:
            v = img.getexif().get(0x0112, 1)
        except Exception:
            v = 1
        orientation = v if isinstance(v, int) and v in _ORIENT else 1
        if orientation != 1:
            img = img.transpose(_ORIENT[orientation])
    icc_present = "icc_profile" in img.info
    rgb = to_rgb(img)
    if min(rgb.shape[0], rgb.shape[1]) < MIN_SIDE:
        raise Abstain("too-small")
    info = {
        "format": fmt,
        "sourceMode": source_mode,
        "width": int(rgb.shape[1]),
        "height": int(rgb.shape[0]),
        "exifOrientation": int(orientation),
        "iccPresent": icc_present,
    }
    return np.ascontiguousarray(rgb), info

