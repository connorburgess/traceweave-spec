# Lane 08: NotebookLM report audit

Prepared 2026-11-22. Companion to the [lane 08 evidence review](08-evidence-review.md), whose source ledger (T, I, A) and claim-audit checklist this audit applies. The report is a hypothesis source, not a requirement. **Verdict: accept the report's top-level architectural split (a shared evidence record, profile-specific carriers). Reject its experiment, thresholds, interface fields and representative selection as written.**

## Capture identity and limitations

| Field | Value |
| --- | --- |
| Notebook | `46f1ae3a-9eec-4721-9802-265e1726e7cf` ("Traceweave 08 — Cross-Media Carrier Architecture"), owner's signed-in account, BB desktop browser |
| Captured | 2026-11-22, read only; no query, source change, share or new research |
| Artifact | Studio report `08-cross-media-carrier-architecture.md`, labelled "17 sources · 8h ago". The notebook chat shows 36 sources, so the report drew on fewer than half. |
| Raw capture | `.local/research/google/08-cross-media-carrier-architecture-ui.txt` (git-ignored; not edited after capture) |
| Size | 38,240 code points; 38,558 bytes; 591 lines |
| SHA-256 | `716a4d1bf58402ed58cb83d37bce467b968f6de3d579c488c6b78885861b03df` |

Limitations are as for [lane 07](07-report-audit.md):
- The center chat only points to the Studio report, so the capture is its rendered `innerText`, not a native export.
- Maths is split across lines, and there are no citation markers.
- Ledger URLs are shortened forms (for example `spec.c2pa.org/2.4/guidance`), not stable links.
- Opening the item cleared its "Unread" label.

## Claim-by-claim audit, by decision impact

Status: **S** supported, **P** partly supported or overstated, **U** unsupported, **C** contradicted, **V** unverifiable in this pass.

