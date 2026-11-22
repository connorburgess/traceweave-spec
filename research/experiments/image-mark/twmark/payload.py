"""Payload derivation and the expected-payload decision rule (protocol §5 and §6).

Payload bits for (key, scheme, entry) are the first n bits, most significant bit first, of
HMAC-SHA256(key, "e-img-m-1|<scheme>|<entry id>"). The two study keys are fixed, public test values,
so anyone can recompute every expected payload from this file; they exercise the statistic, not
key secrecy. The label "e-img-m-1" in the key strings and the HMAC message is the payload-derivation
id; protocol e-img-m-2 keeps it unchanged, so keys and payloads are the same. A deployment would use a secret random key per creator (use case UC-7).

Decision: with raw bits r and expected bits e (both n long), the statistic is the agreement count
m = #{i : r_i = e_i}. Accept iff m >= k(n), where k(n) is the smallest k with
P(Bin(n, 1/2) >= k) <= 10^-6, computed exactly with integers.
"""
from __future__ import annotations

import hashlib
import hmac
from fractions import Fraction
from math import comb

import numpy as np

KEYS = {
    "A": hashlib.sha256(b"traceweave e-img-m-1 study key A (public test key)").digest(),
    "B": hashlib.sha256(b"traceweave e-img-m-1 study key B (public test key)").digest(),
}
PER_COMPARISON_BOUND = Fraction(1, 10**6)


def payload_bits(key_id: str, scheme: str, entry: str, n: int) -> np.ndarray:
    if not (0 < n <= 256):
        raise ValueError("n must be in 1..256")
    mac = hmac.new(KEYS[key_id], f"e-img-m-1|{scheme}|{entry}".encode(), hashlib.sha256).digest()
    bits = np.unpackbits(np.frombuffer(mac, dtype=np.uint8))  # MSB first
    return bits[:n].astype(np.uint8)


def tail(n: int, k: int) -> Fraction:
    """P(Bin(n, 1/2) >= k), exactly."""
    return Fraction(sum(comb(n, i) for i in range(max(k, 0), n + 1)), 2**n)


def k_for(n: int, bound: Fraction = PER_COMPARISON_BOUND) -> int:
    return next(k for k in range(n + 2) if tail(n, k) <= bound)


def agreement(raw: np.ndarray, expected: np.ndarray) -> int:
    if raw.shape != expected.shape:
        raise ValueError(f"length {raw.shape} != {expected.shape}")
    return int(np.count_nonzero(raw == expected))


def bits_hex(bits: np.ndarray) -> str:
    """n bits (n a multiple of 4) as hex, MSB first."""
    b = np.asarray(bits, dtype=np.uint8)
    if b.size % 4:
        raise ValueError("bit count must be a multiple of 4")
    s = "".join(str(int(x)) for x in b)
    return "".join(f"{int(s[i:i + 4], 2):x}" for i in range(0, len(s), 4))


def hex_bits(h: str, n: int) -> np.ndarray:
    s = "".join(f"{int(c, 16):04b}" for c in h)
    if len(s) != n:
        raise ValueError("length mismatch")
    return np.array([int(c) for c in s], dtype=np.uint8)
