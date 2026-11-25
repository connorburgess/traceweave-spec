#!/usr/bin/env python3
"""Cross-check py-tokens draft-1 against the CPython tokenizer of the running interpreter.

    python3 -I harness/crosscheck.py [--vectors] [--stdlib] [--unicode] [--json OUT]

Pinned oracle: CPython 3.14.6 (the script refuses another version unless
--any-version is given, because the profile cites the 3.14.6 tokenizer).

Oracles, both from the interpreter itself, offline:
  * accept/reject and error position: the C tokenizer in parser mode,
    tokenize._generate_tokens_from_c_tokenizer(..., extra_tokens=False). This is
    the tokenizer compile() uses, with identifier and numeric-literal checks on.
  * token boundaries: tokenize.generate_tokens (the same C tokenizer in
    extra-tokens mode), whose positions are mapped back to the original input.

CPython replaces CR LF and lone CR by LF before tokenizing (profile §4.1); the
harness does the same and keeps an offset map, so spans are compared in the
original input. Classes are compared coarsely: NAME = keyword|ident, NUMBER =
int|float|imag, STRING = string|bytes. Adjustments, each counted:
  * fmid-merge: CPython splits an f/t-string literal run at '{{', '}}' and after
    '\\N{...}'; the profile emits one token per run (profile §6.3).
  * empty-fmid: CPython emits empty FSTRING_MIDDLE tokens; dropped.
Everything else that differs is a divergence, classified by cause.

The lexer under test is pylex.py (the checker's lexer), the same module the
checker uses to re-derive every vector.
"""
import argparse
import base64
import collections
import io
import json
import sys
import sysconfig
import token
import tokenize
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import pylex  # noqa: E402

PINNED = (3, 14, 6)
NUMBER = {"int", "float", "imag"}
STRINGS = {"string", "bytes"}


def coarse(cls):
    if cls in ("keyword", "ident"):
        return "name"
    if cls in NUMBER:
        return "number"
    if cls in STRINGS:
        return "string"
    return cls


def translate(text):
    """CR LF and lone CR -> LF, with m[k] = original index of translated index k (m[len] = len)."""
    out, m = [], []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\r":
            out.append("\n")
            m.append(i)
            i += 2 if i + 1 < n and text[i + 1] == "\n" else 1
            continue
        out.append(c)
        m.append(i)
        i += 1
    m.append(n)
    return "".join(out), m


def oracle(text):
    """('ok', [(coarse, start, end)], adjustments) or ('error', type, message, orig offset or None)."""
    t, m = translate(text)
    starts = [0]
    for k, c in enumerate(t):
        if c == "\n":
            starts.append(k + 1)

    def pos(rc):
        row, col = rc
        if row - 1 >= len(starts):
            return len(text)
        k = starts[row - 1] + col
        return m[min(k, len(t))]

    warnings.simplefilter("ignore")
    try:
        for _ in tokenize._generate_tokens_from_c_tokenizer(io.StringIO(t).readline, extra_tokens=False):
            pass
    except (SyntaxError, tokenize.TokenError) as e:
        off = None
        if isinstance(e, tokenize.TokenError) and len(e.args) > 1 and isinstance(e.args[1], tuple):
            row, col = e.args[1]
            if row and col is not None and row - 1 < len(starts):
                off = pos((row, max(col - 1, 0)))
        elif isinstance(e, SyntaxError) and e.lineno and e.offset:
            if e.lineno - 1 < len(starts):
                off = pos((e.lineno, max(e.offset - 1, 0)))
        return ("error", type(e).__name__, str(e.args[0]), off)
    toks = list(tokenize.generate_tokens(io.StringIO(t).readline))
    out, adj = [], collections.Counter()
    i = 0
    while i < len(toks):
        tk = toks[i]
        name = token.tok_name[tk.type]
        if name in ("NL", "COMMENT", "ENDMARKER"):
            i += 1
            continue
        if name in ("FSTRING_MIDDLE", "TSTRING_MIDDLE"):
            j = i
            while j < len(toks) and token.tok_name[toks[j].type] == name:
                j += 1
            a, b = pos(tk.start), pos(toks[j].start)
            if j - i > 1:
                adj["fmid-merge"] += 1
            if a == b:
                adj["empty-fmid"] += 1
            else:
                out.append((name.lower().replace("_", "-"), a, b))
            i = j
            continue
        if name == "NEWLINE":
            p = pos(tk.start)
            out.append(("newline", p, p))
        elif name == "INDENT":
            p = pos(tk.end)
            out.append(("indent", p, p))
        elif name == "DEDENT":
            p = pos(tk.start)
            out.append(("dedent", p, p))
        elif name == "NAME":
            out.append(("name", pos(tk.start), pos(tk.end)))
        elif name == "NUMBER":
            out.append(("number", pos(tk.start), pos(tk.end)))
        elif name == "STRING":
            out.append(("string", pos(tk.start), pos(tk.end)))
        elif name in ("FSTRING_START", "FSTRING_END", "TSTRING_START", "TSTRING_END"):
            out.append((name.lower().replace("_", "-"), pos(tk.start), pos(tk.end)))
        elif name == "OP":
            out.append(("punct", pos(tk.start), pos(tk.end)))
        else:
            out.append((name.lower(), pos(tk.start), pos(tk.end)))
        i += 1
    return ("ok", out, adj)


