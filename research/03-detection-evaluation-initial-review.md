# Detection evaluation: initial review

Reviewed 2026-11-18. Perplexity's original is preserved unchanged as the ignored local input `perplexity/03-detection-evaluation.md`. Google comparison pending. This review does not adopt a result schema or claim executed detector benchmarks.

## Assessment

Useful as a design checklist, weak as an independent literature review. The report preserves the embedded-mark objective, separates error units, groups related versions into splits, freezes thresholds and compares components under an operational budget. However, its source ledger contains only Traceweave documents, with nonportable `[web:N]` citations. The repository states requirements; it does not independently validate the statistical methods proposed to satisfy them.

`main` plus a draft version is not a reproducible repository revision. The report also says first-language selection remains open while elsewhere recognizing the Go/Rust pilot decision. Pin an actual commit and distinguish historical from current state.

## Corrections before implementation

### 1. The zero-event confidence formula is wrong as written

For zero events in n independent, identically distributed Bernoulli trials, the one-sided upper bound at confidence 1-alpha is:

```text
p_upper = 1 - alpha**(1/n)
p_upper ≈ -ln(alpha)/n
```

This follows by solving `(1-p_upper)**n = alpha`; see [NIST's exact-binomial confidence procedures](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm) and [confidence-interval construction](https://itl.nist.gov/div898/handbook/prc/section2/prc241.htm). Distinguish one-sided alpha from the alpha/2 used for each tail of a two-sided interval.

The report instead prints `-ln(1-gamma)/n` at confidence `1-gamma`. For gamma=0.05 and n=100,000 that yields approximately 0.000000513, whereas the correct exact upper bound is approximately 0.0000299569. Its numerical example of approximately 0.00003 is correct; its general formula is not. Calculations checked locally. Zero is a valid observed sample rate when accompanied by count, denominator and uncertainty; it is not a population guarantee.

### 2. Expected hit counts are not repository alert probabilities

Let `F = sum(I_i)` count false elementary hits. Then `E[F] = sum(p_i)` by linearity of expectation, without an independence assumption. If every tested opportunity has marginal probability p and the actual count is N, this becomes Np. Multiplying W, K, R and Q is valid only when those dimensions describe the actual comparisons, without double counting.

For independent tests with common p, the probability of at least one false hit is `1-(1-p)**N`. Without independence, the union bound gives at most `min(1, sum(p_i))`. Neither expression is automatically the expected count of deduplicated repository alerts. Measure the actual complete search and merging rule. Adaptive queries require a separately justified model/protocol.

### 3. Cluster-aware analysis needs a specified sampling design

An unspecified “conservative effective sample size” is not an executable method. Define independently sampled repository families, the cluster-level outcome and the intended population. Resampling all-zero cluster outcomes always produces zero; an ordinary percentile bootstrap cannot supply a meaningful unseen-event upper bound in that case. Hierarchical methods need explicit assumptions and sensitivity analysis. Tens of groups cannot establish extremely rare repository-level errors.

### 4. Separate ancestry, permissions and similarity labels

The proposed manifest's `ancestry_label: none|permitted_historical_copy|unknown` mixes permission into ancestry and omits known copies whose permissions differ. Use separate ancestry relations and rights labels. Same-stack/common-algorithm code is not automatically an ancestry negative: shared dependencies and actual copying need ground truth. Distinguish copied marked fragments from signal-only transplantation onto independent content.

### 5. Make reproducibility and detector failures concrete

Private production keys should stay private, but reproducible synthetic benchmarks need test-only keys/seeds or a precisely declared verifier-access protocol. Digests alone cannot reproduce a secret-dependent detector. Do not publish production secrets.

The proposed result object needs candidate/reference artifact digests, coordinate units and interval conventions, separate component scores/thresholds, parser/config versions, and an `unknown` dependence state. Replace unqualified `mark_presence: absent` with `not_detected` under a named configuration. Separate cryptographic signature validity from trust-policy acceptance. Exact/fingerprint baselines without mark identity should report that metric as not applicable, not zero errors.

### 6. Keep the first pilot implementable

No embedder exists yet. Start with source-subset eligibility, capacity, mark/unmarkable outcomes and clean recovery before hundreds of marked fragments or a broad refactoring suite. Track all embedding and transformation failures, plus conditional and end-to-end recall. Compilation and tests are bounded validity evidence, not semantic equivalence proofs. Keep Go and Rust as separate profiles; Go first is a scheduling proposal rather than evidence against Rust.

The illustrative performance table is explicitly hypothetical and must not become a target or a claim. Reporting required metrics is a completeness gate, not evidence that a method is useful. Choose operational budgets before calibrated comparison and do not automatically publish private per-item evidence.

## Handoff for the second report

Ask for external primary statistical and detection-evaluation sources; a precise grouped sampling/calibration procedure; rare-event uncertainty at the full-search unit; expected-key versus blind multi-key discovery; and a reproducible small Go/Rust pilot that records unsupported inputs. Reconcile those findings before changing normative schemas or conformance requirements.
