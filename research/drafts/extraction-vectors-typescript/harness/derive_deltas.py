#!/usr/bin/env python3
"""Re-derive the profile's Unicode deltas from the digest-pinned UCD 17.0.0 files.

Usage: python3 -I harness/derive_deltas.py UCD_DIR

Checks that ID_Start minus XID_Start, ID_Continue minus XID_Continue, XID minus ID
(must be empty) and General_Category Zs equal the constants in tslex.py.
UCD_DIR needs UnicodeData.txt and DerivedCoreProperties.txt with the digests
pinned in extraction-contract.md §3a. Standard library only.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tslex  # noqa: E402

PINNED = {"UnicodeData.txt": "2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c",
          "DerivedCoreProperties.txt": "24c7fed1195c482faaefd5c1e7eb821c5ee1fb6de07ecdbaa64b56a99da22c08"}
ucd = Path(sys.argv[1])
for name, digest in PINNED.items():
    if hashlib.sha256((ucd / name).read_bytes()).hexdigest() != digest:
        sys.exit(f"FAIL {name}: digest differs from the pinned value")
props = {}
for line in (ucd / "DerivedCoreProperties.txt").read_text(encoding="utf-8").splitlines():
    line = line.split("#")[0].strip()
    if not line:
        continue
    rng, prop = [x.strip() for x in line.split(";")[:2]]
    a, _, b = rng.partition("..")
    props.setdefault(prop, set()).update(range(int(a, 16), int(b or a, 16) + 1))
zs = {int(f[0], 16) for f in (l.split(";") for l in (ucd / "UnicodeData.txt").read_text().splitlines()) if f[2] == "Zs"}
checks = [("ID_Start - XID_Start", props["ID_Start"] - props["XID_Start"], tslex.ID_START_EXTRA),
          ("ID_Continue - XID_Continue", props["ID_Continue"] - props["XID_Continue"], tslex.ID_CONTINUE_EXTRA),
          ("XID_Start - ID_Start", props["XID_Start"] - props["ID_Start"], set()),
          ("XID_Continue - ID_Continue", props["XID_Continue"] - props["ID_Continue"], set()),
          ("Zs", zs, tslex.ZS),
          ("ZWNJ/ZWJ in ID_Continue", {0x200C, 0x200D} & props["ID_Continue"], {0x200C, 0x200D})]
bad = [name for name, got, want in checks if set(got) != set(want)]
for name, got, _ in checks:
    print(f"{'FAIL' if name in bad else 'PASS'} {name}: {len(got)} code points")
sys.exit(1 if bad else 0)
