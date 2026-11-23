#!/usr/bin/env python3
"""Build the draft matching vectors (spec/catalogue-report.md, revision draft-2).

Standard library only. Writes, next to this file:
  extraction-go.json, extraction-rust.json   new synthetic inputs, check_vectors.py format
  comparison-config.json                      exact comparison configuration bytes
  comparison-config-negative.json             configurations that MUST be rejected
  matching.json                               the matching vectors
  example-report.json                         one report document with a provenance block

Each mode of each vector carries a hand expectation with a `derivation` label:
  hand                    written from the inputs and the contract before the value was computed;
  computed-then-reviewed  written or corrected after a computed value had been seen (README lists them).
This script computes hashes, spans, catalogues and report bodies and refuses to write anything if a
computed result contradicts an expectation. check_matching.py re-derives everything independently;
this file is not used by it.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXV = HERE.parent / "extraction"
DOMAIN = b"traceweave/token-kgram/draft-1"
CATALOGUE_VERSION = "traceweave-catalogue-draft-2"
REPORT_VERSION = "traceweave-report-draft-2"
COMPARISON_ID = "traceweave-seed-merge-draft-2"
CHANNELS = ("exact", "normalized")
SUPPORTED_PROFILES = {("go-tokens", "draft-1"), ("rust2024-tokens", "draft-1"), ("ts-tokens", "draft-2"), ("text-plain", "draft-1"),
                      ("py-tokens", "draft-1"),
                      ("go-tokens-three-channel-test", "draft-1")}   # last: TEST-ONLY, flagged in vectors
# Declared channel lists (contract §2b). Comparison `modes` must equal one of them.
CHANNEL_LISTS = {"go-tokens": ["exact", "normalized"], "rust2024-tokens": ["exact", "normalized"],
                 "ts-tokens": ["exact", "normalized"], "text-plain": ["exact", "folded", "skeleton"],
                 "py-tokens": ["exact", "normalized"],
                 "go-tokens-three-channel-test": ["exact", "normalized", "classes"]}
CH3 = ["exact", "normalized", "classes"]
TEST_CONTEXT = [True]   # the builder accepts the TEST-ONLY list except when writing negatives
CONFIG_3CH = (b'{"contract":"traceweave-token-winnow-draft-1","profile":"go-tokens-three-channel-test","profileVersion":"draft-1",'
              b'"channels":["exact","normalized","classes"],"k":5,"window":4,"hash":"sha256-first8-u64be","maxInputBytes":1048576}\n')

# ------------------------------------------------------------------ mini lexers (cross-check only)
# Only the constructs used by the new synthetic inputs. Since the M2.6 hand-derivation ruling the token streams are
# the hand-written HAND_TOKENS below; lex() only cross-checks them, and main() stops if the two disagree.

GO_KW = set("break case chan const continue default defer else fallthrough for func go goto if import "
            "interface map package range return select struct switch type var".split())
GO_OPS = sorted(set("+ & += &= && == != ( ) - | -= |= || < <= [ ] * ^ *= ^= <- > >= { } / << /= <<= ++ = := , ; % "
                    ">> %= >>= -- ! ... . : &^ &^= ~".split()), key=len, reverse=True)
RUST_KW = set("_ as async await break const continue crate dyn else enum extern false fn for if impl in let "
              "loop match mod move mut pub ref return self Self static struct super trait true type unsafe "
              "use where while abstract become box do final gen macro override priv try typeof unsized "
              "virtual yield".split())
RUST_PUNCT = set("!#$%&()*+,-./:;<=>?@[]^{|}~")


def lex(text: str, lang: str):
    toks, i, n, flag = [], 0, len(text), False

    def semi():
        nonlocal flag
        if lang == "go" and flag:
            e = toks[-1]["span"][1]
            toks.append({"class": "punct", "text": ";", "span": [e, e], "inserted": True})
            flag = False

    def emit(cls, s, e):
        nonlocal flag
        toks.append({"class": cls, "text": text[s:e], "span": [s, e]})
        if lang == "go":
            t = text[s:e]
            flag = (cls in ("ident", "int", "string") or t in ("break", "continue", "fallthrough", "return")
                    or (cls == "punct" and t in ("++", "--", ")", "]", "}")))

    while i < n:
        c = text[i]
        if c == "\n":
            semi(); i += 1
        elif c in " \t\r":
            i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            semi()
        elif text.startswith("/*", i):
            j = text.index("*/", i + 2)
            if "\n" in text[i:j]:
                semi()
            i = j + 2
        elif c.isalpha() or c == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            w = text[i:j]
            emit("keyword" if w in (GO_KW if lang == "go" else RUST_KW) else "ident", i, j)
            i = j
        elif c.isascii() and c.isdigit():
            j = i
            while j < n and text[j].isdigit():
                j += 1
            emit("int", i, j); i = j
        elif c == '"':
            j = text.index('"', i + 1)
            assert "\\" not in text[i:j] and "\n" not in text[i:j]
            emit("string", i, j + 1); i = j + 1
        elif lang == "go":
            op = next(o for o in GO_OPS if text.startswith(o, i))
            emit("punct", i, i + len(op)); i += len(op)
        else:
            assert c in RUST_PUNCT, repr(c)
            emit("punct", i, i + 1); i += 1
    semi()
    # Character indices -> UTF-8 byte offsets (contract: spans are byte offsets).
    off, acc = [], 0
    for ch in text:
        off.append(acc)
        acc += len(ch.encode("utf-8"))
    off.append(acc)
    for t in toks:
        t["span"] = [off[t["span"][0]], off[t["span"][1]]]
    return toks


# ------------------------------------------------------------------ hand-written token streams (M2.6, ROADMAP Definitions (a))
# Written by hand from spec/extraction.md (Go and Rust profiles) for the 22 synthetic matching inputs, in the same form
# as ../extraction/harness/build_vectors.py: (class, text) in source order, (P, ";", A) for a Go inserted semicolon
# (zero-width, at the end of the previous token), and an optional third element giving a hand-written start offset where
# a search for the text would land inside a comment. Spans are located by searching for each text in source order
# (arithmetic, ROADMAP Definitions (b)). lex() above is kept only as a cross-check: main() requires it to agree.
A = "AUTO"
I, P, KW, S, N = "ident", "punct", "keyword", "string", "int"


def go_sum(name, total_start=None):
    """GO_SUM's tokens under another function name (same token stream as GO_SUM_FMT)."""
    total = (I, "total") if total_start is None else (I, "total", total_start)
    return [(KW, "func"), (I, name), (P, "("), (I, "values"), (P, "["), (P, "]"), (I, "int"), (P, ")"), (I, "int"), (P, "{"),
            total, (P, ":="), (N, "0"), (P, ";", A),
            (KW, "for"), (I, "_"), (P, ","), (I, "v"), (P, ":="), (KW, "range"), (I, "values"), (P, "{"),
            (KW, "if"), (I, "v"), (P, ">"), (N, "0"), (P, "{"),
            (I, "total"), (P, "+="), (I, "v"), (P, ";", A),
            (P, "}"), (P, ";", A),
            (P, "}"), (P, ";", A),
            (KW, "return"), (I, "total"), (P, ";", A),
            (P, "}"), (P, ";", A)]


GO_HOST_HEAD = [(KW, "package"), (I, "stats"), (P, ";", A),
                (KW, "type"), (I, "Point"), (KW, "struct"), (P, "{"),
                (I, "X"), (P, ","), (I, "Y"), (I, "float64"), (P, ";", A),
                (P, "}"), (P, ";", A),
                (KW, "func"), (P, "("), (I, "p"), (I, "Point"), (P, ")"), (I, "String"), (P, "("), (P, ")"), (I, "string"), (P, "{"),
                (KW, "return"), (I, "fmt"), (P, "."), (I, "Sprintf"), (P, "("), (S, '"(%g, %g)"'), (P, ","),
                (I, "p"), (P, "."), (I, "X"), (P, ","), (I, "p"), (P, "."), (I, "Y"), (P, ")"), (P, ";", A),
                (P, "}"), (P, ";", A)]
GO_HOST_TAIL = [(KW, "var"), (I, "names"), (P, "="), (KW, "map"), (P, "["), (I, "string"), (P, "]"), (I, "bool"), (P, "{"),
                (S, '"a"'), (P, ":"), (I, "true"), (P, ","), (S, '"b"'), (P, ":"), (I, "false"), (P, "}"), (P, ";", A)]
GO_ERR_RETURN = [(KW, "if"), (I, "err"), (P, "!="), (I, "nil"), (P, "{"), (KW, "return"), (I, "err"), (P, ";", A),
                 (P, "}"), (P, ";", A)]
GO_NONASCII_TOKS = [(KW, "func"), (I, "größe"), (P, "("), (I, "näme"), (I, "string"), (P, ")"), (I, "string"), (P, "{"),
                    (I, "grüße"), (P, ":="), (S, '"héllo, 世界"'), (P, ";", A),
                    (KW, "return"), (I, "grüße"), (P, "+"), (I, "näme"), (P, ";", A),
                    (P, "}"), (P, ";", A)]


def go_shadow(inner):
    return [(KW, "func"), (I, "f"), (P, "("), (I, "ok"), (I, "bool"), (P, ")"), (I, "int"), (P, "{"),
            (I, "x"), (P, ":="), (N, "1"), (P, ";", A),
            (KW, "if"), (I, "ok"), (P, "{"),
            (I, inner), (P, ":="), (N, "2"), (P, ";", A),
            (I, "x"), (P, "+="), (I, inner), (P, ";", A),
            (P, "}"), (P, ";", A),
            (KW, "return"), (I, "x"), (P, ";", A),
            (P, "}"), (P, ";", A)]


# "total" on GO_SUM_FMT's second line: a search would find the "total" in the first line's comment. Hand count:
# GO_HOST_FMT's prefix up to "func sumPositive" is 171 bytes (14 + 1 + 20 + 14 + 2 + 1 + 33 + 42 + 2 + 1 + 41), and
# GO_SUM_FMT's first line is 63 bytes, then 4 spaces: 171 + 63 + 4 = 238.
GO_HOST_FMT_TOTAL_START = 238

RUST_SUM_TOKS = [(KW, "fn"), (I, "sum_positive"), (P, "("), (I, "values"), (P, ":"), (P, "&"), (P, "["), (I, "i32"), (P, "]"),
                 (P, ")"), (P, "-"), (P, ">"), (I, "i32"), (P, "{"),
                 (KW, "let"), (KW, "mut"), (I, "total"), (P, "="), (N, "0"), (P, ";"),
                 (KW, "for"), (I, "v"), (KW, "in"), (I, "values"), (P, "{"),
                 (KW, "if"), (P, "*"), (I, "v"), (P, ">"), (N, "0"), (P, "{"),
                 (I, "total"), (P, "+"), (P, "="), (P, "*"), (I, "v"), (P, ";"),
                 (P, "}"),
                 (P, "}"),
                 (I, "total"),
                 (P, "}")]
RUST_HOST_HEAD = [(KW, "use"), (I, "std"), (P, ":"), (P, ":"), (I, "fmt"), (P, ";"),
                  (KW, "pub"), (KW, "struct"), (I, "Point"), (P, "{"),
                  (I, "x"), (P, ":"), (I, "f64"), (P, ","),
                  (I, "y"), (P, ":"), (I, "f64"), (P, ","),
                  (P, "}"),
                  (KW, "impl"), (I, "fmt"), (P, ":"), (P, ":"), (I, "Display"), (KW, "for"), (I, "Point"), (P, "{"),
                  (KW, "fn"), (I, "fmt"), (P, "("), (P, "&"), (KW, "self"), (P, ","), (I, "f"), (P, ":"), (P, "&"), (KW, "mut"),
                  (I, "fmt"), (P, ":"), (P, ":"), (I, "Formatter"), (P, ")"), (P, "-"), (P, ">"),
                  (I, "fmt"), (P, ":"), (P, ":"), (I, "Result"), (P, "{"),
                  (I, "write"), (P, "!"), (P, "("), (I, "f"), (P, ","), (S, '"({}, {})"'), (P, ","),
                  (KW, "self"), (P, "."), (I, "x"), (P, ","), (KW, "self"), (P, "."), (I, "y"), (P, ")"),
                  (P, "}"),
                  (P, "}")]

HAND_TOKENS = {
    "mv-go-sum": go_sum("sumPositive"),
    "mv-go-host": GO_HOST_HEAD + go_sum("sumPositive") + GO_HOST_TAIL,
    "mv-go-partial": [(KW, "func"), (I, "logPositive"), (P, "("), (I, "total"), (I, "int"), (P, ","), (I, "values"), (P, "..."),
                      (I, "int"), (P, ")"), (I, "int"), (P, "{"),
                      (KW, "for"), (I, "_"), (P, ","), (I, "v"), (P, ":="), (KW, "range"), (I, "values"), (P, "{"),
                      (KW, "if"), (I, "v"), (P, ">"), (N, "0"), (P, "{"),
                      (I, "total"), (P, "+="), (I, "v"), (P, ";", A),
                      (P, "}"), (P, ";", A),
                      (P, "}"), (P, ";", A),
                      (KW, "return"), (I, "total"), (P, "*"), (N, "2"), (P, ";", A),
                      (P, "}"), (P, ";", A)],
    "mv-go-twice": go_sum("sumA") + go_sum("sumB"),
    "mv-go-pair": [(KW, "type"), (I, "Pair"), (KW, "struct"), (P, "{"),
                   (I, "Key"), (I, "string"), (P, ";", A),
                   (I, "Value"), (P, "["), (P, "]"), (I, "byte"), (P, ";", A),
                   (P, "}"), (P, ";", A)],
    "mv-go-b1": [(KW, "func"), (I, "load"), (P, "("), (I, "path"), (I, "string"), (P, ")"), (I, "error"), (P, "{"),
                 (I, "data"), (P, ","), (I, "err"), (P, ":="), (I, "os"), (P, "."), (I, "ReadFile"), (P, "("), (I, "path"), (P, ")"),
                 (P, ";", A)]
                + GO_ERR_RETURN
                + [(I, "cache"), (P, "="), (I, "data"), (P, ";", A),
                   (KW, "return"), (I, "nil"), (P, ";", A),
                   (P, "}"), (P, ";", A)],
    "mv-go-b2": [(KW, "func"), (I, "save"), (P, "("), (I, "w"), (I, "io"), (P, "."), (I, "Writer"), (P, ")"), (I, "error"), (P, "{"),
                 (I, "_"), (P, ","), (I, "err"), (P, ":="), (I, "w"), (P, "."), (I, "Write"), (P, "("), (I, "buf"), (P, ")"), (P, ";", A)]
                + GO_ERR_RETURN
                + [(I, "buf"), (P, "="), (I, "buf"), (P, "["), (P, ":"), (N, "0"), (P, "]"), (P, ";", A),
                   (KW, "return"), (I, "nil"), (P, ";", A),
                   (P, "}"), (P, ";", A)],
    "mv-go-b3": [(KW, "func"), (I, "flush"), (P, "("), (I, "sink"), (I, "Sink"), (P, ")"), (I, "error"), (P, "{"),
                 (I, "err"), (P, ":="), (I, "sink"), (P, "."), (I, "Flush"), (P, "("), (P, ")"), (P, ";", A)]
                + GO_ERR_RETURN
                + [(I, "stamp"), (P, "="), (I, "now"), (P, ";", A),
                   (KW, "return"), (I, "nil"), (P, ";", A),
                   (P, "}"), (P, ";", A)],
    "mv-go-put": [(KW, "type"), (I, "Store"), (KW, "struct"), (P, "{"), (I, "m"), (KW, "map"), (P, "["), (I, "string"), (P, "]"),
                  (I, "int"), (P, "}"), (P, ";", A),
                  (KW, "func"), (P, "("), (I, "s"), (P, "*"), (I, "Store"), (P, ")"), (I, "Put"), (P, "("), (I, "k"), (I, "string"),
                  (P, ","), (I, "v"), (I, "int"), (P, ")"), (I, "error"), (P, "{"),
                  (KW, "if"), (I, "err"), (P, ":="), (I, "s"), (P, "."), (I, "check"), (P, "("), (I, "k"), (P, ")"), (P, ";"),
                  (I, "err"), (P, "!="), (I, "nil"), (P, "{"),
                  (KW, "return"), (I, "err"), (P, ";", A),
                  (P, "}"), (P, ";", A),
                  (I, "s"), (P, "."), (I, "m"), (P, "["), (I, "k"), (P, "]"), (P, "="), (I, "v"), (P, ";", A),
                  (KW, "return"), (I, "nil"), (P, ";", A),
                  (P, "}"), (P, ";", A)],
    "mv-go-nonascii": GO_NONASCII_TOKS,
    "mv-go-nonascii-prefixed": GO_NONASCII_TOKS,       # the comment line adds no token
    "mv-go-independent": [(KW, "func"), (I, "positiveTotal"), (P, "("), (I, "xs"), (P, "["), (P, "]"), (I, "int"), (P, ")"),
                          (P, "("), (I, "sum"), (I, "int"), (P, ")"), (P, "{"),
                          (KW, "for"), (I, "i"), (P, ":="), (N, "0"), (P, ";"), (I, "i"), (P, "<"), (I, "len"), (P, "("), (I, "xs"),
                          (P, ")"), (P, ";"), (I, "i"), (P, "++"), (P, "{"),
                          (KW, "if"), (I, "xs"), (P, "["), (I, "i"), (P, "]"), (P, ">"), (N, "0"), (P, "{"),
                          (I, "sum"), (P, "+="), (I, "xs"), (P, "["), (I, "i"), (P, "]"), (P, ";", A),
                          (P, "}"), (P, ";", A),
                          (P, "}"), (P, ";", A),
                          (KW, "return"), (P, ";", A),
                          (P, "}"), (P, ";", A)],
    "mv-go-shadow-a": go_shadow("y"),
    "mv-go-shadow-b": go_shadow("x"),
    "mv-go-periodic6": [(I, "x"), (P, "++"), (P, ";", A)] * 6,
    "mv-go-classes-a": [(KW, "return"), (I, "x"), (P, "+"), (I, "f"), (P, "("), (N, "1"), (P, ")"), (P, ";", A),
                        (KW, "break"), (P, ";", A),
                        (I, "x"), (P, "++"), (P, ";", A)],
    "mv-go-classes-b": [(KW, "defer"), (I, "y"), (P, "-"), (I, "g"), (P, "("), (N, "2"), (P, ")"), (P, ";", A),
                        (KW, "continue"), (P, ";", A),
                        (I, "y"), (P, "--"), (P, ";", A)],
    "mv-go-vendor-lib": [(KW, "func"), (I, "PadLeft"), (P, "("), (I, "s"), (I, "string"), (P, ","), (I, "width"), (I, "int"), (P, ")"),
                         (I, "string"), (P, "{"),
                         (KW, "for"), (I, "len"), (P, "("), (I, "s"), (P, ")"), (P, "<"), (I, "width"), (P, "{"),
                         (I, "s"), (P, "="), (S, '" "'), (P, "+"), (I, "s"), (P, ";", A),
                         (P, "}"), (P, ";", A),
                         (KW, "return"), (I, "s"), (P, ";", A),
                         (P, "}"), (P, ";", A)],
    "mv-go-host-formatted": GO_HOST_HEAD + go_sum("sumPositive", GO_HOST_FMT_TOTAL_START) + GO_HOST_TAIL,
    "mv-go-nonascii-prefixed2": GO_NONASCII_TOKS,
    "mv-rust-sum": RUST_SUM_TOKS,
    "mv-rust-host": RUST_HOST_HEAD + RUST_SUM_TOKS,
}


