# Draft: verification plans for docs/use-cases.md (roadmap gate M0.1)

Status: draft (revised after review Part 2) for later merge into [use-cases.md](../../docs/use-cases.md); that file is not edited. Gate IDs refer to [roadmap-v2.md](../../ROADMAP.md). [Review H2](../reviews/roadmap-v2-review.md) found the plan clause missing. Matching terms follow [catalogue-report-contract.md](catalogue-report-contract.md). No thresholds are set here. A number marked **freeze first** must be measured and committed under the named gate before any pass/fail is read.

Execution key: **Today** = runs now with existing files. **Needs X** = depends on unbuilt pieces. Two commands run today (rerun by me, 2026-11-22): `.venv/bin/python tools/validate.py` (exit 0, prints PASS) and `.venv/bin/python -m unittest discover -s tests` (6 tests, OK). Both check formats, commitment, DSSE framing and contract rejections only. The validate output itself says no signature, timestamp, detector or rights claim was verified. No detector exists, so no similarity or mark-detection plan runs today.

## Plans for docs/use-cases.md

### UC-1 — Find an extracted function
- **Checked:** reported spans are the matched-k-gram spans of the contract (§5.5: half-open UTF-8 byte offsets, a lower bound on the copied extent, never widened); control cases return their frozen expected outcome codes; fragment containment and whole-file similarity are separate fields.
- **By:** the frozen manifest of M2.2 (exact; formatted fragment in large host; rename/shadowing; Unicode/repeated minima/tiny file) and M2.3 control classes, run through the walkthrough under `scripts/offline` (M2.1). Hand-derived vectors (M2.6) give, per case, the expected matched-k-gram spans, containment, similarity and outcome code.
- **Pass:** for every M2.2 case the reported spans equal the hand-derived matched-k-gram spans and lie within the expected source range (N/N). For every M2.3 control case the report's outcome code equals the code frozen in the manifest before the run (N/N); where the frozen code is `match` the control is a counted false alarm, not an error. Each class appears with candidate count and denominator. Two runs give an identical canonical report body (M2.4). Containment and similarity diverge in the large-host fixture (M2.5). Unsupported or malformed input returns the specified error code in both implementations (M1.6).
- **Fail:** any span that differs from the hand-derived spans or exceeds the source range; any control whose code differs from its frozen code (including a control that matches when `no-match` was frozen, and the reverse); a missing class; a report that differs between runs.
- **Today:** only the format layer (`validate`). **Needs** M1 profile, extractor, comparator, `scripts/offline`.
- **Unverifiable:** absence of reuse; heavy rewrites; the false-alarm rate on real code until M3.4. The frozen control codes are hand-derived expectations, not thresholds. Copied extent beyond the matched k-grams.

