#!/usr/bin/env python3
"""Rebuild the illustrative registration fixtures, draft-3 (fixtures/, negative/ and aux/).

Standard library only. Deterministic: Ed25519 signatures are deterministic, and every nonce,
key and placeholder trust anchor below is derived from a fixed public label. The keys are public
test-only keys. Never use any of them for anything real.

The real-format vectors in real-format/ are made once by make_real_vectors.py (local openssl and
a locally mined header file; no external service) and are read here, not regenerated.

Sources (committed elsewhere in this repository, read only):
  - the artifacts: test-vectors/matching/extraction-go.json, vectors mv-go-sum and mv-go-host;
  - the catalogues: test-vectors/matching/matching.json, vector 1;
  - the comparison report: test-vectors/matching/example-report.json;
  - the catalogue nonce: test-vectors/commitment.json. That nonce is public, and core forbids
    reusing it in production; it is reused here only so the opening can be rechecked.

Usage: python3 -I build_fixtures.py   (then run check_registration.py)
"""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_registration", HERE / "check_registration.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def label(text):
    return hashlib.sha256(text.encode()).digest()


SEED, SEED_CO, SEED_NEXT, SEED_WITNESS, SEED_THIEF = (
    label(f"traceweave registration fixture {n} test key; public; never use")
    for n in ("creator", "co-signer", "successor", "witness", "thief"))
PUB, PUB_CO, PUB_NEXT, WITNESS_PUB, PUB_THIEF = (C.ed25519_public(s) for s in (SEED, SEED_CO, SEED_NEXT, SEED_WITNESS, SEED_THIEF))
KEYID, KEYID_CO, KEYID_NEXT, KEYID_W, KEYID_THIEF = (C.keyid(p) for p in (PUB, PUB_CO, PUB_NEXT, WITNESS_PUB, PUB_THIEF))
CREATOR, CO, NEXT, THIEF = (SEED, KEYID, PUB), (SEED_CO, KEYID_CO, PUB_CO), (SEED_NEXT, KEYID_NEXT, PUB_NEXT), (SEED_THIEF, KEYID_THIEF, PUB_THIEF)
NONCE = label("traceweave registration fixture nonce; public; never use").hex()
NONCE_2 = label("traceweave registration fixture nonce 2; public; never use").hex()
NONCE_3 = label("traceweave registration fixture nonce 3; public; never use").hex()
ANCHOR = {k: label(f"PLACEHOLDER trust anchor: {v}; not a real certificate or key").hex() for k, v in {
    "tsa-a": "root certificate of TSA operator A", "tsa-b": "root certificate of TSA operator B",
    "btc": "Bitcoin main chain as pinned by the verifier's own node", "log": "log key of a Rekor v2 shard"}.items()}
ANCHOR["witness"] = C.sha(WITNESS_PUB)  # computed from the witness key, as a verifier would

ARTIFACT_SRC = "test-vectors/matching/extraction-go.json#mv-go-sum"
ARTIFACT_2_SRC = "test-vectors/matching/extraction-go.json#mv-go-host"
CATALOGUE_SRC = "test-vectors/matching/matching.json#/vectors/1/reference/canonical"
OTHER_CATALOGUE_SRC = "test-vectors/matching/matching.json#/vectors/1/candidate/canonical"
REPORT = "test-vectors/matching/example-report.json"
ARTIFACT, ARTIFACT_2 = C.load_source(ARTIFACT_SRC), C.load_source(ARTIFACT_2_SRC)
CATALOGUE, OTHER_CATALOGUE = C.load_source(CATALOGUE_SRC), C.load_source(OTHER_CATALOGUE_SRC)
CAT_NONCE = bytes.fromhex(json.loads((C.ROOT / "test-vectors/commitment.json").read_text())["nonceHex"])
REPORT_BODY = json.loads((C.ROOT / REPORT).read_text())["body"]
ZERO40 = "0" * 40
DELETE = object()
ART = [{"subjectIndex": 0, "source": ARTIFACT_SRC}]
ART2 = [{"subjectIndex": 0, "source": ARTIFACT_2_SRC}]
LIMIT = C.SENTENCE_FIRST
B3 = "fixtures/bundle-three-roots.json"
VT = "2026-11-24T00:00:00Z"


def revocation_data(anchor, name, revocations=()):
    return {"anchorSha256": ANCHOR[anchor], "source": f"PLACEHOLDER CRL of {name}; not fetched", "asOf": VT, "revocations": list(revocations)}


POLICY = {
    "quorum": 2,
    "timeRoots": [
        {"anchorSha256": ANCHOR["tsa-a"], "kind": "tsa-certificate-chain", "independenceGroup": "tsa-operator-a", "policyOids": ["2.999.1"]},
        {"anchorSha256": ANCHOR["tsa-b"], "kind": "tsa-certificate-chain", "independenceGroup": "tsa-operator-b", "policyOids": ["2.999.2"], "accuracySeconds": 1},
        {"anchorSha256": ANCHOR["btc"], "kind": "bitcoin-proof-of-work", "independenceGroup": "bitcoin"},
        {"anchorSha256": ANCHOR["log"], "kind": "log-key", "independenceGroup": "log-a"},
        {"anchorSha256": ANCHOR["witness"], "kind": "witness-service-key", "independenceGroup": "witness-a"},
    ],
    "trustedKeys": [C.sha(PUB)],
    "revocationData": [revocation_data("tsa-a", "TSA operator A"), revocation_data("tsa-b", "TSA operator B")],
    "compromiseLookbackSeconds": 2592000,
    "verificationTime": VT,
}


def policy_with(**changes):
    p = copy.deepcopy(POLICY)
    p.update(changes)
    return p


def statement(nonce=NONCE, artifact=ARTIFACT, name="sum.go", catalogue=CATALOGUE, **changes):
    st = {
        "_type": C.STATEMENT_TYPE,
        "subject": [{"name": name, "digest": {"sha256": C.sha(artifact)}}],
        "predicateType": C.PREDICATE_TYPE,
        "predicate": {
            "registrationVersion": C.REGISTRATION_VERSION,
            "contentKind": "source-code",
            "nonce": nonce,
            "possession": [{"subjectIndex": 0, "scheme": C.POSSESSION_SCHEME, "sha256": C.possession_digest(nonce, artifact)}],
            "catalogue": {"scheme": C.CATALOGUE_SCHEME, "sha256": C.catalogue_commitment(CAT_NONCE, catalogue),
                          "profile": copy.deepcopy(REPORT_BODY["profile"])},
            "implementation": {"name": "build_fixtures.py", "version": "draft-3", "commit": ZERO40},
            "specCommit": ZERO40,
            "claims": {"createdAt": "2026-11-20T09:00:00Z"},
        },
    }
    for path, value in changes.items():
        target = st
        parts = path.split(".")
        for p in parts[:-1]:
            target = target[int(p)] if isinstance(target, list) else target[p]
        if value is DELETE:
            del target[parts[-1]]
        else:
            target[int(parts[-1]) if isinstance(target, list) else parts[-1]] = value
    return st


def b64(data, url_safe=False):
    return (base64.urlsafe_b64encode if url_safe else base64.b64encode)(data).decode()


def envelope(st, signers=(CREATOR,), payload_override=None, url_safe=False):
    payload = C.jcs(st)
    sigs = [C.ed25519_sign(seed, C.pae(C.PAYLOAD_TYPE, payload)) for seed, _, _ in signers]
    body = payload_override if payload_override is not None else payload
    return ({"payloadType": C.PAYLOAD_TYPE, "payload": b64(body, url_safe),
             "signatures": [{"keyid": kid, "sig": b64(s, url_safe)} for (_, kid, _), s in zip(signers, sigs)]}, sigs)


