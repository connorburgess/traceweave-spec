# Traceweave research handoff

Run each prompt in a separate deep-research session. Each is self-contained; copy the complete file. The reports can be researched concurrently, then reconciled before selecting an embedding method.

| Lane | Prompt | Report filename (store under a local provider directory) |
| --- | --- | --- |
| Embedding methods | [01-code-embedding](prompts/01-code-embedding.md) | `01-code-embedding.md` |
| Survival and attacks | [02-robustness-attacks](prompts/02-robustness-attacks.md) | `02-robustness-attacks.md` |
| Detection and evaluation | [03-detection-evaluation](prompts/03-detection-evaluation.md) | `03-detection-evaluation.md` |
| Provenance and verification | [04-provenance-verification](prompts/04-provenance-verification.md) | `04-provenance-verification.md` |

Start with lane 1 if running sequentially, then give its report to lanes 2 and 3 as additional context. Lane 4 can run independently. Research reports are inputs, not adopted requirements. Preserve disagreements and source limitations. After all reports arrive, compare recommendations, verify decisive citations, and choose the smallest embedding/detection experiment with explicit rejection criteria.

The prompts require primary sources, implementation availability, known failures, reproducible experiment plans, and proposed spec changes. They do not authorize experiments on private content, paid model calls, or repository publication. Imported reports remain unchanged in ignored `research/perplexity/` and `research/gemini/` directories. They are not distributed or relicensed by this repository. Published reviews link to primary evidence and identify local inputs without requiring them to be available.


## Research checkpoint — 2026-11-18

[Initial discovery synthesis and next experiments](discovery-checkpoint.md): all four initial lanes reviewed, plus universal-signal architecture.

- [Embedding review](01-code-embedding-review.md) and [synthetic Go/Rust feasibility checks](02-carrier-feasibility.md).
- [Attack report comparison](02-robustness-attacks-comparison.md).
- [Universal signal architecture comparison](05-universal-signal-architecture-comparison.md).

Current direction: shared evidence interfaces and medium-specific embedding, with initial experimentation in Go and Rust and planned expansion to multiple media types. Fingerprints supplement embedded marks. No carrier, payload capacity or robustness guarantee is standardized. Initial discovery reports have been compared; detection calibration remains unvalidated; subsequent synthetic provenance interoperability is recorded below.

Next: define safe source subsets, measure eligible sites and clean recovery, then compare carriers under ordinary edits, deliberate normalization, partial copying and transplantation. Evaluate combined evidence without converting similarity or signature validity into ownership claims. These reviews do not change normative wire formats.


## Detection and language-plan checkpoint

- [Detection report comparison](03-detection-evaluation-comparison.md): statistical corrections and calibration choices still to evaluate.
- [Go/Rust lane plans and reconciliation](lanes/README.md): bounded synthetic carrier experiments, not production marking guarantees.
- [Provenance report comparison](04-provenance-verification-comparison.md): exact-byte verification, commitment, artifact-role and timestamp corrections.
- Google launchers: [detection](prompts/03-detection-evaluation-google-launcher.md) and [provenance](prompts/04-provenance-verification-google-launcher.md).

The language-planning task is complete. The subsequent [synthetic experiment checkpoint](experiment-checkpoint.md) records executed carrier and signing interoperability harnesses. No production embedder or calibrated detector is provided.

## Active work

Follow the [research work queue](work-queue.md): it lists open gate IDs from the [roadmap](../ROADMAP.md), current assignments and the loop rule. Checkpoints and reviews are progress records; a gate closes only by its type, with committed evidence.

[Fragment recovery and signing-policy checkpoint](fragment-policy-checkpoint.md) records the reviewed follow-up experiments. The [public-code census protocol](public-census-plan.md) defines the bounded investigation, and the [census checkpoint](public-census-checkpoint.md) records it: four pinned repositories scanned; current narrow patterns remain experimental controls.

[Lane 06–08 reconciliation checkpoint](research-06-08-checkpoint.md): practical code carriers, fragment recovery and cross-media architecture reviewed; no code carrier cleared the bar, and the image study is deferred until after M3 and needs the owner.

[Independent reviews](reviews/) of the roadmap, repository plan, contracts and checkpoints are kept there. The extraction contract, catalogue and report contract, TypeScript and text profiles and their vectors were promoted on 2026-11-23, and the M4 registration specification, trust policy, timestamp adapter decision, Python profile, and their vectors were promoted on 2026-11-25 to `spec/`, `docs/decisions/`, `schemas/`, `profiles/` and `test-vectors/`; see the [promotion map](promotion-map.md). The image profile, image protocol and evaluation protocol stay in `research/drafts/`.

## Follow-up deep research — 2026-11-22

[Prompt pack and NotebookLM workflow](prompts/README.md): practical carriers first, then fragment/transplant recovery and concrete cross-media architecture. Each includes an independent full brief, a top-left research query and a center-chat synthesis instruction.

The separate [image normalization draft-3 proposal](drafts/extraction-profile-image-draft3.md) specifies ISCC grey/resize arithmetic and supplies bounded synthetic conformance checks. It preserves the frozen draft-2 study and changes no gate status.
