"""NumPy port of the vendored ThreatExchange pure-Python PDQ (commit 9f627fb1).

Every floating-point operation is performed in the same order as in
vendor/threatexchange_pdq/pdqhashing/hasher/pdq_hasher.py, element by element, so the
results are bit-identical by construction (checked, not assumed: tests/test_pdq_port.py and
check_vectors.py compare both on every vector image). Matrix products are written as explicit
k-loops, never as BLAS calls, because BLAS reorders the summation.

Input: a float64 luma array (rows x cols). Output: 256-bit hash as 64 lowercase hex digits in
the vendor's word order, the integer quality 0..100, and optionally the 8 dihedral hashes.
"""
from __future__ import annotations

import math

import numpy as np

LUMA_R, LUMA_G, LUMA_B = 0.299, 0.587, 0.114
_DCT_SCALE = math.sqrt(2.0 / 64.0)
# Same construction as PDQHasher.compute_dct_matrix (scalar math.cos, row by row).
DCT = np.array(
    [[_DCT_SCALE * math.cos((math.pi / 2 / 64.0) * (i + 1) * (2 * j + 1)) for j in range(64)] for i in range(16)],
    dtype=np.float64,
)
DIHEDRAL_NAMES = ("orig", "rot90", "rot180", "rot270", "flipx", "flipy", "flipp", "flipm")


def luma_from_rgb(rgb: np.ndarray) -> np.ndarray:
    """0.299 R + 0.587 G + 0.114 B, evaluated left to right in float64 (vendor order)."""
    r = rgb[..., 0].astype(np.float64)
    g = rgb[..., 1].astype(np.float64)
    b = rgb[..., 2].astype(np.float64)
    return (LUMA_R * r + LUMA_G * g) + LUMA_B * b


def _window(dim: int) -> int:
    return int((dim + 128 - 1) / 128)


def _box_1d(inp: np.ndarray, full_window: int) -> np.ndarray:
    """Vendor box1DFloat along axis 1 for every row at once (running sum, same order)."""
    n_rows, length = inp.shape
    out = np.empty_like(inp)
    half = int((full_window + 2) / 2)
    p1 = half - 1
    p2 = full_window - half + 1
    p3 = length - full_window
    p4 = half - 1
    s = np.zeros(n_rows, dtype=np.float64)
    cur = 0
    li = ri = oi = 0
    for _ in range(p1):
        s = s + inp[:, ri]
        cur += 1
        ri += 1
    for _ in range(p2):
        s = s + inp[:, ri]
        cur += 1
        out[:, oi] = s / cur
        ri += 1
        oi += 1
    for _ in range(p3):
        s = s + inp[:, ri]
        s = s - inp[:, li]
        out[:, oi] = s / cur
        li += 1
        ri += 1
        oi += 1
    for _ in range(p4):
        s = s - inp[:, li]
        cur -= 1
        out[:, oi] = s / cur
        li += 1
        oi += 1
    return out


def _jarosz(luma: np.ndarray) -> np.ndarray:
    rows, cols = luma.shape
    w_rows = _window(cols)  # window along rows uses the column count (vendor naming)
    w_cols = _window(rows)
    buf = luma
    for _ in range(2):
        buf = _box_1d(buf, w_rows)
        buf = _box_1d(buf.T.copy(), w_cols).T.copy()
    return buf


def _decimate(buf: np.ndarray) -> np.ndarray:
    rows, cols = buf.shape
    ri = [int(((i + 0.5) * rows) / 64) for i in range(64)]
    ci = [int(((j + 0.5) * cols) / 64) for j in range(64)]
    return buf[np.ix_(ri, ci)]


def _quality(b64: np.ndarray) -> int:
    dv = ((b64[:-1, :] - b64[1:, :]) * 100) / 255
    dh = ((b64[:, :-1] - b64[:, 1:]) * 100) / 255
    g = int(np.abs(np.trunc(dv)).astype(np.int64).sum()) + int(np.abs(np.trunc(dh)).astype(np.int64).sum())
    q = int(g / 90)
    return 100 if q > 100 else q


def _dct16(a: np.ndarray) -> np.ndarray:
    # T[i][j] = sum_k D[i][k] A[k][j], accumulated k = 0..63 from 0.0 (vendor order)
    t = np.zeros((16, 64), dtype=np.float64)
    for k in range(64):
        t = t + DCT[:, k : k + 1] * a[k : k + 1, :]
    # B[i][j] = sum_k T[i][k] D[j][k]
    b = np.zeros((16, 16), dtype=np.float64)
    for k in range(64):
        b = b + t[:, k : k + 1] * DCT[:, k][None, :]
    return b


def _torben(m: np.ndarray) -> float:
    """Vendor MatrixUtil.torben on the 256 values in row-major order (scalar, exact)."""
    vals = [float(v) for v in m.reshape(-1)]
    n = len(vals)
    midn = int((n + 1) / 2)
    lo = hi = vals[0]
    for v in vals:
        if v < lo:
            lo = v
        if v > hi:
            hi = v
    while True:
        guess = float((lo + hi) / 2)
        less = greater = equal = 0
        maxlt = lo
        mingt = hi
        for v in vals:
            if v < guess:
                less += 1
                if v > maxlt:
                    maxlt = v
            elif v > guess:
                greater += 1
                if v < mingt:
                    mingt = v
            else:
                equal += 1
        if less <= midn and greater <= midn:
            break
        elif less > greater:
            hi = maxlt
        else:
            lo = mingt
    if less >= midn:
        return maxlt
    elif less + equal >= midn:
        return guess
    return mingt


def _bits_to_hex(b16: np.ndarray) -> str:
    med = _torben(b16)
    bits = (b16 > med).reshape(-1)  # bit index i*16 + j
    words = []
    for w in range(16):
        v = 0
        for k in range(16):
            if bits[w * 16 + k]:
                v |= 1 << k
        words.append(v)
    return "".join(f"{words[w]:04x}" for w in range(15, -1, -1))


def _dihedral(b: np.ndarray, name: str) -> np.ndarray:
    i = np.arange(16)[:, None]
    j = np.arange(16)[None, :]
    if name == "orig":
        return b
    if name == "rot90":  # B[j][i] = A[i][j] if j odd else -A[i][j]
        return np.where(j & 1, b, -b).T
    if name == "rot180":
        return np.where((i + j) & 1, -b, b)
    if name == "rot270":
        return np.where(i & 1, b, -b).T
    if name == "flipx":
        return np.where(i & 1, b, -b)
    if name == "flipy":
        return np.where(j & 1, b, -b)
    if name == "flipp":
        return b.T
    if name == "flipm":
        return np.where((i + j) & 1, -b, b).T
    raise ValueError(name)


def pdq_from_luma(luma: np.ndarray, dihedral: bool = False):
    """Return (hex, quality) or (dict name->hex, quality) when dihedral is True."""
    buf = _jarosz(np.ascontiguousarray(luma, dtype=np.float64))
    b64 = _decimate(buf)
    quality = _quality(b64)
    b16 = _dct16(b64)
    if not dihedral:
        return _bits_to_hex(b16), quality
    return {n: _bits_to_hex(_dihedral(b16, n)) for n in DIHEDRAL_NAMES}, quality


def hamming_hex(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()
