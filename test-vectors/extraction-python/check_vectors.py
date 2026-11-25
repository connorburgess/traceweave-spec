#!/usr/bin/env python3
"""Checker for the py-tokens vectors (draft-1).

    python3 -I test-vectors/extraction-python/check_vectors.py

Standard library only. For every vector it:
  * validates the configuration bytes (contract §10) and rejects the negatives;
  * recomputes the shared pre-lexing checks (size, UTF-8, BOM, NUL);
  * re-lexes the input with pylex.py (written from the profile text, separately
    from the hand-written token lists) and requires class, text, byte span,
    error code and error offset to be identical;
  * checks the recorded stream against rules re-implemented here WITHOUT pylex:
      - layout: NEWLINE, INDENT and DEDENT are re-derived from the input bytes and
        the recorded non-layout tokens (bracket depth from the stream, line ends,
        comments and continuations from the gaps between tokens, indentation by
        the tab-size-8 / tab-size-1 rule) and must match exactly;
      - keyword classes from the 35-word list (soft keywords are ident);
      - operator membership and longest match;
      - numeric literal shapes and what may follow a number;
      - string prefixes: letter sets, class by prefix, no missed prefix;
      - closed class and error-code lists, text == input[span], zero-width
        tokens exactly for the layout classes;
  * recomputes normalized values, k-gram bytes, hashes and winnowing
    (sort-based selection, a different formulation from the builder);
  * checks the pair invariants (format, rename, re-indent, line-join, semicolon);
and then runs two self-tests: each vector corruption (rehashed so only the
targeted layer is wrong) must be rejected, and each wrong-but-plausible lexer
(a pylex.Lexer subclass with one rule changed) substituted for the profile's
lexer must make the checker fail on the shipped vectors.
"""
import base64
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pylex  # noqa: E402

DOMAIN = b"traceweave/token-kgram/draft-1"
CONTRACT = "traceweave-token-winnow-draft-1"
KEY_ORDER = ["contract", "profile", "profileVersion", "channels", "k", "window", "hash", "maxInputBytes"]
FILES = ["py.json", "limits-py.json"]
VERSION = "draft-1"
BOUNDS = {"k": 16, "window": 128, "maxInputBytes": 8388608}
EXCLUSIONS = []  # profile §7: py-tokens declares no normalizedExclusions
PAIRS = {"format": [("py-format-a", "py-format-b")], "reindent": [("py-reindent-a", "py-reindent-b")],
         "linejoin": [("py-linejoin-a", "py-linejoin-b")], "rename": [("py-rename-a", "py-rename-b")],
         "semi": [("py-semi-a", "py-semi-b")]}

# Independent restatements of profile rules (not imported from pylex).
KEYWORDS = set("False None True and as assert async await break class continue def del elif else except finally "
               "for from global if import in is lambda nonlocal not or pass raise return try while with "
               "yield".split())
SOFT = {"match", "case", "type", "_"}
OPS = set("+= -= *= **= /= //= %= &= |= ^= <<= >>= @= := & | ^ ~ << >> <= >= < > == != ( ) [ ] { } , : ! ; = -> "
          "+ - ** * // / % ... . @".split())
D = r"[0-9](?:_?[0-9])*"
FLOAT_RX = rf"(?:{D}\.(?:{D})?(?:[eE][+-]?{D})?|\.{D}(?:[eE][+-]?{D})?|{D}[eE][+-]?{D})"
NUM_RX = {"int": re.compile(r"(?:[1-9](?:_?[0-9])*|0(?:_?0)*|0[bB](?:_?[01])+|0[oO](?:_?[0-7])+"
                            r"|0[xX](?:_?[0-9a-fA-F])+)"),
          "float": re.compile(FLOAT_RX), "imag": re.compile(rf"(?:{FLOAT_RX}|{D})[jJ]")}
LAYOUT = {"newline", "indent", "dedent"}
STRINGISH = {"string", "bytes", "fstring-start", "tstring-start"}
MIDDLES = {"fstring-middle", "tstring-middle"}


class CheckError(Exception):
    pass


def require(cond, msg):
    if not cond:
        raise CheckError(msg)


# ------------------------------------------------------------------ configuration

