# Fragment recovery and verification policy checkpoint

Measured and coordinator-reviewed 2026-11-21. This follows the [initial experiment checkpoint](experiment-checkpoint.md). These are synthetic feasibility results, not a normative profile or a calibrated identity detector.

## What the experiments establish

| Lane | Reviewed result | Interpretation |
| --- | --- | --- |
| [Go](lanes/go-fragment-results.md) | 24 main queries: 10 localized raw states and 14 abstentions; 30 definition spans checked; 2 additional own-reference controls and 12 guards; 22 compiled return checks | Complete narrow functions can be relocated; incomplete and ambiguous matches abstain |
| [Rust](lanes/rust-fragment-results.md) | 72 queries: 24 localized raw states and 48 abstentions; 60 localized symbols; 21 regression tests; 156 compiled checks across two build profiles | Closed synthetic hosts support exact original-byte localization, with explicit context and grammar limits |
| [Signing policy](lanes/signing-policy-results.md) | 126 outcomes: 72 shared-policy checks, 50 native commitment outcomes, 4 reference framing counterchecks | Pinned native DSSE implementations agree under the tested common policy; independent Go/Rust commitment implementations reproduce exact-byte vectors |

The coordinator independently reran all six Go tests, the Rust fragment matrix and 21 regressions, and the signing policy harness under OS network denial. Rust generated 66 complete hosts with 78 output checks per build profile. The signing harness confirmed network denial and preservation of the prior result snapshot. The cases differ between languages; neither recovery fraction is a comparative accuracy score.

## Decisions supported by the evidence

1. Keep raw-state recovery, content alignment, signature validity and signer trust as separate results. Both language experiments decode same-context signal transfers. A readable signal, matching context label or valid signature alone does not prove authorship or ancestry.
2. Keep ambiguity explicit. Both implementations collect matching anchors before decoding; neither chooses a convenient first match. Rust's context label is a synthetic constraint, not authenticated context.
3. Retain the complete-function boundary for these prototypes. Partial runs can contain surviving symbols yet fail the current alignment rule. Filling gaps from the reference would invent evidence. No general fragment recovery has been demonstrated.
4. Do not invest in identity framing for these carriers yet. Earlier cheap canonicalization erased every nonzero distinction tested. Useful eligibility and realistic capacity remain unknown. A larger payload would not fix removal or transplant resistance.
5. Keep the signing policy experimental. Strict duplicate-key parsing and key-hint normalization are implemented in a shared Python layer, not independently in both languages. Commitments are independently framed in Go and Rust. Neither fact completes the broader production verification milestone.

## Next bounded research step

Use the [public eligibility census protocol](public-census-plan.md) to decide whether a broader safe syntax subset is worth implementing. Report zero useful capacity if the exact narrow grammar has none; do not expand the grammar merely to improve a result. Then decide whether to reject these carrier families, develop a separately reviewed extension, or prioritize the extracted-fingerprint baseline. Corpus evidence must precede capacity/identity claims, with separate gates for other media.

No private application, production key, timestamp service, normative wire format, diagram, commit or push was involved. Full-query false alerts, held-out recall, authenticated identities and robust multi-media recognition remain unmeasured.