def evidence(kind, sig, anchor, body, index=0, extra_label=""):
    root_kind, body_key = C.EVIDENCE_TYPES[kind]
    ev = {"evidenceVersion": C.EVIDENCE_VERSION, "type": kind, "placeholder": True, "notice": C.PLACEHOLDER_NOTICE,
          "target": {"kind": "dsse-signature", "signatureIndex": index, "sha256": C.sha(sig)},
          "root": {"kind": root_kind, "anchorSha256": ANCHOR[anchor]},
          "token": f"PLACEHOLDER-NOT-A-{kind.upper()}-OBJECT-{C.sha(sig)[:12]}-{anchor}{extra_label}"}
    if body is not None:
        ev[body_key] = body
    return ev


def tsa(sig, which="a", gen="2026-11-23T10:00:00Z", index=0, cert=("2026-01-01T00:00:00Z", "2031-01-01T00:00:00Z"), **extra):
    n = {"a": "5a17c0de00000001", "b": "5a17c0de00000002"}[which]
    body = {"genTime": gen, "policyOid": "2.999.1" if which == "a" else "2.999.2", "nonce": n, "requestNonce": n,
            "signerCertificate": {"notBefore": cert[0], "notAfter": cert[1]}}
    if which == "a":
        body["accuracySeconds"] = 1
    body.update(extra)
    return evidence("rfc3161", sig, f"tsa-{which}", body, index, extra_label=f"-{gen}")


def ots(sig, block="2026-11-23T11:12:00Z", index=0):
    return evidence("opentimestamps", sig, "btc", {"status": "complete", "blockTime": block}, index, extra_label=f"-{block}")


def rekor(sig):
    return evidence("rekor-v2", sig, "log", {"logIndex": 0})


def bundle_of(env, evs, keys=(CREATOR,)):
    return {"bundleVersion": C.BUNDLE_VERSION, "envelope": env,
            "verificationMaterial": {"publicKeys": [{"keyid": k, "alg": "ed25519", "publicKeyHex": p.hex()} for _, k, p in keys]},
            "timeEvidence": evs}


def three_roots(st=None):
    env, sigs = envelope(st or statement())
    s = sigs[0]
    return bundle_of(env, [tsa(s, "a"), tsa(s, "b", "2026-11-23T10:00:05Z"), ots(s), rekor(s)]), s


def fixture(kind, description, obj, expect=None, also=None, **meta):
    m = {"kind": kind, "description": description, "notice": C.FIXTURE_NOTICE}
    m.update(meta)
    if expect:
        m["expect"] = {"code": expect}
        if also:
            m["expect"]["alsoReported"] = also
    return {"fixture": m, "object": obj}