| Impact | Report claim | Status | Basis |
| --- | --- | --- | --- |
| Blocker | Share a logical provenance/evidence envelope across media; reject a universal physical carrier or shared signal space. | **S** | Agrees with the evidence review's inference and with the architecture of the C2PA soft-binding API (B3). It is a design inference, not a measurement. |
| Blocker | Next experiment: three-modality "soft-binding survivability" study with LLaMA-3.2-3B + DEW/WLLM, SD v1.5 + Stable Signature, MusicGen + AudioSeal; 1,000 assets and 10,000 negatives per modality; 35–45 A100 GPU-hours; 120 GB. | **C** (scope) | Breaks standing limits. It needs GPU compute the project lacks, model downloads with separate licences, and public corpora (C4, MS-COCO, ImageNet, VoxPopuli, MusicCaps) beyond "synthetic or already-pinned". The Stable Signature code is CC BY-NC (B2). Generation-time text and image marks cannot mark existing assets. |
| Blocker | Acceptance: empirical FPR ≤ 10⁻⁴ on 10,000 negatives; α fixed "analytically" at 10⁻⁶. | **C** (internal) | Zero false positives in 10,000 independent negatives bounds the rate only below about 3×10⁻⁴ (95% one-sided). Neither 10⁻⁴ nor 10⁻⁶ can be shown that way. The rejection rule ("> 5 false matches") leaves an undecided gap. |
| High | Acceptance/rejection recalls (image ≥ 0.90, audio ≥ 0.85, text ≥ 0.60; reject below 0.25/0.40) and abstention floors (N < 35 tokens, entropy < 0.5, < 128×128 px, < 10% area, < 0.5 s, SNR < 3 dB). | **U** | Invented thresholds with no derivation or source. |
| High | Shared interface fields `artifact_digest`, `verification_timestamp`, `profile_identifier` (`traceweave://profile/image/v1`), `status_code` {VERIFIED, UNWATERMARKED, TAMPERED, ABSTAIN}, `confidence_score`, `p_value`, `resolved_manifest_id`. JSON types `traceweave.carrier.report` and `traceweave.soft_binding.resolution`. Algorithm id `c2pa.softbinding.audioseal`. | **U / C** | Proposed schema names, not adopted. A single `confidence_score` and `VERIFIED` status merge presence, decode, authentication and trust, which the evidence review requires to stay separate. "UNWATERMARKED" asserts absence where only "not detected in configuration" is supported. The example's `calibrated_confidence 0.984` is fabricated. The algorithm id is not shown to be on the C2PA soft-binding algorithm list (not checked). |
| High | Project baseline: compiler optimization, dead-code elimination and AST canonicalization erased all nonzero states; "0–8 bits per function" capacity; "erased under aggressive LTO". | **P / U / C** | The [experiment checkpoint](../experiment-checkpoint.md) shows normalization reset 55/55 nonzero states per language and direct-return rewriting removed Go carriers. Dead-code elimination, optimization passes and LTO were never tested as source attacks, and binary optimization does not rewrite source (lane 06 audit). No net capacity was measured, so "0–8 bits" is **U**. |
| High | "Cryptographic commit signing (DSSE/Sigstore) remains the only verified mechanism for code provenance." | **P** | The project verified DSSE envelope interoperability over an exact statement ([signing results](signing-interop-results.md)). Commit signing and Sigstore were not tested, and "only" is unsupported. |
| High | AudioSeal and WavMark collapse under ±5% time-scale modification (AudioMarkBench, Özer 2025). | **C** for AudioSeal | B1 Table 3 (author measurement, best-accuracy threshold): "Fast (1.25×)" accuracy 0.99 for AudioSeal versus 0.50 for WavMark. Training used speed 0.9–1.1. AudioMarkBench was not checked, so the conflict is unresolved rather than settled. |
| High | Traceweave must mandate stratified demographic calibration, with no profile promoted without false-positive parity (Nemecek 2026). | **U** | An invented project requirement drawn from an unchecked source. The general point that calibration populations must be stated is already in the checklists. |
| Medium | AudioSeal: 16-bit messages, single-pass localized detector, "100× faster detection", "10× faster generation", SI-SNR > 25 dB, survives EnCodec. | **S / P / V** | B1: 16-bit messages **S**; "up to two orders of magnitude faster detection" **S**; generation speedup **V**; SI-SNR 26.00 and PESQ 4.470 (Table 1) **S**, though the authors stress they do not optimize SI-SNR; EnCodec accuracy 0.98 (Table 3) **S**, bitrate not confirmed. MIT repository licence (commit `1496f76`); weight terms not checked. Version cited as "Jan 2024"; v2 is 2024-06-06. |
| Medium | Stable Signature: 48 bits; c ≥ 41 gives FPR ≤ 10⁻⁶; 90+% after 10% crop; PSNR ≈ 30.2, SSIM ≈ 0.895, ΔFID −0.3; "CC-BY-NC main, MIT for core submodules". | **S / P** | B2: τ = 41 for N = 1 at FPR 10⁻⁶, and the 10%-crop claim, are **S**. Table 1 text-to-image row is 30.0 / 0.89, ΔFID −0.3, so **P**. The README says CC BY-NC with `src/ldm` and `src/taming` under MIT; those are vendored dependencies, not the "core". It is a generation-time decoder fine-tune, not a post-hoc mark. |
| Medium | C2PA Soft Binding Resolution API with `/matches/byContent` and `/matches/byBinding`. | **S** | B3 lists both routes plus `/matches/byReference`, and fingerprint fallback. The report's version citation "v1.2, Dec 2021 §9.1–9.3, §18.7" was not checked. |
| Medium | Kirchenbauer: z ≥ 4 gives p < 3.17×10⁻⁵; repository defaults γ = 0.25, δ = 2.0, h = 4, selfhash. | **S / P** | The z-tail arithmetic is correct. The evidence review (T, T-code) shows the repository now recommends an extended processor. Mixing those defaults with original ICML measurements is the conflation its checklist flags. |
| Medium | DEW figures (0.746 TPR at DP-20; 0.650 / 0.498 under translation; 3.71 s to 4.97 s), Watermark under Fire collapse, PGID removal/forgery figures, Hwang 2024. | **V** | Not checked. All are generation-time text or diffusion results with no bearing on post-hoc Traceweave carriers until checked. |
| Low | Numeric confidences 0.90 and 0.35. | **U** | Uncalibrated numbers presented as probabilities. |
| Low | Handoffs to "Container Engineering", "Applied Statistics", "Cryptographic Protocol" and "Ethics and Policy" lanes. | **U** | Invented project structure. The underlying points (composite assets, no multiplying of correlated evidence, private lookup) are consistent with the evidence review. |

