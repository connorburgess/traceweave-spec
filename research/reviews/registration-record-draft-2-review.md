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

## Draft-3 confirmation

Draft-3 (`5250eae`), confirmation pass of 2026-11-24. **Method:** the author's builder, checker and `realformat.py` on a scratch copy (`$TMPDIR/reg3/attack3.py`), openssl 4.1.0, and local test certificates. No service was contacted and the draft was not edited. The author's checker passes: 54 positives, 81 negatives, 25 wrong-implementation cases, 48 codes.

**Verdict: not confirmed.** The draft-2 items are fixed as written, but four new blocking defects remain (D1–D4): two in the key-event rules, and two in the real-format verification that REG.1 would certify.

### Draft-2 items, tested

- **B1: partly.** The direct hijack (`verification-result-rotation-hijack`) and two new variants hold. In a chain K→NEXT→CO with K compromised before the first rotation, CO is `untrusted`. With the successor NEXT compromised before NEXT→CO, CO is `untrusted`. Two further variants break it (D1, D2).
- **B2: resolved.** Events are sorted by proved time, ties by payload digest, and evaluated to a fixed point, so the result is order-independent by construction. With equal proved times, a successor's event is not authorized by a rotation at the same E. That is deterministic, and acceptable.
- **B3: resolved.** Every decision uses SHA-256 of the full key: `trustedKeys`, event target (subject digest, with `keyid` agreement), successor, signer, and the witness anchor. `keyid` remains only for lookup and display. Note: renderings show only the 16-hex keyid, so two keys with colliding hints render identically. Show at least 128 bits.
- **S1, S7, S11: resolved.**
- **S4: resolved.**
- **S8, S12: resolved.**
- **S13: resolved as a proposal.** Gate wording is assessed below.
- **S2: partly.** All five token checks are real: imprint and hash algorithm, request nonce and imprint, ESSCertID/ESSCertIDv2, a single critical timeStamping EKU, and the CMS signature with `messageDigest`. openssl agrees on the positive and on all four negatives: digest failure, imprint mismatch, unsuitable purpose, and ESS cert id not found. The chain step is not real path validation (D4).
- **S3: partly.** `revocationData` with `asOf` exists, but it is keyed by **root anchor**, and its entries name no certificate (`{revokedAt, reasonCode}`). One revoked TSA certificate therefore invalidates every TSA under the same CA, and an intermediate cannot be told from a leaf (D5).
- **S9: resolved for the listed vectors.** D1–D4 have none.
- **S10: partly.** The TSA anchor is computed from the pinned root, but the Bitcoin anchor pins only the first header (D3). Placeholders count only in `simulated: true` results (`_final`), but every rendering fixture is built from a simulated result with no marker (D6).
- **S5, S6: accepted** (below).
- **N1: resolved** (rounded up in `gtime` and accuracy).
- **N2: partly**, because of D3.
- **N3, N4: resolved.**

### Blocking

**D1: a retired or rotated-away key can still rotate, and its successor becomes trusted.** §8, "An event is authorized if it is signed by its target key".
- Owner retires K, proved 2026-11-26. A thief who later obtains K rotates K→THIEF, proved 2027-03-01. Both events are `applied`, and the thief's 2027-03-05 registration is **`trusted`**.
- The same happens with retirement and rotation at equal proved times.
- Retired keys are exactly the ones least likely to be guarded.
- **Change:** after an applied, undisputed `retired` or `rotated` event for K, later events signed by K other than `compromised` are `ignored-superseded`. Add the fixture.

**D2: a later holder of an old key can erase the honest successor chain, with no time limit.** §8, "Two applied rotations of one key to different successors are both disputed".
- Owner rotates K→NEXT, proved 2026-11-26. Eighteen months later, whoever obtained K rotates K→THIEF. Both rotations become `disputed`, and the owner's 2026-12-10 NEXT registration drops to `untrusted`.
- The compromise look-back clamp (§8) does not apply to this rule. Under RD18, the owner cannot repair it through keys.
- **Change:** apply D1's supersession rule, so a second rotation of an already-rotated key is ignored. Dispute conflicting rotations only when both fall within one compromise window, as the thief-first hijack does.

