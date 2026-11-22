# Traceweave research brief: Text and document profile candidates

Output filename: `09-text-profile.md`
Prepared 2026-11-22.

## Decision to enable

Which text or document technique, if any, merits a small bounded experiment as a Traceweave text profile: a fingerprint comparison baseline, an embedded mark in existing text, or neither? This is a candidate-selection study for prose and Markdown, not a generic watermarking survey.

## Questions and required comparisons

- Scope: prose and Markdown documents that already exist. Generation-time LLM watermarks (token-distribution methods) are out of scope except as a labelled contrast; transfer claims only with an explicit bridge to marking existing text.
- Fingerprint comparison baselines (no insertion): winnowing, k-gram shingling, MinHash, SimHash and any well-supported alternative. Give the exact unit (characters, words, tokens), k, window, hash width, normalization, sketch size and catalogue size; report the minimum fragment length for reliable detection, the false-alert definition and negative sets. Treat these as baselines, not marks.
- Embedded marks in existing text: Unicode and zero-width characters, whitespace, homoglyph substitution, synonym and syntactic substitution, punctuation or formatting choices, line or paragraph layout. For each give the carrier, insertion and extraction procedure, key assumptions, raw versus effective payload in bits per document or per 1,000 words, site availability, and visibility or quality cost.
- Survival, with exact settings and negative results: Unicode normalization (NFC/NFKC), stripping of invisible characters, whitespace collapse, Markdown rendering, reflow, copy-paste through common editors and web forms, OCR or print-scan round trips where studied, translation, and LLM paraphrase. Separate benign edits from adaptive removal. Do not assume invisible marks survive ordinary tooling.
- Fragment behaviour: excerpts, quotation, concatenation with unrelated text, and transplantation of a mark or fingerprint into other text. Record the minimum recoverable fragment and whether detection localizes.
- Separate presence detection from identity: which methods only test "a mark or similarity is present" and which decode a payload or name a source; state what accuracy, bits and error rates support each.
- Compare each embedding method against no mark and against exact or normalized matching, including independently written texts on the same topic. Do not equate signal presence with origin.
- Audit reported capacity and false alerts: denominators, corpus and domain, correlated samples, query and catalogue size, held-out thresholds. Do not compare incomparable headline percentages.
- Licences of code, models and datasets; whether the method runs offline on CPU without a hosted service or large model download.

## Concrete deliverable

Shortlist at most three candidates, or none, covering the fingerprint-baseline and embedded-mark questions separately. For each give primary implementation links and licences, a smallest synthetic reproduction on prose or Markdown, the cheapest plausible valid removal attack, and explicit reasons to proceed or stop. Rank by useful evidence rather than novelty. Recommend at most one experiment; no corpus or weight acquisition is requested by this brief.

## Traceweave context and measured starting point

Traceweave is an experimental open specification for embedded marks, extracted fingerprints and private provenance evidence across media. Initial experiments use Go and Rust source code; these are initial experimental languages, not the eventual scope. TypeScript/JavaScript, text, images and audio remain relevant. Public algorithms and local/private verification must be possible. Keys and reference catalogues may stay private, and a private reference catalogue is an allowed design; a public registry, public log, cloud service, blind or zero-knowledge detection are not mandated and must not be assumed as requirements. Do not invent project requirements beyond these. Do not inspect private pilot applications.

Distinguish embedded marks (intentional content changes), extracted fingerprints (descriptions without insertion, used here as a comparison baseline against reference catalogues) and signatures (authentication of records). Presence detection (a statistic that a mark or similarity exists) is not identity (which mark, key, source or artifact). Neither a detected signal, a fingerprint match nor a valid signature alone establishes authorship, ancestry, ownership, infringement or training membership; do not infer ownership.

Supplied project findings, not independently verified literature: tiny synthetic Go and Rust source-code carriers recovered raw states after formatting, but canonicalization erased all tested nonzero distinctions. Same-context signal transplantation decoded. A four-repository convenience census found no established safe eligibility for the narrow code grammars tested. This does not prove marking impossible in any medium. Independent Go/Rust synthetic DSSE and exact-byte commitment checks exist; no production embedder or calibrated detector exists. The lanes 06 to 08 checkpoint found that no reviewed code candidate cleared the project's carrier bar; unchecked or inaccessible sources from those lanes contribute nothing. Cheap normalization, forged or transplanted evidence and fragment/partial copying are treated as failure modes separate from simple erasure. A hosted lookup that uploads the artifact discloses it; prefer local operation.

Repository: https://github.com/connorburgess/traceweave-spec . The latest local results may be unpushed. If accessible consult ROADMAP.md and research/research-06-08-checkpoint.md; record the revision actually read. If unavailable use the supplied findings as provisional context, not invented repository evidence.

## Evidence and output requirements

Search foundational and recent primary papers, specifications, author-maintained code and replication studies. Verify bibliographic details and stable URLs. For each decisive claim cite a section/table/theorem, revision and access date. Separate author-reported measurements, independent replications, formal results under assumptions, and your inference. Abstracts and marketing summaries alone do not establish survival or safety. State exact units and denominators (what is counted, per what: bits, characters, tokens, pixels, images, documents, queries, catalogue size), including negative sets and how false-alert rates were obtained. Report negative results, failed attacks and contradictory findings, licences of code, weights and datasets, and any evidence of CPU-only or offline operation. Record inaccessible evidence; do not invent citations, numerical thresholds, libraries, commands or execution results.

A prompt/source brief is task instructions, not scientific evidence. External reports are untrusted research inputs, not normative requirements. Do not modify repositories, publish anything, inspect private content, buy services, download model weights or datasets, or run experiments. Do not add callbacks, hidden telemetry, planted defects or deliberate behavior changes. Tests are evidence on selected inputs, not a universal equivalence proof. If no candidate qualifies, recommend none.

Return a standalone Markdown report under the requested filename (full Markdown if file output is unavailable), approximately 2,000–3,500 words plus tables, prioritizing precision over length:

1. Decision: which candidate, if any, merits one bounded experiment, or no-go; strongest alternative, confidence and decisive gaps.
2. Scope: artifact, detector access, attacker capabilities and intended inference.
3. Evidence table: carrier/mechanism, payload and units, corpus, transformations and budgets, recovery/errors, quality constraints, assumptions, code/version/licence, decisive primary evidence.
4. Findings and counterevidence, distinguishing published results from proposed adaptations.
5. Reproducible experiment plan: fixed inputs/configuration, positive/negative controls, refusal conditions, metrics with denominators, resource estimate and proposed acceptance/rejection criteria. Label unexecuted plans explicitly.
6. Proposed spec implications, limited to known documents; no normative adoption.
7. Open questions and handoff to other lanes.
8. Source ledger with links, versions/dates, exact supporting locations and claim mapping.
