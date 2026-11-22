# Review: catalogue/report contract, matching vectors, use-case plans, roadmap gates M0.1 and M2.7–M2.9

Status: independent review, 2026-11-22. Scope: [catalogue-report-contract.md](catalogue-report-contract.md) (draft-1), [matching-vectors/](matching-vectors/README.md), [use-cases-verification-plans.md](use-cases-verification-plans.md), and [roadmap-v2.md](../../ROADMAP.md) M0.1 and M2.7–M2.9. I wrote none of these files and re-ran every check myself. Scratch code is in `$TMPDIR/cr/` and not in the repository: `cleanroom.py`, `variants.py` and `corrupt.py`.

**Verdicts.** Part 1: **ready after listed fixes.** Part 2: **ready after listed fixes.** Part 3: M2.8 and M0.1 are **ready after listed fixes**; M2.7 and M2.9 need **rework**.

## Part 1a — Clean-room result

I wrote `cleanroom.py` (about 300 lines) from the contract text and the two schemas only. I opened `check_matching.py` and `build_vectors.py` only after it had produced results. For each vector, the program builds both catalogues from the referenced extraction records (`inputBase64` and the recorded fingerprints), serializes them, validates (§3.6, §4), compares (§5) and emits the body (§6).

**Per-vector result: 23/23 identical on the first run.** Every reference and candidate catalogue SHA-256 matched, all 43 rebuilt and 3 fabricated. Every `bodySha256` matched:

| Vectors | Outcome (exact; normalized) |
| --- | --- |
| go-identical, go-function-in-host, go-partial-copy, go-comments-whitespace, rust-comments-whitespace, rust-function-in-host, rust-identical | match; match |
| go-renamed / rust-renamed | no-shared-fingerprints / below-minimum-evidence; match |
| go-boilerplate-only (6 pairs) | all no-match |
| go-boilerplate-unsuppressed | below-minimum-evidence; match |
| go-no-overlap | no-shared; no-shared |
| go-duplicate-regions, go-tie-equal-candidate-span | ambiguous; ambiguous |
| go-repeated-hash-self | match; ambiguous |
| go-insufficient-tokens, go-malformed-candidate | pair-level insufficient-tokens / candidate-extraction-error |
| 6 rejection vectors | the stated code and side |

My program also rejects all 16 comparison-config negatives.

**Guesses I had to make. Each is an ambiguity finding, even though it matched.**
- G1 (**matters**): fractions are *not reduced*. §5.9 (line 202) says only "integer pair … nothing is rounded". I chose unreduced only because I had already seen `14/14` in one expected body. Reducing changes 14 of the 23 bodies.
- G2: the names of the `inputs` keys and the exact shape of the echoed `comparison` object (including `comparison` and `modes`) appear only in the schema, not in §6.2.
- G3: every artifact in one catalogue must share one extraction-config byte string. The contract implies this (one `extractionConfig`) but never says what a builder does with mixed inputs.
- G4: `unsupported-config` (offset `null`, extraction §2) cannot be a catalogue entry, because the schema's offset is a count. §3.6 (line 84) is silent on this.
- G5: ambiguity is decided by shared seed *positions*, not overlapping *spans*. The text says positions, but no vector distinguishes the two (see Part 1b).
- G6: `kgramCount` is computed as `max(0, tokenCount − k + 1)`, because extraction §9 makes k-gram lists optional in production.

## Part 1b — Shared-mistake search and my own corruptions

The checker streams seeds per diagonal; the generator groups by diagonal; I group as well. All three agree with the text everywhere I could test. **I found no reading on which the checker and the vectors jointly contradict the contract.** The shared weakness is coverage: whatever the vectors do not exercise, neither program checks.

I put wrong-but-plausible implementations into `variants.py`, wrote each one's bodies into a copy of `matching.json` with digests refreshed, and ran `check_matching.py <copy>` on it:

| # | Wrong implementation | Checker on shipped vectors | With my 2 boundary vectors |
| --- | --- | --- | --- |
| 1 | Merge joins gap ≤ mergeGap+1 (off by one at the max-gap boundary) | **ACCEPTED** (PASS) | rejected ("seed gap exceeds mergeGap") |
| 2 | Ambiguity by span overlap instead of shared positions | **ACCEPTED** (PASS) | rejected (outcome differs) |
| 3 | Merge uses `<` mergeGap | rejected (10 vectors) | rejected |
| 4 | Minimum evidence `d > min` (off by one) | rejected (boilerplate-unsuppressed, repeated-hash-self) | rejected |
| 5 | Document frequency counted per occurrence, not per file | rejected (**only** go-repeated-hash-self) | rejected |
| 6 | Document frequency over reference ∪ candidate | rejected (only go-boilerplate-only) | rejected |
| 7 | Regions ordered by (diagonal, p) | rejected | rejected |
| 8 | Fractions reduced | rejected | rejected |
| 9 | `below-minimum-evidence` ranked above `ambiguous` | rejected (only go-repeated-hash-self) | rejected |
| 10 | First occurrence only, no cross product | rejected | rejected |
| 11 | Containment excluding common hashes (OD-C2 b) | rejected | rejected |
| 12 | One-to-many counted as `match` (OD-C6 b) | rejected | rejected |
| 13 | Catalogue/body with trailing LF (OD-C1 b) | rejected | rejected |

The shipped vectors never split a region on the same diagonal except once, at gap 10 (`go-boilerplate-only`). Within regions, the seed gaps are only 1–4. My boundary vectors were built as fabricated catalogues; the correct output PASSes the checker:
- `rv-gap-boundary`: seeds (0,0) and (5,5) with a non-shared fingerprint at 3; expected below-minimum-evidence.
- `rv-span-overlap-disjoint-positions`: candidate spans [0,14) and [6,20) with no shared position; expected match.

Two further gaps:
- No matching input contains a non-ASCII byte, so byte versus code-point spans are never separated at this layer.
- No vector has an error or insufficient-tokens artifact on the *reference* side.

The checker cannot take a purely synthetic catalogue. A fabricated side still needs a resolvable `artifacts` list (`build_catalogue` raises `TypeError` otherwise).

## Part 1c — Findings, most severe first

1. **High — suppression of common code makes a pair's outcome depend on unrelated reference files, and the reference holder controls it** (§5.2, lines 137–141).
   - Measured: with `commonArtifactThreshold` 4 (equivalent to dropping one of the three references), all three `put.go` pairs in `go-boilerplate-only` become normalized `match`. With 3 references, each is one df count from `match`: a region with 2 seeds, 1 of them common.
   - The body shows `referenceArtifactCount`, which counts error entries too, so it does not show whether suppression could act.
   - Line 140 says "artifacts"; it should say "`ok` artifacts".
   - Fix: decide OD-C5 for **(b)**, an explicit boilerplate catalogue bound by digest in the comparison config. Until then, add `referenceOkArtifactCount` and a per-mode `commonHashCount` to the body.
2. **High — minimum evidence counts seeds, not distinct hashes** (§5.6, line 173).
   - In `go-repeated-hash-self`, exact mode returns `match` from one hash repeated twice. Periodic code therefore satisfies "2 distinctive fingerprints".
   - Counting distinct non-common hashes changes only this vector (both modes become below-minimum-evidence). I measured this.
   - Fix: make it an explicit OD and recommend distinct hashes.
3. **High — the vectors do not pin behaviour at the merge boundary or the definition of ambiguity** (corruptions 1 and 2), and several decisions rest on a single vector (5, 6, 9).
   - Fix: add my two boundary vectors.
   - Also add: a reference-side error and a reference-side insufficient-tokens artifact; one non-ASCII input; a duplicate-`catalogueVersion` catalogue (finding 6).
   - Also add the M2.2/M2.3 classes that are missing (Part 3, item 5).
