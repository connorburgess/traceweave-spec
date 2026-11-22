#!/usr/bin/env python3
"""Independent checker for the draft token-fingerprint extraction vectors.

Standard library only. For every vector file it checks:

* configuration bytes against the contract's validation rules (section 10),
  and that every negative configuration in config-negative.json is rejected;
* encoding-level rejections (size, UTF-8, BOM, NUL, isolated CR), recomputed
  from the input bytes;
* the closed error-code list per profile, and offset plausibility for lexical
  errors (the character at the offset can start the failing construct);
* lexical invariants of every recorded token stream, using the pinned Unicode
  17.0.0 tables (unicode-17.0.0-tables.json):
  - Go: identifier characters and maximal munch, keyword classes, operator
    longest match, the numeric candidate scan and literal productions,
    semicolon insertion recomputed from the gaps between tokens;
  - Rust: XID identifier characters, NFC, keyword/raw-identifier classes,
    reserved prefixes, single-character punctuation, lifetimes, the numeric
    scan, literal prefixes and the literal-suffix cut;
  - every gap between tokens is whitespace, comments or a Rust shebang;
* normalization, k-gram bytes, SHA-256-derived hashes, winnowing, spans and
  the pair invariants;
* mutation self-tests: corrupted copies (hashes recomputed so that only the
  lexical layer is wrong) must be rejected.

It is not a lexer: it validates a given token stream rather than producing
one, and lexical error offsets are only checked for plausibility. The
toolchain comparison lives in harness/crosscheck.py.

Usage: python3 check_vectors.py [vector-file ...]
"""

from __future__ import annotations

import base64
import bisect
import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FILES = ["go.json", "rust.json", "limits-go.json", "limits-rust.json"]
TABLES_FILE = "unicode-17.0.0-tables.json"
TABLES_SHA256 = "9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f"
DOMAIN = b"traceweave/token-kgram/draft-1"
CONTRACT = "traceweave-token-winnow-draft-1"
HASH_ID = "sha256-first8-u64be"
CONFIG_KEYS = ["contract", "profile", "profileVersion", "channels", "k", "window", "hash", "maxInputBytes"]
UINT32_MAX = 2**32 - 1
VALUE_RE = re.compile(r"[a-z0-9.-]+")

COMMON_CODES = {"invalid-utf8", "bom", "nul", "input-too-large", "illegal-character",
                "unterminated-comment", "unterminated-literal", "malformed-literal"}
ENCODING_CODES = {"invalid-utf8", "bom", "nul", "isolated-cr", "input-too-large"}

GO_KEYWORDS = set("break case chan const continue default defer else fallthrough for func go goto if import "
                  "interface map package range return select struct switch type var".split())
GO_OPS = set("+ & += &= && == != ( ) - | -= |= || < <= [ ] * ^ *= ^= <- > >= { } / << /= <<= ++ = := , ; % "
             ">> %= >>= -- ! ... . : &^ &^= ~".split())
GO_TRIGGER_KEYWORDS = {"break", "continue", "fallthrough", "return"}
GO_TRIGGER_OPS = {"++", "--", ")", "]", "}"}
RUST_KEYWORDS = set("_ as async await break const continue crate dyn else enum extern false fn for if impl in let "
                    "loop match mod move mut pub ref return self Self static struct super trait true type unsafe "
                    "use where while abstract become box do final gen macro override priv try typeof unsized "
                    "virtual yield".split())
RUST_RESERVED_RAW = {"_", "crate", "self", "Self", "super"}
RUST_PUNCT = set("!#$%&()*+,-./:;<=>?@[]^{|}~")

PROFILES = {
    ("go-tokens", "draft-1"): {
        "lang": "go",
        "codes": COMMON_CODES,
        "literals": {"int", "float", "imag", "rune", "string"},
        "other": {"keyword", "ident", "punct"},
        "whitespace": set(" \t\r\n"),
        "nested": False,
    },
    ("rust2024-tokens", "draft-1"): {
        "lang": "rust",
        "codes": COMMON_CODES | {"isolated-cr", "reserved-token", "unbalanced-delimiter",
                                 "non-nfc-identifier", "malformed-identifier"},
        "literals": {"int", "float", "char", "byte", "string", "rawstring", "bytestring",
                     "rawbytestring", "cstring", "rawcstring"},
        "other": {"keyword", "ident", "punct", "lifetime"},
        "whitespace": set("\t\n\v\f\r \u0085‎‏  "),
        "nested": True,
    },
}
STAT_KEYS = ("tokens", "inserted", "kgrams", "fingerprints", "errors", "lexical-offsets-plausibility-only",
             "tie-windows", "identifiers")


class CheckError(Exception):
    pass


def require(cond, msg):
    if not cond:
        raise CheckError(msg)


# ---------------------------------------------------------------- Unicode tables

class Tables:
    def __init__(self, path: Path):
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == TABLES_SHA256, f"{path.name}: SHA-256 differs from the pinned value")
        data = json.loads(raw)
        require(data["unicodeVersion"] == "17.0.0", "tables must be Unicode 17.0.0")
        self.sets = {}
        for name, ranges in list(data["properties"].items()) + [("assigned", data["assigned"])]:
            self.sets[name] = ([a for a, _ in ranges], [b for _, b in ranges])

    def has(self, name, ch):
        starts, ends = self.sets[name]
        cp = ord(ch)
        i = bisect.bisect_right(starts, cp) - 1
        return i >= 0 and cp <= ends[i]


