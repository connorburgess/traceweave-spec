# Independent review: research 06–08 checkpoint (draft)

> Adoption note: the checkpoint reviewed here was adopted as [research-06-08-checkpoint.md](../research-06-08-checkpoint.md). Line references (`L<n>`) point to the draft as committed in `6f75d55` (`research/drafts/research-06-08-checkpoint.md`).

Reviewed 2026-11-22. Target: `research-06-08-checkpoint.md` (113 lines), with the 07 and 08 report audits and the 06/07/08 evidence reviews. Read-only. The reviewer did not write any of these files. Line numbers refer to the checkpoint unless a file is named.

**Verdict: adopt after fixes.** The two audits and the checkpoint's reasoning are mostly sound. One recommendation is overstated, one cited figure is untraceable, and the proposed image study is not yet specified well enough to authorize.

## Verification performed

- **Hashes.** `shasum -a 256` of the three captures in `.local/research/google/` matches the audits. 07 is `8c19c143…dfab` and 08 is `716a4d1b…03df`. 06 is `b7b9154a…c53a`, as recorded in `06-evidence-review.md:100`. The files are git-ignored (`.gitignore:1`).
- **Links.** Every local link in the checkpoint resolves (lanes 06/07/08 files, the census checkpoint). The checkpoint has no external links.
- **Primary-source spot checks** (read-only HTTP, all returned 200):
  1. **TetherMark** (arXiv 2611.22345v1, HTML) Table 1.
     - Confirmed: TetherMark ASR is 9.17% (WmForger) and 16.25% (WMCopier), with TAR 92.08% over 240 subjects.
     - Confirmed: TrustMark-P ASR is 80.00% and 90.83%, so "80–91%" at L18 is correct.
     - The 07 audit never records the TrustMark-P row (see finding 3).
  2. **CLASP** (arXiv 2510.11251v2). Table 7 shows direct bit prediction without original code at 52.01%. §5.5 tests 2, 4, 6, 8, 16 and 32 bits, and CLASP "maintains high BitAcc" at 16 and 32 bits. Confirmed. The report's "30–100 bits" is wrong, as the audit says.
  3. **AudioSeal** (arXiv 2401.17264v2) Table 3. Fast 1.25× accuracy is 0.99 for AudioSeal versus 0.50 for WavMark. Confirmed. L27 quotes only the AudioSeal half.
  4. **Stable Signature.** `LICENSE` at commit `c91217c` is CC BY-NC 4.0, so "CC BY-NC code" (L20) holds.
  5. **10,000-negatives bound.** With zero events in 10,000 independent negatives, the 95% one-sided upper bound is 1−0.05^(1/10000) = 2.995×10⁻⁴. The 08 audit's "about 3×10⁻⁴" is correct. At 10⁻⁴ or 10⁻⁶ the claim is unattainable, so L72 is right.

## Findings, most severe first

**1. High. The carrier decision overreaches (L13, L33, L41).**
- L13 says "No published code carrier transfers". The evidence covers only SrcMarker, RoSeMary, SEW, CLASP and PLACEMARK. The 06 report's own candidate (Nata'ala, Research Square) was never read: the DOI returned 403 (`06-evidence-review.md:132`). DeCoMa and CodeMark are quarantined as unchecked.
- A negative result about reviewed candidates is not proof that none exists.
- L33 ("no embedded-mark candidate clears the bar") is a claim about the reviewed set and should say so.
- CLASP is cited for blind collapse (L15), but the project's own recovery is reference-assisted. CLASP in reference mode has the best-measured capacity (2–32 bits, clean 97.85–99.72%).
- The real reasons CLASP fails the bar are different: it has no typed safe subset, no Go/Rust measurement, and no cheapest-normalizer test. Say that instead.
- **Fix:** reword to "none of the reviewed candidates (list) meets the bar; Nata'ala remains unverified; absence of a carrier is not established". Replace the L15 argument with the bar-based reason.

