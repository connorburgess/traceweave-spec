# Review: registration record draft, fixtures and lane 13

> Path note: the specification and fixtures reviewed here were promoted on 2026-11-25 to [spec/registration-record.md](../../spec/registration-record.md) and [test-vectors/registration/](../../test-vectors/registration/README.md); link targets below point to the promoted locations. See the [promotion map](../promotion-map.md).

Status: non-author review, 2026-11-23, of [registration-record.md](../../spec/registration-record.md), [registration-fixtures/](../../test-vectors/registration/README.md) and [lane 13](../lanes/13-timestamp-evidence-review.md) at `roadmap-v2` `3d31974` and `7271715` (the A2A section was not available and is not reviewed). Scratch code is in `$TMPDIR/reg` (`clean.py`, `variants.py`); primary sources were fetched read-only; nothing was submitted to any TSA, calendar or log.

**Verdict: ready after listed fixes.** The core idea is sound: countersign one DSSE signature, salt the possession and catalogue digests, report each outcome separately, and keep the §11 limits. Four design gaps need fixing before REG.1/REG.2 (F1–F4). The fixture checker accepts nine wrong-but-plausible outputs (§2).

## 1. Clean room

I implemented the 11-step verification of §10 from the document text alone, before reading `check_registration.py`: pure-Python Ed25519 (RFC 8032 §5.1.7) and the DSSE PAE; the §4 statement rules, the §4.3 possession digest and the core catalogue commitment; evidence targets and `notAfter` (§6.2), the per-root and quorum bounds (§6.3); and the result, link and rendering rules (§9–§11).

**Result: 38/38 fixtures as expected on the first run.** The 11 positives give no code, and each of the 27 negatives gives its expected code. The author's checker, run on a scratch copy, reports the same.

**Guesses, each an ambiguity finding** (D = decides bytes or outcomes):
- **A1 (D):** "the SHA-256 of one DSSE signature value" (§6.1). It must say: the raw decoded signature bytes, not the base64 text. I guessed raw, which matched.
- **A2 (D):** `after-proved-bound` (§10 step 10) does not say which bound is compared. The checker uses `notAfterAnyRoot`; I used the quorum bound. No fixture distinguishes them. Fix: name the bound, preferably `notAfterAnyRoot`, as the checker does.
- **A3 (D), contradiction:** §6.2 makes an RFC 3161 token without `accuracy` (and no policy accuracy) the **outcome** `unsupported`, but `neg-evidence-shape` expects the **failure code** `evidence-shape`, and the policy object (`quorum`, `acceptedRoots`, `trustedKeyids`) has no per-root accuracy field. Fix: add `rootAccuracySeconds` to the policy and make the case an `unsupported` outcome with a fixture.
- **A4 (D):** Ed25519 strictness is unpinned: canonical S (S < L), non-canonical A or R encodings, small-order keys, cofactored or cofactorless equation (RFC 8032 §8.4, §8.8). Two implementations (REG.2) can disagree on edge signatures. Fix: pin RFC 8032 §5.1.7 cofactorless verification with S < L, reject non-canonical encodings and small-order public keys, and add vectors.
- **A5–A8:** the stated-time and policy field names (`genTime`, `accuracySeconds`, `blockTime`, `cosignatureTime`) appear only in fixtures; the `time-in-statement` and `forbidden-field` key lists end in "and others" (§4.6) while the checker has fixed sets; key lookup when the `keyid` hint is absent or matches no key (§10 step 2) is unspecified; and that link-opening "catalogue bytes" are the JCS bytes of the referenced object is stated only in the checker.

## 2. Wrong-but-plausible verifiers and producers against the checker

Each variant was written as a fixture and run through the author's checker. **ACCEPTED** means no code was reported.

| # | Variant | Checker |
| --- | --- | --- |
| W1 | Time evidence over the statement body, not the signature digest | rejected `evidence-wrong-target` |
| W2 | Claimed creation time reported as the proved bound | rejected `claimed-as-proved` |
| W3 | Two TSAs under one CA, given different root ids, counted as two roots | **ACCEPTED**: a root is a free-text label |
| W4 | Nonce reused across two registrations | **ACCEPTED**: not checkable per record |
| W5 | Possession digest computed without the nonce | rejected `possession-mismatch` |
| W6 | Subject digest over normalized bytes (trailing LF stripped) | rejected when the bytes are supplied; **ACCEPTED** when they are not |
| W7 | A later signature (new nonce) carrying the earlier registration's evidence | rejected `evidence-wrong-target` |
| W8 | A second key co-signs the statement later; the result trusts only that key and reports the statement-level bound | **ACCEPTED** (F1) |
| W9 | TSA certificate validity at `genTime` ignored | not testable: placeholders carry no chain or revocation data |
| W10 | Key reported compromised before the bound, still `trusted` | **ACCEPTED**: key events are not a result input (F3) |
| W11 | Two-root bound taken as the earliest | rejected `result-mismatch` |
| W12 | Renderings "This registration establishes your claim to sum.go.", "sum.go is registered to you as its creator.", "This record proves you wrote sum.go.", "Registered first: sum.go belongs to key cd76…" | **all four ACCEPTED** (F4) |
| W13 | Pending OpenTimestamps proof counted | rejected `pending-counted`, `quorum-miscount` |
| W14 | OpenTimestamps margin dropped | rejected `result-mismatch` |