def validate_config(raw):
    """Returns the parsed config or raises CheckError (= unsupported-config)."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise CheckError("not UTF-8")
    require(text.endswith("\n") and "\n" not in text[:-1] and "\r" not in text, "line breaks")

    def pairs(items):
        keys = [k for k, _ in items]
        require(len(keys) == len(set(keys)), "duplicate key")
        return dict(items)

    def bad_const(c):
        raise CheckError("constant " + c)

    try:
        cfg = json.loads(text, object_pairs_hook=pairs, parse_float=lambda s: bad_const(s), parse_constant=bad_const)
    except (ValueError, CheckError) as e:
        raise CheckError(f"JSON: {e}")
    require(isinstance(cfg, dict) and list(cfg) == KEY_ORDER, "keys/order")
    for key in ("contract", "profile", "profileVersion", "hash"):
        require(isinstance(cfg[key], str) and cfg[key] and all(c in "abcdefghijklmnopqrstuvwxyz0123456789.-"
                                                                for c in cfg[key]), key)
    for key in ("k", "window", "maxInputBytes"):
        require(type(cfg[key]) is int and 1 <= cfg[key] <= BOUNDS[key], key)
    require(cfg["channels"] == ["exact", "normalized"], "channels")
    require(cfg["contract"] == CONTRACT and cfg["hash"] == "sha256-first8-u64be", "contract/hash")
    require(cfg["profile"] in pylex.PROFILES and cfg["profileVersion"] == VERSION, "profile pair")
    canon = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False) + "\n"
    require(canon.encode() == raw, "not canonical")
    return cfg


def check_negative_configs():
    items = json.loads((HERE / "config-negative-python.json").read_text(encoding="utf-8"))
    n = 0
    for it in items:
        raw = base64.b64decode(it["configBase64"])
        try:
            validate_config(raw)
        except CheckError:
            er = it["expectedResult"]
            require(er["error"] == {"code": "unsupported-config", "offset": None} and er["profile"] is None
                    and er["configSha256"] == hashlib.sha256(raw).hexdigest(), f"expectedResult of {it['why']}")
            n += 1
            continue
        raise CheckError(f"negative config accepted: {it['why']}")
    return n, len(items)


# ------------------------------------------------------------------ hashing / winnowing

def lp(b):
    return len(b).to_bytes(4, "big") + b


def kgram_hash(cfg, channel, pairs):
    buf = bytearray(lp(DOMAIN) + lp(cfg["profile"].encode()) + lp(cfg["profileVersion"].encode())
                    + lp(channel.encode()) + cfg["k"].to_bytes(4, "big"))
    for cls, val in pairs:
        buf += lp(cls.encode()) + lp(val.encode())
    return hashlib.sha256(bytes(buf)).digest()[:8].hex()


def normalized(cls, text):
    return "" if cls == "ident" or cls in pylex.LITERAL_CLASSES else text


def select(hashes, w):
    m = len(hashes)
    if m == 0:
        return [], False
    wins = [(0, m)] if m < w else [(s, s + w) for s in range(m - w + 1)]
    return [sorted(range(a, b), key=lambda j: (hashes[j], -j))[0] for a, b in wins], m < w


def channels_for(tokens, cfg):
    k, w = cfg["k"], cfg["window"]
    out = {}
    for ch in ("exact", "normalized"):
        vals = [t["text"] if ch == "exact" else normalized(t["class"], t["text"]) for t in tokens]
        pairs = [(t["class"], v) for t, v in zip(tokens, vals)]
        kg = [{"position": i, "hash": kgram_hash(cfg, ch, pairs[i:i + k]),
               "span": [tokens[i]["span"][0], tokens[i + k - 1]["span"][1]]}
              for i in range(max(0, len(tokens) - k + 1))]
        sel, partial = select([int(g["hash"], 16) for g in kg], w)
        c = {"values": vals} if ch == "normalized" else {}
        c.update({"kgrams": kg, "windowSelections": sel, "partialWindow": partial,
                  "fingerprints": [kg[p] for p in sorted(set(sel))]})
        out[ch] = c
    return out


def rehash(v, cfg):
    r = v["result"]
    if r["status"] == "error":
        return
    r["tokenCount"] = len(r["tokens"])
    r["status"] = "ok" if len(r["tokens"]) >= cfg["k"] else "insufficient-tokens"
    r["channels"] = channels_for(r["tokens"], cfg)


# ------------------------------------------------------------------ input checks

def first_invalid_utf8(data):
    try:
        data.decode("utf-8")
        return None
    except UnicodeDecodeError as e:
        return e.start


def expected_result(data, cfg, lexer=pylex.Lexer):
    """('error', code, byte offset) or ('ok', [(class, start, end)] in bytes)."""
    if len(data) > cfg["maxInputBytes"]:
        return ("error", "input-too-large", 0)
    bad = first_invalid_utf8(data)
    if bad is not None:
        return ("error", "invalid-utf8", bad)
    text = data.decode("utf-8")
    boff = [0]
    for ch in text:
        boff.append(boff[-1] + len(ch.encode("utf-8")))
    for i, ch in enumerate(text):
        if ch == "﻿":
            return ("error", "bom", boff[i])
        if ch == "\x00":
            return ("error", "nul", boff[i])
    r = pylex.lex(text, cfg["profile"], lexer)
    if r[0] == "error":
        return ("error", r[1], boff[r[2]])
    return ("ok", [(c, boff[a], boff[b]) for c, a, b in r[1]])


# ------------------------------------------------------------------ independent rule checks

def derive_layout(data, real):
    """Re-derive NEWLINE/INDENT/DEDENT (class, byte offset) from the input and the non-layout tokens."""
    n = len(data)

    def gap_line_ends(a, b):
        ends, i = [], a
        while i < b:
            c = data[i:i + 1]
            if c == b"#":
                while i < b and data[i:i + 1] not in (b"\n", b"\r"):
                    i += 1
                continue
            if c == b"\\":
                i += 1
                i += 2 if data[i:i + 2] == b"\r\n" else 1
                continue
            if c in (b"\n", b"\r"):
                ends.append(i)
                i += 2 if data[i:i + 2] == b"\r\n" else 1
                continue
            i += 1
        return ends

    def indentation(line_start):
        col = alt = 0
        i = line_start
        while i < n:
            c = data[i:i + 1]
            if c == b" ":
                col, alt = col + 1, alt + 1
            elif c == b"\t":
                col, alt = (col // 8 + 1) * 8, alt + 1
            elif c == b"\f":
                col = alt = 0
            elif c == b"\\":
                return col, alt
            else:
                break
            i += 1
        return col, alt

    out, depth, stack = [], 0, [(0, 0)]
    prev_end = 0
    for idx, t in enumerate(real + [None]):
        start = t["span"][0] if t else n
        ends = gap_line_ends(prev_end, start)
        if idx > 0 and depth == 0 and (ends or t is None):
            out.append(("newline", ends[0] if ends else n))
        if t is None:
            break
        if depth == 0 and (idx == 0 or ends):
            ls = (ends[-1] + (2 if data[ends[-1]:ends[-1] + 2] == b"\r\n" else 1)) if ends else 0
            col, alt = indentation(ls)
            if col > stack[-1][0]:
                require(alt > stack[-1][1], f"layout: inconsistent tabs at {start}")
                stack.append((col, alt))
                out.append(("indent", start))
            else:
                while col < stack[-1][0]:
                    stack.pop()
                    out.append(("dedent", start))
                require(col == stack[-1][0] and alt == stack[-1][1], f"layout: bad dedent at {start}")
        cls, txt = t["class"], t["text"]
        if cls == "punct" and txt in "([{":
            depth += 1
        elif cls == "punct" and txt in ")]}":
            depth -= 1
        elif cls in ("fstring-start", "tstring-start"):
            depth += 1
        elif cls in ("fstring-end", "tstring-end"):
            depth -= 1
        prev_end = t["span"][1]
    for _ in stack[1:]:
        out.append(("dedent", n))
    return out


def number_follow_ok(data, k, lit):
    if lit == b"0" and data[k:k + 1] in (b"b", b"B", b"o", b"O", b"x", b"X"):
        return False
    c = data[k:k + 1]
    if not c or not (c.isalnum() or c == b"_") or c[0] >= 128:
        return True
    if any(data.startswith(w, k) for w in (b"if", b"in", b"is")):
        return True
    for w in (b"and", b"else", b"for", b"not", b"or"):
        if data.startswith(w, k):
            e = data[k + len(w):k + len(w) + 1]
            return not e or not (e[0] >= 128 or e.isalnum() or e == b"_")
    return False


def stream_invariants(v, data):
    toks = v["result"]["tokens"]
    prev_end = 0
    for n, t in enumerate(toks):
        a, b = t["span"]
        cls, txt = t["class"], t["text"]
        require(cls in pylex.CLASSES, f"class {cls!r} not in the closed list")
        require(prev_end <= a <= b <= len(data), f"span {t['span']} out of order")
        require(data[a:b] == txt.encode("utf-8"), f"text != input[span] at {t['span']}")
        require((a == b) == (cls in LAYOUT), f"zero-width only for layout tokens ({cls} at {a})")
        prev_end = b
        nxt = toks[n + 1] if n + 1 < len(toks) else None
        if cls == "keyword":
            require(txt in KEYWORDS, f"{txt!r} is not one of the 35 keywords")
        if cls == "ident":
            require(txt not in KEYWORDS, f"keyword {txt!r} classed ident")
        if cls == "punct":
            require(txt in OPS, f"{txt!r} is not an operator or delimiter")
            for q in OPS:
                if len(q) > len(txt) and data.startswith(q.encode(), a):
                    require(txt == ":" and nxt is not None and nxt["class"] in MIDDLES,
                            f"{txt!r} at {a} is not the longest match ({q!r})")
        if cls in NUM_RX:
            require(NUM_RX[cls].fullmatch(txt) is not None, f"{txt!r} is not a {cls} literal")
            for other, rx in NUM_RX.items():
                m = rx.match(data.decode("utf-8", "replace"), len(data[:a].decode("utf-8")))
                require(not m or m.end() - len(data[:a].decode("utf-8")) <= len(txt),
                        f"{txt!r} at {a} is not the longest numeric literal")
            require(number_follow_ok(data, b, txt.encode()), f"{txt!r} at {a} is followed by a name character")
        if cls in STRINGISH:
            q = min(i for i in (txt.find("'"), txt.find('"')) if i >= 0)
            pre = txt[:q].lower()
            require(len(set(pre)) == len(pre) and set(pre) in ({*x} for x in ("", "b", "r", "u", "f", "t", "br",
                                                                               "fr", "tr")),
                    f"prefix {txt[:q]!r} is not valid")
            want = ("tstring-start" if "t" in pre else "fstring-start" if "f" in pre else
                    "bytes" if "b" in pre else "string")
            require(cls == want, f"{txt!r} classed {cls}, prefix says {want}")
            prev = toks[n - 1] if n else None
            if prev and prev["class"] in ("ident", "keyword") and prev["span"][1] == a:
                pw = prev["text"].lower()
                require(not (pw.isascii() and set(pw) <= set("brfut") and len(set(pw)) == len(pw) and q == 0),
                        f"{prev['text']!r} before a quote at {a} should have been a prefix (or an error)")
    real = [t for t in toks if t["class"] not in LAYOUT]
    want = derive_layout(data, real)
    got = [(t["class"], t["span"][0]) for t in toks if t["class"] in LAYOUT]
    require(got == want, f"layout tokens {got} differ from the re-derived {want}")


# ------------------------------------------------------------------ vector check

def check_vector(v, cfg, stats, lexer=pylex.Lexer):
    data = base64.b64decode(v["inputBase64"])
    if v.get("inputText") is not None:
        require(v["inputText"].encode("utf-8") == data, "inputText differs from inputBase64")
    exp = expected_result(data, cfg, lexer)
    r = v["result"]
    if exp[0] == "error":
        require(r["status"] == "error", f"expected error {exp[1]}@{exp[2]}, vector has {r['status']}")
        require(set(r) == {"status", "error"}, "error result carries extra fields")
        code, off = r["error"]["code"], r["error"]["offset"]
        require(code in pylex.ERROR_CODES, f"error code {code!r} not in the closed list")
        require((code, off) == exp[1:], f"error {code}@{off}, re-lex gives {exp[1]}@{exp[2]}")
        stats["errors"] += 1
        return
    require(r["status"] in ("ok", "insufficient-tokens"), f"re-lex accepts; vector has {r['status']}")
    stream_invariants(v, data)
    got = [(t["class"], t["span"][0], t["span"][1]) for t in r["tokens"]]
    if got != exp[1]:
        for i, (x, y) in enumerate(zip(got + [None] * len(exp[1]), exp[1] + [None] * len(got))):
            if x != y:
                raise CheckError(f"token {i}: vector {x}, re-lex {y}")
    require(r["tokenCount"] == len(r["tokens"]), "tokenCount")
    require(r["status"] == ("ok" if len(got) >= cfg["k"] else "insufficient-tokens"), "status vs k")
    require("tokenIndices" not in r["channels"]["normalized"] and "tokenIndices" not in r["channels"]["exact"],
            "tokenIndices emitted by a profile without normalizedExclusions (contract §6)")
    want = channels_for(r["tokens"], cfg)
    for ch in ("exact", "normalized"):
        require(list(r["channels"][ch]) == list(want[ch]), f"{ch}: keys or key order")
        for key, val in want[ch].items():
            require(r["channels"][ch][key] == val, f"{ch}.{key} differs from recomputation")
    if "empty-span" in v["tags"]:
        require(any(f["span"][0] == f["span"][1] for f in want["exact"]["fingerprints"]),
                "empty-span vector has no fingerprint with an empty span (profile §4.5)")
    stats["tokens"] += len(got)
    stats["layout"] += sum(1 for c, _, _ in got if c in LAYOUT)
    stats["kgrams"] += len(want["exact"]["kgrams"])
    stats["fingerprints"] += len(want["exact"]["fingerprints"]) + len(want["normalized"]["fingerprints"])
    for ch in ("exact", "normalized"):
        hs = [g["hash"] for g in want[ch]["kgrams"]]
        w = cfg["window"]
        for s in range(max(0, len(hs) - w + 1)):
            win = hs[s:s + w]
            if win.count(min(win)) > 1:
                stats["tie-windows"] += 1
    for t in r["tokens"]:
        stats["classes"].add(t["class"])


def hashes(r, ch):
    return [g["hash"] for g in r["channels"][ch]["kgrams"]]


def check_pairs(by_id):
    n = 0
    for kind, pairs in PAIRS.items():
        for a, b in pairs:
            if a not in by_id or b not in by_id:
                continue
            ra, rb = by_id[a]["result"], by_id[b]["result"]
            if kind in ("format", "reindent", "linejoin"):
                require([(t["class"], t["text"]) for t in ra["tokens"]] == [(t["class"], t["text"]) for t in rb["tokens"]],
                        f"{kind} pair {a}/{b}: token streams differ")
                require(hashes(ra, "exact") == hashes(rb, "exact"), f"{kind} pair {a}/{b}: exact hashes differ")
                require(hashes(ra, "normalized") == hashes(rb, "normalized"), f"{kind} pair: normalized differ")
            elif kind == "rename":
                require(hashes(ra, "normalized") == hashes(rb, "normalized"), f"rename pair {a}/{b}: normalized")
                require(hashes(ra, "exact") != hashes(rb, "exact"), f"rename pair {a}/{b}: exact hashes equal")
            elif kind == "semi":
                # Profile §7 (PYOD-4 (a)): no exclusions, so ';' layout is visible in both channels.
                require(hashes(ra, "normalized") != hashes(rb, "normalized"),
                        f"semi pair {a}/{b}: normalized hashes equal (an exclusion was applied)")
                require(hashes(ra, "exact") != hashes(rb, "exact"), f"semi pair {a}/{b}: exact hashes equal")
            n += 1
    return n


def run_file(doc, cfg, lexer=pylex.Lexer):
    stats = {"tokens": 0, "layout": 0, "kgrams": 0, "fingerprints": 0, "errors": 0, "tie-windows": 0,
             "classes": set()}
    by_id = {}
    for v in doc["vectors"]:
        require(v["id"] not in by_id, f"duplicate id {v['id']}")
        by_id[v["id"]] = v
        try:
            check_vector(v, cfg, stats, lexer)
        except CheckError as e:
            raise CheckError(f"{v['id']}: {e}")
    stats["pairs"] = check_pairs(by_id)
    for v in doc["vectors"]:
        require(v.get("derivation") == "hand", f"{v['id']}: derivation is not 'hand'")
        if v["result"]["status"] != "error":
            require("pairedRejection" in v, f"{v['id']}: no pairedRejection")
    return stats


def load(name):
    doc = json.loads((HERE / name).read_text(encoding="utf-8"))
    raw = (HERE / doc["configFile"]).read_bytes()
    cfg = validate_config(raw)
    require(hashlib.sha256(raw).hexdigest() == doc["configSha256"], f"{name}: config digest")
    require(cfg["profile"] == doc["profile"], f"{name}: profile")
    require(doc.get("normalizedExclusions") == EXCLUSIONS, f"{name}: normalizedExclusions differs from profile §7")
    return doc, cfg


# ------------------------------------------------------------------ mutation self-test

def toks_of(v):
    return v["result"]["tokens"]


def find(v, text, nth=0, cls=None):
    hits = [i for i, t in enumerate(toks_of(v)) if t["text"] == text and (cls is None or t["class"] == cls)]
    return hits[nth]


def zw(cls, at):
    return {"class": cls, "text": "", "span": [at, at]}


def mutations():
    out = []

    def add(vid, desc, rehash_=True):
        def deco(f):
            out.append(("py.json", vid, desc, f, rehash_))
            return f
        return deco

    @add("py-format-a", "final DEDENT dropped")
    def _(v):
        toks_of(v).pop()

    @add("py-dedent-position", "DEDENT placed at the line start, not at the first token")
    def _(v):
        i = find(v, "", 0, "dedent")
        toks_of(v)[i]["span"] = [toks_of(v)[i]["span"][0] - 4] * 2

    @add("py-newline-after-comment", "NEWLINE at the end of the last token, before the comment")
    def _(v):
        t = toks_of(v)
        t[3]["span"] = [t[2]["span"][1]] * 2

    @add("py-implicit-join", "NEWLINE emitted inside brackets")
    def _(v):
        t = toks_of(v)
        i = find(v, ",")
        t.insert(i + 1, zw("newline", t[i]["span"][1] + 0))
        t[i + 1]["span"] = [7, 7]

    @add("py-blank-comment-lines", "a comment-only line changes indentation (DEDENT, INDENT around it)")
    def _(v):
        t = toks_of(v)
        i = find(v, "b")
        at = t[i]["span"][0]
        t[i:i] = [zw("dedent", at), zw("indent", at)]

    @add("py-eof-dedent", "NEWLINE at end of input missing")
    def _(v):
        t = toks_of(v)
        del t[find(v, "", -1, "newline")]

    @add("py-cr-lines", "lone CR not a line terminator: first NEWLINE dropped")
    def _(v):
        t = toks_of(v)
        del t[find(v, "", 0, "newline")]

    @add("py-reindent-b", "tab level read as deeper: an extra INDENT/DEDENT pair")
    def _(v):
        t = toks_of(v)
        i = find(v, "w")
        at = t[i]["span"][0]
        t.insert(i, zw("indent", at))
        j = find(v, "", -1, "dedent")
        t.insert(j, zw("dedent", t[j]["span"][0]))

    @add("py-soft-keywords", "soft keyword 'match' classed keyword")
    def _(v):
        toks_of(v)[0]["class"] = "keyword"

    @add("py-keywords", "'None' classed ident")
    def _(v):
        toks_of(v)[find(v, "None")]["class"] = "ident"

    @add("py-unicode-names", "fullwidth 'if' classed keyword")
    def _(v):
        toks_of(v)[find(v, "ｉｆ")]["class"] = "keyword"

    @add("py-operators", "'**=' split into '**' '='")
    def _(v):
        t = toks_of(v)
        i = find(v, "**=")
        a = t[i]["span"][0]
        t[i:i + 1] = [{"class": "punct", "text": "**", "span": [a, a + 2]},
                      {"class": "punct", "text": "=", "span": [a + 2, a + 3]}]

    @add("py-operators", "'->' split into '-' '>'")
    def _(v):
        t = toks_of(v)
        i = find(v, "->")
        a = t[i]["span"][0]
        t[i:i + 1] = [{"class": "punct", "text": "-", "span": [a, a + 1]},
                      {"class": "punct", "text": ">", "span": [a + 1, a + 2]}]

    @add("py-ltgt", "'<>' merged into one token (CPython's tokenizer)")
    def _(v):
        t = toks_of(v)
        i = find(v, "<")
        a = t[i]["span"][0]
        t[i:i + 2] = [{"class": "punct", "text": "<>", "span": [a, a + 2]}]

    @add("py-dots", "'..' as one token")
    def _(v):
        t = toks_of(v)
        i = find(v, ".", 1)
        a = t[i]["span"][0]
        t[i:i + 2] = [{"class": "punct", "text": "..", "span": [a, a + 2]}]

    @add("py-numbers", "'0x_fF' classed float")
    def _(v):
        toks_of(v)[find(v, "0x_fF")]["class"] = "float"

    @add("py-numbers", "'09.5' split into '09' '.5'")
    def _(v):
        t = toks_of(v)
        i = find(v, "09.5")
        a = t[i]["span"][0]
        t[i:i + 1] = [{"class": "int", "text": "09", "span": [a, a + 2]},
                      {"class": "float", "text": ".5", "span": [a + 2, a + 4]}]

    @add("py-number-keyword", "'1if' read as one malformed number token")
    def _(v):
        t = toks_of(v)
        i = find(v, "1")
        a = t[i]["span"][0]
        t[i:i + 2] = [{"class": "int", "text": "1if", "span": [a, a + 3]}]

    @add("py-string-prefixes", "b'w' classed string")
    def _(v):
        toks_of(v)[find(v, "b'w'")]["class"] = "string"

    @add("py-prefix-ident", "'uu' + 'x' merged as a prefixed string")
    def _(v):
        t = toks_of(v)
        t[0:2] = [{"class": "string", "text": "uu'x'", "span": [0, 5]}]

    @add("py-fstring-basic", "the whole f-string as one string token")
    def _(v):
        t = toks_of(v)
        e = find(v, "'", 0, "fstring-end")
        end = t[e]["span"][1]
        t[0:e + 1] = [{"class": "string", "text": "f'a{x!r:>{w}}b{{c}}'", "span": [0, end]}]

    @add("py-fstring-basic", "'{{c}}' split into separate middle tokens")
    def _(v):
        t = toks_of(v)
        i = find(v, "b{{c}}")
        a = t[i]["span"][0]
        t[i:i + 1] = [{"class": "fstring-middle", "text": "b{{", "span": [a, a + 3]},
                      {"class": "fstring-middle", "text": "c}}", "span": [a + 3, a + 6]}]

    @add("py-fstring-debug-walrus", "':=' taken by longest match inside a field")
    def _(v):
        t = toks_of(v)
        i = find(v, "=10")
        a = t[i - 1]["span"][0]
        t[i - 1:i + 1] = [{"class": "punct", "text": ":=", "span": [a, a + 2]},
                          {"class": "int", "text": "10", "span": [a + 2, a + 4]}]

    @add("py-tstring", "t-string start classed fstring-start")
    def _(v):
        toks_of(v)[0]["class"] = "fstring-start"

    @add("py-err-tab-vs-spaces", "TabError reported as unmatched-dedent")
    def _(v):
        v["result"]["error"]["code"] = "unmatched-dedent"

    @add("py-err-unclosed", "unclosed bracket reported at the outer opener")
    def _(v):
        v["result"]["error"]["offset"] = 4

    @add("py-err-dollar", "invented error code")
    def _(v):
        v["result"]["error"]["code"] = "syntax-error"

    @add("py-err-fstring-expr-unclosed", "error at the f-string start instead of the inner quote")
    def _(v):
        v["result"]["error"]["offset"] = 0

    @add("py-repeated", "winnowing tie broken leftmost", rehash_=False)
    def _(v):
        ch = v["result"]["channels"]["exact"]
        hs = [int(g["hash"], 16) for g in ch["kgrams"]]
        sel = [min(range(s, s + 4), key=lambda j: (hs[j], j)) for s in range(len(hs) - 3)]
        ch["windowSelections"] = sel
        ch["fingerprints"] = [ch["kgrams"][p] for p in sorted(set(sel))]

    @add("py-format-a", "hash corrupted", rehash_=False)
    def _(v):
        g = v["result"]["channels"]["exact"]["kgrams"][0]
        g["hash"] = "%016x" % (int(g["hash"], 16) ^ 1)

    @add("py-semi-a", "normalized channel drops ';' (an exclusion this profile does not declare)", rehash_=False)
    def _(v):
        ch = v["result"]["channels"]["normalized"]
        ch["values"] = [x for x in ch["values"] if x != ";"]

    @add("py-short", "tokenIndices emitted on the normalized channel", rehash_=False)
    def _(v):
        ch = v["result"]["channels"]["normalized"]
        v["result"]["channels"]["normalized"] = {"tokenIndices": list(range(len(ch["values"]))), **ch}

    return out


NON_LEXICAL = {"winnowing tie broken leftmost", "hash corrupted",
               "normalized channel drops ';' (an exclusion this profile does not declare)",
               "tokenIndices emitted on the normalized channel"}


def self_test(docs):
    rejected, failures = 0, []
    for f, vid, desc, fn, do_rehash in mutations():
        doc, cfg = copy.deepcopy(docs[f][0]), docs[f][1]
        v = next(x for x in doc["vectors"] if x["id"] == vid)
        fn(v)
        if do_rehash:
            rehash(v, cfg)
        try:
            run_file(doc, cfg)
        except CheckError:
            rejected += 1
            continue
        failures.append(desc)
    return rejected, failures


# ------------------------------------------------------------------ wrong-lexer self-test

class WTab4(pylex.Lexer):
    """Tabs advance to the next multiple of 4, not 8."""
    def tab_stop(self, col):
        return (col // 4 + 1) * 4


class WNoTabCheck(pylex.Lexer):
    """No tab-size-1 consistency check (no TabError)."""
    def check_tab_consistency(self):
        return False


class WNoEOFDedent(pylex.Lexer):
    """DEDENT tokens at end of input missing."""
    def dedents_at_eof(self):
        return False


class WBlankComment(pylex.Lexer):
    """Comment-only lines take part in indentation (only empty lines are blank)."""
    def blank_line_starts(self, j):
        return j >= self.n or self.line_terminator_len(j) > 0


class WBracketNewline(pylex.Lexer):
    """Implicit joining inside brackets does not suppress NEWLINE."""
    def joins_implicitly(self):
        return bool(self.stack) and self.stack[-1]["kind"] == "field"


class WFStringPlain(pylex.Lexer):
    """f- and t-strings lexed as plain strings."""
    def recognizes_ftstrings(self):
        return False


class WSoftKeywords(pylex.Lexer):
    """Soft keywords match, case, type, _ classed keyword."""
    def keyword_set(self):
        return pylex.KEYWORDS | pylex.SOFT_KEYWORDS


class WRawBackslash(pylex.Lexer):
    """In raw strings a backslash does not take the next character."""
    def backslash_escapes_in_raw(self):
        return False


class WLoneCR(pylex.Lexer):
    """A lone CR does not end a line (it is ordinary white space)."""
    def line_terminator_len(self, i):
        if i < self.n and self.s[i] == "\r" and not (i + 1 < self.n and self.s[i + 1] == "\n"):
            return 0
        return super().line_terminator_len(i)

    def whitespace(self, c):
        return c in " \t\f"

    def run(self):
        self.s = self.s.replace("\r\n", "\x01\x02")  # keep CR LF intact while lone CR becomes white space
        self.s = self.s.replace("\r", " ").replace("\x01\x02", "\r\n")
        return super().run()


class WCRLFTwo(pylex.Lexer):
    """CR LF counted as two line terminators."""
    def line_terminator_len(self, i):
        return 1 if i < self.n and self.s[i] in "\r\n" else 0


class WFormFeedIgnored(pylex.Lexer):
    """A form feed in leading white space counts as one column."""
    def formfeed_in_indent(self, col, alt):
        return col + 1, alt + 1


class WBackslashIndentCPython(pylex.Lexer):
    """CPython 3.14.6's quirk: a continuation at column 0 lets the next line's spaces count."""
    def continuation_indent(self, cont, col, alt):
        if cont is None or cont[0] == 0:
            return col, alt
        return cont[0], cont[0]


class WSpecEscapes(pylex.Lexer):
    """'{{' and '}}' are escapes inside a format spec too."""
    def spec_brace_escapes(self):
        return True


class WNumberStrict(pylex.Lexer):
    """No keyword exception: any name character after a number is an error ('1if' rejected)."""
    def number_follow_ok(self, s, k, i):
        c = s[k] if k < self.n else ""
        return not (c.isascii() and (c.isalnum() or c == "_"))


class WNumberWordsAsPrefixes(pylex.Lexer):
    """All exception words matched as prefixes ('1orx' accepted)."""
    def number_follow_ok(self, s, k, i):
        if super().number_follow_ok(s, k, i):
            return True
        if k == i + 1 and s[i] == "0" and k < self.n and s[k] in "bBoOxX":
            return False
        return any(s.startswith(w, k) for w in pylex.NUMBER_FOLLOW_WORDS)


class WLegacyOctal(pylex.Lexer):
    """Leading-zero decimal integers ('0777') accepted."""
    def number_at(self, s, i):
        cls, n = super().number_at(s, i)
        m = re.compile(r"0[0-9]+").match(s, i)
        return ("int", m.end() - i) if m and m.end() - i > n else (cls, n)


class WRadixKeyword(pylex.Lexer):
    """'0or' read as 0 then 'or' (no radix-prefix check)."""
    def number_follow_ok(self, s, k, i):
        return super().number_follow_ok(s, k, k)


class WPrefixLoose(pylex.Lexer):
    """Incompatible prefix pairs ('ur', 'bf') accepted as strings."""
    def prefix_kind(self, word):
        k = super().prefix_kind(word)
        return frozenset(word.lower()) if k == "bad" else k


class WPrefixCaseSensitive(pylex.Lexer):
    """Only lowercase prefix letters recognized."""
    def prefix_kind(self, word):
        return super().prefix_kind(word) if word.islower() else None


class WNamedEscapeRaw(pylex.Lexer):
    """'\\N{' treated as a named escape in raw f-strings too."""
    def named_escape_applies(self, raw):
        return True


class WDedentAtLineStart(pylex.Lexer):
    """INDENT/DEDENT placed at the start of the physical line."""
    def layout_position(self, line_start, first):
        return line_start


class WNewlineAtTokenEnd(pylex.Lexer):
    """NEWLINE placed at the end of the line's last token (Go-style)."""
    def newline_position(self, terminator, last_end):
        return last_end


