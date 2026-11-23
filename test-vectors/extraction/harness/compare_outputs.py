#!/usr/bin/env python3
"""Prove that a revision of the extraction vectors changed metadata only.

Usage: python3 -I test-vectors/extraction/harness/compare_outputs.py BEFORE_REV

For every vector file present at BEFORE_REV (git revision) it requires, against
the working tree:

* configuration files (config-*.json except config-negative.json) and the
  Unicode table: byte-identical;
* every vector present before is still present, and its `inputBase64`,
  `inputText`, `inputDisplay` and complete `result` (status, tokens, spans,
  k-grams, hashes, window selections, fingerprints, error code and offset) are
  unchanged;
* every negative/positive configuration present before keeps its
  `configBase64`, `reason` and `expectedResult`;
* every header field present before is unchanged.

Only these additions are allowed: new vectors or configuration entries, and the
metadata fields listed in ALLOWED_NEW. It prints a summary and exits 1 on any
other difference. Standard library only; it runs git to read BEFORE_REV.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIR = "test-vectors/extraction"
ALLOWED_NEW = {"derivation", "derivationNote", "spanStarts", "vectorClasses", "pairedRejection", "pairedPositive"}
ALLOWED_NEW_HEADER = {"metadataRules", "derivationRule"}
OUTPUT_FIELDS = ("inputBase64", "inputText", "inputDisplay", "result")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def main(rev):
    names = [n for n in git("ls-tree", "--name-only", f"{rev}:{DIR}").decode().split() if n.endswith(".json")]
    problems, counts = [], {"files": 0, "identical-bytes": 0, "vectors-compared": 0, "vectors-added": 0,
                            "configs-compared": 0, "configs-added": 0}
    for name in names:
        old_raw = git("show", f"{rev}:{DIR}/{name}")
        new_raw = (ROOT / DIR / name).read_bytes()
        counts["files"] += 1
        if old_raw == new_raw:
            counts["identical-bytes"] += 1
            continue
        if name.startswith("config-") and name != "config-negative.json" or name.startswith("unicode-"):
            problems.append(f"{name}: bytes changed")
            continue
        old, new = json.loads(old_raw), json.loads(new_raw)
        for key, value in old.items():
            if key in ("vectors", "negatives", "boundaryPositives"):
                continue
            if new.get(key) != value:
                problems.append(f"{name}: header {key} changed")
        extra = set(new) - set(old) - ALLOWED_NEW_HEADER
        if extra:
            problems.append(f"{name}: unexpected new header fields {sorted(extra)}")
        for listkey, fields, kind in (("vectors", OUTPUT_FIELDS, "vectors"),
                                      ("negatives", ("configBase64", "reason", "expectedResult"), "configs"),
                                      ("boundaryPositives", ("configBase64", "reason"), "configs")):
            if listkey not in old:
                continue
            nby = {v["id"]: v for v in new[listkey]}
            for v in old[listkey]:
                w = nby.get(v["id"])
                if w is None:
                    problems.append(f"{name}: {v['id']} removed")
                    continue
                for f in fields:
                    if v.get(f) != w.get(f):
                        problems.append(f"{name}: {v['id']} {f} changed")
                for f in set(v) - set(fields):
                    if v[f] != w.get(f):
                        problems.append(f"{name}: {v['id']} {f} changed")
                for f in set(w) - set(v) - ALLOWED_NEW:
                    problems.append(f"{name}: {v['id']} unexpected new field {f}")
                counts[f"{kind}-compared"] += 1
            counts[f"{kind}-added"] += len(new[listkey]) - len(old[listkey])
    print("compare_outputs:", ", ".join(f"{k}={v}" for k, v in counts.items()))
    if problems:
        print("FAIL")
        for p in problems:
            print("  " + p)
        return 1
    print(f"PASS: every expected output present at {rev} is unchanged; only vectors, configuration entries and "
          f"the metadata fields {sorted(ALLOWED_NEW | ALLOWED_NEW_HEADER)} were added")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
