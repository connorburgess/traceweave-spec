# Non-author review: core gates M1.1, M1.2, M1.5, M2.2, M2.3, M2.6, M2.7, M2.9

Reviewed 2026-11-23 on `roadmap-v2` at `488086f`. Extraction side: `9ce62c2`, `488086f`. Catalogue/report side: `a9a5f7e`, `8dd65c3`. I wrote none of it.

**How it was checked.**
- Scratch only, under `$TMPDIR`; 12 GB free beforehand.
- Implementations: both CLIs built unstamped from traceweave `main` `6d35308`, used for extraction runs and for MUST violations.
- My own clean-room comparator and record validators were written from `spec/catalogue-report.md` alone.
- **`tools/validate.py` could not run:** it imports `jsonschema`, which is not installed, and PyPI is unreachable offline. I ran every checker it calls directly instead: `check_vectors.py`, `check_requirement_map.py`, `check_matching.py` and `check_gates.py` all exit 0 at HEAD. `harness/crosscheck.py` (go/scanner, proc-macro2, rustc) passes too.

**Verdicts:** extraction side, **listed fixes first**. Catalogue/report side, **listed fixes first**. All fixes are small. Neither side needs rework.

## 1. Byte identity (both sides, independent)

My script compares every file of `test-vectors/`, `schemas/`, `spec/` and `profiles/` at `437d619` with HEAD. JSON files are compared vector by vector, with only the new metadata keys stripped.
- Unchanged: **every one of the 123 earlier extraction vectors** (34 Go, 78 Rust, 3 + 3 limits, 5 exclusion-rule) and the 28 config negatives.
- Unchanged: **all 76 earlier matching vectors**.
- 79 other files are byte-identical.
- Changed: the documents, the harness and checker code, and `matching.json`'s `requiredTags`, which gained `vendor`, `empty-span`, `equal-starts` and `py-tokens`.
- The author's `compare_outputs.py 437d619` also passes (123 compared, 60 added).

## 2. M1.2: vector classes, derivation, pairing

- **Classes.** All 7 classes are present per language through `vectorClasses` (Go: 1 empty, 7 below-k+w-1, 16 unicode, 33 malformed, 2 repeated, 2 equal-minimum, 6 crlf-bom; Rust likewise).
- **Derivation.** All 183 extraction vectors are `derivation: hand`.
- **Pairing is one-to-one and enforced.** In a scratch clone, each of these made `check_vectors.py` exit 1, against a control that exits 0:
  - removing a `pairedRejection`;
  - deleting a rejection vector;
  - removing a `derivation`;
  - `derivation: computed`;
  - two positives sharing one rejection;
  - a wrong `pairedPositive`;
  - removing `vectorClasses`.
- **The 60 new rejections.** I hand-checked 34 against `spec/extraction.md` and ran all 60 through both implementations. The 5 exclusion-rule rejections were run under `config-go.json`, because only the normalized channel differs there. **58 are correct. 2 are wrong:**
  - `rust-s1-string-digit-expr-rej` (`"x"1 + y"`) records `unterminated-literal`@8. §5.3 step 3 says an identifier immediately followed by `"` is `reserved-token` at the identifier start, so the answer is **`reserved-token`@7**. Both implementations give @7.
  - `rust-q11-shebang-first-line-only-rej` (`#!/*⏎*/ fn"`) records `unterminated-literal`@10. The keyword `fn` followed by `"` is **`reserved-token`@8**; both implementations agree.

  Both recorded results match proc-macro2, which has no reserved-prefix rule. That is why `crosscheck.py` passes them, and `check_vectors.py` checks lexical offsets only for plausibility. **Fix:** correct the two expected results, or change the inputs so the intended defect comes first, and add a crosscheck `EXPECT` entry for the proc-macro2 reserved-prefix divergence. Better still, make `validate` (or the M1.4 runs) require both implementations to reproduce every rejection vector.
- **The meaning of "hand".** `derivationRule` hand-writes token classes, texts, the inserted `;`, error codes and defect positions; spans are located by searching for those texts; hashes, windows and fingerprints are computed. This is the honest reading, because nobody hand-computes SHA-256. But the gate text "derivation: hand" does not say it. **Verdict: met with the wording clarified, after the two fixes.** The roadmap row or the vector README should define `hand` as the derivationRule does.

## 3. M1.1: the registration item map

- **The map is complete.** All 13 item rows and all 6 construct rows answer Go and Rust, with sections that exist and decide each point. I read each against the contract and found no wrong citation. The constructs (raw strings, nested comments, shebang, BOM, CRLF, token classes) cite real vectors.
- **"Scope resolution: none" is an answer, not a hidden TBD.** It is decided (OD-7 (a)), the claim is limited (§12: no scope awareness), and the exact channel always runs beside the normalized one. That satisfies `profiles/code.md`'s rule against erasing identifiers in the *sole* representation.
- **But one line contradicts it.** `profiles/code.md` line 7 still says "Use separate literal-preserving and scope-aware identifier-normalized channels", and these commits left that line unchanged. **Fix:** add one sentence there saying the token baseline's normalized channel is name-erasing by decision (OD-7), and that scope awareness belongs to a later profile, as §6.11 already says for M2.2 shadowing. **Verdict: met on the specification side once that sentence is added.**

