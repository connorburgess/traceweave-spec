# Lane 08: bounded cross-media primary-evidence review

Prepared 2026-11-22. **Google/NotebookLM report audit: pending; no exported report was supplied.** This is a three-source-family review for the coordinator, not the requested external synthesis, a replication, or an adopted profile. No models, experiments, datasets, or private applications were acquired or run. Author implementation source was inspected read-only.

Repository context: HEAD `8d5e6a707ef52201951e9b94cb15a508aa35dda3`, with existing uncommitted work. Read the lane [brief](../prompts/08-cross-media-carrier-architecture.md), repository instructions, CONTRIBUTING, research handoff/work queue, lane checkpoint, and [experiment](../experiment-checkpoint.md), [fragment/policy](../fragment-policy-checkpoint.md), [public census](../public-census-checkpoint.md), and [architecture](../05-universal-signal-architecture-comparison.md) checkpoints as local working-tree evidence. The HEAD alone does not identify those uncommitted checkpoint contents. Only this file belongs to this lane.

## Decision support

**Inference:** the evidence supports trying a common evidence container with medium-specific extraction and evaluation. It does not demonstrate a common physical signal, uniform capacity, or transferable confidence scale. The text representative is generation-time presence detection; the other two are post-hoc payload embedders. None is metadata-only provenance. No candidate here independently authenticates a recovered identity.

**Unexecuted recommendation for parent reconciliation:** if one non-code feasibility study is later authorized, prefer a small TrustMark image study because it has an explicit framing implementation and a supplied removal method. It can test both successful extraction and a meaningful failure condition without controlling a text generator. This is a choice of a testable baseline, not a robust production carrier. Defer execution until model/license pins, permitted fixtures, offline setup, and a frozen evaluation protocol exist. The strongest current alternative is to defer all media experiments and finish the already proposed code fingerprint baseline; this review does not reprioritize that work.

## Four-media comparison

Paper-derived statements below are author results, not independent replications. See T, I, A in the ledger for exact locations.

| Medium / representative | Carrier and access | Capacity / localization | Evidence and failure boundary |
| --- | --- | --- | --- |
| Code: current Go/Rust controls | Post-hoc syntax choices; narrow synthetic grammars; reference-assisted extraction | Raw states only; no measured net authenticated payload; complete-function localization | Local checkpoints: clean/formatter recovery, normalization erases all 55 nonzero states per language; same-context transfers decode. Census establishes no safe eligible sites in its limited sample. Signing interoperability already exists and is separate. |
| Text: Kirchenbauer et al., ICML 2023 (T) | Generation-time green-token logit bias; insertion needs sampler access; detection needs tokenizer/configuration, not generator weights | Presence test, no arbitrary identity payload in the reviewed scheme; token-sequence statistic | OPT-1.3B/C4 news-like evaluation; Fig. 5 T5 span replacement lowers AUC from 0.998 to 0.838 at replacement budget 0.5. This is not translation or modern unconstrained paraphrase evidence. |
| Image: TrustMark, ICCV 2025 (I) | Post-hoc learned image residual; encoder/decoder checkpoints | Implementation: 100 raw bits; default BCH_5 leaves 61 data bits; image-level extraction is not pixel ancestry localization | CLIC/MetFace/DIV2K; Table 1 measures PSNR and noisy-bit accuracy. ReMark reduces target bit accuracy to 55% at 48.5 dB PSNR (§4.4/Table 3). No transplant resistance follows. |
| Audio: WavMark v1 (A) | Post-hoc invertible network over STFT representation; repeated segments and search | 32 raw bits per one-second block; paper utterance setup uses 10 pattern + 22 payload bits; released default uses 16 + 16 | §5.1: 400 test samples. Table 2: 2.35% mean BER at 32 bps; Table 3 clipped/repeated setup: 0.48%. Distinct protocols; no arbitrary removal guarantee. |

## Decisive implementation checks and counterevidence

