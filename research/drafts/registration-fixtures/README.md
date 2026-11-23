# Registration record fixtures, draft-2 (illustrative)

These fixtures belong to the [registration record draft](../registration-record.md), draft-2. They are research material, not test vectors, and nothing in `validate` runs them.

**What these are not.**
- No time-stamping authority, OpenTimestamps calendar, transparency log or witness produced any of them. Every time evidence is a **placeholder** that says so in its `notice` and its `token` text, and the checker rejects one that does not. Times in them are invented.
- Every trust anchor is a **placeholder digest** of a descriptive label, not the digest of any real certificate, key or chain.
- The signing keys (creator, co-signer, successor, witness) are **public test-only keys** derived from fixed labels in `build_fixtures.py`, and so are the nonces. Never use any of them for anything real.
- The catalogue nonce is the public synthetic nonce of `test-vectors/commitment.json`. Core forbids reusing it in production; it is reused here only so the opening can be rechecked.
- Provenance commits are all zeros, as in `example-report.json`.

A fixture registers nothing and proves nothing.

The data is real repository data: the artifacts are `sum.go` and `host.go` (vectors `mv-go-sum` and `mv-go-host` of `test-vectors/matching/extraction-go.json`), the catalogues come from matching vector 1, and the report is `test-vectors/matching/example-report.json`.

## Files

| Path | Kind | Content |
| --- | --- | --- |
| `fixtures/a2a-card-hosted-witness.json` | a2a-agent-card | Illustrative A2A 1.0 Agent Card for a hosted witness (architecture b). Checked against the a2a.proto field lists only. |
| `fixtures/a2a-card-local-registrar.json` | a2a-agent-card | Illustrative A2A 1.0 Agent Card for a local registrar on loopback (architecture a). |
| `fixtures/a2a-request-witness.json` | a2a-request | SendMessageRequest to the witness: one data part with the signature digest. |
| `fixtures/a2a-task-witness.json` | a2a-task | Completed task: one artifact holding the signed witness statement and an RFC 3161 placeholder over the witness signature. |
| `fixtures/bundle-cosigned.json` | bundle | The same statement later co-signed by a second key; evidence covers signature 0 only. |
| `fixtures/bundle-second-work.json` | bundle | A second registration by the same creator, fresh nonce. |
| `fixtures/bundle-three-roots.json` | bundle | Signed statement with placeholders from three independent roots (TSA A, TSA B, Bitcoin) and a Rekor v2 entry (no time). |
| `fixtures/evidence-cosigned-checkpoint.json` | evidence | Witness-cosigned checkpoint placeholder; the witness's clock. |
| `fixtures/evidence-opentimestamps-complete.json` | evidence | Upgraded OpenTimestamps proof placeholder. |
| `fixtures/evidence-opentimestamps-pending.json` | evidence | OpenTimestamps proof before upgrade: no time. |
| `fixtures/evidence-rekor-v2.json` | evidence | Rekor v2 inclusion placeholder; no time of its own. |
| `fixtures/evidence-rfc3161-no-accuracy.json` | evidence | RFC 3161 placeholder without accuracy; the verifier's policy supplies it. |
| `fixtures/evidence-rfc3161.json` | evidence | RFC 3161 placeholder over the raw bytes of signature 0. |
| `fixtures/key-event-compromise-early.json` | key-event | Compromise claimed from a date long before it was reported. |
| `fixtures/key-event-compromise-recent.json` | key-event | Compromise reported two days after the claimed start. |
| `fixtures/key-event-rotation.json` | key-event | The key names its successor; time-stamped like a registration. |
| `fixtures/mcp-tool-register.json` | mcp-tool | Illustrative MCP 2026-07-28 Tool for the local route. |
| `fixtures/registration-set.json` | registration-set | Two registrations by one producer: nonces differ. |
| `fixtures/rendering-agent.json` | rendering | User-facing text for a registration made through an agent. |
| `fixtures/rendering-cosigned.json` | rendering | Text for the co-signed bundle: a bound sentence only for the key that has one. |
| `fixtures/rendering.json` | rendering | User-facing text built only from the allowed templates. |
| `fixtures/report-link.json` | report-link | Links the committed example comparison report to the registration, without changing the report. |
| `fixtures/statement.json` | statement | The registration statement (in-toto Statement v1) before signing. |
| `fixtures/verification-result-compromise-early.json` | verification-result | An early-dated claim is clamped to the look-back window: the honest registration stays `trusted`. |
| `fixtures/verification-result-compromise-recent.json` | verification-result | Registration bound falls between the claimed start and the event's proved time: `disputed`. |
| `fixtures/verification-result-cosigned.json` | verification-result | Per-signature bounds: the co-signer gets none. |
| `fixtures/verification-result-event-unauthorized.json` | verification-result | An event signed by another key is `ignored-unauthorized`. |
| `fixtures/verification-result-no-accuracy.json` | verification-result | TSA B's token has no accuracy and the policy gives none: that evidence is `unsupported`; two roots remain. |
| `fixtures/verification-result-revoked.json` | verification-result | TSA A's certificate revoked without a reasonCode: all its tokens are invalid (RFC 3161 section 4 item 1); quorum survives on TSA B and Bitcoin. |
| `fixtures/verification-result.json` | verification-result | Expected outcomes for bundle-three-roots and sum.go; placeholders assumed valid (simulated). |
| `aux/bundle-cert-expired.json` | bundle | TSA A's signing certificate expired before genTime. |
| `aux/bundle-nonce-reused.json` | bundle | Another work registered with the same nonce. |
| `aux/bundle-other-catalogue.json` | bundle | Registration committing to another catalogue. |
| `aux/bundle-other-profile.json` | bundle | Registration under a different profile version. |
| `aux/bundle-same-anchor.json` | bundle | Two TSA tokens under one trust anchor. |
| `aux/key-event-by-other-key.json` | key-event | A compromise event for the creator key, signed by an unrelated key. |

