#!/usr/bin/env python3
"""Check the extraction requirement map (gate M1.5) and the registration item map (gate M1.1).

Standard library only. Run from anywhere: python3 -I tools/check_requirement_map.py

M1.5, test-vectors/extraction/requirement-map.json against spec/extraction.md:
  * every "MUST" occurrence in the document lies inside a mapped sentence
    (unmapped must be 0), and every mapped sentence still occurs verbatim;
  * each entry has one clause per "MUST" in its sentence;
  * a testable clause cites at least one id in failsOn and at least one
    negative fixture (an error vector, a negative configuration, or a
    self-test that rejects a violating corruption);
  * where a clause names expected error codes, every cited rejection carries one;
  * an implementation-test clause cites tests of the implementation repository
    as impl:<rev>:<path>:<name>; they are verified only when TW_IMPL_REPO names a
    checkout of that repository (otherwise counted as unverified external);
  * an untestable clause gives a reason and is marked for spot-check, and at
    least min(10, untestable) clauses are marked for spot-check;
  * every cited id exists (vector ids, configuration entries, record vectors,
    check_vectors.py self-tests listed by --list-tests, other checkers' self-test
    names found in their source).

M1.2: the derivationRule of every extraction vector file equals the definition
of "hand-derived" in ROADMAP.md (Definitions), with Markdown emphasis removed.

M1.1, profiles/code.md: the "Before registering a profile" list is parsed from
its sentence; the "Registration item map" table must have one row per item, a
link into spec/extraction.md with an existing heading anchor in both the Go
and the Rust column, no "TBD", and rows for the constructs the gate names.

A self-test then corrupts the map in memory (a dropped entry, a non-existent
id, a testable clause without a negative fixture) and requires each corruption
to be rejected.
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "spec/extraction.md"
MAP = ROOT / "test-vectors/extraction/requirement-map.json"
XV = ROOT / "test-vectors/extraction"
VECTOR_FILES = ["go.json", "rust.json", "limits-go.json", "limits-rust.json", "exclusion-rule.json"]
RECORDS = ROOT / "test-vectors/matching/records.json"
CODE = ROOT / "profiles/code.md"
CONSTRUCTS = ["Token classes", "Raw strings", "Nested comments", "Shebang", "BOM", "CRLF"]


class MapError(Exception):
    pass


def require(cond, msg):
    if not cond:
        raise MapError(msg)


def slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def known_ids():
    vectors, errors, codes = set(), set(), {}
    for name in VECTOR_FILES:
        for v in json.loads((XV / name).read_text(encoding="utf-8"))["vectors"]:
            vectors.add(v["id"])
            if v["result"]["status"] == "error":
                errors.add(v["id"])
                codes[v["id"]] = v["result"]["error"]["code"]
    cfg = json.loads((XV / "config-negative.json").read_text(encoding="utf-8"))
    negatives = {n["id"] for n in cfg["negatives"]}
    codes.update({"cfg:" + n["id"]: n["expectedResult"]["error"]["code"] for n in cfg["negatives"]})
    positives = {n["id"] for n in cfg["boundaryPositives"]}
    records = {r["id"] for r in json.loads(RECORDS.read_text(encoding="utf-8"))["records"]}
    listed = subprocess.run([sys.executable, "-I", str(XV / "check_vectors.py"), "--list-tests"],
                            capture_output=True, text=True, check=True).stdout
    selftests = {tuple(line.split("\t", 1)) for line in listed.splitlines() if line}
    return {"vectors": vectors, "errors": errors, "negatives": negatives, "positives": positives,
            "records": records, "selftests": selftests, "codes": codes}


def resolve(ident, ids):
    """Return 'negative' if the id is a negative fixture, 'positive' otherwise; raise if it does not exist."""
    if ident.startswith("cfg:"):
        key = ident[4:]
        require(key in ids["negatives"] | ids["positives"], f"unknown configuration entry {ident}")
        return "negative" if key in ids["negatives"] else "positive"
    if ident.startswith("record:"):
        require(ident[7:] in ids["records"], f"unknown record vector {ident}")
        return "positive"
    if ident.startswith("selftest:"):
        _, f, name = ident.split(":", 2)
        require((f, name) in ids["selftests"], f"unknown check_vectors.py self-test {ident}")
        return "negative"
    if ident.startswith("checker:"):
        _, path, text = ident.split(":", 2)
        p = ROOT / path
        require(p.is_file() and text in p.read_text(encoding="utf-8"), f"unknown checker self-test {ident}")
        return "negative"
    require(ident in ids["vectors"], f"unknown vector id {ident}")
    return "negative" if ident in ids["errors"] else "positive"


def check_external(ident):
    """impl:<rev>:<path>:<name>. True if verified against TW_IMPL_REPO, False if no checkout is configured."""
    require(ident.startswith("impl:") and ident.count(":") >= 3, f"malformed implementation test id {ident}")
    _, rev, path, name = ident.split(":", 3)
    repo = os.environ.get("TW_IMPL_REPO")
    if not repo:
        return False
    shown = subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], capture_output=True, text=True)
    require(shown.returncode == 0 and name in shown.stdout, f"implementation test not found: {ident}")
    return True


def check_derivation_rules():
    road = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    sec = road.split("## Definitions", 1)[1].split("\n## ", 1)[0]
    a = re.search(r"^- \*\*\(a\) (.*)$", sec, re.M).group(1)
    b = re.search(r"^- \*\*\(b\) (.*)$", sec, re.M).group(1)
    last = re.search(r"(A vector whose lexical layer was first produced by a tool.*?otherwise\.)", sec).group(1)
    rule = ("A vector is hand-derived when both of these hold: (a) " + a + " (b) " + b + " " + last).replace("**", "")
    for name in VECTOR_FILES + ["config-negative.json"]:
        got = json.loads((XV / name).read_text(encoding="utf-8")).get("derivationRule")
        require(got == rule, f"{name}: derivationRule differs from the ROADMAP.md definition of hand-derived")
    return len(VECTOR_FILES) + 1


def check_must_map(doc, rmap, ids):
    covered = [False] * len(doc)
    stats = {"MUST": 0, "testable": 0, "implementation-test": 0, "untestable": 0, "definitional": 0, "spot-check": 0,
             "unmapped": 0, "external-verified": 0, "external-unverified": 0}
    seen = set()
    for e in rmap["requirements"]:
        require(e["id"] not in seen, f"duplicate entry {e['id']}")
        seen.add(e["id"])
        sentence = e["sentence"]
        require(sentence in doc, f"{e['id']}: sentence no longer occurs in {DOC.name}: {sentence[:60]!r}")
        n = len(re.findall(r"\bMUST\b", sentence))
        require(n == len(e["clauses"]), f"{e['id']}: {n} MUST in the sentence, {len(e['clauses'])} clauses")
        for m in re.finditer(re.escape(sentence), doc):
            for i in range(m.start(), m.end()):
                covered[i] = True
        for c in e["clauses"]:
            kind = c["kind"]
            require(kind in ("testable", "implementation-test", "untestable", "definitional"), f"{e['id']}: unknown kind {kind}")
            stats[kind] += 1
            if c.get("spotCheck"):
                stats["spot-check"] += 1
            if kind == "testable":
                require(c["failsOn"], f"{e['id']}: testable clause without failsOn")
                for ident in c["failsOn"]:
                    resolve(ident, ids)
                negs = [ident for ident in c["negativeFixtures"] if resolve(ident, ids) == "negative"]
                require(negs, f"{e['id']}: testable clause without a negative fixture")
                require(len(negs) == len(c["negativeFixtures"]), f"{e['id']}: a negativeFixtures id is not a negative fixture")
                require(c.get("violation") and c.get("failsBecause"), f"{e['id']}: state the violation and why it fails")
                for ident in negs:
                    code = ids["codes"].get(ident)
                    if code is not None and "codes" in c:
                        require(code in c["codes"], f"{e['id']}: negative fixture {ident} has code {code}, not one of {c['codes']}")
            elif kind == "implementation-test":
                require(c.get("tests") and c.get("reason") and c.get("spotCheck") is True,
                        f"{e['id']}: implementation-test needs tests, a reason and spotCheck")
                for ident in c["tests"]:
                    stats["external-verified" if check_external(ident) else "external-unverified"] += 1
                for ident in c.get("related", []):
                    resolve(ident, ids)
            elif kind == "untestable":
                require(c.get("reason") and c.get("spotCheck") is True, f"{e['id']}: untestable needs a reason and spotCheck")
                for ident in c.get("related", []):
                    resolve(ident, ids)
                for ident in c.get("relatedTests", []):
                    check_external(ident)
            else:
                require(c.get("reason"), f"{e['id']}: definitional needs a reason")
    for m in re.finditer(r"\bMUST\b", doc):
        stats["MUST"] += 1
        if not covered[m.start()]:
            stats["unmapped"] += 1
            line = doc.count("\n", 0, m.start()) + 1
            raise MapError(f"unmapped MUST at {DOC.name} line {line}")
    require(stats["spot-check"] >= min(10, stats["untestable"]), "fewer spot-check clauses than min(10, untestable)")
    return stats


def check_item_map(code, doc):
    anchors = {slug(h) for h in re.findall(r"^#+ (.*)$", doc, re.M)}
    m = re.search(r"Before registering a profile, specify (.*?)\. ", code)
    require(m, "profiles/code.md: 'Before registering a profile' sentence not found")
    items = [x.strip() for x in re.split(r",\s*(?:and\s+)?", m.group(1))]
    section = code.split("## Registration item map", 1)
    require(len(section) == 2, "profiles/code.md: no 'Registration item map' section")
    rows = {}
    for line in section[1].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 3 and not set(cells[0]) <= set("- "):
            rows[cells[0].lower()] = cells
    require("TBD" not in section[1] and "tbd" not in section[1].lower().split(), "item map contains TBD")
    for item in items + CONSTRUCTS:
        cells = rows.get(item.lower())
        require(cells, f"item map: no row for {item!r}")
        for col, label in ((1, "Go"), (2, "Rust")):
            links = re.findall(r"\]\(\.\./spec/extraction\.md#([^)]+)\)", cells[col])
            if item != "Token classes" or col:
                require(links, f"item map: {item!r} has no {label} link into spec/extraction.md")
            for a in links:
                require(a in anchors, f"item map: {item!r} links to missing anchor #{a}")
    return len(items), len(CONSTRUCTS)


def self_test(doc, rmap, ids):
    cases = []
    m = copy.deepcopy(rmap)
    m["requirements"] = [e for e in m["requirements"] if e["id"] != "EX-07"]
    cases.append(("dropped entry", m))
    m = copy.deepcopy(rmap)
    next(c for e in m["requirements"] for c in e["clauses"] if c["kind"] == "testable")["failsOn"].append("no-such-vector")
    cases.append(("non-existent vector id", m))
    m = copy.deepcopy(rmap)
    c = next(c for e in m["requirements"] for c in e["clauses"] if c["kind"] == "testable")
    c["negativeFixtures"] = [x for x in c["failsOn"] if not ids["errors"] & {x}][:1] or ["go-unicode"]
    cases.append(("negative fixture that is a positive vector", m))
    m = copy.deepcopy(rmap)
    next(c for e in m["requirements"] for c in e["clauses"] if c["kind"] == "untestable").pop("spotCheck")
    cases.append(("untestable without spot-check", m))
    m = copy.deepcopy(rmap)
    m["requirements"][1]["sentence"] += " (edited)"
    cases.append(("sentence not in document", m))
    m = copy.deepcopy(rmap)
    next(c for e in m["requirements"] for c in e["clauses"] if "codes" in c)["codes"] = ["no-such-code"]
    cases.append(("negative fixture with another error code", m))
    missed = []
    for name, corrupted in cases:
        try:
            check_must_map(doc, corrupted, ids)
            missed.append(name)
        except MapError:
            pass
    require(not missed, f"self-test corruptions not detected: {missed}")
    return len(cases)


def main():
    doc = DOC.read_text(encoding="utf-8")
    rmap = json.loads(MAP.read_text(encoding="utf-8"))
    try:
        require(rmap["document"] == "spec/extraction.md", "map names another document")
        ids = known_ids()
        stats = check_must_map(doc, rmap, ids)
        corruptions = self_test(doc, rmap, ids)
        items, constructs = check_item_map(CODE.read_text(encoding="utf-8"), doc)
        rules = check_derivation_rules()
    except (MapError, KeyError, ValueError) as exc:
        print(f"FAIL requirement map: {exc}")
        return 1
    print(f"PASS M1.5 requirement map: MUST occurrences={stats['MUST']} unmapped={stats['unmapped']} "
          f"testable={stats['testable']} implementation-test={stats['implementation-test']} untestable={stats['untestable']} "
          f"definitional={stats['definitional']} marked-for-spot-check={stats['spot-check']} "
          f"self-test-corruptions-rejected={corruptions}/{corruptions}; implementation tests verified="
          f"{stats['external-verified']} unverified={stats['external-unverified']} (set TW_IMPL_REPO to verify)")
    print(f"PASS M1.2 derivationRule: {rules} vector files state the ROADMAP.md definition of hand-derived verbatim")
    print(f"PASS M1.1 item map: {items} registration items and {constructs} named constructs, each answered for Go and Rust "
          f"with links to existing sections of spec/extraction.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
