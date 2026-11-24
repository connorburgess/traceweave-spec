# Registration record fixtures, draft-5 (illustrative)

These fixtures belong to the [registration record draft](../registration-record.md), draft-5. They are research material, not test vectors, and nothing in `validate` runs them yet (REG.1 proposes that).

**What these are not.**
- No external time-stamping authority, calendar, transparency log or witness produced any of them. **No external service was contacted.**
- **Placeholder evidence** says so in its `notice` and `token`, and its times, anchors and certificate dates are written by the producer and accepted as given. So placeholder fixtures do **not** test that a verifier computes anchors (S10).
- The **real-format vectors** in `real-format/` were made locally by `make_real_vectors.py` with the local `openssl` (version in `MANIFEST.json`) and header chains mined locally at regtest difficulty (the honest one, an unrelated one, and a fork on the same first header). Their anchors are test-only and **must never be trusted**. The private keys existed only in a temporary directory during that run.
- The Ed25519 keys (creator, co-signer, successor, witness, thief) and nonces are public test-only values derived from fixed labels in `build_fixtures.py`. Never use them for anything real.
- The catalogue nonce is the public synthetic nonce of `test-vectors/commitment.json`. Core forbids reusing it in production; it is reused here only so the opening can be rechecked.
- Provenance commits are all zeros, as in `example-report.json`.

A fixture registers nothing and proves nothing.

## Files

