# Evaluation protocol

Select the deployment scenario and error unit before tuning: candidate region, artifact, or complete repository search. Freeze configurations and thresholds before held-out evaluation. Keep related repositories and versions in the same data split.

Positive controls include exact partial copies, renaming, formatting, function extraction/inlining, minification/transpilation, repeated multi-model rewrites, and code-to-description-to-code. Record functional validity, attack attempts, tool/model versions and prompts. Broken output is not a successful behavior-preserving evasion.

Negative controls include same-stack repositories, independently implemented identical specifications, dependencies, framework scaffolding, common algorithms, generated helpers, and deliberately transplanted marks. Historical licensed copies are real ancestry positives; any rights conclusion is a separate assessment.

Compare full private catalogue, random subset, keyed subset, and per-feature HMAC variants separately. Hash authentication is not approximate matching. Later compare watermark-only and combined methods at the same false-alarm budget.

Report recall by fragment size and transformation, abstention, candidate volume, false positives with uncertainty, and the complete search's selection behavior. Count attempts over versions, windows and keys; overlapping windows are correlated observations. Do not interpret AUROC or a similarity percentage as a probability of infringement.

The approximate rule-of-three upper 95% bound is `3/N` only for an appropriate independent Bernoulli trial model with zero observed failures. 300,000 files are not automatically independent trials, and tuning to zero on the evaluation set invalidates a held-out claim. No parameter-only `s^k` formula establishes a real-world false-positive bound for normalized code.

There are no production thresholds yet. Required outputs distinguish `candidate`, `insufficient-evidence`, and `unsupported-profile`; any stronger ancestry statement requires reviewable localized evidence. A negative result does not prove no reuse.
