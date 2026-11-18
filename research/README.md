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

- [Embedding review](01-code-embedding-review.md) and [synthetic Go/Rust feasibility checks](02-carrier-feasibility.md).
- [Attack report comparison](02-robustness-attacks-comparison.md).
- [Universal signal architecture comparison](05-universal-signal-architecture-comparison.md).

Current direction: shared evidence interfaces, medium-specific embedding, Go/Rust first and TypeScript/JavaScript next. Fingerprints supplement embedded marks. No carrier, payload capacity or robustness guarantee is standardized. Detection calibration and provenance verification remain open research lanes.

Next: define safe source subsets, measure eligible sites and clean recovery, then compare carriers under ordinary edits, deliberate normalization, partial copying and transplantation. Evaluate combined evidence without converting similarity or signature validity into ownership claims. These reviews do not change normative wire formats.
