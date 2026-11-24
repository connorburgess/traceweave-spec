# Registration record: design draft-3

Status: research draft, draft-3 of 2026-11-24. It resolves the [draft-2 confirmation review](../reviews/registration-record-draft-2-review.md) (`66aec94`); §22 maps B1–B3, S1–S13 and N1–N4 to sections and fixtures. Draft-2 resolved the first [review](../reviews/registration-record-review.md) (`5c3d9c5`), and §21 keeps that table. Not normative. No schema, profile, vector or roadmap file is changed by this draft. **No external time-stamping service, calendar, log or witness was contacted.** Placeholder evidence is labelled as such. The real-format vectors (§6.5) come from a local test-only TSA run with `openssl` and from a synthetic OpenTimestamps proof against a locally mined header file.

Evidence for the mechanisms is in [lane 13](../lanes/13-timestamp-evidence-review.md), cited as T1–T9 and L1–L2. Context:
- the [roadmap](../../ROADMAP.md) finding of 2026-11-23 that a mark is a finding aid and not evidence of origin; M4;
- [attestations](../../spec/attestations.md); [core](../../spec/core.md);
- the [catalogue and report contract](../../spec/catalogue-report.md) §6.6–§8 (B10);
- [use cases](../../docs/use-cases.md) UC-3 and UC-4;
- the [C2PA mapping draft](c2pa-mapping.md); the [lane 11 audit](../lanes/11-report-audit.md) (signed reports are M4).

**What changed from draft-2:**
- **Key handling** (§8):
  - Keys are identified by the SHA-256 of the full public key, never by the 64-bit `keyid` hint (B3).
  - Key events are evaluated in order of proved time, independent of input order (B2).
  - A compromise disputes later rotations and retirements of the key, no trust flows through a disputed rotation, and conflicting rotations are both disputed (B1).
  - With no quorum bound, a signature touched by a key event is `disputed` (S1).
- **Time evidence** (§6):
  - RFC 3161 token checks are specified and run on real-format vectors (S2, S9, S10).
  - Revocation data carries its source and date (S3).
  - A witness counts with the TSA its time comes from (S4).
  - `cosigned-checkpoint` is removed (S5).
  - Renewal is defined (S6).
  - Times are rounded up and the OpenTimestamps header source is pinned (N1, N2).
- **Verification and wording:**
  - URL-safe base64 is accepted (S7).
  - "Registrant", not "creator", throughout; renderings may not order two registrations (S8).
  - The claim is compared with trusted signatures only (S11).
- **C2PA and the roadmap:** the C2PA row is corrected (S12), and exact ROADMAP.md text is proposed for the gates (S13; ROADMAP.md is not edited here).
- Every object version string ends in `draft-3`.

## 1. Summary

A **registration record** lets a registrant later show: *these exact bytes existed, and my key signed a statement naming them, no later than time T.* It is a signed in-toto statement (DSSE), plus time evidences attached as separate objects. Each time evidence countersigns **one** signature under **one** trust anchor. A verifier reports each part separately:
- the digest and possession checks;
- each signature and its signer trust;
- each key event;
- each time evidence;
- **for each signature**, the earliest single-source bound and the bound agreed by a quorum of independent sources.

There is never a single "authentic" verdict.

A registration does **not** show authorship, originality, ownership or permission. It does not show that the registrant created the content rather than copied it first. **First to register is not first to create.** §11 makes this text mandatory wherever a registration is shown to a person, and allows only listed line templates.

A registration does not depend on the content's profile. Python source under `py-tokens` draft-1 is registered exactly like Go, Rust or any other bytes; the profile matters only for the optional catalogue commitment (§4.4).

Recommended first mechanisms: **RFC 3161 time-stamp tokens from two unrelated TSAs** and **OpenTimestamps** (Bitcoin), with quorum 2 (§13). That is three time sources, so losing one, for example to a TSA certificate revocation, still leaves two. Every result also states how current its revocation data is (§6.7): offline verification holds only as of that date.

## 2. Terms

- **Claimed time:** a time written by the registrant (`claims.createdAt`), like core's `recordedAt` and the report's `generatedAt`. Anyone can write any value. It is never shown as proved.
- **Bound (`notAfter`):** an upper bound on when one signature existed, from one verified time evidence under the verifier's policy. Time evidence gives only upper bounds. Nothing here proves a lower bound or a creation time.
- **Trust anchor:** what a time source's validity ultimately rests on, identified by a SHA-256 the verifier computes, never by a name the producer writes:
  - TSA: the DER root certificate of the token's chain;
  - Bitcoin: the chain as pinned by the verifier's own node or header file;
  - log or witness: the public key.
- **Independence group:** a label in the **verifier's** policy. Anchors in the same group count once. An evidence that rests on several anchors (a witness and its TSA) joins their groups (§6.3).
- **Key identity:** the SHA-256 of the raw 32-byte Ed25519 public key. The 16-hex `keyid` is only a lookup hint (B3).
- **Placeholder versus real format:** in placeholder fixtures the anchor digest and certificate dates are written by the producer and accepted as given. Only the real-format vectors (§6.5) test that the verifier computes them (S10).

## 3. Objects

All version strings and predicate URLs are proposals in the `traceweave.org` namespace, which [C2PA draft](c2pa-mapping.md) D3 also leaves to the owner.

| Object | Version string | Content | Fixture |
| --- | --- | --- | --- |
| Registration statement | `traceweave-registration-draft-3`; predicate type `https://traceweave.org/predicate/registration/draft-3` | in-toto Statement v1 (§4) | `statement.json` |
| Bundle | `traceweave-registration-bundle-draft-3` | DSSE envelope with one or more signatures, public keys, time evidences | `bundle-three-roots.json`, `bundle-cosigned.json`, `bundle-second-work.json` |
| Time evidence | `traceweave-time-evidence-draft-3` | One evidence: target (a signature, or the token of an earlier evidence for renewal), trust anchor, type-specific fields or a real-format token (§6) | `evidence-*.json` |
| Witness statement | `traceweave-witness-draft-3`; predicate type `https://traceweave.org/predicate/witness/draft-3` | A hosted witness's signed statement, used as evidence type `traceweave-witness` (§6.2, §19) | `evidence-witness.json` |
| Key event | `traceweave-key-event-draft-3`; predicate type `https://traceweave.org/predicate/key-event/draft-3` | Retire, rotate or report a key compromised, time-stamped like a registration (§8) | `key-event-*.json` |
| Verification result | `traceweave-registration-verification-draft-3` | The closed outcomes of §10, with the policy used | `verification-result*.json` |
| Report link | `traceweave-registration-link-draft-3` | Ties a comparison report to a registration without changing the report (§9) | `report-link.json` |
| Registration set | `traceweave-registration-set-draft-3` | Several registrations by one producer, for the nonce-freshness check (§4.2) | `registration-set.json` |
| Rendering | `traceweave-registration-rendering-draft-3` | User-facing lines from the §11 templates | `rendering*.json` |