| Path | Kind | Content |
| --- | --- | --- |
| `fixtures/a2a-card-hosted-witness.json` | a2a-agent-card | Illustrative A2A 1.0 Agent Card for a hosted witness (architecture b). Checked against the a2a.proto field lists only. |
| `fixtures/a2a-card-local-registrar.json` | a2a-agent-card | Illustrative A2A 1.0 Agent Card for a local registrar on loopback (architecture a). |
| `fixtures/a2a-request-witness.json` | a2a-request | SendMessageRequest to the witness: one data part with the signature digest. |
| `fixtures/a2a-task-witness.json` | a2a-task | Completed task: one artifact holding the signed witness statement and the witness's RFC 3161 placeholder. |
| `fixtures/bundle-cosigned.json` | bundle | The same statement later co-signed by a second key; evidence covers signature 0 only. |
| `fixtures/bundle-real.json` | bundle | Real-format evidence: a token from a local test-only TSA and an OpenTimestamps proof against a locally mined header file. |
| `fixtures/bundle-renewed.json` | bundle | bundle-three-roots plus a renewal token (TSA B, 2030) over TSA A's token bytes. |
| `fixtures/bundle-second-work.json` | bundle | A second registration by the same registrant, fresh nonce. |
| `fixtures/bundle-three-roots.json` | bundle | Signed statement with placeholders from three independent roots (TSA A, TSA B, Bitcoin) and a Rekor v2 entry (no time). |
| `fixtures/bundle-url-safe.json` | bundle | Payload and signature in URL-safe base64; DSSE verifiers MUST accept either (S7). |
| `fixtures/evidence-opentimestamps-complete.json` | evidence | Upgraded OpenTimestamps proof placeholder. |
| `fixtures/evidence-opentimestamps-pending.json` | evidence | OpenTimestamps proof before upgrade: no time. |
| `fixtures/evidence-real-opentimestamps-pending.json` | evidence | Real-format pending OpenTimestamps proof (calendar attestation only). |
| `fixtures/evidence-real-opentimestamps.json` | evidence | Real-format OpenTimestamps proof, attested at height 4 of the synthetic chain. |
| `fixtures/evidence-real-rfc3161.json` | evidence | Real RFC 3161 TimeStampResp from the local test TSA, with its request. |
| `fixtures/evidence-rekor-v2.json` | evidence | Rekor v2 inclusion placeholder; no time of its own. |
| `fixtures/evidence-renewal.json` | evidence | Renewal: an RFC 3161 placeholder whose target is the token bytes of evidence 0. |
| `fixtures/evidence-rfc3161-no-accuracy.json` | evidence | RFC 3161 placeholder without accuracy; the verifier's policy supplies it. |
| `fixtures/evidence-rfc3161.json` | evidence | RFC 3161 placeholder over the raw bytes of signature 0. |
| `fixtures/evidence-witness.json` | evidence | A hosted witness's statement as evidence; its bound comes from its own TSA token. |
| `fixtures/key-event-compromise-early.json` | key-event | Compromise claimed from a date long before it was reported. |
| `fixtures/key-event-compromise-recent.json` | key-event | Compromise reported two days after the claimed start. |
| `fixtures/key-event-rotation.json` | key-event | The key names its successor; time-stamped like a registration. |
| `fixtures/mcp-tool-register.json` | mcp-tool | Illustrative MCP 2026-07-28 Tool for the local route. |
| `fixtures/registration-set.json` | registration-set | Two registrations by one producer: nonces differ. |
| `fixtures/rendering-agent.json` | rendering | User-facing text for a registration made through an agent. |
| `fixtures/rendering-cosigned.json` | rendering | Text for the co-signed bundle: a bound sentence only for the key that has one. |
| `fixtures/rendering.json` | rendering | User-facing text built only from the allowed templates. |
| `fixtures/report-link.json` | report-link | Links the committed example comparison report to the registration, without changing the report. |
| `fixtures/result-equivalence-e1.json` | result-equivalence | E1: the same events with 0, 1 and 2 extra rejected events give byte-identical outcomes for the common events. |
| `fixtures/statement.json` | statement | The registration statement (in-toto Statement v1) before signing. |
| `fixtures/verification-result-chain-same-time.json` | verification-result | Enumeration finding: trust flows only through a rotation proved strictly after its signer became trusted. |
| `fixtures/verification-result-claim-trusted-only.json` | verification-result | The claimed time is compared only with trusted signatures (S11): `claimed-only`. |
| `fixtures/verification-result-compromise-early.json` | verification-result | An early-dated claim is clamped to the look-back window: `trusted`. |
| `fixtures/verification-result-compromise-recent.json` | verification-result | Bound between the claimed start and the event's proved time: `disputed`. |
| `fixtures/verification-result-cosigned.json` | verification-result | Per-signature bounds: the co-signer gets none. |
| `fixtures/verification-result-e1-extra-1.json` | verification-result | E1 with one extra rejected event: same outcomes. |
| `fixtures/verification-result-e1-extra-2.json` | verification-result | E1 with two extra rejected events: same outcomes. |
| `fixtures/verification-result-e1-second-level.json` | verification-result | E1 one level down: the second successor's report about the first successor does not dispute its own appointment. |
| `fixtures/verification-result-e1.json` | verification-result | E1: a successor's compromise report never disputes its own appointment; the successor stays trusted. |
| `fixtures/verification-result-event-order-a.json` | verification-result | B2: retirement listed before the rotation it relies on; identical result to order b. |
| `fixtures/verification-result-event-order-b.json` | verification-result | B2: the same two events in the other order; identical result to order a. |
| `fixtures/verification-result-event-unauthorized.json` | verification-result | An event signed by another key is `ignored-unauthorized`. |
| `fixtures/verification-result-expired.json` | verification-result | Verified in 2032, after both TSA certificates expired, with no renewal: two tokens `expired-unrenewed`. |
| `fixtures/verification-result-late-compromise-claim.json` | verification-result | D2: a compromise claim filed after the look-back window cannot dispute the honest rotation. |
| `fixtures/verification-result-late-second-rotation.json` | verification-result | D2: a second rotation of an already-rotated key is `ignored-superseded`; the honest successor stays trusted. |
| `fixtures/verification-result-no-accuracy.json` | verification-result | TSA B's token has no accuracy and the policy gives none: `unsupported`. |
| `fixtures/verification-result-no-revocation-data.json` | verification-result | No revocation data for TSA A: its token cannot be judged offline (S3). |
| `fixtures/verification-result-real-decoy-first.json` | verification-result | A valid token under an intermediate, with a decoy certificate of the same name inserted first; path building backtracks and the token is valid. |
| `fixtures/verification-result-real-ecdsa.json` | verification-result | D7: a valid token from an ECDSA TSA; this checker reports it `unsupported`, never as a forgery. |
| `fixtures/verification-result-real-expired-intermediate.json` | verification-result | D4: TSA certificate under an intermediate that expired in 2021. Outcome `path-invalid`. |
| `fixtures/verification-result-real-issued-by-end-entity.json` | verification-result | D4: TSA certificate issued by an end-entity (CA:FALSE) certificate. Outcome `path-invalid`. |
| `fixtures/verification-result-real.json` | verification-result | Not simulated: both real-format evidences verify; anchors computed from the pinned root certificate and header file. |
| `fixtures/verification-result-recovery-key.json` | verification-result | RD18: after the thief's rotation is disputed, the owner's recovery key, listed in the policy from 2026-11-29, is trusted for later bounds. |
| `fixtures/verification-result-renewed.json` | verification-result | Verified in 2032: TSA A's token survives its certificate's expiry through the 2030 renewal; TSA B's does not. |
| `fixtures/verification-result-retired-and-rotated-same-time.json` | verification-result | D1: a retirement and a rotation of one key at the same proved time are both `disputed`; no trust flows. |
| `fixtures/verification-result-retired-then-rotated.json` | verification-result | D1: after the retirement, the old key's later rotation is `ignored-superseded`; the thief's key stays untrusted. |
| `fixtures/verification-result-revoked-key-compromise.json` | verification-result | TSA A revoked for key compromise: all its tokens are invalid (section 4 item 2). |
| `fixtures/verification-result-revoked-one-unit.json` | verification-result | D5: the revocation names signing certificate 1; certificate 2's token under the same root stays valid. |
| `fixtures/verification-result-revoked-retaining.json` | verification-result | TSA A revoked as superseded after genTime: its earlier token stays valid. |
| `fixtures/verification-result-revoked.json` | verification-result | TSA A revoked without a reasonCode: all its tokens are invalid (RFC 3161 section 4 item 1). |
| `fixtures/verification-result-rotation-applied.json` | verification-result | The successor is trusted for signatures bounded after the rotation. |
| `fixtures/verification-result-rotation-conflict.json` | verification-result | D2: a second, different rotation of an already-rotated key is `ignored-superseded`; the first successor stays trusted. |
| `fixtures/verification-result-rotation-hijack.json` | verification-result | B1: the rotation falls inside the later compromise window, so it is `disputed` and the thief's key gains no trust. |
| `fixtures/verification-result-same-statement-twice.json` | verification-result | The same signed statement supplied twice is one event, with its earliest proved time. |
| `fixtures/verification-result-same-statement-two-signers.json` | verification-result | Enumeration finding: one statement signed by two keys is two events (identity = SHA-256 of payload and signature). |
| `fixtures/verification-result-single-source-event.json` | verification-result | S1: a key event affects the key and the signature has no quorum bound: `disputed`, never `trusted`. |
| `fixtures/verification-result-stripped.json` | verification-result | Removing an evidence can only make the bounds later (N3). |
| `fixtures/verification-result-witness-independent.json` | verification-result | S4: witness on TSA B plus direct TSA A: two classes, `quorum-met`. |
| `fixtures/verification-result-witness-shared-tsa.json` | verification-result | S4: the witness rests on TSA A, so it and the direct token form one class: `below-quorum`. |
| `fixtures/verification-result-wrong-policy.json` | verification-result | TSA A's token policy OID is not one the verifier accepts: `wrong-policy`. |
| `fixtures/verification-result.json` | verification-result | Expected outcomes for bundle-three-roots and sum.go; placeholders assumed valid (simulated). |
| `aux/bundle-cert-expired.json` | bundle | TSA A's signing certificate expired before genTime. |
| `aux/bundle-claim.json` | bundle | Claimed 10:00:03; the trusted signature's earliest bound is 10:00:06, the untrusted co-signer's 10:00:01. |
| `aux/bundle-nonce-reused.json` | bundle | Another work registered with the same nonce. |
| `aux/bundle-one-source.json` | bundle | Only one time source (TSA A) for the creator's signature. |
| `aux/bundle-other-catalogue.json` | bundle | Registration committing to another catalogue. |
| `aux/bundle-other-profile.json` | bundle | Registration under a different profile version. |
| `aux/bundle-real-decoy-first.json` | bundle | A valid token under an intermediate, with a decoy certificate of the same name inserted first; path building backtracks and the token is valid. |
| `aux/bundle-real-ecdsa.json` | bundle | D7: a valid token from an ECDSA TSA; this checker reports it `unsupported`, never as a forgery. |
| `aux/bundle-real-expired-intermediate.json` | bundle | TSA certificate under an intermediate that expired in 2021. |
| `aux/bundle-real-issued-by-end-entity.json` | bundle | TSA certificate issued by an end-entity (CA:FALSE) certificate. |
| `aux/bundle-same-anchor.json` | bundle | Two TSA tokens under one trust anchor. |
| `aux/bundle-second-successor-late.json` | bundle | A registration signed by the second successor, 2026-12-15. |
| `aux/bundle-second-successor.json` | bundle | A registration signed by the second successor, 2026-12-10. |
| `aux/bundle-stripped.json` | bundle | bundle-three-roots with TSA B's evidence removed in transit. |
| `aux/bundle-successor-dec.json` | bundle | The successor's registration, 2026-12-10. |
| `aux/bundle-successor.json` | bundle | A registration signed by the successor key after the rotation. |
| `aux/bundle-thief-2027.json` | bundle | A registration signed by the thief's key in 2027. |
| `aux/bundle-thief.json` | bundle | A registration signed by the thief's key after the hijacking rotation. |
| `aux/bundle-two-tsa-units.json` | bundle | Tokens from two signing certificates under TSA A's root, plus Bitcoin. |
| `aux/bundle-witness-independent.json` | bundle | Direct TSA A token plus a witness whose token comes from TSA B. |
| `aux/bundle-witness-shared-tsa.json` | bundle | Direct TSA A token plus a witness whose own token also comes from TSA A. |
| `aux/key-event-by-other-key.json` | key-event | A compromise event for the creator key, signed by an unrelated key. |
| `aux/key-event-compromise-2028.json` | key-event | And claims the old key was compromised since 2026-01-01. |
| `aux/key-event-compromise-after-theft.json` | key-event | The owner reports the theft afterwards, from 2026-11-25T12:00. |
| `aux/key-event-compromise-by-second-successor.json` | key-event | The second successor reports the first successor compromised from before its rotation. |
| `aux/key-event-compromise-by-successor.json` | key-event | The successor reports the old key compromised 10 days after the rotation, from 5 days before it. |
| `aux/key-event-onward-rotation-same-time.json` | key-event | The successor rotates onward with the same proved time as its own rotation. |
| `aux/key-event-onward-rotation.json` | key-event | The successor rotates onward, proved 2026-12-01T03:00. |
| `aux/key-event-rejected-1.json` | key-event | An unauthorized event: the attacker's key signs a retirement of the old key. |
| `aux/key-event-rejected-2.json` | key-event | An unauthorized event: the attacker's key signs a retirement of the old key. |
| `aux/key-event-retired-by-successor.json` | key-event | The successor retires the old key after the rotation. |
| `aux/key-event-retired-later-proof.json` | key-event | The same signed retirement as key-event-retired, with a later proof. |
| `aux/key-event-retired.json` | key-event | The owner retires the key, proved 2026-11-26T03:00. |
| `aux/key-event-rotation-after-retirement.json` | key-event | Whoever later holds the retired key rotates it to the thief. |
| `aux/key-event-rotation-conflicting.json` | key-event | A second rotation of the same key to a different successor. |
| `aux/key-event-rotation-honest.json` | key-event | The owner rotates the key to the successor, proved 2026-11-26T03:00. |
| `aux/key-event-rotation-same-time.json` | key-event | A rotation to the thief with the same proved time as the retirement. |
| `aux/key-event-rotation-to-thief-signed-by-thief.json` | key-event | The same rotation statement as key-event-rotation-to-thief, signed by the thief's key instead. |
| `aux/key-event-rotation-to-thief.json` | key-event | A thief holding the key rotates it to the thief's own key. |
| `aux/key-event-second-rotation-2028.json` | key-event | Eighteen months later, whoever obtained the old key rotates it again. |
| `aux/verification-result-e1-flipped.json` | verification-result | Draft-4 behaviour with one extra rejected event (the flip), kept as input to the equivalence negative. |

