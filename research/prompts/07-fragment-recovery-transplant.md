# Traceweave research brief: Fragment recovery, synchronization and signal transplantation

Output filename: `07-fragment-recovery-transplant.md`
Prepared 2026-11-22.

## Decision to enable

What can be recovered from a small edited fragment, and what evidence—if any—distinguishes a copied mark from the origin of surrounding content? Produce a concrete experimental design or a precise limitation, not a promise that cryptography fixes transplantation.

## Questions and required comparisons

- Compare blind versus original/reference-assisted recovery, explicit synchronization patterns versus intrinsic content anchors, local versus global encodings, insertion/deletion channels and error-correcting/redundant payloads. Establish which assumptions match edited source code rather than an ideal communication channel.
- Separate locating a candidate region, recovering symbols, decoding a payload, authenticating a claimed identity and inferring fragment/host ancestry. Distinguish erasure, invalid/unsupported input, ambiguous anchor, wrong payload and no supported claim.
- Explain minimum fragment size and useful capacity after synchronization/framing/redundancy costs. Cover shifted boundaries, gaps, reordering, extracted/inlined functions, repeated common code and multiple competing references. Never fill missing symbols from the reference and count them as recovered evidence.
- Study signal-only transplantation, forged attribution, overwriting, multiple recipients/collusion, replay and adaptive query access. Separate copied content from copied signal and accurately detect a transplanted signal while declining unsupported ancestry claims.
- Evaluate content/context binding and signed commitments. Explain the tension between exact binding and edited-fragment recognition; semantic/robust fingerprints require their own collision and error assumptions. A context label an adversary can reproduce is not authenticated context.
- Identify formal guarantees with assumptions and impossibility claims with their exact scope. Compare published attacks against claimed defenses. Do not generalize impossibility from a single failed carrier.
- Specify calibration over the complete search across fragments/windows/keys/references. Avoid independent-trial bounds on correlated windows, or p-values presented as probabilities of ownership.

## Concrete deliverable

Provide an output-verdict table and an attack/control matrix separating mark presence, payload authentication and ancestry. Design a minimal Go/Rust synthetic test: complete copy, progressively shorter valid fragments, malformed excerpts, duplicate anchors, independent same-task code, signal-only transplant with matching/changed context, wrong key/mark and ordinary normalization. Include original UTF-8 byte localization and abstention criteria. State which experiment could actually distinguish rival explanations and which cannot.

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