def hand_stream(vid, text):
    """Token records from the hand-written list: spans located by searching for each text in source order."""
    src = text.encode()
    toks, pos = [], 0
    for t in HAND_TOKENS[vid]:
        if len(t) > 2 and t[2] == A:
            e = toks[-1]["span"][1]
            toks.append({"class": "punct", "text": ";", "span": [e, e], "inserted": True})
            continue
        b = t[1].encode()
        i = t[2] if len(t) > 2 else src.index(b, pos)
        assert src[i:i + len(b)] == b and i >= pos, (vid, t)
        toks.append({"class": t[0], "text": t[1], "span": [i, i + len(b)]})
        pos = i + len(b)
    return toks


# ------------------------------------------------------------------ extraction (contract §6–§8)

def lp(b: bytes) -> bytes:
    return len(b).to_bytes(4, "big") + b


LITERALS = {"go": {"int", "float", "imag", "rune", "string"},
            "rust": {"int", "float", "char", "byte", "string", "rawstring", "bytestring", "rawbytestring",
                     "cstring", "rawcstring"}}


def norm_value(lang, cls, text):
    if cls == "ident" or cls in LITERALS[lang]:
        return ""
    if cls == "lifetime" and text not in ("'static", "'_"):
        return ""
    return text


def channel_value(ch, lang, cls, text):
    """exact: the text; normalized: §6; classes (TEST-ONLY third channel): the empty string, so only classes count."""
    return text if ch == "exact" else norm_value(lang, cls, text) if ch == "normalized" else ""


def channels_for(tokens, cfg, lang):
    k, w = cfg["k"], cfg["window"]
    out = {}
    for ch in cfg["channels"]:
        values = [channel_value(ch, lang, t["class"], t["text"]) for t in tokens]
        kg = []
        for i in range(max(0, len(tokens) - k + 1)):
            buf = bytearray(lp(DOMAIN) + lp(cfg["profile"].encode()) + lp(cfg["profileVersion"].encode())
                            + lp(ch.encode()) + k.to_bytes(4, "big"))
            for t, v in zip(tokens[i:i + k], values[i:i + k]):
                buf += lp(t["class"].encode()) + lp(v.encode())
            kg.append({"position": i, "hash": hashlib.sha256(bytes(buf)).digest()[:8].hex(),
                       "span": [tokens[i]["span"][0], tokens[i + k - 1]["span"][1]]})
        m = len(kg)
        if m == 0:
            picks, partial = [], False
        else:
            wins = [(0, m)] if m < w else [(s, s + w) for s in range(m - w + 1)]
            picks = []
            for lo, hi in wins:
                best = lo
                for p in range(lo, hi):
                    if int(kg[p]["hash"], 16) <= int(kg[best]["hash"], 16):
                        best = p
                picks.append(best)
            partial = m < w
        c = {"values": values} if ch != "exact" else {}
        c.update({"kgrams": kg, "windowSelections": picks, "partialWindow": partial,
                  "fingerprints": [dict(kg[p]) for p in sorted(set(picks))]})
        out[ch] = c
    return out


def roadmap_definition():
    """ROADMAP.md, Definitions: the hand-derived rule as one paragraph, Markdown emphasis removed (same reading as
    tools/check_requirement_map.py and check_matching.py)."""
    road = (HERE.parent.parent / "ROADMAP.md").read_text(encoding="utf-8")
    sec = road.split("## Definitions", 1)[1].split("\n## ", 1)[0]
    a = re.search(r"^- \*\*\(a\) (.*)$", sec, re.M).group(1)
    b = re.search(r"^- \*\*\(b\) (.*)$", sec, re.M).group(1)
    last = re.search(r"(A vector whose lexical layer was first produced by a tool.*?otherwise\.)", sec).group(1)
    return ("A vector is hand-derived when both of these hold: (a) " + a + " (b) " + b + " " + last).replace("**", "")


ROADMAP_DEFINITION = roadmap_definition()
EXTRACTION_RULE_APPLICATION = (
    "Applied to these vectors: every token's class and text, and every inserted semicolon, is written by hand from "
    "spec/extraction.md as a literal list in build_vectors.py (HAND_TOKENS), as in ../extraction/harness/build_vectors.py. "
    "The arithmetic over those judgments (byte spans, normalized values, k-gram hashes, window selections and "
    "fingerprints) is computed by this specification's own builder, not by an implementation under test, and is "
    "independently recomputed by ../extraction/check_vectors.py and check_matching.py. A span is located by searching "
    "for the token's hand-written text in source order, except in vectors marked spanStarts: hand, where a hand-written "
    "start replaces a search that would land inside a comment. The builder's mini-lexer lex() is kept only as a "
    "cross-check and must produce the same tokens; it produces no expected value.")
MATCHING_RULE_APPLICATION = (
    "Applied to these vectors: which regions match, their outcomes and every rejection code are written by hand in "
    "each vector's handExpectations, per mode, before the body is computed. Every input token stream is hand-derived: a "
    "vector labelled hand uses only extraction vectors and records labelled derivation hand (the matching lane's four "
    "extraction files are hand-written literals in build_vectors.py) or catalogues written as literals in the "
    "builder, and check_matching.py fails a hand vector that rests on any other lexical layer. Catalogues, report "
    "bodies, spans, counts and digests are computed by build_vectors.py, the specification's own builder, and are "
    "independently recomputed by check_matching.py and by a clean-room review. A vector labelled mixed, or a mode "
    "labelled computed-then-reviewed, had values seen computed before they were written down (README, Derivation).")


def extraction_record(vid, tags, desc, text, cfg, lang):
    toks = hand_stream(vid, text)
    cross = lex(text, lang)
    if toks != cross:   # the contract decides which one is wrong; neither is silently preferred
        bad = next(i for i, (a, b) in enumerate(zip(toks + [None] * len(cross), cross + [None] * len(toks))) if a != b)
        raise SystemExit(f"{vid}: hand-written token {bad} {toks[bad] if bad < len(toks) else None} differs from the "
                         f"lexer cross-check {cross[bad] if bad < len(cross) else None}")
    data = text.encode()
    starts = {"spanStarts": "hand"} if any(len(t) > 2 and t[2] != A for t in HAND_TOKENS[vid]) else {}
    return {"id": vid, "derivation": "hand", **starts, "tags": tags, "description": desc,
            "inputBase64": base64.b64encode(data).decode(), "inputText": text,
            "result": {"status": "ok" if len(toks) >= cfg["k"] else "insufficient-tokens",
                       "tokenCount": len(toks), "tokens": toks, "channels": channels_for(toks, cfg, lang)}}


# ------------------------------------------------------------------ inputs

GO_SUM = """func sumPositive(values []int) int {
\ttotal := 0
\tfor _, v := range values {
\t\tif v > 0 {
\t\t\ttotal += v
\t\t}
\t}
\treturn total
}
"""
GO_SUM_BODY = GO_SUM[len("func sumPositive"):]  # "(values []int) int {...}\n"
GO_HOST = """package stats

type Point struct {
\tX, Y float64
}

func (p Point) String() string {
\treturn fmt.Sprintf("(%g, %g)", p.X, p.Y)
}

""" + GO_SUM + """
var names = map[string]bool{"a": true, "b": false}
"""
GO_PARTIAL = """func logPositive(total int, values ...int) int {
\tfor _, v := range values {
\t\tif v > 0 {
\t\t\ttotal += v
\t\t}
\t}
\treturn total * 2
}
"""
GO_LOOP_EXCERPT = "for _, v := range values {\n\t\tif v > 0 {\n\t\t\ttotal += v\n\t\t}\n\t}\n\treturn total"
GO_TWICE = "func sumA" + GO_SUM_BODY + "\nfunc sumB" + GO_SUM_BODY
GO_PAIR = """type Pair struct {
\tKey   string
\tValue []byte
}
"""
GO_B1 = """func load(path string) error {
\tdata, err := os.ReadFile(path)
\tif err != nil {
\t\treturn err
\t}
\tcache = data
\treturn nil
}
"""
GO_B2 = """func save(w io.Writer) error {
\t_, err := w.Write(buf)
\tif err != nil {
\t\treturn err
\t}
\tbuf = buf[:0]
\treturn nil
}
"""
GO_B3 = """func flush(sink Sink) error {
\terr := sink.Flush()
\tif err != nil {
\t\treturn err
\t}
\tstamp = now
\treturn nil
}
"""
GO_PUT = """type Store struct{ m map[string]int }

func (s *Store) Put(k string, v int) error {
\tif err := s.check(k); err != nil {
\t\treturn err
\t}
\ts.m[k] = v
\treturn nil
}
"""
RUST_SUM = """fn sum_positive(values: &[i32]) -> i32 {
    let mut total = 0;
    for v in values {
        if *v > 0 {
            total += *v;
        }
    }
    total
}
"""
RUST_HOST = """use std::fmt;

pub struct Point {
    x: f64,
    y: f64,
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

""" + RUST_SUM

GO_NONASCII = """func größe(näme string) string {
\tgrüße := "héllo, 世界"
\treturn grüße + näme
}
"""
GO_NONASCII_PREFIX = "// 日本語のコメント\n"   # 3 + 8*3 + 1 = 28 bytes, 12 code points
GO_INDEPENDENT = """func positiveTotal(xs []int) (sum int) {
\tfor i := 0; i < len(xs); i++ {
\t\tif xs[i] > 0 {
\t\t\tsum += xs[i]
\t\t}
\t}
\treturn
}
"""
GO_SHADOW_A = """func f(ok bool) int {
\tx := 1
\tif ok {
\t\ty := 2
\t\tx += y
\t}
\treturn x
}
"""
GO_SHADOW_B = """func f(ok bool) int {
\tx := 1
\tif ok {
\t\tx := 2
\t\tx += x
\t}
\treturn x
}
"""
GO_PERIODIC6 = "x++\n" * 6

NEW_GO = [
    ("mv-go-sum", ["function"], "Original function used as the reference in several matching vectors.", GO_SUM),
    ("mv-go-host", ["large-host"], "Larger host file containing GO_SUM verbatim among unrelated declarations.", GO_HOST),
    ("mv-go-partial", ["partial"], "Different function that copies only the loop and the start of the return of GO_SUM.", GO_PARTIAL),
    ("mv-go-twice", ["duplicate"], "The body of GO_SUM twice, under two other function names.", GO_TWICE),
    ("mv-go-pair", ["unrelated"], "Unrelated struct declaration.", GO_PAIR),
    ("mv-go-b1", ["boilerplate"], "Reference file with the `if err != nil { return err }` idiom.", GO_B1),
    ("mv-go-b2", ["boilerplate"], "Boilerplate-catalogue file with the same idiom.", GO_B2),
    ("mv-go-b3", ["boilerplate"], "Boilerplate-catalogue file with the same idiom.", GO_B3),
    ("mv-go-put", ["boilerplate"], "Candidate sharing only the idiom with the reference.", GO_PUT),
    ("mv-go-nonascii", ["unicode"], "Function with multi-byte identifiers and string.", GO_NONASCII),
    ("mv-go-nonascii-prefixed", ["unicode"], "The same function after a 28-byte, 12-code-point comment line.",
     GO_NONASCII_PREFIX + GO_NONASCII),
    ("mv-go-independent", ["independent"], "GO_SUM's task written independently (index loop, named result).", GO_INDEPENDENT),
    ("mv-go-shadow-a", ["shadowing"], "Inner block declares a fresh variable y.", GO_SHADOW_A),
    ("mv-go-shadow-b", ["shadowing"], "Inner block shadows x instead; same normalized token stream as shadow-a.", GO_SHADOW_B),
    ("mv-go-periodic6", ["repeated-hash"], "x++ six times (periodic hashes).", GO_PERIODIC6),
]
# Inputs for the TEST-ONLY three-channel profile (contract §2b): same class sequence, different keywords and
# operators, non-periodic, 13 tokens (9 k-grams > 2w - 1, so at least two distinct fingerprints).
NEW_GO_CLASSES = [
    ("mv-go-classes-a", ["classes"], "return/break/++ shape.", "return x + f(1)\nbreak\nx++\n"),
    ("mv-go-classes-b", ["classes"], "Same classes as mv-go-classes-a with other keywords and operators.",
     "defer y - g(2)\ncontinue\ny--\n"),
]
# The first draft of this input (a Reverse helper) repeated a normalized 5-gram (the swap line), which broke the
# hand expectation of one diagonal-0 region; it was replaced by this helper, whose 28 normalized 5-grams were checked
# by hand to be distinct (README "Derivation").
GO_VENDOR_LIB = """// Package strutil is a vendored third-party helper.
func PadLeft(s string, width int) string {
\tfor len(s) < width {
\t\ts = " " + s
\t}
\treturn s
}
"""
GO_SUM_FMT = """func sumPositive(values []int)   int {   // total of positives
    total := 0
    for _, v := range values {   // each value
        if v > 0 { total += v
        }
    }
    return total
}
"""
GO_HOST_FMT = """package stats

type Point struct {
\tX, Y float64
}

func (p Point) String() string {
\treturn fmt.Sprintf("(%g, %g)", p.X, p.Y)
}

// sumPositive adds the positive values.
""" + GO_SUM_FMT + """
var names = map[string]bool{"a": true, "b": false}
"""
GO_NONASCII_PREFIX2 = "// Ünïcödé\n"   # 3 + 11 + 1 = 15 bytes, 3 + 7 + 1 = 11 code points (hand count)
NEW_GO_GATES = [
    ("mv-go-vendor-lib", ["vendor"], "A vendored third-party helper file (vendor control class, OD-C19).", GO_VENDOR_LIB),
    ("mv-go-host-formatted", ["large-host", "formatted"],
     "Large host containing GO_SUM reformatted (spacing, indentation, comments, a joined line) with the same token stream.",
     GO_HOST_FMT),
    ("mv-go-nonascii-prefixed2", ["unicode"], "mv-go-nonascii after a 15-byte, 11-code-point comment line.",
     GO_NONASCII_PREFIX2 + GO_NONASCII),
]
NG_ = "../extraction/go.json"
TEXT_RECORDS = "../extraction-text/records-text-plain.json"
TEXT_CFG = "../extraction-text/config-text-plain.json"


def text_record(rid):
    """Record bytes and input of a frozen text-plain record (owned by the text-profile lane, not generated here)."""
    r = next(x for x in json.loads((HERE / TEXT_RECORDS).read_text())["records"] if x["id"] == rid)
    return r["expectedRecordText"].encode("utf-8"), base64.b64decode(r["inputBase64"])
REC3 = {  # TEST-ONLY three-channel records: id -> Go token source (contract §2b)
    "rec-3ch-format-a": f"{NG_}#go-format-a", "rec-3ch-format-b": f"{NG_}#go-format-b",
    "rec-3ch-rename-a": f"{NG_}#go-rename-a", "rec-3ch-rename-b": f"{NG_}#go-rename-b",
    "rec-3ch-classes-a": "extraction-go-classes.json#mv-go-classes-a",
    "rec-3ch-classes-b": "extraction-go-classes.json#mv-go-classes-b",
    "rec-3ch-insufficient": f"{NG_}#go-short", "rec-3ch-lexical-error": f"{NG_}#go-err-unterminated-string",
}


def rederive(result, cfg):
    """Result of the same Go token stream under another channel list (TEST-ONLY three-channel profile)."""
    if result["status"] == "error":
        return result
    toks = result["tokens"]
    return {"status": "ok" if len(toks) >= cfg["k"] else "insufficient-tokens", "tokenCount": len(toks),
            "tokens": toks, "channels": channels_for(toks, cfg, "go")}


NEW_RUST = [
    ("mv-rust-sum", ["function"], "Original Rust function.", RUST_SUM),
    ("mv-rust-host", ["large-host"], "Rust host file containing RUST_SUM verbatim after unrelated items.", RUST_HOST),
]

# ------------------------------------------------------------------ catalogue (contract §3)


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_extraction(path: Path):
    d = json.loads(path.read_text())
    raw = (path.parent / d["configFile"]).read_bytes()
    return d, raw, json.loads(raw)


def catalogue_entry(aid, rec):
    data = base64.b64decode(rec["inputBase64"])
    res = rec["result"]
    e = {"byteLength": len(data), "id": aid, "sha256": sha(data), "status": res["status"]}
    if res["status"] == "error" and res["error"]["code"] == "input-too-large":
        e["byteLength"], e["sha256"] = None, None      # extraction Q10: input not read past the limit
    if res["status"] == "error":
        e["error"] = {"code": res["error"]["code"], "offset": res["error"]["offset"]}
        return e
    e["tokenCount"] = res["tokenCount"]
    e["channels"] = {ch: {"fingerprints": [{"hash": f["hash"], "position": f["position"], "span": list(f["span"])}
                                           for f in res["channels"][ch]["fingerprints"]],
                          "kgramCount": len(res["channels"][ch]["kgrams"]),
                          "partialWindow": res["channels"][ch]["partialWindow"]} for ch in res["channels"]}
    return e


