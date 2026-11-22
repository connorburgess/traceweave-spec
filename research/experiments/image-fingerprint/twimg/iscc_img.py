"""ISCC Content-Code Image v0 (iscc-core 1.5.0) with the iscc-sdk 0.9.7 caller normalization.

iscc-core leaves normalization to the caller (module docstring of code_content_image). The steps
below are re-implemented following iscc-sdk 0.9.7 image_normalize with its defaults (tolerant
border trim, tolerance 16, at most 16 passes; grey conversion; 32x32 BICUBIC resize); iscc-sdk is
Apache-2.0, commit cc11f771e4efbf0a600f196c7e9155b529ad7598, licence in vendor/. Equality with
iscc-sdk's own outputs is NOT tested (iscc-sdk is not installed and no vector covers this step).
EXIF orientation and transparency are handled earlier, by the shared decode stage's own rules.
Grey: Pillow convert("L") = (19595 R + 38470 G + 7471 B + 0x8000) >> 16 (checked by a unit test).
Resize: Pillow 13.0.0 BICUBIC, defined by that implementation (profile §5 step 3).
"""
from __future__ import annotations

import numpy as np
from PIL import Image
import iscc_core

TRIM_MAX_PASSES = 16
TRIM_TOLERANCE = 16
DIHEDRAL_NAMES = ("orig", "rot90", "rot180", "rot270", "flipx", "flipy", "flipp", "flipm")


def _border_bbox(img: Image.Image, tolerance: int):
    ref = img.getpixel((0, 0))
    ref = ref if isinstance(ref, tuple) else (ref,)
    lut = [255 if abs(v - c) > tolerance else 0 for c in ref for v in range(256)]
    return img.point(lut).getbbox()


def trim_tolerant(img: Image.Image) -> Image.Image:
    mask_img = img if img.mode in ("RGB", "L") else img.convert("RGB")
    for _ in range(TRIM_MAX_PASSES):
        bbox = _border_bbox(mask_img, TRIM_TOLERANCE)
        if bbox is None or bbox == (0, 0) + mask_img.size:
            break
        w, h = mask_img.size
        sides = (bbox[0] > 0) + (bbox[1] > 0) + (bbox[2] < w) + (bbox[3] < h)
        if sides == 1 and _border_bbox(mask_img, TRIM_TOLERANCE // 2) != bbox:
            break
        img, mask_img = img.crop(bbox), mask_img.crop(bbox)
    return img


def normalize(rgb: np.ndarray) -> np.ndarray:
    img = Image.fromarray(rgb, "RGB")
    img = trim_tolerant(img)
    img = img.convert("L")
    img = img.resize((32, 32), Image.Resampling.BICUBIC)
    return np.asarray(img, dtype=np.uint8)


def _variant(p: np.ndarray, name: str) -> np.ndarray:
    # Same geometric meaning as the PDQ dihedral names: rotations are counter-clockwise
    # (numpy rot90), flipx mirrors top-bottom, flipy mirrors left-right, flipp is the
    # transpose and flipm the anti-transpose.
    return {
        "orig": p,
        "rot90": np.rot90(p, 1),
        "rot180": np.rot90(p, 2),
        "rot270": np.rot90(p, 3),
        "flipx": p[::-1, :],
        "flipy": p[:, ::-1],
        "flipp": p.T,
        "flipm": np.rot90(p, 2).T,
    }[name]


def digest_hex(pixels32: np.ndarray, bits: int = 64) -> str:
    flat = [int(v) for v in np.ascontiguousarray(pixels32).reshape(-1)]
    return iscc_core.soft_hash_image_v0(flat, bits=bits).hex()


def iscc_from_rgb(rgb: np.ndarray, dihedral: bool = False):
    p = normalize(rgb)
    if not dihedral:
        return digest_hex(p)
    return {n: digest_hex(_variant(p, n)) for n in DIHEDRAL_NAMES}


def iscc_string(digest: str) -> str:
    """ISCC string for a digest (header: CONTENT / IMAGE / V0 / bit length)."""
    return "ISCC:" + iscc_core.encode_component(
        mtype=iscc_core.MT.CONTENT,
        stype=iscc_core.ST_CC.IMAGE,
        version=iscc_core.VS.V0,
        bit_length=len(digest) * 4,
        digest=bytes.fromhex(digest),
    )
