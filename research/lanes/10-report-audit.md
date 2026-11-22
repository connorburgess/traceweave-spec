# Lane 10: NotebookLM report audit

Prepared 2026-11-22. Companion to the [lane 10 evidence review](10-evidence-review.md); this audit applies its source ledger (F1–F8) and claim-audit checklist. The report is a hypothesis source, not a requirement. **Verdict: reject the report's recommendation, acceptance gates and specification mandates as written.** Keep its decisive primary source, a 2026 benchmark preprint (X1), which I checked directly: it changes the evidence review in four places, listed at the end. Most of the report's headline numbers are copied correctly from X1. The errors are in what it does with them:
- it applies a video-only cross-host result to still images;
- it presents preprint author results as "peer-reviewed benchmarks and multi-source replications";
- it attributes TetherMark's defended rates to "conventional watermarks";
- it turns observations into normative "must" rules.

## Capture identity and limitations

| Field | Value |
| --- | --- |
| Supplied by | Coordinator, 2026-11-22. I did not open the notebook, query it or change it |
| Artifact | Studio report titled "Traceweave Still-Image Profile: Technical Evaluation and Candidate Selection (10-image-profile.md)" |
| Raw capture | `.local/research/google/10-image-profile-ui.txt` (git-ignored by `.gitignore` `.local/`; read only) |
| Size | 39,252 code points; 39,515 bytes; 425 lines |
| SHA-256 | `86550fcbc961f93273943643a818dc4acced1caf67f767929eac41a98de3039f`, checked before and after this audit |

Limitations:
- **Not a native export.** The capture is rendered Studio text, so maths is broken across lines (for example `P` / `FM` / `≤6.2×10` / `−7`) and tables are tab-separated.
- **No citation markers.** Claims cannot be traced to the notebook's imported sources.
- **Notebook metadata not supplied.** Source count and notebook ID were not given to this lane.
- **Bounded checks.** I made three additional primary-source checks (X1–X3), so the rest of the report's ledger stays unverified.

## Claim-by-claim audit, by decision impact

Status: **S** supported, **P** partly supported or overstated, **U** unsupported (no evidence offered), **C** contradicted, **V** unverifiable in this pass.

