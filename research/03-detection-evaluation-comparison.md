# Detection evaluation comparison

Reviewed 2026-11-18. Originals remain unchanged in ignored local inputs perplexity/03-detection-evaluation.md and gemini/03-detection-evaluation.md. This is a selective source check, not a complete bibliography audit.

Google adds external literature leads and correctly states the zero-event formula that Perplexity misprinted. Its mandatory conformal/hybrid design, universal carrier minimums and binary-survival requirements are unsupported. Retain the statistical questions without adopting those prescriptions.

## Statistical findings

- [Angelopoulos and Bates v6](https://arxiv.org/html/2107.07511v6), sections 1, 3 and 4, distinguish marginal coverage from conditional guarantees. Exchangeability does not follow from identical marginal distributions or repository-disjoint splits alone. Freeze scores independently of calibration; evaluate the complete query including candidate/key selection. Pooled Go/Rust calibration does not automatically control each language's errors. Distribution shift and adaptive queries need additional treatment.
- A null-score rank threshold uses ceil((n+1)(1-alpha)), explicit ties/strictness and an infinite threshold when the rank exceeds n. Google's quantile expression can exceed 1. Resolution near 1/(n+1) does not establish eight carrier bits, sixty token positions or a twenty-five-token minimum. Calibration size, capacity and power are distinct.
- Replacing n with a cluster count in a binomial formula is not an automatic exact file-level correction. Define a cluster-level outcome, such as any false alert in one independently sampled repository query, and state population/sampling assumptions. [NIST's exact-binomial procedure](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm) does not remove these assumptions. Confidence bounds are not guaranteed true specificity.
- FWER and FDR address different error objectives. Expected false-discovery fraction does not generally control the probability of any false hit in a query. Candidate filtering belongs inside evaluation; nominal expected-key significance requires a valid null/test.
- Syntax alone does not establish positive covariance, stationarity or applicability of the report's infinite autocorrelation-sum effective sample size. Specify a model or calibrate actual query outcomes.
- Google's PPV example mixes watermark presence with unauthorized reuse. Keep rights labels separate. A finite held-out rate above alpha does not by itself disprove a marginal theorem; use a predeclared uncertainty-aware acceptance procedure.

## Evidence and implementation findings

- [Winnowing](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf), section 3, guarantees a shared selected k-gram for matching substrings of length at least w+k-1, not w tokens. This is exact matching in a representation, not historical derivation. No blanket public-domain implementation license follows.
- [CRUSTPairs](https://arxiv.org/abs/2611.11711) pairs C/Rust solutions to shared problems. Independent authorship/no copying needs per-item evidence before using these as negative controls.
- The proposed Traceweave hybrid has no demonstrated 100% rename survival, independent channels or native implementation. Its table mixes proposals and established capabilities. Paper-specific percentages, latency and licenses still require verification.
- Compilation does not erase distributed source. Binary recovery is a separate profile. Reject mandatory unavoidable binary side effects: they are unnecessary for the source pilot and conflict with behavior preservation.
- Go's proposed command includes -l, which [disables inlining](https://pkg.go.dev/cmd/compile); -m reports optimization decisions. [Cargo release](https://doc.rust-lang.org/cargo/reference/profiles.html) does not automatically configure cross-crate full LTO. Go has no while keyword. Define language-valid transformations.
- Invented private paths, commits and digests in the example manifest are not corpus evidence. The 1,000-module/4.5 CPU-hour plan is unexecuted. Keep public/synthetic fixtures first.
- Reject the 0.5% marking-induced test-failure allowance. Failed attempted marks need rollback/refusal; passing tests remains bounded evidence.
- The proposed Unmarked verdict contradicts its own earlier caution. Use configuration-scoped not_detected, distinct from inconclusive/error, signature validity and trust. P-values are not ownership confidence. Do not adopt invented repository section numbers.

## Effect on the Go/Rust plans

Continue [raw-state extraction and refusal experiments](lanes/checkpoint.md) before keyed identity or rare-error claims. Later compare empirical query-level thresholds with conformal null-score calibration if its assumptions fit. Record separate language evaluations, family grouping, rank/tie rules, catalogue/window/key counts, abstentions and shift limitations. No mandatory calibration algorithm, universal carrier floor, binary-survival requirement or normative schema change is adopted.
