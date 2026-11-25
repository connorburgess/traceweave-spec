# Attestations and interoperability

Status: experimental draft, normative for conformance of this draft version, aligned with [registration-record.md](registration-record.md) (`traceweave-registration-draft-5`), [trust-policy.md](trust-policy.md), and [timestamp-adapter-decision.md](../docs/decisions/timestamp-adapter-decision.md).

## in-toto and DSSE

Traceweave supports two restricted in-toto Statement v1 / DSSE adapter forms, both verified by [test-vectors/intoto-adapter/](../test-vectors/intoto-adapter/README.md) (`check_intoto_adapter.py`):

- **`0.1.0-draft.1` minimal commitment statement** ([schemas/statement.schema.json](../schemas/statement.schema.json), [schemas/evidence.schema.json](../schemas/evidence.schema.json)): `_type: https://in-toto.io/Statement/v1`, `predicateType: https://github.com/connorburgess/traceweave-spec/blob/main/spec/core.md#evidence-0.1.0-draft.1`, one subject with a SHA-256 digest, `contentKind` in `["code", "text", "image", "audio", "binary", "other"]`, top-level `profile`, and required `catalogueCommitment` (`sha256-salted-catalogue-v1`).
- **`traceweave-registration-draft-5` registration statement** ([registration-record.md](registration-record.md) §4): `_type: https://in-toto.io/Statement/v1`, `predicateType: https://traceweave.org/predicate/registration/draft-5`, `1..64` unique-digest subjects, `contentKind` in `["text", "source-code", "image", "other"]`, 32-byte OS CSPRNG `nonce`, `possession` (`sha256-salted-possession-v1`), optional `catalogue` (`sha256-salted-catalogue-v1` with `profile`), `implementation`, `specCommit`, and `claims` (`createdAt`, optional `aiUse`).

This is a deliberately restricted Traceweave adapter, not a complete validator for arbitrary in-toto statements. Draft predicate identifiers under the project GitHub URL or `traceweave.org` are provisional; they are not standards registrations.

For DSSE, `payloadType` is `application/vnd.in-toto+json`. Sign the actual decoded payload bytes using the upstream pre-authentication encoding:

```text
PAE(type, body) = "DSSEv1" + SP + LEN(type) + SP + type + SP + LEN(body) + SP + body
```

Lengths count bytes, encoded as ASCII decimal without leading zeroes. `SP` is the ASCII space byte. The payload's base64 text is not the signing input (verifiers MUST accept both standard and URL-safe base64). Retain the verified byte sequence through parsing. Reject ambiguous JSON (including duplicate keys and non-finite constants) under the strict parsing policy ([trust-policy.md](trust-policy.md) §4.1). Key identifiers (`keyid`) are lookup hints, not proof of identity; full key identity is `SHA-256(raw 32-byte Ed25519 public key)`. [DSSE protocol](https://github.com/dsse-lf/dsse/blob/master/protocol.md), [in-toto statement](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md).

Normative commitment and selective-disclosure verification rules — including `sha256-salted-catalogue-v1`, `sha256-salted-possession-v1`, independent OS CSPRNG nonce generation, and `catalogueOpening` verification — are specified in [core.md](core.md#private-catalogue-commitment) and [registration-record.md](registration-record.md) (§4.2–§4.4, §9), with fixtures in [test-vectors/registration/](../test-vectors/registration/README.md). `possession[i]` binds to a signer key only through the enclosing verified DSSE signature over the statement.

**Side-channel boundary.** Comparing public commitment digests during `catalogueOpening` verification does not compare secret material (both `R` and `C` are supplied by the opener). By contrast, private Ed25519 signing and OS CSPRNG nonce generation operate on secret material and MUST use constant-time / side-channel-safe cryptographic primitives and OS CSPRNG APIs with no non-cryptographic fallback.

A signed statement can remain intact while a derived artifact changes. In that case the statement signature may verify while the subject digest fails. Report both results separately; a soft match does not repair that digest.

## Trust and time

Verifiers MUST evaluate signatures, signer trust, key events, and time evidence against an explicit local policy as specified in [trust-policy.md](trust-policy.md). Identity strings inside a signed payload are assertions, not independent identity authentication. Signing someone else's public content does not establish ownership.

Self-managed signing, private evidence storage, and strictly offline-first verification are normative defaults ([timestamp-adapter-decision.md](../docs/decisions/timestamp-adapter-decision.md)). Timestamping is an optional adapter, never mandatory for valid DSSE statements: untimestamped statements report time outcome `none-valid` and any `claims.createdAt` / `recordedAt` strictly as `claimed-only`. When attached, offline verification supports locally retained RFC 3161 tokens and OpenTimestamps proofs against local pinned anchors and revocation data ([trust-policy.md](trust-policy.md) §5–§7). Sigstore Rekor v2 (`rekor-v2`) provides inclusion/discoverability only with no independent clock, and hosted witness cosigning remains deferred behind `SK.5`.

An RFC 3161 integration must preserve and verify the signed token, message imprint, algorithm, TSA signature, RFC 5280 trust chain at `genTime`, retained revocation data (`revocationDataAsOf`), and applicable policy OIDs ([trust-policy.md](trust-policy.md) §6–§7). An ISO date string is not a timestamp token. Time evidence countersigns only the SHA-256 of raw decoded DSSE signature bytes (or an earlier evidence token's raw bytes for RFC 4998-style renewal). Long-term archival verification requires retained trust material, revocation data, and renewal before TSA certificate expiry. [RFC 3161](https://www.rfc-editor.org/rfc/rfc3161).

## C2PA mapping remains open

Traceweave should reuse existing content-provenance infrastructure where possible. No C2PA compatibility is claimed yet. A future mapping must specify hard bindings, soft-binding discovery, assertion transport, signer trust, private disclosure, and independent test artifacts. Referencing C2PA terminology does not establish interoperability.
