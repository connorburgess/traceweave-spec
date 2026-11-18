# Language research lanes

Read the [Go plan](go-carrier-plan.md), [Rust plan](rust-carrier-plan.md) and [coordinator reconciliation](checkpoint.md). Both plans include external research prompts.

Go and Rust have separate carrier-feasibility lanes. Both preserve the embedded-mark use case and share the evaluation requirements in [the detection review](../03-detection-evaluation-initial-review.md). This first increment produces candidate comparisons and bounded experiment plans; it does not select a normative algorithm.

Each lane owns its language plan and an external research prompt within it. Private pilot applications remain outside this work. The parent reconciles shared interfaces, capacity assumptions and evaluation before implementation or publication.

Required comparisons: eligibility and unmarkable inputs; clean recovery; wrong-key/identity controls; unmarked and independent same-task programs; attack validity versus evasion; fragments and transplantation; localization; runtime; explicit error units and denominators. Language-specific semantics and safety exclusions must remain explicit.
