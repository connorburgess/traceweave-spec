# Draft roadmap v2: gated milestones and an implementation track

Status: **draft for owner review, not adopted.** Revised after the [independent review](roadmap-v2-review.md). This file does not edit [ROADMAP.md](../../ROADMAP.md) or any normative file. It keeps M0–M5, adds a parallel implementation track and later profiles with their own gates, and gives every gate a checkable criterion and a status. No dates or detection guarantees are promised. Embedded marking stays a first-class track alongside extracted fingerprints. Companion: [implementation repository plan](implementation-repo-plan.md).

**Gate types.**
- **E (engineering)**: closes only when **met**.
- **R (research question)**: closes when **met** or **negative-result**. A negative result is a valid answer to the question.
- **O (owner decision)**: closes when a decision record exists.

**Statuses.** met, open, negative-result (R gates only).

**Uncommitted evidence.** A gate whose evidence exists only in the uncommitted working tree stays **open**, with the note "evidence exists, uncommitted". Such evidence cannot be rechecked from a clean clone; the gate changes status when the evidence is committed.

## 1. Assessment of the "always completing" problem

The owner's concern was that Traceweave keeps completing while the roadmap barely moves. The coordinator offered four diagnoses. I checked each against the repository:

1. **Phase-scoped supervision closes quickly. Supported by the files, though I did not inspect the loop configs.** [work-queue.md](../work-queue.md) marks "Reviewed phase — complete" and "Public census — complete", and its operating rules say to "close supervision only at its declared phase boundary". Three checkpoints each end by saying they complete a bounded phase and not the roadmap: [experiment](../experiment-checkpoint.md) (2026-11-18), [fragment/policy](../fragment-policy-checkpoint.md) (11-21) and [census](../public-census-checkpoint.md) (11-21). The roadmap still says only M0 is complete. The loop settings belong to a private application and were not inspected.
2. **Exit gates are qualitative and untracked. Mostly confirmed, with one refinement.** [ROADMAP.md](../../ROADMAP.md) M2 and M2E rely on "localized" and "reported honestly". M1's "byte-for-byte" is checkable. Setting no threshold in M3 is correct, because the false-alarm budget is an open owner choice. The larger gap is that no gate has an ID, a named artifact or a status, and TW-01…TW-08 have no status column.
3. **No implementation track. Confirmed.** All executable work is research harnesses under `research/experiments/`. Nothing extracts a fingerprint. [conformance.md](../../spec/conformance.md) says there is "no complete DSSE signer/verifier, token extractor, resolver, or benchmark corpus". TW-04 plans the reference "using the existing Python tooling". The fingerprint baseline that the work queue proposed has not started; work went to evidence lanes [06](../lanes/06-evidence-review.md), [07](../lanes/07-evidence-review.md) and [08](../lanes/08-evidence-review.md) instead.
4. **Later items are ungated. Confirmed.** The "Later, with separate gates" list in ROADMAP.md never defines those gates.

Is the roadmap big enough? M0–M5 is a substantial scope: a frozen profile, a benchmark, cross-language verification and a release. What was missing is a way to see how much of it remains. **Against the 47 counted core gates in §3: 3 are met (all in M0), none is negative-result, and 44 are open.** Two of the open gates (M4.1, M4.2) already have evidence that is not yet committed. The rejected synthetic carriers' rows are research records and are not counted. All implementation-repository and later gates are open.

## 2. Supervision rule (proposal)

1. **Declare against gate IDs.** A supervision loop names the gate IDs it is working on. It may be marked complete only when every named gate is closed according to its type: E met, R met or negative-result, O decision recorded. Each gate must cite committed evidence.
2. **Checkpoints are not completion.** Phase checkpoints, evidence reviews and "bounded phase complete" notes are progress records. A loop that changes no gate status ends as **paused** or **blocked**, and names the gate.
3. **Status and evidence change together.** A status changes in the same change as its evidence. Someone who did not do the work must be able to recheck it: rerun the command, recount, or open the review.
4. **Blocked on the owner.** The loop asks once, then moves to another open gate. It does not invent a phase to have something to close.
5. **Work queue.** The work queue lists open gate IDs, not free-standing phases.

