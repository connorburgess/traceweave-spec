# Signing interoperability: measured offline experiment

Measured 2026-11-18. This implements the smallest bare-envelope increment from the [provenance comparison](../04-provenance-verification-comparison.md), with synthetic public test-only Ed25519 seeds. It does not implement timestamping or production key management.

## Library selection and reproducible pins

| Component | Pin and concrete API | License / maintenance evidence |
| --- | --- | --- |
| Go DSSE | `github.com/secure-systems-lab/go-securesystemslib v0.11.1`; `NewEnvelopeSigner().SignPayload`, `NewEnvelopeVerifier().VerifyAndDecode` | MIT; [versioned API](https://pkg.go.dev/github.com/secure-systems-lab/go-securesystemslib@v0.11.1/dsse), [pinned license](https://github.com/secure-systems-lab/go-securesystemslib/blob/662f0f738ddc65cf9543c3e90114bd6d95a7e361/LICENSE) |
| Rust DSSE | `wsc-dsse =0.12.1`; `DsseEnvelope::sign`, `from_json`, `verify`, `Ed25519DsseSigner`, `Ed25519DsseVerifier` | MIT declared by [pinned crate manifest](https://github.com/pulseengine/sigil/blob/37bad055a13a137dbaeec7693e77963c942a6ac4/src/dsse/Cargo.toml); [actual implementation](https://github.com/pulseengine/sigil/blob/37bad055a13a137dbaeec7693e77963c942a6ac4/src/dsse/src/lib.rs) |
| Rust key construction | `ed25519-compact =2.3.0`, `KeyPair::from_seed` | MIT, [crate release](https://crates.io/crates/ed25519-compact/2.3.0) |

These are real DSSE implementations, not a manually written PAE experiment. Go injects standard-library Ed25519 through the documented `Signer`/`Verifier` interfaces; Rust uses the crate's Ed25519 wrappers. Go's module checksum and all Rust transitive checksums are retained in [experiment source and lockfiles](../experiments/signing-interop/README.md). Rust release checksum: `4af95cee5947fb0299ddd60ec1bc676f2084eb61b4376c8b7ae9f905cadc6f59`; VCS commit/path above came from the downloaded crate's `.cargo_vcs_info.json`.

Maintenance was checked against the [Go repository API](https://api.github.com/repos/secure-systems-lab/go-securesystemslib) and [Rust repository API](https://api.github.com/repos/pulseengine/sigil): both unarchived at inspection; latest pushes were 2026-11-16 and 2026-11-18 respectively. The [Rust registry metadata](https://crates.io/api/v1/crates/wsc-dsse/0.12.1) reports publication on 2026-11-13. Recent activity is an observation, not a support guarantee or security audit. Repository metadata for Rust did not identify a repository-wide license; the published crate explicitly declares MIT. Dependencies are fetched, not vendored or relicensed.

An earlier Rust candidate, `dsse` 0.1.6 (Apache-2.0), was rejected because both its old [standalone repository](https://github.com/probityai-archive/dsse) and [replacement repository](https://api.github.com/repos/probityai/agent-evidence) were archived at inspection. It is not an experiment dependency. `sigstore` 0.15.0 was inspected as an alternative, but its broader sign/verify feature graph was unnecessary for this bounded test. No conclusion about its suitability is inferred.

## Measured outcomes

All 66 recorded outcomes passed expected assertions. Four combinations were exercised: Go→Go, Go→Rust, Rust→Go, Rust→Rust. [Measurement snapshot](../experiments/signing-interop/results.json) contains individual outcomes.

The signed payload is the existing 762-byte statement, without reserialization, SHA-256 `d56168540b70fca582fd2f39752f72617e0c2d246890f447341b712ac29eacec`. Its existing schema validates, with exactly one subject. The two producers use different public test keys. Each consumer returns the exact original raw bytes after verification. The [DSSE protocol](https://github.com/dsse-lf/dsse/blob/v1.0.2/protocol.md) binds payload type and body through PAE; no JCS or catalogue format change is introduced.

| Case | Observed result |
| --- | --- |
| Same raw statement; valid envelope whitespace/key-order changes | Signature verifies; returned bytes exactly equal original |
| Payload byte appended; payload type changed; signature bit flipped | Verification fails in both languages |
| Different public key, same key hint | Signature verification fails in both languages |
| Correct signature/key, key absent from local trusted set | Signature valid; signer trust false, recorded separately |
| Correct signed statement, altered candidate bytes | Signature valid; exact subject binding false; fingerprint comparison not checked |
| Correct signature over duplicate-key inner statement | Both libraries authenticate exact bytes; strict application parsing rejects duplicate `_type`; schema is not evaluated after parsing rejection |
| Duplicate outer envelope key | Strict Python preflight rejects; separate native probe: Go accepts last value, Rust rejects duplicate field |
| Changed unsigned `keyid` hint | Go rejects because its provider filters mismatched nonempty IDs; Rust verifies with explicitly supplied key |
| Empty signature list; invalid payload base64 | Rejected |
| Envelope >16 KiB; decoded payload >8 KiB | Rejected by explicit harness policy before cryptographic verification |
| Existing full catalogue opening | Existing Python helper reproduces the exact existing commitment vector and signed commitment |
| Altered opening bytes/nonce; nonce lengths 0, 31, 33 | Changed openings mismatch; invalid nonce lengths rejected |

Native duplicate parsing and key-hint differences have explicit expected assertions, so drift fails a rerun. The key hint never selects trusted keys in the harness: public keys are supplied explicitly. This experiment does not resolve the differing hint semantics or propose a production adapter. The commitment check uses the existing **Python** implementation of `SHA256(D || R || L || C)`; it is not independent Go/Rust commitment interoperability. No new normative schema is added.

## Isolation, checks and limits

Dependencies were fetched online first. Verification then ran under macOS `sandbox-exec` with `(deny network*)`, inherited by subprocesses. The harness required and observed `PermissionError` on a local socket bind; both cross-verification directions completed under that restriction. It performed no TSA/log/key lookup and did not fetch signed references or execute candidate bytes. This is a runtime isolation check on one OS, not a formal proof of dependency supply-chain safety.

Host: Apple M5 Pro, arm64, macOS 26.4; Go 1.27.3, rustc 1.97.1. A warm complete harness run took 0.4218 s, including subprocess launches and all cases, excluding dependency fetch/build. This is one observation, not a latency percentile, memory benchmark or basis for the previously proposed 50 ms/32 MiB gates. No peak RSS was measured.

Checks completed: cached Go build with `GOPROXY=off GOSUMDB=off` and `-mod=readonly`; `go vet`; Rust release build with `--locked --offline`; `cargo fmt --check`; network-denied 66-outcome harness; repository `tools/validate.py`; all six existing contract tests. Reproduction commands are in the [experiment README](../experiments/signing-interop/README.md).

This is not a full hostile-input validator. Only bounded fixtures, selected duplicate fields, one signature and one Ed25519 algorithm were exercised; no parser fuzzing, nesting-depth corpus, multi-signature threshold, malformed-point corpus, streaming/racing input, certificate/revocation, compromise-time or platform matrix was evaluated. Timestamp evidence is unavailable; empirical fingerprint comparison and rights assessment are not checked. A valid signature authenticates bytes under a key and does not establish truth, identity, ownership or trusted time. The next increment can isolate timestamp target bytes and trust roots without changing this successful bare-envelope test.