## 4. The registration statement

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [{"name": "sum.go", "digest": {"sha256": "974c8d0a…697c"}}],
  "predicateType": "https://traceweave.org/predicate/registration/draft-3",
  "predicate": {
    "registrationVersion": "traceweave-registration-draft-3",
    "contentKind": "source-code",
    "nonce": "<64 hex: 32 fresh random bytes>",
    "possession": [{"subjectIndex": 0, "scheme": "sha256-salted-possession-v1", "sha256": "…"}],
    "catalogue": {"scheme": "sha256-salted-catalogue-v1", "sha256": "…", "profile": {"configSha256": "…", "id": "go-tokens", "version": "draft-1"}},
    "implementation": {"name": "…", "version": "…", "commit": "<40 hex>"},
    "specCommit": "<40 hex>",
    "claims": {"createdAt": "2026-11-20T09:00:00Z"}
  }
}
```

### 4.1 Subjects

- Each subject is the SHA-256 of the **original artifact bytes**, exactly as stored, with no normalization (`sha256`, contract §3.2).
- There are one to 64 subjects, and no two share a digest.
- `name` is an opaque label with the catalogue id pattern `^[a-z0-9][a-z0-9._-]{0,63}$`, so it cannot hold a path (`subject-name`). in-toto matches subjects "purely by digest", so the name rule is a local one.

**Producer obligation:** hash the original bytes. A verifier can check this only when the bytes are supplied (§10 step 5). Without them, the only correct outcome is `not-supplied`; reporting `match` is wrong (`neg-subject-unsupplied-match`).

### 4.2 Nonce

`nonce` is 32 fresh bytes from an operating-system random source, new for every registration. It has two jobs:
- It makes the statement bytes unguessable, so the signature digest sent to time services reveals nothing, even to someone holding the content (§5).
- It salts the possession digest.

An all-zero or malformed nonce is rejected (`nonce-invalid`).

**Producer obligation:** never reuse a nonce. Reuse cannot be seen in one record. A verifier given several registrations by the same producer checks that their nonces differ (`registration-set`; `nonce-reused`).

### 4.3 Possession digest

`possession[i].sha256 = SHA256("Traceweave-Possession-v1" || 0x00 || nonce || L || A)`, where `A` is the artifact bytes and `L` its length as an unsigned 64-bit big-endian integer. This mirrors the core commitment framing.

*What it adds.* A time evidence over a plain artifact digest shows that *someone* knew that digest by T, and a digest can be copied from anywhere it was published. The possession digest uses the registrant's own fresh nonce, so nobody could have computed it before the registration. Whoever made it held the bytes, or was given them, by T. The verifier recomputes it from the supplied bytes (`possession-mismatch`).

*What it does not add.* Anyone holding the bytes at registration time can compute it. So for content that was already public at T, it adds nothing, and it never excludes a copier. Once the statement is disclosed, the nonce is known, and the possession digest confirms guessed content just as the artifact digest does (§5).

### 4.4 Catalogue commitment (optional)

`catalogue` commits to the private catalogue with the existing salted scheme `sha256-salted-catalogue-v1` ([core](../../spec/core.md#private-catalogue-commitment)), plus the profile triple. It lets a later comparison report be tied to the registered catalogue (§9) without revealing fingerprints now. A plain catalogue digest is rejected (`catalogue-unsalted`; §5 explains why). The catalogue bytes committed to and later opened are the exact stored catalogue bytes, which for the fixtures are the RFC 8785 bytes of the catalogue object (contract §3.3).

### 4.5 Implementation provenance (B10)

`implementation` and `specCommit` have the report provenance form (contract §6.6), and the same rule applies: the commit is fixed at build time, and only by a verified, clean build (§6.8 B10). An unstamped build refuses to write a registration, as it refuses a report document (`provenance-shape` covers the form only). The fixtures carry placeholder all-zero commits, as `example-report.json` does. Provenance stays cooperative-build evidence: a registration signature attests who registered, not which code ran.

### 4.6 Claims, and the closed key lists

`claims.createdAt` is the only time in the statement, and it is claimed. The checker's lists are closed and are part of the rule:
- **Time keys** rejected anywhere in the predicate (`time-in-statement`): `provedAt`, `timestamp`, `notAfter`, `genTime`, `registeredAt`, `recordedAt`, `time`, `provedTime`.
- **Content keys** rejected anywhere in the predicate, and in hosted-route requests (`forbidden-field`): `fingerprints`, `tokens`, `source`, `text`, `content`, `catalogueBytes`, `opening`, `nonceHex`, `inputBase64`.
- Other unknown fields are rejected (`statement-shape`), and so is a wrong predicate type (`predicate-type`), including the types of earlier drafts.

## 5. What publishing each value reveals

A registration is **private by default**. The registrant keeps the bundle; only digests of signatures go to time services (§6). The table assumes the item named is published, for example in a dispute.

| Published value | Reveals about unknown content | Guessing attack | Verdict |
| --- | --- | --- | --- |
| Digest of a DSSE signature (what time services see) | Nothing; the statement contains a fresh 256-bit nonce | None feasible | Safe to send. Links the evidences of one registration to each other and to the requester's IP address and timing (T1 §4 item 5, T4) |
| Artifact digest (`subject`) | Nothing about content the attacker lacks | **Confirmation:** anyone holding a candidate file confirms exact equality. Low-entropy content (a short snippet, a template with few variants) can be enumerated | Disclose only with the bytes, in a dispute |
| Possession digest | Nothing without the nonce. After disclosure, the same as the artifact digest, so short snippets are not protected by it either | As the artifact digest, after disclosure | Disclosed with the statement |
| Salted catalogue commitment | Nothing until opened | None before opening. **Opening reveals the whole catalogue** (core) | Safe in the statement |
| Plain catalogue digest | Nothing directly | **Whole-set confirmation:** catalogues are deterministic in their artifacts, ids and configuration (contract §3.3), so anyone with candidate files and guessed ids rebuilds and confirms | Never (`catalogue-unsalted`) |
| Fingerprints | Structure, positions and spans | **Fragment membership:** anyone can fingerprint any text and learn which fragments the private content contains | Never in a registration (`forbidden-field`) |
| Public key | Links every registration made under it | — | One key per registrant (I0) links all disclosed registrations and all time-service requests under it. A per-work key avoids that, at the cost of identity continuity (§7) |
| OIDC identity in a public log | Identity, time and the logged digest, **for ever** (T3) | — | Opt-in only, owner-gated |

## 6. Time evidence

### 6.1 What is time-stamped (A1)

Each evidence targets **one** object:
- **A signature:** `target: {kind: "dsse-signature", signatureIndex, sha256}`. `sha256` is the SHA-256 of the **raw decoded signature bytes** (64 bytes for Ed25519), not of the base64 text in the envelope (`neg-evidence-target-base64`). This follows Sigstore's countersigning advice and C2PA's v2 payload (T3, T6).
- **An earlier evidence's token**, for renewal only (§6.6): `target: {kind: "evidence-token", evidenceIndex, sha256}`.

A signature exists only after its statement does, so a bound on the signature bounds the statement, including its subjects and possession digests. The bound also survives a later theft of the key: a thief can sign new statements but cannot obtain evidence dated before the theft. Evidence over another digest, such as the statement bytes, is rejected (`evidence-wrong-target`). So is an index the envelope does not have (`evidence-shape`; `neg-signature-index-out-of-range`).

### 6.2 Evidence types: fields, checks and bounds

Every evidence has `evidenceVersion`, `type`, `placeholder`, `notice`, `target`, `root: {kind, anchorSha256}` and `token`.
- **Placeholder evidence** (`placeholder: true`) adds one type-specific object, and its `token` text starts with `PLACEHOLDER`.
- **Real-format evidence** (`placeholder: false`, §6.5) carries the real token (and, for RFC 3161, the request) as base64, and every field is read from it.

A root identified by anything other than an anchor digest is rejected (`root-not-anchored`). Wrong labelling is rejected (`placeholder-unlabelled`). Malformed evidence is `evidence-shape`.

**`rfc3161`**, root kind `tsa-certificate-chain`. Placeholder fields: `rfc3161: {genTime, accuracySeconds (optional), policyOid, nonce, requestNonce, signerCertificate: {notBefore, notAfter}}`. The checks below run in this order, and the real-format vectors exercise every one (S2):
1. **Imprint.** `messageImprint.hashAlgorithm` is `id-sha256` and `hashedMessage` equals `target.sha256` (RFC 3161 §2.4.1–§2.4.2); otherwise `tsa-imprint-mismatch`.
2. **Request nonce.** The producer sends a fresh nonce in the request (§2.4.1) and checks that the token echoes it with the same imprint. That is what detects a replayed response at request time; otherwise `tsa-nonce-mismatch`.
3. **Signing certificate.** The SigningCertificate attribute, ESSCertIDv2 (RFC 5816 §2, "MUST be included") or ESSCertID, identifies the certificate named by the SignerInfo; otherwise `tsa-signing-cert-mismatch`.
4. **Key usage.** That certificate carries exactly one extended key usage, `id-kp-timeStamping`, marked critical (RFC 3161 §2.3); otherwise `tsa-eku-invalid`.
5. **Signature.** There is exactly one SignerInfo; the `messageDigest` attribute equals the SHA-256 of the TSTInfo; and the signature over the signed attributes verifies; otherwise `tsa-signature-invalid`.
6. **Chain.** The chain verifies to the **pinned root certificate** whose SHA-256 is the anchor (outcome `untrusted-root` or `invalid`).
7. **Policy OID.** The token's `policy` must be one the verifier's policy lists for that anchor (outcome `wrong-policy`).
8. **Certificate validity.** `genTime` must lie within the TSA certificate's validity (outcome `invalid`).
9. **Revocation** (RFC 3161 §4 items 1–2; §6.7). Revocation **without** a reasonCode, or with `keyCompromise`, invalidates **every** token of that key, including past ones (outcome `revoked`). With reasonCode `unspecified`, `affiliationChanged`, `superseded` or `cessationOfOperation`, tokens before the revocation time stay valid (`verification-result-revoked-retaining`). Missing revocation data gives `no-revocation-data`.
10. **Expiry.** If the verification time is after the TSA certificate's expiry, the token counts only through a renewal (§6.6); otherwise `expired-unrenewed`.
11. **Bound.** `notAfter = genTime + accuracy`, **rounded up to the whole second** when `genTime` or the accuracy has fractional parts (N1). Accuracy comes from the token, else from the verifier's policy for that anchor (RFC 3161 §2.4.2); with neither, the outcome is `unsupported` (A3).

**`opentimestamps`**, root kind `bitcoin-proof-of-work`. Placeholder fields: `opentimestamps: {status: "pending"}` or `{status: "complete", blockTime}`.
- **Pending.** A pending proof has no time, and stating one is rejected (`pending-counted`).
- **Real-format proofs:**
  - The checker applies the proof's operations to the target digest (python-opentimestamps serialization, pinned at `8c3dc6fb`). The proof's file digest must equal the target (`evidence-wrong-target`).
  - The attested block header is read from the verifier's **pinned header source**: a header file or node whose first header's SHA-256 is the anchor.
  - The checker verifies proof of work and linkage up to that height, and that the header's Merkle root equals the commitment.
  - It requires `minConfirmations` later headers (outcome `insufficient-confirmations`).
  - It takes `blockTime` **from that header, never from the evidence** (N2).
- **Offline.** "Verifiable offline" holds only with such a header source (T4: "a local Bitcoin Core node (a pruned node is fine)").
- **Margin and its assumption.** `notAfter = blockTime + 7,200 s`. An upper bound on existence needs a header time that cannot lag the real mining time by much. Consensus gives only that a header time must exceed the median of the previous 11 blocks. That keeps the lag to roughly an hour **only under an honest-majority assumption**: most recent blocks were mined by honest miners with roughly correct clocks. The 7,200 s margin covers that with slack. The two-hour future rule bounds the other direction and does not justify the margin (draft-1 had this backwards). See RD6 for the alternative.

**`rekor-v2`**, root kind `log-key`. Fields: `rekorV2: {logIndex}`. **No bound**: Rekor v2 has no time of its own (T3), and stating one is rejected (`log-time-claimed`). Inclusion and discoverability only.

**`traceweave-witness`**, root kind `witness-service-key`. Fields: `witness: {bundle}`. The bundle holds the witness's signed statement over the presented signature digest (§19), with the witness's own RFC 3161 evidence over the witness signature.
- The anchor is the SHA-256 of the witness public key, computed from the bundle.
- The bound is the witness's TSA bound, not the witness's clock.
- It rests on **two** anchors, the witness key and that TSA, and counts in both groups (§6.3, S4).

**`cosigned-checkpoint` is removed in draft-3** (S5). A cosignature bounds a checkpoint, not our digest. Without an inclusion proof of the signature digest at that checkpoint, it shows nothing about the registration. If needed later, it returns with an inclusion proof and the checkpoint body. The old type is `evidence-shape` (`neg-checkpoint-type-removed`).

### 6.3 Roots, independence and the policy (F2, S4)

The verifier's policy lists accepted anchors:

```json
"timeRoots": [{"anchorSha256": "…", "kind": "tsa-certificate-chain", "independenceGroup": "tsa-operator-a",
               "policyOids": ["…"], "accuracySeconds": 1, "rootCertificate": "…"},
              {"anchorSha256": "…", "kind": "bitcoin-proof-of-work", "independenceGroup": "bitcoin",
               "headerFile": "…", "minConfirmations": 6}, …]