def build_catalogue(cfg_raw, cfg, entries):
    return {"artifacts": sorted(entries, key=lambda e: e["id"]),
            "catalogueVersion": CATALOGUE_VERSION,
            "extractionConfig": dict(cfg),
            "profile": {"configSha256": sha(cfg_raw), "id": cfg["profile"], "version": cfg["profileVersion"]}}


def extraction_config_bytes(cfg):
    order = ["contract", "profile", "profileVersion", "channels", "k", "window", "hash", "maxInputBytes"]
    return (json.dumps({k: cfg[k] for k in order}, separators=(",", ":")) + "\n").encode()


def synthetic_catalogue(cfg_raw, cfg, aid, m, fps):
    """A winnowing-shaped catalogue with no source bytes (contract §11, synthetic vectors).
    fps: list of (position, hash) or (position, hash, span). Default spans are [2p, 2p+10).
    Both channels carry the same data."""
    k = cfg["k"]
    spans = [f[2] if len(f) > 2 else [2 * f[0], 2 * f[0] + 10] for f in fps]
    blen = max([2 * (m - 1) + 10] + [sp[1] for sp in spans])
    chan = {"fingerprints": [{"hash": f[1], "position": f[0], "span": list(sp)} for f, sp in zip(fps, spans)],
            "kgramCount": m, "partialWindow": 1 <= m < cfg["window"]}
    art = {"byteLength": blen, "channels": {"exact": copy.deepcopy(chan), "normalized": copy.deepcopy(chan)},
           "id": aid, "sha256": sha(f"traceweave synthetic artifact {aid}".encode()), "status": "ok",
           "tokenCount": m + k - 1}
    return build_catalogue(cfg_raw, cfg, [art])


# ------------------------------------------------------------------ comparison (contract §4–§5)

def comparison_config_bytes(min_hashes=2, gap=4, max_seeds=100000, max_regions=1000, supp="none",
                            modes=("exact", "normalized")):
    return ('{"comparison":"%s","modes":[%s],"minRegionDistinctHashes":%d,"mergeGap":%d,'
            '"maxSeedsPerMode":%d,"maxRegionsPerMode":%d,"suppressionCatalogueSha256":"%s"}\n'
            % (COMPARISON_ID, ",".join('"%s"' % m for m in modes), min_hashes, gap, max_seeds, max_regions, supp)).encode()


COMPARISON_CONFIG = comparison_config_bytes()
CC_KEYS = ["comparison", "modes", "minRegionDistinctHashes", "mergeGap", "maxSeedsPerMode", "maxRegionsPerMode",
           "suppressionCatalogueSha256"]


def parse_comparison_config(raw: bytes):
    try:
        text = raw.decode("utf-8")
        assert text.endswith("\n") and "\n" not in text[:-1] and "\r" not in text

        def pairs(items):
            keys = [k for k, _ in items]
            assert len(keys) == len(set(keys))
            return dict(items)
        obj = strict_document(raw)
        assert type(obj) is dict and list(obj) == CC_KEYS
        assert obj["comparison"] == COMPARISON_ID and obj["modes"] in list(CHANNEL_LISTS.values())
        assert TEST_CONTEXT[0] or obj["modes"] != CH3
        for key in ("minRegionDistinctHashes", "mergeGap", "maxSeedsPerMode", "maxRegionsPerMode"):
            assert type(obj[key]) is int and 1 <= obj[key] <= 2**32 - 1
        assert obj["maxSeedsPerMode"] <= 10**7 and obj["maxRegionsPerMode"] <= 10**5      # §4 step 5 bounds
        s = obj["suppressionCatalogueSha256"]
        assert type(s) is str and (s == "none" or re.fullmatch(r"[0-9a-f]{64}", s))
        assert comparison_config_bytes(obj["minRegionDistinctHashes"], obj["mergeGap"], obj["maxSeedsPerMode"],
                                       obj["maxRegionsPerMode"], s, obj["modes"]) == raw
        return obj
    except (AssertionError, ValueError, UnicodeDecodeError, KeyError, TypeError):
        return None


MAX_DEPTH = 64          # contract §3.6 step 1 (K4)
ZERO_WIDTH_PROFILES = {"py-tokens"}   # §3.6 step 5: profiles that declare zero-width tokens (A14)
EXTRACTION_BOUNDS = {"k": 16, "window": 128, "maxInputBytes": 8388608}   # extraction §10 step 5 / §10a (K1)
FAMILY = {"text-plain": "traceweave-text-winnow-draft-1"}                 # others: traceweave-token-winnow-draft-1


def strict_document(raw: bytes):
    """Contract §3.6 step 1 (K3, K4): UTF-8, container depth <= 64 (scanned before parsing), strict JSON without
    duplicate keys, non-integer numbers or constants, and every string a sequence of Unicode scalar values."""
    text = raw.decode("utf-8")
    depth = deepest = 0
    in_str = esc = False
    for ch in text:
        if in_str:
            esc, in_str = (False, True) if esc else (ch == "\\", ch != '"')
        elif ch == '"':
            in_str = True
        elif ch in "[{":
            depth += 1
            deepest = max(deepest, depth)
        elif ch in "]}":
            depth -= 1
    if deepest > MAX_DEPTH:
        raise ValueError("nesting deeper than 64")

    def pairs(items):
        keys = [k for k, _ in items]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate key")
        return dict(items)

    def refuse(x):
        raise ValueError("non-integer number or constant")
    obj = json.loads(text, object_pairs_hook=pairs, parse_float=refuse, parse_constant=refuse)

    def strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, list):
            for e in x:
                yield from strings(e)
        elif isinstance(x, dict):
            for k, v in x.items():
                yield k
                yield from strings(v)
    if any(0xD800 <= ord(c) <= 0xDFFF for st in strings(obj) for c in st):
        raise ValueError("lone surrogate")
    return obj


def catalogue_status(raw: bytes):
    """Simplified mirror of contract §3.6 for the catalogues this script produces or fabricates."""
    try:
        obj = strict_document(raw)
    except (ValueError, UnicodeDecodeError):
        return None, "malformed-catalogue"
    if not isinstance(obj, dict) or not isinstance(obj.get("catalogueVersion"), str):
        return None, "malformed-catalogue"
    if obj["catalogueVersion"] != CATALOGUE_VERSION:
        return None, "unsupported-catalogue"
    if canonical(obj) != raw:
        return None, "malformed-catalogue"
    if (obj["profile"]["id"], obj["profile"]["version"]) not in SUPPORTED_PROFILES:
        return None, "unsupported-profile"
    assert sha(extraction_config_bytes(obj["extractionConfig"])) == obj["profile"]["configSha256"]
    ec = obj["extractionConfig"]
    if any(ec[key] > b for key, b in EXTRACTION_BOUNDS.items()) or \
            ec["contract"] != FAMILY.get(ec["profile"], "traceweave-token-winnow-draft-1"):
        return None, "malformed-catalogue"                                  # K1: step 6
    zero_width = ec["profile"] in ZERO_WIDTH_PROFILES                       # A14: declared profile property
    for a in obj["artifacts"]:
        for c in a.get("channels", {}).values():
            fps = c["fingerprints"]
            for f in fps:
                if f["span"][0] == f["span"][1] and ec["k"] > 1 and not zero_width:
                    return None, "malformed-catalogue"
            for x, y in zip(fps, fps[1:]):
                if (y["span"][0] < x["span"][0]) if zero_width else (y["span"][0] <= x["span"][0]):
                    return None, "malformed-catalogue"
    return obj, None


def mode_result(rf, cf, common, cc):
    by_hash = {}
    for f in cf:
        by_hash.setdefault(f["hash"], []).append(f)
    seeds = sorted((r["position"], c["position"], r, c) for r in rf for c in by_hash.get(r["hash"], []))
    hr, hc = {f["hash"] for f in rf}, {f["hash"] for f in cf}
    shared = hr & hc

    def frac(n, d):
        return {"denominator": d, "numerator": n}
    res = {"containment": {"candidateInReference": frac(len(shared), len(hc)),
                           "referenceInCandidate": frac(len(shared), len(hr))},
           "seedCount": len(seeds), "sharedCommonDistinctHashes": len(shared & common),
           "similarity": {"jaccard": frac(len(shared), len(hr | hc))}}
    counts = {"belowMinimumEvidence": 0, "commonOnly": 0, "reportable": 0}
    if not seeds:
        res.update(outcome={"class": "no-match", "code": "no-shared-fingerprints"}, regions=[], regionCounts=counts,
                   truncatedRegions=0)
        return res
    if len(seeds) > cc["maxSeedsPerMode"]:
        res.update(outcome={"class": "abstain", "code": "seed-limit-exceeded"}, regions=[], regionCounts=counts,
                   truncatedRegions=0)
        return res
    groups = {}
    for s in seeds:
        groups.setdefault(s[1] - s[0], []).append(s)
    runs = []
    for d in sorted(groups):
        run = []
        for s in groups[d]:
            if run and s[0] - run[-1][0] > cc["mergeGap"]:
                runs.append(run); run = []
            run.append(s)
        runs.append(run)
    out = []
    for run in runs:
        hs = {s[2]["hash"] for s in run}
        dc = len(hs & common)
        ev = len(hs) - dc
        status = ("reportable" if ev >= cc["minRegionDistinctHashes"] else "below-minimum-evidence" if ev > 0 else "common-only")
        out.append({"ambiguous": False,
                    "candidateSpan": [min(s[3]["span"][0] for s in run), max(s[3]["span"][1] for s in run)],
                    "distinctCommonHashes": dc, "distinctHashes": len(hs),
                    "referenceSpan": [min(s[2]["span"][0] for s in run), max(s[2]["span"][1] for s in run)],
                    "seeds": [[s[0], s[1]] for s in run], "status": status})
    out.sort(key=lambda r: (r["seeds"][0][0], r["seeds"][0][1]))
    rep = [r for r in out if r["status"] == "reportable"]
    for a in rep:
        for b in rep:
            if a is not b and ({s[0] for s in a["seeds"]} & {s[0] for s in b["seeds"]}
                               or {s[1] for s in a["seeds"]} & {s[1] for s in b["seeds"]}):
                a["ambiguous"] = True
    for r in out:
        counts[{"reportable": "reportable", "below-minimum-evidence": "belowMinimumEvidence",
                "common-only": "commonOnly"}[r["status"]]] += 1
    if any(not r["ambiguous"] for r in rep):
        outcome = {"class": "match", "code": "match"}
    elif rep:
        outcome = {"class": "abstain", "code": "ambiguous"}
    elif counts["belowMinimumEvidence"]:
        outcome = {"class": "no-match", "code": "below-minimum-evidence"}
    else:
        outcome = {"class": "no-match", "code": "common-only"}
    res.update(outcome=outcome, regions=out[:cc["maxRegionsPerMode"]], regionCounts=counts,
               truncatedRegions=max(0, len(out) - cc["maxRegionsPerMode"]))
    return res


def compare(ref_raw, cand_raw, cc_raw, supp_raw=None):
    body = {"inputs": {"candidateCatalogueSha256": sha(cand_raw), "comparisonConfigSha256": sha(cc_raw),
                       "referenceCatalogueSha256": sha(ref_raw),
                       "suppressionCatalogueSha256": "none" if supp_raw is None else sha(supp_raw)},
            "reportVersion": REPORT_VERSION, "resultKind": "token-fingerprint-comparison"}

    def reject(cls, code, side):
        body.update({"rejection": {"class": cls, "code": code, "side": side}, "status": "rejected"})
        return body
    cc = parse_comparison_config(cc_raw)
    if cc is None:
        return reject("unsupported-input", "unsupported-comparison-config", "comparison-config")
    if cc["suppressionCatalogueSha256"] != body["inputs"]["suppressionCatalogueSha256"]:
        return reject("mismatch", "suppression-catalogue-mismatch", "suppression")
    cats = {}
    for side, raw in (("reference", ref_raw), ("candidate", cand_raw), ("suppression", supp_raw)):
        if raw is None:
            continue
        cats[side], err = catalogue_status(raw)
        if err:
            return reject("unsupported-input", err, side)
    R = cats["reference"]
    others = [s for s in ("candidate", "suppression") if s in cats]
    for side in others:
        if (cats[side]["profile"]["id"], cats[side]["profile"]["version"]) != (R["profile"]["id"], R["profile"]["version"]):
            return reject("mismatch", "profile-mismatch", side)
    for side in others:
        if cats[side]["profile"]["configSha256"] != R["profile"]["configSha256"]:
            return reject("mismatch", "config-mismatch", side)
    modes = cc["modes"]
    if modes != R["extractionConfig"]["channels"]:
        return reject("mismatch", "mode-mismatch", "comparison-config")
    C = cats["candidate"]
    common = {ch: set() for ch in modes}
    if "suppression" in cats:
        for a in cats["suppression"]["artifacts"]:
            if a["status"] == "ok":
                for ch in modes:
                    common[ch] |= {f["hash"] for f in a["channels"][ch]["fingerprints"]}
        suppression = {"artifactCount": len(cats["suppression"]["artifacts"]),
                       "distinctHashes": {ch: len(common[ch]) for ch in modes}, "status": "supplied"}
    else:
        suppression = {"status": "none"}
    pairs = []
    for ra in R["artifacts"]:
        for ca in C["artifacts"]:
            p = {"candidate": {"id": ca["id"], "sha256": ca["sha256"]},
                 "reference": {"id": ra["id"], "sha256": ra["sha256"]}}
            if ra["status"] == "error":
                p.update({"outcome": {"class": "unsupported-input", "code": "reference-extraction-error"}, "status": "not-compared"})
            elif ca["status"] == "error":
                p.update({"outcome": {"class": "unsupported-input", "code": "candidate-extraction-error"}, "status": "not-compared"})
            elif "insufficient-tokens" in (ra["status"], ca["status"]):
                p.update({"outcome": {"class": "abstain", "code": "insufficient-tokens"}, "status": "not-compared"})
            else:
                p.update({"modes": {ch: mode_result(ra["channels"][ch]["fingerprints"], ca["channels"][ch]["fingerprints"],
                                                    common[ch], cc) for ch in modes}, "status": "compared"})
            pairs.append(p)
    body.update({"candidateArtifactCount": len(C["artifacts"]),
                 "comparison": {k: cc[k] for k in CC_KEYS} | {"parameterStatus": "experimental"},
                 "pairs": pairs, "profile": dict(R["profile"]), "referenceArtifactCount": len(R["artifacts"]),
                 "status": "compared", "suppression": suppression})
    return body


# ------------------------------------------------------------------ hand expectations

def occurrences(text: str, excerpt: str):
    data, ex = text.encode(), excerpt.encode()
    out, i = [], data.find(ex)
    while i >= 0:
        out.append((i, i + len(ex)))
        i = data.find(ex, i + 1)
    return out


def check_hand(vid, hand, body, texts):
    def fail(msg):
        raise SystemExit(f"HAND EXPECTATION FAILED {vid}: {msg}")
    if body["status"] != hand["status"]:
        fail(f"status {body['status']} {body.get('rejection')}")
    if hand["status"] == "rejected":
        if (body["rejection"]["code"], body["rejection"]["side"]) != (hand["rejectionCode"], hand["rejectionSide"]):
            fail(f"rejection {body['rejection']}")
        return
    if "suppressionArtifactCount" in hand and body["suppression"].get("artifactCount") != hand["suppressionArtifactCount"]:
        fail(f"suppression block {body['suppression']}")
    got = {(p["reference"]["id"], p["candidate"]["id"]): p for p in body["pairs"]}
    if [(h["reference"], h["candidate"]) for h in hand["pairs"]] != list(got):
        fail(f"pair list/order {list(got)}")
    for h in hand["pairs"]:
        p = got[(h["reference"], h["candidate"])]
        if p["status"] != h["status"]:
            fail(f"pair status {p['status']}")
        if p["status"] == "not-compared":
            if p["outcome"]["code"] != h["outcomeCode"]:
                fail(f"pair outcome {p['outcome']}")
            continue
        for ch, e in h["modes"].items():
            m = p["modes"][ch]
            allr = m["regions"]
            rep = [r for r in allr if r["status"] == "reportable"]
            tag = f"{h['reference']}/{h['candidate']} {ch}"
            if m["outcome"]["code"] not in e["codeIn"]:
                fail(f"{tag}: code {m['outcome']['code']} not in {e['codeIn']} regions={[r['seeds'] for r in allr]}")
            if "reportable" in e and m["regionCounts"]["reportable"] != e["reportable"]:
                fail(f"{tag}: {m['regionCounts']['reportable']} reportable regions")
            if "regions" in e and sum(m["regionCounts"].values()) != e["regions"]:
                fail(f"{tag}: {sum(m['regionCounts'].values())} regions")
            if "listed" in e and len(allr) != e["listed"]:
                fail(f"{tag}: {len(allr)} listed")
            if "seedCount" in e and m["seedCount"] != e["seedCount"]:
                fail(f"{tag}: seedCount {m['seedCount']}")
            if "seeds" in e and [r["seeds"] for r in allr] != e["seeds"]:
                fail(f"{tag}: seeds {[r['seeds'] for r in allr]}")
            if "ambiguous" in e and [r["ambiguous"] for r in allr] != e["ambiguous"]:
                fail(f"{tag}: ambiguous flags {[r['ambiguous'] for r in allr]}")
            if e.get("exhaustiveDiagonalZero"):
                if len(allr) != 1 or any(a != b for a, b in allr[0]["seeds"]):
                    fail(f"{tag}: not one diagonal-0 region")
            if "regionSpans" in e and [[r["referenceSpan"], r["candidateSpan"]] for r in allr] != e["regionSpans"]:
                fail(f"{tag}: region spans {[[r['referenceSpan'], r['candidateSpan']] for r in allr]}")
            if "candidateShift" in e:
                for r in allr:
                    if [x + e["candidateShift"] for x in r["referenceSpan"]] != r["candidateSpan"]:
                        fail(f"{tag}: candidate span is not reference span + {e['candidateShift']}")
            for side, key in (("reference", "referenceSpan"), ("candidate", "candidateSpan")):
                if "within" in e:
                    exs = e["within"][side]
                    occ = [o for x in (exs if isinstance(exs, list) else [exs]) for o in occurrences(texts[side][h[side]], x)]
                    if not occ:
                        fail(f"{tag}: excerpt not found in {side}")
                    for r in rep:
                        s, t = r[key]
                        if not any(lo <= s and t <= hi for lo, hi in occ):
                            fail(f"{tag}: {key} {r[key]} outside excerpt")


