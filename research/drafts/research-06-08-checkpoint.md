# Research lanes 06–08: reconciliation checkpoint (draft)

Drafted 2026-11-22 and revised the same day after an [independent review](research-06-08-checkpoint-review.md). This is a non-normative research draft, not adopted policy. It reconciles three evidence reviews and three NotebookLM report audits:

- Lane 06: [evidence review with report audit](../lanes/06-evidence-review.md)
- Lane 07: [evidence review](../lanes/07-evidence-review.md) and [report audit](../lanes/07-report-audit.md)
- Lane 08: [evidence review](../lanes/08-evidence-review.md) and [report audit](../lanes/08-report-audit.md)

All three reports were captured as rendered Studio text, not native exports. Capture hashes are in each audit. No experiment was run for this checkpoint.

## What the lanes establish

1. **None of the five reviewed code candidates clears the project's carrier bar.**
   - The five are SrcMarker, RoSeMary, SEW, CLASP and PLACEMARK.
   - The bar, from the [census checkpoint](../public-census-checkpoint.md): a typed safe subset, measured eligible sites in real Go/Rust code, defined blind or reference-assisted extraction and alignment, and a cheapest-valid-normalizer test before identity framing.
   - SrcMarker, RoSeMary and SEW report bit accuracy or keyed presence tests on other languages, not net authenticated capacity (lane 06).
   - CLASP's reference-assisted mode is the best-measured of the five: 2–32 bits tested, clean bit accuracy 97.85–99.72%. It still has no typed safe subset, no Go/Rust measurement and no cheapest-normalizer test (07 audit, A2).
   - PLACEMARK is Python-only. Its authors state that Go loses the placement property (07 audit, A3).
   - The lane 06 report's own candidate (Nata'ala, Research Square) remains unread because its DOI returned HTTP 403. DeCoMa and CodeMark are unchecked.
   - No conclusion follows that no suitable carrier exists.
2. **The project's own failures are narrow.**
   - In the two narrow synthetic carriers tested, cheap normalization erased all 55 nonzero states per language.
   - The four-repository census established no safe eligible sites.
   - Neither result shows the failure is general.
   - Both NotebookLM code proposals (lanes 06 and 07) rely on commutative operand orientation. The Go string-concatenation counterexample against it is unexecuted (it follows from Go semantics). Operand sorting erasing the mark is an inference, not a measurement.
3. **Forgery and transplantation are failures separate from erasure.**
   - Both project carriers decode same-context transfers.
   - TetherMark is a recent, unreviewed image-only preprint (2026-11-17) whose attacks were run by its authors. It reports that a keyed, enrollment-relative relation check lowers success of the WmForger and WMCopier forgery attacks to 9.17% and 16.25%, not to zero.
   - On the same attacks, the TrustMark-P baseline without that check accepts 80.00% and 90.83% (07 audit, A1).
4. **Synchronization and fragment recovery cost carrier states.**
   - Insertion/deletion codes need encoded synchronization symbols (07 review, S1); window maximization changes the false-alert statistic (S2); spoofing can exceed benign false-alert rates (S3). None gives a universal minimum fragment size.
5. **Cross-media design should share an evidence record, not a signal.**
   - Text marks (Kirchenbauer) are generation-time presence tests, and Stable Signature is a generation-time decoder fine-tune with CC BY-NC code. TrustMark, WavMark and AudioSeal are post-hoc embedders with distinct units, framing and failure modes (08 review and audit).
6. **C2PA already specifies soft-binding lookup** (`/matches/byBinding`, `/matches/byContent`) and keeps hard binding mandatory (08 audit, B3). This is a precedent for "decoded mark → signed record", not a Traceweave protocol.

## What they do not establish

- **Identity or ancestry.** No authenticated identity payload, ancestry or authorship conclusion follows from a recovered mark in any medium.
- **Thresholds.** No fragment-size floor, BER/relation/entropy threshold or FPR figure for Traceweave.
  - Every threshold the audits flag as unsupported stays unadopted, for example τ_BER 0.25, τ_rel 0.80, the 4.5-bit entropy floor, the recall gates and the abstention floors.
  - Stable Signature's published τ = 41 at FPR 10⁻⁶ is supported, but it applies only to that system.
- **Time-scale robustness.** AudioSeal's Table 3 reports 0.99 accuracy at 1.25× speed, against 0.50 for WavMark. That is one author-run comparison at a best-accuracy threshold; the report's contrary AudioMarkBench claim is unchecked.
- **Schema changes.** No schema, spec-file, verdict-name or API change. Report-proposed names stay quarantined, for example `VERDICT_*`, `lineage_id`, `instance_relation`, `traceweave.carrier.report`, `status_code` and `confidence_score`.
- **Unchecked report sources.** These sources were not checked and contribute nothing:
  - code: Nata'ala (Research Square), DeCoMa, CodeMark, Collberg–Thomborson;
  - synchronization: Sharma–Coumou, Xiang 2014;
  - text: HSPMark, DEW, Watermark under Fire, Nemecek;
  - image and video: PGID, Hwang 2024, the image-attack survey, the video phase coding paper;
  - audio: AudioMarkBench, Özer 2025.

