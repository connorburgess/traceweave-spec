#!/usr/bin/env python3
"""Measure how layout tokens and ';' affect the normalized channel (profile §7, PYOD-4).

    python3 -I harness/layout_survival.py [--limit N]

Sample: every top-level module of the running interpreter's standard library
(Lib/*.py, sorted; no packages, no tests) that py-tokens accepts. Each file is
rewritten by source transformations that keep the program the same (checked
with ast.dump: any file whose rewrite changes the AST is skipped and counted):

  reindent2   every block level becomes 2 spaces instead of the original width
  tabs        every block level becomes one tab
  semi-split  every ';' between simple statements becomes a line break at the
              same indentation (the formatter rule of black and ruff)
  expand      every one-line compound statement 'if x: y' becomes a header line
              and an indented body (also a black/ruff rule)
  dedent-last a CONTROL that changes the program: the last statement of the
              first block with at least two statements is moved out of the
              block. A good normalized channel must NOT be blind to this.

For each normalizedExclusions variant the script reports the share of the
original file's distinct normalized fingerprint hashes that survive in the
rewritten file (k = 5, w = 4, the contract §7/§8 hash with profile py-tokens
draft-1), pooled over files, and for the control the number of files whose
normalized fingerprint set is unchanged ("blind").
"""
import argparse
import ast
import hashlib
import io
import sys
import sysconfig
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import pylex  # noqa: E402

VARIANTS = {
    "none": [],
    "semicolon": [("punct", ";")],
    "semicolon+newline": [("punct", ";"), ("newline", None)],
    "all-layout+semicolon": [("punct", ";"), ("newline", None), ("indent", None), ("dedent", None)],
}
DOMAIN = b"traceweave/token-kgram/draft-1"


def lp(b):
    return len(b).to_bytes(4, "big") + b


def fingerprints(text, excl, k=5, w=4):
    r = pylex.lex(text)
    if r[0] != "ok":
        return None
    toks = [(c, text[a:b]) for c, a, b in r[1]]
    keep = [(c, "" if c == "ident" or c in pylex.LITERAL_CLASSES else t) for c, t in toks
            if not any(c == ec and (et is None or t == et) for ec, et in excl)]
    pre = lp(DOMAIN) + lp(b"py-tokens") + lp(b"draft-1") + lp(b"normalized") + k.to_bytes(4, "big")
    hs = []
    for i in range(max(0, len(keep) - k + 1)):
        h = hashlib.sha256(pre + b"".join(lp(c.encode()) + lp(v.encode()) for c, v in keep[i:i + k]))
        hs.append(int.from_bytes(h.digest()[:8], "big"))
    if not hs:
        return set()
    if len(hs) < w:
        return {min(hs)}
    out = set()
    for s in range(len(hs) - w + 1):
        win = hs[s:s + w]
        m = min(win)
        out.add(m)
    return out


def toks(src):
    return list(tokenize.generate_tokens(io.StringIO(src).readline))


def logical_lines(src):
    """[(row of first token, indent depth, [tokens])] for each logical line."""
    out, depth, cur = [], 0, []
    for t in toks(src):
        if t.type == tokenize.INDENT:
            depth += 1
            continue
        if t.type == tokenize.DEDENT:
            depth -= 1
            continue
        if t.type in (tokenize.NL, tokenize.COMMENT, tokenize.ENDMARKER):
            continue
        if t.type == tokenize.NEWLINE:
            if cur:
                out.append((cur[0].start[0], depth, cur))
            cur = []
            continue
        cur.append(t)
    return out


def reindent(src, unit):
    lines = src.splitlines(keepends=True)
    for row, depth, cur in logical_lines(src):
        line = lines[row - 1]
        lines[row - 1] = unit * depth + line.lstrip(" \t")
    return "".join(lines)


def depth0_ops(cur, text):
    d, out = 0, []
    for t in cur:
        if t.type == tokenize.OP and t.string in "([{":
            d += 1
        elif t.type == tokenize.OP and t.string in ")]}":
            d -= 1
        elif t.type in (tokenize.FSTRING_START, tokenize.TSTRING_START):
            d += 1
        elif t.type in (tokenize.FSTRING_END, tokenize.TSTRING_END):
            d -= 1
        elif d == 0 and t.type == tokenize.OP and t.string == text:
            out.append(t)
    return out


def semi_split(src):
    lines = src.splitlines(keepends=True)
    edits = []
    for row, depth, cur in logical_lines(src):
        ind = lines[row - 1][:len(lines[row - 1]) - len(lines[row - 1].lstrip(" \t"))]
        for t in depth0_ops(cur, ";"):
            edits.append((t.start, t.end, "\n" + ind))
    return apply(src, edits)


HEADERS = {"if", "elif", "else", "for", "while", "try", "except", "finally", "with", "def", "class", "async"}


def expand(src):
    lines = src.splitlines(keepends=True)
    edits = []
    for row, depth, cur in logical_lines(src):
        if cur[0].string not in HEADERS:
            continue
        colons = depth0_ops(cur, ":")
        if not colons:
            continue
        c = colons[0]
        rest = [t for t in cur if t.start > c.start]
        if not rest:
            continue
        ind = lines[row - 1][:len(lines[row - 1]) - len(lines[row - 1].lstrip(" \t"))]
        body = ind + "    "
        edits.append((c.end, rest[0].start, "\n" + body))
        for t in depth0_ops(rest, ";"):
            edits.append((t.start, t.end, "\n" + body))
    return apply(src, edits)


