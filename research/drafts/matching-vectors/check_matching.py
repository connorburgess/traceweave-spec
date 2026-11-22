#!/usr/bin/env python3
"""Independent checker for the draft matching vectors (catalogue-report-contract.md, draft-2).

Standard library only. It does not import build_vectors.py. For every vector it:

1. re-reads each artifact's extraction record, checks the input bytes, and recomputes every
   k-gram hash, window selection and fingerprint from the recorded tokens (contract §2);
2. rebuilds each catalogue from those records, serializes it with its own canonical-JSON
   writer, and checks the recorded catalogue object and SHA-256 (contract §3);
3. validates catalogues and report bodies against catalogue.schema.json / report.schema.json
   with its own interpreter for the schema keywords used, plus the contract's ordering,
   count and consistency rules, which a schema cannot express;
4. recomputes the comparison from the recorded fingerprints (contract §4–§5) and requires the
   expected report body and its digest to be identical;
5. checks the hand expectations (outcome codes, region counts, seeds, excerpt bounds) and the
   derivation label of each, and requires every recognized rule situation in at least two vectors.

Self-tests: targeted corruptions of the vectors (digests recomputed so that only the targeted layer
is wrong), single-defect catalogues against the consumer rules, single-field deletions against the
schemas, and wrong implementations (plausible misreadings) that the vectors must expose.

Usage: python3 -I check_matching.py [matching.json]
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHANNELS = ("exact", "normalized")
KGRAM_DOMAIN = b"traceweave/token-kgram/draft-1"
CATALOGUE_VERSION = "traceweave-catalogue-draft-2"
REPORT_VERSION = "traceweave-report-draft-2"
COMPARISON_ID = "traceweave-seed-merge-draft-2"
CC_KEYS = ["comparison", "modes", "minRegionDistinctHashes", "mergeGap", "maxSeedsPerMode", "maxRegionsPerMode",
           "suppressionCatalogueSha256"]
CATALOGUE_VARIANT = [None]   # set only by the wrong-implementation self-test
EX_KEYS = ["contract", "profile", "profileVersion", "channels", "k", "window", "hash", "maxInputBytes"]
GO_CODES = {"invalid-utf8", "bom", "nul", "input-too-large", "illegal-character", "unterminated-comment",
            "unterminated-literal", "malformed-literal"}
PROFILES = {
    ("go-tokens", "draft-1"): {"lang": "go", "codes": GO_CODES,
                               "literals": {"int", "float", "imag", "rune", "string"}},
    ("rust2024-tokens", "draft-1"): {"lang": "rust",
                                     "codes": GO_CODES | {"isolated-cr", "reserved-token", "unbalanced-delimiter",
                                                          "non-nfc-identifier", "malformed-identifier"},
                                     "literals": {"int", "float", "char", "byte", "string", "rawstring", "bytestring",
                                                  "rawbytestring", "cstring", "rawcstring"}},
}
U32 = 2**32 - 1
MAX_INT = 2**53 - 1


class CheckError(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise CheckError(msg)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ strict JSON and canonical form

def _no_dups(items):
    seen = {}
    for k, v in items:
        if k in seen:
            raise ValueError(f"duplicate key {k!r}")
        seen[k] = v
    return seen


def _refuse(s):
    raise ValueError(f"forbidden JSON number or constant {s!r}")


def strict_loads(raw: bytes):
    """UTF-8, no duplicate keys, no non-integer numbers, no NaN/Infinity."""
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_no_dups, parse_float=_refuse, parse_constant=_refuse)


def canon(x) -> str:
    """Contract §3.3: RFC 8785 restricted to objects, arrays, safe ASCII strings, integers 0..2^53-1, booleans,
    and null only where the schemas allow it (input-too-large entries)."""
    if x is None:
        return "null"
    if x is True:
        return "true"
    if x is False:
        return "false"
    if type(x) is int:
        if not 0 <= x <= MAX_INT:
            raise CheckError(f"integer {x} outside 0..2^53-1")
        return str(x)
    if type(x) is str:
        if any(not (0x20 <= ord(c) <= 0x7E) or c in '"\\' for c in x):
            raise CheckError(f"string {x!r} outside the canonical character set")
        return '"' + x + '"'
    if type(x) is list:
        return "[" + ",".join(canon(e) for e in x) + "]"
    if type(x) is dict:
        keys = list(x)
        for k in keys:
            canon(k)
        return "{" + ",".join(canon(k) + ":" + canon(x[k]) for k in sorted(keys)) + "}"
    raise CheckError(f"value of type {type(x).__name__} is not allowed in canonical JSON")


def canon_bytes(x) -> bytes:
    return canon(x).encode("ascii")


# ------------------------------------------------------------------ schema interpreter (subset)

SUPPORTED_KEYWORDS = {"$schema", "$id", "title", "description", "$defs", "$ref", "type", "const", "enum", "pattern",
                      "minimum", "maximum", "minLength", "maxLength", "properties", "required",
                      "additionalProperties", "items", "minItems", "maxItems", "oneOf"}


def same(a, b):
    """JSON equality that keeps booleans and integers apart."""
    if type(a) is not type(b):
        return False
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if type(a) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return a == b


def audit_schema(node, where="#"):
    if isinstance(node, dict):
        unknown = set(node) - SUPPORTED_KEYWORDS
        need(not unknown, f"schema {where}: unsupported keyword(s) {sorted(unknown)}")
        if "additionalProperties" in node:
            need(node["additionalProperties"] is False, f"schema {where}: only additionalProperties false is supported")
        if "$ref" in node:
            need(set(node) == {"$ref"} and node["$ref"].startswith("#/$defs/"), f"schema {where}: unsupported $ref form")
        for key in ("properties", "$defs"):
            for name, sub in node.get(key, {}).items():
                audit_schema(sub, f"{where}/{key}/{name}")
        for key in ("items",):
            if key in node:
                audit_schema(node[key], f"{where}/{key}")
        for i, sub in enumerate(node.get("oneOf", [])):
            audit_schema(sub, f"{where}/oneOf/{i}")


TYPES = {"object": lambda v: type(v) is dict, "array": lambda v: type(v) is list, "string": lambda v: type(v) is str,
         "integer": lambda v: type(v) is int, "boolean": lambda v: type(v) is bool}


def schema_errors(schema, inst, root, path="$"):
    """Return a list of violations (empty when valid)."""
    if "$ref" in schema:
        return schema_errors(root["$defs"][schema["$ref"][len("#/$defs/"):]], inst, root, path)
    errs = []
    if "type" in schema and not TYPES[schema["type"]](inst):
        return [f"{path}: expected {schema['type']}"]
    if "const" in schema and not same(inst, schema["const"]):
        errs.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and not any(same(inst, e) for e in schema["enum"]):
        errs.append(f"{path}: {inst!r} not in {schema['enum']}")
    if type(inst) is str:
        if "pattern" in schema and not re.fullmatch(schema["pattern"].removeprefix("^").removesuffix("$"), inst):
            errs.append(f"{path}: {inst!r} does not match {schema['pattern']}")
        if len(inst) < schema.get("minLength", 0) or len(inst) > schema.get("maxLength", float("inf")):
            errs.append(f"{path}: length out of range")
    if type(inst) is int:
        if inst < schema.get("minimum", -float("inf")) or inst > schema.get("maximum", float("inf")):
            errs.append(f"{path}: {inst} out of range")
    if type(inst) is dict:
        for r in schema.get("required", []):
            if r not in inst:
                errs.append(f"{path}: missing required field {r!r}")
        props = schema.get("properties", {})
        for k, v in inst.items():
            if k in props:
                errs += schema_errors(props[k], v, root, f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unknown field {k!r}")
    if type(inst) is list:
        if len(inst) < schema.get("minItems", 0) or len(inst) > schema.get("maxItems", float("inf")):
            errs.append(f"{path}: {len(inst)} items out of range")
        if "items" in schema:
            for i, e in enumerate(inst):
                errs += schema_errors(schema["items"], e, root, f"{path}[{i}]")
    if "oneOf" in schema:
        results = [schema_errors(s, inst, root, path) for s in schema["oneOf"]]
        ok = [r for r in results if not r]
        if len(ok) != 1:
            best = min(results, key=len)
            errs.append(f"{path}: matches {len(ok)} of {len(results)} alternatives"
                        + (f" (closest: {best[0]})" if best else ""))
    return errs


def schema_check(schema, inst, what, defname=None):
    target = {"$ref": f"#/$defs/{defname}"} if defname else schema
    errs = schema_errors(target, inst, schema)
    if errs:
        raise CheckError(f"{what}: schema violation: {errs[0]}")


# ------------------------------------------------------------------ extraction recomputation (extraction contract §6–§8)

def kgram_hash(cfg, channel, window_tokens, lit):
    parts = [KGRAM_DOMAIN, cfg["profile"].encode(), cfg["profileVersion"].encode(), channel.encode()]
    buf = b"".join(len(p).to_bytes(4, "big") + p for p in parts) + cfg["k"].to_bytes(4, "big")
    for t in window_tokens:
        cls, text = t["class"], t["text"]
        if channel == "normalized" and (cls == "ident" or cls in lit or (cls == "lifetime" and text not in ("'static", "'_"))):
            text = ""
        for s in (cls, text):
            b = s.encode("utf-8")
            buf += len(b).to_bytes(4, "big") + b
    return hashlib.sha256(buf).digest()[:8].hex()


def winnow(hashes, w):
    """Rightmost minimum per window, scanning each window right to left and keeping strict improvements."""
    m = len(hashes)
    if m == 0:
        return [], False
    starts = [0] if m < w else range(m - w + 1)
    width = m if m < w else w
    picks = []
    for s in starts:
        best = s + width - 1
        for p in range(s + width - 2, s - 1, -1):
            if int(hashes[p], 16) < int(hashes[best], 16):
                best = p
        picks.append(best)
    return picks, m < w


def recompute_record(rec, cfg, prof):
    """Fingerprints (per channel) recomputed from recorded tokens; also cross-checks the record itself."""
    data = base64.b64decode(rec["inputBase64"], validate=True)
    res = rec["result"]
    if res["status"] == "error":
        need(set(res) == {"status", "error"}, f"{rec['id']}: error record carries extra data")
        return data, None
    toks, k = res["tokens"], cfg["k"]
    need(res["tokenCount"] == len(toks), f"{rec['id']}: tokenCount")
    need(res["status"] == ("ok" if len(toks) >= k else "insufficient-tokens"), f"{rec['id']}: status")
    for t in toks:
        s, e = t["span"]
        need(0 <= s <= e <= len(data), f"{rec['id']}: token span outside input")
        if not t.get("inserted"):
            need(data[s:e] == t["text"].encode("utf-8"), f"{rec['id']}: token text != input[span]")
    out = {}
    for ch in CHANNELS:
        m = max(0, len(toks) - k + 1)
        hashes = [kgram_hash(cfg, ch, toks[i:i + k], prof["literals"]) for i in range(m)]
        spans = [[toks[i]["span"][0], toks[i + k - 1]["span"][1]] for i in range(m)]
        picks, partial = winnow(hashes, cfg["window"])
        fps = [{"hash": hashes[p], "position": p, "span": spans[p]} for p in sorted(set(picks))]
        rc = res["channels"][ch]
        need([g["hash"] for g in rc["kgrams"]] == hashes, f"{rec['id']}: recorded {ch} k-gram hashes differ from recomputation")
        need(rc["windowSelections"] == picks and rc["partialWindow"] == partial, f"{rec['id']}: {ch} selection differs")
        need([{"hash": f["hash"], "position": f["position"], "span": f["span"]} for f in rc["fingerprints"]] == fps,
             f"{rec['id']}: recorded {ch} fingerprints differ from recomputation")
        out[ch] = {"fingerprints": fps, "kgramCount": m, "partialWindow": partial}
    return data, out


def parse_extraction_config(raw: bytes):
    """Extraction contract §10, enough to bind a catalogue (full validation lives in check_vectors.py)."""
    text = raw.decode("utf-8")
    need(text.endswith("\n") and "\n" not in text[:-1] and "\r" not in text, "extraction config line form")
    obj = strict_loads(raw)
    need(type(obj) is dict and list(obj) == EX_KEYS, "extraction config keys")
    need((json.dumps(obj, separators=(",", ":")) + "\n").encode() == raw, "extraction config not canonical")
    return obj


def ex_config_bytes(cfg: dict) -> bytes:
    """Extraction contract §10 canonical form (fixed key order, final LF) from parsed values."""
    def val(v):
        return canon(v)
    return ("{" + ",".join(f'"{k}":{val(cfg[k])}' for k in EX_KEYS) + "}\n").encode("ascii")


class Sources:
    def __init__(self):
        self.files = {}

    def get(self, ref):
        need("#" in ref, f"bad source reference {ref!r}")
        fname, vid = ref.split("#", 1)
        if fname not in self.files:
            path = (HERE / fname).resolve()
            need(path.is_relative_to(HERE.parent), f"source {fname} outside research/drafts")
            d = strict_loads(path.read_bytes())
            raw = (path.parent / d["configFile"]).read_bytes()
            need(sha(raw) == d["configSha256"], f"{fname}: config digest")
            cfg = parse_extraction_config(raw)
            prof = PROFILES.get((cfg["profile"], cfg["profileVersion"]))
            need(prof is not None, f"{fname}: unknown profile")
            self.files[fname] = (d, raw, cfg, prof, {})
        d, raw, cfg, prof, cache = self.files[fname]
        if vid not in cache:
            rec = next((v for v in d["vectors"] if v["id"] == vid), None)
            need(rec is not None, f"source {ref} not found")
            cache[vid] = (rec,) + recompute_record(rec, cfg, prof)
        rec, data, chans = cache[vid]
        return rec, data, chans, raw, cfg


def build_catalogue(side, sources):
    entries, cfg_raw, cfg = [], None, None
    for a in side["artifacts"]:
        rec, data, chans, raw, c = sources.get(a["source"])
        need(cfg_raw is None or raw == cfg_raw, "artifacts of one catalogue must share configuration bytes")
        cfg_raw, cfg = raw, c
        e = {"byteLength": len(data), "id": a["id"], "sha256": sha(data), "status": rec["result"]["status"]}
        if chans is None and rec["result"]["error"]["code"] == "input-too-large":
            e["byteLength"], e["sha256"] = None, None          # extraction Q10
        if chans is None:
            e["error"] = dict(rec["result"]["error"])
        else:
            e["tokenCount"] = rec["result"]["tokenCount"]
            e["channels"] = chans
        entries.append(e)
    return {"artifacts": sorted(entries, key=lambda e: e["id"].encode()), "catalogueVersion": CATALOGUE_VERSION,
            "extractionConfig": {k: cfg[k] for k in EX_KEYS},
            "profile": {"configSha256": sha(cfg_raw), "id": cfg["profile"], "version": cfg["profileVersion"]}}




# ------------------------------------------------------------------ comparison configuration (contract §4)

def comparison_config(raw: bytes):
    """Return the parsed configuration, or None when it MUST be rejected."""
    try:
        text = raw.decode("utf-8")
        if not text.endswith("\n") or "\n" in text[:-1] or "\r" in text:
            return None
        obj = strict_loads(raw)           # duplicate keys rejected here, before any field is read
    except (ValueError, UnicodeDecodeError):
        return None
    if type(obj) is not dict or list(obj) != CC_KEYS:
        return None
    if obj["comparison"] != COMPARISON_ID or not same(obj["modes"], ["exact", "normalized"]):
        return None
    for key in ("minRegionDistinctHashes", "mergeGap", "maxSeedsPerMode", "maxRegionsPerMode"):
        if type(obj[key]) is not int or not 1 <= obj[key] <= U32:
            return None
    supp = obj["suppressionCatalogueSha256"]
    if type(supp) is not str or not (supp == "none" or re.fullmatch(r"[0-9a-f]{64}", supp)):
        return None
    rebuilt = ('{"comparison":"%s","modes":["exact","normalized"],"minRegionDistinctHashes":%d,"mergeGap":%d,'
               '"maxSeedsPerMode":%d,"maxRegionsPerMode":%d,"suppressionCatalogueSha256":"%s"}\n'
               % (obj["comparison"], obj["minRegionDistinctHashes"], obj["mergeGap"], obj["maxSeedsPerMode"],
                  obj["maxRegionsPerMode"], supp))
    return obj if rebuilt.encode() == raw else None




# ------------------------------------------------------------------ catalogue validation (contract §3.6)

def catalogue_rejection(raw: bytes, schema):
    """Return (catalogue, None) or (None, code), applying the contract's steps in order."""
    try:
        if CATALOGUE_VARIANT[0] == "last-duplicate-key-wins":
            obj = json.loads(raw.decode("utf-8"))
        else:
            obj = strict_loads(raw)       # duplicate keys rejected here, before any field is read
    except (ValueError, UnicodeDecodeError):
        return None, "malformed-catalogue"
    if type(obj) is not dict or type(obj.get("catalogueVersion")) is not str:
        return None, "malformed-catalogue"
    if obj["catalogueVersion"] != CATALOGUE_VERSION:
        return None, "unsupported-catalogue"
    if schema_errors(schema, obj, schema):
        return None, "malformed-catalogue"
    try:
        if canon_bytes(obj) != raw:
            return None, "malformed-catalogue"
    except CheckError:
        return None, "malformed-catalogue"
    prof = PROFILES.get((obj["profile"]["id"], obj["profile"]["version"]))
    if prof is None:
        return None, "unsupported-profile"
    return (obj, None) if not catalogue_semantic_errors(obj, prof) else (None, "malformed-catalogue")


