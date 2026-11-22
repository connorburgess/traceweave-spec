# Lane 07: bounded primary-evidence review

Prepared 2026-11-22. **Report-audit pending:** the coordinator has not supplied the exported NotebookLM/Google report. This file reviews three primary papers now; it does not review, endorse or reconstruct that report. Reports are hypotheses, not normative requirements.

## Decision and scope

Keep the current complete-function, reference-assisted recovery boundary until a separately specified alignment method has evidence. Do not add identity framing to compensate for erased carriers or unknown useful capacity. The strongest alternative is the already proposed synthetic token-fingerprint comparison baseline, with ambiguous/common-code matches retained explicitly. Confidence is high in these measurement boundaries, low in any prediction of a new carrier's practical fragment recovery.

This is a bounded evidence review, not a new experiment, corpus survey, implementation audit or normative proposal. The three sources below concern communication-channel coding and natural-language watermarks. None directly measures behavior-preserving Go/Rust fragment marking. No external code was downloaded or executed. Browser control, NotebookLM research/export and decision reconciliation remain with the coordinator.

Local context read at checkout HEAD `8d5e6a707ef52201951e9b94cb15a508aa35dda3`, including uncommitted checkpoint files: [lane brief](../prompts/07-fragment-recovery-transplant.md), [fragment policy](../fragment-policy-checkpoint.md), [public census](../public-census-checkpoint.md), [initial experiments](../experiment-checkpoint.md), [detection comparison](../03-detection-evaluation-comparison.md), [lane reconciliation](checkpoint.md) and [work queue](../work-queue.md). The HEAD identifier alone does not identify those uncommitted files. Their results are coordinator-reported evidence, not independently rerun in this review. The newer fragment-policy checkpoint supersedes the initial experiment checkpoint's older commitment-implementation limitation.

## Source ledger and exact support

All URLs below were read on 2026-11-22. Versioned arXiv full texts, rather than abstracts alone, support the findings. No numerical result here is an independent replication.

