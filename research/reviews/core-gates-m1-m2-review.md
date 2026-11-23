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
- **The meaning of "hand".** Judged against the ROADMAP definition (ruling of 2026-11-23) in §11.

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
| M1.2 | **Not met** until the 2 wrong rejections are fixed; the labels then meet the definition (§11) | §2 fixes; the §11 `derivationRule` wording; a crosscheck `EXPECT` entry | Reproduce all 60 new rejections (M1.4/M1.6) |
| M1.5 | Met as worded | Optional: cite process and timing tests for EX-04/05 and EX-20–23 | Those tests exist; cite them |
| M2.2 | Met (frozen, 56/56) | Optional: list or exclude the two below-minimum regions | Reproduce every digest and span N/N (owner I) |
| M2.3 | Vendor vectors present | §7 text on vendor effects | Report the vendor class with its candidate count and denominator (owner I) |
| M2.6 | **Not met** under the definition: 48 `hand` vectors rest on lexer-made token streams (§11) | Hand-write those streams or relabel; add `derivationRule` to each file | I2 runs the 7 new vectors |
| M2.7 | Met except the upstream/source digest tie (§8) | Tie the digests or state them as claims | I2 writes and validates packets |
| M2.9 | Met | State that `exhaustive` is a claim | An index and two retrieval paths in I2 |
| (OD-C64) | Unsound as a global rule (§6) | Make it profile-conditional | Keep strict validation for Go/Rust |

**Decided in draft, pending owner confirmation** (catalogue side, A13): OD-C19 (vendor code as the suppression catalogue plus a review packet), OD-C61 (the review packet), OD-C62 (the candidate-generation record), OD-C63 (the frozen M2.2 manifest), OD-C64 (empty spans, non-decreasing starts), OD-C65 (`py-tokens` registered, not implemented).

The extraction side marks nothing as decided in draft. The owner would also be confirming "scope resolution: none".

## 11. Ruling applied: hand derivation (M1.2, M2.6)

Rule: (a) a person writes every judgment from the contract; (b) the spec's own builder or checker computes the arithmetic, and an independent recomputation confirms it. A lexical layer first made by a tool and then reviewed is not `hand`. Reviewed at `3b6e9f3`; the uncommitted A14 edits in the tree were not reviewed.
- **M1.2, (a) holds.** The builder `test-vectors/extraction/harness/build_vectors.py` imports only `base64`, `hashlib`, `json`, `sys` and `pathlib`. Every token list is written as literal tuples, and every rejection code and offset is a literal. Its only helpers are hashing, winnowing and list repetition (`[(P, "+")] * 10`), so no lexical layer is tool-produced. The 2 wrong rejections in §2 are hand errors, so they still need fixing but do not break the label.
- **M1.2, (b) holds, with my recomputation as the confirmation.** I wrote a recomputation from `spec/extraction.md` §6–§8 alone and ran it on all 65 `ok`/`insufficient-tokens` vectors in the 5 files. It rebuilt the spans from the token texts, the normalized values, every k-gram hash, the windows, `partialWindow` and the fingerprints, and **65/65 agree**. The one span difference is `rust-q11-shebang-first-line-only`: `*` also occurs inside the skipped shebang, so the builder gives an explicit hand start (5) rather than searching. Rejection offsets are judgments under (a); §2 covers them.
- **M1.2, the `derivationRule` text needs updating.** The text in all 5 files lacks two things. It never says the arithmetic is computed by the spec's builder, not an implementation, and confirmed independently (clause (b)). It also says spans are searched, but some starts are hand-written where a search would land on the wrong text. **Fix:** state (a) and (b) and the explicit-start case.
- **M2.6, (a) fails for 48 of the 77 `hand` matching vectors.** Those 48 draw on `extraction-go.json`, `extraction-rust.json`, `extraction-go-gates.json` or `extraction-go-classes.json`. Those files' token streams are produced by `lex()` in `test-vectors/matching/build_vectors.py`: the file's own `lexingCheck` says so, and they carry no per-vector `derivation`. That is a tool-made lexical layer, reviewed at most. It includes 7 of the 11 M2.2 cases. The other 29 `hand` vectors are fine: 10 use frozen hand extraction vectors or the `extraction-py.json` copies, and 19 use hand-written synthetic catalogues. Their region and outcome judgments in `handExpectations` are hand-written. The 6 `mixed` vectors are correctly not labelled `hand`.
- **M2.6 fix.** Write those 22 inputs' token lists by hand, as the extraction builder does, and keep `lex()` only as a cross-check. Alternatively, relabel the 48 vectors, which would leave M2.2 and M2.3 resting on non-`hand` vectors.
- **M2.6, no rule text.** `matching.json`, `m22-fixture-manifest.json`, `review-packets.json` and `candidate-generation.json` have no `derivationRule` next to their labels. **Fix:** add one in the ruling's words.
- **M2.6, (b) is confirmed by my clean room (§5, §9)** for the 7 new bodies, the 56 compared bodies, the 56 M2.2 spans and 33 digests. It does not recompute the lexer streams' fingerprints; the remedy above makes that unnecessary.
## Confirmation pass (HEAD `28f5b6d`: extraction `34eea25`, `a625c97`; catalogue `a77c657`, `28f5b6d`)

