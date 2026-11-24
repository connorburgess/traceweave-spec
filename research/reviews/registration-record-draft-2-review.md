# Review: registration record, draft-2 (confirmation)

Status: non-author confirmation review, 2026-11-24, of [registration-record.md](../drafts/registration-record.md) draft-2 (`c4848c1`, with §19 from `1dd9c1f`) at `roadmap-v2` `a6851dd`, its [fixtures](../drafts/registration-fixtures/README.md), and the [C2PA mapping draft](../drafts/c2pa-mapping.md) where they meet.
- **Read first:** the draft-1 review, [registration-record-review.md](registration-record-review.md) (`5c3d9c5`).
- **Method:** scratch code in `$TMPDIR/reg2` (`attack.py`), run against the author's builder and checker on a scratch copy. No service was contacted.
- **Primary sources** (fetched read-only for the draft-1 review and re-read): RFC 3161, RFC 5816, RFC 8032, RFC 4998, the DSSE `protocol.md`, the in-toto Statement v1 spec, and the OpenTimestamps client README at `f3a9e92e`.

**Verdict: confirm with changes.** The draft-1 findings are resolved in substance (§1), not just reworded. Code, fixtures and the checker's wrong-implementation self-test back them, and `check_registration.py` reports 30 positives, 58 negatives, 14 wrong-implementation cases and 41 codes, all as expected. Three blocking defects remain, all in key handling (B1–B3), and must be fixed before REG.1.

## 1. Draft-1 findings: verdicts

| Draft-1 finding | Draft-2 change | Verdict |
| --- | --- | --- |
| F1 bounds per statement | Per-signature bounds (§6.4); `bundle-cosigned`, `neg-key-bound-misattributed*` | **Resolved** |
| F2 roots by label | `root.anchorSha256`, policy groups (§6.3); `neg-quorum-same-anchor`, `neg-root-not-anchored` | **Resolved in the format.** But the placeholders carry the anchor and certificate dates written by the producer, and the checker trusts them, so "the verifier computes the anchor" (§2) is untested (S10) |
| F3 key events, hostile compromise | §8 events, look-back clamp, `disputed` | **Partly resolved.** The early-claim clamp works (`verification-result-compromise-early`). Rotation by a stolen key is not handled (B1), event evaluation depends on input order (B2), and trust can rest on one source (S1) |
| F4 rendering rules, "permission" | Allow-list of templates (§11); sentence 2 now ends "…or that its use is permitted" | **Resolved**: `neg-authorship-claim-0`…`-4`, `neg-rendering-unlisted-line` |
| A1 target bytes | Raw decoded signature bytes (§6.1), `neg-evidence-target-base64` | **Resolved** |
| A2 bound for `after-proved-bound` | Earliest `notAfterAnyRoot`, reported as `comparedWith` (§10 step 11) | **Resolved**, with S11 |
| A3 accuracy contradiction | Policy `accuracySeconds`, outcome `unsupported` (`verification-result-no-accuracy`) | **Resolved** |
| A4 Ed25519 strictness | §10.1 rule set, self-tested against two lenient verifiers | **Resolved** |
| A5–A8 field names, closed key lists, key lookup, opening bytes | §6.2, §4.6, §10 step 2, §4.4 | **Resolved** |
| W3, W4, W6b, W8, W10, W12 | Fixtures and self-test cases | **Resolved** (W10 only for non-rotation events; see B1) |
| W9 certificate validity at `genTime` | `signerCertificate` placeholder fields, `neg-cert-validity-ignored` | **Partly resolved:** only the producer-written dates are checked; chain, key usage and the signing-certificate attribute are not (S2) |
| RFC 3161 revocation, request nonce, policy OID | §6.2 `revoked`, `tsa-nonce-mismatch`, `wrong-policy` | **Resolved in text.** `wrong-policy` has no fixture, and only "no reasonCode" is exercised (S9) |
| OpenTimestamps header source; RD6 rationale | §6.2, RD6 | **Resolved**; the honest-majority assumption is now stated |
| Lane 13 RFC 3161 §4.1 claim; "offline" | Lane 13 T1 row and Decision | **Resolved** |
| Retroactive loss of a source; theft window; linkage; low entropy; renewal triggers | §12, §7 (I0′), §5 | **Resolved**, except that the renewal object is undefined (S6) |