```

- An evidence whose anchor is not listed for its kind is `untrusted-root`.
- Independence is decided **only** by the policy's groups. A producer-written label never counts (`root-not-anchored`). Two TSAs under one CA share an anchor, so they count once (`neg-quorum-same-anchor`).
- **An evidence that rests on several anchors joins their groups.** Groups that co-occur in one evidence are merged (union-find over all evidence of the bundle), and each merged class counts once. So a witness whose time comes from TSA A, plus a direct TSA A token, is **one** source (`verification-result-witness-shared-tsa`: `below-quorum`). With the witness on TSA B, they are two (`verification-result-witness-independent`).

### 6.4 Per-signature bounds and quorum (F1)

For **each signature** i, only evidence whose target is signature i counts; renewals never do.
1. Take the smallest valid `notAfter` in each independence class.
2. Sort those values.
3. `notAfterAnyRoot` is the smallest. One source vouches for it, so one dishonest or compromised source can backdate it.
4. `notAfterQuorum` is the q-th smallest (default q = 2).

Both bounds are always reported, with `distinctRoots`. A signature with no evidence of its own has **no** bound, and a later co-signature never inherits an earlier bound (`key-bound-misattributed`). Removing an evidence from a bundle can only make bounds later or remove them (N3; `verification-result-stripped`).

### 6.5 Real-format vectors (S9, S10)

`registration-fixtures/real-format/` holds real-format vectors made by `make_real_vectors.py`. No external service was contacted. **Their anchors must never be trusted.**
- **TSA tokens.** A local `openssl` (version in `MANIFEST.json`) creates a test-only root CA and a TSA certificate with a critical `id-kp-timeStamping` EKU, then issues RFC 3161 tokens over the fixture signature's digest. `openssl ts -verify` reports `Verification: OK`, recorded in the manifest.
- **Negative variants:**
  - a token over another digest;
  - a token whose `genTime` was edited after signing;
  - a token re-signed under a certificate whose EKU is not critical;
  - a token whose ESSCertIDv2 names another certificate.

  The last two were re-signed with `openssl pkeyutl`.
- **OpenTimestamps.** A proof in the python-opentimestamps format commits the digest through append, SHA-256 and prepend operations into the Merkle root of header 4 of a 13-header chain. The chain was mined locally at regtest difficulty (`nBits` 0x207fffff), so its proof of work is real but trivial. There is also a pending proof and a proof for another digest.
- **What the checker does with them.** It verifies them with `realformat.py`, standard library only: DER, X.509, CMS, RSA PKCS #1 v1.5, and the OpenTimestamps operations and headers. It computes the anchors itself from the pinned root certificate and the header file (S10).
- **What it is not.** `realformat.py` is not a general path validator: no name constraints, policy mappings or revocation fetching.
- **Not reproducible.** The tokens carry their issuing time and a random nonce, so the build does not regenerate them. Rerun `make_real_vectors.py` after any change to the statement, because the tokens are bound to its signature. The private keys exist only in a temporary directory during that run.
- **Placeholder fixtures still trust producer-written anchors and dates.** Only the real-format vectors test the anchor computation, and REG.1 must name them (S10).

### 6.6 Renewal (S6)

A **renewal** is an `rfc3161` evidence whose target is `{kind: "evidence-token", evidenceIndex: j, sha256}`, the SHA-256 of evidence j's token bytes (for placeholders, the UTF-8 token text). This is RFC 4998's timestamp renewal: a new token over the old one.

**Rule:** at verification time V, if V is after the expiry of evidence j's TSA certificate, evidence j counts only if some valid renewal of it has `notAfter` no later than that expiry. A renewal is itself an RFC 3161 evidence and may need renewing in turn. A renewal never adds to any signature's bounds.

**Not covered:**
- Renewal does **not** rescue a token whose TSA key was revoked without a retaining reasonCode or for `keyCompromise`. RFC 3161 §4 item 2 says such tokens "cannot be trusted anymore". RFC 4998 renewal guards against expiry and algorithm ageing, not compromise.
- Hash-tree renewal over the original data (RFC 4998 §1.2), needed if SHA-256 weakens, is outside draft-3. It needs a new statement over a new digest, so it is a new registration that references the old one.

Fixtures: `bundle-renewed`, `evidence-renewal`, `verification-result-renewed` (V = 2032; TSA A survives through a 2030 renewal, TSA B does not), `verification-result-expired`, `neg-expired-accepted`, `neg-renewal-wrong-target`.

### 6.7 Revocation data and "as of" (S3)

The policy's `revocationData` lists, for each TSA anchor, the `source` of the revocation data used (a CRL or OCSP response, retained with the bundle), its date `asOf`, and the revocations found.
- A token whose anchor has no revocation data is `no-revocation-data`.
- Each RFC 3161 evidence in the result reports `revocationDataAsOf`.
- **An offline result holds only as of that date.** A later `keyCompromise` revocation can still invalidate the token retroactively (§6.2, RFC 3161 §4 item 2).

## 7. Signer identity options

| Option | What a verifier learns | Cost to the registrant | Privacy |
| --- | --- | --- | --- |
| I0 Self-managed Ed25519 key, public key only in the bundle (**default**) | "Whoever holds this key signed it." Nothing about who that is. Later, the key holder can show control by signing a challenge | None. Must keep the key safe and backed up | Nothing published. One key links all disclosed registrations |
| I0′ A fresh key per work, optionally linked later by a signed key list | As I0, per work | Key management per work | Disclosing one registration does not link the others. Proving that two works share a creator needs the key list |
| I1 I0 with the public key posted somewhere dated and third-party-observable | A weak link between key and a name, as strong as that site's history | None | Key linkable to the name |
| I2 Sigstore Fulcio short-lived certificate (OIDC) | "Someone who authenticated as this identity at an OIDC provider signed it" (T3). Needs time evidence: the certificate lasts 10 minutes | An identity-provider account | Identity and time in public CT and Rekor logs **for ever** |
| I3 Organisation or qualified certificate | The CA's identity checks, under its policy | Paid; identity verification | Whatever the certificate contains |

The key id is a lookup hint, not identity ([attestations](../../spec/attestations.md)). Signer trust is the verifier's policy decision, listed by SHA-256 of the full public key (`trustedKeys`; B3), and reported separately from signature validity.

## 8. Key identity, rotation, compromise and revocation (F3, B1–B3, S1)

**Key identity (B3).** Every decision about a key uses the SHA-256 of its raw 32-byte public key:
- the policy's `trustedKeys`;
- a key event's target, which is its subject digest;
- a rotation's successor, from `successorPublicKeyHex`;
- the signer of an event.

`keyid` (16 hex digits) is only a lookup hint. A policy that lists 16-hex keyids, or the draft-2 field `trustedKeyids`, is `key-identity-by-hint`. An event whose `keyid` does not equal the first 16 hex digits of its subject digest is `key-event-shape` (`neg-key-event-subject-mismatch`).

**Key events are statements too.** A key event is an in-toto statement whose single subject is the target key (digest = SHA-256 of the public key), with predicate `{eventVersion, keyid, event, successorPublicKeyHex (rotated only), compromisedNotBefore (compromised only)}`. It is signed and time-stamped like a registration. Its **proved time E** is its own quorum bound (§6.4); without one it is `ignored-no-proved-time`.

**Evaluation is order-independent (B2).** Events are taken in order of E, with ties broken by the SHA-256 of the event payload. "Earlier" always means a smaller E, never a position in the input.
- An event is **authorized** if it is signed by its target key, or by the successor named in an applied, undisputed rotation of that key with a smaller E. Otherwise it is `ignored-unauthorized`.
- The evaluation repeats until nothing changes, because a later compromise can dispute an earlier rotation.
- The result lists every event, sorted the same way, by payload digest, with its outcome: `applied` | `disputed` | `ignored-unauthorized` | `ignored-no-proved-time` | `invalid-signature`.
- Supplying the same events in another order gives an identical result (`verification-result-event-order-a` and `-b`).

**Compromise disputes later rotations and retirements (B1).** An applied `compromised` event for key K, with claimed start Tc and proved time E, defines `start = max(Tc, E − lookback)`.
- Every applied `rotated` or `retired` event for K with proved time ≥ `start` becomes **`disputed`**. Within that window a thief holding K could have signed it.
- **No trust flows through a disputed rotation.** Its successor gains nothing (`verification-result-rotation-hijack`).
- **Two applied rotations of one key to different successors are both `disputed`** (`verification-result-rotation-conflict`).
- The consequence for an honest owner: a rotation the owner makes after reporting a compromise is disputed too, so a new key must be established out of band (I1 or I2), not through the compromised key.

**Effect on a signature by key D**, where B is that signature's **quorum bound** (S1):
1. **Trusted set.** D is in the trusted set if it is in `trustedKeys`, or is the successor of an applied, undisputed rotation of a trusted key. A successor is trusted only for signatures with B ≥ the rotation's E. Otherwise the signer is `untrusted`.
2. **No quorum (S1).** If any applied or disputed event targets D, or names D as successor, and the signature has **no quorum bound**, the signer is **`disputed`**, never `trusted`. One source could have moved the bound across the event (`verification-result-single-source-event`; `neg-trust-without-quorum`).
3. **`compromised` (applied):** B < `start`: trust unchanged; `start` ≤ B < E: `disputed`; B ≥ E: `untrusted`.
4. **`retired` or `rotated` (applied, undisputed):** B ≥ E: `untrusted`; earlier signatures are unchanged.

**Why an early-dated false claim cannot erase honest history.** The event's effect starts no earlier than E − lookback. Inside that window the outcome is `disputed`, shown with both times, not silently `untrusted`. Registrations bounded before the window keep their trust (`verification-result-compromise-early`). The trade-off: an honest owner who discovers a theft later than the look-back window cannot dispute registrations made before it (RD15).

**Key loss.** Existing registrations stay verifiable, because the bundle carries the public key and each signature's bound. Recovery is a new key, linked through I1 or I2.

**TSA revocation** is a separate input: the policy's `revocationData` (§6.7).

## 9. How a comparison report references a registration

The report body is closed (contract §6.2, §7). A report never embeds a registration. A separate **report link** joins them:
- `report`: the report path and `bodySha256`, recomputed from the canonical body (`report-digest`).
- `registration`: the bundle, and the SHA-256 of the statement payload bytes (`statement-digest`).
- `links`: for each pair, the role, the subject index and the digest. The report pair's digest, the link digest and the registered subject digest must be equal (`subject-mismatch`).
- `catalogueOpening` (optional): the catalogue bytes (the exact stored bytes; RFC 8785 bytes of the catalogue object in the fixtures) and the nonce.
  - They must open the registered commitment (`catalogue-does-not-open`).
  - They must hash to the report's `referenceCatalogueSha256` (`catalogue-not-report-input`).
  - The registered profile must equal the report's (`profile-mismatch`).

  Opening reveals the whole catalogue to whoever receives the link.
- `notShown`: the §11 list.

This shows that the reference artifact compared in the report is byte-identical to content registered under the named key no later than that signature's bound. It shows nothing about the candidate's origin, about direction of copying, or about anything contract §8 forbids.

## 10. Verification procedure

**Inputs:**
- a bundle;
- optionally, the artifact bytes, a catalogue opening and key-event bundles;
- the verifier's **policy**: `{quorum, timeRoots, trustedKeys, revocationData, compromiseLookbackSeconds, verificationTime}`. A result carries the policy it used, so its revocation date and verification time are on record (S3).

Every step reports its own outcome, and a failure in one step does not change another step's outcome.

1. **Parse** strictly: no duplicate keys (`duplicate-key`); size limits as in the signing harness. Base64 fields may be standard or URL-safe, because DSSE says verifiers "MUST accept either" (S7; `bundle-url-safe`). Outcome `envelope`: `ok` | `malformed` (`envelope-shape`, which also covers one key signing twice: `neg-duplicate-signer`).
2. **Signatures.** Look up each key by its `keyid` hint among the bundle's keys. A missing or unmatched hint gives `unknown-key`; there is no trial verification (A7). Verify under §10.1 over `PAE(payloadType, payload)` of the exact payload bytes. Per signature: `valid` | `invalid` | `unknown-key`, with `keySha256` (`signature-invalid`).
3. **Key events,** evaluated in order of proved time (§8). Per event: `applied` | `disputed` | `ignored-unauthorized` | `ignored-no-proved-time` | `invalid-signature`.
4. **Signer trust**, from the policy's `trustedKeys` (by full key digest) and the events, using quorum bounds only (§8). Per signature: `trusted` | `untrusted` | `disputed` | `not-evaluated`.
5. **Statement.** Strictly parse the payload and apply §4. Outcome `statement`: `ok` | `malformed` | `unsupported`.
6. **Subject digests.** Per subject: `match` | `mismatch` | `not-supplied`.
7. **Possession digests.** Per subject: `match` | `mismatch` | `not-supplied`.
8. **Catalogue.** `opens` | `does-not-open` | `not-supplied` | `not-committed`.
9. **Each time evidence** (§6.2), offline from retained material, as of the policy's revocation dates. Per evidence: `valid` | `invalid` | `wrong-target` | `pending` | `untrusted-root` | `unsupported` | `wrong-policy` | `revoked` | `no-revocation-data` | `expired-unrenewed` | `insufficient-confirmations`, with its target, `notAfter` and `revocationDataAsOf`. In fixtures only, `placeholder`, or `placeholder-assumed-valid` when the result says `simulated: true`.
10. **Bounds, per signature** (§6.4): `quorum-met` | `below-quorum` | `none-valid`, with `keyid`, `keySha256`, `quorum`, `distinctRoots`, `notAfterAnyRoot` and `notAfterQuorum`.
11. **Claimed time.** `absent` | `claimed-only` | `after-proved-bound` | `not-compared`. The comparison is with the earliest `notAfterAnyRoot` over signatures whose signer is **`trusted`** (S11). An untrusted co-signer with one early source cannot change the registrant's outcome (`verification-result-claim-trusted-only`). With no trusted signature, the outcome is `not-compared`. The value compared with is reported as `comparedWith`.
12. **Output** all outcomes, and the fixed `notShown` list: `authorship`, `originality`, `first-creation`, `ownership`, `permission`.

A result must not:
- add a combined verdict (`single-verdict`);
- report the claimed time as a bound (`claimed-as-proved`);
- count a pending proof (`pending-counted`);
- give a signature a bound it has no evidence for (`key-bound-misattributed`);
- count one class twice (`quorum-miscount`);
- ignore an applicable key event (`key-event-ignored`);
- trust a signature on one source after a key event (`trust-without-quorum`);
- match keys by hint (`key-identity-by-hint`);
- add an authorship or ownership field (`authorship-claim`).

Any other disagreement with the recomputed outcomes is `result-mismatch`.

### 10.1 Ed25519 verification rule set (A4)

Verification follows RFC 8032 §5.1.7 with the **cofactorless** equation `[S]B = R + [k]A`, plus these rejections:
- a signature that is not 64 bytes, or a key that is not 32 bytes;
- `S ≥ L`;
- a non-canonical encoding of A or R (y ≥ p, or x = 0 encoded with the sign bit set);
- a public key A of small order (`[8]A` is the identity).

R of small order is not rejected separately. Implementations must reject exactly these, so two verifiers (REG.2) agree on edge cases. The checker's self-test shows two lenient verifiers that this rule set rejects:
- one that reduces S modulo L accepts a malleated signature;
- one without the small-order check accepts R = identity, S = 0 under the identity key, for **any** message.

It also shows that a non-canonical point is refused.

## 11. What a registration does not show (required text, F4)

A registration does not show **authorship**, **originality**, **ownership** or **permission**. It does not show that the registrant **created** the content rather than copied it, or that they were first: anyone who obtains a copy can register it, and an earlier creator may never have registered. **First to register is not first to create.** It gives upper bounds on when each signature existed, not a creation time.

**Renderings use an allow-list.** Every line of user-facing text that presents a registration (command-line output, the WEB page, an agent skill under SK.3, a C2PA export) is one of the following lines, filled from the verification result:

| Template | Filled from |
| --- | --- |
| `Registration of <name> (SHA-256 <first 8 hex>…<last 4 hex>).` | subject |
| `Content digest: matches the file you supplied.` / `does not match the file you supplied.` / `not checked, because no file was supplied.` | step 6 |
| `Signature by key <keyid>: <valid/invalid/unknown key>; signer <trusted/not trusted/disputed by a key event/not evaluated> under your policy.` | steps 2, 4 |
| `This record shows that the content existed, and that key <keyid> signed a statement naming it, no later than <T>.`, where T is that signature's `notAfterQuorum`; if quorum was not met, T is its `notAfterAnyRoot` and the line ends `… no later than <T> (according to one time source only).` | step 10, **one line per signature with a bound** |
| `Time sources for key <keyid>: <distinctRoots> independent, <quorum> required; the earliest single source says <notAfterAnyRoot>.` | step 10 |
| `No proved time for key <keyid>.` | step 10, for a signature with no bound |
| `Creation time claimed by the registrant, not proved: <T>.` | step 11 |
| `Witnessed: the caller <subject> presented the signature digest no later than <T>, according to the witness's time-stamp authority.` | §19 witness; T is the witness's TSA bound, not its clock (S8) |

