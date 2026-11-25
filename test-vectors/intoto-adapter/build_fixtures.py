#!/usr/bin/env python3
"""Deterministic builder for the Traceweave <-> in-toto adapter fixtures.

Standard library only. Uses public test-only Ed25519 keys derived from fixed
labels; never use any key or nonce here for production signing.

Usage: python3 -I test-vectors/intoto-adapter/build_fixtures.py
"""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_intoto_adapter", HERE / "check_intoto_adapter.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)

NOTICE = (
    "Illustrative fixture for Traceweave M4.5 in-toto Statement v1 / DSSE adapter. "
    "Public test-only keys and synthetic nonces; registers nothing."
)

SEED_TRUSTED = hashlib.sha256(b"traceweave m4.5 intoto adapter trusted test key; public; never use").digest()
SEED_UNTRUSTED = hashlib.sha256(b"traceweave m4.5 intoto adapter untrusted test key; public; never use").digest()

PUB_TRUSTED = C.ed25519_public(SEED_TRUSTED)
PUB_UNTRUSTED = C.ed25519_public(SEED_UNTRUSTED)
SHA_TRUSTED = C.sha256_hex(PUB_TRUSTED)
SHA_UNTRUSTED = C.sha256_hex(PUB_UNTRUSTED)
KID_TRUSTED = SHA_TRUSTED[:16]
KID_UNTRUSTED = SHA_UNTRUSTED[:16]

NONCE_1 = hashlib.sha256(b"traceweave m4.5 intoto fixture nonce 1; public; never use").hexdigest()
NONCE_2 = hashlib.sha256(b"traceweave m4.5 intoto fixture nonce 2; public; never use").hexdigest()
ZERO40 = "0" * 40


def b64(data: bytes, url_safe: bool = False) -> str:
    fn = base64.urlsafe_b64encode if url_safe else base64.b64encode
    return fn(data).decode("ascii")


def sign_raw_payload(
    raw_payload: bytes,
    payload_type: str = C.DSSE_PAYLOAD_TYPE,
    seed: bytes = SEED_TRUSTED,
    kid: str = KID_TRUSTED,
    url_safe: bool = False,
) -> dict:
    sig = C.ed25519_sign(seed, C.dsse_pae(payload_type.encode("utf-8"), raw_payload))
    return {
        "payloadType": payload_type,
        "payload": b64(raw_payload, url_safe=url_safe),
        "signatures": [{"keyid": kid, "sig": b64(sig, url_safe=url_safe)}],
    }