W4 and W6b cannot be caught from one record. The document should say that nonce freshness and subject canonicality are producer obligations, verifiable only when the bytes are supplied.

## 3. Cryptographic and protocol correctness (primary sources fetched 2026-11-23)

**RFC 3161 (2001), RFC 5816 (2010) and RFC 4998.**
- **Correct:** `notAfter = genTime + accuracy`, and absent `accuracy` "may be available through other means, e.g., the TSAPolicyId" (§2.4.2); `messageImprint` = SHA-256 of the signature; RFC 5816 ESSCertIDv2 for SHA-256 certificate identifiers; RFC 4998 hash-tree renewal needs all the data again (§1.2).
- **Missing from the draft:**
  - **§4.1:** when a TSA certificate is revoked without a reasonCode, "all the tokens that have been signed with the corresponding key SHALL be considered as invalid". With a reasonCode of key compromise (§4.2), "Any token signed by the TSA using that private key cannot be trusted anymore". Past tokens die retroactively. Renewal (§14 step 5) must happen *before* any revocation, and the threat model must say one root can be lost in this way.
  - **Request nonce:** the RFC 3161 request `nonce` (§2.4.1) protects against a replayed response at request time. The producer must send it and check it. The draft's statement nonce does not do this job.
  - **Policy OID:** the verifier must check the token's `policy` OID against the root's policy. §10 step 8 should say so.

**DSSE and in-toto.**
- PAE is used correctly, and `keyid` is an unauthenticated hint (DSSE protocol). Subjects match "purely by digest" (in-toto Statement v1), so the restricted names are a local rule. That is fine.

**Time evidence over SHA-256 of one signature: sound for the signature, but reported at the wrong level (F1).**
- The evidence bounds *that signature*, hence (statement, that key). Ed25519 is deterministic, and with S < L enforced nobody can produce a second encoding of my signature; a lenient-verifier encoding would have a different digest and could only lose time. Nobody can get an *earlier* time for their own signature over my statement, which stays private (fresh nonce) until disclosure.
- **The problem:** after disclosure anyone can add their own signature to my envelope. §6.3 and the result give one statement-level bound, and §11 sentence 1 says "this key signed … no later than". W8 shows a result that trusts only the later key and still reports T.
- **Fix:** compute bounds per signature, using only evidence that targets that signature. Name the key in the rendering, and reject a result that reports a bound for a key none of whose signatures has evidence.

**Possession digest:** it adds what it claims and no more. Without the bytes nobody can compute `SHA256(tag‖0x00‖nonce‖L‖A)` for a fresh nonce, so a published artifact digest is not enough; but anyone who holds the bytes when they register can, so for content public at T it adds nothing. §4.3 says so; §12 should repeat it.

**Salted catalogue commitment:** hiding (32-byte secret nonce, SHA-256 as a random oracle) and binding (collision resistance, length-framed), as core states. The fixtures reuse the published `test-vectors/commitment.json` nonce, which core forbids in production; say so in the README.

**OpenTimestamps (client README `f3a9e92e`).**
- A pending proof shows nothing until upgraded; a complete proof shows a commitment in a Bitcoin block, and calendars are trusted only for liveness before the upgrade. Verifying needs "a local Bitcoin Core node (a pruned node is fine)", a trusted header source, so "verifiable offline once complete" (§1, §13) holds only if headers are retained or a node is available.
- **The RD6 rationale points the wrong way.** The two-hour future rule bounds the mining time from *below* (header time ≤ mining time + 2 h). An *upper* bound on existence needs the claim that a header time lags the real mining time by at most X. That holds only under an honest-majority assumption through median-time-past. State the assumption, and justify the 7,200 s on that basis.

## 4. Threat model completeness (§12)

The draft covers backdating by the registrant, copiers registering, transplanting evidence, privacy of digests and the catalogue, pending proofs and service shutdown. It is missing:
- **F2: root identity.** A root must be identified by its trust anchor (CA certificate digest, Bitcoin genesis), not by a label the producer writes (W3). Two TSAs under one CA, or a TSA the registrant runs, must count once or not at all. Policy should list anchors.
- **Retroactive loss of one root** (RFC 3161 §4.1 and §4.2). With q = 2 and exactly two roots, losing one leaves `below-quorum` for every past registration. Recommend obtaining evidence from three roots (two unrelated TSAs plus OpenTimestamps), so q = 2 survives one loss.
- **F3: hostile compromise events.** A thief, or an ex-collaborator holding the key, can publish `compromised` with a very early `compromisedNotBefore`, and every honest past registration becomes `untrusted`. §8 says such an event "only reduces trust"; it is a denial of all past evidence. Key events must be a verification input in the result and fixtures (W10), reported with their own proved time instead of silently flipping trust.
- **Key theft window.** Registrations signed with a stolen key between theft and the compromise event are listed as "ambiguous". Say that they are indistinguishable from the owner's.
- **Linkage.** One I0 key across all registrations links every disclosed registration and every time-service request made under it. Offer a per-work key option, and state the trade-off against I1.
- **Low-entropy content.** The subject digest confirms guesses (§5 says so). The possession digest does too once the statement is disclosed, so it does not protect short snippets either.
- **Algorithm ageing.** Covered; add Ed25519 and SHA-256 to the renewal trigger list, with RFC 4998 hash-tree renewal for SHA-256.

