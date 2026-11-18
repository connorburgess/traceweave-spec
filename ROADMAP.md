# Traceweave roadmap

Status: proposed delivery plan, 2026-11-18. The existing 0.1.0-draft.1 scaffold validates record shapes and synthetic vectors. It does not detect reuse or verify signatures yet.

Start with [use cases](docs/use-cases.md), then [implementation patterns](docs/implementation-patterns.md) and the [source register](docs/sources.md). These planning documents do not change normative wire formats.

## Core tracks

Embedded marking and detection are a first-class research track alongside extracted fingerprint matching. Provenance verification supports both. A baseline matcher is useful for comparison, but does not satisfy the embedding use case. No marking method is standardized yet.

## Delivery sequence

| Milestone | What becomes possible | Deliverables | Exit gate |
| --- | --- | --- | --- |
| M0 — Explain and bound | A maintainer understands the use cases and remaining uncertainty | Use cases, source register, patterns, example matrix, decision backlog | Each proposed capability has an input, observable output, limit, and verification plan |
| M1 — Freeze one code experiment | Two runs extract identical features from identical inputs | One language/profile proposal; exact configuration bytes; token serialization; spans; catalogue and report schemas; positive and negative vectors | Independent reruns agree byte-for-byte; unknown profiles and malformed inputs fail explicitly; every normative requirement maps to a check |
| M2 — Local comparison | A maintainer finds candidate fragments without uploading source | Reference extractor, local catalogue, matcher, localized reports, synthetic walkthrough | Exact and partial-copy cases are localized; unrelated/common-code controls are reported honestly; no network required; deterministic results with recorded config |
| M2E — Embed and detect | A creator can test recognition of deliberately marked content | One experimental embedding/detection profile; private mark record; original/marked digests; quality checks; transformation and attack fixtures | Reproducible embedding with recorded test randomness; unmarked/wrong-mark controls; removal and transplantation tests; functionality/quality gate; detection failures reported honestly |
| M3 — Measure usefulness | A reviewer can assess which transformations are detected and at what cost | Licensed corpus manifest; grouped data splits; frozen thresholds; reproducible benchmark and failure report | Held-out recall by transformation/fragment size, false alarms per repository search, abstention, candidate volume, runtime and memory reported with limitations |
| M4 — Verify evidence | A recipient independently checks a signed evidence record under their own trust policy | Library-based DSSE signing/verification; in-toto adapter; trust policy; optional timestamp adapter; negative cryptographic vectors | Two implementations agree on bytes and verdicts; tampering, untrusted keys, malformed payloads and subject mismatches are distinguished; commitment/disclosure design receives independent review |
| M5 — Candidate release | Another implementer can build against a coherent version | Versioned spec, schemas, fixtures, conformance matrix, migration notes, reproducible demo | No undocumented MUSTs; advertised features have interoperability evidence; unresolved security/measurement limits are explicit |

Order: M0 → M1 → parallel M2 and M2E experiments → M3 → M5. Both experiments are core scope; a release that omits embedding must explicitly say so. M4 can follow M1 independently, but is required before a release claims cryptographic verification. A detector-only experimental release can remain explicitly unsigned. No dates or detection guarantees are promised before the baseline is measured.

## Next work, in order

1. **TW-01: Choose the first deployment.** Use UC-1, UC-2 and UC-6 in the use-case guide. Inventory intended languages and artifact types using authorized local repositories; publish only a synthetic inventory. Proposed starting scope: source files in one language, local comparison, no remote resolver. Acceptance: a short decision record names the language, supported syntax, artifact boundary, excluded generated/vendor files, and search unit. Language selection remains open until that inventory.
2. **TW-02: Specify extraction completely.** Define encoding, parser/grammar revision, failure handling, token channels, hash bytes, k/window parameters, rightmost-minimum ties, duplicates and byte coordinates. Acceptance: hand-checkable vectors for empty, short, Unicode, malformed, repeated and equal-minimum inputs. Parameters begin as experimental choices, not accuracy promises.
3. **TW-03: Define catalogue and report contracts.** Add schemas with profile/config binding and artifact digests. Separate comparison from exact/signature/trust/time results. Acceptance: schemas, valid examples, rejection fixtures and version notes move together.
4. **TW-04: Build the smallest end-to-end reference.** Implement extract → catalogue → compare → localized report using the existing Python tooling where practical. Acceptance: a documented offline synthetic walkthrough is reproducible, with no private material in the checkout.
5. **TW-05: Establish an evaluation corpus.** Record provenance, permitted redistribution, split groups and transformations; retain a test set that tuning never sees. Acceptance: evaluation protocol and corpus manifest are frozen before threshold selection is evaluated on held-out data.
6. **TW-06: Add cryptographic verification.** Choose maintained upstream libraries and pin versions after checking their current interfaces/security notes. Acceptance: the M4 negative tests and interoperability gate pass; schema validation never stands in for verification.
7. **TW-08: Research and prototype embedding/detection.** Begin alongside TW-02. Compare candidate marking methods against the intended language and transformations; record primary sources before choosing a method. Specify mark payload/identity, any key and randomness handling, embedding capacity, detector access assumptions, output localization, and transplant limitations. Acceptance: M2E fixtures plus quality/performance checks; separate mark-only, fingerprint-only and combined evaluation at the same false-alarm budget. No callbacks, planted defects or hidden telemetry.
8. **TW-07: Review the release claims.** Map each README claim to a fixture, benchmark or external review. Acceptance: unmeasured claims remain goals and incompatible changes receive new identifiers.

These are local backlog IDs, not published GitHub issues. M0 is the planning package; TW-01 onward are future implementation work.

## Later, with separate gates

- Structural/semantic matching: compare against the token baseline on the same corpus and error budget before adopting it.
- Keyed feature selection for extracted fingerprints: evaluate separately from embedding. Selecting secret features does not embed a mark.
- Agent skill: wrap stable local commands; keep private catalogues and keys out of model context.
- Text, image, audio and binary profiles: independent use cases, extraction contracts and modality-specific benchmarks.
- Resolver: only after a query/disclosure threat model and leakage evaluation. Public registration stays optional.
- C2PA: first write a mapping and interoperability fixtures; no compatibility claim from shared terminology.

## How work is accepted

Use one reviewable change per decision or capability. Explain the use case, source support, normative delta, fixtures, measured result and known failures. Update [conformance](spec/conformance.md) whenever supported behavior changes. Run the repository validator and tests. Keep source revisions and implementation dependencies reproducible. Record disagreements as decisions with alternatives and revisit conditions.

Open choices: first language; representative authorized corpus; operational false-alarm budget; supported trust/key distribution model; and the second implementation/reviewer. None prevents completing this plan, and none should be guessed into a stable standard.