**Method.** Scratch was a `git archive` copy under `$TMPDIR` (17 GB free beforehand), deleted afterwards. `.venv/bin/python tools/validate.py` **passes** (exit 0, jsonschema 4.23.0); the unit tests pass (9/9).

**(2) Byte identity and recomputation.**
- **Unchanged since `3b6e9f3`:** every earlier expected output except the two corrected rejections. That covers 183 extraction vectors, 28 config negatives, the 22 matching inputs and the 83 earlier matching vectors. Intended changes: headers, review packets (draft-2), the manifest, and 7 new vectors.
- **My comparator:** 58/58 compared bodies of the 90 vectors, with their catalogue digests (the 32 rejected bodies are out of its scope). M2.2 against manifest `349bd149…`: 56/56 spans, 33/33 digests, 21/21 outcomes; exactly the reportable regions are listed.
- **My extraction recomputation:** 87/87 (65 extraction vectors + 22 matching inputs). The only hand-written span starts, `*`@5 and `total`@238, are where a source-order search lands wrongly.

**(1) Findings.**
- **Extraction side, resolved:**
  - The two rejections are now `reserved-token`@8 and @7 (`rust.json:2905`, `:2983`). `check_vectors.py:624–675` applies the reserved-prefix rule and `:955–983` checks each rejection against its positive. Restoring the old records fails `check_vectors.py`, and `crosscheck.py` now catches the old `s1` record.
  - `derivationRule` (`go.json:11` and the other four files) gives the definition plus (b) and `spanStarts: hand` (`rust.json:2269`). Removing that mark fails the checker.
  - `profiles/code.md:29` reconciles scope.
  - EX-05/22/23 cite implementation tests (`requirement-map.json:105`, `:514`, `:528`); EX-22/23 cite only Go's `TestNFCLinearTime`.
- **Extraction side, residual (low).** An offset moved *inside* the failing token passes `check_vectors.py`: 8 of 18 ±1 shifts of `reserved-token` offsets got through (e.g. `q11-rej`@9, `err-pounds`@3, `q1-raw-extra-pounds`@5). `crosscheck.py` passes the three I tried as well. Cause: `check_prefix_consistency` skips tokens that end after the offset. **Fix:** reject an offset strictly inside a positive's token over shared bytes.
- **Catalogue side, resolved:** OD-C64 is profile-conditional (`catalogue-report.md:192`, `check_matching.py:607`). The vendor effects are stated with vectors (`:301`, OD-C66); the companion comparison instead of per-class reporting is acceptable. M2.3 is assigned to the implementations (`:619`). P1b and the source digest are bound (`:576`, `check_gates.py:144–147`). P3: identifier removed (`:584`). C2: stated as a claim (`:598`). `regionsListed` added (`:617`).
- **Catalogue side, residual (minor).** `matching/extraction-py.json` and `matching/records.json` are `hand`-labelled but have no `derivationRule`. ROADMAP `:109` and `:238` still say the vendor class is missing and "5 mixed"; there are 6.