## Additional primary-source checks (three)

Fetched 2026-11-22 with read-only HTTP (each returned 200). Repository heads were read through GitHub's API.

| ID | Source | Locations used |
| --- | --- | --- |
| B1 | San Roman, Fernandez et al., *Proactive Detection of Voice Cloning with Localized Watermarking*, [arXiv:2401.17264v2](https://arxiv.org/abs/2401.17264v2), 2024-06-06, CC BY 4.0. [Repository](https://github.com/facebookresearch/audioseal) MIT, head `1496f7662d6aa625602bb0dcd1b4997b63b47609` | Abstract (speed); Table 1 (SI-SNR/PESQ); Table 3 (edits, Fast 1.25×, EnCodec); attribution setup (16-bit messages); App. D.2 augmentation ranges |
| B2 | Fernandez et al., *The Stable Signature*, [arXiv:2303.15435v2](https://arxiv.org/abs/2303.15435) PDF. [Repository](https://github.com/facebookresearch/stable_signature) LICENSE (CC BY-NC 4.0) and README licence section, head `c91217c06e953a4eaf270ef9de4a3939bcea3366` | Fig. 1 / intro (10% crop, FPR < 10⁻⁶); detection section (τ = 41 for N = 1, τ = 44 for N = 1000); Table 1 |
| B3 | C2PA [Implementation Guidance 2.4](https://spec.c2pa.org/specifications/specifications/2.4/guidance/Guidance.html) and [Soft Binding API 2.2](https://spec.c2pa.org/specifications/specifications/2.2/softbinding/Decoupled.html) | Guidance §4.1 (hard binding required; soft-binding collisions); Soft Binding Resolution API routes; Soft Binding API §1.4 OpenAPI (`/matches/byBinding`, `/matches/byContent`) |

## Flags

- **Invented thresholds:** all §5.3 abstention floors, §5.7 acceptance/rejection recalls and FPRs, the GPU-hour and storage budget, and the 0.90/0.35 confidences.
- **Invented project requirements:** a demographic-parity mandate, the `traceweave://` profile URI scheme, a uniform status enum, and four new lanes.
- **Unsupported guarantees:** "the determination is definitive"; marks as "probabilistic locators" whose resolution FPR is "analytically bounded"; "zero execution impact"; "only verified mechanism".
- **Proposed schema names:** `traceweave.carrier.report`, `traceweave.soft_binding.resolution`, `c2pa.softbinding.audioseal`, `status_code`, `confidence_score`, `resolved_manifest_id`, `soft_binding_handle`, `inferred_model_id`.

## What survives

1. A common evidence record with profile-specific coordinates, statistics and distortion measures. This matches the evidence review's proposed container, minus the merged status/confidence fields.
2. C2PA's soft-binding lookup (B3) is a documented, existing pattern for re-associating a stripped asset with a signed record through a decoded mark or fingerprint. Hard binding stays mandatory. A Traceweave locator protocol would still be unimplemented. A hosted `/matches/byContent` route discloses the asset, so the local/private lookup the evidence review prefers remains the safer default.
3. Representative choice changes. Text (generation-time logits) and Stable Signature (generation-time, non-commercial code) cannot mark existing artifacts. AudioSeal is post-hoc with an MIT-licensed repository and 16-bit messages. The evidence review's TrustMark choice (post-hoc, 61 data bits by default, ReMark removal supplied) is not undermined by anything checked here. The report never evaluates it.
