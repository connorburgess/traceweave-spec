#!/usr/bin/env python3
"""Check the M3 corpus manifest (protocol m3-eval-draft-4). Standard library only.

Usage:
  python3 -I verify_manifest.py [MANIFEST] [--schema SCHEMA]   exit 0 valid, 1 invalid, 2 usage or I/O error
  python3 -I verify_manifest.py --licence-dir DIR [MANIFEST]    also recheck every licence file against
                                                                 DIR/<owner>/<repo>/<path> (acquisition, M5):
                                                                 SHA-256 and classification must match
  python3 -I verify_manifest.py --self-test [MANIFEST]          exit 0 when the manifest passes and every
                                                                 generated broken manifest (and broken licence
                                                                 text) is rejected with its expected error code

The checker interprets the schema keywords used by manifest.schema.json, then makes the semantic checks a
schema cannot express: licence expression and redistribution follow from the classified licence files,
census and excluded owners are absent, groups are one owner each and disjoint across splits, no two entries
are dependency-linked, acquisition-time rejections name an earlier accepted repository and stay within the
replacement limit, the split assignment and its digest are recomputed, the selection walk is recomputed
from the pool snapshot, and the totals add up. With --licence-dir it also reruns the licence classifier
(m3-licence-classifier-v1) on the fetched licence texts. It makes no network request.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENSUS = ["davecgh/go-spew", "rakyll/hey", "dtolnay/itoa", "sharkdp/hexyl"]
REQUIRED_EXCLUDED_OWNERS = {"davecgh": "census", "rakyll": "census", "dtolnay": "census", "sharkdp": "census",
                            "golang": "development-exposed", "rust-lang": "development-exposed"}
LANGUAGES = ("Go", "Rust")
IGNORED_TOPICS = {"go", "golang", "rust", "rustlang", "hacktoberfest"}
PREFILTER_REASONS = {"excluded-owner-census", "excluded-owner-development-exposed", "list-repository", "owner-already-selected"}
FACT_REASONS = {"licence-file-missing", "licence-unclassified", "licence-not-allowed", "too-few-eligible-files",
                "eligible-bytes-over-limit"}
NO_FACT_REASONS = {"revision-unresolved", "tree-truncated"}
LINK_REASONS = {"dependency-linked", "duplicate-content"}

# m3-licence-classifier-v1 (protocol section 3.2)
PHRASES = {
    "MIT": ["permission is hereby granted, free of charge, to any person obtaining a copy",
            "the above copyright notice and this permission notice shall be included"],
    "Apache-2.0": ["apache license", "version 2.0, january 2004"],
    "BSD-3-Clause": ["redistribution and use in source and binary forms, with or without modification, are permitted",
                     "endorse or promote products derived from this software"],
    "BSD-2-Clause": ["redistribution and use in source and binary forms, with or without modification, are permitted"],
    "ISC": ["permission to use, copy, modify, and",
            "distribute this software for any purpose with or without fee is hereby granted",
            "provided that the above copyright notice and this permission notice appear in all copies"],
    "0BSD": ["permission to use, copy, modify, and",
             "distribute this software for any purpose with or without fee is hereby granted"],
    "Unlicense": ["this is free and unencumbered software released into the public domain"],
    "Zlib": ["altered source versions must be plainly marked as such"],
    "GPL-3.0": ["gnu general public license version 3, 29 june 2007"],
    "GPL-2.0": ["gnu general public license version 2, june 1991"],
    "AGPL-3.0": ["gnu affero general public license version 3, 19 november 2007"],
    "LGPL-3.0": ["gnu lesser general public license version 3, 29 june 2007"],
    "MPL-2.0": ["mozilla public license version 2.0"],
    "CC": ["creative commons"],
    "EUPL": ["european union public licence"],
}


def classify(data):
    text = data.decode("utf-8", "replace").lower().replace("*", " ").replace("#", " ")
    text = re.sub(r"\s+", " ", text)
    hits = {k for k, phrases in PHRASES.items() if all(ph in text for ph in phrases)}
    if "BSD-3-Clause" in hits:
        hits.discard("BSD-2-Clause")
    if "ISC" in hits:
        hits.discard("0BSD")
    if len(hits) == 1:
        return hits.pop()
    if not hits:
        return "unrecognized"
    return "multiple:" + "+".join(sorted(hits))


def recheck_licences(m, directory, only=None):
    """Fail closed: every licence file of every entry must exist under directory with the recorded
    SHA-256 and classification."""
    checked = 0
    for e in m["entries"]:
        if only is not None and e["id"] not in only:
            continue
        for f in e["licence"]["files"]:
            path = Path(directory) / e["fullName"] / f["path"]
            try:
                data = path.read_bytes()
            except OSError:
                raise Invalid("E-LICENCE-TEXT", f"{e['fullName']}: {f['path']} not found under {directory}")
            if hashlib.sha256(data).hexdigest() != f["sha256"]:
                raise Invalid("E-LICENCE-TEXT", f"{e['fullName']}: {f['path']} SHA-256 differs from the manifest")
            if len(data) != f["bytes"]:
                raise Invalid("E-LICENCE-TEXT", f"{e['fullName']}: {f['path']} length differs from the manifest")
            got = classify(data)
            if got != f["spdx"]:
                raise Invalid("E-LICENCE-TEXT", f"{e['fullName']}: {f['path']} classifies as {got}, manifest says {f['spdx']}")
            checked += 1
    return checked


class Invalid(Exception):
    def __init__(self, code, detail):
        super().__init__(f"{code}: {detail}")
        self.code = code


# ---------------------------------------------------------------- schema subset

def _type_ok(value, name):
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "string":
        return isinstance(value, str)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "null":
        return value is None
    raise Invalid("E-SCHEMA-KEYWORD", f"unknown type {name}")


SUPPORTED = {"$schema", "$id", "title", "description", "$defs", "$ref", "type", "const", "enum", "pattern", "minimum",
             "maximum", "minLength", "minItems", "maxItems", "uniqueItems", "required", "properties",
             "additionalProperties", "items"}


def validate(value, schema, root, path="$"):
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise Invalid("E-SCHEMA-KEYWORD", f"{path}: unsupported keywords {sorted(unknown)}")
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise Invalid("E-SCHEMA-KEYWORD", f"{path}: only local $defs references are supported")
        validate(value, root["$defs"][ref[len("#/$defs/"):]], root, path)
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(value, n) for n in names):
            raise Invalid("E-SCHEMA", f"{path}: expected {names}")
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        raise Invalid("E-SCHEMA", f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise Invalid("E-SCHEMA", f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise Invalid("E-SCHEMA", f"{path}: {value!r} does not match {schema['pattern']}")
        if len(value) < schema.get("minLength", 0):
            raise Invalid("E-SCHEMA", f"{path}: too short")
    if _type_ok(value, "integer"):
        if "minimum" in schema and value < schema["minimum"]:
            raise Invalid("E-SCHEMA", f"{path}: below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise Invalid("E-SCHEMA", f"{path}: above {schema['maximum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            raise Invalid("E-SCHEMA", f"{path}: item count {len(value)} out of range")
        if schema.get("uniqueItems"):
            seen = [json.dumps(v, sort_keys=True) for v in value]
            if len(seen) != len(set(seen)):
                raise Invalid("E-SCHEMA", f"{path}: items not unique")
        if "items" in schema:
            for i, item in enumerate(value):
                validate(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise Invalid("E-SCHEMA", f"{path}: missing {key}")
        props = schema.get("properties", {})
        for key, item in value.items():
            if key in props:
                validate(item, props[key], root, f"{path}.{key}")
            elif "additionalProperties" in schema:
                extra = schema["additionalProperties"]
                if extra is False:
                    raise Invalid("E-SCHEMA", f"{path}: unexpected field {key}")
                if isinstance(extra, dict):
                    validate(item, extra, root, f"{path}.{key}")


# ---------------------------------------------------------------- semantic checks

def order_key(salt, full_name):
    return hashlib.sha256((salt + full_name.lower()).encode("utf-8")).hexdigest()


def split_key(salt, language, group):
    return hashlib.sha256((salt + language + "\n" + group).encode("utf-8")).hexdigest()


def split_lines(entries):
    return sorted(f"{e['language']}\t{e['split']}\t{e['splitGroup']}\t{e['fullName']}\t{e['revision']}\n" for e in entries)


def entry_id(language, full_name):
    return re.sub(r"[^a-z0-9.-]", "-", f"{language}-{full_name}".lower())


def licence_outcome(files, allow):
    ids = [f["spdx"] for f in files]
    if not files:
        return "licence-file-missing"
    if any(i.startswith("multiple") or i == "unrecognized" for i in ids):
        return "licence-unclassified"
    if any(i not in allow for i in ids):
        return "licence-not-allowed"
    return None


def check(m):
    sel, exc = m["selection"], m["exclusions"]
    allow = sel["licenceAllowlist"]

    # Exclusion lists cannot be weakened.
    if sorted(exc["censusRepositories"]) != sorted(CENSUS):
        raise Invalid("E-EXCLUSION-LIST", "censusRepositories must list exactly the four census repositories")
    for owner, why in REQUIRED_EXCLUDED_OWNERS.items():
        if exc["excludedOwners"].get(owner) != why:
            raise Invalid("E-EXCLUSION-LIST", f"excludedOwners must contain {owner}: {why}")
    for full in exc["censusRepositories"]:
        if full.split("/")[0].lower() not in exc["excludedOwners"]:
            raise Invalid("E-EXCLUSION-LIST", f"census owner of {full} not excluded")

    bounds = sel["queryBounds"]
    entries = m["entries"]
    by_full = {}
    ids = set()
    for e in entries:
        key = e["fullName"].lower()
        if key in by_full:
            raise Invalid("E-DUPLICATE", f"repository listed twice: {e['fullName']}")
        by_full[key] = e
        if e["id"] in ids:
            raise Invalid("E-DUPLICATE", f"id listed twice: {e['id']}")
        ids.add(e["id"])
        if e["id"] != entry_id(e["language"], e["fullName"]):
            raise Invalid("E-ID", f"{e['id']} should be {entry_id(e['language'], e['fullName'])}")

        # Exclusions.
        if e["fullName"].lower() in {c.lower() for c in CENSUS}:
            raise Invalid("E-CENSUS", f"census repository {e['fullName']} in corpus")
        if e["owner"] in exc["excludedOwners"] or e["fullName"].split("/")[0].lower() in exc["excludedOwners"]:
            raise Invalid("E-EXCLUDED-OWNER", f"{e['fullName']}: owner excluded ({exc['excludedOwners'].get(e['owner'])})")

        # Identity and pinning.
        if e["owner"] != e["fullName"].split("/")[0].lower():
            raise Invalid("E-OWNER", f"{e['fullName']}: owner field {e['owner']}")
        if e["url"] != "https://github.com/" + e["fullName"]:
            raise Invalid("E-URL", f"{e['fullName']}: url {e['url']}")

        # Licence and redistribution.
        files = e["licence"]["files"]
        outcome = licence_outcome(files, allow)
        if outcome:
            raise Invalid("E-LICENCE", f"{e['fullName']}: {outcome}")
        if len({f['path'] for f in files}) != len(files):
            raise Invalid("E-LICENCE", f"{e['fullName']}: licence file listed twice")
        for f in files:
            want = f"https://raw.githubusercontent.com/{e['fullName']}/{e['revision']}/{f['path']}"
            if f["url"] != want:
                raise Invalid("E-URL", f"{e['fullName']}: licence url {f['url']} should be {want}")
        ids_sorted = sorted({f["spdx"] for f in files})
        if e["licence"]["expression"] != " AND ".join(ids_sorted):
            raise Invalid("E-LICENCE-EXPRESSION", f"{e['fullName']}: {e['licence']['expression']!r} should be {' AND '.join(ids_sorted)!r}")
        want_red = "permitted" if all(allow[i] == "permitted" for i in ids_sorted) else "permitted-with-notice"
        if e["redistribution"]["permittedByLicence"] != want_red:
            raise Invalid("E-REDISTRIBUTION", f"{e['fullName']}: should be {want_red}")

        # Size limits.
        s = e["size"]
        if s["githubSizeKiB"] > bounds["maxSizeKiB"]:
            raise Invalid("E-SIZE", f"{e['fullName']}: githubSizeKiB {s['githubSizeKiB']} > {bounds['maxSizeKiB']}")
        if s["eligiblePathCount"] < sel["minEligiblePaths"]:
            raise Invalid("E-SIZE", f"{e['fullName']}: {s['eligiblePathCount']} eligible paths < {sel['minEligiblePaths']}")
        if s["eligiblePathBytes"] > sel["maxEligiblePathBytes"]:
            raise Invalid("E-SIZE", f"{e['fullName']}: eligible bytes over limit")

    # Pool snapshot consistency and fork/duplicate exclusion.
    pool_by_full = {}
    for language in LANGUAGES:
        for p in m["pools"][language]:
            key = p["fullName"].lower()
            if key in pool_by_full:
                raise Invalid("E-POOL", f"{p['fullName']} appears twice in the pools")
            pool_by_full[key] = (language, p)
            if p["language"] != language:
                raise Invalid("E-POOL", f"{p['fullName']}: language {p['language']} in the {language} pool")
            if p["fork"] or p["archived"]:
                raise Invalid("E-POOL", f"{p['fullName']}: fork or archived repository in pool")
            if p["stars"] < bounds["minStars"] or p["sizeKiB"] > bounds["maxSizeKiB"]:
                raise Invalid("E-POOL", f"{p['fullName']}: outside the query bounds")
            if not (p["createdAt"] < bounds["createdBefore"] and p["pushedAt"] >= bounds["pushedSince"]):
                raise Invalid("E-POOL", f"{p['fullName']}: outside the query dates")
            if p["fullName"].split("/")[0] != p["owner"] or p["fullName"].split("/")[1] != p["name"]:
                raise Invalid("E-POOL", f"{p['fullName']}: owner/name mismatch")
    for e in entries:
        hit = pool_by_full.get(e["fullName"].lower())
        if hit is None:
            raise Invalid("E-WALK", f"{e['fullName']} is not in the pool snapshot")
        language, p = hit
        if language != e["language"]:
            raise Invalid("E-WALK", f"{e['fullName']}: entry language {e['language']}, pool {language}")
        if p["sizeKiB"] != e["size"]["githubSizeKiB"] or p["defaultBranch"] != e["defaultBranch"] or p["topics"] != e["topics"]:
            raise Invalid("E-POOL", f"{e['fullName']}: entry disagrees with the pool snapshot")

    # Selection walk, recomputed.
    for language in LANGUAGES:
        pool = sorted(m["pools"][language], key=lambda p: order_key(sel["orderSalt"], p["fullName"]))
        walk = m["walks"][language]
        if len(walk) > len(pool):
            raise Invalid("E-WALK", f"{language}: walk longer than pool")
        accepted_owners, accepted, replacements = set(), [], 0
        for pos, (w, p) in enumerate(zip(walk, pool)):
            if w["fullName"] != p["fullName"]:
                raise Invalid("E-WALK", f"{language} walk position {pos + 1}: {w['fullName']}, order requires {p['fullName']}")
            owner = p["owner"].lower()
            if owner in exc["excludedOwners"]:
                expected = "excluded-owner-" + exc["excludedOwners"][owner]
            elif sel["listMarker"] in p["name"].lower() or any(sel["listMarker"] in t.lower() for t in p["topics"]):
                expected = "list-repository"
            elif owner in accepted_owners:
                expected = "owner-already-selected"
            else:
                expected = None
            reason = w.get("reason")
            if expected:
                if w["verdict"] != "rejected" or reason != expected:
                    raise Invalid("E-WALK", f"{language} {p['fullName']}: verdict must be rejected/{expected}")
                continue
            if reason in PREFILTER_REASONS:
                raise Invalid("E-WALK", f"{language} {p['fullName']}: {reason} does not apply")
            facts = w.get("facts")
            if reason in NO_FACT_REASONS:
                if w["verdict"] != "rejected":
                    raise Invalid("E-WALK", f"{language} {p['fullName']}: verdict/reason mismatch")
                replacements += 1
                continue
            if reason in LINK_REASONS:
                linked = w.get("linkedTo", "").lower()
                if w["verdict"] != "rejected" or facts is None:
                    raise Invalid("E-WALK", f"{language} {p['fullName']}: {reason} needs a rejected verdict and recorded facts")
                if linked not in {a["fullName"].lower() for a, _ in accepted}:
                    raise Invalid("E-WALK", f"{language} {p['fullName']}: {reason} must name an accepted repository earlier in the walk")
                replacements += 1
                continue
            if "linkedTo" in w:
                raise Invalid("E-WALK", f"{language} {p['fullName']}: linkedTo without a link reason")
            if facts is None or "licenceFiles" not in facts or "eligiblePathCount" not in facts:
                raise Invalid("E-WALK", f"{language} {p['fullName']}: verdict needs recorded facts")
            derived = licence_outcome(facts["licenceFiles"], allow)
            if derived is None and facts["eligiblePathCount"] < sel["minEligiblePaths"]:
                derived = "too-few-eligible-files"
            if derived is None and facts["eligiblePathBytes"] > sel["maxEligiblePathBytes"]:
                derived = "eligible-bytes-over-limit"
            if derived is None:
                if w["verdict"] != "accepted" or reason is not None:
                    raise Invalid("E-WALK", f"{language} {p['fullName']}: facts require acceptance")
                accepted_owners.add(owner)
                accepted.append((p, facts))
            elif w["verdict"] != "rejected" or reason != derived:
                raise Invalid("E-WALK", f"{language} {p['fullName']}: facts require rejected/{derived}")
        if replacements > m["acquisition"]["replacementLimitPerLanguage"]:
            raise Invalid("E-REPLACEMENTS", f"{language}: {replacements} acquisition-time rejections exceed the limit "
                                            f"{m['acquisition']['replacementLimitPerLanguage']}")
        if len(accepted) != sel["targetPerLanguage"]:
            raise Invalid("E-WALK", f"{language}: {len(accepted)} accepted, target {sel['targetPerLanguage']}")
        if walk and walk[-1]["verdict"] != "accepted":
            raise Invalid("E-WALK", f"{language}: walk must stop at the acceptance that reaches the target")
        got = sorted(e["fullName"] for e in entries if e["language"] == language)
        if got != sorted(p["fullName"] for p, _ in accepted):
            raise Invalid("E-WALK", f"{language}: entries differ from the walk's accepted set")
        for p, facts in accepted:
            e = by_full[p["fullName"].lower()]
            if e["revision"] != facts["revision"] or e["revisionResolvedAt"] != facts["resolvedAt"]:
                raise Invalid("E-WALK", f"{p['fullName']}: revision differs from the walk record")
            if e["licence"]["files"] != facts["licenceFiles"]:
                raise Invalid("E-WALK", f"{p['fullName']}: licence files differ from the walk record")
            for k in ("eligiblePathCount", "eligiblePathBytes", "oversizePathCount", "submoduleCount", "symlinkCount"):
                if e["size"][k] != facts.get(k):
                    raise Invalid("E-WALK", f"{p['fullName']}: size.{k} differs from the walk record")

    # Groups: owner-derived unless merged; disjoint across splits.
    group_split, owner_group = {}, {}
    for e in entries:
        want = e["owner"]
        if e["splitGroup"] != want:
            raise Invalid("E-GROUP", f"{e['fullName']}: splitGroup {e['splitGroup']}, rule gives {want}")
        prev = owner_group.setdefault((e["language"], e["owner"]), e["splitGroup"])
        if prev != e["splitGroup"]:
            raise Invalid("E-GROUP", f"owner {e['owner']} in two groups")
        key = (e["language"], e["splitGroup"])
        if group_split.setdefault(key, e["split"]) != e["split"]:
            raise Invalid("E-GROUP-DISJOINT", f"group {e['splitGroup']} ({e['language']}) appears in both splits")
    rejected_link = {}
    for language in LANGUAGES:
        for w in m["walks"][language]:
            if w.get("reason") == "dependency-linked":
                rejected_link[w["fullName"].lower()] = w["linkedTo"].lower()
    for edge in m["dependencyEdges"]:
        a, b = edge["from"].lower(), edge["to"].lower()
        if a in by_full and b in by_full:
            raise Invalid("E-DEPENDENCY-LINKED", f"accepted entries {edge['from']} and {edge['to']} are dependency-linked")
        if rejected_link.get(a) != b and rejected_link.get(b) != a:
            raise Invalid("E-DEPENDENCY-LINKED", f"edge {edge['from']} -> {edge['to']}: the later repository must be "
                                                 "rejected dependency-linked to the earlier one")

    # Split assignment and digest, recomputed.
    for language in LANGUAGES:
        groups = sorted({g for (lang, g) in group_split if lang == language},
                        key=lambda g: split_key(m["split"]["salt"], language, g))
        held = set(groups[: len(groups) // 2])
        for g in groups:
            want = "held-out" if g in held else "tuning"
            if group_split[(language, g)] != want:
                raise Invalid("E-SPLIT-RULE", f"{language} group {g}: split {group_split[(language, g)]}, rule gives {want}")
    digest = hashlib.sha256("".join(split_lines(entries)).encode("utf-8")).hexdigest()
    if digest != m["split"]["digest"]:
        raise Invalid("E-SPLIT-DIGEST", f"split digest {m['split']['digest']}, recomputed {digest}")

    # Totals.
    def tot(sel_entries):
        return {"repositories": len(sel_entries),
                "githubSizeKiB": sum(e["size"]["githubSizeKiB"] for e in sel_entries),
                "eligiblePathCount": sum(e["size"]["eligiblePathCount"] for e in sel_entries),
                "eligiblePathBytes": sum(e["size"]["eligiblePathBytes"] for e in sel_entries)}
    want_totals = {"all": tot(entries)}
    for language in LANGUAGES:
        for split in ("held-out", "tuning"):
            want_totals[f"{language}/{split}"] = tot([e for e in entries if e["language"] == language and e["split"] == split])
    if m["totals"] != want_totals:
        raise Invalid("E-TOTALS", "totals do not match the entries")

    return {"entries": len(entries), "digest": digest,
            "negativeSearches": sum(n * (n - 1) // 2 for n in (
                len({e["splitGroup"] for e in entries if e["language"] == lang and e["split"] == "held-out"})
                for lang in LANGUAGES)),
            "sameDomainSearches": same_domain(entries)}


def same_domain(entries):
    count = 0
    held = [e for e in entries if e["split"] == "held-out"]
    for i, a in enumerate(held):
        for b in held[i + 1:]:
            if a["language"] != b["language"] or a["splitGroup"] == b["splitGroup"]:
                continue
            if (set(a["topics"]) - IGNORED_TOPICS) & (set(b["topics"]) - IGNORED_TOPICS):
                count += 1
    return count


def verify(manifest, schema):
    validate(manifest, schema, schema)
    return check(manifest)


# ---------------------------------------------------------------- self-test

def mutations(m):
    """Yield (name, expected code, broken manifest). Each breaks exactly one rule."""
    def first(lang, split=None):
        return next(e for e in m["entries"] if e["language"] == lang and (split is None or e["split"] == split))

    def mut(name, code, fn):
        b = copy.deepcopy(m)
        fn(b)
        return name, code, b

    def entry(b, lang="Go", split=None):
        target = first(lang, split)["id"]
        return next(e for e in b["entries"] if e["id"] == target)

    yield mut("revision missing", "E-SCHEMA", lambda b: entry(b).pop("revision"))
    yield mut("revision abbreviated", "E-SCHEMA", lambda b: entry(b).update(revision=entry(b)["revision"][:12]))
    yield mut("revision uppercase", "E-SCHEMA", lambda b: entry(b).update(revision=entry(b)["revision"].upper()))
    yield mut("unknown field", "E-SCHEMA", lambda b: entry(b).update(note="x"))
    yield mut("status says acquired", "E-SCHEMA", lambda b: entry(b).update(status="acquired"))
    yield mut("redistribution planned", "E-SCHEMA", lambda b: entry(b)["redistribution"].update(projectRedistributesSource=True))
    yield mut("split value invalid", "E-SCHEMA", lambda b: entry(b).update(split="test"))
    yield mut("licence files empty", "E-SCHEMA", lambda b: entry(b)["licence"].update(files=[]))

    def gpl(b):
        e = entry(b)
        e["licence"]["files"][0]["spdx"] = "GPL-3.0"
    yield mut("licence not allowed", "E-LICENCE", gpl)

    def unclassified(b):
        entry(b)["licence"]["files"][0]["spdx"] = "multiple:Apache-2.0+MIT"
    yield mut("licence unclassified", "E-LICENCE", unclassified)
    yield mut("expression mismatch", "E-LICENCE-EXPRESSION",
              lambda b: entry(b)["licence"].update(expression="MIT OR Apache-2.0"))

    def red(b):
        e = entry(b)
        e["redistribution"]["permittedByLicence"] = ("permitted" if e["redistribution"]["permittedByLicence"]
                                                     == "permitted-with-notice" else "permitted-with-notice")
    yield mut("redistribution inconsistent with licence", "E-REDISTRIBUTION", red)

    def census(b):
        e = copy.deepcopy(entry(b))
        e.update(fullName="davecgh/go-spew", owner="davecgh", url="https://github.com/davecgh/go-spew",
                 id="go-davecgh-go-spew", splitGroup="davecgh")
        for f in e["licence"]["files"]:
            f["url"] = f"https://raw.githubusercontent.com/davecgh/go-spew/{e['revision']}/{f['path']}"
        b["entries"].append(e)
    yield mut("census repository added", "E-CENSUS", census)

    def dev_owner(b):
        e = copy.deepcopy(entry(b, "Rust"))
        e.update(fullName="rust-lang/regex", owner="rust-lang", url="https://github.com/rust-lang/regex",
                 id="rust-rust-lang-regex", splitGroup="rust-lang")
        for f in e["licence"]["files"]:
            f["url"] = f"https://raw.githubusercontent.com/rust-lang/regex/{e['revision']}/{f['path']}"
        b["entries"].append(e)
    yield mut("development-exposed owner added", "E-EXCLUDED-OWNER", dev_owner)
    yield mut("census list shortened", "E-EXCLUSION-LIST", lambda b: b["exclusions"]["censusRepositories"].pop())
    yield mut("excluded owner removed", "E-EXCLUSION-LIST", lambda b: b["exclusions"]["excludedOwners"].pop("golang"))

    def straddle(b):
        held, tune = entry(b, "Go", "held-out"), entry(b, "Go", "tuning")
        tune["splitGroup"] = held["splitGroup"]
    yield mut("tuning entry put in a held-out owner's group", "E-GROUP", straddle)

    def edge(b):
        held, tune = entry(b, "Go", "held-out"), entry(b, "Go", "tuning")
        b["dependencyEdges"].append({"from": held["fullName"], "to": tune["fullName"], "declaredIn": "go.mod"})
    yield mut("two accepted entries dependency-linked", "E-DEPENDENCY-LINKED", edge)

    def edge_same_split(b):
        x, y = [e for e in b["entries"] if e["language"] == "Rust" and e["split"] == "held-out"][:2]
        b["dependencyEdges"].append({"from": x["fullName"], "to": y["fullName"], "declaredIn": "Cargo.toml"})
    yield mut("dependency edge inside one split is still rejected", "E-DEPENDENCY-LINKED", edge_same_split)

    def link_without_target(b):
        w = next(w for w in b["walks"]["Rust"] if w.get("reason") == "licence-not-allowed")
        w["reason"] = "dependency-linked"
    yield mut("dependency-linked rejection without linkedTo", "E-WALK", link_without_target)

    def link_to_later(b):
        walk = b["walks"]["Rust"]
        i = next(i for i, w in enumerate(walk) if w.get("reason") == "licence-not-allowed")
        later = next(w for w in walk[i + 1:] if w["verdict"] == "accepted")
        walk[i]["reason"] = "duplicate-content"
        walk[i]["linkedTo"] = later["fullName"]
    yield mut("duplicate-content linked to a later repository (tie rule)", "E-WALK", link_to_later)

    def too_many_replacements(b):
        b["acquisition"]["replacementLimitPerLanguage"] = 0
        walk = b["walks"]["Rust"]
        first_accepted = next(w for w in walk if w["verdict"] == "accepted")
        w = next(w for w in walk if w.get("reason") == "licence-not-allowed" and walk.index(w) > walk.index(first_accepted))
        w["reason"] = "dependency-linked"
        w["linkedTo"] = first_accepted["fullName"]
    yield mut("acquisition rejections above the replacement limit", "E-REPLACEMENTS", too_many_replacements)
    yield mut("older manifest version", "E-SCHEMA", lambda b: b.update(manifestVersion="traceweave-m3-corpus-manifest-draft-1"))
    yield mut("older protocol version", "E-SCHEMA", lambda b: b.update(protocolVersion="m3-eval-draft-2"))
    yield mut("ordered search unit", "E-SCHEMA", lambda b: b["acquisition"].update(searchUnit="ordered repository pair"))
    yield mut("replacement limit above 8", "E-SCHEMA", lambda b: b["acquisition"].update(replacementLimitPerLanguage=9))

    def wrong_group(b):
        entry(b)["splitGroup"] = "someone-else"
    yield mut("group not derived from owner", "E-GROUP", wrong_group)

    def flip(b):
        e = entry(b, "Rust", "held-out")
        e["split"] = "tuning"
    yield mut("split flipped against the hash rule", "E-SPLIT-RULE", flip)

    def flip_pair(b):
        h, t = entry(b, "Rust", "held-out"), entry(b, "Rust", "tuning")
        h["split"], t["split"] = "tuning", "held-out"
    yield mut("two groups swapped between splits", "E-SPLIT-RULE", flip_pair)
    yield mut("split digest altered", "E-SPLIT-DIGEST", lambda b: b["split"].update(digest="0" * 64))

    def dup(b):
        b["entries"].append(copy.deepcopy(entry(b)))
    yield mut("duplicate repository", "E-DUPLICATE", dup)
    yield mut("url mismatch", "E-URL", lambda b: entry(b).update(url="https://github.com/someone/else"))

    def licence_url(b):
        f = entry(b)["licence"]["files"][0]
        f["url"] = f["url"].replace(entry(b)["revision"], "main")
    yield mut("licence url not pinned", "E-URL", licence_url)
    yield mut("id not derived", "E-ID", lambda b: entry(b).update(id="go-renamed"))
    yield mut("size over limit", "E-SIZE", lambda b: entry(b)["size"].update(githubSizeKiB=50001))
    yield mut("too few eligible files", "E-SIZE", lambda b: entry(b)["size"].update(eligiblePathCount=3))
    yield mut("totals off by one", "E-TOTALS", lambda b: b["totals"]["all"].update(repositories=b["totals"]["all"]["repositories"] + 1))

    def fork(b):
        b["pools"]["Go"][0]["fork"] = True
    yield mut("fork in pool", "E-POOL", fork)

    def walk_skip(b):
        b["walks"]["Go"].pop(0)
    yield mut("walk skips the first pool repository", "E-WALK", walk_skip)

    def walk_reason(b):
        w = next(w for w in b["walks"]["Rust"] if w.get("reason") == "licence-not-allowed")
        w["verdict"] = "accepted"
        w.pop("reason")
    yield mut("licence rejection turned into acceptance", "E-WALK", walk_reason)

    def drop_entry(b):
        e = entry(b, "Rust")
        b["entries"].remove(e)
    yield mut("accepted repository dropped from entries", "E-WALK", drop_entry)

    def revision_swap(b):
        e = entry(b)
        e["revision"] = "f" * 40
        for f in e["licence"]["files"]:
            f["url"] = f"https://raw.githubusercontent.com/{e['fullName']}/{e['revision']}/{f['path']}"
    yield mut("revision differs from walk record", "E-WALK", revision_swap)


SYNTHETIC_MIT = (b"MIT License\n\nCopyright (c) synthetic test\n\nPermission is hereby granted, free of charge, to any person "
                 b"obtaining a copy\nof this software ...\n\nThe above copyright notice and this permission notice shall be "
                 b"included in all\ncopies or substantial portions of the Software.\n")
SYNTHETIC_GPL = b"GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n"


def licence_text_target(m):
    return next(e for e in m["entries"] if len(e["licence"]["files"]) == 1 and e["licence"]["files"][0]["spdx"] == "MIT")


def licence_text_cases(m):
    """Yield (name, expected code or None, manifest, files) for the --licence-dir recheck, on one entry whose single
    licence file is replaced by a synthetic text (no third-party text is shipped)."""
    target = licence_text_target(m)

    def with_text(data, recorded_sha=None, spdx="MIT", present=True):
        b = copy.deepcopy(m)
        e = next(x for x in b["entries"] if x["id"] == target["id"])
        f = e["licence"]["files"][0]
        f["sha256"] = recorded_sha or hashlib.sha256(data).hexdigest()
        f["bytes"] = len(data)
        f["spdx"] = spdx
        return b, ({(e["fullName"], f["path"]): data} if present else {})
    yield ("synthetic MIT text, recorded correctly", None) + with_text(SYNTHETIC_MIT)
    yield ("SHA-256 changed consistently in the manifest (review M5)", "E-LICENCE-TEXT") + with_text(SYNTHETIC_MIT, "ab" * 32)
    yield ("fetched text classifies differently", "E-LICENCE-TEXT") + with_text(SYNTHETIC_GPL, spdx="MIT")
    yield ("licence file missing from the checkout", "E-LICENCE-TEXT") + with_text(SYNTHETIC_MIT, present=False)
    yield ("text edited after recording", "E-LICENCE-TEXT") + with_text(SYNTHETIC_MIT, hashlib.sha256(SYNTHETIC_MIT + b" ").hexdigest())


def self_test(m, schema):
    import tempfile
    verify(m, schema)
    rejected, failures = 0, []
    for name, code, b, files in licence_text_cases(m):
        with tempfile.TemporaryDirectory() as d:
            for (full, path), data in files.items():
                (Path(d) / full).mkdir(parents=True, exist_ok=True)
                (Path(d) / full / path).write_bytes(data)
            try:
                recheck_licences(b, d, only={licence_text_target(m)["id"]})
                if code is not None:
                    failures.append(f"accepted: {name}")
            except Invalid as err:
                if code is None:
                    failures.append(f"{name}: unexpected {err}")
                elif err.code == code:
                    rejected += 1
                else:
                    failures.append(f"{name}: expected {code}, got {err}")
    for name, code, broken in mutations(m):
        try:
            verify(broken, schema)
            failures.append(f"accepted: {name}")
        except Invalid as err:
            if err.code == code:
                rejected += 1
            else:
                failures.append(f"{name}: expected {code}, got {err}")
    return rejected, failures


def main(argv):
    args = list(argv)
    selftest = "--self-test" in args
    if selftest:
        args.remove("--self-test")
    schema_path = HERE / "manifest.schema.json"
    licence_dir = None
    if "--licence-dir" in args:
        i = args.index("--licence-dir")
        if i + 1 >= len(args):
            print("usage: verify_manifest.py [--self-test] [--licence-dir DIR] [MANIFEST] [--schema SCHEMA]", file=sys.stderr)
            return 2
        licence_dir = args[i + 1]
        del args[i:i + 2]
    if "--schema" in args:
        i = args.index("--schema")
        if i + 1 >= len(args):
            print("usage: verify_manifest.py [--self-test] [--licence-dir DIR] [MANIFEST] [--schema SCHEMA]", file=sys.stderr)
            return 2
        schema_path = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) > 1 or any(a.startswith("-") for a in args):
        print("usage: verify_manifest.py [--self-test] [--licence-dir DIR] [MANIFEST] [--schema SCHEMA]", file=sys.stderr)
        return 2
    manifest_path = Path(args[0]) if args else HERE / "manifest-proposal.json"

    def strict(pairs):
        keys = [k for k, _ in pairs]
        if len(keys) != len(set(keys)):
            raise Invalid("E-JSON", "duplicate key")
        return dict(pairs)
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"), object_pairs_hook=strict)
    except OSError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    except (ValueError, Invalid) as err:
        print(f"INVALID E-JSON: {err}")
        return 1

    if selftest:
        rejected, failures = self_test(manifest, schema)
        for f in failures:
            print("FAIL", f)
        print(f"self-test: manifest valid; {rejected} broken manifests and licence texts rejected with the expected code; "
              f"{len(failures)} failures")
        return 0 if not failures and rejected >= 10 else 1
    try:
        info = verify(manifest, schema)
        checked = recheck_licences(manifest, licence_dir) if licence_dir else None
    except Invalid as err:
        print(f"INVALID {err}")
        return 1
    if checked is not None:
        print(f"licence recheck: {checked} licence files match SHA-256, length and classification")
    print(f"VALID: {info['entries']} entries; split digest {info['digest']}; "
          f"{info['negativeSearches']} held-out negative searches; {info['sameDomainSearches']} labelled same-domain")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
