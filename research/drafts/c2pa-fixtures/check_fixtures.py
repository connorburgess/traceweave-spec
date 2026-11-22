#!/usr/bin/env python3
"""Check the illustrative Traceweave <-> C2PA fixtures against mapping-rules.json.

Standard library only; runs on Python 3.11 or later. This is not a C2PA validator:
it reads JSON diagnostic text written by hand, checks it against the mapping
rules of ../c2pa-mapping.md, and never parses CBOR or JUMBF or verifies a signature.

Every fixture in fixtures/ must produce no failure. Every fixture in negative/
must produce exactly its expected code (plus any codes it lists in
expect.alsoReported). The run also checks that every rule pointer appears in
the mapping document, so the table and the rules cannot drift apart.

Usage: python3 -I check_fixtures.py [--verbose]
Exit status 0 when every fixture behaves as expected, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CATEGORIES = ("lossy", "unmapped", "opaque", "conflicting")
UNDECLARED = {"lossy": "lossy-undeclared", "unmapped": "unmapped-undeclared", "opaque": "opaque-undeclared", "conflicting": "conflict-undeclared"}
BSTR_HEX = re.compile(r"^h'([0-9a-f]*)'$")
BSTR_TEXT = re.compile(r"^'(.*)'$", re.S)
TDATE = re.compile(r'^0\("(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"\)$')
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MANIFEST_ID = re.compile(r"^urn:c2pa:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
RELATIONS = ("same-bytes", "bytes-minus-exclusions", "found-by-soft-binding")
MISSING = object()


# ---------------------------------------------------------------- JSON helpers

def strict_load(path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate key at {path}")
            out[key] = value
        return out

    def constant(value):
        raise ValueError(f"non-finite number in {path}")

    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def jcs(value):
    # Restricted RFC 8785: the sources use ASCII strings and non-negative integers only.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def split(pointer):
    return [] if pointer in ("", "/") else pointer.split("/")[1:]


def get(obj, pointer):
    node = obj
    for segment in split(pointer):
        if isinstance(node, dict) and segment in node:
            node = node[segment]
        elif isinstance(node, list) and segment.isdigit() and int(segment) < len(node):
            node = node[int(segment)]
        else:
            return MISSING
    return node


def nodes(obj, prefix=()):
    """Every node with its path (as a tuple of segments), the root included."""
    yield prefix, obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from nodes(value, prefix + (key,))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from nodes(value, prefix + (str(index),))


def leaves(obj):
    for path, value in nodes(obj):
        if not (isinstance(value, (dict, list)) and value):
            yield path


def match(pattern, path):
    """Exact match of a wildcard pattern (segments; '*' matches one segment). Returns the wildcard values or None."""
    if len(pattern) != len(path):
        return None
    stars = []
    for p, s in zip(pattern, path):
        if p == "*":
            stars.append(s)
        elif p != s:
            return None
    return stars


def covers(pattern, path):
    return len(pattern) <= len(path) and match(pattern, path[: len(pattern)]) is not None


def concrete(obj, pointer):
    pattern = tuple(split(pointer))
    return [(path, stars) for path, _ in nodes(obj) for stars in [match(pattern, path)] if stars is not None]


def fill(pointer, stars):
    out, i = [], 0
    for segment in split(pointer):
        if segment == "*":
            out.append(stars[i])
            i += 1
        else:
            out.append(segment)
    return "/" + "/".join(out)


def bstr_bytes(value):
    if not isinstance(value, str):
        return None
    m = BSTR_HEX.match(value)
    if m:
        return bytes.fromhex(m.group(1)) if len(m.group(1)) % 2 == 0 else None
    m = BSTR_TEXT.match(value)
    return m.group(1).encode("utf-8") if m else None


def strings(obj):
    for _, value in nodes(obj):
        if isinstance(value, str):
            yield value
        if isinstance(value, dict):
            yield from value.keys()


# ---------------------------------------------------------------- checks

class Checker:
    def __init__(self, rules):
        self.rules = rules
        self.claim_words = re.compile(rules["claimWordsPattern"])
        self.registered = set(rules["registeredSoftBindingAlgorithms"]["alg"])

    def check(self, fx):
        self.failures = []
        self.fx = fx
        required = ("fixtureVersion", "id", "kind", "notice", "c2paVersion", "traceweave", "mapping")
        if any(key not in fx for key in required):
            self.fail("fixture-shape", "missing top-level field")
            return self.failures
        if fx["notice"] != self.rules["notice"]:
            self.fail("notice-missing", "the illustrative notice is missing or altered")
        if fx["c2paVersion"] != self.rules["c2paVersion"]:
            self.fail("version-pin", "fixture is not pinned to the rules' C2PA version")
        scanned = {k: v for k, v in fx.items() if k not in ("notice", "expect")}
        for text in strings(scanned):
            if self.claim_words.search(text):
                self.fail("claim-wording", f"claim wording: {self.claim_words.search(text).group(0)!r}")
        self.check_source_ref()
        kind = self.rules["kinds"].get(fx["kind"])
        if kind is None:
            self.fail("kind-unknown", fx["kind"])
            return self.failures
        rules = self.rules["kinds"][kind["rulesFrom"]] if "rulesFrom" in kind else kind
        side_name = rules["side"]
        side = fx.get(side_name)
        if not isinstance(side, dict):
            self.fail("fixture-shape", f"missing {side_name} side")
            return self.failures
        for _, value in nodes(side):
            if isinstance(value, dict):
                for key in value:
                    if key in self.rules["forbiddenKeys"]:
                        self.fail("forbidden-field", f"forbidden key {key}")
        for pointer in rules["forbidden"]:
            if get(side, pointer) is not MISSING:
                self.fail("forbidden-field", pointer)
        if side_name == "c2pa":
            self.check_manifest(side, rules)
        else:
            self.check_statement(side, rules)
        self.check_rules(fx["traceweave"], side, rules)
        if fx["kind"] == "round-trip-image":
            self.check_round_trip(fx, rules)
        return self.failures

    def fail(self, code, detail):
        self.failures.append((code, detail))

    def check_source_ref(self):
        ref = self.fx.get("sourceRef") or {}
        if ref.get("path"):
            path = ROOT / ref["path"]
            if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != ref.get("sha256"):
                self.fail("source-drift", f"{ref['path']} changed since the fixture was built")

    # ---- C2PA side

    def check_manifest(self, man, rules):
        if man.get("signature") != "absent: nothing was signed":
            self.fail("signature-claimed", "a fixture must not claim a signature")
        assertions = man.get("assertions", {})
        claim = man.get("claim", {})
        urls = {u.get("url") for field in ("created_assertions", "gathered_assertions") for u in claim.get(field, [])}
        ns = self.rules["placeholderNamespace"] + "."
        hard = []
        for label, body in assertions.items():
            base = re.sub(r"__\d+$", "", label)
            if base.startswith("c2pa."):
                if base not in self.rules["standardLabels"]:
                    self.fail("label-namespace", f"{label} uses the reserved c2pa namespace")
            elif not base.startswith(ns):
                self.fail("label-namespace", f"{label} is in a namespace this project does not own")
            if f"self#jumbf=c2pa.assertions/{label}" not in urls:
                self.fail("assertion-undeclared", f"{label} is not referenced by the claim")
            if base in self.rules["hardBindingLabels"]:
                hard.append((label, body))
            for dep in self.rules["deprecated"]:
                if dep.get("label") == base and concrete(body, dep["pointer"]):
                    self.fail("deprecated-construct", f"{label}{dep['pointer']}")
            if base == "c2pa.soft-binding":
                alg = body.get("alg")
                if alg not in self.registered and not (self.fx["mapping"].get("unregisteredAlg") is True and isinstance(alg, str) and alg.startswith(ns)):
                    self.fail("alg-unregistered-undeclared", f"{label} alg {alg!r}")
        for url in urls:
            if url is not None and url.split("/", 1)[-1] not in assertions:
                self.fail("assertion-missing", url)
        if len(hard) != 1:
            self.fail("hard-binding-count", f"{len(hard)} hard bindings; a manifest has exactly one (12.2.1)")
        for label, body in hard:
            if body.get("alg", claim.get("alg")) not in self.rules["hashAlgorithms"]:
                self.fail("soft-as-hard", f"{label} alg {body.get('alg')!r} is not a hash algorithm of 12.1")
        actions = [a.get("action") for body in (assertions.get("c2pa.actions.v2") or {}, ) for a in body.get("actions", [])]
        if "c2pa.watermarked" in actions:
            self.fail("deprecated-construct", "c2pa.watermarked action")
        if "c2pa.watermarked.bound" in actions and not any(re.sub(r"__\d+$", "", l) == "c2pa.soft-binding" for l in assertions):
            self.fail("soft-binding-missing", "c2pa.watermarked.bound without a soft-binding assertion (14.10.4.2.4)")
        label = rules.get("assertionLabel")
        if label and label in assertions:
            gathered = {u.get("url") for u in claim.get("gathered_assertions", [])}
            if f"self#jumbf=c2pa.assertions/{label}" not in gathered and self.fx["mapping"].get("signerRanComparison") is not True:
                self.fail("attribution", "the report would be attributed to the manifest signer (10.2.2)")
            carried = bstr_bytes(assertions[label].get("body"))
            digest = bstr_bytes(assertions[label].get("bodySha256"))
            if carried is not None and digest is not None and hashlib.sha256(carried).digest() != digest:
                self.fail("body-digest-mismatch", "carried body bytes do not hash to bodySha256")

    # ---- in-toto side

    def check_statement(self, st, rules):
        subject = st.get("subject")
        if st.get("_type") != "https://in-toto.io/Statement/v1" or not isinstance(subject, list) or len(subject) != 1:
            self.fail("intoto-shape", "Statement v1 with exactly one subject")
            return
        digest = subject[0].get("digest", {})
        if set(digest) != {"sha256"} or not HEX64.match(digest.get("sha256", "")):
            self.fail("intoto-shape", "subject digest must be exactly one sha256")
        if st.get("predicateType") != rules["predicateType"]:
            self.fail("intoto-shape", "predicateType is not the placeholder of the rules")
        pred = st.get("predicate", {})
        if hashlib.sha256(jcs(pred.get("body"))).hexdigest() != pred.get("bodySha256"):
            self.fail("body-digest-mismatch", "predicate body does not hash to bodySha256")
        ref = pred.get("c2paManifest")
        if not isinstance(ref, dict):
            self.fail("intoto-shape", "no c2paManifest reference")
            return
        hb = ref.get("hardBinding", {})
        store = ref.get("manifestStoreSha256")
        if not MANIFEST_ID.match(str(ref.get("manifestId"))) or not (store is None or HEX64.match(str(store))) \
                or hb.get("label") not in self.rules["hardBindingLabels"] or hb.get("alg") not in self.rules["hashAlgorithms"] \
                or not HEX64.match(str(hb.get("hash"))) or not isinstance(hb.get("exclusions"), list) or ref.get("relation") not in RELATIONS:
            self.fail("intoto-shape", "malformed c2paManifest reference")
            return
        relation, exclusions = ref["relation"], hb["exclusions"]
        if relation == "same-bytes" and (exclusions or hb["hash"] != digest.get("sha256")):
            self.fail("identity-conflation", "same-bytes needs a whole-file hard binding equal to the subject digest")
        if relation == "bytes-minus-exclusions" and not exclusions:
            self.fail("identity-conflation", "bytes-minus-exclusions needs at least one exclusion")
        if relation == "found-by-soft-binding" and "softBindingAlg" not in ref:
            self.fail("identity-conflation", "a manifest found by soft binding must name the algorithm used")

    # ---- mapping rules

    def check_rules(self, tw, side, rules):
        declared = {cat: {d.get("field"): d for d in self.fx["mapping"].get(cat, [])} for cat in CATEGORIES}
        patterns = []
        for rule in rules["mapped"]:
            patterns.append(tuple(split(rule["tw"])))
            for path, stars in concrete(tw, rule["tw"]):
                target = fill(rule["to"], stars)
                value = get(side, target)
                if value is MISSING:
                    self.fail("mapped-missing", f"{'/' + '/'.join(path)} -> {target}")
                    continue
                self.check_value(get(tw, "/" + "/".join(path)), value, rule, target, side)
        for cat in CATEGORIES:
            for pointer in rules[cat]:
                patterns.append(tuple(split(pointer)))
                if concrete(tw, pointer) and pointer not in declared[cat]:
                    self.fail(UNDECLARED[cat], pointer)
            for field, entry in declared[cat].items():
                if field not in rules[cat]:
                    self.fail("declaration-unknown", f"{cat} {field} is not a {cat} rule")
                if "carriedAt" in entry and concrete(tw, field):
                    if get(side, entry["carriedAt"]) != get(tw, field):
                        self.fail("value-mismatch", f"{field} carried at {entry['carriedAt']}")
        for path in leaves(tw):
            if not any(covers(p, path) for p in patterns):
                self.fail("field-unruled", "/" + "/".join(path))

    def check_value(self, src, value, rule, target, side):
        kind, conv = rule["type"], rule["conv"]
        ok_type = {
            "bstr": bstr_bytes(value) is not None,
            "tstr": isinstance(value, str) and bstr_bytes(value) is None,
            "tdate": isinstance(value, str) and TDATE.match(value) is not None,
            "map": isinstance(value, dict),
            "object": isinstance(value, dict),
            "string": isinstance(value, str),
            "hex64": isinstance(value, str) and HEX64.match(value) is not None,
        }[kind]
        if not ok_type:
            self.fail("type-mismatch", f"{target} is not {kind}")
            return
        if conv in ("hex-to-bstr", "hex-to-bstr-whole-file"):
            good = bstr_bytes(value) == bytes.fromhex(src)
            if conv == "hex-to-bstr-whole-file":
                parent = get(side, target.rsplit("/", 1)[0])
                if isinstance(parent, dict) and parent.get("exclusions"):
                    self.fail("identity-conflation", f"{target} excludes byte ranges, so it does not name the whole artifact")
        elif conv == "jcs-bytes":
            good = bstr_bytes(value) == jcs(src)
        elif conv in ("text", "same"):
            good = value == src
        elif conv == "tdate":
            good = value == f'0("{src}")'
        elif conv.startswith("prefix:"):
            good = value == conv[len("prefix:"):] + src
        elif conv == "pixel-rect":
            good = self.pixel_rect(src, value, target)
            if good is None:
                return
        else:
            self.fail("rules-error", f"unknown conversion {conv}")
            return
        if not good:
            self.fail("value-mismatch", target)

    def pixel_rect(self, src, value, target):
        ranges = value.get("region")
        if not isinstance(ranges, list) or len(ranges) != 1 or ranges[0].get("type") != "spatial":
            return False
        shape = ranges[0].get("shape", {})
        numbers = [shape.get("origin", {}).get("x"), shape.get("origin", {}).get("y"), shape.get("width"), shape.get("height")]
        if not all(isinstance(n, float) for n in numbers):
            self.fail("type-mismatch", f"{target}: region-map coordinates are floats (16.9.2.3)")
            return None
        if shape.get("type") != "rectangle" or shape.get("unit") != src.get("unit"):
            return False
        return numbers == [float(src["x"]), float(src["y"]), float(src["width"]), float(src["height"])]

    def check_round_trip(self, fx, rules):
        before, after = fx["traceweave"], fx.get("traceweaveAfter", {})
        before_leaves = {"/" + "/".join(p) for p in leaves(before)}
        after_leaves = {"/" + "/".join(p) for p in leaves(after)}
        survives = {p for p in before_leaves if get(after, p) is not MISSING and get(after, p) == get(before, p)}
        if survives != set(fx.get("survives", [])) or before_leaves - survives != set(fx.get("lost", [])):
            self.fail("round-trip-misdeclared", "declared survivors and losses differ from the records")
        if after_leaves - before_leaves:
            self.fail("round-trip-invented", ", ".join(sorted(after_leaves - before_leaves)))
        mapped = [tuple(split(r["tw"])) for r in rules["mapped"]]
        for pointer in survives:
            if not any(match(m, tuple(split(pointer))) is not None for m in mapped):
                self.fail("round-trip-unsupported", f"{pointer} survived without a mapped rule")


def doc_drift(rules):
    """Every rule pointer must appear, in backticks, in the mapping document."""
    doc = (HERE / rules["mappingDocument"]).read_text(encoding="utf-8")
    missing = []
    for name, kind in rules["kinds"].items():
        if "rulesFrom" in kind:
            continue
        pointers = [r["tw"] for r in kind["mapped"]] + [r["to"] for r in kind["mapped"]]
        pointers += [p for cat in CATEGORIES for p in kind[cat]]
        missing += [f"{name}: {p}" for p in pointers if f"`{p}`" not in doc]
    return missing


def main(argv):
    verbose = "--verbose" in argv
    rules = strict_load(HERE / "mapping-rules.json")
    checker = Checker(rules)
    problems = 0
    counts = {"fixtures": 0, "negative": 0}
    for directory in ("fixtures", "negative"):
        for path in sorted((HERE / directory).glob("*.json")):
            counts[directory] += 1
            try:
                fx = strict_load(path)
            except ValueError as error:
                print(f"FAIL {directory}/{path.name}: {error}")
                problems += 1
                continue
            failures = checker.check(fx)
            codes = {code for code, _ in failures}
            if directory == "fixtures":
                ok = not failures
                status = "PASS" if ok else "FAIL"
                print(f"{status} fixtures/{path.name}" + ("" if ok else ": " + "; ".join(f"{c} ({d})" for c, d in failures)))
            else:
                expect = fx.get("expect", {})
                wanted = {expect.get("code")} | set(expect.get("alsoReported", []))
                ok = codes == wanted
                status = "PASS" if ok else "FAIL"
                detail = f"rejected with {sorted(codes)}" if ok else f"expected {sorted(wanted)}, got {sorted(codes)}"
                print(f"{status} negative/{path.name}: {detail}")
                if verbose or not ok:
                    for code, text in failures:
                        print(f"      {code}: {text}")
            problems += 0 if ok else 1
    drift = doc_drift(rules)
    for item in drift:
        print(f"FAIL doc-drift: {item} is not in the mapping document")
    problems += len(drift)
    print(f"{counts['fixtures']} fixtures, {counts['negative']} negative fixtures, mapping-document drift {len(drift)}; "
          + ("all as expected" if problems == 0 else f"{problems} problem(s)"))
    return 0 if problems == 0 and counts["fixtures"] >= 6 and counts["negative"] >= 8 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
