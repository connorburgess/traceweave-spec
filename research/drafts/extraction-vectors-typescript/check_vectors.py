#!/usr/bin/env python3
"""Checker for the draft ts-tokens / tsx-tokens vectors (draft-1).

    python3 -I research/drafts/extraction-vectors-typescript/check_vectors.py

Standard library only. For every vector it:
  * validates the configuration bytes (contract §10) and rejects the negatives;
  * recomputes the shared pre-lexing checks (size, UTF-8, BOM, NUL);
  * re-lexes the input with tslex.py (written from the profile text, separately
    from the hand-written token lists) and requires class, text, byte span,
    error code and error offset to be identical;
  * enforces lexical invariants directly on the recorded stream: closed class
    and error-code lists, keyword classes from the word list, punctuator
    longest match, token shapes, text == input[span], ordered spans;
  * recomputes normalized values, k-gram bytes, hashes and winnowing
    (sort-based selection, a different formulation from the builder);
  * checks the comment/whitespace and rename pair invariants;
and then runs a mutation self-test: each corruption, rehashed so only the
targeted layer is wrong, must be rejected.
"""
import base64
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tslex  # noqa: E402

DOMAIN = b"traceweave/token-kgram/draft-1"
CONTRACT = "traceweave-token-winnow-draft-1"
KEY_ORDER = ["contract", "profile", "profileVersion", "channels", "k", "window", "hash", "maxInputBytes"]
FILES = [("ts.json", "ts-tokens"), ("tsx.json", "tsx-tokens"), ("limits-ts.json", "ts-tokens")]
PAIRS = {"format": [("ts-format-a", "ts-format-b"), ("tsx-format-a", "tsx-format-b")],
         "rename": [("ts-rename-a", "ts-rename-b")]}


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
        require(type(cfg[key]) is int and 1 <= cfg[key] <= 2 ** 32 - 1, key)
    require(cfg["channels"] == ["exact", "normalized"], "channels")
    require(cfg["contract"] == CONTRACT and cfg["hash"] == "sha256-first8-u64be", "contract/hash")
    require(cfg["profile"] in tslex.PROFILES and cfg["profileVersion"] == "draft-1", "profile pair")
    canon = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False) + "\n"
    require(canon.encode() == raw, "not canonical")
    return cfg


def check_negative_configs():
    items = json.loads((HERE / "config-negative-typescript.json").read_text(encoding="utf-8"))
    n = 0
    for it in items:
        raw = base64.b64decode(it["configBase64"])
        try:
            validate_config(raw)
        except CheckError:
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
    return "" if cls in tslex.LITERAL_CLASSES or cls == "ident" else text


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


def expected_result(data, cfg):
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
    r = tslex.lex(text, cfg["profile"])
    if r[0] == "error":
        return ("error", r[1], boff[r[2]])
    return ("ok", [(c, boff[a], boff[b]) for c, a, b in r[1]])


# ------------------------------------------------------------------ stream invariants

def stream_invariants(v, data, cfg):
    toks = v["result"]["tokens"]
    prev_end = 0
    for n, t in enumerate(toks):
        a, b = t["span"]
        require(t["class"] in tslex.CLASSES, f"class {t['class']!r} not in the closed list")
        require(prev_end <= a < b <= len(data), f"span {t['span']} out of order or empty")
        require(data[a:b] == t["text"].encode("utf-8"), f"text != input[span] at {t['span']}")
        prev_end = b
        txt, cls = t["text"], t["class"]
        prev = toks[n - 1] if n else None
        if cls == "keyword":
            require(txt in tslex.KEYWORDS, f"{txt!r} is not in the keyword list")
            require(not (prev and prev["class"] == "punct" and prev["text"] in (".", "?.")),
                    f"keyword {txt!r} after '.'")
        if cls == "ident" and cfg["profile"] == "ts-tokens" and txt in tslex.KEYWORDS:
            require(prev and prev["class"] == "punct" and prev["text"] in (".", "?."),
                    f"reserved word {txt!r} classed ident outside a property position")
        if cls == "punct":
            require(txt in tslex.PUNCTUATORS, f"{txt!r} is not a punctuator")
            for q in tslex.PUNCTUATORS:
                if len(q) > len(txt) and data.startswith(q.encode(), a):
                    digit = q == "?." and data[a + 2:a + 3].isdigit()
                    require(digit, f"{txt!r} at {a} is not the longest match ({q!r})")
        if cls == "regex":
            require(txt.startswith("/") and not txt.startswith("//") and txt.count("/") >= 2, "regex shape")
        if cls in ("template", "template-head"):
            require(txt.startswith("`"), "template start")
        if cls in ("template-middle", "template-tail"):
            require(txt.startswith("}"), "template continuation start")
        if cls in ("template-head", "template-middle"):
            require(txt.endswith("${"), "template head/middle end")
        if cls in ("template", "template-tail"):
            require(txt.endswith("`") and len(txt) >= 2, "template end")
        if cls == "jsx-text":
            require(txt[0] not in tslex.TRIVIA_CHARS and txt[-1] not in tslex.TRIVIA_CHARS, "jsx-text not trimmed")
            require(not any(c in txt for c in "{}<>"), "jsx-text holds { } < >")
        if cls in ("number", "bigint"):
            require(txt[0].isdigit() or txt[0] == ".", "number start")
            require((cls == "bigint") == txt.endswith("n"), "bigint suffix")


