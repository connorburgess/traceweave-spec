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
DEFAULT_FILES = ["go.json", "rust.json", "limits-go.json", "limits-rust.json", "exclusion-rule.json"]
TABLES_FILE = "unicode-17.0.0-tables.json"
TABLES_SHA256 = "9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f"
DOMAIN = b"traceweave/token-kgram/draft-1"
CONTRACT = "traceweave-token-winnow-draft-1"
HASH_ID = "sha256-first8-u64be"
CONFIG_KEYS = ["contract", "profile", "profileVersion", "channels", "k", "window", "hash", "maxInputBytes"]
K_MAX, WINDOW_MAX, MAX_INPUT_BYTES = 16, 128, 8_388_608  # contract section 10 step 5
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
        "exclusions": (),
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
        "exclusions": (),
    },
}
# TEST-ONLY synthetic profile for the shared normalized-stream exclusion rule (contract section 6): Go lexing,
# with every punct ';' (explicit or inserted) excluded from the normalized stream. No implementation is
# expected to support it as a real profile; exclusion-rule.json uses it to pin the shared arithmetic.
PROFILES[("go-tokens-exclusion-test", "draft-1")] = dict(PROFILES[("go-tokens", "draft-1")], exclusions=(("punct", ";"),))
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
    for key, top in (("k", K_MAX), ("window", WINDOW_MAX), ("maxInputBytes", MAX_INPUT_BYTES)):
        v = cfg[key]
        require(type(v) is int and 1 <= v <= top, f"{key} must be an integer in 1..{top}")
    require(cfg["channels"] == ["exact", "normalized"], "channels must be [\"exact\",\"normalized\"]")
    require(cfg["contract"] == CONTRACT, "unknown contract")
    require((cfg["profile"], cfg["profileVersion"]) in PROFILES, "unknown profile/version")
    require(cfg["hash"] == HASH_ID, "unknown hash")
    canonical = (json.dumps(cfg, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
    require(raw == canonical, "bytes differ from the canonical serialization")
    return cfg


def check_config_metadata(data, name="config-negative.json"):
    """M1.2: every configuration entry is hand-derived; boundary positives pair one-to-one with negatives."""
    require(data.get("metadataRules") == "m1.2", f"{name}: metadataRules must be m1.2")
    neg = {n["id"]: n for n in data["negatives"]}
    for item in data["negatives"] + data["boundaryPositives"]:
        require(item.get("derivation") == "hand", f"{name}:{item['id']}: derivation must be 'hand'")
    for x in data["boundaryPositives"]:
        rid = x.get("pairedRejection")
        require(rid in neg, f"{name}:{x['id']}: pairedRejection must name a negative configuration")
        require(neg[rid].get("pairedPositive") == x["id"], f"{name}:{x['id']}: {rid} does not pair back")
    paired = [n for n in data["negatives"] if "pairedPositive" in n]
    require(len(paired) == len(data["boundaryPositives"]), f"{name}: pairing is not one-to-one")


def config_metadata_mutations(data):
    def mut(fn):
        d = copy.deepcopy(data)
        fn(d)
        return d
    yield "config negative without derivation", mut(lambda d: d["negatives"][0].pop("derivation"))
    yield "boundary positive without pairedRejection", mut(lambda d: d["boundaryPositives"][0].pop("pairedRejection"))
    yield "two boundary positives share a negative", mut(
        lambda d: d["boundaryPositives"][1].__setitem__("pairedRejection", d["boundaryPositives"][0]["pairedRejection"]))


def check_negative_configs(path: Path):
    data = strict_json(path)
    check_config_metadata(data)
    for name, d in config_metadata_mutations(data):
        try:
            check_config_metadata(d)
        except (CheckError, KeyError):
            continue
        raise CheckError(f"{path.name}: metadata mutation not detected: {name}")
    want = {"status": "error", "error": {"code": "unsupported-config", "offset": None}}
    for item in data["negatives"]:
        require(item["expectedResult"] == want, f"{path.name}:{item['id']}: expectedResult must be {want}")
        raw = base64.b64decode(item["configBase64"], validate=True)
        try:
            validate_config(raw)
        except CheckError:
            continue
        raise CheckError(f"{path.name}:{item['id']}: accepted, must be rejected ({item['reason']})")
    for item in data["boundaryPositives"]:
        try:
            validate_config(base64.b64decode(item["configBase64"], validate=True))
        except CheckError as exc:
            raise CheckError(f"{path.name}:{item['id']}: rejected, must be accepted ({exc})") from None
    return len(data["negatives"]), len(data["boundaryPositives"])


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


def excluded(spec, token):
    """Contract section 6: a token is excluded from the normalized stream if (class, text) matches a declared
    exclusion; an entry with text None matches the whole class."""
    return any(token["class"] == c and (x is None or token["text"] == x) for c, x in spec["exclusions"])


def channel_indices(spec, tokens, channel):
    """Indices into tokens that form the channel's stream (exact: all; normalized: all minus exclusions)."""
    if channel == "exact":
        return list(range(len(tokens)))
    return [i for i, t in enumerate(tokens) if not excluded(spec, t)]


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
        idx = channel_indices(spec, tokens, channel)
        stream = [tokens[i] for i in idx]
        values = [t["text"] if channel == "exact" else normalized_value(spec, t["class"], t["text"]) for t in stream]
        pairs = [(t["class"], v) for t, v in zip(stream, values)]
        kg = [{"position": i, "hash": hash_kgram(cfg, channel, pairs[i:i + k]),
               "span": [stream[i]["span"][0], stream[i + k - 1]["span"][1]]} for i in range(max(0, len(stream) - k + 1))]
        picks, partial = select([int(g["hash"], 16) for g in kg], w)
        ch = {}
        if channel == "normalized":
            if spec["exclusions"]:
                ch["tokenIndices"] = idx
            ch["values"] = values
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


def rust_doc_comment_at(text, j):
    """True if a doc comment starts at j: '///' not followed by '/', '//!', '/**' not followed by '*' or '/', '/*!'."""
    return ((text.startswith("///", j) and not text.startswith("////", j)) or text.startswith("//!", j)
            or (text.startswith("/**", j) and text[j + 3:j + 4] not in ("*", "/")) or text.startswith("/*!", j))


def rust_shebang_end(text):
    """End (exclusive) of a Rust shebang at offset 0, or None.

    Look-ahead per Reference SHEBANG and rustc: skip white space and non-doc
    comments (an unterminated non-doc block comment runs to end of input); a
    doc comment is content and ends the look-ahead."""
    if not text.startswith("#!"):
        return None
    ws = PROFILES[("rust2024-tokens", "draft-1")]["whitespace"]
    j = 2
    while j < len(text):
        if text[j] in ws:
            j += 1
        elif rust_doc_comment_at(text, j):
            break
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
        # Maximal munch: a suffix absorbs every following XID_Continue; without a suffix, only a SUFFIX start
        # ('_' or XID_Start) may not follow. A digit may follow ("x"0 is two tokens).
        if tail:
            require(not nxt or not xid_continue(nxt), f"{s!r}: suffix not maximal")
        else:
            require(not nxt or not (nxt == "_" or xid_start(nxt)), f"{s!r}: literal followed by a suffix start")


# ---------------------------------------------------------------- per-vector checks

def rust_reserved_prefix_at(text, ci):
    """Contract section 5.3 step 3, applied by the checker itself. If the character at ci is '"', "'" or '#'
    and is immediately preceded by a plain identifier or keyword (not raw, not a literal prefix, not a lifetime
    name or literal suffix), return the identifier's start: scanning reaches the identifier first, and it is
    reserved-token there. Otherwise return None."""
    if ci >= len(text) or text[ci] not in "\"'#":
        return None
    j = ci
    while j > 0 and xid_continue(text[j - 1]):
        j -= 1
    if j == ci or not (xid_start(text[j]) or text[j] == "_"):
        return None
    before = text[j - 1] if j > 0 else ""
    if before in ("'", "\"", "#") or (before and (before.isdigit() or xid_continue(before))):
        return None  # lifetime name, literal suffix or raw identifier: not a plain identifier
    if text[j:ci] in ("r", "br", "cr", "b", "c"):
        return None  # a literal prefix: the literal starts at j and is judged there
    return j


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
    if spec["lang"] == "rust":
        j = rust_reserved_prefix_at(text, ci)
        if j is not None:
            byte_j = len(text[:j].encode("utf-8"))
            require(code == "reserved-token" and offset == byte_j,
                    f"{c!r} at the offset directly follows the identifier {text[j:ci]!r}: section 5.3 step 3 makes "
                    f"this reserved-token at {byte_j}, not {code} at {offset}")


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
        # Contract sections 6-8: each channel has its own token stream; positions index that stream, spans are the
        # original byte spans of its first and last tokens. tokenIndices appears only when exclusions are declared.
        idx = channel_indices(spec, tokens, channel)
        stream = [tokens[i] for i in idx]
        keys = ["kgrams", "windowSelections", "partialWindow", "fingerprints"]
        if channel == "normalized":
            keys = (["tokenIndices"] if spec["exclusions"] else []) + ["values"] + keys
        require(list(ch) == keys, f"{channel}: keys must be {keys}")
        values = [t["text"] if channel == "exact" else normalized_value(spec, t["class"], t["text"]) for t in stream]
        if channel == "normalized":
            if spec["exclusions"]:
                require(ch["tokenIndices"] == idx, f"normalized tokenIndices must be {idx}")
            require(ch["values"] == values, "normalized values mismatch")
        pairs = [(t["class"], val) for t, val in zip(stream, values)]
        m = max(0, len(stream) - k + 1)
        require(len(ch["kgrams"]) == m, f"{channel}: expected {m} k-grams")
        hashes = []
        for i, g in enumerate(ch["kgrams"]):
            require(g["position"] == i, "k-gram positions must be 0..m-1")
            require(g["hash"] == hash_kgram(cfg, channel, pairs[i:i + k]), f"{channel}: hash mismatch at {i}")
            require(g["span"] == [stream[i]["span"][0], stream[i + k - 1]["span"][1]], f"{channel}: k-gram span at {i}")
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


def check_exclusion_rule(vectors, spec):
    """Shared-rule invariants for a profile that declares normalized-stream exclusions (contract section 6)."""
    require(spec["exclusions"], "exclusion checks need a profile with exclusions")
    by_tag = {}
    for v in vectors:
        for tag in v["tags"]:
            by_tag.setdefault(tag, []).append(v)
    a, b = sorted(by_tag["exclusion-pair"], key=lambda v: v["id"])
    ca, cb = a["result"]["channels"], b["result"]["channels"]
    require([g["hash"] for g in ca["exact"]["kgrams"]] != [g["hash"] for g in cb["exact"]["kgrams"]], "exclusion pair: exact must differ")
    for key in ("kgrams", "fingerprints"):
        require([(g["position"], g["hash"]) for g in ca["normalized"][key]] == [(g["position"], g["hash"]) for g in cb["normalized"][key]],
                f"exclusion pair: normalized {key} positions and hashes must be identical")
    require(any(v["result"]["status"] == "ok" and not v["result"]["channels"]["normalized"]["kgrams"] for v in by_tag["exclusion-empty"]),
            "need an ok vector whose normalized channel is empty")
    require(any(any(t.get("inserted") for t in v["result"]["tokens"]) for v in vectors), "need an excluded inserted token")
    return 1


def exclusion_mutations(data, cfg, spec):
    base = data["vectors"]

    def variant(fn):
        vs = copy.deepcopy(base)
        fn(vs)
        return vs

    def keep_semicolons(vs):  # implementation ignores the declared exclusions
        nospec = dict(spec, exclusions=())
        for v in vs:
            if v["result"]["status"] != "error":
                rebuild_channels(v["result"], cfg, nospec)
                ch = v["result"]["channels"]["normalized"]
                ch_new = {"tokenIndices": list(range(len(v["result"]["tokens"])))}
                ch_new.update(ch)
                v["result"]["channels"]["normalized"] = ch_new
    yield "exclusions ignored (normalized keeps ';')", variant(keep_semicolons)

    def exact_positions(vs):  # normalized spans taken from the exact stream's k-grams
        v = next(x for x in vs if x["id"] == "excl-semi-explicit")
        ex, no = v["result"]["channels"]["exact"]["kgrams"], v["result"]["channels"]["normalized"]["kgrams"]
        for g, h in zip(no, ex):
            g["span"] = list(h["span"])
    yield "normalized spans from exact positions", variant(exact_positions)

    def status_from_normalized(vs):
        v = next(x for x in vs if x["id"] == "excl-ok-normalized-empty")
        v["result"]["status"] = "insufficient-tokens"
    yield "status from the normalized count", variant(status_from_normalized)

    def drop_indices(vs):
        v = next(x for x in vs if x["id"] == "excl-semi-newlines")
        del v["result"]["channels"]["normalized"]["tokenIndices"]
    yield "tokenIndices omitted", variant(drop_indices)


M12_CLASSES = ["empty", "below-k+w-1", "unicode", "malformed", "repeated", "equal-minimum", "crlf-bom"]


def expected_classes(v, cfg):
    """The M1.2 classes a vector belongs to, derived from its input and result (independent of the builder)."""
    data = base64.b64decode(v["inputBase64"])
    res = v["result"]
    ok = res["status"] != "error"
    flags = {
        "empty": len(data) == 0,
        "below-k+w-1": ok and res["tokenCount"] < cfg["k"] + cfg["window"] - 1,
        "unicode": any(b > 0x7F for b in data),
        "malformed": not ok,
        "repeated": "repeated" in v["tags"],
        "equal-minimum": "equal-minimum" in v["tags"],
        "crlf-bom": b"\r\n" in data or b"\xef\xbb\xbf" in data,
    }
    return [c for c in M12_CLASSES if flags[c]]


def check_metadata(vectors, cfg, required, name="vectors"):
    """M1.2: derivation metadata, labelled classes, and one-to-one positive/rejection pairs within the file."""
    by = {v["id"]: v for v in vectors}
    for v in vectors:
        vid = v["id"]
        require(v.get("derivation") == "hand", f"{name}:{vid}: derivation must be 'hand'")
        require(v.get("vectorClasses") == expected_classes(v, cfg),
                f"{name}:{vid}: vectorClasses {v.get('vectorClasses')} != {expected_classes(v, cfg)}")
        if v["result"]["status"] == "error":
            require("pairedRejection" not in v, f"{name}:{vid}: an error vector cannot have a pairedRejection")
            pid = v.get("pairedPositive")
            if pid is not None:
                require(pid in by and by[pid].get("pairedRejection") == vid, f"{name}:{vid}: {pid} does not pair back")
        else:
            require("pairedPositive" not in v, f"{name}:{vid}: a positive vector cannot have a pairedPositive")
            rid = v.get("pairedRejection")
            require(rid in by, f"{name}:{vid}: positive vector without a pairedRejection in this file")
            require(by[rid]["result"]["status"] == "error", f"{name}:{vid}: pairedRejection {rid} is not an error vector")
            require(by[rid].get("pairedPositive") == vid, f"{name}:{vid}: {rid} does not pair back (not one-to-one)")
    for v in vectors:  # span rule stated in derivationRule: a source-order search reproduces every start unless marked
        if v["result"]["status"] == "error":
            require("spanStarts" not in v, f"{name}:{v['id']}: spanStarts on an error vector")
            continue
        data, pos, mislocated = base64.b64decode(v["inputBase64"]), 0, 0
        for t in v["result"]["tokens"]:
            if t.get("inserted"):
                continue
            found = data.find(t["text"].encode("utf-8"), pos)
            mislocated += found != t["span"][0]
            pos = t["span"][1]
        if v.get("spanStarts") == "hand":
            require(mislocated > 0, f"{name}:{v['id']}: spanStarts hand, but a search reproduces every start")
        else:
            require("spanStarts" not in v and mislocated == 0,
                    f"{name}:{v['id']}: {mislocated} token start(s) differ from the source-order search; mark spanStarts: hand")
    for v in vectors:  # prefix consistency of each paired rejection against its positive's token stream
        rid = v.get("pairedRejection")
        if v["result"]["status"] == "error" or rid not in by:
            continue
        check_prefix_consistency(v, by[rid], cfg, name)
    if required:
        present = {c for v in vectors for c in v["vectorClasses"]}
        require(present >= set(M12_CLASSES), f"{name}: missing M1.2 classes {sorted(set(M12_CLASSES) - present)}")
    positives = [v for v in vectors if v["result"]["status"] != "error"]
    return len(positives)


def check_prefix_consistency(pos, rej, cfg, name):
    """Every real token of the positive that ends at or before the rejection's error offset, over bytes the two
    inputs share, must still pass the per-token lexical checks in the rejection's input. If one fails (for
    example an identifier now directly followed by '"'), scanning would fail at that token: the recorded error
    must be at or before its start."""
    pdata, rdata = base64.b64decode(pos["inputBase64"]), base64.b64decode(rej["inputBase64"])
    err = rej["result"]["error"]
    if err["code"] in ENCODING_CODES:
        return
    try:
        rtext = rdata.decode("utf-8")
    except UnicodeDecodeError:
        return
    lang = PROFILES[(cfg["profile"], cfg["profileVersion"])]["lang"]
    check = check_go_token if lang == "go" else check_rust_token
    for t in pos["result"]["tokens"]:
        s, e = t["span"]
        if t.get("inserted") or e > err["offset"] or pdata[:e] != rdata[:e]:
            continue
        try:
            ci, ce = len(rdata[:s].decode("utf-8")), len(rdata[:e].decode("utf-8"))
        except UnicodeDecodeError:
            continue  # a span that splits a character is rejected by the span checks
        try:
            check(t, rtext, ci, ce)
        except CheckError as exc:
            require(err["offset"] <= s, f"{name}:{rej['id']}: token {t['text']!r} at {s} of {pos['id']} is no longer valid "
                                        f"in the rejection ({exc}); the first error is at or before {s}, not at {err['offset']}")


def metadata_mutations(data):
    base = data["vectors"]

    def mut(fn):
        vs = copy.deepcopy(base)
        fn(vs)
        return vs

    def first(vs, error):
        return next(v for v in vs if (v["result"]["status"] == "error") == error and (error is False or "pairedPositive" in v))

    yield "derivation removed", mut(lambda vs: vs[0].pop("derivation"))
    yield "derivation 'computed'", mut(lambda vs: vs[0].__setitem__("derivation", "computed"))
    yield "positive without pairedRejection", mut(lambda vs: first(vs, False).pop("pairedRejection"))

    def share(vs):
        ps = [v for v in vs if v["result"]["status"] != "error"]
        if len(ps) > 1:
            ps[1]["pairedRejection"] = ps[0]["pairedRejection"]
        else:
            ps[0]["pairedRejection"] = ps[0]["id"]
    yield "two positives share one rejection", mut(share)
    yield "rejection does not pair back", mut(lambda vs: first(vs, True).pop("pairedPositive"))
    yield "spanStarts mark removed", mut(lambda vs: [v.pop("spanStarts") for v in vs if "spanStarts" in v] or vs[0].setdefault("spanStarts", "hand"))
    yield "vectorClasses label dropped", mut(lambda vs: vs[0]["vectorClasses"].pop() if vs[0]["vectorClasses"] else vs[0]["vectorClasses"].append("empty"))


def load(path):
    data = strict_json(path)
    raw = (path.parent / data["configFile"]).read_bytes()
    cfg = validate_config(raw)
    require(hashlib.sha256(raw).hexdigest() == data["configSha256"], "config digest mismatch")
    for key in ("contract", "profile", "profileVersion", "k", "window"):
        require(data[key] == cfg[key], f"vector file {key} differs from its configuration")
    return data, cfg, PROFILES[(cfg["profile"], cfg["profileVersion"])]


def run_vectors(vectors, cfg, spec, required, name="vectors", metadata=False):
    stats = dict.fromkeys(STAT_KEYS, 0)
    if metadata:
        stats["positives-paired"] = check_metadata(vectors, cfg, required, name)
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

        def accept_0b2i(v):
            v["result"] = {"status": "ok", "tokens": [{"class": "imag", "text": "0b2i", "span": [0, 4]}], "channels": {}}
            rebuild_channels(v["result"], cfg, spec)
        yield "'0b2i' accepted as imaginary", mutate("go-q11-imag-binary-digit", accept_0b2i, rehash=False)
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

        def no_reserved_prefix_rule(vid, off):
            def fn(v):
                v["result"]["error"] = {"code": "unterminated-literal", "offset": off}
            return fn
        yield "wrong lexer without the reserved-prefix rule: rust-s1-string-digit-expr-rej", mutate(
            "rust-s1-string-digit-expr-rej", no_reserved_prefix_rule("rust-s1-string-digit-expr-rej", 8))
        yield "wrong lexer without the reserved-prefix rule: rust-q11-shebang-first-line-only-rej", mutate(
            "rust-q11-shebang-first-line-only-rej", no_reserved_prefix_rule("rust-q11-shebang-first-line-only-rej", 10))

        def lifetime_as_char(v):
            ts = v["result"]["tokens"]
            i = next(j for j, t in enumerate(ts) if t["class"] == "lifetime")
            ts[i]["class"] = "char"
        yield "lifetime relabelled char", mutate("rust-lifetimes-chars", lifetime_as_char)

        def string_digit_one_token(v):
            v["result"]["tokens"] = [{"class": "string", "text": "\"x\"0", "span": [0, 4]}]
        yield "'\"x\"0' as one string with suffix", mutate("rust-s1-string-digit", string_digit_one_token)

        def doc_skipped(v):
            v["result"]["tokens"] = [{"class": "punct", "text": "#", "span": [0, 1]}, {"class": "punct", "text": "!", "span": [1, 2]},
                                     {"class": "punct", "text": "[", "span": [7, 8]}, {"class": "ident", "text": "a", "span": [8, 9]},
                                     {"class": "punct", "text": "]", "span": [9, 10]}]
        yield "shebang look-ahead skips '///'", mutate("rust-q8-shebang-outer-line-doc", doc_skipped)


def mutation_self_test(data, cfg, spec, required, metadata=False):
    names, missed = [], []
    meta = list(metadata_mutations(data)) if metadata else []
    for name, vectors in (list(mutations(data, cfg, spec)) if required else []) + meta:
        names.append(name)
        try:
            run_vectors(vectors, cfg, spec, required, metadata=metadata)
            missed.append(name)
        except CheckError:
            pass
    require(not missed, f"mutations not detected: {missed}")
    return len(names)


TOKEN_INDICES_TEST = "tokenIndices emitted without exclusions"


def list_tests():
    """Every self-test name, one per line as FILE<TAB>NAME, for mechanical citation (tools/check_requirement_map.py)."""
    data = strict_json(HERE / "config-negative.json")
    for name, _ in config_metadata_mutations(data):
        print(f"config-negative.json\t{name}")
    for f in DEFAULT_FILES:
        data, cfg, spec = load(HERE / f)
        names = []
        if data.get("requiredCoverage"):
            names += [n for n, _ in mutations(data, cfg, spec)]
            if not spec["exclusions"]:
                names.append(TOKEN_INDICES_TEST)
        if data.get("metadataRules") == "m1.2":
            names += [n for n, _ in metadata_mutations(data)]
        if spec["exclusions"]:
            names += [n for n, _ in exclusion_mutations(data, cfg, spec)]
        for n in names:
            print(f"{f}\t{n}")
    return 0


def main(argv):
    global TABLES
    TABLES = Tables(HERE / TABLES_FILE)
    if argv == ["--list-tests"]:
        return list_tests()
    paths = [Path(a) for a in argv] or [HERE / f for f in DEFAULT_FILES]
    failed = False
    try:
        negatives, positives = check_negative_configs(HERE / "config-negative.json")
        print(f"PASS config-negative.json: {negatives}/{negatives} invalid configurations rejected, "
              f"{positives}/{positives} boundary configurations accepted")
    except CheckError as exc:
        print(f"FAIL {exc}")
        failed = True
    total_mut = 0
    for path in paths:
        try:
            data, cfg, spec = load(path)
            required = data.get("requiredCoverage", False)
            metadata = data.get("metadataRules") == "m1.2"
            require(metadata or path.parent != HERE, "vector files in this directory must declare metadataRules m1.2")
            s = run_vectors(data["vectors"], cfg, spec, required, path.name, metadata)
            muts = mutation_self_test(data, cfg, spec, required, metadata) if (required or metadata) else 0
            if spec["exclusions"]:
                check_exclusion_rule(data["vectors"], spec)
                names, missed = [], []
                for name, vectors in exclusion_mutations(data, cfg, spec):
                    names.append(name)
                    try:
                        run_vectors(vectors, cfg, spec, False, metadata=metadata)
                        check_exclusion_rule(vectors, spec)
                        missed.append(name)
                    except (CheckError, KeyError, ValueError):
                        pass
                require(not missed, f"exclusion mutations not detected: {missed}")
                muts, required = muts + len(names), True
            elif required:
                vs = copy.deepcopy(data["vectors"])  # a profile without exclusions must not emit tokenIndices
                v = next(x for x in vs if x["result"]["status"] == "ok")
                ch = v["result"]["channels"]["normalized"]
                v["result"]["channels"]["normalized"] = dict({"tokenIndices": list(range(len(v["result"]["tokens"])))}, **ch)
                try:
                    run_vectors(vs, cfg, spec, required, metadata=metadata)
                    raise CheckError(f"{TOKEN_INDICES_TEST}: tokenIndices accepted on a profile without exclusions")
                except CheckError as exc:
                    require("tokenIndices accepted" not in str(exc), str(exc))
                muts += 1
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
              + (f" positives={s.get('positives-paired', 0)} paired-one-to-one" if metadata else "")
              + (f" mutations-rejected={muts}/{muts}" if (required or metadata) else ""))
    print(f"Unicode tables {TABLES_FILE} sha256={TABLES_SHA256[:16]}...; NFC via Python unicodedata "
          f"{unicodedata.unidata_version} for characters assigned in both 16.0 and 17.0 only.")
    print("Not a lexer: token streams are validated, not produced; exact lexical error offsets are compared "
          "with the toolchains by harness/crosscheck.py.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