TABLES: Tables | None = None


def go_letter(c):
    return TABLES.has("go_letter", c)


def go_digit(c):
    return TABLES.has("go_digit", c)


def xid_start(c):
    return TABLES.has("xid_start", c)


def xid_continue(c):
    return TABLES.has("xid_continue", c)


def nfc_ok(name):
    """NFC check with Python's unicodedata, valid only for characters assigned in both versions.

    Normalization stability: NFC of a string of characters assigned in Unicode
    16.0 is unchanged in 17.0, so a 16.0 implementation answers correctly for
    them. Characters new in 17.0 cannot be checked here and fail loudly.
    """
    for c in name:
        require(TABLES.has("assigned", c), f"U+{ord(c):04X} unassigned in Unicode 17.0.0")
        require(unicodedata.category(c) != "Cn",
                f"U+{ord(c):04X} is new in 17.0; Python unicodedata {unicodedata.unidata_version} cannot verify NFC")
    return unicodedata.is_normalized("NFC", name)


# ---------------------------------------------------------------- configuration

def validate_config(raw: bytes):
    """Contract section 10. Returns the parsed configuration or raises CheckError(reason)."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise CheckError("not UTF-8") from None
    require(text.endswith("\n") and "\n" not in text[:-1] and "\r" not in text, "must be one line ending in LF")

    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, f"duplicate key {k}")
            out[k] = v
        return out

    def no_float(s):
        raise CheckError(f"non-integer number {s}")

    def no_const(s):
        raise CheckError(f"invalid constant {s}")

    try:
        cfg = json.loads(text, object_pairs_hook=pairs, parse_float=no_float, parse_constant=no_const)
    except ValueError as exc:
        raise CheckError(f"not JSON ({exc})") from None
    require(isinstance(cfg, dict) and list(cfg) == CONFIG_KEYS, f"keys must be exactly {CONFIG_KEYS} in order")
    for key in ("contract", "profile", "profileVersion", "hash"):
        require(isinstance(cfg[key], str) and VALUE_RE.fullmatch(cfg[key]), f"{key} must match [a-z0-9.-]+")
    for key in ("k", "window", "maxInputBytes"):
        v = cfg[key]
        require(type(v) is int and 1 <= v <= UINT32_MAX, f"{key} must be an integer in 1..2^32-1")
    require(cfg["channels"] == ["exact", "normalized"], "channels must be [\"exact\",\"normalized\"]")
    require(cfg["contract"] == CONTRACT, "unknown contract")
    require((cfg["profile"], cfg["profileVersion"]) in PROFILES, "unknown profile/version")
    require(cfg["hash"] == HASH_ID, "unknown hash")
    canonical = (json.dumps(cfg, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
    require(raw == canonical, "bytes differ from the canonical serialization")
    return cfg


def check_negative_configs(path: Path):
    data = strict_json(path)
    for item in data["negatives"]:
        raw = base64.b64decode(item["configBase64"], validate=True)
        try:
            validate_config(raw)
        except CheckError:
            continue
        raise CheckError(f"{path.name}:{item['id']}: accepted, must be rejected ({item['reason']})")
    return len(data["negatives"])


def strict_json(path):
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, f"{path.name}: duplicate key {k}")
            out[k] = v
        return out
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


# ---------------------------------------------------------------- hashing and winnowing

def lp(b: bytes) -> bytes:
    return len(b).to_bytes(4, "big") + b


def hash_kgram(cfg, channel, pairs) -> str:
    buf = bytearray(lp(DOMAIN) + lp(cfg["profile"].encode()) + lp(cfg["profileVersion"].encode())
                    + lp(channel.encode()) + cfg["k"].to_bytes(4, "big"))
    for cls, value in pairs:
        buf += lp(cls.encode("utf-8")) + lp(value.encode("utf-8"))
    return hashlib.sha256(bytes(buf)).digest()[:8].hex()


def normalized_value(spec, cls, text):
    if cls == "ident" or cls in spec["literals"]:
        return ""
    if cls == "lifetime" and text not in ("'static", "'_"):
        return ""
    return text


def select(hashes, window):
    """Per-window selections, sort-based (rightmost minimum wins), and the partial flag."""
    m = len(hashes)
    if m == 0:
        return [], False
    spans = [(0, m)] if m < window else [(s, s + window) for s in range(m - window + 1)]
    return [sorted(range(lo, hi), key=lambda j: (hashes[j], -j))[0] for lo, hi in spans], m < window


def rebuild_channels(result, cfg, spec):
    """Recompute k-grams and fingerprints from tokens (used only to build mutations)."""
    tokens, k, w = result["tokens"], cfg["k"], cfg["window"]
    result["tokenCount"] = len(tokens)
    result["status"] = "ok" if len(tokens) >= k else "insufficient-tokens"
    for channel in ("exact", "normalized"):
        values = [t["text"] if channel == "exact" else normalized_value(spec, t["class"], t["text"]) for t in tokens]
        pairs = [(t["class"], v) for t, v in zip(tokens, values)]
        kg = [{"position": i, "hash": hash_kgram(cfg, channel, pairs[i:i + k]),
               "span": [tokens[i]["span"][0], tokens[i + k - 1]["span"][1]]} for i in range(max(0, len(tokens) - k + 1))]
        picks, partial = select([int(g["hash"], 16) for g in kg], w)
        ch = {"values": values} if channel == "normalized" else {}
        ch.update({"kgrams": kg, "windowSelections": picks, "partialWindow": partial,
                   "fingerprints": [{"position": p, "hash": kg[p]["hash"], "span": kg[p]["span"]} for p in sorted(set(picks))]})
        result["channels"][channel] = ch


# ---------------------------------------------------------------- encoding layer

def first_invalid_utf8(data: bytes):
    try:
        data.decode("utf-8", errors="strict")
        return None
    except UnicodeDecodeError as exc:
        return exc.start


def first_forbidden(text: str, lang: str):
    offset = 0
    for i, ch in enumerate(text):
        if ch == "﻿":
            return offset, "bom"
        if ch == "\x00":
            return offset, "nul"
        if lang == "rust" and ch == "\r" and text[i + 1:i + 2] != "\n":
            return offset, "isolated-cr"
        offset += len(ch.encode("utf-8"))
    return None


# ---------------------------------------------------------------- trivia

def skip_block(text, i, nested):
    """End index of the block comment starting at i, or None if unterminated."""
    depth, j = 1, i + 2
    while j < len(text):
        if nested and text.startswith("/*", j):
            depth += 1
            j += 2
        elif text.startswith("*/", j):
            depth -= 1
            j += 2
            if depth == 0:
                return j
        else:
            j += 1
    return None


def rust_shebang_end(text):
    """End (exclusive) of a Rust shebang at offset 0, or None. Unterminated comments count as comment."""
    if not text.startswith("#!"):
        return None
    ws = PROFILES[("rust2024-tokens", "draft-1")]["whitespace"]
    j = 2
    while j < len(text):
        if text[j] in ws:
            j += 1
        elif text.startswith("//", j):
            nl = text.find("\n", j)
            j = len(text) if nl < 0 else nl
        elif text.startswith("/*", j):
            end = skip_block(text, j, True)
            j = len(text) if end is None else end
        else:
            break
    if text.startswith("[", j):
        return None
    nl = text.find("\n")
    return len(text) if nl < 0 else nl + 1


def scan_trivia(text, start, end, spec, at_file_start):
    """Require text[start:end] to be trivia. Returns True if it acts as a newline (Go rules)."""
    i, newline = start, False
    if at_file_start and spec["lang"] == "rust":
        sb = rust_shebang_end(text)
        if sb is not None:
            require(sb <= end, "shebang overlaps a token")
            i = sb
    while i < end:
        if text[i] in spec["whitespace"]:
            newline |= text[i] == "\n"
            i += 1
        elif text.startswith("//", i):
            nl = text.find("\n", i)
            i = len(text) if nl < 0 else nl
            newline = True
        elif text.startswith("/*", i):
            j = skip_block(text, i, spec["nested"])
            require(j is not None, f"unterminated comment in gap at char {i}")
            newline |= "\n" in text[i:j]
            i = j
        else:
            raise CheckError(f"non-trivia character {text[i]!r} between tokens at char {i}")
    require(i == end, f"comment extends into a token at char {end}")
    return newline


# ---------------------------------------------------------------- Go lexical checks

_dd = r"[0-9](?:_?[0-9])*"
_hd = r"[0-9a-fA-F](?:_?[0-9a-fA-F])*"
_int = r"(?:0|[1-9](?:_?" + _dd + r")?|0[bB]_?[01](?:_?[01])*|0[oO]?_?[0-7](?:_?[0-7])*|0[xX]_?" + _hd + ")"
_dexp = r"[eE][+-]?" + _dd
_dfl = r"(?:" + _dd + r"\.(?:" + _dd + r")?(?:" + _dexp + r")?|" + _dd + _dexp + r"|\." + _dd + r"(?:" + _dexp + r")?)"
_hfl = r"0[xX](?:_?" + _hd + r"\.(?:" + _hd + r")?|_?" + _hd + r"|\." + _hd + r")[pP][+-]?" + _dd
GO_INT, GO_FLOAT = re.compile(_int), re.compile(r"(?:" + _dfl + "|" + _hfl + ")")
GO_IMAG = re.compile(r"(?:" + _dd + "|" + _int + "|" + _dfl + "|" + _hfl + ")i")


def go_number_candidate(text, i):
    """Contract section 4.4 candidate scan; returns the end index."""
    j, base = i, 10
    if text.startswith(("0x", "0X"), j):
        base, j = 16, j + 2
    elif text.startswith(("0b", "0B", "0o", "0O"), j):
        j += 2
    run = "0123456789abcdefABCDEF_" if base == 16 else "0123456789_"
    if text[i] != ".":
        while j < len(text) and text[j] in run:
            j += 1
    if j < len(text) and text[j] == ".":
        j += 1
        while j < len(text) and text[j] in run:
            j += 1
    if j < len(text) and text[j] in "eEpP":
        j += 1
        if j < len(text) and text[j] in "+-":
            j += 1
        while j < len(text) and text[j] in "0123456789_":
            j += 1
    if j < len(text) and text[j] == "i":
        j += 1
    return j


def go_longest_op(text, i):
    return max((op for op in GO_OPS if text.startswith(op, i)), key=len, default=None)


def check_go_token(t, text, ci, ce):
    cls, s = t["class"], t["text"]
    nxt = text[ce] if ce < len(text) else ""
    if cls in ("ident", "keyword"):
        require(go_letter(s[0]) and all(go_letter(c) or go_digit(c) for c in s[1:]), f"{s!r}: not a Go identifier")
        require(not nxt or not (go_letter(nxt) or go_digit(nxt)), f"{s!r}: identifier not maximal")
        require((cls == "keyword") == (s in GO_KEYWORDS), f"{s!r}: class must be {'keyword' if s in GO_KEYWORDS else 'ident'}")
    elif cls == "punct":
        require(s in GO_OPS and go_longest_op(text, ci) == s, f"{s!r}: not the longest operator at char {ci}")
    elif cls in ("int", "float", "imag"):
        require(go_number_candidate(text, ci) == ce, f"{s!r}: numeric candidate scan gives a different extent")
        want = "int" if GO_INT.fullmatch(s) else "float" if GO_FLOAT.fullmatch(s) else "imag" if GO_IMAG.fullmatch(s) else None
        require(want == cls, f"{s!r}: literal class {cls}, productions say {want}")
    elif cls == "rune":
        require(len(s) >= 3 and s[0] == s[-1] == "'", f"{s!r}: rune delimiters")
    elif cls == "string":
        require(len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "`")), f"{s!r}: string delimiters")


def go_triggers(t):
    c = t["class"]
    return (c == "ident" or c in ("int", "float", "imag", "rune", "string")
            or (c == "keyword" and t["text"] in GO_TRIGGER_KEYWORDS) or (c == "punct" and t["text"] in GO_TRIGGER_OPS))


# ---------------------------------------------------------------- Rust lexical checks

def rust_ident_ok(name):
    return bool(name) and (xid_start(name[0]) or name[0] == "_") and all(xid_continue(c) for c in name[1:])


def rust_number(text, i):
    """Contract section 5.4 scan. Returns (end, class)."""
    j = i
    def run(chars):
        nonlocal j
        while j < len(text) and text[j] in chars:
            j += 1
    if text.startswith(("0b", "0o", "0x"), j):
        radix = text[j + 1]
        j += 2
        start = j
        run("0123456789abcdefABCDEF_" if radix == "x" else "0123456789_")
        digits = {"b": "01", "o": "01234567", "x": "0123456789abcdefABCDEF"}[radix]
        body = text[start:j].replace("_", "")
        require(body and all(c in digits for c in body), "prefixed literal digits")
        cls = "int"
    else:
        run("0123456789_")
        cls = "int"
        if j < len(text) and text[j] == "." and not (j + 1 < len(text) and (text[j + 1] in "._" or xid_start(text[j + 1]))):
            j += 1
            cls = "float"
            if j < len(text) and text[j].isascii() and text[j].isdigit():
                run("0123456789_")
            else:
                return j, cls
        if j < len(text) and text[j] in "eE":
            j += 1
            if j < len(text) and text[j] in "+-":
                j += 1
            start = j
            run("0123456789_")
            require(any(c.isdigit() for c in text[start:j]), "exponent without digits")
            cls = "float"
    return rust_suffix_end(text, j), cls


def rust_suffix_end(text, j):
    """SUFFIX -> '_' ^ XID_Continue+ | XID_Start XID_Continue*. '_' without XID_Continue after it is an error."""
    if j < len(text) and text[j] == "_":
        require(j + 1 < len(text) and xid_continue(text[j + 1]), "'_' suffix cut: no XID_Continue follows")
        j += 1
    elif not (j < len(text) and xid_start(text[j])):
        return j
    while j < len(text) and xid_continue(text[j]):
        j += 1
    return j


RUST_PREFIX = [("br", "rawbytestring"), ("cr", "rawcstring"), ("r", "rawstring"), ("b'", "byte"),
               ("b\"", "bytestring"), ("c\"", "cstring"), ("'", "char"), ("\"", "string")]


def check_rust_token(t, text, ci, ce):
    cls, s = t["class"], t["text"]
    nxt = text[ce] if ce < len(text) else ""
    if cls in ("ident", "keyword"):
        raw = s.startswith("r#") and len(s) > 2
        name = s[2:] if raw else s
        require(rust_ident_ok(name), f"{s!r}: not an XID identifier")
        require("‌" not in name and "‍" not in name, f"{s!r}: zero-width joiner in identifier")
        require(nfc_ok(name), f"{s!r}: identifier not NFC")
        require(not nxt or not xid_continue(nxt), f"{s!r}: identifier not maximal")
        if raw:
            require(cls == "ident" and name not in RUST_RESERVED_RAW, f"{s!r}: raw identifier class/reserved name")
        else:
            require((cls == "keyword") == (name in RUST_KEYWORDS), f"{s!r}: class must be {'keyword' if name in RUST_KEYWORDS else 'ident'}")
            require(nxt not in ("\"", "'", "#") or not nxt, f"{s!r}: reserved prefix (identifier followed by {nxt!r})")
            require(s not in ("r", "br", "cr", "b", "c") or nxt not in ("\"", "'", "#"), f"{s!r}: should start a literal")
    elif cls == "punct":
        require(len(s) == 1 and s in RUST_PUNCT, f"{s!r}: Rust punctuation is single characters")
        require(not (s == "#" and nxt in ("#", "\"")), "reserved '#' form")
    elif cls == "lifetime":
        body = s[1:]
        raw = body.startswith("r#")
        name = body[2:] if raw else body
        require(s[0] == "'" and rust_ident_ok(name) and nfc_ok(name), f"{s!r}: lifetime name")
        require(nxt != "'" and (not nxt or not xid_continue(nxt)), f"{s!r}: lifetime not maximal or is a char")
        require(not raw or name not in RUST_RESERVED_RAW, f"{s!r}: reserved raw lifetime")
        require(raw or nxt != "#", f"{s!r}: reserved lifetime prefix")
    elif cls in ("int", "float"):
        end, want = rust_number(text, ci)
        require(end == ce and want == cls, f"{s!r}: numeric scan gives {text[ci:end]!r} as {want}")
    else:
        want = next((c for p, c in RUST_PREFIX if s.startswith(p) and (p not in ("br", "cr", "r") or s[len(p):len(p) + 1] in ("#", "\""))), None)
        require(want == cls, f"{s!r}: literal prefix says {want}, class is {cls}")
        require(not nxt or not xid_continue(nxt), f"{s!r}: literal or suffix not maximal")
        # The literal body must be closed by its own delimiter, then an optional suffix.
        p = next(p for p, c in RUST_PREFIX if c == cls)
        rest = s[len(p):] if cls not in ("char", "string") else s[1:]
        if cls in ("rawstring", "rawbytestring", "rawcstring"):
            hashes = len(rest) - len(rest.lstrip("#"))
            close = "\"" + "#" * hashes
            body_end = rest.find(close, hashes + 1)
            require(rest[hashes:hashes + 1] == "\"" and body_end > hashes, f"{s!r}: unterminated raw literal")
            tail = rest[body_end + len(close):]
        else:
            q = "'" if cls in ("char", "byte") else "\""
            i, n = 0, len(rest)
            while i < n and rest[i] != q:
                i += 2 if rest[i] == "\\" else 1
            require(i < n and (q == "\"" or i > 0), f"{s!r}: literal not closed by {q}")
            tail = rest[i + 1:]
        require(tail == "" or rust_suffix_end(tail, 0) == len(tail), f"{s!r}: text after the literal is not a suffix")


# ---------------------------------------------------------------- per-vector checks

def check_error_offset(code, offset, data, spec):
    """Plausibility only: the character at the offset can start the failing construct."""
    text = data.decode("utf-8")
    prefix = data[:offset].decode("utf-8")
    ci = len(prefix)
    require(ci < len(text), "lexical error offset at end of input")
    c = text[ci]
    if code == "illegal-character":
        if spec["lang"] == "go":
            starts = go_letter(c) or c.isascii() and c.isdigit() or c in "\"'`/" or any(op.startswith(c) for op in GO_OPS)
        else:
            starts = xid_start(c) or c == "_" or c.isascii() and c.isdigit() or c in "\"'/" or c in RUST_PUNCT
        require(not starts and c not in spec["whitespace"], f"{c!r} can start a token")
    elif code == "unterminated-comment":
        require(text.startswith("/*", ci), "unterminated-comment offset is not at '/*'")
    elif code == "unterminated-literal":
        require(c in "\"'`rbc", "unterminated-literal offset is not at a literal start")
    elif code == "unbalanced-delimiter":
        require(c in "()[]{}", "unbalanced-delimiter offset is not at a delimiter")
    elif code == "non-nfc-identifier":
        require(not unicodedata.is_normalized("NFC", text[ci:]), "input after offset is already NFC")
    elif code == "malformed-identifier":
        require("‌" in text[ci:] or "‍" in text[ci:], "no zero-width joiner after offset")
    elif code in ("malformed-literal", "reserved-token"):
        require(not c.isspace(), "offset at whitespace")


def check_vector(v, cfg, spec, stats):
    data = base64.b64decode(v["inputBase64"], validate=True)
    res, lang = v["result"], spec["lang"]
    bad = first_invalid_utf8(data)
    if bad is not None:
        require(v["inputText"] is None, "inputText must be null for invalid UTF-8")
    else:
        require(v["inputText"] == data.decode("utf-8"), "inputText does not match inputBase64")
    if res["status"] == "error":
        code, offset = res["error"]["code"], res["error"]["offset"]
        require(set(res) == {"status", "error"}, "error results carry no tokens or fingerprints")
        require(code in spec["codes"], f"error code {code!r} is not in the closed list for this profile")
        require(type(offset) is int and 0 <= offset <= len(data), "error offset outside input")
        if len(data) > cfg["maxInputBytes"]:
            require((code, offset) == ("input-too-large", 0), "size check precedes all others")
        elif bad is not None:
            require((code, offset) == ("invalid-utf8", bad), f"expected invalid-utf8 at {bad}")
        else:
            forbidden = first_forbidden(data.decode("utf-8"), lang)
            if forbidden is not None:
                require((offset, code) == forbidden, f"expected {forbidden[1]} at {forbidden[0]}")
            else:
                require(code not in ENCODING_CODES, f"{code} not justified by the input bytes")
                check_error_offset(code, offset, data, spec)
                stats["lexical-offsets-plausibility-only"] += 1
        stats["errors"] += 1
        return
    require(len(data) <= cfg["maxInputBytes"], "accepted input exceeds maxInputBytes")
    require(bad is None, "accepted input is not UTF-8")
    text = data.decode("utf-8")
    require(first_forbidden(text, lang) is None, "accepted input contains a forbidden code point")
    k, w = cfg["k"], cfg["window"]
    tokens = res["tokens"]
    require(res["tokenCount"] == len(tokens), "tokenCount mismatch")
    require(res["status"] == ("ok" if len(tokens) >= k else "insufficient-tokens"), "status mismatch")
    b2c, acc = {}, 0
    for ci, ch in enumerate(text):
        b2c[acc] = ci
        acc += len(ch.encode("utf-8"))
    b2c[acc] = len(text)
    real = []
    prev_end = 0
    for idx, t in enumerate(tokens):
        s, e = t["span"]
        require(set(t) <= {"class", "text", "span", "inserted"}, f"token {idx}: unknown field")
        require(t["class"] in spec["literals"] | spec["other"], f"unknown class {t['class']}")
        require(0 <= s <= e <= len(data) and s >= prev_end, f"token {idx}: span {t['span']} invalid or overlapping")
        if t.get("inserted"):
            require(lang == "go" and t["class"] == "punct" and t["text"] == ";", "only Go inserts ';'")
            continue
        require("inserted" not in t, "inserted must be true or absent")
        require(e > s and data[s:e] == t["text"].encode("utf-8"), f"token {idx}: text != input[{s}:{e}]")
        require(s in b2c and e in b2c, f"token {idx}: span splits a character")
        real.append(t)
        prev_end = e
    # Trivia between real tokens, lexical invariants, and Go semicolon insertion.
    expected, prev_char_end = [], 0
    for i, t in enumerate(real):
        ci, ce = b2c[t["span"][0]], b2c[t["span"][1]]
        nl = scan_trivia(text, prev_char_end, ci, spec, i == 0)
        if lang == "go" and i > 0 and nl and go_triggers(real[i - 1]):
            end = real[i - 1]["span"][1]
            expected.append({"class": "punct", "text": ";", "span": [end, end], "inserted": True})
        (check_go_token if lang == "go" else check_rust_token)(t, text, ci, ce)
        if t["class"] in ("ident", "keyword"):
            stats["identifiers"] += 1
        expected.append(t)
        prev_char_end = ce
    scan_trivia(text, prev_char_end, len(text), spec, not real)
    if lang == "go" and real and go_triggers(real[-1]):
        end = real[-1]["span"][1]
        expected.append({"class": "punct", "text": ";", "span": [end, end], "inserted": True})
    require(tokens == expected, "inserted semicolons differ from those recomputed by contract section 4.3"
            if lang == "go" else "token list mismatch")
    if lang == "rust":
        stack = []
        for t in real:
            if t["class"] == "punct" and t["text"] in "([{":
                stack.append(t["text"])
            elif t["class"] == "punct" and t["text"] in ")]}":
                require(stack and stack.pop() == {")": "(", "]": "[", "}": "{"}[t["text"]], "unbalanced delimiters")
        require(not stack, "unclosed delimiter")
    stats["tokens"] += len(tokens)
    stats["inserted"] += len(tokens) - len(real)
    for channel in ("exact", "normalized"):
        ch = res["channels"][channel]
        values = [t["text"] if channel == "exact" else normalized_value(spec, t["class"], t["text"]) for t in tokens]
        if channel == "normalized":
            require(ch["values"] == values, "normalized values mismatch")
        pairs = [(t["class"], val) for t, val in zip(tokens, values)]
        m = max(0, len(tokens) - k + 1)
        require(len(ch["kgrams"]) == m, f"{channel}: expected {m} k-grams")
        hashes = []
        for i, g in enumerate(ch["kgrams"]):
            require(g["position"] == i, "k-gram positions must be 0..m-1")
            require(g["hash"] == hash_kgram(cfg, channel, pairs[i:i + k]), f"{channel}: hash mismatch at {i}")
            require(g["span"] == [tokens[i]["span"][0], tokens[i + k - 1]["span"][1]], f"{channel}: k-gram span at {i}")
            hashes.append(int(g["hash"], 16))
        picks, partial = select(hashes, w)
        require(ch["windowSelections"] == picks, f"{channel}: window selections {ch['windowSelections']} != {picks}")
        require(ch["partialWindow"] == partial, f"{channel}: partialWindow flag")
        want = [{"position": p, "hash": ch["kgrams"][p]["hash"], "span": ch["kgrams"][p]["span"]} for p in sorted(set(picks))]
        require(ch["fingerprints"] == want, f"{channel}: fingerprints mismatch")
        spans = [(0, len(hashes))] if partial else [(s, s + w) for s in range(len(hashes) - w + 1)]
        for lo, hi in spans:
            win = hashes[lo:hi]
            if win and win.count(min(win)) > 1:
                stats["tie-windows"] += 1
                v["_ties"] = v.get("_ties", 0) + 1
        if len({f["hash"] for f in want}) != len(want):
            v["_dup"] = True
        stats["kgrams"] += len(hashes)
        stats["fingerprints"] += len(want)


REQUIRED_TAGS = {"empty", "short", "exact-k", "unicode", "unicode-boundary", "malformed", "repeated",
                 "equal-minimum", "trivia-pair", "rename-pair"}


def check_pairs(vectors, lang):
    by_tag = {}
    for v in vectors:
        for tag in v["tags"]:
            by_tag.setdefault(tag, []).append(v)
    missing = REQUIRED_TAGS - set(by_tag)
    require(not missing, f"{lang}: missing required cases {sorted(missing)}")
    for v in by_tag["equal-minimum"]:
        require(v.get("_ties", 0) > 0, f"{v['id']}: tagged equal-minimum but no window tie occurs")
    require(any(v.get("_dup") for v in by_tag["repeated"]), f"{lang}: no repeated case retains duplicate hashes")
    for tag, same_exact in (("trivia-pair", True), ("rename-pair", False)):
        group = sorted(by_tag[tag], key=lambda v: v["id"])
        require(len(group) == 2, f"{lang}: {tag} needs exactly two vectors")
        a, b = (x["result"]["channels"] for x in group)
        for c in ("exact", "normalized"):
            ha, hb = [g["hash"] for g in a[c]["kgrams"]], [g["hash"] for g in b[c]["kgrams"]]
            fa = [(f["position"], f["hash"]) for f in a[c]["fingerprints"]]
            fb = [(f["position"], f["hash"]) for f in b[c]["fingerprints"]]
            require(ha, f"{tag}: pair must produce k-grams")
            if c == "exact" and not same_exact:
                require(ha != hb and fa != fb, f"{tag}: exact channel must differ")
            else:
                require(ha == hb and fa == fb, f"{tag}: {c} hashes and fingerprints must be identical")
    return 2


def load(path):
    data = strict_json(path)
    raw = (path.parent / data["configFile"]).read_bytes()
    cfg = validate_config(raw)
    require(hashlib.sha256(raw).hexdigest() == data["configSha256"], "config digest mismatch")
    for key in ("contract", "profile", "profileVersion", "k", "window"):
        require(data[key] == cfg[key], f"vector file {key} differs from its configuration")
    return data, cfg, PROFILES[(cfg["profile"], cfg["profileVersion"])]


def run_vectors(vectors, cfg, spec, required, name="vectors"):
    stats = dict.fromkeys(STAT_KEYS, 0)
    ids = set()
    for v in vectors:
        require(v["id"] not in ids, f"duplicate id {v['id']}")
        ids.add(v["id"])
        try:
            check_vector(v, cfg, spec, stats)
        except CheckError as exc:
            raise CheckError(f"{name}:{v['id']}: {exc}") from None
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise CheckError(f"{name}:{v['id']}: malformed vector ({exc!r})") from None
    stats["pairs"] = check_pairs(vectors, spec["lang"]) if required else 0
    return stats


# ---------------------------------------------------------------- mutation self-tests

def mutations(data, cfg, spec):
    """Yield (name, corrupted vectors). Hashes are recomputed so only the targeted layer is wrong."""
    base = data["vectors"]

    def mutate(vid, fn, rehash=True):
        vs = copy.deepcopy(base)
        v = next(x for x in vs if x["id"] == vid)
        fn(v)
        if rehash and v["result"]["status"] != "error":
            rebuild_channels(v["result"], cfg, spec)
        return vs

    def tok(v, text):
        return next(i for i, t in enumerate(v["result"]["tokens"]) if t["text"] == text and not t.get("inserted"))

    lang = spec["lang"]
    uni = f"{lang}-unicode"

    def flip(v):
        g = v["result"]["channels"]["exact"]["kgrams"][0]
        g["hash"] = ("0" if g["hash"][0] != "0" else "1") + g["hash"][1:]
    yield "flipped hash digit", mutate(uni, flip, rehash=False)

    def leftmost(v):
        ch = v["result"]["channels"]["exact"]
        hs = [int(g["hash"], 16) for g in ch["kgrams"]]
        ch["windowSelections"] = [min(range(s, s + cfg["window"]), key=lambda j: (hs[j], j)) for s in range(len(hs) - cfg["window"] + 1)]
        ch["fingerprints"] = [{"position": p, "hash": ch["kgrams"][p]["hash"], "span": ch["kgrams"][p]["span"]} for p in sorted(set(ch["windowSelections"]))]
    yield "leftmost-minimum tie rule", mutate(f"{lang}-equal-minimum", leftmost, rehash=False)

    def cut(v):
        t = v["result"]["tokens"][0]
        t["span"][1] -= 1
        t["text"] = base64.b64decode(v["inputBase64"])[t["span"][0]:t["span"][1]].decode("utf-8", "replace")
    yield "span cuts a UTF-8 character", mutate(uni, cut)
    yield "dropped real token", mutate(f"{lang}-literals", lambda v: v["result"]["tokens"].pop(1))

    def bad_utf8(v):
        v["result"]["error"]["offset"] -= 1
    yield "wrong invalid-utf8 offset", mutate(f"{lang}-err-invalid-utf8", bad_utf8)
    yield "invented error code", mutate(f"{lang}-err-unterminated-string",
                                        lambda v: v["result"]["error"].__setitem__("code", "made-up-code"))
    kw = "func" if lang == "go" else "fn"

    def relabel_all(vs_ids):
        vs = copy.deepcopy(base)
        for v in vs:
            if v["id"] in vs_ids:
                for t in v["result"]["tokens"]:
                    if t["text"] == kw:
                        t["class"] = "ident"
                rebuild_channels(v["result"], cfg, spec)
        return vs
    yield f"'{kw}' relabelled ident in both pairs", relabel_all({f"{lang}-format-a", f"{lang}-format-b", f"{lang}-rename-a", f"{lang}-rename-b"})
    if lang == "go":
        yield "final inserted ';' dropped", mutate("go-literals", lambda v: v["result"]["tokens"].pop())

        def split(v):
            ts = v["result"]["tokens"]
            i = tok(v, ":=")
            a = ts[i]["span"][0]
            ts[i:i + 1] = [{"class": "punct", "text": ":", "span": [a, a + 1]}, {"class": "punct", "text": "=", "span": [a + 1, a + 2]}]
        yield "':=' split into ':' '='", mutate("go-unicode", split)

        def semi_after_comma(v):
            ts = v["result"]["tokens"]
            i = tok(v, ",")
            e = ts[i]["span"][1]
            ts.insert(i + 1, {"class": "punct", "text": ";", "span": [e, e], "inserted": True})
        yield "inserted ';' after ','", mutate("go-semicolon-comments", semi_after_comma)

        def accept_u2160(v):
            v["result"] = {"status": "ok", "tokens": [
                {"class": "ident", "text": "xⅠ", "span": [0, 4]}, {"class": "punct", "text": ":=", "span": [5, 7]},
                {"class": "int", "text": "1", "span": [8, 9]}, {"class": "punct", "text": ";", "span": [9, 9], "inserted": True}],
                "channels": {}}
        yield "U+2160 accepted as a Go letter", mutate("go-err-u2160", lambda v: (accept_u2160(v), rebuild_channels(v["result"], cfg, spec)), rehash=False)
    else:
        def split_suffix(v):
            v["result"] = {"status": "ok", "tokens": [
                {"class": "keyword", "text": "let", "span": [0, 3]}, {"class": "ident", "text": "s", "span": [4, 5]},
                {"class": "punct", "text": "=", "span": [6, 7]}, {"class": "string", "text": "\"x\"", "span": [8, 11]},
                {"class": "keyword", "text": "_", "span": [11, 12]}, {"class": "punct", "text": ";", "span": [12, 13]}],
                "channels": {}}
            rebuild_channels(v["result"], cfg, spec)
        yield "'\"x\"_' split into string and '_'", mutate("rust-err-string-underscore-suffix", split_suffix, rehash=False)

        def merge_arrow(v):
            ts = v["result"]["tokens"]
            i = tok(v, "-")
            ts[i:i + 2] = [{"class": "punct", "text": "->", "span": [ts[i]["span"][0], ts[i + 1]["span"][1]]}]
        yield "'->' as one token", mutate("rust-format-a", merge_arrow)

        def accept_u2e2f(v):
            v["result"] = {"status": "ok", "tokens": [
                {"class": "keyword", "text": "let", "span": [0, 3]}, {"class": "ident", "text": "aⸯ", "span": [4, 8]},
                {"class": "punct", "text": "=", "span": [9, 10]}, {"class": "int", "text": "1", "span": [11, 12]},
                {"class": "punct", "text": ";", "span": [12, 13]}], "channels": {}}
            rebuild_channels(v["result"], cfg, spec)
        yield "U+2E2F accepted as XID", mutate("rust-err-u2e2f", accept_u2e2f, rehash=False)

        def lifetime_as_char(v):
            ts = v["result"]["tokens"]
            i = next(j for j, t in enumerate(ts) if t["class"] == "lifetime")
            ts[i]["class"] = "char"
        yield "lifetime relabelled char", mutate("rust-lifetimes-chars", lifetime_as_char)


def mutation_self_test(data, cfg, spec, required):
    names, missed = [], []
    for name, vectors in mutations(data, cfg, spec):
        names.append(name)
        try:
            run_vectors(vectors, cfg, spec, required)
            missed.append(name)
        except CheckError:
            pass
    require(not missed, f"mutations not detected: {missed}")
    return len(names)


def main(argv):
    global TABLES
    TABLES = Tables(HERE / TABLES_FILE)
    paths = [Path(a) for a in argv] or [HERE / f for f in DEFAULT_FILES]
    failed = False
    try:
        negatives = check_negative_configs(HERE / "config-negative.json")
        print(f"PASS config-negative.json: {negatives}/{negatives} invalid configurations rejected")
    except CheckError as exc:
        print(f"FAIL {exc}")
        failed = True
    total_mut = 0
    for path in paths:
        try:
            data, cfg, spec = load(path)
            required = data.get("requiredCoverage", False)
            s = run_vectors(data["vectors"], cfg, spec, required, path.name)
            muts = mutation_self_test(data, cfg, spec, required) if required else 0
            total_mut += muts
        except CheckError as exc:
            print(f"FAIL {path.name}: {exc}")
            failed = True
            continue
        print(f"PASS {path.name} profile={cfg['profile']}/{cfg['profileVersion']} config={data['configSha256'][:16]}... "
              f"vectors={len(data['vectors'])} tokens={s['tokens']} (inserted ';'={s['inserted']}) "
              f"identifiers={s['identifiers']} kgrams={s['kgrams']} fingerprints={s['fingerprints']} "
              f"tie-windows={s['tie-windows']} errors={s['errors']} "
              f"(lexical offsets plausibility-only: {s['lexical-offsets-plausibility-only']}) pairs={s['pairs']}"
              + (f" mutations-rejected={muts}/{muts}" if required else ""))
    print(f"Unicode tables {TABLES_FILE} sha256={TABLES_SHA256[:16]}...; NFC via Python unicodedata "
          f"{unicodedata.unidata_version} for characters assigned in both 16.0 and 17.0 only.")
    print("Not a lexer: token streams are validated, not produced; exact lexical error offsets are compared "
          "with the toolchains by harness/crosscheck.py.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