## 3. Gate table: M0–M5

Owner column: **S** = spec repository; **I** = implementation repository (proposed). `validate` means `.venv/bin/python tools/validate.py && .venv/bin/python -m unittest discover -s tests`.

### M0 — Explain and bound

| ID | Type | Verifiable criterion | Status / evidence | Owner |
| --- | --- | --- | --- | --- |
| M0.1 | E | The capability list is exactly: UC-1…UC-6 and walkthroughs W-1, W-2 from `docs/use-cases.md`, plus one row per `##` heading of `docs/implementation-patterns.md` except "Example matrix" (13 rows today). A non-author recounts it from those documents. Each row needs a verification plan, merged into `docs/`, whose pass/fail is a command exit code or a count, with no judgment words. Met when every recounted row has such a plan. Stays open until the merge; the working draft is [use-cases-verification-plans.md](use-cases-verification-plans.md) | open: not merged into `docs/` | S |
| M0.2 | E | Five discovery lanes are reviewed against both provider reports | met: [discovery-checkpoint.md](../discovery-checkpoint.md) | S |
| M0.3 | E | Example matrix: each row names its use case and expected assertion | met: [example matrix](../../docs/implementation-patterns.md#example-matrix) | S |
| M0.4 | E | `validate` exits 0 with 6 tests | met: [validate.py](../../tools/validate.py), rerun 2026-11-22 | S |

### M1 — Freeze one code experiment (token-fingerprint profile, Go and Rust)

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M1.1 | E | A profile document answers every item in "Before registering a profile" in [profiles/code.md](../../profiles/code.md), with no TBDs. Token classes are defined independently of any lexer's token kinds: raw strings, nested comments, shebang, BOM, CRLF | open | S |
| M1.2 | E | At least these 7 vector classes per language: empty, below `k+w-1`, Unicode, malformed, repeated, equal-minimum ties, CRLF/BOM. Each vector carries `derivation: hand` metadata and its expected output. Each positive vector has a paired rejection vector. `validate` checks them | open | S |
| M1.3 | E | Catalogue and report schemas bind profile ID, config digest and artifact digests. Each has at least 1 valid example and at least 1 rejection fixture per required field. `validate` passes | open (TW-03) | S |
| M1.4 | E | Each of two implementations, using independent lexers, produces output equal to the **committed expected bytes** for every M1.2 vector. Ordering is enforced by a script: the implementation commit that first adds an extractor already pins a spec commit containing those vectors | open | I |
| M1.5 | E | A requirement map maps each MUST in the profile to a vector or test ID that **fails when the MUST is violated**, with at least 1 negative fixture per testable MUST. MUSTs that cannot be tested are listed, and someone else spot-checks them on a stated sample of at least 10 (all, if fewer). Unmapped: 0 | open | S |
| M1.6 | E | Unknown profile IDs and every M1.2 negative return the specified error code in both implementations | open | I |

### M2 — Local comparison

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M2.1 | E | The walkthrough (extract → catalogue → compare → report) passes under `scripts/offline`. The wrapper first proves network denial with a probe that must fail | open | I |
| M2.2 | E | The frozen manifest has at least 1 positive case for each UC-1 example-matrix row: exact; formatted fragment in a large host; rename/shadowing; Unicode/repeated minima/tiny file. Passes only if every case's spans equal the expected UTF-8 byte spans (N/N) | open | I |
| M2.3 | E | Control classes, each with at least 1 case: independent same-task, common boilerplate/vendor, unrelated, malformed/unsupported. Passes when every class appears in the report with its candidate count and denominator. No threshold is set before M3 | open | I |
| M2.4 | E | Two runs produce an identical **canonical report body**, which excludes the provenance block. The comparison-config digest is in the body inputs, as the draft contract places it. The provenance block is checked separately: implementation commit and spec pin present and correct | open | I |
| M2.5 | E | Fragment containment and whole-file similarity are separate fields, shown in a large-host fixture where they diverge | open | S+I |
| M2.6 | E | Hand-derived matching vectors in `test-vectors/` (`derivation: hand`). They cover at least the M2.2 positive classes and the M2.3 control classes, give expected spans, containment and similarity, and `validate` checks them. These are the vectors I2 uses to complete conformance level 4 | open | S |
| M2.7 | E | UC-2 origin and dependency links live in a **separate review-packet record**, never in the comparison report. The record references the report's `bodySha256` and a region key: reference id, candidate id, mode, first seed. A spec schema with at least 1 valid example and 1 rejection fixture per required field, checked by `validate`. A rejection fixture whose region key is absent from the referenced body fails the semantic check. At least 3 valid fixtures: own-origin region; vendored/dependency region with an archived licence-text digest; historical permitted copy. The record has no rights-verdict field | open | S+I (I2) |
| M2.8 | E | Storage boundary (P-3). With no path option, a fixture run inside a temporary git checkout writes 0 files under it. The catalogue written to the documented private default has the expected catalogue SHA-256, so writing nothing cannot pass. Fault injection, 3/3, each leaving the previous valid catalogue byte-identical and no partial file at the final path: (1) an injected error before the temporary file opens; (2) SIGKILL after a partial write of the temporary file; (3) an injected rename failure. Keys are added to this gate only when M4 produces any | open | I (I2) |
| M2.9 | E | Index ranking is not evidence (P-5). Candidate generation (`exhaustive`, or the SHA-256 of the selected candidate-id set) is recorded in a **separate record keyed by the report's `bodySha256`**, never in the report body. In at least 2 fixtures, a fixed candidate catalogue gives a byte-identical canonical body whatever retrieval path (exhaustive or one index) or order produced it. A different candidate set is expected to change the candidate catalogue digest, the candidate count and the pairs. A rejection fixture adding a rank, score or index field fails the report schema | open | S+I (I2) |
| M2.10 | E | Common-code suppression uses an explicit boilerplate catalogue bound by its SHA-256 in the comparison config (draft contract OD-C5 option b; decision pending). Vectors, at least 1 each: suppression driven only by the boilerplate catalogue; an invariance case whose starting reference set **already holds at least 2 files sharing the idiom**, where adding 1 more reference file (sharing the idiom, or unrelated) leaves every pair's outcome unchanged, so document-frequency suppression fails it; a config whose boilerplate digest mismatches is rejected with its code. Both implementations match | open | S+I (I2) |
| M2.11 | E | Minimum evidence counts **distinct** non-common hashes, not seeds (decision pending in the contract). At least 1 vector where one hash repeats in at least 2 seeds: below-minimum-evidence in both modes. At least 1 vector at exactly the minimum: match. Both implementations match | open | S+I (I2) |

### M2E — Embed and detect (per candidate carrier)

**Research record: candidate SYN** (existing synthetic Go/Rust carriers). Not counted in progress.

| Record | Result | Status / evidence |
| --- | --- | --- |
| SYN.1 | Deliberate insertion recovers after the formatter: **55/55** nonzero insertions per language. The 62/62 total includes 7 already-zero states, which show decoding only | measured; evidence exists, uncommitted: [experiment-checkpoint.md](../experiment-checkpoint.md) |
| SYN.2 | Functionality checks on marked outputs only: Go 124/124 (clean + formatted); Rust 124/124 per build profile, 248 across two. Attack outputs excluded | measured; evidence exists, uncommitted: [Go](../lanes/go-carrier-results.md), [Rust](../lanes/rust-carrier-results.md) |
| SYN.3 | Nonzero states survive cheap canonicalization | negative-result measured; evidence exists, uncommitted: 55/55 reset per language |
| SYN.4 | Signal transplant is not decoded as same-context evidence | negative-result measured; evidence exists, uncommitted: transfers decode, [fragment-policy-checkpoint.md](../fragment-policy-checkpoint.md) |
| SYN.5 | Safe eligible sites in the 4-repository census, narrow patterns | inconclusive: no eligible site established; 5 Go singletons unassessed, [census](../public-census-checkpoint.md) |

**Counted gates for the next candidate C:**

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M2E.0 | O | A decision record either selects candidate C (when C meets M2E.1) or omits embedding from the next release. M5.4 cannot state omission without it | open | S |
| M2E.1 | R | Frozen and committed before measurement: (a) eligible subset; (b) declared transformations, including full cheap normalization; (c) minimum net authenticated bits per unit, derived from the UC-6 payload and **approved by the owner**; (d) behavior checks; (e) the survival rate required for each declared transformation. Measured on a sample from a new owner-approved census protocol, never tuning data. **Met only if the owner-approved minimum (c) holds on that sample; otherwise negative-result** | open ([lane 06](../lanes/06-evidence-review.md): no ready candidate) | S |
| M2E.2 | E | Reproducible insertion: seeds are recorded and a rerun reproduces every marked-output digest. Only deliberate insertions are counted | open | I |
| M2E.3 | E | Functionality/quality checks on **marked outputs only**, k/k. Attack outputs are reported separately | open | I |
| M2E.4 | E | Private mark-record schema with example and rejection fixtures. Fields: original and marked digests, profile/config digest, seed/key reference (never key bytes). Stored outside the checkout by default. `validate` checks it | open | S |
| M2E.5 | E | Controls measured, each with at least 1 case and a denominator: unmarked, wrong mark/key, removal by full cheap normalization, transplant, partial fragment | open | I |
| M2E.6 | R | Each declared M2E.1(b) transformation reaches the survival rate frozen in M2E.1(e), measured with denominators. Met only if every rate holds; otherwise negative-result | open | I |
| M2E.7 | E | Mark-only, fingerprint-only and combined detection compared on the same held-out cases at the M3.0 budget | open (needs M3) | I |

### M3 — Measure usefulness

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M3.0 | O | Operational false-alarm budget and its unit (per repository search) recorded | open | S |
| M3.1 | E | Corpus manifest gives, per entry: pinned revision, licence, redistribution permission and split group. Excludes the census repositories. A script verifies every field | open | I |
| M3.2 | E | Split file digest committed; groups disjoint (script check) | open | I |
| M3.3 | E | The commits freezing thresholds/config and splits are **git ancestors** of the first held-out result commit. Ancestry is checked, not timestamps | open | I |
| M3.4 | E | Held-out report: recall by transformation × fragment-size bucket; false alarms per repository search; abstentions; candidate volume; runtime; peak memory. Every figure has a denominator | open | I |
| M3.5 | E | A second person reruns M3.4 and gets identical counts. Runtime and memory may differ within the tolerance stated in the report | open | I |
| M3.6 | R | Computed usefulness verdict, not chosen. Met when measured false alarms per repository search, at the frozen M3.3 configuration on held-out data, are at or below the budget frozen at M3.0; above it, recorded as negative-result (the M3.4 report remains valid evidence). No recall floor is set; recall is reported without a pass line | open | S |

### M4 — Verify evidence

| ID | Type | Verifiable criterion | Status / evidence | Owner |
| --- | --- | --- | --- | --- |
| M4.1 | R | Pinned Go/Rust DSSE libraries interoperate on the existing statement: 4 producer/consumer pairs, no network | open: evidence exists, uncommitted (66 outcomes, [signing-interop-results.md](../lanes/signing-interop-results.md)) | S |
| M4.2 | R | Independent Go/Rust commitment code reproduces `test-vectors/commitment.json` and rejects changed openings | open: evidence exists, uncommitted ([signing-policy-results.md](../lanes/signing-policy-results.md)) | S |
| M4.3 | E | Negative cryptographic vectors (tampered payload, type or signature; untrusted key; malformed or duplicate-key payload; subject mismatch), each with a distinct reason code. `validate` checks them | open | S |
| M4.4 | E | Two implementations, each with its own strict parser and key-hint policy, produce identical bytes and reason codes on every M4.3 vector | open | I |
| M4.5 | E | in-toto adapter accept/reject fixtures, checked by `validate`. A trust-policy document. A recorded decision on the optional timestamp adapter | open | S |
| M4.6 | E | Commitment/disclosure design reviewed by a named non-author. Report in `docs/reviews/`; every finding has a disposition | open | S |

### M5 — Candidate release

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M5.1 | E | M1.5 rules applied to every MUST in `spec/` and `profiles/`; unmapped 0 | open | S |
| M5.2 | E | A script extracts every sentence in the whole README, minus a script-recognised exclusion list (headings, link-only lines, code blocks). Each claim sentence maps to a fixture, benchmark row or review. Unmapped 0 (TW-07). A non-author checks the map and the exclusions | open | S |
| M5.3 | E | A non-author reproduces the demo offline after dependency fetch: clean clone → pinned implementation | open | S+I |
| M5.4 | E | Release notes list every unresolved limit and state (a) whether embedding is included, citing M2E.0 if omitted, and (b) whether signing is included. Claiming cryptographic verification requires all M4 E gates met; otherwise the release is labelled unsigned detector-only | open | S |
| M5.5 | E | Versioned spec, migration notes and a conformance matrix (feature × level × implementation) | open | S |

## 4. Enlarged sequence (all **proposals awaiting the owner**)

```
M0 ─► M1 ─► M2 ──┬─► M3 ─► M5 ─► EXT ─► RC (1.0 candidate)
      │    M2E ──┘          ▲ M4 required only if the release claims signatures
      └─► M4 ─ ─ ─ ─ ─ ─ ─ ─┘
I0 ► I1 ► I2 ► I3;  I4 after I0;  I5a after I2 and M2E.1 met;  I5b after I3
After M1: TS   After I2: SK   After M4: C2PA
After M3.4 (or a recorded owner override): IMG, BIN, RES, STRUCT, KEYED
```

Media and resolver lanes wait for M3.4. Starting them earlier repeats the drift diagnosed in §1.3, and [lane 08](../lanes/08-evidence-review.md) names deferral as the strongest alternative. The implementation-track gate mapping is in [the plan](implementation-repo-plan.md#milestones).

| ID | Type | Verifiable criterion | Owner |
| --- | --- | --- | --- |
| **TS — second code profile (TypeScript/JavaScript)** | | | |
| TS.1 | E | Profile covers the M1.1 list plus ASI, regex vs division, template literals, JSX/TSX, and `.d.ts`/generated/minified exclusions | S |
| TS.2 | E | Hand-derived vectors cover the M1.2 classes plus the TS.1 classes | S |
| TS.3 | E | Two implementations without a shared lexer match the TS.2 expected bytes | I |
| TS.4 | E | Own M3 split, reported separately and not pooled | I |
| **IMG — first non-code profile: images** ([lane 08](../lanes/08-evidence-review.md)) | | | |
| IMG.0 | O | Owner approves UC-7 ("a creator marks images they publish and later checks a candidate"), written like UC-6. **This is a prerequisite of IMG.1–5**, and approval is also the override if IMG starts before M3.4 | S |
| IMG.1 | E | Pin record: TrustMark code commit; weight SHA-256; code, weight and dependency licences; licensed non-private image set | I |
| IMG.2 | E | Embed and detect pass under `scripts/offline` after provisioning | I |
| IMG.3 | E | Frozen and committed before running: transformation list (JPEG, resize, crop, ReMark), PSNR floor, threshold | I |
| IMG.4 | R | Whole-message success per transformation; unmarked and wrong-key false detections; transplant result. Each has a denominator | I |
| IMG.5 | E | Results fit the lane-08 container fields, or a schema change goes through CONTRIBUTING | S |
| **BIN — binary/compiled artifacts** | | | |
| BIN.1 | R | Primary-source review of source-to-binary mark survival and binary similarity, in the lanes 06–08 format | S |
| BIN.2 | O | Decision record citing BIN.1: a binary profile with its own gates, or out of scope | S |
| **RES — resolver threat model** | | | |
| RES.1 | E | Threat model: query leakage, enumeration, catalogue inference, membership disclosure, abuse. Public registration stays optional | S |
| RES.2 | R | The adversary query model and the leakage metric are named and committed before running; then measured on synthetic catalogues with denominators | S/I |
| RES.3 | E | Independent review filed, with every finding dispositioned | S |
| **C2PA — mapping with interop fixtures** | | | |
| C2PA.1 | E | Mapping pinned to one C2PA version; each field mapped, unmapped or conflicting | S |
| C2PA.2 | E | Fixtures from a pinned open-source C2PA tool round-trip through a Traceweave adapter in both directions | I |
| C2PA.3 | E | README makes no compatibility claim until C2PA.2 passes | S |
| **SK — agent skill** | | | |
| SK.1 | E | Wraps only stable I2 commands; diagnostics pass through unchanged | I |
| SK.2 | E | Canary strings seeded into catalogues, paths and keys appear 0 times in model-visible transcripts across all fixture runs | I |
| **Later matching methods** (ROADMAP "Later") | | | |
| STRUCT.1 | R | Structural/semantic matching compared with the token baseline on the M3 corpus and budget | I |
| KEYED.1 | R | Keyed feature selection evaluated separately from embedding on the M3 corpus and budget | I |
| **EXT and RC** | | | |
| EXT.1 | E | Named non-contributors review the spec, M3 methodology and M4 crypto (may reuse M4.6 if that reviewer qualifies). Reports filed; every finding dispositioned | S |
| RC.1 | E | Every E gate in M1–M5 met; every R gate met or negative-result; every O gate recorded; EXT.1 met. If M2E.0 records that embedding is omitted, M2E.2–M2E.5 and M2E.7 are exempt | S |
| RC.2 | E | Two implementations pass conformance levels 1–4 for every profile marked stable. Whether they need different implementers is an owner decision ([plan](implementation-repo-plan.md#needs-the-owner)) | S+I |
| RC.3 | E | Scope statement covering media, embedding (M2E.0) and signing (M5.4) | S |

## 5. Order of work (proposal)

1. **Make the existing evidence rechecked from a clean clone.** Commit the uncommitted evidence listed above, together with a toolchain record, and explain or revert the `go 1.23 → 1.27` change in `research/experiments/go-carrier/go.mod`. This is outside this lane: no commits.
2. **Adopt §2 and these gates, and update ROADMAP.md (owner decision).** Add a status column to TW-01…TW-08, mapped as:
   - TW-01, TW-02 → M1.1, M1.2
   - TW-03 → M1.3
   - TW-05 → M3.1–M3.3
   - TW-06 → M4.3–M4.5 and I4
   - TW-07 → M5.2
   - TW-08 → M2E.0–M2E.7

   **TW-04 is amended:** the reference moves from spec-repository Python to the implementation repository (I2, M2.1–M2.11).
3. **Run spec and implementation work in parallel.** M1.1–M1.3 in the spec repository; I0–I1 in the implementation repository.
4. **Keep embedding active.** Pursue M2E.1 with a frozen candidate. Do not broaden the SYN carriers.
5. **Later lanes.** IMG, BIN, RES, STRUCT and KEYED start after M3.4, or earlier on a recorded owner override.

Open questions for the owner: the M3.0 budget, the M2E.1(c) payload minimum, the IMG.0 use case, the EXT reviewers, and whether implementers must be independent.

## Review responses

- **M2 (commit evidence, go.mod).** Not fixable in these two files under the no-commit limit. Gates with uncommitted evidence stay open (confirmation pass N3), and the commit is step 1 of §5.
- **B5 (pinned commit must be pushed).** Accepted as a rule in the plan. It cannot be satisfied until the owner pushes a spec commit.
- **Low (BIN.2 padding).** Accepted by dropping the measurement on rejected carriers rather than moving it. A binary measurement belongs to a future BIN profile's own gates.
- No other finding was rejected.
