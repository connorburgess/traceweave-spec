# Initial discovery checkpoint

2026-11-18. Both provider reports have been reviewed for all four initial discovery lanes, plus the supplementary universal-signal architecture lane. Discovery is complete at this level; robustness, detection performance and signing interoperability are not yet validated.

## What the research supports

| Lane | Working direction | Remaining evidence |
| --- | --- | --- |
| [Embedding](01-code-embedding-review.md) | Medium-specific carriers behind shared evidence interfaces | Safe eligible sites, useful capacity and recovery |
| [Attacks](02-robustness-attacks-comparison.md) | Separate ordinary edits, deliberate removal, transplantation and adaptive attacks | Behavior-preserving attack experiments and measured survival |
| [Detection](03-detection-evaluation-comparison.md) | Freeze evaluation scope and thresholds; measure errors at the actual query level | Held-out controls, uncertainty and calibrated search errors |
| [Provenance](04-provenance-verification-comparison.md) | Exact signed bytes, private commitments and separate trust/time decisions | Cross-language verification and concrete library compatibility |
| [Universal architecture](05-universal-signal-architecture-comparison.md) | Common records and verification interfaces with content-specific methods | Evidence for each proposed media profile |

Initial experimentation uses Go and Rust source code, with planned expansion to multiple media types. Those experiments are a starting point for testing the architecture, not a boundary on Traceweave's intended scope. The research does not establish a universal embedded signal that survives arbitrary transformations.

## Next bounded work

1. Follow the reconciled [carrier plans](lanes/checkpoint.md): eligible-site/refusal reporting, clean raw-state recovery, formatter and canonicalization checks, then fragment and transplant tests. Begin with synthetic fixtures; do not imply a production identity payload or robustness guarantee.
2. Specify evaluation cases alongside those experiments. Distinguish mark presence, recovered identity, artifact relationship and attribution. Collect failures before selecting a statistical calibration method or promising a false-alarm rate.
3. Independently test bare DSSE interoperability with synthetic bytes and public test keys. Preserve the existing commitment and adapter for this first increment; defer optional timestamp integration until the base works.
4. Use results to propose explicit spec changes. Media expansion needs its own carrier, transformations, quality constraints and evaluation evidence; common interfaces can be reused without assuming common signal behavior.

No normative format is changed by this checkpoint. No additional diagram is introduced. The next milestone is measured experiment results, not another broad discovery round.