**Text.** T §§2–4 specify the statistic; §6 and Table 2 define empirical error tests; §7.1/Fig. 5 specify the removal experiment. Low-entropy failures are explicit (§4.1/Table 1). The current author repository recommends an extended processor and later parameters; it is not a frozen copy of the original experiment. Its README identifies the old experiment directory as stale. Code is Apache-2.0. Any report conflating original one-token-context measurements with later configurations needs correction. A keyed presence test is not a signed payload. [T paper](https://proceedings.mlr.press/v202/kirchenbauer23a/kirchenbauer23a.pdf), [T implementation](https://github.com/jwkirchenbauer/lm-watermarking/tree/82922516930c02f8aa322765defdb5863d07a00e).

**Image.** The ICCV version differs from the 2023 preprint, including the remover name ReMark. Use its own tables rather than combining numbers across versions. Implementation `datalayer.py` reserves four version bits: default arithmetic is 100 − 35 ECC − 4 version = 61 data bits; other documented modes provide 68, 75, or 40. These are before application identity, binding, or authentication costs. `process_encode` truncates/pads input: an adapter should validate length before calling it. Repository MIT text is present; the paper states code/models MIT. Weight artifacts and dependencies still need individual pinning before use. [I paper](https://collomosse.com/pubs/Bui-ICCV-2025.pdf), [I framing](https://github.com/adobe/trustmark/blob/4c60b9fdb4125fca3001f0803e6890a6b55371ac/python/trustmark/datalayer.py#L118).

**Audio.** A §3.4 bounds attacks: MP3 64 kbps, resampling out/back, and speed factors 0.9/1.1, among others. §5.2 uses repeated messages and pattern-based selection; §5.4 tests locating one second in three seconds on 200 samples. These do not establish recovery from arbitrarily short crops. The README's `1/2^16` detection assertion is a pattern-match heuristic, not measured full-file/search false alerts. Search multiplicity and decoder-output distribution need evaluation. The code is MIT; model artifact licensing is not separately established here. [A paper](https://arxiv.org/html/2308.12770v1), [A implementation](https://github.com/wavmark/wavmark/tree/6ab3bf7ce0679e5b5cfeff3a62e8df9cd2024b37).

**Inference across candidates:** ordinary processing results cannot substitute for adaptive removal, repainting, translation, or signal transplantation tests. PSNR, PESQ, text perplexity, and compiled behavior checks have different meanings. Average bit accuracy/BER does not establish whole-message success or a false attribution rate. Repeating the same message increases redundancy, not the number of distinct identity bits per recording. No reviewed result tests a Traceweave framing adaptation.

## Shared interface boundary (proposal only)

A smallest useful experimental container could carry:

- Exact examined-artifact digest and role, profile/version, extraction implementation, configuration digest, model/checkpoint digest where applicable, and reference availability.
- Detected region with coordinate system, preprocessing mapping, and ambiguity status. Keep UTF-8 bytes/tokens, pixel coordinates/resolution, and samples/sample-rate distinct; a whole-artifact result need not invent a region.
- Raw evidence and decoded payload as separate optional fields; record decode errors, erasure, unsupported input, ambiguous alignment, and abstention explicitly.
- Statistic name/value, threshold, evaluation/calibration identifier, decision unit and search scope. Leave confidence unavailable when it has not been calibrated; do not turn a z-score or BCH success into an attribution probability.
- Record-resolution outcome, exact signed bytes/digest, signature validity, signer-trust decision, and provenance claims as separate results. Distinguish missing metadata/reference from a checked contradiction.

This container is a handoff hypothesis, not a schema change. Algorithm/configuration binding needs canonical bytes before signatures are meaningful. A decoded short locator could resolve in a private catalogue, but that is an unimplemented application protocol; collisions, unavailable entries, wrong identity, and context binding need controls. An exact digest changes under edits even when a mark survives. A signature authenticates a statement about its subject; it does not establish that a transformed candidate shares ancestry. A fingerprint match supplies similarity evidence and may share failure causes with a mark. Their scores must not be multiplied as independent evidence without joint calibration.

## Local/private feasibility

**Implementation inspection, not an offline execution claim:** T supports local detection with tokenizer/configuration and local generation with compatible model access. Model availability, model license and generation hardware remain separate constraints. It does not retrofit a mark into an arbitrary existing human document without generating replacement text.

I selects CPU/MPS/CUDA locally. Its loader checks local model files and fetches missing/invalid files from an Adobe model host; README says weights are not in Git. A provisioned deployment could stay offline, but that has not been demonstrated here. Publicly decodable marks do not require a public record catalogue.

A `load_model(path=...)` supports a local checkpoint; its default downloads from Hugging Face `M4869/WavMark`. README uses mono 16 kHz audio and permits CPU execution. This demonstrates an implementation path toward local operation, not measured runtime, offline reliability, model-license clearance, or support for every audio format. No candidate requires uploading private content to a hosted inference service in the inspected core paths. Dependency/model provisioning and telemetry behavior of the complete environment remain outside this review.

## Source ledger

All accesses 2026-11-22. Exactly three paper/author-implementation families were reviewed. Branch tips were resolved through GitHub's read-only commits API; immutable links below pin inspected files, not downloaded model weights.

| ID | Exact primary source / version | Supporting locations and audit use |
| --- | --- | --- |
| T | Kirchenbauer, Geiping, Wen, Katz, Miers, Goldstein, *A Watermark for Large Language Models*, PMLR 202:17061–17084, ICML 2023. [Published paper](https://proceedings.mlr.press/v202/kirchenbauer23a/kirchenbauer23a.pdf); [bibliography](https://proceedings.mlr.press/v202/kirchenbauer23a.html) | §§2–4 algorithms/statistic; §4.1 low entropy; §6 C4/OPT protocol, Table 2 errors; §7.1/Fig. 5 bounded span attack; Appendix B.1 discusses other attacks. Formal claims apply under stated assumptions, not arbitrary transformed text. |
| T-code | Commit `82922516930c02f8aa322765defdb5863d07a00e`, 2025-09-17. [README](https://github.com/jwkirchenbauer/lm-watermarking/blob/82922516930c02f8aa322765defdb5863d07a00e/README.md); [license](https://github.com/jwkirchenbauer/lm-watermarking/blob/82922516930c02f8aa322765defdb5863d07a00e/LICENSE.md) | README “Repo contents”, “How to Watermark”, updates: original/extended distinction and stale experiments. License: Apache-2.0. |
| I | Bui, Agarwal, Collomosse, *TrustMark: Robust Watermarking and Watermark Removal for Arbitrary Resolution Images*, ICCV 2025, [author-hosted paper](https://collomosse.com/pubs/Bui-ICCV-2025.pdf) | §3 mechanisms/resolution scaling; §4.1 datasets/metrics; §4.2/Table 1 image results; §4.4/Table 3 targeted removal. Publisher PDF returned HTTP 403; inspected author copy, not byte-compared against publisher copy. |
| I-code | Commit `4c60b9fdb4125fca3001f0803e6890a6b55371ac`, 2026-11-11. [CONFIG](https://github.com/adobe/trustmark/blob/4c60b9fdb4125fca3001f0803e6890a6b55371ac/python/CONFIG.md); [data layer](https://github.com/adobe/trustmark/blob/4c60b9fdb4125fca3001f0803e6890a6b55371ac/python/trustmark/datalayer.py); [loader](https://github.com/adobe/trustmark/blob/4c60b9fdb4125fca3001f0803e6890a6b55371ac/python/trustmark/trustmark.py); [license](https://github.com/adobe/trustmark/blob/4c60b9fdb4125fca3001f0803e6890a6b55371ac/LICENSE) | CONFIG encoding-mode table; data layer lines 19, 37–45, 118–146 version bits/capacity/truncation; loader lines 29, 82–88, 141–151 device/download policy. MIT repository license. |
| A | Chen, Wu, Liu, Liu, Du, Wei, *WavMark: Watermarking for Audio Generation*, [arXiv:2308.12770v1](https://arxiv.org/html/2308.12770v1), 2023-08-24 | §§3.2–3.4 carrier/shift/attack budgets; §§4.1–4.2 datasets/metrics; §5.1/Table 2 segment protocol; §5.2/Table 3 repetition/clip protocol; §5.4 localization. |
| A-code | Commit `6ab3bf7ce0679e5b5cfeff3a62e8df9cd2024b37`, 2024-01-07. [README](https://github.com/wavmark/wavmark/blob/6ab3bf7ce0679e5b5cfeff3a62e8df9cd2024b37/README.md); [API/loader](https://github.com/wavmark/wavmark/blob/6ab3bf7ce0679e5b5cfeff3a62e8df9cd2024b37/src/wavmark/__init__.py); [license](https://github.com/wavmark/wavmark/blob/6ab3bf7ce0679e5b5cfeff3a62e8df9cd2024b37/LICENSE) | README “How it works?” default framing and heuristic false alert; API lines 8–20 local/default checkpoint; 23–51 framing/decode/no-result. MIT repository license; no separate weight terms verified. |

## Claim-audit checklist for the pending report

Unchecked items are future report checks, not findings about a report that has not arrived.

- [ ] Separate common record/interface from common physical carrier; require actual evidence for any multi-media universal-signal claim.
- [ ] Identify generation-time, post-hoc and metadata-only mechanisms; do not present T as arbitrary-document payload embedding.
- [ ] Pin paper edition, implementation commit, configuration and model artifact separately; reconcile old TrustMark preprint names/numbers with ICCV 2025.
- [ ] Count framing/ECC/synchronization/repetition before claiming useful capacity; then subtract application binding/authentication overhead. Keep 61/16 data bits distinct from authenticated payload.
- [ ] Keep T original/extended algorithms apart; demand direct measurements for paraphrase, translation and excerpt claims.
- [ ] State image crop fraction, resize/recompression settings and repainting/removal access; do not extrapolate aggregate noise results to those cases.
- [ ] Keep WavMark Table 2 segment and Table 3 utterance protocols apart; state attack parameters, clip lengths, message repetition and retained complete blocks.
- [ ] Do not adopt WavMark's pattern probability as calibrated full-search false alerts. State denominator, trial dependence, catalogue/key/window counts and threshold-selection split.
- [ ] Distinguish BER/bit accuracy, whole-payload success, erasures, wrong accepted identities, abstentions and query-level errors.
- [ ] Treat localized signal as evidence of location only; include transplant, overwrite, absent reference and contradictory record cases.
- [ ] Keep signature validity, trust, similarity and provenance inference separate; do not claim independent evidence fusion without measurement.
- [ ] Require artifact-level license/model/dependency checks and demonstrate offline runtime before claiming fully local operation; distinguish provisioning from private-content disclosure.
- [ ] Preserve code's normalization/transplant failures and existing signing experiments; no claim of real-code authenticated capacity follows from the census.
- [ ] Label every proposed Traceweave adaptation, interface example and experiment unexecuted/non-normative; do not present report recommendations as adoption.

## Validation and handoff

Validation completed: all local Markdown targets exist; all 16 unique external URLs resolved successfully (GitHub blob/tree targets checked through immutable raw/API equivalents); final newline and trailing-whitespace checks passed. The inaccessible publisher PDF noted in I is not a validated delivery link. Repository-wide tests were not run for this isolated research note and would not replicate the reviewed systems. No commits or pushes were made. The coordinator owns report export, reconciliation, and any next experiment decision. Report-audit remains pending; this lane stops after the bounded handoff and can resume on the supplied export.