def ours(text):
    r = pylex.lex(text)
    if r[0] == "error":
        return r
    return ("ok", [(coarse(c), a, b) for c, a, b in r[1]])


def classify(text, mine, theirs):
    """Name the cause of a divergence (profile §9). Returns a short class name."""
    if mine[0] == "error" and theirs[0] == "ok":
        code, off = mine[1], mine[2]
        ch = text[off] if off < len(text) else ""
        if code == "illegal-character" and ch in "$?`":
            return "D-ascii-unused (CPython tokenizer: OP; parser rejects)"
        if code == "illegal-character" and ch == "\\":
            return "D-backslash-continuation"
        if code == "illegal-character" and ord(ch or "\0") >= 128:
            return "D-unicode-17 (character newer than CPython's Unicode 16.0.0)"
        if code == "unterminated-literal" and ":" in text:
            return "D-11 (closing quote inside a format spec; CPython's compiler rejects too)"
        return f"profile rejects, CPython accepts: {code}"
    if mine[0] == "ok" and theirs[0] == "error":
        msg = theirs[2]
        if any(ord(c) >= 128 and not c.isidentifier() and (pylex.T.has("xid_start", ord(c))
               or pylex.T.has("xid_continue", ord(c))) and not ("a" + c).isidentifier() for c in text):
            return "D-unicode-17 (character newer than CPython's Unicode 16.0.0)"
        if any(l.lstrip(" \t\f").startswith("\\") for l in text.replace("\r", "\n").split("\n")):
            return "D-backslash-indent"
        if "invalid character" in msg or "non-printable" in msg:
            return "CPython rejects identifier character"
        if "too many nested" in msg or "nested too deeply" in msg or "too many levels" in msg:
            return "D-9 (CPython depth limit)"
        return f"CPython rejects, profile accepts: {theirs[1]}: {msg[:60]}"
    a, b = mine[1], theirs[1]
    texts_a = [text[s:e] for _, s, e in a if _ == "punct"]
    texts_b = [text[s:e] for _, s, e in b if _ == "punct"]
    if "<>" in texts_b and "<>" not in texts_a:
        return "D-ltgt (CPython OP '<>'; profile '<' '>')"
    if any(l.lstrip(" \t\f").startswith("\\") for l in text.replace("\r", "\n").split("\n")):
        return "D-backslash-indent"
    import re
    if re.search(r":[^'\"]*\}\{\{", text):
        return "D-spec-brace (CPython: '{{' after a nested field in a format spec is an escape)"
    return "token streams differ"