The text must also contain the three fixed sentences, and for agent-made registrations the §19.5 sentence:

> It does not show who created the content, that it is original, that the registrant was first to create it, who owns it, or that its use is permitted.
> First to register is not first to create.
> Comparing the times of two registrations does not show which was made first.

The third sentence is new in draft-3 (S8). Each bound is an upper bound, so an earlier bound on A than on B does not show that A was registered first: B's registrant may simply have obtained evidence later.

**What the checker rejects:**
- A line outside the templates is `rendering-unlisted-line`, even a harmless one.
- An unlisted line that also uses an authorship or ownership word is additionally `authorship-claim`. The words are `author…`, `wrote`, `written`, `belongs`, `your`, `claim to`, `registered to you`, `first to create`, `priority`, `created`, `creator`, `own…`, `original…`, `copyright`, `proves`, `proof`, `establish…`, `authentic…`, `verified`, `genuine`, `legitimate`. This rejects the four renderings the review's checker accepted (`neg-authorship-claim-1` to `-4`).
- An unlisted line that orders registrations or times (`before`, `after`, `earlier`, `later`, `first`, `sooner`, `precede`, `predate`, `older`, `newer`) is additionally `ordering-claim` (`neg-ordering-claim`).
- A bound sentence for a key without that bound is `key-bound-misattributed`.
- A bound sentence carrying the claimed time is `claimed-as-proved`.
- A missing fixed sentence, or a missing bound sentence for a key that has a bound, is `notice-missing`.

The allow-list is a floor, not a wording review: REG.4 still needs a non-author to read every template.

## 12. Threat model

| Threat | Who | What stops it | What remains |
| --- | --- | --- | --- |
| Backdating a registration | Registrant | Evidence binds one signature; the registrant cannot choose `genTime` or a block time. q = 2 over independent anchors | One colluding or compromised source moves `notAfterAnyRoot` only. Bitcoin's bound rests on the honest-majority assumption (§6.2) |
| Retroactive loss of one source | Time | RFC 3161 revocation without a retaining reasonCode kills every token of that key (§6.2). Three sources and q = 2 survive one loss (`verification-result-revoked`) | Losing two sources leaves `below-quorum` |
| Counting one source twice | Producer or careless verifier | Anchors, not labels; groups set by the verifier (§6.3) | A policy that groups badly |
| Registering someone else's work | Anyone with a copy | Nothing technical; §11 text | First to register is not first to create |
| Replay or transplant of evidence | Anyone | Evidence targets one signature's raw bytes (`evidence-wrong-target`); co-signers get no inherited bound (§6.4); the TSA request nonce catches replayed responses at request time (`tsa-nonce-mismatch`) | Copying a whole bundle proves only that the original key holder registered |
| Claiming a published digest without the content | Anyone | Possession digest (§4.3) | Useless for content already public at T, and for short guessable content after disclosure |
| Key theft | Attacker | Bounds on earlier signatures; compromise events (§8) | Signatures between theft and the event's proved time are `disputed`: indistinguishable from the owner's |
| Hostile or early-dated compromise claim | Thief or former collaborator | Authorized signers only; proved time required; look-back clamp; `disputed`, not `untrusted` (§8) | Registrations inside the look-back window can be disputed |
| Nonce reuse | Careless producer | Producer obligation; cross-record check (§4.2) | Not detectable from one record |
| Linkage | Observers of disclosed records or time-service traffic | Per-work keys (I0′); one signature digest per registration | Timing and IP address at time services |
| Privacy leaks | Services, recipients | Only signature digests leave; fresh nonce; salted commitments; no fingerprints (§5) | Opening a catalogue reveals all of it; low-entropy content is confirmable after disclosure |
| Service shutdown | TSA, calendar, log | Three sources; complete evidence verifiable offline from retained chains, retained revocation data and a pinned header source, **as of the revocation data's date** (§6.7) | An OpenTimestamps proof is lost if every calendar disappears before upgrade (T4) |
| Algorithm ageing and certificate expiry | Time | Renewal evidence over the earlier token (§6.6), made before the TSA certificate expires; triggers: expiry approaching, any non-compromise revocation notice, reported weakness in SHA-256 or Ed25519 | A renewal must happen before the expiry or break. Hash-tree renewal for SHA-256 is outside draft-3 (§6.6). Renewal does not rescue a compromised TSA key |
| Stolen key rotated to the thief | Thief | A later compromise disputes rotations inside its window; no trust through a disputed rotation; conflicting rotations both disputed (§8; `verification-result-rotation-hijack`, `-rotation-conflict`) | Until the owner's compromise event is proved, a verifier without it sees the rotation as applied |
| Events supplied in a convenient order | Anyone | Order-independent evaluation by proved time (§8; `-event-order-a`, `-b`) | — |
| Keys matched by hint | Implementations | Full-key SHA-256 everywhere (§8; `neg-trust-by-hint`, `neg-key-event-subject-mismatch`) | — |
| One backdating source deciding trust | Thief plus one source | Quorum bound only for event decisions; otherwise `disputed` (S1) | — |
| A witness and its TSA counted twice | Producer | Union of groups per evidence (§6.3; `verification-result-witness-shared-tsa`) | A policy that does not list the witness's TSA anchor |
| Evidence stripped in transit | Anyone handling a bundle | Bounds can only become later or disappear (N3; `verification-result-stripped`) | A record can be made to look later than it is |
| Lenient signature verifiers | Implementations | §10.1 rule set, self-tested | — |

## 13. The two mechanisms to implement first, and why

1. **RFC 3161 tokens (T1), from two unrelated TSAs.** Implement this first. It is the standard form consumed by C2PA, Sigstore bundles, eIDAS qualified time-stamps and RFC 4998 renewal. Precision is about a second. Verification needs only the retained chain and revocation data, and no header source, and holds as of that revocation data's date (§6.7). The real-format vectors (§6.5) exercise every token check locally. Public TSAs need no account, but the owner must read their terms. A qualified TSA can be added later for registrants who want the eIDAS presumption (L1), without a format change.
2. **OpenTimestamps (T4).** Its root, Bitcoin proof of work, has no operator who can backdate. It needs no account and no fee. Once upgraded, it survives the shutdown of every calendar. Its costs are acceptable for the third source: hours of precision, a pending window, LGPL-3.0 client code, and a trusted Bitcoin header source to verify.

