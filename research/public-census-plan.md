# Public-code eligibility census protocol

Proposed 2026-11-21; no corpus has been acquired or evaluated. This is the next bounded step after the [fragment/policy checkpoint](fragment-policy-checkpoint.md), not a benchmark of detection quality.

## Decision

Do the currently reviewed carrier boundaries offer useful sites in ordinary public code, or should we stop pursuing them before adding payload framing? The present synthetic function grammars are unusually narrow. Zero eligible sites is an informative result.

## Freeze before collection

Select two independently maintained public repositories per language, one library and one application each, using an explicit selection rationale. Pin commit hashes and record acquisition date, upstream URL, license file/path/hash, source provenance, included directories and exclusions. Check applicable source and fixture licenses before acquisition or redistribution; publish the manifest and aggregate measurements without copying third-party code into this repository. No private pilot applications. This convenience sample cannot represent all Go or Rust software.

Use source-only inspection. Do not run builds, tests, build scripts, macros, dependency installation or candidate programs. Do not traverse symlinks outside the pinned checkout. Record unreadable files, parser failures and unsupported configurations instead of silently dropping them. Dependencies, generated/vendor code and tests should be reported separately, with primary eligibility results on first-party non-generated implementation files.

Freeze the scanner revision and rule inventory before scanning all four repositories. A later rule change requires a new census version and rerunning the same manifest. Keep this feasibility sample out of any later held-out evaluation set.

## Two distinct measurements

1. **Exact current eligibility:** count sites only where the reviewed grammar and required source/build preconditions can actually be established. Unknown preconditions are unsupported, never assumed safe. Rust's supplied synthetic source-observer boundary will often be unestablished on real repositories; report that explicitly.
2. **Potential structural sites:** separately count syntactic patterns that might motivate a reviewed extension. These are not safely markable sites or available payload capacity. Record which safety proof or analysis is missing.

A scanner may need broader parsing to locate candidate syntax; this does not broaden the carrier's acceptance grammar. Inspect only and never rewrite acquired source.

## Required output

Per repository and language, report total selected files/bytes/functions, successfully inspected units, refusals by reason, exact eligible units, potential-only units, and distribution by file. Include zero-result repositories in every denominator. Preserve file digests and byte offsets locally for reproducibility without redistributing source excerpts.

For truly eligible independent runs, report raw state counts and log2 of their state spaces. Keep factorial order capacity separate from binary literal/name capacity. Do not add overlapping, correlated or mutually exclusive sites. Distinguish ideal raw capacity from zero currently demonstrated authenticated payload bits; synchronization, framing, redundancy and security overhead remain unimplemented. Report counts before and after applicable formatter/normalization rules analytically only where justified by the tested mapping; do not label predictions as measured survival.

Manually audit a fixed small sample of accepted candidates and each refusal category, including at least one Unicode-offset case if available. Check scanner counts against independent file/function inventory. Store structured counts, rule versions and reproducible commands; redact nothing silently and retain failure reasons.

## Exit and next decision

Stop after the four pinned repositories and audit. If no exact sites qualify, report that result and propose at most one narrowly justified grammar extension or recommend rejecting the carrier. If sites qualify, assess whether capacity is distributed usefully before designing identity framing. This census cannot establish transformation robustness, false-alert rates, copyright conclusions or applicability to text, images or audio.