class WPythonUnicode(pylex.Lexer):
    """Identifier classes from the running interpreter (Unicode 16.0.0), not the pinned 17.0.0 tables."""
    def name_start(self, c):
        return c.isidentifier()

    def name_continue(self, c):
        return ("a" + c).isidentifier()


class WColonLongest(pylex.Lexer):
    """Inside a field, ':=' wins by longest match over the format-spec ':'."""
    def colon_starts_spec_first(self):
        return False


class WDedentNoAlt(pylex.Lexer):
    """Review W03: no tab-size-1 check after a dedent."""
    def dedent_checks_alt(self):
        return False


class WNonAsciiAfterNumber(pylex.Lexer):
    """Review W12: a non-ASCII character after a number is malformed."""
    def number_follow_ok(self, s, k, i):
        if k < self.n and ord(s[k]) >= 128:
            return False
        return super().number_follow_ok(s, k, i)


class WSpecQuoteEnds(pylex.Lexer):
    """Review W15: the closing quote inside a format spec ends the f-string (CPython's tokenizer)."""
    def spec_closing_quote_is_error(self):
        return False


class WNamedEscapeBraceText(pylex.Lexer):
    """Review W17: inside '\\N{...}' a '{' is text."""
    def brace_in_named_escape_opens_field(self):
        return False