def compare(text):
    """Returns (verdict, detail). verdict in agree, agree-error-same, agree-error-other, diverge."""
    mine, theirs = ours(text), oracle(text)
    if mine[0] == "error" and theirs[0] == "error":
        return ("both-reject-same" if theirs[3] == mine[2] else "both-reject-other"), (mine, theirs), None
    if mine[0] == "ok" and theirs[0] == "ok":
        if mine[1] == theirs[1]:
            return "agree", None, theirs[2]
        return "diverge", classify(text, mine, theirs), theirs[2]
    return "diverge", classify(text, mine, theirs), None


def precheck(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None, "invalid-utf8"
    if "﻿" in text:
        return None, "bom"
    if "\x00" in text:
        return None, "nul"
    return text, None


def run_stdlib(report):
    lib = Path(sysconfig.get_paths()["stdlib"])
    files = sorted(p for p in lib.rglob("*.py") if "site-packages" not in p.parts)
    counts, classes, adj = collections.Counter(), collections.Counter(), collections.Counter()
    examples, ntok, nbytes = {}, 0, 0
    for p in files:
        data = p.read_bytes()
        nbytes += len(data)
        text, pre = precheck(data)
        if pre:
            counts["pre-lexing: " + pre] += 1
            examples.setdefault("pre-lexing: " + pre, str(p.relative_to(lib)))
            continue
        verdict, detail, a = compare(text)
        counts[verdict] += 1
        if a:
            adj.update(a)
        if verdict == "agree":
            ntok += len(pylex.lex(text)[1])
        if verdict == "diverge":
            classes[detail] += 1
            examples.setdefault(detail, str(p.relative_to(lib)))
    report["stdlib"] = {"root": "stdlib of the running interpreter", "files": len(files), "bytes": nbytes,
                        "agreeTokens": ntok, "verdicts": dict(counts), "divergenceClasses": dict(classes),
                        "adjustments": dict(adj), "examples": examples}
    print(f"stdlib: {len(files)} files, {nbytes} bytes; " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"  agreeing files: {ntok} tokens; adjustments: {dict(adj)}")
    for k, v in classes.most_common():
        print(f"  divergence {v:5d}  {k}   e.g. {examples[k]}")


def run_vectors(report):
    doc = json.loads((HERE.parent / "py.json").read_text(encoding="utf-8"))
    counts, rows = collections.Counter(), []
    for v in doc["vectors"]:
        data = base64.b64decode(v["inputBase64"])
        text, pre = precheck(data)
        if pre or len(data) > 1048576:
            counts["pre-lexing (not compared)"] += 1
            continue
        verdict, detail, _ = compare(text)
        dep = "departure" in v["tags"]
        key = verdict + (" (tagged departure)" if dep else "")
        counts[key] += 1
        if verdict == "diverge" or dep:
            rows.append((v["id"], verdict, detail if isinstance(detail, str) else ""))
    report["vectors"] = {"verdicts": dict(counts), "rows": rows}
    print("vectors: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    for r in rows:
        print(f"  {r[0]}: {r[1]} {r[2]}")
    bad = [r for r in rows if r[1] == "diverge" and not any(
        v["id"] == r[0] and "departure" in v["tags"] for v in doc["vectors"])]
    report["vectors"]["undocumented"] = len(bad)
    print(f"  undocumented divergences: {len(bad)}")


def run_unicode(report):
    starts, conts, removed = 0, 0, 0
    for cp in range(0x110000):
        if 0xD800 <= cp < 0xE000:
            continue
        c = chr(cp)
        ps, pc = c.isidentifier(), ("a" + c).isidentifier()
        qs = cp == 0x5F or pylex.T.has("xid_start", cp)
        qc = pylex.T.has("xid_continue", cp)
        starts += ps != qs
        conts += pc != qc
        removed += (ps and not qs) or (pc and not qc)
    import unicodedata
    report["unicode"] = {"cpythonUnicode": unicodedata.unidata_version, "profileUnicode": "17.0.0",
                         "startDiffers": starts, "continueDiffers": conts, "acceptedOnlyByCPython": removed}
    print(f"unicode: CPython {unicodedata.unidata_version} vs pinned 17.0.0: name start differs on {starts}, "
          f"continue on {conts} code points; accepted only by CPython: {removed}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vectors", action="store_true")
    ap.add_argument("--stdlib", action="store_true")
    ap.add_argument("--unicode", action="store_true")
    ap.add_argument("--fuzz", type=int, default=0, metavar="N")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--any-version", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    if sys.version_info[:3] != PINNED and not a.any_version:
        raise SystemExit(f"oracle is CPython {'.'.join(map(str, PINNED))}; this is {sys.version.split()[0]}")
    report = {"python": sys.version.split()[0]}
    if a.vectors:
        run_vectors(report)
    if a.stdlib:
        run_stdlib(report)
    if a.unicode:
        run_unicode(report)
    if a.fuzz:
        run_fuzz(report, a.seed, a.fuzz)
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


ALPHABET = list("'\"{}()[]\\\n\r\t\f #0123456789frbutFRBUT_.ejJxXoObB:=!<>-+*/%@&|^~,; ") + ["\r\n", "    ", "\t", "é", "€", "꟎", "$", "?", "`", "\x0b"]


PIECES = ["f'", 'f"', "rf'", "Rb'", "f'''", 'f"""', "t'", "u'", "ur'", "b'", "'", '"', "'''", "{", "}", "{{",
          "}}", ":", "!r", "!", "=", ":=", "!=", "\\N{DASH}", "\\N{", "\\", "\\{", "x", "y", "lambda", "if", "match",
          "1", "0", "0o", "1_0", "1e", "1j", ".5", "\n", "\r", "\r\n", " ", "    ", "\t", "\f", "#c", "(", ")", "[",
          "]", ",", "\\\n", "else", "or", "and", "<>", "->", "...", "@", "é", "%", "}'", "'}"]


def gen_piece_soup(rnd):
    """A random concatenation of fragments that stress f-strings, prefixes, numbers and layout."""
    return "".join(rnd.choice(PIECES) for _ in range(rnd.randrange(2, 14)))


def run_fuzz(report, seed, cases):
    import random
    rnd = random.Random(seed)
    lib = Path(sysconfig.get_paths()["stdlib"])
    files = sorted(p for p in lib.rglob("*.py") if "site-packages" not in p.parts)
    texts = []
    for p in files:
        text, pre = precheck(p.read_bytes())
        if text and len(text) > 400:
            texts.append(text)
    counts, classes, examples = collections.Counter(), collections.Counter(), {}
    for _ in range(cases):
        if rnd.random() < 0.5:
            s = gen_piece_soup(rnd)
            verdict, detail, _ = compare(s)
            counts["soup " + verdict] += 1
            if verdict == "diverge":
                classes[detail] += 1
                if detail not in examples or len(s) < len(examples[detail]):
                    examples[detail] = s
            continue
        t = rnd.choice(texts)
        a = rnd.randrange(len(t) - 300)
        s = t[a:a + rnd.randrange(20, 300)]
        for _m in range(rnd.randrange(1, 4)):
            k = rnd.randrange(len(s) + 1)
            op = rnd.random()
            if op < 0.5:
                s = s[:k] + rnd.choice(ALPHABET) + s[k:]
            elif op < 0.8:
                s = s[:k] + s[k + 1:]
            else:
                s = s[:k] + rnd.choice(ALPHABET) + s[k + 1:]
        verdict, detail, _ = compare(s)
        counts[verdict] += 1
        if verdict == "diverge":
            classes[detail] += 1
            if detail not in examples or len(s) < len(examples[detail]):
                examples[detail] = s
    report["fuzz"] = {"seed": seed, "cases": cases, "verdicts": dict(counts), "divergenceClasses": dict(classes),
                      "examples": examples}
    print(f"fuzz (seed {seed}): {cases} mutated snippets; " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    for k, v in classes.most_common():
        print(f"  divergence {v:5d}  {k}   e.g. {examples[k][:120]!r}")


if __name__ == "__main__":
    main()
