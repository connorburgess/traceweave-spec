# Conformance matrix and migration notes — 0.1.0-draft.1

Status: release inventory for independent M5.5 review, 2026-11-26. No M5 gate is marked met by this document. Levels are defined in [spec/conformance.md](../../spec/conformance.md): L1 record structure, L2 commitment opening, L3 attestation verification, L4 profile reproduction, L5 detection evaluation. Levels describe features, not a blanket certification of a product.

## Evidence scope and implementations

Go and Rust refer to the independent implementations in `connorburgess/traceweave`, not the Python fixture checkers here. Recorded core evidence is the [core review](../../research/reviews/core-gates-m1-m2-review.md) and [implementation review](../../research/reviews/implementation-merge-i2-review.md). Later implementation review paths and pins are recorded in [ROADMAP.md](../../ROADMAP.md): TS/TXT `8011b6d`, PY `b5d981c`, WASM `51f29d7`, registration `5b9a881` with spec pin `9cf78ee`. These are evidence snapshots, not claims about a newly fetched latest build. No implementation build or held evaluation was run for this document.

**Recorded** means the cited repository record reports passing applicable fixtures. **Draft** means specified/research only. **Unverified** means this repository has no sufficient conformance evidence. Shelf static app is an explicitly listed implementation target; neither its code nor a pinned conformance review is present here, so every capability is unverified. Browser WASM parity establishes core function bytes; it does not establish all Shelf UI flows or native filesystem/build behavior.

## Feature × level × implementation

| Feature / profile | Level | Go | Rust | WASM | Shelf static app | Exact evidence / limitation |
| --- | --- | --- | --- | --- | --- | --- |
| Restricted statements and extraction records | L1 | Recorded | Recorded | Recorded parity | Unverified | [record vectors](../../test-vectors/matching/records.json); core review; WEB.1 |
| Salted catalogue commitment / changed openings | L2 | Recorded | Recorded | Recorded parity | Unverified | [commitment fixture](../../test-vectors/commitment.json); M4.2 / M4.4 |
| DSSE / registration-draft-5 signatures and exact subjects | L3 | Recorded | Recorded | Recorded parity | Unverified | [registration](../../test-vectors/registration/README.md); M4.3 / M4.4 |
| Trust policy, key events, per-signature time and revocation outcomes | L3 | Recorded | Recorded | Recorded parity | Unverified | Registration fixtures; [policy](../../spec/trust-policy.md); M4.4; test roots only |
| Optional offline RFC 3161 / OTS evidence | L3 | Recorded fixture scope | Recorded fixture scope | Recorded fixture scope | Unverified | [adapter decision](../decisions/timestamp-adapter-decision.md); no live-service compatibility claim |
| in-toto minimal-core and registration adapter | L3 | Recorded | Recorded | Recorded parity scope | Unverified | [4 accept / 26 reject](../../test-vectors/intoto-adapter/README.md); M4.4 / M4.5 |
| `tw1-` references, registration/report links and claim-safe renderings | L3 | Recorded | Recorded | Recorded parity scope | Unverified | Registration fixtures; M4.4; no authorship or chronology from a reference |
| `go-tokens` / `draft-1` extraction | L4 | Recorded | Recorded | Recorded | Unverified | [Go vectors](../../test-vectors/extraction/go.json); core review; WEB.1 |
| `rust2024-tokens` / `draft-1` extraction | L4 | Recorded | Recorded | Recorded | Unverified | [Rust vectors](../../test-vectors/extraction/rust.json); core review; WEB.1 |
| `ts-tokens` / `draft-1` extraction | L4 | Recorded | Recorded | Recorded | Unverified | [TS vectors](../../test-vectors/extraction-typescript/ts.json); TS.3 / WEB.1 |
| `py-tokens` / `draft-1` extraction and empty spans | L4 | Recorded | Recorded | Recorded | Unverified | [Python vectors](../../test-vectors/extraction-python/py.json); PY.3 / WEB.1 |
| `text-plain` / `draft-1` exact/folded/skeleton channels | L4 | Recorded | Recorded | Recorded | Unverified | [text records](../../test-vectors/extraction-text/records-text-plain.json); TXT.3 / WEB.1 |
| Catalogue building / validation for registered profiles | L4 | Recorded | Recorded | Recorded | Unverified | [record/catalogue vectors](../../test-vectors/matching/records.json); registered-profile acceptance does not require that implementation to extract it |
| Matching, containment, similarity, suppression, caps and abstention | L4 | Recorded | Recorded | Recorded | Unverified | [matching vectors](../../test-vectors/matching/matching.json); core review; WEB.1 |
| Review packets / candidate-generation records | L4 | Recorded core scope | Recorded core scope | Recorded catalogue/matching scope; separate record APIs unverified | Unverified | [review packets](../../test-vectors/matching/review-packets.json), [candidate generation](../../test-vectors/matching/candidate-generation.json); M2.7 / M2.9 |
| Native private output handling and stamped report provenance | L4 integration | Recorded native review scope | Recorded native review scope | Not applicable to native filesystem/build interface | Unverified | Implementation I2 review; output body parity does not test permissions, cleanup or build provenance |
| `tsx-tokens` / `text-markdown` extraction | L4 draft | Unsupported Stage 1 | Unsupported Stage 1 | Unsupported Stage 1 | Unverified | [TS profile](../../profiles/typescript.md), [text profile](../../profiles/text.md); draft fixtures do not imply supported extraction |
| Held-out detection and false-alarm usefulness | L5 | Held / unmeasured | Held / unmeasured | Unmeasured | Unverified | M3.1–M3.6 open; no evaluation run authorized here |
| Still-image perceptual fingerprints / marks | No promoted L4 claim | Draft research | Draft research | Unverified | Unverified | IMGF synthetic results; IMG finding aid only |
| C2PA mapping / audio / video / binary perceptual matching | No promoted conformance claim | Draft/scoping | Draft/scoping | Unverified | Unverified | C2PA.3 no compatibility; exact-byte registration is independent of perceptual support |
| Embedded marking; resolver / hosted witness / live timestamp submission | No included conformance feature | Deferred | Deferred | Deferred | Unverified | M2E.0 omission; REG.3 / SK.5 / RES owner-gated |

