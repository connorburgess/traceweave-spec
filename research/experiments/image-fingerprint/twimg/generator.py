"""Deterministic synthetic image generator (image-experiment-protocol.md §3).

generate(seed) depends only on the seed, NumPy 2.5.5 (PCG64 bit generator and Generator
methods) and Pillow 13.0.0 (ImageDraw rasterization, BILINEAR resize of mode "F"). No file,
network or clock is read. The image is an RGB uint8 array; its identity is the SHA-256 of the
array bytes (row-major, HxWx3), recorded as pixelSha256.
"""
from __future__ import annotations

import hashlib
import math

import numpy as np
from PIL import Image, ImageDraw

GENERATOR_ID = "traceweave-synth-draft-1"
DOMAIN = 0x7477_696D  # "twim"; separates this generator's streams from any other use of a seed
SIZES = ((512, 512), (1024, 768), (1920, 1080))  # (width, height), chosen by seed % 3


def size_for(seed: int) -> tuple[int, int]:
    return SIZES[seed % 3]


def _rng(seed: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence([DOMAIN, seed])))


def _colour(rng: np.random.Generator) -> tuple[int, int, int]:
    c = rng.integers(0, 256, size=3)
    return int(c[0]), int(c[1]), int(c[2])


def generate(seed: int) -> np.ndarray:
    if not (0 <= seed < 2**32):
        raise ValueError("seed out of range")
    rng = _rng(seed)
    w, h = size_for(seed)

    # 1. Background: linear gradient between two colours at a random angle.
    c0 = np.array(_colour(rng), dtype=np.float64)
    c1 = np.array(_colour(rng), dtype=np.float64)
    angle = float(rng.random()) * 2.0 * math.pi
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float64)
    proj = xs * math.cos(angle) + ys * math.sin(angle)
    t = (proj - proj.min()) / (proj.max() - proj.min())
    bg = c0[None, None, :] * (1.0 - t[..., None]) + c1[None, None, :] * t[..., None]
    img = Image.fromarray(np.clip(np.rint(bg), 0, 255).astype(np.uint8), "RGB")

    # 2. Shapes: 6..14 filled rectangles, ellipses, polygons and thick lines.
    draw = ImageDraw.Draw(img)
    n_shapes = int(rng.integers(6, 15))
    for _ in range(n_shapes):
        kind = int(rng.integers(0, 4))
        colour = _colour(rng)
        cx, cy = float(rng.random()) * w, float(rng.random()) * h
        rx = (0.05 + 0.30 * float(rng.random())) * w
        ry = (0.05 + 0.30 * float(rng.random())) * h
        box = [int(cx - rx), int(cy - ry), int(cx + rx), int(cy + ry)]
        if kind == 0:
            draw.rectangle(box, fill=colour)
        elif kind == 1:
            draw.ellipse(box, fill=colour)
        elif kind == 2:
            n = int(rng.integers(3, 7))
            pts = [
                (int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)))
                for a in sorted(float(rng.random()) * 2.0 * math.pi for _ in range(n))
            ]
            draw.polygon(pts, fill=colour)
        else:
            width = int(rng.integers(max(2, w // 200), max(3, w // 40)))
            draw.line([box[0], box[1], box[2], box[3]], fill=colour, width=width)

    out = np.asarray(img, dtype=np.float64)

    # 3. Mid-frequency texture: a coarse random grid (8..32 cells per side) upsampled
    #    with BILINEAR, amplitude up to +-24 grey levels per channel.
    cells = int(rng.integers(8, 33))
    amp = 8.0 + 16.0 * float(rng.random())
    for ch in range(3):
        grid = (rng.random((cells, cells)) * 2.0 - 1.0).astype(np.float32)
        up = Image.fromarray(grid, "F").resize((w, h), Image.Resampling.BILINEAR)
        out[..., ch] += amp * np.asarray(up, dtype=np.float64)

    # 4. Pixel noise: Gaussian, sigma 1..6 grey levels.
    sigma = 1.0 + 5.0 * float(rng.random())
    out += rng.normal(0.0, sigma, size=out.shape)

    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def pixel_sha256(rgb: np.ndarray) -> str:
    a = np.ascontiguousarray(rgb, dtype=np.uint8)
    head = f"{a.shape[1]}x{a.shape[0]}x3:".encode()
    return hashlib.sha256(head + a.tobytes()).hexdigest()