def write(folder, name, doc):
    (HERE / folder).mkdir(exist_ok=True)
    (HERE / folder / f"{name}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def result_for(bundle_rel, policy=POLICY, artifacts=ART, events=(), simulated=True):
    obj = json.loads((HERE / bundle_rel).read_text())["object"]
    arts = {a["subjectIndex"]: C.load_source(a["source"]) for a in artifacts}
    ctx = C.check_bundle(obj, arts, set())
    return C.expected_result(ctx, arts, copy.deepcopy(policy), simulated, C.sha((HERE / bundle_rel).read_bytes()), list(events), set())


def key_event(event, target=CREATOR, signer=CREATOR, gen="2026-11-25T00:00:00Z", block="2026-11-25T01:00:00Z", **pred):
    st = {"_type": C.STATEMENT_TYPE, "subject": [{"name": "key", "digest": {"sha256": C.sha(target[2])}}],
          "predicateType": C.KEY_EVENT_TYPE,
          "predicate": {"eventVersion": C.KEY_EVENT_VERSION, "keyid": target[1], "event": event, **pred}}
    env, sigs = envelope(st, signers=(signer,))
    return bundle_of(env, [tsa(sigs[0], "a", gen), ots(sigs[0], block)], keys=(signer,)), st


def witness_bundle(presented, which="a", gen="2026-11-23T10:00:03Z", **pred_changes):
    pred = {"witnessVersion": C.WITNESS_VERSION, "presentedKind": "dsse-signature-sha256", "receivedAt": "2026-11-23T10:00:02Z",
            "caller": {"scheme": "openIdConnect", "issuer": "https://issuer.example.invalid", "subject": "placeholder-subject-0001"},
            "requestMessageId": "0f6c2a8e-illustrative-0001", "notShown": C.NOT_SHOWN}
    pred.update(pred_changes)
    st = {"_type": C.STATEMENT_TYPE, "subject": [{"name": "presented-digest", "digest": {"sha256": presented}}],
          "predicateType": C.WITNESS_TYPE, "predicate": pred}
    env, wsigs = envelope(st, signers=((SEED_WITNESS, KEYID_W, WITNESS_PUB),))
    return bundle_of(env, [tsa(wsigs[0], which, gen)], keys=((SEED_WITNESS, KEYID_W, WITNESS_PUB),))


def witness_evidence(sig, which="a"):
    ev = evidence("traceweave-witness", sig, "witness", {"bundle": witness_bundle(C.sha(sig), which)}, extra_label=f"-{which}")
    return ev


def render(result, name="sum.go", artifact=ARTIFACT, context=None, witness=None):
    o = result["outcomes"]
    h = C.sha(artifact)
    lines = [f"Registration of {name} (SHA-256 {h[:8]}…{h[-4:]}).",
             {"match": "Content digest: matches the file you supplied.",
              "mismatch": "Content digest: does not match the file you supplied.",
              "not-supplied": "Content digest: not checked, because no file was supplied."}[o["subjects"][0]["outcome"]]]
    trust_words = {"trusted": "trusted", "untrusted": "not trusted", "disputed": "disputed by a key event", "not-evaluated": "not evaluated"}
    for sig, trust, t in zip(o["signatures"], o["signerTrust"], o["time"]):
        lines.append(f"Signature by key {sig['keyid']}: {sig['outcome'].replace('unknown-key', 'unknown key')}; signer {trust_words[trust['outcome']]} under your policy.")
        if t["notAfterQuorum"]:
            lines.append(f"This record shows that the content existed, and that key {t['keyid']} signed a statement naming it, no later than {t['notAfterQuorum']}.")
        elif t["notAfterAnyRoot"]:
            lines.append(f"This record shows that the content existed, and that key {t['keyid']} signed a statement naming it, no later than {t['notAfterAnyRoot']} (according to one time source only).")
        else:
            lines.append(f"No proved time for key {t['keyid']}.")
        if t["notAfterAnyRoot"]:
            lines.append(f"Time sources for key {t['keyid']}: {t['distinctRoots']} independent, {t['quorum']} required; the earliest single source says {t['notAfterAnyRoot']}.")
    if witness:
        lines.append(witness)
    if o["claimedCreatedAt"]["value"]:
        lines.append(f"Creation time claimed by the registrant, not proved: {o['claimedCreatedAt']['value']}.")
    return lines + C.REQUIRED_SENTENCES + ([C.AGENT_SENTENCE] if context == "agent" else [])


# ------------------------------------------------------------------ real-format vectors (made by make_real_vectors.py)

REAL = HERE / "real-format"


def real_bytes(name):
    return (REAL / name).read_bytes()


def real_policy():
    root = C.RF.Cert(real_bytes("test-root-ca.der"))
    genesis = real_bytes("headers.bin")[:80]
    return {
        "quorum": 2,
        "timeRoots": [
            {"anchorSha256": root.sha256(), "kind": "tsa-certificate-chain", "independenceGroup": "test-tsa",
             "policyOids": ["2.999.1"], "rootCertificate": "real-format/test-root-ca.der"},
            {"anchorSha256": C.sha(genesis), "kind": "bitcoin-proof-of-work", "independenceGroup": "synthetic-chain",
             "headerFile": "real-format/headers.bin", "minConfirmations": 6},
        ],
        "trustedKeys": [C.sha(PUB)],
        "revocationData": [{"anchorSha256": root.sha256(), "source": "real-format test CA: no CRL issued", "asOf": "2026-11-24T12:00:00Z", "revocations": []}],
        "compromiseLookbackSeconds": 2592000,
        "verificationTime": "2026-11-24T12:00:00Z",
    }


def real_evidence(kind, sig, token, request=None):
    p = real_policy()
    anchor = p["timeRoots"][0 if kind == "rfc3161" else 1]["anchorSha256"]
    ev = {"evidenceVersion": C.EVIDENCE_VERSION, "type": kind, "placeholder": False, "notice": C.REAL_NOTICE,
          "target": {"kind": "dsse-signature", "signatureIndex": 0, "sha256": C.sha(sig)},
          "root": {"kind": C.EVIDENCE_TYPES[kind][0], "anchorSha256": anchor}, "token": b64(token)}
    if request is not None:
        ev["request"] = b64(request)
    return ev


def build_real():
    if not (REAL / "MANIFEST.json").exists():
        raise SystemExit("real-format/ is missing: run make_real_vectors.py first")
    env, sigs = envelope(statement())
    sig = sigs[0]
    good = [real_evidence("rfc3161", sig, real_bytes("rfc3161-response.der"), real_bytes("rfc3161-request.der")),
            real_evidence("opentimestamps", sig, real_bytes("opentimestamps-proof.ots"))]
    write("fixtures", "bundle-real", fixture("bundle", "Real-format evidence: a token from a local test-only TSA and an OpenTimestamps proof against a locally mined header file.",
                                             bundle_of(env, good), artifacts=ART))
    BR = "fixtures/bundle-real.json"
    write("fixtures", "evidence-real-rfc3161", fixture("evidence", "Real RFC 3161 TimeStampResp from the local test TSA, with its request.", good[0], bundle=BR))
    write("fixtures", "evidence-real-opentimestamps", fixture("evidence", "Real-format OpenTimestamps proof, attested at height 4 of the synthetic chain.", good[1], bundle=BR))
    write("fixtures", "evidence-real-opentimestamps-pending", fixture("evidence", "Real-format pending OpenTimestamps proof (calendar attestation only).",
                                                                      real_evidence("opentimestamps", sig, real_bytes("opentimestamps-pending.ots")), bundle=BR))
    rp = real_policy()
    write("fixtures", "verification-result-real", fixture("verification-result", "Not simulated: both real-format evidences verify; anchors computed from the pinned root certificate and header file.",
                                                          result_for(BR, rp, simulated=False), bundle=BR, artifacts=ART))
    neg = lambda name, doc: write("negative", f"neg-{name}", doc)
    for name, file, code, desc in [
        ("tsa-imprint-mismatch", "rfc3161-response-other-digest.der", "tsa-imprint-mismatch", "A real token over another digest (the statement bytes)."),
        ("tsa-signature-invalid", "rfc3161-response-tampered.der", "tsa-signature-invalid", "genTime edited after signing: messageDigest no longer matches."),
        ("tsa-eku-invalid", "rfc3161-response-noncritical-eku.der", "tsa-eku-invalid", "Re-signed by a TSA certificate whose timeStamping EKU is not critical."),
        ("tsa-signing-cert-mismatch", "rfc3161-response-wrong-ess.der", "tsa-signing-cert-mismatch", "ESSCertIDv2 names another certificate (RFC 5816)."),
    ]:
        req = "rfc3161-request-other-digest.der" if name == "tsa-imprint-mismatch" else "rfc3161-request.der"
        neg(name, fixture("evidence", desc, real_evidence("rfc3161", sig, real_bytes(file), real_bytes(req)), code, bundle=BR))
    neg("real-ots-wrong-target", fixture("evidence", "A real-format proof for another digest.",
                                         real_evidence("opentimestamps", sig, real_bytes("opentimestamps-other-digest.ots")), "evidence-wrong-target", bundle=BR))
    r = result_for(BR, rp, simulated=False)
    bad_policy = copy.deepcopy(rp)
    bad_policy["timeRoots"][1]["headerFile"] = "real-format/headers-other.bin"
    r2 = copy.deepcopy(r)
    r2["policy"] = bad_policy
    neg("real-ots-other-chain", fixture("verification-result", "Header file that does not contain the attested block; the proof is reported valid anyway.", r2,
                                        "quorum-miscount", bundle=BR, artifacts=ART))
    bad_policy = copy.deepcopy(rp)
    bad_policy["timeRoots"][0]["rootCertificate"] = "real-format/headers.bin"
    r3 = copy.deepcopy(r)
    r3["policy"] = bad_policy
    neg("real-root-not-pinned", fixture("verification-result", "Pinned root file does not hash to the anchor; the token is reported valid anyway.", r3,
                                        "quorum-miscount", bundle=BR, artifacts=ART))


def build():
    for folder in ("fixtures", "negative", "aux"):
        for old in (HERE / folder).glob("*.json"):
            old.unlink()
    st = statement()
    three, sig = three_roots(st)
    write("fixtures", "statement", fixture("statement", "The registration statement (in-toto Statement v1) before signing.", st, artifacts=ART))
    write("fixtures", "bundle-three-roots", fixture(
        "bundle", "Signed statement with placeholders from three independent roots (TSA A, TSA B, Bitcoin) and a Rekor v2 entry (no time).", three, artifacts=ART))
    write("fixtures", "evidence-rfc3161", fixture("evidence", "RFC 3161 placeholder over the raw bytes of signature 0.", three["timeEvidence"][0], bundle=B3))
    write("fixtures", "evidence-rfc3161-no-accuracy", fixture("evidence", "RFC 3161 placeholder without accuracy; the verifier's policy supplies it.", three["timeEvidence"][1], bundle=B3))
    write("fixtures", "evidence-opentimestamps-complete", fixture("evidence", "Upgraded OpenTimestamps proof placeholder.", three["timeEvidence"][2], bundle=B3))
    write("fixtures", "evidence-opentimestamps-pending", fixture("evidence", "OpenTimestamps proof before upgrade: no time.",
                                                                  evidence("opentimestamps", sig, "btc", {"status": "pending"}), bundle=B3))
    write("fixtures", "evidence-rekor-v2", fixture("evidence", "Rekor v2 inclusion placeholder; no time of its own.", three["timeEvidence"][3], bundle=B3))
    write("fixtures", "evidence-witness", fixture("evidence", "A hosted witness's statement as evidence; its bound comes from its own TSA token.", witness_evidence(sig, "b"), bundle=B3))

    result = result_for(B3)
    rmeta = {"bundle": B3, "artifacts": ART}
    vr = lambda name, desc, res, **meta: write("fixtures", f"verification-result{name}", fixture("verification-result", desc, res, **(meta or rmeta)))
    vr("", "Expected outcomes for bundle-three-roots and sum.go; placeholders assumed valid (simulated).", result)
    no_acc = copy.deepcopy(POLICY)
    del no_acc["timeRoots"][1]["accuracySeconds"]
    vr("-no-accuracy", "TSA B's token has no accuracy and the policy gives none: `unsupported`.", result_for(B3, no_acc))
    for name, reason, when, desc in [
        ("-revoked", None, "2027-03-01T00:00:00Z", "TSA A revoked without a reasonCode: all its tokens are invalid (RFC 3161 section 4 item 1)."),
        ("-revoked-key-compromise", "keyCompromise", "2027-03-01T00:00:00Z", "TSA A revoked for key compromise: all its tokens are invalid (section 4 item 2)."),
        ("-revoked-retaining", "superseded", "2027-03-01T00:00:00Z", "TSA A revoked as superseded after genTime: its earlier token stays valid."),
    ]:
        p = copy.deepcopy(POLICY)
        p["revocationData"][0]["revocations"] = [{"revokedAt": when, "reasonCode": reason}]
        vr(name, desc, result_for(B3, p))
    p = copy.deepcopy(POLICY)
    p["timeRoots"][0]["policyOids"] = ["2.999.9"]
    vr("-wrong-policy", "TSA A's token policy OID is not one the verifier accepts: `wrong-policy`.", result_for(B3, p))
    p = copy.deepcopy(POLICY)
    p["revocationData"] = p["revocationData"][1:]
    vr("-no-revocation-data", "No revocation data for TSA A: its token cannot be judged offline (S3).", result_for(B3, p))
    vr("-expired", "Verified in 2032, after both TSA certificates expired, with no renewal: two tokens `expired-unrenewed`.",
       result_for(B3, policy_with(verificationTime="2032-01-01T00:00:00Z")))
    renewed = copy.deepcopy(three)
    tok_a = renewed["timeEvidence"][0]["token"].encode()
    ren = tsa(sig, "b", "2030-06-01T00:00:00Z", cert=("2029-01-01T00:00:00Z", "2036-01-01T00:00:00Z"))
    ren["target"] = {"kind": "evidence-token", "evidenceIndex": 0, "sha256": C.sha(tok_a)}
    ren["token"] += "-renewal"
    renewed["timeEvidence"].append(ren)
    write("fixtures", "bundle-renewed", fixture("bundle", "bundle-three-roots plus a renewal token (TSA B, 2030) over TSA A's token bytes.", renewed, artifacts=ART))
    write("fixtures", "evidence-renewal", fixture("evidence", "Renewal: an RFC 3161 placeholder whose target is the token bytes of evidence 0.", ren, bundle="fixtures/bundle-renewed.json"))
    vr("-renewed", "Verified in 2032: TSA A's token survives its certificate's expiry through the 2030 renewal; TSA B's does not.",
       result_for("fixtures/bundle-renewed.json", policy_with(verificationTime="2032-01-01T00:00:00Z")), bundle="fixtures/bundle-renewed.json", artifacts=ART)
    stripped = copy.deepcopy(three)
    del stripped["timeEvidence"][1]
    write("aux", "bundle-stripped", fixture("bundle", "bundle-three-roots with TSA B's evidence removed in transit.", stripped))
    vr("-stripped", "Removing an evidence can only make the bounds later (N3).", result_for("aux/bundle-stripped.json"), bundle="aux/bundle-stripped.json", artifacts=ART)

    env_co, sigs_co = envelope(st, signers=(CREATOR, CO))
    cos = bundle_of(env_co, [tsa(sigs_co[0], "a"), ots(sigs_co[0])], keys=(CREATOR, CO))
    write("fixtures", "bundle-cosigned", fixture("bundle", "The same statement later co-signed by a second key; evidence covers signature 0 only.", cos, artifacts=ART))
    res_co = result_for("fixtures/bundle-cosigned.json")
    vr("-cosigned", "Per-signature bounds: the co-signer gets none.", res_co, bundle="fixtures/bundle-cosigned.json", artifacts=ART)
    write("fixtures", "rendering-cosigned", fixture("rendering", "Text for the co-signed bundle: a bound sentence only for the key that has one.",
                                                    {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result-cosigned.json", "lines": render(res_co)}))
    st_claim = statement(**{"predicate.claims.createdAt": "2026-11-23T10:00:03Z"})
    env_cl, sigs_cl = envelope(st_claim, signers=(CREATOR, CO))
    write("aux", "bundle-claim", fixture("bundle", "Claimed 10:00:03; the trusted signature's earliest bound is 10:00:06, the untrusted co-signer's 10:00:01.",
                                         bundle_of(env_cl, [tsa(sigs_cl[0], "b", "2026-11-23T10:00:05Z"), tsa(sigs_cl[1], "a", index=1)], keys=(CREATOR, CO))))
    res_claim = result_for("aux/bundle-claim.json")
    vr("-claim-trusted-only", "The claimed time is compared only with trusted signatures (S11): `claimed-only`.", res_claim, bundle="aux/bundle-claim.json", artifacts=ART)

    # key events
    rot, _ = key_event("rotated", gen="2026-12-01T00:00:00Z", block="2026-12-01T01:00:00Z", successorPublicKeyHex=PUB_NEXT.hex())
    write("fixtures", "key-event-rotation", fixture("key-event", "The key names its successor; time-stamped like a registration.", rot))
    recent, _ = key_event("compromised", compromisedNotBefore="2026-11-23T00:00:00Z")
    write("fixtures", "key-event-compromise-recent", fixture("key-event", "Compromise reported two days after the claimed start.", recent))
    early, _ = key_event("compromised", gen="2027-01-15T00:00:00Z", block="2027-01-15T01:00:00Z", compromisedNotBefore="2026-01-01T00:00:00Z")
    write("fixtures", "key-event-compromise-early", fixture("key-event", "Compromise claimed from a date long before it was reported.", early))
    other, _ = key_event("compromised", signer=CO, compromisedNotBefore="2026-01-01T00:00:00Z")
    write("aux", "key-event-by-other-key", fixture("key-event", "A compromise event for the creator key, signed by an unrelated key.", other))
    retire_next, _ = key_event("retired", signer=NEXT, gen="2026-12-03T00:00:00Z", block="2026-12-03T01:00:00Z")
    write("aux", "key-event-retired-by-successor", fixture("key-event", "The successor retires the old key after the rotation.", retire_next))
    hijack, _ = key_event("rotated", gen="2026-11-26T00:00:00Z", block="2026-11-26T01:00:00Z", successorPublicKeyHex=PUB_THIEF.hex())
    write("aux", "key-event-rotation-to-thief", fixture("key-event", "A thief holding the key rotates it to the thief's own key.", hijack))
    late_comp, _ = key_event("compromised", gen="2026-11-28T00:00:00Z", block="2026-11-28T01:00:00Z", compromisedNotBefore="2026-11-25T12:00:00Z")
    write("aux", "key-event-compromise-after-theft", fixture("key-event", "The owner reports the theft afterwards, from 2026-11-25T12:00.", late_comp))
    conflict, _ = key_event("rotated", gen="2026-12-02T00:00:00Z", block="2026-12-02T01:00:00Z", successorPublicKeyHex=PUB_THIEF.hex())
    write("aux", "key-event-rotation-conflicting", fixture("key-event", "A second rotation of the same key to a different successor.", conflict))

    env_s, sigs_s = envelope(statement(NONCE_3, ARTIFACT_2, "host.go"), signers=(NEXT,))
    write("aux", "bundle-successor", fixture("bundle", "A registration signed by the successor key after the rotation.",
                                             bundle_of(env_s, [tsa(sigs_s[0], "a", "2026-12-02T00:00:00Z"), ots(sigs_s[0], "2026-12-02T01:00:00Z")], keys=(NEXT,))))
    env_t, sigs_t = envelope(statement(NONCE_3, ARTIFACT_2, "host.go"), signers=(THIEF,))
    write("aux", "bundle-thief", fixture("bundle", "A registration signed by the thief's key after the hijacking rotation.",
                                         bundle_of(env_t, [tsa(sigs_t[0], "a", "2026-11-27T00:00:00Z"), ots(sigs_t[0], "2026-11-27T01:00:00Z")], keys=(THIEF,))))
    env_1, sigs_1 = envelope(st)
    write("aux", "bundle-one-source", fixture("bundle", "Only one time source (TSA A) for the creator's signature.", bundle_of(env_1, [tsa(sigs_1[0], "a")])))
    succ, thief = {"bundle": "aux/bundle-successor.json", "artifacts": ART2}, {"bundle": "aux/bundle-thief.json", "artifacts": ART2}
    events = {
        "-compromise-recent": (["fixtures/key-event-compromise-recent.json"], rmeta, "Bound between the claimed start and the event's proved time: `disputed`."),
        "-compromise-early": (["fixtures/key-event-compromise-early.json"], rmeta, "An early-dated claim is clamped to the look-back window: `trusted`."),
        "-event-unauthorized": (["aux/key-event-by-other-key.json"], rmeta, "An event signed by another key is `ignored-unauthorized`."),
        "-rotation-applied": (["fixtures/key-event-rotation.json"], succ, "The successor is trusted for signatures bounded after the rotation."),
        "-rotation-hijack": (["aux/key-event-rotation-to-thief.json", "aux/key-event-compromise-after-theft.json"], thief,
                             "B1: the rotation falls inside the later compromise window, so it is `disputed` and the thief's key gains no trust."),
        "-rotation-conflict": (["fixtures/key-event-rotation.json", "aux/key-event-rotation-conflicting.json"], succ,
                               "B1: two rotations of one key to different successors are both `disputed`."),
        "-event-order-a": (["aux/key-event-retired-by-successor.json", "fixtures/key-event-rotation.json"], rmeta,
                           "B2: retirement listed before the rotation it relies on; identical result to order b."),
        "-event-order-b": (["fixtures/key-event-rotation.json", "aux/key-event-retired-by-successor.json"], rmeta,
                           "B2: the same two events in the other order; identical result to order a."),
        "-single-source-event": (["fixtures/key-event-rotation.json"], {"bundle": "aux/bundle-one-source.json", "artifacts": ART},
                                 "S1: a key event affects the key and the signature has no quorum bound: `disputed`, never `trusted`."),
    }
    for name, (evs, meta, desc) in events.items():
        vr(name, desc, result_for(meta["bundle"], artifacts=meta["artifacts"], events=evs), keyEvents=evs, **meta)

    env_w, sigs_w = envelope(st)
    write("aux", "bundle-witness-shared-tsa", fixture("bundle", "Direct TSA A token plus a witness whose own token also comes from TSA A.",
                                                      bundle_of(env_w, [tsa(sigs_w[0], "a"), witness_evidence(sigs_w[0], "a")])))
    write("aux", "bundle-witness-independent", fixture("bundle", "Direct TSA A token plus a witness whose token comes from TSA B.",
                                                       bundle_of(env_w, [tsa(sigs_w[0], "a"), witness_evidence(sigs_w[0], "b")])))
    vr("-witness-shared-tsa", "S4: the witness rests on TSA A, so it and the direct token form one class: `below-quorum`.",
       result_for("aux/bundle-witness-shared-tsa.json"), bundle="aux/bundle-witness-shared-tsa.json", artifacts=ART)
    vr("-witness-independent", "S4: witness on TSA B plus direct TSA A: two classes, `quorum-met`.",
       result_for("aux/bundle-witness-independent.json"), bundle="aux/bundle-witness-independent.json", artifacts=ART)

    env_u, sigs_u = envelope(st, url_safe=True)
    assert any(ch in env_u["payload"] + env_u["signatures"][0]["sig"] for ch in "-_"), "URL-safe fixture must use - or _"
    write("fixtures", "bundle-url-safe", fixture("bundle", "Payload and signature in URL-safe base64; DSSE verifiers MUST accept either (S7).",
                                                 bundle_of(env_u, [tsa(sigs_u[0], "a"), ots(sigs_u[0])]), artifacts=ART))

    link = {"linkVersion": C.LINK_VERSION, "report": {"path": REPORT, "bodySha256": C.sha(C.jcs(REPORT_BODY))},
            "registration": {"bundle": B3, "statementSha256": C.sha(C.jcs(st))},
            "links": [{"pair": 0, "role": "reference", "subjectIndex": 0, "sha256": C.sha(ARTIFACT)}],
            "catalogueOpening": {"catalogue": CATALOGUE_SRC, "nonceHex": CAT_NONCE.hex()}, "notShown": C.NOT_SHOWN}
    write("fixtures", "report-link", fixture("report-link", "Links the committed example comparison report to the registration, without changing the report.", link))
    ren_doc = {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result.json", "lines": render(result)}
    write("fixtures", "rendering", fixture("rendering", "User-facing text built only from the allowed templates.", ren_doc))

    env2, sigs2 = envelope(statement(NONCE_2, ARTIFACT_2, "host.go"))
    write("fixtures", "bundle-second-work", fixture("bundle", "A second registration by the same registrant, fresh nonce.",
                                                    bundle_of(env2, [tsa(sigs2[0], "a", "2026-11-23T11:00:00Z"), ots(sigs2[0])])))
    write("fixtures", "registration-set", fixture("registration-set", "Two registrations by one producer: nonces differ.",
                                                  {"setVersion": C.SET_VERSION, "registrations": [B3, "fixtures/bundle-second-work.json"]}))

    build_negatives(st, sig, three, result, rmeta, link, ren_doc, res_co, recent, res_claim)
    build_real()
    build_agent(sig, result)


def build_negatives(st, sig, three, result, rmeta, link, ren, res_co, recent, res_claim):
    neg = lambda name, doc: write("negative", f"neg-{name}", doc)

    def vneg(name, desc, base_rel, mutate, code, also=None, **meta):
        r = json.loads((HERE / base_rel).read_text())
        obj = copy.deepcopy(r["object"])
        mutate(obj)
        m = {k: v for k, v in r["fixture"].items() if k in ("bundle", "artifacts", "keyEvents")}
        m.update(meta)
        neg(name, fixture("verification-result", desc, obj, code, also, **m))

    bad = copy.deepcopy(link)
    bad["links"][0]["sha256"] = REPORT_BODY["pairs"][0]["candidate"]["sha256"]
    neg("subject-mismatch", fixture("report-link", "Links the candidate's digest instead of the registered reference.", bad, "subject-mismatch"))
    wrong = copy.deepcopy(three["timeEvidence"][0])
    wrong["target"]["sha256"] = C.sha(C.jcs(st))
    neg("evidence-wrong-target", fixture("evidence", "Token over the statement bytes, not over the signature.", wrong, "evidence-wrong-target", bundle=B3))
    wrong = copy.deepcopy(three["timeEvidence"][0])
    wrong["target"]["sha256"] = C.sha(base64.b64encode(sig))
    neg("evidence-target-base64", fixture("evidence", "Token over the base64 text of the signature, not its raw bytes (A1).", wrong, "evidence-wrong-target", bundle=B3))
    wrong = copy.deepcopy(three["timeEvidence"][0])
    wrong["target"]["signatureIndex"] = 5
    neg("signature-index-out-of-range", fixture("evidence", "Target names a signature the envelope does not have.", wrong, "evidence-shape", bundle=B3))
    ren_bad = json.loads((HERE / "fixtures/evidence-renewal.json").read_text())["object"]
    ren_bad["target"]["sha256"] = C.sha(b"another token")
    neg("renewal-wrong-target", fixture("evidence", "Renewal whose target digest is not the renewed token's bytes.", ren_bad, "evidence-wrong-target", bundle="fixtures/bundle-renewed.json"))
    ck = copy.deepcopy(three["timeEvidence"][0])
    ck["type"] = "cosigned-checkpoint"
    neg("checkpoint-type-removed", fixture("evidence", "The cosigned-checkpoint type is removed in draft-3 (S5).", ck, "evidence-shape", bundle=B3))

    vneg("claimed-as-proved", "Claimed creation time reported as the earliest bound.", "fixtures/verification-result.json",
         lambda r: r["outcomes"]["time"][0].update(notAfterAnyRoot="2026-11-20T09:00:00Z"), "claimed-as-proved")
    for i, line in enumerate(["This registration proves you are the author of sum.go.",
                              "This registration establishes your claim to sum.go.", "sum.go is registered to you as its creator.",
                              "This record proves you wrote sum.go.", f"Registered first: sum.go belongs to key {KEYID}."]):
        rb = copy.deepcopy(ren)
        rb["lines"].insert(1, line)
        also = ["rendering-unlisted-line"] + (["ordering-claim"] if i == 4 else [])
        neg(f"authorship-claim-{i}", fixture("rendering", f"Rendering adds: {line}", rb, "authorship-claim", also))
    rb = copy.deepcopy(ren)
    rb["lines"].insert(1, "sum.go was registered before host.go.")
    neg("ordering-claim", fixture("rendering", "Two registrations' times presented as an order (S8).", rb, "ordering-claim", ["rendering-unlisted-line"]))
    rb = copy.deepcopy(ren)
    rb["lines"].insert(1, "Thank you for registering with Traceweave.")
    neg("rendering-unlisted-line", fixture("rendering", "A harmless line outside the template list is still refused.", rb, "rendering-unlisted-line"))
    rb = copy.deepcopy(ren)
    rb["lines"] = rb["lines"][:-3]
    neg("notice-missing", fixture("rendering", "Rendering without the three fixed sentences.", rb, "notice-missing"))
    rb = {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result-cosigned.json", "lines": render(res_co)}
    rb["lines"] = [l.replace(f"No proved time for key {KEYID_CO}.", f"This record shows that the content existed, and that key {KEYID_CO} signed a statement naming it, no later than 2026-11-23T10:00:01Z (according to one time source only).") for l in rb["lines"]]
    neg("key-bound-misattributed-rendering", fixture("rendering", "The co-signer is given the first signature's bound (W8).", rb, "key-bound-misattributed"))
    vneg("key-bound-misattributed", "A later co-signature inherits the earlier signature's bound (W8).", "fixtures/verification-result-cosigned.json",
         lambda r: r["outcomes"]["time"][1].update({k: res_co["outcomes"]["time"][0][k] for k in ("notAfterAnyRoot", "notAfterQuorum", "outcome")}),
         "key-bound-misattributed")
    vneg("key-event-ignored", "A compromise event covering the bound is ignored; signer still `trusted` (W10).",
         "fixtures/verification-result-compromise-recent.json", lambda r: r["outcomes"]["signerTrust"][0].update(outcome="trusted"), "key-event-ignored")
    vneg("rotation-hijack", "B1: the thief's successor key reported `trusted`.", "fixtures/verification-result-rotation-hijack.json",
         lambda r: r["outcomes"]["signerTrust"][0].update(outcome="trusted"), "key-event-ignored")
    vneg("rotation-conflict", "B1: a successor of conflicting rotations reported `trusted`.", "fixtures/verification-result-rotation-conflict.json",
         lambda r: r["outcomes"]["signerTrust"][0].update(outcome="trusted"), "key-event-ignored")

    def order_dependent(r):
        for e in r["outcomes"]["keyEvents"]:
            if e["event"] == "retired":
                e["outcome"] = "ignored-unauthorized"
    vneg("event-order-dependent", "B2: a list-order evaluator ignores the retirement that precedes its rotation in the list.",
         "fixtures/verification-result-event-order-a.json", order_dependent, "key-event-ignored")
    vneg("trust-without-quorum", "S1: trust after a key event decided on one source.", "fixtures/verification-result-single-source-event.json",
         lambda r: r["outcomes"]["signerTrust"][0].update(outcome="trusted"), "trust-without-quorum")
    vneg("trust-by-hint", "B3: the policy lists trusted keys by their 64-bit keyid.", "fixtures/verification-result.json",
         lambda r: r["policy"].update(trustedKeys=[KEYID]), "key-identity-by-hint")
    vneg("witness-shared-tsa", "S4: a witness and the TSA its time comes from counted as two sources.", "fixtures/verification-result-witness-shared-tsa.json",
         lambda r: r["outcomes"]["time"][0].update(distinctRoots=2, outcome="quorum-met", notAfterQuorum="2026-11-23T10:00:04Z"), "quorum-miscount")
    vneg("claim-any-signer", "S11: the claim compared with the untrusted co-signer's earlier bound.", "fixtures/verification-result-claim-trusted-only.json",
         lambda r: r["outcomes"]["claimedCreatedAt"].update(status="after-proved-bound", comparedWith="2026-11-23T10:00:01Z"), "result-mismatch")

    def ignore_expiry(r):
        for e in r["outcomes"]["timeEvidence"]:
            if e["outcome"] == "expired-unrenewed":
                e.update(outcome="placeholder-assumed-valid", notAfter="2026-11-23T10:00:01Z")
    vneg("expired-accepted", "S6: tokens accepted after their TSA certificates expired, with no renewal.", "fixtures/verification-result-expired.json",
         ignore_expiry, "result-mismatch")
    vneg("single-verdict", "Adds a single 'authentic' verdict.", "fixtures/verification-result.json",
         lambda r: r["outcomes"].update(authentic=True), "single-verdict")
    vneg("quorum-miscount", "The Rekor entry, which has no time, counted as a fourth root.", "fixtures/verification-result.json",
         lambda r: r["outcomes"]["time"][0].update(distinctRoots=4), "quorum-miscount")
    vneg("result-mismatch", "An outcome value outside the closed list.", "fixtures/verification-result-compromise-recent.json",
         lambda r: r["outcomes"]["claimedCreatedAt"].update(status="proved"), "result-mismatch")
    vneg("accuracy-assumed", "A token without accuracy, and none in policy, counted anyway (A3).", "fixtures/verification-result-no-accuracy.json",
         lambda r: r["outcomes"]["timeEvidence"][1].update(outcome="placeholder-assumed-valid"), "result-mismatch")
    vneg("wrong-policy-accepted", "A token whose policy OID the verifier does not accept, counted anyway.", "fixtures/verification-result-wrong-policy.json",
         lambda r: r["outcomes"]["timeEvidence"][0].update(outcome="placeholder-assumed-valid", notAfter="2026-11-23T10:00:01Z"), "result-mismatch")
    vneg("revocation-ignored", "A key-compromise revocation ignored.", "fixtures/verification-result-revoked-key-compromise.json",
         lambda r: r["outcomes"]["timeEvidence"][0].update(outcome="placeholder-assumed-valid", notAfter="2026-11-23T10:00:01Z"), "result-mismatch")
    r = result_for(B3, artifacts=[])
    r["outcomes"]["subjects"][0]["outcome"] = "match"
    neg("subject-unsupplied-match", fixture("verification-result", "Reports `match` without the file (W6b).", r, "result-mismatch", bundle=B3))

    tampered = copy.deepcopy(st)
    tampered["predicate"]["claims"]["createdAt"] = "2026-01-01T00:00:00Z"
    env_t, sigs_t = envelope(st, payload_override=C.jcs(tampered))
    neg("signature-invalid", fixture("bundle", "Claimed time edited after signing.", bundle_of(env_t, [tsa(sigs_t[0])]), "signature-invalid"))
    env_d, sigs_d = envelope(st, signers=(CREATOR, CREATOR))
    neg("duplicate-signer", fixture("bundle", "The same key signs the envelope twice.", bundle_of(env_d, [tsa(sigs_d[0])]), "envelope-shape"))
    unl = copy.deepcopy(three["timeEvidence"][0])
    unl["notice"] = "RFC 3161 time-stamp token issued by the TSA."
    neg("placeholder-unlabelled", fixture("evidence", "Placeholder presented as a real token.", unl, "placeholder-unlabelled", bundle=B3))
    neg("pending-counted", fixture("evidence", "A pending proof that states a block time.",
                                   evidence("opentimestamps", sig, "btc", {"status": "pending", "blockTime": "2026-11-23T11:12:00Z"}), "pending-counted", bundle=B3))
    lt = copy.deepcopy(three["timeEvidence"][3])
    lt["statedTime"] = {"genTime": "2026-11-23T10:00:00Z"}
    neg("log-time-claimed", fixture("evidence", "Rekor v2 placeholder that claims a time.", lt, "log-time-claimed", bundle=B3))
    lab = copy.deepcopy(three["timeEvidence"][0])
    lab["root"] = {"kind": "tsa-certificate-chain", "id": "my-favourite-tsa"}
    neg("root-not-anchored", fixture("evidence", "Root named by a producer-written label instead of a trust anchor (W3).", lab, "root-not-anchored", bundle=B3))
    nm = tsa(sig, "a", nonce="5a17c0de000000ff")
    neg("tsa-nonce-mismatch", fixture("evidence", "Token nonce differs from the request nonce: a possibly replayed response.", nm, "tsa-nonce-mismatch", bundle=B3))
    shp = copy.deepcopy(three["timeEvidence"][0])
    shp["rfc3161"]["genTime"] = "2026-11-23 10:00"
    neg("evidence-shape", fixture("evidence", "Malformed genTime.", shp, "evidence-shape", bundle=B3))

    def resigned(name, desc, code, **changes):
        b, _ = three_roots(statement(**changes))
        neg(name, fixture("bundle", desc, b, code, artifacts=ART))

    resigned("catalogue-unsalted", "Plain catalogue digest.", "catalogue-unsalted",
             **{"predicate.catalogue.scheme": "sha256", "predicate.catalogue.sha256": C.sha(CATALOGUE)})
    resigned("forbidden-field", "Fingerprints in the statement.", "forbidden-field", **{"predicate.fingerprints": ["9f3a52c1d07e4b21"]})
    resigned("nonce-invalid", "All-zero nonce.", "nonce-invalid", **{"predicate.nonce": "0" * 64})
    resigned("subject-name", "A path as subject name.", "subject-name", **{"subject.0.name": "private/drafts/sum.go"})
    resigned("time-in-statement", "A 'provedAt' written by the registrant.", "time-in-statement", **{"predicate.provedAt": "2026-11-01T00:00:00Z"})
    resigned("possession-mismatch", "Possession digest not computed from the content.", "possession-mismatch",
             **{"predicate.possession.0.sha256": C.sha(b"not computed from the content")})
    resigned("predicate-type", "Draft-2 predicate type.", "predicate-type",
             **{"predicateType": "https://traceweave.org/predicate/registration/draft-2"})
    resigned("provenance-shape", "Implementation commit is not an object id (B10).", "provenance-shape", **{"predicate.implementation.commit": "main"})
    resigned("statement-shape", "Unknown predicate field.", "statement-shape", **{"predicate.licence": "all rights reserved"})
    b, _ = three_roots()
    b["envelope"]["payloadType"] = "application/json"
    neg("envelope-shape", fixture("bundle", "Wrong DSSE payload type.", b, "envelope-shape"))

    env_s, sigs_s = envelope(st)
    write("aux", "bundle-same-anchor", fixture("bundle", "Two TSA tokens under one trust anchor.",
                                               bundle_of(env_s, [tsa(sigs_s[0], "a"), tsa(sigs_s[0], "a", "2026-11-23T10:00:30Z")])))
    r = result_for("aux/bundle-same-anchor.json")
    r["outcomes"]["time"][0].update(distinctRoots=2, outcome="quorum-met", notAfterQuorum="2026-11-23T10:00:31Z")
    neg("quorum-same-anchor", fixture("verification-result", "Two tokens under one CA counted as two roots (W3).", r, "quorum-miscount",
                                      bundle="aux/bundle-same-anchor.json", artifacts=ART))
    env_c, sigs_c = envelope(st)
    write("aux", "bundle-cert-expired", fixture("bundle", "TSA A's signing certificate expired before genTime.", bundle_of(env_c, [
        tsa(sigs_c[0], "a", cert=("2025-01-01T00:00:00Z", "2026-06-30T00:00:00Z")), ots(sigs_c[0])])))
    r = result_for("aux/bundle-cert-expired.json")
    r["outcomes"]["timeEvidence"][0].update(outcome="placeholder-assumed-valid", notAfter="2026-11-23T10:00:01Z")
    neg("cert-validity-ignored", fixture("verification-result", "TSA certificate validity at genTime ignored (W9).", r, "result-mismatch",
                                         bundle="aux/bundle-cert-expired.json", artifacts=ART))

    bad = copy.deepcopy(link)
    bad["catalogueOpening"]["nonceHex"] = "ff" * 32
    neg("catalogue-does-not-open", fixture("report-link", "Wrong opening nonce.", bad, "catalogue-does-not-open"))
    bad = copy.deepcopy(link)
    bad["registration"]["statementSha256"] = C.sha(b"another statement")
    neg("statement-digest", fixture("report-link", "The link names a different statement.", bad, "statement-digest"))
    bad = copy.deepcopy(link)
    bad["report"]["bodySha256"] = C.sha(b"another report body")
    neg("report-digest", fixture("report-link", "The link names a different report body.", bad, "report-digest"))
    st_p = statement(**{"predicate.catalogue.profile.version": "draft-0"})
    bp, _ = three_roots(st_p)
    write("aux", "bundle-other-profile", fixture("bundle", "Registration under a different profile version.", bp))
    bad = copy.deepcopy(link)
    bad["registration"] = {"bundle": "aux/bundle-other-profile.json", "statementSha256": C.sha(C.jcs(st_p))}
    neg("profile-mismatch", fixture("report-link", "Registered profile differs from the report's.", bad, "profile-mismatch"))
    st_c = statement(catalogue=OTHER_CATALOGUE)
    bc, _ = three_roots(st_c)
    write("aux", "bundle-other-catalogue", fixture("bundle", "Registration committing to another catalogue.", bc))
    bad = copy.deepcopy(link)
    bad["registration"] = {"bundle": "aux/bundle-other-catalogue.json", "statementSha256": C.sha(C.jcs(st_c))}
    bad["catalogueOpening"]["catalogue"] = OTHER_CATALOGUE_SRC
    neg("catalogue-not-report-input", fixture("report-link", "Opens a registered catalogue that is not the report's reference catalogue.", bad, "catalogue-not-report-input"))
    doc = fixture("statement", "Fixture notice removed.", st, "fixture-shape")
    doc["fixture"]["notice"] = "A real registration."
    neg("fixture-shape", doc)

    env_r, sigs_r = envelope(statement(artifact=ARTIFACT_2, name="host.go"))
    write("aux", "bundle-nonce-reused", fixture("bundle", "Another work registered with the same nonce.", bundle_of(env_r, [tsa(sigs_r[0])])))
    neg("nonce-reused", fixture("registration-set", "Nonce reused across two registrations (W4).",
                                {"setVersion": C.SET_VERSION, "registrations": [B3, "aux/bundle-nonce-reused.json"]}, "nonce-reused"))
    st_k = json.loads(base64.b64decode(recent["envelope"]["payload"]))
    del st_k["predicate"]["compromisedNotBefore"]
    e2, s2 = envelope(st_k)
    neg("key-event-shape", fixture("key-event", "Compromise event without its claimed start.", bundle_of(e2, [tsa(s2[0], "a", "2026-11-25T00:00:00Z")]), "key-event-shape"))
    st_k = json.loads(base64.b64decode(recent["envelope"]["payload"]))
    st_k["subject"][0]["digest"]["sha256"] = C.sha(PUB_CO)
    e3, s3 = envelope(st_k)
    neg("key-event-subject-mismatch", fixture("key-event", "B3: the event's keyid hint names the creator key but its subject digest names another key.",
                                              bundle_of(e3, [tsa(s3[0], "a", "2026-11-25T00:00:00Z")]), "key-event-shape"))
    raw = json.dumps(fixture("statement", "Duplicate key.", st), indent=2)
    (HERE / "negative" / "neg-duplicate-key.json").write_text(raw.replace('"contentKind": "source-code",', '"contentKind": "source-code",\n      "contentKind": "text",', 1), encoding="utf-8")


# ------------------------------------------------------------------ agent fixtures (design section 19)

EXT = {"uri": C.A2A_EXTENSION, "description": "Traceweave registration profile (proposed; not published).", "required": True}


def hosted_card(**changes):
    card = {
        "name": "Traceweave witness (illustrative)",
        "description": "Illustrative only; no such service exists. Receives the SHA-256 of a registrant's DSSE signature, never content or fingerprints, and returns a signed, time-stamped witness statement. " + LIMIT,
        "supportedInterfaces": [{"url": "https://witness.example.invalid/a2a/v1", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
        "provider": {"organization": "Traceweave (illustrative; no operator exists)", "url": "https://traceweave.org"},
        "version": "0.0.0-illustrative",
        "capabilities": {"streaming": False, "pushNotifications": False, "extensions": [dict(EXT, params={"wire": "digests-only"})]},
        "securitySchemes": {"oidc": {"openIdConnectSecurityScheme": {"openIdConnectUrl": "https://issuer.example.invalid/.well-known/openid-configuration"}}},
        "securityRequirements": [{"schemes": {"oidc": {"list": ["openid"]}}}],
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [{
            "id": "witness-digest", "name": "Witness a registration digest",
            "description": "Records that the authenticated caller presented this signature digest, signs a witness statement and attaches the witness's own RFC 3161 token. It does not register content, check authorship or check originality. " + LIMIT,
            "tags": ["traceweave", "registration", "witness", "timestamp"],
            "examples": ['{"requestVersion": "traceweave-witness-request-draft-3", "presented": {"kind": "dsse-signature-sha256", "sha256": "<64 hex>"}}'],
            "inputModes": ["application/json"], "outputModes": ["application/json"]}],
    }
    card.update(changes)
    return card


def local_card():
    return {
        "name": "Traceweave local registrar (illustrative)",
        "description": "Illustrative only. Runs on the registrant's machine, on loopback. Signs with the registrant's own key and requests time evidence; only a signature digest leaves the machine. " + LIMIT,
        "supportedInterfaces": [{"url": "http://127.0.0.1:8765/a2a/v1", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
        "version": "0.0.0-illustrative",
        "capabilities": {"streaming": True, "pushNotifications": False, "extensions": [dict(EXT, params={"wire": "local-only"})]},
        "defaultInputModes": ["application/json"], "defaultOutputModes": ["application/json"],
        "skills": [
            {"id": "register", "name": "Register files", "tags": ["traceweave", "registration"],
             "description": "Registers local files by path: hashes them, signs a registration statement with the registrant key held by this tool, and requests time evidence. " + LIMIT},
            {"id": "verify", "name": "Verify a registration", "tags": ["traceweave", "verification"],
             "description": "Verifies a registration bundle against local files under the caller's policy and returns separate outcomes, never a single verdict. " + LIMIT},
        ],
    }


def witness_request(presented, parts_extra=None, data_extra=None):
    data = {"requestVersion": C.WITNESS_REQUEST_VERSION, "presented": {"kind": "dsse-signature-sha256", "sha256": presented}}
    data.update(data_extra or {})
    return {"message": {"messageId": "0f6c2a8e-illustrative-0001", "role": "ROLE_USER",
                        "parts": [{"data": data, "mediaType": "application/json"}] + (parts_extra or []), "extensions": [C.A2A_EXTENSION]}}


def witness_task(presented, **pred_changes):
    wb = witness_bundle(presented, "a", **pred_changes)
    return {"id": "task-illustrative-0001", "contextId": "ctx-illustrative-0001", "status": {"state": "TASK_STATE_COMPLETED"},
            "artifacts": [{"artifactId": "witness-0001", "name": "witness statement", "parts": [{"data": wb, "mediaType": "application/json"}]}]}


def mcp_tool(**changes):
    tool = {
        "name": "traceweave_register",
        "title": "Register files with Traceweave (illustrative)",
        "description": "Registers local files: hashes them, signs a registration statement with the registrant key held by this local server, and requests time evidence. Only a signature digest leaves the machine. " + LIMIT,
        "inputSchema": {"type": "object", "additionalProperties": False, "required": ["paths"],
                        "properties": {"paths": {"type": "array", "minItems": 1, "maxItems": 64, "items": {"type": "string"}},
                                       "claimedCreatedAt": {"type": "string", "description": "Optional claimed creation time; never shown as proved."}}},
        "outputSchema": {"type": "object", "required": ["bundleId", "statementSha256", "timeEvidence"],
                         "properties": {"bundleId": {"type": "string", "description": "Opaque id of the bundle in the private store; never a path (SK.2)."},
                                        "statementSha256": {"type": "string"}, "timeEvidence": {"type": "array", "items": {"type": "object"}}}},
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    }
    tool.update(changes)
    return tool


def build_agent(sig, result):
    presented = C.sha(sig)
    agent_meta = {"bundle": B3}
    write("fixtures", "a2a-card-hosted-witness", fixture("a2a-agent-card", "Illustrative A2A 1.0 Agent Card for a hosted witness (architecture b). Checked against the a2a.proto field lists only.", hosted_card()))
    write("fixtures", "a2a-card-local-registrar", fixture("a2a-agent-card", "Illustrative A2A 1.0 Agent Card for a local registrar on loopback (architecture a).", local_card()))
    write("fixtures", "a2a-request-witness", fixture("a2a-request", "SendMessageRequest to the witness: one data part with the signature digest.", witness_request(presented), **agent_meta))
    write("fixtures", "a2a-task-witness", fixture("a2a-task", "Completed task: one artifact holding the signed witness statement and the witness's RFC 3161 placeholder.",
                                                   witness_task(presented), request="fixtures/a2a-request-witness.json"))
    write("fixtures", "mcp-tool-register", fixture("mcp-tool", "Illustrative MCP 2026-07-28 Tool for the local route.", mcp_tool()))
    wline = "Witnessed: the caller placeholder-subject-0001 presented the signature digest no later than 2026-11-23T10:00:04Z, according to the witness's time-stamp authority."
    ren = {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result.json", "context": "agent",
           "lines": render(result, context="agent", witness=wline)}
    write("fixtures", "rendering-agent", fixture("rendering", "User-facing text for a registration made through an agent.", ren))

    neg = lambda name, doc: write("negative", f"neg-{name}", doc)
    neg("content-on-wire", fixture("a2a-request", "Sends the file itself as a raw part to the hosted witness.",
                                   witness_request(presented, parts_extra=[{"raw": base64.b64encode(ARTIFACT).decode(), "filename": "sum.go", "mediaType": "text/plain"}]),
                                   "content-on-wire", **agent_meta))
    neg("fingerprints-on-wire", fixture("a2a-request", "Sends fingerprints to the hosted witness.",
                                        witness_request(presented, data_extra={"fingerprints": ["9f3a52c1d07e4b21"]}), "forbidden-field", **agent_meta))
    neg("witness-wrong-digest", fixture("a2a-request", "Presents the artifact digest instead of the signature digest.",
                                        witness_request(C.sha(ARTIFACT)), "evidence-wrong-target", **agent_meta))
    bad = hosted_card()
    bad["supportedInterfaces"][0]["protocolVersion"] = "1.0.1"
    neg("a2a-shape", fixture("a2a-agent-card", "Patch version in protocolVersion (A2A 3.6: Major.Minor only).", bad, "a2a-shape"))
    bad = hosted_card()
    bad["skills"][0]["description"] = "Registers your work and proves you made it."
    neg("card-notice-missing", fixture("a2a-agent-card", "Skill description without the limit sentence.", bad, "notice-missing"))
    bad = hosted_card()
    bad["supportedInterfaces"][0]["url"] = "http://witness.example.invalid/a2a/v1"
    neg("hosted-plain-http", fixture("a2a-agent-card", "Digests-only witness offered over plain HTTP.", bad, "content-on-wire"))
    neg("witness-authorship", fixture("a2a-task", "Witness statement asserts the caller is the author.",
                                      witness_task(presented, author="placeholder-subject-0001"), "authorship-claim", request="fixtures/a2a-request-witness.json"))
    neg("witness-shape", fixture("a2a-task", "Witness statement without the caller it authenticated.",
                                 witness_task(presented, caller={"scheme": "none"}), "witness-shape", request="fixtures/a2a-request-witness.json"))
    neg("mcp-tool-shape", fixture("mcp-tool", "Registration tool declared closed-world and idempotent.",
                                  mcp_tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}), "mcp-tool-shape"))
    neg("agent-notice-missing", fixture("rendering", "Agent-made registration without the agent sentence.", dict(ren, lines=ren["lines"][:-1]), "notice-missing"))
    lines = list(ren["lines"])
    lines.insert(1, "This shows the agent created sum.go.")
    neg("agent-authorship", fixture("rendering", "Rendering says the agent created the content.", dict(ren, lines=lines), "authorship-claim", ["rendering-unlisted-line"]))


if __name__ == "__main__":
    build()
    counts = {f: len(list((HERE / f).glob("*.json"))) for f in ("fixtures", "negative", "aux")}
    print("built", counts["fixtures"], "positive,", counts["negative"], "negative and", counts["aux"], "auxiliary fixtures")
