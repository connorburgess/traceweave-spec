#!/usr/bin/env python3
"""Independent checker for the draft text-profile extraction vectors.

Standard library only. Python's unicodedata module is NOT used: its data is
Unicode 16.0.0 in the interpreter this was written with, and the profile pins
17.0.0. Everything Unicode-related comes from text-tables-17.0.0.json, whose
digest is pinned below and which harness/gen_text_tables.py regenerates from
the UCD and security files.

For every vector file it recomputes, from the input bytes alone:

* configuration validation (profile section 11) and the negative
  configurations in config-negative-text.json;
* the input checks in order: size, UTF-8, NUL (profile section 3);
* the Markdown masks for text-markdown (profile section 5), compared with the
  vector's `masked` list;
* character classes and the token rule (profile sections 6-7), compared token
  by token: exact text, half-open byte span;
* the fold and the skeleton (profile section 8): NFD, NFKC_Casefold mapping,
  NFC, separator removal, NFC; then UTS #39 skeleton of the folded value;
* k-gram bytes, SHA-256-derived hashes, rightmost-minimum winnowing, partial
  windows and fingerprints for each of the three channels;
* the pair relations declared in each file.

Then it runs two self-tests. The paired rejections in rejections.json are
deliberately wrong expected results (hashes recomputed so that only the
targeted layer is wrong) that MUST be rejected. The wrong-implementation
self-test re-extracts every vector input with each of 14 plausible but wrong
extractors (WRONG_IMPLEMENTATIONS); each MUST differ on at least one vector.

Profiles and versions: text-plain draft-1 (frozen for stage 1), text-markdown
draft-2.

Usage:
  python3 -I check_text_vectors.py [--normalization-test NormalizationTest.txt]
"""

from __future__ import annotations

import base64
import bisect
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VECTOR_FILES = ["text-plain.json", "text-markdown.json", "limits-text.json"]
TABLES_FILE = "text-tables-17.0.0.json"
TABLES_SHA256 = "49eb0304ece1f9351f4db79ddf853fdc3bce353d4a833f7c4f9424bf80ae53f4"
NORMALIZATION_TEST_SHA256 = "5019ffd530751a741900c849c0e010332f142a3612234639bd200b82138a87db"
DOMAIN = b"traceweave/text-kgram/draft-1"
CONTRACT = "traceweave-text-winnow-draft-1"
HASH_ID = "sha256-first8-u64be"
PROFILES = {"text-plain": "draft-1", "text-markdown": "draft-2"}  # profile -> the version implemented
# Wrong-implementation switches (profile section 14). Empty for the real checker.
VAR = frozenset()
NON_DI_FORMAT = set(range(0x0600, 0x0606)) | {0x06DD, 0x070F, 0x0890, 0x0891, 0x08E2, 0xFFF9, 0xFFFA, 0xFFFB,
                                              0x110BD, 0x110CD} | set(range(0x13430, 0x13440))
CHANNELS = ["exact", "folded", "skeleton"]
TOKEN_CLASS = b"word"
CONFIG_KEYS = ["contract", "profile", "profileVersion", "channels", "k", "window", "hash", "maxInputBytes"]
K_MAX, WINDOW_MAX, MAX_INPUT_BYTES = 16, 128, 8_388_608
VALUE_RE = re.compile(r"[a-z0-9.-]+")
ERROR_CODES = {"invalid-utf8", "nul", "input-too-large"}


class CheckError(Exception):
    def __init__(self, layer, msg):
        super().__init__(f"[{layer}] {msg}")
        self.layer = layer


def require(cond, layer, msg):
    if not cond:
        raise CheckError(layer, msg)


# ---------------------------------------------------------------- tables

class Tables:
    def __init__(self, path):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != TABLES_SHA256:
            sys.exit(f"FAIL {path.name}: SHA-256 {digest} != pinned {TABLES_SHA256}")
        t = json.loads(raw)
        assert t["unicodeVersion"] == "17.0.0"
        self.word = self._ranges(t["classes"]["word"])
        self.ideo = self._ranges(t["classes"]["ideographic"])
        self.ign = self._ranges(t["classes"]["ignorable"])
        self.white = self._ranges(t["whiteSpace"])
        self.fce = self._ranges(t["fullCompositionExclusion"])
        self.ccc_lo = [r[0] for r in t["ccc"]]
        self.ccc = t["ccc"]
        self.decomp = {cp: m for cp, m in t["canonicalDecomposition"]}
        self.cf = t["nfkcCasefold"]
        self.cf_lo = [r[0] for r in self.cf]
        self.conf = {cp: m for cp, m in t["confusables"]}
        self.compose = {}
        for cp, m in self.decomp.items():
            if len(m) == 2 and not self.fce(cp):
                self.compose[(m[0], m[1])] = cp

    @staticmethod
    def _ranges(r):
        lo = [a for a, _ in r]

        def member(c):
            i = bisect.bisect_right(lo, c) - 1
            return i >= 0 and r[i][0] <= c <= r[i][1]
        return member

    def combining_class(self, c):
        i = bisect.bisect_right(self.ccc_lo, c) - 1
        if i >= 0 and self.ccc[i][0] <= c <= self.ccc[i][1]:
            return self.ccc[i][2]
        return 0

    def char_class(self, c):
        if VAR:
            if "u16" in VAR and _unassigned_16(c):
                return "S"
            if "cf-ignorable" in VAR and c in NON_DI_FORMAT:
                return "I"
            if "zwsp-sep" in VAR and c == 0x200B:
                return "S"
            if "ideo-runs" in VAR and self.ideo(c) and not self.ign(c):
                return "W"
        if self.ign(c):
            return "I"
        if self.ideo(c):
            return "C"
        if self.word(c):
            return "W"
        return "S"

    def nfkc_cf(self, c):
        i = bisect.bisect_right(self.cf_lo, c) - 1
        if i >= 0 and self.cf[i][0] <= c <= self.cf[i][1]:
            return self.cf[i][2]
        return [c]


def _unassigned_16(c):
    import unicodedata  # only for the "Unicode 16.0 library" wrong implementation
    return unicodedata.category(chr(c)) == "Cn" and not 0xE0000 <= c <= 0xE0FFF


def _cherokee_small(c):
    return 0x13F8 <= c <= 0x13FD or 0xAB70 <= c <= 0xABBF