`negative/` holds 94 broken fixtures; each must produce exactly the codes listed below. `aux/` holds inputs that other fixtures refer to; they are not checked on their own.

| Real-format file | SHA-256 (from `MANIFEST.json`) |
| --- | --- |
| `real-format/headers-forked.bin` | `38585f3e8565531a…` |
| `real-format/headers-other.bin` | `6c9ae8ff0cb017d2…` |
| `real-format/headers.bin` | `7ffedf9065723d4f…` |
| `real-format/opentimestamps-other-digest.ots` | `bc4ca13c114cfb82…` |
| `real-format/opentimestamps-pending.ots` | `1bd5597f59ad87ad…` |
| `real-format/opentimestamps-proof.ots` | `6d4ad3c8729ca55c…` |
| `real-format/rfc3161-request-other-digest.der` | `d8e3653cec3ee22d…` |
| `real-format/rfc3161-request.der` | `52f0f4d2a680f6c1…` |
| `real-format/rfc3161-response-decoy-first.der` | `2be6a66c1782ce44…` |
| `real-format/rfc3161-response-ecdsa.der` | `1aeb3f1350944c0b…` |
| `real-format/rfc3161-response-expired-intermediate.der` | `d455a077d35df16d…` |
| `real-format/rfc3161-response-issued-by-end-entity.der` | `4b473b0b20ded5e4…` |
| `real-format/rfc3161-response-noncritical-eku.der` | `28b7123ebd20bcb1…` |
| `real-format/rfc3161-response-other-digest.der` | `d3efbbc4b2899242…` |
| `real-format/rfc3161-response-tampered.der` | `338fbee6b301ab36…` |
| `real-format/rfc3161-response-valid-intermediate.der` | `42b3b622266ba555…` |
| `real-format/rfc3161-response-wrong-ess.der` | `4e9017fea8cd27bb…` |
| `real-format/rfc3161-response.der` | `01dd5b7bfb11a4e9…` |
| `real-format/test-root-ca.der` | `ba5c2850a36caee8…` |