| ID | Primary source and inspected version | Exact supporting locations | Supported claim and boundary |
| --- | --- | --- | --- |
| S1 | Bernhard Haeupler and Amirbehshad Shahrasbi, *Synchronization Strings: Codes for Insertions and Deletions Approaching the Singleton Bound*. [Full text, arXiv:1704.00807v1](https://arxiv.org/html/1704.00807v1), 2017-04-03; [version metadata](https://arxiv.org/abs/1704.00807v1). Related STOC 2017 DOI: `10.1145/3055399.3055498`; the reviewed text is the preprint, not a checked proceedings comparison. | Theorem 1.1; §§1.1.1–1.1.2; §3; §4, Theorems 4.1–4.2 and Algorithm 2. | Formal result under an encoded insdel-channel model: payload symbols carry synchronization information. Algorithm 2 treats zero or multiple received symbols at an index as erasures before ECC. No code-corpus or source-edit survival measurement. |
| S2 | John Kirchenbauer et al., *On the Reliability of Watermarks for Large Language Models*, ICLR 2024. [Full text, arXiv:2306.04634v4](https://arxiv.org/html/2306.04634v4), 2024-05-01; [version metadata](https://arxiv.org/abs/2306.04634v4). | §3.2; §4 experimental setup and §4.2; Appendix A.3, Figures 7–8; A.9.1, Equation (4), Figure 19. | Author experiments on text; WinMax maximizes a contiguous-window score and is calibrated against non-watermarked text because of multiple testing. A.3 checks repeated n-gram effects. Neither a Go/Rust guarantee nor a multi-key/reference search calibration. |
| S3 | Nikola Jovanović, Robin Staab and Martin Vechev, *Watermark Stealing in Large Language Models*, ICML 2024, PMLR 235:22570–22593. [Proceedings record](https://proceedings.mlr.press/v235/jovanovic24a.html); inspected [full text, arXiv:2402.19361v2](https://arxiv.org/html/2402.19361v2), 2024-06-24. | §§3–5; §6 threat-model dimensions, stealing parameters and metric definitions; §6.1, Tables 1–2; Appendix B.1, Table 7. | Author-reported spoofing under generation-API access; main setting has no detector access or base responses. Table 7 separately evaluates detector-assisted selection. Not signature forgery or a code-watermark impossibility theorem. |

### S1: synchronization is an encoded resource

Theorem 1.1 gives rate greater than `1 − δ − ε` for a suitable alphabet and decoding within `δn` insertion/deletion distance. Section 4 attaches synchronization symbols to ECC symbols; the receiver first estimates indices, then decodes. This is a formal construction, not measured useful capacity for code. [S1](https://arxiv.org/html/1704.00807v1)

**Traceweave inference:** a source profile must explain how its safe carrier states represent both payload and synchronization. Arbitrary source edits, extracted functions and reordered blocks need an explicit mapping into the claimed channel budget. Losing most of a global codeword is not automatically a locally decodable fragment. The theorem supplies no universal fragment-size floor. Intrinsic anchors avoid explicit indexing symbols only by assuming recognizable content; duplicate anchors still require a policy. ECC inference and reference lookup must not be recorded as symbols observed in candidate bytes.

### S2: window search changes the evaluated detector

WinMax is a presence statistic, not an identity-payload decoder. Its maximum-window score is empirically calibrated on non-watermarked text. Figure 19 reports stronger performance at the severe copy-paste setting; A.3 reports that counting repeated n-grams can understate false positives relative to nominal p-values. These are author measurements for their text settings. [S2](https://arxiv.org/html/2306.04634v4)

**Traceweave inference:** copying a span can preserve a detectable local signal while the host remains unrelated. Calibration must evaluate candidate generation, windows, keys, references and final merging together. Removing duplicate n-grams is not a general cure for duplicate code anchors or correlated candidate windows. Never treat the largest window's ordinary single-test p-value as the full-search p-value, or any p-value as an ownership probability. A union bound does not require independence, but does require valid constituent bounds and a controlled test family; an independence-product calculation needs additional justification.

### S3: detector acceptance and genuine generation can diverge

The main experiments learn from 30,000 watermarked responses of at most 800 tokens each. Section 6 defines quality-filtered attack metrics. Table 2 reports KGW2-SelfHash spoofing rates of 0.81–0.87 across its four displayed model/dataset settings at nominal non-adversarial FPR `10^-3`. The budget estimate uses historical API pricing; it is not a current cost quotation. [S3](https://arxiv.org/html/2402.19361v2)

**Traceweave inference:** a low benign false-alert rate cannot alone establish low adversarial false attribution. Distinguish literal transfer of carrier states from learning a rule and synthesizing new signal. A copied authentic payload need not involve forging a signature. Reproducing a context label is not evidence that the surrounding context was authenticated. This paper motivates separate attack controls; it supplies no attack success prediction for Traceweave's carriers, no proof against all context-binding designs and no ancestry conclusion.

## Claim boundaries for the coordinator

The fragment checkpoint reports 10 localized Go raw states among 24 main queries, and 24 Rust raw states among 72 queries. The remainder abstained. These denominators describe different synthetic cases and cannot be compared as language accuracy. Both decode same-context signal transfers; complete narrow functions relocate, while incomplete or ambiguous anchors abstain. These are project observations reported in the [checkpoint](../fragment-policy-checkpoint.md), not results of S1–S3.

Keep five outputs separate: candidate localization, observed raw symbols, decoded payload, payload authentication and historical inference. Payload authentication is currently unavailable in the carrier experiment; the separate signing harness does not make every recovered raw state an authenticated identity. A decoded identity, if later implemented, would still require an explicit trust policy and a stated bound-content check.

For reference-assisted recovery, every purported observation needs a candidate UTF-8 half-open byte span, extraction rule and raw value. A missing site stays missing. If a future ECC reconstructs a message from surviving candidate symbols, report the received-symbol evidence and decoder output separately. If the reference supplies a value without candidate evidence, classify it as reference-supplied; it contributes zero observed symbols. Even a mathematically valid decoder must not convert its reconstruction into a claimed observed byte span.

Blind search must not silently use a known source, expected payload or winning reference to repair candidate syntax. Reference-assisted search can use a declared catalogue to locate candidates, but ambiguity is an outcome, not permission to select whichever match authenticates. An already-matching raw state is compatible with no intentional insertion.

## Proposed output-verdict table

These are review categories, not new schema fields or normative names.

| Candidate evidence | Mark/payload result | Authentication result | Permitted historical conclusion |
| --- | --- | --- | --- |
| Malformed or unsupported excerpt | Unsupported input; no decoder success | Not evaluated | No supported claim |
| Multiple indistinguishable anchors | Ambiguous location; enumerate candidates or abstain | Separate, if available | No unique localization or ancestry |
| Unique valid anchor with missing sites | Observed subset plus erasures; no reference filling | Not evaluated unless a complete accepted payload exists | No host ancestry |
| Raw states read, framing/ECC absent | Raw recovery only | Unavailable | No identity or insertion-intent claim |
| Payload decodes but authentication fails | Payload bytes retained as unauthenticated evidence | Invalid/untrusted, with reason | No authenticated identity |
| Authentic payload with mismatched exact commitment | Signal/payload can still be present | Signature validity separate from binding failure | No match to the bound artifact |
| Authentic payload and checked bound bytes | State exactly which bytes/record satisfy checks | Valid under declared key/trust policy | Does not alone establish authorship or host ancestry |
| Full configured search finds no accepted result | Not detected within that configuration | No positive authentication | Not proof of unmarkedness |

## Attack/control matrix for a later bounded design

**Unexecuted proposal only.** No fixtures, corpus or experiment are created by this review. Reuse existing synthetic families if the coordinator later authorizes implementation. Do not select parameters here to imply validated thresholds.

| Control or attack | Rival explanation it can test | Required evidence/refusal boundary |
| --- | --- | --- |
| Complete copy with shifted host boundaries | Location dependence versus recognizable complete region | Original candidate UTF-8 spans; expected raw states; keep host ancestry unsupported |
| Progressively shorter valid fragments; gaps | Observed local recovery versus complete-function requirement | Count surviving observed sites and erasures; no automatic wrappers or invented syntax |
| Malformed excerpt | Parser rejection versus accidental repair | Unsupported result before payload claims |
| Duplicate anchors, including competing references | Deterministic ambiguity versus convenient first-match selection | Retain all matching locations/reference IDs; abstain from unique localization |
| Independent same-task/common code | Recognition versus ubiquitous structure | No assumed independent authorship without fixture provenance; no identity claim from shared structure |
| Signal-only transfer, matching context | Signal recognition versus surrounding-content ancestry | A readable signal is expected under the existing counterexample; distinguish it from copied content |
| Signal-only transfer, changed context | Reproducible label constraint versus checked content binding | Record signal reading and binding outcome separately; a failed label check is not transplant immunity |
| Wrong key, wrong mark, replayed signed record | Detection specificity versus authentication/binding/trust | Separate wrong-key rejection, invalid signature, valid replay and content mismatch |
| Normalization, overwrite, mixed recipients | Removal or competing signal versus unsupported clean decoding | Valid removal counts as removal; preserve erasure, wrong-payload and ambiguity outcomes |
| Complete negative search over frozen catalogue/keys/windows | Per-comparison success versus full-query false alerts | Denominator is full negative queries with any false accepted result; retain comparison counts separately |

Literal signal transplant with independently constructed host content can distinguish successful signal recovery from the claim that all surrounding content descended from the marked source. It cannot establish the historical origin of arbitrary real fragments. Duplicate-anchor controls can falsify uniqueness rules. Neither control establishes a rare-event false-alert rate. Adaptive attacks and collusion require separate defined budgets; none of S1–S3 establishes those rates for this project.

## Claim-audit checklist for the pending report

All boxes remain open until the coordinator supplies the export. This is an audit queue, not a claim that the report contains these errors.

- [ ] Record the report path, export date and exact artifact revision; preserve the raw report unchanged.
- [ ] Map each decisive assertion to a primary version and section, distinguishing author measurements, formal results, project observations and proposals.
- [ ] Check that synchronization/index/framing/ECC costs are charged against usable carrier states; reject a universal token/byte minimum without a matching profile and budget.
- [ ] Identify blind versus reference-assisted access and local versus global encoding; account for gaps, reordered/extracted/inlined functions and competing references explicitly.
- [ ] Require candidate-byte evidence for every observed symbol; label decoder reconstruction and reference-supplied values separately.
- [ ] Check duplicate anchors before decoding; no first-hit selection or post-selection reference filling.
- [ ] Separate mark presence, payload decode, signature validity, key trust, context/content binding and ancestry in every result and denominator.
- [ ] Verify a same-context signal-only transplant control; do not claim that a readable context label, secret key or copied valid signature establishes host ancestry.
- [ ] Distinguish benign copy-paste survival from spoofing/scrubbing under generation or detector query access; state budgets, quality filters and success denominators.
- [ ] Calibrate the complete search; no independent-window bounds without assumptions, nominal single-window tail used after maximization, or p-value interpreted as ownership probability.
- [ ] Do not report unmeasured identity/error metrics as zero, convert synthetic family variants into independent trials, or treat a finite fixture result as universal behavior preservation.
- [ ] Preserve the newer signing/commitment evidence and the census's zero established safe eligibility; do not resurrect obsolete project limitations or infer general impossibility.
- [ ] Keep any new Go/Rust adaptation explicitly unexecuted and any specification implication advisory for parent reconciliation.

## Access limits and handoff

The proceedings PDF endpoints for S3 were not readable through the web tool (one fetch failed and the publisher-linked raw PDF returned an unsupported content type). Bibliography was verified on the PMLR record; detailed claims use the accessible versioned arXiv full text. No claim of byte identity between those editions is made. Author code licenses, release pins and reproducibility were not audited; no implementation recommendation follows.

The decisive remaining gap is a concrete source-code carrier/alignment model with measured useful capacity and a declared inference target. This review provides no new experiment, statistical guarantee or normative change. Report-audit remains pending; the next work in this same file is a bounded claim-by-claim comparison after the coordinator supplies the Google report. No polling or additional research lane is needed.

Validation on 2026-11-22: all six distinct external Markdown URLs returned HTTP 200; all eight local Markdown link occurrences resolved; no trailing whitespace or missing final newline was found. These checks validate links and file hygiene, not scientific reproducibility.