def catalogue_semantic_errors(cat, prof):
    errs = []
    cfg = cat["extractionConfig"]
    k, w, cap = cfg["k"], cfg["window"], cfg["maxInputBytes"]
    if (cat["profile"]["id"], cat["profile"]["version"]) != (cfg["profile"], cfg["profileVersion"]):
        errs.append("profile triple differs from extractionConfig")
    if cat["profile"]["configSha256"] != sha(ex_config_bytes(cfg)):
        errs.append("configSha256 is not the digest of the extractionConfig canonical bytes")
    ids = [a["id"].encode() for a in cat["artifacts"]]
    if ids != sorted(set(ids)) or len(ids) != len(set(ids)):
        errs.append("artifacts not strictly ordered by id")
    digests = [a["sha256"] for a in cat["artifacts"] if a["sha256"] is not None]
    if len(set(digests)) != len(digests):
        errs.append("two artifacts with the same sha256")
    for a in cat["artifacts"]:
        n = a["byteLength"]
        if a["status"] == "error":
            code, off = a["error"]["code"], a["error"]["offset"]
            if code not in prof["codes"]:
                errs.append(f"{a['id']}: error code {code} not in the profile's closed list")
            if code == "input-too-large":
                if not (n is None and a["sha256"] is None and off == 0):
                    errs.append(f"{a['id']}: input-too-large has null sha256 and byteLength and offset 0")
            elif n is None or a["sha256"] is None or n > cap or off > n:
                errs.append(f"{a['id']}: error offset/size inconsistent")
            continue
        if n > cap:
            errs.append(f"{a['id']}: byteLength above maxInputBytes")
        tc = a["tokenCount"]
        if (a["status"] == "ok") != (tc >= k):
            errs.append(f"{a['id']}: status inconsistent with tokenCount")
        for ch in CHANNELS:
            c = a["channels"][ch]
            m = c["kgramCount"]
            if m != max(0, tc - k + 1):
                errs.append(f"{a['id']}/{ch}: kgramCount != tokenCount-k+1")
            if c["partialWindow"] != (1 <= m < w):
                errs.append(f"{a['id']}/{ch}: partialWindow")
            fps = c["fingerprints"]
            if c["partialWindow"] and len(fps) != 1:
                errs.append(f"{a['id']}/{ch}: a partial window selects exactly one fingerprint")
            if m >= w and not (-(-(m - w + 1) // w) <= len(fps) <= m - w + 1):
                errs.append(f"{a['id']}/{ch}: fingerprint count outside winnowing bounds")
            if m >= w and fps and not (fps[0]["position"] < w and fps[-1]["position"] >= m - w):
                errs.append(f"{a['id']}/{ch}: first or last window has no fingerprint")
            prev = None
            for f in fps:
                s, e = f["span"]
                if not (f["position"] < m and 0 <= s <= e <= n):
                    errs.append(f"{a['id']}/{ch}: fingerprint position or span out of range")
                if prev and not (f["position"] > prev["position"] and s > prev["span"][0] and e >= prev["span"][1]):
                    errs.append(f"{a['id']}/{ch}: fingerprints not ordered by position with monotone spans")
                if prev and f["position"] - prev["position"] > w:
                    errs.append(f"{a['id']}/{ch}: gap between fingerprints exceeds the window")
                prev = f
    return errs




# ------------------------------------------------------------------ comparison (contract §5)
#
# `variant` is used only by the wrong-implementation self-test: each value reproduces one plausible
# misreading of the contract, and the self-test requires the vectors to expose every one of them.

def compare(ref_raw, cand_raw, cc_raw, cat_schema, supp_raw=None, variant=None):
    body = {"inputs": {"candidateCatalogueSha256": sha(cand_raw), "comparisonConfigSha256": sha(cc_raw),
                       "referenceCatalogueSha256": sha(ref_raw),
                       "suppressionCatalogueSha256": "none" if supp_raw is None else sha(supp_raw)},
            "reportVersion": REPORT_VERSION, "resultKind": "token-fingerprint-comparison"}

    def rejected(cls, code, side):
        body["status"] = "rejected"
        body["rejection"] = {"class": cls, "code": code, "side": side}
        return body

    cc = comparison_config(cc_raw)
    if cc is None:
        return rejected("unsupported-input", "unsupported-comparison-config", "comparison-config")
    if variant == "none-plus-supplied-ignored" and cc["suppressionCatalogueSha256"] == "none":
        supp_raw = None
    binding_ok = cc["suppressionCatalogueSha256"] == ("none" if supp_raw is None else sha(supp_raw))
    if variant not in ("suppression-lenient-digest", "binding-after-validation") and not binding_ok:
        return rejected("mismatch", "suppression-catalogue-mismatch", "suppression")
    cats = {}
    for side, raw in (("reference", ref_raw), ("candidate", cand_raw), ("suppression", supp_raw)):
        if raw is None:
            continue
        cats[side], err = catalogue_rejection(raw, cat_schema)
        if err:
            return rejected("unsupported-input", err, side)
    if variant == "binding-after-validation" and not binding_ok:
        return rejected("mismatch", "suppression-catalogue-mismatch", "suppression")
    ref, cand = cats["reference"], cats["candidate"]
    others = [s for s in (("suppression", "candidate") if variant == "suppression-before-candidate"
                          else ("candidate", "suppression")) if s in cats]
    for side in others:
        if [cats[side]["profile"]["id"], cats[side]["profile"]["version"]] != [ref["profile"]["id"], ref["profile"]["version"]]:
            return rejected("mismatch", "profile-mismatch", side)
    for side in others:
        if cats[side]["profile"]["configSha256"] != ref["profile"]["configSha256"]:
            return rejected("mismatch", "config-mismatch", side)

    common = {ch: frozenset() for ch in CHANNELS}
    suppression = {"status": "none"}
    if "suppression" in cats and variant != "suppression-ignored":
        sup = cats["suppression"]
        common = {ch: frozenset(f["hash"] for a in sup["artifacts"] if a["status"] == "ok"
                                for f in a["channels"][ch]["fingerprints"]) for ch in CHANNELS}
    if variant == "draft1-document-frequency":
        for ch in CHANNELS:
            df = {}
            for a in ref["artifacts"]:
                if a["status"] == "ok":
                    for h in set(f["hash"] for f in a["channels"][ch]["fingerprints"]):
                        df[h] = df.get(h, 0) + 1
            common[ch] = common[ch] | frozenset(h for h, n in df.items() if n >= 3)
    if "suppression" in cats:
        sup = cats["suppression"]
        count = sum(a["status"] == "ok" for a in sup["artifacts"]) if variant == "artifact-count-ok-only" else len(sup["artifacts"])
        suppression = {"artifactCount": count, "status": "supplied",
                       "distinctHashes": {ch: len({f["hash"] for a in sup["artifacts"] if a["status"] == "ok"
                                                   for f in a["channels"][ch]["fingerprints"]}) for ch in CHANNELS}}

    pairs = []
    for ra in ref["artifacts"]:
        for ca in cand["artifacts"]:
            p = {"candidate": {"id": ca["id"], "sha256": ca["sha256"]}, "reference": {"id": ra["id"], "sha256": ra["sha256"]}}
            st = (ra["status"], ca["status"])
            if st[0] == "error":
                p["status"], p["outcome"] = "not-compared", {"class": "unsupported-input", "code": "reference-extraction-error"}
            elif st[1] == "error":
                p["status"], p["outcome"] = "not-compared", {"class": "unsupported-input", "code": "candidate-extraction-error"}
            elif "insufficient-tokens" in st:
                p["status"], p["outcome"] = "not-compared", {"class": "abstain", "code": "insufficient-tokens"}
            else:
                p["status"] = "compared"
                p["modes"] = {ch: compare_mode(ra["channels"][ch]["fingerprints"], ca["channels"][ch]["fingerprints"],
                                               common[ch], cc, variant) for ch in CHANNELS}
            pairs.append(p)
    body.update({"status": "compared", "profile": dict(ref["profile"]),
                 "referenceArtifactCount": len(ref["artifacts"]), "candidateArtifactCount": len(cand["artifacts"]),
                 "comparison": {"comparison": cc["comparison"], "maxRegionsPerMode": cc["maxRegionsPerMode"],
                                "maxSeedsPerMode": cc["maxSeedsPerMode"], "mergeGap": cc["mergeGap"],
                                "minRegionDistinctHashes": cc["minRegionDistinctHashes"], "modes": list(cc["modes"]),
                                "parameterStatus": "experimental",
                                "suppressionCatalogueSha256": cc["suppressionCatalogueSha256"]},
                 "suppression": suppression, "pairs": pairs})
    return body


def fraction(n, d, variant):
    if variant == "fractions-reduced" and d:
        g = __import__("math").gcd(n, d)
        n, d = n // g, d // g
    return {"denominator": d, "numerator": n}


def compare_mode(rf, cf, common, cc, variant=None):
    hr, hc = set(f["hash"] for f in rf), set(f["hash"] for f in cf)
    inter = hr & hc
    cont_inter = inter - common if variant == "containment-excludes-common" else inter
    result = {"containment": {"candidateInReference": fraction(len(cont_inter), len(hc), variant),
                              "referenceInCandidate": fraction(len(cont_inter), len(hr), variant)},
              "sharedCommonDistinctHashes": len(inter & common),
              "similarity": {"jaccard": fraction(len(cont_inter), len(hr | hc), variant)}}
    cand_by_hash = {}
    for f in cf:
        cand_by_hash.setdefault(f["hash"], []).append(f)
    seeds = []                                   # (p, q, refFp, candFp)
    seen_hash = set()
    for r in rf:
        for c in cand_by_hash.get(r["hash"], ()):
            if variant == "first-occurrence-only":
                if r["hash"] in seen_hash:
                    break
                seeds.append((r["position"], c["position"], r, c))
                seen_hash.add(r["hash"])
                break
            seeds.append((r["position"], c["position"], r, c))
    seeds.sort(key=lambda s: (s[0], s[1]))
    result["seedCount"] = len(seeds)
    zero = {"belowMinimumEvidence": 0, "commonOnly": 0, "reportable": 0}
    over = len(seeds) >= cc["maxSeedsPerMode"] if variant == "seed-limit-inclusive" else len(seeds) > cc["maxSeedsPerMode"]
    if not seeds or over:
        result.update(outcome={"class": "no-match", "code": "no-shared-fingerprints"} if not seeds
                      else {"class": "abstain", "code": "seed-limit-exceeded"},
                      regionCounts=zero, regions=[], truncatedRegions=0)
        return result
    gap = cc["mergeGap"] + (1 if variant == "merge-gap-plus-one" else -1 if variant == "merge-gap-strict" else 0)
    open_region, regions = {}, []
    for s in seeds:
        d = s[1] - s[0]
        cur = open_region.get(d)
        if cur is not None and s[0] - cur[-1][0] <= gap:
            cur.append(s)
        else:
            cur = [s]
            regions.append(cur)
            open_region[d] = cur
    built = []
    for reg in regions:
        hashes = set(s[2]["hash"] for s in reg)
        dc = len(hashes & common)
        evidence = (len(reg) - len([s for s in reg if s[2]["hash"] in common])) if variant == "evidence-counts-seeds" \
            else len(hashes) - dc
        need_min = cc["minRegionDistinctHashes"] + (1 if variant == "evidence-strictly-greater" else 0)
        status = "reportable" if evidence >= need_min else "below-minimum-evidence" if evidence >= 1 else "common-only"
        built.append({"ambiguous": False,
                      "candidateSpan": [min(s[3]["span"][0] for s in reg), max(s[3]["span"][1] for s in reg)],
                      "distinctCommonHashes": dc, "distinctHashes": len(hashes),
                      "referenceSpan": [min(s[2]["span"][0] for s in reg), max(s[2]["span"][1] for s in reg)],
                      "seeds": [[s[0], s[1]] for s in reg], "status": status})
    if variant == "order-by-diagonal":
        built.sort(key=lambda r: (r["seeds"][0][1] - r["seeds"][0][0], r["seeds"][0][0]))
    else:
        built.sort(key=lambda r: tuple(r["seeds"][0]))
    if variant == "truncate-before-ambiguity":
        built = built[:cc["maxRegionsPerMode"]]
    reportable = [r for r in (built[:cc["maxRegionsPerMode"]] if variant == "ambiguity-among-listed" else built)
                  if r["status"] == "reportable"]
    for a in reportable:
        for b in reportable:
            if a is b:
                continue
            if variant == "ambiguity-by-span-overlap":
                hit = (a["referenceSpan"][0] < b["referenceSpan"][1] and b["referenceSpan"][0] < a["referenceSpan"][1]) or \
                      (a["candidateSpan"][0] < b["candidateSpan"][1] and b["candidateSpan"][0] < a["candidateSpan"][1])
            elif variant == "one-to-many-is-match":
                hit = bool({q for _, q in a["seeds"]} & {q for _, q in b["seeds"]})
            else:
                hit = bool({p for p, _ in a["seeds"]} & {p for p, _ in b["seeds"]}
                           or {q for _, q in a["seeds"]} & {q for _, q in b["seeds"]})
            a["ambiguous"] = a["ambiguous"] or hit
    counted = built[:cc["maxRegionsPerMode"]] if variant == "counts-after-truncation" else built
    counts = dict(zero)
    for r in counted:
        counts[{"reportable": "reportable", "below-minimum-evidence": "belowMinimumEvidence",
                "common-only": "commonOnly"}[r["status"]]] += 1
    has_below = any(r["status"] == "below-minimum-evidence" for r in built)
    if variant == "below-ranked-above-ambiguous" and reportable and all(r["ambiguous"] for r in reportable) and has_below:
        outcome = ("no-match", "below-minimum-evidence")
    elif reportable and not all(r["ambiguous"] for r in reportable):
        outcome = ("match", "match")
    elif reportable:
        outcome = ("abstain", "ambiguous")
    elif has_below:
        outcome = ("no-match", "below-minimum-evidence")
    else:
        outcome = ("no-match", "common-only")
    cap = cc["maxRegionsPerMode"]
    result.update(outcome={"class": outcome[0], "code": outcome[1]}, regionCounts=counts, regions=built[:cap],
                  truncatedRegions=max(0, len(built) - cap))
    return result


VARIANTS = [
    # (name, description) — reviewer's 13 (adapted to draft-2 where the rule changed) and five more.
    ("merge-gap-plus-one", "R1: merge joins gap <= mergeGap+1"),
    ("ambiguity-by-span-overlap", "R2: ambiguity by overlapping spans instead of shared positions"),
    ("merge-gap-strict", "R3: merge uses gap < mergeGap"),
    ("evidence-strictly-greater", "R4: minimum evidence tested as d > min"),
    ("evidence-counts-seeds", "R5 (draft-2 form): evidence counts seeds/occurrences, not distinct hashes"),
    ("suppression-ignored", "R6 (draft-2 form): common set not taken from the bound suppression catalogue"),
    ("order-by-diagonal", "R7: regions ordered by (diagonal, p)"),
    ("fractions-reduced", "R8: fractions reduced"),
    ("below-ranked-above-ambiguous", "R9: below-minimum-evidence ranked above ambiguous"),
    ("first-occurrence-only", "R10: first occurrence only, no cross product"),
    ("containment-excludes-common", "R11: containment and similarity exclude common hashes"),
    ("one-to-many-is-match", "R12: one reference region to many candidate regions counted as match"),
    ("trailing-lf", "R13: canonical body bytes with a trailing LF"),
    ("truncate-before-ambiguity", "N1: cap applied before ambiguity and counting"),
    ("counts-after-truncation", "N2: regionCounts counted after truncation"),
    ("seed-limit-inclusive", "N3: seed limit tested as seedCount >= maxSeedsPerMode"),
    ("suppression-lenient-digest", "N4: suppression digest not enforced"),
    ("last-duplicate-key-wins", "N5: catalogue duplicate keys resolved last-wins"),
    ("draft1-document-frequency", "C(a): draft-1 reference document-frequency suppression applied on top of the boilerplate catalogue"),
    ("ambiguity-among-listed", "C(b): ambiguity computed only among the regions listed under the cap"),
    ("none-plus-supplied-ignored", "C(c): configuration none with a supplied suppression catalogue silently ignored"),
    ("binding-after-validation", "C(d): suppression binding checked after catalogue validation"),
    ("suppression-before-candidate", "C(e): suppression profile/config checks run before the candidate's"),
    ("artifact-count-ok-only", "C(f): suppression.artifactCount counts ok entries only"),
]


# ------------------------------------------------------------------ report rules beyond the schema (contract §6)

CODE_FOR = {"reportable": "reportable", "below-minimum-evidence": "belowMinimumEvidence", "common-only": "commonOnly"}


def report_semantic_check(body, what):
    need(body["inputs"]["suppressionCatalogueSha256"] == body.get("comparison", {}).get(
        "suppressionCatalogueSha256", body["inputs"]["suppressionCatalogueSha256"]) or body["status"] == "rejected",
         f"{what}: comparison.suppressionCatalogueSha256 differs from inputs")
    if body["status"] == "rejected":
        return
    cc = body["comparison"]
    need((body["suppression"]["status"] == "none") == (cc["suppressionCatalogueSha256"] == "none"),
         f"{what}: suppression block inconsistent with the configuration")
    keys = [(p["reference"]["id"].encode(), p["candidate"]["id"].encode()) for p in body["pairs"]]
    need(keys == sorted(keys) and len(set(keys)) == len(keys), f"{what}: pairs not ordered by (reference id, candidate id)")
    need(len(keys) == body["referenceArtifactCount"] * body["candidateArtifactCount"],
         f"{what}: pairs must be the full reference x candidate product")
    for p in body["pairs"]:
        if p["status"] != "compared":
            continue
        for ch, m in p["modes"].items():
            where = f"{what}: {p['reference']['id']}/{p['candidate']['id']} {ch}"
            regs, rc, code = m["regions"], m["regionCounts"], m["outcome"]["code"]
            total = sum(rc.values())
            need(len(regs) == min(total, cc["maxRegionsPerMode"]) and m["truncatedRegions"] == total - len(regs),
                 f"{where}: listed regions, cap and truncatedRegions inconsistent")
            need([tuple(r["seeds"][0]) for r in regs] == sorted(tuple(r["seeds"][0]) for r in regs),
                 f"{where}: regions not ordered by first seed")
            need(sum(len(r["seeds"]) for r in regs) <= m["seedCount"], f"{where}: seedCount below listed seeds")
            if m["truncatedRegions"] == 0 and code != "seed-limit-exceeded":
                need(sum(len(r["seeds"]) for r in regs) == m["seedCount"], f"{where}: seedCount != listed seeds")
                for st, key in CODE_FOR.items():
                    need(rc[key] == sum(r["status"] == st for r in regs), f"{where}: regionCounts.{key} != listed regions")
            for r in regs:
                sd = r["seeds"]
                need(len({q - p for p, q in sd}) == 1, f"{where}: a region's seeds must share one diagonal")
                need(all(b[0] - a[0] >= 1 for a, b in zip(sd, sd[1:])), f"{where}: seeds not ordered")
                need(all(b[0] - a[0] <= cc["mergeGap"] for a, b in zip(sd, sd[1:])), f"{where}: seed gap exceeds mergeGap")
                need(r["distinctCommonHashes"] <= r["distinctHashes"] <= len(sd), f"{where}: distinct hash counts")
                d = r["distinctHashes"] - r["distinctCommonHashes"]
                want = "reportable" if d >= cc["minRegionDistinctHashes"] else "below-minimum-evidence" if d else "common-only"
                need(r["status"] == want, f"{where}: region status {r['status']} inconsistent with distinct counts")
                need(r["status"] == "reportable" or r["ambiguous"] is False, f"{where}: only reportable regions can be ambiguous")
                for key in ("referenceSpan", "candidateSpan"):
                    need(r[key][0] <= r[key][1], f"{where}: inverted {key}")
            if m["seedCount"] == 0:
                need(code == "no-shared-fingerprints" and total == 0, f"{where}: outcome {code} with no seeds")
            elif m["seedCount"] > cc["maxSeedsPerMode"]:
                need(code == "seed-limit-exceeded" and total == 0, f"{where}: seed limit not applied")
            else:
                need(code != "seed-limit-exceeded" and total > 0, f"{where}: seed limit applied below the limit")
                if rc["reportable"]:
                    need(code in ("match", "ambiguous"), f"{where}: outcome {code} with reportable regions")
                    if m["truncatedRegions"] == 0:
                        rep = [r for r in regs if r["status"] == "reportable"]
                        need(code == ("ambiguous" if all(r["ambiguous"] for r in rep) else "match"),
                             f"{where}: outcome {code} inconsistent with ambiguity flags")
                else:
                    need(code == ("below-minimum-evidence" if rc["belowMinimumEvidence"] else "common-only"),
                         f"{where}: outcome {code} inconsistent with region counts")
            cr, rcn, jac = m["containment"]["candidateInReference"], m["containment"]["referenceInCandidate"], m["similarity"]["jaccard"]
            need(cr["numerator"] == rcn["numerator"] == jac["numerator"], f"{where}: shared-hash numerators differ")
            need(all(f["numerator"] <= f["denominator"] for f in (cr, rcn, jac)), f"{where}: numerator above denominator")
            need(jac["denominator"] == cr["denominator"] + rcn["denominator"] - jac["numerator"], f"{where}: jaccard union")
            need(m["sharedCommonDistinctHashes"] <= jac["numerator"], f"{where}: sharedCommonDistinctHashes")
            need((m["seedCount"] > 0) == (jac["numerator"] > 0), f"{where}: seeds exist iff a hash is shared")


def first_difference(a, b, path="body"):
    if type(a) is not type(b):
        return path
    if type(a) is dict:
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                return f"{path}.{k}"
            d = first_difference(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if type(a) is list:
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_difference(x, y, f"{path}[{i}]")
            if d:
                return d
        return None if len(a) == len(b) else f"{path} (length {len(a)} vs {len(b)})"
    return None if a == b else path


# ------------------------------------------------------------------ hand expectations

def excerpt_ranges(text: bytes, excerpts):
    out = []
    for ex in excerpts if isinstance(excerpts, list) else [excerpts]:
        b, start = ex.encode("utf-8"), 0
        while (i := text.find(b, start)) >= 0:
            out.append((i, i + len(b)))
            start = i + 1
    return out


def check_hand(v, body, texts):
    h = v["handExpectations"]
    need(body["status"] == h["status"], f"hand: status {body['status']} != {h['status']}")
    if h["status"] == "rejected":
        need([body["rejection"]["code"], body["rejection"]["side"]] == [h["rejectionCode"], h["rejectionSide"]],
             f"hand: rejection {body['rejection']}")
        return
    if "suppressionArtifactCount" in h:
        need(body["suppression"].get("artifactCount") == h["suppressionArtifactCount"],
             f"hand: suppression.artifactCount {body['suppression'].get('artifactCount')} != {h['suppressionArtifactCount']}")
    pairs = {(p["reference"]["id"], p["candidate"]["id"]): p for p in body["pairs"]}
    need(sorted(pairs) == sorted((x["reference"], x["candidate"]) for x in h["pairs"]), "hand: pair set differs")
    labels = set()
    for x in h["pairs"]:
        p = pairs[(x["reference"], x["candidate"])]
        need(p["status"] == x["status"], f"hand: pair status {p['status']}")
        if p["status"] == "not-compared":
            need(p["outcome"]["code"] == x["outcomeCode"], f"hand: pair outcome {p['outcome']['code']}")
            continue
        for ch, e in x["modes"].items():
            need(e.get("derivation") in ("hand", "computed-then-reviewed"), "hand: each mode needs a derivation label")
            labels.add(e["derivation"])
            m = p["modes"][ch]
            regs = m["regions"]
            rep = [r for r in regs if r["status"] == "reportable"]
            tag = f"hand: {x['reference']}/{x['candidate']} {ch}"
            need(m["outcome"]["code"] in e["codeIn"], f"{tag}: outcome {m['outcome']['code']} not in {e['codeIn']}")
            need(e.get("reportable", m["regionCounts"]["reportable"]) == m["regionCounts"]["reportable"], f"{tag}: reportable count")
            need(e.get("regions", sum(m["regionCounts"].values())) == sum(m["regionCounts"].values()), f"{tag}: region count")
            need(e.get("listed", len(regs)) == len(regs), f"{tag}: listed region count")
            need(e.get("seedCount", m["seedCount"]) == m["seedCount"], f"{tag}: seedCount")
            if "seeds" in e:
                need([r["seeds"] for r in regs] == e["seeds"], f"{tag}: seeds differ from the hand derivation")
            if "ambiguous" in e:
                need([r["ambiguous"] for r in regs] == e["ambiguous"], f"{tag}: ambiguity flags differ")
            if e.get("exhaustiveDiagonalZero"):
                need(len(regs) == 1 and all(a == b for a, b in regs[0]["seeds"]), f"{tag}: not one diagonal-0 region")
            if "candidateShift" in e:
                need(all([s + e["candidateShift"] for s in r["referenceSpan"]] == r["candidateSpan"] for r in regs),
                     f"{tag}: candidate spans are not reference spans + {e['candidateShift']} bytes")
            for side, key in (("reference", "referenceSpan"), ("candidate", "candidateSpan")):
                if "within" in e:
                    rng = excerpt_ranges(texts[side][x[side]], e["within"][side])
                    need(rng, f"{tag}: excerpt absent from {side}")
                    for r in rep:
                        need(any(lo <= r[key][0] and r[key][1] <= hi for lo, hi in rng), f"{tag}: {key} {r[key]} outside the hand excerpt")
    want = "hand" if labels <= {"hand"} else "mixed"
    need(v["derivation"] == want, f"hand: vector derivation must be {want!r}")


# ------------------------------------------------------------------ vector checks

class Context:
    def __init__(self):
        self.cat_schema = strict_loads((HERE / "catalogue.schema.json").read_bytes())
        self.rep_schema = strict_loads((HERE / "report.schema.json").read_bytes())
        self.rec_schema = strict_loads((HERE / "record.schema.json").read_bytes())
        audit_schema(self.cat_schema)
        audit_schema(self.rep_schema)
        audit_schema(self.rec_schema)
        self.sources = Sources()


SIDES = ("reference", "candidate", "suppression")


def vector_inputs(v, doc, ctx, stats=None):
    cc = v["comparisonConfig"]
    if "file" in cc:
        need(cc["file"] == doc["comparisonConfigFile"], "only the shipped comparison config may be referenced by file")
        cc_raw = (HERE / cc["file"]).read_bytes()
        need(sha(cc_raw) == doc["comparisonConfigSha256"], "comparison config digest")
    else:
        cc_raw = base64.b64decode(cc["bytesBase64"], validate=True)
    raws, texts = {}, {}
    for side in SIDES:
        if side not in v:
            need(side == "suppression", f"missing {side} catalogue")
            continue
        entry = v[side]
        texts[side] = {}
        kinds = [k for k in ("canonical", "bytesBase64") if k in entry]
        need(len(kinds) == 1, f"{side}: exactly one of canonical / bytesBase64")
        if "synthetic" in entry:
            need("artifacts" not in entry and "canonical" in entry and type(entry["synthetic"]) is str,
                 f"{side}: a synthetic catalogue has a note and a canonical object and no artifact sources")
            schema_check(ctx.cat_schema, entry["canonical"], f"{side} synthetic catalogue")
            raw = canon_bytes(entry["canonical"])
            need(catalogue_rejection(raw, ctx.cat_schema)[1] is None, f"{side}: synthetic catalogue fails the §3.6 rules")
            if stats is not None:
                stats["synthetic"] += 1
        else:
            for a in entry["artifacts"]:
                _, data, _, _, _ = ctx.sources.get(a["source"])
                texts[side][a["id"]] = data
            built = build_catalogue(entry, ctx.sources)
            if "canonical" in entry:
                need("fabricated" not in entry, f"{side}: canonical catalogues are not fabricated")
                need(entry["canonical"] == built, f"{side} catalogue differs from the one rebuilt from its extraction records "
                                                  f"(first difference at {first_difference(entry['canonical'], built, 'catalogue')})")
                schema_check(ctx.cat_schema, entry["canonical"], f"{side} catalogue")
                raw = canon_bytes(entry["canonical"])
                if stats is not None:
                    stats["catalogues"] += 1
            else:
                need(type(entry.get("fabricated")) is str and entry["fabricated"], f"{side}: raw catalogue bytes need a 'fabricated' note")
                raw = base64.b64decode(entry["bytesBase64"], validate=True)
                if stats is not None:
                    stats["fabricated"] += 1
        need(sha(raw) == entry["sha256"], f"{side} catalogue sha256 does not match its canonical bytes")
        raws[side] = raw
    return cc_raw, raws, texts


def check_vector(v, doc, ctx, stats):
    need(v.get("derivation") in ("hand", "mixed"), "derivation must be 'hand' or 'mixed'")
    cc_raw, raws, texts = vector_inputs(v, doc, ctx, stats)
    exp = v["expectedReport"]
    body = exp["body"]
    schema_check(ctx.rep_schema, body, "expected report body", "body")
    report_semantic_check(body, "expected report body")
    got = compare(raws["reference"], raws["candidate"], cc_raw, ctx.cat_schema, raws.get("suppression"))
    need(body == got, f"expected report body differs from recomputation at {first_difference(body, got)}")
    need(sha(canon_bytes(body)) == exp["bodySha256"], "bodySha256 is not the digest of the canonical body")
    check_hand(v, body, texts)
    if body["status"] == "rejected":
        stats["rejected"] += 1
    else:
        for p in body["pairs"]:
            stats["pairs"] += 1
            for m in p.get("modes", {}).values():
                stats["regions"] += sum(m["regionCounts"].values())
                stats["reportable"] += m["regionCounts"]["reportable"]


SITUATIONS = ("match-over-ambiguous", "match-over-weaker", "ambiguous-over-weaker", "below-over-common",
              "region-repeats-hash", "mixed-common-region", "merge-split-at-gap-plus-one", "merge-join-at-gap",
              "span-overlap-without-shared-position", "truncated", "seed-limit", "ambiguity-before-cap")


def situations(doc):
    """Recognize rule situations from the expected bodies themselves (not from tags)."""
    seen = {s: set() for s in SITUATIONS}
    for v in doc["vectors"]:
        b = v["expectedReport"]["body"]
        if b["status"] != "compared":
            continue
        gap = b["comparison"]["mergeGap"]
        for p in b["pairs"]:
            for m in p.get("modes", {}).values():
                rc, regs, code = m["regionCounts"], m["regions"], m["outcome"]["code"]
                if code == "match" and any(r["ambiguous"] for r in regs):
                    seen["match-over-ambiguous"].add(v["id"])
                if code == "match" and (rc["belowMinimumEvidence"] or rc["commonOnly"]):
                    seen["match-over-weaker"].add(v["id"])
                if code == "ambiguous" and (rc["belowMinimumEvidence"] or rc["commonOnly"]):
                    seen["ambiguous-over-weaker"].add(v["id"])
                if code == "below-minimum-evidence" and rc["commonOnly"]:
                    seen["below-over-common"].add(v["id"])
                if m["truncatedRegions"]:
                    seen["truncated"].add(v["id"])
                    listed_rep = [r for r in regs if r["status"] == "reportable"]
                    if listed_rep and len(listed_rep) < rc["reportable"] and any(r["ambiguous"] for r in listed_rep):
                        seen["ambiguity-before-cap"].add(v["id"])
                if code == "seed-limit-exceeded":
                    seen["seed-limit"].add(v["id"])
                for r in regs:
                    if len(r["seeds"]) > r["distinctHashes"]:
                        seen["region-repeats-hash"].add(v["id"])
                    if 0 < r["distinctCommonHashes"] < r["distinctHashes"]:
                        seen["mixed-common-region"].add(v["id"])
                    if any(b2[0] - a2[0] == gap for a2, b2 in zip(r["seeds"], r["seeds"][1:])):
                        seen["merge-join-at-gap"].add(v["id"])
                by_diag = {}
                for r in regs:
                    by_diag.setdefault(r["seeds"][0][1] - r["seeds"][0][0], []).append(r)
                for rs in by_diag.values():
                    for a2, b2 in zip(rs, rs[1:]):
                        if b2["seeds"][0][0] - a2["seeds"][-1][0] == gap + 1:
                            seen["merge-split-at-gap-plus-one"].add(v["id"])
                rep = [r for r in regs if r["status"] == "reportable"]
                for a2 in rep:
                    for b2 in rep:
                        if a2 is not b2 and not a2["ambiguous"] and \
                                a2["candidateSpan"][0] < b2["candidateSpan"][1] and b2["candidateSpan"][0] < a2["candidateSpan"][1]:
                            seen["span-overlap-without-shared-position"].add(v["id"])
    return seen


def check_all(doc, ctx, negatives, example):
    stats = dict.fromkeys(("catalogues", "fabricated", "synthetic", "pairs", "regions", "reportable", "rejected"), 0)
    need(comparison_config((HERE / doc["comparisonConfigFile"]).read_bytes()) is not None, "shipped comparison config invalid")
    need(sha((HERE / doc["comparisonConfigFile"]).read_bytes()) == doc["comparisonConfigSha256"], "comparison config digest")
    for n in negatives:
        need(comparison_config(base64.b64decode(n["bytesBase64"])) is None, f"negative comparison config {n['id']} accepted")
    ids = set()
    for v in doc["vectors"]:
        need(v["id"] not in ids, f"duplicate vector id {v['id']}")
        ids.add(v["id"])
        try:
            check_vector(v, doc, ctx, stats)
        except CheckError as exc:
            raise CheckError(f"{v['id']}: {exc}") from None
        except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
            raise CheckError(f"{v['id']}: malformed vector ({exc!r})") from None
    tags = {t for v in doc["vectors"] for t in v["tags"]}
    need(not set(doc["requiredTags"]) - tags, f"missing required cases {sorted(set(doc['requiredTags']) - tags)}")
    groups = {}
    for v in doc["vectors"]:
        for t in v["tags"]:
            if t.startswith("invariance-group-"):
                groups.setdefault(t, []).append(v)
    for g, vs in groups.items():
        need(len(vs) >= 2, f"{g}: an invariance group needs at least two vectors")
        need(all(sum(a["status"] == "ok" for a in v["reference"]["canonical"]["artifacts"]) >= 2 for v in vs),
             f"{g}: invariance vectors need at least two ok reference artifacts")
        results = {}
        for v in vs:
            for p in v["expectedReport"]["body"]["pairs"]:
                key = (p["reference"]["id"], p["reference"]["sha256"], p["candidate"]["id"], p["candidate"]["sha256"])
                val = {k: p[k] for k in ("status", "modes", "outcome") if k in p}
                need(results.setdefault(key, val) == val, f"{g}: pair {key[0]}/{key[2]} differs between vectors "
                                                         "(adding a reference file changed an outcome)")
    stats["invariance-groups"] = len(groups)
    seen = situations(doc)
    thin = {s: sorted(ids_) for s, ids_ in seen.items() if len(ids_) < 2}
    need(not thin, f"rule situations exercised by fewer than two vectors: {thin}")
    stats["situations"] = {s: len(x) for s, x in seen.items()}
    diverge = False
    for v in doc["vectors"]:
        if "large-host" in v["tags"]:
            for p in v["expectedReport"]["body"]["pairs"]:
                m = p["modes"]["exact"]
                c, j = m["containment"]["referenceInCandidate"], m["similarity"]["jaccard"]
                diverge |= c["numerator"] == c["denominator"] > 0 and j["numerator"] < j["denominator"]
    need(diverge, "no large-host vector shows complete containment with partial similarity")
    schema_check(ctx.rep_schema, example, "example-report.json")
    need(example["provenance"]["bodySha256"] == sha(canon_bytes(example["body"])), "example provenance.bodySha256")
    need(example["provenance"]["comparisonConfigSha256"] == example["body"]["inputs"]["comparisonConfigSha256"],
         "example provenance.comparisonConfigSha256 differs from the body")
    need(any(example["body"] == v["expectedReport"]["body"] for v in doc["vectors"]), "example body is not a vector body")
    return stats


# ------------------------------------------------------------------ corruption self-test

def corruptions(doc, negatives, example):
    """Yield (name, doc, negatives, example). Digests are refreshed so only the targeted layer is wrong."""

    def vec(d, vid):
        return next(x for x in d["vectors"] if x["id"] == vid)

    def refresh(v):
        for side in SIDES:
            if side in v and "canonical" in v[side]:
                try:
                    v[side]["sha256"] = sha(canon_bytes(v[side]["canonical"]))
                except CheckError:
                    pass
        b = v["expectedReport"]["body"]
        b["inputs"]["referenceCatalogueSha256"] = v["reference"]["sha256"]
        b["inputs"]["candidateCatalogueSha256"] = v["candidate"]["sha256"]
        try:
            v["expectedReport"]["bodySha256"] = sha(canon_bytes(b))
        except CheckError:
            pass

    def mode(v, ch, pair=0):
        return v["expectedReport"]["body"]["pairs"][pair]["modes"][ch]

    def make(name, vid, fn, do_refresh=True, neg=None, ex=None):
        d = copy.deepcopy(doc)
        v = vec(d, vid) if vid else None
        fn(v if v is not None else d)
        if do_refresh and v is not None:
            refresh(v)
        return name, d, neg if neg is not None else negatives, ex if ex is not None else example

    def flip_hex(s):
        return ("0" if s[0] != "0" else "1") + s[1:]

    def setp(path_fn, key, value):
        return lambda v: path_fn(v).__setitem__(key, value)

    def swap(lst, i, j):
        lst[i], lst[j] = lst[j], lst[i]

    def drop_seed(v):
        r = mode(v, "exact")["regions"][0]
        r["seeds"].pop()

    def canonical_instead_of_pretty(v):
        raw = canon_bytes(strict_loads(base64.b64decode(v["candidate"]["bytesBase64"])))
        v["candidate"]["bytesBase64"] = base64.b64encode(raw).decode()
        v["candidate"]["sha256"] = sha(raw)

    good_cc = (HERE / doc["comparisonConfigFile"]).read_bytes()
    yield make("wrong-span", "go-function-in-host",
               lambda v: mode(v, "exact")["regions"][0]["candidateSpan"].__setitem__(1, mode(v, "exact")["regions"][0]["candidateSpan"][1] + 1))
    yield make("wrong-outcome-code", "go-renamed", setp(lambda v: mode(v, "normalized"), "outcome", {"class": "abstain", "code": "ambiguous"}))
    yield make("wrong-outcome-class", "go-no-overlap", setp(lambda v: mode(v, "exact")["outcome"], "class", "abstain"))
    yield make("exact-match-claimed-for-rename", "go-renamed", setp(lambda v: mode(v, "exact"), "outcome", {"class": "match", "code": "match"}))
    yield make("reordered-regions", "go-duplicate-regions", lambda v: swap(mode(v, "exact")["regions"], 0, 1))
    yield make("reordered-pairs", "go-reference-side-failures", lambda v: swap(v["expectedReport"]["body"]["pairs"], 0, 1))
    yield make("missing-region", "go-repeated-hash-self", lambda v: mode(v, "exact")["regions"].pop())
    yield make("missing-pair", "go-reference-side-failures", lambda v: v["expectedReport"]["body"]["pairs"].pop(3))
    yield make("extra-region", "go-identical", lambda v: mode(v, "exact")["regions"].append(copy.deepcopy(mode(v, "exact")["regions"][0])))
    yield make("seed-removed", "go-identical", drop_seed)
    yield make("ambiguity-flag-cleared", "go-duplicate-regions", setp(lambda v: mode(v, "exact")["regions"][0], "ambiguous", False))
    yield make("ambiguity-flag-set-on-span-overlap", "rv-span-overlap-disjoint-positions",
               setp(lambda v: mode(v, "exact")["regions"][0], "ambiguous", True))
    yield make("region-status-downgraded", "go-partial-copy", setp(lambda v: mode(v, "exact")["regions"][0], "status", "below-minimum-evidence"))
    yield make("distinct-count-inflated", "go-repeated-hash-self", setp(lambda v: mode(v, "exact")["regions"][0], "distinctHashes", 2))
    yield make("common-count-cleared", "rv-common-reduces-evidence", setp(lambda v: mode(v, "exact")["regions"][0], "distinctCommonHashes", 0))
    yield make("containment-numerator-wrong", "go-function-in-host",
               lambda v: mode(v, "exact")["containment"]["referenceInCandidate"].__setitem__(
                   "numerator", mode(v, "exact")["containment"]["referenceInCandidate"]["numerator"] - 1))
    yield make("fraction-reduced", "go-function-in-host",
               setp(lambda v: mode(v, "exact")["containment"], "referenceInCandidate", {"denominator": 1, "numerator": 1}))
    yield make("float-similarity", "go-function-in-host", setp(lambda v: mode(v, "exact")["similarity"], "jaccard", 0.5))
    yield make("truncated-count-wrong", "go-output-caps", setp(lambda v: mode(v, "exact"), "truncatedRegions", 0))
    yield make("region-beyond-cap", "go-output-caps",
               lambda v: mode(v, "exact")["regions"].append({"ambiguous": False, "candidateSpan": [7, 16], "distinctCommonHashes": 0,
                                                             "distinctHashes": 1, "referenceSpan": [13, 22], "seeds": [[5, 2]],
                                                             "status": "below-minimum-evidence"}))
    yield make("seed-limit-not-applied", "go-output-caps", setp(lambda v: mode(v, "normalized"), "outcome",
                                                                {"class": "no-match", "code": "below-minimum-evidence"}))
    yield make("seed-count-wrong", "go-periodic-distinct", setp(lambda v: mode(v, "exact"), "seedCount", 7))
    yield make("ownership-field-in-report", "go-identical", setp(lambda v: v["expectedReport"]["body"], "ownership", "reference-author"))
    yield make("signature-result-in-report", "go-identical", setp(lambda v: v["expectedReport"]["body"], "signatureValid", True))
    yield make("index-rank-in-report", "go-identical", setp(lambda v: v["expectedReport"]["body"]["pairs"][0], "rank", 1))
    yield make("origin-link-in-region", "go-identical", setp(lambda v: mode(v, "exact")["regions"][0], "origin", "upstream"))
    yield make("suppression-block-dropped", "go-boilerplate-suppressed",
               setp(lambda v: v["expectedReport"]["body"], "suppression", {"status": "none"}))
    yield make("suppression-digest-not-recorded", "go-boilerplate-suppressed",
               setp(lambda v: v["expectedReport"]["body"]["inputs"], "suppressionCatalogueSha256", "none"))
    yield make("suppression-artifact-count-ok-only", "go-suppression-artifact-count",
               setp(lambda v: v["expectedReport"]["body"]["suppression"], "artifactCount", 1))
    yield make("ambiguity-cleared-when-partner-truncated", "go-cap-straddles-ambiguous",
               lambda v: (mode(v, "exact")["regions"][0].__setitem__("ambiguous", False),
                          mode(v, "exact").__setitem__("outcome", {"class": "match", "code": "match"})))
    yield make("invariance-broken", "go-invariance-plus-unrelated",
               setp(lambda v: v["expectedReport"]["body"]["pairs"][0]["modes"]["normalized"], "outcome",
                    {"class": "no-match", "code": "common-only"}))
    yield make("wrong-rejection-code", "go-config-mismatch", setp(lambda v: v["expectedReport"]["body"]["rejection"], "code", "profile-mismatch"))
    yield make("wrong-rejection-side", "go-suppression-config-mismatch", setp(lambda v: v["expectedReport"]["body"]["rejection"], "side", "candidate"))
    yield make("insufficient-pair-compared", "go-insufficient-tokens",
               setp(lambda v: v["expectedReport"]["body"]["pairs"][0], "outcome", {"class": "no-match", "code": "no-shared-fingerprints"}))
    yield make("pair-precedence-swapped", "go-reference-side-failures",
               setp(lambda v: v["expectedReport"]["body"]["pairs"][2], "outcome", {"class": "abstain", "code": "insufficient-tokens"}))
    yield make("wrong-body-digest", "go-partial-copy",
               lambda v: v["expectedReport"].__setitem__("bodySha256", flip_hex(v["expectedReport"]["bodySha256"])), do_refresh=False)
    yield make("wrong-catalogue-digest", "go-partial-copy",
               lambda v: v["candidate"].__setitem__("sha256", flip_hex(v["candidate"]["sha256"])), do_refresh=False)
    yield make("catalogue-fingerprint-hash", "go-identical",
               lambda v: v["reference"]["canonical"]["artifacts"][0]["channels"]["exact"]["fingerprints"][0].__setitem__(
                   "hash", flip_hex(v["reference"]["canonical"]["artifacts"][0]["channels"]["exact"]["fingerprints"][0]["hash"])))
    yield make("catalogue-fingerprint-span", "go-identical",
               lambda v: v["reference"]["canonical"]["artifacts"][0]["channels"]["exact"]["fingerprints"][0]["span"].__setitem__(0, 1))
    yield make("catalogue-artifacts-unsorted", "go-reference-side-failures", lambda v: v["reference"]["canonical"]["artifacts"].reverse())
    yield make("catalogue-source-text", "go-identical", setp(lambda v: v["reference"]["canonical"]["artifacts"][0], "text", "func sumPositive"))
    yield make("catalogue-config-digest", "go-identical", setp(lambda v: v["reference"]["canonical"]["profile"], "configSha256", "0" * 64))
    yield make("synthetic-fingerprint-moved", "rv-gap-boundary",
               lambda v: v["candidate"]["canonical"]["artifacts"][0]["channels"]["exact"]["fingerprints"][2].__setitem__("position", 4))
    yield make("non-canonical-catalogue-accepted", "go-malformed-catalogue", canonical_instead_of_pretty, do_refresh=False)
    yield make("hand-excerpt-violated", "go-partial-copy",
               lambda v: v["handExpectations"]["pairs"][0]["modes"]["exact"].__setitem__("within", {"reference": "return total", "candidate": "return total"}),
               do_refresh=False)
    yield make("post-hoc-labelled-hand", "go-repeated-hash-self",
               lambda v: v["handExpectations"]["pairs"][0]["modes"]["normalized"].__setitem__("derivation", "hand"), do_refresh=False)
    bad_neg = copy.deepcopy(negatives)
    bad_neg[0]["bytesBase64"] = base64.b64encode(good_cc).decode()
    yield make("valid-config-listed-as-negative", None, lambda d: None, neg=bad_neg)
    ex_note = copy.deepcopy(example)
    ex_note["provenance"]["note"] = "func sumPositive(values []int) int {"
    yield make("free-text-note-in-provenance", None, lambda d: None, ex=ex_note)
    ex_name = copy.deepcopy(example)
    ex_name["provenance"]["implementation"]["name"] = "total := 0; for _, v := range values"
    yield make("source-text-in-implementation-name", None, lambda d: None, ex=ex_name)
    ex_cfg = copy.deepcopy(example)
    ex_cfg["provenance"]["comparisonConfigSha256"] = "0" * 64
    yield make("provenance-config-digest-wrong", None, lambda d: None, ex=ex_cfg)


def catalogue_rule_self_test(doc, ctx):
    """Corrupt one valid catalogue at a time, re-serialize canonically, and require the §3.6 rule layer
    (no extraction records available, as for a consumer) to return the stated result."""
    vecs = {v["id"]: v for v in doc["vectors"]}
    base = vecs["go-reference-side-failures"]["reference"]["canonical"]
    okidx = next(i for i, a in enumerate(base["artifacts"]) if a["status"] == "ok")

    def ok(c, ch="exact"):
        return c["artifacts"][okidx]["channels"][ch]

    def art(c, status):
        return next(a for a in c["artifacts"] if a["status"] == status)

    def k1(c):
        """Valid k=1 catalogue: a Go inserted ';' k-gram has the empty span [e, e) with e = byteLength."""
        c["extractionConfig"]["k"] = 1
        c["profile"]["configSha256"] = sha(ex_config_bytes(c["extractionConfig"]))
        c["artifacts"] = [{"byteLength": 1, "channels": {ch: {"fingerprints": [{"hash": "0123456789abcdef", "position": 1, "span": [1, 1]}],
                                                              "kgramCount": 2, "partialWindow": True} for ch in CHANNELS},
                           "id": "k1.go", "sha256": "1" * 64, "status": "ok", "tokenCount": 2}]

    cases = [
        ("unsorted-artifacts", lambda c: c["artifacts"].reverse(), "malformed-catalogue"),
        ("duplicate-artifact-id", lambda c: c["artifacts"][1].__setitem__("id", c["artifacts"][0]["id"]), "malformed-catalogue"),
        ("duplicate-artifact-digest", lambda c: c["artifacts"][1].__setitem__("sha256", c["artifacts"][0]["sha256"]), "malformed-catalogue"),
        ("source-text-field", lambda c: c["artifacts"][okidx].__setitem__("text", "func sumPositive"), "malformed-catalogue"),
        ("token-list-field", lambda c: c["artifacts"][okidx].__setitem__("tokens", []), "malformed-catalogue"),
        ("config-digest", lambda c: c["profile"].__setitem__("configSha256", "0" * 64), "malformed-catalogue"),
        ("profile-triple", lambda c: c["profile"].__setitem__("id", "rust2024-tokens"), "malformed-catalogue"),
        ("fingerprints-unordered", lambda c: ok(c)["fingerprints"].reverse(), "malformed-catalogue"),
        ("span-beyond-input", lambda c: ok(c)["fingerprints"][-1]["span"].__setitem__(1, c["artifacts"][okidx]["byteLength"] + 1), "malformed-catalogue"),
        ("span-inverted", lambda c: ok(c)["fingerprints"][0].__setitem__("span", [ok(c)["fingerprints"][0]["span"][1], ok(c)["fingerprints"][0]["span"][0]]), "malformed-catalogue"),
        ("position-beyond-kgrams", lambda c: ok(c)["fingerprints"][-1].__setitem__("position", ok(c)["kgramCount"]), "malformed-catalogue"),
        ("kgram-count", lambda c: ok(c).__setitem__("kgramCount", ok(c)["kgramCount"] + 1), "malformed-catalogue"),
        ("partial-window-flag", lambda c: ok(c).__setitem__("partialWindow", True), "malformed-catalogue"),
        ("window-gap", lambda c: ok(c).__setitem__("fingerprints", [ok(c)["fingerprints"][0], ok(c)["fingerprints"][-1]]), "malformed-catalogue"),
        ("first-window-empty", lambda c: ok(c).__setitem__("fingerprints", [f for f in ok(c)["fingerprints"]
                                                                            if f["position"] >= c["extractionConfig"]["window"]]),
         "malformed-catalogue"),
        ("insufficient-with-fingerprint", lambda c: art(c, "insufficient-tokens")["channels"]["exact"]["fingerprints"].append(
            {"hash": "0" * 16, "position": 0, "span": [0, 1]}), "malformed-catalogue"),
        ("error-code-not-in-profile", lambda c: art(c, "error")["error"].__setitem__("code", "reserved-token"), "malformed-catalogue"),
        ("unsupported-config-as-entry", lambda c: art(c, "error")["error"].__setitem__("code", "unsupported-config"), "malformed-catalogue"),
        ("error-with-channels", lambda c: art(c, "error").__setitem__("channels", {}), "malformed-catalogue"),
        ("unknown-version", lambda c: c.__setitem__("catalogueVersion", "traceweave-catalogue-draft-1"), "unsupported-catalogue"),
        ("unknown-profile-version", lambda c: (c["profile"].__setitem__("version", "draft-9"),
                                               c["extractionConfig"].__setitem__("profileVersion", "draft-9")), "unsupported-profile"),
        ("k1-empty-span-at-end-accepted", k1, None),
        ("input-too-large-with-length", lambda c: art(c, "error").__setitem__("error", {"code": "input-too-large", "offset": 0}),
         "malformed-catalogue"),
        ("null-digest-on-lexical-error", lambda c: art(c, "error").__setitem__("sha256", None), "malformed-catalogue"),
        ("input-too-large-nulls-accepted", lambda c: art(c, "error").update(
            {"error": {"code": "input-too-large", "offset": 0}, "byteLength": None, "sha256": None}), None),
    ]
    out = []
    need(catalogue_rejection(canon_bytes(base), ctx.cat_schema)[1] is None, "rule self-test base catalogue rejected")
    for name, fn, want in cases:
        c = copy.deepcopy(base)
        fn(c)
        try:
            raw = canon_bytes(c)
        except CheckError:
            raw = json.dumps(c, sort_keys=True, separators=(",", ":")).encode()
        got = catalogue_rejection(raw, ctx.cat_schema)[1]
        out.append((name, got == want, got))
    pretty = json.dumps(base, sort_keys=True, indent=1).encode()
    out.append(("non-canonical-bytes", catalogue_rejection(pretty, ctx.cat_schema)[1] == "malformed-catalogue", "pretty-printed"))
    dup = canon_bytes(base)[:-1] + b',"catalogueVersion":"traceweave-catalogue-draft-9"}'
    out.append(("duplicate-key-before-version-read", catalogue_rejection(dup, ctx.cat_schema)[1] == "malformed-catalogue", "duplicate key"))
    return out


def required_field_self_test(doc, ctx, example):
    """M1.3: delete each field of a valid instance alone; required fields must be rejected by the schema,
    optional fields (provenance generatedAt) accepted."""
    vecs = {v["id"]: v for v in doc["vectors"]}
    cat = vecs["go-reference-side-failures"]["reference"]["canonical"]
    rejected = [vecs[i]["expectedReport"]["body"] for i in
                ("go-config-mismatch", "go-malformed-catalogue", "go-unsupported-comparison-config", "go-suppression-missing")]
    compared = [vecs[i]["expectedReport"]["body"] for i in ("go-reference-side-failures", "go-boilerplate-suppressed", "go-output-caps")]
    targets = [("catalogue", ctx.cat_schema, None, copy.deepcopy(cat)), ("report document", ctx.rep_schema, None, copy.deepcopy(example))]
    targets += [("compared body", ctx.rep_schema, "body", copy.deepcopy(b)) for b in compared]
    targets += [("rejected body", ctx.rep_schema, "body", copy.deepcopy(b)) for b in rejected]
    optional = {("provenance", "generatedAt")}
    checked, failures = 0, []

    def walk(node, path):
        if type(node) is dict:
            for k in node:
                yield path, node, k
                yield from walk(node[k], path + [k])
        elif type(node) is list:
            for i, e in enumerate(node):
                yield from walk(e, path + [i])

    for name, schema, defname, inst in targets:
        target = {"$ref": f"#/$defs/{defname}"} if defname else schema
        need(not schema_errors(target, inst, schema), f"required-field test base {name} invalid")
        for path, parent, key in list(walk(inst, [])):
            value = parent.pop(key)
            errs = schema_errors(target, inst, schema)
            parent[key] = value
            is_optional = bool(path) and (path[-1], key) in optional
            if is_optional == bool(errs):
                failures.append(f"{name}: {'/'.join(map(str, path + [key]))}")
            checked += 1
    return checked, failures


def wrong_implementation_self_test(doc, ctx):
    """Each VARIANT re-derives every vector body with one plausible misreading. A variant is caught when at
    least one vector's body (or body digest) differs from the expected one; the vectors that catch it are listed."""
    results = []
    for name, desc in VARIANTS:
        catching = []
        for v in doc["vectors"]:
            cc_raw, raws, _ = vector_inputs(v, doc, ctx)
            exp = v["expectedReport"]
            if name == "trailing-lf":
                if sha(canon_bytes(exp["body"]) + b"\n") != exp["bodySha256"]:
                    catching.append(v["id"])
                continue
            if name in ("suppression-lenient-digest", "last-duplicate-key-wins"):
                CATALOGUE_VARIANT[0] = name
            try:
                got = compare(raws["reference"], raws["candidate"], cc_raw, ctx.cat_schema, raws.get("suppression"), variant=name)
            finally:
                CATALOGUE_VARIANT[0] = None
            if got != exp["body"]:
                catching.append(v["id"])
        results.append((name, desc, catching))
    return results


# ------------------------------------------------------------------ extraction records (contract §2a)

RECORD_VERSION = "traceweave-extraction-record-draft-1"
ENVELOPE_KEYS = ["recordVersion", "profile", "profileVersion", "configSha256", "inputSha256", "inputLength", "result"]


def rec_str(s):
    """ECMAScript JSON.stringify / RFC 8785 string escaping; everything else is written as raw UTF-8."""
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch in "\b\f\n\r\t":
            out.append({"\b": "\\b", "\f": "\\f", "\n": "\\n", "\r": "\\r", "\t": "\\t"}[ch])
        elif o < 0x20:
            out.append("\\u%04x" % o)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def rec_val(x):
    if x is None:
        return "null"
    if x is True or x is False:
        return "true" if x else "false"
    if type(x) is int:
        need(0 <= x <= MAX_INT, "record integer out of range")
        return str(x)
    if type(x) is str:
        return rec_str(x)
    raise CheckError(f"unexpected record value {x!r}")


def rec_obj(d, keys, optional=()):
    """Write an object with exactly `keys` (plus present `optional` keys) in the given order."""
    need(set(d) == set(keys) | (set(optional) & set(d)), f"record object keys {sorted(d)} != {keys}")
    return "{" + ",".join(rec_str(k) + ":" + d[k] for k in keys + [k for k in optional if k in d]) + "}"


def write_record(r):
    """Canonical record text from a parsed record, in the fixed key order of contract §2a."""
    def span(sp):
        need(type(sp) is list and len(sp) == 2, "span")
        return "[" + rec_val(sp[0]) + "," + rec_val(sp[1]) + "]"

    def kg(g):
        return rec_obj({"position": rec_val(g["position"]), "hash": rec_val(g["hash"]), "span": span(g["span"])},
                       ["position", "hash", "span"]) if set(g) == {"position", "hash", "span"} else need(False, "k-gram keys")

    def chan(c, values):
        keys = (["values"] if values else []) + ["kgrams", "windowSelections", "partialWindow", "fingerprints"]
        need(list(c) == keys or set(c) == set(keys), "channel keys")
        o = {"kgrams": "[" + ",".join(kg(g) for g in c["kgrams"]) + "]",
             "windowSelections": "[" + ",".join(rec_val(p) for p in c["windowSelections"]) + "]",
             "partialWindow": rec_val(c["partialWindow"]),
             "fingerprints": "[" + ",".join(kg(g) for g in c["fingerprints"]) + "]"}
        if values:
            o["values"] = "[" + ",".join(rec_val(v) for v in c["values"]) + "]"
        need(set(c) == set(o), "channel keys")
        return rec_obj(o, keys)

    res = r["result"]
    if res.get("status") == "error":
        err = rec_obj({"code": rec_val(res["error"]["code"]), "offset": rec_val(res["error"]["offset"])}, ["code", "offset"]) \
            if set(res["error"]) == {"code", "offset"} else need(False, "error keys")
        result = rec_obj({"status": rec_val("error"), "error": err}, ["status", "error"]) \
            if set(res) == {"status", "error"} else need(False, "error result keys")
    else:
        toks = []
        for t in res["tokens"]:
            o = {"class": rec_val(t["class"]), "text": rec_val(t["text"]), "span": span(t["span"])}
            if "inserted" in t:
                need(t["inserted"] is True, "inserted is true or absent")
                o["inserted"] = "true"
            need(set(t) == set(o), "token keys")
            toks.append(rec_obj(o, ["class", "text", "span"], optional=["inserted"]))
        chans = res["channels"]
        need(set(chans) == {"exact", "normalized"}, "channel names")
        cs = rec_obj({"exact": chan(chans["exact"], False), "normalized": chan(chans["normalized"], True)},
                     ["exact", "normalized"])
        result = rec_obj({"status": rec_val(res["status"]), "tokenCount": rec_val(res["tokenCount"]),
                          "tokens": "[" + ",".join(toks) + "]", "channels": cs},
                         ["status", "tokenCount", "tokens", "channels"])
    env = {k: rec_val(r[k]) for k in ENVELOPE_KEYS[:-1] if k in r}
    env["result"] = result
    return rec_obj(env, ENVELOPE_KEYS) + "\n"


def expected_record(cfg_raw, data, result):
    """Contract §2a and extraction Q10, from (configuration bytes, input bytes, result)."""
    code = result["error"]["code"] if result["status"] == "error" else None
    if code == "unsupported-config":
        prof, ver = None, None
    else:
        cfg = parse_extraction_config(cfg_raw)
        prof, ver = cfg["profile"], cfg["profileVersion"]
    unread = code in ("unsupported-config", "input-too-large")
    return write_record({"recordVersion": RECORD_VERSION, "profile": prof, "profileVersion": ver,
                         "configSha256": sha(cfg_raw), "inputSha256": None if unread else sha(data),
                         "inputLength": None if unread else len(data), "result": result}).encode("utf-8")


def check_record_bytes(rb, rec_schema):
    """Consumer-side record validation (no source): framing, strict JSON, schema, canonical bytes, profile codes."""
    need(rb.endswith(b"\n") and rb.count(b"\n") == 1, "a record is one line ending in exactly one LF")
    need(b"\r" not in rb, "raw CR in a record")
    try:
        r = strict_loads(rb[:-1])
    except (ValueError, UnicodeDecodeError) as exc:
        raise CheckError(f"record is not strict UTF-8 JSON ({exc})") from None
    schema_check(rec_schema, r, "record")
    need(write_record(r).encode("utf-8") == rb, "record bytes are not canonical (key order, escaping or whitespace)")
    res = r["result"]
    if res["status"] == "error" and res["error"]["code"] not in ("unsupported-config", "input-too-large"):
        prof = PROFILES.get((r["profile"], r["profileVersion"]))
        need(prof is not None and res["error"]["code"] in prof["codes"], "error code not in the profile's closed list")
    if res["status"] != "error":
        need(res["tokenCount"] == len(res["tokens"]), "tokenCount != number of tokens")
        need((res["status"] == "ok") == bool(res["channels"]["exact"]["kgrams"]), "status inconsistent with k-grams")
    return r


def catalogue_from_records(cfg_raw, items, rec_schema):
    """Contract §3.8: build catalogue bytes from (id, record bytes) pairs, or raise CheckError."""
    cfg = parse_extraction_config(cfg_raw)
    need(PROFILES.get((cfg["profile"], cfg["profileVersion"])) is not None, "unsupported profile")
    entries = []
    for aid, rb in items:
        r = check_record_bytes(rb, rec_schema)
        res = r["result"]
        need(not (res["status"] == "error" and res["error"]["code"] == "unsupported-config"),
             "an unsupported-config record cannot enter a catalogue")
        need(r["configSha256"] == sha(cfg_raw), "record configSha256 is not the digest of the catalogue configuration")
        need([r["profile"], r["profileVersion"]] == [cfg["profile"], cfg["profileVersion"]], "record profile differs")
        e = {"byteLength": r["inputLength"], "id": aid, "sha256": r["inputSha256"], "status": res["status"]}
        if res["status"] == "error":
            e["error"] = dict(res["error"])
        else:
            e["tokenCount"] = res["tokenCount"]
            e["channels"] = {ch: {"fingerprints": [{"hash": f["hash"], "position": f["position"], "span": f["span"]}
                                                   for f in res["channels"][ch]["fingerprints"]],
                                  "kgramCount": max(0, res["tokenCount"] - cfg["k"] + 1),
                                  "partialWindow": res["channels"][ch]["partialWindow"]} for ch in CHANNELS}
        entries.append(e)
    return canon_bytes({"artifacts": sorted(entries, key=lambda e: e["id"].encode()), "catalogueVersion": CATALOGUE_VERSION,
                        "extractionConfig": {k: cfg[k] for k in EX_KEYS},
                        "profile": {"configSha256": sha(cfg_raw), "id": cfg["profile"], "version": cfg["profileVersion"]}})


def check_records(rdoc, mdoc, ctx):
    need(rdoc["recordVersion"] == RECORD_VERSION, "records.json recordVersion")
    stats = {"records": 0, "nullInput": 0, "catalogues": 0, "rejections": 0}
    by_id, codes = {}, set()
    for v in rdoc["records"]:
        try:
            need(v["id"] not in by_id, "duplicate record id")
            fname, rid = v["source"].split("#", 1)
            if fname.endswith("config-negative.json"):
                neg = {n["id"]: n for n in strict_loads((HERE / fname).read_bytes())["negatives"]}[rid]
                cfg_raw = base64.b64decode(neg["configBase64"], validate=True)
                need(v["configBase64"] == neg["configBase64"], "configuration bytes differ from the negative")
                data, result = base64.b64decode(v["inputBase64"], validate=True), neg["expectedResult"]
            else:
                rec, data, _, cfg_raw, _ = ctx.sources.get(v["source"])   # recomputes hashes from tokens
                need(v["inputBase64"] == rec["inputBase64"], "input differs from the source vector")
                result = rec["result"]
            rb = v["expectedRecordText"].encode("utf-8")
            need(sha(rb) == v["expectedRecordSha256"], "expectedRecordSha256 is not the digest of the record bytes")
            r = check_record_bytes(rb, ctx.rec_schema)
            need(rb == expected_record(cfg_raw, data, result), "record differs from the one derived from its source")
            by_id[v["id"]] = rb
            codes.add(r["result"]["status"] if r["result"]["status"] != "error" else r["result"]["error"]["code"])
            stats["records"] += 1
            stats["nullInput"] += r["inputSha256"] is None
        except CheckError as exc:
            raise CheckError(f"records.json:{v.get('id')}: {exc}") from None
    need({"ok", "insufficient-tokens", "unsupported-config", "input-too-large"} <= codes
         and codes - {"ok", "insufficient-tokens", "unsupported-config", "input-too-large"},
         "record vectors must cover ok, insufficient-tokens, a lexical error, unsupported-config and input-too-large")
    mvec = {v["id"]: v for v in mdoc["vectors"]}
    for c in rdoc["cataloguesFromRecords"]:
        cb = catalogue_from_records((HERE / c["extractionConfigFile"]).read_bytes(),
                                    [(a["id"], by_id[a["record"]]) for a in c["artifacts"]], ctx.rec_schema)
        need(sha(cb) == c["expectedCatalogueSha256"], f"{c['id']}: catalogue from records digest")
        vid, side = c["sameAs"].split("#", 1)[1].split("/")
        need(sha(cb) == mvec[vid][side]["sha256"], f"{c['id']}: differs from the catalogue in {c['sameAs']}")
        stats["catalogues"] += 1
    for c in rdoc["catalogueBuildRejections"]:
        try:
            catalogue_from_records((HERE / c["extractionConfigFile"]).read_bytes(),
                                   [(a["id"], by_id[a["record"]]) for a in c["artifacts"]], ctx.rec_schema)
        except CheckError:
            stats["rejections"] += 1
            continue
        raise CheckError(f"{c['id']}: the catalogue builder accepted records it must refuse")
    return stats


def record_corruptions(rdoc):
    """Yield (name, corrupted records doc). Record digests are refreshed unless the digest itself is the target."""
    def edit(rid, fn, refresh=True):
        d = copy.deepcopy(rdoc)
        v = next(x for x in d["records"] if x["id"] == rid)
        v["expectedRecordText"] = fn(v["expectedRecordText"])
        if refresh:
            v["expectedRecordSha256"] = sha(v["expectedRecordText"].encode("utf-8"))
        return d

    def sub(old, new, count=1):
        def f(t):
            need(old in t, f"corruption setup: {old!r} not in record")
            return t.replace(old, new, count)
        return f

    def reparse(fn):
        def f(t):
            r = json.loads(t)
            fn(r)
            return json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n"
        return f

    yield "field-inputBytes", edit("rec-go-ok", sub('"inputLength":', '"inputBytes":'))
    yield "extra-contract-key", edit("rec-go-ok", sub('"profile":', '"contract":"traceweave-token-winnow-draft-1","profile":'))
    yield "missing-recordVersion", edit("rec-go-ok", sub('"recordVersion":"traceweave-extraction-record-draft-1",', ''))
    yield "envelope-order-swapped", edit("rec-go-ok", lambda t: t.replace('"profile":"go-tokens","profileVersion":"draft-1"',
                                                                           '"profileVersion":"draft-1","profile":"go-tokens"'))
    yield "result-order-swapped", edit("rec-go-ok", reparse(lambda r: r.__setitem__("result", {
        "tokenCount": r["result"]["tokenCount"], "status": r["result"]["status"], "tokens": r["result"]["tokens"],
        "channels": r["result"]["channels"]})))
    yield "jcs-sorted-keys", edit("rec-go-ok", lambda t: json.dumps(json.loads(t), sort_keys=True, separators=(",", ":"),
                                                                     ensure_ascii=False) + "\n")
    yield "no-final-lf", edit("rec-go-ok", lambda t: t[:-1])
    yield "crlf-ending", edit("rec-go-ok", lambda t: t[:-1] + "\r\n")
    yield "insignificant-whitespace", edit("rec-go-ok", sub('","profile":', '", "profile":'))
    yield "non-ascii-escaped", edit("rec-go-ok-unicode", lambda t: json.dumps(json.loads(t), separators=(",", ":"),
                                                                              ensure_ascii=True) + "\n")
    yield "uppercase-hex-escape", edit("rec-go-ok-vt", sub("\\u000b", "\\u000B", count=99))
    yield "raw-control-character", edit("rec-go-ok-vt", sub("\\u000b", "\u000b", count=99))
    yield "unnecessary-escape-in-text", edit("rec-go-ok", sub('"text":"add"', '"text":"\\u0061dd"'))
    yield "unsupported-config-input-digest", edit("rec-unsupported-config", sub('"inputSha256":null', '"inputSha256":"' + "0" * 64 + '"'))
    yield "unsupported-config-profile", edit("rec-unsupported-config", sub('"profile":null', '"profile":"go-tokens"'))
    yield "unsupported-config-offset", edit("rec-unsupported-config", sub('"offset":null', '"offset":0'))
    yield "over-limit-input-length", edit("rec-go-over-limit", sub('"inputLength":null', '"inputLength":17'))
    yield "lexical-error-null-offset", edit("rec-go-lexical-error", lambda t: re.sub(r'"offset":\d+', '"offset":null', t))
    yield "kgrams-omitted", edit("rec-go-ok", reparse(lambda r: [c.pop("kgrams") for c in r["result"]["channels"].values()]))
    yield "windowSelections-omitted", edit("rec-go-ok", reparse(lambda r: r["result"]["channels"]["exact"].pop("windowSelections")))
    yield "values-omitted", edit("rec-go-ok", reparse(lambda r: r["result"]["channels"]["normalized"].pop("values")))
    yield "inserted-false", edit("rec-go-ok", sub('"span":[0,4]}', '"span":[0,4],"inserted":false}'))
    yield "tokenCount-wrong", edit("rec-go-ok", lambda t: re.sub(r'"tokenCount":(\d+)', lambda m: f'"tokenCount":{int(m.group(1)) + 1}', t))
    yield "tokenCount-float", edit("rec-go-ok", lambda t: re.sub(r'"tokenCount":(\d+)', r'"tokenCount":\1.0', t))
    yield "duplicate-key", edit("rec-go-ok", sub('"inputLength":', '"inputLength":0,"inputLength":'))
    yield "input-digest-wrong", edit("rec-go-lexical-error", lambda t: re.sub(r'"inputSha256":"[0-9a-f]{64}"', '"inputSha256":"' + "1" * 64 + '"', t))
    yield "fingerprint-hash-changed", edit("rec-go-ok", reparse(lambda r: r["result"]["channels"]["exact"]["fingerprints"][0].__setitem__(
        "hash", "0" * 16)))
    d = copy.deepcopy(rdoc)
    d["records"][0]["expectedRecordSha256"] = "0" * 64
    yield "record-digest-wrong", d
    d = copy.deepcopy(rdoc)
    d["cataloguesFromRecords"][0]["expectedCatalogueSha256"] = "0" * 64
    yield "catalogue-from-records-digest-wrong", d
    d = copy.deepcopy(rdoc)
    d["catalogueBuildRejections"][0]["artifacts"] = d["catalogueBuildRejections"][0]["artifacts"][:1]
    yield "build-rejection-that-is-valid", d
    d = copy.deepcopy(rdoc)
    d["records"] = [r for r in d["records"] if "input-too-large" not in r["tags"]]
    d["cataloguesFromRecords"] = d["cataloguesFromRecords"][:1]
    yield "input-too-large-coverage-dropped", d


def main(argv):
    path = Path(argv[0]) if argv else HERE / "matching.json"
    ctx = Context()
    try:
        doc = strict_loads(path.read_bytes())
        negatives = strict_loads((HERE / "comparison-config-negative.json").read_bytes())
        example = strict_loads((HERE / "example-report.json").read_bytes())
        stats = check_all(doc, ctx, negatives, example)
    except CheckError as exc:
        print(f"FAIL {path.name}: {exc}")
        return 1
    print(f"PASS {path.name}: vectors={len(doc['vectors'])} catalogues-rebuilt={stats['catalogues']} "
          f"synthetic-catalogues={stats['synthetic']} fabricated-catalogues={stats['fabricated']} pairs={stats['pairs']} "
          f"regions={stats['regions']} reportable={stats['reportable']} rejected-reports={stats['rejected']} "
          f"comparison-config-negatives={len(negatives)}/{len(negatives)} rejected; example-report.json valid")
    print("  rule situations (vectors each, minimum 2): " + ", ".join(f"{k}={n}" for k, n in stats["situations"].items()))
    missed = []
    results = []
    for name, d, neg, ex in corruptions(doc, negatives, example):
        try:
            check_all(d, ctx, neg, ex)
            results.append((name, None))
        except CheckError as exc:
            results.append((name, str(exc)))
    for name, msg in results:
        print(f"  corruption {name}: {'REJECTED: ' + msg if msg else 'ACCEPTED (checker defect)'}")
    missed += [n for n, msg in results if msg is None]
    print(f"{'PASS' if not missed else 'FAIL'} corruption self-test: rejected {sum(m is not None for _, m in results)}/{len(results)}")
    rules = catalogue_rule_self_test(doc, ctx)
    for name, good, got in rules:
        print(f"  catalogue rule {name}: {'OK (' + str(got) + ')' if good else 'NOT AS STATED, got ' + str(got)}")
    rule_missed = [n for n, good, _ in rules if not good]
    print(f"{'PASS' if not rule_missed else 'FAIL'} catalogue rule self-test (no extraction records used): "
          f"{len(rules) - len(rule_missed)}/{len(rules)} as stated")
    missed += rule_missed
    checked, failures = required_field_self_test(doc, ctx, example)
    for f in failures:
        print(f"  required-field deletion not handled as stated: {f}")
    print(f"{'PASS' if not failures else 'FAIL'} required-field self-test: {checked - len(failures)}/{checked} single-field "
          f"deletions handled (required fields rejected, optional provenance field accepted)")
    missed += failures
    wrong = wrong_implementation_self_test(doc, ctx)
    for name, desc, catching in wrong:
        print(f"  wrong implementation {name} ({desc}): "
              + (f"REJECTED by {len(catching)} vector(s): {', '.join(catching[:4])}{' ...' if len(catching) > 4 else ''}"
                 if catching else "ACCEPTED (vectors do not pin this rule)"))
    wrong_missed = [n for n, _, c in wrong if not c]
    print(f"{'PASS' if not wrong_missed else 'FAIL'} wrong-implementation self-test: rejected {len(wrong) - len(wrong_missed)}/{len(wrong)}")
    missed += wrong_missed
    try:
        rdoc = strict_loads((HERE / "records.json").read_bytes())
        rs = check_records(rdoc, doc, ctx)
        print(f"PASS records.json: records={rs['records']} (null input fields: {rs['nullInput']}) "
              f"catalogues-from-records={rs['catalogues']} (equal to matching.json catalogues) build-rejections={rs['rejections']}")
    except CheckError as exc:
        print(f"FAIL records.json: {exc}")
        return 1
    rec_results = []
    for name, d in record_corruptions(rdoc):
        try:
            check_records(d, doc, ctx)
            rec_results.append((name, None))
        except (CheckError, KeyError, ValueError, TypeError) as exc:
            rec_results.append((name, str(exc)))
    for name, msg in rec_results:
        print(f"  record corruption {name}: {'REJECTED: ' + msg if msg else 'ACCEPTED (checker defect)'}")
    rec_missed = [n for n, m in rec_results if m is None]
    print(f"{'PASS' if not rec_missed else 'FAIL'} record corruption self-test: rejected "
          f"{len(rec_results) - len(rec_missed)}/{len(rec_results)}")
    missed += rec_missed
    print("Scope: recomputes extraction from recorded tokens and matching from recorded fingerprints; it does not lex. "
          "Token streams are validated by ../extraction-vectors/check_vectors.py.")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
