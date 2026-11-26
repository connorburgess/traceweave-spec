#!/usr/bin/env python3
"""Check the extraction requirement map (gate M1.5) and the registration item map (gate M1.1).

M5.1 extends the same per-clause checks to every UTF-8 file in spec/ and
profiles/, retaining the reviewed extraction map as its delegated inventory.
New files and occurrences are scanned independently of the release map.

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

M1.2: the derivationRule of every extraction vector file starts with the
definition of "hand-derived" in ROADMAP.md (Definitions), verbatim with Markdown
emphasis removed; the five vector files then state how it applies (builder, not
an implementation under test; independent recomputation; spanStarts rule).

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
import ast
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
    if ident.startswith("unittest:"):
        _, filename, test_id = ident.split(":", 2)
        path = ROOT / filename
        require(path.resolve().is_relative_to(ROOT) and path.is_file(), f"unknown test file {ident}")
        cls, method = test_id.split(".", 1)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        tests = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == cls
                 for node in node.body if isinstance(node, ast.FunctionDef) and node.name == method]
        require(len(tests) == 1 and method.startswith("test_"), f"unknown unittest method {ident}")
        require(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr.startswith("assert") for node in ast.walk(tests[0])),
                f"test has no assertion {ident}")
        return "negative"
    if ident.startswith("registered:"):
        registry = json.loads((ROOT / "test-vectors/requirements/checker-tests.json").read_text(encoding="utf-8"))
        key = ident.split(":", 1)[1]
        require(key in registry, f"unknown registered checker test {ident}")
        test = registry[key]
        require(test.get("description"), f"checker test lacks failure description {ident}")
        return resolve("checker:" + test["checker"] + ":" + test["locator"], ids)
    if ident.startswith("negative:"):
        path = ROOT / ident.split(":", 1)[1]
        require(path.resolve().is_relative_to(ROOT) and path.is_file(), f"unknown negative fixture {ident}")
        require(path.parent == ROOT / "test-vectors/registration/negative", f"not a promoted negative fixture {ident}")
        data = json.loads(path.read_text(encoding="utf-8"))
        require(data["fixture"]["expect"]["code"], f"negative fixture lacks expected rejection {ident}")
        return "negative"
    if ident.startswith("rejection:"):
        _, filename, key = ident.split(":", 2)
        path = ROOT / filename
        require(path.resolve().is_relative_to(ROOT) and path.is_file(), f"unknown rejection file {ident}")
        matches = [v for v in json.loads(path.read_text(encoding="utf-8"))["rejections"] if v["id"] == key]
        require(len(matches) == 1 and matches[0].get("mutation") and matches[0].get("layer"),
                f"unknown rejection mutation {ident}")
        return "negative"
    if ident.startswith("vector:"):
        _, filename, key = ident.split(":", 2)
        path = ROOT / filename
        require(path.resolve().is_relative_to(ROOT) and path.is_file(), f"unknown vector file {ident}")
        vectors = json.loads(path.read_text(encoding="utf-8"))["vectors"]
        matches = [v for v in vectors if v["id"] == key]
        require(len(matches) == 1, f"unknown or ambiguous vector {ident}")
        return "negative" if matches[0]["result"]["status"] == "error" else "positive"
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
        got = json.loads((XV / name).read_text(encoding="utf-8")).get("derivationRule") or ""
        require(got.startswith(rule), f"{name}: derivationRule does not start with the ROADMAP.md definition of hand-derived")
        if name in VECTOR_FILES:  # the application to these vectors (review section 11)
            for phrase in ("computed by this specification's own builder", "not by an implementation under test",
                           "independently recomputed", "spanStarts: hand"):
                require(phrase in got, f"{name}: derivationRule application lacks {phrase!r}")
    return len(VECTOR_FILES) + 1


def check_must_map(doc, rmap, ids, document="spec/extraction.md"):
    covered = [False] * len(doc)
    stats = {"MUST": 0, "testable": 0, "implementation-test": 0, "untestable": 0, "definitional": 0, "spot-check": 0,
             "unmapped": 0, "external-verified": 0, "external-unverified": 0}
    seen = set()
    for e in rmap["requirements"]:
        require(e["id"] not in seen, f"duplicate entry {e['id']}")
        seen.add(e["id"])
        sentence = e["sentence"]
        require(sentence in doc, f"{e['id']}: sentence no longer occurs in {document}: {sentence[:60]!r}")
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
            raise MapError(f"unmapped MUST at {document} line {line}")
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


ALL_MAP = ROOT / "test-vectors/requirements/requirement-map.json"


def check_release_map(rmap, ids, documents=None):
    """Extend the reviewed M1.5 map without replacing it; scan new files too."""
    if documents is None:
        documents = {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8")
                     for directory in ("spec", "profiles")
                     for p in sorted((ROOT / directory).rglob("*")) if p.is_file()}
    require(all(e["document"] in documents and e["document"] != "spec/extraction.md"
                for e in rmap["requirements"]), "release map names a missing or delegated document")
    for entry in rmap["requirements"]:
        for clause in entry["clauses"]:
            for field in ("failsOn", "negativeFixtures", "related"):
                require(not any(ref.startswith("checker:") for ref in clause.get(field, [])),
                        f"{entry['id']}: use a registered test ID, not arbitrary checker source text")
            if clause["kind"] == "implementation-test":
                require(clause.get("negativeCases"), f"{entry['id']}: implementation test needs explicit negative cases")
    all_ids = [e["id"] for e in rmap["requirements"]]
    require(len(all_ids) == len(set(all_ids)), "duplicate release requirement id")
    totals = {}
    for path, doc in documents.items():
        if path == "spec/extraction.md":
            mapped = json.loads(MAP.read_text(encoding="utf-8"))
        else:
            mapped = {"requirements": [e for e in rmap["requirements"] if e["document"] == path]}
        try:
            stats = check_must_map(doc, mapped, ids, document=path)
            require(sum(len(e["clauses"]) for e in mapped["requirements"]) == stats["MUST"],
                    "overlapping or duplicate MUST mappings")
        except MapError as exc:
            raise MapError(f"{path}: {exc}") from exc
        for key, value in stats.items():
            totals[key] = totals.get(key, 0) + value
    return totals


def main():
    doc = DOC.read_text(encoding="utf-8")
    rmap = json.loads(MAP.read_text(encoding="utf-8"))
    try:
        require(rmap["document"] == "spec/extraction.md", "map names another document")
        ids = known_ids()
        stats = check_must_map(doc, rmap, ids)
        corruptions = self_test(doc, rmap, ids)
        release = check_release_map(json.loads(ALL_MAP.read_text(encoding="utf-8")), ids)
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
    print(f"PASS M5.1 requirement map: MUST occurrences={release['MUST']} unmapped={release['unmapped']} "
          f"testable={release['testable']} implementation-test={release['implementation-test']} "
          f"untestable={release['untestable']} definitional={release['definitional']}; independent review recorded for 07c98ca (see ROADMAP.md for gate status)")
    print(f"PASS M1.2 derivationRule: {rules} files state the ROADMAP.md definition of hand-derived verbatim, the 5 vector files with its application")
    print(f"PASS M1.1 item map: {items} registration items and {constructs} named constructs, each answered for Go and Rust "
          f"with links to existing sections of spec/extraction.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
