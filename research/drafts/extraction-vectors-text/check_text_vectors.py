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

Then it runs the paired rejections in rejections.json: each is a deliberately
wrong expected result (hashes recomputed so that only the targeted layer is
wrong) that MUST be rejected.

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
PROFILES = {"text-plain", "text-markdown"}
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
    for c in nfd(T, cps):
        mapped.extend(T.nfkc_cf(c))
    v = nfc(T, mapped)
    v = [c for c in v if T.char_class(c) in ("W", "C")]
    return nfc(T, v)


def skeleton(T, cps):
    """UTS #39 section 4 skeleton, applied to a folded value."""
    out = []
    for c in nfd(T, cps):
        if T.ign(c):
            continue
        out.extend(T.conf.get(c, [c]))
    return nfd(T, out)


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
    # MD-1 front matter
    if line_starts and content(0) == "---":
        for j in range(1, len(line_starts)):
            if content(line_starts[j]) in ("---", "..."):
                masks.append((0, line_end(line_starts[j])))
                li = j + 1
                break
    fence = None
    resume = None
    comment_unclosed_from = None
    while li < len(line_starts):
        ls = line_starts[li]
        le = line_end(ls)
        body = content(ls)
        if fence is not None:
            masks.append((ls, le))
            m = re.match(r" {0,3}(" + re.escape(fence[0]) + "+)[ \t]*$", body)
            if m and len(m.group(1)) >= fence[1]:
                fence = None
            li += 1
            continue
        p = ls
        if resume is None:
            m = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", body)
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                masks.append((ls, le))
                fence = (m.group(1)[0], len(m.group(1)))
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
    if cfg["contract"] != CONTRACT or cfg["profile"] not in PROFILES or cfg["profileVersion"] != "draft-1" or cfg["hash"] != HASH_ID:
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
    masked = markdown_masks(cps) if cfg["profile"] == "text-markdown" else []
    toks = []
    for a, b in tokenize(T, cps, masked):
        piece = cps[a:b + 1]
        f = fold(T, piece)
        toks.append({"text": s_of(piece), "span": [offs[a], offs[b + 1]],
                     "folded": s_of(f), "skeleton": s_of(skeleton(T, f))})
    res = {"status": "ok" if len(toks) >= cfg["k"] else "insufficient-tokens"}
    if cfg["profile"] == "text-markdown":
        res["masked"] = [[offs[a], offs[b]] for a, b in masked]
    res["tokens"] = toks
    res.update(downstream(cfg, toks))
    return res


def compare(exp, got, where):
    """Compare recomputed vs recorded, naming the first differing layer."""
    if exp.get("status") == "error" or got.get("status") == "error":
        require(exp == got, "error", f"{where}: expected {exp.get('error') or exp['status']}, vector has {got.get('error') or got.get('status')}")
        return
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
    for ch in pair["channels"]:
        ha = [g["hash"] for g in a["result"][ch]["kgrams"]]
        hb = [g["hash"] for g in b["result"][ch]["kgrams"]]
        fa = {g["hash"] for g in a["result"][ch]["fingerprints"]}
        fb = {g["hash"] for g in b["result"][ch]["fingerprints"]}
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
            stats["fps"] += len(got[ch]["fingerprints"])
            stats["partial"] += got[ch]["partialWindow"]
            hs = [g["hash"] for g in got[ch]["kgrams"]]
            w = cfg["window"]
            for s in range(max(0, len(hs) - w + 1)):
                win = hs[s:s + w]
                if win.count(min(win)) > 1:
                    stats["ties"] += 1
        all_vectors[v["id"]] = v
    return stats


def mutate(T, cfg, result, op):
    r = copy.deepcopy(result)
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
    if "--normalization-test" in argv:
        n, bad = normalization_test(T, argv[argv.index("--normalization-test") + 1])
        print(f"{'PASS' if bad == 0 else 'FAIL'} NormalizationTest.txt (17.0.0): NFC and NFD checks {n - bad}/{n}")
        ok = ok and bad == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
