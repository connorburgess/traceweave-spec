# Registration record fixtures (illustrative)

These fixtures belong to the [registration record draft](../registration-record.md). They are research material, not test vectors, and nothing in `validate` runs them.

**What these are not.** No time-stamping authority, OpenTimestamps calendar, transparency log or witness produced any of them. Every time evidence is a **placeholder** that says so in its `notice` and in its `token` text, and the checker rejects one that does not. Times in them are invented. The signing key is a **public test-only key** derived from a fixed label in `build_fixtures.py`, and the nonces are derived the same way; never use either for anything real. The catalogue nonce is the public synthetic nonce of `test-vectors/commitment.json`. Provenance commits are all zeros, as in `example-report.json`. A fixture registers nothing and proves nothing.

The data is real repository data: the artifact is `sum.go` (vector `mv-go-sum` of `test-vectors/matching/extraction-go.json`), its catalogue is the reference catalogue of matching vector 1, and the report is `test-vectors/matching/example-report.json`.

## Files

| Path | Content |
| --- | --- |
| `fixtures/statement.json` | The registration statement before signing (§4) |
| `fixtures/bundle-two-roots.json` | Signed statement (real Ed25519 over the DSSE PAE, test key), with RFC 3161, OpenTimestamps (complete) and Rekor v2 placeholders |
| `fixtures/evidence-rfc3161.json` | RFC 3161 placeholder over the bundle's signature digest |
| `fixtures/evidence-opentimestamps-complete.json` | Upgraded OpenTimestamps placeholder |
| `fixtures/evidence-opentimestamps-pending.json` | OpenTimestamps placeholder before upgrade: no time |
| `fixtures/evidence-rekor-v2.json` | Rekor v2 placeholder: inclusion only, no time |
| `fixtures/evidence-cosigned-checkpoint.json` | Witness-cosigned checkpoint placeholder |
| `fixtures/verification-result.json` | The closed outcomes of §10 for the bundle and `sum.go`, with `simulated: true` (placeholders assumed valid) |
| `fixtures/report-link.json` | Ties `example-report.json` to the registration, with a catalogue opening (§9) |
| `fixtures/rendering.json` | User-facing text with the §11 sentences |
| `fixtures/key-event-rotation.json` | A signed, time-stamped key rotation (§8) |
| `fixtures/a2a-card-hosted-witness.json`, `fixtures/a2a-card-local-registrar.json` | Illustrative A2A 1.0 Agent Cards (§19.4); **not validated against a published A2A schema** (none is committed upstream), checked against the field lists of `a2a.proto` at `v1.0.1` |
| `fixtures/a2a-request-witness.json`, `fixtures/a2a-task-witness.json` | Witness request (one data part with the signature digest) and completed task; the witness statement is signed with a second public test-only key; its RFC 3161 evidence is a placeholder |
| `fixtures/mcp-tool-register.json` | Illustrative MCP 2026-07-28 Tool for the local route; validated once against MCP `schema.json` `$defs/Tool` (§19.4) |
| `fixtures/rendering-agent.json` | Text for a registration made through an agent, with the agent sentence |
| `negative/` | 38 broken fixtures; each changes one thing and must produce exactly the code in `expect.code` (for `neg-duplicate-key.json`, which cannot be parsed, the code is in the file name) |
| `build_fixtures.py` | Rebuilds both directories deterministically |
| `check_registration.py` | The checker, standard library only, Python 3.11 or later |

## What the checker does