def make_fixture(
    fid: str,
    kind: str,
    description: str,
    envelope: dict,
    artifacts: list[dict] | None = None,
    catalogue_opening: dict | None = None,
    expected_round_trip: dict | None = None,
    expect: dict | None = None,
    public_keys: list[dict] | None = None,
    trusted_keys: list[str] | None = None,
) -> dict:
    if public_keys is None:
        public_keys = [{"keyid": KID_TRUSTED, "alg": "ed25519", "publicKeyHex": PUB_TRUSTED.hex()}]
    if trusted_keys is None:
        trusted_keys = [SHA_TRUSTED]
    doc = {
        "fixtureVersion": "traceweave-intoto-adapter-fixture-v1",
        "id": fid,
        "kind": kind,
        "description": description,
        "notice": NOTICE,
        "envelope": envelope,
        "verificationMaterial": {"publicKeys": public_keys},
        "trustedKeys": trusted_keys,
    }
    if artifacts is not None:
        doc["artifacts"] = artifacts
    if catalogue_opening is not None:
        doc["catalogueOpening"] = catalogue_opening
    if expected_round_trip is not None:
        doc["expectedRoundTrip"] = expected_round_trip
    if expect is not None:
        doc["expect"] = expect
    return doc


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    # Load committed repository inputs.
    core_stmt = json.loads((C.ROOT / "examples/statement.json").read_text(encoding="utf-8"))
    commitment_vec = json.loads((C.ROOT / "test-vectors/commitment.json").read_text(encoding="utf-8"))
    cat_nonce_hex = commitment_vec["nonceHex"]

    sum_go_src = "test-vectors/matching/extraction-go.json#mv-go-sum"
    host_go_src = "test-vectors/matching/extraction-go.json#mv-go-host"
    sum_go_bytes = C.load_source(sum_go_src)
    host_go_bytes = C.load_source(host_go_src)

    matching_vec = json.loads((C.ROOT / "test-vectors/matching/matching.json").read_text(encoding="utf-8"))
    report_body = json.loads((C.ROOT / "test-vectors/matching/example-report.json").read_text(encoding="utf-8"))["body"]
    cat_src = "test-vectors/matching/matching.json#/vectors/1/reference/canonical"
    cat_bytes = C.load_source(cat_src)
    cat_sha = C.catalogue_commitment(bytes.fromhex(cat_nonce_hex), cat_bytes)

    # -------------------------------------------------------------- ACCEPT FIXTURES

    # 1. Core catalogue-commitment statement (canonical JCS payload, standard base64)
    core_bytes = C.jcs(core_stmt)
    accept_core = make_fixture(
        fid="accept-catalogue-core",
        kind="catalogue",
        description="Core catalogue-commitment statement mapped to in-toto Statement v1 in DSSE (canonical JCS payload).",
        envelope=sign_raw_payload(core_bytes),
        artifacts=[{"subjectIndex": 0, "source": "examples/artifact.txt"}],
        catalogue_opening={"source": "examples/catalogue.json", "nonceHex": cat_nonce_hex},
        expected_round_trip={
            "statementSha256": C.sha256_hex(core_bytes),
            "canonicalStatementSha256": C.sha256_hex(core_bytes),
            "record": C.adapter_decode(core_stmt),
        },
    )

    # 2. Core statement with recordedAt, pretty-printed payload bytes & URL-safe base64
    core_recorded = copy.deepcopy(core_stmt)
    core_recorded["predicate"]["recordedAt"] = "2026-11-20T09:00:00Z"
    pretty_bytes = (json.dumps(core_recorded, indent=2) + "\n").encode("utf-8")
    accept_urlsafe = make_fixture(
        fid="accept-catalogue-core-urlsafe",
        kind="catalogue",
        description="Core statement with optional recordedAt, pretty-printed payload bytes, and URL-safe base64 DSSE encoding.",
        envelope=sign_raw_payload(pretty_bytes, url_safe=True),
        artifacts=[{"subjectIndex": 0, "source": "examples/artifact.txt"}],
        catalogue_opening={"source": "examples/catalogue.json", "nonceHex": cat_nonce_hex},
        expected_round_trip={
            "statementSha256": C.sha256_hex(pretty_bytes),
            "canonicalStatementSha256": C.sha256_hex(C.jcs(core_recorded)),
            "record": C.adapter_decode(core_recorded),
        },
    )

    # 3. Registration draft-5 statement with catalogue commitment
    reg_stmt = {
        "_type": C.STATEMENT_TYPE,
        "subject": [{"name": "sum.go", "digest": {"sha256": C.sha256_hex(sum_go_bytes)}}],
        "predicateType": C.REG_PREDICATE_TYPE,
        "predicate": {
            "registrationVersion": C.REG_VERSION,
            "contentKind": "source-code",
            "nonce": NONCE_1,
            "possession": [
                {
                    "subjectIndex": 0,
                    "scheme": C.POSSESSION_SCHEME,
                    "sha256": C.possession_digest(NONCE_1, sum_go_bytes),
                }
            ],
            "catalogue": {
                "scheme": C.CATALOGUE_SCHEME,
                "sha256": cat_sha,
                "profile": copy.deepcopy(report_body["profile"]),
            },
            "implementation": {"name": "build_fixtures.py", "version": "draft-5", "commit": ZERO40},
            "specCommit": ZERO40,
            "claims": {"createdAt": "2026-11-20T09:00:00Z"},
        },
    }
    reg_bytes = C.jcs(reg_stmt)
    accept_reg = make_fixture(
        fid="accept-registration-draft5",
        kind="registration",
        description="Registration draft-5 statement with possession digest and salted catalogue commitment wrapped in DSSE.",
        envelope=sign_raw_payload(reg_bytes),
        artifacts=[{"subjectIndex": 0, "source": sum_go_src}],
        catalogue_opening={"source": cat_src, "nonceHex": cat_nonce_hex},
        expected_round_trip={
            "statementSha256": C.sha256_hex(reg_bytes),
            "canonicalStatementSha256": C.sha256_hex(reg_bytes),
            "record": C.adapter_decode(reg_stmt),
        },
    )

    # 4. Registration draft-5 multi-subject statement with optional claims.aiUse and no catalogue
    reg_ai_stmt = {
        "_type": C.STATEMENT_TYPE,
        "subject": [
            {"name": "sum.go", "digest": {"sha256": C.sha256_hex(sum_go_bytes)}},
            {"name": "host.go", "digest": {"sha256": C.sha256_hex(host_go_bytes)}},
        ],
        "predicateType": C.REG_PREDICATE_TYPE,
        "predicate": {
            "registrationVersion": C.REG_VERSION,
            "contentKind": "source-code",
            "nonce": NONCE_2,
            "possession": [
                {
                    "subjectIndex": 0,
                    "scheme": C.POSSESSION_SCHEME,
                    "sha256": C.possession_digest(NONCE_2, sum_go_bytes),
                },
                {
                    "subjectIndex": 1,
                    "scheme": C.POSSESSION_SCHEME,
                    "sha256": C.possession_digest(NONCE_2, host_go_bytes),
                },
            ],
            "implementation": {"name": "build_fixtures.py", "version": "draft-5", "commit": ZERO40},
            "specCommit": ZERO40,
            "claims": {
                "createdAt": "2026-11-24T12:00:00Z",
                "aiUse": {"declared": "modified", "tool": "ExampleFormatter-1.0"},
            },
        },
    }
    reg_ai_bytes = C.jcs(reg_ai_stmt)
    accept_reg_ai = make_fixture(
        fid="accept-registration-ai-use",
        kind="registration",
        description="Multi-subject registration draft-5 statement with optional self-declared claims.aiUse and omitted catalogue.",
        envelope=sign_raw_payload(reg_ai_bytes),
        artifacts=[
            {"subjectIndex": 0, "source": sum_go_src},
            {"subjectIndex": 1, "source": host_go_src},
        ],
        expected_round_trip={
            "statementSha256": C.sha256_hex(reg_ai_bytes),
            "canonicalStatementSha256": C.sha256_hex(reg_ai_bytes),
            "record": C.adapter_decode(reg_ai_stmt),
        },
    )

    accept_list = [accept_core, accept_urlsafe, accept_reg, accept_reg_ai]

    # -------------------------------------------------------------- REJECT FIXTURES

    def reject_signed_stmt(fid: str, kind: str, desc: str, stmt_obj: dict, code: str, artifacts=None, also=None) -> dict:
        raw = C.jcs(stmt_obj)
        exp = {"code": code}
        if also:
            exp["alsoReported"] = also
        return make_fixture(
            fid=fid,
            kind=kind,
            description=desc,
            envelope=sign_raw_payload(raw),
            artifacts=artifacts,
            expect=exp,
        )

    reject_list = []

    # 1. Wrong _type
    s = copy.deepcopy(core_stmt)
    s["_type"] = "urn:in-toto:Statement:v1"
    reject_list.append(reject_signed_stmt(
        "reject-wrong-type", "catalogue",
        "Statement _type uses wrong identifier instead of https://in-toto.io/Statement/v1.",
        s, "statement-type",
    ))

    # 2. Wrong predicateType
    s = copy.deepcopy(reg_stmt)
    s["predicateType"] = "https://traceweave.org/predicate/registration/draft-4"
    reject_list.append(reject_signed_stmt(
        "reject-wrong-predicate-type", "registration",
        "Statement predicateType uses an unsupported/deprecated draft URI.",
        s, "predicate-type",
    ))

    # 3. Subject digest mismatch (signature valid; artifact bytes mismatch statement digest)
    s = copy.deepcopy(core_stmt)
    s["subject"][0]["digest"]["sha256"] = "f" * 64
    reject_list.append(reject_signed_stmt(
        "reject-subject-digest-mismatch", "catalogue",
        "Signed statement whose subject sha256 digest mismatches the supplied artifact bytes.",
        s, "subject-digest-mismatch",
        artifacts=[{"subjectIndex": 0, "source": "examples/artifact.txt"}],
    ))

    # 4. Missing required top-level statement field
    s = copy.deepcopy(core_stmt)
    del s["subject"]
    reject_list.append(reject_signed_stmt(
        "reject-missing-statement-field", "catalogue",
        "Statement omits required top-level 'subject' field.",
        s, "missing-required-field",
    ))

    # 5. Missing required predicate field
    s = copy.deepcopy(core_stmt)
    del s["predicate"]["catalogueCommitment"]
    reject_list.append(reject_signed_stmt(
        "reject-missing-predicate-field", "catalogue",
        "Core predicate omits required 'catalogueCommitment' field.",
        s, "missing-required-field",
    ))

    # 6. Extra field on statement
    s = copy.deepcopy(core_stmt)
    s["extra"] = True
    reject_list.append(reject_signed_stmt(
        "reject-extra-field-statement", "catalogue",
        "Statement carries an unallowed top-level 'extra' field.",
        s, "extra-field",
    ))

    # 7. Extra field on predicate
    s = copy.deepcopy(core_stmt)
    s["predicate"]["unexpectedFlag"] = True
    reject_list.append(reject_signed_stmt(
        "reject-extra-field-predicate", "catalogue",
        "Predicate carries an unallowed 'unexpectedFlag' field.",
        s, "extra-field",
    ))

    # 8. Invalid base64 in DSSE payload
    env = sign_raw_payload(core_bytes)
    env["payload"] = "not!valid!base64==="
    reject_list.append(make_fixture(
        "reject-invalid-base64", "catalogue",
        "DSSE envelope payload contains invalid base64 characters.",
        env, expect={"code": "invalid-base64"},
    ))

    # 9. Wrong DSSE payloadType
    reject_list.append(make_fixture(
        "reject-wrong-dsse-payload-type", "catalogue",
        "DSSE envelope uses application/json instead of application/vnd.in-toto+json.",
        sign_raw_payload(core_bytes, payload_type="application/json"),
        expect={"code": "dsse-payload-type"},
    ))

    # 10. Authorship/ownership claim smuggling by key
    s = copy.deepcopy(reg_stmt)
    s["predicate"]["claims"]["author"] = "Alice"
    reject_list.append(reject_signed_stmt(
        "reject-authorship-smuggling-key", "registration",
        "Predicate attempts to smuggle an 'author' key into claims.",
        s, "authorship-claim",
    ))

    # 11. Authorship/origin claim smuggling by value (claims.aiUse.tool caught by tool_has_origin_claim)
    s = copy.deepcopy(reg_ai_stmt)
    s["predicate"]["claims"]["aiUse"]["tool"] = "Penned-by-Bob"
    reject_list.append(reject_signed_stmt(
        "reject-authorship-smuggling-value", "registration",
        "claims.aiUse.tool smuggles human-origin wording ('Penned-by-Bob').",
        s, "authorship-claim",
    ))

    # 11b. Authorship smuggling in core subject[0].name
    s = copy.deepcopy(core_stmt)
    s["subject"][0]["name"] = "written by Alice"
    reject_list.append(reject_signed_stmt(
        "reject-authorship-smuggling-subject-name", "catalogue",
        "Core subject[0].name smuggles human-authorship wording ('written by Alice').",
        s, "authorship-claim",
    ))

    # 11c. Authorship smuggling in registration predicate.implementation.name
    s = copy.deepcopy(reg_stmt)
    s["predicate"]["implementation"]["name"] = "proves authorship"
    reject_list.append(reject_signed_stmt(
        "reject-authorship-smuggling-impl-name", "registration",
        "predicate.implementation.name smuggles authorship wording ('proves authorship').",
        s, "authorship-claim",
    ))

    # 11d. Authorship smuggling in registration predicate.contentKind
    s = copy.deepcopy(reg_stmt)
    s["predicate"]["contentKind"] = "authored by Bob"
    reject_list.append(reject_signed_stmt(
        "reject-authorship-smuggling-content-kind", "registration",
        "predicate.contentKind smuggles authorship wording ('authored by Bob').",
        s, "authorship-claim",
        also=["statement-shape"],
    ))

    # 11e. Unrecognized contentKind in registration mode (closed allow-list)
    s = copy.deepcopy(reg_stmt)
    s["predicate"]["contentKind"] = "executable"
    reject_list.append(reject_signed_stmt(
        "reject-unknown-content-kind", "registration",
        "Registration predicate.contentKind uses a value outside the closed registration allow-list.",
        s, "statement-shape",
    ))

    # 11f. Permuted predicate.possession subjectIndex ordering
    s = copy.deepcopy(reg_ai_stmt)
    s["predicate"]["possession"] = list(reversed(s["predicate"]["possession"]))
    reject_list.append(reject_signed_stmt(
        "reject-permuted-possession-index", "registration",
        "Multi-subject registration predicate.possession entries appear out of canonical subjectIndex order.",
        s, "statement-shape",
        artifacts=[
            {"subjectIndex": 0, "source": sum_go_src},
            {"subjectIndex": 1, "source": host_go_src},
        ],
    ))

    # 12. Time claim smuggling (provedAt inside predicate)
    s = copy.deepcopy(core_stmt)
    s["predicate"]["provedAt"] = "2026-11-20T09:00:00Z"
    reject_list.append(reject_signed_stmt(
        "reject-time-claim-smuggling", "catalogue",
        "Predicate attempts to embed an unverified 'provedAt' timestamp key.",
        s, "time-in-statement",
    ))

    # 13. Forbidden secret/content key smuggling
    s = copy.deepcopy(core_stmt)
    s["predicate"]["privateKey"] = "must-not-be-here"
    reject_list.append(reject_signed_stmt(
        "reject-forbidden-secret-field", "catalogue",
        "Predicate attempts to smuggle a forbidden 'privateKey' field.",
        s, "forbidden-field",
    ))

    # 14. Duplicate JSON key in signed payload bytes
    dup_bytes = (
        b'{"_type":"https://in-toto.io/Statement/v1","_type":"https://in-toto.io/Statement/v1",'
        + core_bytes[1:]
    )
    reject_list.append(make_fixture(
        "reject-duplicate-json-key", "catalogue",
        "Valid DSSE signature over payload bytes containing a duplicate '_type' JSON key.",
        sign_raw_payload(dup_bytes),
        expect={"code": "duplicate-key"},
    ))

    # 15. Signature computed over base64 text instead of raw decoded payload bytes
    b64_text_bytes = b64(core_bytes).encode("ascii")
    bad_sig = C.ed25519_sign(SEED_TRUSTED, C.dsse_pae(C.DSSE_PAYLOAD_TYPE.encode("utf-8"), b64_text_bytes))
    reject_list.append(make_fixture(
        "reject-signature-over-base64", "catalogue",
        "DSSE signature computed over the base64 payload text instead of decoded payload bytes.",
        {
            "payloadType": C.DSSE_PAYLOAD_TYPE,
            "payload": b64(core_bytes),
            "signatures": [{"keyid": KID_TRUSTED, "sig": b64(bad_sig)}],
        },
        expect={"code": "signature-invalid"},
    ))

    # 16. Tampered payload after signing
    tampered = copy.deepcopy(core_stmt)
    tampered["subject"][0]["name"] = "tampered.txt"
    env_tampered = sign_raw_payload(core_bytes)
    env_tampered["payload"] = b64(C.jcs(tampered))
    reject_list.append(make_fixture(
        "reject-tampered-payload", "catalogue",
        "DSSE payload modified after signing while keeping the original signature.",
        env_tampered,
        expect={"code": "signature-invalid"},
    ))

    # 17. Untrusted signer key (valid Ed25519 signature under a key absent from trustedKeys)
    reject_list.append(make_fixture(
        "reject-untrusted-key", "catalogue",
        "Valid Ed25519 DSSE signature produced by a key absent from trustedKeys.",
        sign_raw_payload(core_bytes, seed=SEED_UNTRUSTED, kid=KID_UNTRUSTED),
        public_keys=[{"keyid": KID_UNTRUSTED, "alg": "ed25519", "publicKeyHex": PUB_UNTRUSTED.hex()}],
        trusted_keys=[SHA_TRUSTED],
        expect={"code": "untrusted-signer"},
    ))

    # 18. Core statement with multiple subjects (core adapter enforces exactly 1 subject)
    s = copy.deepcopy(core_stmt)
    s["subject"].append({"name": "extra.txt", "digest": {"sha256": "a" * 64}})
    reject_list.append(reject_signed_stmt(
        "reject-core-multiple-subjects", "catalogue",
        "Core evidence statement carries two subjects instead of exactly one.",
        s, "subject-count",
    ))

    # 19. Malformed subject digest hex
    s = copy.deepcopy(core_stmt)
    s["subject"][0]["digest"]["sha256"] = "ab12"
    reject_list.append(reject_signed_stmt(
        "reject-malformed-subject-digest", "catalogue",
        "Subject sha256 digest is truncated instead of 64 lowercase hex characters.",
        s, "statement-shape",
    ))

    # 20. Unknown key hint (missing from verificationMaterial.publicKeys)
    reject_list.append(make_fixture(
        "reject-missing-key-hint", "catalogue",
        "DSSE signature references a keyid hint absent from verificationMaterial.publicKeys.",
        sign_raw_payload(core_bytes, kid="0000000000000000"),
        expect={"code": "unknown-key"},
    ))

    # 21. Empty DSSE signatures list
    env_empty_sigs = sign_raw_payload(core_bytes)
    env_empty_sigs["signatures"] = []
    reject_list.append(make_fixture(
        "reject-empty-signatures", "catalogue",
        "DSSE envelope carries an empty signatures array.",
        env_empty_sigs,
        expect={"code": "dsse-shape"},
    ))

    for d in ("accept", "reject"):
        target_dir = HERE / d
        if target_dir.exists():
            for old in target_dir.glob("*.json"):
                old.unlink()

    for fx in accept_list:
        write_json(HERE / "accept" / f"{fx['id']}.json", fx)
    for fx in reject_list:
        write_json(HERE / "reject" / f"{fx['id']}.json", fx)

    print(f"Built {len(accept_list)} accept and {len(reject_list)} reject fixtures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