## Versioned specification summary

The release identifier `0.1.0-draft.1` does not replace individual wire versions. Preserve all of these independently:

| Contract | Identifier / authoritative source |
| --- | --- |
| Minimal core predicate | `0.1.0-draft.1`; [statement schema](../../schemas/statement.schema.json) and [attestations](../../spec/attestations.md) |
| Code extraction configuration | `traceweave-token-winnow-draft-1`; [extraction §10](../../spec/extraction.md) |
| Text extraction configuration | `traceweave-text-winnow-draft-1`; [text profile](../../profiles/text.md) |
| Profile identity | Exact `id`, `version`, `configSha256` triple; `rust2024-tokens` is the wire id, not shorthand `rs-tokens` |
| Extraction record | `traceweave-extraction-record-draft-1`; [record schema](../../schemas/record.schema.json) |
| Catalogue / report / companion records | Preserve each version field from [catalogue/report contract](../../spec/catalogue-report.md) and its canonical [schemas](../../schemas/README.md); do not infer a shared version from the release label |
| Registration family | `traceweave-registration-draft-5` and distinct bundle, evidence, verification, link, rendering, key-event, set and equivalence `draft-5` identifiers; [registration record](../../spec/registration-record.md) |
| Trust policy and timestamp material | Verifier-local pinned roots, groups, checkpoint, revocation data and policy; not producer-selected authority |

## Migration and compatibility rules

1. **Pin the whole contract.** Record the specification commit, applicable `spec/`, `profiles/`, `schemas/` and vectors, implementation commit and supported conformance levels. Preserve exact configuration bytes, `configSha256`, profile versions, input bytes/digests and canonical output fixtures. Fixture checker success alone is not a production verifier claim.
2. **No silent reinterpretation.** A change to tokenization, Unicode tables, folding, hash framing, channels, offsets, canonical serialization or matching semantics that changes any frozen output needs a new contract/profile version and configuration digest. Keep old vectors to test old behavior; never recalculate old expected bytes to disguise an incompatible algorithm change. Unknown profile/version combinations are rejected. TSX and Markdown drafts remain separate from frozen Stage 1.
3. **Promoted paths.** The [promotion map](../../research/promotion-map.md) records draft-to-`spec/`, `profiles/`, `schemas/` and `test-vectors/` moves. A path-only move is not a wire migration. Canonical schemas live in `schemas/`; do not keep a second divergent copy under matching vectors. JSON Schema checks structure; the checkers enforce byte framing, ordering, digest binding and semantic rules.
4. **Minimal core versus registration.** The minimal `0.1.0-draft.1` commitment predicate and registration-draft-5 are distinct adapter forms, not interchangeable schemas. Select by exact payload type/predicate/version and preserve signed decoded bytes. Do not rewrite an old signed payload to upgrade it; create a new signed record under the new version and retain the old one. Regenerate `tw1-` references and report links when the bound statement/report bytes change.
5. **Private retained material.** Copy catalogue bytes verbatim, not through a JSON serializer; retain private nonces and local time/trust evidence outside source trees. A reserialized catalogue can have equivalent JSON yet fail the original commitment. Do not import test fixture keys/roots into production trust. Public disclosure, live timestamp submission and hosted resolution are separate actions.
6. **Revalidate on upgrade.** Run `tools/validate.py`, `--links-all`, unit tests and hygiene with pinned development dependencies, then reproduce the applicable positive and negative vectors in each implementation. Separately audit behavior outside output bytes (resource bounds, nonce APIs, side channels, diagnostics, native outputs, UI claims). M5 requires independent review, and M5.3 independent offline demonstration; neither is supplied by this author inventory.
