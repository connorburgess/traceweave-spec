# Go/Rust lane reconciliation

Reviewed planning checkpoint, 2026-11-18. Inputs: [Go](go-carrier-plan.md) and [Rust](rust-carrier-plan.md). No new embedder or detector is implemented here.

## Agreed first experiment

Use declaration-order permutations as the shared baseline. Compare Go's scope-resolved identifier choices and Rust's integer-literal spelling as language-specific alternatives. All admit cheap normalization attacks. They test safety boundaries, capacity accounting and extraction mechanics, not production robustness.

Keep the narrow synthetic grammars and exclusions. Go needs complete-package type resolution; Rust excludes macros, source-reading build steps and unsupported configurations. Pin matching toolchains and semantic references before execution: the Rust plan's archived 1.85 reference and inspected 1.97 compiler are not automatically interchangeable.

## Future implementation sequence

1. Eligibility, deterministic refusals with unchanged bytes, and raw state counts including zero capacity.
2. Deterministic state mapping and reference-assisted raw-symbol extraction; exhaustive small state spaces. Identity authentication remains unavailable until its protocol exists.
3. Formatter and behavior checks, then sorting, alpha-renaming/separator stripping and direct-return rewriting. Separate invalid attacks from valid carrier erasure.
4. Whole-function copies, excerpts, duplicate anchors and signal-only transplants. Do not infer host origin from a copied region.
5. Review measured capacity/alignment before identity payloads, keyed framing, redundancy and blind search. Add test-key identity controls and full-search calibration only when implemented.

## Shared measurement rules

- Separate changed, already-matching, unmarkable, validation failure and rollback outcomes. An unchanged matching state can decode but does not establish intentional insertion. State denominators explicitly.
- Report eligible/all inputs, completed/attempted embeddings, raw recovery/completed embeddings and end-to-end recovery/all requests. Keep decoded errors, erasures and abstentions distinct.
- Expected-identity verification and blind discovery are different protocols. Raw-symbol extraction alone implements neither. Unavailable identity/false-alert metrics must not be reported as zero.
- Later false-alert evaluation uses negative full queries with at least one incorrect accepted identity, under fixed catalogue/key counts and merging rules. Keep primitive comparison counts separately.
- Group synthetic variants by family. Permutations are dependent cases, not independent evidence for rare-event bounds. Compare components on the same fixtures and budgets.
- Record valid removal even when it erases all carriers; do not hide it behind similarity gates.

## Verification and scope

The Go lane's system-Python jsonschema failure is an environment issue. Coordinator validation uses the repository virtual environment. Repository checks and existing carrier fixtures do not validate the new proposed carriers.

Both plans contain external research prompts. The subsequent [detection comparison](../03-detection-evaluation-comparison.md) retains query-level calibration as future work and rejects universal carrier-size and binary-survival requirements. No normative formats, diagrams or robustness guarantees are adopted. No publication is part of this checkpoint.
