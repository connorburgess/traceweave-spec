#!/usr/bin/env python3
"""Rebuild the illustrative registration fixtures (fixtures/ and negative/).

Standard library only. Deterministic: Ed25519 signatures are deterministic, and
every nonce and key below is derived from a fixed public label. The key is a
public test-only key; never use it, or these nonces, for anything real.

Sources (committed elsewhere in this repository, read only):
  - the artifact `sum.go`: test-vectors/matching/extraction-go.json, vector mv-go-sum;
  - its reference catalogue: test-vectors/matching/matching.json, vector 1 reference canonical;
  - the comparison report: test-vectors/matching/example-report.json;
  - the catalogue nonce: test-vectors/commitment.json (a public synthetic nonce).

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

SEED = hashlib.sha256(b"traceweave registration fixture test key; public; never use").digest()
SEED_NEXT = hashlib.sha256(b"traceweave registration fixture successor test key; public; never use").digest()
NONCE = hashlib.sha256(b"traceweave registration fixture nonce; public; never use").hexdigest()
PUB, PUB_NEXT = C.ed25519_public(SEED), C.ed25519_public(SEED_NEXT)
KEYID, KEYID_NEXT = C.keyid(PUB), C.keyid(PUB_NEXT)

ARTIFACT_SRC = "test-vectors/matching/extraction-go.json#mv-go-sum"
CATALOGUE_SRC = "test-vectors/matching/matching.json#/vectors/1/reference/canonical"
REPORT = "test-vectors/matching/example-report.json"
ARTIFACT = C.load_source(ARTIFACT_SRC)
CATALOGUE = C.load_source(CATALOGUE_SRC)
CAT_NONCE = bytes.fromhex(json.loads((C.ROOT / "test-vectors/commitment.json").read_text())["nonceHex"])
REPORT_BODY = json.loads((C.ROOT / REPORT).read_text())["body"]
ZERO40 = "0" * 40


def statement(**changes):
    st = {
        "_type": C.STATEMENT_TYPE,
        "subject": [{"name": "sum.go", "digest": {"sha256": C.sha(ARTIFACT)}}],
        "predicateType": C.PREDICATE_TYPE,
        "predicate": {
            "registrationVersion": C.REGISTRATION_VERSION,
            "contentKind": "source-code",
            "nonce": NONCE,
            "possession": [{"subjectIndex": 0, "scheme": C.POSSESSION_SCHEME, "sha256": C.possession_digest(NONCE, ARTIFACT)}],
            "catalogue": {"scheme": C.CATALOGUE_SCHEME, "sha256": C.catalogue_commitment(CAT_NONCE, CATALOGUE),
                          "profile": REPORT_BODY["profile"]},
            "implementation": {"name": "build_fixtures.py", "version": "draft-1", "commit": ZERO40},
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


DELETE = object()


def envelope(st, seed=SEED, kid=KEYID, payload_override=None):
    payload = C.jcs(st)
    sig = C.ed25519_sign(seed, C.pae(C.PAYLOAD_TYPE, payload))
    body = payload_override if payload_override is not None else payload
    return {"payloadType": C.PAYLOAD_TYPE, "payload": base64.b64encode(body).decode(),
            "signatures": [{"keyid": kid, "sig": base64.b64encode(sig).decode()}]}, sig


def evidence(kind, sig, **extra):
    roots = {"rfc3161": "placeholder-tsa-a", "opentimestamps": "bitcoin-mainnet", "rekor-v2": "placeholder-log-2026",
             "cosigned-checkpoint": "placeholder-witness-a"}
    ev = {"evidenceVersion": C.EVIDENCE_VERSION, "type": kind, "placeholder": True, "notice": C.PLACEHOLDER_NOTICE,
          "target": {"kind": "dsse-signature", "signatureIndex": 0, "sha256": C.sha(sig)},
          "root": {"kind": C.EVIDENCE_ROOT[kind], "id": roots[kind]},
          "token": f"PLACEHOLDER-NOT-A-{kind.upper()}-OBJECT"}
    ev.update(extra)
    return ev


def ev_rfc3161(sig):
    return evidence("rfc3161", sig, statedTime={"genTime": "2026-11-23T10:00:00Z", "accuracySeconds": 1})


def ev_ots(sig):
    return evidence("opentimestamps", sig, status="complete", statedTime={"blockTime": "2026-11-23T11:12:00Z"})


def bundle(st=None, evidences=None, env=None, sig=None, keys=None):
    if env is None:
        env, sig = envelope(st or statement())
    evs = evidences(sig) if evidences else [ev_rfc3161(sig), ev_ots(sig), evidence("rekor-v2", sig, logIndex=0)]
    return {"bundleVersion": C.BUNDLE_VERSION, "envelope": env,
            "verificationMaterial": {"publicKeys": keys or [{"keyid": KEYID, "alg": "ed25519", "publicKeyHex": PUB.hex()}]},
            "timeEvidence": evs}


def fixture(kind, description, obj, expect=None, **meta):
    m = {"kind": kind, "description": description, "notice": C.FIXTURE_NOTICE}
    m.update(meta)
    if expect:
        m["expect"] = {"code": expect}
    return {"fixture": m, "object": obj}


ART = [{"subjectIndex": 0, "source": ARTIFACT_SRC}]
POLICY = {"quorum": 2, "acceptedRoots": ["bitcoin-mainnet", "placeholder-log-2026", "placeholder-tsa-a"], "trustedKeyids": [KEYID]}


def write(folder, name, doc):
    (HERE / folder).mkdir(exist_ok=True)
    (HERE / folder / f"{name}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build():
    for folder in ("fixtures", "negative"):
        for old in (HERE / folder).glob("*.json"):
            old.unlink()
    st = statement()
    env, sig = envelope(st)
    two = bundle()
    write("fixtures", "statement", fixture("statement", "The registration statement (in-toto Statement v1) before signing.", st, artifacts=ART))
    write("fixtures", "bundle-two-roots", fixture(
        "bundle", "Signed statement with an RFC 3161 placeholder, a complete OpenTimestamps placeholder and a Rekor v2 placeholder (no time).",
        two, artifacts=ART))
    write("fixtures", "evidence-rfc3161", fixture("evidence", "RFC 3161 token placeholder over the DSSE signature.", ev_rfc3161(sig), bundle="fixtures/bundle-two-roots.json"))
    write("fixtures", "evidence-opentimestamps-complete", fixture("evidence", "Upgraded OpenTimestamps proof placeholder.", ev_ots(sig), bundle="fixtures/bundle-two-roots.json"))
    write("fixtures", "evidence-opentimestamps-pending", fixture(
        "evidence", "OpenTimestamps proof before upgrade: calendar commitments only, so no time.",
        evidence("opentimestamps", sig, status="pending"), bundle="fixtures/bundle-two-roots.json"))
    write("fixtures", "evidence-rekor-v2", fixture("evidence", "Rekor v2 inclusion placeholder; carries no time of its own.", evidence("rekor-v2", sig, logIndex=0), bundle="fixtures/bundle-two-roots.json"))
    write("fixtures", "evidence-cosigned-checkpoint", fixture(
        "evidence", "Witness-cosigned checkpoint placeholder; the cosignature time is the witness's clock.",
        evidence("cosigned-checkpoint", sig, statedTime={"cosignatureTime": "2026-11-23T10:05:00Z"}), bundle="fixtures/bundle-two-roots.json"))

    bundle_sha = C.sha((HERE / "fixtures/bundle-two-roots.json").read_bytes())
    ctx = C.check_bundle(two, {0: ARTIFACT}, set())
    result = C.expected_result(ctx, {0: ARTIFACT}, POLICY, True, bundle_sha)
    rmeta = {"bundle": "fixtures/bundle-two-roots.json", "artifacts": ART}
    write("fixtures", "verification-result", fixture(
        "verification-result", "Expected verifier output for bundle-two-roots and sum.go, with placeholders assumed valid (simulated).", result, **rmeta))

    link = {"linkVersion": C.LINK_VERSION,
            "report": {"path": REPORT, "bodySha256": C.sha(C.jcs(REPORT_BODY))},
            "registration": {"bundle": "fixtures/bundle-two-roots.json", "statementSha256": C.sha(C.jcs(st))},
            "links": [{"pair": 0, "role": "reference", "subjectIndex": 0, "sha256": C.sha(ARTIFACT)}],
            "catalogueOpening": {"catalogue": CATALOGUE_SRC, "nonceHex": CAT_NONCE.hex()},
            "notShown": C.NOT_SHOWN}
    write("fixtures", "report-link", fixture("report-link", "Links the committed example comparison report to the registration, without changing the report.", link))

    t = result["outcomes"]["time"]
    lines = [
        "Registration of sum.go (SHA-256 974c8d0a…697c).",
        "Content digest: matches the file you supplied.",
        f"Signature: valid; signer key {KEYID} is trusted under your policy.",
        f"Existed no later than {t['notAfterQuorum']} (agreed by 2 independent time sources); one source alone says {t['notAfterAnyRoot']}.",
        f"Creation time claimed by the registrant, not proved: {result['outcomes']['claimedCreatedAt']['value']}.",
        "Each result above was checked separately.",
        *C.REQUIRED_SENTENCES,
    ]
    ren = {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result.json", "lines": lines}
    write("fixtures", "rendering", fixture("rendering", "User-facing text for the verification result, with the required statement of limits.", ren))

    ke = {"_type": C.STATEMENT_TYPE, "subject": [{"name": "key", "digest": {"sha256": C.sha(PUB)}}],
          "predicateType": C.KEY_EVENT_TYPE,
          "predicate": {"eventVersion": C.KEY_EVENT_VERSION, "keyid": KEYID, "event": "rotated", "successorPublicKeyHex": PUB_NEXT.hex()}}
    ke_env, ke_sig = envelope(ke)
    ke_bundle = bundle(env=ke_env, sig=ke_sig, evidences=lambda s: [ev_rfc3161(s)])
    write("fixtures", "key-event-rotation", fixture("key-event", "The old key names its successor; time-stamped like a registration.", ke_bundle))

    # ---------------------------------------------------------------- negatives
    neg = lambda name, doc: write("negative", f"neg-{name}", doc)
    bad = copy.deepcopy(link)
    bad["links"][0]["sha256"] = REPORT_BODY["pairs"][0]["candidate"]["sha256"]
    neg("subject-mismatch", fixture("report-link", "Links the registration to the candidate's digest instead of the registered reference.", bad, "subject-mismatch"))
    wrong = ev_rfc3161(sig)
    wrong["target"]["sha256"] = C.sha(C.jcs(st))
    neg("evidence-wrong-target", fixture("evidence", "Token over the statement bytes, not over the signature it claims to cover.", wrong, "evidence-wrong-target", bundle="fixtures/bundle-two-roots.json"))
    r = copy.deepcopy(result)
    r["outcomes"]["time"]["notAfterAnyRoot"] = "2026-11-20T09:00:00Z"
    neg("claimed-as-proved", fixture("verification-result", "The registrant's claimed creation time reported as the proved bound.", r, "claimed-as-proved", **rmeta))
    ren_bad = copy.deepcopy(ren)
    ren_bad["lines"][5] = "This registration proves you are the author of sum.go."
    neg("authorship-claim", fixture("rendering", "Rendering that presents the registration as proof of authorship.", ren_bad, "authorship-claim"))
    ren_bad = copy.deepcopy(ren)
    ren_bad["lines"] = ren_bad["lines"][:-2]
    neg("notice-missing", fixture("rendering", "Rendering without the statement of what a registration does not show.", ren_bad, "notice-missing"))
    r = copy.deepcopy(result)
    r["outcomes"]["authentic"] = True
    neg("single-verdict", fixture("verification-result", "Adds a single 'authentic' verdict on top of the separate outcomes.", r, "single-verdict", **rmeta))
    tampered = copy.deepcopy(st)
    tampered["predicate"]["claims"]["createdAt"] = "2026-01-01T00:00:00Z"
    env_t, sig_t = envelope(st, payload_override=C.jcs(tampered))
    neg("signature-invalid", fixture("bundle", "Claimed time edited after signing; the signature no longer verifies.", bundle(env=env_t, sig=sig_t), "signature-invalid"))
    unl = ev_rfc3161(sig)
    unl["notice"] = "RFC 3161 time-stamp token issued by the TSA."
    neg("placeholder-unlabelled", fixture("evidence", "Placeholder presented as a real token.", unl, "placeholder-unlabelled", bundle="fixtures/bundle-two-roots.json"))
    pend = evidence("opentimestamps", sig, status="pending", statedTime={"blockTime": "2026-11-23T11:12:00Z"})
    neg("pending-counted", fixture("evidence", "A pending OpenTimestamps proof that states a block time it does not have yet.", pend, "pending-counted", bundle="fixtures/bundle-two-roots.json"))
    neg("log-time-claimed", fixture("evidence", "Rekor v2 placeholder that claims a time; Rekor v2 has none.",
                                    evidence("rekor-v2", sig, logIndex=0, statedTime={"genTime": "2026-11-23T10:00:00Z", "accuracySeconds": 1}),
                                    "log-time-claimed", bundle="fixtures/bundle-two-roots.json"))

    def resigned(name, desc, code, **changes):
        neg(name, fixture("bundle", desc, bundle(st=statement(**changes)), code, artifacts=ART))

    resigned("catalogue-unsalted", "Publishes the plain catalogue digest, which confirms a guessed catalogue.", "catalogue-unsalted",
             **{"predicate.catalogue.scheme": "sha256", "predicate.catalogue.sha256": C.sha(CATALOGUE)})
    resigned("forbidden-field", "Puts fingerprints into the statement.", "forbidden-field",
             **{"predicate.fingerprints": ["9f3a52c1d07e4b21"]})
    resigned("nonce-invalid", "All-zero nonce: the statement becomes guessable.", "nonce-invalid",
             **{"predicate.nonce": "0" * 64})
    resigned("subject-name", "A path as subject name discloses the private directory layout.", "subject-name",
             **{"subject.0.name": "private/drafts/sum.go"})
    resigned("time-in-statement", "The registrant writes a 'provedAt' time into its own statement.", "time-in-statement",
             **{"predicate.provedAt": "2026-11-01T00:00:00Z"})
    resigned("possession-mismatch", "Possession digest computed without the file (copied from elsewhere).", "possession-mismatch",
             **{"predicate.possession.0.sha256": C.sha(b"not computed from the content")})
    resigned("predicate-type", "Uses the evidence predicate type instead of the registration one.", "predicate-type",
             **{"predicateType": "https://github.com/connorburgess/traceweave-spec/blob/main/spec/core.md#evidence-0.1.0-draft.1"})
    resigned("provenance-shape", "Implementation commit is not a 40-digit object id (B10).", "provenance-shape",
             **{"predicate.implementation.commit": "main"})
    r = copy.deepcopy(result)
    r["outcomes"]["timeEvidence"].append(dict(r["outcomes"]["timeEvidence"][0], index=3))
    r["outcomes"]["time"].update(distinctRoots=3)
    neg("quorum-miscount", fixture("verification-result", "A second token from the same TSA counted as another independent root.", r, "quorum-miscount", **rmeta))
    r = copy.deepcopy(result)
    r["outcomes"]["claimedCreatedAt"]["status"] = "proved"
    neg("result-mismatch", fixture("verification-result", "An outcome value outside the closed list.", r, "result-mismatch", **rmeta))
    bad = copy.deepcopy(link)
    bad["catalogueOpening"]["nonceHex"] = "ff" * 32
    neg("catalogue-does-not-open", fixture("report-link", "Wrong nonce: the disclosed catalogue does not open the commitment.", bad, "catalogue-does-not-open"))
    bad = copy.deepcopy(link)
    bad["registration"]["statementSha256"] = C.sha(b"another statement")
    neg("statement-digest", fixture("report-link", "The link names a different statement.", bad, "statement-digest"))
    ke_bad = copy.deepcopy(ke)
    del ke_bad["predicate"]["successorPublicKeyHex"]
    e2, s2 = envelope(ke_bad)
    neg("key-event-shape", fixture("key-event", "Rotation without naming the successor key.", bundle(env=e2, sig=s2, evidences=lambda s: [ev_rfc3161(s)]), "key-event-shape"))
    shapeless = ev_rfc3161(sig)
    del shapeless["statedTime"]["accuracySeconds"]
    neg("evidence-shape", fixture("evidence", "RFC 3161 placeholder without its accuracy, so no upper bound can be computed.", shapeless, "evidence-shape", bundle="fixtures/bundle-two-roots.json"))
    b = bundle()
    b["envelope"]["payloadType"] = "application/json"
    neg("envelope-shape", fixture("bundle", "Wrong DSSE payload type.", b, "envelope-shape"))
    resigned("statement-shape", "Unknown predicate field 'licence'.", "statement-shape", **{"predicate.licence": "all rights reserved"})
    raw = json.dumps(fixture("statement", "Duplicate key.", st), indent=2)
    (HERE / "negative" / "neg-duplicate-key.json").write_text(raw.replace('"contentKind": "source-code",', '"contentKind": "source-code",\n      "contentKind": "text",', 1), encoding="utf-8")

    build_agent(sig)


WITNESS_SEED = hashlib.sha256(b"traceweave witness fixture test key; public; never use").digest()
WITNESS_PUB = C.ed25519_public(WITNESS_SEED)
LIMIT = C.REQUIRED_SENTENCES[2]
EXT = {"uri": C.A2A_EXTENSION, "description": "Traceweave registration profile (proposed; not published).", "required": True}


def hosted_card(**changes):
    card = {
        "name": "Traceweave witness (illustrative)",
        "description": "Illustrative only; no such service exists. Receives the SHA-256 of a creator's DSSE signature, never content or fingerprints, and returns a signed, time-stamped witness statement. " + LIMIT,
        "supportedInterfaces": [{"url": "https://witness.example.invalid/a2a/v1", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
        "provider": {"organization": "Traceweave (illustrative; no operator exists)", "url": "https://traceweave.org"},
        "version": "0.0.0-illustrative",
        "capabilities": {"streaming": False, "pushNotifications": False,
                         "extensions": [dict(EXT, params={"wire": "digests-only"})]},
        "securitySchemes": {"oidc": {"openIdConnectSecurityScheme": {"openIdConnectUrl": "https://issuer.example.invalid/.well-known/openid-configuration"}}},
        "securityRequirements": [{"schemes": {"oidc": {"list": ["openid"]}}}],
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [{
            "id": "witness-digest",
            "name": "Witness a registration digest",
            "description": "Records that the authenticated caller presented this signature digest at the witness's receipt time, signs a witness statement and attaches time evidence. It does not register content, check authorship or check originality. " + LIMIT,
            "tags": ["traceweave", "registration", "witness", "timestamp"],
            "examples": ['{"requestVersion": "traceweave-witness-request-draft-1", "presented": {"kind": "dsse-signature-sha256", "sha256": "<64 hex>"}}'],
            "inputModes": ["application/json"],
            "outputModes": ["application/json"],
        }],
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
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
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
    parts = [{"data": data, "mediaType": "application/json"}] + (parts_extra or [])
    return {"message": {"messageId": "0f6c2a8e-illustrative-0001", "role": "ROLE_USER", "parts": parts, "extensions": [C.A2A_EXTENSION]}}


def witness_task(presented, **pred_changes):
    pred = {"witnessVersion": C.WITNESS_VERSION, "presentedKind": "dsse-signature-sha256", "receivedAt": "2026-11-23T10:00:02Z",
            "caller": {"scheme": "openIdConnect", "issuer": "https://issuer.example.invalid", "subject": "placeholder-subject-0001"},
            "requestMessageId": "0f6c2a8e-illustrative-0001", "notShown": C.NOT_SHOWN}
    pred.update(pred_changes)
    st = {"_type": C.STATEMENT_TYPE, "subject": [{"name": "presented-digest", "digest": {"sha256": presented}}],
          "predicateType": C.WITNESS_TYPE, "predicate": pred}
    env, wsig = envelope(st, seed=WITNESS_SEED, kid=C.keyid(WITNESS_PUB))
    wb = {"bundleVersion": C.BUNDLE_VERSION, "envelope": env,
          "verificationMaterial": {"publicKeys": [{"keyid": C.keyid(WITNESS_PUB), "alg": "ed25519", "publicKeyHex": WITNESS_PUB.hex()}]},
          "timeEvidence": [ev_rfc3161(wsig)]}
    return {"id": "task-illustrative-0001", "contextId": "ctx-illustrative-0001", "status": {"state": "TASK_STATE_COMPLETED"},
            "artifacts": [{"artifactId": "witness-0001", "name": "witness statement",
                           "parts": [{"data": wb, "mediaType": "application/json"}]}]}


def mcp_tool(**changes):
    tool = {
        "name": "traceweave_register",
        "title": "Register files with Traceweave (illustrative)",
        "description": "Registers local files at creation time: hashes them, signs a registration statement with the creator key held by this local server, and requests time evidence. Only a signature digest leaves the machine. " + LIMIT,
        "inputSchema": {"type": "object", "additionalProperties": False, "required": ["paths"],
                        "properties": {"paths": {"type": "array", "minItems": 1, "maxItems": 64, "items": {"type": "string"}},
                                       "claimedCreatedAt": {"type": "string", "description": "Optional claimed creation time; never shown as proved."}}},
        "outputSchema": {"type": "object", "required": ["bundleId", "statementSha256", "timeEvidence"],
                         "properties": {"bundleId": {"type": "string", "description": "Opaque id of the bundle in the private store; never a path (SK.2)."}, "statementSha256": {"type": "string"},
                                        "timeEvidence": {"type": "array", "items": {"type": "object"}}}},
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    }
    tool.update(changes)
    return tool


def build_agent(sig):
    presented = C.sha(sig)
    agent_meta = {"bundle": "fixtures/bundle-two-roots.json"}
    write("fixtures", "a2a-card-hosted-witness", fixture("a2a-agent-card", "Illustrative A2A 1.0 Agent Card for a hosted witness (architecture b). Checked against the a2a.proto field lists only.", hosted_card()))
    write("fixtures", "a2a-card-local-registrar", fixture("a2a-agent-card", "Illustrative A2A 1.0 Agent Card for a local registrar on loopback (architecture a).", local_card()))
    write("fixtures", "a2a-request-witness", fixture("a2a-request", "SendMessageRequest to the witness: one data part with the signature digest.", witness_request(presented), **agent_meta))
    write("fixtures", "a2a-task-witness", fixture("a2a-task", "Completed task: one artifact holding the signed witness statement and an RFC 3161 placeholder over the witness signature.",
                                                   witness_task(presented), request="fixtures/a2a-request-witness.json"))
    write("fixtures", "mcp-tool-register", fixture("mcp-tool", "Illustrative MCP 2026-07-28 Tool for the local route.", mcp_tool()))
    ren = {"renderingVersion": C.RENDERING_VERSION, "result": "fixtures/verification-result.json", "context": "agent",
           "lines": ["Registration of sum.go, made through an agent; signed by key " + KEYID + ".",
                     "Witnessed: the caller placeholder-subject-0001 presented the signature digest at 2026-11-23T10:00:02Z by the witness's clock.",
                     *C.REQUIRED_SENTENCES, C.AGENT_SENTENCE]}
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
    neg("mcp-tool-shape", fixture("mcp-tool", "Registration tool that declares itself closed-world and idempotent.",
                                  mcp_tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}), "mcp-tool-shape"))
    ren_bad = dict(ren, lines=ren["lines"][:-1])
    neg("agent-notice-missing", fixture("rendering", "Agent-made registration without the agent sentence.", ren_bad, "notice-missing"))
    ren_bad = dict(ren, lines=[ren["lines"][0], "This shows the agent created sum.go.", *ren["lines"][2:]])
    neg("agent-authorship", fixture("rendering", "Rendering says the agent created the content.", ren_bad, "authorship-claim"))


if __name__ == "__main__":
    build()
    print("built", len(list((HERE / "fixtures").glob("*.json"))), "positive and", len(list((HERE / "negative").glob("*.json"))), "negative fixtures")
