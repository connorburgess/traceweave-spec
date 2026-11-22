# Traceweave research brief: Practical code carriers after failed narrow baselines

Output filename: `06-practical-code-carriers.md`
Prepared 2026-11-22.

## Decision to enable

Which published code-marking candidate, if any, merits a small new experiment after our narrow raw-state carriers failed removal and practical eligibility tests? This is a focused candidate-selection study, not another generic watermarking survey.

## Questions and required comparisons

- Distinguish post-hoc marking of existing human code from generation-time LLM watermarking, model-weight watermarking, binary/software watermarks and extracted clone fingerprints. Only transfer claims with an explicit bridge to our source-code use case.
- Compare plausible source-level families: scope-aware identifier choices, behavior-preserving AST/data/control-flow alternatives, literal representations, and any well-supported alternative. Identify whether marks survive only formatting, ordinary maintenance, targeted normalization, or stronger attacks. Do not assume structural means robust.
- Require the concrete carrier, insertion/extraction procedure, blind versus reference-assisted detection, key/secret assumptions, raw versus effective payload, site availability and minimum recoverable fragment. Account for framing, redundancy, synchronization and multiple mark identities.
- For Go/Rust, explain scope/capture, evaluation order, effects, concurrency, numeric semantics, borrowing/lifetimes/Drop, macros/cfg/build scripts, source observers and performance/code-quality constraints where relevant. Clearly label language adaptations that lack evidence. Refuse unsupported inputs rather than silently rewriting them.
- Separate benign edits from adaptive removal. Include formatter, renaming, dead-code elimination, canonicalization, function extraction/inlining, partial copying and AI rewrites; document exact attack settings, validity checks and failure cases. Treat ports to another language as a separate regime.
- Compare against no mark, exact/normalized matching and extracted fingerprints. A keyed feature selector is not an embedding algorithm. Include independently written same-task programs and mark transplantation; do not equate signal presence with origin.
- Audit reported capacity and false alerts: site-selection denominators, eligible fraction, correlated samples, query/catalogue size and held-out thresholds. Do not compare incomparable paper headline percentages.

## Concrete deliverable

Shortlist at most three candidates, or none. For each provide primary implementation links and licenses, a proposed Go/Rust safe subset, smallest synthetic reproduction, cheapest plausible valid removal attack, and explicit reasons to proceed or stop. Rank by useful evidence rather than novelty. Recommend at most one experiment; no extra corpus acquisition is requested by this brief.

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
