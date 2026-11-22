#!/usr/bin/env python3
"""Measure how many normalized fingerprints survive a semi -> no-semi reformat (profile TSOD-5b).

Usage: python3 -I harness/semi_survival.py FILE [MAX_TOKENS]

The reformat deletes every ';' token that is followed, after spaces or tabs only, by a
line terminator. Survival = share of the original's distinct normalized fingerprint
hashes that also occur in the reformatted input, under draft-1 (';' kept in normalized)
and draft-2 (';' dropped from normalized). ts-tokens, k=5, w=4.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check_vectors as cv  # noqa: E402
import tslex  # noqa: E402

text = Path(sys.argv[1]).read_text(encoding="utf-8")
r = tslex.lex(text, "ts-tokens")
assert r[0] == "ok", r
toks = r[1]
if len(sys.argv) > 2:
    toks = toks[:int(sys.argv[2])]
    text = text[:toks[-1][2]]
drop = set()
for n, (c, a, b) in enumerate(toks):
    if c == "punct" and text[a:b] == ";":
        j = b
        while j < len(text) and text[j] in " \t":
            j += 1
        if j < len(text) and text[j] in tslex.LINE_TERMINATORS:
            drop.add(n)


def fps(tokens, keep):
    cfg = {"profile": "ts-tokens", "profileVersion": "draft-2", "k": 5, "window": 4}
    ts = [{"class": c, "text": text[a:b], "span": [a, b]} for c, a, b in tokens]
    return {f["hash"] for f in cv.channels_for(ts, cfg, keep_semicolons=keep)["normalized"]["fingerprints"]}


variant = [t for n, t in enumerate(toks) if n not in drop]
print(f"{sys.argv[1]}: {len(toks)} tokens, {len(drop)} ';' removed by the reformat")
for label, keep in (("draft-1 (';' kept in normalized)", True), ("draft-2 (';' dropped from normalized)", False)):
    a, b = fps(toks, keep), fps(variant, keep)
    print(f"  {label}: {len(a & b)}/{len(a)} distinct normalized fingerprints survive = {100 * len(a & b) / len(a):.1f}%")
