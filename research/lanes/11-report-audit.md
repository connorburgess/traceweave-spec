# Lane 11: external design feedback, report audit

Prepared 2026-11-23. Audits two answers to the [lane 11 brief](../prompts/11-external-feedback.md), one from Perplexity and one from Google's research tooling, plus a third model's critique of the Google answer. All three are hypothesis sources, not requirements.

**Verdict.**
- **Perplexity: keep as a checklist, with corrections.** Its outside-world facts are mostly right; I checked 15 claims and found 1 contradicted. Most of its criticisms of Traceweave come from the brief being short: the contract already specifies seed merging, and the protocol already reports abstentions and states its limits. Its two concrete design proposals are infeasible as written: span verification inside a catalogue-only comparison, and a "lossless" `.wfp` mapping.
- **Google: reject its verdict and four of its six recommendations.** Its numbers about other tools are mostly copied correctly. Its conclusions about Traceweave come from treating `k` as the only noise threshold and from misreading the suppression mechanism. It is wrong on Unicode 17.0.0, on Dolos hashing and on in-toto/C2PA "redundancy". It cites no sources.
- **What survives from both.** The k=5 false-match risk is real and testable, and it can be tested on tuning data before the freeze (§8). The adversarial and LLM-rewrite gap is real, but it belongs in a follow-up.

## Capture identity

| Field | Perplexity | Google |
| --- | --- | --- |
| Raw capture (git-ignored by `.local/`) | `.local/research/perplexity/11-external-feedback.txt` (pasted prose, citation links lost); `.local/research/perplexity/11-external-feedback.pdf` (same response with 45 numbered citations, 13 pages) | `.local/research/google/11-external-feedback.txt` |
| Size | text: 32,013 code points, 32,302 bytes, 338 line breaks; PDF: 782,720 bytes | 34,651 code points, 34,685 bytes, 199 line breaks |
| SHA-256 | text `fd0ee7205951a41f814d6ed4abb506ff8e8f2130efe829c0c58cd663142bb757`; PDF `1d173538e492dd8e7c949314d35911103a68ff9ae38d5cb43138da7a65dd5105` | `47197c1b3f3ee594e30c11111294c257da09e0fc3f4757b1af87b48982126dc7` |
| Citations | 45 listed; 23 used in the text ([1]–[23]); [24]–[45] are never cited, among them a bioRxiv preprint and a patent | none: the "Sources" column is empty |

Hashes were checked before and after this audit. Fetches were read-only HTTP on 2026-11-23. Nothing was run or installed.

## Primary sources checked

