#!/usr/bin/env python3
"""Build py.json and limits-py.json (py-tokens draft-1) from the hand-written sources.

This adds spans, k-grams, hashes and winnowing to hand-derived token streams.
It does not lex: span placement follows the rules in vector_sources.py. It
also writes the configuration files and config-negative-python.json.
Standard library only.

Usage: python3 -I harness/build_vectors.py   (from extraction-vectors-python/)
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
PROFILE, VERSION = "py-tokens", "draft-1"
LITERALS = {"ident", "int", "float", "imag", "string", "bytes", "fstring-start", "fstring-middle", "fstring-end",
            "tstring-start", "tstring-middle", "tstring-end"}
ZERO_WIDTH = {"newline", "indent", "dedent"}


def config_bytes(profile=PROFILE, version=VERSION, limit=1048576, **over):
    fields = {"contract": "traceweave-token-winnow-draft-1", "profile": profile, "profileVersion": version,
              "channels": ["exact", "normalized"], "k": 5, "window": 4, "hash": "sha256-first8-u64be",
              "maxInputBytes": limit}
    fields.update(over)
    return (json.dumps(fields, separators=(",", ":")) + "\n").encode()


def lp(b):
    return len(b).to_bytes(4, "big") + b


def kgram_hash(channel, k, pairs):
    h = hashlib.sha256()
    h.update(lp(DOMAIN) + lp(PROFILE.encode()) + lp(VERSION.encode()) + lp(channel.encode()) + k.to_bytes(4, "big"))
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


def place(vid, text, exp):
    """Code-point spans for the hand-written stream (rules in vector_sources.py)."""
    spans, pos = [], 0
    for n, (cls, t, at) in enumerate(exp):
        if cls == "newline" and at is not None:
            spans.append((at, at))
            continue
        if cls == "newline":
            cands = [i for i in (text.find("\n", pos), text.find("\r", pos)) if i >= 0]
            p = min(cands) if cands else len(text)
            spans.append((p, p))
            continue
        if cls in ("indent", "dedent"):
            nxt = next(((t2, a2) for c2, t2, a2 in exp[n + 1:] if c2 not in ZERO_WIDTH), None)
            if nxt is None:
                p = len(text)
            else:
                p = nxt[1] if nxt[1] is not None else text.find(nxt[0], pos)
            spans.append((p, p))
            pos = p
            continue
        a = at if at is not None else text.find(t, pos)
        if a < 0 or text[a:a + len(t)] != t:
            raise SystemExit(f"{vid}: token {t!r} not found after code point {pos}")
        spans.append((a, a + len(t)))
        pos = a + len(t)
    return spans


def build(vid, tags, desc, inp, exp, limit):
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
        kind, code, off = exp
        if kind == "error" and text is not None:
            off = len(text[:off].encode("utf-8"))
        v["result"] = {"status": "error", "error": {"code": code, "offset": off}}
        return v
    assert len(data) <= limit, vid
    boff = [0]
    for ch in text:
        boff.append(boff[-1] + len(ch.encode("utf-8")))
    toks = []
    for (cls, t, _), (a, b) in zip(exp, place(vid, text, exp)):
        toks.append({"class": cls, "text": text[a:b], "span": [boff[a], boff[b]]})
    k, w = 5, 4
    res = {"status": "ok" if len(toks) >= k else "insufficient-tokens", "tokenCount": len(toks), "tokens": toks,
           "channels": {}}
    for ch in ("exact", "normalized"):
        vals = [t["text"] if ch == "exact" or t["class"] not in LITERALS else "" for t in toks]
        pairs = [(t["class"], x) for t, x in zip(toks, vals)]
        kg = [{"position": i, "hash": kgram_hash(ch, k, pairs[i:i + k]),
               "span": [toks[i]["span"][0], toks[i + k - 1]["span"][1]]} for i in range(max(0, len(toks) - k + 1))]
        sel, partial = winnow([int(g["hash"], 16) for g in kg], w)
        c = {"values": vals} if ch == "normalized" else {}
        c.update({"kgrams": kg, "windowSelections": sel, "partialWindow": partial,
                  "fingerprints": [kg[p] for p in sorted(set(sel))]})
        res["channels"][ch] = c
    v["result"] = res
    return v


def write(name, cfgfile, limit, items):
    cfg = config_bytes(limit=limit)
    (OUT / cfgfile).write_bytes(cfg)
    doc = {"contract": "traceweave-token-winnow-draft-1", "profile": PROFILE, "profileVersion": VERSION,
           "configFile": cfgfile, "configSha256": hashlib.sha256(cfg).hexdigest(), "k": 5, "window": 4,
           "normalizedExclusions": [],
           "lexingCheck": "Token streams are hand-derived (harness/vector_sources.py); check_vectors.py re-lexes "
                          "every input with pylex.py and checks layout, keyword, operator, number and prefix rules "
                          "on the recorded stream; harness/crosscheck.py compares them with the CPython 3.14.6 "
                          "tokenizer.",
           "vectors": [build(*it, limit) for it in items]}
    (OUT / name).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {name}: {len(items)} vectors, config {cfgfile} sha256={doc['configSha256']}")


def negatives():
    good = config_bytes().decode()
    items = [
        ("unknown profile python-tokens", config_bytes(profile="python-tokens")),
        ("unknown profile py3-tokens", config_bytes(profile="py3-tokens")),
        ("unknown profile version draft-2", config_bytes(version="draft-2")),
        ("profile id is not versioned by interpreter (py314-tokens)", config_bytes(profile="py314-tokens")),
        ("uppercase profile", config_bytes(profile="PY-tokens")),
        ("ts profile id is not implemented by a Python-only implementation", config_bytes(profile="ts-tokens",
                                                                                           version="draft-2")),
        ("no trailing LF", good[:-1].encode()),
        ("CRLF line end", (good[:-1] + "\r\n").encode()),
        ("space after colon", good.replace('"k":5', '"k": 5').encode()),
        ("keys reordered", good.replace('"k":5,"window":4', '"window":4,"k":5').encode()),
        ("channels reversed", good.replace('["exact","normalized"]', '["normalized","exact"]').encode()),
        ("exact channel only", good.replace('["exact","normalized"]', '["exact"]').encode()),
        ("k zero", config_bytes(k=0)),
        ("k above the contract bound 16", config_bytes(k=17)),
        ("window above the contract bound 128", config_bytes(window=129)),
        ("maxInputBytes above the contract bound 8388608", config_bytes(limit=8388609)),
        ("duplicate profile key", good.replace('"profile":"py-tokens"',
                                               '"profile":"py-tokens","profile":"py-tokens"').encode()),
        ("escaped profile string", good.replace('"py-tokens"', '"py\\u002dtokens"').encode()),
        ("float k", good.replace('"k":5', '"k":5.0').encode()),
        ("normalizedExclusions is not a configuration key",
         good.replace(',"maxInputBytes"', ',"normalizedExclusions":[],"maxInputBytes"').encode()),
    ]
    out = [{"why": why, "configBase64": base64.b64encode(b).decode(),
            "expectedResult": {"status": "error", "error": {"code": "unsupported-config", "offset": None},
                               "profile": None, "profileVersion": None,
                               "configSha256": hashlib.sha256(b).hexdigest(), "inputSha256": None,
                               "inputLength": None}} for why, b in items]
    (OUT / "config-negative-python.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"wrote config-negative-python.json: {len(out)} negatives")


if __name__ == "__main__":
    write("py.json", "config-py.json", 1048576, src.PY)
    write("limits-py.json", "config-py-limit16.json", 16, src.LIMITS)
    negatives()