## 4. M1.5: the requirement map

- **Counts.** The map has 28 MUST clauses: 17 testable, 9 untestable, 2 definitional. `check_requirement_map.py` reports 10 marked for spot-check. I spot-checked **all 11** non-testable clauses.
- **Untestable clauses.**
  - EX-03 (an undecided state) is correctly untestable.
  - **EX-04 and EX-05** (check the size before reading; stop after `maxInputBytes + 1`) are untestable *by vectors* but testable by a **process test**: an oversize FIFO, or an infinite stdin that must still end in `input-too-large`.
  - **EX-20 to EX-23** (linear time) are testable by scaling tests, which the implementations already run.
  - Recommendation: reclassify these as "test, not vector" and cite the implementation tests. This is not blocking: the gate allows listing them.
- **Violating MUSTs.** I violated 9 testable MUSTs in the real Rust CLI, one rebuild each, and ran all 201 extraction vectors and config negatives each time. **Every violation failed at least one cited vector:**

  | MUST | Violation | Failing vectors |
  | --- | --- | --- |
  | EX-12 | NFC check off | 6 |
  | EX-13 | zero-width-joiner check off | 3 |
  | EX-02 | BOM not rejected | 9 |
  | EX-06 | ill-formed UTF-8 accepted | 2 |
  | EX-14 | exponent without digits | `rust-literals-rej` |
  | EX-15 | `_`-suffix backtracking | 9 |
  | EX-10 | unmatched Go number accepted | 6 |
  | EX-11 | multi-value rune accepted | `go-unicode-rej` |
  | EX-18 | unknown profile version falls back | `cfg-unknown-profile-version` |

  Baseline: only the two wrong vectors of §2 fail.
- **Unmapped MUSTs.** A MUST added to `spec/extraction.md` without a row, plain or `**MUST**`, makes `check_requirement_map.py` exit 1. A lowercase "must" or a "SHALL" is not detected, but the contract uses only MUST and MUST NOT normatively; its two SHOULDs are advisory. **Verdict: met as worded on the specification side.**

## 5. Catalogue/report: clean room

- **My comparator.** I wrote it from §3.3, §4 and §5.3–§6.5 only. On the 7 new vectors, all **7 bodies and every catalogue digest match** byte for byte: `vendor-suppressed`, `vendor-unsuppressed`, `go-formatted-fragment-in-host`, `go-non-ascii-shift-2`, `py-empty-span-self`, `py-equal-starts` and `rv-py-empty-span-region`. It also matches all 56 compared-body vectors. The 27 rejected bodies are outside it.
- **Guesses** (small): catalogue bytes are the JCS of the canonical object, and ambiguity is judged by shared seed positions, not span overlap (§5.7 says so).
- **My record validators**, also from the text: 4/4 valid packets accepted and 55/55 invalid rejected; 4/4 retrievals and 7/7 invalid candidate-generation records behave as specified.
- **Guesses for the records:** commit ids are 40 lowercase hex characters; `selectedIdsSha256` is taken over the candidate catalogue's ids. I could not rebuild the subset retrieval's body: it is not in `matching.json` and needs §3.8 building from records.

## 6. OD-C64: span starts non-decreasing, empty spans at every k

- **Region rules are unaffected.** Merging, ordering, the region key, ambiguity and duplicate detection all use positions or digests, never span starts. Region spans are min/max values and are fine when empty.
- **But the relaxation is global, and it weakens Go and Rust validation.** For `go-tokens` and `rust2024-tokens`, distinct positions always have distinct starts: Rust tokens are non-empty, and a Go inserted `;` starts at the end of the token before it. So the old strict rule could only ever fire on a broken extractor.
- **Two wrong implementations demonstrate it.** I fed both to `check_matching.py`'s own catalogue validation on a Go catalogue:
  - W1 reuses the previous fingerprint's span start;
  - W2 gives two consecutive positions identical spans.

  Both are now **accepted**; the pre-A13 strict rule rejects both as `malformed-catalogue`.
- **Fix:** non-decreasing starts and empty spans at every k only for profiles whose tokens can be zero-width (a column in the §3.6 step 5 table; today only `py-tokens`), and strictly increasing starts for the others. No byte changes.

## 7. OD-C19: vendor code as the suppression catalogue

