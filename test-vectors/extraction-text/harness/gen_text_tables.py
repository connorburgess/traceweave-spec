#!/usr/bin/env python3
"""Derive the pinned text-profile tables from Unicode 17.0.0 data files.

Usage: python3 -I gen_text_tables.py DATA_DIR OUTPUT_JSON

DATA_DIR must hold the six files below with exactly these SHA-256 digests;
any other bytes are rejected. The UCD files come from
https://www.unicode.org/Public/17.0.0/ucd/ and confusables.txt from
https://www.unicode.org/Public/17.0.0/security/ . Output is deterministic:
a rerun must reproduce the committed text-tables-17.0.0.json byte for byte.
Standard library only; Python's own unicodedata module is not used.
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
    "PropList.txt": "130dcddcaadaf071008bdfce1e7743e04fdfbc910886f017d9f9ac931d8c64dd",
    "confusables.txt": "091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a",
}
WORD_CATEGORIES = {"Lu", "Ll", "Lt", "Lm", "Lo", "Mn", "Mc", "Me", "Nd", "Nl", "No"}


def ranges(points):
    out = []
    for cp in sorted(points):
        if out and out[-1][1] == cp - 1:
            out[-1][1] = cp
        else:
            out.append([cp, cp])
    return out


def data_lines(path):
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        body = line.split("#", 1)[0].strip()
        if body:
            yield [f.strip() for f in body.split(";")]


def cp_range(field):
    lo, _, hi = field.partition("..")
    return range(int(lo, 16), int(hi or lo, 16) + 1)


def main(data_dir, output):
    d = Path(data_dir)
    for name, digest in SOURCES.items():
        actual = hashlib.sha256((d / name).read_bytes()).hexdigest()
        if actual != digest:
            sys.exit(f"{name}: SHA-256 {actual} != pinned {digest}")
    gc, ccc, decomp = {}, {}, {}
    first = None
    for line in (d / "UnicodeData.txt").read_text(encoding="utf-8").splitlines():
        f = line.split(";")
        cp, name, cat = int(f[0], 16), f[1], f[2]
        if name.endswith(", First>"):
            first = cp
            continue
        span = range(first, cp + 1) if name.endswith(", Last>") else range(cp, cp + 1)
        first = None
        for c in span:
            gc[c] = cat
            if int(f[3]):
                ccc[c] = int(f[3])
        if f[5] and not f[5].startswith("<"):
            decomp[cp] = [int(x, 16) for x in f[5].split()]
    di = set()
    for fields in data_lines(d / "DerivedCoreProperties.txt"):
        if fields[1] == "Default_Ignorable_Code_Point":
            di.update(cp_range(fields[0]))
    ideo, white = set(), set()
    for fields in data_lines(d / "PropList.txt"):
        if fields[1] == "Ideographic":
            ideo.update(cp_range(fields[0]))
        elif fields[1] == "White_Space":
            white.update(cp_range(fields[0]))
    fce, nfkccf = set(), []
    for fields in data_lines(d / "DerivedNormalizationProps.txt"):
        if fields[1] == "Full_Composition_Exclusion":
            fce.update(cp_range(fields[0]))
        elif fields[1] == "NFKC_CF":
            r = cp_range(fields[0])
            nfkccf.append([r.start, r.stop - 1, [int(x, 16) for x in fields[2].split()]])
    conf = []
    for fields in data_lines(d / "confusables.txt"):
        conf.append([int(fields[0], 16), [int(x, 16) for x in fields[1].split()]])
    # Sanity: CompositionExclusions.txt is a subset of Full_Composition_Exclusion.
    for fields in data_lines(d / "CompositionExclusions.txt"):
        assert set(cp_range(fields[0])) <= fce
    ignorable = di
    ideographic = ideo - di
    word = {c for c, k in gc.items() if k in WORD_CATEGORIES} - di - ideo
    assert not (white & (ignorable | ideographic | word)), "White_Space must be a separator"
    table = {
        "unicodeVersion": "17.0.0",
        "sources": SOURCES,
        "classes": {"ignorable": ranges(ignorable), "ideographic": ranges(ideographic), "word": ranges(word)},
        "whiteSpace": ranges(white),
        "ccc": [[lo, hi, ccc[lo]] for lo, hi in _ranges_by_value(ccc)],
        "canonicalDecomposition": sorted([k, v] for k, v in decomp.items()),
        "fullCompositionExclusion": ranges(fce),
        "nfkcCasefold": sorted(nfkccf),
        "confusables": sorted(conf),
    }
    out = ["{"]
    keys = list(table)
    for i, key in enumerate(keys):
        sep = "," if i < len(keys) - 1 else ""
        val = table[key]
        if isinstance(val, list) and val and isinstance(val[0], list):
            out.append(f'  "{key}": [')
            for j, item in enumerate(val):
                out.append("    " + json.dumps(item, separators=(",", ":")) + ("," if j < len(val) - 1 else ""))
            out.append("  ]" + sep)
        elif key == "classes":
            out.append('  "classes": {')
            names = list(val)
            for j, n in enumerate(names):
                out.append(f'    "{n}": ' + json.dumps(val[n], separators=(",", ":")) + ("," if j < len(names) - 1 else ""))
            out.append("  }" + sep)
        else:
            out.append(f'  "{key}": ' + json.dumps(val, separators=(", ", ": ")) + sep)
    out.append("}")
    Path(output).write_bytes(("\n".join(out) + "\n").encode("utf-8"))


def _ranges_by_value(mapping):
    out = []
    for cp in sorted(mapping):
        if out and out[-1][1] == cp - 1 and mapping[out[-1][0]] == mapping[cp]:
            out[-1][1] = cp
        else:
            out.append([cp, cp])
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