class WEofAtFieldBrace(pylex.Lexer):
    """Review W19: end of input in a field reported at the field's '{'."""
    def eof_in_field_offset(self, field):
        return field["pos"]


WRONG_LEXERS = [WTab4, WNoTabCheck, WNoEOFDedent, WBlankComment, WBracketNewline, WFStringPlain, WSoftKeywords,
                WRawBackslash, WLoneCR, WCRLFTwo, WFormFeedIgnored, WBackslashIndentCPython, WSpecEscapes,
                WNumberStrict, WNumberWordsAsPrefixes, WLegacyOctal, WRadixKeyword, WPrefixLoose,
                WPrefixCaseSensitive, WNamedEscapeRaw, WDedentAtLineStart, WNewlineAtTokenEnd, WPythonUnicode,
                WColonLongest, WDedentNoAlt, WNonAsciiAfterNumber, WSpecQuoteEnds, WNamedEscapeBraceText,
                WEofAtFieldBrace]


def wrong_lexer_test(docs):
    """Each variant must fail on at least one shipped vector; returns every vector that rejects it."""
    rejected, failures, where = 0, [], {}
    for cls in WRONG_LEXERS:
        hits = []
        for name, (doc, cfg) in docs.items():
            for v in doc["vectors"]:
                st = {"tokens": 0, "layout": 0, "kgrams": 0, "fingerprints": 0, "errors": 0, "tie-windows": 0,
                      "classes": set()}
                try:
                    check_vector(v, cfg, st, cls)
                except CheckError:
                    hits.append(v["id"])
        if hits:
            rejected += 1
            where[cls.__name__] = hits
        else:
            failures.append(f"{cls.__name__}: {cls.__doc__}")
    return rejected, failures, where


