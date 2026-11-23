#!/usr/bin/env python3
"""Build the gate fixtures that sit beside the matching vectors (spec/catalogue-report.md §6.9, §6.10; roadmap
M2.2, M2.7, M2.9). Standard library only. Run after build_vectors.py. Writes, next to this file:

  m22-fixture-manifest.json   frozen M2.2 manifest: per UC-1 row, cases with input digests and expected byte spans
  review-packets.json         M2.7 review-packet fixtures: valid records and rejections
  candidate-generation.json   M2.9 candidate-generation fixtures: retrieval paths, records and report rejections
  licence-texts/              archived synthetic licence texts referenced by digest from the review packets

Every expected value is taken from matching.json bodies or recomputed with build_vectors.py's own functions;
check_gates.py re-derives all of it with check_matching.py's independent implementation.
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
import build_vectors as bv  # noqa: E402

MANIFEST_VERSION = "traceweave-m22-fixture-manifest-draft-1"
PACKET_VERSION = "traceweave-review-packet-draft-2"
CANDGEN_VERSION = "traceweave-candidate-generation-draft-1"
RULE = bv.ROADMAP_DEFINITION   # ROADMAP.md, Definitions (M2.6); each file adds how it applies
MANIFEST_RULE = RULE + (
    " Applied to this manifest: which vectors serve as positive and companion cases of each UC-1 example-matrix row is "
    "written by hand; each case's derivation label is the matching vector's own (matching.json derivationRule). The "
    "listed digests, outcomes and spans are copied by build_gates.py from the bodies build_vectors.py computed, and "
    "check_gates.py recomputes every body and requires every digest and span to match.")
PACKET_RULE = RULE + (
    " Applied to these fixtures: each packet's origin kind, side, region, package and commit, each rejection's "
    "corrupted field and expected verdict (schema or semantic), and the archived licence texts are written by hand from "
    "spec/catalogue-report.md section 6.9. Region keys and artifact, body and licence-text digests are copied or "
    "computed by build_gates.py from matching.json bodies, and check_gates.py recomputes the bodies and re-checks "
    "every packet.")
CANDGEN_RULE = RULE + (
    " Applied to these fixtures: the retrieval orders, the selected subset, each invalid record's defect and each "
    "rejected report field are written by hand from spec/catalogue-report.md section 6.10. Catalogues, bodies and "
    "id-set digests are computed by build_gates.py with build_vectors.py's functions, and check_gates.py rebuilds "
    "them independently.")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dump(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


def load_vectors():
    doc = json.loads((HERE / "matching.json").read_text())
    return doc, {v["id"]: v for v in doc["vectors"]}


def source_input(ref):
    """Input bytes behind a matching-vector artifact source reference."""
    fname, vid = ref.split("#", 1)
    d = json.loads((HERE / fname).read_text())
    rec = next(v for v in d["vectors"] if v["id"] == vid)
    return base64.b64decode(rec["inputBase64"])


# ------------------------------------------------------------------ M2.2 manifest

ROWS = [
    ("exact", "Exact reference/candidate", [("go-identical", "positive"), ("rust-identical", "positive")]),
    ("formatted-fragment-in-large-host", "Formatted fragment in a large host",
     [("go-formatted-fragment-in-host", "positive"), ("go-function-in-host", "positive"),
      ("go-comments-whitespace", "positive")]),
    ("rename-shadowing", "Identifier rename and shadowing",
     [("go-renamed", "positive"), ("go-shadowing", "positive"), ("rust-renamed", "positive")]),
    ("unicode-repeated-minima-tiny", "Unicode / repeated minima / tiny file",
     [("go-non-ascii-shift-2", "positive"), ("go-periodic-distinct", "companion"),
      ("go-insufficient-tokens", "companion")]),
]


def manifest_case(v, role):
    body = v["expectedReport"]["body"]
    arts = []
    for side in ("reference", "candidate"):
        for a in v[side]["artifacts"]:
            data = source_input(a["source"])
            arts.append({"side": side, "id": a["id"], "inputSha256": sha(data), "byteLength": len(data)})
    spans = []
    for p in body["pairs"]:
        if p["status"] != "compared":
            spans.append({"reference": p["reference"]["id"], "candidate": p["candidate"]["id"],
                          "pairOutcome": p["outcome"]["code"]})
            continue
        for mode, m in p["modes"].items():
            regs = m["regions"] if role == "companion" else [r for r in m["regions"] if r["status"] == "reportable"]
            spans.append({"reference": p["reference"]["id"], "candidate": p["candidate"]["id"], "mode": mode,
                          "outcome": m["outcome"]["code"],
                          "regions": [{"firstSeed": r["seeds"][0], "referenceSpan": r["referenceSpan"],
                                       "candidateSpan": r["candidateSpan"], "status": r["status"]} for r in regs]})
    return {"vectorId": v["id"], "role": role, "derivation": v["derivation"],
            "regionsListed": "all" if role == "companion" else "reportable",
            "referenceCatalogueSha256": v["reference"]["sha256"], "candidateCatalogueSha256": v["candidate"]["sha256"],
            "bodySha256": v["expectedReport"]["bodySha256"], "artifacts": arts, "expectedSpans": spans}


def build_manifest(vecs):
    rows = []
    for key, title, cases in ROWS:
        rows.append({"row": key, "exampleMatrixRow": title, "useCase": "UC-1",
                     "cases": [manifest_case(vecs[vid], role) for vid, role in cases]})
    return {"manifestVersion": MANIFEST_VERSION,
            "note": "Frozen M2.2 fixture manifest. Each UC-1 example-matrix row has at least one positive case derived by hand "
                    "(derivation 'hand'). Spans are half-open UTF-8 byte offsets [start, end). Positive cases list their REPORTABLE "
                    "regions only (regionsListed 'reportable'); companion cases list every region ('all'). Other regions are "
                    "covered by the body digest. An implementation passes M2.2 only if, for every case, its catalogues and body "
                    "reproduce these digests and every listed span (N/N).",
            "derivationRule": MANIFEST_RULE,
            "matchingVectorsFile": "matching.json", "rows": rows}


# ------------------------------------------------------------------ M2.7 review packets

LICENCES = {
    "licence-synthetic-mit-style.txt": "Synthetic licence text for a Traceweave test fixture (MIT-style placeholder).\n"
                                       "It is not a real licence and grants nothing.\n",
    "licence-synthetic-bsd-style.txt": "Synthetic licence text for a Traceweave test fixture (BSD-style placeholder).\n"
                                       "It is not a real licence and grants nothing.\n",
}


def region_key(v, ref_id, cand_id, mode, index=0):
    p = next(p for p in v["expectedReport"]["body"]["pairs"] if p["reference"]["id"] == ref_id and p["candidate"]["id"] == cand_id)
    r = p["modes"][mode]["regions"][index]
    return {"referenceId": ref_id, "candidateId": cand_id, "mode": mode, "firstSeed": list(r["seeds"][0])}, p


def packet(v, ref_id, cand_id, mode, origin):
    key, _ = region_key(v, ref_id, cand_id, mode)
    return {"reviewPacketVersion": PACKET_VERSION, "report": {"bodySha256": v["expectedReport"]["bodySha256"]},
            "region": key, "origin": origin}


def build_packets(vecs):
    lic_dir = HERE / "licence-texts"
    lic_dir.mkdir(exist_ok=True)
    lic = {}
    for name, text in LICENCES.items():
        (lic_dir / name).write_bytes(text.encode())
        lic[name] = sha(text.encode())
    fih, vun, vsu, gpc = vecs["go-function-in-host"], vecs["vendor-unsuppressed"], vecs["vendor-suppressed"], vecs["go-partial-copy"]
    _, p_fih = region_key(fih, "sum.go", "host.go", "exact")
    _, p_v = region_key(vun, "vendor.strutil.go", "vendor.strutil.go", "exact")
    _, p_gpc = region_key(gpc, "sum.go", "partial.go", "exact")
    valid = [
        {"id": "packet-own-origin", "description": "Own-origin region: the GO_SUM region found in a larger host is the "
                                                   "reference project's own code at a recorded commit.",
         "packet": packet(fih, "sum.go", "host.go", "exact", {
             "kind": "own-origin", "side": "reference", "artifactSha256": p_fih["reference"]["sha256"],
             "repositoryCommit": "1" * 40})},
        {"id": "packet-vendored-dependency", "description": "Vendored dependency region (vendor control class): the "
                                                            "vendored file matches itself; the packet names the package and "
                                                            "the digest of the archived licence text.",
         "packet": packet(vun, "vendor.strutil.go", "vendor.strutil.go", "exact", {
             "kind": "vendored-dependency", "side": "candidate", "vendoredArtifactSha256": p_v["candidate"]["sha256"],
             "package": {"name": "example.org/strutil", "version": "1.4.0"},
             "upstreamArtifactSha256": p_v["reference"]["sha256"],
             "licence": {"textSha256": lic["licence-synthetic-mit-style.txt"]}})},
        {"id": "packet-vendored-common-only", "description": "The same vendored region under the vendor catalogue, where "
                                                            "it is common-only: a common-only region is still referenceable.",
         "packet": packet(vsu, "vendor.strutil.go", "vendor.strutil.go", "exact", {
             "kind": "vendored-dependency", "side": "reference", "vendoredArtifactSha256": p_v["reference"]["sha256"],
             "package": {"name": "example.org/strutil", "version": "1.4.0"},
             "upstreamArtifactSha256": p_v["reference"]["sha256"],
             "licence": {"textSha256": lic["licence-synthetic-mit-style.txt"]}})},
        {"id": "packet-historical-copy", "description": "Historical copy: the loop was copied from an earlier version of "
                                                       "the reference at a recorded commit, under the licence then in force. "
                                                       "Whether the copy was permitted is a rights conclusion outside the record.",
         "packet": packet(gpc, "sum.go", "partial.go", "exact", {
             "kind": "historical-copy", "side": "candidate", "copyArtifactSha256": p_gpc["candidate"]["sha256"],
             "sourceArtifactSha256": p_gpc["reference"]["sha256"], "sourceCommit": "2" * 40,
             "licence": {"textSha256": lic["licence-synthetic-bsd-style.txt"]}})},
    ]
    invalid = []
    base = valid[1]["packet"]

    def paths(node, path=()):
        if isinstance(node, dict):
            for k, val in node.items():
                yield path + (k,)
                yield from paths(val, path + (k,))
    for vp in (valid[0]["packet"], valid[1]["packet"], valid[3]["packet"]):
        for pth in paths(vp):
            d = copy.deepcopy(vp)
            node = d
            for k in pth[:-1]:
                node = node[k]
            del node[pth[-1]]
            rid = "missing-" + ".".join(pth) + "-" + vp["origin"]["kind"]
            if any(x["id"] == rid for x in invalid):
                continue
            invalid.append({"id": rid, "reason": f"required field {'.'.join(pth)} removed", "expect": "schema",
                            "packet": d})
    d = copy.deepcopy(base)
    d["region"]["firstSeed"] = [999, 999]
    invalid.append({"id": "region-key-absent", "reason": "the region key is not a region of the referenced body",
                    "expect": "semantic", "packet": d})
    d = copy.deepcopy(base)
    d["region"]["mode"] = "folded"
    invalid.append({"id": "region-mode-absent", "reason": "the referenced body has no mode folded", "expect": "semantic", "packet": d})
    d = copy.deepcopy(base)
    d["report"]["bodySha256"] = "0" * 64
    invalid.append({"id": "body-unknown", "reason": "no known body has this bodySha256", "expect": "semantic", "packet": d})
    d = copy.deepcopy(valid[0]["packet"])
    d["origin"]["artifactSha256"] = "3" * 64
    invalid.append({"id": "own-origin-digest-mismatch", "reason": "own-origin artifactSha256 is not the digest of the named side",
                    "expect": "semantic", "packet": d})
    d = copy.deepcopy(valid[0]["packet"])
    d["origin"]["side"] = "candidate"
    invalid.append({"id": "own-origin-wrong-side", "reason": "the named side's digest differs from artifactSha256",
                    "expect": "semantic", "packet": d})
    # Review P1b: a vendored packet re-pointed at an unrelated own-code region of another body, digests left as they were.
    d = copy.deepcopy(base)
    gid = vecs["go-identical"]
    d["report"]["bodySha256"] = gid["expectedReport"]["bodySha256"]
    d["region"], _ = region_key(gid, "sum.go", "copy.go", "exact")
    invalid.append({"id": "vendored-repointed-p1b", "reason": "review P1b: vendoredArtifactSha256 is not the digest of the named "
                                                              "side of the new region", "expect": "semantic", "packet": d})
    d = copy.deepcopy(base)
    d["origin"]["vendoredArtifactSha256"] = "9" * 64
    invalid.append({"id": "vendored-digest-mismatch", "reason": "vendoredArtifactSha256 is not the digest of the named side",
                    "expect": "semantic", "packet": d})
    d = copy.deepcopy(valid[3]["packet"])
    d["origin"]["sourceArtifactSha256"] = "a" * 64
    invalid.append({"id": "historical-source-unbound", "reason": "review: sourceArtifactSha256 is not the digest of the region's "
                                                                 "other side", "expect": "semantic", "packet": d})
    d = copy.deepcopy(valid[3]["packet"])
    d["origin"]["copyArtifactSha256"] = d["origin"]["sourceArtifactSha256"]
    invalid.append({"id": "historical-copy-digest-mismatch", "reason": "copyArtifactSha256 is not the digest of the named side",
                    "expect": "semantic", "packet": d})
    d = copy.deepcopy(base)
    d["origin"]["licence"]["identifier"] = "GPL-3.0-only"
    invalid.append({"id": "licence-identifier-p3", "reason": "review P3: a licence identifier is not a field (it could contradict "
                                                             "the archived text); the text digest identifies the licence",
                    "expect": "schema", "packet": d})
    d = copy.deepcopy(base)
    d["origin"]["package"]["permitted"] = True
    invalid.append({"id": "permitted-inside-package-p4", "reason": "review P4: no permission flag anywhere", "expect": "schema",
                    "packet": d})
    d = copy.deepcopy(base)
    d["report"]["bodySha256"] = d["report"]["bodySha256"].upper()
    invalid.append({"id": "uppercase-digest-p6", "reason": "review P6: digests are lowercase hex", "expect": "schema", "packet": d})
    d = copy.deepcopy(valid[0]["packet"])
    reg = next(p for p in fih["expectedReport"]["body"]["pairs"] if p["candidate"]["id"] == "host.go")["modes"]["exact"]["regions"][0]
    d["region"]["firstSeed"] = list(reg["seeds"][1])
    invalid.append({"id": "non-first-seed-p2", "reason": "review P2: a region is keyed by its first seed only", "expect": "semantic",
                    "packet": d})
    d = copy.deepcopy(base)
    d["origin"]["licence"]["textSha256"] = "4" * 64
    invalid.append({"id": "licence-text-unarchived", "reason": "no archived licence text has this digest", "expect": "semantic",
                    "packet": d})
    for field, val in (("rightsVerdict", "permitted"), ("permitted", True), ("owner", "x"), ("score", 1), ("note", "free text")):
        d = copy.deepcopy(base)
        d[field] = val
        invalid.append({"id": f"forbidden-field-{field}", "reason": f"{field} is not a review-packet field (no rights verdict, "
                                                                    f"ownership, score or free text)", "expect": "schema", "packet": d})
    d = copy.deepcopy(base)
    d["origin"]["licenceCompatible"] = True
    invalid.append({"id": "forbidden-field-origin-licenceCompatible", "reason": "a licence-compatibility verdict is a rights "
                                                                               "conclusion", "expect": "schema", "packet": d})
    d = copy.deepcopy(vecs["go-function-in-host"]["expectedReport"]["body"])
    d["pairs"][0]["modes"]["exact"]["regions"][0]["origin"] = "own"
    report_reject = {"id": "origin-inside-report", "reason": "origin links are never report fields; the report schema rejects them",
                     "body": d}
    return {"packetVersion": PACKET_VERSION,
            "note": "M2.7 review-packet fixtures (spec/catalogue-report.md §6.9). Bodies are matching.json bodies; licence texts are "
                    "archived under licence-texts/ and referenced by SHA-256.",
            "derivationRule": PACKET_RULE,
            "licenceTexts": [{"file": f"licence-texts/{n}", "sha256": d_} for n, d_ in lic.items()],
            "valid": valid, "invalid": invalid, "reportRejections": [report_reject]}


# ------------------------------------------------------------------ M2.9 candidate generation

def ids_digest(ids):
    return sha(json.dumps(sorted(ids, key=lambda s: s.encode()), separators=(",", ":")).encode())


def build_candgen(vecs):
    v = vecs["text-plain-three-modes"]
    cc_raw = base64.b64decode(v["comparisonConfig"]["bytesBase64"])
    ref_raw = bv.canonical(v["reference"]["canonical"])
    corpus = [(a["id"], a["record"].split("#", 1)[1]) for a in v["candidate"]["fromRecords"]["artifacts"]]
    cfg_raw = (HERE / bv.TEXT_CFG).read_bytes()

    def run(order):
        cb = bv.catalogue_from_records(cfg_raw, [(a, bv.text_record(r)[0]) for a, r in order])
        body = bv.compare(ref_raw, cb, cc_raw)
        return cb, body
    paths = [
        ("retrieval-exhaustive", "Exhaustive: every corpus document, in corpus order.", corpus, {"method": "exhaustive"}),
        ("retrieval-index-reversed", "A toy index returns all four documents, in reverse order.", list(reversed(corpus)),
         {"method": "selected", "index": {"name": "toy-index", "version": "1"}}),
        ("retrieval-index-shuffled", "A second toy index returns all four documents in another order.",
         [corpus[2], corpus[0], corpus[3], corpus[1]], {"method": "selected", "index": {"name": "other-index", "version": "2"}}),
        ("retrieval-index-subset", "An index selects only two documents: a different candidate set, so the candidate "
                                   "catalogue digest, candidateArtifactCount and pairs change.",
         [corpus[2], corpus[0]], {"method": "selected", "index": {"name": "toy-index", "version": "1"}}),
    ]
    out = []
    for rid, desc, order, gen in paths:
        cb, body = run(order)
        gen = dict(gen)
        if gen["method"] == "selected":
            gen["selectedIdsSha256"] = ids_digest([a for a, _ in order])
        rec = {"candidateGenerationVersion": CANDGEN_VERSION, "report": {"bodySha256": sha(bv.canonical(body))},
               "candidateCatalogueSha256": sha(cb), "generation": gen}
        out.append({"id": rid, "description": desc,
                    "retrievalOrder": [{"id": a, "record": f"{bv.TEXT_RECORDS}#{r}"} for a, r in order],
                    "expectedCandidateCatalogueSha256": sha(cb), "expectedBodySha256": sha(bv.canonical(body)),
                    "expectedBody": body if rid == "retrieval-index-subset" else None,
                    "sameBodyAs": None if rid == "retrieval-index-subset" else "matching.json#text-plain-three-modes",
                    "record": rec})
    for o in out:
        if o["expectedBody"] is None:
            del o["expectedBody"]
        if o["sameBodyAs"] is None:
            del o["sameBodyAs"]
    assert all(o["expectedBodySha256"] == v["expectedReport"]["bodySha256"] for o in out[:3])
    assert out[3]["expectedBodySha256"] != v["expectedReport"]["bodySha256"]
    good = out[1]["record"]
    bad_records = []
    for rid, fn, reason in (
            ("rank-field", lambda r: r["generation"].__setitem__("rank", [1, 2, 3, 4]), "ranks are not recorded"),
            ("score-field", lambda r: r.__setitem__("scores", [90]), "scores are not recorded"),
            ("unknown-method", lambda r: r["generation"].__setitem__("method", "top-k"), "closed method list"),
            ("selected-without-digest", lambda r: r["generation"].pop("selectedIdsSha256"), "selected needs the id-set digest"),
            ("selected-digest-mismatch", lambda r: r["generation"].__setitem__("selectedIdsSha256", "5" * 64),
             "the digest is not that of the candidate catalogue's ids"),
            ("catalogue-mismatch", lambda r: r.__setitem__("candidateCatalogueSha256", "6" * 64),
             "candidateCatalogueSha256 differs from the body's inputs"),
            ("body-unknown", lambda r: r["report"].__setitem__("bodySha256", "7" * 64), "no fixture body has this digest")):
        d = copy.deepcopy(good)
        fn(d)
        bad_records.append({"id": rid, "reason": reason, "record": d})
    rejections = []
    body = v["expectedReport"]["body"]
    for rid, fn in (("report-rank-in-pair", lambda b: b["pairs"][0].__setitem__("rank", 1)),
                    ("report-score-in-region", lambda b: b["pairs"][4]["modes"]["exact"]["regions"][0].__setitem__("score", 97)),
                    ("report-index-in-body", lambda b: b.__setitem__("index", {"name": "toy-index", "version": "1"})),
                    ("report-candidate-generation-in-inputs", lambda b: b["inputs"].__setitem__("candidateGeneration", "exhaustive"))):
        d = copy.deepcopy(body)
        fn(d)
        rejections.append({"id": rid, "reason": "candidate generation, ranks, scores and indexes are never report fields",
                           "body": d})
    return {"candidateGenerationVersion": CANDGEN_VERSION,
            "note": "M2.9 fixtures (spec/catalogue-report.md §6.10): one fixed candidate catalogue reached by three retrieval "
                    "paths and orders gives a byte-identical catalogue and body; a different candidate set changes the catalogue "
                    "digest, the candidate count and the pairs. selectedIdsSha256 is the SHA-256 of the RFC 8785 array of the "
                    "selected candidate ids sorted by bytes.",
            "derivationRule": CANDGEN_RULE,
            "baseVector": "matching.json#text-plain-three-modes", "retrievals": out,
            "invalidRecords": bad_records, "reportRejections": rejections}


def main():
    doc, vecs = load_vectors()
    dump("m22-fixture-manifest.json", build_manifest(vecs))
    dump("review-packets.json", build_packets(vecs))
    dump("candidate-generation.json", build_candgen(vecs))
    for f in ("m22-fixture-manifest.json", "review-packets.json", "candidate-generation.json"):
        print(f, sha((HERE / f).read_bytes()))


if __name__ == "__main__":
    main()