- Runs a self-test of its pure-Python Ed25519 against RFC 8032 §7.1 tests 1 and 2, and of the PAE against the first case of `test-vectors/dsse-pae.json` (values written inline).
- Verifies each envelope signature over the exact payload bytes; parses payloads strictly (duplicate keys rejected).
- Applies the statement rules of §4: subject form and names, nonce, possession digests (recomputed from `sum.go`), the salted catalogue commitment, B10 provenance form, claimed time only, no fingerprints or other content.
- Checks each time evidence's form, placeholder labelling, root kind, and that its target is the SHA-256 of the signature it names; computes `notAfter` per §6.2.
- Recomputes the full verification result from the bundle, the artifact and the result's policy, and compares it field by field.
- For the report link: recomputes the report's `bodySha256`, the statement digest, the subject–pair link, the profile, and opens the catalogue commitment.
- For the rendering: the three required sentences, no authorship or single-verdict wording, and no claimed time shown without "claimed".
- For the agent fixtures (§19): A2A card, request and task fields against the `a2a.proto` lists; the profile extension and its `wire` value; HTTPS for digests-only and loopback for local-only; no `raw` or `url` parts and no fingerprints on the wire; the presented digest is the signature digest; the witness signature, its caller and its limit list; MCP tool name, annotations and limit sentence; the agent sentence in agent renderings.
- Checks that every failure code appears in the design document.

Four codes have no negative fixture yet: `catalogue-not-report-input`, `profile-mismatch`, `report-digest` and `fixture-shape`. They are checked on the positives.

## Negative fixtures

| File | Must produce |
| --- | --- |
| `neg-subject-mismatch` | link names the candidate's digest, not the registered subject |
| `neg-evidence-wrong-target` | token over the statement bytes instead of the signature |
| `neg-claimed-as-proved` | claimed creation time reported as the proved bound |
| `neg-authorship-claim` | rendering says the registration proves authorship |
| `neg-notice-missing` | rendering lacks the "does not show" sentences |
| `neg-single-verdict` | result adds `authentic: true` |
| `neg-signature-invalid` | claimed time edited after signing |
| `neg-placeholder-unlabelled` | placeholder presented as a real token |
| `neg-pending-counted` | pending OpenTimestamps proof states a block time |
| `neg-log-time-claimed` | Rekor v2 evidence claims a time |
| `neg-catalogue-unsalted` | plain catalogue digest in the statement |
| `neg-forbidden-field` | fingerprints in the statement |
| `neg-nonce-invalid` | all-zero nonce |
| `neg-subject-name` | path as subject name |
| `neg-time-in-statement` | `provedAt` written by the registrant |
| `neg-possession-mismatch` | possession digest not computed from the content |
| `neg-predicate-type` | wrong predicate type |
| `neg-provenance-shape` | implementation commit `main` |
| `neg-quorum-miscount` | two tokens from one TSA counted as two roots |
| `neg-result-mismatch` | outcome value outside the closed list |
| `neg-catalogue-does-not-open` | wrong opening nonce |
| `neg-statement-digest` | link names another statement |
| `neg-key-event-shape` | rotation without a successor key |
| `neg-evidence-shape` | RFC 3161 placeholder without accuracy |
| `neg-envelope-shape` | wrong DSSE payload type |
| `neg-statement-shape` | unknown predicate field |
| `neg-duplicate-key` | duplicate JSON key |
| `neg-content-on-wire` | file sent as a `raw` part to the hosted witness |
| `neg-fingerprints-on-wire` | fingerprints in a witness request (`forbidden-field`) |
| `neg-witness-wrong-digest` | artifact digest presented instead of the signature digest (`evidence-wrong-target`) |
| `neg-a2a-shape` | `protocolVersion` `1.0.1` |
| `neg-card-notice-missing` | skill description without the limit sentence |
| `neg-hosted-plain-http` | digests-only witness over plain HTTP (`content-on-wire`) |
| `neg-witness-authorship` | witness statement asserts an author |
| `neg-witness-shape` | witness statement without the authenticated caller |
| `neg-mcp-tool-shape` | registration tool declared closed-world and idempotent |
| `neg-agent-notice-missing` | agent rendering without the agent sentence |
| `neg-agent-authorship` | rendering says the agent created the content |

## Run

```sh
python3 -I research/drafts/registration-fixtures/build_fixtures.py
python3 -I research/drafts/registration-fixtures/check_registration.py --verbose
git status --short research/drafts/registration-fixtures   # rebuilt files must be unchanged
```
