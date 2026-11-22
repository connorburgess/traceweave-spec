"""Query construction for e-img-m-1 (protocol §7): edits, removal, forgery, and decoding.

The 12 edits are imported unchanged from the frozen e-img-f-2 harness (twimg.transforms). Every
query is a file's bytes; the harness decodes those bytes like any candidate. Every random draw comes
from a PCG64 stream keyed by a domain tag and the image seed.
"""
from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image, ImageFilter

from . import env  # noqa: F401  (sys.path first)
from twimg import transforms as tx  # noqa: E402  (frozen e-img-f-2 edits)

EDITS = tx.TRANSFORMS  # 12 names, in the e-img-f-2 order
REMOVALS = ("remark", "regen", "jpeg10", "noisejpeg", "rotate5")
NOISE_DOMAIN = 0x74776D6B  # "twmk"
NOISE_SIGMA = 8.0
ROTATE_DEG = 5.0
ROTATE_FILL = (128, 128, 128)


class Abstain(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def png(rgb: np.ndarray) -> bytes:
    """Marked images and every array-producing attack are stored as PNG, compress_level 6."""
    return tx.encode_png(Image.fromarray(rgb, "RGB"), 6)


def decode(data: bytes) -> np.ndarray:
    """Candidate bytes to RGB uint8. Only 8-bit RGB PNG or baseline JPEG are expected here."""
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as e:  # noqa: BLE001
        raise Abstain("undecodable") from e
    if im.mode != "RGB":
        raise Abstain("unsupported-mode")
    return np.asarray(im, dtype=np.uint8).copy()


def edit(name: str, rgb: np.ndarray) -> bytes:
    return tx.apply(name, rgb)


def jpeg(rgb: np.ndarray, quality: int) -> bytes:
    return tx.encode_jpeg(Image.fromarray(rgb, "RGB"), quality)


def regen(rgb: np.ndarray) -> bytes:
    """Model-free regeneration-style chain: LANCZOS to half size, Gaussian blur radius 1.0,
    JPEG quality 50 (4:2:0), decode, BICUBIC back to the original size, PNG."""
    h, w = rgb.shape[:2]
    img = Image.fromarray(rgb, "RGB").resize((w // 2, h // 2), Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    small = Image.open(io.BytesIO(tx.encode_jpeg(img, 50)))
    small.load()
    return tx.encode_png(small.convert("RGB").resize((w, h), Image.Resampling.BICUBIC), 6)


def noise_jpeg(rgb: np.ndarray, seed: int) -> bytes:
    """Additive Gaussian noise, sigma 8 grey levels per channel, then JPEG quality 75."""
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([NOISE_DOMAIN, seed])))
    noisy = rgb.astype(np.float64) + rng.normal(0.0, NOISE_SIGMA, size=rgb.shape)
    out = np.clip(np.rint(noisy), 0, 255).astype(np.uint8)
    return tx.encode_jpeg(Image.fromarray(out, "RGB"), 75)


def rotate5(rgb: np.ndarray) -> bytes:
    img = Image.fromarray(rgb, "RGB").rotate(ROTATE_DEG, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=ROTATE_FILL)
    return tx.encode_png(img, 6)


def transplant(marked: np.ndarray, cover: np.ndarray, host: np.ndarray) -> np.ndarray:
    """Literal residual copy: host + (marked - cover), rounded half to even and clipped."""
    if not (marked.shape == cover.shape == host.shape):
        raise ValueError("transplant needs equal shapes")
    out = host.astype(np.float64) + (marked.astype(np.float64) - cover.astype(np.float64))
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- quality


def psnr(a: np.ndarray, b: np.ndarray) -> float | None:
    """PSNR in dB over all RGB samples, peak 255; None if the shapes differ; 'inf' never returned
    (identical arrays give None as well, recorded as identical)."""
    if a.shape != b.shape:
        return None
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    if mse == 0.0:
        return None
    return round(10.0 * math.log10(255.0 ** 2 / mse), 4)


def quality(cover: np.ndarray, marked: np.ndarray) -> dict:
    d = np.abs(marked.astype(np.int16) - cover.astype(np.int16))
    return {
        "psnr": psnr(cover, marked),
        "identical": bool(not d.any()),
        "maxAbsDiff": int(d.max()),
        "meanAbsDiff": round(float(d.mean()), 6),
        "changedSampleFraction": round(float(np.count_nonzero(d)) / d.size, 6),
    }
