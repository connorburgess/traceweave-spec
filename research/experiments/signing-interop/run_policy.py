#!/usr/bin/env python3
"""Experiment policy plus independent Go/Rust commitment checks; no new format.

The shared Python policy is an orchestrator, not independent parser implementations.
Go/Rust still independently produce PAE/signatures and catalogue commitment framing.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import time

from run import BIN, HERE, ROOT, TYPE, preflight, schema_validator, strict
from tools.validate import catalogue_commitment


def verify_policy(raw, public, trusted, consumer, directory):
    result = {"envelope_policy": False, "signature_valid": "not-checked",
              "signer_trusted": public in trusted, "payload_policy": "not-checked",
              "schema_valid": "not-checked", "accepted": False}
    try:
        envelope = preflight(raw)  # recursive duplicate rejection, bounded payload
        if set(envelope) != {"payload", "payloadType", "signatures"}:
            raise ValueError("unexpected/missing envelope field")
        if not isinstance(envelope["payloadType"], str):
            raise ValueError("payload type must be string")
        signature = envelope["signatures"][0]
        if not isinstance(signature, dict) or set(signature) - {"sig", "keyid"} or "sig" not in signature:
            raise ValueError("signature fields")
        if "keyid" in signature and not isinstance(signature["keyid"], str):
            raise ValueError("key hint must be string when present")
        if len(base64.b64decode(signature["sig"], validate=True)) != 64:
            raise ValueError("signature length")
        # Ignore the unauthenticated hint consistently. Public key is caller supplied,
        # never selected from the envelope. PAE inputs/payload/signature are unchanged.
        normalized = copy.deepcopy(envelope)
        normalized["signatures"][0]["keyid"] = ""
        result["envelope_policy"] = True
    except (ValueError, TypeError, KeyError):
        return result
    env_path, key_path = directory / "policy-envelope.json", directory / "policy-key.bin"
    env_path.write_text(json.dumps(normalized))
    key_path.write_bytes(public)
    verification = subprocess.run([str(BIN[consumer]), "verify", str(env_path), str(key_path)],
                                  capture_output=True, timeout=10)
    result["signature_valid"] = verification.returncode == 0
    if not result["signature_valid"]:
        return result
    assert verification.stdout == base64.b64decode(envelope["payload"], validate=True)
    try:
        payload = strict(verification.stdout)
        result["payload_policy"] = True
    except ValueError:
        result["payload_policy"] = False
        return result
    result["schema_valid"] = schema_validator().is_valid(payload)
    result["accepted"] = (result["signer_trusted"] and result["schema_valid"]
                          and envelope["payloadType"] == TYPE)
    return result


def main():
    denied = False
    try:
        sock = socket.socket()
        try:
            sock.bind(("127.0.0.1", 0))
        finally:
            sock.close()
    except PermissionError:
        denied = True
    if "--require-network-denied" in sys.argv:
        assert denied, "network isolation is required"
    started = time.perf_counter()
    prior = (HERE / "results.json").read_bytes()
    raw = (ROOT / "examples/statement.json").read_bytes()
    records = []
    with tempfile.TemporaryDirectory(prefix="traceweave-policy-") as path:
        temp = Path(path)
        def call(language, *args):
            return subprocess.run([str(BIN[language]), *map(str, args)], capture_output=True, timeout=10)
        public = {}
        for language in BIN:
            response = call(language, "public")
            assert response.returncode == 0 and len(response.stdout) == 32
            public[language] = response.stdout
        for producer in BIN:
            signed = call(producer, "sign", ROOT / "examples/statement.json")
            assert signed.returncode == 0, signed.stderr
            original = strict(signed.stdout)
            for consumer in BIN:
                def check(name, content, *, accepted=False, signature=True, envelope=True,
                          payload=True, schema=True, key=None, trusted=None):
                    result = verify_policy(content, public[producer] if key is None else key,
                                           {public[producer]} if trusted is None else trusted,
                                           consumer, temp)
                    assert result["accepted"] == accepted, (name, result)
                    for field, expected in (("signature_valid", signature), ("envelope_policy", envelope),
                                            ("payload_policy", payload), ("schema_valid", schema)):
                        assert result[field] == expected, (name, field, result)
                    records.append({"case": name, "producer": producer, "consumer": consumer, **result})
                for name, hint in (("absent", None), ("empty", ""), ("original", "synthetic-test-only"),
                                   ("wrong", "not-this-key"), ("other-known-key", public["rust" if producer == "go" else "go"].hex()),
                                   ("unicode", "hint-\u00e9-\u2603")):
                    changed = copy.deepcopy(original)
                    if hint is None:
                        changed["signatures"][0].pop("keyid", None)
                    else:
                        changed["signatures"][0]["keyid"] = hint
                    check("hint-" + name, json.dumps(changed).encode(), accepted=True)
                check("valid-but-untrusted", signed.stdout, trusted=set())
                check("wrong-key-with-correct-hint", signed.stdout,
                      key=public["rust" if producer == "go" else "go"],
                      signature=False, payload="not-checked", schema="not-checked")
                changed = copy.deepcopy(original)
                changed["signatures"][0]["sig"] = base64.b64encode(bytes(64)).decode()
                check("bad-signature-cannot-be-repaired-by-hint-normalization", json.dumps(changed).encode(),
                      signature=False, payload="not-checked", schema="not-checked")
                duplicate_cases = {
                    "duplicate-payloadType": b'{"payloadType":"ignored",' + signed.stdout.lstrip()[1:],
                    "duplicate-escaped-payload": b'{"paylo\\u0061d":"ignored",' + signed.stdout.lstrip()[1:],
                    "duplicate-signatures": b'{"signatures":[],' + signed.stdout.lstrip()[1:],
                    "duplicate-nested-keyid": json.dumps(original).replace('"keyid":', '"keyid":"ignored","keyid":').encode(),
                }
                changed = copy.deepcopy(original)
                changed["PayloadType"] = TYPE  # Go struct aliases must not bypass exact field policy.
                duplicate_cases["case-alias-extra-field"] = json.dumps(changed).encode()
                changed = copy.deepcopy(original)
                changed["signatures"][0]["keyid"] = 42
                duplicate_cases["nonstring-hint"] = json.dumps(changed).encode()
                for name, content in duplicate_cases.items():
                    check(name, content, signature="not-checked", envelope=False,
                          payload="not-checked", schema="not-checked")
                for name, content in (
                    ("duplicate-inner-top", b'{"_type":"ignored",' + raw.lstrip()[1:]),
                    ("duplicate-inner-nested", raw.replace(b'"sha256":', b'"sha256":"ignored","sha256":', 1)),
                ):
                    payload_file = temp / "payload.json"
                    payload_file.write_bytes(content)
                    envelope = call(producer, "sign", payload_file)
                    assert envelope.returncode == 0
                    check(name, envelope.stdout, payload=False, schema="not-checked")
                invalid = strict(raw)
                invalid["subject"].append(copy.deepcopy(invalid["subject"][0]))
                payload_file = temp / "payload.json"
                payload_file.write_text(json.dumps(invalid))
                envelope = call(producer, "sign", payload_file)
                assert envelope.returncode == 0
                check("signed-two-subjects-schema-rejected", envelope.stdout, schema=False)

        vector = strict((ROOT / "test-vectors/commitment.json").read_bytes())
        nonce = bytes.fromhex(vector["nonceHex"])
        fixture = (ROOT / vector["catalogue"]).read_bytes()
        def commitment(name, catalogue, opening_nonce, expected=None):
            catalogue_path, nonce_path = temp / "catalogue.bin", temp / "nonce.bin"
            catalogue_path.write_bytes(catalogue)
            nonce_path.write_bytes(opening_nonce)
            outputs = {}
            for language in BIN:
                response = call(language, "commit", catalogue_path, nonce_path)
                valid = len(opening_nonce) == 32 and len(catalogue) <= 1048576
                assert (response.returncode == 0) == valid, (name, language, response.stderr)
                if valid:
                    digest = response.stdout.decode().strip()
                    reference = catalogue_commitment(catalogue, opening_nonce)
                    assert digest == reference and len(digest) == 64
                    if expected is not None:
                        assert digest == expected
                    outputs[language] = digest
                records.append({"case": name, "implementation": language, "catalogue_bytes": len(catalogue),
                                "nonce_bytes": len(opening_nonce), "accepted": valid,
                                "commitment": outputs.get(language)})
            if outputs:
                assert outputs["go"] == outputs["rust"]
                return outputs["go"]
        original = commitment("existing-repository-vector", fixture, nonce, vector["expectedSha256"])
        statement = strict(raw)
        assert original == statement["predicate"]["catalogueCommitment"]["sha256"]
        for length in (0, 1, 55, 56, 63, 64, 65, 255, 256, 65535, 65536, 1048576):
            commitment("catalogue-byte-length-" + str(length), bytes(i % 256 for i in range(length)), nonce)
        for name, catalogue in (("utf8", "caf\u00e9 \u2603".encode()), ("embedded-zero-nonutf8", b"\x00\xff\x80\x00"),
                                ("json-reserialization", json.dumps(strict(fixture), separators=(",", ":")).encode()),
                                ("catalogue-bit-tamper", bytes([fixture[0] ^ 1]) + fixture[1:]),
                                ("catalogue-trailing-whitespace", fixture + b" ")):
            assert commitment(name, catalogue, nonce) != original
        assert commitment("nonce-bit-tamper", fixture, bytes([nonce[0] ^ 1]) + nonce[1:]) != original
        for length in (0, 1, 31, 33, 64):
            commitment("invalid-nonce-length-" + str(length), fixture, b"x" * length)
        commitment("catalogue-resource-limit", b"x" * 1048577, nonce)
        # Reference distinguishes common framing mistakes; both implementations matched
        # the correct expected vector above, so none of these alternate framings match.
        domain = b"Traceweave-Catalogue-v0.1\0"
        mistakes = {"missing-domain-zero": domain[:-1] + nonce + len(fixture).to_bytes(8, "big") + fixture,
                    "little-endian-length": domain + nonce + len(fixture).to_bytes(8, "little") + fixture,
                    "missing-length": domain + nonce + fixture,
                    "length-after-catalogue": domain + nonce + fixture + len(fixture).to_bytes(8, "big")}
        for name, framed in mistakes.items():
            assert hashlib.sha256(framed).hexdigest() != original
            records.append({"case": name, "reference_framing_rejected": True})
    assert (HERE / "results.json").read_bytes() == prior, "earlier results changed"
    output = {"platform": platform.platform(), "machine": platform.machine(), "network_denied": denied,
              "elapsed_seconds": round(time.perf_counter() - started, 4),
              "prior_results_sha256": hashlib.sha256(prior).hexdigest(),
              "statement_sha256": hashlib.sha256(raw).hexdigest(), "outcomes": len(records), "results": records}
    (HERE / "last-policy-results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k != "results"}, indent=2))
    print("PASS: policy and independent Go/Rust commitment assertions")


if __name__ == "__main__":
    main()
