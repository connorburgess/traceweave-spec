#!/usr/bin/env python3
"""Rebuild the illustrative registration fixtures, draft-2 (fixtures/, negative/ and aux/).

Standard library only. Deterministic: Ed25519 signatures are deterministic, and
every nonce, key and trust anchor below is derived from a fixed public label. The
keys are public test-only keys; the anchors are placeholders, not digests of real
certificates. Never use any of them for anything real.

Sources (committed elsewhere in this repository, read only):
  - the artifacts: test-vectors/matching/extraction-go.json, vectors mv-go-sum and mv-go-host;
  - the reference catalogue: test-vectors/matching/matching.json, vector 1 reference canonical;
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


SEED, SEED_CO, SEED_NEXT, SEED_WITNESS = (label(f"traceweave registration fixture {n} test key; public; never use")
                                          for n in ("creator", "co-signer", "successor", "witness"))
PUB, PUB_CO, PUB_NEXT, WITNESS_PUB = (C.ed25519_public(s) for s in (SEED, SEED_CO, SEED_NEXT, SEED_WITNESS))
KEYID, KEYID_CO, KEYID_NEXT = C.keyid(PUB), C.keyid(PUB_CO), C.keyid(PUB_NEXT)
NONCE = label("traceweave registration fixture nonce; public; never use").hex()
NONCE_2 = label("traceweave registration fixture nonce 2; public; never use").hex()
ANCHOR = {k: label(f"PLACEHOLDER trust anchor: {v}; not a real certificate or key").hex() for k, v in {
    "tsa-a": "root certificate of TSA operator A", "tsa-b": "root certificate of TSA operator B",
    "btc": "Bitcoin main chain as pinned by the verifier's own node", "log": "log key of a Rekor v2 shard",
    "witness": "key of a checkpoint witness"}.items()}

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
LIMIT = C.SENTENCE_FIRST
B3 = "fixtures/bundle-three-roots.json"

POLICY = {
    "quorum": 2,
    "timeRoots": [
        {"anchorSha256": ANCHOR["tsa-a"], "kind": "tsa-certificate-chain", "independenceGroup": "tsa-operator-a", "policyOids": ["2.999.1"]},
        {"anchorSha256": ANCHOR["tsa-b"], "kind": "tsa-certificate-chain", "independenceGroup": "tsa-operator-b", "policyOids": ["2.999.2"], "accuracySeconds": 1},
        {"anchorSha256": ANCHOR["btc"], "kind": "bitcoin-proof-of-work", "independenceGroup": "bitcoin"},
        {"anchorSha256": ANCHOR["log"], "kind": "log-key", "independenceGroup": "log-a"},
    ],
    "trustedKeyids": [KEYID],
    "tsaRevocations": [],
    "compromiseLookbackSeconds": 2592000,
}


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
            "implementation": {"name": "build_fixtures.py", "version": "draft-2", "commit": ZERO40},
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


def envelope(st, signers=((SEED, KEYID),), payload_override=None):
    payload = C.jcs(st)
    sigs = [C.ed25519_sign(seed, C.pae(C.PAYLOAD_TYPE, payload)) for seed, _ in signers]
    body = payload_override if payload_override is not None else payload
    return ({"payloadType": C.PAYLOAD_TYPE, "payload": base64.b64encode(body).decode(),
             "signatures": [{"keyid": kid, "sig": base64.b64encode(s).decode()} for (_, kid), s in zip(signers, sigs)]}, sigs)


def evidence(kind, sig, anchor, body, index=0):
    root_kind, body_key = C.EVIDENCE_TYPES[kind]
    ev = {"evidenceVersion": C.EVIDENCE_VERSION, "type": kind, "placeholder": True, "notice": C.PLACEHOLDER_NOTICE,
          "target": {"kind": "dsse-signature", "signatureIndex": index, "sha256": C.sha(sig)},
          "root": {"kind": root_kind, "anchorSha256": ANCHOR[anchor]},
          "token": f"PLACEHOLDER-NOT-A-{kind.upper()}-OBJECT"}
    if body is not None:
        ev[body_key] = body
    return ev


def tsa(sig, which="a", gen="2026-11-23T10:00:00Z", index=0, **extra):
    n = {"a": "5a17c0de00000001", "b": "5a17c0de00000002"}[which]
    body = {"genTime": gen, "policyOid": "2.999.1" if which == "a" else "2.999.2", "nonce": n, "requestNonce": n,
            "signerCertificate": {"notBefore": "2026-01-01T00:00:00Z", "notAfter": "2031-01-01T00:00:00Z"}}
    if which == "a":
        body["accuracySeconds"] = 1
    body.update(extra)
    return evidence("rfc3161", sig, f"tsa-{which}", body, index)


def ots(sig, block="2026-11-23T11:12:00Z", index=0):
    return evidence("opentimestamps", sig, "btc", {"status": "complete", "blockTime": block}, index)


def rekor(sig):
    return evidence("rekor-v2", sig, "log", {"logIndex": 0})


def bundle_of(env, evs, keys=((PUB, KEYID),)):
    return {"bundleVersion": C.BUNDLE_VERSION, "envelope": env,
            "verificationMaterial": {"publicKeys": [{"keyid": k, "alg": "ed25519", "publicKeyHex": p.hex()} for p, k in keys]},
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


def result_for(bundle_rel, policy=POLICY, artifacts=ART, events=()):
    obj = json.loads((HERE / bundle_rel).read_text())["object"]
    arts = {a["subjectIndex"]: C.load_source(a["source"]) for a in artifacts}
    ctx = C.check_bundle(obj, arts, set())
    return C.expected_result(ctx, arts, copy.deepcopy(policy), True, C.sha((HERE / bundle_rel).read_bytes()), list(events), set())


def key_event(event, signer=(SEED, KEYID), signer_pub=PUB, gen="2026-11-25T00:00:00Z", block="2026-11-25T01:00:00Z", **pred):
    st = {"_type": C.STATEMENT_TYPE, "subject": [{"name": "key", "digest": {"sha256": C.sha(PUB)}}],
          "predicateType": C.KEY_EVENT_TYPE,
          "predicate": {"eventVersion": C.KEY_EVENT_VERSION, "keyid": KEYID, "event": event, **pred}}
    env, sigs = envelope(st, signers=(signer,))
    return bundle_of(env, [tsa(sigs[0], "a", gen), ots(sigs[0], block)], keys=((signer_pub, signer[1]),)), st


def render(result, name="sum.go", context=None, witness=None):
    o = result["outcomes"]
    h = C.sha(ARTIFACT)
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


def build():
    for folder in ("fixtures", "negative", "aux"):
        for old in (HERE / folder).glob("*.json"):
            old.unlink()
    st = statement()
    three, sig = three_roots(st)
    write("fixtures", "statement", fixture("statement", "The registration statement (in-toto Statement v1) before signing.", st, artifacts=ART))
    write("fixtures", "bundle-three-roots", fixture(
        "bundle", "Signed statement with placeholders from three independent roots (TSA A, TSA B, Bitcoin) and a Rekor v2 entry (no time).", three, artifacts=ART))
    write("fixtures", "evidence-rfc3161", fixture("evidence", "RFC 3161 placeholder over the raw bytes of signature 0.", tsa(sig, "a"), bundle=B3))
    write("fixtures", "evidence-rfc3161-no-accuracy", fixture("evidence", "RFC 3161 placeholder without accuracy; the verifier's policy supplies it.", tsa(sig, "b", "2026-11-23T10:00:05Z"), bundle=B3))
    write("fixtures", "evidence-opentimestamps-complete", fixture("evidence", "Upgraded OpenTimestamps proof placeholder.", ots(sig), bundle=B3))
    write("fixtures", "evidence-opentimestamps-pending", fixture("evidence", "OpenTimestamps proof before upgrade: no time.",
                                                                  evidence("opentimestamps", sig, "btc", {"status": "pending"}), bundle=B3))
    write("fixtures", "evidence-rekor-v2", fixture("evidence", "Rekor v2 inclusion placeholder; no time of its own.", rekor(sig), bundle=B3))
    write("fixtures", "evidence-cosigned-checkpoint", fixture("evidence", "Witness-cosigned checkpoint placeholder; the witness's clock.",
                                                              evidence("cosigned-checkpoint", sig, "witness", {"cosignatureTime": "2026-11-23T10:05:00Z"}), bundle=B3))

    result = result_for(B3)
    rmeta = {"bundle": B3, "artifacts": ART}
    write("fixtures", "verification-result", fixture("verification-result", "Expected outcomes for bundle-three-roots and sum.go; placeholders assumed valid (simulated).", result, **rmeta))
    no_acc = copy.deepcopy(POLICY)
    del no_acc["timeRoots"][1]["accuracySeconds"]
    write("fixtures", "verification-result-no-accuracy", fixture(
        "verification-result", "TSA B's token has no accuracy and the policy gives none: that evidence is `unsupported`; two roots remain.", result_for(B3, no_acc), **rmeta))
    revoked = copy.deepcopy(POLICY)
    revoked["tsaRevocations"] = [{"anchorSha256": ANCHOR["tsa-a"], "revokedAt": "2027-03-01T00:00:00Z", "reasonCode": None}]
    write("fixtures", "verification-result-revoked", fixture(
        "verification-result", "TSA A's certificate revoked without a reasonCode: all its tokens are invalid (RFC 3161 section 4 item 1); quorum survives on TSA B and Bitcoin.", result_for(B3, revoked), **rmeta))

    env_co, sigs_co = envelope(st, signers=((SEED, KEYID), (SEED_CO, KEYID_CO)))
    cos = bundle_of(env_co, [tsa(sigs_co[0], "a"), ots(sigs_co[0])], keys=((PUB, KEYID), (PUB_CO, KEYID_CO)))
    write("fixtures", "bundle-cosigned", fixture("bundle", "The same statement later co-signed by a second key; evidence covers signature 0 only.", cos, artifacts=ART))
    res_co = result_for("fixtures/bundle-cosigned.json")
    write("fixtures", "verification-result-cosigned", fixture("verification-result", "Per-signature bounds: the co-signer gets none.", res_co,
                                                              bundle="fixtures/bundle-cosigned.json", artifacts=ART))
    write("fixtures", "rendering-cosigned", fixture("rendering", "Text for the co-signed bundle: a bound sentence only for the key that has one.",
                                                    {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result-cosigned.json", "lines": render(res_co)}))

    rot, _ = key_event("rotated", gen="2026-12-01T00:00:00Z", block="2026-12-01T01:00:00Z", successorPublicKeyHex=PUB_NEXT.hex())
    write("fixtures", "key-event-rotation", fixture("key-event", "The key names its successor; time-stamped like a registration.", rot))
    recent, _ = key_event("compromised", compromisedNotBefore="2026-11-23T00:00:00Z")
    write("fixtures", "key-event-compromise-recent", fixture("key-event", "Compromise reported two days after the claimed start.", recent))
    early, _ = key_event("compromised", gen="2027-01-15T00:00:00Z", block="2027-01-15T01:00:00Z", compromisedNotBefore="2026-01-01T00:00:00Z")
    write("fixtures", "key-event-compromise-early", fixture("key-event", "Compromise claimed from a date long before it was reported.", early))
    other, _ = key_event("compromised", signer=(SEED_CO, KEYID_CO), signer_pub=PUB_CO, compromisedNotBefore="2026-01-01T00:00:00Z")
    write("aux", "key-event-by-other-key", fixture("key-event", "A compromise event for the creator key, signed by an unrelated key.", other))
    for name, rel, desc in [
        ("compromise-recent", "fixtures/key-event-compromise-recent.json", "Registration bound falls between the claimed start and the event's proved time: `disputed`."),
        ("compromise-early", "fixtures/key-event-compromise-early.json", "An early-dated claim is clamped to the look-back window: the honest registration stays `trusted`."),
        ("event-unauthorized", "aux/key-event-by-other-key.json", "An event signed by another key is `ignored-unauthorized`."),
    ]:
        write("fixtures", f"verification-result-{name}", fixture("verification-result", desc, result_for(B3, events=[rel]), keyEvents=[rel], **rmeta))

    link = {"linkVersion": C.LINK_VERSION, "report": {"path": REPORT, "bodySha256": C.sha(C.jcs(REPORT_BODY))},
            "registration": {"bundle": B3, "statementSha256": C.sha(C.jcs(st))},
            "links": [{"pair": 0, "role": "reference", "subjectIndex": 0, "sha256": C.sha(ARTIFACT)}],
            "catalogueOpening": {"catalogue": CATALOGUE_SRC, "nonceHex": CAT_NONCE.hex()}, "notShown": C.NOT_SHOWN}
    write("fixtures", "report-link", fixture("report-link", "Links the committed example comparison report to the registration, without changing the report.", link))
    ren = {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result.json", "lines": render(result)}
    write("fixtures", "rendering", fixture("rendering", "User-facing text built only from the allowed templates.", ren))

    env2, sigs2 = envelope(statement(NONCE_2, ARTIFACT_2, "host.go"))
    write("fixtures", "bundle-second-work", fixture("bundle", "A second registration by the same creator, fresh nonce.",
                                                    bundle_of(env2, [tsa(sigs2[0], "a", "2026-11-23T11:00:00Z"), ots(sigs2[0])])))
    write("fixtures", "registration-set", fixture("registration-set", "Two registrations by one producer: nonces differ.",
                                                  {"setVersion": C.SET_VERSION, "registrations": [B3, "fixtures/bundle-second-work.json"]}))

    build_negatives(st, sig, result, rmeta, link, ren, res_co, recent)
    build_agent(sig, result)


def build_negatives(st, sig, result, rmeta, link, ren, res_co, recent):
    neg = lambda name, doc: write("negative", f"neg-{name}", doc)

    bad = copy.deepcopy(link)
    bad["links"][0]["sha256"] = REPORT_BODY["pairs"][0]["candidate"]["sha256"]
    neg("subject-mismatch", fixture("report-link", "Links the candidate's digest instead of the registered reference.", bad, "subject-mismatch"))
    wrong = tsa(sig, "a")
    wrong["target"]["sha256"] = C.sha(C.jcs(st))
    neg("evidence-wrong-target", fixture("evidence", "Token over the statement bytes, not over the signature.", wrong, "evidence-wrong-target", bundle=B3))
    wrong = tsa(sig, "a")
    wrong["target"]["sha256"] = C.sha(base64.b64encode(sig))
    neg("evidence-target-base64", fixture("evidence", "Token over the base64 text of the signature, not its raw bytes (A1).", wrong, "evidence-wrong-target", bundle=B3))
    r = copy.deepcopy(result)
    r["outcomes"]["time"][0]["notAfterAnyRoot"] = "2026-11-20T09:00:00Z"
    neg("claimed-as-proved", fixture("verification-result", "Claimed creation time reported as the earliest bound.", r, "claimed-as-proved", **rmeta))
    for i, line in enumerate(["This registration proves you are the author of sum.go.",
                              "This registration establishes your claim to sum.go.", "sum.go is registered to you as its creator.",
                              "This record proves you wrote sum.go.", f"Registered first: sum.go belongs to key {KEYID}."]):
        rb = copy.deepcopy(ren)
        rb["lines"].insert(1, line)
        neg(f"authorship-claim-{i}", fixture("rendering", f"Rendering adds: {line}", rb, "authorship-claim", ["rendering-unlisted-line"]))
    rb = copy.deepcopy(ren)
    rb["lines"].insert(1, "Thank you for registering with Traceweave.")
    neg("rendering-unlisted-line", fixture("rendering", "A harmless line outside the template list is still refused.", rb, "rendering-unlisted-line"))
    rb = copy.deepcopy(ren)
    rb["lines"] = rb["lines"][:-2]
    neg("notice-missing", fixture("rendering", "Rendering without the two fixed limit sentences.", rb, "notice-missing"))
    rb = {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result-cosigned.json", "lines": render(res_co)}
    rb["lines"] = [l.replace(f"No proved time for key {KEYID_CO}.", f"This record shows that the content existed, and that key {KEYID_CO} signed a statement naming it, no later than 2026-11-23T10:00:01Z (according to one time source only).") for l in rb["lines"]]
    neg("key-bound-misattributed-rendering", fixture("rendering", "The co-signer is given the first signature's bound (W8).", rb, "key-bound-misattributed"))
    r = copy.deepcopy(res_co)
    r["outcomes"]["time"][1].update({k: res_co["outcomes"]["time"][0][k] for k in ("notAfterAnyRoot", "notAfterQuorum", "outcome")})
    neg("key-bound-misattributed", fixture("verification-result", "A later co-signature inherits the earlier signature's bound (W8).", r,
                                           "key-bound-misattributed", bundle="fixtures/bundle-cosigned.json", artifacts=ART))
    r = copy.deepcopy(result_for(B3, events=["fixtures/key-event-compromise-recent.json"]))
    r["outcomes"]["signerTrust"][0]["outcome"] = "trusted"
    neg("key-event-ignored", fixture("verification-result", "A compromise event covering the bound is ignored; signer still `trusted` (W10).", r,
                                     "key-event-ignored", keyEvents=["fixtures/key-event-compromise-recent.json"], **rmeta))
    r = copy.deepcopy(result)
    r["outcomes"]["authentic"] = True
    neg("single-verdict", fixture("verification-result", "Adds a single 'authentic' verdict.", r, "single-verdict", **rmeta))
    tampered = copy.deepcopy(st)
    tampered["predicate"]["claims"]["createdAt"] = "2026-01-01T00:00:00Z"
    env_t, sigs_t = envelope(st, payload_override=C.jcs(tampered))
    neg("signature-invalid", fixture("bundle", "Claimed time edited after signing.", bundle_of(env_t, [tsa(sigs_t[0])]), "signature-invalid"))
    unl = tsa(sig, "a")
    unl["notice"] = "RFC 3161 time-stamp token issued by the TSA."
    neg("placeholder-unlabelled", fixture("evidence", "Placeholder presented as a real token.", unl, "placeholder-unlabelled", bundle=B3))
    neg("pending-counted", fixture("evidence", "A pending proof that states a block time.",
                                   evidence("opentimestamps", sig, "btc", {"status": "pending", "blockTime": "2026-11-23T11:12:00Z"}), "pending-counted", bundle=B3))
    lt = rekor(sig)
    lt["statedTime"] = {"genTime": "2026-11-23T10:00:00Z"}
    neg("log-time-claimed", fixture("evidence", "Rekor v2 placeholder that claims a time.", lt, "log-time-claimed", bundle=B3))
    lab = tsa(sig, "a")
    lab["root"] = {"kind": "tsa-certificate-chain", "id": "my-favourite-tsa"}
    neg("root-not-anchored", fixture("evidence", "Root named by a producer-written label instead of a trust anchor (W3).", lab, "root-not-anchored", bundle=B3))
    nm = tsa(sig, "a", nonce="5a17c0de000000ff")
    neg("tsa-nonce-mismatch", fixture("evidence", "Token nonce differs from the request nonce: a possibly replayed response.", nm, "tsa-nonce-mismatch", bundle=B3))
    shp = tsa(sig, "a")
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
    resigned("predicate-type", "Draft-1 predicate type.", "predicate-type",
             **{"predicateType": "https://traceweave.org/predicate/registration/draft-1"})
    resigned("provenance-shape", "Implementation commit is not an object id (B10).", "provenance-shape", **{"predicate.implementation.commit": "main"})
    resigned("statement-shape", "Unknown predicate field.", "statement-shape", **{"predicate.licence": "all rights reserved"})
    b, _ = three_roots()
    b["envelope"]["payloadType"] = "application/json"
    neg("envelope-shape", fixture("bundle", "Wrong DSSE payload type.", b, "envelope-shape"))

    r = copy.deepcopy(result)
    r["outcomes"]["time"][0]["distinctRoots"] = 4
    neg("quorum-miscount", fixture("verification-result", "The Rekor entry, which has no time, counted as a fourth root.", r, "quorum-miscount", **rmeta))
    env_s, sigs_s = envelope(st)
    write("aux", "bundle-same-anchor", fixture("bundle", "Two TSA tokens under one trust anchor.",
                                               bundle_of(env_s, [tsa(sigs_s[0], "a"), tsa(sigs_s[0], "a", "2026-11-23T10:00:30Z")])))
    r = result_for("aux/bundle-same-anchor.json")
    r["outcomes"]["time"][0].update(distinctRoots=2, outcome="quorum-met", notAfterQuorum="2026-11-23T10:00:31Z")
    neg("quorum-same-anchor", fixture("verification-result", "Two tokens under one CA counted as two roots (W3).", r, "quorum-miscount",
                                      bundle="aux/bundle-same-anchor.json", artifacts=ART))
    r = copy.deepcopy(result_for(B3, events=["fixtures/key-event-compromise-recent.json"]))
    r["outcomes"]["claimedCreatedAt"]["status"] = "proved"
    neg("result-mismatch", fixture("verification-result", "An outcome value outside the closed list.", r, "result-mismatch",
                                   keyEvents=["fixtures/key-event-compromise-recent.json"], **rmeta))
    r = result_for(B3, artifacts=[])
    r["outcomes"]["subjects"][0]["outcome"] = "match"
    neg("subject-unsupplied-match", fixture("verification-result", "Reports `match` without the file (W6b).", r, "result-mismatch", bundle=B3))
    noacc = copy.deepcopy(POLICY)
    del noacc["timeRoots"][1]["accuracySeconds"]
    r = result_for(B3, noacc)
    r["outcomes"]["timeEvidence"][1]["outcome"] = "placeholder-assumed-valid"
    neg("accuracy-assumed", fixture("verification-result", "A token without accuracy, and none in policy, counted anyway (A3).", r, "result-mismatch", **rmeta))
    env_c, sigs_c = envelope(st)
    write("aux", "bundle-cert-expired", fixture("bundle", "TSA A's signing certificate expired before genTime.", bundle_of(env_c, [
        tsa(sigs_c[0], "a", signerCertificate={"notBefore": "2025-01-01T00:00:00Z", "notAfter": "2026-06-30T00:00:00Z"}), ots(sigs_c[0])])))
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
    raw = json.dumps(fixture("statement", "Duplicate key.", st), indent=2)
    (HERE / "negative" / "neg-duplicate-key.json").write_text(raw.replace('"contentKind": "source-code",', '"contentKind": "source-code",\n      "contentKind": "text",', 1), encoding="utf-8")


# ------------------------------------------------------------------ agent fixtures (design section 19)

EXT = {"uri": C.A2A_EXTENSION, "description": "Traceweave registration profile (proposed; not published).", "required": True}


def hosted_card(**changes):
    card = {
        "name": "Traceweave witness (illustrative)",
        "description": "Illustrative only; no such service exists. Receives the SHA-256 of a creator's DSSE signature, never content or fingerprints, and returns a signed, time-stamped witness statement. " + LIMIT,
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
            "description": "Records that the authenticated caller presented this signature digest at the witness's receipt time, signs a witness statement and attaches time evidence. It does not register content, check authorship or check originality. " + LIMIT,
            "tags": ["traceweave", "registration", "witness", "timestamp"],
            "examples": ['{"requestVersion": "traceweave-witness-request-draft-1", "presented": {"kind": "dsse-signature-sha256", "sha256": "<64 hex>"}}'],
            "inputModes": ["application/json"], "outputModes": ["application/json"]}],
    }
    card.update(changes)
    return card


def local_card():
    return {
        "name": "Traceweave local registrar (illustrative)",
        "description": "Illustrative only. Runs on the creator's machine, on loopback. Signs with the creator's own key and requests time evidence; only a signature digest leaves the machine. " + LIMIT,
        "supportedInterfaces": [{"url": "http://127.0.0.1:8765/a2a/v1", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
        "version": "0.0.0-illustrative",
        "capabilities": {"streaming": True, "pushNotifications": False, "extensions": [dict(EXT, params={"wire": "local-only"})]},
        "defaultInputModes": ["application/json"], "defaultOutputModes": ["application/json"],
        "skills": [
            {"id": "register", "name": "Register files at creation", "tags": ["traceweave", "registration"],
             "description": "Registers local files by path: hashes them, signs a registration statement with the creator key held by this tool, and requests time evidence. " + LIMIT},
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
    pred = {"witnessVersion": C.WITNESS_VERSION, "presentedKind": "dsse-signature-sha256", "receivedAt": "2026-11-23T10:00:02Z",
            "caller": {"scheme": "openIdConnect", "issuer": "https://issuer.example.invalid", "subject": "placeholder-subject-0001"},
            "requestMessageId": "0f6c2a8e-illustrative-0001", "notShown": C.NOT_SHOWN}
    pred.update(pred_changes)
    st = {"_type": C.STATEMENT_TYPE, "subject": [{"name": "presented-digest", "digest": {"sha256": presented}}],
          "predicateType": C.WITNESS_TYPE, "predicate": pred}
    env, wsigs = envelope(st, signers=((SEED_WITNESS, C.keyid(WITNESS_PUB)),))
    wb = bundle_of(env, [tsa(wsigs[0], "a", "2026-11-23T10:00:03Z")], keys=((WITNESS_PUB, C.keyid(WITNESS_PUB)),))
    return {"id": "task-illustrative-0001", "contextId": "ctx-illustrative-0001", "status": {"state": "TASK_STATE_COMPLETED"},
            "artifacts": [{"artifactId": "witness-0001", "name": "witness statement", "parts": [{"data": wb, "mediaType": "application/json"}]}]}


def mcp_tool(**changes):
    tool = {
        "name": "traceweave_register",
        "title": "Register files with Traceweave (illustrative)",
        "description": "Registers local files at creation time: hashes them, signs a registration statement with the creator key held by this local server, and requests time evidence. Only a signature digest leaves the machine. " + LIMIT,
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
    write("fixtures", "a2a-task-witness", fixture("a2a-task", "Completed task: one artifact holding the signed witness statement and an RFC 3161 placeholder over the witness signature.",
                                                   witness_task(presented), request="fixtures/a2a-request-witness.json"))
    write("fixtures", "mcp-tool-register", fixture("mcp-tool", "Illustrative MCP 2026-07-28 Tool for the local route.", mcp_tool()))
    wline = "Witnessed: the caller placeholder-subject-0001 presented the signature digest at 2026-11-23T10:00:02Z by the witness's clock."
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
