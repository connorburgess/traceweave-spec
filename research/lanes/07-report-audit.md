# Lane 07: NotebookLM report audit

Prepared 2026-11-22. Companion to the [lane 07 evidence review](07-evidence-review.md), whose source ledger (S1–S3) and claim-audit checklist this audit applies. The report is a hypothesis source, not a requirement. **Verdict: reject the report's proposed experiment and specification changes as written; keep three narrow, primary-supported points** (listed at the end).

## Capture identity and limitations

| Field | Value |
| --- | --- |
| Notebook | `26268423-7182-45d4-8f34-bf018da9463d` ("Traceweave 07 — Fragment Recovery and Transplant Resistance"), owner's signed-in account, BB desktop browser |
| Captured | 2026-11-22, read only; no query, source change, share or new research |
| Artifact | Studio report `07-fragment-recovery-transplant.md`, labelled "33 sources · 8h ago" |
| Raw capture | `.local/research/google/07-fragment-recovery-transplant-ui.txt` (git-ignored; not edited after capture) |
| Size | 39,252 code points; 39,627 bytes; 648 lines |
| SHA-256 | `8c19c143485085c5ce2e69c6a2ac2c2b39018e5c9f3bcfea7805faf7de69dfab` |

Limitations:
- The center-chat answer only says the report was "published to your Studio panel". The capture is the rendered `innerText` of that Studio report, not a native Markdown export.
- Rendered maths is broken across lines (subscripts split, for example `x` / `query`). Tables are tab-separated, and ledger URLs are run into the adjacent cell text. The capture also includes UI words (`open_in_new`, `thumb_up`).
- NotebookLM citation markers are not present, so claims cannot be traced to specific imported sources.
- Opening the Studio item cleared its "Unread" label. That was the only account state changed.

## Claim-by-claim audit, by decision impact

Status: **S** supported, **P** partly supported or overstated, **U** unsupported (no evidence offered), **C** contradicted, **V** unverifiable in this pass.

