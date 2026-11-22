# Language research lanes

Read the [Go plan](go-carrier-plan.md), [Rust plan](rust-carrier-plan.md) and [coordinator reconciliation](checkpoint.md). Both plans include external research prompts.

Go and Rust have separate carrier-feasibility lanes. Both preserve the embedded-mark use case and share the evaluation requirements in [the detection review](../03-detection-evaluation-initial-review.md). This first increment produces candidate comparisons and bounded experiment plans; it does not select a normative algorithm.

Each lane owns its language plan and an external research prompt within it. Private pilot applications remain outside this work. The coordinator reconciles shared interfaces, capacity assumptions and evaluation before implementation or publication.

Required comparisons: eligibility and unmarkable inputs; clean recovery; wrong-key/identity controls; unmarked and independent same-task programs; attack validity versus evasion; fragments and transplantation; localization; runtime; explicit error units and denominators. Language-specific semantics and safety exclusions must remain explicit.

## Executed synthetic increment

See the [coordinator experiment checkpoint](../experiment-checkpoint.md), [Go results](go-carrier-results.md), [Rust results](rust-carrier-results.md), and [signing interoperability results](signing-interop-results.md). These measure bounded fixtures; the broader comparisons above remain future work where the reports identify gaps.

## Fragment and policy follow-up

See the [coordinator reconciliation](../fragment-policy-checkpoint.md), [Go fragment results](go-fragment-results.md), [Rust fragment results](rust-fragment-results.md), and [signing policy results](signing-policy-results.md). These distinguish localized raw states from authenticated identity and retain explicit abstentions.

## Public-code census

[Coordinator checkpoint](../public-census-checkpoint.md), [Go census](go-census-results.md) and [Rust census](rust-census-results.md) record the bounded four-repository source-only study. Exact eligibility remains unestablished; no carrier was promoted.

## Lanes 06–08

[Evidence reviews and report audits](../research-06-08-checkpoint.md) for practical code carriers (06), fragment recovery and transplant (07) and cross-media architecture (08): [06](06-evidence-review.md), [07](07-evidence-review.md) with its [audit](07-report-audit.md), [08](08-evidence-review.md) with its [audit](08-report-audit.md). Raw provider reports stay untracked.

## Assignments

Current assignments are by gate ID in the [work queue](../work-queue.md) and the [roadmap](../../ROADMAP.md). The implementation repository holds the I1 extractors on local branches; a differential test is in progress and I2 is next. A lane finishing is a progress record, not a closed gate.
