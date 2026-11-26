"""Proposed grey/resize arithmetic, ordinary binary64 implementation.

Research only. No decoding, trim, DCT, corpus, or experiment runner.
"""
import math

SCALE = 1 << 22


def grey(rgb):
    return [[(19595*r + 38470*g + 7471*b + 32768)//65536
             for r, g, b in row] for row in rgb]


def coefficients(n):
    result = []
    scale = n / 32
    f = max(1.0, scale)
    inv = 1.0 / f
    support = 2.0 * f
    for j in range(32):
        center = (j + 0.5) * scale
        lo = max(0, int(center - support + 0.5))
        hi = min(n, int(center + support + 0.5))
        weights = []
        for i in range(lo, hi):
            t = abs((i - center + 0.5) * inv)
            if t < 1:
                w = ((1.5*t - 2.5)*t)*t + 1.0
            elif t < 2:
                w = (((t - 5.0)*t + 8.0)*t - 4.0)*-0.5
            else:
                w = 0.0
            weights.append(w)
        total = 0.0
        for w in weights:
            total += w
        weights = [w / total if total != 0 else w for w in weights]
        result.append((lo, [int(w*SCALE + (-0.5 if w < 0 else 0.5)) for w in weights]))
    return result


def axis(a, direction, quantize=True):
    if direction == 'y':
        return list(map(list, zip(*axis(list(map(list, zip(*a))), 'x', quantize))))
    if len(a[0]) == 32:
        return [row[:] for row in a]
    cs = coefficients(len(a[0]))
    out = []
    for row in a:
        line = []
        for lo, qs in cs:
            value = sum(row[lo+i]*q for i, q in enumerate(qs))
            line.append(max(0, min(255, (value + SCALE//2)//SCALE)) if quantize else value/SCALE)
        out.append(line)
    return out


def resize(a, mutation=None):
    h, w = len(a), len(a[0])
    order = ['y', 'x'] if h > 32 and h-32 > 2*(w-32) else ['x', 'y']
    if mutation == 'wrong-order':
        order.reverse()
    first = axis(a, order[0], mutation != 'final-only')
    out = axis(first, order[1], mutation != 'final-only')
    if mutation == 'final-only':
        out = [[max(0, min(255, math.floor(v+0.5))) for v in row] for row in out]
    return out, first, ''.join(order)