- **What the design does.** Regions stay visible (`common-only`, with counts) and never count as evidence, and `vendor-unsuppressed` shows the alternative. The review-packet link works: the `common-only` vendored region is listed, so its key can be cited (`packet-vendored-common-only`).
- **Hidden reuse.** Suppression is per hash, for *every* pair, so it can hide real reuse. Code copied from the vendored library into a project's **own** files also becomes `common-only`.
- **Changed outcomes for unrelated pairs.** Any pair sharing an idiom with the vendor files loses evidence. The vendor and boilerplate lists are one catalogue per comparison (§5.2), so the report cannot say which suppressed hashes came from vendor files.
- **Fix:** state these effects in §5.2 and §8. Recommend reporting suppressed regions per suppression-artifact class, or allowing a vendor-unsuppressed rerun as a standard companion.
- **M2.3 is not met by the spec alone.** It requires each control class "in the report with its candidate count and denominator". The vendor class has vectors, but the report has no class field; the counts and denominators are an implementation report (owner I), which must now add the vendor class.

## 8. M2.7 and M2.9 records

- **Region keys are checked.** A packet whose region key is absent fails, and so do a non-first seed and a foreign mode (my P2 and P5).
- **"No rights-verdict field" is enforced** by the closed schema: a `permitted` flag inside `package` is rejected (P4). An uppercase digest is rejected (P6).
- **Not caught:**
  - **P1b:** a `vendored-dependency` packet re-pointed at an unrelated own-code region of another body (`go-identical`), with an arbitrary `upstreamArtifactSha256`, **validates**. `historical-copy`'s `sourceArtifactSha256` is likewise never compared with the region.
  - **P3:** a licence `identifier` that contradicts the archived text (GPL with the MIT-style text) **validates**.
- **Fix:** require `upstreamArtifactSha256` and `sourceArtifactSha256` to equal the region's reference or candidate artifact digest, or state that they are unverified claims; and say that `identifier` is not checked against the text.
- **Candidate generation.**
  - Caught: ids hashed unsorted (C1), `rank` inside `index` (C3), `index` without a version (C4), an extra top-level field (C5), an unknown body (C6).
  - **Not caught: C2**, a subset retrieval recorded as `exhaustive`. That is inherent, since the record holds no corpus, but §6.10 should say `exhaustive` is the producer's claim.
- **No fixture lets rank, score or index data into a report.** The 4 report rejections and `origin-inside-report` fail the report schema.

## 9. M2.2

I recomputed **all 56 spans** (28 regions) from my own bodies: **56/56 equal**, along with 21/21 outcomes and 33/33 catalogue and body digests.

Low: the manifest omits two `below-minimum-evidence` regions that the bodies list (`go-shadowing` exact, `rust-renamed` exact). The body digests still cover them, but either list them or say "reportable regions only".

The "Unicode / repeated minima / tiny file" row has one positive case (Unicode). The other two are companion cases, which the gate wording allows.

## 10. Gate by gate

| Gate | Specification side | What remains | Implementations must add |
| --- | --- | --- | --- |
| M1.1 | Met once code.md line 7 is reconciled (§3) | One sentence in `profiles/code.md` | Nothing |
| M1.2 | **Not met** until the 2 wrong rejections are fixed; then met with "hand" clarified | §2 fixes; a crosscheck `EXPECT` entry; reproduction of rejections in validate or M1.4 | Reproduce all 60 new rejections (M1.4/M1.6) |
| M1.5 | Met as worded | Optional: cite process and timing tests for EX-04/05 and EX-20–23 | Those tests exist; cite them |
| M2.2 | Met (frozen, 56/56) | Optional: list or exclude the two below-minimum regions | Reproduce every digest and span N/N (owner I) |
| M2.3 | Vendor vectors present | §7 text on vendor effects | Report the vendor class with its candidate count and denominator (owner I) |
| M2.6 | Met for coverage; 6 `mixed` vectors disclosed (1 new) | Wording: M2.2/M2.3 rest on `hand` vectors only | I2 runs the 7 new vectors |
| M2.7 | Met except the upstream/source digest tie (§8) | Tie the digests or state them as claims | I2 writes and validates packets |
| M2.9 | Met | State that `exhaustive` is a claim | An index and two retrieval paths in I2 |
| (OD-C64) | Unsound as a global rule (§6) | Make it profile-conditional | Keep strict validation for Go/Rust |

**Decided in draft, pending owner confirmation** (catalogue side, amendment A13):
- OD-C19, vendor code as the suppression catalogue plus a review packet;
- OD-C61, the review packet;
- OD-C62, the candidate-generation record;
- OD-C63, the frozen M2.2 manifest;
- OD-C64, empty spans and non-decreasing starts;
- OD-C65, `py-tokens` registered as specified but not implemented.

The extraction side marks nothing as decided in draft. The owner would also be confirming the reading of "hand" in `derivationRule`, and "scope resolution: none".