4. **Medium — fractions: reduction is unstated** (line 202). Fix: "numerator and denominator are the raw counts, never reduced".
5. **Medium — the report's privacy class is unstated, and §1 overclaims** (line 18: "compare without exchanging code").
   - The parties do exchange catalogues, and §3.7 says unkeyed fingerprints allow guessed code to be tested against them.
   - The body carries reference artifact SHA-256s (whole-file guess confirmation), ids and byte spans.
   - `provenance.note` (1024 chars, no charset) and `implementation.name` can carry source text verbatim (`report.schema.json`).
   - Fix: say that catalogue exchange discloses testable features. Classify the body as private by default. Restrict `note` to the §3.3 charset or drop it.
6. **Medium — lenient JSON parsers diverge on codes.** A catalogue with `catalogueVersion` duplicated, the valid value first and `draft-9` last, is `malformed-catalogue` under §3.6 step 1. Go's `encoding/json` keeps the last value and reports `unsupported-catalogue`. Fix: add this vector, and state that duplicate detection precedes any field read.
7. **Medium — output size and implementation discretion** (OD-C7, line 318; §6.3, line 246).
   - Cross-product seeding is quadratic, and "fails outside the report" lets two implementations differ on which inputs produce a body at all.
   - Fix before implementation: put a cap in the comparison config, applied deterministically after §5.5 ordering. Add a `truncated` count, and keep per-status region counts uncapped.
8. **Medium — the account of the author's own findings is partly inaccurate** (§10).
   - §9, line 297 says the `go-repeated-hash-self` values "were written by hand … before any computation". README line 42 says the normalized channel was *not derived* until computation showed it.
   - The headline result of `go-boilerplate-unsuppressed` (normalized `match`, §10 finding 2) has hand expectation `codeIn: ALL` (`build_vectors.py:659`). That is vacuous, yet the vector is labelled `derivation: hand`.
   - Fix: mark post-hoc values `derivation: computed-then-reviewed` and give the unsuppressed vector a real hand expectation.
   - On findings 1–3, the contract should state normatively that suppression is advisory and corpus-dependent, that a match on boilerplate is expected, and that results at a margin of one are reported as such. Finding 2 above removes the repeated-hash case.
9. **Low — §3.6 rejects legal configurations.**
   - `0 ≤ start < end` (line 86) fails for Go with k = 1: an inserted `;` k-gram has the empty span `[e,e)`, and at end of input `e = byteLength`.
   - Extraction §10 allows any positive k. `report_semantic_check` has the same rule.
   - Fix: allow `start ≤ end` and `start ≤ byteLength`, or require k ≥ 2 in this contract.
10. **Low — G2–G4 above**: move the `inputs` names into §6.2, require one config per catalogue, and say that an `unsupported-config` extraction yields no catalogue.

**Consistency with spec/ and schemas/.**
- Catalogue bytes = `C` of `sha256-salted-catalogue-v1`. The profile triple matches `evidence.schema.json`.
- Core's "insufficient matching evidence" and its separation of results are respected (§7, §8), and the closed codes and precedence are complete for what the vectors exercise.
- One mismatch: roadmap M2.4 asks that the *provenance* carry the config digest, but the contract puts it in `body.inputs` (`roadmap-v2.md:64`).
- No calibrated-rate leakage: there is no score field, and the fractions are counts.

**Open decisions: settle before implementation (my recommendation in brackets).**
- OD-C1 [a]; OD-C2 [a, as implemented, plus finding 4]; OD-C3 [a for draft-1]; OD-C4 [a]; OD-C6 [a]; OD-C8 [a]; OD-C9 [a]; OD-C11 [a].
- OD-C5 [b, finding 1]; OD-C7 [b with a config cap, finding 7]; OD-C10 [a after the finding-3 additions, since M2.6 requires `test-vectors/`].
- New: distinct-hash evidence (finding 2); fraction form (finding 4); report privacy class (finding 5).

## Part 2 — use-cases-verification-plans.md

