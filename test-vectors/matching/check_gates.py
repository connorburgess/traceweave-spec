#!/usr/bin/env python3
"""Check the gate fixtures beside the matching vectors (spec/catalogue-report.md §6.9, §6.10; roadmap M2.2, M2.7,
M2.9). Standard library only. It does not import build_gates.py or build_vectors.py: every body, catalogue and
digest is re-derived with check_matching.py's independent implementation.

  M2.2  m22-fixture-manifest.json is frozen (its SHA-256 is pinned below); every case's input digests, catalogue
        and body digests are recomputed, and every listed UTF-8 byte span must equal the recomputed body (N/N).
  M2.7  review-packets.json: valid packets pass schemas/review-packet.schema.json and the semantic rules (the
        region key exists in the referenced body, own-origin digest, archived licence texts); each invalid packet
        fails as stated; an origin field inside a report body fails the report schema.
  M2.9  candidate-generation.json: each retrieval path rebuilds the candidate catalogue from records in its own
        order, recompares, and must give the stated catalogue and body digests; records are checked against them;
        invalid records and report bodies with rank, score or index fields are rejected.

Then it corrupts copies of the fixtures and requires each corruption to be rejected.

Usage: python3 -I check_gates.py
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_matching as cm  # noqa: E402

# Frozen M2.2 manifest (roadmap M2.2 "frozen manifest"). Changing the manifest requires changing this digest in
# the same commit, which makes every change to the frozen fixture set visible in review.
M22_MANIFEST_SHA256 = "3fe1f8e729442239cc3230f01c9745594ea6d3a8fdf026bd99066efa3c69620f"
PACKET_SCHEMA = cm.HERE.parent.parent / "schemas" / "review-packet.schema.json"
CANDGEN_SCHEMA = cm.HERE.parent.parent / "schemas" / "candidate-generation.schema.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Ctx:
    def __init__(self):
        self.cm = cm.Context()
        self.packet_schema = cm.strict_loads(PACKET_SCHEMA.read_bytes())
        self.candgen_schema = cm.strict_loads(CANDGEN_SCHEMA.read_bytes())
        cm.audit_schema(self.packet_schema)
        cm.audit_schema(self.candgen_schema)
        self.doc = cm.strict_loads((HERE / "matching.json").read_bytes())
        self.vectors = {v["id"]: v for v in self.doc["vectors"]}
        self._bodies = {}

    def recomputed_body(self, vid):
        """The body of a matching vector, recomputed from its catalogues (not read from expectedReport)."""
        if vid not in self._bodies:
            v = self.vectors[vid]
            cm.ALLOW_TEST_PROFILES[0] = bool(v.get("testOnlyProfile"))
            try:
                cc_raw, raws, _ = cm.vector_inputs(v, self.doc, self.cm)
                self._bodies[vid] = cm.compare(raws["reference"], raws["candidate"], cc_raw, self.cm.cat_schema,
                                               raws.get("suppression"))
            finally:
                cm.ALLOW_TEST_PROFILES[0] = False
        return self._bodies[vid]

    def known_bodies(self):
        return {v["expectedReport"]["bodySha256"]: v["id"] for v in self.doc["vectors"]}


# ------------------------------------------------------------------ M2.2

def check_manifest(m, ctx, frozen=True):
    raw = (HERE / "m22-fixture-manifest.json").read_bytes()
    if frozen:
        cm.need(sha(raw) == M22_MANIFEST_SHA256, "m22-fixture-manifest.json differs from the frozen digest")
    cm.need(m["manifestVersion"] == "traceweave-m22-fixture-manifest-draft-1", "manifestVersion")
    rows = {r["row"]: r for r in m["rows"]}
    cm.need(set(rows) == {"exact", "formatted-fragment-in-large-host", "rename-shadowing", "unicode-repeated-minima-tiny"},
            "the manifest must name exactly the four UC-1 example-matrix rows")
    spans = cases = 0
    for row in m["rows"]:
        positives = 0
        for c in row["cases"]:
            v = ctx.vectors.get(c["vectorId"])
            cm.need(v is not None, f"{c['vectorId']}: not a matching vector")
            cm.need(c["derivation"] == v["derivation"], f"{c['vectorId']}: derivation label differs from the vector")
            body = ctx.recomputed_body(c["vectorId"])
            cm.need(sha(cm.canon_bytes(body)) == c["bodySha256"] == v["expectedReport"]["bodySha256"],
                    f"{c['vectorId']}: body digest")
            cm.need(body["inputs"]["referenceCatalogueSha256"] == c["referenceCatalogueSha256"]
                    and body["inputs"]["candidateCatalogueSha256"] == c["candidateCatalogueSha256"], f"{c['vectorId']}: catalogue digests")
            listed = [(a["side"], a["id"]) for a in c["artifacts"]]
            want = [(side, a["id"]) for side in ("reference", "candidate") for a in v[side]["artifacts"]]
            cm.need(listed == want, f"{c['vectorId']}: artifact list")
            for a, (side, _) in zip(c["artifacts"], want):
                src = next(x["source"] for x in v[side]["artifacts"] if x["id"] == a["id"])
                _, data, _, _, _ = ctx.cm.sources.get(src)
                cm.need([sha(data), len(data)] == [a["inputSha256"], a["byteLength"]], f"{c['vectorId']}: input digest of {a['id']}")
            pairs = {(p["reference"]["id"], p["candidate"]["id"]): p for p in body["pairs"]}
            seen = set()
            for e in c["expectedSpans"]:
                p = pairs[(e["reference"], e["candidate"])]
                if "pairOutcome" in e:
                    cm.need(p["status"] == "not-compared" and p["outcome"]["code"] == e["pairOutcome"], f"{c['vectorId']}: pair outcome")
                    seen.add((e["reference"], e["candidate"], None))
                    continue
                m_ = p["modes"][e["mode"]]
                cm.need(m_["outcome"]["code"] == e["outcome"], f"{c['vectorId']}: {e['mode']} outcome")
                cm.need(c["regionsListed"] == ("all" if c["role"] == "companion" else "reportable"),
                        f"{c['vectorId']}: regionsListed must be 'all' for companions and 'reportable' for positives")
                regs = m_["regions"] if c["regionsListed"] == "all" else [r for r in m_["regions"] if r["status"] == "reportable"]
                got = [{"firstSeed": r["seeds"][0], "referenceSpan": r["referenceSpan"], "candidateSpan": r["candidateSpan"],
                        "status": r["status"]} for r in regs]
                cm.need(got == e["regions"], f"{c['vectorId']} {e['reference']}/{e['candidate']} {e['mode']}: spans differ")
                spans += 2 * len(got)
                seen.add((e["reference"], e["candidate"], e["mode"]))
                if c["role"] == "positive" and e["outcome"] == "match" and got:
                    positives += 1 if (c["derivation"] == "hand") else 0
            cm.need(seen == {(k[0], k[1], md) for k, p in pairs.items()
                             for md in (p["modes"] if p["status"] == "compared" else [None])}, f"{c['vectorId']}: not every pair and mode listed")
            cases += 1
        cm.need(positives >= 1, f"row {row['row']}: no hand-derived positive case with a localized match")
    return cases, spans


# ------------------------------------------------------------------ M2.7

def packet_semantic(pk, ctx, licences):
    body_vid = ctx.known_bodies().get(pk["report"]["bodySha256"])
    cm.need(body_vid is not None, "no known report body has this bodySha256")
    body = ctx.recomputed_body(body_vid)
    key = pk["region"]
    p = next((p for p in body["pairs"] if [p["reference"]["id"], p["candidate"]["id"]] == [key["referenceId"], key["candidateId"]]), None)
    cm.need(p is not None and p["status"] == "compared", "the region key's pair is not a compared pair of the body")
    cm.need(key["mode"] in p["modes"], "the region key's mode is not a mode of the body")
    cm.need(any(r["seeds"][0] == key["firstSeed"] for r in p["modes"][key["mode"]]["regions"]),
            "the region key's first seed is not a listed region of the body")
    o = pk["origin"]
    side, other = o["side"], "candidate" if o["side"] == "reference" else "reference"
    bound = {"own-origin": "artifactSha256", "vendored-dependency": "vendoredArtifactSha256",
             "historical-copy": "copyArtifactSha256"}[o["kind"]]
    cm.need(o[bound] == p[side]["sha256"], f"{o['kind']} {bound} is not the digest of the region's {side} artifact")
    if o["kind"] == "historical-copy":
        cm.need(o["sourceArtifactSha256"] == p[other]["sha256"],
                "historical-copy sourceArtifactSha256 is not the digest of the region's other artifact")
    # vendored-dependency upstreamArtifactSha256 is a claim: checkable only against the upstream archive, not from body + packet.
    if "licence" in o:
        cm.need(o["licence"]["textSha256"] in licences, "the licence text digest is not an archived licence text")


def check_packets(d, ctx):
    licences = set()
    for lt in d["licenceTexts"]:
        cm.need(sha((HERE / lt["file"]).read_bytes()) == lt["sha256"], f"{lt['file']}: digest")
        licences.add(lt["sha256"])
    kinds = set()
    for v in d["valid"]:
        errs = cm.schema_errors(ctx.packet_schema, v["packet"], ctx.packet_schema)
        cm.need(not errs, f"{v['id']}: schema: {errs[:1]}")
        packet_semantic(v["packet"], ctx, licences)
        kinds.add(v["packet"]["origin"]["kind"])
    cm.need(kinds == {"own-origin", "vendored-dependency", "historical-copy"}, "valid packets must cover all three origin kinds")
    required_paths = set()
    for v in d["invalid"]:
        errs = cm.schema_errors(ctx.packet_schema, v["packet"], ctx.packet_schema)
        if v["expect"] == "schema":
            cm.need(errs, f"{v['id']}: expected a schema rejection")
            if v["id"].startswith("missing-"):
                required_paths.add(v["id"])
        else:
            cm.need(not errs, f"{v['id']}: expected to pass the schema")
            try:
                packet_semantic(v["packet"], ctx, licences)
            except cm.CheckError:
                continue
            raise cm.CheckError(f"{v['id']}: semantic rejection expected")
    # one rejection per required field of each valid origin kind
    for v in d["valid"]:
        if v["id"] == "packet-vendored-common-only":
            continue
        def paths(node, path=()):
            if isinstance(node, dict):
                for k, val in node.items():
                    yield path + (k,)
                    yield from paths(val, path + (k,))
        for pth in paths(v["packet"]):
            cm.need(f"missing-{'.'.join(pth)}-{v['packet']['origin']['kind']}" in required_paths,
                    f"no rejection fixture for required field {'.'.join(pth)} ({v['packet']['origin']['kind']})")
    for r in d["reportRejections"]:
        cm.need(cm.schema_errors({"$ref": "#/$defs/body"}, r["body"], ctx.cm.rep_schema), f"{r['id']}: report schema accepted it")
    return len(d["valid"]), len(d["invalid"]), len(d["reportRejections"])


# ------------------------------------------------------------------ M2.9

def ids_digest(ids):
    return sha(cm.canon_bytes(sorted(ids, key=lambda s: s.encode())))


def check_candgen(d, ctx):
    base = ctx.vectors[d["baseVector"].split("#", 1)[1]]
    cc = base["comparisonConfig"]
    cc_raw = base64.b64decode(cc["bytesBase64"]) if "bytesBase64" in cc else (HERE / cc["file"]).read_bytes()
    ref_raw = cm.canon_bytes(base["reference"]["canonical"])
    cfg_raw = (HERE / base["candidate"]["fromRecords"]["extractionConfigFile"]).read_bytes()
    bodies, same = {}, 0
    for r in d["retrievals"]:
        items = [(a["id"], cm.resolve_record(a["record"], ctx.cm)["expectedRecordText"].encode("utf-8")) for a in r["retrievalOrder"]]
        cb = cm.catalogue_from_records(cfg_raw, items, ctx.cm.rec_schema)
        cm.need(sha(cb) == r["expectedCandidateCatalogueSha256"], f"{r['id']}: candidate catalogue digest")
        body = cm.compare(ref_raw, cb, cc_raw, ctx.cm.cat_schema)
        bsha = sha(cm.canon_bytes(body))
        cm.need(bsha == r["expectedBodySha256"], f"{r['id']}: body digest")
        if "sameBodyAs" in r:
            cm.need(body == base["expectedReport"]["body"] and bsha == base["expectedReport"]["bodySha256"],
                    f"{r['id']}: body differs from the base vector's")
            same += 1
        else:
            cm.need(body == r["expectedBody"], f"{r['id']}: body differs from expectedBody")
            cm.need(body["inputs"]["candidateCatalogueSha256"] != base["expectedReport"]["body"]["inputs"]["candidateCatalogueSha256"]
                    and body["candidateArtifactCount"] != base["expectedReport"]["body"]["candidateArtifactCount"]
                    and body["pairs"] != base["expectedReport"]["body"]["pairs"],
                    f"{r['id']}: a different candidate set must change the catalogue digest, the count and the pairs")
        rec = r["record"]
        errs = cm.schema_errors(ctx.candgen_schema, rec, ctx.candgen_schema)
        cm.need(not errs, f"{r['id']}: record schema: {errs[:1]}")
        candgen_semantic(rec, {bsha: (body, cb)})
        cm.need(rec["generation"]["method"] != "selected" or
                ids_digest([a["id"] for a in r["retrievalOrder"]]) == rec["generation"]["selectedIdsSha256"],
                f"{r['id']}: selected ids digest is not that of the retrieved ids")
        bodies[bsha] = (body, cb)
    cm.need(same >= 2, "at least two retrieval paths must give the base vector's body")
    for b in d["invalidRecords"]:
        errs = cm.schema_errors(ctx.candgen_schema, b["record"], ctx.candgen_schema)
        if errs:
            continue
        try:
            candgen_semantic(b["record"], bodies)
        except cm.CheckError:
            continue
        raise cm.CheckError(f"{b['id']}: invalid record accepted")
    for b in d["reportRejections"]:
        cm.need(cm.schema_errors({"$ref": "#/$defs/body"}, b["body"], ctx.cm.rep_schema), f"{b['id']}: report schema accepted it")
    return len(d["retrievals"]), same, len(d["invalidRecords"]), len(d["reportRejections"])


def candgen_semantic(rec, bodies):
    cm.need(rec["report"]["bodySha256"] in bodies, "no fixture body has this bodySha256")
    body, cb = bodies[rec["report"]["bodySha256"]]
    cm.need(rec["candidateCatalogueSha256"] == sha(cb) == body["inputs"]["candidateCatalogueSha256"],
            "candidateCatalogueSha256 differs from the body's inputs")
    if rec["generation"]["method"] == "selected":
        ids = [a["id"] for a in cm.strict_loads(cb)["artifacts"]]
        cm.need(rec["generation"]["selectedIdsSha256"] == ids_digest(ids), "selectedIdsSha256 is not the candidate catalogue's id set")


# ------------------------------------------------------------------ self-test and main

def run_all(m, pk, cg, ctx, frozen=True):
    return check_manifest(m, ctx, frozen), check_packets(pk, ctx), check_candgen(cg, ctx)


def corruptions(m, pk, cg):
    def mm(fn):
        d = copy.deepcopy(m)
        fn(d)
        return d, pk, cg

    def pp(fn):
        d = copy.deepcopy(pk)
        fn(d)
        return m, d, cg

    def cc(fn):
        d = copy.deepcopy(cg)
        fn(d)
        return m, pk, d
    yield "manifest-span-shifted", mm(lambda d: d["rows"][1]["cases"][0]["expectedSpans"][0]["regions"][0]["candidateSpan"].__setitem__(0, 0))
    yield "manifest-input-digest", mm(lambda d: d["rows"][0]["cases"][0]["artifacts"][0].__setitem__("inputSha256", "0" * 64))
    yield "manifest-row-dropped", mm(lambda d: d["rows"].pop(3))
    yield "manifest-positive-relabelled-mixed-only", mm(lambda d: [c.__setitem__("derivation", "mixed") for c in d["rows"][3]["cases"]])
    yield "manifest-region-dropped", mm(lambda d: d["rows"][2]["cases"][0]["expectedSpans"][1]["regions"].pop())
    yield "packet-valid-made-forbidden", pp(lambda d: d["valid"][0]["packet"].__setitem__("rightsVerdict", "permitted"))
    yield "packet-region-moved", pp(lambda d: d["valid"][3]["packet"]["region"].__setitem__("firstSeed", [0, 1]))
    yield "manifest-regions-listed-relabelled", mm(lambda d: d["rows"][2]["cases"][0].__setitem__("regionsListed", "all"))
    yield "packet-own-origin-side-flipped", pp(lambda d: d["valid"][0]["packet"]["origin"].__setitem__("side", "candidate"))
    yield "packet-vendored-digest-moved", pp(lambda d: d["valid"][1]["packet"]["origin"].__setitem__("vendoredArtifactSha256", "6" * 64))
    yield "packet-historical-source-moved", pp(lambda d: d["valid"][3]["packet"]["origin"].__setitem__("sourceArtifactSha256", "5" * 64))
    yield "packet-licence-identifier-added", pp(lambda d: d["valid"][1]["packet"]["origin"]["licence"].__setitem__("identifier", "MIT"))
    yield "packet-missing-fixture-dropped", pp(lambda d: d["invalid"].pop(0))
    yield "packet-licence-file-digest", pp(lambda d: d["licenceTexts"][0].__setitem__("sha256", "8" * 64))
    yield "candgen-order-changes-body", cc(lambda d: d["retrievals"][1].__setitem__("expectedBodySha256", "9" * 64))
    yield "candgen-record-wrong-digest", cc(lambda d: d["retrievals"][1]["record"]["generation"].__setitem__("selectedIdsSha256", "a" * 64))
    yield "candgen-subset-claimed-same", cc(lambda d: d["retrievals"][3].__setitem__("sameBodyAs", d["baseVector"]))
    yield "candgen-rank-accepted", cc(lambda d: d["reportRejections"].__setitem__(0, {"id": "x", "body": copy.deepcopy(
        next(r for r in d["retrievals"] if "expectedBody" in r)["expectedBody"])}))


def check_python_copies():
    """extraction-py.json holds verbatim copies of frozen py-tokens draft-1 vectors (profile frozen at 58c25a9)."""
    frozen = cm.HERE.parent.parent / "research" / "drafts" / "extraction-vectors-python" / "py.json"
    mine = cm.strict_loads((HERE / "extraction-py.json").read_bytes())
    src = {v["id"]: v for v in cm.strict_loads(frozen.read_bytes())["vectors"]}
    cm.need(all(v == src[v["id"]] for v in mine["vectors"]), "extraction-py.json vectors differ from the frozen py-tokens vectors")
    cm.need(mine["configSha256"] == sha((HERE / "config-py.json").read_bytes()) == sha((frozen.parent / "config-py.json").read_bytes()),
            "config-py.json differs from the frozen py-tokens configuration")
    return len(mine["vectors"])


def main():
    ctx = Ctx()
    try:
        npy = check_python_copies()
    except cm.CheckError as exc:
        print(f"FAIL py-tokens copies: {exc}")
        return 1
    print(f"PASS extraction-py.json: {npy} vectors and config-py.json are verbatim copies of the frozen py-tokens draft-1 files")
    m = cm.strict_loads((HERE / "m22-fixture-manifest.json").read_bytes())
    pk = cm.strict_loads((HERE / "review-packets.json").read_bytes())
    cg = cm.strict_loads((HERE / "candidate-generation.json").read_bytes())
    try:
        (cases, spans), (pv, pi, pr), (rn, same, ci, cr) = run_all(m, pk, cg, ctx)
    except cm.CheckError as exc:
        print(f"FAIL gates: {exc}")
        return 1
    print(f"PASS M2.2 m22-fixture-manifest.json (frozen {M22_MANIFEST_SHA256[:16]}...): 4 rows, {cases} cases, "
          f"spans {spans}/{spans} equal to the recomputed bodies")
    print(f"PASS M2.7 review-packets.json: {pv} valid packets (3 origin kinds), {pi} rejections as stated, "
          f"{pr} report-body rejection")
    print(f"PASS M2.9 candidate-generation.json: {rn} retrieval paths ({same} give the base body byte for byte, 1 different set), "
          f"{ci} invalid records rejected, {cr} report bodies with rank/score/index rejected")
    results = []
    for name, (dm, dp, dc) in corruptions(m, pk, cg):
        try:
            run_all(dm, dp, dc, ctx, frozen=False)
            results.append((name, None))
        except (cm.CheckError, KeyError, IndexError, TypeError) as exc:
            results.append((name, str(exc) or type(exc).__name__))
    for name, msg in results:
        print(f"  corruption {name}: {'REJECTED: ' + msg if msg else 'ACCEPTED (checker defect)'}")
    missed = [n for n, msg in results if msg is None]
    print(f"{'PASS' if not missed else 'FAIL'} gate corruption self-test: rejected {len(results) - len(missed)}/{len(results)}")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