| Impact | Report claim | Status | Basis |
| --- | --- | --- | --- |
| Blocker | Recommend one experiment: PixelSeal at α = 0.20 with an expected-payload test, k = 167 of 256 and analytic P_FM = 6.2×10⁻⁷, against a PDQ baseline. | **P** | X1 Table 8 gives k/n = 167/256 and P_FM 6.2×10⁻⁷ as a theoretical per-key value. The observed evidence is 0/340 trials on 85 unmarked sources, a 95% upper bound of 0.042, and X1 §4.4 says the 10⁻⁶ "rests on the theoretical value". With N catalogue keys, the per-query bound is min(1, N×10⁻⁶) (X1 §3.3). A real candidate (X3), but the experiment as specified breaks standing limits (next row). |
| Blocker | Protocol §5: dual A100 and Apple nodes; PyTorch with weights; 1,000 "synthetic photorealistic" images; gates PSNR ≥ 45 dB, FLIP ≤ 0.030, bit accuracy ≥ 0.95, TPR ≥ 0.99, 0/50,000 false matches "(P_FM ≤ 10⁻⁶)". | **C** (scope) / **U** | It needs GPU hardware and a weight download from `dl.fbaipublicfiles.com` (X3), both owner decisions. All five gate values are invented. **Internal contradiction:** 0 events in 50,000 comparisons bounds the rate only near 6×10⁻⁵, not 10⁻⁶, and comparisons drawn from 1,000 images are correlated: X1 counts sources for exactly this reason. "Photorealistic" images from "procedural noise seeds" is undefined. |
| Blocker | TrustMark is "disqualified" by its blind-detector false positives of 5.9–15.3%. | **P** | The rates are **S**: X1 Table 8 per source, 85 sources, any of four decodes; for example Q 8/85 (upper 0.18), C 13/85 (upper 0.25). The same table shows 0/340 false matches for every TrustMark variant under the expected-payload test (k = 74/100). This disqualifies blind BCH success as presence evidence, not TrustMark. |
| Blocker | Cross-platform: "decoded watermark bits flipped between x86 and ARM hosts" for still-image decoders; the spec must mandate a portable colour pipeline. | **C** for images | X1 §4.6 and Table 10: the flips occurred in 2 of 13 **video** files (Video Seal, H.264 YUV→RGB), up to 2 of 256 bits. TrustMark-Q on a JPEG-75 image changed no bit across hosts. X1 §5.7: PDQ and the ISCC codes were bit-identical across hosts on 200 PNG files. The portable-conversion advice is X1's, for video. |
| Blocker | "Anchored directly in published, peer-reviewed benchmarks and multi-source replications"; confidence High. | **C** | X1 is an arXiv v1 preprint (2026-10-02), run by its authors. Its authors work for Original Pictures Technologies (competing-interests section), the registrant of the `com.originalpictures.*` PDQ, TMK+PDQF and vPDQ soft-binding ids in the C2PA list (F8). No independent replication was checked. |
| High | Transplant: in "conventional schemes" the transplanted payload decodes; the 9.17% and 16.25% rates are for "conventional watermarks". | **C** / **P** | F7 Table 1: 9.17% and 16.25% are TetherMark's own rates with relation gating. The conventional TrustMark-P baseline accepts 80.00% and 90.83%. These are forgery attacks (WmForger, WMCopier), not a literal residual copy. |
| High | Watermarking moves fingerprints: ISCC 62.0%, PDQ 0.00%, SSCD 18%, DINOv2-S 6.0%, DINOv2-S LSH-256 21%. Register the fingerprint of the marked asset. | **S / P / V** | X1 §6: ISCC 62.0% **S**; PDQ 0.3% and SSCD 17.7% make the report's 0.00% **C** and 18% a rounding; DINOv2-S 5.7% **P**; the LSH figure is **V**. The advice to register the marked asset's fingerprint is X1's, so **S** as advice. |
| High | DINOv2-S LSH-256 is "unkeyed" and allows thumbnail inversion; manifests must never expose raw continuous vectors. | **C** / **P** | X1 §3.3 defines it as a keyed 384×256 sign projection. X1 §5.6: with any other key, reconstruction is the mean image, identifying images at 0.0%. Float descriptors invert to thumbnails; PDQ leaks 0.2%. The "must never" is a report mandate. |
| High | SSCD: CC BY-NC 4.0 weights and data, "DISQUALIFIED FOR PRODUCTION"; TPR 71.2% at 10⁻⁷ and 69.7% at 10⁻⁸. | **P** | X1 §3.3: the weights carry **no licence of their own**, and the training data DISC21 is CC BY-NC 4.0. The TPRs are **S** (X1 §5.1 and the 10⁻⁸ comparison). "Disqualified" is X1's product-eligibility tier, not a Traceweave rule. Consistent with F3. |
| High | PDQ: survives JPEG, WebP, resize and colour; fails crops ≥ 50%, rotation > 15°, overlays. Dihedral 54.6%. | **P** | X1 §5.1: a crop keeping 70% of each side drops PDQ to 0% Recall@1, so the failure begins before the 50% the report gives. A 15° rotation gives PDQ 0%. Every hash scores 0% on screenshot templates. Dihedral 54.6% and plain 49.5% at pair-level 10⁻⁷ **S**. |
| High | Spec implications: core must forbid unkeyed presence assertions, mandate `/matches/byBinding`, prohibit `/matches/byContent`, and dictate post-mark fingerprinting and colour kernels. | **U** (invented requirements) | These are normative mandates from one preprint. The project prefers local lookup but has adopted no such rule. Normative changes are the owner's (ROADMAP "Needs the owner"). |
| Medium | C2PA 2.4 CDDL includes `? "url": uri ; Manifest resolution endpoint`; spec "commit 5c864efb, April 2026". | **C** / **V** | F8 §18.10: `url` is "Unused and deprecated", and claim generators shall not add it. The commit and date are not checked. The three API routes match the lane 08 audit (B3). |
| Medium | TrustMark-Q 63.5 ms/MP "on an NVIDIA A100"; PixelSeal 9.13 ms/MP; quality figures (PSNR 48.3/45.9, FLIP 0.024/0.030, TrustMark-Q 42.1 dB / 0.0401). | **S / C** | The numbers match X1 Table 3 and the appendix table. X1's GPU host is an **A10G** (§3.1), not an A100. The cost is "c": the CPU is the cheaper host. |
| Medium | Crop bit accuracy: TrustMark-Q 0.510 at 50%-side crop; PixelSeal (0.15) 0.826; WAM 0.964. | **S / V** | X1 §4.1: 0.510 and 0.826 **S**; WAM 0.964 not located (**V**). These are bit accuracies, not whole-payload success. |
| Medium | Union of watermark and fingerprint successes 69% (78% with ISC21); TrustMark 62%, DINOv2-S 61%. | **S** | X1 §6. X1 calls union rates "complementary coverage, not the measured accuracy of a deployed cascade". |
| Medium | 16-bit audio: no 10⁻⁶ threshold exists. Audio fingerprints outperform watermarks; Video Seal covers 92%. | **S** | 2⁻¹⁶ ≈ 1.53×10⁻⁵ is arithmetic. X1 §6: AudioSeal 24% against Chromaprint 67%, Video Seal 92%. Outside this lane's scope. |
| Low | WAVES, MarkNull (100% evasion at 25.36 dB), Bui thesis (DECORAIT 91.2%), Mixpeek guide, pdq-wasm port. | **V** | Not checked. Mixpeek is a vendor guide, not primary evidence. Regeneration removal is already established for other marks by F6. |
| Low | Handoff: code could be mapped to "continuous latent spaces" so deep watermarking transfers. | **U** | No evidence. It contradicts the checkpoint's behaviour-preserving constraint for code carriers. |