# ------------------------------------------------------------------ vector check

def check_vector(v, cfg, stats):
    data = base64.b64decode(v["inputBase64"])
    if v.get("inputText") is not None:
        require(v["inputText"].encode("utf-8") == data, "inputText differs from inputBase64")
    exp = expected_result(data, cfg)
    r = v["result"]
    if exp[0] == "error":
        require(r["status"] == "error", f"expected error {exp[1]}@{exp[2]}, vector has {r['status']}")
        require(set(r) == {"status", "error"}, "error result carries extra fields")
        code, off = r["error"]["code"], r["error"]["offset"]
        require(code in tslex.ERROR_CODES, f"error code {code!r} not in the closed list")
        require((code, off) == exp[1:], f"error {code}@{off}, re-lex gives {exp[1]}@{exp[2]}")
        stats["errors"] += 1
        return
    require(r["status"] in ("ok", "insufficient-tokens"), f"re-lex accepts; vector has {r['status']}")
    stream_invariants(v, data, cfg)
    got = [(t["class"], t["span"][0], t["span"][1]) for t in r["tokens"]]
    if got != exp[1]:
        for i, (x, y) in enumerate(zip(got + [None] * len(exp[1]), exp[1] + [None] * len(got))):
            if x != y:
                raise CheckError(f"token {i}: vector {x}, re-lex {y}")
    require(r["tokenCount"] == len(r["tokens"]), "tokenCount")
    require(r["status"] == ("ok" if len(got) >= cfg["k"] else "insufficient-tokens"), "status vs k")
    want = channels_for(r["tokens"], cfg)
    for ch in ("exact", "normalized"):
        for key, val in want[ch].items():
            require(r["channels"][ch][key] == val, f"{ch}.{key} differs from recomputation")
    stats["tokens"] += len(got)
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


def check_pairs(by_id):
    n = 0
    for a, b in PAIRS["format"]:
        if a in by_id and b in by_id:
            ra, rb = by_id[a]["result"], by_id[b]["result"]
            require([(t["class"], t["text"]) for t in ra["tokens"]] == [(t["class"], t["text"]) for t in rb["tokens"]],
                    f"format pair {a}/{b}: token streams differ")
            require([g["hash"] for g in ra["channels"]["exact"]["kgrams"]]
                    == [g["hash"] for g in rb["channels"]["exact"]["kgrams"]], f"format pair {a}/{b}: exact hashes")
            n += 1
    for a, b in PAIRS["rename"]:
        if a in by_id and b in by_id:
            ra, rb = by_id[a]["result"], by_id[b]["result"]
            require(ra["channels"]["normalized"]["values"] == rb["channels"]["normalized"]["values"],
                    f"rename pair {a}/{b}: normalized values differ")
            require([g["hash"] for g in ra["channels"]["normalized"]["kgrams"]]
                    == [g["hash"] for g in rb["channels"]["normalized"]["kgrams"]], "rename pair normalized hashes")
            require([g["hash"] for g in ra["channels"]["exact"]["kgrams"]]
                    != [g["hash"] for g in rb["channels"]["exact"]["kgrams"]], "rename pair exact hashes equal")
            n += 1
    return n


def run_file(doc, cfg):
    stats = {"tokens": 0, "kgrams": 0, "fingerprints": 0, "errors": 0, "tie-windows": 0, "classes": set()}
    by_id = {}
    for v in doc["vectors"]:
        require(v["id"] not in by_id, f"duplicate id {v['id']}")
        by_id[v["id"]] = v
        try:
            check_vector(v, cfg, stats)
        except CheckError as e:
            raise CheckError(f"{v['id']}: {e}")
    stats["pairs"] = check_pairs(by_id)
    for v in doc["vectors"]:
        require(v.get("derivation") == "hand", f"{v['id']}: derivation is not 'hand'")
        if v["result"]["status"] != "error":
            stats["paired"] = stats.get("paired", 0) + 1
            require("pairedRejection" in v, f"{v['id']}: no pairedRejection")
    return stats


