# Signing policy and independent commitment experiment

Measured 2026-11-21. The [follow-up harness](../experiments/signing-interop/run_policy.py) resolves the experiment-level parser/key-hint differences from the [first signing experiment](signing-interop-results.md) and adds independent Go/Rust implementations of the existing catalogue commitment. It does not amend any normative schema or DSSE format. The earlier `run.py` and checked-in `results.json` are preserved; the latter's SHA-256 remains `8edb54aee33f214568e7494abc2cc5f79ace2e8f88503a624538f966c1134814`.

## Explicit experiment policy

1. Reject duplicate JSON object keys recursively, including names that become equal after JSON unescaping. Validate the envelope's exact field names and types, one signature, 16 KiB envelope and 8 KiB decoded-payload limits. Repeated names in different objects remain allowed. The existing statement already exercises that distinction.
2. Receive the verification public key and trusted-key set from the caller, never from envelope hints or a remote lookup. After strict parsing, set the unsigned `keyid` to an empty string before passing the envelope to either native library. The authenticated payload bytes, payload type and decoded signature bytes remain unchanged. Envelope JSON can be reserialized without becoming a new signed payload.
3. Record cryptographic validity and caller-supplied signer trust independently. After successful verification, use exactly the returned payload bytes, assert they equal the decoded signed body, reject inner duplicate keys, and validate the existing restricted single-subject schema. Accept only with expected payload type, a valid signature, trusted key and valid application payload. A signed malformed/ambiguous payload remains signature-valid while application policy rejects it.

The policy is implemented once in Python and calls both native drivers. It does **not** demonstrate independent Go/Rust strict parser implementations. The earlier native behavior is deliberately retained: Go filters mismatching nonempty key IDs and accepts some duplicate fields under its default JSON decoder, whereas Rust ignores the hint during verification and rejects duplicate struct fields. The pinned [Go verification source](https://github.com/secure-systems-lab/go-securesystemslib/blob/v0.11.1/dsse/verify.go), [Rust DSSE source](https://github.com/pulseengine/sigil/blob/37bad055a13a137dbaeec7693e77963c942a6ac4/src/dsse/src/lib.rs) and [DSSE envelope definition](https://github.com/dsse-lf/dsse/blob/v1.0.2/envelope.md) support keeping the hint separate from authenticated content. Clearing it here is a local interoperability policy, not an upstream library fix or normative protocol change.

## Independent exact-byte commitments

The Go and Rust drivers each implement `SHA256(D || R || L || C)` directly, using the current [core definition](../../spec/core.md): `D = UTF8("Traceweave-Catalogue-v0.1") || 0x00`; `R` exactly 32 bytes; `L` an unsigned eight-byte big-endian byte length; `C` the opaque catalogue bytes. Neither implementation parses or reserializes the catalogue.

Go uses [`crypto/sha256.New`](https://pkg.go.dev/crypto/sha256) and [`binary.BigEndian.PutUint64`](https://pkg.go.dev/encoding/binary#ByteOrder). Rust uses [`sha2 =0.10.9`, `Sha256::new/update/finalize`](https://docs.rs/sha2/0.10.9/sha2/) with `u64::to_be_bytes`. The [pinned Rust crate](https://crates.io/crates/sha2/0.10.9) declares `MIT OR Apache-2.0`; it and transitive versions/checksums are retained in `Cargo.lock`. The Go/Rust DSSE library pins and test-only seed handling are unchanged from the previous experiment. This is now independent commitment framing in both languages; Python's existing helper supplies a third reference, not the commitment implementation used by either driver.

Both reproduce repository commitment `f4df04ab00454b3a4b1bc25d80009a8a3e82f9d5d4f4eeed08c6cbbd9891c4a9`, matching [the existing vector](../../test-vectors/commitment.json) and the commitment inside the unchanged 762-byte signed statement. This is full opening consistency; it is not selective disclosure or proof that catalogue contents are true.

## Measured outcomes

All **126 recorded outcomes** passed: 72 policy outcomes across Go→Go, Go→Rust, Rust→Go and Rust→Rust; 50 native commitment outcomes; four reference-only framing counterchecks. Individual results are in [policy-results.json](../experiments/signing-interop/policy-results.json).

| Test group | Measured result |
| --- | --- |
| Hints absent, empty, original, wrong, another known public-key string, Unicode | Both consumers accept valid trusted signatures after hint normalization; authenticated bytes match exactly |
| Valid signature but no trusted signer | Signature valid and schema valid; signer trust false; acceptance false |
| Wrong actual public key with correct hint | Signature invalid; no payload parsing; acceptance false |
| Zeroed signature with hint normalization | Still invalid; normalization cannot repair a signature |
| Duplicate outer payload type, escaped duplicate payload name, duplicate signature list, nested duplicate `keyid` | Rejected before native verification by common strict policy |
| Case alias extra field, numeric key hint | Rejected before native verification by exact field/type policy |
| Correct signatures over duplicate top-level or nested inner fields | Signature valid in both consumers; payload parsing policy rejects; schema not checked after parse rejection |
| Correct signature over two subjects | Signature valid; existing schema rejects two subjects |
| Repository vector and signed-statement commitment | Go, Rust and Python agree exactly |
| Catalogue lengths 0, 1, 55, 56, 63, 64, 65, 255, 256, 65535, 65536, 1048576 | Go/Rust agree with Python for all, including empty, SHA block-adjacent lengths and multibyte length boundaries |
| UTF-8; embedded zero/non-UTF-8 bytes | Go/Rust agree with Python using byte lengths and opaque bytes |
| JSON reserialization, catalogue bit flip/trailing whitespace, nonce bit flip | Go/Rust agree with Python; each changed opening mismatches the original commitment |
| Nonce lengths 0, 1, 31, 33, 64 | Both drivers reject |
| Catalogue 1048577 bytes | Both drivers reject the experiment's 1 MiB resource cap |
| Missing domain zero, little-endian length, missing length, length moved after catalogue | Python reference counterchecks all differ from existing vector; both native implementations matched the correct vector above |

Runtime was under inherited macOS `sandbox-exec` `(deny network*)`, with a denied local socket bind asserted. The complete follow-up run took **1.7602 s** on the existing Apple M5 Pro/arm64/macOS 26.4 host, excluding dependency fetch/build. This is one elapsed measurement, not a performance or memory guarantee. Installing the newly pinned SHA-256 dependency was online; runtime checks and subsequent cached builds were offline. The original 66-outcome harness also passed again without altering its historical snapshot.

Checks completed: `go vet ./...`; cached Go readonly build with `GOPROXY=off GOSUMDB=off`; `cargo fmt --check`; Rust `--release --locked --offline` build; both network-denied harnesses; repository validation and six existing contract tests. Commands are in the [experiment README](../experiments/signing-interop/README.md).

Limits: one signature, public synthetic keys, selected bounded JSON cases and regular temporary files. No parser fuzzing/depth corpus, streaming file hardening, production key identity, certificate/revocation policy, TSA, timestamp target, resolver, private app, paid service, empirical fingerprint comparison or rights assessment was added. The commitment cap limits tested lengths to 1 MiB; uint64 framing above that boundary was not exercised. No schema, core commitment, or single-subject adapter change is proposed.