**D3: the OpenTimestamps header source pins only the first header, and difficulty is not enforced.** §6.2 ("a header file or node whose first header's SHA-256 is the anchor"); `header_ok` compares each header's hash with the target from that header's **own** `nBits`.
- I mined twelve headers at `nBits` 0x207fffff on top of the same pinned first header, with the shipped proof's commitment at height 4 and time 2001-01-01.
- `header_ok` returns True and the Merkle root matches, so the bound becomes 2001-01-01 plus 2 h for the real `opentimestamps-proof.ots`.
- Against a mainnet genesis anchor, the same attack needs only easy-difficulty headers.
- **Change:**
  - The policy pins a **checkpoint**, the hash of a header at a height ≥ the attested height plus `minConfirmations`. The checker links back from the checkpoint to the attested header, so a fork cannot contain the checkpoint without the real work.
  - Header files come from the verifier's own node, never from a bundle.
  - Add a `neg-real-ots-forked-headers` vector.

**D4: the RFC 3161 chain check is not path validation.** §6.2 step 6 ("the chain verifies to the pinned root"); `chain_to_root` checks signatures only. I issued two TSA certificates under a local root:
- **One signed by an end-entity certificate** (`CA:FALSE`): openssl says "invalid CA certificate", but `check_token` and `chain_to_root` accept it.
- **One under an intermediate that expired in 2021:** openssl says "certificate has expired", but `realformat.py` accepts it.

With a commercial CA root as anchor, anyone holding any end-entity certificate under it could mint a TSA certificate and backdate tokens.
- **Change:** §6.2 step 6 requires RFC 5280 path validation at `genTime`: CA basic constraints and `keyCertSign` on every issuer, validity of every certificate, and critical extensions understood. `realformat.py` enforces it. Add both vectors.

### Should-fix and notes

- **D5 (S3):** revocation entries must name the certificate (issuer and serial, or SHA-256), and apply to the TSA certificate or the intermediate they name.
- **D6 (S10):** a rendering made from a `simulated: true` result is presented as real. Either refuse to render simulated results, or require a template line such as "Simulated: time evidence is placeholder only".
- **D7:** `realformat.py` rejects valid tokens: ECDSA (documented), RSA-PSS, SHA-384/512 signatures, and ESSCertIDv2 with a non-SHA-256 hash, which it compares with SHA-1. That is fine for REG.1, but REG.3 against real TSAs may meet these. State the supported algorithms in §6.2.
- **D8:** TSTInfo `version` is parsed but not checked, and duplicate signed attributes are not rejected.
- **D9 (S6):** the renewal hashes only the old token's bytes. RFC 3161 §4 item 3 renews trust "if authentic copies of old CRLs are available", and RFC 4998 covers the verification data too. Either include the chain and revocation data in the renewed bytes, or state that the renewal relies on the policy's `revocationData`.

### The author's choices

- **S5, removing `cosigned-checkpoint`: acceptable for REG.1.** **Cost:** no log-based time source, which is fine while logs are out of scope (RD3). Rekor v2 stays without a bound.
- **S6, renewal as a token over the earlier token, with hash-tree renewal out of scope: acceptable for REG.1.** **Costs:**
  - a SHA-256 weakness ends every bound; re-registering starts a new, later bound, so continuity is lost;
  - renewal does not rescue `keyCompromise` revocations;
  - D9 above.
- **RD18, an honest owner's rotation after a compromise report is disputed: acceptable**, given the pre-listed recovery-key option. **Costs:**
  - continuity rests on out-of-band links or per-verifier recovery keys;
  - with D2 unfixed, any later leak of an old key erases continuity too. That is why D2 is blocking.