def check_paired(docs):
    errors = {v["id"] for d, _ in docs.values() for v in d["vectors"] if v["result"]["status"] == "error"}
    for d, _ in docs.values():
        for v in d["vectors"]:
            if "pairedRejection" in v:
                require(v["pairedRejection"] in errors, f"{v['id']}: pairedRejection {v['pairedRejection']} "
                                                        "is not an error vector")


def main():
    neg, total = check_negative_configs()
    print(f"PASS config-negative-python.json: {neg}/{total} invalid configurations rejected")
    docs = {}
    for name in FILES:
        doc, cfg = load(name)
        docs[name] = (doc, cfg)
        st = run_file(doc, cfg)
        print(f"PASS {name} profile={cfg['profile']}/{cfg['profileVersion']} config={doc['configSha256'][:16]}... "
              f"vectors={len(doc['vectors'])} tokens={st['tokens']} (layout {st['layout']}) kgrams={st['kgrams']} "
              f"fingerprints={st['fingerprints']} tie-windows={st['tie-windows']} errors={st['errors']} "
              f"(code and offset re-derived) pairs={st['pairs']} classes={len(st['classes'])}")
    check_paired(docs)
    print("PASS every accepted vector has derivation=hand and a pairedRejection that is an error vector")
    rejected, failures = self_test(docs)
    total = rejected + len(failures)
    lexical = sum(1 for m in mutations() if m[2] not in NON_LEXICAL)
    for d in failures:
        print(f"FAIL mutation not rejected: {d}")
    if failures:
        sys.exit(1)
    print(f"PASS mutation self-test: {rejected}/{total} corruptions rejected ({lexical} lexical)")
    wr, wf, where = wrong_lexer_test(docs)
    for d in wf:
        print(f"FAIL wrong lexer accepted: {d}")
    if wf:
        sys.exit(1)
    print(f"PASS wrong-lexer self-test: {wr}/{len(WRONG_LEXERS)} wrong lexers rejected")
    if "-v" in sys.argv:
        for k, v in where.items():
            print(f"  {k:24} rejected by {len(v)}: {' '.join(v)}")


if __name__ == "__main__":
    try:
        main()
    except CheckError as e:
        print(f"FAIL {e}")
        sys.exit(1)