`negative/` holds 58 broken fixtures; each must produce exactly the codes listed below. `aux/` holds inputs that negatives or results refer to; they are not checked on their own. `build_fixtures.py` rebuilds all three directories deterministically. `check_registration.py` is the checker: standard library only, Python 3.11 or later.

## What the checker does

- **Self-tests.** Ed25519 against RFC 8032 §7.1 tests 1 and 2; the PAE against the first case of `test-vectors/dsse-pae.json` (values written inline).
- **Signatures.** Verifies every envelope signature over the exact payload bytes under the strict rule set of design §10.1: cofactorless; S < L; canonical A and R; A not of small order. Key lookup is by hint only.
- **Statements.** Applies §4: subjects and names; nonce; possession digests recomputed from the artifact; the salted catalogue commitment; the B10 provenance form; claimed time only; the closed time and content key lists.
- **Time evidence** (§6). Target = SHA-256 of the raw signature bytes; roots by `anchorSha256` only; placeholder labelling; RFC 3161 request nonce, policy OID, certificate validity, revocation and reason codes, accuracy from token or policy; OpenTimestamps pending or complete, with the 7,200 s margin; no time for Rekor v2.
- **Verification results** (§10). Recomputes everything from the bundle, the artifact, the key events and the result's policy, and compares field by field:
  - per-signature bounds and quorum by independence group;
  - signer trust with key events (authorized signers, proved time, look-back clamp, `disputed`);
  - the claimed-time comparison.
- **Links and sets.** For the report link: the report digest, statement digest, subject, profile and catalogue opening. For a registration set: nonce freshness.
- **Renderings** (§11). Every line must match an allow-listed template and agree with the result. The fixed sentences are required. Authorship words outside the templates are rejected.
- **Agent fixtures** (§19). A2A card, request and task fields against the `a2a.proto` lists; the profile extension; HTTPS for digests-only and loopback for local-only; no `raw` or `url` parts and no fingerprints on the wire; the presented digest is the signature digest; the witness signature, caller and limits; MCP tool name, annotations and limit sentence; the agent sentence.
- **Wrong-implementation self-test.** Fourteen plausible wrong outputs are built in memory and each must be rejected:
  - the two-root bound taken as the earliest;
  - a co-signer inheriting a bound;
  - key events ignored;
  - the OpenTimestamps margin dropped;
  - roots identified by label;
  - RFC 3161 revocation ignored;
  - a target computed over text;
  - the four authorship renderings;
  - a lenient Ed25519 accepting S ≥ L;
  - a lenient Ed25519 accepting a small-order key;
  - a non-canonical point.