## 2. Blocking

**B1: a stolen key can rotate itself to the thief, and a later compromise event does not undo it.** §8, "Who can assert an event" and "Effect on a signature". Reproduced with the builder's own `key_event` and `result_for`:
- The thief, holding key K, publishes `rotated` from K to the thief's own key, proved 2026-11-26.
- The thief signs a registration under the new key, bounded 2026-11-27.
- The owner then publishes `compromised` for K with `compromisedNotBefore` 2026-11-25T12:00, proved 2026-11-28. Both events are `applied`.
- **Result: the thief's signature is `trusted`, in both event orders.** A compromise affects only signatures by K, and a successor inherits trust from a rotation without regard to whether that rotation fell inside a compromise window.

**Change:**
- An applied `compromised` event for K, with `start` computed as in §8, makes every rotation (and retirement) signed by K with proved time E ≥ `start` **`disputed`**. A successor gains no trust from a disputed rotation.
- Two applied rotations of one key to different successors are both `disputed`.
- Add `verification-result-rotation-hijack` and `verification-result-rotation-conflict`.

**B2: event outcomes depend on the order in which events are supplied.** §8 ("a successor named by an earlier event that was itself applied") and §10 step 3.
- The checker processes events in list order and keeps one successor per key.
- An event signed by the successor about K (I used `retired`) is `applied` when listed after the rotation, and `ignored-unauthorized` when listed before it. I reproduced this.
- So two conforming verifiers given the same events in different orders disagree, which breaks REG.2. "Earlier" is undefined (list position or proved time).

**Change:**
- Define evaluation as order-independent: sort events by proved time E (ties by SHA-256 of the event payload), and evaluate authorization against events with a smaller E, repeating until nothing changes.
- State that "earlier" means a smaller E.
- Add a fixture that supplies the same events in two orders and expects identical results.

**B3: trust and key-event targets are keyed on a 64-bit hint.** §7 (`trustedKeyids`), §8 (event predicate `keyid`), §10 steps 2–4.
- `keyid` is the first 16 hex digits of SHA-256(public key). The draft itself says it is "a lookup hint, not identity", and DSSE calls KEYID an "unauthenticated hint".
- Yet policy trust and every key event are matched on it, and `check_key_event_statement` never reads the event's subject digest.
- A key whose keyid equals a trusted one is a 2⁶⁴ second-preimage search, which is far below the design's other 128-bit margins. With it, an attacker gets `trusted`, or can issue events that target the victim's key.

**Change:**
- The policy lists trusted keys by SHA-256 of the raw 32-byte public key (or the key itself).
- A key event names its target by subject digest = SHA-256(raw public key), and must agree with `keyid`; otherwise `key-event-shape`.
- Successors are matched by full key.
- Keep `keyid` only for lookup.
- Add `neg-key-event-subject-mismatch`.

## 3. Should-fix

- **S1** (§8, "where B is the signature's quorum bound (or its single-source bound when there is no quorum)"). Trust relative to a compromise or rotation is decided on one source's time when there is no quorum. That is exactly the bound §6.4 says one compromised source can move. A thief holding the stolen key plus one backdating source reaches `trusted`.
  - **Change:** with no quorum bound, a signature affected by any applied event is `disputed`, never `trusted`.
- **S2** (§6.2 `rfc3161`; the departures from the primary texts). The token-structure checks are absent from the text and the checker. Add each with an outcome:
  - `messageImprint.hashAlgorithm` is `id-sha256` and `hashedMessage` equals `target.sha256` (RFC 3161 §2.4.1–§2.4.2);
  - the TSA certificate carries exactly one extended-key-usage extension, `id-kp-timeStamping`, marked critical (RFC 3161 §2.3);
  - the token's SigningCertificate attribute (ESSCertID or ESSCertIDv2) identifies the signer certificate (RFC 5816 §2, "MUST be included");
  - no signature other than the TSA's;
  - the chain validates to the anchor at `genTime`.