- All 44 gate IDs exist as rows in roadmap-v2. Both "Today" commands re-ran for me: `validate` exits 0 and prints PASS; the unit tests run 6/6 OK. `use-cases.md` has 5 UC table rows plus UC-6.
- **Stale against roadmap-v2** (medium). The plans still say there is no gate for UC-2 origin records, P-3 atomic writes/default location, or P-5 index ranking (lines 22–23, 31, 76, 82, 97, 106, 108, 126–127). M2.7, M2.8 and M2.9 now exist. Fix: cite them and remove decisions 2 and 3.
- **Spans** (medium, lines 10 and 12): "candidate spans equal expected source ranges". Contract §5.5 says spans are lower bounds over the matched k-grams (`go-identical` localizes [16,124) of a 127-byte file). Fix: "equal the hand-derived matched-k-gram spans and lie within the expected source range".
- **Plans that pass trivially** (medium):
  - UC-1/W-2 pass with any control outcome, since only presence and denominator are checked (line 12).
  - UC-5 passes "M3.6 recorded either way" (line 44).
  - UC-2 "stays separate from ancestry" is a judgment (line 20).
  - Fix: state these as format-only plans and add an observable check. For example, a control's outcome code is listed in the report; the rights field is absent from `report.schema.json`.
- **P-4** (low, line 79): "comparison candidate" is not a contract code. Use the §6.3 code, `match`, with the report's `bodySha256`.

## Part 3 — Roadmap gates

1. **M2.9** (rework, `roadmap-v2.md:69`).
   - "No index field; a fixture adding one fails `validate`" is already true through `additionalProperties: false`, so it is satisfied trivially.
   - "Reversing candidate order leaves the body identical" is guaranteed by the §5.3 id ordering.
   - "Swapping in a second index" changes the candidate set, and with it `candidateCatalogueSha256` and the pairs. The body cannot stay identical, and the contract has no index input to record it.
   - Fix: the body records candidate generation (`exhaustive` or a digest of the selected id set). The gate tests that the same set in any order, from either index, gives an identical body, and that a different set changes only the recorded set and the pairs.
2. **M2.7** (rework, line 67). "Each report links matched regions to origin records" contradicts contract §1 (origin records out of scope) and the closed body schema. Fix: a separate review-packet record that references `bodySha256` plus a region key `(reference id, candidate id, mode, first seed)`; §5.5 already makes the first seed unique.
3. **M2.8** (ready after fixes, line 68). It is checkable by a non-author. Fix:
   - Name the fault-injection mechanism for each of the 3 points.
   - Require the private-default catalogue bytes to equal the expected catalogue digest, so that "writes nothing" cannot pass.
   - Drop "keys" until M4 produces any.
4. **M0.1** (ready after fixes, line 41). "A non-author counts 15/15" checks only that plans are present, and the 15 depend on the author's own grouping of implementation-patterns headings into P-1…P-7 (P-5 is a paragraph, not a heading). Fix: the non-author derives the list from `docs/` independently. Each plan must name a pass/fail that is a command exit code or a count, with no judgment words.
5. **M2.6 versus these vectors.** The vectors lack the Unicode, shadowing, independent-same-task and vendor classes that M2.2/M2.3 require, so the contract's gate claim (line 3) is not yet met.

## Confirmation pass (draft-2, 2026-11-22)

**Clean room.** I updated my program (`$TMPDIR/cr/cleanroom2.py`) from the draft-2 text before opening the new checker. **47/47 vectors are identical**, covering every catalogue digest (67 rebuilt, 30 synthetic, 4 fabricated) and every `bodySha256`. `check_matching.py` passes every section, including its 18/18 wrong-implementation self-test. One guess remains, G7: does `suppression.artifactCount` (contract line 281) count all entries or only `ok` ones? Every suppression catalogue in the vectors is all-`ok`, so the vectors cannot tell.

**Wrong implementations against the checker** (`$TMPDIR/cr/corrupt2.py`; variant bodies with refreshed digests):
- **Rejected:** all 13 earlier variants, including the two it used to accept (merge gap+1; ambiguity by span overlap). Also seeds-not-distinct, common hashes excluded from evidence, seed limit `≥`, outcome or counts taken after the cap, and last-duplicate-key-wins.
- **Accepted (PASS), 6 cases:**
  - (a) reference document frequency still applied on top of the boilerplate catalogue; no vector has ≥2 `ok` reference artifacts;
  - (b) ambiguity computed only among the regions listed under the cap; the cap vectors have no reportable regions;
  - (c) config `none` with a supplied suppression catalogue, silently ignored;
  - (d) suppression binding checked after catalogue validation;
  - (e) the suppression config check run before the candidate's (§5.1 steps 6–7);
  - (f) the G7 count.