| ID | Source (immutable reference) | Used for |
| --- | --- | --- |
| W | Schleimer, Wilkerson, Aiken, *Winnowing*, SIGMOD 2003, [PDF](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf) | §1 guarantee threshold t, noise threshold k; §3 `w = t − k + 1`, Lemma 1, density 2/(w+1); §5.1 Definition 3 (robust winnowing); §5.2 MOSS (rolling hash ">4×", inverted index, boilerplate, merging, "sharp threshold", no collisions reported) |
| S | SCANOSS [scanoss.py at `37f3508e`](https://github.com/scanoss/scanoss.py/blob/37f3508eecd68c51dab55978f592a4488f5f642a/src/scanoss/winnowing.py) (MIT per the GitHub licence API) and its [winnowing docs page](https://docs.scanoss.com/en/latest/advanced/fast-winnowing-fingerprint-algorithms) (a "latest" page that can change) | `GRAM = 30`, `WINDOW = 64`, `crc32c`, `file=<md5>,<size>,<path>`, `<line>=<hash>,…`, secondary hash on selected values. `scanoss/wfp` and `scanoss/engine` are GPL-2.0 |
| G20 | Gurioli et al., [arXiv:2605.28510v3](https://arxiv.org/abs/2605.28510v3) | Winnowing baseline: character k-grams, `k=5`, `w=4`, last 16 bits of SHA-1 |
| J | JPlag [at `3ee7de91`](https://github.com/jplag/JPlag/tree/3ee7de912b90ef82462fa1fbe0a57aa48b4e8f15) (GPL-3.0) | `GreedyStringTiling.java` (Wise's algorithm); `minimumTokenMatch` is 8 for Go and Rust and 9 for Java; README `--min-tokens` |
| H | [swhid.org](https://www.swhid.org/) | "officially adopted as ISO/IEC 18670:2025 on April 23, 2025". iso.org returned 403 to a script; the Software Heritage provenance docs served a bot check, so they were not read |
| B | Svajlenko, Roy, *BigCloneEval*, ICSME 2016, [PDF](https://clones.usask.ca/pubfiles/articles/SvajlenkoBigCloneEvalICSME2016.pdf) | §I–II: 25,000 Java systems, "over 8 million clone pairs across 43 functionalities"; §XI: "BigCloneEval does not measure clone detection precision" |
| K | Krinke, Ragkhitwetsagul, [arXiv:2505.04311v2](https://arxiv.org/abs/2505.04311v2) (v2 of 2026-11-04) and [IWSC 2022](https://discovery.ucl.ac.uk/id/eprint/10156341/1/2022_iwsc.pdf) | WT3/T4: 406-pair stratified sample, 379 false (93.3% unweighted), population-weighted 93.9% (CI 91.5–96.2%); IWSC: 86 of 100 false, one functionality, "too small to be representative" |
| M | Devore-McDonald, Berger, *Mossad*, [arXiv:2010.01700v1](https://arxiv.org/abs/2010.01700v1) | §4–§5: inserts statements into C assignments (3 projects) and measures detector similarity of the variants; §5.7: also JPlag, Sherlock, Fett |
| Z | Zhang, Saber, ICCQ 2024, [arXiv:2407.02402v1](https://arxiv.org/abs/2407.02402v1); figures quoted in [arXiv:2611.07887v1](https://arxiv.org/abs/2611.07887v1) §1 | GPT-3.5 and GPT-4 used **as clone detectors**; low Type-4 results. The 0.07/0.23 numbers were read only in the secondary paper |
| C | [C2PA 2.1](https://spec.c2pa.org/specifications/specifications/2.1/specs/C2PA_Specification.html) (CC BY 4.0) | §9.1: a soft binding is "computed from the digital content … useful for identifying derived assets"; §18.9 `c2pa.soft-binding`, algorithm list typed `watermark` or `fingerprint`; guiding-principles quote |
| L | [SLSA provenance v1.1](https://slsa.dev/spec/v1.1/provenance) (marked retired; v1.2 is current) | "Provenance is an attestation that a particular build platform produced a set of software artifacts through execution of the buildDefinition"; defined as an in-toto predicate |
| D | Dolos [at `e236c446`](https://github.com/dodona-edu/dolos/tree/e236c4463f5c4c205d71c730caf196ce7c550822) (MIT) | `lib/src/lib/options.ts`: `defaultKgramLength = 23`, `defaultKgramsInWindow = 17`; `core/src/hashing/rollingHash.ts`: modulus 33,554,393; `winnowFilter.ts`: rightmost minimum with `<=`; `codeTokenizer.ts`: emits `(`, node type, `)` per Tree-sitter node |
| R | Sajnani et al., *SourcererCC*, [arXiv:1512.06448v1](https://arxiv.org/abs/1512.06448v1) | Table 1 (6 lines, 70% overlap, function granularity); Table 5 BigCloneBench recall; precision 355/390 = 91%; 250 MLOC in 4.5 days, 1.2 GB index |
| U | [Unicode 17.0.0](https://www.unicode.org/versions/Unicode17.0.0/) | Released 2025 September 9 |

## Perplexity: claims about the outside world, by decision impact

Status: **S** supported, **P** partly supported or overstated, **U** unsupported, **C** contradicted, **V** unverifiable in this pass. Source quality: primary (paper, spec or code at a commit); vendor (vendor documentation); secondary (cites someone else's figure); none.

| Impact | Claim (citation) | Status | Source quality | Basis |
| --- | --- | --- | --- | --- |
| High | Winnowing guarantees detection of any shared substring of length ≥ w+k−1; k=5, w=4 give 8 tokens ([1]) | **S**, with a unit slip | primary | W §1, §3: t = w+k−1, in the units of the k-gram (characters in W). 4+5−1 = 8 is right and matches extraction §8. Section B of the report once says "w+k−1 **k-grams**", which is wrong |
| High | One inserted token every k−1 tokens breaks every k-gram ([1]) | **S** | arithmetic | Period-5 insertion (4 kept, 1 inserted) puts an inserted token in every 5-token window. This is the brief's own point and is not stated in W |
| High | "A reported modern winnowing configuration: k=5, w=4, SHA-1 truncated to 16 bits"; so our parameters are "plausible and conventional" ([20]) | **P** | primary preprint | G20 uses exactly that configuration, but over **character** k-grams and keeps the *last* 16 bits. Five characters are not five tokens, so it is no evidence for token k=5 |
| High | SCANOSS `.wfp`: 30-byte normalized grams, CRC32C, per-line records, file MD5 ([8], [9]) | **S**; licence omitted | vendor + primary code | S: `GRAM = 30`, `WINDOW = 64` (the report omits the window); `file=` holds MD5, size and path. Code licences are MIT (client) and GPL-2.0 (`wfp`, engine); the report says only "open" |
| High | Define a lossless mapping to `.wfp` ([8], [11]) | **C** | n/a | Not possible in either direction; see the next table |
| High | JPlag uses Greedy String Tiling with a minimum-match threshold ([5], [6]) | **S** | primary code | J. The defaults are 8 tokens for Go and Rust and 9 for Java. Citation [6] (an Auckland repository file) was not opened |
| Medium | BigCloneEval measures recall, not precision ([13], [14]) | **S** | primary | B §XI |
| Medium | 93% of a 406-pair WT3/T4 sample lacked similar functionality; 86% of 100 in an earlier sample ([3], [21]) | **P** / **S** | primary | K: 93.3% unweighted (379/406) and 93.9% population-weighted, under the authors' operational definition. IWSC: 86/100, for one functionality. The report presents the weighted estimate as a raw sample fraction |
| Medium | Mossad attacks MOSS-style detection ([2]) | **S** | primary (via the ar5iv mirror) | M: automatic statement insertion on C assignments, measured by the similarity scores of Moss, JPlag, Sherlock and Fett. It is evidence about evading thresholded scores, not a recall figure |
| Medium | GPT-3.5 and GPT-4 Type-4 recall of 0.07 and 0.23 ([22]) | **P** | secondary | [22] attributes them to Z. Z's abstract confirms that LLMs were the *detectors* and did poorly on Type-4; I did not check the exact figures in Z. The report's caveat (not fingerprint survival) is correct |
| Medium | SWHID is ISO/IEC 18670; the SWH provenance service maps a SWHID to origins and releases ([10]–[12]) | **S** / **V** | [12] is a French marketing page | H confirms ISO/IEC 18670:2025. The provenance-service capabilities could not be read |
| Medium | C2PA soft bindings are fingerprints or watermarks that reconnect derived assets; C2PA "does not advocate a particular technology" ([15]–[17]) | **S** / **V** | primary | C §9.1 and §18.9. The non-advocacy wording is from guidance 2.4 ([17]), which I did not fetch |
| Medium | SLSA provenance is a build-platform attestation; in-toto is its carrier ([4], [18]) | **S** | primary, but a retired version | L. [18] is a v0.1 page |
| Low | Expected 64-bit collisions in N fingerprints ≈ N²/2⁶⁵ | **S** | arithmetic | Expected colliding pairs inside one catalogue. For a comparison the relevant figure is n_R·n_C/2⁶⁴ (computed in the next table) |
| Low | MOSS uses robust winnowing; MOSS merges consecutive matching fingerprints | **S** | primary | W §5.2 |

## Perplexity: claims about Traceweave, checked against the repository

| Claim | Verdict | Evidence |
| --- | --- | --- |
| Seed merging is underspecified: gap units, maximum gap, cross-file behaviour, repeated fingerprints, order relative to suppression | **Wrong (artefact of the brief)** | [catalogue-report §5.3–§5.6](../../spec/catalogue-report.md#55-regions-and-the-region-key):<ul><li>gap = difference in reference fingerprint positions ≤ `mergeGap`, with boundary vectors `rv-gap-equal` and `rv-gap-boundary`;</li><li>comparison is per artifact pair, so merging never crosses files;</li><li>repeated hashes form the full cross product of seeds, and evidence counts distinct hashes;</li><li>common hashes reduce region evidence after merging (`rv-common-reduces-evidence`).</li></ul> |
| Abstentions should be reported separately, not only counted as alarms | **Already done** | [protocol §1](../drafts/evaluation-protocol.md#1-units) "Alarm counts are reported per reason and per mode beside the total"; §10 has an Abstentions row |
| "1 in 20" is a budget, not a demonstrated rate | **Right; the protocol already says so** | §11: it "cannot demonstrate a rate below about 0.2 with independent-search confidence, nor below 0.022"; §14.1 prints the operating characteristics |
| Only retrieve with the 64-bit hash, and verify exact or normalized spans before `match` | **Infeasible in this design; would make no difference in M3** | A catalogue stores no source ([§3.5](../../spec/catalogue-report.md#35-not-stored)), so a catalogue-only comparison has nothing to verify against. Collision exposure, upper bound: held-out source ≤ 29.4 M bytes, so ≤ 29.4 M fingerprints per channel, and Σ n_R·n_C ≤ F²/2; that gives ≤ 2.3×10⁻⁵ expected accidental seeds per channel over all 132 searches. A `match` also needs ≥ 2 distinct hashes on one diagonal. False alarms will come from real equal token runs, which verification would *confirm*. Verification belongs in the UC-2 review packet (M2.7), where both sources are present |
| Emit SWHIDs | **Feasible, additive, owner decision** | A content SWHID is `swh:1:cnt:` plus the git blob SHA-1 of the bytes. It must be computed at extraction (the catalogue keeps only the SHA-256) and is a catalogue format change. It discloses no more than the existing `sha256` ([§3.7](../../spec/catalogue-report.md#37-commitment-and-privacy-class)). It identifies whole files only, never fragments |
| Map to SCANOSS `.wfp` | **Lossy both ways** | **Traceweave → wfp:** wfp needs file MD5, line numbers and CRC32C of 30-character grams, none of which can be derived from 64-bit token-k-gram SHA-256 hashes and byte spans without the source. **wfp → Traceweave:** there are no tokens, spans or channels. The only option is a parallel wfp extractor over the same source: a second method, not a mapping |
| No privacy threat model | **Partly wrong** | [§3.7](../../spec/catalogue-report.md#37-commitment-and-privacy-class): catalogues are private; holders can test guesses, confirm whole files and read structure. [§6.7](../../spec/catalogue-report.md#67-privacy-class-of-the-report) covers reports, [extraction §7](../../spec/extraction.md#7-k-grams-and-hashing) says unkeyed hashes give no privacy, and [threat-model](../../spec/threat-model.md) has a dictionary-attack row. Query and membership leakage of a resolver are gate RES.1 (open) |
| LLM-rewrite and adversarial transformations are missing from the nine | **Right** | §6.3 lists `verbatim`, `ws`, `comments-strip`, `comments-add`, `fmt`, `rename`, `reorder`, `split-mix`, `compound`; §15: "None is an adversarial evasion budget" |
| The provenance stamp is narrower than SLSA provenance | **Right, and stated** | The contract calls the stamp cooperative-build evidence; signing is M4.3–M4.5 |

## Google: claims, checked against primary sources and the repository

| Impact | Claim | Status | Basis |
| --- | --- | --- | --- |
| Blocker | k=5, w=4 "guarantees rampant false positives"; raise k to 15–20 tokens | **U** (threshold invented) | No measurement is offered. W §5.2 reports, informally, that some document-dependent k separates copying from noise, but gives no value for code. Published token thresholds differ: JPlag Go/Rust 8 tokens (J); Dolos k=23 Tree-sitter tokens, w=17 (D); SCANOSS 30 characters, window 64 (S). The report ignores that our `match` needs `minRegionDistinctHashes` distinct non-common hashes on one diagonal (§8 below) |
| Blocker | Suppression "only through a static digest catalogue" is infeasible; one-token variants escape | **C** on the mechanism | Suppression is per-hash membership ([§5.2](../../spec/catalogue-report.md#52-common-hashes-suppression)), as in MOSS (W §5.2: fingerprint boilerplate under a special document id). Third-opinion section, item 5 |
| High | Replace sequence winnowing with SourcererCC bag-of-tokens | **P** | R: 91% precision (355/390 sampled pairs). BigCloneBench recall: T1 100, T2 98, VST3 93, ST3 61, MT3 5, WT3/T4 0. Detection is at function granularity (≥ 6 lines, 70% token overlap), so there are no byte spans below a block, and MT3 recall is near zero anyway |
| High | Evaluate on BigCloneBench: 25,000 systems, 8 M validated pairs | **S** figures / **C** usability | B gives those figures, but the corpus is Java and BigCloneEval measures recall only. K finds 93% of the WT3/T4 labels wrong. Its WT3/T4 "pairs" combine two methods tagged for the same functionality (K) |
| High | 1/20 "≈ 4.5%" is untenable; 25,000 repositories would give 15 M alarms | **P** | The budget is 5%, and 6/132 = 4.5% is the largest passing count. 312,487,500 pairs × 0.05 = 15.6 M is correct arithmetic. But the unit is any alarm or abstention among ~10⁴ file pairs per search; per-file-pair false matches are reported separately (§10). Published rates (R's 91%) are precision over reported pairs, a different unit. §14.1 already tabulates expected alarms per sweep size |
| High | The per-search unit hides snippet-level false positives | **C** | §10 reports pair-level false matches, candidate volume and regions |
| High | Rolling hash: ">4×" throughput | **S** for 2003 / **U** for us | W §5.2 measured with k=50 characters and 64-bit arithmetic. No per-byte extraction throughput has been measured here; the cross-check report times 14.3 M differential cases in about 277 s per seed including harness, which is not a throughput benchmark. Changing the hash has no accuracy effect (both are 64-bit), invalidates every vector and `configSha256` (OD-11), and is easier to collide on purpose |
| Medium | MOSS uses robust winnowing for low-entropy runs; density 2/(w+1); inverted index; no hash collisions reported | **S** | W §5.1 Definition 3, §3, §5.2. Our tie rule is the **plain** local rule (rightmost minimum, `≤`; [extraction §8](../../spec/extraction.md#8-winnowing-selection)), not robust winnowing, which is non-local. Low-entropy runs are handled downstream: repeated hashes count once (`go-repeated-hash-self`), and `maxSeedsPerMode` abstains |
| Medium | Dolos: Tree-sitter, MIT, hashes "64-bit … < 2⁵³", longest-common-substring matching, Gaussian threshold | **S** / **C** / **V** | D: Tree-sitter parsers and MIT **S**. The rolling hash is modulo 33,554,393 (a 25-bit modulus, so products stay below 2⁵³), **C**. The matching and threshold claims are **V** |
| Medium | "Unicode 17.0.0 is unreleased" | **C** | U: released 2025-09-09 |
| Medium | in-toto/C2PA make Traceweave "totally redundant" | **C** | Neither does similarity: L defines a build attestation, and C stores a registered algorithm's value. Alignment is already gated: M4.5 (in-toto adapter), C2PA.1–C2PA.3 |
| Medium | Normalized 5-gram dictionaries let a catalogue holder "fully reconstruct" source structure | **P** | Guessing and confirmation are real and already stated (§3.7). Fingerprints cover about 2/(w+1) = 40% of k-gram positions, so "fully" is overstated. The 82% singleton statistic is from 20,000 web pages (W §5), not code |
| Low | Gacek et al. 2026, CodeSteer, STONE, CodeIP figures | **V** | Not located: an arXiv title search for CodeSteer returns a different 2025 paper, and an author search for Gacek returns nothing relevant. By the report's own description, Gacek compares independently written human and LLM solutions, and CodeSteer measures LLM Pass@1. Neither measures detecting a rewrite of a given source, so both are misapplied |
| Low | AFC case law makes the boilerplate design "legally insufficient" | **U** | No source. The report already must not claim infringement ([§8](../../spec/catalogue-report.md#8-what-the-report-must-not-claim)) |

## Where the two reports agree, contradict, and who is right

- **Agree, and right.**
  - The core is winnowing prior art; the contract's determinism is the differentiator.
  - 132 searches cannot show a low rate (both match §11).
  - Insertion and reordering evade k-grams.
  - Embedded marks in existing code stay negative.
  - Reports need signing (M4).
- **Contradict.**
  - *k=5 conventional (Perplexity) against k=5 disqualifying (Google):* both overreach. G20's k=5 is in characters, and Google gives no data. The question is empirical and goes to the tuning stage (§8).
  - *Align with SCANOSS/SWHID (Perplexity) against "no evidence found" on them (Google):* Perplexity is right that they are the closest prior art (S, H). Its mapping proposal is wrong.
  - *Collision risk.* Google: 64 bits is adequate. Perplexity: verify spans. Google is right at our scale (computed above).
  - *Provenance.* Perplexity: align with SLSA/in-toto. Google: redundant. Perplexity is right: they are envelopes, not matchers.

## Third opinion on the Google report, checked

1. **Binomial bounds**, recomputed exactly for N = 132 searches:
   - 0 alarms: one-sided 95% upper bound 0.0224 (rule of three gives 0.0227);
   - 6 alarms: observed 0.0455; one-sided upper bound 0.0877; two-sided (97.5%) 0.0963, which is the critique's "near 10%".

   These assume independent searches. Our unit is the unordered pair, each repository appears in 11 of 66 searches per language, and the protocol already prints 0.088 at 6 alarms (§14.1). Its disjoint 12-search bound is 0.221 at 0 alarms (§11). **Holds.**
2. **Dolos defaults:** k=23 and w=17 (D `options.ts`). The units differ from ours: the tokenizer emits `(`, the node type and `)` for each Tree-sitter node, so 23 Dolos tokens cover only a handful of syntax nodes, not 23 lexer tokens. It is no basis for a token count in our profile. **Holds, with that caveat.**
3. **Unicode 17.0.0:** released 2025-09-09 (U). **Holds.**
4. **Gacek and CodeSteer misused:** I could not open either paper. On the Google report's own description, the critique is right (previous table).
5. **Exact-digest suppression is brittle: wrong premise, real residue.**
   - A hash is common if it occurs among the suppression catalogue's fingerprints in that channel, and evidence subtracts common hashes per region (`rv-common-reduces-evidence`, `rv-common-reduces-evidence-2`).
   - A one-token change alters only the ≤ k k-grams that cover the changed token; every other k-gram of the idiom keeps its hash.
   - In the normalized channel, a different identifier or literal does not change any hash.
   - The real brittleness is selection: suppression covers only the hashes winnowing selected in the boilerplate file's context (§5.2). M3 already removes it by cutting **one snippet per frequent hash**, exactly the k-gram span, kept only if that hash survives extraction (protocol §5.2).
   - No shipped vector shows a one-token variant; one should be added (ranked list, item 6).
6. **Proposal (a): keyed fingerprints (HMAC per catalogue or relationship).**
   - **Cross-party comparison:** both sides must extract under the same key, so the key is per relationship, not per catalogue. Catalogues made under different keys share nothing.
   - **Where the key lives:** never in configuration bytes, catalogue or report. The configuration would carry a key identifier or commitment (core already has `sha256-salted-catalogue-v1`), and the key itself sits in private storage under M2.8.
   - **Canonical records and vectors:** they need a published test key and a new hash identifier. The report body is unaffected, because it holds no hashes ([§6.7](../../spec/catalogue-report.md#67-privacy-class-of-the-report)).
   - **Attacks:** a keyed hash stops outsiders who obtain a catalogue but not the key. It does **not** stop the counterparty, who holds the key by construction and can test guesses: membership testing between comparing parties remains ([threat-model](../../spec/threat-model.md): "no claimed k-anonymity").
   - **Recommendation:** gate KEYED.1 after M3.4, plus RES.1. Not before the freeze: a per-run key changes no M3 outcome.
7. **Proposal (b): the "20 unrelated repositories" pre-experiment.** Design it inside the tuning stage, not separately (§8, change 1).
   - Use fold-S repositories only. They build suppression and are never used for selection, so nothing leaks into held-out data or the fold-E choice.
   - The pool beyond the walk (71 Go and 61 Rust) would need new acquisition approval.

## Recommendations triage

**Perplexity (P1–P10, E1–E3).** "Later" names the gate. Effort is in lane-days.

| Item | Decision | Concrete change | Effort |
| --- | --- | --- | --- |
| P1 Reframe as a reuse-evidence reporter | Already adopted | [extraction §12](../../spec/extraction.md#12-what-the-baseline-does-not-claim) and [report §8](../../spec/catalogue-report.md#8-what-the-report-must-not-claim); README claims audited at M5.2 | 0 |
| P2 Run the evaluation before features; denominators and intervals | Already adopted | Protocol §10–§12 | 0 |
| P3 Separate syntactic from semantic robustness; add LLM-rewritten cases | Later | Syntactic cells exist (§6.3). LLM rewrites go in a new adversarial gate after M3.4; they need an owner decision because they use an external model | 3–5 |
| P4 Verify spans before `match` | Reject in the comparison; later in M2.7 | A review-packet step with both sources | 0.5 |
| P5 SWHIDs; `.wfp` mapping | SWHID later (owner, format change, M5.5); `.wfp` rejected | Optional catalogue field; a parallel SCANOSS-style arm could join STRUCT.1 | 1 / 2 |
| P6 Specify seed merging | Reject: already specified | none | 0 |
| P7 Adversarial benchmark | Later, new gate after M3.4 | Pre-registered lexical insertion, statement reorder, dead code; then LLM paraphrase; human-validated regions | 3–5 |
| P8 Embedded marks optional | Already adopted | M2E.0 (owner) | 0 |
| P9 SLSA/in-toto attestations, transparency log | Later: M4.3–M4.5; a log is a publication decision (owner) | Sign report bodies with DSSE | per M4 |
| P10 Privacy threat model | Later: RES.1 | Add catalogue-holder guessing and counterparty membership; cite §3.7 | 1 |
| E1 `.wfp` import/export, run against SCANOSS | Reject as stated | Querying the SCANOSS knowledge base would send fingerprints to a service. A local MIT client arm is possible under STRUCT.1 | — |
| E2 Blinded manual validation of every negative match | Adopt now, procedure only | Freeze the audit-label procedure (§1 labels; two labellers; blind to configuration) before the freeze; labels never change M3.6 | 0.5 |
| E3 Small pre-registered adversarial set | Later | As P7 | — |

**Google (G1–G6, risks R1–R3)** and **third opinion (T1–T4)**.

| Item | Decision | Reason or change | Effort |
| --- | --- | --- | --- |
| G1 Raise k to ≥ 15–20 | Reject the mandate; adopt the test | Invented threshold. Widen the grid to k=16, the contract bound, and count fold-S matches (§8) | 0.75 |
| G2 Switch to bag-of-tokens | Reject as replacement; later as an arm | STRUCT.1, on the same corpus and budget; it loses byte spans | 3–5 |
| G3 Abandon code marks for existing code | Owner (M2E.0) | Evidence supports recording omission | 0 |
| G4 in-toto/DSSE reports | Later (M4) | Same as P9 | per M4 |
| G5 BigCloneBench instead of 48 repositories | Reject | Java, recall only, bad WT3/T4 labels. No Go/Rust ground-truth benchmark was found in either report. Our §6 generator already is a Roy–Cordy-style mutation/injection design | — |
| G6 Karp–Rabin hash | Reject | No accuracy effect; breaks vectors; revisit only if M3 runtime (§10) shows hashing dominates | — |
| R1 False positives at k=5 | Test before the freeze | §8 | (G1) |
| R2 Brittle to edits and LLMs | Later | P7. Its BigCloneBench-ST3 test is Java | — |
| R3 Redundant with in-toto/C2PA | Reject | They do no matching | — |
| T1 Statistics | Already in the protocol | §11, §14.1 | 0 |
| T2 k=5 test | Adopt, inside tuning | §8 | (G1) |
| T3 Keyed hashes | Later: KEYED.1, RES.1 | Item 6 above | 3 |
| T4 Signed reports | Later: M4 | — | per M4 |

## Combined ranked list of changes

1. **Before the freeze (M3.3, protocol `m3-eval-draft-5`):** extend the timing pilot (§5.5), whose outcomes are now discarded unread, to record outcome-class counts on **all** fold-S searches at `T` = none and `minRegionDistinctHashes` = 2, for every (`k`, `window`). It is still tuning-split only and still before the digest (step 5 precedes step 6). 0.5 days. Pre-declared rule, committed before the pilot runs:
   - if the most conservative grid configuration (with item 2 adopted: `k` 16, `window` 16, `minRegionDistinctHashes` 6, `T` none) still alarms in more than half of the fold-S searches of either language, add `minRegionDistinctHashes` 8 and 12 to the grid before the digest is filled;
   - otherwise the grid stands.

   Either way, the k=5 counts are reported as the answer to R1.
2. **Before the freeze:** add `k` = 16, the extraction bound, to the grid. That gives 192 configurations and 12 (`k`, `window`) settings. Revise the §5.5 reduction order to drop `window` 16 first and then `k` 8, so that both ends of `k` survive. 0.25 days.

   Why: under the shipped comparison the smallest possible `match` is **k + m − 1 = 6 tokens**, two adjacent selected k-grams. The guaranteed one is **m·w + k − 1 = 12 tokens**, two disjoint full windows whose selections are ≤ w apart and so merge under `mergeGap` = w. The current grid floor k+m−1 runs from 6 to 17 tokens. `k` = 16 adds floors up to 21, covering the range Google names, without adopting it.
3. **Before the freeze:** commit the per-configuration fold-E table (*a*, *r*, regions per search, by `k`) with `freeze.json`. Also freeze the alarm-audit procedure (E2). 0.5 days.
4. Signed report bodies (M4.3–M4.5): unchanged priority.
5. Adversarial and LLM-rewrite set as a new gate after M3.4 (P3, P7, R2). 3–5 days, plus an owner decision for model use.
6. A one-token-variant suppression vector, drafted in `research/drafts/` for the next promotion (M2.10/M2.6 follow-up). 0.25 days.
7. Bag-of-tokens and SCANOSS-style arms under STRUCT.1, on the M3 corpus and budget. 3–5 days each.
8. KEYED.1 and the RES.1 privacy additions. 1 + 3 days.
9. Optional SWHID catalogue field (owner; M5.5). 1 day.

**Rejected:** span verification inside comparison, a lossless `.wfp` mapping, a rolling hash, BigCloneBench as the evaluation, a k ≥ 15–20 mandate, abandoning winnowing.

## What this changes, and what must happen before the M3 freeze

**Must change before the freeze:** items 1–3 above. All are tuning-stage or record changes. They touch no held-out data, change neither M3.0 nor the M3.6 rule, and make the protocol `m3-eval-draft-5`. They take one lane-day in all.

**Must not be folded into the freeze:**
- **Adversarial transformations.** The M3.6 verdict depends on negatives only. The insertion result is known analytically. An LLM arm needs an owner decision.
- **A bag-of-tokens arm.** It is a different system under test (STRUCT.1).
- **Keyed hashes.** No M3 effect.
- **Span verification.** Expected accidental seeds ≤ 5×10⁻⁵ over the whole held-out run.

These are follow-up measurements on the same frozen corpus and budget. Nothing in either report justifies changing the 1/20 budget or delaying acquisition. Neither report's verdict on k=5 should be accepted until item 1 has counted.