Scripts, all standard library only, Python 3.11 or later:
- `build_fixtures.py` rebuilds `fixtures/`, `negative/` and `aux/` deterministically, reading `real-format/` as input.
- `make_real_vectors.py` remakes `real-format/` and is run by hand. It needs the local `openssl`, contacts nothing, and its output is not reproducible byte for byte.
- `check_registration.py` is the checker, and `realformat.py` is its DER, X.509 (with RFC 5280 path validation), CMS, RSA and OpenTimestamps code. The checker loads it by path.
- `enumerate_key_events.py` is the key-event enumeration test (design §8). It checks every sequence of length 1–3 over 100 symbols (1,010,100) and 200,000 sampled sequences of length 4 against 13 invariants. It also rebuilds 300 sampled sequences as real signed bundles and loads them, and runs a mutation check against three weakened rule sets, the draft-4 fixed point among them. It runs separately, in about a minute.

## What the checker does

- **Self-tests.** Ed25519 against RFC 8032 §7.1 tests 1 and 2; the PAE against the first case of `test-vectors/dsse-pae.json` (values written inline).
- **Signatures.** Strict Ed25519 (design §10.1); one signature per key; standard or URL-safe base64; key identity by SHA-256 of the full key.
- **Statements.** The §4 rules.
- **Time evidence** (§6):
  - targets over raw signature bytes, or over an earlier token for renewal;
  - roots by anchor; placeholder labelling;
  - RFC 3161: nonce, policy OID, certificate validity, revocation with reason codes and dated revocation data, expiry and renewal, and accuracy from the token or the policy;
  - OpenTimestamps pending or complete, with the 7,200 s margin;
  - no time for Rekor v2;
  - witness evidence resting on two anchors.
