# Traceweave ↔ in-toto Statement v1 / DSSE adapter fixtures (M4.5)

Illustrative accept and reject fixtures for core gate **M4.5**, exercising the restricted Traceweave in-toto Statement v1 / DSSE adapter defined in [attestations](../../../spec/attestations.md), [core](../../../spec/core.md), [registration-record.md](../registration-record.md), and [trust-policy.md](../trust-policy.md).

**Test-only keys and nonces.** All Ed25519 keys, key identifiers, and nonces in these fixtures are synthetic values derived deterministically from fixed public labels in [build_fixtures.py](build_fixtures.py). Never use them in production. No external TSA, calendar, or transparency log was contacted.

## Contents

- [accept/](accept/) — 4 valid DSSE-signed Statement v1 fixtures:
  - `accept-catalogue-core.json`: core catalogue-commitment statement (`evidence-0.1.0-draft.1`) over `examples/artifact.txt` and `examples/catalogue.json`, canonical JCS payload bytes, standard base64.
  - `accept-catalogue-core-urlsafe.json`: core catalogue-commitment statement with optional claimed `recordedAt`, pretty-printed non-canonical payload bytes (verifying PAE signs exact decoded bytes, not reserialized JSON), and URL-safe base64 DSSE encoding.
  - `accept-registration-draft5.json`: registration statement (`registration/draft-5`) over `sum.go` (`test-vectors/matching/extraction-go.json#mv-go-sum`) with possession digest and salted catalogue commitment.
  - `accept-registration-ai-use.json`: multi-subject registration statement (`sum.go`, `host.go`) with optional self-declared `claims.aiUse` and omitted `catalogue`.
- [reject/](reject/) — 21 distinct negative fixtures covering:
  - Statement/adapter structure: `reject-wrong-type`, `reject-wrong-predicate-type`, `reject-missing-statement-field`, `reject-missing-predicate-field`, `reject-extra-field-statement`, `reject-extra-field-predicate`, `reject-core-multiple-subjects`, `reject-malformed-subject-digest`.
  - DSSE & JSON strictness: `reject-invalid-base64`, `reject-wrong-dsse-payload-type`, `reject-duplicate-json-key`, `reject-signature-over-base64`, `reject-tampered-payload`, `reject-missing-key-hint`, `reject-empty-signatures`.
  - Trust & binding separation: `reject-subject-digest-mismatch` (valid signature, mismatched artifact digest), `reject-untrusted-key` (valid signature, key absent from `trustedKeys`).
  - Smuggling protections: `reject-authorship-smuggling-key`, `reject-authorship-smuggling-value`, `reject-time-claim-smuggling`, `reject-forbidden-secret-field`.
- [check_intoto_adapter.py](check_intoto_adapter.py) — standard-library-only checker (Python 3.11+) wired into [tools/validate.py](../../../tools/validate.py). Runs strict JSON parsing, DSSE PAE + strict RFC 8032 Ed25519 verification, full-key trust verification, schema/smuggling checks, subject/possession/catalogue bindings, canonical RFC 8785 / exact-byte round-tripping, required/extra-field self-tests, and reject-code coverage checks.
- [build_fixtures.py](build_fixtures.py) — deterministic fixture generator.

## Commands

From the repository root:

```sh
python3 -I research/drafts/intoto-adapter-fixtures/build_fixtures.py
python3 -I research/drafts/intoto-adapter-fixtures/check_intoto_adapter.py --verbose
```