| Impact | Report claim | Status | Basis |
| --- | --- | --- | --- |
| Blocker | Next experiment: a dual-layer Go/Rust engine whose payload rides on commutative operand pairs and independent statement orders. | **C** | This is the carrier the [lane 06 audit](06-evidence-review.md) rejected. Operand sorting is a cheap valid normalizer that erases the choice. There is a Go string-concatenation counterexample to "safe" commutation. No typed safe subset is defined. The census found no established safe eligibility. Report Arm 8 itself predicts erasure. |
| Blocker | Relation channel `C_rel = MerkleRoot(NormalizedASTSubtrees)` with gate `C_rel ≥ 0.80`. | **C** (internal) | A Merkle root is an exact commitment: equality is binary, so a 0.80 threshold is undefined. A 50% fragment cannot reproduce the root, yet Arm 2b expects the gate to pass. A graded relation needs a similarity/fingerprint method, which is the roadmap's unbuilt baseline. |
| Blocker | TetherMark shows that relation gating defeats transplantation, and the paradigm adapts to source code. | **P** | Checked (A1). A1 is a recent preprint (v1, 2026-11-17), not peer reviewed, and its attacks were run by the authors. It covers images only, with 240 subjects. Pooled TAR is 92.08%. Table 1 gives attack success (ASR) of 9.17% under WmForger and 16.25% under WMCopier. Those two are forgery attacks evaluated by the authors, not a literal residual copy. The relation is a keyed, enrollment-relative patch-pair reader on images. Attacks still succeed 9–16% of the time. Transfer to code ASTs is the report's inference, with no measurement. |
| Medium | (Not in report; recorded for the checkpoint.) Baselines without a relation check accept forged evidence. | **S** | A1 Table 1, TrustMark-P row: ASR 80.00% under WmForger and 90.83% under WMCopier, over 240 attempts each, as reported by the authors. This measures those two forgery attacks only, not a residual transplant onto unrelated images. |
| High | Baseline detectors without instance binding suffer 85.4–92.5% ASR. | **C** | A1 Table 1: baseline ASR spans 77.92–100% (WmForger) and 85.42–99.17% (WMCopier). 92.5 does not appear. The table row "Material TAR 85.42–92.08%" mixes a Table 2 per-condition value with the pooled TAR. |
| High | Thresholds τ_BER = 0.25, τ_rel = 0.80, τ_H = 4.5 bits, FPR ≤ 10⁻⁴; expected BER per arm (≤0.05 at 75%, ≤0.15 at 50%, ≥0.35 at 25%). | **U** | Invented values, presented as "theoretical expectations" with no derivation. The lane 07 checklist rejects universal fragment floors without a profile budget. 200 synthetic modules cannot support an FPR of 10⁻⁴ under clustering. |
| High | RS(32,16) "corrects up to (n−k)/2 missing blocks". | **P** | RS corrects up to n−k *erasures* or ⌊(n−k)/2⌋ *errors*. The report does not say which applies, and gives no synchronization or indexing budget (S1). |
| High | Verdicts `VERDICT_AUTHENTIC` ("assert authentic descendant") and `VERDICT_TRANSPLANT` ("declare forged attribution attempt"). | **C** | Overclaims both ways. Authentication plus binding does not establish ancestry or authorship (evidence-review verdict table). A failed relation check is also consistent with legitimate heavy editing. The names are proposed schema names; none is adopted. |
| High | Spec changes: `spec/embedded-marks.md`, `spec/extracted-fingerprints.md`, `spec/provenance-signatures.md`; manifest fields `lineage_id`, `payload_binding`, `instance_relation`, `abstention_policy`. | **U** | Invented project requirements and schema names, outside this research scope. Normative files are unchanged. The underlying separation of results already exists in the [fragment checkpoint](../fragment-policy-checkpoint.md). |
| High | Project findings: Go/Rust carriers "entirely erased under canonicalization"; census shows negligible eligibility for "suffixed literal assignments or swappable statements". | **P** | Normalization reset all 55 nonzero states per language ([experiment checkpoint](../experiment-checkpoint.md)). Both survived gofmt/rustfmt. The four-repository [census](../public-census-checkpoint.md) did not measure swappable statements. It records zero *established* eligibility, not "near-zero across real-world repositories". |
| High | "Formatting erasure floor": CI formatters guarantee erasure of non-semantic marks; lexical marks have zero survivability. | **C** | Project measurement: declaration-order and naming states survived gofmt/rustfmt. Formatters also keep comments and identifier choices. Erasure came from a separate normalizer, which is the real attack to test. |
| Medium | CLASP: blind extraction collapses to 52.01% bit accuracy without a reference; clean 97.85–99.72%; attacked 76.93–90.35%; capacity "30–100 bits per function". | **S / P / C** | Checked (A2, v2 HTML): Table 7 direct prediction 52.01% (MBJP) **S**; the clean row matches **S**. The attacked range is selected column extremes **P**. Section 5.5 tests 2–32 bits, so "30–100 bits" is **C**. The report cites v1 (cs.SE, 2025-10-13); the numbers were checked on v2 (cs.CR, 2026-04-20). |
| Medium | PLACEMARK: 249–2,166 bits; 216 exact trials; renaming drives BER to 0.36–0.52; "fails on Go/Java". | **S / P** | Checked (A3, v1, 2026-10-15, cs.CR; the report says 26 Oct and cs.SE): capacity in 9 of 10 repositories, 216 exact trials and the BER ranges are **S**. The authors evaluate Python only. For Go they state that relocation would require editing the file, losing the property. "Fails" is an unmeasured inference **P**. There is still no Go evidence for a placement carrier. |
| Medium | HSPMark: 93.34% bit accuracy on a 25% snippet with a w-sentence warm-up. | **V** | Not checked. The report cites both "Table 7" and "Table 9" for it. Generation-time text logits do not transfer to post-hoc code. |
| Medium | Davey–MacKay inner markers plus outer codes as the synchronization remedy; IDS channel framing. | **P** | Consistent with S1 (synchronization is an encoded resource). Sharma–Coumou corpus details ("PSOLA", "Buckeye") are **V**. |
| Medium | "Theorem": any edit invalidates an embedded signature over H(x₀). | **P** | The logical point matches project evidence: exact-byte signatures do not cover derivatives. "Probability 1−2⁻²⁵⁶" is decorative precision, not a theorem from a cited source. |
| Low | Collberg–Thomborson 1999 cited as PLDI; dynamic PPCT overhead ≤15%. | **V** | Not checked. The venue is suspect (the paper is commonly cited as POPL 1999). Runtime heap marks are out of the source-only scope. |
| Low | C2PA 2.4: soft bindings never replace hard bindings. | **P** | The [C2PA 2.4 guidance](https://spec.c2pa.org/specifications/specifications/2.4/guidance/Guidance.html) §4.1 requires a hard binding on every manifest and notes collision attacks on soft bindings. "Fingerprint re-verification against transplantation" is not stated there. |
| Low | Video phase coding, Xiang 2014, image-attack survey, Research Square AST paper. | **V** | Not checked. The Research Square DOI already failed in the lane 06 audit (HTTP 403). |

## Additional primary-source checks (three)

All fetched 2026-11-22 with read-only HTTP (each returned 200). Numbers are author results, not replications.

| ID | Source | Locations used |
| --- | --- | --- |
| A1 | Wei et al., *TetherMark*, [arXiv:2611.22345v1](https://arxiv.org/abs/2611.22345), cs.CR, 2026-11-17 (unreviewed preprint), CC BY 4.0 | Abstract; Eq. (1)/(11) joint accept rule; Table 1 (ASR/IBA over 240 attempts; baseline rows including TrustMark-P 80.00/90.83); Table 2 (TAR per edit); MessageValid at ≥71/100 VINE-B or 32/32 WAM bits |
| A2 | Xu et al., *CLASP*, [arXiv:2510.11251](https://arxiv.org/abs/2510.11251), v2 HTML, cs.CR, 2026-04-20 | Accuracy table (clean bit accuracy); robustness table; §5.5 capacity 2–32 bits; Table 7 ablation |
| A3 | Mohamed, Fathy et al., *Blind Watermarking of Software Repositories via Module Placement*, [arXiv:2610.21031v1](https://arxiv.org/abs/2610.21031), cs.CR, 2026-10-15 | Abstract (249–2,166 bits, 216 trials); renaming table (BER 0.36–0.52); scope limits (Python only; Java/Go bind directory to package) |

Unchecked report sources stay quarantined: HSPMark, video phase coding, Sharma–Coumou, Xiang 2014, Collberg–Thomborson, the image-attack survey and the Research Square paper.

## Flags

- **Invented thresholds:** τ_BER 0.25, τ_rel 0.80, τ_H 4.5 bits, FPR ≤ 10⁻⁴, per-arm BER expectations, 150–500-line modules, 200-module corpus size.
- **Invented project requirements:** the three new spec documents, manifest extensions, a mandatory verifier API shape, and three new "lanes" (fingerprint engineering, formal verification, provenance ledger).
- **Unsupported guarantees:** "Confidence High" in the bound; "guarantees erasure" by formatters; "zero survivability" of lexical marks; transplant "proves" from a relation failure; "100% detection" expected in Arm 1.
- **Proposed schema names:** the `VERDICT_*` / `ABSTAIN_*` states, the State E/I/A/W/T letters, `lineage_id`, `payload_binding`, `instance_relation`, `abstention_policy`.

## What survives

1. Forgery and transplantation are distinct failures from erasure. A message-only detector accepts forged evidence, and an instance/relation check is a separate result that can reduce but not eliminate it (A1: images only, recent unreviewed preprint).
2. Reference-assisted extraction is a real dependency for structural code marks (A2 ablation). Keep blind and reference-assisted results separate, as the evidence review already requires.
3. Repository-placement marking has no Go evidence (A3 authors' own limit). Do not import it as a Go/Rust carrier.

Everything else adds nothing beyond the [evidence review](07-evidence-review.md) or conflicts with it. Its checklist items on observed-versus-reconstructed symbols, duplicate anchors and full-search calibration are not addressed by the report's plan.
