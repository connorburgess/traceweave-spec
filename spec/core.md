# Traceweave core — 0.1.0-draft.1

Status: proposed normative requirements for this draft only. MUST, MUST NOT, SHOULD and MAY express requirement levels; they are not evidence that an implementation exists. This draft is not a stable standard.

<a id="evidence-0.1.0-draft.1"></a>

## Claims and records

An **artifact** is an exact byte sequence. A **fingerprint** is a profile-defined feature representation. A **catalogue** stores private references and their extraction context. A **commitment** binds a record to exact private catalogue bytes. An **attestation** signs a record. A **match report** describes an observed comparison.

These objects have different meanings. A valid signature does not establish the truth of an assertion. A fingerprint match does not establish authorship, permission, infringement, or training membership. A self-declared creation time is not an independently verified time.

The core evidence predicate records `specVersion`, `contentKind`, an extraction profile, and a private catalogue commitment. An optional in-toto adapter binds the predicate to one exact subject using SHA-256. Other content profiles can reuse the predicate without assuming a Git repository exists.

Extraction is specified in the [extraction contract](extraction.md) and catalogues, comparison and reports in the [catalogue and report contract](catalogue-report.md); both are experimental drafts. The profile includes `id`, `version`, and `configSha256`. The configuration digest binds exact configuration bytes; parameter order or whitespace changes those bytes. An implementation MUST retain them. A matching implementation MUST reject unknown profile/version combinations rather than silently apply another algorithm.

`recordedAt` is an optional claimed time only. No timestamp token or identity proof is represented by that string. `contentKind` is a coarse Traceweave category, not a MIME type.

## Private catalogue commitment

Normative exact-byte commitments and opening verification rules are specified here and in [registration-record.md](registration-record.md) (§4.2–§4.4, §9), with vectors in [test-vectors/commitment.json](../test-vectors/commitment.json), [test-vectors/registration/](../test-vectors/registration/README.md), and [test-vectors/intoto-adapter/](../test-vectors/intoto-adapter/README.md). Let:

- `D` be UTF-8 bytes of `Traceweave-Catalogue-v0.1` followed by one zero byte.
- `R` be a 32-byte nonce generated with an operating-system cryptographic random source (no non-cryptographic fallback), never all-zero, and kept private with the opening. When paired with a registration statement's `predicate.nonce`, `R` MUST be drawn independently and MUST NOT equal `predicate.nonce` (`nonce-reused`).
- `C` be the exact private catalogue byte sequence.
- `L` be the length of `C` encoded as an unsigned 64-bit big-endian integer.

`commitment = SHA256(D || R || L || C)`, encoded as 64 lowercase hexadecimal characters.

The public record contains the scheme identifier `sha256-salted-catalogue-v1` and the digest only. It MUST NOT include `R` or `C`. Use fresh nonces per commitment; never reuse the synthetic vectors' nonce in production. Opening a commitment discloses the entire catalogue `C` and nonce `R`. Selective disclosure is not specified in `v1`; registrants requiring per-file selective disclosure SHOULD register one work/catalogue per statement rather than batching unrelated works.

The catalogue MUST bind the extraction profile, configuration digest, exact reference artifact digests, feature representations, and source coordinates or media ranges. Merely committing a list of hashes without their interpretation is insufficient for reproduction.

Re-serializing a catalogue creates different bytes and normally a different commitment. Producers MUST retain `C` as exact raw bytes (never re-serialized before opening). Verifiers MUST enforce a bounded size cap when checking `C` (`1 MiB` / `1,048,576` bytes in the M4 policy/harness) and stream/bound artifact hashing for `A`. A commitment supports later consistency checks; timestamping it can support prior existence. Neither establishes who created or owns the content.

### Salted possession digest

`sha256-salted-possession-v1` binds a registration statement to possession of exact artifact bytes `A` using the statement's fresh 32-byte `predicate.nonce` ([registration-record.md](registration-record.md) §4.2–§4.3):

- `D` be UTF-8 bytes of `Traceweave-Possession-v1` followed by one zero byte (`0x00`).
- `nonce` be the 32-byte random value in `predicate.nonce`, drawn from an operating-system cryptographic random source (no non-cryptographic fallback), never all-zero and never reused across registrations.
- `A` be the exact original artifact bytes.
- `L` be the length of `A` encoded as an unsigned 64-bit big-endian integer.

`possession[i].sha256 = SHA256(D || nonce || L || A)`, encoded as 64 lowercase hexadecimal characters.

`possession[i]` binds to a signer key **only** through the enclosing verified DSSE signature over the statement ([registration-record.md](registration-record.md) §4.3, §6.1). Once a registration statement is disclosed, `predicate.nonce` is public, so `possession[i]` does not protect low-entropy artifacts from offline confirmation guessing.

### Catalogue opening verification

When verifying a `catalogueOpening` (`{catalogue, nonceHex}`, [registration-record.md](registration-record.md) §9), a verifier MUST enforce all of the following:

1. `nonceHex` MUST be exact 64 lowercase hexadecimal characters (`HEX64`, 32 bytes) and MUST NOT be all zeros (`nonce-invalid`).
2. `nonceHex` MUST NOT equal the statement's `predicate.nonce` (`nonce-reused`).
3. `SHA256("Traceweave-Catalogue-v0.1\x00" || bytes.fromhex(nonceHex) || uint64be(len(C)) || C)` MUST equal `predicate.catalogue.sha256` (`catalogue-does-not-open`).
4. When linking to a comparison report (`report-link`), `C` MUST be retained as exact raw bytes (bounded to the verifier's maximum catalogue size), `SHA256(C)` MUST equal the report's `referenceCatalogueSha256` (or `candidateCatalogueSha256` when every linked entry has `role: "candidate"`, `catalogue-not-report-input`), and `predicate.catalogue.profile` MUST equal the report's `profile` (`profile-mismatch`).

## Privacy defaults

Local extraction and comparison MUST be available without public network registration. Keys, private catalogues, and real evidence MUST NOT be placed in source trees by default. Publishing a record, subject digest, signature identity, or log event is a separate disclosure action; it can reveal use of Traceweave or permit correlation even when the catalogue stays private.

No privacy guarantee is made for truncated hash queries. No remote resolver is required by the core. A future resolver profile must describe its leakage to the operator, other participants, and observers, and assess adaptive queries and dictionary attacks.

## Interpretation

Implementations MUST keep exact-digest verification, signature verification, signer trust, timestamp verification, fingerprint comparison, and rights assessment as separate results. A soft match MUST NOT be reported as a valid exact subject digest. A failed comparison means insufficient matching evidence, not proof that reuse did not occur.

Rights metadata MUST be treated as claims with supporting references. Retain historical licenses and mixed-origin regions. A technical ancestry match can be real even when reuse is permitted. Neither a permissive-era label nor a post-transition commit alone settles permitted conduct.
