# Synthetic experiment checkpoint

Executed and reviewed 2026-11-18. The coordinator reviewed the implementations, requested fixes for malformed Rust array acceptance and additional signed-payload parsing controls, and independently reran all three harnesses. This completes the bounded milestone following [initial discovery](discovery-checkpoint.md). It does not validate a production marking scheme.

## Measured results

| Experiment | Clean result | Deliberate failure or compatibility limit |
| --- | --- | --- |
| [Go carriers](lanes/go-carrier-results.md): declaration order and local names | 62/62 completed raw states recover and survive gofmt; 248 compiled return-value checks pass | Normalization resets all 55 nonzero states; direct-return rewriting removes all 62 carrier instances |
| [Rust carriers](lanes/rust-carrier-results.md): declaration order and literal spelling | 62/62 completed raw states recover after actual rustfmt rewrites; 372 compiled checks pass across debug/optimized builds | Normalization resets all 55 nonzero states; malformed syntax and unsupported inputs refuse unchanged |
| [Signing interoperability](lanes/signing-interop-results.md): pinned Go and Rust DSSE libraries | 66 expected outcomes pass across four producer/consumer combinations under OS network denial | Native duplicate-key and unsigned key-hint handling differ; strict application policy remains necessary |

The carrier counts include already-matching state-zero sources: seven per language. Those demonstrate decoding, not intentional insertion. The 55 nonzero states per language are reset to zero rather than producing parser erasures. State sweeps are dependent synthetic examples, not independent evidence for rare false-alert rates. No net authenticated payload capacity or real-code coverage was measured.

The signing experiment authenticates the exact existing 762-byte single-subject statement. Separate controls cover signer trust, candidate digest mismatch, correctly signed duplicate-key payloads and the existing full commitment opening. The commitment check still uses Python; it is not a second independent Go/Rust commitment implementation. Library dependency downloads occurred before the network-denied verification run. Public test-only seeds are fixtures, not deployable keys.

## Decisions supported

Keep these carriers as weak, reproducible baselines. They make the insertion/extraction mechanics and refusal boundaries testable, and expose inexpensive removal. Their successful clean recovery does not justify selecting them for adversarially robust marking.

Retain the existing normative formats. The bare-envelope experiment supplies concrete compatibility evidence for one algorithm and payload, without requiring a new signature format, dual-subject schema, timestamp service or public registry. Parser and hint differences should become explicit adapter decisions before a production verifier is proposed.

Initial Go/Rust experimentation remains a starting point for eventual multiple-media profiles. These source-level results establish nothing about text, images, audio or compiled binaries.

## Next decision

The next useful increment is fragment/alignment and signal-transplant controls on synthetic fixtures, followed by a small explicitly authorized public-code capacity census. Define localization and ambiguity outcomes before identity framing or a blind detector. Separately, decide application parser/key-hint policy and cross-language commitment vectors before optional timestamp integration. Neither stronger carriers nor these extensions are implemented by this milestone.

Remaining gaps: useful-code eligibility, independently reviewed broader transformation safety, authenticated identity/context framing, partial-copy recovery, transplantation resistance, calibrated full-query errors and production key/trust lifecycle. A decoded raw state is not evidence of ownership or ancestry.

## Verification

Coordinator reruns passed: Go's four top-level tests; Rust's full experiment with 186 compiled checks in each of two profiles; the network-denied 66-outcome signing harness; repository validator and all six contract tests. Local Markdown links and whitespace were checked. Source review found and fixed the Rust list-parser issue before final verification. These are bounded checks, not a security audit.

No normative format, private application, diagram or production credential was changed. No commit or push is part of this milestone.