- **Real-format vectors** (§6.5):
  - RFC 3161 imprint, request nonce, ESSCertIDv2, critical timeStamping EKU, single SignerInfo, TSTInfo version, no duplicate signed attributes, messageDigest and RSA signature, and RFC 5280 path validation to the pinned root at `genTime`; `MANIFEST.json` records `openssl ts -verify` for every token, and the checker agrees;
  - OpenTimestamps operations, proof of work, Merkle root, and linkage back from the pinned checkpoint header, with `blockTime` read from the header.
- **Verification results** (§10). Recomputed and compared field by field: per-signature bounds over union-find independence classes; key events evaluated in two passes (standing, then disputes; no fixed point), with supersession and the own-standing exemption (B1–B3, D1, D2, E1); event identity by payload and signature; recovery keys; certificate-level revocation (D5); trust from quorum bounds only (S1); the claim compared with trusted signatures only (S11).
- **Result equivalence** (`result-equivalence` fixtures): results that differ only by rejected events must agree byte for byte (E1).
- **Links, sets, renderings and agent fixtures** as in the design: the report link; nonce freshness; the §11 allow-list with three fixed sentences, the ordering rule, 128-bit key display and the simulated-result marker (D6); and §19.
- **Wrong-implementation self-test.** 33 cases: plausible wrong verifiers, renderings and decoders built in memory, each of which must be caught.
- **Drift.** Every failure code appears in the design document and has a negative fixture.

