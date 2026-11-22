# Traceweave research brief: Still-image profile candidates

Output filename: `10-image-profile.md`
Prepared 2026-11-22.

## Decision to enable

Which still-image technique, if any, merits a small bounded experiment as a Traceweave image profile: a perceptual-fingerprint comparison baseline, an embedded watermark (TrustMark or an alternative), a C2PA-style manifest or soft-binding layer, or none? This is a candidate-selection study, not a generic watermarking survey.

## Questions and required comparisons

- Scope: still raster images that already exist (post-hoc marking). Generation-time watermarks (for example decoder fine-tuning or latent-noise methods) are a labelled contrast only; transfer claims need an explicit bridge to post-hoc marking.
- Fingerprint comparison baselines (no insertion): perceptual hashes (aHash, dHash, pHash, wavelet/block variants) and learned descriptors (copy-detection or self-supervised embeddings). Give hash or descriptor size, distance metric, threshold source, dataset, negative set, catalogue size and the false-alert definition; report which edits they survive and which they do not (crop, rotation, resize, JPEG, colour change, overlay, screenshot, generative re-rendering). Treat them as baselines, not marks.
- Embedded watermarks: TrustMark (code, model and weight licences, 100 raw bits and 61 data bits under BCH_5, residual image, resolution handling, CPU and offline operation, author-supplied remover) and well-supported alternatives, post-hoc and learned or classical (for example DWT-DCT, HiDDeN-style, RivaGAN, StegaStamp, VideoSeal-image mode), with exact payload units, quality metrics (PSNR/SSIM/LPIPS and their conditions), embedding and detection cost per megapixel, keys and detector access.
- Attacks with exact settings and negative results: crop and resize, JPEG/WebP recompression, blur and noise, screenshot and print-scan, regeneration/diffusion purification, adversarial removal, repainting or inpainting. Include forgery and transplantation: copying a watermark residual or decoded payload onto other images (for example WmForger, WMCopier and related forgery attacks), and any keyed relation checks with their measured attack-success rates. Do not assume survival under one attack implies survival under another.
- Fragment and localization: partial crops, patches and collages; minimum recoverable region; whether detection localizes. Separate decoded payload recovery from presence detection from identity.
- C2PA: manifests as signed metadata, hard binding versus soft binding, the specification's soft-binding algorithm lists and lookup endpoints (by binding and by content), metadata stripping, and what a valid manifest does and does not establish. Treat C2PA as a metadata/binding layer, not a robust signal; note which lookups disclose the asset to a hosted service and what stays local.
- Compare each method against no mark and against exact and perceptual matching on independent images of similar content. Do not equate signal presence with origin or ownership.
- Audit reported bit accuracy and false alerts: image counts per condition, datasets, resolutions, negative sets, threshold selection versus evaluation split, correlated samples. Do not compare incomparable headline percentages.
- Licences of code, weights and datasets; CPU-only and network-denied operation evidence; install and weight-download requirements and who hosts them.

## Concrete deliverable

Shortlist at most three candidates, or none, covering the fingerprint-baseline, embedded-watermark and C2PA/soft-binding questions. For each give primary implementation links and licences, a smallest synthetic reproduction (synthetic images, random test payload, no identity framing), the cheapest plausible valid removal or transplant attack, and explicit reasons to proceed or stop. Rank by useful evidence rather than novelty. Recommend at most one experiment; no weight or dataset download is requested by this brief.

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