Two TSAs plus OpenTimestamps give **three independent sources with q = 2**, so one retroactive TSA revocation still leaves a quorum. Rekor and witness cosigning are deferred: they add discoverability and split-view protection that private registrations do not need, and Rekor v2 needs a TSA token for time anyway (T3).

## 14. What a registrant would do in practice

1. **Once:** generate a signing key with the tool, stored in the private location of contract §6.8 B11, and back it up in two places. Optionally publish the public key somewhere dated (I1), or choose per-work keys (I0′).
2. **For each piece of work:** run a local `register` command on the original files. It hashes them, draws a nonce, computes the possession digests, and optionally builds the private catalogue and its commitment. It then signs the statement and sends **only the SHA-256 of the signature bytes** to two TSAs, each with a fresh request nonce that it checks, and to OpenTimestamps calendars. No content and no identity leaves the machine. It reports `pending` for the Bitcoin part.
3. **A few hours later:** upgrade the OpenTimestamps proof and save the bundle again. The tool can do this on its next run.
4. **Keep, unchanged and backed up:** the original bytes, the bundle, the catalogue and its opening, the TSA certificate chains, and access to a Bitcoin header source.
5. **Renew** before a TSA certificate expires, on any non-compromise revocation notice, or on reported weakness in SHA-256 or Ed25519: run `renew` to add renewal evidence over the existing tokens (§6.6). Also keep the revocation data fetched at each check, with its date (§6.7).
6. **In a dispute:** hand over the original bytes and the bundle, and the catalogue opening only if needed. The other side runs §10 with their own policy and reads the §11 limits.

## 15. Roadmap mapping and proposed ROADMAP.md text (S13; ROADMAP.md is not changed here)

ROADMAP.md M4.3–M4.6 are unchanged. M4.5 still asks for a decision on "the optional timestamp adapter", and REG gates exist only as proposals here. **Until the owner adopts text like the following, no M4 gate tests a registration, and M4 cannot be evidenced from this draft.** The text below is written to drop into the M4 table and to be checkable as written.

| ID | Type | Proposed verifiable criterion | Owner |
| --- | --- | --- | --- |
| M4 row, "What becomes possible" | — | "A registrant can show that registered bytes existed under a named key no later than a time agreed by two independent time sources. A registration never shows authorship, first creation, or which of two registrations was made first." | — |
| M4.3 (amended) | E | "Negative cryptographic vectors (tampered payload, type or signature; untrusted key; malformed or duplicate-key payload; subject mismatch; and, for registrations, `evidence-wrong-target`, `tsa-imprint-mismatch`, `tsa-signature-invalid`, `tsa-eku-invalid`, `tsa-signing-cert-mismatch`, `tsa-nonce-mismatch`, `key-event-shape`, and the §10.1 Ed25519 edge vectors), each with a distinct reason code. `validate` checks them." | S |
| M4.5 (replaced) | O+E | "A recorded owner decision selecting the time-evidence types for registration records (proposed: RFC 3161 from two unrelated TSAs, and OpenTimestamps), the default quorum (2), the compromise look-back (RD15), and whether any external service may be contacted for test tokens. In-toto adapter accept/reject fixtures and a trust-policy document, checked by `validate`." | S |
| M4.6 (amended) | E | "Commitment, disclosure and key-event design (`research/drafts/registration-record.md` §4, §5, §8) reviewed by a named non-author. Report in `docs/reviews/`; every finding has a disposition." | S |
| REG.1 | E | "`check_registration.py` exits 0 under `validate`: every positive fixture gives no code, every negative gives exactly its codes, every code has a negative, and the wrong-implementation self-test passes. The real-format vectors in `real-format/` (local test-only TSA token and synthetic OpenTimestamps proof) verify with computed anchors, and their four TSA and one proof negatives are rejected." | S |
| REG.2 | E | "Two implementations, each with its own parser, produce byte-identical verification results (§10) on every REG.1 fixture, including the §10.1 edge vectors and the two event orders." | I |
| REG.3 | E | "After the owner approves the services: real RFC 3161 tokens from two unrelated TSAs and one upgraded OpenTimestamps proof over a synthetic registration, verified with the network denied, retained chains and a pinned header source, k/k. Failure directions tested: wrong target, tampered token, wrong policy OID, wrong nonce, revoked certificate." | I |
| REG.4 | E | "Every user-facing rendering uses only the §11 templates and the three fixed sentences; a named non-author reviews the templates. Feeds M5.2 and WEB.5." | S+I |
| REG.5 | E | "The §19 agent fixtures are checked by `validate`: 0 `raw` or `url` parts and 0 fingerprints in hosted-route fixtures; every skill description and agent rendering carries the required sentences." | S |
| UC-9 (proposed) | — | Owner wording. This draft supplies the limit text (§11); UC-3's "Signing alone proves neither ownership nor earlier existence" stays for signing alone | — |

**C2PA (S12).** A C2PA v2 time-stamp countersigns the **C2PA claim signature** (`sigTst2`; T6), not the DSSE signature. A registration's RFC 3161 token over its DSSE signature therefore **cannot be reused** in a C2PA manifest. A C2PA export obtains its own RFC 3161 token over the claim signature, and **registration time evidence does not map**. The [C2PA mapping draft](c2pa-mapping.md) correctly keeps the time-stamp row `conflicting`; this draft no longer says otherwise.

## 16. Open decisions

| ID | Decision | Options | Recommendation |
| --- | --- | --- | --- |
| RD1 | First mechanisms | (a) RFC 3161 from two TSAs + OpenTimestamps; (b) RFC 3161 from two TSAs only; (c) Rekor v2 + TSA | (a); implement RFC 3161 first, because OpenTimestamps verification needs a header source. (b) if Bitcoin verification is unwanted, accepting that one more revocation drops quorum |
| RD2 | Which TSAs | Free public TSAs listed by Sigstore (terms unread); a qualified eIDAS TSA (paid); none until approved | **Owner.** None until approved; then two unrelated public TSAs for tests, after reading their terms |
| RD3 | Public logs | Never; opt-in per registration; a project-run log | Never by default; opt-in only after RES.1 and an owner decision (SK.5) |
| RD4 | Default identity | I0, I0′, I1, I2, I3 | I0, with I0′ and I1 documented. I2 opt-in only |
| RD5 | Default quorum | 1 or 2 | 2 over three sources; always report both bounds; count by policy group |
| RD6 | OpenTimestamps margin | 7,200 s under the honest-majority assumption; use the median-time-past of a later block; no OpenTimestamps bound | 7,200 s with the assumption stated (§6.2); revisit with a reviewer who knows Bitcoin consensus |
| RD7 | Possession digest | Mandatory or optional | Mandatory |
| RD8 | Time-stamp target | Raw signature bytes; statement digest; artifact digest | Raw signature bytes, with per-signature bounds (§6.1, §6.4) |
| RD9 | Many files | 64 subjects; a Merkle root | 64 now |
| RD10 | Identifiers | Predicate URLs under `traceweave.org` | Proposed only; publish nothing (shared with C2PA D3) |
| RD11 | Renewal | Re-time-stamp the bundle; RFC 4998 evidence records | Re-time-stamping on the §12 triggers; evidence records if a qualified archive is ever needed |
| RD12 | Architecture for registration at creation (§19) | Local-first; hosted witness; custodial hosting | Local-first first; witness only as an optional extra source after SK.5; never custodial |
| RD13 | Agent identity in the statement | None; claimed `claims.generator`; delegated-identity field | None in draft-3 (§19.5) |
| RD14 | Local agent route | MCP over stdio; A2A on loopback; command line only | MCP over stdio first |
| RD15 | Compromise look-back | 30 days; 90 days; no clamp | 30 days as the fixture default. **Owner/policy choice:** longer protects owners who discover theft late, shorter protects honest history from hostile claims |
| RD16 | Ed25519 rule set (§10.1) | As specified; also reject small-order R; cofactored equation | As specified; record it with REG.2 vectors |
| RD17 | Who may assert key events | The key and verified successors; plus policy-listed keys | The key and verified, undisputed successors by default; policy may add keys |
| RD18 | Recovery after reporting a compromise | Rotation by the compromised key (disputed under §8); out-of-band link (I1 or I2); policy-listed recovery keys | Out of band, or a recovery key listed in advance in the verifier's policy. A rotation by a compromised key cannot carry trust |
| RD19 | Witnessed checkpoints | Removed (draft-3); restore with an inclusion proof and checkpoint body | Removed until a log is in scope (S5, RD3) |
| RD20 | Hash-tree renewal for SHA-256 | Outside draft-3; define with RFC 4998 evidence records | Outside draft-3; a new registration referencing the old one if SHA-256 weakens (§6.6) |

## 17. Needs the owner

- **Using any external service at all**, including one test token (REG.3). The reviewer's answer on what one test submission discloses, recorded for this decision:
  - **RFC 3161:** the TSA sees the SHA-256 imprint of a signature over a synthetic statement, the hash OID, the request nonce, the client IP address, the time, the user agent and TLS metadata, and may log them under its terms. Nothing is published.
  - **OpenTimestamps:** each calendar sees the digest (further hashed with a nonce), the IP address and the time. The calendar's Merkle root is placed in a Bitcoin transaction **permanently**. The digest itself is not revealed unless the proof is shown.
  - **Neither** reveals content or identity beyond network metadata. Both reveal that this address used a time-stamping service at that time.
  - The reviewer suggests one TSA and one calendar (`--calendar`) for the test, over a synthetic statement.
- Which TSAs, after reading their terms; any paid or qualified TSA.
- Whether anything is ever written to a public transparency log, and whether the project ever operates a log, witness or signer (SK.5).
- Identity choices: whether I2 is offered; the default between I0 and I0′.
- The compromise look-back default (RD15).
- Publishing the predicate identifiers under `traceweave.org`.
- Adopting the ROADMAP.md text proposed in §15 (M4.3, M4.5, M4.6, REG.1–REG.5). Until it is adopted, no M4 gate tests a registration (S13). Also the new use case.
- Everything listed at the end of §19.7.
- Legal questions. Lane 13 quotes eIDAS and the US Federal Rules of Evidence only; nothing here is legal advice.

## 18. Fixtures and checker

See the [fixtures README](registration-fixtures/README.md). `check_registration.py` (standard library, with `realformat.py`) does four things:
- **It checks the fixtures.** It verifies Ed25519 signatures under §10.1 with public test-only keys. It recomputes digests, possession digests, the catalogue commitment and the full expected verification result: per-signature bounds; independence classes; revocation data; renewal; key events in proved-time order with full-key identities; trust from quorum bounds only. It applies the §11 allow-list.
- **It verifies the real-format vectors for real** (§6.5): the RFC 3161 structure, signature, ESSCertIDv2, EKU, chain and imprint, and the OpenTimestamps operations, proof of work, linkage and Merkle root, with anchors it computes itself.
- **It runs a wrong-implementation self-test.** Twenty-five plausible wrong verifiers, renderings and decoders are built in memory, and each must be rejected or shown to misbehave. Among them: B1 hijack and conflict, B2 list-order evaluation, B3 hint trust, S1 one-source trust, S4 witness double counting, S6 expiry ignored, S7 standard-only base64, S11 any-signer claim comparison, S2 an imprint-blind token check, and two lenient Ed25519 verifiers.
- **It runs a drift check.** Every failure code must appear here and have a negative fixture.

