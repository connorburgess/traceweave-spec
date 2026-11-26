"""Independent mathematical oracle: exact rationals plus software binary64 rounding.

Does not import the implementation or Pillow. No native float operations.
Expected fixture bytes are computed, not labelled hand-derived.
"""
from fractions import Fraction as F


def nearest_integer(q):
    n, r = divmod(q.numerator, q.denominator)
    return n + (2*r > q.denominator or (2*r == q.denominator and n % 2 == 1))


def b64(q):
    """Round rational to nearest binary64, ties even (finite normal range used here)."""
    q = F(q)
    if not q:
        return q
    sign = -1 if q < 0 else 1
    q = abs(q)
    e = q.numerator.bit_length() - q.denominator.bit_length()
    power = lambda k: F(2**k) if k >= 0 else F(1, 2**(-k))
    if q < power(e):
        e -= 1
    if e < -1022 or e > 1023:
        raise ValueError('oracle only needs finite normal coefficient arithmetic')
    unit = power(e - 52)
    return sign * nearest_integer(q / unit) * unit


def add(a, b): return b64(a+b)
def sub(a, b): return b64(a-b)
def mul(a, b): return b64(a*b)
def div(a, b): return b64(a/b)


def weights(n):
    s = div(F(n), F(32))
    f = max(F(1), s)
    u = div(F(1), f)
    radius = mul(F(2), f)
    table = []
    for destination in range(32):
        c = mul(add(F(destination), F(1, 2)), s)
        left = max(0, int(add(sub(c, radius), F(1, 2))))
        right = min(n, int(add(add(c, radius), F(1, 2))))
        raw = []
        for source in range(left, right):
            x = abs(mul(add(sub(F(source), c), F(1, 2)), u))
            if x >= 2:
                value = F(0)
            elif x >= 1:
                value = mul(sub(mul(add(mul(sub(x, F(5)), x), F(8)), x), F(4)), F(-1, 2))
            else:
                value = add(mul(mul(sub(mul(F(3, 2), x), F(5, 2)), x), x), F(1))
            raw.append(value)
        z = F(0)
        for value in raw:
            z = add(z, value)
        normalized = [div(value, z) if z else value for value in raw]
        quantized = [int(add(mul(value, F(2**22)), F(-1, 2) if value < 0 else F(1, 2)))
                     for value in normalized]
        table.append((left, quantized))
    return table


def grey(rgb):
    # Rational round-half-up differs structurally from integer implementation.
    return [[(F(19595*r+38470*g+7471*b, 65536)+F(1, 2)).__floor__()
             for r, g, b in row] for row in rgb]


def resize(a):
    """Two explicit coordinate passes, no transpose helper or implementation imports."""
    height, width = len(a), len(a[0])
    vertical = height > 32 and height-32 > 2*(width-32)
    order = 'yx' if vertical else 'xy'
    first = None
    for direction in order:
        height, width = len(a), len(a[0])
        n = width if direction == 'x' else height
        if n != 32:
            table = weights(n)
            rows, cols = (height, 32) if direction == 'x' else (32, width)
            out = []
            for y in range(rows):
                row = []
                for x in range(cols):
                    start, qs = table[x if direction == 'x' else y]
                    total = 2**21
                    for offset, coefficient in enumerate(qs):
                        sample = a[y][start+offset] if direction == 'x' else a[start+offset][x]
                        total += sample*coefficient
                    row.append(min(255, max(0, total//(2**22))))
                out.append(row)
            a = out
        if first is None:
            first = [row[:] for row in a]
    return a, first, order
