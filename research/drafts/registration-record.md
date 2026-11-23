# Registration record: design draft-2

Status: research draft, draft-2 of 2026-11-23. It resolves the non-author [review](../reviews/registration-record-review.md) (`5c3d9c5`); §21 maps every finding to its change. Not normative. No schema, profile, vector or roadmap file is changed by this draft. Nothing was submitted to any time-stamping authority, log, calendar or witness. Every time evidence in the [fixtures](registration-fixtures/README.md) is a labelled placeholder, and every trust anchor in them is a placeholder digest.

Evidence for the mechanisms is in [lane 13](../lanes/13-timestamp-evidence-review.md), cited as T1–T9 and L1–L2. Context:
- the [roadmap](../../ROADMAP.md) finding of 2026-11-23 that a mark is a finding aid and not evidence of origin; M4;
- [attestations](../../spec/attestations.md); [core](../../spec/core.md);
- the [catalogue and report contract](../../spec/catalogue-report.md) §6.6–§8 (B10);
- [use cases](../../docs/use-cases.md) UC-3 and UC-4;
- the [C2PA mapping draft](c2pa-mapping.md); the [lane 11 audit](../lanes/11-report-audit.md) (signed reports are M4).

**What changed from draft-1:**
- Time bounds are per signature and name their key (§6.4).
- Time sources are identified by trust anchor, and the verifier's policy decides independence. Three sources are recommended, with quorum 2 (§6.3).
- Key events are a verification input with their own outcomes, and an early-dated compromise claim is bounded (§8).
- Renderings use an allow-list of line templates (§11).
- Ed25519 verification is pinned (§10.1).
- RFC 3161 revocation, the request nonce and the policy OID are checked (§6.2).
- The OpenTimestamps header source and margin rationale are corrected (§6.2).
- Every object version string ends in `draft-2`.

## 1. Summary

A **registration record** lets a creator later show: *these exact bytes existed, and my key signed a statement naming them, no later than time T.* It is a signed in-toto statement (DSSE), plus time evidences attached as separate objects. Each time evidence countersigns **one** signature under **one** trust anchor. A verifier reports each part separately:
- the digest and possession checks;
- each signature and its signer trust;
- each key event;
- each time evidence;
- **for each signature**, the earliest single-source bound and the bound agreed by a quorum of independent sources.

There is never a single "authentic" verdict.

A registration does **not** show authorship, originality, ownership or permission. It does not show that the registrant created the content rather than copied it first. **First to register is not first to create.** §11 makes this text mandatory wherever a registration is shown to a person, and allows only listed line templates.

A registration does not depend on the content's profile. Python source under `py-tokens` draft-1 is registered exactly like Go, Rust or any other bytes; the profile matters only for the optional catalogue commitment (§4.4).

Recommended first mechanisms: **RFC 3161 time-stamp tokens from two unrelated TSAs** and **OpenTimestamps** (Bitcoin), with quorum 2 (§13). That is three time sources, so losing one, for example to a TSA certificate revocation, still leaves two.

## 2. Terms

- **Claimed time:** a time written by the registrant (`claims.createdAt`), like core's `recordedAt` and the report's `generatedAt`. Anyone can write any value. It is never shown as proved.
- **Bound (`notAfter`):** an upper bound on when one signature existed, from one verified time evidence under the verifier's policy. Time evidence gives only upper bounds. Nothing here proves a lower bound or a creation time.
- **Trust anchor:** what a time source's validity ultimately rests on, identified by a SHA-256 the verifier computes, never by a name the producer writes:
  - TSA: the DER root certificate of the token's chain;
  - Bitcoin: the chain as pinned by the verifier's own node or header file;
  - log or witness: the public key.
- **Independence group:** a label in the **verifier's** policy. Anchors in the same group count once.

## 3. Objects

All version strings and predicate URLs are proposals in the `traceweave.org` namespace, which [C2PA draft](c2pa-mapping.md) D3 also leaves to the owner.