def dedent_last(src):
    """Move the last statement of the first block of >= 2 simple statements out of its block."""
    lls = logical_lines(src)
    lines = src.splitlines(keepends=True)
    for i in range(1, len(lls) - 1):
        row, depth, cur = lls[i]
        prow, pdepth, _ = lls[i - 1]
        nrow, ndepth, _ = lls[i + 1]
        if depth >= 1 and pdepth == depth and ndepth < depth and cur[0].string not in HEADERS \
                and cur[-1].start[0] == row and lls[i - 1][2][0].string not in HEADERS:
            line = lines[row - 1]
            unit = line[:len(line) - len(line.lstrip(" \t"))]
            new = unit[:len(unit) - (len(unit) // depth)] if " " in unit else unit[:-1]
            lines[row - 1] = new + line.lstrip(" \t")
            return "".join(lines)
    return None


def apply(src, edits):
    if not edits:
        return src
    starts = [0]
    for line in src.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))

    def off(rc):
        return starts[rc[0] - 1] + rc[1]
    out, last = [], 0
    for a, b, rep in sorted(edits, key=lambda e: off(e[0])):
        out.append(src[last:off(a)])
        out.append(rep)
        last = off(b)
    out.append(src[last:])
    return "".join(out)


def same_ast(a, b):
    try:
        return ast.dump(ast.parse(a)) == ast.dump(ast.parse(b))
    except SyntaxError:
        return False


def semi_corpus():
    lib = Path(sysconfig.get_paths()["stdlib"])
    stats = {v: [0, 0] for v in VARIANTS}
    files = changed = skipped = semis = 0
    for p in sorted(lib.rglob("*.py")):
        if "site-packages" in p.parts:
            continue
        try:
            src = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if ";" not in src or pylex.lex(src)[0] != "ok":
            continue
        files += 1
        try:
            n = sum(len(depth0_ops(cur, ";")) for _, _, cur in logical_lines(src))
            out = semi_split(src) if n else src
        except (tokenize.TokenError, IndentationError, SyntaxError):
            continue
        if out == src:
            continue
        if not same_ast(src, out) or pylex.lex(out)[0] != "ok":
            skipped += 1
            continue
        changed += 1
        semis += n
        for v, e in VARIANTS.items():
            b, o = fingerprints(src, e), fingerprints(out, e)
            stats[v][0] += len(b & o)
            stats[v][1] += len(b)
    print(f"semi-split over the stdlib: {files} lexable files contain ';'; {changed} rewritten ({semis} ';' "
          f"statement separators), {skipped} skipped (rewrite changed the AST, e.g. 'if x: a; b')")
    for v in VARIANTS:
        sv, nv = stats[v]
        print(f"  {v:22} {100 * sv / nv:6.2f}% ({sv}/{nv}) of distinct normalized fingerprints survive")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--semi-corpus", action="store_true",
                    help="semi-split only, over every stdlib file (tests included) that has a ';' between statements")
    a = ap.parse_args()
    if a.semi_corpus:
        return semi_corpus()
    lib = Path(sysconfig.get_paths()["stdlib"])
    files = sorted(lib.glob("*.py"))
    if a.limit:
        files = files[:a.limit]
    transforms = {"reindent2": lambda s: reindent(s, "  "), "tabs": lambda s: reindent(s, "\t"),
                  "semi-split": semi_split, "expand": expand}
    stats = {t: {v: [0, 0] for v in VARIANTS} for t in transforms}
    changed = {t: 0 for t in transforms}
    skipped = {t: 0 for t in transforms}
    blind = {v: 0 for v in VARIANTS}
    controls, nfiles, ntokens = 0, 0, 0
    for p in files:
        try:
            src = p.read_text(encoding="utf-8")
            ast.parse(src)
        except (UnicodeDecodeError, SyntaxError):
            continue
        r = pylex.lex(src)
        if r[0] != "ok":
            continue
        nfiles += 1
        ntokens += len(r[1])
        base = {v: fingerprints(src, e) for v, e in VARIANTS.items()}
        for name, fn in transforms.items():
            try:
                out = fn(src)
            except (tokenize.TokenError, IndentationError):
                skipped[name] += 1
                continue
            if out == src:
                continue
            if not same_ast(src, out) or pylex.lex(out)[0] != "ok":
                skipped[name] += 1
                continue
            changed[name] += 1
            for v, e in VARIANTS.items():
                fp = fingerprints(out, e)
                stats[name][v][0] += len(base[v] & fp)
                stats[name][v][1] += len(base[v])
        ctl = dedent_last(src)
        if ctl and not same_ast(src, ctl) and pylex.lex(ctl)[0] == "ok":
            controls += 1
            for v, e in VARIANTS.items():
                blind[v] += fingerprints(ctl, e) == base[v]
    print(f"sample: {nfiles} top-level stdlib modules, {ntokens} tokens (Python {sys.version.split()[0]})")
    print("transform     files changed (skipped)   " + "   ".join(f"{v:>22}" for v in VARIANTS))
    for name in transforms:
        cells = []
        for v in VARIANTS:
            s, n = stats[name][v]
            cells.append(f"{(100 * s / n if n else 100):6.2f}% ({s}/{n})".rjust(22))
        print(f"{name:12} {changed[name]:6d} ({skipped[name]:3d})          " + "   ".join(cells))
    print(f"control dedent-last: {controls} files; normalized fingerprint set unchanged (blind): "
          + ", ".join(f"{v} {blind[v]}" for v in VARIANTS))


if __name__ == "__main__":
    main()
