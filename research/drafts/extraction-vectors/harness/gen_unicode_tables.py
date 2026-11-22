#!/usr/bin/env python3
"""Derive the pinned identifier tables from Unicode 17.0.0 UCD files.

Usage: python3 gen_unicode_tables.py UCD_DIR OUTPUT_JSON

UCD_DIR must hold the files below with exactly these SHA-256 digests; any
other bytes are rejected. Download them from
https://www.unicode.org/Public/17.0.0/ucd/ . Output is deterministic, so a
rerun must reproduce the committed unicode-17.0.0-tables.json byte for byte.
Standard library only.
"""
import hashlib
import json
import sys
from pathlib import Path

SOURCES = {
    "UnicodeData.txt": "2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c",
    "DerivedCoreProperties.txt": "24c7fed1195c482faaefd5c1e7eb821c5ee1fb6de07ecdbaa64b56a99da22c08",
    "DerivedNormalizationProps.txt": "71fd6a206a2c0cdd41feb6b7f656aa31091db45e9cedc926985d718397f9e488",
    "CompositionExclusions.txt": "2f239196ef3b5b61db5cc476e9bd80f534d15aa1b74e1be1dea5d042a344c85f",
}


def ranges(points):
    out = []
    for cp in sorted(points):
        if out and out[-1][1] == cp - 1:
            out[-1][1] = cp
        else:
            out.append([cp, cp])
    return out


def main(ucd, output):
    ucd = Path(ucd)
    for name, digest in SOURCES.items():
        actual = hashlib.sha256((ucd / name).read_bytes()).hexdigest()
        if actual != digest:
            sys.exit(f"{name}: SHA-256 {actual} != pinned {digest}")
    gc = {}
    first = None
    for line in (ucd / "UnicodeData.txt").read_text(encoding="utf-8").splitlines():
        fields = line.split(";")
        cp, name, cat = int(fields[0], 16), fields[1], fields[2]
        if name.endswith(", First>"):
            first = cp
            continue
        if name.endswith(", Last>"):
            for c in range(first, cp + 1):
                gc[c] = cat
            first = None
            continue
        gc[cp] = cat
    props = {"XID_Start": set(), "XID_Continue": set()}
    for line in (ucd / "DerivedCoreProperties.txt").read_text(encoding="utf-8").splitlines():
        body = line.split("#", 1)[0].strip()
        if not body:
            continue
        cps, prop = [x.strip() for x in body.split(";")[:2]]
        if prop in props:
            lo, _, hi = cps.partition("..")
            props[prop].update(range(int(lo, 16), int(hi or lo, 16) + 1))
    table = {
        "unicodeVersion": "17.0.0",
        "sources": SOURCES,
        "properties": {
            "go_letter": ranges([c for c, k in gc.items() if k in ("Lu", "Ll", "Lt", "Lm", "Lo")] + [0x5F]),
            "go_digit": ranges([c for c, k in gc.items() if k == "Nd"]),
            "xid_start": ranges(props["XID_Start"]),
            "xid_continue": ranges(props["XID_Continue"]),
        },
        "assigned": ranges([c for c, k in gc.items() if k != "Cn"]),
    }
    lines = ["{", f'  "unicodeVersion": "{table["unicodeVersion"]}",',
             '  "sources": ' + json.dumps(SOURCES, separators=(", ", ": ")) + ",", '  "properties": {']
    names = list(table["properties"])
    for i, n in enumerate(names):
        lines.append(f'    "{n}": ' + json.dumps(table["properties"][n], separators=(",", ":")) + ("," if i < len(names) - 1 else ""))
    lines.append("  },")
    lines.append('  "assigned": ' + json.dumps(table["assigned"], separators=(",", ":")))
    lines.append("}")
    Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
