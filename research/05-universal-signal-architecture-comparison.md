# Universal signal architecture: comparison

Reviewed 2026-11-18. Inputs: Google (local input: `gemini/05-universal-signal-architecture.md`; not distributed), Perplexity (local input: `perplexity/05-universal-signal-architecture.md`; not distributed), and the [initial review](05-universal-signal-architecture-initial-review.md). Originals are preserved unchanged. This review checks decisive claims; it is not a complete audit of every citation or a new experimental result.

## Decision

Both reports support investigating shared records/interfaces with medium-specific carriers and supplementary fingerprint discovery. Google adds useful primary sources, but its recommendation to abandon watermark development and become AI-origin audit middleware does not fulfill Traceweave's Go/Rust content-marking use case. No architecture or dependency is adopted from these reports.

## Verified research worth retaining

- [Soft-binding benchmark, arXiv:2610.04151](https://arxiv.org/abs/2610.04151): this is the real identifier behind Google's placeholder `2610.xxxxx`. The authors report complementary failures between marks and fingerprints, 69% union coverage on their attacked image copies, and substantial ISCC matching drift after watermarking. These support paired evaluation and measuring original/final fingerprints. They are dataset/implementation results, not universal hybrid guarantees or code results. A union of successes is not by itself a deployable decision rule with calibrated false positives.
- [Integrity Clash, arXiv:2603.02378](https://arxiv.org/abs/2603.02378): real work demonstrating risks when watermark evidence and signed declarations are evaluated separately. Its reported 100% classification accuracy is restricted to its test corpus and states. Retain evidence reconciliation as a test case, not a universal truth classifier.
- [HaloMark, arXiv:2608.08645](https://arxiv.org/abs/2608.08645): real embedding-vector watermark research. Its adaptive-attack threshold is empirical, with an explicitly bounded attack evaluation. Marking a vector does not establish that its source code, source text or rendered media contains a recoverable mark.

## Corrections that change the recommendation

1. **No general impossibility proof is supplied.** Different media constraints motivate specialized carriers, but do not prove every shared algorithm is physically or mathematically impossible. Use “not demonstrated under the required fidelity, capacity and attack conditions.” A theorem needs explicit distributions, transformations, fidelity constraints and adversary access.
2. **SWHID is exact object identification, not robust code marking.** Its [core identifier specification](https://www.swhid.org/specification/v1.2/5.Core_identifiers/) hashes object representations. Formatting can change a file identifier; identical independently created bytes share an identifier. It neither embeds information nor guarantees historical attribution. Google's proposed architecture has no Go/Rust embedder despite listing code as a supported medium.
3. **An editing declaration is not a human-origin claim.** [C2PA defines `c2pa.edited`](https://spec.c2pa.org/specifications/specifications/2.5/specs/ContentCredentials.html) as an editorial transformation. Human editing of generated media is consistent with an AI-origin mark. Missing origin disclosure, an explicit contradictory origin claim, and unknown origin must remain separate states. No detected AI mark cannot establish “Human Passed.” A mark can be transplanted, forged or falsely detected; its issuer, payload, scope and error rate matter.
4. **Private/local operation remains possible.** A fingerprint index or manifest store can be local. Network dependence is a deployment choice. Server-side storage does not automatically protect private descriptors, query privacy or linkability. DLT lookup and public registries are not required by our use case.
5. **Binding and key derivation need a real protocol.** Hashing the final marked artifact is distinct from tolerant discovery. Google's diagram fingerprints the original on a parallel branch while its text requires post-mark fingerprinting. Deriving watermark secrets from public manifest hashes alone does not make them secret, and hashing a manifest that depends on the marked result can create a dependency cycle. Specify secret input, domain separation and processing order before implementation.
6. **License labels need artifact-level checks.** The report calls Chromaprint MIT, but its [license notice](https://github.com/acoustid/chromaprint/blob/master/LICENSE.md) describes the combined project as LGPL 2.1 due to included FFmpeg code, with FFT dependency considerations. [AudioSeal](https://github.com/facebookresearch/audioseal) does state MIT for code and weights. This spot check does not certify every suggested model, checkpoint, dataset or binary dependency.

## Correct the experiment

The image/audio experiment plus 100 repositories and embedding vectors is neither minimal nor aligned with the first pilot. Its stated aim to definitively prove hybrid superiority prejudges the result. Code repositories evaluated only through SWHID cannot test code-mark survival.

Keep Go/Rust first, using the same held-out fixtures and attack budgets for mark-only, fingerprint-only and combined decisions. Include independent equivalent programs, wrong keys, partial copying and transplantation. Evaluate recovered-record accuracy, functional validity and false attribution separately. A second medium can later test interface generality.

Five hundred independent negative decisions with zero errors give a one-sided 95% binomial upper bound of approximately 0.006, not 0.000001. To obtain that latter bound with zero errors requires about three million independent trials. Pairwise comparisons sharing assets are dependent; a large pair count is not automatically equivalent to that many independent trials. Declare whether error is per comparison, per query or per catalogue search.

Measure the combined rule's false positives and abstentions as well as recovery. Set thresholds on separate calibration data, preserve failures, and treat test-set percentages as scoped results. Explicit source/record disagreements should produce reviewable evidence; automatic quarantine or ownership verdicts are not adopted.

## Effect on Traceweave

Continue embedded marking research and reuse existing components where they meet the requirements. Add paired pre/post-mark fingerprint measurement and conflicting-evidence cases to the evaluation backlog. Keep standards integration optional until mapped to the existing private/local model. These reports refine the plan; they do not justify replacing the product goal, publishing a new diagram, or declaring a universal signal impossible.