### Proposed ROADMAP text (§15)

- **M4 row, M4.3 (amended), M4.5 (replaced), M4.6 (amended) and REG.5:** verifiable as written.
- **REG.1:** verifiable, but:
  - it counts "four TSA and one proof negatives", while the fixtures have two OpenTimestamps negatives (`neg-real-ots-other-chain`, `neg-real-ots-wrong-target`);
  - as written it passes with D3 and D4 present. Add the forked-header and bad-chain vectors.
- **REG.2:** "byte-identical verification results" needs a canonical serialization for results (RFC 8785, as for reports). State it.
- **REG.3:** "k/k" has no k; name the counts. A "revoked certificate" cannot be produced on demand at a real TSA, so test that direction with the local test TSA. "Pinned header source" must mean the checkpoint pin of D3.
- **REG.4:** verifiable as a process gate (a named non-author); add "no rendering from a simulated result" (D6).

## Draft-4 confirmation

Reviewed commit dba683b, 2026-11-24. Verdict: **not confirmed**, with one blocking item (E1). D1–D9 and the REG.1–REG.4 text are resolved. E1 is narrow, and the enumeration already detects it once its time steps are shorter than the look-back. All tests ran on a scratch copy outside the repository; no external service was contacted.

### D1–D4, retested

- **D1, D2: hold.** Hand-built variants, all as the draft predicts:
  - S retires K, then K rotates to A: ignored-superseded.
  - An honest rotation and a thief's rotation at the same E: both disputed, so neither successor is trusted.
  - Retirement, then a thief's compromise report within the window, then a thief's rotation: the rotation is ignored, and the retirement is disputed but still supersedes K.
  - S→S2, then the stolen S rotates S→A 18 months later: ignored, and S2 stays trusted.
  - A thief's report exactly 30 days after K→S disputes the rotation; at 31 days it does not.
- **D3: holds, including forks that start below the checkpoint.** Headers were re-mined with the fixture's `nBits`:
  - forked at height 3 and re-mined through the checkpoint height: rejected, because the checkpoint hash does not match;
  - forked at 3 with the real checkpoint header kept: rejected, because linkage breaks;
  - attested header 4 real, fork starting at 6: rejected.
  - **A header file kept real up to the checkpoint and forged above it** passes `header_ok` and `linked_to_checkpoint` for an attested height above the checkpoint. Only `cp.height − height < minConfirmations` stops it, and `minConfirmations` is never validated, so 0 or a negative value admits the forgery. Should-fix: require `height ≤ checkpoint.height − minConfirmations` with `minConfirmations ≥ 1`, and validate it and the checkpoint shape in the policy check.
- **D4: holds.** `validate_path` agrees with `openssl ts -verify` (OpenSSL 4.1.0) on every token from a local scratch CA:
  - the two draft-3 cases (non-CA intermediate; expired intermediate);
  - an intermediate with `CA:TRUE` but no `keyCertSign` (openssl: "invalid CA cert");
  - an unknown critical extension on the intermediate (openssl: "unhandled critical extension");
  - two intermediates under `pathlen:0` (openssl: "path length constraint exceeded").
  - The control case, a TSA certificate issued directly by the root, passes both.
  - openssl refused to issue a token from a TSA certificate whose `keyUsage` lacks `digitalSignature`, so the leaf keyUsage check has no openssl cross-check.
  - Note: the path builder takes the first certificate with a matching subject and does not backtrack. The SignedData `certificates` field is unsigned, so anyone carrying the bundle can put a decoy certificate first and turn a valid token into `path-invalid`. That is denial of service only, no worse than deleting the token, but RFC 5280 path building should try every candidate.

### Blocking

