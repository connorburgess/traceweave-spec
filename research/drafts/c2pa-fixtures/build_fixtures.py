#!/usr/bin/env python3
"""Build the illustrative Traceweave <-> C2PA mapping fixtures (standard library only).

Reads committed Traceweave sources (one image-catalogue entry, one token-catalogue
entry, the example report) and writes:

  fixtures/  six positive fixtures, one per mapping case
  negative/  broken fixtures, each derived from a positive one by one mutation,
             each naming the single checker code it must produce

Nothing here is a C2PA implementation. The C2PA side is written by hand in JSON
diagnostic form and nothing is serialized to CBOR or JUMBF or signed.

Usage: python3 -I build_fixtures.py   (run from any directory)
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RULES = json.loads((HERE / "mapping-rules.json").read_text(encoding="utf-8"))
NOTICE = RULES["notice"]
FIXTURE_VERSION = "traceweave-c2pa-fixture-draft-1"
SIGNATURE = "absent: nothing was signed"
NOT_COMPUTED = "not computed: no JUMBF box was serialized"
NS = RULES["proposedNamespace"]

IMAGE_CATALOGUE = "research/experiments/image-fingerprint/results/e-img-f-2/full-1/catalogue.json"
MATCHING = "test-vectors/matching/matching.json"
REPORT = "test-vectors/matching/example-report.json"


def sha256_file(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def jcs(value):
    # Sufficient for these sources: ASCII strings, non-negative integers, no floats.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def bstr(hex_text):
    return f"h'{hex_text}'"


def hashed_uri(label):
    return {"url": f"self#jumbf=c2pa.assertions/{label}", "hash": NOT_COMPUTED}


def manifest(created, gathered, assertions, instance):
    claim = {
        "instanceID": f"xmp:iid:{instance}",
        "claim_generator_info": {"name": "traceweave-c2pa-fixture-builder", "version": "draft-1", "specVersion": "2.5.0"},
        "signature": "self#jumbf=c2pa.signature",
        "alg": "sha256",
        "created_assertions": [hashed_uri(label) for label in created],
    }
    if gathered:
        claim["gathered_assertions"] = [hashed_uri(label) for label in gathered]
    return {
        "fragment": "only the assertions this mapping needs; not a complete manifest",
        "activeManifest": f"urn:c2pa:{instance}",
        "claim": claim,
        "assertions": assertions,
        "signature": SIGNATURE,
    }


def base(fixture_id, kind, description, source_ref, traceweave, mapping):
    return {
        "fixtureVersion": FIXTURE_VERSION,
        "id": fixture_id,
        "kind": kind,
        "notice": NOTICE,
        "c2paVersion": RULES["c2paVersion"],
        "description": description,
        "sourceRef": source_ref,
        "traceweave": traceweave,
        "mapping": mapping,
    }


def decl(field, reason, carried_at=None):
    entry = {"field": field, "reason": reason}
    if carried_at is not None:
        entry["carriedAt"] = carried_at
    return entry


# ---------------------------------------------------------------- image entry

def image_source():
    catalogue = json.loads((ROOT / IMAGE_CATALOGUE).read_text(encoding="utf-8"))
    entry = next(a for a in catalogue["artifacts"] if a["id"] == "s0000000")
    artifact = {k: v for k, v in entry.items() if k not in ("seed", "pixelSha256")}  # experiment-only fields
    return {
        "catalogueVersion": catalogue["catalogueVersion"],
        "profile": catalogue["profile"],
        "matchingConfigSha256": catalogue["matchingConfigSha256"],
        "artifact": artifact,
    }


IMAGE_ALG = f"{NS}.pdq.draft-2"
META_PROFILE = f"{NS}.profile"
META_MATCHING = f"{NS}.matchingConfigSha256"
META_QUALITY = f"{NS}.pdqQuality"
SB = "/assertions/c2pa.soft-binding"


def image_c2pa(tw):
    a = tw["artifact"]
    assertions = {
        "c2pa.hash.data": {"alg": "sha256", "hash": bstr(a["sha256"]), "pad": "h''", "name": "whole file; sidecar manifest, no exclusions"},
        "c2pa.soft-binding": {
            "alg": IMAGE_ALG,
            "blocks": [{"scope": {}, "value": bstr(a["pdq"]["hash"])}],
            "name": "PDQ 256-bit hash of the decoded image (profile section 4)",
            "bindingMetadata": {
                "description": "Proposed identifier, not registered anywhere; see c2pa-mapping.md section 2",
                META_PROFILE: tw["profile"],
                META_MATCHING: tw["matchingConfigSha256"],
                META_QUALITY: a["pdq"]["quality"],
            },
        },
    }
    return manifest(["c2pa.hash.data", "c2pa.soft-binding"], [], assertions, "00000000-0000-4000-8000-000000000001")


def image_mapping():
    return {
        "unregisteredAlg": True,
        "lossy": [
            decl("/artifact/pdq/quality", "carried only in bindingMetadata, which a validator should not use (16.3.7.3.1); the quality floor and abstention it drives have no C2PA meaning", f"{SB}/bindingMetadata/{META_QUALITY}"),
            decl("/profile", "carried only in bindingMetadata; the alg string names an algorithm, not a profile triple with a configuration digest", f"{SB}/bindingMetadata/{META_PROFILE}"),
            decl("/matchingConfigSha256", "threshold and dihedral policy; C2PA leaves matching to the algorithm entry (16.3.7.5.1)", f"{SB}/bindingMetadata/{META_MATCHING}"),
            decl("/artifact/decode/width", "whole-image scope is written as an empty scope; the pixel size is not carried"),
            decl("/artifact/decode/height", "whole-image scope is written as an empty scope; the pixel size is not carried"),
        ],
        "unmapped": [
            decl("/catalogueVersion", "no C2PA field for a Traceweave record format"),
            decl("/artifact/id", "caller-chosen label; instanceID identifies the asset version, not a catalogue entry"),
            decl("/artifact/byteLength", "the data hash assertion carries no length"),
            decl("/artifact/pdq/status", "an abstaining entry produces no soft binding at all; C2PA has no abstention record"),
            decl("/artifact/iscc", "a 64-bit Image-Code body without ISCC header is not an io.iscc.v0 value: IEP-0020 requires 256-bit units including Data-Code and Instance-Code and ignores shorter units"),
            decl("/artifact/decode/status", "no C2PA field for a decoder result"),
            decl("/artifact/decode/format", "implied by the asset container; C2PA records no decoder view"),
            decl("/artifact/decode/sourceMode", "no C2PA field"),
            decl("/artifact/decode/iccPresent", "no C2PA field"),
        ],
        "opaque": [],
        "conflicting": [
            decl("/artifact/decode/exifOrientation", "the PDQ value is computed after the profile's orientation step; a soft-binding value states no orientation basis"),
        ],
    }


# ---------------------------------------------------------------- token entry

def token_source():
    data = json.loads((ROOT / MATCHING).read_text(encoding="utf-8"))
    vector = next(v for v in data["vectors"] if v["id"] == "go-function-in-host")
    catalogue = vector["reference"]["canonical"]
    return {
        "catalogueVersion": catalogue["catalogueVersion"],
        "profile": catalogue["profile"],
        "extractionConfig": catalogue["extractionConfig"],
        "artifact": catalogue["artifacts"][0],
    }


def token_c2pa(tw):
    a = tw["artifact"]
    assertions = {"c2pa.hash.data": {"alg": "sha256", "hash": bstr(a["sha256"]), "pad": "h''", "name": "whole file; sidecar manifest, no exclusions"}}
    for label, channel in (("c2pa.soft-binding", "exact"), ("c2pa.soft-binding__1", "normalized")):
        assertions[label] = {
            "alg": f"{NS}.go-tokens.{channel}.draft-1",
            "blocks": [{"scope": {}, "value": bstr(fp["hash"])} for fp in a["channels"][channel]["fingerprints"]],
            "name": f"winnowed {channel}-channel fingerprints, one block each, in position order",
            "bindingMetadata": {META_PROFILE: tw["profile"], f"{NS}.extractionConfig": tw["extractionConfig"]},
        }
    return manifest(["c2pa.hash.data", "c2pa.soft-binding", "c2pa.soft-binding__1"], [], assertions, "00000000-0000-4000-8000-000000000002")


def token_mapping():
    span = "a half-open UTF-8 byte span has no C2PA home: a textual range counts characters with an inclusive end inside a fragment identifier (16.9.2.2.5), so it is not written"
    return {
        "unregisteredAlg": True,
        "lossy": [
            decl("/profile", "carried only in bindingMetadata", f"{SB}/bindingMetadata/{META_PROFILE}"),
            decl("/extractionConfig", "carried only in bindingMetadata; k, window and hash framing have no C2PA meaning", f"{SB}/bindingMetadata/{NS}.extractionConfig"),
            decl("/artifact/channels/exact/fingerprints/*/position", "block order keeps the sequence; the k-gram position number is lost"),
            decl("/artifact/channels/normalized/fingerprints/*/position", "block order keeps the sequence; the k-gram position number is lost"),
        ],
        "unmapped": [
            decl("/catalogueVersion", "no C2PA field"),
            decl("/artifact/id", "caller-chosen label"),
            decl("/artifact/byteLength", "the data hash assertion carries no length"),
            decl("/artifact/status", "no C2PA field; error and insufficient-tokens entries produce no soft binding"),
            decl("/artifact/tokenCount", "no C2PA field"),
            decl("/artifact/channels/exact/kgramCount", "no C2PA field"),
            decl("/artifact/channels/exact/partialWindow", "no C2PA field"),
            decl("/artifact/channels/normalized/kgramCount", "no C2PA field"),
            decl("/artifact/channels/normalized/partialWindow", "no C2PA field"),
        ],
        "opaque": [],
        "conflicting": [
            decl("/artifact/channels/exact/fingerprints/*/span", span),
            decl("/artifact/channels/normalized/fingerprints/*/span", span),
        ],
    }


# ---------------------------------------------------------------- report

REPORT_LABEL = f"{NS}.comparison-report"
EXCLUSION_LENGTH = 96  # illustrative length of a structured-text manifest block line (A.9.5.1)


def report_source():
    return json.loads((ROOT / REPORT).read_text(encoding="utf-8"))


def report_c2pa(tw):
    body, prov = tw["body"], tw["provenance"]
    candidate = body["pairs"][0]["candidate"]
    assertions = {
        "c2pa.hash.data": {
            "alg": "sha256",
            "hash": bstr(candidate["sha256"]),
            "pad": "h''",
            "name": "structured-text manifest block at the start of the file, excluded (A.9.5.1)",
            "exclusions": [{"start": 0, "length": EXCLUSION_LENGTH}],
        },
        REPORT_LABEL: {
            "reportVersion": body["reportVersion"],
            "body": "'" + jcs(body) + "'",
            "bodySha256": bstr(prov["bodySha256"]),
            "comparisonConfigSha256": bstr(prov["comparisonConfigSha256"]),
            "producer": dict(prov["implementation"]),
            "specCommit": prov["specCommit"],
            "generatedAt": '0("' + prov["generatedAt"] + '")',
        },
    }
    return manifest(["c2pa.hash.data"], [REPORT_LABEL], assertions, "00000000-0000-4000-8000-000000000003")


def report_c2pa_mapping():
    return {
        "signerRanComparison": False,
        "lossy": [],
        "unmapped": [],
        "opaque": [
            decl("/body/pairs/*/modes/*/outcome", "outcome classes and codes are carried as bytes; C2PA defines no outcome vocabulary and no validator reads them"),
            decl("/body/pairs/*/modes/*/regions/*/status", "reportable, below-minimum-evidence and common-only have no C2PA meaning"),
            decl("/body/comparison/minRegionDistinctHashes", "minimum evidence has no C2PA meaning"),
            decl("/body/inputs/suppressionCatalogueSha256", "the suppression catalogue digest has no C2PA meaning"),
            decl("/body/suppression", "no C2PA meaning"),
            decl("/body/pairs/*/modes/*/containment", "raw counts, not a similarity score; must not be turned into similarityScore"),
            decl("/body/pairs/*/modes/*/similarity", "raw counts, not a similarity score; must not be turned into similarityScore"),
        ],
        "conflicting": [
            decl("/body/pairs/*/candidate/sha256", "names the compared bytes; the hard binding names the file minus the manifest block, which here has the same digest but a different byte set and offsets"),
            decl("/body/pairs/*/modes/*/regions/*/candidateSpan", "byte offsets into the compared bytes; in the file that carries the manifest block they shift by the exclusion length"),
        ],
    }


def report_intoto(tw):
    body, prov = tw["body"], tw["provenance"]
    candidate = body["pairs"][0]["candidate"]
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": candidate["id"], "digest": {"sha256": candidate["sha256"]}}],
        "predicateType": RULES["kinds"]["intoto-statement-report"]["predicateType"],
        "predicate": {
            "body": body,
            "bodySha256": prov["bodySha256"],
            "provenance": prov,
            "c2paManifest": {
                "manifestId": "urn:c2pa:00000000-0000-4000-8000-000000000003",
                "manifestStoreSha256": None,
                "relation": "bytes-minus-exclusions",
                "hardBinding": {"label": "c2pa.hash.data", "alg": "sha256", "hash": candidate["sha256"], "exclusions": [{"start": 0, "length": EXCLUSION_LENGTH}]},
            },
        },
    }


# ---------------------------------------------------------------- mark detection

def mark_source():
    query = hashlib.sha256(b"traceweave c2pa fixture: no image exists").hexdigest()
    return {
        "recordKind": "mark-detection-illustrative",
        "artifact": {"sha256": query, "role": "query"},
        "carrier": {"algorithm": "trustmark", "variant": "P", "codeCommit": "0" * 40, "weightSha256": "0" * 64},
        "region": {"unit": "pixel", "basis": "after-exif-orientation", "x": 0, "y": 0, "width": 512, "height": 512, "imageWidth": 512, "imageHeight": 512},
        "raw": {"bitCount": 100, "bitsHex": "a5c3e1f00f1e3c5a96a5c3e1f0"},
        "decoded": {"status": "ok", "ecc": "BCH_5", "payloadHex": "1f2e3d4c5b6a7980"},
        "statistic": {"name": "expected-payload-agreement", "matchedBits": 97, "comparedBits": 100, "threshold": 90, "calibrationId": "none"},
        "outcome": {"class": "match", "code": "expected-payload"},
        "searchScope": {"keys": 1, "expectedPayloads": 1},
        "confidence": None,
    }


def mark_c2pa(tw):
    r = tw["region"]
    region = {"region": [{"type": "spatial", "shape": {"type": "rectangle", "unit": "pixel", "origin": {"x": float(r["x"]), "y": float(r["y"])}, "width": float(r["width"]), "height": float(r["height"])}}]}
    assertions = {
        "c2pa.hash.data": {"alg": "sha256", "hash": bstr("0" * 64), "pad": "h''", "name": "hard binding of the marked asset written by the embedder; unknown to a detector, so zero here"},
        "c2pa.soft-binding": {"alg": "com.adobe.trustmark." + tw["carrier"]["variant"], "blocks": [{"scope": {"region": region}, "value": bstr(tw["decoded"]["payloadHex"])}]},
        "c2pa.actions.v2": {"actions": [{"action": "c2pa.watermarked.bound", "parameters": {"relatedAssertions": [hashed_uri("c2pa.soft-binding")]}}]},
    }
    return manifest(["c2pa.hash.data", "c2pa.soft-binding", "c2pa.actions.v2"], [], assertions, "00000000-0000-4000-8000-000000000004")


def mark_mapping():
    return {
        "unregisteredAlg": False,
        "direction": "the C2PA side is what the embedder's manifest would hold; a detection is a verifier result with no C2PA home",
        "lossy": [
            decl("/region/imageWidth", "a pixel rectangle does not record the image size it refers to"),
            decl("/region/imageHeight", "a pixel rectangle does not record the image size it refers to"),
        ],
        "unmapped": [
            decl("/recordKind", "no C2PA field"),
            decl("/artifact", "the queried artifact is not the asset the embedder's manifest binds"),
            decl("/carrier/algorithm", "folded into alg"),
            decl("/carrier/codeCommit", "the algorithm entry pins no code commit"),
            decl("/carrier/weightSha256", "the algorithm entry pins no weights"),
            decl("/raw", "raw bits before error correction have no C2PA field"),
            decl("/decoded/status", "no C2PA field"),
            decl("/decoded/ecc", "no C2PA field"),
            decl("/statistic", "presence statistic, threshold and calibration id are verifier results"),
            decl("/outcome", "no C2PA outcome vocabulary"),
            decl("/searchScope", "no C2PA field; needed to bound false detections"),
            decl("/confidence", "empty because nothing is calibrated; C2PA has no confidence field"),
        ],
        "opaque": [],
        "conflicting": [
            decl("/region/basis", "Traceweave pixels are after EXIF orientation; C2PA spatial ranges state no orientation basis (16.9.2.2.2)"),
            decl("/decoded/payloadHex", "the value byte layout is algorithm-specific (16.3.7.4) and was not checked against the TrustMark informational page"),
        ],
    }


# ---------------------------------------------------------------- build

def positives():
    img, tok, rep, mark = image_source(), token_source(), report_source(), mark_source()
    image_ref = {"path": IMAGE_CATALOGUE, "sha256": sha256_file(IMAGE_CATALOGUE), "entry": "s0000000"}
    token_ref = {"path": MATCHING, "sha256": sha256_file(MATCHING), "entry": "go-function-in-host reference sum.go"}
    report_ref = {"path": REPORT, "sha256": sha256_file(REPORT)}

    f1 = base("f1-image-pdq-soft-binding", "soft-binding-image", "An image-catalogue PDQ fingerprint written as a c2pa.soft-binding assertion beside a whole-file hard binding.", image_ref, img, image_mapping())
    f1["c2pa"] = image_c2pa(img)

    f2 = base("f2-report-custom-assertion", "custom-assertion-report", "A comparison report carried as a gathered custom assertion whose body is the exact canonical body bytes.", report_ref, rep, report_c2pa_mapping())
    f2["c2pa"] = report_c2pa(rep)

    f3 = base("f3-report-intoto-statement", "intoto-statement-report", "The same report as the predicate of an in-toto statement naming the candidate artifact and referencing its C2PA manifest.", report_ref, rep, {"lossy": [], "unmapped": [], "opaque": [], "conflicting": []})
    f3["intoto"] = report_intoto(rep)

    f4 = base("f4-mark-detection", "mark-detection", "An invented mark-detection record against the soft binding and watermarked.bound action an embedder would write.", {"path": None, "note": "invented values; no mark was embedded or detected"}, mark, mark_mapping())
    f4["c2pa"] = mark_c2pa(mark)

    f5 = base("f5-image-round-trip", "round-trip-image", "f1 exported and imported back by an importer that reads only mapped fields.", image_ref, img, image_mapping())
    f5["c2pa"] = image_c2pa(img)
    after = {"artifact": {"sha256": img["artifact"]["sha256"], "pdq": {"hash": img["artifact"]["pdq"]["hash"]}}}
    f5["traceweaveAfter"] = after
    f5["survives"] = ["/artifact/pdq/hash", "/artifact/sha256"]
    f5["lost"] = sorted(p for p in leaf_pointers(img) if p not in f5["survives"])

    f6 = base("f6-token-soft-binding", "soft-binding-tokens", "A Go token-catalogue entry written as two soft-binding assertions, one per channel; spans are not carried.", token_ref, tok, token_mapping())
    f6["c2pa"] = token_c2pa(tok)
    return [f1, f2, f3, f4, f5, f6]


def leaf_pointers(value, prefix=""):
    if isinstance(value, dict) and value:
        out = []
        for key in value:
            out.extend(leaf_pointers(value[key], f"{prefix}/{key}"))
        return out
    if isinstance(value, list) and value:
        out = []
        for index, item in enumerate(value):
            out.extend(leaf_pointers(item, f"{prefix}/{index}"))
        return out
    return [prefix]


def negative(source, neg_id, code, why, mutate, also=()):
    fixture = copy.deepcopy(source)
    fixture["id"] = neg_id
    mutate(fixture)
    fixture["expect"] = {"code": code, "why": why}
    if also:
        fixture["expect"]["alsoReported"] = list(also)
    return fixture


def negatives(pos):
    f1, f2, f3, f4, f5, f6 = pos
    sb = lambda f: f["c2pa"]["assertions"]["c2pa.soft-binding"]
    rep = lambda f: f["c2pa"]["assertions"][REPORT_LABEL]

    def drop_quality(f):
        del sb(f)["bindingMetadata"][META_QUALITY]
        f["mapping"]["lossy"] = [d for d in f["mapping"]["lossy"] if d["field"] != "/artifact/pdq/quality"]

    def claim_words(f):
        f["description"] = "A C2PA-compatible soft binding for the PDQ fingerprint."

    def drop_value(f):
        del sb(f)["blocks"][0]["value"]

    def text_value(f):
        sb(f)["blocks"][0]["value"] = f["traceweave"]["artifact"]["pdq"]["hash"]

    def flip_nibble(f):
        h = f["traceweave"]["artifact"]["pdq"]["hash"]
        sb(f)["blocks"][0]["value"] = bstr(("0" if h[0] != "0" else "1") + h[1:])

    def add_score(f):
        rep(f)["similarityScore"] = 36

    def soft_as_hard(f):
        f["c2pa"]["assertions"]["c2pa.hash.data"]["alg"] = "com.originalpictures.pdq.1"

    def c2pa_namespace(f):
        a = f["c2pa"]["assertions"].pop(REPORT_LABEL)
        f["c2pa"]["assertions"]["c2pa.traceweave.comparison-report"] = a
        f["c2pa"]["claim"]["gathered_assertions"] = [hashed_uri("c2pa.traceweave.comparison-report")]

    def extent(f):
        sb(f)["blocks"][0]["scope"]["extent"] = "h'00'"

    def same_bytes(f):
        f["intoto"]["predicate"]["c2paManifest"]["relation"] = "same-bytes"

    def body_edit(f):
        body = copy.deepcopy(f["traceweave"]["body"])
        body["pairs"][0]["modes"]["exact"]["seedCount"] += 1
        rep(f)["body"] = "'" + jcs(body) + "'"
        f["traceweave"]["body"] = body  # source and carried bytes agree; the digest no longer does

    def watermark_without_binding(f):
        f["c2pa"]["assertions"].pop("c2pa.soft-binding")
        f["c2pa"]["claim"]["created_assertions"] = [u for u in f["c2pa"]["claim"]["created_assertions"] if not u["url"].endswith("/c2pa.soft-binding")]
        f["c2pa"]["assertions"]["c2pa.actions.v2"]["actions"][0]["parameters"]["relatedAssertions"] = []
        f["mapping"]["conflicting"] = [d for d in f["mapping"]["conflicting"] if d["field"] != "/decoded/payloadHex"]
        # The mapped fields now have nowhere to go; keep the source to show the missing binding first.
        f["traceweave"].pop("decoded")
        f["traceweave"].pop("region")
        f["traceweave"]["carrier"].pop("variant")
        f["mapping"]["lossy"] = []

    def misdeclare(f):
        f["survives"] = sorted(f["survives"] + ["/artifact/pdq/quality"])
        f["lost"] = [p for p in f["lost"] if p != "/artifact/pdq/quality"]

    def basis_undeclared(f):
        f["mapping"]["conflicting"] = [d for d in f["mapping"]["conflicting"] if d["field"] != "/region/basis"]

    def created_placement(f):
        f["c2pa"]["claim"]["created_assertions"].append(f["c2pa"]["claim"].pop("gathered_assertions")[0])

    def unregistered(f):
        f["mapping"]["unregisteredAlg"] = False

    def signed(f):
        f["c2pa"]["signature"] = "COSE_Sign1_Tagged, ES256, x5chain present"

    def integer_rect(f):
        shape = sb(f)["blocks"][0]["scope"]["region"]["region"][0]["shape"]
        shape["width"] = 512

    return [
        negative(f1, "neg-lossy-dropped", "lossy-undeclared", "PDQ quality is dropped from the export and not declared lossy", drop_quality),
        negative(f1, "neg-compatibility-claim", "claim-wording", "the fixture text claims compatibility", claim_words),
        negative(f1, "neg-mapped-missing", "mapped-missing", "the soft-binding block has no value", drop_value),
        negative(f1, "neg-type-text-not-bstr", "type-mismatch", "the hash is written as a text string, not a byte string", text_value),
        negative(f1, "neg-value-changed", "value-mismatch", "one hex digit of the PDQ value differs", flip_nibble),
        negative(f2, "neg-similarity-score", "forbidden-field", "a similarityScore is invented for the report", add_score),
        negative(f1, "neg-soft-as-hard", "soft-as-hard", "the hard binding names a soft-binding algorithm", soft_as_hard),
        negative(f2, "neg-c2pa-namespace", "label-namespace", "the custom assertion uses the reserved c2pa namespace; the mapped fields then miss their target", c2pa_namespace, also=("mapped-missing",)),
        negative(f1, "neg-deprecated-extent", "deprecated-construct", "scope.extent is deprecated (16.3.7.1)", extent),
        negative(f3, "neg-identity-same-bytes", "identity-conflation", "the statement says same-bytes although the hard binding excludes a range", same_bytes),
        negative(f2, "neg-body-digest", "body-digest-mismatch", "the carried body no longer hashes to bodySha256", body_edit),
        negative(f4, "neg-watermark-no-binding", "soft-binding-missing", "c2pa.watermarked.bound without a soft-binding assertion", watermark_without_binding),
        negative(f5, "neg-round-trip-misdeclared", "round-trip-misdeclared", "PDQ quality is declared as surviving but is not in the imported record", misdeclare),
        negative(f4, "neg-conflict-undeclared", "conflict-undeclared", "the orientation basis conflict is not declared", basis_undeclared),
        negative(f2, "neg-report-attributed", "attribution", "the report is placed in created_assertions although the signer did not run the comparison", created_placement),
        negative(f1, "neg-alg-unregistered", "alg-unregistered-undeclared", "a proposed, unregistered algorithm id is not declared as unregistered", unregistered),
        negative(f1, "neg-signature-claimed", "signature-claimed", "the fixture claims a signature", signed),
        negative(f4, "neg-region-integer", "type-mismatch", "a region width is an integer; region-map coordinates are floats", integer_rect),
    ]


def write(directory, fixture):
    path = HERE / directory / f"{fixture['id']}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    pos = positives()
    for fixture in pos:
        write("fixtures", fixture)
    neg = negatives(pos)
    for fixture in neg:
        write("negative", fixture)
    print(f"wrote {len(pos)} fixtures and {len(neg)} negative fixtures")


if __name__ == "__main__":
    main()