- **S3** (§6.2 revocation; §12 "Service shutdown": "verifiable offline from retained chains and headers"; §13).
  - `tsaRevocations` is a policy input, and a `keyCompromise` revocation invalidates past tokens (RFC 3161 §4 item 2). So an offline result is only as current as the revocation data it used.
  - **Change:** the result records the source and date of the revocation data used for each anchor, and §12 and §13 say that offline verification holds "as of" that date.
- **S4** (§19.2 (b), §6.3: "the verifier's policy decides which independence group it belongs to"). The witness's time "does not rest on its own clock" but on its RFC 3161 token. If that token comes from TSA A, the witness evidence and a direct TSA A token both rest on TSA A, and q = 2 can be met by one operator.
  - **Change:** a `traceweave-witness` evidence belongs to the independence group of the TSA anchor its bound comes from, as well as the witness key's own.
  - Add a fixture where the witness and a direct token share TSA A and the result is `below-quorum`.
- **S5** (§6.2 `cosigned-checkpoint`: fields `checkpoint: {cosignatureTime}` only). A cosignature bounds a checkpoint, not our digest. Without an inclusion proof of the signature digest in the tree at that checkpoint, the evidence shows nothing about the registration.
  - **Change:** require the inclusion proof and checkpoint body, or remove the type from draft-2.
- **S6** (§12 algorithm ageing, §14 step 5, RD11: "re-time-stamp the bundle"). No renewal object, target or rule exists. Evidence over anything but a signature is `evidence-wrong-target` (§6.1), so a renewed bundle would fail verification.
  - **Change:** define a renewal evidence whose target is the SHA-256 of the earlier evidence's token bytes, with chain rules following RFC 4998 (timestamp renewal; hash-tree renewal over the original data, §1.2). Otherwise state that renewal is outside draft-2 and drop the claim from §12.
- **S7** (§10 step 1; checker `b64d` uses `validate=True`). DSSE: "Either standard or URL-safe base64 encodings are allowed … verifiers **MUST** accept either". The checker rejects URL-safe encoding.
  - **Change:** state the rule, and add a URL-safe envelope as a positive fixture.
- **S8 (claims discipline).**
  - §11 has no rule against **ordering registrations**. Each bound is an upper bound, so an earlier bound on A than on B does not show that A was registered first. Someone may register first and obtain evidence later. Add a fixed sentence and a checker rule: "Comparing the times of two registrations does not show which was made first."
  - §1 ("lets a creator later show"), §14 ("What a creator would do") and the §15 M4 wording ("A creator can show…") presuppose creation. Use "registrant".
  - §19.2 (a), "Registering at creation time only makes T close to the moment of creation", implies a property the record cannot show. Write: "can make T close to creation if the registrant registers promptly; the record does not show that they did."
  - The witness template, "…at <T> by the witness's clock", contradicts §19.2, which bases the witness's time on its TSA token. Name the source.
- **S9 (missing vectors; testability).** The fixtures cannot exercise:
  - **Per-outcome and per-route gaps:** a `wrong-policy` outcome; revocation with `keyCompromise` and with a retaining reasonCode (only "absent" is exercised); a verification result that applies a rotation (the rotation fixture is never used in a result); B1–B3; key events in two orders; a key-event subject mismatch; S1 (no quorum plus an event); S4 (witness and TSA on one anchor); a URL-safe envelope; two signatures under one key; an out-of-range `signatureIndex`; and an evidence stripped from a bundle (which may only lower bounds).
  - **Real formats:** there is not one real-format token. A local test TSA, for example `openssl ts` with a self-made CA (no external service), and a synthetic OpenTimestamps proof against a local header file would let REG.1 test S2, the anchor computation (S10) and the OpenTimestamps path without waiting for REG.3.