**Part 1 findings: resolved / not resolved.**
- 1 (suppression depends on unrelated files): resolved by design (lines 152, 176–178; OD-C5 line 412). **Not tested:** the line-178 invariance claim has no vector, so (a) passes.
- 2 (distinct-hash evidence): resolved (lines 218–225).
- 3 (coverage): resolved by the `rv-gap-*` and `rv-span-overlap` vectors, reference-side failures, non-ASCII and duplicate-key vectors. Vendor class still open and declared (line 428).
- 4 (unreduced fractions): resolved (line 78).
- 5 (privacy class, §1 overclaim, free-text provenance): resolved (lines 22, 113–122, 326–340).
- 6 (duplicate keys): resolved (line 100), with one vector only.
- 7 (output caps): resolved (lines 191–237), but ambiguity-before-cap is untested (b).
- 8 (author's account of own findings): resolved (lines 364–400; README line 34).
- 9 (k = 1 spans): resolved (line 109).
- 10 / G2–G6: resolved (lines 38, 53, 65, 229, 277–284).

**New problems in Part 1:**
- G7 above.
- Line 325 still says M2.4 checks the config digest in provenance; M2.4 now puts it in the body (`roadmap-v2.md:64`).
- A region key can name only a listed region. Regions past `maxRegionsPerMode` cannot be linked, and M2.7's semantic check would reject a link to one that exists. Say so in §5.5.

**Part 2: resolved / not resolved.**
- Resolved: stale "no gate" claims (lines 19–22, 31, 78); span wording (lines 10–13); trivial passes in UC-1 (lines 12–13), UC-2 (line 20) and UC-5 (lines 44–45). UC-5 still depends on M3.6 (`roadmap-v2.md:108`), which still reads "recorded verdict".
- P-4 resolved (line 81), but it cites §6.3; the codes are now in §6.4. All 47 gate IDs exist in roadmap-v2.
- **New, blocking:** M0.1 (`roadmap-v2.md:41`) counts implementation-patterns headings *and example-matrix rows*, and from use-cases only table rows and UC-6. The plans exclude the matrix rows (line 69, "covered by M0.3", which asks for no plan) and include W-1/W-2.
- Stale text: line 19 ("depends on the gate being reworded"), line 78 ("per Part 3's rewording"), lines 106/119 ("15"), line 121.

**Part 3: resolved / not resolved.**
- Resolved: M2.7 (line 67, subject to the truncation note), M2.8 (line 68), the M2.6 claim (now stated honestly as unmet, contract line 428).
- M0.1: reworded, but now conflicts with the plans (above).
- **M2.9: not resolved, and it now contradicts the contract.** Line 69 says "the body records candidate generation". Contract lines 25 and 467 and `report.schema.json` give the body no such field. "A different set changes only the recorded set and the pairs" is also false: `inputs.candidateCatalogueSha256` and `candidateArtifactCount` change too.
- **New:** M2.10 (line 70), "adding 1 unrelated reference file", is passed by implementation (a) unless the reference already holds threshold − 1 files that share the idiom. Specify that; the resulting vector closes (a).

**Final verdicts.**
- **Part 1: ready.** Non-blocking: add an invariance vector, a cap vector whose reportable regions straddle the cap, and a "`none` plus supplied catalogue" vector; define G7.
- **Part 2 — blocking:** use one capability source in both this file and M0.1 (matrix rows and walkthroughs in or out of both), then remove the stale lines.
- **Part 3 — blocking:** M2.9 (move the candidate-generation record into a separate record keyed by `bodySha256`, or add the field to the contract; fix the diff claim) and M0.1 (align with the plans). M2.7, M2.8 and M2.11 are ready; M2.10 is ready once tightened as above.