**2. High. The image study is under-specified (L52–72).** The study states pins and an outcome taxonomy but omits the following:
- **Data.** There is no image count, resolution set, generation method, or negative-set size. Without n, the "exact binomial bounds" (L72) have no resolution. For example, 1,000 negatives give about 3×10⁻³.
- **Compute.** There is no wall-clock, disk or weight-size estimate. L52 says "runs on CPU", but the 08 review says only that the loader selects CPU, MPS or CUDA (`08-evidence-review.md:50`). CPU use and offline use are undemonstrated.
- **Failure.** The only failure statement says transplant acceptance is not one (L70). No criterion states when the study fails: clean decode below some rate, wrong-decoder or negative false decodes, BCH erasure rate, or ReMark removal. "Frozen" thresholds also never name their split sizes.
- **Licences.**
  - Repository MIT is noted. The weight-file licence is flagged unchecked. Dependency licences are not mentioned.
  - The 08 review says the loader downloads weights from an Adobe host if missing, but "provision once" (L56) does not say who authorizes that network access or the package install.
- **Owner-only items to flag.** These are the weight licence acceptance, permission for the one-time weight and dependency download, the install location, and the decision to spend any effort at all. None is marked as needing the owner. L111 says only "authorize, defer or reject".
- **Fix:** add a table with n for each condition, a time and disk budget (or "unmeasured, owner to bound"), explicit stop and failure rules, and an "Owner needed" list.

**3. Medium. An untraceable figure, and a transfer inference stated as expectation (L18, L70).**
- "80–91%" is cited to "07 audit, A1". The audit does not contain it. It records only the ranges 77.92–100% and 85.42–99.17%, and 9.17%/16.25%.
- The number is correct in the primary source, but the claim does not trace to an audit entry. Add the row to the audit or cite Table 1 directly.
- The TetherMark attacks are WmForger and WMCopier forgery attacks. They are not a literal residual transplant. L70's "expect transplant acceptance" is an extrapolation, so label it a hypothesis.
- TetherMark is a five-day-old unreviewed preprint (2026-11-17) with author-run attacks. Say so.

**4. Medium. Project failure called "general" (L17).** The 55/55 erasure comes from two narrow synthetic carriers (`experiment-checkpoint.md:9–13`). The census covers four repositories and found zero established eligibility. Neither shows the failure is general. The "Go string counterexample" is unexecuted (`06-evidence-review.md:111`). Operand sorting as an eraser is an inference about a safe subset, not a measurement. **Fix:** "in the narrow carriers tested", and label the counterexample unexecuted.

**5. Medium. The dual-role fingerprint baseline is a new, unsupported claim (L77).**
- TetherMark's relation check is a keyed, enrollment-relative patch-pair reader on images.
- `08-evidence-review.md:44` warns that fingerprint evidence "may share failure causes with a mark".
- No source shows that an exact or normalized span matcher gives a transplant-resistant relation check for code.
- **Fix:** state it as a design hypothesis to test, not an assumption that one artifact answers two questions.

**6. Low. "Every numeric threshold in the three reports is invented" (L26).** The 08 audit shows Stable Signature τ=41 at FPR 10⁻⁶ is supported (B2). Say "every threshold the audits flag as unsupported".

**7. Low. Time-scale evidence is one-sided (L27, L85).** Table 3 shows WavMark at 0.50 for 1.25×. Add this, then say whether WavMark stays a candidate, as L85 implies. AudioMarkBench remains unchecked.

**8. Low. The SEW check prejudges its result (L43–50).**
- It says the "expected result is a documented rejection". It should be framed as a falsification test with a pass/fail rule.
- SEW was evaluated on Python, Java and C++; the unexecuted counterexample is Java.
- The Go counterexample comes from the Go spec, not SEW code. The checkpoint does not say which language the "tiny synthetic hosts" use.

**9. Low. The unchecked-source list is incomplete (L29).** It omits DeCoMa, CodeMark, Sharma–Coumou, Xiang 2014 and the image-attack survey, all named as unchecked in the audits.

## Item checks

- **(1) Traceability.** Apart from finding 3, every decision-relevant claim traces to an audit or review entry (CLASP 52.01%, PLACEMARK, TetherMark 9.17/16.25, C2PA, Stable Signature, RS erasure versus error).
- **(2) Carrier decision.** It follows for the reviewed set and for the project's own bar (findings 1 and 4). The bar itself is from the census checkpoint, not re-derived here.
- **(3) Image experiment.** Findings 2 and 3.
- **(4) Leakage.** None found. Report thresholds, `VERDICT_*`, `lineage_id`, `traceweave.carrier.report` and the Merkle gate appear only as rejected (L26–28). The shared-record idea and the C2PA precedent are the accepted survivors (08 audit "What survives"), and the checkpoint labels them non-normative.
- **(5) Links.** Local links resolve; there are no external links to test.
