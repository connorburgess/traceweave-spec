# Lane 2: initial review of Perplexity report

Reviewed 2026-11-18. Original report (local input: `perplexity/02-robustness-attacks.md`; not distributed) preserved byte-for-byte. This initial assessment predates the Google report; see [the subsequent comparison](02-robustness-attacks-comparison.md). It is not adoption into the specification. No new attack experiments were run for this review.

## Assessment

Useful as an attack-harness checklist. Its strongest contributions are separating mark presence from ancestry and attribution, distinguishing zero-query and adaptive attackers, retaining failed attempts, and requiring behavior checks independently of detection scores. It correctly limits transfer of Python/LLM-generation findings to the Go/Rust pilots.

The recommended harness should be built around explicitly specified candidate carriers, not a presumed “behavior-preserving syntactic transformation.” Our [existing feasibility checks](02-carrier-feasibility.md) already show why simple ordering is a weak baseline: formatter survival does not prevent canonicalization from collapsing the encoded states, and side effects or Rust destructors invalidate naive reordering.

## Source verification

- The report attributes *Is The Watermarking Of LLM-Generated Code Robust?* to Cao et al. The [v4 record](https://arxiv.org/abs/2403.17983v4) names Tarun Suresh, Shubham Ugare, Gagandeep Singh and Sasa Misailovic. Its abstract does support the general claim of reduced detection under transformations on generated Python code. Correct the authors and pin the version; it is not direct evidence for a Go/Rust post-hoc marker.
- [Disappearing Ink v2](https://arxiv.org/abs/2507.05512v2) is real. Its abstract supports the conditional distribution-consistency result and reported near-random AUROC for the tested n-gram schemes after obfuscation. This is a scoped negative result, not an impossibility theorem for every code watermark. Full proof assumptions and experiment details have not been independently audited here.
- The apparently inconsistent CodeMark-LLM/CLASP title is a version change, not a fabricated citation: [v1](https://arxiv.org/abs/2510.11251v1) is *Large Language Models Are Effective Code Watermarkers* and calls the method CodeMark-LLM; [v2](https://arxiv.org/abs/2510.11251v2) is CLASP. The report needs explicit version citations for individual results. Its detailed rename/three-transformation figures are not validated by this metadata check.
- The taxonomy citation and truncated ACM survey reference remain unaudited. Internal `[web:N]` tokens are not portable citations; the usable ledger should contain actual links, versions and sections for every material claim.

## Changes needed before implementing the proposed protocol

1. **Language-aware comment removal.** Go build constraints and `//go:embed` directives use comment syntax and affect builds or data inclusion. Rust doc comments become attributes. Treat ordinary comment stripping separately from directive/doc removal, preserve token separation, and record the affected build/documentation contract. References: [Go build constraints](https://pkg.go.dev/cmd/go#hdr-Build_constraints), [Go embed](https://pkg.go.dev/embed), [Rust comments](https://doc.rust-lang.org/reference/comments.html).
2. **Do not label all marked-fragment transplantation false ancestry.** A copied function has real fragment ancestry even in an unrelated host. The false claim is typically whole-artifact origin or ownership. A mark-only reconstruction on independently written code is a different test. Define region-level ground truth for both.
3. **Specify which artifact is being detected.** Source-to-source edits, macro expansion, compilation and binary optimization are different pipelines. Dead-code elimination in a binary does not by itself remove a mark from distributed source. Cross-language ports remain a separate regime.
4. **Record model outputs, not just seeds.** “Deterministic LLM rewrites” is too strong without a demonstrated deterministic runtime. Retain exact outputs, digests, model/build identifiers and all attempts. No model calls are authorized or needed for the first local harness.
5. **Define denominators and invalid-output handling.** Report attack validity rate and evasion among valid outputs separately, plus overall attempts. A compile/test failure is neither a successful behavior-preserving attack nor evidence of detector robustness. Whole-search calibration belongs to lane 3.
6. **Keep trust states separate.** Mark detection linked to a key/catalogue does not authenticate a human owner automatically. Key compromise, re-marking, signature trust and retroactive revocation need lane-4 policy; do not imply old distributed marks can simply be revoked out of existence.
7. **Define collusion concretely.** “Averaging” is not an executable source-code transform without a representation and validity rule. Start with aligned variant comparisons, site selection and valid merges, retaining all failures.
8. **Freeze before evaluating.** Register thresholds, splits and budgets before the held-out run. The report's final “freeze and publish” step should be split into pre-run freezing and post-run reporting. Publication is a separate action; private pilot material must not become public raw logs by default.

## Proposed first harness increment

Use synthetic Go/Rust fixtures only: unchanged marked baseline, unmarked/wrong-mark controls, formatting, canonical normalization, one typed/scope-aware rename, partial fragment extraction, fragment transplantation, and mark-only forgery where the candidate permits it. Preserve all inputs/outputs and label validity, presence and localized ancestry separately. Add composition and bounded adaptive search only after deterministic single-transform behavior is established.

Do not defer the embedded-mark use case merely because fingerprint benchmarks are easier; reuse the harness across mark-only, fingerprint-only and combined experiments. Keep no-op transformations and zero-capacity fixtures visible.

## Questions for the Google comparison

- Does it identify concrete Go/Rust-valid transformations and exceptions rather than generic AST edits?
- Does it distinguish real fragment ancestry from falsely attributing the enclosing host?
- Does it give versioned primary evidence and a usable strategy for normalization/removal?
- Does it define resource budgets, valid-output denominators and detector abstention?

Original report retained unchanged; corrections belong in this review until both reports are reconciled.
