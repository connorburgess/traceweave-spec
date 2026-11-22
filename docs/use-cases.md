# What Traceweave is for

Traceweave aims to help people **mark content so it can be recognized later, find candidate reuse, and preserve reviewable evidence**. Start locally with code. Text, images and audio are future profiles, not working detectors.

Today the repo supplies draft formats, synthetic fixtures and validation tools. The workflows below are planned. A match is evidence to review; it is not a verdict about ownership or permission.

| Case | Person and question | Inputs and workflow | Useful result | Important limit | Verification plan |
| --- | --- | --- | --- | --- |
| UC-1 — Find an extracted function | A software maintainer asks whether a larger project contains a fragment of their reference code | Catalogue an authorized reference snapshot; compare a locally available candidate; inspect aligned spans | Candidate source ranges, profile/config, exact artifact digests and comparison evidence | Heavy rewrites may evade detection; common code may match; no result does not establish absence | [UC-1 plan](#uc-1-verification-plan); gates M1.1–M1.6, M2.1–M2.6 |
| UC-2 — Review license history | A reviewer asks where a matched region came from and which historical notices need inspection | Combine UC-1 evidence with region origins, dependency records and archived license text | A reproducible review packet linking regions to historical evidence | A later restrictive license does not decide the status of all earlier expression; the detector makes no legal determination | [UC-2 plan](#uc-2-verification-plan); gates M2.3, M2.7, M3.1 |
| UC-3 — Preserve a private reference | A creator wants to retain a record of a reference catalogue without publishing its contents | Keep exact catalogue bytes/config and a fresh commitment opening privately; optionally sign or timestamp the defined record | Later verification that disclosed bytes open the recorded commitment | Signing alone proves neither ownership nor earlier existence; a claimed date is not trusted time; opening currently reveals the whole catalogue | [UC-3 plan](#uc-3-verification-plan); gates M4.2, M4.5, M4.6 |
| UC-4 — Check a received evidence packet | An auditor wants to separate authenticity from similarity | Verify payload bytes, subject digest, accepted signer and any time evidence independently; rerun comparison if authorized reference material is supplied | Separate verdicts with reasons and reproducible localized evidence | A valid signature on a false assertion remains possible; unavailable private material can prevent independent comparison | [UC-4 plan](#uc-4-verification-plan); gates M2.1, M4.1, M4.3–M4.5 |
| UC-5 — Assess transformations | An implementer asks whether renaming, extraction or rewriting defeats a profile | Apply recorded transformations to synthetic/licensed positives; include unrelated and independently written same-task controls | Held-out detection and false-alarm report, including failure cases and resource costs | Results apply to the tested profile, corpus and pipeline; they do not establish universal resilience | [UC-5 plan](#uc-5-verification-plan); gates M2.3, M3.0–M3.6 |

## Verification plans

Each capability carries a verification plan: what is checked, by which gate, what counts as pass or fail, what runs today, and what cannot be verified. Gate IDs refer to the [roadmap](../ROADMAP.md). Matching terms follow the [draft catalogue and report contract](../research/drafts/catalogue-report-contract.md). No threshold is set here. A number marked **freeze first** must be measured and committed under the named gate before any pass/fail is read.

Execution key: **Today** = runs now with existing files. **Needs X** = depends on unbuilt pieces. Two commands run today (rerun 2026-11-22): `.venv/bin/python tools/validate.py` (exit 0, prints PASS) and `.venv/bin/python -m unittest discover -s tests` (6 tests, OK). Both check formats, commitment, DSSE framing and contract rejections only. The validate output itself says no signature, timestamp, detector or rights claim was verified. No detector exists, so no similarity or mark-detection plan runs today.

### UC-1 verification plan

- **Checked:** reported spans are the matched-k-gram spans of the contract (§5.5: half-open UTF-8 byte offsets, a lower bound on the copied extent, never widened); control cases return their frozen expected outcome codes; fragment containment and whole-file similarity are separate fields.
- **By:** the frozen manifest of M2.2 (exact; formatted fragment in large host; rename/shadowing; Unicode/repeated minima/tiny file) and M2.3 control classes, run through the walkthrough under `scripts/offline` (M2.1). Hand-derived vectors (M2.6) give, per case, the expected matched-k-gram spans, containment, similarity and outcome code.
- **Pass:** for every M2.2 case the reported spans equal the hand-derived matched-k-gram spans and lie within the expected source range (N/N). For every M2.3 control case the report's outcome code equals the code frozen in the manifest before the run (N/N); where the frozen code is `match` the control is a counted false alarm, not an error. Each class appears with candidate count and denominator. Two runs give an identical canonical report body (M2.4). Containment and similarity diverge in the large-host fixture (M2.5). Unsupported or malformed input returns the specified error code in both implementations (M1.6).
- **Fail:** any span that differs from the hand-derived spans or exceeds the source range; any control whose code differs from its frozen code (including a control that matches when `no-match` was frozen, and the reverse); a missing class; a report that differs between runs.
- **Today:** only the format layer (`validate`). **Needs** M1 profile, extractor, comparator, `scripts/offline`.
- **Unverifiable:** absence of reuse; heavy rewrites; the false-alarm rate on real code until M3.4. The frozen control codes are hand-derived expectations, not thresholds. Copied extent beyond the matched k-grams.

### UC-2 verification plan

- **Checked:** a review packet links each matched region to origin and dependency records, with the comparison result and the rights state kept apart.
- **By:** M2.7 (origin and dependency record schema; fixtures for own-origin, vendored with archived licence-text digest, and historical permitted copy; no rights-verdict field), the boilerplate/vendor control class (M2.3), the example-matrix rows "Common boilerplate/vendor region" and "Historical permitted copy" in [implementation-patterns.md](implementation-patterns.md#example-matrix), and the licence fields in the corpus manifest (M3.1). M2.7 now links by a separate review-packet record that cites the report `bodySha256` and a region key (reference id, candidate id, mode, first seed); a key absent from the referenced body fails its semantic check. Only regions listed in the body can be linked (see §5.5 of the contract).
- **Pass:** `validate` accepts the 3 fixtures and rejects 1 fixture per required field (counts, exit code); every region key in a packet resolves to exactly 1 region in the report whose `bodySha256` it cites; neither the report schema nor the packet schema has a rights-verdict field (a fixture adding one fails `validate`).
- **Fail:** an unresolved or ambiguous region key, a mismatched `bodySha256`, or an accepted rights field.
- **Today:** nothing. **Needs** the M2.7 schema and fixtures, I2.
- **Unverifiable:** legal status; whether a later licence change affects earlier expression; completeness of archived notices; whether the origin records are true.

### UC-3 verification plan

- **Checked:** disclosed bytes open the recorded commitment; changed nonce, catalogue or length is rejected; stored files are exact bytes.
- **By:** [commitment.json](../test-vectors/commitment.json) through `validate` and `tests/test_contract.py` (`test_commitment_detects_changed_openings`, `test_commitment_rejects_wrong_nonce_length`). Independent Go/Rust reproduction is M4.2. Design review is M4.6. Timestamp handling is the M4.5 decision.
- **Pass:** unchanged synthetic opening accepted; each changed opening rejected; two independent implementations reproduce the vectors (M4.2).
- **Fail:** any accepted changed opening or a digest mismatch.
- **Today:** yes, for the Python reference (command above). **Needs** M4.2 (see its status in the [roadmap](../ROADMAP.md#gate-tables-m0m5)) and M4.6.
- **Unverifiable:** ownership, earlier existence, trusted time. Opening reveals the whole catalogue (a design limit, not testable away). Atomic-write behaviour under interruption is covered by M2.8 (3 fault-injection points); the keys part waits for M4.

### UC-4 verification plan

- **Checked:** payload bytes, subject digest, signer trust and time are separate verdicts, each with a reason.
- **By:** M4.3 negative vectors (tampered payload/type/signature, untrusted key, malformed or duplicate-key payload, subject mismatch, each with a distinct reason code). M4.4 runs two strict parsers over them. M4.1 covers Go/Rust DSSE interop. M4.5 covers the in-toto adapter fixtures and trust policy. Optional comparison rerun uses M2.1.
- **Pass:** identical bytes and reason codes across both implementations on every M4.3 vector; a valid signature from an untrusted key never satisfies trust; a changed subject fails the digest verdict while the signature verdict is unaffected.
- **Fail:** a collapsed single verdict, a shared or missing reason code, or implementation disagreement.
- **Today:** PAE framing and ambiguous-JSON rejection only (command above). **Needs** M4.3 fixtures, a verifier, M4.4.
- **Unverifiable:** truth of a signed assertion; comparison when private reference material is absent; timestamp authority trust (unless the M4.5 decision adopts the adapter).

### UC-5 verification plan

- **Checked:** recall by transformation and fragment size, false alarms per repository search, abstentions, candidate volume, runtime, peak memory, failure cases.
- **By:** the M3 protocol. Corpus manifest and split (M3.1, M3.2), threshold/config freeze as git ancestors of the first held-out result (M3.3), report (M3.4), independent rerun (M3.5), verdict against the budget (M3.6). Budget and unit: M3.0.
- **Pass:** M3.4 figures all carry denominators; M3.5 counts are identical on the rerun; and M3.6 is computed, not chosen: false alarms per repository search at the frozen configuration are at or below the number recorded in M3.0. The M3.0 budget is **freeze first**; no recall floor is invented here, and recall is reported without a pass line.
- **Fail:** any figure without a denominator; a freeze commit that is not an ancestor; counts that differ on rerun; or false alarms above the M3.0 budget, which M3.6 records as negative-result. The last is a fail of usefulness, and the report stays valid evidence.
- **Today:** nothing. **Needs** M1, M2, a licensed corpus.
- **Unverifiable:** universal resilience; results outside the tested profile, corpus and pipeline. Behaviour validity of rewritten code is assessed independently.

## Primary use case: embed now, recognize later

**UC-6 — Recognize distributed content.** A creator embeds a profile-defined mark into content they are authorized to modify, validates the marked output, and distributes it. Later, they check a candidate for that mark and inspect the localized evidence. Preserve the original and marked artifact digests, embedding profile/configuration, and private mark record. A detection result is separate from ownership and permission.

The first embedding experiment must test unmarked controls, wrong marks or keys, removal, transplantation, partial extraction and transformations. Reject marked outputs that fail the profile’s functional or quality requirements. Detection can return insufficient evidence. No embedding scheme or survival guarantee is selected yet.

### UC-6 verification plan

- **Checked:** marks embed reproducibly; marked outputs still function; the mark is recovered; unmarked, wrong-key, removal, transplant and partial-fragment controls behave.
- **By:** M2E.1 (frozen eligible subset, transformations, minimum net authenticated bits, behaviour checks, survival rates, owner-approved) then M2E.2, .3, .4, .5, .6; M2E.7 compares mark-only, fingerprint-only and combined detection. M2E.0 records select-or-omit. Existing synthetic evidence SYN.1–SYN.5 is for rejected candidates only.
- **Pass:** every marked-output digest reproduces from recorded seeds (M2E.2); k/k functionality checks on marked outputs only (M2E.3); each control has a case and denominator (M2E.5); each declared transformation reaches its frozen survival rate, else negative-result (M2E.6). The minimum bit budget and survival rates are **freeze first**.
- **Fail:** a rate below its frozen value, a transplant decoded as same-context evidence, or non-reproducible digests.
- **Today:** only reruns of the existing research experiments (rerun by the independent review): `go test -count=1 -v ./...` in `research/experiments/go-carrier` and `python3 research/experiments/rust-carrier/experiment.py`. They show SYN.1 55/55 intentional insertions recover and SYN.3 55/55 reset under cheap canonicalization, so no candidate currently qualifies. **Needs** a selected carrier, the M2E.4 mark-record schema, a new owner-approved census protocol.
- **Unverifiable:** survival under arbitrary rewrites; ownership or permission; behaviour on any carrier not yet chosen.

An **embedded mark** changes the content; an **extracted fingerprint** describes existing content; a **provenance record** binds claims to exact artifacts and verification material. These are separate mechanisms.

## First walkthroughs to build

For embedding: create a synthetic reference → embed a test mark → validate behavior → transform or extract a fragment → attempt detection → inspect the result. Include unmarked, independently marked and transplanted-mark controls. The mark recipe and language must be selected through the research gate, not invented for a demo.

For extracted matching:

A maintainer has a synthetic `reference.py` containing an original scoring function. A synthetic `candidate.py` contains that function inside a much larger file, with formatting changed. A `control.py` independently solves the same task.

1. Extract the reference with a pinned profile and retain its exact bytes, digest, configuration and private catalogue.
2. Compare candidate and control using the same supported profile.
3. Show candidate spans with their source coordinates and evidence. Show the control outcome even when it exposes a false alarm.
4. Report directional fragment containment separately from whole-file similarity. A small fragment inside a large file should not disappear behind a whole-file denominator.
5. Let a reviewer inspect the source and origin records. Keep permission assessment separate.

These filenames describe a proposed example; these three files and the detector do not exist yet. See the [example matrix](implementation-patterns.md#example-matrix) for its acceptance tests.

### W-1 verification plan

- **Checked:** reference → embed → validate → transform or extract → detect → inspect, with unmarked, independently marked and transplanted controls.
- **By:** M2E.2–M2E.5 as one scripted run; the recipe comes from the M2E.1 freeze, not from the demo.
- **Pass/fail:** as UC-6, plus every step's command exits 0 in order. **Needs** a selected carrier; **Today:** none. **Unverifiable:** any recipe not selected.

### W-2 verification plan

- **Checked:** the five numbered steps, including control outcome shown even if a false alarm, directional containment against whole-file similarity, and separation of permission.
- **By:** M2.1 (offline run), M2.2/M2.3 (the three files become cases), M2.5, M2.6; M5.3 has a non-author reproduce it from a clean clone.
- **Pass/fail:** as UC-1, including the control rule: `control.py` must return the outcome code frozen for it, and a `match` there is shown as a false alarm. **Today:** none; the three files do not exist yet. **Unverifiable:** reviewer judgment in step 5 (a person inspects origin records), and the permission assessment.

## Outside the first release

Internet-wide scanning, automatic enforcement, proving model-training membership, automatic ownership attribution, and guaranteed survival under arbitrary rewrites are outside the initial scope. Traceweave is not a DRM system. Optional provenance adapters do not turn similarity into proof.

## Capability index and recount

The capabilities are UC-1…UC-6, the walkthroughs W-1 and W-2, and one row per `##` heading of [implementation patterns](implementation-patterns.md) other than "Example matrix" (H-1…H-5). The example-matrix rows are fixtures for UC-1…UC-6, covered by gate M0.3. A non-author recounts the list from the documents with these commands, then checks that every row has a plan and that no plan's pass or fail rests on a judgment word:

- `grep -cE '^\| UC-[0-9] — ' docs/use-cases.md` gives 5, `grep -c '^\*\*UC-6' docs/use-cases.md` gives 1, and the two walkthroughs ("For embedding:", "For extracted matching:") give 2: 8 in total.
- `grep -n '^## ' docs/implementation-patterns.md` lists 6 headings; excluding "Example matrix" leaves 5.

**Count: 13 capabilities.** `grep -cE '^\| (UC|W|H)-[0-9]+ [A-Z"]' docs/use-cases.md` counts the index rows below and gives 13. Input, output and limit are abbreviated from the two documents; each H row's plan sits at the end of its section in implementation patterns.

| Capability | Input | Observable output | Limit | Plan | Gate IDs |
| --- | --- | --- | --- | --- | --- |
| UC-1 Find an extracted function | Authorized reference snapshot, local candidate | Candidate source ranges, profile/config, digests, comparison evidence | Rewrites evade; common code matches; no result is not absence | [plan](#uc-1-verification-plan) | M1.1–M1.6, M2.1–M2.6, M3.4 |
| UC-2 Review license history | UC-1 evidence, region origins, dependency records, archived licence text | Reproducible review packet linking regions to history | No legal determination; later licence does not decide earlier expression | [plan](#uc-2-verification-plan) | M2.3, M2.7, M3.1 |
| UC-3 Preserve a private reference | Catalogue bytes/config, fresh commitment opening | Disclosed bytes open the recorded commitment | Not ownership or earlier existence; date not trusted; opening reveals all | [plan](#uc-3-verification-plan) | M4.2, M4.5, M4.6 |
| UC-4 Check a received evidence packet | Payload, subject digest, signer, time evidence, optional reference | Separate verdicts with reasons and localized evidence | Valid signature on false assertion; missing private material | [plan](#uc-4-verification-plan) | M2.1, M4.1, M4.3, M4.4, M4.5 |
| UC-5 Assess transformations | Recorded transformations, positives, unrelated and same-task controls | Held-out detection and false-alarm report with failures and costs | Only the tested profile, corpus and pipeline | [plan](#uc-5-verification-plan) | M2.3, M3.0–M3.6 |
| UC-6 Recognize distributed content | Original bytes, authorized to modify; profile; private mark record | Marked output, validation, localized detection evidence or insufficient evidence | No scheme or survival guarantee selected; not ownership | [plan](#uc-6-verification-plan) | M2E.0–M2E.7, SYN.1–SYN.5 |
| W-1 Embedding walkthrough | Synthetic reference, test mark, controls | Detection result per control | Recipe set by the research gate | [plan](#w-1-verification-plan) | M2E.1–M2E.5 |
| W-2 Extracted-matching walkthrough | `reference.py`, `candidate.py`, `control.py` | Spans, control outcome, containment vs similarity | Files do not exist yet; permission is separate | [plan](#w-2-verification-plan) | M2.1, M2.2, M2.3, M2.5, M2.6, M5.3 |
| H-1 "Embed and detect as an explicit pair" | Original bytes, mark, profile/config, secret | Marked bytes, private record; detection evidence | Transplantation survives crypto checks; algorithm undecided | [plan](implementation-patterns.md) | M2E.4, M2E.5, M2E.7 |
| H-2 "Keep deterministic extraction separate from comparison" | Bytes, profile, config bytes | Features, spans, diagnostics; explicit error | Pinned grammar only; no silent substitution | [plan](implementation-patterns.md) | M1.1–M1.6 |
| H-3 "Treat storage as a boundary" | Catalogue, config, artifact digests, local feature index | Bound, atomically written private files; candidates then alignment | Ranking is not evidence; real-filesystem behaviour beyond fixtures | [plan](implementation-patterns.md) | M1.3, M2.8, M2.9, M2E.4, M4.2 |
| H-4 "Preserve independent verification results" | Statement, candidate, policy | Per-field results (subject, signature, trust, time, comparison, rights) | Field names subject to TW-03 | [plan](implementation-patterns.md) | M1.3, M4.3, M4.4 |
| H-5 "Reproducible evaluation, then adapters" | Corpus with rights, grouped splits; stable commands, C2PA fixtures | Scoped benchmark report; wrapped diagnostics; interop fixtures | Scoped claims only; adapters wait for gates | [plan](implementation-patterns.md) | M3.1–M3.5, SK.1, SK.2, C2PA.1–C2PA.3 |