## Carrier decisions (coordinator, 2026-11-22)

1. **Source code: no code-carrier experiment now, and no SEW falsification check.** Revisit only if a new candidate is read in primary form and plausibly meets the bar, Nata'ala included.
2. **Next implementation step: the synthetic token-fingerprint comparison baseline**, as already proposed in the census checkpoint.
3. **The TrustMark synthetic-image study is deferred until after M3 and needs the owner.** It stays a proposal only; see the note below.

### Deferred proposal note: post-hoc image study

TrustMark remains the preferred first non-code candidate: it marks existing artifacts, its repository is MIT-licensed, its framing is explicit (100 raw bits; 61 data bits under BCH_5), and its authors supply a remover.

Nothing is authorized. A future protocol must state the following before any run:
- **Image count.** Resolutions, the synthetic generation method, and n per condition, including the negative set. The achievable false-alert bound depends on n: zero events in 1,000 negatives bounds the rate only below about 3×10⁻³. Threshold-selection and evaluation split sizes must also be stated.
- **Compute and disk budget.** Wall-clock time, weight and dependency size, and disk use. All are unmeasured so far, and the owner is to bound them.
- **Failure criterion.** When the study fails, for example clean decode below a stated rate, false decodes from negatives or the wrong decoder above a stated count, or a stated BCH failure/erasure rate. Removal success and acceptance of forged or transplanted evidence are recorded as profile limits.
- **Weight licence.** The weight-file terms and the dependency licences, separately from the repository's MIT licence. Accepting them is the owner's decision.
- **Download and install.** The loader fetches missing weights from an Adobe host. The protocol must state who permits the one-time weight and package download, and where they are installed.
- **Offline and CPU evidence.** CPU-only, network-denied operation has not been demonstrated; the loader only selects CPU, MPS or CUDA. The protocol must state how it will be shown.

Acceptance of transplanted residuals is a hypothesis to test, since TetherMark measured forgery attacks, not residual transplant. Any payload stays a random test vector, with no identity framing.

## Implications for fragment recovery and calibration

- Keep the complete-function boundary for the code prototypes.
- Report observed symbols, ECC reconstruction and reference-supplied values separately. Reed–Solomon codes repair n−k erasures but only ⌊(n−k)/2⌋ errors, so declare which applies.
- A graded relation or binding check cannot be an exact Merkle root: a root either matches or it doesn't, so any fragment fails.
- **Untested design hypothesis:** the fingerprint baseline's exact/normalized span matching might later serve as a relation check in transplant controls. No source shows such matching resists transplantation in code, and fingerprints may share failure causes with marks (08 review). The baseline is justified on its own; test the dual role later.
- Calibrate whole queries after all windows, anchors, keys and catalogue entries are searched. Synthetic family variants are clustered, so they cannot support rare-event rates.
- Even a relation gate yields a measured attack rate, not immunity (TetherMark: 9–16%, images, preprint).
- Interpret conservatively: authentication plus binding means "these bytes satisfy these checks", not "authentic descendant"; a failed relation check means "not bound", not "forgery".

## Implications for the first non-code media profile

- **Order:** image first and post-hoc only (deferred, as above). Text needs generator control and is presence-only.
- **Audio** is second:
  - AudioSeal (MIT code, 16-bit messages) is the stronger audio candidate on time-scale evidence.
  - WavMark stays a candidate only for segment-aligned, non-time-scaled use; its 1.25× result is 0.50.
  - Weight licences and search calibration are unresolved for both.
- **Shared record:** use the one from the 08 review, keeping distinct the artifact digest and role; profile, configuration and model digests; coordinate system (pixels at a stated resolution); raw bits, decode result and statistic, each with its calibration identifier; and record resolution, signature validity and trust.
- **Confidence:** leave it empty unless calibrated, and never multiply mark, fingerprint and signature evidence.
- **Lookup:** a C2PA-style soft-binding lookup is a compatible later layer, with hard binding still required. Prefer a local catalogue, because hosted by-content lookup discloses the asset.

## What stays unmeasured

- **Code:** safe Go/Rust eligibility beyond the four-repository sample; partial-copy recovery beyond complete functions; transplant rates for any code relation check.
- **Any medium:** net authenticated payload capacity; full-query false-alert rates; adaptive removal budgets.
- **Non-code:** TrustMark behaviour on synthetic images; weight licences for TrustMark, AudioSeal and WavMark; offline runtime of any non-code toolchain.
- **Sources:** every unchecked source listed above, notably AudioMarkBench versus AudioSeal, and Nata'ala.

## Remaining decisions

1. Whether to promote any part of this draft into `research/` checkpoints. Normative files stay untouched either way.
2. After M3, the owner decides whether to commission the image protocol under the note above.