- **Drift.** Every failure code must appear in the design document and have at least one negative fixture.

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
| `neg-authorship-claim-4` | `authorship-claim` + `rendering-unlisted-line` | Rendering adds: Registered first: sum.go belongs to key 18c3eead08646614. |
| `neg-card-notice-missing` | `notice-missing` | Skill description without the limit sentence. |
| `neg-catalogue-does-not-open` | `catalogue-does-not-open` | Wrong opening nonce. |
| `neg-catalogue-not-report-input` | `catalogue-not-report-input` | Opens a registered catalogue that is not the report's reference catalogue. |
| `neg-catalogue-unsalted` | `catalogue-unsalted` | Plain catalogue digest. |
| `neg-cert-validity-ignored` | `result-mismatch` | TSA certificate validity at genTime ignored (W9). |
| `neg-claimed-as-proved` | `claimed-as-proved` | Claimed creation time reported as the earliest bound. |
| `neg-content-on-wire` | `content-on-wire` | Sends the file itself as a raw part to the hosted witness. |
| `neg-duplicate-key` | `duplicate-key` | Duplicate JSON key; unparseable on purpose, so the code is in the file name |
| `neg-envelope-shape` | `envelope-shape` | Wrong DSSE payload type. |
| `neg-evidence-shape` | `evidence-shape` | Malformed genTime. |
| `neg-evidence-target-base64` | `evidence-wrong-target` | Token over the base64 text of the signature, not its raw bytes (A1). |
| `neg-evidence-wrong-target` | `evidence-wrong-target` | Token over the statement bytes, not over the signature. |
| `neg-fingerprints-on-wire` | `forbidden-field` | Sends fingerprints to the hosted witness. |
| `neg-fixture-shape` | `fixture-shape` | Fixture notice removed. |
| `neg-forbidden-field` | `forbidden-field` | Fingerprints in the statement. |
| `neg-hosted-plain-http` | `content-on-wire` | Digests-only witness offered over plain HTTP. |
| `neg-key-bound-misattributed-rendering` | `key-bound-misattributed` | The co-signer is given the first signature's bound (W8). |
| `neg-key-bound-misattributed` | `key-bound-misattributed` | A later co-signature inherits the earlier signature's bound (W8). |
| `neg-key-event-ignored` | `key-event-ignored` | A compromise event covering the bound is ignored; signer still `trusted` (W10). |
| `neg-key-event-shape` | `key-event-shape` | Compromise event without its claimed start. |
| `neg-log-time-claimed` | `log-time-claimed` | Rekor v2 placeholder that claims a time. |
| `neg-mcp-tool-shape` | `mcp-tool-shape` | Registration tool declared closed-world and idempotent. |
| `neg-nonce-invalid` | `nonce-invalid` | All-zero nonce. |
| `neg-nonce-reused` | `nonce-reused` | Nonce reused across two registrations (W4). |
| `neg-notice-missing` | `notice-missing` | Rendering without the two fixed limit sentences. |
| `neg-pending-counted` | `pending-counted` | A pending proof that states a block time. |
| `neg-placeholder-unlabelled` | `placeholder-unlabelled` | Placeholder presented as a real token. |
| `neg-possession-mismatch` | `possession-mismatch` | Possession digest not computed from the content. |
| `neg-predicate-type` | `predicate-type` | Draft-1 predicate type. |
| `neg-profile-mismatch` | `profile-mismatch` | Registered profile differs from the report's. |
| `neg-provenance-shape` | `provenance-shape` | Implementation commit is not an object id (B10). |
| `neg-quorum-miscount` | `quorum-miscount` | The Rekor entry, which has no time, counted as a fourth root. |
| `neg-quorum-same-anchor` | `quorum-miscount` | Two tokens under one CA counted as two roots (W3). |
| `neg-rendering-unlisted-line` | `rendering-unlisted-line` | A harmless line outside the template list is still refused. |
| `neg-report-digest` | `report-digest` | The link names a different report body. |
| `neg-result-mismatch` | `result-mismatch` | An outcome value outside the closed list. |
| `neg-root-not-anchored` | `root-not-anchored` | Root named by a producer-written label instead of a trust anchor (W3). |
| `neg-signature-invalid` | `signature-invalid` | Claimed time edited after signing. |
| `neg-single-verdict` | `single-verdict` | Adds a single 'authentic' verdict. |
| `neg-statement-digest` | `statement-digest` | The link names a different statement. |
| `neg-statement-shape` | `statement-shape` | Unknown predicate field. |
| `neg-subject-mismatch` | `subject-mismatch` | Links the candidate's digest instead of the registered reference. |
| `neg-subject-name` | `subject-name` | A path as subject name. |
| `neg-subject-unsupplied-match` | `result-mismatch` | Reports `match` without the file (W6b). |
| `neg-time-in-statement` | `time-in-statement` | A 'provedAt' written by the registrant. |
| `neg-tsa-nonce-mismatch` | `tsa-nonce-mismatch` | Token nonce differs from the request nonce: a possibly replayed response. |
| `neg-witness-authorship` | `authorship-claim` | Witness statement asserts the caller is the author. |
| `neg-witness-shape` | `witness-shape` | Witness statement without the caller it authenticated. |
| `neg-witness-wrong-digest` | `evidence-wrong-target` | Presents the artifact digest instead of the signature digest. |

## Run

```sh
python3 -I research/drafts/registration-fixtures/build_fixtures.py
python3 -I research/drafts/registration-fixtures/check_registration.py --verbose
git status --short research/drafts/registration-fixtures   # rebuilt files must be unchanged
```