**E1. A compromise report signed by a successor can dispute the rotation that authorizes it, and the evaluation never converges. The result then depends on how many unrelated events are in the input.**
- **The cycle.** K→S is applied at T. S signs `compromised` for K at T+10 d with claimed start T−5 d.
  - Pass 1: the report is authorized, because K→S is not yet disputed. Its window, starting at T−5 d, disputes K→S.
  - Pass 2: K→S is disputed, so the report is unauthorized and nothing is disputed.
  - Pass 3 repeats pass 1, and so on.
  - The loop stops after `len(events) + 2` passes, so the outcome is set by the parity of the event count.
- **Measured.**
  - The two events alone: K→S applied, report ignored, S trusted.
  - Add one unauthorized event (A signs `retired` for K): K→S disputed, report applied, S `untrusted`, and K disputed before T.
  - Add two such events: S trusted again.
  - Reversing the input keeps the same result, so I1 does not catch this. But anyone can add an unauthorized event file, so the "attacker events change nothing" claim (I2) and the B2 determinism claim both fail.
  - The same happens one level down: S2 signs a compromise of S within 30 days after S→S2. It also happens when the thief's A reports K compromised after the thief's own K→A.
- **Why the enumeration misses it.**
  - Every "later" step is 40 days, longer than the 30-day look-back. A step of 0 is never strictly later, so a successor report never lands inside (0, 30 d] after its own authorizing rotation.
  - With steps of ±20 days, and a claimed start 30 days before E, the author's own invariants report **558 violating sequences at length 3**: 540 under I2 and 18 under I6.
  - Every one of them contains a successor-signed or attacker-signed compromise report.
- **This is also the natural honest flow.** The owner rotates because K leaked, then reports the compromise with S (RD17).
- **Change.**
  1. Define the rule so that it is monotone. For example: a compromise report's window never disputes the rotation chain that authorizes its own signer. Or: decide authorization for compromise reports before computing windows, without fixed-point feedback.
  2. Make a loop that has not converged after its bound an error, not a result.
  3. Add the cycle as a fixture.
  4. Widen the enumeration so that steps are shorter than the look-back and claimed starts reach before the earlier event (see the enumeration section).

### The enumeration (question 2)

- **Same code path, no drift in the core.** It imports `check_registration` and calls its `evaluate_events` and `signer_trust`.
- **What it bypasses.** It skips `load_events`: no signature, subject or `keyid` checks, and no `E = None` path. It also skips signature bounds: every probe has `quorum == anyRoot`, and none has `None`.
- **Mutation check.** Run here: 8,289 and 5,184, as stated. Length 3: 0 violations. Length 4: 1,727,604 sequences, 0 violations, 99 s.
- **What length 4 with this alphabet cannot reach, tested by hand:**
  - A successor-signed report inside the window: E1.
  - Overlapping compromises of K (starts −10 d and +5 d; E +20 d and +35 d): trusted below −10 d, disputed from −10 d, untrusted from +20 d. Correct.
  - A three-key chain with a mid-chain compromise of S reported by a copy of S: S→S2 disputed, S2 untrusted; S trusted below the start, disputed from it. Correct. Reported by S2: E1.
  - A thief rotates first, the owner reports, and a recovery key R is in `trustedKeys`: A and S untrusted, R trusted. Correct, but R is trusted for every bound, including before it was listed (see the look-back section).
  - Events and signatures with no quorum: an event with no proved time is ignored; a signature with no quorum bound by a key an event touches is `disputed`. Both as the draft says.
- **Trust claims with no invariant:**
  - effect rule 3: `disputed` for start ≤ B < E, and trust unchanged below the start. Probes sit only at max E + 1 d and T0 − 400 d, so no window or boundary is probed;
  - effect rule 2, no quorum gives `disputed`;
  - "the result is identical whatever other events are supplied", beyond attacker-signed ones: no invariant adds unauthorized events, which is exactly E1;
  - authorization: a successor acts only through an undisputed rotation with a smaller E;
  - equal-time supersessions are both disputed;
  - "after the window the honest chain is final" against successor-signed reports: I6 removes only events by the `old` role.