def load(name):
    doc = json.loads((HERE / name).read_text(encoding="utf-8"))
    raw = (HERE / doc["configFile"]).read_bytes()
    cfg = validate_config(raw)
    require(hashlib.sha256(raw).hexdigest() == doc["configSha256"], f"{name}: config digest")
    require(cfg["profile"] == doc["profile"], f"{name}: profile")
    return doc, cfg


# ------------------------------------------------------------------ mutation self-test

def tok(cls, text, a):
    return {"class": cls, "text": text, "span": [a, a + len(text.encode("utf-8"))]}


def find(v, text, nth=0):
    hits = [i for i, t in enumerate(v["result"]["tokens"]) if t["text"] == text]
    return hits[nth]


def mutations():
    """(file, vector id, description, function(vector) -> None, rehash?)."""
    M = []

    def add(f, vid, desc, rehash=True):
        def deco(fn):
            M.append((f, vid, desc, fn, rehash))
            return fn
        return deco

    @add("ts.json", "ts-regex-after-header", "regex relabelled as division: /a+/ split into / a + /")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, "/a+/")
        a = ts[i]["span"][0]
        ts[i:i + 1] = [tok("punct", "/", a), tok("ident", "a", a + 1), tok("punct", "+", a + 2), tok("punct", "/", a + 3)]

    @add("ts.json", "ts-template-nested", "template split wrongly: nested template merged into one token")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, "`c${")
        a, b = ts[i]["span"][0], ts[i + 2]["span"][1]
        ts[i:i + 3] = [tok("template", "`c${d}e`", a)]
        assert ts[i]["span"][1] == b

    @add("ts.json", "ts-template-nested", "template split wrongly: substitution closed at the object literal's '}'")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, "}", 0)  # the object literal's closing brace
        a = ts[i]["span"][0]
        ts[i:] = [tok("template-tail", "}.g }h`", a), tok("punct", ";", a + len("}.g }h`"))]

    @add("tsx.json", "tsx-text-comment-keywords", "JSX text tokenized as identifiers (and '//' as a comment)")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, "if // not a comment")
        a = ts[i]["span"][0]
        ts[i:i + 1] = [tok("keyword", "if", a)]

    @add("tsx.json", "tsx-text-whitespace", "JSX text not trimmed (leading space kept)")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, "a  b")
        a = ts[i]["span"][0]
        ts[i] = tok("jsx-text", " a  b", a - 1)

    @add("ts.json", "ts-shift-ops", "'>>' split into '>' '>' in an expression")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, ">>")
        a = ts[i]["span"][0]
        ts[i:i + 1] = [tok("punct", ">", a), tok("punct", ">", a + 1)]

    @add("ts.json", "ts-generics-gt", "'>>' closing generics split into '>' '>'")
    def _(v):
        ts = v["result"]["tokens"]
        for i in reversed([j for j, t in enumerate(ts) if t["text"] == ">>"]):
            a = ts[i]["span"][0]
            ts[i:i + 1] = [tok("punct", ">", a), tok("punct", ">", a + 1)]

    @add("ts.json", "ts-format-a", "'return' relabelled ident")
    def _(v):
        v["result"]["tokens"][find(v, "return")]["class"] = "ident"

    @add("ts.json", "ts-contextual-keywords", "contextual 'type' relabelled keyword")
    def _(v):
        v["result"]["tokens"][find(v, "type")]["class"] = "keyword"

    @add("ts.json", "ts-property-keywords", "'.catch' relabelled keyword")
    def _(v):
        v["result"]["tokens"][find(v, "catch")]["class"] = "keyword"

    @add("ts.json", "ts-unicode-escape-ident", "escaped '\\u0069f' relabelled keyword")
    def _(v):
        v["result"]["tokens"][find(v, "\\u0069f")]["class"] = "keyword"

    @add("ts.json", "ts-optional-chaining", "'?.5' lexed as '?.' '5'")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, ".5")
        a = ts[i - 1]["span"][0]
        ts[i - 1:i + 1] = [tok("punct", "?.", a), tok("number", "5", a + 2)]

    @add("ts.json", "ts-legacy-octal", "'07.5' lexed as one number")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, "07")
        ts[i:i + 2] = [tok("number", "07.5", ts[i]["span"][0])]

    @add("ts.json", "ts-hashbang", "hashbang line tokenized")
    def _(v):
        v["result"]["tokens"].insert(0, tok("ident", "node", 15))

    @add("ts.json", "ts-html-comment", "'<!--' treated as a line comment")
    def _(v):
        ts = v["result"]["tokens"]
        del ts[1:5]

    @add("tsx.json", "tsx-attr-keyword-names", "JSX attribute name 'class' relabelled keyword")
    def _(v):
        v["result"]["tokens"][find(v, "class")]["class"] = "keyword"

    @add("ts.json", "ts-no-asi", "semicolon inserted after '1' (ASI)")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, "1")
        e = ts[i]["span"][1]
        ts.insert(i + 1, {"class": "punct", "text": ";", "span": [e, e]})

    @add("ts.json", "ts-regex-after-keyword", "regex flags split from the body")
    def _(v):
        ts = v["result"]["tokens"]
        i = find(v, "/y/i")
        a = ts[i]["span"][0]
        ts[i:i + 1] = [tok("regex", "/y/", a), tok("ident", "i", a + 3)]

    @add("ts.json", "ts-template-nested", "template-head relabelled template")
    def _(v):
        v["result"]["tokens"][find(v, "`a${")]["class"] = "template"

    @add("ts.json", "ts-unicode-boundary", "U+309B rejected as an identifier start (XID instead of ID)")
    def _(v):
        a = v["result"]["tokens"][find(v, "\u309b1")]["span"][0]
        v["result"] = {"status": "error", "error": {"code": "illegal-character", "offset": a}}

    @add("ts.json", "ts-err-hash", "invented error code")
    def _(v):
        v["result"]["error"]["code"] = "invalid-token"

    @add("ts.json", "ts-err-unterminated-string", "error offset moved off the token start")
    def _(v):
        v["result"]["error"]["offset"] = 8

    @add("ts.json", "ts-err-unterminated-before-malformed", "malformed reported before unterminated")
    def _(v):
        v["result"]["error"]["code"] = "malformed-literal"

    @add("ts.json", "ts-repeated", "winnowing tie broken leftmost", rehash=False)
    def _(v):
        for ch in ("exact", "normalized"):
            c = v["result"]["channels"][ch]
            hs = [int(g["hash"], 16) for g in c["kgrams"]]
            sel = [min(range(s, s + 4), key=lambda j: (hs[j], j)) for s in range(len(hs) - 3)]
            c["windowSelections"] = sel
            c["fingerprints"] = [c["kgrams"][p] for p in sorted(set(sel))]

    @add("ts.json", "ts-exact-k", "hash corrupted", rehash=False)
    def _(v):
        g = v["result"]["channels"]["exact"]["kgrams"][0]
        g["hash"] = "%016x" % (int(g["hash"], 16) ^ 1)

    return M