## Additional primary-source checks (three)

Fetched 2026-11-22 with read-only HTTP. Repository heads were read through GitHub's API. No weights, corpora or code were downloaded or run.

| ID | Source | Locations used |
| --- | --- | --- |
| X1 | Kazempourradi, Mojtahedi, Mohseni, *Watermarks and Fingerprints as Soft Bindings for Content Provenance: An Open-Licence Benchmark for Images, Audio and Video*, [arXiv:2610.04151v1](https://arxiv.org/abs/2610.04151v1), 2026-10-02, author-run preprint | §3.1 (licence audit; source as unit; A10G and M5 Pro hosts); §3.2.1 Table 1 (TrustMark 100 transmitted / 61 payload bits; PixelSeal 256, MIT/MIT); §3.2.2 (85 images: Kodak 24, DIV2K 25, CLIC 28, HDR 8); §3.3 (DISC21 CC BY-NC; SSCD weights unlicensed; keyed LSH; union bound N×10⁻⁶); §4.4 and Table 8; §4.6 and Table 10; §5.1; §5.2 (PDQ at pair 10⁻⁷: 267 false bindings / 26,820 held-out queries, 1.00%); §5.6 inversion; §5.7 cross-host hashes; §6; competing interests |
| X2 | Benchmark repository [Original-Pictures/soft-bindings-benchmark](https://github.com/Original-Pictures/soft-bindings-benchmark/tree/6158ae83b55e3353217e4562ddaf7ff56da1e9b5), head `6158ae83b55e3353217e4562ddaf7ff56da1e9b5` (2026-10-02), Apache-2.0 per the GitHub licence API | Exists and is licensed as X1's "Data and Code Availability" section states. Contents, lockfiles and reproducibility were not inspected |
| X3 | Souček et al., *Pixel Seal: Adversarial-only training for invisible image and video watermarking*, [arXiv:2512.16874v1](https://arxiv.org/abs/2512.16874v1), 2025-12-18; code [facebookresearch/videoseal README](https://github.com/facebookresearch/videoseal/blob/f12875a9b5e711e0c6e2dc3a22aca18231ce4a1a/README.md) at `f12875a9b5e711e0c6e2dc3a22aca18231ce4a1a` | Paper: embedder adds α-scaled residual to an existing image; nbits = 256; trained on SA-1B (training section). README: "All models … released under MIT"; PixelSeal checkpoint hosted at `dl.fbaipublicfiles.com`; `videoseal.load` downloads on first use. SA-1B dataset terms not checked |

## Flags

- **Invented thresholds:** the §5.4 gates (PSNR ≥ 45.0, FLIP ≤ 0.030, bit accuracy ≥ 0.95, TPR ≥ 0.99, 0/50,000); the quality-refusal gate (SSIM < 0.60, PSNR < 20 dB); α = 0.20 as a profile value (X1 used it as one setting, and its combined-score pick is 0.15).
- **Invented project requirements:** forbidding unkeyed presence in "Traceweave core"; mandating `/matches/byBinding` and prohibiting `/matches/byContent`; mandating fingerprint sequencing and a colour kernel; the "fully air-gapped … must" wording, where the brief says local verification "must be possible".
- **Unsupported guarantees:** "verified resistance", "bounded false-positive rates", "cryptographic reliability" from an expected-payload test; "High" confidence; "multi-source replications"; "Δbits = 0" presented as an achievable gate rather than a measured outcome.
- **Proposed schema names:** none new. The report reuses `c2pa.soft-binding` and C2PA routes and introduces no Traceweave field names. Its "Expected-Payload Verification Rule" and abstention symbol (⊥) are proposals, not adopted terms.

## What survives

1. **Expected-payload verification, not blind decoding.** For TrustMark, BCH success on unmarked images is common (X1 Table 8). A k-of-n match against the payload the verifier expects is the decision rule the evidence supports. Its 10⁻⁶ is analytic and per key; the measured bound is only 0.042 per source.
2. **PDQ and ISCC already have a large calibrated measurement.** On 98,985 registry items, the threshold was fixed on held-out negatives (X1 §5). PDQ: 1.00% per-query false bindings at its strict threshold on a product catalogue; geometric failures from 70%-side crops and 15° rotation; 0% on screenshot templates; bit-identical across x86 and arm64.
3. **Watermarking moves the ISCC code in 62.0% of images.** A combined profile must register the fingerprint of the marked asset.
4. **PixelSeal is a second credible post-hoc mark candidate.** It carries 256 bits under MIT code and README-stated MIT weights, and X1 ranks it best for images. Its weight download, SA-1B training terms and removal and transplant behaviour are unverified here.