SBASE, LBASE, VBASE, TBASE = 0xAC00, 0x1100, 0x1161, 0x11A7
LCOUNT, VCOUNT, TCOUNT = 19, 21, 28
NCOUNT, SCOUNT = VCOUNT * TCOUNT, LCOUNT * VCOUNT * TCOUNT


def decompose(T, c, out):
    if SBASE <= c < SBASE + SCOUNT:
        s = c - SBASE
        out.append(LBASE + s // NCOUNT)
        out.append(VBASE + (s % NCOUNT) // TCOUNT)
        if s % TCOUNT:
            out.append(TBASE + s % TCOUNT)
        return
    m = T.decomp.get(c)
    if m is None:
        out.append(c)
    else:
        for x in m:
            decompose(T, x, out)


def nfd(T, cps):
    out = []
    for c in cps:
        decompose(T, c, out)
    # Canonical ordering: stable sort of each run of non-starters by ccc.
    i = 0
    while i < len(out):
        if T.combining_class(out[i]) == 0:
            i += 1
            continue
        j = i
        while j < len(out) and T.combining_class(out[j]) != 0:
            j += 1
        out[i:j] = sorted(out[i:j], key=T.combining_class)
        i = j
    return out


def compose_pair(T, s, c):
    if LBASE <= s < LBASE + LCOUNT and VBASE <= c < VBASE + VCOUNT:
        return SBASE + ((s - LBASE) * VCOUNT + (c - VBASE)) * TCOUNT
    if SBASE <= s < SBASE + SCOUNT and (s - SBASE) % TCOUNT == 0 and TBASE < c < TBASE + TCOUNT:
        return s + (c - TBASE)
    return T.compose.get((s, c))


def nfc(T, cps):
    """Canonical composition (UAX #15) over the NFD of cps."""
    out = []
    starter = None
    last = 0
    for c in nfd(T, cps):
        cc = T.combining_class(c)
        if starter is not None and (len(out) - 1 == starter or last < cc):
            comp = compose_pair(T, out[starter], c)
            if comp is not None:
                out[starter] = comp
                continue
        if cc == 0:
            starter = len(out)
            last = 0
        else:
            last = cc
        out.append(c)
    return out


def fold(T, cps):
    """Profile section 8: folded value of one token's code points."""
    mapped = []
    for c in (cps if "no-nfd" in VAR else nfd(T, cps)):
        mapped.extend([c] if "cherokee" in VAR and _cherokee_small(c) else T.nfkc_cf(c))
    v = nfc(T, mapped)
    if "no-filter" in VAR:
        return v
    v = [c for c in v if T.char_class(c) in ("W", "C")]
    return nfc(T, v)


def skeleton(T, cps):
    """UTS #39 section 4 skeleton, applied once to a folded value."""
    out = []
    for c in nfd(T, cps):
        if T.ign(c):
            continue
        out.extend(T.conf.get(c, [c]))
    out = nfd(T, out)
    if "skel-iter" in VAR and out != list(cps):
        return skeleton(T, out)
    return out


def s_of(cps):
    return "".join(map(chr, cps))


# ---------------------------------------------------------------- input

def decode(data):
    """Strict UTF-8 (Unicode 3.9 D92). Returns (code points, byte offsets) or error offset."""
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as e:
        return None, e.start
    cps = [ord(ch) for ch in text]
    offs = []
    o = 0
    for c in cps:
        offs.append(o)
        o += 1 if c < 0x80 else 2 if c < 0x800 else 3 if c < 0x10000 else 4
    offs.append(o)
    return (cps, offs), None


ENTITY_RE = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]{0,31}|#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6});")


def markdown_masks(cps):
    """Profile section 5. Returns a list of half-open code point ranges."""
    s = s_of(cps)
    n = len(s)
    masks = []
    line_starts = [0] + [i + 1 for i, ch in enumerate(s) if ch == "\n"]

    def line_end(start):
        e = s.find("\n", start)
        return n if e < 0 else e

    def content(start):
        e = line_end(start)
        body = s[start:e]
        return body[:-1] if body.endswith("\r") else body

    li = 0
    # MD-1 front matter; draft-2: a leading U+FEFF is skipped
    first = content(0)
    bom = 1 if first.startswith("\ufeff") and "bom-no-fm" not in VAR else 0
    if line_starts and first[bom:] == "---":
        for j in range(1, len(line_starts)):
            if content(line_starts[j]) in ("---", "..."):
                masks.append((bom, line_end(line_starts[j])))
                li = j + 1
                break
    fence = None
    html_block = False
    resume = None
    comment_unclosed_from = None
    while li < len(line_starts):
        ls = line_starts[li]
        le = line_end(ls)
        body = content(ls)
        if html_block:  # wrong-implementation switch only: CommonMark HTML block runs to a blank line
            if body.strip(" \t") == "":
                html_block = False
            else:
                masks.append((ls, le))
                li += 1
                continue
        if fence is not None:
            masks.append((ls, le))
            m = re.match(r"( *)(" + re.escape(fence[0]) + "+)[ \t]*$", body)
            if m and len(m.group(1)) <= 3 + fence[2] and len(m.group(2)) >= fence[1]:
                fence = None
            li += 1
            continue
        p = ls
        if resume is None:
            if "fence-v1" in VAR:
                m = re.match(r"( {0,3})()()(`{3,}|~{3,})(.*)$", body)
            else:  # draft-2: an optional list marker before the fence
                m = re.match(r"( {0,3})(?:([-*+]|[0-9]{1,9}[.)])( {1,4}))?(`{3,}|~{3,})(.*)$", body)
            if m and not (m.group(4)[0] == "`" and "`" in m.group(5)):
                masks.append((ls, le))
                extra = m.start(4) if m.group(2) else 0
                fence = (m.group(4)[0], len(m.group(4)), extra)
                li += 1
                continue
            if "html-block" in VAR and re.match(r" {0,3}</?[A-Za-z]", body):
                masks.append((ls, le))
                html_block = True
                li += 1
                continue
            if re.match(r" {0,3}\[[^\]^][^\]]*\]:", body):
                masks.append((ls, le))
                li += 1
                continue
        else:
            p = resume
            resume = None
        jumped = False
        while p < le:
            if s.startswith("<!--", p) and (comment_unclosed_from is None or p < comment_unclosed_from):
                q = s.find("-->", p + 4)
                if q >= 0:
                    masks.append((p, q + 3))
                    p = q + 3
                    if p > le:
                        li = bisect.bisect_right(line_starts, p) - 1
                        resume = p
                        jumped = True
                        break
                    continue
                comment_unclosed_from = p
            if s[p] == "<":
                j = p + 1
                if j < le and s[j] == "/":
                    j += 1
                if j < le and ("A" <= s[j] <= "Z" or "a" <= s[j] <= "z"):
                    k = j + 1
                    while k < le and s[k] not in "<>":
                        k += 1
                    if k < le and s[k] == ">":
                        masks.append((p, k + 1))
                        p = k + 1
                        continue
            if s.startswith("](", p):
                depth = 0
                k = p + 1
                while k < le:
                    if s[k] == "(":
                        depth += 1
                    elif s[k] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                if k < le:
                    masks.append((p + 1, k + 1))
                    p = k + 1
                    continue
            if s[p] == "&":
                m = ENTITY_RE.match(s, p)
                if m:
                    masks.append((p, m.end()))
                    p = m.end()
                    continue
            p += 1
        if not jumped:
            li += 1
    # Merge into sorted, non-overlapping ranges.
    merged = []
    for a, b in sorted(masks):
        if a == b:
            continue
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def tokenize(T, cps, masked):
    """Profile section 7. Returns a list of (first, last) code point indexes."""
    n = len(cps)
    cls = [T.char_class(c) for c in cps]
    if "apos-join" in VAR:
        for i in range(1, n - 1):
            if cps[i] in (0x27, 0x2019) and cls[i - 1] == "W" and cls[i + 1] == "W":
                cls[i] = "W"
    for a, b in masked:
        for i in range(a, b):
            cls[i] = "S"
    toks = []
    i = 0
    while i < n:
        if cls[i] in ("S", "I"):
            i += 1
            continue
        if cls[i] == "C":
            toks.append((i, i))
            i += 1
            continue
        last = i
        j = i + 1
        while j < n:
            if cls[j] == "I":
                j += 1
                continue
            if cls[j] == "W":
                last = j
                j += 1
                continue
            break
        toks.append((i, last))
        i = last + 1
    return toks


# ---------------------------------------------------------------- config

def validate_config(raw):
    """Returns the parsed config or raises ValueError (profile section 11)."""
    if not isinstance(raw, bytes):
        raise ValueError("not bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("step 1: not UTF-8")
    if not text.endswith("\n") or "\n" in text[:-1] or "\r" in text:
        raise ValueError("step 1: line breaks")

    def no_dupes(pairs):
        keys = [k for k, _ in pairs]
        if len(keys) != len(set(keys)):
            raise ValueError("step 2: duplicate key")
        return dict(pairs)

    def bad_const(x):
        raise ValueError("step 2: constant")
    try:
        cfg = json.loads(text, object_pairs_hook=no_dupes, parse_float=lambda x: (_ for _ in ()).throw(ValueError("step 2: float")), parse_constant=bad_const)
    except json.JSONDecodeError:
        raise ValueError("step 2: not JSON")
    if not isinstance(cfg, dict) or list(cfg) != CONFIG_KEYS:
        raise ValueError("step 3: keys")
    for key in ("contract", "profile", "profileVersion", "hash"):
        if not isinstance(cfg[key], str) or not VALUE_RE.fullmatch(cfg[key]):
            raise ValueError(f"step 4: {key}")
    for key, hi in (("k", K_MAX), ("window", WINDOW_MAX), ("maxInputBytes", MAX_INPUT_BYTES)):
        v = cfg[key]
        if type(v) is not int or not 1 <= v <= hi:
            raise ValueError(f"step 5: {key}")
    if cfg["channels"] != CHANNELS:
        raise ValueError("step 6: channels")
    if cfg["contract"] != CONTRACT or PROFILES.get(cfg["profile"]) != cfg["profileVersion"] or cfg["hash"] != HASH_ID:
        raise ValueError("step 7: identifiers")
    canon = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False) + "\n"
    if canon.encode("utf-8") != raw:
        raise ValueError("step 8: not canonical")
    return cfg


# ---------------------------------------------------------------- hashing

def lp(b):
    return len(b).to_bytes(4, "big") + b


def kgram_hash(cfg, channel, values):
    msg = (lp(DOMAIN) + lp(cfg["profile"].encode()) + lp(cfg["profileVersion"].encode())
           + lp(channel.encode()) + cfg["k"].to_bytes(4, "big"))
    for v in values:
        msg += lp(TOKEN_CLASS) + lp(v.encode("utf-8"))
    return hashlib.sha256(msg).digest()[:8].hex()


def winnow(hashes, w):
    m = len(hashes)
    if m == 0:
        return [], False
    if m < w:
        best = 0
        for p in range(m):
            if hashes[p] <= hashes[best]:
                best = p
        return [best], True
    sel = []
    for s in range(m - w + 1):
        best = s
        for p in range(s, s + w):
            if hashes[p] <= hashes[best]:
                best = p
        sel.append(best)
    return sel, False


def channel_block(cfg, values, spans):
    k, w = cfg["k"], cfg["window"]
    m = max(0, len(values) - k + 1)
    kgrams = []
    for i in range(m):
        kgrams.append({"position": i, "hash": kgram_hash(cfg, CHANNEL_CTX[0], values[i:i + k]),
                       "span": [spans[i][0], spans[i + k - 1][1]]})
    sel, partial = winnow([g["hash"] for g in kgrams], w)
    fps = [kgrams[p] for p in sorted(set(sel))]
    return {"kgrams": kgrams, "windowSelections": sel, "partialWindow": partial, "fingerprints": fps}


CHANNEL_CTX = [None]


def downstream(cfg, tokens):
    """Status and the three channel blocks from a token list (shared by self-test)."""
    spans = [t["span"] for t in tokens]
    out = {}
    for ch in CHANNELS:
        CHANNEL_CTX[0] = ch
        vals = [t["text"] if ch == "exact" else t[ch] for t in tokens]
        block = channel_block(cfg, vals, spans)
        if ch != "exact":
            block = {"values": vals, **block}
        out[ch] = block
    return out


# ---------------------------------------------------------------- vectors

def expected_result(T, cfg, data):
    """Recompute the full result from input bytes."""
    if len(data) > cfg["maxInputBytes"]:
        return {"status": "error", "error": {"code": "input-too-large", "offset": 0}}
    dec, bad = decode(data)
    if dec is None:
        return {"status": "error", "error": {"code": "invalid-utf8", "offset": bad}}
    cps, offs = dec
    if 0 in cps:
        return {"status": "error", "error": {"code": "nul", "offset": offs[cps.index(0)]}}
    if "bom-strip" in VAR and cps[:1] == [0xFEFF]:
        cps, offs = cps[1:], [o - 3 for o in offs[1:]]
    masked = markdown_masks(cps) if cfg["profile"] == "text-markdown" else []
    toks = []
    for a, b in tokenize(T, cps, masked):
        piece = cps[a:b + 1]
        f = fold(T, piece)
        sk = fold(T, skeleton(T, piece)) if "skel-before-fold" in VAR else skeleton(T, f)
        toks.append({"text": s_of(piece), "span": [offs[a], offs[b + 1]],
                     "folded": s_of(f), "skeleton": s_of(sk)})
    res = {"status": "ok" if len(toks) >= cfg["k"] else "insufficient-tokens"}
    if cfg["profile"] == "text-markdown":
        res["masked"] = [[offs[a], offs[b]] for a, b in masked]
    res["tokens"] = toks
    res.update(downstream(cfg, toks))
    return res


RESULT_CHANNEL_KEYS = ["kgrams", "windowSelections", "partialWindow", "fingerprints"]


def to_record_result(flat):
    """Internal flat result -> contract section 2a `result` (A3 channel list exact, folded, skeleton)."""
    if flat.get("status") == "error":
        return flat
    r = {"status": flat["status"], "tokenCount": len(flat["tokens"]),
         "tokens": [{"class": "word", "text": t["text"], "span": t["span"]} for t in flat["tokens"]]}
    if "masked" in flat:  # text-markdown only; placement after tokens is PROPOSED (open item, profile section 10)
        r["masked"] = flat["masked"]
    r["channels"] = {"exact": {k: flat["exact"][k] for k in RESULT_CHANNEL_KEYS}}
    for ch in CHANNELS[1:]:
        r["channels"][ch] = {"values": flat[ch]["values"], **{k: flat[ch][k] for k in RESULT_CHANNEL_KEYS}}
    return r


def to_flat(rec, where):
    """Contract section 2a `result` -> internal flat form, checking its structure (layer `record`)."""
    if rec.get("status") == "error":
        require(list(rec) == ["status", "error"] and list(rec["error"]) == ["code", "offset"], "record",
                f"{where}: error result keys")
        return rec
    keys = ["status", "tokenCount", "tokens"] + (["masked"] if "masked" in rec else []) + ["channels"]
    require(list(rec) == keys, "record", f"{where}: result keys {list(rec)} != {keys}")
    toks = rec["tokens"]
    require(rec["tokenCount"] == len(toks), "record", f"{where}: tokenCount {rec['tokenCount']} != {len(toks)} tokens")
    for i, t in enumerate(toks):
        require(list(t) == ["class", "text", "span"] and t["class"] == "word", "record",
                f"{where}: token {i} must be exactly class (word), text, span")
    chans = rec["channels"]
    require(list(chans) == CHANNELS, "record", f"{where}: channels {list(chans)} != declared list {CHANNELS}")
    require(list(chans["exact"]) == RESULT_CHANNEL_KEYS, "record", f"{where}: exact channel keys")
    for ch in CHANNELS[1:]:
        require(list(chans[ch]) == ["values"] + RESULT_CHANNEL_KEYS, "record", f"{where}: {ch} channel keys")
        require(len(chans[ch]["values"]) == len(toks), "record", f"{where}: {ch} has one value per token")
    flat = {"status": rec["status"]}
    if "masked" in rec:
        flat["masked"] = rec["masked"]
    flat["tokens"] = [{"text": t["text"], "span": t["span"], "folded": chans["folded"]["values"][i],
                       "skeleton": chans["skeleton"]["values"][i]} for i, t in enumerate(toks)]
    flat["exact"] = dict(chans["exact"])
    for ch in CHANNELS[1:]:
        flat[ch] = dict(chans[ch])
    return flat


def compare(exp, got, where):
    """Compare a recomputed (flat) result with a recorded section 2a result, naming the first differing layer."""
    if exp.get("status") == "error" or got.get("status") == "error":
        require(exp == got, "error", f"{where}: expected {exp.get('error') or exp['status']}, vector has {got.get('error') or got.get('status')}")
        return
    got = to_flat(got, where)
    require(set(got) == set(exp), "record", f"{where}: result keys {sorted(got)} != {sorted(exp)}")
    if "masked" in exp:
        require(exp["masked"] == got["masked"], "markdown", f"{where}: masked {got['masked']} != {exp['masked']}")
    et, gt = exp["tokens"], got["tokens"]
    for i in range(max(len(et), len(gt))):
        e = et[i] if i < len(et) else None
        g = gt[i] if i < len(gt) else None
        require(e is not None and g is not None and e["text"] == g["text"] and e["span"] == g["span"],
                "segmentation", f"{where}: token {i}: vector {g and (g['text'], g['span'])!r} != recomputed {e and (e['text'], e['span'])!r}")
        require(set(g) == {"text", "span", "folded", "skeleton"}, "record", f"{where}: token {i} keys")
        require(e["folded"] == g["folded"], "fold", f"{where}: token {i} folded {g['folded']!r} != {e['folded']!r}")
        require(e["skeleton"] == g["skeleton"], "skeleton", f"{where}: token {i} skeleton {g['skeleton']!r} != {e['skeleton']!r}")
    require(exp["status"] == got["status"], "status", f"{where}: status {got['status']} != {exp['status']}")
    for ch in CHANNELS:
        e, g = exp[ch], got[ch]
        if ch != "exact":
            require(e["values"] == g["values"], "values", f"{where}: {ch} values")
        for i, (eg, gg) in enumerate(zip(e["kgrams"], g["kgrams"])):
            require(eg == gg, "hash", f"{where}: {ch} k-gram {i}: {gg} != {eg}")
        require(len(e["kgrams"]) == len(g["kgrams"]), "hash", f"{where}: {ch} k-gram count")
        require(e["windowSelections"] == g["windowSelections"] and e["partialWindow"] == g["partialWindow"],
                "winnow", f"{where}: {ch} selections {g['windowSelections']} != {e['windowSelections']}")
        require(e["fingerprints"] == g["fingerprints"], "winnow", f"{where}: {ch} fingerprints")
        require(set(g) == set(e), "record", f"{where}: {ch} keys")


def check_spans(data, res, where):
    """Spans are half-open, on character boundaries, ordered; text == input[span]."""
    if res.get("status") == "error":
        return
    prev = 0
    for i, t in enumerate(res["tokens"]):
        a, b = t["span"]
        require(prev <= a < b <= len(data), "span", f"{where}: token {i} span {t['span']}")
        require(data[a:b].decode("utf-8") == t["text"], "span", f"{where}: token {i} text != input[span]")
        prev = b


def check_relation(T, files, pair):
    a = files[pair["a"]]
    b = files[pair["b"]]
    if pair["relation"] == "input-rejected":
        require(a["result"]["status"] != "error" and b["result"]["status"] == "error", "pair",
                f"pair {pair['a']} / {pair['b']}: not an accepted input paired with a rejected one")
        return
    for ch in pair["channels"]:
        ca, cb = a["result"]["channels"][ch], b["result"]["channels"][ch]
        ha = [g["hash"] for g in ca["kgrams"]]
        hb = [g["hash"] for g in cb["kgrams"]]
        fa = {g["hash"] for g in ca["fingerprints"]}
        fb = {g["hash"] for g in cb["fingerprints"]}
        rel = pair["relation"]
        if rel == "identical-hashes":
            ok = ha == hb and len(ha) > 0
        elif rel == "different-hashes":
            ok = not (set(ha) & set(hb))
        elif rel == "shares-fingerprint":
            ok = bool(fa & fb)
        else:
            ok = False
        require(ok, "pair", f"pair {pair['a']} / {pair['b']} channel {ch}: not {rel}")


def load_vectors():
    out = {}
    for name in VECTOR_FILES:
        out[name] = json.loads((HERE / name).read_text(encoding="utf-8"))
    return out


def check_file(T, name, doc, configs, all_vectors):
    stats = {"vectors": 0, "tokens": 0, "errors": 0, "ties": 0, "fps": 0, "partial": 0, "masked": 0}
    for v in doc["vectors"]:
        where = f"{name}:{v['id']}"
        require(v.get("derivation") == "hand", "record", f"{where}: derivation must be hand")
        cfg = configs[v["config"]]
        data = base64.b64decode(v["inputBase64"])
        if v.get("inputText") is not None:
            require(v["inputText"].encode("utf-8") == data, "record", f"{where}: inputText != inputBase64")
        exp = expected_result(T, cfg, data)
        got = v["result"]
        if got.get("status") == "error":
            require(got["error"]["code"] in ERROR_CODES, "error", f"{where}: code outside the closed list")
        compare(exp, got, where)
        check_spans(data, got, where)
        stats["vectors"] += 1
        all_vectors[v["id"]] = v
        if got["status"] == "error":
            stats["errors"] += 1
            continue
        stats["tokens"] += len(got["tokens"])
        stats["masked"] += len(got.get("masked", []))
        for ch in CHANNELS:
            stats["fps"] += len(got["channels"][ch]["fingerprints"])
            stats["partial"] += got["channels"][ch]["partialWindow"]
            hs = [g["hash"] for g in got["channels"][ch]["kgrams"]]
            w = cfg["window"]
            for s in range(max(0, len(hs) - w + 1)):
                win = hs[s:s + w]
                if win.count(min(win)) > 1:
                    stats["ties"] += 1
        all_vectors[v["id"]] = v
    return stats


def mutate(T, cfg, result, op):
    """Apply a rejection's mutation to a section 2a result; returns a section 2a result."""
    if op["op"] == "error":
        return {"status": "error", "error": {"code": op["code"], "offset": op["offset"]}}
    return to_record_result(_mutate_flat(T, cfg, to_flat(copy.deepcopy(result), "mutate"), op))


def _mutate_flat(T, cfg, r, op):
    kind = op["op"]
    toks = r.get("tokens")
    if kind == "set":
        toks[op["token"]][op["field"]] = op["value"]
    elif kind == "split":
        t = toks[op["token"]]
        cut = op["at"]  # character index inside text
        text = t["text"]
        left, right = text[:cut], text[cut:]
        lb = len(left.encode("utf-8"))
        t1 = {"text": left, "span": [t["span"][0], t["span"][0] + lb], "folded": op["folded"][0], "skeleton": op["skeleton"][0]}
        t2 = {"text": right, "span": [t["span"][0] + lb, t["span"][1]], "folded": op["folded"][1], "skeleton": op["skeleton"][1]}
        toks[op["token"]:op["token"] + 1] = [t1, t2]
    elif kind == "replace-tokens":
        r["tokens"] = op["tokens"]
    elif kind == "drop":
        del toks[op["token"]]
    elif kind == "error":
        return {"status": "error", "error": {"code": op["code"], "offset": op["offset"]}}
    elif kind == "set-masked":
        r["masked"] = op["masked"]
    elif kind == "status":
        r["status"] = op["status"]
        return r
    elif kind == "leftmost-ties":
        for ch in CHANNELS:
            hs = [g["hash"] for g in r[ch]["kgrams"]]
            w = cfg["window"]
            if len(hs) >= w:
                sel = [min(range(s, s + w), key=lambda p: (hs[p], p)) for s in range(len(hs) - w + 1)]
                r[ch]["windowSelections"] = sel
                r[ch]["fingerprints"] = [r[ch]["kgrams"][p] for p in sorted(set(sel))]
        return r
    elif kind == "hash-without-k":
        for ch in CHANNELS:
            vals = [t["text"] if ch == "exact" else t[ch] for t in r["tokens"]]
            for g in r[ch]["kgrams"]:
                p = g["position"]
                msg = (lp(DOMAIN) + lp(cfg["profile"].encode()) + lp(cfg["profileVersion"].encode()) + lp(ch.encode()))
                for v in vals[p:p + cfg["k"]]:
                    msg += lp(TOKEN_CLASS) + lp(v.encode())
                g["hash"] = hashlib.sha256(msg).digest()[:8].hex()
            hs = [g["hash"] for g in r[ch]["kgrams"]]
            sel, partial = winnow(hs, cfg["window"])
            r[ch]["windowSelections"], r[ch]["partialWindow"] = sel, partial
            r[ch]["fingerprints"] = [r[ch]["kgrams"][p] for p in sorted(set(sel))]
        return r
    else:
        raise SystemExit(f"unknown mutation op {kind}")
    if r.get("tokens") is not None and kind != "status":
        r["status"] = "ok" if len(r["tokens"]) >= cfg["k"] else "insufficient-tokens"
        r.update(downstream(cfg, r["tokens"]))
    return r


def run_rejections(T, configs, vectors):
    doc = json.loads((HERE / "rejections.json").read_text(encoding="utf-8"))
    rejected, layers, failures = 0, {}, []
    paired = set()
    for rj in doc["rejections"]:
        v = vectors[rj["vector"]]
        cfg = configs[v["config"]]
        bad = mutate(T, cfg, v["result"], rj["mutation"])
        data = base64.b64decode(v["inputBase64"])
        try:
            compare(expected_result(T, cfg, data), bad, rj["id"])
            check_spans(data, bad, rj["id"])
            failures.append(f"{rj['id']}: corruption NOT rejected")
        except CheckError as e:
            if e.layer != rj["layer"]:
                failures.append(f"{rj['id']}: rejected at layer {e.layer}, declared {rj['layer']}")
            else:
                rejected += 1
                layers[e.layer] = layers.get(e.layer, 0) + 1
        paired.add(rj["vector"])
    positives = [vid for vid, v in vectors.items() if v["result"]["status"] != "error"]
    unpaired = [vid for vid in positives if vid not in paired]
    return rejected, len(doc["rejections"]), layers, failures, unpaired, len(positives)


WRONG_IMPLEMENTATIONS = [
    # (switch, description). The first five are the variants the clean-room review found the
    # draft-1 checker accepted; the rest are review variants it already rejected.
    ("u16", "Unicode 16.0 library data: code points new in 17.0 are unassigned"),
    ("skel-iter", "skeleton iterated to a fixed point instead of applied once"),
    ("html-block", "CommonMark-style HTML block: from a line starting with a tag through the next blank line"),
    ("bom-no-fm", "draft-1 rule: a leading BOM disables front matter"),
    ("bom-strip", "BOM stripped before extraction, offsets taken from the stripped text"),
    ("fence-v1", "draft-1 fence rule: no list marker before a fence opener"),
    ("cf-ignorable", "the 32 non-Default_Ignorable format characters treated as ignorable"),
    ("cherokee", "golang.org/x/text cases.Fold: Cherokee small letters left unfolded"),
    ("no-nfd", "NFKC_CF mapping without the leading NFD"),
    ("no-filter", "no separator filter after the fold"),
    ("skel-before-fold", "skeleton of the exact text, then folded"),
    ("zwsp-sep", "ZWSP treated as a separator"),
    ("ideo-runs", "ideographs grouped into runs like letters"),
    ("apos-join", "apostrophes between letters kept inside words"),
]


def run_wrong_implementations(T, configs, vectors):
    """Each wrong implementation recomputes every vector; at least one must differ."""
    global VAR
    rows = []
    for switch, desc in WRONG_IMPLEMENTATIONS:
        if switch == "u16":
            import unicodedata
            if unicodedata.unidata_version == "17.0.0":
                rows.append((switch, desc, None, "not applicable: this Python's unicodedata is 17.0.0"))
                continue
        VAR = frozenset([switch])
        first = None
        differing = 0
        try:
            for vid, v in vectors.items():
                data = base64.b64decode(v["inputBase64"])
                try:
                    compare(expected_result(T, configs[v["config"]], data), v["result"], vid)
                except CheckError:
                    differing += 1
                    first = first or vid
        finally:
            VAR = frozenset()
        rows.append((switch, desc, differing, first))
    return rows


# ---------------------------------------------------------------- records (contract section 2a)

RECORD_VERSION = "traceweave-extraction-record-draft-1"
ENVELOPE = ["recordVersion", "profile", "profileVersion", "configSha256", "inputSha256", "inputLength", "result"]
RECORDS_FILE = "records-text-plain.json"


def rec_json(x):
    """Canonical record serialization (contract section 2a rules 1-4), written independently."""
    if x is None:
        return "null"
    if x is True:
        return "true"
    if x is False:
        return "false"
    if type(x) is int:
        return str(x)
    if type(x) is str:
        out = []
        for ch in x:
            o = ord(ch)
            if ch == '"':
                out.append('\\"')
            elif ch == "\\":
                out.append("\\\\")
            elif ch in "\b\t\n\f\r":
                out.append({"\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}[ch])
            elif o < 0x20:
                out.append("\\u%04x" % o)
            else:
                out.append(ch)
        return '"' + "".join(out) + '"'
    if type(x) is list:
        return "[" + ",".join(rec_json(v) for v in x) + "]"
    if type(x) is dict:  # insertion order is the contract's key order
        return "{" + ",".join(rec_json(k) + ":" + rec_json(v) for k, v in x.items()) + "}"
    raise ValueError(f"not a record value: {x!r}")


def expected_record(T, cfg_raw, data):
    """Record bytes for (configuration bytes, input bytes): contract section 2a and extraction Q10."""
    try:
        cfg = validate_config(cfg_raw)
    except ValueError:
        env = {"recordVersion": RECORD_VERSION, "profile": None, "profileVersion": None,
               "configSha256": hashlib.sha256(cfg_raw).hexdigest(), "inputSha256": None, "inputLength": None,
               "result": {"status": "error", "error": {"code": "unsupported-config", "offset": None}}}
        return (rec_json(env) + "\n").encode("utf-8")
    res = to_record_result(expected_result(T, cfg, data))
    unread = res["status"] == "error" and res["error"]["code"] == "input-too-large"
    env = {"recordVersion": RECORD_VERSION, "profile": cfg["profile"], "profileVersion": cfg["profileVersion"],
           "configSha256": hashlib.sha256(cfg_raw).hexdigest(),
           "inputSha256": None if unread else hashlib.sha256(data).hexdigest(),
           "inputLength": None if unread else len(data), "result": res}
    return (rec_json(env) + "\n").encode("utf-8")


def consumer_check(rb):
    """Validate record bytes without the source: framing, strict JSON, canonical bytes, A3 structure."""
    require(rb.endswith(b"\n") and rb.count(b"\n") == 1 and b"\r" not in rb, "record", "one line, one final LF")

    def no_dupes(pairs):
        require(len({k for k, _ in pairs}) == len(pairs), "record", "duplicate key")
        return dict(pairs)
    try:
        r = json.loads(rb[:-1].decode("utf-8"), object_pairs_hook=no_dupes,
                       parse_float=lambda x: (_ for _ in ()).throw(ValueError("float")))
    except (ValueError, UnicodeDecodeError) as exc:
        raise CheckError("record", f"not strict UTF-8 JSON ({exc})") from None
    require(list(r) == ENVELOPE and r["recordVersion"] == RECORD_VERSION, "record", "envelope keys")
    require((rec_json(r) + "\n").encode("utf-8") == rb, "record", "bytes are not canonical")
    if r["profile"] is not None:
        require(PROFILES.get(r["profile"]) == r["profileVersion"], "record", "profile/version not implemented")
    res = r["result"]
    to_flat(res, "record")
    if res["status"] == "error":
        code = res["error"]["code"]
        require(code in ERROR_CODES | {"unsupported-config"}, "record", "error code outside the closed list")
        require((r["inputSha256"] is None) == (code in ("unsupported-config", "input-too-large")), "record",
                "inputSha256 is null exactly for unsupported-config and input-too-large")
        require((r["profile"] is None) == (code == "unsupported-config"), "record", "profile null only for unsupported-config")
    return r


def check_records(T, vectors):
    """records-text-plain.json: recompute every record from its configuration and input bytes."""
    doc = json.loads((HERE / RECORDS_FILE).read_text(encoding="utf-8"))
    n = 0
    sources = 0
    for e in doc["records"]:
        where = f"{RECORDS_FILE}:{e['id']}"
        cfg_raw = (HERE / e["configFile"]).read_bytes() if "configFile" in e else base64.b64decode(e["configBase64"])
        require(hashlib.sha256(cfg_raw).hexdigest() == e["configSha256"], "record", f"{where}: configSha256")
        data = base64.b64decode(e["inputBase64"])
        rb = expected_record(T, cfg_raw, data)
        require(rb == e["expectedRecordText"].encode("utf-8"), "record", f"{where}: record bytes differ from recomputation")
        require(hashlib.sha256(rb).hexdigest() == e["expectedRecordSha256"], "record", f"{where}: record SHA-256")
        r = consumer_check(rb)
        require(r["configSha256"] == e["configSha256"], "record", f"{where}: record configSha256")
        if e.get("source"):
            v = vectors[e["source"].split("#", 1)[1]]
            require(base64.b64decode(v["inputBase64"]) == data and r["result"] == v["result"], "record",
                    f"{where}: result differs from its source vector")
            sources += 1
        n += 1
    return n, sources, doc


RECORD_CORRUPTIONS = [
    # (id, function of the record text) -> must fail consumer_check
    ("per-token-folded", lambda t: t.replace('"class":"word","text":"Shared","span":[0,6]}',
                                             '"class":"word","text":"Shared","span":[0,6],"folded":"shared"}', 1)),
    ("channels-reordered", lambda t: _swap_channels(t)),
    ("tokenCount-off-by-one", lambda t: t.replace('"tokenCount":23', '"tokenCount":22', 1)),
    ("class-not-word", lambda t: t.replace('"class":"word"', '"class":"WORD"', 1)),
    ("values-in-exact", lambda t: t.replace('"exact":{"kgrams"', '"exact":{"values":[],"kgrams"', 1)),
    ("skeleton-channel-dropped", lambda t: t[:t.index(',"skeleton":{')] + "}}}\n"),
    ("non-ascii-escaped", lambda t: t.replace("\u00e9", "\\u00e9", 1)),
    ("missing-final-lf", lambda t: t[:-1]),
    ("pretty-whitespace", lambda t: t.replace('{"recordVersion":', '{ "recordVersion": ', 1)),
    ("inputBytes-name", lambda t: t.replace('"inputLength":', '"inputBytes":', 1)),
    ("sorted-keys", lambda t: json.dumps(json.loads(t), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"),
    ("unsupported-config-with-profile", lambda t: t.replace('"profile":null,"profileVersion":null',
                                                            '"profile":"text-plain","profileVersion":"draft-1"', 1)),
]


def _swap_channels(t):
    r = json.loads(t)
    c = r["result"]["channels"]
    r["result"]["channels"] = {"exact": c["exact"], "skeleton": c["skeleton"], "folded": c["folded"]}
    return rec_json(r) + "\n"


def run_record_corruptions(doc):
    by_id = {e["id"]: e["expectedRecordText"] for e in doc["records"]}
    targets = {"skeleton-channel-dropped": "rec-plain-reflow-a", "non-ascii-escaped": "rec-plain-nfc",
               "unsupported-config-with-profile": "rec-cfg-text-two-channels"}
    rejected, failures = 0, []
    for cid, fn in RECORD_CORRUPTIONS:
        text = by_id[targets.get(cid, "rec-plain-reflow-a")]
        bad = fn(text)
        if bad == text:
            failures.append(f"{cid}: corruption did not change the record")
            continue
        try:
            consumer_check(bad.encode("utf-8"))
            failures.append(f"{cid}: corrupted record accepted")
        except CheckError:
            rejected += 1
    return rejected, len(RECORD_CORRUPTIONS), failures


def matching_checker_records(doc):
    """Optional: the catalogue/report contract's own record validator (written by another author)."""
    path = HERE.parent / "matching" / "check_matching.py"
    schema = HERE.parent.parent / "schemas" / "record.schema.json"
    if not path.exists() or not schema.exists():
        return None
    import importlib.util
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("check_matching_ext", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rec_schema = json.loads(schema.read_text(encoding="utf-8"))
    ok = 0
    errs = []
    for e in doc["records"]:
        try:
            m.check_record_bytes(e["expectedRecordText"].encode("utf-8"), rec_schema)
            ok += 1
        except Exception as exc:  # report, do not hide
            errs.append(f"{e['id']}: {exc}")
    return ok, len(doc["records"]), errs


def normalization_test(T, path):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != NORMALIZATION_TEST_SHA256:
        sys.exit(f"FAIL NormalizationTest.txt SHA-256 {digest} != {NORMALIZATION_TEST_SHA256}")
    n = bad = 0
    for line in raw.decode("utf-8").splitlines():
        body = line.split("#", 1)[0].strip()
        if not body or body.startswith("@"):
            continue
        cols = [[int(x, 16) for x in f.split()] for f in body.split(";")[:5]]
        c1, c2, c3 = cols[0], cols[1], cols[2]
        for src in (c1, c2, c3):
            n += 2
            bad += nfc(T, src) != c2
            bad += nfd(T, src) != c3
    return n, bad


def main(argv):
    T = Tables(HERE / TABLES_FILE)
    ok = True
    # White_Space is always a separator (profile section 6).
    configs = {}
    for name in ("config-text-plain.json", "config-text-markdown.json", "config-text-plain-limit16.json"):
        raw = (HERE / name).read_bytes()
        configs[name] = validate_config(raw)
    neg = json.loads((HERE / "config-negative-text.json").read_text(encoding="utf-8"))
    nrej = 0
    for c in neg["negatives"]:
        try:
            validate_config(c["configText"].encode("utf-8"))
            print(f"FAIL config {c['id']} accepted")
            ok = False
        except ValueError:
            nrej += 1
            if c["expectedResult"] != {"status": "error", "error": {"code": "unsupported-config", "offset": None},
                                        "profile": None, "profileVersion": None,
                                        "configSha256": hashlib.sha256(c["configText"].encode("utf-8")).hexdigest(),
                                        "inputSha256": None, "inputLength": None}:
                print(f"FAIL config {c['id']} expectedResult")
                ok = False
    for c in neg["boundaryPositives"]:
        validate_config(c["configText"].encode("utf-8"))
    print(f"PASS config-negative-text.json: {nrej}/{len(neg['negatives'])} invalid configurations rejected, "
          f"{len(neg['boundaryPositives'])}/{len(neg['boundaryPositives'])} boundary configurations accepted; "
          + ", ".join(f"{n}={hashlib.sha256((HERE / n).read_bytes()).hexdigest()[:16]}" for n in configs))
    docs = load_vectors()
    vectors = {}
    total = 0
    for name, doc in docs.items():
        try:
            st = check_file(T, name, doc, configs, vectors)
            total += st["vectors"]
            print(f"PASS {name} vectors={st['vectors']} tokens={st['tokens']} errors={st['errors']} "
                  f"masked-ranges={st['masked']} fingerprints(all channels)={st['fps']} "
                  f"partial-windows={st['partial']} tie-windows={st['ties']}")
        except CheckError as e:
            print(f"FAIL {name}: {e}")
            ok = False
    if not ok:
        return 1
    pairs = 0
    for doc in docs.values():
        for pair in doc.get("pairs", []):
            try:
                check_relation(T, vectors, pair)
                pairs += 1
            except CheckError as e:
                print(f"FAIL {e}")
                ok = False
    classes = sorted({c for v in vectors.values() for c in v["tags"] if c.startswith("class:")})
    print(f"PASS pairs={pairs} classes={len(classes)} total-vectors={total}")
    rej, nrj, layers, failures, unpaired, npos = run_rejections(T, configs, vectors)
    for f in failures:
        print(f"FAIL {f}")
    if unpaired:
        print(f"FAIL positive vectors without a paired rejection: {unpaired}")
    status = "PASS" if not failures and not unpaired else "FAIL"
    print(f"{status} rejections.json: {rej}/{nrj} corruptions rejected at their declared layer "
          f"({', '.join(f'{k}={v}' for k, v in sorted(layers.items()))}); "
          f"positive vectors with a paired rejection: {npos - len(unpaired)}/{npos}")
    ok = ok and status == "PASS"
    rows = run_wrong_implementations(T, configs, vectors)
    applicable = [r for r in rows if r[2] is not None]
    caught = [r for r in applicable if r[2] > 0]
    for sw, desc, n, first in rows:
        if n is None:
            print(f"  wrong implementation {sw}: {first}")
        else:
            print(f"  wrong implementation {sw} ({desc}): {'REJECTED' if n else 'ACCEPTED'}, "
                  f"{n} vector(s) differ, first {first}")
    wstatus = "PASS" if len(caught) == len(applicable) else "FAIL"
    print(f"{wstatus} wrong-implementation self-test: rejected {len(caught)}/{len(applicable)}"
          + (f" ({len(rows) - len(applicable)} not applicable)" if len(rows) != len(applicable) else ""))
    ok = ok and wstatus == "PASS"
    nrec, nsrc, rdoc = check_records(T, vectors)
    print(f"PASS {RECORDS_FILE}: {nrec} text-plain records recomputed byte for byte from (configuration, input) "
          f"with SHA-256; {nsrc} equal their source vector's result")
    rr, rn, rf = run_record_corruptions(rdoc)
    for f in rf:
        print(f"FAIL record corruption {f}")
    print(f"{'PASS' if not rf else 'FAIL'} record corruption self-test: rejected {rr}/{rn}")
    ok = ok and not rf
    mc = matching_checker_records(rdoc)
    if mc is None:
        print("SKIP matching/check_matching.py not found; record bytes not validated by it")
    else:
        # check_matching.py has no text-plain profile entry, so its closed-error-code lookup refuses every
        # text-plain error record. That refusal is reported, not counted as a record defect.
        unreg = [e for e in mc[2] if e.endswith("error code not in the profile's closed list")]
        other = [e for e in mc[2] if e not in unreg]
        for e in other:
            print(f"FAIL matching checker: {e}")
        print(f"{'PASS' if not other else 'FAIL'} record bytes accepted by matching/check_matching.py "
              f"check_record_bytes + record.schema.json: {mc[0]}/{mc[1]}; refused only because that checker has no "
              f"text-plain profile registered (error-code lookup): {len(unreg)}; other refusals: {len(other)}")
        ok = ok and not other
    if "--normalization-test" in argv:
        n, bad = normalization_test(T, argv[argv.index("--normalization-test") + 1])
        print(f"{'PASS' if bad == 0 else 'FAIL'} NormalizationTest.txt (17.0.0): NFC and NFD checks {n - bad}/{n}")
        ok = ok and bad == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