The A2A fixtures are **not validated against a published A2A schema** (none is committed upstream). The MCP tool fixture was validated against MCP `schema.json` `$defs/Tool` (design §19.4).

## Negative fixtures

| File | Must produce | What is wrong |
| --- | --- | --- |
| `neg-a2a-shape` | `a2a-shape` | Patch version in protocolVersion (A2A 3.6: Major.Minor only). |
| `neg-accuracy-assumed` | `result-mismatch` | A token without accuracy, and none in policy, counted anyway (A3). |
| `neg-agent-authorship` | `authorship-claim` + `rendering-unlisted-line` | Rendering says the agent created the content. |
| `neg-agent-notice-missing` | `notice-missing` | Agent-made registration without the agent sentence. |
| `neg-authorship-claim-0` | `authorship-claim` + `rendering-unlisted-line` | Rendering adds: This registration proves you are the author of sum.go. |
| `neg-authorship-claim-1` | `authorship-claim` + `rendering-unlisted-line` | Rendering adds: This registration establishes your claim to sum.go. |
| `neg-authorship-claim-2` | `authorship-claim` + `rendering-unlisted-line` | Rendering adds: sum.go is registered to you as its creator. |
| `neg-authorship-claim-3` | `authorship-claim` + `rendering-unlisted-line` | Rendering adds: This record proves you wrote sum.go. |
| `neg-authorship-claim-4` | `authorship-claim` + `rendering-unlisted-line` + `ordering-claim` | Rendering adds: Registered first: sum.go belongs to key 18c3eead08646614. |
| `neg-card-notice-missing` | `notice-missing` | Skill description without the limit sentence. |
| `neg-catalogue-does-not-open` | `catalogue-does-not-open` | Wrong opening nonce. |
| `neg-catalogue-not-report-input` | `catalogue-not-report-input` | Opens a registered catalogue that is not the report's reference catalogue. |
| `neg-catalogue-unsalted` | `catalogue-unsalted` | Plain catalogue digest. |
| `neg-cert-validity-ignored` | `result-mismatch` | TSA certificate validity at genTime ignored (W9). |
| `neg-chain-same-time` | `key-event-ignored` | Enumeration finding: trust passed on through a rotation with the same proved time as the predecessor's own. |
| `neg-checkpoint-type-removed` | `evidence-shape` | The cosigned-checkpoint type is removed in draft-3 (S5). |
| `neg-claim-any-signer` | `result-mismatch` | S11: the claim compared with the untrusted co-signer's earlier bound. |
| `neg-claimed-as-proved` | `claimed-as-proved` | Claimed creation time reported as the earliest bound. |
| `neg-content-on-wire` | `content-on-wire` | Sends the file itself as a raw part to the hosted witness. |
| `neg-duplicate-key` | `duplicate-key` | Duplicate JSON key; the strict parser refuses the file, so the code is in the file name |
| `neg-duplicate-signer` | `envelope-shape` | The same key signs the envelope twice. |
| `neg-e1-report-disputes-own-appointment` | `key-event-ignored` | E1 (review case): the successor's report disputes the rotation that gives it standing; successor reported untrusted. |
| `neg-envelope-shape` | `envelope-shape` | Wrong DSSE payload type. |
| `neg-event-identity-collision` | `key-event-ignored` | Enumeration finding: two signers of one statement collapsed into one event. |
| `neg-event-order-dependent` | `key-event-ignored` | B2: a list-order evaluator ignores the retirement that precedes its rotation in the list. |
| `neg-evidence-shape` | `evidence-shape` | Malformed genTime. |
| `neg-evidence-target-base64` | `evidence-wrong-target` | Token over the base64 text of the signature, not its raw bytes (A1). |
| `neg-evidence-wrong-target` | `evidence-wrong-target` | Token over the statement bytes, not over the signature. |
| `neg-expired-accepted` | `result-mismatch` | S6: tokens accepted after their TSA certificates expired, with no renewal. |
| `neg-extra-event-changed-result` | `extra-event-changed-result` | E1 (review case): adding one rejected event flips the successor's trust. |
| `neg-fingerprints-on-wire` | `forbidden-field` | Sends fingerprints to the hosted witness. |
| `neg-fixture-shape` | `fixture-shape` | Fixture notice removed. |
| `neg-forbidden-field` | `forbidden-field` | Fingerprints in the statement. |
| `neg-hosted-plain-http` | `content-on-wire` | Digests-only witness offered over plain HTTP. |
| `neg-key-bound-misattributed-rendering` | `key-bound-misattributed` | The co-signer is given the first signature's bound (W8). |
| `neg-key-bound-misattributed` | `key-bound-misattributed` | A later co-signature inherits the earlier signature's bound (W8). |
| `neg-key-event-ignored` | `key-event-ignored` | A compromise event covering the bound is ignored; signer still `trusted` (W10). |
| `neg-key-event-shape` | `key-event-shape` | Compromise event without its claimed start. |
| `neg-key-event-subject-mismatch` | `key-event-shape` | B3: the event's keyid hint names the creator key but its subject digest names another key. |
| `neg-late-rotation-erases-chain` | `key-event-ignored` | D2 (review case): a much later second rotation disputes the honest chain; the successor reported untrusted. |
| `neg-log-time-claimed` | `log-time-claimed` | Rekor v2 placeholder that claims a time. |
| `neg-mcp-tool-shape` | `mcp-tool-shape` | Registration tool declared closed-world and idempotent. |
| `neg-nonce-invalid` | `nonce-invalid` | All-zero nonce. |
| `neg-nonce-reused` | `nonce-reused` | Nonce reused across two registrations (W4). |
| `neg-notice-missing` | `notice-missing` | Rendering without the three fixed sentences. |
| `neg-ordering-claim` | `ordering-claim` + `rendering-unlisted-line` | Two registrations' times presented as an order (S8). |
| `neg-pending-counted` | `pending-counted` | A pending proof that states a block time. |
| `neg-placeholder-unlabelled` | `placeholder-unlabelled` | Placeholder presented as a real token. |
| `neg-policy-min-confirmations-zero` | `result-mismatch` | Draft-4 review: minConfirmations 0 would admit headers forged above the checkpoint; the policy is refused. |
| `neg-policy-negative-lookback` | `result-mismatch` | Draft-4 review: a negative compromise look-back is refused. |
| `neg-possession-mismatch` | `possession-mismatch` | Possession digest not computed from the content. |
| `neg-predicate-type` | `predicate-type` | Draft-2 predicate type. |
| `neg-profile-mismatch` | `profile-mismatch` | Registered profile differs from the report's. |
| `neg-provenance-shape` | `provenance-shape` | Implementation commit is not an object id (B10). |
| `neg-quorum-miscount` | `quorum-miscount` | The Rekor entry, which has no time, counted as a fourth root. |
| `neg-quorum-same-anchor` | `quorum-miscount` | Two tokens under one CA counted as two roots (W3). |
| `neg-real-expired-intermediate-accepted` | `quorum-miscount` | D4 (review case): TSA certificate under an intermediate that expired in 2021. The token is reported valid anyway. |
| `neg-real-issued-by-end-entity-accepted` | `quorum-miscount` | D4 (review case): TSA certificate issued by an end-entity (CA:FALSE) certificate. The token is reported valid anyway. |
| `neg-real-ots-forked-headers` | `quorum-miscount` | D3 (review case): headers re-mined on the pinned first header at easy difficulty, attested time 2001-01-01; reported valid anyway. |
| `neg-real-ots-other-chain` | `quorum-miscount` | Header file that does not contain the attested block; the proof is reported valid anyway. |
| `neg-real-ots-wrong-target` | `evidence-wrong-target` | A real-format proof for another digest. |
| `neg-real-root-not-pinned` | `quorum-miscount` | Pinned root file does not hash to the anchor; the token is reported valid anyway. |
| `neg-rendering-unlisted-line` | `rendering-unlisted-line` | A harmless line outside the template list is still refused. |
| `neg-renewal-wrong-target` | `evidence-wrong-target` | Renewal whose target digest is not the renewed token's bytes. |
| `neg-report-digest` | `report-digest` | The link names a different report body. |
| `neg-result-mismatch` | `result-mismatch` | An outcome value outside the closed list. |
| `neg-retired-key-rotates-same-time` | `key-event-ignored` | D1 (review case): equal proved times; the thief's key reported trusted. |
| `neg-retired-key-rotates` | `key-event-ignored` | D1 (review case): the thief's key reported trusted after a retired key's rotation. |
| `neg-revocation-by-root` | `result-mismatch` | D5 (review case): one revoked TSA certificate invalidates every TSA under the same root. |
| `neg-revocation-ignored` | `result-mismatch` | A key-compromise revocation ignored. |
| `neg-root-not-anchored` | `root-not-anchored` | Root named by a producer-written label instead of a trust anchor (W3). |
| `neg-rotation-hijack` | `key-event-ignored` | B1: the thief's successor key reported `trusted`. |
| `neg-signature-index-out-of-range` | `evidence-shape` | Target names a signature the envelope does not have. |
| `neg-signature-invalid` | `signature-invalid` | Claimed time edited after signing. |
| `neg-simulated-unmarked` | `simulated-unmarked` | D6 (review case): a rendering of a simulated result without the marker line. |
| `neg-single-verdict` | `single-verdict` | Adds a single 'authentic' verdict. |
| `neg-statement-digest` | `statement-digest` | The link names a different statement. |
| `neg-statement-shape` | `statement-shape` | Unknown predicate field. |
| `neg-subject-mismatch` | `subject-mismatch` | Links the candidate's digest instead of the registered reference. |
| `neg-subject-name` | `subject-name` | A path as subject name. |
| `neg-subject-unsupplied-match` | `result-mismatch` | Reports `match` without the file (W6b). |
| `neg-time-in-statement` | `time-in-statement` | A 'provedAt' written by the registrant. |
| `neg-trust-by-hint` | `key-identity-by-hint` | B3: the policy lists trusted keys by their 64-bit keyid. |
| `neg-trust-without-quorum` | `trust-without-quorum` | S1: trust after a key event decided on one source. |
| `neg-tsa-eku-invalid` | `tsa-eku-invalid` | Re-signed by a TSA certificate whose timeStamping EKU is not critical. |
| `neg-tsa-imprint-mismatch` | `tsa-imprint-mismatch` | A real token over another digest (the statement bytes). |
| `neg-tsa-nonce-mismatch` | `tsa-nonce-mismatch` | Token nonce differs from the request nonce: a possibly replayed response. |
| `neg-tsa-signature-invalid` | `tsa-signature-invalid` | genTime edited after signing: messageDigest no longer matches. |
| `neg-tsa-signing-cert-mismatch` | `tsa-signing-cert-mismatch` | ESSCertIDv2 names another certificate (RFC 5816). |
| `neg-witness-authorship` | `authorship-claim` | Witness statement asserts the caller is the author. |
| `neg-witness-shape` | `witness-shape` | Witness statement without the caller it authenticated. |
| `neg-witness-shared-tsa` | `quorum-miscount` | S4: a witness and the TSA its time comes from counted as two sources. |
| `neg-witness-wrong-digest` | `evidence-wrong-target` | Presents the artifact digest instead of the signature digest. |
| `neg-wrong-policy-accepted` | `result-mismatch` | A token whose policy OID the verifier does not accept, counted anyway. |

## Run

```sh
python3 -I research/drafts/registration-fixtures/build_fixtures.py
python3 -I research/drafts/registration-fixtures/check_registration.py --verbose
python3 -I research/drafts/registration-fixtures/enumerate_key_events.py      # about a minute; --quick for length <= 2
git status --short research/drafts/registration-fixtures   # rebuilt files must be unchanged
# only after a change to the registration statement (needs the local openssl; contacts nothing):
python3 -I research/drafts/registration-fixtures/make_real_vectors.py
```
