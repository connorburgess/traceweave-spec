# Source register and evidence policy

Status: planning register, checked 2026-11-18. Primary sources inform decisions; they do not establish that Traceweave implements a feature or achieves an accuracy target.

## Sources to use

| Source | Use in Traceweave | Limit and next action |
| --- | --- | --- |
| [Winnowing: Local Algorithms for Document Fingerprinting](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf), Schleimer, Wilkerson, Aiken, SIGMOD 2003 | M1 selection/locality definition; M2 fragment baseline | Locality under specified token/hash assumptions does not establish ancestry or real-world false alarms. Reproduce selection vectors and evaluate on the intended code corpus. |
| [DSSE protocol](https://github.com/dsse-lf/dsse/blob/master/protocol.md) | M4 envelope signing bytes and PAE | DSSE authenticates payloads, not their truth. Pin an upstream commit and library version before interoperability work; test byte lengths and tampering. |
| [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md) | M1/M4 subject and predicate adapter structure | Statement structure is not a trust policy or fingerprint algorithm. Pin a revision; test the restricted Traceweave adapter separately from arbitrary in-toto statements. |
| [Sigstore bundle format](https://docs.sigstore.dev/about/bundle/) | M4 optional transport of verification material | Bundle support is an integration choice. Select an explicit bundle version and verification policy; assess disclosure before enabling public services. |
| [RFC 3161](https://www.rfc-editor.org/rfc/rfc3161) | M4 optional trusted-time adapter | Specify the exact object timestamped, imprint, TSA trust and validation policy. Check updates and errata before implementation; a date string is insufficient. |
| [C2PA specification portal](https://spec.c2pa.org/) | Later media provenance mapping | Discovery entry point only: no technical mapping reviewed here. Select and record a concrete specification version before making compatibility claims. |
| [SynthID-Text](https://www.nature.com/articles/s41586-024-08025-4), Dathathri et al., *Nature* 634, 2024; reference code [`google-deepmind/synthid-text`](https://github.com/google-deepmind/synthid-text/tree/6452fbb837d0ad4281ccddb94b0af75d219b1a14) at `6452fbb8` | AIO: how a keyed token-choice text watermark is seeded and scored ([lane 14](../research/lanes/14-ai-origin-signals.md) §1, §4) | Detection needs the key and the tokenizer; nobody outside Google can check Gemini output, and there is no public text route (lane 14 G1, G3, G11). Detection figures are plot readings, not tabulated values. Reuse only with an experimenter-chosen key (AIO.3, owner-gated). |
| [Anthropic, "How Claude's text watermark works"](https://www.anthropic.com/news/claude-text-watermark), 2026-08-14, updated 2026-09-01 | AIO: operator's own wording for what a positive and a negative mean (lane 14 §7) | Living page; no accuracy figure; detector is in private preview for approved organisations; detector terms not published (lane 14 A1–A6). Re-read before quoting. |
| [OpenAI, "Our approach to EU text provenance rules"](https://openai.com/index/eu-text-provenance/), 2026-10-05, and the [textGrain report](https://cdn.openai.com/pdf/e9508624-d767-41b6-a26d-e34ca798ada6/textgrain-entropy-calibrated-watermarking-for-language-model-text.pdf) | AIO: scheme, scope and operator-claimed figures (lane 14 §1) | Figures have no sample sizes and are not independently measured; detector limited to approved organisations; the report has no empirical results (lane 14 O1–O6). |
| [Regulation (EU) 2024/1689](https://publications.europa.eu/resource/cellar/dc8116a1-3fe6-11ef-865a-01aa75ed71a1.0006.01/DOC_1) Art. 50; [Code of Practice on Transparency of AI-Generated Content](https://ec.europa.eu/newsroom/dae/redirection/document/129555), 2026-06-10; [Guidelines C(2026) 7702](https://ec.europa.eu/newsroom/dae/redirection/document/131215) | AIO: what providers must offer (free, signed, downloadable detection results; zero retention) and what is out of scope (text under 200 tokens, source code) (lane 14 §1.2) | Not legal advice. Duties fall on providers, not on independent tools. Interoperable detection is due 2027-02-02 (AIO.8 watch item). |
| [WaterPark, "Watermark under Fire"](https://arxiv.org/html/2411.13425v4), v4, and [Nemecek et al., "Watermarks Without Verification"](https://arxiv.org/abs/2609.09604v1), v1 | AIO: independent measurements on the open SynthID-Text implementation, including lower-casing (the proxy for the text profile's case fold) and code (lane 14 §1.3, §4) | Open implementation only, not any deployed key or configuration. No paper measures NFKC alone on clean watermarked text. |
| [Liang et al., *Patterns* 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10382961/); [Weber-Wulff et al. 2023](https://eprints.whiterose.ac.uk/207396/1/s40979-023-00146-z.pdf); [RAID, ACL 2024](https://arxiv.org/abs/2405.07940v2) | AIO.6: evidence against including an unkeyed AI-text classifier (lane 14 §5) | Small or dated samples in places; vendor counter-claims are not independently reproduced on student or non-native corpora. |

The first five documents were opened for this planning pass; the C2PA portal was checked only as a future source location. The AIO rows were added on 2026-11-24 from [lane 14](../research/lanes/14-ai-origin-signals.md), whose ledger gives versions and sections. GitHub branch URLs and documentation sites are mutable. Before a source justifies a normative requirement, record its immutable revision/version, section, retrieval date, supported claim and reproduction test. This register is not yet a pinned dependency manifest.

## Project evidence to retain

- [Initial draft review](reviews/initial-draft-review.md): unresolved risks and reasons the original numerical/privacy claims were removed. The supplied draft is proposal material, not external authority.
- [Core](../spec/core.md), [attestations](../spec/attestations.md) and [threat model](../spec/threat-model.md): current proposed contract. Resolve contradictions explicitly rather than silently promoting a new document above the spec.
- [Evaluation protocol](evaluation.md): rules for generating measured evidence. A future results report must name corpus/split/config digests, software versions, thresholds, search unit and known failures.
- Authorized source histories and license snapshots: evidence for region-origin review, stored privately when necessary. Never publish real investigation material as an example.
- Redistributable synthetic fixtures: primary evidence for deterministic behavior. Maintain expected outputs independently enough to catch implementation errors.

## How a proposal becomes a requirement

For each substantive decision, write a short record containing: user case; question; alternatives; primary source and exact section; proposed choice; security/privacy impact; test or experiment; evidence obtained; remaining uncertainty; and conditions that would change the decision.

Use four explicit labels: **proposed**, **specified**, **implemented**, **measured**. A mechanism can be specified without being implemented; a passing unit test does not establish general detection quality. Add **independently reviewed** only with a named review artifact and scope.

Blogs, product marketing, and generated summaries may suggest research leads. Follow their claims back to primary sources before relying on them. Evaluate libraries against current documentation and security history when selecting them, then pin versions. Do not invent a cryptographic primitive or copy an unexplained similarity threshold from a different corpus.

## Research questions for the next pass

1. Which first language/artifact type best represents the intended local use case?
2. What ambiguity remains in normalization, spans, hash serialization and repeated features?
3. Which unrelated and same-task controls are representative and redistributable?
4. What candidate-review burden and false-alarm budget make a repository search useful?
5. Which established signing library and trust distribution model satisfy the private workflow?
6. What evidence would justify structural matching, keyed selection or another modality after the baseline?

Each question should produce a decision or experiment with an acceptance gate, not an expanding list of references.

## Embedding research gap

The sources above do not select or validate an embedding algorithm. TW-08 must identify original watermarking papers and maintained reference implementations for the chosen content type, reproduce their assumptions, and compare removal and transplantation attacks. Record detector access, capacity, behavior/quality costs and empirical false detections. Winnowing is an extracted-fingerprint baseline, not an embedding method. This gap blocks algorithm selection, not recognition of embedding as a core use case.