Placeholder time evidence is never verified (§6.5, S10).

Failure codes: `authorship-claim`, `catalogue-does-not-open`, `catalogue-not-report-input`, `catalogue-unsalted`, `claimed-as-proved`, `duplicate-key`, `envelope-shape`, `evidence-shape`, `evidence-wrong-target`, `fixture-shape`, `forbidden-field`, `key-bound-misattributed`, `key-event-ignored`, `key-event-shape`, `key-identity-by-hint`, `log-time-claimed`, `nonce-invalid`, `nonce-reused`, `notice-missing`, `ordering-claim`, `pending-counted`, `placeholder-unlabelled`, `possession-mismatch`, `predicate-type`, `profile-mismatch`, `provenance-shape`, `quorum-miscount`, `rendering-unlisted-line`, `report-digest`, `result-mismatch`, `root-not-anchored`, `signature-invalid`, `single-verdict`, `statement-digest`, `statement-shape`, `subject-mismatch`, `subject-name`, `time-in-statement`, `trust-without-quorum`, `tsa-eku-invalid`, `tsa-imprint-mismatch`, `tsa-nonce-mismatch`, `tsa-signature-invalid`, `tsa-signing-cert-mismatch`; for §19: `content-on-wire`, `a2a-shape`, `mcp-tool-shape`, `witness-shape`.

## 19. Registration at creation time and agent interoperability

The owner wants content registered at the moment it is created, including by AI agents, over A2A. This section designs that from the protocol texts. Nothing was run against any agent, server or service.

**Sources, read 2026-11-23 over read-only HTTP.**
- **A1:** A2A at tag `v1.0.1`, commit `3303592588e388e62e0f69f701af531d2f4e3991`: [specification.md](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/docs/specification.md) (its banner names `1.0.0` as the latest released version; the protocol version on the wire is `1.0`, §3.6), [a2a.proto](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/specification/a2a.proto), [extensions](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/docs/topics/extensions.md), [GOVERNANCE.md](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/GOVERNANCE.md), [README](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/README.md), [JSON artifact README](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/specification/json/README.md). Apache-2.0.
- **A1 governance:** "an open source project under the Linux Foundation, contributed by Google" (README). It is "governed by the Technical Steering Committee", with eight seats held by Google, Microsoft, Cisco, Amazon Web Services, Salesforce, ServiceNow, SAP and IBM Research, in a "Startup Phase" composition (GOVERNANCE.md).
- **M1:** Model Context Protocol at commit `862397cec702e8f828713071da501cf56158e8fc`, revision `2026-07-28`, labelled "(latest)" in the [docs navigation](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/docs.json): [tools](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/specification/2026-07-28/server/tools.mdx), [stdio](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/specification/2026-07-28/basic/transports/stdio.mdx), [authorization](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/specification/2026-07-28/basic/authorization/index.mdx), [overview](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/specification/2026-07-28/index.mdx), [schema.ts](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/schema/2026-07-28/schema.ts), [schema.json](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/schema/2026-07-28/schema.json), [GOVERNANCE.md](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/GOVERNANCE.md). MCP "has been established as Model Context Protocol a Series of LF Projects, LLC"; specifications are Apache-2.0 (GOVERNANCE.md).

### 19.1 What the protocols give, and what they do not

| Feature | What the text says (A1 unless marked) | Consequence for registration |
| --- | --- | --- |
| Normative source | "`spec/a2a.proto` is the single authoritative normative definition"; `a2a.json` is "a non-normative build artifact", "generated during builds and intentionally **not** committed" (§1.4; JSON README) | No published A2A JSON Schema could be validated against offline. The fixtures are checked against the proto field lists (§19.4) |
| Agent Card | "A2A Servers **MUST** make an Agent Card available"; discovery at `https://{server_domain}/.well-known/agent-card.json` (§8.1, §8.2). Required fields in the proto: `name`, `description`, `supportedInterfaces`, `version`, `capabilities`, `defaultInputModes`, `defaultOutputModes`, `skills` | A card describes a service. It is not evidence about content |
| Skills | `AgentSkill` requires `id`, `name`, `description`, `tags`; a skill "is largely a descriptive concept" (proto comment on `skills`) | Skill descriptions are where the §11 limit text must appear |
| Tasks | `TaskState`: `SUBMITTED`, `WORKING`, `COMPLETED`, `FAILED`, `CANCELED`, `INPUT_REQUIRED`, `REJECTED`, `AUTH_REQUIRED` (proto) | §19.4 lifecycle |
| Messages and artifacts | "Results SHOULD BE returned using Artifacts"; "Messages MUST NOT be considered a reliable delivery mechanism for critical information" (§3.7) | The witness statement is returned as an artifact, never only as a message |
| Parts | A `Part` holds exactly one of `text`, `raw` (bytes), `url` or `data` (JSON), plus `metadata`, `filename`, `mediaType` (proto) | `raw` and `url` are how content would leave; the profile forbids them (§19.3) |
| Transports | `protocolBinding` values `JSONRPC`, `GRPC`, `HTTP+JSON` (proto); "Production deployments **MUST** use encrypted communication" (§7.1) | A hosted witness is HTTPS only |
| Authentication | "Identity information is handled at the protocol layer, not within A2A semantics" (§7); credentials are obtained "out-of-band" (§7.3); the server "**MUST** authenticate every incoming request" (§7.4). Schemes: API key, HTTP, OAuth 2.0, OpenID Connect, mutual TLS (proto `SecurityScheme`) | The witness can say which authenticated caller presented a digest. That caller identity is whatever the identity provider asserts |
| Idempotency | "**Send Message** operations MAY be idempotent. Agents may utilize the messageId to detect duplicate messages" (§3.3.1) | §19.4 defines it for the witness |
| Errors | Authentication, authorization, validation, resource and system categories, plus A2A errors such as `ContentTypeNotSupportedError`, `ExtensionSupportRequiredError`, `VersionNotSupportedError` (§3.3.2); "rate limit exceeded" is an example system error | §19.4 error mapping |
| Signing and provenance | The only signing in the core is of the **Agent Card**, by JWS over the RFC 8785 canonical card (§8.4, §8.4.1). Nothing signs messages, tasks or artifacts, and the proto has no provenance field | A2A cannot carry evidence by itself. Registration evidence travels as Traceweave's own signed objects inside a `data` part |
| Time | Timestamps are ISO 8601 UTC strings (§5.6.1). The extensions page lists a sample "Timestamp Extension" that adds timestamps to `metadata` (not read further) | Any A2A time is a claimed time, never time evidence |
| Extensions | Declared in the card with `uri`, `description`, `required`, `params` (proto `AgentExtension`); "Anyone is able to define, publish, and implement an extension" (extensions page) | A Traceweave profile extension, proposed URI `https://traceweave.org/a2a/ext/registration/draft-1` (not published), declares `wire: digests-only` or `local-only` |
| Versioning | Major.Minor only; patch numbers "SHOULD NOT be used in requests, responses and Agent Cards" (§3.6) | `protocolVersion: "1.0"`; `"1.0.1"` is rejected (`a2a-shape`) |
| Discrepancy | The sample card in §8.5 uses a `security` field; the proto names it `security_requirements` (`securityRequirements` in JSON), holding `{"schemes": {…}}` | The fixtures follow the proto, which §1.4 makes normative |
| MCP tools (M1) | Tools are "model-controlled"; "there **SHOULD** always be a human in the loop with the ability to deny tool invocations"; clients "**MUST** consider tool annotations to be untrusted unless they come from trusted servers"; servers "**MUST** … Rate limit tool invocations" (tools.mdx). Annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` (schema.ts) | The local route is an MCP tool whose annotations say it writes and reaches the network |
| MCP stdio (M1) | "the client launches the MCP server as a subprocess"; implementations using stdio "**SHOULD NOT** follow this [authorization] specification, and instead retrieve credentials from the environment" | A local stdio tool needs no listener, no network authentication and no account |

### 19.2 Two architectures and what each means

**(a) Local-first (recommended first).** The creating tool or agent calls a local Traceweave tool when it writes a file. The local tool may be an MCP tool over stdio, a local A2A agent on loopback, or the command line. It does everything in §14 step 2 on the machine: digests, nonce, possession digests, optional catalogue and commitment. It signs with the **creator's** key and requests evidence over the raw signature bytes from two TSAs (each with a checked request nonce) and OpenTimestamps (§13). The trust meaning is exactly §1: this key signed a statement naming these bytes no later than T. Registering at creation time can make T close to creation, if the registrant registers promptly; the record does not show that they did (S8). It never proves the creation moment, and the bound is still an upper bound.

**(b) Hosted Traceweave witness over A2A.** A remote agent receives **only the SHA-256 of a registrant's DSSE signature**, after (a) has signed. It authenticates the caller and signs a **witness statement** (predicate type `https://traceweave.org/predicate/witness/draft-1`, proposed). The statement says: *this digest was presented at `receivedAt` by the witness's clock, by the caller authenticated as {scheme, issuer, subject}, in request `requestMessageId`*. The witness attaches its own RFC 3161 token over its signature, so its time does not rest on its own clock. The result returns as an A2A artifact. The creator adds it to the bundle as one more time evidence (proposed type `traceweave-witness`, root kind `witness-service-key`). Its root is identified by the anchor of the witness key (§6.3), and the verifier's policy decides which independence group it belongs to. Its bound is per signature, like every other bound (§6.4).

"Signed by Traceweave" would mean only that: a presented digest, a time, an authenticated caller. It would **not** mean authorship or originality. It would not even mean that the caller held the content: the witness never sees content, and possession is shown by the creator's own possession digest (§4.3). A custodial variant, where the hosted service holds creators' keys and signs registrations for them, is **not recommended**. It would make the operator able to sign as any creator.

**What operating (b) requires.**
- **Key custody:** a hardware or cloud key service, rotation, a published key history, and a compromise procedure (§8 applies to the witness key too).
- **Availability:** a stated service level. Registration must still succeed without the witness, because it is an extra root, never a required one.
- **Abuse handling:** quotas, rate limits and refusal policies (§19.6).
- **An accountable operator:** someone who answers for the key, the logs and incidents, and who can contract with a TSA.
- **Cost:** hosting, the key service, monitoring, and any paid TSA.
- **A retention and privacy policy:** caller identity, digest, time and IP address together are personal data about creative activity. This is not legal advice; the owner would need advice for any jurisdiction.