def self_test(docs):
    rejected, failures = 0, []
    for f, vid, desc, fn, do_rehash in mutations():
        doc, cfg = copy.deepcopy(docs[f][0]), docs[f][1]
        v = next(x for x in doc["vectors"] if x["id"] == vid)
        fn(v)
        if do_rehash:
            rehash(v, cfg)
        # keep format pairs consistent so only the targeted layer is wrong
        if vid == "ts-format-a":
            w = next(x for x in doc["vectors"] if x["id"] == "ts-format-b")
            w["result"]["tokens"][find(w, "return")]["class"] = "ident"
            rehash(w, cfg)
        try:
            run_file(doc, cfg)
        except CheckError:
            rejected += 1
            continue
        failures.append(desc)
    return rejected, failures


def check_paired(docs):
    errors = {v["id"] for d, _ in docs.values() for v in d["vectors"] if v["result"]["status"] == "error"}
    for d, _ in docs.values():
        for v in d["vectors"]:
            if "pairedRejection" in v:
                require(v["pairedRejection"] in errors, f"{v['id']}: pairedRejection {v['pairedRejection']} "
                                                        "is not an error vector")


def main():
    neg, total = check_negative_configs()
    print(f"PASS config-negative-typescript.json: {neg}/{total} invalid configurations rejected")
    docs = {}
    for name, profile in FILES:
        doc, cfg = load(name)
        docs[name] = (doc, cfg)
        st = run_file(doc, cfg)
        print(f"PASS {name} profile={cfg['profile']}/draft-1 config={doc['configSha256'][:16]}... "
              f"vectors={len(doc['vectors'])} tokens={st['tokens']} kgrams={st['kgrams']} "
              f"fingerprints={st['fingerprints']} tie-windows={st['tie-windows']} errors={st['errors']} "
              f"(code and offset re-derived) pairs={st['pairs']} classes={len(st['classes'])}")
    check_paired(docs)
    print("PASS every accepted vector has derivation=hand and a pairedRejection that is an error vector")
    rejected, failures = self_test(docs)
    total = rejected + len(failures)
    lexical = sum(1 for m in mutations() if m[2] not in ("winnowing tie broken leftmost", "hash corrupted"))
    if failures:
        for d in failures:
            print(f"FAIL mutation not rejected: {d}")
        sys.exit(1)
    print(f"PASS mutation self-test: {rejected}/{total} corruptions rejected ({lexical} lexical)")


if __name__ == "__main__":
    try:
        main()
    except CheckError as e:
        print(f"FAIL {e}")
        sys.exit(1)