| Object | Version string | Content | Fixture |
| --- | --- | --- | --- |
| Registration statement | `traceweave-registration-draft-2`; predicate type `https://traceweave.org/predicate/registration/draft-2` | in-toto Statement v1 (§4) | `statement.json` |
| Bundle | `traceweave-registration-bundle-draft-2` | DSSE envelope with one or more signatures, public keys, time evidences | `bundle-three-roots.json`, `bundle-cosigned.json`, `bundle-second-work.json` |
| Time evidence | `traceweave-time-evidence-draft-2` | One evidence: target signature, trust anchor, type-specific fields (§6) | `evidence-*.json` |
| Key event | `traceweave-key-event-draft-2`; predicate type `https://traceweave.org/predicate/key-event/draft-2` | Retire, rotate or report a key compromised, time-stamped like a registration (§8) | `key-event-*.json` |
| Verification result | `traceweave-registration-verification-draft-2` | The closed outcomes of §10, with the policy used | `verification-result*.json` |
| Report link | `traceweave-registration-link-draft-2` | Ties a comparison report to a registration without changing the report (§9) | `report-link.json` |
| Registration set | `traceweave-registration-set-draft-2` | Several registrations by one producer, for the nonce-freshness check (§4.2) | `registration-set.json` |
| Rendering | `traceweave-registration-rendering-draft-2` | User-facing lines from the §11 templates | `rendering*.json` |