**What the project's status implies.** Traceweave is an independent, non-commercial specification and "not a legal entity" (roadmap). It has no body that can be the accountable operator, sign a TSA contract, or promise availability. A witness run by volunteers that later stops leaves its past statements verifiable, because the bundle carries the witness key and its TSA token, but no new ones can be made. A hosted signer would turn the project into a trust anchor it cannot currently back. **Recommendation: build (a) first. Specify (b) as an optional evidence type, and operate nothing until SK.5 is decided.** The roadmap already says "Until then, nothing is hosted".

### 19.3 What crosses the wire, and the privacy exposure

| Hop | Architecture | What is sent | What the receiver learns |
| --- | --- | --- | --- |
| Creating agent → local Traceweave | (a) | File paths or bytes over stdio or loopback; **never leaves the machine** | — |
| Local Traceweave → TSA | (a), (b) | An RFC 3161 request whose imprint is the SHA-256 of the signature, plus an optional request nonce | The digest, the requester's IP address and the time (lane 13, T1) |
| Local Traceweave → OpenTimestamps calendars | (a), (b) | The same digest | The same; the client adds its own nonce (T4) |
| Creator → hosted witness | (b) | TLS; the `A2A-Version` header; a credential (§7.3); a `SendMessageRequest` whose message has one `data` part `{"requestVersion": "traceweave-witness-request-draft-1", "presented": {"kind": "dsse-signature-sha256", "sha256": "…"}}` and the extension URI | Caller identity from the credential, the digest, the time, the IP address, the message id |
| Hosted witness → registrant | (b) | A `Task` with one artifact: the signed witness statement and its TSA evidence | — |

**Neither source code nor fingerprints need to leave the machine.** The statement, possession digests and catalogue are built locally (§4). The only value any remote party needs is a 32-byte digest of a signature over a statement that contains a fresh 256-bit nonce. That digest reveals nothing about the content, even to someone holding a guessed file (§5). The fixtures enforce this. A `raw` or `url` part sent to the witness is rejected (`content-on-wire`), and so is a digests-only card served over plain HTTP. Fingerprints in a request are `forbidden-field`. Presenting the artifact digest instead of the signature digest is `evidence-wrong-target`: it would let the witness confirm guessed files.

**Residual exposure.** The witness operator learns who registers, when, and how often. Repeated requests link a caller's registrations. If the operator ever publishes its records, that becomes a public activity log of identities. The witness statement given to the creator contains the caller identity, so disclosing that statement in a dispute discloses the identity too.

### 19.4 Agent cards, skills, lifecycle, errors, idempotency and caller authentication

Illustrative fixtures (labelled illustrative; no service exists):
- `a2a-card-hosted-witness.json`: an OpenID Connect security scheme with a security requirement, HTTPS, one skill `witness-digest`, and the profile extension with `required: true` and `wire: digests-only`.
- `a2a-card-local-registrar.json`: loopback interface, skills `register` and `verify`, `wire: local-only`.
- `a2a-request-witness.json` and `a2a-task-witness.json`: the request and the completed task. The witness statement is really signed with a second public test-only key; its RFC 3161 evidence is a placeholder.
- `mcp-tool-register.json`: the local MCP tool. Its inputs are paths. Its output is an opaque bundle id, never a path (SK.2). Its annotations are `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: false` (each call makes a new registration) and `openWorldHint: true` (it contacts time services).
- `rendering-agent.json`: user-facing text for an agent-made registration.

**Validation.** No A2A JSON Schema is published in the repository (§19.1), so the A2A fixtures were **not validated against a published schema**. The checker compares them with the field lists of `a2a.proto` at `v1.0.1`: required and allowed fields, bindings, Major.Minor version, part one-of, task states. The MCP tool fixture **was** validated against `$defs/Tool` of MCP `schema.json` at `862397ce` (SHA-256 `907dcebc…b551`), with the repository's pinned `jsonschema` 4.23.0: 0 errors. The negative `neg-mcp-tool-shape` is also schema-valid: it fails only a Traceweave rule.

**Lifecycle.** `SUBMITTED` → `WORKING` (obtaining the TSA token) → `COMPLETED`, with exactly one artifact holding the witness bundle. `REJECTED` covers a policy refusal: quota exhausted, or a caller barred for abuse. `FAILED` covers a witness that could not obtain its TSA token; it gives no partial statement. `INPUT_REQUIRED` and `AUTH_REQUIRED` are not used: authentication happens up front (§7.4), and the request is complete or invalid.

**Errors** (categories from A1 §3.3.2):

| Condition | Error |
| --- | --- |
| Missing or invalid credential | Authentication error (HTTP 401) |
| Malformed data part, wrong `requestVersion`, digest not 64 hex | Validation error (JSON-RPC `-32602`) |
| A `raw`, `url` or `text` part | `ContentTypeNotSupportedError` |
| Request without the profile extension | `ExtensionSupportRequiredError` |
| `A2A-Version` not `1.0` | `VersionNotSupportedError` |
| Rate limit or TSA outage | System error, with `Retry-After` |

**Idempotency.** The witness keys requests on (authenticated caller, `messageId`). A retry with the same pair returns the same task and the same artifact. A new `messageId` for the same digest creates a second witness statement. That is correct, because each statement records one presentation.

**Caller authentication.** Use OpenID Connect or OAuth 2.0 client credentials for agents, and mutual TLS for organisations. The witness records `{scheme, issuer, subject}` as authenticated by that issuer, nothing more. A hosted card should be signed with JWS (§8.4) and its key pinned in verifier policy, so a fake witness card is detectable.

**Local route.** A2A §7.1 requires encryption for production deployments, so a loopback A2A listener is a development convenience. The preferred local route is MCP over stdio. It opens no listener, and its credentials come from the environment (M1 authorization).

### 19.5 What an agent-made registration can and cannot evidence

It **can** show that a particular key signed a statement naming these bytes no later than T. With (b), it also shows that a caller authenticated by a named issuer presented the signature digest at the witness's receipt time.

It **cannot** show:
- whether a person or an agent created the content;
- whether the agent acted on a person's instruction;
- on whose behalf it acted. An OAuth token held "on behalf of" a user shows delegated **authorization** to call the witness, not creation;
- that the content came from that agent rather than being copied into its output.

A key held by an agent runtime says nothing about the human. A key held by a person but used by their agent says nothing about which of them wrote the bytes.

**Design choices.** The statement gets **no** creator or agent field in draft-3 (`authorship-claim` covers attempts). If the owner wants the generating tool recorded, add it later only as a claim (`claims.generator`), shown as claimed. By default, the creator key belongs to the person or organisation, and an agent uses it only through the local tool with the person's consent. MCP's "human in the loop" SHOULD applies.

**Required wording.** Every rendering of an agent-made registration uses only the §11 templates, includes the per-key bound sentence and the two fixed §11 sentences, and adds this one (`notice-missing`):

> A registration made by or through an agent shows which key signed it and, for a hosted witness, which authenticated caller presented the digest; it does not show whether a person or an agent created the content, or on whose behalf.

### 19.6 Abuse and mitigations

| Abuse | Mitigation | What remains |
| --- | --- | --- |
| Registering content one did not create, including mass registration of scraped content by agents to manufacture earlier records | None technical. §11 and §19.5 wording everywhere. The hosted witness offers **no** public lookup by digest, so it is not a registry that answers "who registered this?". Per-caller quotas | Anyone with a copy can register it. First to register is not first to create |
| Flooding the hosted witness | Authentication on every request; per-caller rate limits and quotas (MCP servers "**MUST** … Rate limit tool invocations"); one 64-hex digest per request; refusal as `REJECTED` | Cost to the operator, which is why SK.5 must decide |
| Flooding public TSAs and calendars from the local tool | One signature covers up to 64 subjects (§4.1); batch per work session | Each service's own limits apply |
| Backdating through the witness | The caller cannot set `receivedAt`. The witness's own TSA token bounds its statement. The witness counts as one independence group under the verifier's policy, so q = 2 still needs an unrelated root | A compromised witness backdates its own statements only |
| Claimed agent times presented as proof | A2A timestamps, timestamp-extension metadata and `claims.createdAt` are claimed only (§2) | — |
| Replaying a witness response onto another registration | The statement names the exact signature digest (`evidence-wrong-target`) | — |
| Prompt injection that makes an agent register or disclose | Only digests leave the machine; the tool's paths and outputs stay local; human confirmation; annotations treated as untrusted (M1) | An agent can still be induced to register something; that registration shows only what §19.5 allows |
| A fake witness | JWS-signed card (A1 §8.4); witness key pinned in verifier policy | — |

### 19.7 Roadmap mapping (proposed wording for the roadmap author)

- **SK.1** (wraps stable I2 commands): the MCP tool and the local A2A registrar wrap `register` and `verify` once those commands exist and are stable. Diagnostics pass through unchanged.
- **SK.2** (canaries): add "registration tools return opaque bundle ids; seeded paths, key material and nonces appear 0 times in model-visible output".
- **SK.3** (A2A design): proposed addition: "Registration is local-first with the registrant's key; a hosted witness, if any, receives only the SHA-256 of a DSSE signature and returns a signed witness statement as an A2A artifact. Design: `research/drafts/registration-record.md` §19." The non-author review stays required.
- **SK.4** (A2A interoperability): A2A publishes no committed JSON Schema; `a2a.json` is generated from `a2a.proto`. **New wording needed:** "the agent card and skill descriptions validate against the JSON Schema generated from `specification/a2a.proto` at a pinned A2A tag, with the generator and its version recorded (0 errors)".
- **SK.5** (hosted service, owner): add the operating requirements of §19.2 as the decision's checklist: key custody, accountable operator, availability, cost, retention and privacy policy, accepted identity providers, abuse policy.
- **M4:** the witness becomes one more time-evidence type (`traceweave-witness`), counted as one independence group by the verifier's policy. The M4.5 decision record should say whether that type exists.
- **New REG.5 (E, S):** the agent fixtures (cards, request, task, tool, renderings) are checked by `validate`; 0 `raw` or `url` parts and 0 fingerprints in any hosted-route fixture; every card skill and agent rendering carries the required sentences.

**Needs the owner:**
- running any hosted witness or signer (SK.5), and who operates it;
- its keys, custody and costs;
- which identity providers callers may use;
- whether agents may hold their own registration keys by default;
- publishing the extension URI and the witness predicate under `traceweave.org`;
- the SK.3–SK.5 and REG wording above.

## 20. Verification of this draft

Run on 2026-11-24 on `roadmap-v2` (parent `66aec94`), over this draft, lane 13 and the fixtures directory:

- `make_real_vectors.py`, run once: it wrote 13 files to `real-format/`, and `openssl ts -verify` reported `Verification: OK` for the good token. Only the local `openssl` was used; no external service was contacted.
- `check_registration.py` (draft-3):
  - the Ed25519 (RFC 8032 tests 1 and 2) and PAE self-tests pass;
  - 54 positive fixtures give no code, and each of the 81 negative fixtures gives exactly its expected codes;
  - all 25 wrong-implementation cases behave as required;
  - all 48 codes appear in this document and have a negative fixture.