- **S10** (§2 "a SHA-256 the verifier computes"; fixtures). In every fixture the anchor digest and certificate validity are fields the producer writes, and the checker accepts them as given. State in the README and in REG.1 that these properties are untested until real-format vectors exist (S9).
- **S11** (§10 step 11). `after-proved-bound` compares against the earliest bound "over all valid signatures, whoever signed". An untrusted co-signer with a single early source then changes the honest registrant's claim outcome.
  - **Change:** compare against trusted signatures only, or report the outcome per signature.
- **S12 (C2PA).**
  - §15 says "One TSA evidence maps" into a C2PA manifest. But C2PA's v2 time-stamp countersigns the **C2PA claim signature** (`sigTst2`; lane 13 T6), not the DSSE signature. A token over the DSSE signature cannot be reused there, and a C2PA export needs its own token.
  - [c2pa-mapping.md](../drafts/c2pa-mapping.md) still marks the row `conflicting`.
  - **Change:** correct §15 to "a C2PA export obtains its own RFC 3161 token over the claim signature; registration evidence does not map", and keep the C2PA row as is.
- **S13 (roadmap gates as written).** ROADMAP.md M4.3–M4.6 are unchanged.
  - M4.5 still asks for a decision on "the optional timestamp adapter", while the draft says time evidence "is not optional" (§15).
  - REG.1–REG.5 exist only as proposals, and M4.6 requires its report in `docs/reviews/`.
  - So no M4 gate currently tests a registration. Until the owner adopts the §15 wording, M4 cannot be evidenced from this draft. When adopted, REG.1 should name the S9 vectors.

## 4. Notes

- **N1** (§6.2 bound): `genTime` may carry fractional seconds, and accuracy has milliseconds and microseconds (RFC 3161 §2.4.2). State that `notAfter` is rounded **up** to the whole second.
- **N2** (§6.2 OpenTimestamps):
  - `blockTime` must be read from the trusted header at the attested height, never from the evidence. The fixture field is producer-written.
  - State a minimum confirmation depth, or that the header must be on the verifier's best chain.
- **N3:** time evidences sit outside the signature, so anyone handling a bundle can remove one. That only lowers bounds; say so in §12.
- **N4:** the in-toto Statement v1 rules are met: subject `digest` set, "matched purely by digest", and a local `name` rule. DSSE PAE and payload type are as specified. Ed25519 follows RFC 8032 §5.1.7, with stricter rejections stated (§10.1). That is a deliberate, documented departure, and it is the right one for REG.2.

## 5. Adversarial summary (question 2)

- **Back-dating:** one source can move only `notAfterAnyRoot`. The quorum needs two independent groups, except through B3 (a forged trusted key), S1 (a single source deciding trust) and S4 (a witness sharing a TSA).
- **Forward-dating:** an upper bound cannot be made earlier by delay. Stripping evidence makes a record look later (N3).
- **A later-compromised key:** the holder can sign new statements bounded after the theft. With B1 the holder can also take over the key's succession, and with S1 can reach `trusted` using one backdating source.
- **Replay onto another statement:** closed. The target is the raw signature, Ed25519 is deterministic and canonical-S, a co-signature inherits nothing, and the request nonce catches replay at request time. S2's `messageImprint` check is what makes this hold for real tokens.
- **Canonical bytes:** the statement is verified over its exact payload bytes. Base64 acceptance (S7) and event ordering (B2) are the remaining ambiguities between implementations.
- **One time source unavailable or disagreeing:** with three sources and q = 2, one loss leaves a quorum (`verification-result-revoked`). Disagreement is resolved by taking the q-th smallest bound. With two losses, the result is `below-quorum` and the rendering says "according to one time source only". Under S1, that single source must not decide trust.
- **Algorithm agility:** SHA-256 and Ed25519 are fixed per version string, which is acceptable. Renewal is undefined (S6).