### UC-2 — Review license history
- **Checked:** a review packet links each matched region to origin and dependency records, with the comparison result and the rights state kept apart.
- **By:** M2.7 (origin and dependency record schema; fixtures for own-origin, vendored with archived licence-text digest, and historical permitted copy; no rights-verdict field), the boilerplate/vendor control class (M2.3), the example-matrix rows "Common boilerplate/vendor region" and "Historical permitted copy" in [implementation-patterns.md](../../docs/implementation-patterns.md#example-matrix), and the licence fields in the corpus manifest (M3.1). M2.7 now links by a separate review-packet record that cites the report `bodySha256` and a region key (reference id, candidate id, mode, first seed); a key absent from the referenced body fails its semantic check. Only regions listed in the body can be linked (see §5.5 of the contract).
- **Pass:** `validate` accepts the 3 fixtures and rejects 1 fixture per required field (counts, exit code); every region key in a packet resolves to exactly 1 region in the report whose `bodySha256` it cites; neither the report schema nor the packet schema has a rights-verdict field (a fixture adding one fails `validate`).
- **Fail:** an unresolved or ambiguous region key, a mismatched `bodySha256`, or an accepted rights field.
- **Today:** nothing. **Needs** the M2.7 schema and fixtures, I2.
- **Unverifiable:** legal status; whether a later licence change affects earlier expression; completeness of archived notices; whether the origin records are true.

### UC-3 — Preserve a private reference
- **Checked:** disclosed bytes open the recorded commitment; changed nonce, catalogue or length is rejected; stored files are exact bytes.
- **By:** [commitment.json](../../test-vectors/commitment.json) through `validate` and `tests/test_contract.py` (`test_commitment_detects_changed_openings`, `test_commitment_rejects_wrong_nonce_length`). Independent Go/Rust reproduction is M4.2. Design review is M4.6. Timestamp handling is the M4.5 decision.
- **Pass:** unchanged synthetic opening accepted; each changed opening rejected; two independent implementations reproduce the vectors (M4.2).
- **Fail:** any accepted changed opening or a digest mismatch.
- **Today:** yes, for the Python reference (command above). **Needs** M4.2 evidence committed (it exists, uncommitted: [signing-policy-results.md](../lanes/signing-policy-results.md)), M4.6.
- **Unverifiable:** ownership, earlier existence, trusted time. Opening reveals the whole catalogue (a design limit, not testable away). Atomic-write behaviour under interruption is covered by M2.8 (3 fault-injection points); the keys part waits for M4.

### UC-4 — Check a received evidence packet
- **Checked:** payload bytes, subject digest, signer trust and time are separate verdicts, each with a reason.
- **By:** M4.3 negative vectors (tampered payload/type/signature, untrusted key, malformed or duplicate-key payload, subject mismatch, each with a distinct reason code). M4.4 runs two strict parsers over them. M4.1 covers Go/Rust DSSE interop. M4.5 covers the in-toto adapter fixtures and trust policy. Optional comparison rerun uses M2.1.
- **Pass:** identical bytes and reason codes across both implementations on every M4.3 vector; a valid signature from an untrusted key never satisfies trust; a changed subject fails the digest verdict while the signature verdict is unaffected.
- **Fail:** a collapsed single verdict, a shared or missing reason code, or implementation disagreement.
- **Today:** PAE framing and ambiguous-JSON rejection only (command above). **Needs** M4.3 fixtures, a verifier, M4.4.
- **Unverifiable:** truth of a signed assertion; comparison when private reference material is absent; timestamp authority trust (unless the M4.5 decision adopts the adapter).

### UC-5 — Assess transformations
- **Checked:** recall by transformation and fragment size, false alarms per repository search, abstentions, candidate volume, runtime, peak memory, failure cases.
- **By:** the M3 protocol. Corpus manifest and split (M3.1, M3.2), threshold/config freeze as git ancestors of the first held-out result (M3.3), report (M3.4), independent rerun (M3.5), verdict against the budget (M3.6). Budget and unit: M3.0.
- **Pass:** M3.4 figures all carry denominators; M3.5 counts are identical on the rerun; and M3.6 is computed, not chosen: false alarms per repository search at the frozen configuration are at or below the number recorded in M3.0. The M3.0 budget is **freeze first**; no recall floor is invented here, and recall is reported without a pass line.
- **Fail:** any figure without a denominator; a freeze commit that is not an ancestor; counts that differ on rerun; or false alarms above the M3.0 budget, which M3.6 records as negative-result. The last is a fail of usefulness, and the report stays valid evidence.
- **Today:** nothing. **Needs** M1, M2, a licensed corpus.
- **Unverifiable:** universal resilience; results outside the tested profile, corpus and pipeline. Behaviour validity of rewritten code is assessed independently.

### UC-6 — Recognize distributed content
- **Checked:** marks embed reproducibly; marked outputs still function; the mark is recovered; unmarked, wrong-key, removal, transplant and partial-fragment controls behave.
- **By:** M2E.1 (frozen eligible subset, transformations, minimum net authenticated bits, behaviour checks, survival rates, owner-approved) then M2E.2, .3, .4, .5, .6; M2E.7 compares mark-only, fingerprint-only and combined detection. M2E.0 records select-or-omit. Existing synthetic evidence SYN.1–SYN.5 is for rejected candidates only.
- **Pass:** every marked-output digest reproduces from recorded seeds (M2E.2); k/k functionality checks on marked outputs only (M2E.3); each control has a case and denominator (M2E.5); each declared transformation reaches its frozen survival rate, else negative-result (M2E.6). The minimum bit budget and survival rates are **freeze first**.
- **Fail:** a rate below its frozen value, a transplant decoded as same-context evidence, or non-reproducible digests.
- **Today:** only reruns of the existing research experiments (run by the review, not by me): `go test -count=1 -v ./...` in `research/experiments/go-carrier` and `python3 research/experiments/rust-carrier/experiment.py`. They show SYN.1 55/55 intentional insertions recover and SYN.3 55/55 reset under cheap canonicalization, so no candidate currently qualifies. **Needs** a selected carrier, the M2E.4 mark-record schema, a new owner-approved census protocol.
- **Unverifiable:** survival under arbitrary rewrites; ownership or permission; behaviour on any carrier not yet chosen.

### W-1 — Embedding walkthrough (use-cases.md, "First walkthroughs")
- **Checked:** reference → embed → validate → transform or extract → detect → inspect, with unmarked, independently marked and transplanted controls.
- **By:** M2E.2–M2E.5 as one scripted run; the recipe comes from the M2E.1 freeze, not from the demo.
- **Pass/fail:** as UC-6, plus every step's command exits 0 in order. **Needs** a selected carrier; **Today:** none. **Unverifiable:** any recipe not selected.

### W-2 — Extracted-matching walkthrough (`reference.py`, `candidate.py`, `control.py`)
- **Checked:** the five numbered steps, including control outcome shown even if a false alarm, directional containment against whole-file similarity, and separation of permission.
- **By:** M2.1 (offline run), M2.2/M2.3 (the three files become cases), M2.5, M2.6; M5.3 has a non-author reproduce it from a clean clone.
- **Pass/fail:** as UC-1, including the control rule: `control.py` must return the outcome code frozen for it, and a `match` there is shown as a false alarm. **Today:** none; the three files do not exist yet. **Unverifiable:** reviewer judgment in step 5 (a person inspects origin records), and the permission assessment.

## Plans for capabilities added in docs/implementation-patterns.md

Each H2 heading of that file other than "Example matrix" (whose rows are fixtures for UC-1…UC-6, covered by M0.3) is one capability. A non-author can recount with `grep -n '^## ' docs/implementation-patterns.md`: 6 headings, minus "Example matrix", gives 5. The "Candidate retrieval" paragraph sits under H-3, and the adapters sentence under H-5; neither is a heading, so neither gets its own row.

### H-1 — "Embed and detect as an explicit pair"
- **By:** M2E.4 (private record: original and marked digests, profile/config digest, seed/key reference, never key bytes), M2E.5, M2E.7. **Pass:** `validate` accepts the record example and rejects 1 fixture per required field; detection returns evidence, unsupported or insufficient evidence, never a single score. **Needs** a carrier. **Unverifiable:** blind, reference-assisted and key-assisted modes beyond the selected carrier; the marking algorithm itself.

### H-2 — "Keep deterministic extraction separate from comparison"
- **By:** M1.1 (profile answers every pre-registration item), M1.2 (7 vector classes, hand-derived, with the `[8, 4, 4, 7, 2]` winnowing example as a candidate hand vector), M1.4 (two independent lexers equal committed bytes), M1.5, M1.6. **Pass:** output equals expected bytes in every vector; each MUST maps to a test that fails when it is violated. **Today:** none. **Unverifiable:** untestable MUSTs, which M1.5 lists and has spot-checked.

### H-3 — "Treat storage as a boundary" (includes the retrieval-index paragraph)
- **By:** M1.3 (catalogue schema binds profile ID, config digest, artifact digests; valid and rejection fixtures), M2E.4, M4.2; M2.8 (storage: 0 files written under the checkout with no path option, 3/3 fault-injection points leave the previous file byte-identical); M2.9 (index ranking is not evidence: no rank field in the report schema; same candidate set in any order or from either index gives an identical body: the body records `exhaustive` or the digest of the candidate-id set, and a different set changes only that record and the pairs). **Today:** catalogue example and schema validity through `validate`. **Needs** I2 for M2.8 and M2.9. **Unverifiable:** permissions on a user's real filesystem beyond the tested fixture; index quality, which M3.4 reports as candidate volume and runtime only.

### H-4 — "Preserve independent verification results"
- **By:** M1.3 report schema with separate fields, M4.3, M4.4. **Pass:** for the changed-subject example, signature = pass, subject digest = fail, time = not checked and comparison = outcome code `match` (§6.4) with the report's `bodySha256`; the expected result equals the committed vector. **Needs** TW-03 schema and a verifier. **Today:** statement schema rejection cases in `tests/test_contract.py` only.

### H-5 — "Reproducible evaluation, then adapters"
- **By:** M3.1–M3.5 as in UC-5; adapters SK.1, SK.2 (canary strings appear 0 times in transcripts), C2PA.1–C2PA.3 (no compatibility claim until C2PA.2). **Needs** I2 commands. **Unverifiable:** corpus representativeness; any adapter before its gates are met.

## M0.1 table

Input and limit are abbreviated from use-cases.md and implementation-patterns.md. Rows W-1/W-2 and H-1…H-5 are labelled so they cannot be confused with UC rows; each H row names its heading in implementation-patterns.md.

| Capability | Input | Observable output | Limit | Plan present | Gate IDs |
| --- | --- | --- | --- | --- | --- |
| UC-1 Find an extracted function | Authorized reference snapshot, local candidate | Candidate source ranges, profile/config, digests, comparison evidence | Rewrites evade; common code matches; no result is not absence | yes | M1.1–M1.6, M2.1–M2.6, M3.4 |
| UC-2 Review license history | UC-1 evidence, region origins, dependency records, archived licence text | Reproducible review packet linking regions to history | No legal determination; later licence does not decide earlier expression | yes | M2.3, M2.7, M3.1 |
| UC-3 Preserve a private reference | Catalogue bytes/config, fresh commitment opening | Disclosed bytes open the recorded commitment | Not ownership or earlier existence; date not trusted; opening reveals all | yes | M4.2, M4.5, M4.6 |
| UC-4 Check a received evidence packet | Payload, subject digest, signer, time evidence, optional reference | Separate verdicts with reasons and localized evidence | Valid signature on false assertion; missing private material | yes | M2.1, M4.1, M4.3, M4.4, M4.5 |
| UC-5 Assess transformations | Recorded transformations, positives, unrelated and same-task controls | Held-out detection and false-alarm report with failures and costs | Only the tested profile, corpus and pipeline | yes | M2.3, M3.0–M3.6 |
| UC-6 Recognize distributed content | Original bytes, authorized to modify; profile; private mark record | Marked output, validation, localized detection evidence or insufficient evidence | No scheme or survival guarantee selected; not ownership | yes | M2E.0–M2E.7, SYN.1–SYN.5 |
| W-1 Embedding walkthrough | Synthetic reference, test mark, controls | Detection result per control | Recipe set by the research gate | yes | M2E.1–M2E.5 |
| W-2 Extracted-matching walkthrough | `reference.py`, `candidate.py`, `control.py` | Spans, control outcome, containment vs similarity | Files do not exist yet; permission is separate | yes | M2.1, M2.2, M2.3, M2.5, M2.6, M5.3 |
| H-1 "Embed and detect as an explicit pair" | Original bytes, mark, profile/config, secret | Marked bytes, private record; detection evidence | Transplantation survives crypto checks; algorithm undecided | yes | M2E.4, M2E.5, M2E.7 |
| H-2 "Keep deterministic extraction separate from comparison" | Bytes, profile, config bytes | Features, spans, diagnostics; explicit error | Pinned grammar only; no silent substitution | yes | M1.1–M1.6 |
| H-3 "Treat storage as a boundary" | Catalogue, config, artifact digests, local feature index | Bound, atomically written private files; candidates then alignment | Ranking is not evidence; real-filesystem behaviour beyond fixtures | yes | M1.3, M2.8, M2.9, M2E.4, M4.2 |
| H-4 "Preserve independent verification results" | Statement, candidate, policy | Per-field results (subject, signature, trust, time, comparison, rights) | Field names subject to TW-03 | yes | M1.3, M4.3, M4.4 |
| H-5 "Reproducible evaluation, then adapters" | Corpus with rights, grouped splits; stable commands, C2PA fixtures | Scoped benchmark report; wrapped diagnostics; interop fixtures | Scoped claims only; adapters wait for gates | yes | M3.1–M3.5, SK.1, SK.2, C2PA.1–C2PA.3 |

**Count: 13 rows.** From use-cases.md: 8 (UC-1…UC-6, W-1, W-2). From implementation-patterns.md: 5 (H-1…H-5, one per heading). The 15 in roadmap-v2 M0.1 predates this regrouping and needs updating to 13.

## Verification notes

Counted with grep on 2026-11-22:
- `grep -cE '^\| UC-[0-9] ' docs/use-cases.md` gives 5 (UC-1…UC-5 table rows); `grep -c '^\*\*UC-6'` gives 1; the two walkthroughs ("For embedding:", "For extracted matching:") give 2. Total 8.
- `grep -n '^## ' docs/implementation-patterns.md` lists 6 headings; "Example matrix" is excluded (fixtures, M0.3), leaving 5.
- This file's table: `grep -cE '^\| (UC|W|H)-[0-9]+ '` gives 13, each label once.
- Gate IDs are checked against roadmap-v2.md rows by script; links with `test -e`; whitespace with grep.
- M0.1 now asks a non-author to derive the capability list from `docs/` independently; the recount commands above are written for that. The agreed list is 13 rows. M0.1's wording also names example-matrix rows, which this draft excludes as fixtures covered by M0.3; the gate text is being aligned.
- M0.1 also asks each plan's pass/fail to be an exit code or a count. UC-1, UC-2 and UC-5 are written that way; the `Needs` plans still state some observations in words and should be tightened when their fixtures exist.

## Decisions for the coordinator

1. Whether W-1 and W-2 count, or only UC-1…UC-6 (6 rows); the agreed list currently includes them (13 rows).
2. M0.1 wording mentions example-matrix rows; either add them as capabilities or drop that phrase.
3. UC-5's computed verdict needs M3.6 reworded as a comparison against the M3.0 number; `roadmap-v2.md` still reads "recorded verdict".
4. M2E.4 and M4.2 evidence is still uncommitted, so UC-3 and UC-6 "Needs" items stay open until it is committed.
