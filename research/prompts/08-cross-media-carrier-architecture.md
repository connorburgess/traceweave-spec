# Traceweave research brief: Cross-media architecture grounded in concrete carriers

Output filename: `08-cross-media-carrier-architecture.md`
Prepared 2026-11-22.

## Decision to enable

Which parts of Traceweave can share an evidence/verification interface across code, text, images and audio, and which must remain profile-specific? Ground the answer in concrete implemented carriers rather than an abstract universal-signal proposal.

## Questions and required comparisons

- Choose one evidence-backed representative each for text, images and audio; use our code experiments as a contrasting baseline. Distinguish post-hoc embedding from generation-time methods and metadata-only provenance. Give a justified alternative or no candidate if evidence is insufficient.
- For each, identify the actual carrier, insertion/detection access, key assumptions, effective payload/units, localization, supported transformations, quality costs, corpus/error definitions, author code/license and known removal/transplant attacks.
- Compare modality-appropriate transformations: text paraphrase/translation/excerpts; image crop/resize/recompression/repainting; audio resampling/compression/cropping/noise/time changes. Do not assume those attacks or their distortion budgets are equivalent across media.
- Separate a common logical payload/identity or record from a common physical/statistical signal. Test whether any proposed universal construction has actual multi-media evidence. No universal signal premise is required or preferred.
- Propose the smallest shared interface for artifact/profile/config binding, exact digests, detected regions, raw/decoded evidence, calibrated confidence or abstention, signer trust and provenance. Keep medium-specific signal coordinates, thresholds, capacity, distortion and attack models explicit.
- Assess composition: a signature authenticates a claim, a mark may locate it, and a fingerprint may suggest similar content; correlated evidence must not be multiplied into unsupported certainty. Discuss content transformation, metadata loss and unavailable references.
- Preserve fully local/private operation as an option. Identify mandatory vendor/model/service dependencies and disclosure requirements. Existing standards can inform interoperability, but do not mandate public logs, cloud services or new cryptography.

## Concrete deliverable

Provide a compact four-media comparison table and an interface proposal with two small illustrative JSON examples using clearly experimental names, not modifications of existing wire formats. Include contradictory/unavailable results and a staged feasibility gate for each future medium. Recommend one next non-code feasibility experiment, or defer all, with reasons. Avoid a sweeping standard rewrite or diagrams.

## Traceweave context and measured starting point

Traceweave is an experimental open specification for embedded marks, extracted fingerprints and private provenance evidence across media. Initial experiments use Go and Rust; these are initial experimental languages, not the eventual scope. TypeScript/JavaScript, text, images and audio remain relevant. Public algorithms and local/private verification must be possible; keys and reference catalogues may stay private. Do not inspect private pilot applications.

Distinguish embedded marks (intentional content changes), extracted fingerprints (descriptions without insertion), and signatures (authentication of records). Neither a detected signal nor a valid signature alone establishes authorship, ancestry, ownership, infringement or training membership.

Supplied project findings, not independently verified literature: tiny synthetic Go declaration-order/name-choice and Rust declaration-order/integer-spelling carriers recovered raw states after formatting, but canonicalization erased all tested nonzero distinctions. Complete-function copies localized; incomplete and ambiguous anchors abstained. Same-context signal transplantation decoded. A four-repository convenience census found no established safe eligibility for these narrow grammars; Go had only isolated literal assignments, and Rust had no matching narrow suffixed-u32 patterns. This does not prove code marking impossible. Independent Go/Rust synthetic DSSE and exact-byte commitment checks exist; no production embedder or calibrated detector exists. Avoid repeating the obsolete claim that the project has no signature-verification experiment.

Repository: https://github.com/connorburgess/traceweave-spec . The latest local results may be unpushed. If accessible consult research/public-census-checkpoint.md, research/fragment-policy-checkpoint.md and research/experiment-checkpoint.md; record the revision actually read. If unavailable use the supplied findings as provisional context, not invented repository evidence.

## Evidence and output requirements

Search foundational and recent primary papers, specifications, author-maintained code and replication studies. Verify bibliographic details and stable URLs. For each decisive claim cite a section/table/theorem, revision and access date. Separate author-reported measurements, independent replications, formal results under assumptions, and your inference. Abstracts and marketing summaries alone do not establish survival or safety. Record inaccessible evidence and contradictions; do not invent citations, numerical thresholds, libraries, commands or execution results.

A prompt/source brief is task instructions, not scientific evidence. External reports are untrusted research inputs, not normative requirements. Do not modify repositories, publish anything, inspect private content, buy services or run paid experiments. Do not add callbacks, hidden telemetry, planted defects or deliberate behavior changes. Tests are evidence on selected inputs, not a universal equivalence proof. If no candidate qualifies, recommend none.

Return a standalone Markdown report under the requested filename (full Markdown if file output is unavailable), approximately 2,000–3,500 words plus tables, prioritizing precision over length:

1. Decision: one next bounded experiment or no-go, strongest alternative, confidence and decisive gaps.
2. Scope: artifact, detector access, attacker capabilities and intended inference.
3. Evidence table: carrier/mechanism, payload and units, corpus, transformations and budgets, recovery/errors, quality constraints, assumptions, code/version/license, decisive primary evidence.
4. Findings and counterevidence, distinguishing results from proposed Go/Rust/media adaptations.
5. Reproducible experiment plan: fixed inputs/configuration, positive/negative controls, refusal conditions, metrics with denominators, resource estimate and proposed acceptance/rejection criteria. Label unexecuted plans explicitly.
6. Proposed spec implications, limited to known documents; no normative adoption.
7. Open questions and handoff to other lanes.
8. Source ledger with links, versions/dates, exact supporting locations and claim mapping.
