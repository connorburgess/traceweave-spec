#!/usr/bin/env python3
"""Print the tslex.py result for each file as one JSON line: byte spans, for crosscheck.js --corpus.

Usage: python3 -I lex_json.py PROFILE FILE...   (no size limit; shared pre-lexing checks applied)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tslex  # noqa: E402

profile = sys.argv[1]
for name in sys.argv[2:]:
    data = Path(name).read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        print(json.dumps({"file": name, "error": ["invalid-utf8", e.start]}))
        continue
    boff = [0]
    for ch in text:
        boff.append(boff[-1] + len(ch.encode("utf-8")))
    bad = next((("bom" if c == "﻿" else "nul", boff[i]) for i, c in enumerate(text) if c in "﻿\x00"), None)
    if bad:
        print(json.dumps({"file": name, "error": list(bad)}))
        continue
    r = tslex.lex(text, profile)
    if r[0] == "error":
        print(json.dumps({"file": name, "error": [r[1], boff[r[2]]]}))
    else:
        print(json.dumps({"file": name, "tokens": [[c, boff[a], boff[b]] for c, a, b in r[1]]}))