## 4. The registration statement

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [{"name": "sum.go", "digest": {"sha256": "974c8d0a…697c"}}],
  "predicateType": "https://traceweave.org/predicate/registration/draft-2",
  "predicate": {
    "registrationVersion": "traceweave-registration-draft-2",
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
- Other unknown fields are rejected (`statement-shape`), and so is a wrong predicate type (`predicate-type`), including the draft-1 type.

## 5. What publishing each value reveals

A registration is **private by default**. The creator keeps the bundle; only digests of signatures go to time services (§6). The table assumes the item named is published, for example in a dispute.

| Published value | Reveals about unknown content | Guessing attack | Verdict |
| --- | --- | --- | --- |
| Digest of a DSSE signature (what time services see) | Nothing; the statement contains a fresh 256-bit nonce | None feasible | Safe to send. Links the evidences of one registration to each other and to the requester's IP address and timing (T1 §4 item 5, T4) |
| Artifact digest (`subject`) | Nothing about content the attacker lacks | **Confirmation:** anyone holding a candidate file confirms exact equality. Low-entropy content (a short snippet, a template with few variants) can be enumerated | Disclose only with the bytes, in a dispute |
| Possession digest | Nothing without the nonce. After disclosure, the same as the artifact digest, so short snippets are not protected by it either | As the artifact digest, after disclosure | Disclosed with the statement |
| Salted catalogue commitment | Nothing until opened | None before opening. **Opening reveals the whole catalogue** (core) | Safe in the statement |
| Plain catalogue digest | Nothing directly | **Whole-set confirmation:** catalogues are deterministic in their artifacts, ids and configuration (contract §3.3), so anyone with candidate files and guessed ids rebuilds and confirms | Never (`catalogue-unsalted`) |
| Fingerprints | Structure, positions and spans | **Fragment membership:** anyone can fingerprint any text and learn which fragments the private content contains | Never in a registration (`forbidden-field`) |
| Public key | Links every registration made under it | — | One key per creator (I0) links all disclosed registrations and all time-service requests under it. A per-work key avoids that, at the cost of identity continuity (§7) |
| OIDC identity in a public log | Identity, time and the logged digest, **for ever** (T3) | — | Opt-in only, owner-gated |

## 6. Time evidence

### 6.1 What is time-stamped (A1)

Each evidence targets **one** signature: `target: {kind: "dsse-signature", signatureIndex, sha256}`. `sha256` is the SHA-256 of the **raw decoded signature bytes** (64 bytes for Ed25519), not of the base64 text in the envelope (`neg-evidence-target-base64`). This follows Sigstore's countersigning advice and C2PA's v2 payload (T3, T6).

A signature exists only after its statement does, so a bound on the signature bounds the statement, including its subjects and possession digests. The bound also survives a later theft of the registrant's key: a thief can sign new statements but cannot obtain evidence dated before the theft. Evidence over another digest, such as the statement bytes, is rejected (`evidence-wrong-target`).

### 6.2 Evidence types: fields, checks and bounds

Every evidence has `evidenceVersion`, `type`, `placeholder`, `notice`, `target`, `root: {kind, anchorSha256}` and `token`, plus one type-specific object. A root identified by anything other than an anchor digest is rejected (`root-not-anchored`). A placeholder without the exact notice, or whose token text does not start with `PLACEHOLDER`, is rejected (`placeholder-unlabelled`). A malformed evidence is `evidence-shape`.

**`rfc3161`**, root kind `tsa-certificate-chain`. Fields: `rfc3161: {genTime, accuracySeconds (optional), policyOid, nonce, requestNonce, signerCertificate: {notBefore, notAfter}}`. A real implementation reads `genTime`, `accuracy`, `policy` and `nonce` from the token (TSTInfo, RFC 3161 §2.4.2), `requestNonce` from its own request record, and the certificate validity and anchor from the chain.
- **Request nonce.** The producer sends a fresh nonce in the request (§2.4.1) and checks that the token echoes it. That is what detects a replayed response at request time; the statement nonce does not do this job. A token whose nonce differs from the request nonce is `tsa-nonce-mismatch`.
- **Policy OID.** The token's `policy` must be one of the OIDs the verifier's policy lists for that anchor; otherwise the outcome is `wrong-policy`.
- **Certificate validity.** `genTime` must lie within the TSA signing certificate's validity; otherwise the outcome is `invalid`.
- **Revocation** (RFC 3161 §4 items 1–2). If the TSA certificate is revoked **without** a reasonCode, or with `keyCompromise`, **every** token signed with that key is invalid, including past ones: outcome `revoked`. Only with reasonCode `unspecified`, `affiliationChanged`, `superseded` or `cessationOfOperation` do tokens issued before the revocation time stay valid. So **one TSA can be lost retroactively**, which is why §13 recommends three sources. It is also why renewal (§14 step 5) must happen *before* any revocation.
- **Bound.** `notAfter = genTime + accuracy`. When the token carries no accuracy, the verifier's policy may give one for that anchor (`accuracySeconds`; RFC 3161 §2.4.2 allows accuracy to be "available through other means, e.g., the TSAPolicyId"). With neither, the outcome is `unsupported` (A3; `verification-result-no-accuracy`).

**`opentimestamps`**, root kind `bitcoin-proof-of-work`. Fields: `opentimestamps: {status: "pending"}` or `{status: "complete", blockTime}`.
- A pending proof has no time, and stating one is rejected (`pending-counted`).
- **Header source.** Verifying a complete proof needs the attesting block header from a **trusted source**: the client README says verification needs "a local Bitcoin Core node (a pruned node is fine)" (T4). So "verifiable offline" holds only if the verifier keeps such a node or a header file it obtained from one (block headers are "80-byte" structures). The anchor is that chain as pinned by the verifier.
- **Margin and its assumption.** `notAfter = blockTime + 7,200 s`. Draft-1 justified this margin with the wrong rule. The two-hour future rule says a header time is at most two hours *ahead* of nodes' clocks. That bounds how early the block could have been mined relative to its header, which is the wrong direction for an upper bound on existence. An upper bound needs the opposite fact: a header time cannot lag the real mining time by much. Consensus gives only that a header time must exceed the **median time of the previous 11 blocks**. That keeps the lag small **only under an honest-majority assumption**: most recent blocks were mined by honest miners with roughly correct clocks, so the median of the previous 11 blocks, about an hour of blocks, is close to real time. Under that assumption, a header time lags real time by roughly an hour at most. The 7,200 s margin covers that with slack. Without the assumption, the margin has no basis. The alternative is RD6.

**`rekor-v2`**, root kind `log-key`. Fields: `rekorV2: {logIndex}`. **No bound**: Rekor v2 has no time of its own (T3), and stating one is rejected (`log-time-claimed`). It gives inclusion and discoverability only.

**`cosigned-checkpoint`**, root kind `witness-key`. Fields: `checkpoint: {cosignatureTime}`. The bound is the cosignature time, from the witness's clock (T5).

Field names are part of the format (A5). The fixtures use exactly these.

### 6.3 Roots, independence and the policy (F2)

The verifier's policy lists accepted anchors:

```json
"timeRoots": [{"anchorSha256": "…", "kind": "tsa-certificate-chain", "independenceGroup": "tsa-operator-a",
               "policyOids": ["…"], "accuracySeconds": 1}, …]
```

- An evidence whose anchor is not listed for its kind is `untrusted-root`.
- Independence is decided **only** by the policy's groups. Two TSAs under one CA share an anchor, so they count once. Two anchors that the verifier knows to be run by one operator (or by the registrant) should share a group, or not be listed at all.
- A producer-written label never counts (`root-not-anchored`). Counting two evidences with one anchor as two sources is `quorum-miscount` (`neg-quorum-same-anchor`).

### 6.4 Per-signature bounds and quorum (F1)

For **each signature** i, only evidence whose target is signature i counts.
1. Take the smallest valid `notAfter` in each independence group.
2. Sort those values.
3. `notAfterAnyRoot` is the smallest. One source vouches for it, so one dishonest or compromised source can backdate it.
4. `notAfterQuorum` is the q-th smallest (default q = 2). At least q independent sources agree that signature i existed by then.

Both bounds are always reported, with `distinctRoots`. A signature with no evidence of its own has **no** bound, even when another signature on the same statement has one. A later co-signature never inherits an earlier signature's bound (`key-bound-misattributed`; `bundle-cosigned.json`, `neg-key-bound-misattributed*`).

In the main fixture, the three sources give 10:00:01Z (TSA A), 10:00:06Z (TSA B, policy accuracy) and 13:12:00Z (Bitcoin with its margin). The bounds are therefore 10:00:01Z from any one source, and 10:00:06Z from two independent sources. With TSA A revoked, they become 10:00:06Z and 13:12:00Z (`verification-result-revoked`).

## 7. Signer identity options

| Option | What a verifier learns | Cost to the creator | Privacy |
| --- | --- | --- | --- |
| I0 Self-managed Ed25519 key, public key only in the bundle (**default**) | "Whoever holds this key signed it." Nothing about who that is. Later, the creator can show control by signing a challenge | None. Must keep the key safe and backed up | Nothing published. One key links all disclosed registrations |
| I0′ A fresh key per work, optionally linked later by a signed key list | As I0, per work | Key management per work | Disclosing one registration does not link the others. Proving that two works share a creator needs the key list |
| I1 I0 with the public key posted somewhere dated and third-party-observable | A weak link between key and a name, as strong as that site's history | None | Key linkable to the name |
| I2 Sigstore Fulcio short-lived certificate (OIDC) | "Someone who authenticated as this identity at an OIDC provider signed it" (T3). Needs time evidence: the certificate lasts 10 minutes | An identity-provider account | Identity and time in public CT and Rekor logs **for ever** |
| I3 Organisation or qualified certificate | The CA's identity checks, under its policy | Paid; identity verification | Whatever the certificate contains |

The key id is a lookup hint, not identity ([attestations](../../spec/attestations.md)). Signer trust is the verifier's policy decision (`trustedKeyids`), reported separately from signature validity.

## 8. Key loss, rotation, compromise and revocation (F3)

**Key events are statements too.** A key event is an in-toto statement whose subject is the public key, with predicate `{eventVersion, keyid, event, successorPublicKeyHex (rotated only), compromisedNotBefore (compromised only)}`. It is signed and time-stamped exactly like a registration. A malformed event is `key-event-shape`.

**Who can assert an event:**
- the key itself;
- a successor named by an earlier event that was itself applied.

An event signed by any other key is `ignored-unauthorized` (`verification-result-event-unauthorized`). A verifier may add other authorized keys in its own policy; the fixtures do not.

**An event counts only with proved time.** Its own quorum bound E (§6.4) is the time it was proved to exist. Without a quorum bound it is `ignored-no-proved-time`. An event with an invalid signature is `invalid-signature`. Otherwise it is `applied`. The result lists every event supplied, with its outcome and E.

**Effect on a signature by that key**, where B is the signature's quorum bound (or its single-source bound when there is no quorum):
- **`compromised` with claimed start Tc.** Let `start = max(Tc, E − lookback)`, where `lookback` is the verifier's `compromiseLookbackSeconds` (30 days in the fixtures; RD15).
  - B < start: trust unchanged.
  - start ≤ B < E: **`disputed`**. A registration made with a stolen key in that window cannot be told apart from the owner's.
  - B ≥ E, or no bound: `untrusted`.
- **`retired`, or `rotated` to a successor:** B ≥ E, or no bound, gives `untrusted`; earlier signatures are unchanged. A rotation makes the successor trusted for signatures with B ≥ E, if the old key was trusted.

**Why an early-dated false claim cannot erase honest history.** A thief, or a former collaborator who holds the key, can publish `compromised` with Tc far in the past. Draft-1 let that flip every past registration to `untrusted`. Now:
- the event's effect starts no earlier than E − lookback;
- inside that window the outcome is `disputed`, shown with both times, not silently `untrusted`;
- registrations bounded before the window keep their trust (`verification-result-compromise-early`: Tc 2026-01-01, E 2027-01-15, the 2026-11-23 registration stays `trusted`).

The trade-off: an honest owner who discovers a theft later than the look-back window cannot dispute registrations made before it. A result that ignores an applicable event is `key-event-ignored`.

**Key loss.** Existing registrations stay verifiable, because the bundle carries the public key and each signature's bound. The creator can no longer sign new registrations or events with that key. Recovery is a new key, linked through I1 or I2.

**TSA revocation** is a separate input: the policy's `tsaRevocations` (§6.2).

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
- the verifier's **policy**: `{quorum, timeRoots, trustedKeyids, tsaRevocations, compromiseLookbackSeconds}`. A result carries the policy it used.

Every step reports its own outcome, and a failure in one step does not change another step's outcome.

1. **Parse** strictly: no duplicate keys (`duplicate-key`); size limits as in the signing harness. Outcome `envelope`: `ok` | `malformed` (`envelope-shape`).
2. **Signatures.** Look up each key by its `keyid` hint among the bundle's keys. A missing or unmatched hint gives `unknown-key`; there is no trial verification against other keys (A7). Verify under §10.1 over `PAE(payloadType, payload)` of the exact payload bytes. Per signature: `valid` | `invalid` | `unknown-key` (`signature-invalid`).
3. **Key events.** Verify each event bundle as in steps 1, 2 and 8. Per event: `applied` | `ignored-unauthorized` | `ignored-no-proved-time` | `invalid-signature`, with its proved time E (§8).
4. **Signer trust**, from the policy and the applied events. Per signature: `trusted` | `untrusted` | `disputed` | `not-evaluated` (when the signature is not valid).
5. **Statement.** Strictly parse the payload and apply §4. Outcome `statement`: `ok` | `malformed` | `unsupported`.
6. **Subject digests.** Per subject: `match` | `mismatch` | `not-supplied`.
7. **Possession digests.** Per subject: `match` | `mismatch` | `not-supplied`.
8. **Catalogue.** `opens` | `does-not-open` | `not-supplied` | `not-committed`.
9. **Each time evidence.** Check the target, then verify under its anchor and the policy (§6.2), offline from retained material. Per evidence: `valid` | `invalid` | `wrong-target` | `pending` | `untrusted-root` | `unsupported` | `wrong-policy` | `revoked`, with its target signature and `notAfter`. In fixtures only, `placeholder`, or `placeholder-assumed-valid` when the result says `simulated: true`.
10. **Bounds, per signature** (§6.4): `quorum-met` | `below-quorum` | `none-valid`, with `keyid`, `quorum`, `distinctRoots`, `notAfterAnyRoot` and `notAfterQuorum`.
11. **Claimed time.** `absent` | `claimed-only` | `after-proved-bound`. The comparison (A2) is with **the earliest `notAfterAnyRoot` over all valid signatures**: the earliest evidence that the statement existed, whoever signed. The value compared with is reported as `comparedWith`. A claim later than that is impossible, and points at a wrong clock or a careless registrant.
12. **Output** all outcomes, and the fixed `notShown` list: `authorship`, `originality`, `first-creation`, `ownership`, `permission`.

A result must not:
- add a combined verdict (`authentic`, `verdict`, `overall` and similar: `single-verdict`);
- report the claimed time as a bound (`claimed-as-proved`);
- count a pending proof (`pending-counted`);
- give a signature a bound it has no evidence for (`key-bound-misattributed`);
- count one group twice (`quorum-miscount`);
- ignore an applicable key event (`key-event-ignored`);
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
| `Witnessed: the caller <subject> presented the signature digest at <T> by the witness's clock.` | §19 witness |

The text must also contain the two fixed sentences, and for agent-made registrations the §19.5 sentence:

> It does not show who created the content, that it is original, that the registrant was first to create it, who owns it, or that its use is permitted.
> First to register is not first to create.

**What the checker rejects:**
- A line outside the templates is `rendering-unlisted-line`, even a harmless one.
- An unlisted line that also uses an authorship or ownership word is additionally `authorship-claim`. The words are `author…`, `wrote`, `written`, `belongs`, `your`, `claim to`, `registered to you`, `first to create`, `priority`, `created`, `creator`, `own…`, `original…`, `copyright`, `proves`, `proof`, `establish…`, `authentic…`, `verified`, `genuine`, `legitimate`. This rejects the four renderings the review's checker accepted (`neg-authorship-claim-1` to `-4`).
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
| Service shutdown | TSA, calendar, log | Three sources; complete evidence verifiable offline from retained chains and headers | An OpenTimestamps proof is lost if every calendar disappears before upgrade (T4) |
| Algorithm ageing | Time | Renewal triggers: a TSA key nearing expiry, any revocation notice, or weakness reported in SHA-256 or Ed25519. Renew by re-time-stamping the bundle (T9); for SHA-256, hash-tree renewal over the original data per RFC 4998 | A renewal must happen before a break, not after |
| Lenient signature verifiers | Implementations | §10.1 rule set, self-tested | — |

## 13. The two mechanisms to implement first, and why

1. **RFC 3161 tokens (T1), from two unrelated TSAs.** Implement this first. It is the standard form consumed by C2PA, Sigstore bundles, eIDAS qualified time-stamps and RFC 4998 renewal. Precision is about a second. Verification needs only the retained chain and revocation data, and no header source. Public TSAs need no account, but the owner must read their terms. A qualified TSA can be added later for creators who want the eIDAS presumption (L1), without a format change.
2. **OpenTimestamps (T4).** Its root, Bitcoin proof of work, has no operator who can backdate. It needs no account and no fee. Once upgraded, it survives the shutdown of every calendar. Its costs are acceptable for the third source: hours of precision, a pending window, LGPL-3.0 client code, and a trusted Bitcoin header source to verify.

Two TSAs plus OpenTimestamps give **three independent sources with q = 2**, so one retroactive TSA revocation still leaves a quorum. Rekor and witness cosigning are deferred: they add discoverability and split-view protection that private registrations do not need, and Rekor v2 needs a TSA token for time anyway (T3).

## 14. What a creator would do in practice

1. **Once:** generate a signing key with the tool, stored in the private location of contract §6.8 B11, and back it up in two places. Optionally publish the public key somewhere dated (I1), or choose per-work keys (I0′).
2. **For each piece of work:** run a local `register` command on the original files. It hashes them, draws a nonce, computes the possession digests, and optionally builds the private catalogue and its commitment. It then signs the statement and sends **only the SHA-256 of the signature bytes** to two TSAs, each with a fresh request nonce that it checks, and to OpenTimestamps calendars. No content and no identity leaves the machine. It reports `pending` for the Bitcoin part.
3. **A few hours later:** upgrade the OpenTimestamps proof and save the bundle again. The tool can do this on its next run.
4. **Keep, unchanged and backed up:** the original bytes, the bundle, the catalogue and its opening, the TSA certificate chains, and access to a Bitcoin header source.
5. **Renew** before a TSA key expires, on any revocation notice, or on reported weakness in SHA-256 or Ed25519: run `renew` to time-stamp the existing bundle again (T9).
6. **In a dispute:** hand over the original bytes and the bundle, and the catalogue opening only if needed. The other side runs §10 with their own policy and reads the §11 limits.

## 15. Roadmap mapping (proposed wording; ROADMAP.md is not changed here)

| Gate | Today | Proposed change |
| --- | --- | --- |
| M4 row, "What becomes possible" | A recipient checks a signed evidence record | Add: "A creator can show that registered bytes existed under a named key no later than a time, agreed by two independent time sources; a registration never shows authorship or first creation." |
| M4.3 | Negative cryptographic vectors | Add the registration codes: `evidence-wrong-target`, `possession-mismatch`, `subject-mismatch`, `signature-invalid`, `duplicate-key`, `pending-counted`, `log-time-claimed`, `tsa-nonce-mismatch`, `key-bound-misattributed`, plus the §10.1 Ed25519 edge vectors, each distinct |
| M4.5 | "A recorded decision on the optional timestamp adapter" | **New wording needed:** "A recorded owner decision selecting the time-evidence types for registration records (proposed: RFC 3161 from two TSAs, and OpenTimestamps), the quorum default, the look-back default, and which external services may be used for test tokens." Time evidence is not optional for a registration record |
| M4.6 | Commitment/disclosure design review | Extend to the nonce, the possession digest, the §5 table and the §8 key-event rules |
| New REG.1 (E, S) | — | Registration fixtures (this directory, after review) checked by `validate`: every positive passes, every negative gives its codes, the wrong-implementation self-test passes |
| New REG.2 (E, I) | — | Two implementations produce identical outcomes (§10) on every REG.1 fixture, including the §10.1 edge vectors |
| New REG.3 (E, I) | — | With owner approval for the services: real RFC 3161 tokens from two TSAs and one upgraded OpenTimestamps proof over a synthetic registration, verified with the network denied and retained headers, k/k; failure directions tested (wrong target, tampered token, wrong policy OID, wrong nonce) |
| New REG.4 (E, S+I) | — | Every user-facing rendering uses only the §11 templates and the fixed sentences; a non-author reviews the templates (feeds M5.2 and WEB.5) |
| UC-3 | Limit: "Signing alone proves neither ownership nor earlier existence" | Unchanged for signing alone. A new use case (for example UC-9, "Register content now, show possession later") needs owner wording; this draft supplies its limit text (§11) |
| C2PA mapping | Time-stamp row "conflicting" | A C2PA manifest holds **one** RFC 3161 token over its claim signature (T6). One TSA evidence maps; the second TSA, OpenTimestamps and the quorum are unmapped |

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
| RD13 | Agent identity in the statement | None; claimed `claims.generator`; delegated-identity field | None in draft-2 (§19.5) |
| RD14 | Local agent route | MCP over stdio; A2A on loopback; command line only | MCP over stdio first |
| RD15 | Compromise look-back | 30 days; 90 days; no clamp | 30 days as the fixture default. **Owner/policy choice:** longer protects owners who discover theft late, shorter protects honest history from hostile claims |
| RD16 | Ed25519 rule set (§10.1) | As specified; also reject small-order R; cofactored equation | As specified; record it with REG.2 vectors |
| RD17 | Who may assert key events | The key and verified successors; plus policy-listed keys | The key and verified successors by default; policy may add keys |

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
- The ROADMAP wording of §15, the new REG gates and the new use case.
- Everything listed at the end of §19.7.
- Legal questions. Lane 13 quotes eIDAS and the US Federal Rules of Evidence only; nothing here is legal advice.

## 18. Fixtures and checker

See the [fixtures README](registration-fixtures/README.md). `check_registration.py` (standard library) does three things:
- **It checks the fixtures.** It verifies Ed25519 signatures under §10.1 with public test-only keys; recomputes digests, possession digests, the catalogue commitment and the full expected verification result (per-signature bounds, policy groups, revocations, key events); and applies the §11 allow-list.
- **It runs a wrong-implementation self-test.** Fourteen plausible wrong verifiers and renderings are built in memory, and each must be rejected.
- **It runs a drift check.** Every failure code must appear here and have a negative fixture.

It verifies no real time evidence.

Failure codes: `authorship-claim`, `catalogue-does-not-open`, `catalogue-not-report-input`, `catalogue-unsalted`, `claimed-as-proved`, `duplicate-key`, `envelope-shape`, `evidence-shape`, `evidence-wrong-target`, `fixture-shape`, `forbidden-field`, `key-bound-misattributed`, `key-event-ignored`, `key-event-shape`, `log-time-claimed`, `nonce-invalid`, `nonce-reused`, `notice-missing`, `pending-counted`, `placeholder-unlabelled`, `possession-mismatch`, `predicate-type`, `profile-mismatch`, `provenance-shape`, `quorum-miscount`, `rendering-unlisted-line`, `report-digest`, `result-mismatch`, `root-not-anchored`, `signature-invalid`, `single-verdict`, `statement-digest`, `statement-shape`, `subject-mismatch`, `subject-name`, `time-in-statement`, `tsa-nonce-mismatch`; for §19: `content-on-wire`, `a2a-shape`, `mcp-tool-shape`, `witness-shape`.

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

**(a) Local-first (recommended first).** The creating tool or agent calls a local Traceweave tool when it writes a file. The local tool may be an MCP tool over stdio, a local A2A agent on loopback, or the command line. It does everything in §14 step 2 on the machine: digests, nonce, possession digests, optional catalogue and commitment. It signs with the **creator's** key and requests evidence over the raw signature bytes from two TSAs (each with a checked request nonce) and OpenTimestamps (§13). The trust meaning is exactly §1: this key signed a statement naming these bytes no later than T. Registering at creation time only makes T close to the moment of creation. It never proves the creation moment, and the bound is still an upper bound.

**(b) Hosted Traceweave witness over A2A.** A remote agent receives **only the SHA-256 of a creator's DSSE signature**, after (a) has signed. It authenticates the caller and signs a **witness statement** (predicate type `https://traceweave.org/predicate/witness/draft-1`, proposed). The statement says: *this digest was presented at `receivedAt` by the witness's clock, by the caller authenticated as {scheme, issuer, subject}, in request `requestMessageId`*. The witness attaches its own RFC 3161 token over its signature, so its time does not rest on its own clock. The result returns as an A2A artifact. The creator adds it to the bundle as one more time evidence (proposed type `traceweave-witness`, root kind `witness-service-key`). Its root is identified by the anchor of the witness key (§6.3), and the verifier's policy decides which independence group it belongs to. Its bound is per signature, like every other bound (§6.4).

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
| Hosted witness → creator | (b) | A `Task` with one artifact: the signed witness statement and its TSA evidence | — |

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

**Design choices.** The statement gets **no** creator or agent field in draft 1 (`authorship-claim` covers attempts). If the owner wants the generating tool recorded, add it later only as a claim (`claims.generator`), shown as claimed. By default, the creator key belongs to the person or organisation, and an agent uses it only through the local tool with the person's consent. MCP's "human in the loop" SHOULD applies.

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
- **SK.3** (A2A design): proposed addition: "Registration is local-first with the creator's key; a hosted witness, if any, receives only the SHA-256 of a DSSE signature and returns a signed witness statement as an A2A artifact. Design: `research/drafts/registration-record.md` §19." The non-author review stays required.
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

Run on 2026-11-23 on `roadmap-v2` (parent `58c25a9`), over this draft, lane 13 and the fixtures directory:

- `check_registration.py` (draft-2):
  - the Ed25519 (RFC 8032 tests 1 and 2) and PAE self-tests pass;
  - 30 positive fixtures give no code, and each of the 58 negative fixtures gives exactly its expected codes;
  - all 14 wrong-implementation cases are rejected;
  - all 41 codes appear in this document and have a negative fixture.
- `build_fixtures.py` rerun: the rebuilt files are byte-identical to the committed ones.
- `tools/validate.py`, `python -m unittest discover -s tests`, `tools/validate.py --links-all`, `tools/check_hygiene.py --messages` and `git diff --cached --check`: results in the commit message of this change.
- The MCP tool fixture still validates against MCP `schema.json` `$defs/Tool` (0 errors). The A2A fixtures are not validated against a published A2A schema, because none is committed upstream (§19.4).
- No new external URL was added in draft-2. The draft-1 and §19 URLs were checked when added: 28, then 14.
- **Not done:** no real time-stamp token, proof, log entry or cosignature was requested or verified, and no implementation exists.

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
