#!/usr/bin/env python3
"""Build ts.json, tsx.json and limits-ts.json (draft-2) from the hand-written sources.

This adds spans, k-grams, hashes and winnowing to hand-derived token streams.
It does not lex: a token's span is the first occurrence of its hand-written
text at or after the previous token's end. Standard library only.

Usage: python3 -I harness/build_vectors.py   (from extraction-vectors-typescript/)
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
sys.path.insert(0, str(HERE))
import vector_sources as src  # noqa: E402

DOMAIN = b"traceweave/token-kgram/draft-1"
VERSION = "draft-2"
LITERALS = {"ident", "privatename", "number", "bigint", "string", "template", "template-head", "template-middle",
            "template-tail", "regex", "jsx-text", "jsx-string"}


def config_bytes(profile, limit):
    return ('{"contract":"traceweave-token-winnow-draft-1","profile":"%s","profileVersion":"draft-2",'
            '"channels":["exact","normalized"],"k":5,"window":4,"hash":"sha256-first8-u64be",'
            '"maxInputBytes":%d}\n' % (profile, limit)).encode()


def lp(b):
    return len(b).to_bytes(4, "big") + b


def kgram_hash(profile, channel, k, pairs):
    h = hashlib.sha256()
    h.update(lp(DOMAIN) + lp(profile.encode()) + lp(VERSION.encode()) + lp(channel.encode()) + k.to_bytes(4, "big"))
    for cls, val in pairs:
        h.update(lp(cls.encode()) + lp(val.encode()))
    return h.digest()[:8].hex()


def winnow(hashes, w):
    """Sliding-window rightmost minimum (a loop, not the checker's sort)."""
    m = len(hashes)
    if m == 0:
        return [], False
    if m < w:
        best = 0
        for p in range(m):
            if hashes[p] <= hashes[best]:
                best = p
        return [best], True
    out = []
    for s in range(m - w + 1):
        best = s
        for p in range(s, s + w):
            if hashes[p] <= hashes[best]:
                best = p
        out.append(best)
    return out, False


def build(vid, tags, desc, inp, exp, profile, limit):
    data = inp if isinstance(inp, bytes) else inp.encode("utf-8")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    v = {"id": vid, "derivation": "hand", "tags": tags, "description": desc,
         "inputBase64": base64.b64encode(data).decode(), "inputText": text}
    if vid in src.PAIRED:
        v["pairedRejection"] = src.PAIRED[vid]
    if text is None:
        v["inputDisplay"] = "".join(chr(b) if 32 <= b < 127 else "\\x%02x" % b for b in data)
    if isinstance(exp, tuple):
        v["result"] = {"status": "error", "error": {"code": exp[1], "offset": exp[2]}}
        return v
    assert len(data) <= limit, vid
    toks, pos = [], 0
    for cls, t in exp:
        at = data.find(t.encode(), pos)
        if at < 0:
            raise SystemExit(f"{vid}: token {t!r} not found after byte {pos}")
        toks.append({"class": cls, "text": t, "span": [at, at + len(t.encode())]})
        pos = at + len(t.encode())
    k, w = 5, 4
    res = {"status": "ok" if len(toks) >= k else "insufficient-tokens", "tokenCount": len(toks), "tokens": toks,
           "channels": {}}
    for ch in ("exact", "normalized"):
        # Profile §6 (TSOD-5b (c)): the normalized stream omits every punct ';'.
        idx = [n for n, t in enumerate(toks) if ch == "exact" or (t["class"], t["text"]) != ("punct", ";")]
        sub = [toks[n] for n in idx]
        vals = [t["text"] if ch == "exact" or t["class"] not in LITERALS else "" for t in sub]
        pairs = [(t["class"], x) for t, x in zip(sub, vals)]
        kg = [{"position": i, "hash": kgram_hash(profile, ch, k, pairs[i:i + k]),
               "span": [sub[i]["span"][0], sub[i + k - 1]["span"][1]]} for i in range(max(0, len(sub) - k + 1))]
        sel, partial = winnow([int(g["hash"], 16) for g in kg], w)
        fps = [kg[p] for p in sorted(set(sel))]
        c = {"tokenIndices": idx, "values": vals} if ch == "normalized" else {}
        c.update({"kgrams": kg, "windowSelections": sel, "partialWindow": partial, "fingerprints": fps})
        res["channels"][ch] = c
    v["result"] = res
    return v


def write(name, profile, cfgfile, limit, items):
    cfg = config_bytes(profile, limit)
    (OUT / cfgfile).write_bytes(cfg)
    doc = {"contract": "traceweave-token-winnow-draft-1", "profile": profile, "profileVersion": VERSION,
           "configFile": cfgfile, "configSha256": hashlib.sha256(cfg).hexdigest(), "k": 5, "window": 4,
           "normalizedExclusions": [{"class": "punct", "text": ";"}],
           "lexingCheck": "Token streams are hand-derived (harness/vector_sources.py); check_vectors.py re-lexes "
                          "every input with tslex.py and harness/crosscheck.js compares them with the TypeScript "
                          "6.0.3 parser and scanner.",
           "vectors": [build(*it, profile, limit) for it in items]}
    (OUT / name).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {name}: {len(items)} vectors, config {cfgfile} sha256={doc['configSha256']}")


if __name__ == "__main__":
    write("ts.json", "ts-tokens", "config-ts.json", 1048576, src.TS)
    write("tsx.json", "tsx-tokens", "config-tsx.json", 1048576, src.TSX)
    write("limits-ts.json", "ts-tokens", "config-ts-limit16.json", 16, src.LIMITS)
