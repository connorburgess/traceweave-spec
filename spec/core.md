# Traceweave core — 0.1.0-draft.1

Status: proposed normative requirements for this draft only. MUST, MUST NOT, SHOULD and MAY express requirement levels; they are not evidence that an implementation exists. This draft is not a stable standard.

<a id="evidence-0.1.0-draft.1"></a>

## Claims and records

An **artifact** is an exact byte sequence. A **fingerprint** is a profile-defined feature representation. A **catalogue** stores private references and their extraction context. A **commitment** binds a record to exact private catalogue bytes. An **attestation** signs a record. A **match report** describes an observed comparison.

These objects have different meanings. A valid signature does not establish the truth of an assertion. A fingerprint match does not establish authorship, permission, infringement, or training membership. A self-declared creation time is not an independently verified time.

The core evidence predicate records `specVersion`, `contentKind`, an extraction profile, and a private catalogue commitment. An optional in-toto adapter binds the predicate to one exact subject using SHA-256. Other content profiles can reuse the predicate without assuming a Git repository exists.

The profile includes `id`, `version`, and `configSha256`. The configuration digest binds exact configuration bytes; parameter order or whitespace changes those bytes. An implementation MUST retain them. A matching implementation MUST reject unknown profile/version combinations rather than silently apply another algorithm.

`recordedAt` is an optional claimed time only. No timestamp token or identity proof is represented by that string. `contentKind` is a coarse Traceweave category, not a MIME type.

## Private catalogue commitment

This draft proposes a salted exact-byte commitment. It has not had an independent protocol review. Let:

- `D` be UTF-8 bytes of `Traceweave-Catalogue-v0.1` followed by one zero byte.
- `R` be a 32-byte nonce generated with an operating-system cryptographic random source, kept private with the opening.
- `C` be the exact private catalogue byte sequence.
- `L` be the length of `C` encoded as an unsigned 64-bit big-endian integer.

`commitment = SHA256(D || R || L || C)`, encoded as 64 lowercase hexadecimal characters.

The public record contains the scheme identifier `sha256-salted-catalogue-v1` and the digest only. It MUST NOT include `R` or `C`. Use fresh nonces per commitment; never reuse the synthetic vectors' nonce in production. Opening a commitment discloses the entire catalogue and nonce. Selective disclosure is not specified in this draft.

The catalogue MUST bind the extraction profile, configuration digest, exact reference artifact digests, feature representations, and source coordinates or media ranges. Merely committing a list of hashes without their interpretation is insufficient for reproduction. The catalogue's internal schema awaits a concrete fingerprint profile; synthetic fixtures demonstrate the commitment operation only.

Re-serializing a catalogue creates different bytes and normally a different commitment. Keep the exact opening. A commitment supports later consistency checks; timestamping it can support prior existence. Neither establishes who created or owns the content.

## Privacy defaults

Local extraction and comparison MUST be available without public network registration. Keys, private catalogues, and real evidence MUST NOT be placed in source trees by default. Publishing a record, subject digest, signature identity, or log event is a separate disclosure action; it can reveal use of Traceweave or permit correlation even when the catalogue stays private.

No privacy guarantee is made for truncated hash queries. No remote resolver is required by the core. A future resolver profile must describe its leakage to the operator, other participants, and observers, and assess adaptive queries and dictionary attacks.

## Interpretation

Implementations MUST keep exact-digest verification, signature verification, signer trust, timestamp verification, fingerprint comparison, and rights assessment as separate results. A soft match MUST NOT be reported as a valid exact subject digest. A failed comparison means insufficient matching evidence, not proof that reuse did not occur.

Rights metadata MUST be treated as claims with supporting references. Retain historical licenses and mixed-origin regions. A technical ancestry match can be real even when reuse is permitted. Neither a permissive-era label nor a post-transition commit alone settles permitted conduct.