ALL = ["match", "ambiguous", "no-shared-fingerprints", "below-minimum-evidence", "common-only", "seed-limit-exceeded"]
NOMATCH = ["no-shared-fingerprints", "below-minimum-evidence", "common-only"]
HAND, POST = "hand", "computed-then-reviewed"


def ex(d=HAND, **kw):
    kw["derivation"] = d
    return kw


def exhaust(d=HAND):
    return ex(d, codeIn=["match"], reportable=1, exhaustiveDiagonalZero=True)


def both(e):
    return {"exact": copy.deepcopy(e), "normalized": copy.deepcopy(e)}


# ------------------------------------------------------------------ main

def main():
    go_cfg_raw = (EXV / "config-go.json").read_bytes()
    rust_cfg_raw = (EXV / "config-rust.json").read_bytes()
    go_cfg, rust_cfg = json.loads(go_cfg_raw), json.loads(rust_cfg_raw)

    def ext_file(name, cfgfile, cfg_raw, cfg, lang, items):
        d = {"contract": cfg["contract"], "profile": cfg["profile"], "profileVersion": cfg["profileVersion"],
             "configFile": f"../extraction/{cfgfile}", "configSha256": sha(cfg_raw),
             "k": cfg["k"], "window": cfg["window"], "requiredCoverage": False,
             "derivationRule": ROADMAP_DEFINITION + " " + EXTRACTION_RULE_APPLICATION,
             "lexingCheck": "New synthetic inputs for the matching vectors. Token streams are hand-written literals "
                            "(HAND_TOKENS in build_vectors.py); its mini-lexer lex() is only a cross-check that must "
                            "agree. Re-verified by ../extraction/check_vectors.py; see README.md.",
             "vectors": [extraction_record(i, t, ds, tx, cfg, lang) for i, t, ds, tx in items]}
        (HERE / name).write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")

    ext_file("extraction-go.json", "config-go.json", go_cfg_raw, go_cfg, "go", NEW_GO)
    ext_file("extraction-rust.json", "config-rust.json", rust_cfg_raw, rust_cfg, "rust", NEW_RUST)
    ext_file("extraction-go-classes.json", "config-go.json", go_cfg_raw, go_cfg, "go", NEW_GO_CLASSES)
    ext_file("extraction-go-gates.json", "config-go.json", go_cfg_raw, go_cfg, "go", NEW_GO_GATES)
    (HERE / "config-three-channel-test.json").write_bytes(CONFIG_3CH)
    cfg3 = json.loads(CONFIG_3CH)

    sources = {}
    for f in ["extraction-go.json", "extraction-rust.json", "../extraction/go.json",
              "../extraction/rust.json", "../extraction/limits-go.json",
              "../extraction/exclusion-rule.json", "extraction-go-classes.json", "extraction-go-gates.json",
              "extraction-py.json"]:
        d, raw, cfg = load_extraction(HERE / f)
        for v in d["vectors"]:
            sources[f"{f}#{v['id']}"] = (v, raw, cfg)

    (HERE / "comparison-config.json").write_bytes(COMPARISON_CONFIG)
    C = COMPARISON_CONFIG
    negatives = [
        ("no-final-lf", C[:-1], "missing final LF"),
        ("crlf", C[:-1] + b"\r\n", "CR before the final LF"),
        ("spaces", C.replace(b",", b", "), "insignificant whitespace"),
        ("key-order", C.replace(b'"mergeGap":4,"maxSeedsPerMode":100000', b'"maxSeedsPerMode":100000,"mergeGap":4'), "keys out of order"),
        ("duplicate-key", C.replace(b'"mergeGap":4', b'"mergeGap":4,"mergeGap":4'), "duplicate key"),
        ("unknown-id", C.replace(COMPARISON_ID.encode(), b"traceweave-seed-merge-draft-9"), "unknown comparison identifier"),
        ("draft-1-id", C.replace(COMPARISON_ID.encode(), b"traceweave-seed-merge-draft-1"), "previous draft identifier"),
        ("modes-subset", C.replace(b'["exact","normalized"]', b'["exact"]'), "modes subset"),
        ("modes-order", C.replace(b'["exact","normalized"]', b'["normalized","exact"]'), "modes order"),
        ("min-zero", C.replace(b'"minRegionDistinctHashes":2', b'"minRegionDistinctHashes":0'), "minRegionDistinctHashes below 1"),
        ("gap-zero", C.replace(b'"mergeGap":4', b'"mergeGap":0'), "mergeGap below 1"),
        ("seeds-zero", C.replace(b'"maxSeedsPerMode":100000', b'"maxSeedsPerMode":0'), "maxSeedsPerMode below 1"),
        ("regions-zero", C.replace(b'"maxRegionsPerMode":1000', b'"maxRegionsPerMode":0'), "maxRegionsPerMode below 1"),
        ("float", C.replace(b'"mergeGap":4', b'"mergeGap":4.0'), "non-integer number"),
        ("leading-zero", C.replace(b'"mergeGap":4', b'"mergeGap":04'), "leading zero"),
        ("too-large", C.replace(b'"mergeGap":4', b'"mergeGap":4294967296'), "above 2^32-1"),
        ("extra-key", C.replace(b'}\n', b',"x":1}\n'), "unknown key"),
        ("not-object", b'["exact"]\n', "top level not an object"),
        ("suppression-uppercase", C.replace(b'"none"', b'"' + b"A" * 64 + b'"'), "suppression digest not lowercase hex"),
        ("suppression-short", C.replace(b'"none"', b'"abc"'), "suppression digest wrong length"),
        ("suppression-null", C.replace(b'"none"', b'null'), "suppression digest not a string"),
        ("old-key", C.replace(b'minRegionDistinctHashes', b'minRegionFingerprints'), "draft-1 key name"),
    ]
    for _, raw, _ in negatives:
        assert parse_comparison_config(raw) is None, raw
    TEST_CONTEXT[0] = False
    chneg = [
        ("modes-three-reordered", comparison_config_bytes(modes=["exact", "classes", "normalized"]), "not a declared channel list (order)"),
        ("modes-duplicate", comparison_config_bytes(modes=["exact", "exact"]), "duplicate mode"),
        ("modes-unknown-channel", comparison_config_bytes(modes=["exact", "folded"]), "no implemented profile declares this list"),
        ("modes-test-list-outside-tests", comparison_config_bytes(modes=CH3),
         "the TEST-ONLY three-channel list; accepted only for vectors flagged testOnlyProfile"),
        ("modes-empty", comparison_config_bytes(modes=[]), "empty modes"),
    ]
    assert all(parse_comparison_config(b) is None for _, b, _ in chneg)
    TEST_CONTEXT[0] = True
    bounds = {"description": "Comparison-configuration bounds (contract §4 step 5): maxSeedsPerMode <= 10^7, "
                             "maxRegionsPerMode <= 10^5. Negatives MUST be rejected; positives MUST be accepted.",
              "negatives": [{"id": i, "bytesBase64": base64.b64encode(b).decode()} for i, b in (
                  ("seeds-bound-plus-1", comparison_config_bytes(max_seeds=10**7 + 1)),
                  ("seeds-u32-max", comparison_config_bytes(max_seeds=2**32 - 1)),
                  ("regions-bound-plus-1", comparison_config_bytes(max_regions=10**5 + 1)),
                  ("regions-u32-max", comparison_config_bytes(max_regions=2**32 - 1)))],
              "positives": [{"id": i, "bytesBase64": base64.b64encode(b).decode()} for i, b in (
                  ("seeds-at-bound", comparison_config_bytes(max_seeds=10**7)),
                  ("seeds-bound-minus-1", comparison_config_bytes(max_seeds=10**7 - 1)),
                  ("regions-at-bound", comparison_config_bytes(max_regions=10**5)),
                  ("both-at-bound", comparison_config_bytes(max_seeds=10**7, max_regions=10**5)))]}
    assert all(parse_comparison_config(base64.b64decode(n["bytesBase64"])) is None for n in bounds["negatives"])
    assert all(parse_comparison_config(base64.b64decode(n["bytesBase64"])) is not None for n in bounds["positives"])
    (HERE / "comparison-config-bounds.json").write_text(json.dumps(bounds, indent=1) + "\n")
    (HERE / "comparison-config-negative-channels.json").write_text(json.dumps(
        [{"id": i, "reason": r, "bytesBase64": base64.b64encode(b).decode()} for i, b, r in chneg], indent=1) + "\n")
    (HERE / "comparison-config-negative.json").write_text(json.dumps(
        [{"id": i, "reason": r, "bytesBase64": base64.b64encode(b).decode()} for i, b, r in negatives], indent=1) + "\n")

    GO, RU, NG = "extraction-go.json", "extraction-rust.json", "../extraction/go.json"
    RX, LG = "../extraction/rust.json", "../extraction/limits-go.json"
    V = []

    def vec(vid, tags, desc, ref, cand, hand, cc=None, supp=None, overrides=None):
        V.append(dict(id=vid, tags=tags, description=desc, ref=ref, cand=cand, supp=supp, hand=hand, cc=cc,
                      overrides=overrides or {}))

    def pair(r, c, modes=None, status="compared", code=None):
        p = {"reference": r, "candidate": c, "status": status}
        if modes is not None:
            p["modes"] = modes
        if code:
            p["outcomeCode"] = code
        return p

    def rej(code, side):
        return {"status": "rejected", "rejectionCode": code, "rejectionSide": side}

    SUM = [("sum.go", f"{GO}#mv-go-sum")]
    COPY = [("copy.go", f"{GO}#mv-go-sum")]

    # --- vectors carried over from draft-1 (expectations unchanged unless noted) -------------------
    vec("go-identical", ["identical"], "Identical bytes under two artifact ids: one diagonal-0 region holding every fingerprint, both modes.",
        SUM, COPY, {"status": "compared", "pairs": [pair("sum.go", "copy.go", both(exhaust()))]})
    vec("go-function-in-host", ["function-in-host", "large-host"],
        "GO_SUM copied verbatim into a larger host file. Reference-in-candidate containment is complete while Jaccard similarity is lower (M2.5).",
        SUM, [("host.go", f"{GO}#mv-go-host")],
        {"status": "compared", "pairs": [pair("sum.go", "host.go", both(
            ex(codeIn=["match"], reportable=1, within={"reference": GO_SUM, "candidate": GO_SUM})))]})
    vec("go-partial-copy", ["partial-copy"],
        "Only the loop of GO_SUM (and the start of its return statement) is copied into a different function.",
        SUM, [("partial.go", f"{GO}#mv-go-partial")],
        {"status": "compared", "pairs": [pair("sum.go", "partial.go", both(
            ex(codeIn=["match"], reportable=1, within={"reference": GO_LOOP_EXCERPT, "candidate": GO_LOOP_EXCERPT})))]})
    vec("go-comments-whitespace", ["trivia-pair"],
        "Extraction pair go-format-a/b: same tokens, different comments and layout. Equal positions and hashes; spans differ.",
        [("a.go", f"{NG}#go-format-a")], [("b.go", f"{NG}#go-format-b")],
        {"status": "compared", "pairs": [pair("a.go", "b.go", both(exhaust()))]})
    vec("go-renamed", ["rename-pair"],
        "Extraction pair go-rename-a/b: identifiers renamed. Normalized mode matches completely; exact mode does not match.",
        [("a.go", f"{NG}#go-rename-a")], [("b.go", f"{NG}#go-rename-b")],
        {"status": "compared", "pairs": [pair("a.go", "b.go", {"exact": ex(codeIn=NOMATCH, reportable=0),
                                                              "normalized": exhaust()})]})
    vec("go-no-overlap", ["no-overlap"], "Unrelated files share no fingerprint in either mode.",
        SUM, [("pair.go", f"{GO}#mv-go-pair")],
        {"status": "compared", "pairs": [pair("sum.go", "pair.go", both(ex(codeIn=["no-shared-fingerprints"], regions=0)))]})
    vec("go-insufficient-tokens", ["insufficient-tokens"], "Candidate has fewer than k tokens: the pair abstains.",
        SUM, [("short.go", f"{NG}#go-short")],
        {"status": "compared", "pairs": [pair("sum.go", "short.go", status="not-compared", code="insufficient-tokens")]})
    vec("go-malformed-candidate", ["malformed-candidate"],
        "Candidate failed extraction (unterminated string); the catalogue records the error and the pair is not compared.",
        SUM, [("bad.go", f"{NG}#go-err-unterminated-string")],
        {"status": "compared", "pairs": [pair("sum.go", "bad.go", status="not-compared", code="candidate-extraction-error")]})
    vec("go-duplicate-regions", ["duplicate-regions", "precedence"],
        "Candidate holds the body of GO_SUM twice: two reportable regions share every reference position, so both are ambiguous and the mode abstains.",
        SUM, [("twice.go", f"{GO}#mv-go-twice")],
        {"status": "compared", "pairs": [pair("sum.go", "twice.go", {
            "exact": ex(codeIn=["ambiguous"], reportable=2, within={"reference": GO_SUM_BODY, "candidate": GO_SUM_BODY}),
            "normalized": ex(POST, codeIn=["ambiguous"], reportable=2,
                             within={"reference": GO_SUM, "candidate": ["func sumA" + GO_SUM_BODY, "func sumB" + GO_SUM_BODY]})})]})
    vec("go-tie-equal-candidate-span", ["tie", "precedence"],
        "Mirror of go-duplicate-regions: the reference holds the body twice. The two regions have equal candidate spans and are ordered by reference position.",
        [("twice.go", f"{GO}#mv-go-twice")], SUM,
        {"status": "compared", "pairs": [pair("twice.go", "sum.go", {
            "exact": ex(codeIn=["ambiguous"], reportable=2, within={"reference": GO_SUM_BODY, "candidate": GO_SUM_BODY}),
            "normalized": ex(POST, codeIn=["ambiguous"], reportable=2,
                             within={"reference": ["func sumA" + GO_SUM_BODY, "func sumB" + GO_SUM_BODY], "candidate": GO_SUM})})]})
    vec("go-repeated-hash-self", ["tie", "repeated-hash", "distinct-evidence"],
        "go-equal-minimum against itself. Exact fingerprints at positions 2 and 5 share one hash: four seeds form a diagonal-0 region "
        "and two off-diagonal regions, each with ONE distinct hash, so all are below the minimum evidence (draft-2 counts distinct hashes). "
        "Normalized: fingerprints at 1, 4, 7 share one hash; nine seeds, five regions, all with one distinct hash.",
        [("x.go", f"{NG}#go-equal-minimum")], [("y.go", f"{NG}#go-equal-minimum")],
        {"status": "compared", "pairs": [pair("x.go", "y.go", {
            "exact": ex(codeIn=["below-minimum-evidence"], reportable=0, regions=3, seedCount=4,
                        seeds=[[[2, 2], [5, 5]], [[2, 5]], [[5, 2]]]),
            "normalized": ex(POST, codeIn=["below-minimum-evidence"], reportable=0, regions=5, seedCount=9,
                             seeds=[[[1, 1], [4, 4], [7, 7]], [[1, 4], [4, 7]], [[1, 7]], [[4, 1], [7, 4]], [[7, 1]]])})]})
    vec("go-config-mismatch", ["config-mismatch"],
        "Same profile, different configuration bytes (maxInputBytes 16): the report is rejected before any comparison.",
        SUM, [("tiny.go", f"{LG}#go-limit-exact")], rej("config-mismatch", "candidate"))
    vec("profile-mismatch", ["profile-mismatch"], "Go reference against a Rust candidate.",
        SUM, [("sum.rs", f"{RU}#mv-rust-sum")], rej("profile-mismatch", "candidate"))
    vec("go-unsupported-comparison-config", ["unsupported-comparison-config"],
        "Comparison configuration with minRegionDistinctHashes 0 is rejected before the catalogues are read.",
        SUM, COPY, rej("unsupported-comparison-config", "comparison-config"),
        cc=COMPARISON_CONFIG.replace(b'"minRegionDistinctHashes":2', b'"minRegionDistinctHashes":0'))
    vec("go-malformed-catalogue", ["malformed-catalogue"],
        "Candidate catalogue with the right content but pretty-printed (not canonical bytes).",
        SUM, COPY, rej("malformed-catalogue", "candidate"), overrides={"candidate": "pretty"})
    vec("go-unsupported-catalogue", ["unsupported-catalogue"],
        "Reference catalogue declares catalogueVersion traceweave-catalogue-draft-9.",
        SUM, COPY, rej("unsupported-catalogue", "reference"), overrides={"reference": "version"})
    vec("go-unsupported-profile", ["unsupported-profile"],
        "Reference catalogue declares profileVersion draft-2 with a consistent configuration digest; draft-2 is not implemented.",
        SUM, COPY, rej("unsupported-profile", "reference"), overrides={"reference": "profile"})
    vec("rust-comments-whitespace", ["trivia-pair", "rust"],
        "Extraction pair rust-format-a/b (CRLF, nested comment).",
        [("a.rs", f"{RX}#rust-format-a")], [("b.rs", f"{RX}#rust-format-b")],
        {"status": "compared", "pairs": [pair("a.rs", "b.rs", both(exhaust()))]})
    vec("rust-renamed", ["rename-pair", "rust"],
        "Extraction pair rust-rename-a/b. Normalized matches completely; exact keeps one shared return-type fingerprint.",
        [("a.rs", f"{RX}#rust-rename-a")], [("b.rs", f"{RX}#rust-rename-b")],
        {"status": "compared", "pairs": [pair("a.rs", "b.rs", {"exact": ex(codeIn=NOMATCH, reportable=0),
                                                              "normalized": exhaust()})]})
    vec("rust-function-in-host", ["function-in-host", "large-host", "rust"],
        "RUST_SUM copied verbatim after unrelated items.",
        [("sum.rs", f"{RU}#mv-rust-sum")], [("host.rs", f"{RU}#mv-rust-host")],
        {"status": "compared", "pairs": [pair("sum.rs", "host.rs", both(
            ex(codeIn=["match"], reportable=1, within={"reference": RUST_SUM, "candidate": RUST_SUM})))]})
    vec("rust-identical", ["identical", "rust"], "rust-lifetimes-chars against itself.",
        [("l.rs", f"{RX}#rust-lifetimes-chars")], [("m.rs", f"{RX}#rust-lifetimes-chars")],
        {"status": "compared", "pairs": [pair("l.rs", "m.rs", both(exhaust()))]})

    # --- common-code suppression (OD-C5 (b), decided in draft) -------------------------------------
    B1 = [("b1.go", f"{GO}#mv-go-b1")]
    CANDS = [("put.go", f"{GO}#mv-go-put"), ("pair.go", f"{GO}#mv-go-pair")]
    BOILER = [("b2.go", f"{GO}#mv-go-b2"), ("b3.go", f"{GO}#mv-go-b3")]
    vec("go-boilerplate-suppressed", ["boilerplate", "suppression", "multi-artifact"],
        "Reference b1.go and candidate put.go share only the err-check idiom and call shapes that also occur in the "
        "boilerplate catalogue (b2.go, b3.go), bound by digest in the comparison configuration. No pair matches.",
        B1, CANDS, {"status": "compared", "pairs": [pair("b1.go", c, both(ex(codeIn=NOMATCH, reportable=0)))
                                                    for c in ("pair.go", "put.go")]},
        supp=BOILER, cc="suppress")
    vec("go-boilerplate-unsuppressed", ["boilerplate", "demonstrative"],
        "Demonstrative: the same reference and candidates with no suppression catalogue. The err-check idiom and call shape "
        "alone give a normalized match. The expectation for put.go was fixed after the draft-1 computation (computed-then-reviewed).",
        B1, CANDS, {"status": "compared", "pairs": [
            pair("b1.go", "pair.go", both(ex(codeIn=["no-shared-fingerprints"], regions=0))),
            pair("b1.go", "put.go", {"exact": ex(POST, codeIn=["below-minimum-evidence"], reportable=0),
                                     "normalized": ex(POST, codeIn=["match"], reportable=2)})]})
    vec("go-suppression-digest-mismatch", ["suppression", "suppression-catalogue-mismatch"],
        "The configuration names the digest of the boilerplate catalogue, but a different catalogue is supplied.",
        B1, CANDS, rej("suppression-catalogue-mismatch", "suppression"), supp=[("b2.go", f"{GO}#mv-go-b2")], cc="suppress-other")
    vec("go-suppression-missing", ["suppression", "suppression-catalogue-mismatch"],
        "The configuration names a suppression catalogue digest, but no suppression catalogue is supplied.",
        B1, CANDS, rej("suppression-catalogue-mismatch", "suppression"), cc="suppress")
    vec("go-suppression-config-mismatch", ["suppression", "config-mismatch"],
        "The suppression catalogue was built under a different extraction configuration (maxInputBytes 16).",
        B1, CANDS, rej("config-mismatch", "suppression"), supp=[("tiny.go", f"{LG}#go-limit-exact")], cc="suppress-supplied")

    # --- new in draft-2: boundaries, non-ASCII, reference-side failures, caps, controls --------------
    A, B, X, Y = "a000000000000001", "b000000000000002", "c000000000000003", "d000000000000004"
    vec("rv-gap-boundary", ["synthetic", "merge-boundary"],
        "Reviewer boundary vector: shared seeds (0,0) and (5,5) on one diagonal, gap 5 = mergeGap + 1, so they are two "
        "single-hash regions (below minimum evidence). Positions 3 differ.",
        ("synthetic", "r.syn", 9, [(0, A), (3, X), (5, B)]), ("synthetic", "c.syn", 9, [(0, A), (3, Y), (5, B)]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["below-minimum-evidence"], reportable=0,
                                                                         seeds=[[[0, 0]], [[5, 5]]])))]})
    vec("rv-gap-equal", ["synthetic", "merge-boundary"],
        "Companion: seeds (0,0) and (4,4), gap 4 = mergeGap, join into one reportable region.",
        ("synthetic", "r.syn", 8, [(0, A), (4, B)]), ("synthetic", "c.syn", 8, [(0, A), (4, B)]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["match"], reportable=1,
                                                                         seeds=[[[0, 0], [4, 4]]])))]})
    H = ["e00000000000000%d" % i for i in range(1, 7)]
    vec("rv-span-overlap-disjoint-positions", ["synthetic", "ambiguity-definition"],
        "Reviewer vector: two reportable regions whose candidate spans overlap ([0,12) and [4,16)) but share no position. "
        "Ambiguity is by shared positions, so neither is ambiguous and the mode is match.",
        ("synthetic", "r.syn", 12, [(0, H[0]), (1, H[1]), (5, H[4]), (9, H[5]), (10, H[2]), (11, H[3])]),
        ("synthetic", "c.syn", 7, [(0, H[0]), (1, H[1]), (2, H[2]), (3, H[3])]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["match"], reportable=2,
                                                                         seeds=[[[0, 0], [1, 1]], [[10, 2], [11, 3]]],
                                                                         ambiguous=[False, False])))]})
    vec("go-non-ascii-shift", ["unicode", "non-ascii"],
        "Multi-byte identifiers and string; the candidate adds a comment line of 28 bytes but 12 code points. Every span "
        "shifts by exactly 28: offsets are UTF-8 bytes, not code points. (The hand count first said 25/11; corrected.)",
        [("g.go", f"{GO}#mv-go-nonascii")], [("h.go", f"{GO}#mv-go-nonascii-prefixed")],
        {"status": "compared", "pairs": [pair("g.go", "h.go", both(ex(POST, codeIn=["match"], reportable=1,
                                                                       exhaustiveDiagonalZero=True, candidateShift=28)))]})
    vec("go-reference-side-failures", ["reference-error", "insufficient-tokens", "malformed-candidate", "pair-precedence",
                                       "multi-artifact"],
        "Reference holds an extraction error, a too-short file and GO_SUM; candidate holds GO_SUM and another error. "
        "Pins pair-level precedence: reference error, then candidate error, then insufficient tokens.",
        [("bad.go", f"{NG}#go-err-unterminated-string"), ("short.go", f"{NG}#go-short"), ("sum.go", f"{GO}#mv-go-sum")],
        [("cbad.go", f"{NG}#go-err-unterminated-comment"), ("copy.go", f"{GO}#mv-go-sum")],
        {"status": "compared", "pairs": [
            pair("bad.go", "cbad.go", status="not-compared", code="reference-extraction-error"),
            pair("bad.go", "copy.go", status="not-compared", code="reference-extraction-error"),
            pair("short.go", "cbad.go", status="not-compared", code="candidate-extraction-error"),
            pair("short.go", "copy.go", status="not-compared", code="insufficient-tokens"),
            pair("sum.go", "cbad.go", status="not-compared", code="candidate-extraction-error"),
            pair("sum.go", "copy.go", both(exhaust()))]})
    vec("go-duplicate-key-catalogue", ["malformed-catalogue", "duplicate-key"],
        "Reference catalogue with catalogueVersion twice, the valid value first and draft-9 last. Duplicate detection precedes "
        "any field read, so this is malformed-catalogue (a last-value-wins parser would wrongly say unsupported-catalogue).",
        SUM, COPY, rej("malformed-catalogue", "reference"), overrides={"reference": "dupkey"})
    vec("go-output-caps", ["output-cap", "seed-limit"],
        "go-equal-minimum against itself with maxSeedsPerMode 4 and maxRegionsPerMode 2. Exact: 4 seeds (at the limit), 3 regions, "
        "2 listed, 1 truncated, outcome from all 3. Normalized: 9 seeds exceed 4, so the mode abstains with seed-limit-exceeded.",
        [("x.go", f"{NG}#go-equal-minimum")], [("y.go", f"{NG}#go-equal-minimum")],
        {"status": "compared", "pairs": [pair("x.go", "y.go", {
            "exact": ex(codeIn=["below-minimum-evidence"], regions=3, listed=2, seedCount=4,
                        seeds=[[[2, 2], [5, 5]], [[2, 5]]]),
            "normalized": ex(codeIn=["seed-limit-exceeded"], regions=0, listed=0, seedCount=9)})]},
        cc=comparison_config_bytes(max_seeds=4, max_regions=2))
    vec("go-periodic-distinct", ["repeated-hash", "distinct-evidence"],
        "Second distinct-hash vector: x++ four times against six times. Exact fingerprints {2,5} and {2,5,8,11} share one hash: "
        "8 seeds on diagonals 0, +3, +6, +9, -3, each region with one distinct hash.",
        [("x.go", f"{NG}#go-equal-minimum")], [("x6.go", f"{GO}#mv-go-periodic6")],
        {"status": "compared", "pairs": [pair("x.go", "x6.go", {
            "exact": ex(codeIn=["below-minimum-evidence"], reportable=0, regions=5, seedCount=8,
                        seeds=[[[2, 2], [5, 5]], [[2, 5], [5, 8]], [[2, 8], [5, 11]], [[2, 11]], [[5, 2]]]),
            "normalized": ex(codeIn=["below-minimum-evidence"], reportable=0, seedCount=15)})]})
    vec("go-independent-same-task", ["independent-same-task", "control"],
        "Control: GO_SUM's task written independently. Exact mode has no reportable region. The normalized outcome is "
        "not constrained by hand: it depends on which k-grams winnowing selects.",
        SUM, [("ind.go", f"{GO}#mv-go-independent")],
        {"status": "compared", "pairs": [pair("sum.go", "ind.go", {"exact": ex(codeIn=NOMATCH, reportable=0),
                                                                  "normalized": ex(codeIn=ALL)})]})
    vec("go-shadowing", ["shadowing", "rename-pair"],
        "Shadowing versus a fresh name: identical normalized token streams, so the normalized mode matches completely and "
        "cannot tell them apart (not scope-aware). Exact is not constrained by hand.",
        [("a.go", f"{GO}#mv-go-shadow-a")], [("b.go", f"{GO}#mv-go-shadow-b")],
        {"status": "compared", "pairs": [pair("a.go", "b.go", {"exact": ex(codeIn=ALL), "normalized": exhaust()})]})

    # --- outcome precedence and suppression arithmetic, two vectors each (synthetic, hand-derived) ------
    Cc, Dd = "f000000000000005", "f100000000000006"
    left = ("synthetic", "r.syn", 8, [(0, A), (1, B), (5, Cc), (6, Dd)])
    right = ("synthetic", "c.syn", 10, [(0, A), (1, B), (4, A), (5, B), (8, Cc), (9, Dd)])
    vec("rv-match-over-ambiguous", ["synthetic", "precedence", "match-over-ambiguous"],
        "Three reportable regions: two share reference positions 0 and 1 (ambiguous), the third shares nothing, so the mode is match.",
        left, ("synthetic", "c.syn", 10, right[3]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["match"], reportable=3,
            seeds=[[[0, 0], [1, 1]], [[0, 4], [1, 5]], [[5, 8], [6, 9]]], ambiguous=[True, True, False])))]})
    vec("rv-match-over-ambiguous-mirror", ["synthetic", "precedence", "match-over-ambiguous"],
        "Mirror: the duplicated hashes are on the reference side, so the ambiguous regions share candidate positions.",
        ("synthetic", "r.syn", 10, right[3]), ("synthetic", "c.syn", 8, left[3]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["match"], reportable=3,
            seeds=[[[0, 0], [1, 1]], [[4, 0], [5, 1]], [[8, 5], [9, 6]]], ambiguous=[True, True, False])))]})
    l2 = [(0, A), (1, B), (5, Cc)]
    r2 = [(0, A), (1, B), (4, A), (5, B), (8, Cc)]
    vec("rv-ambiguous-over-below", ["synthetic", "precedence", "ambiguous-over-weaker"],
        "Two ambiguous reportable regions and one single-hash region: ambiguous ranks above below-minimum-evidence.",
        ("synthetic", "r.syn", 8, l2), ("synthetic", "c.syn", 10, r2),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["ambiguous"], reportable=2,
            seeds=[[[0, 0], [1, 1]], [[0, 4], [1, 5]], [[5, 8]]], ambiguous=[True, True, False])))]})
    vec("rv-ambiguous-over-below-mirror", ["synthetic", "precedence", "ambiguous-over-weaker"],
        "Mirror of rv-ambiguous-over-below.",
        ("synthetic", "r.syn", 10, r2), ("synthetic", "c.syn", 8, l2),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["ambiguous"], reportable=2,
            seeds=[[[0, 0], [1, 1]], [[4, 0], [5, 1]], [[8, 5]]], ambiguous=[True, True, False])))]})
    SUPP_C = ("synthetic", "s.syn", 1, [(0, Cc)])
    vec("rv-below-over-common", ["synthetic", "precedence", "below-over-common", "suppression"],
        "Seeds (0,0) [hash A] and (6,6) [hash C] are 6 apart, so two regions. C is in the suppression catalogue: "
        "regions below-minimum-evidence and common-only; below-minimum-evidence ranks above common-only.",
        ("synthetic", "r.syn", 8, [(0, A), (3, X), (6, Cc)]), ("synthetic", "c.syn", 8, [(0, A), (3, Y), (6, Cc)]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["below-minimum-evidence"], reportable=0,
            seeds=[[[0, 0]], [[6, 6]]])))]}, supp=SUPP_C, cc="suppress-supplied")
    vec("rv-below-over-common-reversed", ["synthetic", "precedence", "below-over-common", "suppression"],
        "The same with the common hash first: the common-only region is listed first, and the outcome is still below-minimum-evidence.",
        ("synthetic", "r.syn", 8, [(0, Cc), (3, X), (6, A)]), ("synthetic", "c.syn", 8, [(0, Cc), (3, Y), (6, A)]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["below-minimum-evidence"], reportable=0,
            seeds=[[[0, 0]], [[6, 6]]])))]}, supp=SUPP_C, cc="suppress-supplied")
    vec("rv-common-reduces-evidence", ["synthetic", "suppression", "mixed-common-region"],
        "One region with two distinct hashes, one of them in the suppression catalogue: evidence 1 < 2, so below-minimum-evidence "
        "(without suppression it would be match).",
        ("synthetic", "r.syn", 5, [(0, A), (1, Cc)]), ("synthetic", "c.syn", 5, [(0, A), (1, Cc)]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["below-minimum-evidence"], reportable=0,
            seeds=[[[0, 0], [1, 1]]])))]}, supp=SUPP_C, cc="suppress-supplied")
    vec("rv-common-reduces-evidence-unsuppressed", ["synthetic", "mixed-common-region"],
        "Control for rv-common-reduces-evidence: the same catalogues with no suppression catalogue give match.",
        ("synthetic", "r.syn", 5, [(0, A), (1, Cc)]), ("synthetic", "c.syn", 5, [(0, A), (1, Cc)]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["match"], reportable=1,
            seeds=[[[0, 0], [1, 1]]])))]})

    vec("rv-common-reduces-evidence-2", ["synthetic", "suppression", "mixed-common-region"],
        "One region with three distinct hashes, two of them in the suppression catalogue: evidence 1, below-minimum-evidence.",
        ("synthetic", "r.syn", 6, [(0, A), (1, Cc), (2, Dd)]), ("synthetic", "c.syn", 6, [(0, A), (1, Cc), (2, Dd)]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["below-minimum-evidence"], reportable=0,
            seeds=[[[0, 0], [1, 1], [2, 2]]])))]}, supp=("synthetic", "s.syn", 5, [(0, Cc), (1, Dd)]), cc="suppress-supplied")
    vec("rv-gap-boundary-offset", ["synthetic", "merge-boundary"],
        "Second gap boundary on diagonal +2: seeds (0,2) and (5,7), gap 5 = mergeGap + 1, two single-hash regions.",
        ("synthetic", "r.syn", 9, [(0, A), (3, X), (5, B)]), ("synthetic", "c.syn", 11, [(2, A), (5, Y), (7, B)]),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["below-minimum-evidence"], reportable=0,
                                                                         seeds=[[[0, 2]], [[5, 7]]])))]})
    vec("go-output-caps-2", ["output-cap", "seed-limit"],
        "x++ four times against six times with maxSeedsPerMode 8 and maxRegionsPerMode 3. Exact: 8 seeds (at the limit), 5 regions, "
        "3 listed, 2 truncated. Normalized: 15 seeds exceed 8, seed-limit-exceeded.",
        [("x.go", f"{NG}#go-equal-minimum")], [("x6.go", f"{GO}#mv-go-periodic6")],
        {"status": "compared", "pairs": [pair("x.go", "x6.go", {
            "exact": ex(codeIn=["below-minimum-evidence"], regions=5, listed=3, seedCount=8,
                        seeds=[[[2, 2], [5, 5]], [[2, 5], [5, 8]], [[2, 8], [5, 11]]]),
            "normalized": ex(codeIn=["seed-limit-exceeded"], regions=0, listed=0, seedCount=15)})]},
        cc=comparison_config_bytes(max_seeds=8, max_regions=3))

    # --- draft-2 confirmation-pass additions (hand-derived before computation) ---------------------
    PARTIAL = [("partial.go", f"{GO}#mv-go-partial")]
    THREE = [("host.go", f"{GO}#mv-go-host"), ("sum.go", f"{GO}#mv-go-sum"), ("twice.go", f"{GO}#mv-go-twice")]
    loop = ex(codeIn=["match"], reportable=1, within={"reference": GO_LOOP_EXCERPT, "candidate": GO_LOOP_EXCERPT})
    loop2 = ex(codeIn=["ambiguous"], reportable=2, within={"reference": GO_LOOP_EXCERPT, "candidate": GO_LOOP_EXCERPT})
    inv_pairs = [pair("host.go", "partial.go", both(loop)), pair("sum.go", "partial.go", both(loop)),
                 pair("twice.go", "partial.go", both(loop2))]
    vec("go-invariance-three-references", ["invariance", "invariance-group-a", "multi-artifact"],
        "Three ok reference files all contain GO_SUM's loop; the candidate copies the loop. With no suppression catalogue no "
        "hash is common, so every pair matches (twice.go: two copies, ambiguous). An implementation that still applies draft-1 "
        "reference document-frequency suppression (threshold 3) would mark the loop's hashes common here.",
        THREE, PARTIAL, {"status": "compared", "pairs": inv_pairs})
    vec("go-invariance-plus-unrelated", ["invariance", "invariance-group-a", "multi-artifact"],
        "The same with an unrelated fourth reference file (pair.go). Every pair present in go-invariance-three-references has "
        "an identical result; the checker compares them.",
        THREE + [("pair.go", f"{GO}#mv-go-pair")], PARTIAL,
        {"status": "compared", "pairs": [inv_pairs[0], pair("pair.go", "partial.go", both(ex(codeIn=NOMATCH, reportable=0))),
                                         inv_pairs[1], inv_pairs[2]]})
    vec("go-cap-straddles-ambiguous", ["output-cap", "ambiguity-before-cap"],
        "go-duplicate-regions with maxRegionsPerMode 1: only the first of the two ambiguous reportable regions is listed. It is "
        "still ambiguous (ambiguity is computed before the cap), truncatedRegions is 1 and the outcome is ambiguous.",
        SUM, [("twice.go", f"{GO}#mv-go-twice")],
        {"status": "compared", "pairs": [pair("sum.go", "twice.go", both(ex(codeIn=["ambiguous"], reportable=2, regions=2,
                                                                             listed=1, ambiguous=[True])))]},
        cc=comparison_config_bytes(max_regions=1))
    vec("go-cap-straddles-ambiguous-mirror", ["output-cap", "ambiguity-before-cap"],
        "Mirror (reference holds the body twice) with maxRegionsPerMode 1.",
        [("twice.go", f"{GO}#mv-go-twice")], SUM,
        {"status": "compared", "pairs": [pair("twice.go", "sum.go", both(ex(codeIn=["ambiguous"], reportable=2, regions=2,
                                                                             listed=1, ambiguous=[True])))]},
        cc=comparison_config_bytes(max_regions=1))
    vec("go-suppression-artifact-count", ["suppression", "suppression-artifact-count"],
        "Suppression catalogue with one ok entry, one insufficient-tokens entry and one error entry: suppression.artifactCount "
        "counts all 3 entries; distinctHashes come from the ok entry only. Outcomes as in go-boilerplate-suppressed would not "
        "be guaranteed (only b2.go suppresses), so outcomes are not constrained here.",
        B1, CANDS, {"status": "compared", "suppressionArtifactCount": 3,
                    "pairs": [pair("b1.go", c, both(ex(codeIn=ALL))) for c in ("pair.go", "put.go")]},
        supp=[("b2.go", f"{GO}#mv-go-b2"), ("bad.go", f"{NG}#go-err-unterminated-string"), ("short.go", f"{NG}#go-short")],
        cc="suppress-supplied")
    vec("go-suppression-unexpected", ["suppression", "suppression-catalogue-mismatch"],
        "Configuration says none but a suppression catalogue is supplied: rejected explicitly, never silently ignored.",
        B1, CANDS, rej("suppression-catalogue-mismatch", "suppression"), supp=BOILER)
    vec("go-suppression-order-binding-before-reference", ["suppression", "suppression-order"],
        "Malformed (pretty-printed) reference catalogue and an unexpected suppression catalogue: the binding check (step 2) "
        "precedes reference validation (step 3).",
        B1, CANDS, rej("suppression-catalogue-mismatch", "suppression"), supp=BOILER, overrides={"reference": "pretty"})
    vec("go-suppression-order-binding-before-validity", ["suppression", "suppression-order"],
        "Pretty-printed suppression catalogue whose bytes do not match the configured digest: binding mismatch, not malformed.",
        B1, CANDS, rej("suppression-catalogue-mismatch", "suppression"), supp=BOILER, cc="suppress",
        overrides={"suppression": "pretty"})
    vec("go-suppression-order-malformed-bound", ["suppression", "suppression-order"],
        "The configuration binds the exact digest of a pretty-printed suppression catalogue: the binding holds, then the "
        "catalogue fails validation (step 5).",
        B1, CANDS, rej("malformed-catalogue", "suppression"), supp=BOILER, cc="suppress-supplied",
        overrides={"suppression": "pretty"})
    vec("go-suppression-order-candidate-validity-first", ["suppression", "suppression-order"],
        "Malformed candidate and malformed (bound) suppression catalogue: the candidate (step 4) is reported first.",
        B1, CANDS, rej("malformed-catalogue", "candidate"), supp=BOILER, cc="suppress-supplied",
        overrides={"candidate": "pretty", "suppression": "pretty"})
    vec("go-suppression-order-candidate-config-first", ["suppression", "suppression-order"],
        "Candidate and suppression catalogue both under the maxInputBytes-16 configuration: config-mismatch is reported for "
        "the candidate first.",
        B1, [("tiny.go", f"{LG}#go-limit-exact")], rej("config-mismatch", "candidate"),
        supp=[("tiny.go", f"{LG}#go-limit-exact")], cc="suppress-supplied")
    vec("go-suppression-order-profile-before-config", ["suppression", "suppression-order"],
        "Candidate has a config mismatch, suppression catalogue a profile mismatch (Rust): all profile checks (step 6) "
        "precede all configuration checks (step 7), so profile-mismatch for the suppression catalogue.",
        B1, [("tiny.go", f"{LG}#go-limit-exact")], rej("profile-mismatch", "suppression"),
        supp=[("sum.rs", f"{RU}#mv-rust-sum")], cc="suppress-supplied")

    vec("go-input-too-large", ["input-too-large", "malformed-candidate"],
        "Catalogues under the maxInputBytes-16 configuration. Two candidate inputs exceed the limit: their catalogue entries "
        "carry null sha256 and byteLength (extraction Q10), the pairs are candidate-extraction-error, and the report "
        "references them with a null sha256. The in-limit copy shares one fingerprint (below minimum evidence).",
        [("tiny.go", f"{LG}#go-limit-exact")],
        [("copy.go", f"{LG}#go-limit-exact"), ("over.go", f"{LG}#go-limit-over"), ("prec.go", f"{LG}#go-limit-precedence")],
        {"status": "compared", "pairs": [
            pair("tiny.go", "copy.go", both(ex(codeIn=["below-minimum-evidence"], reportable=0, regions=1))),
            pair("tiny.go", "over.go", status="not-compared", code="candidate-extraction-error"),
            pair("tiny.go", "prec.go", status="not-compared", code="candidate-extraction-error")]},
        cc=None)

    # --- channel lists (contract §2b; TEST-ONLY three-channel profile; hand-derived before computation) ----
    def r3(*items):
        return ("records3", list(items))
    CC3 = comparison_config_bytes(modes=CH3)
    vec("tc-rename", ["three-channel", "test-only-profile"],
        "go-rename-a/b under the TEST-ONLY three-channel profile: exact does not match; normalized and classes match "
        "completely on diagonal 0.",
        r3(("a.go", "rec-3ch-rename-a")), r3(("b.go", "rec-3ch-rename-b")),
        {"status": "compared", "pairs": [pair("a.go", "b.go", {"exact": ex(codeIn=NOMATCH, reportable=0),
                                                              "normalized": exhaust(), "classes": exhaust()})]}, cc=CC3)
    vec("tc-classes-only", ["three-channel", "test-only-profile"],
        "Same class sequence, different keywords and operators: only the third channel matches. Normalized shares at most "
        "one k-gram (\"\" ( \"\" ) ;).",
        r3(("a.go", "rec-3ch-classes-a")), r3(("b.go", "rec-3ch-classes-b")),
        {"status": "compared", "pairs": [pair("a.go", "b.go", {
            "exact": ex(codeIn=["no-shared-fingerprints"], regions=0),
            "normalized": ex(codeIn=NOMATCH, reportable=0), "classes": exhaust()})]}, cc=CC3)
    vec("tc-format-suppressed", ["three-channel", "test-only-profile", "suppression"],
        "go-format-a/b with a three-channel suppression catalogue holding go-format-a itself: every hash in every mode is "
        "common, so each mode is common-only, and suppression.distinctHashes has one key per mode.",
        r3(("a.go", "rec-3ch-format-a")), r3(("b.go", "rec-3ch-format-b")),
        {"status": "compared", "pairs": [pair("a.go", "b.go", {ch: ex(codeIn=["common-only"], reportable=0, regions=1)
                                                              for ch in CH3})]},
        supp=r3(("s.go", "rec-3ch-format-a")), cc="suppress-supplied-3ch")
    vec("tc-mode-mismatch-three-on-two", ["three-channel", "test-only-profile", "mode-mismatch"],
        "Three-channel modes with two-channel Go catalogues: rejected with mode-mismatch.",
        [("a.go", f"{NG}#go-format-a")], [("b.go", f"{NG}#go-format-b")], rej("mode-mismatch", "comparison-config"), cc=CC3)
    vec("tc-mode-mismatch-two-on-three", ["three-channel", "test-only-profile", "mode-mismatch"],
        "The shipped two-channel modes with three-channel catalogues: rejected with mode-mismatch.",
        r3(("a.go", "rec-3ch-format-a")), r3(("b.go", "rec-3ch-format-b")), rej("mode-mismatch", "comparison-config"))

    # --- real text-plain records (frozen by the text lane, commit 794f1fe), three modes ------------------
    # Hand expectations below were derived from the recorded fingerprint lists in records-text-plain.json
    # (positions and hashes), before this comparison was computed. mergeGap 8 = the text profile's window;
    # minRegionDistinctHashes 1 because the homoglyph pair shares exactly one skeleton fingerprint (position 7).
    CCT = comparison_config_bytes(min_hashes=1, gap=8, modes=["exact", "folded", "skeleton"])
    TE = ["exact", "folded", "skeleton"]
    none3 = {ch: ex(codeIn=["no-shared-fingerprints"], regions=0) for ch in TE}
    vec("text-plain-three-modes", ["text-plain", "three-mode", "homoglyph"],
        "Real text-plain records: identical copy and reflowed copy match in all three modes; the Cyrillic homoglyph variant "
        "of confusable-latin matches only in skeleton (one shared fingerprint, at position 7, so minRegionDistinctHashes 1); "
        "an unrelated text shares nothing. mergeGap 8 equals the text window.",
        ("textrecords", [("latin.txt", "rec-plain-confusable-latin"), ("src.txt", "rec-plain-reflow-a")]),
        ("textrecords", [("copy.txt", "rec-plain-reflow-a"), ("cyr.txt", "rec-plain-confusable-cyrillic"),
                         ("reflow.txt", "rec-plain-reflow-b"), ("unrel.txt", "rec-plain-numbers")]),
        {"status": "compared", "pairs": [
            pair("latin.txt", "copy.txt", copy.deepcopy(none3)),
            pair("latin.txt", "cyr.txt", {"exact": ex(codeIn=["no-shared-fingerprints"], regions=0),
                                          "folded": ex(codeIn=["no-shared-fingerprints"], regions=0),
                                          "skeleton": ex(codeIn=["match"], reportable=1, seeds=[[[7, 7]]])}),
            pair("latin.txt", "reflow.txt", copy.deepcopy(none3)),
            pair("latin.txt", "unrel.txt", copy.deepcopy(none3)),
            pair("src.txt", "copy.txt", {ch: ex(codeIn=["match"], reportable=1, exhaustiveDiagonalZero=True,
                                                seeds=[[[p, p] for p in ps]])
                                         for ch, ps in (("exact", (3, 10, 15)), ("folded", (2, 4, 11)), ("skeleton", (1, 8, 11)))}),
            pair("src.txt", "cyr.txt", copy.deepcopy(none3)),
            pair("src.txt", "reflow.txt", {ch: ex(codeIn=["match"], reportable=1, exhaustiveDiagonalZero=True,
                                                  seeds=[[[p, p] for p in ps]])
                                           for ch, ps in (("exact", (3, 10, 15)), ("folded", (2, 4, 11)), ("skeleton", (1, 8, 11)))}),
            pair("src.txt", "unrel.txt", copy.deepcopy(none3))]},
        cc=CCT)

    # --- I2 cross-check rulings K1-K4 and bounds (hand-derived before computation) ----------------------
    vec("k1-extraction-bounds-k17", ["k1", "extraction-bounds", "malformed-catalogue"],
        "K1: an error-only go-tokens catalogue whose extractionConfig has k 17 (above the extraction bound 16), with "
        "configSha256 recomputed so the digest binding holds. Step 6 rejects it: malformed-catalogue, reference side.",
        [("bad.go", f"{NG}#go-err-unterminated-string")], COPY, rej("malformed-catalogue", "reference"),
        overrides={"reference": "k17"})
    vec("k1-extraction-bounds-max-input", ["k1", "extraction-bounds", "malformed-catalogue"],
        "K1: the same with maxInputBytes 8388609 (one above 8 MiB), as the candidate.",
        SUM, [("bad.go", f"{NG}#go-err-unterminated-string")], rej("malformed-catalogue", "candidate"),
        overrides={"candidate": "max8m1"})
    vec("k1-extraction-bounds-at-bound", ["k1", "extraction-bounds"],
        "K1 companion: both catalogues error-only with k 16 and window 128 (at the bounds) are valid; the pair is not "
        "compared (reference-extraction-error).",
        [("bad.go", f"{NG}#go-err-unterminated-string")], [("bad2.go", f"{NG}#go-err-unterminated-comment")],
        {"status": "compared", "pairs": [pair("bad.go", "bad2.go", status="not-compared", code="reference-extraction-error")]},
        overrides={"reference": "k16w128", "candidate": "k16w128"})
    vec("k3-lone-surrogate", ["k3", "strict-json", "malformed-catalogue"],
        "K3: {\"catalogueVersion\":\"\\ud800\"}: a lone surrogate escape is ill-formed (I-JSON), decided at step 1 "
        "before the version is read: malformed-catalogue, not unsupported-catalogue.",
        SUM, COPY, rej("malformed-catalogue", "reference"), overrides={"reference": "surrogate"})
    vec("k3-non-integer-number", ["k3", "strict-json", "malformed-catalogue"],
        "Step 1: {\"catalogueVersion\":\"x\",\"a\":1.0} has a non-integer number: malformed-catalogue.",
        SUM, COPY, rej("malformed-catalogue", "reference"), overrides={"reference": "float"})
    vec("k4-depth-64", ["k4", "nesting-depth"],
        "K4: 64 nested containers (the object plus 63 arrays) is within the limit, so step 2 decides: unsupported-catalogue.",
        SUM, COPY, rej("unsupported-catalogue", "reference"), overrides={"reference": "depth64"})
    vec("k4-depth-65", ["k4", "nesting-depth", "malformed-catalogue"],
        "K4: 65 nested containers exceeds the limit of 64: malformed-catalogue at step 1.",
        SUM, COPY, rej("malformed-catalogue", "reference"), overrides={"reference": "depth65"})
    vec("bounds-seeds-above", ["config-bounds", "unsupported-comparison-config"],
        "maxSeedsPerMode 10000001 (one above 10^7): unsupported-comparison-config.",
        SUM, COPY, rej("unsupported-comparison-config", "comparison-config"), cc=comparison_config_bytes(max_seeds=10**7 + 1))
    vec("bounds-regions-above", ["config-bounds", "unsupported-comparison-config"],
        "maxRegionsPerMode 100001 (one above 10^5): unsupported-comparison-config.",
        SUM, COPY, rej("unsupported-comparison-config", "comparison-config"), cc=comparison_config_bytes(max_regions=10**5 + 1))
    vec("bounds-at-limits", ["config-bounds"],
        "maxSeedsPerMode 10^7 and maxRegionsPerMode 10^5 (at the bounds) are valid: GO_SUM against itself matches completely.",
        SUM, COPY, {"status": "compared", "pairs": [pair("sum.go", "copy.go", both(exhaust()))]},
        cc=comparison_config_bytes(max_seeds=10**7, max_regions=10**5))

    # --- M2.2 / M2.3 / M2.6 / py-tokens additions (hand-derived before computation) -------------------
    GG = "extraction-go-gates.json"
    PY = "extraction-py.json"
    LIB = ("vendor.strutil.go", f"{GG}#mv-go-vendor-lib")
    VREF = [("own.go", f"{GO}#mv-go-pair"), LIB]
    VCAND = [("app.go", "extraction-go-classes.json#mv-go-classes-a"), LIB]
    nm = both(ex(codeIn=NOMATCH, reportable=0))
    vec("vendor-suppressed", ["vendor", "control", "suppression", "multi-artifact"],
        "Vendor control class (OD-C19, decided in draft): both projects vendor the same third-party file "
        "(vendor.strutil.go). The vendor catalogue holding that file is bound as the suppression catalogue, so every hash "
        "of the vendored pair is common: one diagonal-0 region, common-only, still listed with its counts. Own code is "
        "unrelated.",
        VREF, VCAND, {"status": "compared", "pairs": [
            pair("own.go", "app.go", copy.deepcopy(nm)), pair("own.go", "vendor.strutil.go", copy.deepcopy(nm)),
            pair("vendor.strutil.go", "app.go", copy.deepcopy(nm)),
            pair("vendor.strutil.go", "vendor.strutil.go", both(ex(codeIn=["common-only"], reportable=0, regions=1,
                                                                    exhaustiveDiagonalZero=True)))]},
        supp=[("strutil.go", f"{GG}#mv-go-vendor-lib")], cc="suppress-supplied")
    vec("vendor-unsuppressed", ["vendor", "control", "demonstrative-vendor"],
        "The same projects with no vendor catalogue: the vendored file matches itself completely in both modes, which is why "
        "vendored code is supplied as a vendor (suppression) catalogue and its origin recorded in a review packet (M2.7).",
        VREF, VCAND, {"status": "compared", "pairs": [
            pair("own.go", "app.go", copy.deepcopy(nm)), pair("own.go", "vendor.strutil.go", copy.deepcopy(nm)),
            pair("vendor.strutil.go", "app.go", copy.deepcopy(nm)),
            pair("vendor.strutil.go", "vendor.strutil.go", both(exhaust()))]})
    vec("go-formatted-fragment-in-host", ["formatted-fragment-in-host", "large-host", "trivia-pair"],
        "UC-1 row 'formatted fragment in a large host': GO_SUM reformatted (spacing, indentation, comments, a joined line) "
        "inside a larger host. The token stream is unchanged, so both modes match, localized inside the reformatted "
        "function.",
        SUM, [("host.go", f"{GG}#mv-go-host-formatted")],
        {"status": "compared", "pairs": [pair("sum.go", "host.go", both(
            ex(codeIn=["match"], reportable=1, within={"reference": GO_SUM, "candidate": GO_SUM_FMT})))]})
    vec("go-non-ascii-shift-2", ["unicode", "non-ascii"],
        "Second byte-offset vector, derived by hand before computation: the comment prefix '// Ünïcödé' plus LF is 15 bytes "
        "but 11 code points, so every candidate span is the reference span plus 15.",
        [("g.go", f"{GO}#mv-go-nonascii")], [("h.go", f"{GG}#mv-go-nonascii-prefixed2")],
        {"status": "compared", "pairs": [pair("g.go", "h.go", both(ex(codeIn=["match"], reportable=1,
                                                                       exhaustiveDiagonalZero=True, candidateShift=15)))]})
    vec("py-empty-span-self", ["py-tokens", "empty-span"],
        "py-tokens (registered, specified): py-empty-span-fingerprint against itself. Its exact catalogue stores the "
        "empty-span fingerprint [35, 35) unchanged; the identical pair matches completely in both modes.",
        [("a.py", f"{PY}#py-empty-span-fingerprint")], [("b.py", f"{PY}#py-empty-span-fingerprint")],
        {"status": "compared", "pairs": [pair("a.py", "b.py", {
            "exact": exhaust(),
            "normalized": ex(POST, codeIn=["ambiguous"], reportable=5)})]})
    vec("py-equal-starts", ["py-tokens", "equal-starts"],
        "py-tokens format pair py-format-a/b: zero-width layout tokens give consecutive fingerprints with equal span starts, "
        "which §3.6 allows (starts are non-decreasing). Identical hashes, so both modes match completely.",
        [("a.py", f"{PY}#py-format-a")], [("b.py", f"{PY}#py-format-b")],
        {"status": "compared", "pairs": [pair("a.py", "b.py", both(exhaust()))]})
    # --- A14 (core-gates review): OD-C64 profile-conditional; vendor-suppression effects (hand-derived) ----
    for lang, src, vid0 in (("go", SUM, "go"), ("rust", [("sum.rs", f"{RU}#mv-rust-sum")], "rust")):
        cand0 = COPY if lang == "go" else [("copy.rs", f"{RU}#mv-rust-sum")]
        side_id = src[0][0]
        vec(f"{vid0}-w1-reused-span-start", ["zero-width-rule", "malformed-catalogue"],
            f"A14 (review W1): a {lang} catalogue whose second exact fingerprint reuses the first one's span start. {lang}-tokens "
            "declares no zero-width tokens, so span starts must strictly increase: malformed-catalogue.",
            src, cand0, rej("malformed-catalogue", "reference"), overrides={"reference": "w1"})
        vec(f"{vid0}-w2-identical-spans", ["zero-width-rule", "malformed-catalogue"],
            f"A14 (review W2): a {lang} catalogue with identical spans at two consecutive fingerprint positions: malformed-catalogue.",
            src, cand0, rej("malformed-catalogue", "reference"), overrides={"reference": "w2"})
    vec("go-empty-span-k5", ["zero-width-rule", "malformed-catalogue"],
        "A14: an empty fingerprint span at k = 5 in a go-tokens catalogue. Only profiles with zero-width tokens (py-tokens) may "
        "have empty spans at k > 1: malformed-catalogue.",
        SUM, COPY, rej("malformed-catalogue", "reference"), overrides={"reference": "emptyk"})
    vec("vendor-copied-into-own-code", ["vendor", "vendor-effect"],
        "A14 (vendor-suppression effect 1): the vendored helper copied whole into each project's own source tree under its own "
        "name (util.go, helpers.go). With the vendor catalogue bound, the copy is common-only exactly like the vendored file: "
        "suppression cannot tell own code from vendored code. Compare without the vendor catalogue to see the reuse "
        "(vendor-unsuppressed shows it matching).",
        [("util.go", f"{GG}#mv-go-vendor-lib")], [("helpers.go", f"{GG}#mv-go-vendor-lib")],
        {"status": "compared", "pairs": [pair("util.go", "helpers.go", both(ex(codeIn=["common-only"], reportable=0, regions=1,
                                                                            exhaustiveDiagonalZero=True)))]},
        supp=[("strutil.go", f"{GG}#mv-go-vendor-lib")], cc="suppress-supplied")
    vec("vendor-idiom-suppresses-pair", ["vendor", "vendor-effect"],
        "A14 (vendor-suppression effect 2): two projects share GO_SUM, and the vendor catalogue happens to hold a vendored file "
        "with the same code. Suppression is per hash for every pair, so this pair loses all evidence (common-only) although "
        "neither side is vendored; the counts (distinctCommonHashes, sharedCommonDistinctHashes, suppression.distinctHashes) "
        "show it.",
        SUM, COPY, {"status": "compared", "pairs": [pair("sum.go", "copy.go", both(ex(codeIn=["common-only"], reportable=0,
                                                                                     regions=1, exhaustiveDiagonalZero=True)))]},
        supp=[("strutil.go", f"{GG}#mv-go-vendor-lib"), ("vendored-sum.go", f"{GO}#mv-go-sum")], cc="suppress-supplied")

    Z = "a0a0a0a0a0a0a0a0"
    vec("rv-py-empty-span-region", ["synthetic", "py-tokens", "empty-span"],
        "Synthetic py-tokens catalogues whose only shared fingerprint has an empty span ([30, 30) and [20, 20)): the region's "
        "spans are carried unchanged as empty spans. minRegionDistinctHashes 1, so the single hash is reportable.",
        ("synthetic", "r.syn", 8, [(0, A, [0, 10]), (4, Z, [30, 30])], "py"),
        ("synthetic", "c.syn", 8, [(0, B, [0, 10]), (4, Z, [20, 20])], "py"),
        {"status": "compared", "pairs": [pair("r.syn", "c.syn", both(ex(codeIn=["match"], reportable=1, seeds=[[[4, 4]]],
                                                                         regionSpans=[[[30, 30], [20, 20]]])))]},
        cc=comparison_config_bytes(min_hashes=1))

    cc_cache = {}
    out = []
    for v in V:
        cats, texts, bytes_ = {}, {}, {}
        for side, arts in (("reference", v["ref"]), ("candidate", v["cand"]), ("suppression", v["supp"])):
            if arts is None:
                continue
            texts[side] = {}
            if isinstance(arts, tuple) and arts[0] == "textrecords":
                items = arts[1]
                cb = catalogue_from_records((HERE / TEXT_CFG).read_bytes(), [(a, text_record(r)[0]) for a, r in items])
                for a, r in items:
                    texts[side][a] = text_record(r)[1].decode("utf-8", "replace")
                cats[side] = {"fromRecords": {"extractionConfigFile": TEXT_CFG,
                                              "artifacts": [{"id": a, "record": f"{TEXT_RECORDS}#{r}"} for a, r in items]},
                              "sha256": sha(cb), "canonical": json.loads(cb)}
                bytes_[side] = cb
                continue
            if isinstance(arts, tuple) and arts[0] == "records3":
                items = arts[1]
                cb = catalogue_from_records(CONFIG_3CH, [(a, record_bytes(CONFIG_3CH, base64.b64decode(sources[REC3[r]][0]["inputBase64"]),
                                                                          rederive(sources[REC3[r]][0]["result"], cfg3)))
                                                         for a, r in items])
                for a, r in items:
                    texts[side][a] = base64.b64decode(sources[REC3[r]][0]["inputBase64"]).decode("utf-8", "replace")
                cats[side] = {"fromRecords": {"extractionConfigFile": "config-three-channel-test.json",
                                              "artifacts": [{"id": a, "record": r} for a, r in items]},
                              "sha256": sha(cb), "canonical": json.loads(cb)}
                bytes_[side] = cb
                continue
            if isinstance(arts, tuple) and arts[0] == "synthetic":
                _, aid, m, fps, *prof = arts
                if prof and prof[0] == "py":
                    cat = synthetic_catalogue((HERE / "config-py.json").read_bytes(), json.loads((HERE / "config-py.json").read_bytes()),
                                              aid, m, fps)
                else:
                    cat = synthetic_catalogue(go_cfg_raw, go_cfg, aid, m, fps)
                b = canonical(cat)
                cats[side] = {"sha256": sha(b), "canonical": cat,
                              "synthetic": "Winnowing-shaped catalogue with no source bytes; the artifact digest is the SHA-256 "
                                           f"of the ASCII string 'traceweave synthetic artifact {aid}'."}
                bytes_[side] = b
                continue
            entries, cfg_raw, cfg = [], None, None
            for aid, src in arts:
                rec, raw, c = sources[src]
                assert cfg_raw is None or raw == cfg_raw, "one configuration per catalogue"
                cfg_raw, cfg = raw, c
                entries.append(catalogue_entry(aid, rec))
                texts[side][aid] = base64.b64decode(rec["inputBase64"]).decode("utf-8", "replace")
            cat = build_catalogue(cfg_raw, cfg, entries)
            ov = v["overrides"].get(side)
            entry = {"artifacts": [{"id": a, "source": s} for a, s in arts]}
            if ov is None:
                b = canonical(cat)
                entry.update({"sha256": sha(b), "canonical": cat})
            else:
                if ov == "pretty":
                    b = (json.dumps(cat, sort_keys=True, indent=2) + "\n").encode()
                    note = "Pretty-printed form of the catalogue built from the listed artifacts."
                elif ov == "version":
                    cat["catalogueVersion"] = "traceweave-catalogue-draft-9"
                    b = canonical(cat)
                    note = "Catalogue built from the listed artifacts with catalogueVersion changed to traceweave-catalogue-draft-9."
                elif ov in ("k17", "max8m1", "k16w128"):
                    upd = {"k17": {"k": 17}, "max8m1": {"maxInputBytes": 8388609}, "k16w128": {"k": 16, "window": 128}}[ov]
                    cat["extractionConfig"].update(upd)
                    cat["profile"]["configSha256"] = sha(extraction_config_bytes(cat["extractionConfig"]))
                    b = canonical(cat)
                    note = (f"Catalogue built from the listed artifacts (error entries only), then extractionConfig changed to "
                            f"{json.dumps(upd)} and configSha256 recomputed.")
                    if ov == "k16w128":
                        entry.update({"sha256": sha(b), "canonical": json.loads(b), "configOverride": upd})
                        cats[side] = entry
                        bytes_[side] = b
                        continue
                elif ov in ("w1", "w2", "emptyk"):
                    fp = cat["artifacts"][0]["channels"]["exact"]["fingerprints"]
                    if ov == "w1":
                        fp[1]["span"][0] = fp[0]["span"][0]            # W1: the previous fingerprint's start reused
                    elif ov == "w2":
                        fp[1]["span"] = list(fp[0]["span"])            # W2: identical spans at consecutive positions
                    else:
                        fp[0]["span"][1] = fp[0]["span"][0]            # an empty span at k = 5
                    b = canonical(cat)
                    note = {"w1": "Catalogue built from the listed artifact, then its second exact fingerprint's span start set to "
                                  "the first fingerprint's start (review W1).",
                            "w2": "Catalogue built from the listed artifact, then its second exact fingerprint's span set equal to "
                                  "the first's (review W2).",
                            "emptyk": "Catalogue built from the listed artifact, then its first exact fingerprint's span made empty "
                                      "([start, start)) at k = 5."}[ov]
                elif ov in ("surrogate", "float", "depth64", "depth65"):
                    b = {"surrogate": b'{"catalogueVersion":"\\ud800"}',
                         "float": b'{"catalogueVersion":"x","a":1.0}',
                         "depth64": b'{"catalogueVersion":"x","a":' + b"[" * 63 + b"]" * 63 + b"}",
                         "depth65": b'{"catalogueVersion":"x","a":' + b"[" * 64 + b"]" * 64 + b"}"}[ov]
                    note = "Fabricated bytes for contract §3.6 step 1 (" + ov + "); the artifact list is not used."
                elif ov == "dupkey":
                    c = canonical(cat)
                    b = c[:-1] + b',"catalogueVersion":"traceweave-catalogue-draft-9"}'
                    note = ("Canonical catalogue built from the listed artifacts, with a second catalogueVersion member "
                            "(traceweave-catalogue-draft-9) appended after the last member.")
                else:
                    cat["extractionConfig"]["profileVersion"] = "draft-2"
                    cat["profile"]["version"] = "draft-2"
                    cat["profile"]["configSha256"] = sha(extraction_config_bytes(cat["extractionConfig"]))
                    b = canonical(cat)
                    note = ("Fabricated: catalogue built from the listed artifacts, then profileVersion set to draft-2 and the "
                            "configuration digest recomputed. No draft-2 extraction exists.")
                entry.update({"sha256": sha(b), "bytesBase64": base64.b64encode(b).decode(), "fabricated": note})
            cats[side] = entry
            bytes_[side] = b
        if v["cc"] == "suppress":
            boiler = build_catalogue(go_cfg_raw, go_cfg, [catalogue_entry(a, sources[s][0]) for a, s in BOILER])
            cc_raw = comparison_config_bytes(supp=sha(canonical(boiler)))
        elif v["cc"] == "suppress-other":
            cc_raw = comparison_config_bytes(supp=sha(canonical(build_catalogue(
                go_cfg_raw, go_cfg, [catalogue_entry(a, sources[s][0]) for a, s in BOILER]))))
        elif v["cc"] == "suppress-supplied-3ch":
            cc_raw = comparison_config_bytes(supp=sha(bytes_["suppression"]), modes=CH3)
        elif v["cc"] == "suppress-supplied":
            cc_raw = comparison_config_bytes(supp=sha(bytes_["suppression"]))
        elif v["cc"] is None:
            cc_raw = COMPARISON_CONFIG
        else:
            cc_raw = v["cc"]
        body = compare(bytes_["reference"], bytes_["candidate"], cc_raw, bytes_.get("suppression"))
        check_hand(v["id"], v["hand"], body, texts)
        derivs = {e["derivation"] for p in v["hand"].get("pairs", []) for e in p.get("modes", {}).values()}
        test3 = "three-channel" in v["tags"]
        rec = {"id": v["id"], "tags": v["tags"], "description": v["description"], **({"testOnlyProfile": True} if test3 else {}),
               "derivation": "hand" if derivs <= {HAND} else "mixed",
               "comparisonConfig": ({"file": "comparison-config.json"} if cc_raw == COMPARISON_CONFIG
                                    else {"bytesBase64": base64.b64encode(cc_raw).decode()}),
               "reference": cats["reference"], "candidate": cats["candidate"]}
        if "suppression" in cats:
            rec["suppression"] = cats["suppression"]
        rec.update({"handExpectations": v["hand"],
                    "expectedReport": {"bodySha256": sha(canonical(body)), "body": body}})
        out.append(rec)
    doc = {"contract": "traceweave-catalogue-report-draft-2",
           "note": "Draft matching vectors (spec/catalogue-report.md). No detection-accuracy claim.",
           "derivationRule": ROADMAP_DEFINITION + " " + MATCHING_RULE_APPLICATION,
           "comparisonConfigFile": "comparison-config.json", "comparisonConfigSha256": sha(COMPARISON_CONFIG),
           "requiredTags": sorted({"identical", "function-in-host", "large-host", "partial-copy", "trivia-pair", "rename-pair",
                                   "boilerplate", "suppression", "no-overlap", "config-mismatch", "profile-mismatch",
                                   "malformed-candidate", "malformed-catalogue", "duplicate-regions", "tie",
                                   "insufficient-tokens", "unsupported-comparison-config", "unsupported-catalogue",
                                   "unsupported-profile", "rust", "merge-boundary", "ambiguity-definition", "non-ascii",
                                   "reference-error", "duplicate-key", "output-cap", "seed-limit", "distinct-evidence",
                                   "suppression-catalogue-mismatch", "independent-same-task", "shadowing",
                                   "pair-precedence", "match-over-ambiguous", "ambiguous-over-weaker",
                                   "below-over-common", "mixed-common-region", "invariance", "ambiguity-before-cap",
                                   "suppression-artifact-count", "suppression-order", "input-too-large",
                                   "three-channel", "mode-mismatch", "text-plain", "k1", "k3", "k4", "config-bounds",
                                   "vendor", "formatted-fragment-in-host", "py-tokens", "empty-span", "equal-starts",
                                   "zero-width-rule", "vendor-effect"}),
           "vectors": out}
    (HERE / "matching.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    build_records(sources, out)

    ex_body = next(r for r in out if r["id"] == "go-function-in-host")["expectedReport"]
    report = {"body": ex_body["body"],
              "provenance": {"bodySha256": ex_body["bodySha256"],
                             "comparisonConfigSha256": ex_body["body"]["inputs"]["comparisonConfigSha256"],
                             "generatedAt": "2026-11-22T00:00:00Z",
                             "implementation": {"commit": "0" * 40, "name": "build_vectors.py", "version": "draft-2"},
                             "specCommit": "0" * 40}}
    (HERE / "example-report.json").write_text(json.dumps(report, indent=1) + "\n")
    for r in out:
        b = r["expectedReport"]["body"]
        if b["status"] == "rejected":
            line = f"rejected {b['rejection']['code']} ({b['rejection']['side']})"
        else:
            line = " ".join(
                (f"{p['reference']['id']}/{p['candidate']['id']}:" +
                 (p["outcome"]["code"] if p["status"] == "not-compared" else
                  ",".join(f"{ch[0]}={m['outcome']['code']}[{m['regionCounts']['reportable']}/{sum(m['regionCounts'].values())}]"
                           for ch, m in p["modes"].items()))) for p in b["pairs"])
        print(f"{r['id']}: {line}")
    print(f"wrote {len(out)} vectors")


# ------------------------------------------------------------------ extraction records (contract §2a)

RECORD_VERSION = "traceweave-extraction-record-draft-1"


def record_bytes(cfg_raw, data, result):
    """Canonical extraction record: fixed key order, compact, ECMAScript/JCS string escaping, final LF."""
    try:
        cfg = json.loads(cfg_raw)
        valid = not (result["status"] == "error" and result["error"]["code"] == "unsupported-config")
    except ValueError:
        valid = False
    unread = result["status"] == "error" and result["error"]["code"] in ("unsupported-config", "input-too-large")
    rec = {"recordVersion": RECORD_VERSION,
           "profile": cfg["profile"] if valid else None,
           "profileVersion": cfg["profileVersion"] if valid else None,
           "configSha256": sha(cfg_raw),
           "inputSha256": None if unread else sha(data),
           "inputLength": None if unread else len(data)}
    if result["status"] == "error":
        r = {"status": "error", "error": {"code": result["error"]["code"], "offset": result["error"]["offset"]}}
    else:
        def kg(g):
            return {"position": g["position"], "hash": g["hash"], "span": list(g["span"])}

        def chan(c, values):
            o = {"tokenIndices": list(c["tokenIndices"])} if "tokenIndices" in c else {}   # only profiles with exclusions
            o.update({"values": list(c["values"])} if values else {})
            o.update({"kgrams": [kg(g) for g in c["kgrams"]], "windowSelections": list(c["windowSelections"]),
                      "partialWindow": c["partialWindow"], "fingerprints": [kg(g) for g in c["fingerprints"]]})
            return o
        toks = []
        for t in result["tokens"]:
            o = {"class": t["class"], "text": t["text"], "span": list(t["span"])}
            if t.get("inserted"):
                o["inserted"] = True
            toks.append(o)
        r = {"status": result["status"], "tokenCount": result["tokenCount"], "tokens": toks,
             "channels": {ch: chan(c, ch != "exact") for ch, c in result["channels"].items()}}
    rec["result"] = r
    return (json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


REGISTERED = {("go-tokens", "draft-1"), ("rust2024-tokens", "draft-1"), ("ts-tokens", "draft-2"), ("text-plain", "draft-1"),
              ("py-tokens", "draft-1")}


def catalogue_from_records(cfg_raw, items, allow_test=True):
    """Contract §3.8: items = [(id, record bytes)]. Returns catalogue bytes, or raises ValueError.
    Validation depth (§3.8 step 2): canonical form and §2a structure, including tokenCount; no hash re-derivation."""
    cfg = json.loads(cfg_raw)
    if not items:
        raise ValueError("no artifacts: a catalogue has at least one")
    if (cfg["profile"], cfg["profileVersion"]) not in REGISTERED and not (allow_test and "test" in cfg["profile"]):
        raise ValueError("profile not registered")
    entries = []
    for aid, rb in items:
        r = json.loads(rb)
        if r["configSha256"] != sha(cfg_raw):
            raise ValueError("record configuration differs from the catalogue configuration")
        res = r["result"]
        if res["status"] == "error" and res["error"]["code"] == "unsupported-config":
            raise ValueError("unsupported-config records yield no catalogue entry")
        if res["status"] != "error" and res["tokenCount"] != len(res["tokens"]):
            raise ValueError("tokenCount differs from the number of tokens")
        e = {"byteLength": r["inputLength"], "id": aid, "sha256": r["inputSha256"], "status": res["status"]}
        if res["status"] == "error":
            e["error"] = dict(res["error"])
        else:
            e["tokenCount"] = res["tokenCount"]
            e["channels"] = {ch: {"fingerprints": [{"hash": f["hash"], "position": f["position"], "span": f["span"]}
                                                   for f in res["channels"][ch]["fingerprints"]],
                                  "kgramCount": max(0, len(res["channels"][ch].get("tokenIndices", res["tokens"])) - cfg["k"] + 1),
                                  "partialWindow": res["channels"][ch]["partialWindow"]} for ch in cfg["channels"]}
        entries.append(e)
    return canonical(build_catalogue(cfg_raw, cfg, entries))


def build_records(sources, matching_out):
    neg = json.loads((EXV / "config-negative.json").read_text())["negatives"]
    negs = {n["id"]: n for n in neg}
    NG, NR, LG = "../extraction/go.json", "../extraction/rust.json", "../extraction/limits-go.json"
    GO = "extraction-go.json"
    specs = [
        ("rec-go-ok", ["ok"], f"{NG}#go-format-a", "ok result (Go): inserted semicolons carry inserted:true."),
        ("rec-go-ok-unicode", ["ok", "non-ascii"], f"{NG}#go-unicode", "Non-ASCII token text is written as raw UTF-8, never as \\u escapes."),
        ("rec-go-ok-raw-cr", ["ok", "escape"], f"{NG}#go-raw-string-cr", "A raw string containing CR LF: written as \\r\\n."),
        ("rec-go-ok-vt", ["ok", "escape"], f"{NG}#go-escapes-vt-raw", "A raw string containing U+000B: written as \\u000b (lowercase hex)."),
        ("rec-go-ok-sum", ["ok"], f"{GO}#mv-go-sum", "ok result for GO_SUM (used by the catalogue-from-records vector)."),
        ("rec-go-insufficient", ["insufficient-tokens"], f"{NG}#go-short", "insufficient-tokens: tokens and values present, k-gram lists empty."),
        ("rec-go-empty", ["insufficient-tokens"], f"{NG}#go-empty", "Empty input: zero tokens, empty arrays."),
        ("rec-go-lexical-error", ["error", "lexical-error"], f"{NG}#go-err-unterminated-string", "Lexical error: input digest and length present, integer offset."),
        ("rec-go-encoding-error", ["error"], f"{NG}#go-err-invalid-utf8", "Invalid UTF-8 input: the record is still UTF-8 (no token text)."),
        ("rec-go-over-limit", ["error", "input-too-large"], f"{LG}#go-limit-over", "input-too-large: inputSha256 and inputLength null, offset 0 (Q10)."),
        ("rec-go-over-limit-precedence", ["error", "input-too-large"], f"{LG}#go-limit-precedence", "Over the limit and invalid UTF-8: input-too-large, nulls."),
        ("rec-go-limit-exact", ["ok"], f"{LG}#go-limit-exact", "Exactly maxInputBytes (16): ok."),
        ("rec-unsupported-config", ["error", "unsupported-config"], "../extraction/config-negative.json#cfg-whitespace",
         "unsupported-config: profile, profileVersion, inputSha256, inputLength and offset null; configSha256 over the bytes supplied."),
        ("rec-unsupported-config-2", ["error", "unsupported-config"], "../extraction/config-negative.json#" + neg[1]["id"],
         "A second unsupported-config record (" + neg[1]["reason"] + ")."),
        ("rec-rust-ok", ["ok"], f"{NR}#rust-literals", "Rust ok result: token text with quotes and backslashes is escaped as \\\" and \\\\."),
        ("rec-rust-lexical-error", ["error", "lexical-error"], f"{NR}#rust-err-unbalanced", "Rust lexical error."),
    ] + [(f"rec-{vid}", ["exclusions", "test-only-profile"], f"../extraction/exclusion-rule.json#{vid}",
          f"TEST-ONLY profile go-tokens-exclusion-test (extraction OD-23): normalized channel with tokenIndices; {why}.")
         for vid, why in (("excl-semi-newlines", "inserted semicolons excluded from normalized"),
                          ("excl-semi-explicit", "explicit semicolons excluded too"),
                          ("excl-ok-normalized-empty", "ok status with an empty normalized channel"),
                          ("excl-insufficient", "insufficient-tokens decided by the exact count"),
                          ("excl-partial-window", "normalized partial window while exact is full"))]
    go_cfg_raw = (EXV / "config-go.json").read_bytes()
    UC_INPUT = b"x := 1\n"
    records, by_id = [], {}
    cfg3 = json.loads(CONFIG_3CH)
    for rid, src in REC3.items():
        rec, _, _ = sources[src]
        data = base64.b64decode(rec["inputBase64"])
        rb = record_bytes(CONFIG_3CH, data, rederive(rec["result"], cfg3))
        by_id[rid] = (rb, CONFIG_3CH)
        records.append({"id": rid, "tags": ["three-channel", "test-only-profile"],
                        "description": "TEST-ONLY three-channel profile go-tokens-three-channel-test (contract §2b): the token "
                                       "stream of the source vector, re-derived under channels exact, normalized, classes.",
                        "source": src, "rederivedFromTokens": True, "derivation": "hand",
                        "configFile": "config-three-channel-test.json", "configSha256": sha(CONFIG_3CH),
                        "inputBase64": rec["inputBase64"], "expectedRecordSha256": sha(rb),
                        "expectedRecordText": rb.decode("utf-8")})
    for rid, tags, src, desc in specs:
        if "config-negative.json" in src:
            n = negs[src.split("#")[1]]
            cfg_raw, data, result = base64.b64decode(n["configBase64"]), UC_INPUT, n["expectedResult"]
            entry = {"configBase64": n["configBase64"], "configSha256": sha(cfg_raw),
                     "inputBase64": base64.b64encode(data).decode()}
        else:
            rec, cfg_raw, _ = sources[src]
            data, result = base64.b64decode(rec["inputBase64"]), rec["result"]
            fname = src.split("#")[0]
            cfg_file = str(Path(fname).parent / json.loads((HERE / fname).read_text())["configFile"])
            cfg_file = "../extraction/" + Path(cfg_file).name if "extraction" in cfg_file else cfg_file
            assert (HERE / cfg_file).read_bytes() == cfg_raw
            entry = {"configFile": cfg_file, "configSha256": sha(cfg_raw), "inputBase64": rec["inputBase64"]}
        rb = record_bytes(cfg_raw, data, result)
        by_id[rid] = (rb, cfg_raw)
        records.append({"id": rid, "tags": tags, "description": desc, "source": src, "derivation": "hand", **entry,
                        "expectedRecordSha256": sha(rb), "expectedRecordText": rb.decode("utf-8")})
    m = {v["id"]: v for v in matching_out}
    builds = [
        ("cat-go-reference-side-failures", "config-go.json",
         [("bad.go", "rec-go-lexical-error"), ("short.go", "rec-go-insufficient"), ("sum.go", "rec-go-ok-sum")],
         "go-reference-side-failures", "reference"),
        ("cat-go-input-too-large", "config-go-limit16.json",
         [("copy.go", "rec-go-limit-exact"), ("over.go", "rec-go-over-limit"), ("prec.go", "rec-go-over-limit-precedence")],
         "go-input-too-large", "candidate"),
    ]
    cats = []
    for cid, cfgname, items, vid, side in builds:
        cfg_raw = (EXV / cfgname).read_bytes()
        cb = catalogue_from_records(cfg_raw, [(a, by_id[r][0]) for a, r in items])
        assert sha(cb) == m[vid][side]["sha256"], cid
        cats.append({"id": cid, "extractionConfigFile": f"../extraction/{cfgname}",
                     "artifacts": [{"id": a, "record": r} for a, r in items],
                     "expectedCatalogueSha256": sha(cb), "sameAs": f"matching.json#{vid}/{side}"})
    excl = [("e1.go", "rec-excl-semi-newlines"), ("e2.go", "rec-excl-semi-explicit"), ("e3.go", "rec-excl-ok-normalized-empty"),
            ("e4.go", "rec-excl-insufficient"), ("e5.go", "rec-excl-partial-window")]
    cfg_raw = (EXV / "config-exclusion-test.json").read_bytes()
    cb = catalogue_from_records(cfg_raw, [(a, by_id[r][0]) for a, r in excl])
    cats.append({"id": "cat-exclusion-test", "testOnlyProfile": True,
                 "extractionConfigFile": "../extraction/config-exclusion-test.json",
                 "artifacts": [{"id": a, "record": r} for a, r in excl], "expectedCatalogueSha256": sha(cb),
                 "note": "TEST-ONLY profile: per-channel kgramCount max(0, n_C - k + 1); the normalized channel of e3.go is "
                         "empty although its status is ok. Checked against a catalogue rebuilt from the extraction vectors."})
    rejections = [
        ("build-mixed-configurations", "config-go.json", [("a.go", "rec-go-ok"), ("tiny.go", "rec-go-limit-exact")],
         "records under two different configurations cannot form one catalogue"),
        ("build-unsupported-config-record", "config-go.json", [("a.go", "rec-go-ok"), ("bad.cfg", "rec-unsupported-config")],
         "an unsupported-config record yields no catalogue entry, and its configuration is not the catalogue's"),
        ("build-wrong-config-bytes", "config-go-limit16.json", [("a.go", "rec-go-ok")],
         "the record's configSha256 is not the digest of the configuration supplied to the builder"),
    ]
    cb = catalogue_from_records(CONFIG_3CH, [(a, by_id[r][0]) for a, r in
                                             (("a.go", "rec-3ch-format-a"), ("bad.go", "rec-3ch-lexical-error"),
                                              ("short.go", "rec-3ch-insufficient"))])
    cats.append({"id": "cat-three-channel-test", "testOnlyProfile": True,
                 "extractionConfigFile": "config-three-channel-test.json",
                 "artifacts": [{"id": a, "record": r} for a, r in (("a.go", "rec-3ch-format-a"), ("bad.go", "rec-3ch-lexical-error"),
                                                                    ("short.go", "rec-3ch-insufficient"))],
                 "expectedCatalogueSha256": sha(cb),
                 "note": "TEST-ONLY three-channel profile: every entry has channels exact, normalized, classes."})
    titems = [("err.txt", "rec-plain-err-nul"), ("short.txt", "rec-plain-short"), ("src.txt", "rec-plain-reflow-a")]
    cb = catalogue_from_records((HERE / TEXT_CFG).read_bytes(), [(a, text_record(r)[0]) for a, r in titems])
    cats.append({"id": "cat-text-plain", "extractionConfigFile": TEXT_CFG,
                 "artifacts": [{"id": a, "record": f"{TEXT_RECORDS}#{r}"} for a, r in titems],
                 "expectedCatalogueSha256": sha(cb),
                 "note": "Built from frozen text-plain records (ok, insufficient-tokens, nul error): channels exact, folded, skeleton."})
    # K2: build from records for every registered profile, text-plain included (explicit vector).
    k2 = [("latin.txt", "rec-plain-confusable-latin"), ("thai.txt", "rec-plain-thai")]
    cb = catalogue_from_records((HERE / TEXT_CFG).read_bytes(), [(a, text_record(r)[0]) for a, r in k2], allow_test=False)
    cats.append({"id": "cat-k2-text-plain-registered", "extractionConfigFile": TEXT_CFG,
                 "artifacts": [{"id": a, "record": f"{TEXT_RECORDS}#{r}"} for a, r in k2], "expectedCatalogueSha256": sha(cb),
                 "note": "K2 (I2 cross-check): a builder builds from records for every registered profile, text-plain included; "
                         "refusing a registered profile is non-conformant (contract §3.8 step 1)."})
    # §3.8 step 2 validation depth: a hash changed consistently in kgrams and fingerprints is ACCEPTED (no re-derivation).
    r0 = json.loads(by_id["rec-go-ok"][0])
    old = r0["result"]["channels"]["exact"]["fingerprints"][0]["hash"]
    for g in r0["result"]["channels"]["exact"]["kgrams"] + r0["result"]["channels"]["exact"]["fingerprints"]:
        if g["hash"] == old:
            g["hash"] = "0123456789abcdef"
    altered = (json.dumps(r0, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    cb = catalogue_from_records(go_cfg_raw, [("a.go", altered)])
    cats.append({"id": "cat-builder-hash-not-rederived", "extractionConfigFile": "../extraction/config-go.json",
                 "artifacts": [{"id": "a.go", "recordText": altered.decode("utf-8")}], "expectedCatalogueSha256": sha(cb),
                 "note": "§3.8 step 2: rec-go-ok with its first exact fingerprint hash replaced by 0123456789abcdef in both "
                         "kgrams and fingerprints. The record is canonical and structurally consistent, so the builder ACCEPTS it: "
                         "builders do not re-derive hashes (they have no input bytes)."})
    rows = []
    r1 = json.loads(by_id["rec-go-ok"][0])
    r1["result"]["tokenCount"] += 1
    rows.append(("build-tokencount-mismatch", "config-go.json",
                 [("a.go", None, (json.dumps(r1, separators=(",", ":"), ensure_ascii=False) + "\n"))],
                 "§3.8 step 2: tokenCount differs from the number of tokens"))
    rows.append(("build-unregistered-profile", "config-exclusion-test.json", [("e1.go", "rec-excl-semi-newlines", None)],
                 "§3.8 step 1: go-tokens-exclusion-test is TEST-ONLY, not registered (no testOnlyProfile flag)"))
    rows.append(("build-empty-artifact-list", "config-go.json", [], "a catalogue has at least one artifact"))
    extra_rej = []
    for rid, cfgname, items, reason in rows:
        try:
            catalogue_from_records((EXV / cfgname).read_bytes(),
                                   [(a, txt.encode("utf-8") if txt else by_id[r][0]) for a, r, txt in items], allow_test=False)
            raise SystemExit(f"builder accepted {rid}")
        except ValueError:
            pass
        extra_rej.append({"id": rid, "extractionConfigFile": f"../extraction/{cfgname}",
                          "artifacts": [({"id": a, "record": r} if r else {"id": a, "recordText": txt}) for a, r, txt in items],
                          "reason": reason})
    rej = []
    for rid, cfgname, items, reason in rejections:
        try:
            catalogue_from_records((EXV / cfgname).read_bytes(), [(a, by_id[r][0]) for a, r in items])
            raise SystemExit(f"builder accepted {rid}")
        except ValueError:
            pass
        rej.append({"id": rid, "extractionConfigFile": f"../extraction/{cfgname}",
                    "artifacts": [{"id": a, "record": r} for a, r in items], "reason": reason})
    doc = {"recordVersion": RECORD_VERSION,
           "note": "Expected canonical extraction records (contract §2a). Every record names its extraction configuration "
                   "explicitly: configFile (path relative to this file) or configBase64 (the exact bytes, used for rejected "
                   "configurations), plus configSha256 over those bytes. expectedRecordText is the UTF-8 decoding of the "
                   "exact record bytes, including the final LF; expectedRecordSha256 is over those bytes.",
           "records": records, "cataloguesFromRecords": cats, "catalogueBuildRejections": rej + extra_rej}
    (HERE / "records.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} record vectors, {len(cats)} catalogue-from-records vectors, {len(rej)} build rejections")


if __name__ == "__main__":
    main()