## 5. Verifier output honesty

- Separate outcomes, `notShown` and the three fixed sentences are present. The result has no combined verdict.
- **The sentences are not sufficient alone (F4).** The checker's authorship test needs a verb from a short list ("proves", "establishes", …) followed by an authorship noun, and any "not" in the line suppresses it, so "proves you wrote", "registered to you as its creator", "establishes your claim" and "belongs to key …" all pass (W12). Fix: an allow-list of rendering templates, or a broader deny-list (wrote, belongs, yours, claim to, registered to you, first to create, priority), plus a non-author wording review under REG.4.
- §11 sentence 2 omits **permission**, although `notShown` lists it. Add "or that its use is permitted".
- With several signatures, sentence 1 ("this key") must name the key whose signature carries the bound (F1).

## 6. Lane 13 spot-check (eight decision-relevant claims, against the texts fetched today)

| Claim | Source | Result |
| --- | --- | --- |
| Two tokens from two TSAs defend against a compromised TSA key | RFC 3161 §4.2 | Confirmed |
| Tokens SHOULD be re-time-stamped before TSA key expiry | RFC 3161 §4.3 | Confirmed ("if authentic copies of old CRLs are available") |
| TSA must not examine the imprint or identify the requester | RFC 3161 §2.1 items 8, 9 | Confirmed |
| Tokens before a non-compromise revocation "remain valid" | RFC 3161 §4.1 | **Incomplete:** only if the CRL entry has a reasonCode; otherwise all tokens are invalid. Add the condition |
| Calendars receive "an opaque and meaningless digest"; a 51% attack does not unverify past stamps; verification needs "the relevant calendar data" | OpenTimestamps README | Confirmed |
| Verifying needs a local Bitcoin Core node | OpenTimestamps README | Confirmed; contradicts the Decision's "verifiable offline once complete" unless headers are retained |
| Rekor v1 time is internal and mutable; v2 takes time from a TSA; Sigstore recommends countersigning the signature | Sigstore `timestamps.md` at `8aed8c10` | Confirmed |
| Hash-tree renewal needs all data again | RFC 4998 §1.2 | Confirmed |

## 7. Decisions before implementation, and the test submissions

**Decisions:**
- **RD1** [(a) RFC 3161 + OpenTimestamps is the right first pair: unrelated roots, no accounts, digest only]. Add: allow two TSAs as well (three evidences), and implement RFC 3161 first, since OpenTimestamps verification needs a Bitcoin header source.
- **RD5** [q = 2, always report both bounds, roots counted by trust anchor (F2)]; **RD6** [keep 7,200 s only with the honest-majority lag assumption stated (§3); else use a later block's median-time-past]; **RD7** [mandatory]; **RD8** [signature digest, with per-signature bounds (F1)]; **RD2–RD4** [owner; I0 default plus a per-work-key option].
- **New:** Ed25519 strictness (A4); the policy accuracy field (A3); key events as a verification input (F3).

**What one test submission discloses** (no service was contacted):
- **RFC 3161:** the request holds the SHA-256 imprint of a signature over a synthetic statement, the hash OID, an optional nonce and `certReq`. The TSA sees the client IP, the time, the HTTP user agent and TLS metadata, and may log them under its terms. Nothing is published. The token returns the TSA certificate chain.
- **OpenTimestamps:** the client by default submits the digest (further hashed with a nonce) to several calendars (three in the README example). Each calendar sees the IP and the time. The calendar's Merkle root is published in a Bitcoin transaction for ever, but the digest is not revealed unless the proof is shown. Anyone who knows the digest can fetch the proof path from the calendar. That is unguessable here.
- **Neither** reveals content or identity beyond network metadata; both reveal that this address used a time-stamping service at that time. Use one TSA and one calendar for the test (`--calendar`), over a synthetic statement.

## Fixes, in priority order

1. **F1:** bounds per signature; name the key in sentence 1; add a two-signature fixture (W8).
2. **F2:** identify roots by trust anchor in the policy (W3), and recommend three evidences.
3. **F3:** key events as verification input; hostile compromise events in the threat model (W10).
4. **F4:** stronger rendering rules; add "permission" to sentence 2 (W12).
5. Resolve A1–A4 (target bytes, the `after-proved-bound` bound, the accuracy contradiction, Ed25519 strictness), and list A5, A6 and A8 in the text.
6. Add RFC 3161 §4.1/§4.2 retroactive invalidation, the request nonce and policy-OID checks; correct lane 13's §4.1 claim; correct the OpenTimestamps offline claim and the RD6 rationale.