**(3) Hand derivation.** I read ten `HAND_TOKENS` lists against `spec/extraction.md`, not against `lex()`: `mv-go-put`, `-partial`, `-independent`, `-classes-a`, `-classes-b`, `-nonascii-prefixed`, `-host-formatted`, `-vendor-lib`, `-b2` and `mv-rust-host`. All are correct: `;` insertion (including after a bare `return`), explicit `;`, `...`, `[:0]`, comments, Unicode identifiers, Rust single-character punctuation and `write!`. All 84 `hand` matching vectors rest only on `hand` records or literal catalogues.

**(4) Corruptions.**
- **Earlier misses, now caught:** P1b, P3, and W1/W2 rebuilt on `rust-identical` and `go-renamed`. P2, P4–P6, C1 and C3–C6 are still caught. C2 is still not caught, as the contract now states.
- **New, all caught:**
  - **N1.** `go-tokens` declared zero-width in the checker fails at `go-w1-reused-span-start`; a `zeroWidthTokens` field in a catalogue fails the schema.
  - **N2.** Wrong-side digests fail all three ways: historical copy and source digests swapped, historical `side` flipped, and own-origin `side: candidate` with the reference digest.
  - **N3.** Relabelling a `hand` vector's source fails three ways: `mv-go-sum` set to `computed-then-reviewed`, its label removed, and `go.json#go-format-a` set to `mixed`.

**(6) Gates: specification side; what the implementations must add.**
- **M1.1:** met; nothing to add.
- **M1.2:** met. Re-vendor `extraction/rust.json` `7d53e9e6…` and the files whose headers changed: `go.json` `5eb7c2e2…`, `limits-go` `c70c60a1…`, `limits-rust` `b1f43876…`, `exclusion-rule` `8d5cb794…`, `config-negative` `e4212a74…`. Reproduce `reserved-token`@7 and @8 and every exact rejection offset (M1.4).
- **M1.5:** met. Keep the cited tests, and add or cite a Rust timing test for EX-22/23.
- **M2.2:** met. Reproduce 33 digests and 56 spans of `349bd149…` N/N.
- **M2.3:** met as far as the specification can supply. Report each control class with its candidate count and denominator, **including vendor** (4 vectors).
- **M2.6:** met, apart from the two rule texts above. Re-vendor `matching.json` `6652a8ce…` and the input files `405225d9…`, `0cc19730…`, `ba0b03b5…`, `0dfd8eb2…`. Implement zero-width-conditional span validation, and pass the 7 new vectors.
- **M2.7:** met. Validate draft-2 packets (schema `8ebc4c8f…`, `review-packets.json` `9c91e501…`): side digest, source bound to the other side, no identifier. That is 4 valid and 67 invalid.
- **M2.9:** met. Validate `candidate-generation.json` `bc98f970…`; build an index and two retrieval paths.

**Owner would confirm (decided in draft).**
- Catalogue: OD-C1–C16; A1 C21–C25; A2 (extraction OD-23); A3 C26–C28; A5 C29–C38; A6 C39–C47; A7 C48–C55; A8–A12 C56–C60; A13 C19 and C61–C65; A14 OD-C64 revised, C66 and C67, plus `exhaustive` as a claim and `regionsListed`; A15 OD-C68.
- Extraction: OD-23 and Q10.

**Verdicts.** Extraction side: **met**, with the low offset residual. Catalogue/report side: **met** on the specification side, with the two missing rule texts and stale ROADMAP cells as minor items.