- **Add** a step shorter than the look-back, several claimed starts, probes at start − 1 s, start, E − 1 s and E, a no-quorum probe, and an invariant that adding an unauthorized event changes nothing. The run time stays practical at length 3 with these parameters (2 s).

### Look-back and RD18 (question 3)

- **Coherent apart from E1.**
  - The look-back bounds two things symmetrically: how long a thief holding K can dispute the owner's rotation, and how long an owner has to dispute a thief's rotation.
  - After the window, the first supersession is final in-band.
- **What an attacker holding K can do inside the window (30 days after the owner's rotation):**
  - Dispute the honest rotation **permanently**. S never regains trust, and K cannot be rotated again, so the owner must recover out of band. The window is short, but the harm is permanent.
  - Make K's own signatures bounded in [E − 30 d, E) `disputed`.
  - Gain no trust for any key.
  - The draft states the first point (§8, owner rotates first), but the §13 threat row lists only "registrations inside the window can be disputed". Add that the successor chain is lost.
- **30 days.** It is a named policy parameter, `compromiseLookbackSeconds` (RD15), with 30 days stated as the fixture default.
  - The justification is a trade-off only. Nothing ties 30 days to an expected discovery time, so it is a placeholder for the owner to set.
  - The value is not validated: zero, negative or non-integer values are accepted. A negative value makes every compromise window start after its own report. Validate it as a non-negative integer.
- **Recovery keys (RD18).** No policy field holds them. `POLICY_KEYS` is fixed, and RD17's "policy may add keys" has no field either.
  - The only working form is an extra `trustedKeys` entry. That key is trusted for every bound, including signatures made before it was listed, and is not tied to K.
  - State that this is the mechanism, or add a field that names the key and the key it may recover.

### D5–D9 and gate text (question 4)

- **D5:** resolved. Revocations name a certificate by SHA-256 and apply only to paths through it; placeholder evidence uses its signer's hash.
- **D6:** resolved (marker line; REG.4 refusal).
- **D7:** stated, but the code does not match the text. §6.2 says ECDSA and others are "rejected as unsupported". The ECDSA token here instead raises `tsa-signature-invalid`, which reads as a forged signature. Should-fix: report `unsupported`.
- **D8:** resolved. `version ≠ 1` and duplicate signed attributes are rejected.
- **D9:** resolved as text. The renewal relies on retained revocation data, and the stronger form is left to RD11.
- **REG.1–REG.4:** the draft-3 items are fixed: the counts, the D3 and D4 vectors, RFC 8785 bytes, k = 3, the local test TSA for revocation, the checkpoint pin, and the refusal of simulated results. But REG.1's "`enumerate_key_events.py` reports 0 violations up to length 4" passes with E1 present. Tie it to the widened parameters above.

## Draft-5 confirmation

Reviewed commit aab6717, 2026-11-24. Verdict: **confirmed, with changes.** Nothing blocks. Two should-fix items remain (F1, F2), plus notes. All tests ran on a scratch copy outside the repository; no external service was contacted.

### E1 and its variants (question 1)

- **The count and order of other events no longer change anything.**
  - Setup: the E1 pair (K→S at T; S reports K compromised at T+10 d from T−5 d), plus every subset of six extra events, each subset in four shuffled orders: 256 runs.
  - The six extra events:
    - unauthorized (J retires K);
    - superseded (K rotates to A later);
    - no proved time;
    - a bad signature;
    - an unauthorized report reaching 50 days back;
    - the same rotation statement signed by A instead of K.
  - Result: the E1 events' outcomes, and every key's trust at 18 probe times (including no quorum), match the pair alone in all 256 runs.
- **Through real bundles** (`load_event_bundles`):
  - E1 as signed bundles: both events applied, S trusted.
  - The rotation file supplied twice: one event.
  - The rotation statement signed by a second key: two events. The second is `ignored-unauthorized`.
- **Thief and owner scenarios.** Every outcome below is defensible: each is the most a verifier can conclude without knowing who held K.

| Case | Outcome | Defensible? |
| --- | --- | --- |
| Thief K→S′ at T; owner reports with K at T+5 d from T−3 d | K→S′ disputed; S′ untrusted | Yes |
| Same, and the thief also reports with S′ (from T−100 d) | K→S′ still disputed. The thief's report only marks K's own signatures from T−24 d as `disputed`, which the thief could already do with K | Yes |
| Thief reports with S′ first (T+1 d), then the owner reports with K | K→S′ disputed. The thief's report cannot pre-empt the owner's, because reports are never superseded or disputed | Yes |
| Thief K→S′; owner reports at T+40 d (outside the window), or with a claimed start after T | K→S′ applied; S′ trusted | Yes, it is the stated RD15 trade-off. The owner must recover with a recovery key or out of band |
| Thief K→S′ at T; owner rotates K→S at T+2 d and reports | Owner's rotation ignored as superseded; K→S′ disputed; neither successor trusted | Yes (RD18) |
| Owner K→S at T; thief reports with K at T+10 d | K→S disputed permanently | Yes, and now stated in the threat row |
| Same at T+40 d | S trusted; the chain is final | Yes |
| Owner K→S, owner reports with S at T+10 d, thief reports with K at T+12 d | K→S disputed | Yes. The exemption protects S only from its own report |
| Owner K→S at T; thief rotates K→S′ at T+3 d and reports with S′ | Thief's rotation ignored as superseded; thief's report unauthorized; S trusted | Yes |
| Owner and thief rotate at the same T; each reports with its own successor | Both rotations disputed; neither successor trusted | Yes |

- **The exemption cannot be exploited.**
  - A rotation of K that grants standing is always signed by K: a rotation of K signed by its successor arrives after K was superseded, so it is ignored.
  - So whoever gains standing through a rotation held K when it was made. Every report that successor can file, the holder of K could file with K directly.
  - The exemption covers only the report's own signer. A K-signed report, the owner's tool against a thief who rotated first, has no exemption and disputes the thief's rotation.

### Two-pass soundness (question 2)

- **None.** No state makes pass-1 standing need to depend on a dispute.
  - Standing granted through a disputed rotation allows only compromise reports about the old key. Its other events are superseded, because the appointing rotation itself superseded the key.
  - A compromise report only restricts. It disputes other applied supersessions of the key (in practice, only ones at the same E, which the equal-time rule already disputes), and it marks the key's own signatures in its window as `disputed`.
  - As shown above, the holder of the old key had the same power without the rotation.
- **One cosmetic edge case.** Two different rotation statements K→S, for example re-serialized or signed with a random nonce, can be proved at the same E.
  - They are not a conflict, because both name the same successor.
  - S's report then disputes the twin that is not its own appointment. S stays trusted through the other twin, but the result lists one rotation as `disputed`.
  - Treat same-target, same-successor rotations as one appointment when applying the exemption.

### Enumeration and mutation check (question 3)

- **Rerun as shipped.** Mutation counts 345 / 430 / 40. Length 1–3: 1,010,100 sequences. Length 4: 200,000 sampled. 0 violations; loading sample 0 mismatches of 300; 57 s.
- **Boundary variant on a scratch copy.** Steps of ±29, ±30, ±31 days and 0; claimed starts 29, 30 and 31 days back (140 symbols); length-4 seeds starting at 777000; loading seed 99.
  - Length 1–3: 2,763,740 sequences, exhaustive. Length 4: 200,000 sampled.
  - 0 violations, and 0 loading mismatches. Mutation counts 693 / 896 / 140. 128 s.
- The invariants now cover every gap named in the draft-4 pass:
  - windows and their boundaries (I8);
  - no quorum (I9);
  - added rejected events (I10);
  - who may sign (I11);
  - equal times (I12);
  - late successor-signed reports (I6).

### Earlier items and new ones (question 4)

- **Fixed and retested:**
  - `minConfirmations ≥ 1` and the checkpoint's shape are validated, and the attested height must be at most the checkpoint height minus `minConfirmations`.
  - The look-back must be a non-negative integer.
  - ECDSA gives `unsupported` (retested with the scratch ECDSA token).
  - Path building backtracks.
    - A valid chain with a same-subject decoy listed first passes `validate_path`. Every chain tested in the draft-4 pass still gets the same verdict.
    - openssl 4.1.0 fails that decoy-first chain ("certificate signature failure") when the certificates carry no key identifiers, and passes it with the decoy last. The checker's answer is the RFC 5280 one. openssl is not an oracle for decoy chains without key identifiers; real TSA chains carry them.
  - `recoveryKeys` exists, is validated, and is trusted only from `notBefore`.
  - The threat row states that the successor chain is lost permanently.
- **F1 (should-fix): a key event is read from its first signature only, which contradicts "one statement signed by two keys is two events".**
  - `load_event_bundles` takes `keyDigests[0]` and `sigs[0]`. Envelope signatures are not signed, so anyone carrying a K-signed event file can put their own signature first.
  - Reproduced: the file then loads as one event signed by A, `ignored-unauthorized`. K's valid signature is never considered, and the S report that depended on it becomes unauthorized too.
  - That is only as bad as deleting the file. Supplied next to the original, the copy loads as a separate event and changes nothing. It is still a silent mask.
  - Either require exactly one signature on a key event (`key-event-shape`), or load each valid signature as its own event.
- **Event identity (payload plus signature):**
  - Only a key holder can multiply events, because Ed25519 is checked as non-malleable (S < L, canonical encodings). The holder can make any number of distinct signatures, but duplicates add nothing: later ones are ignored as superseded, and equal-time ones with the same successor are not a conflict (see the cosmetic edge case).
  - Masking is possible only through F1.
  - Merging copies of one signed statement to its earliest proved time is sound, because each copy's E is a valid upper bound.
- **F2 (should-fix, text): RD17 contradicts §8.** RD17 still says "the key and verified, **undisputed** successors", while §8 pass 1 now grants standing through a rotation "disputed or not". It also says "policy may add keys", but there is no policy field for that. Align RD17 with §8, and drop the policy option or name its field.
- **Note on recovery keys.** A recovery key adds a trust root; it does not end K's chain. If a thief's K→A is never disputed, A and the recovery key are both trusted. That is acceptable, but say so in RD18.

### Decisions the owner must take before implementation

1. **External services:**
   - whether any may be contacted at all, including a single REG.3 test submission (§17 lists what each one sees);
   - which two unrelated RFC 3161 TSAs, after reading their terms, and whether any paid or qualified TSA is used (RD2);
   - whether OpenTimestamps is used. Its commitment lands in Bitcoin permanently, and it needs the verifier's own Bitcoin node or header source (RD1, RD21). Without it, option (b) leaves one revocation able to drop the quorum;
   - the signature algorithms to support, from what the chosen TSAs issue (RD22).
2. **Policy defaults:**
   - quorum (2 of 3 proposed, RD5);
   - the compromise look-back (RD15; 30 days is a placeholder with no derivation);
   - `minConfirmations` and how the checkpoint is refreshed (6 in the fixtures);
   - the OpenTimestamps margin (7,200 s, RD6);
   - the independence groups for the chosen TSAs.
3. **Recovery keys (RD18):** whether the tool offers to generate and list one at registration; how verifiers learn of it; and its default `notBefore`.
4. **Who may assert key events (RD17)**, after F2.
5. **Already listed in §17 and still open:**
   - public logs and any project-run log, witness or signer (RD3, SK.5);
   - the default identity mode, I0 or I0′, and whether I2 is offered (RD4);
   - publishing the predicate identifiers under `traceweave.org` (RD10);
   - adopting the §15 ROADMAP text.