- `build_fixtures.py` rerun: the rebuilt files are byte-identical to the committed ones.
- The two event-order fixtures have identical result objects (B2).
- `tools/validate.py`, `python -m unittest discover -s tests`, `tools/validate.py --links-all`, `tools/check_hygiene.py --messages` and `git diff --cached --check`: results in the commit message of this change.
- The MCP tool fixture still validates against MCP `schema.json` `$defs/Tool` (0 errors). The A2A fixtures are not validated against a published A2A schema, because none is committed upstream (§19.4).
- No new external URL was added in draft-3.
- **Not done:** no token, proof, log entry or cosignature from any real service was requested or verified, and no implementation exists.

## 21. Review dispositions (draft-2)

Every finding of the [non-author review](../reviews/registration-record-review.md) (`5c3d9c5`), with what changed. "Fixture" names the evidence in [registration-fixtures](registration-fixtures/README.md).

| Finding | Disposition | Where |
| --- | --- | --- |
| F1 bounds per signature, not per statement | Fixed. Bounds are computed per signature from evidence targeting it. Each names its key. A later co-signature inherits nothing. The bound sentence is generated per key | §6.4, §10 step 10, §11; `bundle-cosigned`, `verification-result-cosigned`, `rendering-cosigned`, `neg-key-bound-misattributed`, `neg-key-bound-misattributed-rendering` |
| F2 roots by trust anchor; independence by policy; three sources | Fixed. `root: {kind, anchorSha256}` replaces labels. The policy lists anchors and independence groups. Three sources (two TSAs and Bitcoin) with q = 2 are recommended, and both bounds are always reported | §2, §6.3, §13, RD1, RD5; `neg-root-not-anchored`, `neg-quorum-same-anchor`, `verification-result-revoked` |
| F3 key events as verification input; hostile early compromise claims | Fixed. Who may assert an event; events need their own quorum bound; a look-back clamp; `disputed` instead of silent `untrusted`; event outcomes in the result | §8, §10 steps 3–4, RD15, RD17; `verification-result-compromise-recent`, `-compromise-early`, `-event-unauthorized`, `neg-key-event-ignored` |
| F4 rendering rules; "permission" in sentence 2 | Fixed. The allow-list of templates rejects all four accepted renderings. Sentence 2 now ends "…who owns it, or that its use is permitted." | §11; `neg-authorship-claim-0`…`-4`, `neg-rendering-unlisted-line` |
| A1 which bytes the target covers | The raw decoded signature bytes | §6.1; `neg-evidence-target-base64` |
| A2 which bound `after-proved-bound` compares | The earliest `notAfterAnyRoot` over valid signatures, reported as `comparedWith` | §10 step 11 |
| A3 accuracy contradiction | The policy gives `accuracySeconds` per anchor. A token without accuracy and with none in policy is the outcome `unsupported`, not a failure code. `neg-evidence-shape` now tests a malformed `genTime` | §6.2; `verification-result-no-accuracy`, `neg-accuracy-assumed` |
| A4 Ed25519 strictness | Pinned to RFC 8032 §5.1.7, cofactorless, with S < L, canonical A and R, and A not of small order; self-tested against two lenient verifiers | §10.1, RD16 |
| A5 field names only in fixtures | Named in §6.2 | §6.2 |
| A6 "and others" key lists | Closed lists, stated | §4.6 |
| A7 key lookup with absent or unmatched hint | `unknown-key`; no trial verification | §10 step 2 |
| A8 opening catalogue bytes | The exact stored bytes; RFC 8785 bytes in the fixtures | §4.4, §9 |
| W3 two TSAs under one CA as two roots | Rejected by anchors and policy groups | `neg-quorum-same-anchor`, `neg-root-not-anchored` |
| W4 nonce reused | Producer obligation; cross-record check | §4.2; `neg-nonce-reused` |
| W6b subject over normalized bytes, bytes not supplied | Producer obligation; a verifier without the bytes must say `not-supplied` | §4.1; `neg-subject-unsupplied-match` |
| W8 co-signer reported with the earlier bound | Rejected | as F1 |
| W9 TSA certificate validity at `genTime` | Placeholders now carry `signerCertificate`; outside validity gives `invalid` | §6.2; `neg-cert-validity-ignored` |
| W10 compromised key still `trusted` | Rejected | as F3 |
| W12 four authorship renderings | Rejected | as F4 |
| Four codes with no negative fixture | `report-digest`, `profile-mismatch`, `catalogue-not-report-input` and `fixture-shape` now have one each. The checker now fails if any code lacks one | §18 |
| Wrong-implementation self-test | Added: 14 in-memory cases (W3, W8, W10, the four W12 lines, the margin dropped, the earliest taken as quorum, revocation ignored, the base64 target, two lenient Ed25519 verifiers, a non-canonical point) | §18 |
| RFC 3161 revocation and reason codes; request nonce; policy OID | Added, with outcomes `revoked` and `wrong-policy`, and code `tsa-nonce-mismatch` | §6.2; `verification-result-revoked`, `neg-tsa-nonce-mismatch` |
| OpenTimestamps "offline" needs a header source | Stated: a trusted node or retained header file | §6.2, §13, §14 |
| RD6 margin rationale pointed the wrong way | Corrected; the honest-majority assumption is stated | §6.2, RD6 |
| Retroactive loss of one source | Threat added; three sources recommended | §12, §13 |
| Key-theft window; linkage; low-entropy content; algorithm ageing triggers | Added | §5, §7 (I0′), §12 |
| Possession digest adds nothing for content public at T | Stated | §4.3, §12 |
| Published commitment nonce reused in fixtures | Stated in the README and in the builder | README |
| Lane 13 RFC 3161 §4.1 claim incomplete; "offline once complete" | Corrected in lane 13 | lane 13 T1 row, Decision |
| §7 test-submission disclosure | Recorded for the owner decision | §17 |

## 22. Resolution table (draft-3)

Every item of the [draft-2 confirmation review](../reviews/registration-record-draft-2-review.md) (`66aec94`). Fixtures are in [registration-fixtures](registration-fixtures/README.md); "self-test" means a case in the checker's wrong-implementation self-test.

| Item | Resolution | Section | Fixtures |
| --- | --- | --- | --- |
| **B1** stolen key rotates to the thief; successor stays trusted | Compromise disputes rotations and retirements of the key with proved time ≥ `start`; no trust through a disputed rotation; conflicting rotations both disputed | §8 | `verification-result-rotation-hijack`, `verification-result-rotation-conflict`, `neg-rotation-hijack`, `neg-rotation-conflict`; self-test ×2 |
| **B2** event outcomes depend on input order | Evaluation by proved time E (ties by payload digest), authorization only from smaller E, iterated to a fixed point; output sorted | §8, §10 step 3 | `verification-result-event-order-a` and `-b` (identical objects), `neg-event-order-dependent`; self-test |
| **B3** trust and events keyed on the 64-bit keyid | `trustedKeys` and event targets and successors by SHA-256 of the full key; `keyid` must agree with the subject digest | §7, §8 | `neg-trust-by-hint` (`key-identity-by-hint`), `neg-key-event-subject-mismatch`; self-test |
| **S1** trust decided on one source | With no quorum bound, a signature touched by an event is `disputed` | §8, §10 step 4 | `verification-result-single-source-event`, `neg-trust-without-quorum`; self-test |
| **S2** RFC 3161 token checks missing | Imprint, request nonce, ESSCertID or ESSCertIDv2, critical timeStamping EKU, single SignerInfo and signature, chain to the pinned root; each with a code or outcome | §6.2 | real-format: `evidence-real-rfc3161`, `neg-tsa-imprint-mismatch`, `neg-tsa-signature-invalid`, `neg-tsa-eku-invalid`, `neg-tsa-signing-cert-mismatch`, `neg-real-root-not-pinned`; self-test |
| **S3** offline result without revocation date | `revocationData` with `source` and `asOf` per anchor; `no-revocation-data`; `revocationDataAsOf` per evidence; "as of" in §12 and §13 | §6.7, §12, §13 | `verification-result-no-revocation-data` |
| **S4** witness and its TSA counted twice | A witness evidence rests on two anchors; groups merged per evidence (union-find) | §6.2, §6.3, §19.2 | `verification-result-witness-shared-tsa` (`below-quorum`), `-witness-independent`, `neg-witness-shared-tsa`, `evidence-witness`; self-test |
| **S5** cosigned checkpoint without inclusion proof | Type removed in draft-3 | §6.2, RD19 | `neg-checkpoint-type-removed` |
| **S6** renewal undefined | Renewal evidence over the earlier token's bytes; rule at verification time; limits stated | §6.6, §12, §14 | `bundle-renewed`, `evidence-renewal`, `verification-result-renewed`, `-expired`, `neg-expired-accepted`, `neg-renewal-wrong-target`; self-test |
| **S7** URL-safe base64 rejected | Accepted, as DSSE requires | §10 step 1 | `bundle-url-safe`; self-test |
| **S8** claims discipline | Third fixed sentence on ordering; `ordering-claim`; "registrant" throughout; §19.2 (a) reworded; the witness template names its TSA | §1, §11, §14, §15, §19 | `neg-ordering-claim`, `rendering-agent`; self-test |
| **S9** missing vectors | Added: `wrong-policy`; `keyCompromise` and retaining-reason revocations; a result that applies a rotation; B1–B3; two orders; subject mismatch; S1; S4; URL-safe; duplicate signer; out-of-range index; stripped evidence; real-format TSA and OpenTimestamps vectors made locally | §6.5 | `verification-result-wrong-policy`, `-revoked-key-compromise`, `-revoked-retaining`, `-rotation-applied`, `-stripped`, `neg-duplicate-signer`, `neg-signature-index-out-of-range`, `bundle-real`, `verification-result-real`, `evidence-real-*`, `neg-real-ots-*` |
| **S10** anchors written by the producer | Real-format vectors compute anchors from the pinned root certificate and header file; README and REG.1 say placeholders do not test this | §2, §6.5, §15 | `verification-result-real`, `neg-real-root-not-pinned`, `neg-real-ots-other-chain` |
| **S11** untrusted co-signer changes the claim outcome | Compare only with trusted signatures; `not-compared` when none | §10 step 11 | `verification-result-claim-trusted-only`, `neg-claim-any-signer`; self-test |
| **S12** C2PA claim in §15 | Corrected: a C2PA export needs its own token over the claim signature; registration evidence does not map | §15 | — (text) |
| **S13** roadmap gates cannot be evidenced | Exact ROADMAP.md text proposed for M4.3, M4.5, M4.6 and REG.1–REG.5; adoption is the owner's | §15, §17 | — (text) |
| **N1** fractional seconds | `notAfter` rounded up to the whole second | §6.2 | `realformat.py` (`gtime`, accuracy) |
| **N2** `blockTime` from the evidence | Read from the pinned header; minimum confirmations | §6.2 | `verification-result-real`, `neg-real-ots-other-chain` |
| **N3** evidence can be stripped | Stated: bounds only get later | §6.4, §12 | `verification-result-stripped` |
| **N4** in-toto, DSSE, Ed25519 conformance | No change needed | §10.1 | — |
