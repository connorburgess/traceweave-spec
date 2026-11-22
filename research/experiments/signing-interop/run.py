#!/usr/bin/env python3
"""Synthetic DSSE compatibility checks; build first, then run offline.

No candidate content is executed and no signed URL is resolved.
The strict JSON/resource preflight below is experiment policy, not DSSE itself.
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.validate import catalogue_commitment, schema_validator  # noqa: E402

BIN = {"go": HERE / "bin/go-dsse", "rust": HERE / "rust/target/release/traceweave-signing-interop"}
MAX_ENVELOPE, MAX_PAYLOAD = 16384, 8192
TYPE = "application/vnd.in-toto+json"


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def strict(data):
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))


def preflight(raw):
    if len(raw) > MAX_ENVELOPE:
        raise ValueError("envelope limit")
    envelope = strict(raw)
    if len(envelope["signatures"]) != 1:
        raise ValueError("signature count")
    payload = base64.b64decode(envelope["payload"], validate=True)
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload limit")
    return envelope


def main():
    # Proves the OS sandbox denies a network syscall, without contacting a service.
    # Passing --require-network-denied makes a missing sandbox a hard failure.
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
        assert denied, "network sandbox did not deny local bind"
    start = time.perf_counter()
    raw_statement = (ROOT / "examples/statement.json").read_bytes()
    statement = strict(raw_statement)
    schema_validator().validate(statement)
    assert len(statement["subject"]) == 1
    results = []
    def record(case, **values):
        results.append({"case": case, **values})
    with tempfile.TemporaryDirectory(prefix="traceweave-dsse-") as directory:
        temp = Path(directory)
        def invoke(language, *args):
            return subprocess.run([str(BIN[language]), *map(str, args)], capture_output=True, timeout=10)
        public = {}
        for language in BIN:
            response = invoke(language, "public")
            assert response.returncode == 0 and len(response.stdout) == 32
            public[language] = temp / f"{language}.public"
            public[language].write_bytes(response.stdout)
        assert public["go"].read_bytes() != public["rust"].read_bytes()
        envelope_path = temp / "envelope.json"
        for producer in BIN:
            response = invoke(producer, "sign", ROOT / "examples/statement.json")
            assert response.returncode == 0, response.stderr
            original = strict(response.stdout)
            assert base64.b64decode(original["payload"]) == raw_statement
            for consumer in BIN:
                def verify(case, raw, expected, pub=None, precheck=True):
                    try:
                        if precheck:
                            preflight(raw)
                    except (ValueError, KeyError, TypeError):
                        assert not expected, case
                        record(case, producer=producer, consumer=consumer, accepted=False, layer="preflight")
                        return
                    envelope_path.write_bytes(raw)
                    actual = invoke(consumer, "verify", envelope_path, pub or public[producer])
                    assert (actual.returncode == 0) == expected, (case, actual.stderr)
                    if expected:
                        assert actual.stdout == raw_statement, case
                    record(case, producer=producer, consumer=consumer, accepted=expected, layer="library-driver")
                def changed(field, value):
                    envelope = copy.deepcopy(original)
                    envelope[field] = value
                    return json.dumps(envelope).encode()
                verify("same-exact-raw-statement", response.stdout, True)
                verify("envelope-whitespace-and-key-order", json.dumps(dict(reversed(list(original.items()))), indent=3).encode(), True)
                verify("payload-byte-mutation", changed("payload", base64.b64encode(raw_statement + b" ").decode()), False)
                verify("payload-type-mutation", changed("payloadType", "application/json"), False)
                sig = bytearray(base64.b64decode(original["signatures"][0]["sig"]))
                sig[0] ^= 1
                verify("signature-bit-mutation", changed("signatures", [{**original["signatures"][0], "sig": base64.b64encode(sig).decode()}]), False)
                other = public["rust" if producer == "go" else "go"]
                verify("different-public-key", response.stdout, False, pub=other)
                # A valid signature with its own known public key does not imply trust.
                trusted = {public["rust" if producer == "go" else "go"].read_bytes()}
                assert public[producer].read_bytes() not in trusted
                record("valid-signature-untrusted-signer", producer=producer, consumer=consumer,
                       signature_valid=True, signer_trusted=False)
                expected_digest = statement["subject"][0]["digest"]["sha256"]
                assert hashlib.sha256((ROOT / "examples/artifact.txt").read_bytes()).hexdigest() == expected_digest
                assert hashlib.sha256(b"synthetic changed candidate").hexdigest() != expected_digest
                record("candidate-mismatch", producer=producer, consumer=consumer,
                       signature_valid=True, exact_binding=False, fingerprint_comparison="not-checked")
                duplicate = b'{"payloadType":"ignored",' + response.stdout.lstrip()[1:]
                verify("duplicate-envelope-key-policy", duplicate, False)
                # Probe native parsers independently to expose Go/Rust differences.
                envelope_path.write_bytes(duplicate)
                native = invoke(consumer, "verify", envelope_path, public[producer])
                assert (native.returncode == 0) == (consumer == "go"), "native duplicate parser behavior changed"
                record("duplicate-envelope-key-native-probe", producer=producer, consumer=consumer,
                       accepted=native.returncode == 0)
                verify("oversize-envelope", b" " * MAX_ENVELOPE + response.stdout, False)
                verify("oversize-decoded-payload", changed("payload", base64.b64encode(b"x" * (MAX_PAYLOAD + 1)).decode()), False)
                verify("empty-signature-list", changed("signatures", []), False)
                verify("invalid-base64", changed("payload", "%%%"), False)
                hint = [{**original["signatures"][0], "keyid": "different-hint"}]
                # keyid is unsigned. Go filters mismatched nonempty hints; Rust ignores them.
                verify("changed-keyid-hint", changed("signatures", hint), consumer == "rust")
            # Authenticated bytes can still violate application parsing policy.
            inner = b'{"_type":"ignored",' + raw_statement.lstrip()[1:]
            inner_path = temp / "duplicate-statement.json"
            inner_path.write_bytes(inner)
            signed_inner = invoke(producer, "sign", inner_path)
            assert signed_inner.returncode == 0, signed_inner.stderr
            preflight(signed_inner.stdout)
            envelope_path.write_bytes(signed_inner.stdout)
            for consumer in BIN:
                verified = invoke(consumer, "verify", envelope_path, public[producer])
                assert verified.returncode == 0 and verified.stdout == inner
                try:
                    strict(verified.stdout)
                    raise AssertionError("duplicate authenticated payload accepted")
                except ValueError:
                    pass
                record("signed-duplicate-inner-payload", producer=producer, consumer=consumer,
                       signature_valid=True, payload_policy_valid=False, schema="not-checked-after-parse-rejection")
        vector = strict((ROOT / "test-vectors/commitment.json").read_bytes())
        catalogue = (ROOT / vector["catalogue"]).read_bytes()
        nonce = bytes.fromhex(vector["nonceHex"])
        commitment = statement["predicate"]["catalogueCommitment"]["sha256"]
        assert catalogue_commitment(catalogue, nonce) == vector["expectedSha256"] == commitment
        assert catalogue_commitment(catalogue + b" ", nonce) != commitment
        assert catalogue_commitment(catalogue, nonce[::-1]) != commitment
        record("existing-commitment-opening", consistent=True, altered_catalogue=False, altered_nonce=False)
        for size in (0, 31, 33):
            try:
                catalogue_commitment(catalogue, b"x" * size)
                raise AssertionError("invalid nonce accepted")
            except ValueError:
                pass
        record("nonce-lengths", rejected=[0, 31, 33])
    output = {"platform": platform.platform(), "machine": platform.machine(),
              "network_denied": denied, "payload_bytes": len(raw_statement),
              "statement_sha256": hashlib.sha256(raw_statement).hexdigest(),
              "elapsed_seconds": round(time.perf_counter() - start, 4),
              "results": results}
    (HERE / "last-results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k != "results"}, indent=2))
    print(f"PASS: {len(results)} recorded outcomes (four producer/consumer combinations)")


if __name__ == "__main__":
    main()
