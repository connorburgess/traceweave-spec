# Optional timestamp adapter decision record

Status: recorded decision for core gate **M4.5**, synthesizing [attestations](../../spec/attestations.md), [lane 13](../lanes/13-timestamp-evidence-review.md), and [registration-record.md](registration-record.md).

## 1. Context

Core gate M4.5 requires a recorded architectural decision on the optional timestamp adapter alongside the in-toto/DSSE adapter fixtures and the verifier trust-policy specification.

Traceweave separates cryptographic signing from trusted time:
- A bare DSSE-signed statement authenticates exact payload bytes under a key, but a key holder can backdate `claims.createdAt` or `recordedAt` at will (`lane 13` T7).
- By contrast, obtaining live external timestamps introduces network dependencies, provider terms, IP/timing metadata exposure, and (for public logs or blockchains) permanent metadata commitments (`registration-record.md` §5, §17).
- Verification must remain strictly **offline-first** (`spec/core.md` privacy defaults; `trust-policy.md` §7), never requiring live contact with external services during verification or specification CI.

## 2. Decision

1. **Timestamping is an optional adapter, never mandatory for valid DSSE statements.**
   - A Traceweave DSSE attestation without attached time evidence remains a valid signed statement.
   - When no valid time evidence is present, per-signature time outcomes MUST be reported as `none-valid`, and any self-declared `claims.createdAt` or `recordedAt` MUST be reported strictly as `claimed-only` (or `absent` / `not-compared` when no trusted signature exists).
   - Verifiers MUST NEVER fabricate, infer, or upgrade claimed dates (`claims.createdAt`, `recordedAt`, A2A metadata, git dates) into proved time bounds (`claimed-as-proved`).

2. **Offline-first verification of RFC 3161 and OpenTimestamps against local retained material is supported.**
   - **RFC 3161 (`rfc3161`):** Verifiers evaluate RFC 3161 `TimeStampResp` tokens offline against retained DER root certificates, token-carried intermediate chains (RFC 5280 path validation at `genTime`), and retained CRL/OCSP `revocationData` (with explicit `revocationDataAsOf` reporting and RFC 4998-style token renewal support).
   - **OpenTimestamps (`opentimestamps`):** Verifiers evaluate upgraded OpenTimestamps proofs offline against the verifier's own retained Bitcoin block header source and a verifier-pinned `checkpoint` (`minConfirmations >= 1`), deriving `notAfter = blockTime + 7200s` under the stated honest-majority assumption. Pending proofs (`PendingAttestation`) receive outcome `pending` and never contribute a time bound.
   - **Recommended multi-source baseline:** Two unrelated RFC 3161 TSAs plus OpenTimestamps (`quorum = 2` over verifier-assigned `independenceGroup` labels), so one retroactive TSA revocation still preserves a quorum. Both `notAfterAnyRoot` and `notAfterQuorum` are always reported separately per signature.
   - **Target binding:** Time evidence countersigns **only** the SHA-256 of raw decoded DSSE signature bytes (or an earlier evidence token's raw bytes for renewal), never base64 envelope text, statement bytes, or artifact bytes directly.

3. **Live external TSA / OpenTimestamps contact remains strictly optional and owner-gated (`REG.3`).**
   - No specification test, validator, or offline verifier contacts any external TSA, OpenTimestamps calendar, transparency log, or witness.
   - Submitting even a single synthetic digest to live external services requires explicit owner approval under proposed gate `REG.3` (`registration-record.md` §15, §17), covering provider selection, terms-of-service review, and acceptance of network metadata disclosure (requester IP/timing to TSAs and calendars; permanent Bitcoin Merkle root anchoring for OpenTimestamps).
   - Until `REG.3` is approved and executed, real-format test vectors use locally generated test-only TSA certificates and locally mined regtest-difficulty headers whose anchors are explicitly untrusted in production (`trust-policy.md` §6).

4. **Transparency logs and hosted witnesses remain optional and deferred.**
   - Sigstore Rekor v2 (`rekor-v2`) provides inclusion and public discoverability only; it carries no independent clock (`log-time-claimed` if time is asserted) and remains opt-in and owner-gated (`RD3`).
   - Hosted witness cosigning (`traceweave-witness`) remains optional and deferred behind `SK.5` (`registration-record.md` §19.2); if configured in a policy, its witness key and backing TSA join independence groups together.
   - `cosigned-checkpoint` without an inclusion proof is removed/rejected (`evidence-shape`).

## 3. Consequences

- **Enabled immediately:**
  - Deterministic offline verification of DSSE-signed Traceweave statements (`none-valid` / `claimed-only` when untimestamped).
  - Deterministic offline verification of locally retained RFC 3161 tokens, OpenTimestamps proofs, certificate revocations, and renewals under [trust-policy.md](trust-policy.md).
- **Explicitly forbidden:**
  - Treating `recordedAt` or `claims.createdAt` as proved time.
  - Counting `pending` OpenTimestamps proofs or unpinned header sources.
  - Embedding proved timestamps inside the signed statement predicate (`time-in-statement`).
  - Making live outbound network requests from `tools/validate.py`, offline verifiers, or CI.

## 4. Alternatives considered

- **Mandatory external timestamping for all statements:** Rejected. Violates local-first / offline-first privacy defaults (`spec/core.md`), blocks air-gapped workflows, and forces external network metadata disclosure on every attestation.
- **RFC 3161 only (omitting OpenTimestamps):** Not chosen as the sole mechanism. Two TSAs reduce single-operator risk, but OpenTimestamps provides an operator-independent proof-of-work anchor; implementations may still evaluate RFC 3161 first while supporting OpenTimestamps offline when a local header source is configured.
- **Rekor v2 as primary time source:** Rejected. Rekor v2 delegates time to an external TSA anyway and publishes keys/identities permanently.
