# Lane 1 comparison and preliminary verification

Reviewed 2026-11-18. Inputs are preserved unchanged in Perplexity report (local input: `perplexity/01-code-embedding.md`; not distributed) and Gemini report (local input: `gemini/01-code-embedding.md`; not distributed). This is a targeted review of decision-changing claims, not a complete literature or bibliographic audit. No proposed watermark has been implemented or benchmarked. Neither report is adopted as a specification.

## Decision

Retain structural source marking as a candidate for a narrowly scoped experiment. Do not select Python, statement permutation, a payload length, or public-key detection as a stable profile yet. Both reports recommend Python structural transformations, but their agreement does not independently establish safety, capacity or robustness. Both report limited access to the repository and neither supplies executed benchmark evidence.

Perplexity offers a broader candidate survey and generally more explicit uncertainty. Gemini proposes a more specific permutation mechanism, but that mechanism and several supporting claims are internally inconsistent. Perplexity's newer paper links and precise performance numbers still need a full source audit; this comparison does not certify them.

## Findings that change the decision

### 1. A Gemini watermarking citation points to an unrelated paper

Gemini lists “Towards Codified Watermarking for Source Code Generation,” attributed to Sweet et al., with arXiv:2402.14207. The [actual arXiv record](https://arxiv.org/abs/2402.14207) is Shao et al., “Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models,” the STORM paper. Gemini also lists that actual paper separately. The identifier does not support the claimed code-watermarking evidence. This does not establish whether a similarly titled paper exists elsewhere; the supplied citation is wrong.

For contrast, [arXiv:2309.00860](https://arxiv.org/abs/2309.00860), cited by Perplexity, is genuinely “Towards Code Watermarking with Dual-Channel Transformations,” describing SrcMarker and learned selection of AST-based transformations. Checking that abstract establishes relevance, not the separate numerical claims in the report or suitability of a hand-written Python permutation scheme.

### 2. HMAC does not supply the proposed public-key detector

Gemini selects permutations using HMAC with an owner secret, but its detector interface accepts only an owner public key. [RFC 2104](https://www.rfc-editor.org/rfc/rfc2104) defines HMAC using a shared secret. No construction is supplied for deriving the selected permutation from a public key. Resolve this as a secret/key-assisted or reference-assisted detector, or supply a separately justified asymmetric design. A signature on a record does not bridge this gap.

Perplexity's interface also takes a key identifier without specifying how secret material is resolved. That is an incomplete interface, not necessarily an asymmetric-cryptography error.

### 3. Gemini's example is not generally behavior-preserving

Its reordering moves a timestamp lookup before a list comprehension comparing each status to "ACTIVE". Python permits comparison methods to execute user-defined behavior; annotations do not make list/dict contents pure. See the [Python data model](https://docs.python.org/3/reference/datamodel.html).

A local synthetic counterexample used a normal list containing a normal dictionary whose status object's equality method changes that dictionary's timestamp to 99. The original order returns timestamp 99; the reordered order returns 0. This counterexample was executed during review. It does not reject every restricted permutation scheme: it rejects the report's general safety claim for the supplied example and assumptions.

A valid experiment needs a precisely restricted subset, effect and alias assumptions, and an explicit unmarkable outcome. Disjoint variable names alone do not establish independence. Perplexity's augmented-assignment example also requires its stated type/operator restrictions; passing tests is not a general equivalence proof.

### 4. The claimed false-positive bound is incorrect

Gemini claims zero detections on 500 negatives establishes FPR < 0.002. Under an independent identical Bernoulli-trial model, zero failures gives the one-sided exact 95% upper bound `1 - 0.05**(1/500)`, approximately 0.00597 (0.597%), not 0.2%. This calculation was checked locally. Correlated files and threshold tuning make even that model-dependent bound inappropriate without further design. The observed sample rate is zero; that is not a population guarantee.

Its requested universal FDR guarantee from a count of permutation sites is also unsupported. Lane 3 must specify the search procedure, dependence, background distributions and deployment prevalence.

### 5. Capacity and payload encoding remain undefined

Gemini's four-statement cluster has at most 24 permutations, allowing at most four fixed-length binary bits if all permutations are usable. That is a capacity ceiling, not a false-positive guarantee. Its HMAC expression selects a keyed order but never incorporates `payload_data`, so it does not specify recovery of an arbitrary payload. Order-independent canonicalization, scope/identifier normalization, site synchronization and fragment recovery are also missing. Survival under renaming requires those details, not just unchanged statement positions.

Perplexity requests 16-bit embedding while admitting functions with only five safe sites. This is not necessarily impossible if sites offer multiple choices, but no capacity calculation or codebook establishes it. Repetition or error correction consumes capacity; it does not create it.

### 6. Guarantees and normative changes are premature

Do not adopt Gemini's universal formatter/transpiler survival, numerical fragment lengths, mandatory epoch-key derivation, invented repository section numbers, or public-key verification interface. Both reports need actual implementation licenses and pinned versions before reuse. Perplexity's “perfect semantic equivalence” gate must become a scoped test result plus explicit semantic assumptions.

## Next experiment and handoff

Before building an embedder, write a carrier-feasibility experiment: define one deliberately restricted source subset; enumerate genuinely eligible sites; record capacity and skipped inputs; test normal toolchain behavior; compare against unmarked natural ordering. It may conclude that useful capacity is too low. Do not choose an arbitrary 16-bit payload first.

Send both reports and this review to lanes 2 and 3 as additional context. Ask lane 2 to challenge purity assumptions, synchronization after edits, removal and transplantation. Ask lane 3 to design capacity-aware controls and whole-search calibration. Lane 4 must keep secret-assisted mark detection separate from public signature verification.

The next decision is whether any narrowly defined carrier justifies a prototype, not whether a robust general-purpose code watermark has been found. Keep the original research reports unchanged and reconcile corrections here rather than silently editing their claims.
