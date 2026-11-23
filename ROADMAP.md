# Traceweave roadmap

Status: active research roadmap, version 2, updated 2026-11-22. The 0.1.0-draft.1 scaffold validates record shapes and synthetic vectors. Separate experimental harnesses recover synthetic carrier states and cross-verify Go/Rust signatures; production reuse detection remains unimplemented. No dates and no detection guarantees are promised. See the [measured checkpoint](research/experiment-checkpoint.md), the [active work queue](research/work-queue.md) and the [implementation repository plan](docs/implementation-repo-plan.md).

Start with [use cases](docs/use-cases.md), then [implementation patterns](docs/implementation-patterns.md) and the [source register](docs/sources.md). These planning documents do not change normative wire formats.

**What the project is.** Traceweave is an open, non-commercial, independent specification, not a legal entity. Since 2026-11-23 the project has owned the domain `traceweave.org`, registered that day. It is intended for the documentation site and for stable specification and schema identifiers, and later for the browser tool (WEB). The [independent review](research/reviews/roadmap-v2-review.md) of this version is kept with the other reviews.

## Pilot languages

Initial experimentation uses synthetic Go and Rust source code, with planned expansion to multiple media types. TypeScript/JavaScript, still images and text are owner-approved profile targets (2026-11-22; scope under [later profiles](#later-profiles-and-sequence)). Private applications are outside the current experimental scope. Shared evidence formats stay language-independent; transformations, safety conditions and build-pipeline tests are profile-specific. Python research tooling does not select Python as the marked language. See the [feasibility investigation](research/02-carrier-feasibility.md).

## Core tracks

Embedded marking and detection are a first-class research track alongside extracted fingerprint matching. Provenance verification supports both. A baseline matcher is useful for comparison, but does not satisfy the embedding use case. No marking method is standardized yet.

**Finding (2026-11-23, image marks).** On the `e-img-m-2` evidence (synthetic images, [results recheck](research/reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2)), an image mark can serve as a finding aid, but not as evidence of origin. The marks transfer between images without the key, and every copy was accepted. Evidence of origin must come from a signed, timestamped registration record (M4, and the C2PA mapping). The embedded-code results (the SYN records) remain negative. So does the embedded-text evidence (lane 09); TXT.8 stays formally open until a non-author confirms that reading.

## How progress is counted

Every milestone is split into gates. A gate has an ID, a verifiable criterion, a type, a status and an owner. Embedded marking stays a first-class track alongside extracted fingerprints.

**Gate types.**
- **E (engineering)**: closes only when **met**.
- **R (research question)**: closes when **met** or **negative-result**. A negative result is a valid answer to the question.
- **O (owner decision)**: closes when a decision record exists.

**Statuses.** met, open, negative-result (R gates only).

**Committed evidence.** A gate is **met** only when its evidence is committed, so someone who did not do the work can recheck it from a clean clone. A status changes in the same change as its evidence, and the change cites the commit.

## Supervision rule

1. **Declare against gate IDs.** A supervision loop names the gate IDs it is working on. It may be marked complete only when every named gate is closed according to its type: E met, R met or negative-result, O decision recorded. Each gate must cite committed evidence.
2. **Checkpoints are not completion.** Phase checkpoints, evidence reviews and "bounded phase complete" notes are progress records. A loop that changes no gate status ends as **paused** or **blocked**, and names the gate.
3. **Status and evidence change together.** A status changes in the same change as its evidence. Someone who did not do the work must be able to recheck it: rerun the command, recount, or open the review.
4. **Blocked on the owner.** The loop asks once, then moves to another open gate. It does not invent a phase to have something to close.
5. **Work queue.** The [work queue](research/work-queue.md) lists open gate IDs, not free-standing phases.

## Delivery sequence

| Milestone | What becomes possible | Deliverables | Gates |
| --- | --- | --- | --- |
| M0 — Explain and bound | A maintainer understands the use cases and remaining uncertainty | Use cases, source register, patterns, example matrix, verification plans | M0.1–M0.4 |
| M1 — Freeze one code experiment | Two runs extract identical features from identical inputs | One language/profile proposal; exact configuration bytes; token serialization; spans; catalogue and report schemas; positive and negative vectors | M1.1–M1.6 |
| M2 — Local comparison | A maintainer finds candidate fragments without uploading source | Reference extractor, local catalogue, matcher, localized reports, synthetic walkthrough | M2.1–M2.11 |
| M2E — Embed and detect | A creator can test recognition of deliberately marked content | One experimental embedding/detection profile for a selected candidate; private mark record; quality checks; transformation and attack fixtures | M2E.0–M2E.7 |
| M3 — Measure usefulness | A reviewer can assess which transformations are detected and at what cost | Licensed corpus manifest; grouped data splits; frozen thresholds; reproducible benchmark and failure report | M3.0–M3.6 |
| M4 — Verify evidence | A recipient independently checks a signed evidence record under their own trust policy | Library-based DSSE signing/verification; in-toto adapter; trust policy; optional timestamp adapter; negative cryptographic vectors | M4.1–M4.6 |
| M5 — Candidate release | Another implementer can build against a coherent version | Versioned spec, schemas, fixtures, conformance matrix, migration notes, reproducible demo | M5.1–M5.5 |

Order: M0 → M1 → parallel M2 and M2E → M3 → M5. A release that omits embedding must say so, and omission needs an owner decision (M2E.0). M4 can follow M1 independently, but is required before a release claims cryptographic verification. A detector-only experimental release can remain explicitly unsigned (M5.4).

## Gate tables: M0–M5

Owner column: **S** = spec repository; **I** = implementation repository (`traceweave`, see the [repository plan](docs/implementation-repo-plan.md)). `validate` means `.venv/bin/python tools/validate.py && .venv/bin/python -m unittest discover -s tests`.

### M0 — Explain and bound

| ID | Type | Verifiable criterion | Status / evidence | Owner |
| --- | --- | --- | --- | --- |
| M0.1 | E | The capability list is exactly: UC-1…UC-6 and walkthroughs W-1, W-2 from `docs/use-cases.md`, plus one row per `##` heading of `docs/implementation-patterns.md` except "Example matrix" (13 rows today). A non-author recounts it from those documents. Each row needs a verification plan, merged into `docs/`, whose pass/fail is a command exit code or a count, with no judgment words. Met when every recounted row has such a plan | met: verification plans merged into `docs/` in `b13cb68` and `215145b`; the non-author recounts in the [adoption check](research/reviews/roadmap-v2-review.md#adoption-check) found 8 of 13 decidable, then 13/13 after the rewrite, recorded in `3a640b3` | S |
| M0.2 | E | Five discovery lanes are reviewed against both provider reports | met: [discovery-checkpoint.md](research/discovery-checkpoint.md) | S |
| M0.3 | E | Example matrix: each row names its use case and expected assertion | met: [example matrix](docs/implementation-patterns.md#example-matrix) | S |
| M0.4 | E | `validate` exits 0 with 6 tests | met: [validate.py](tools/validate.py), rerun 2026-11-22 | S |

### M1 — Freeze one code experiment (token-fingerprint profile, Go and Rust)

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M1.1 | E | A profile document answers every item in "Before registering a profile" in [profiles/code.md](profiles/code.md), with no TBDs. Token classes are defined independently of any lexer's token kinds: raw strings, nested comments, shebang, BOM, CRLF | open. (a) The [extraction contract](spec/extraction.md)'s decided items are confirmed and its promotion to `profiles/` is approved; promotion is in progress. (b) No item map against the [profiles/code.md](profiles/code.md) list exists yet (my reading; neither review names it) | S |
| M1.2 | E | At least these 7 vector classes per language: empty, below `k+w-1`, Unicode, malformed, repeated, equal-minimum ties, CRLF/BOM. Each vector carries `derivation: hand` metadata and its expected output. Each positive vector has a paired rejection vector. `validate` checks them | open. (a) Promotion from `test-vectors/extraction/` to `test-vectors/` is approved and in progress; `validate` checks the vectors only after it. Both implementations reproduce them ([I1 review](research/reviews/implementation-merge-i1-review.md) `9c03c95`) | S |
| M1.3 | E | Catalogue and report schemas bind profile ID, config digest and artifact digests. Each has at least 1 valid example and at least 1 rejection fixture per required field. `validate` passes | open. (a) Promotion of the draft catalogue and report schemas to `schemas/` is approved and in progress | S |
| M1.4 | E | Each of two implementations, using independent lexers, produces output equal to the **committed expected bytes** for every M1.2 vector. Ordering is enforced by `check-vector-precedence`. The implementation commit that first adds each extractor must carry a `spec.lock` whose recorded SHA-256 digests for every vendored vector file equal the digests of those files in the spec commit later pinned. A provisional pin satisfies the rule on that condition; the script verifies the digest equality. Any vector whose bytes changed after the extractor commit needs the recorded decision and re-run already required for pin updates ([plan](docs/implementation-repo-plan.md#how-it-references-the-spec)). Completion needs a pushed spec commit, which is owner-blocked | open. (a) The strict pin. `roadmap-v2` is now public at `dec460e` (2026-11-23), but the implementation repository must first re-vendor from the promoted paths at a pushed public commit and pass its strict pin check. Until then the pin is at local `15a4b2d` with `repository: null`. Satisfied: both implementations reproduce the vendored vectors; `scripts/check-vector-precedence` now exists; the 3 files changed at `2fa2b58` are additions only, with a recorded decision ([I1 review](research/reviews/implementation-merge-i1-review.md) `9c03c95`; [I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §4) | I |
| M1.5 | E | A requirement map maps each MUST in the profile to a vector or test ID that **fails when the MUST is violated**, with at least 1 negative fixture per testable MUST. MUSTs that cannot be tested are listed, and someone else spot-checks them on a stated sample of at least 10 (all, if fewer). Unmapped: 0 | open. (b) A requirement map of each MUST to a failing vector or test has not been written. `scripts/vector-coverage` covers files and records, not MUSTs | S |
| M1.6 | E | Unknown profile IDs and every M1.2 negative return the specified error code in both implementations | open. (a) "Every M1.2 negative" waits on M1.2's promotion (approved, in progress). Satisfied today: every draft negative and all 28 config negatives return their codes in both implementations ([I1 review](research/reviews/implementation-merge-i1-review.md) `9c03c95` §5) | I |

### M2 — Local comparison

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M2.1 | E | The walkthrough (extract → catalogue → compare → report) passes under `scripts/offline`. The wrapper first proves network denial with a probe that must fail | open. (b) No `scripts/offline` wrapper or network-denial probe exists in the implementation repository; the walkthrough commands themselves work ([I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §7) | I |
| M2.2 | E | The frozen manifest has at least 1 positive case for each UC-1 example-matrix row: exact; formatted fragment in a large host; rename/shadowing; Unicode/repeated minima/tiny file. Passes only if every case's spans equal the expected UTF-8 byte spans (N/N) | open. (b) There is no frozen fixture manifest. (a) Pin-dependent: the branch is public at `dec460e`, but the implementation repository must first re-vendor from the promoted paths at a pushed public commit and pass its strict pin check. Satisfied: one case per class, with spans N/N in both lanes ([I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §7) | I |
| M2.3 | E | Control classes, each with at least 1 case: independent same-task, common boilerplate/vendor, unrelated, malformed/unsupported. Passes when every class appears in the report with its candidate count and denominator. No threshold is set before M3 | open. (b) The vendor control class is absent (contract OD-C19 open). Same-task, boilerplate, unrelated and malformed controls are present, with counts and denominators ([I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §7) | I |
| M2.4 | E | Two runs produce an identical **canonical report body**, which excludes the provenance block. The comparison-config digest is in the body inputs, as the [draft contract](spec/catalogue-report.md) places it. The provenance block is checked separately: implementation commit and spec pin present and correct | open. Satisfied in substance: two runs give identical bodies; the config digest is in `inputs`; provenance names `82b02ab` and `15a4b2d` ([I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §7). (b) The rebuild-from-clean-clone check required by B10 ([contract](spec/catalogue-report.md) §6.6 and §6.8) is not yet run. (a) Pin correctness: the branch is public at `dec460e`, but the implementation repository must first re-vendor from the promoted paths at a pushed public commit and pass its strict pin check | I |
| M2.5 | E | Fragment containment and whole-file similarity are separate fields, shown in a large-host fixture where they diverge | **met**: `go-function-in-host` gives reference-in-candidate 14/14 against Jaccard 14/39 in both implementations (implementation `82b02ab`; [I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §7). The fixture is a draft vector; its promotion is tracked under M2.6 | S+I |
| M2.6 | E | Hand-derived matching vectors in `test-vectors/` (`derivation: hand`). They cover at least the M2.2 positive classes and the M2.3 control classes, give expected spans, containment and similarity, and `validate` checks them. These are the vectors I2 uses to complete conformance level 4 | open. (a) Promotion from `test-vectors/matching/` to `test-vectors/` is approved and in progress. (b) The vectors do not yet cover the vendor control class (M2.3) | S |
| M2.7 | E | UC-2 origin and dependency links live in a **separate review-packet record**, never in the comparison report. The record references the report's `bodySha256` and a region key: reference id, candidate id, mode, first seed. A spec schema with at least 1 valid example and 1 rejection fixture per required field, checked by `validate`. A rejection fixture whose region key is absent from the referenced body fails the semantic check. At least 3 valid fixtures: own-origin region; vendored/dependency region with an archived licence-text digest; historical permitted copy. The record has no rights-verdict field | open. (b) Review packets are not started | S+I (I2) |
| M2.8 | E | Storage boundary (P-3). With no path option, a fixture run inside a temporary git checkout writes 0 files under it. The catalogue written to the documented private default has the expected catalogue SHA-256, so writing nothing cannot pass. Fault injection, 3/3, each leaving the previous valid catalogue byte-identical and no partial file at the final path: (1) an injected error before the temporary file opens; (2) SIGKILL after a partial write of the temporary file; (3) an injected rename failure. Keys are added to this gate only when M4 produces any | **met** for both CLIs at implementation `82b02ab` ([I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §5): 0 files under the checkout; the same catalogue SHA-256 at each default private location; faults 3/3 per lane | I (I2) |
| M2.9 | E | Index ranking is not evidence (P-5). Candidate generation (`exhaustive`, or the SHA-256 of the selected candidate-id set) is recorded in a **separate record keyed by the report's `bodySha256`**, never in the report body. In at least 2 fixtures, a fixed candidate catalogue gives a byte-identical canonical body whatever retrieval path (exhaustive or one index) or order produced it. A different candidate set is expected to change the candidate catalogue digest, the candidate count and the pairs. A rejection fixture adding a rank, score or index field fails the report schema | open. (b) No candidate-generation record keyed by `bodySha256` exists, and no index, so the two-retrieval-path fixtures cannot run. Satisfied: both validators reject rank and score fields ([I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §7) | S+I (I2) |
| M2.10 | E | Common-code suppression uses an explicit boilerplate catalogue bound by its SHA-256 in the comparison config ([draft contract](spec/catalogue-report.md) OD-C5 option b, confirmed; see [owner decisions of 2026-11-23](#owner-decisions-2026-11-23)). Vectors, at least 1 each: suppression driven only by the boilerplate catalogue; an invariance case whose starting reference set **already holds at least 2 files sharing the idiom**, where adding 1 more reference file (sharing the idiom, or unrelated) leaves every pre-existing pair's outcome unchanged (the added file adds new pairs), so document-frequency suppression fails it; a config whose boilerplate digest mismatches is rejected with its code. Both implementations match | **met**. OD-C5 is confirmed ([owner decisions of 2026-11-23](#owner-decisions-2026-11-23)). Every vector clause passes in both implementations: suppression by catalogue, invariance from three references and from added unrelated files, and digest-mismatch rejection. The sabotages are caught (implementation `82b02ab`; [I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §7). The vectors are draft vectors; their promotion is tracked under M2.6 | S+I (I2) |
| M2.11 | E | Minimum evidence counts **distinct** non-common hashes, not seeds (decision pending in the contract). At least 1 vector where one hash repeats in at least 2 seeds: below-minimum-evidence in both modes. At least 1 vector at exactly the minimum: match. Both implementations match | **met**. The distinct-hash rule is confirmed ([owner decisions of 2026-11-23](#owner-decisions-2026-11-23)). `go-repeated-hash-self` gives below-minimum in both modes, and `rv-gap-equal` and 5 more vectors at exactly the minimum give match, in both implementations (implementation `82b02ab`; [I2 review](research/reviews/implementation-merge-i2-review.md) `de9a5b7` §7) | S+I (I2) |

### M2E — Embed and detect (per candidate carrier)

**Research record: candidate SYN** (existing synthetic Go/Rust carriers). Not counted in progress.

| Record | Result | Status / evidence |
| --- | --- | --- |
| SYN.1 | Deliberate insertion recovers after the formatter: **55/55** nonzero insertions per language. The 62/62 total includes 7 already-zero states, which show decoding only | measured; evidence committed in `4d0288f`: [experiment-checkpoint.md](research/experiment-checkpoint.md) |
| SYN.2 | Functionality checks on marked outputs only: Go 124/124 (clean + formatted); Rust 124/124 per build profile, 248 across two. Attack outputs excluded | measured; evidence committed in `4d0288f`: [Go](research/lanes/go-carrier-results.md), [Rust](research/lanes/rust-carrier-results.md) |
| SYN.3 | Nonzero states survive cheap canonicalization | negative-result measured; evidence committed in `4d0288f`: 55/55 reset per language ([experiment-checkpoint.md](research/experiment-checkpoint.md)) |
| SYN.4 | Signal transplant is not decoded as same-context evidence | negative-result measured; evidence committed in `4d0288f`: same-context transfers decode, [fragment-policy-checkpoint.md](research/fragment-policy-checkpoint.md) |
| SYN.5 | Safe eligible sites in the 4-repository census, narrow patterns | inconclusive: no eligible site established; 5 Go singletons unassessed, [census](research/public-census-checkpoint.md), committed in `95fb157` |

**Counted gates for the next candidate C:** (H-1 relies on detection-output schema fixtures; the gate that creates them is to be named when a carrier is selected.)

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M2E.0 | O | A decision record either selects candidate C (when C meets M2E.1) or omits embedding from the next release. M5.4 cannot state omission without it | open | S |
| M2E.1 | R | Frozen and committed before measurement: (a) eligible subset; (b) declared transformations, including full cheap normalization; (c) minimum net authenticated bits per unit, derived from the UC-6 payload and **approved by the owner**; (d) behavior checks; (e) the survival rate required for each declared transformation. Measured on a sample from a new owner-approved census protocol, never tuning data. **Met only if the owner-approved minimum (c) holds on that sample; otherwise negative-result** | open ([lane 06](research/lanes/06-evidence-review.md): no ready candidate) | S |
| M2E.2 | E | Reproducible insertion: seeds are recorded and a rerun reproduces every marked-output digest. Only deliberate insertions are counted | open | I |
| M2E.3 | E | Functionality/quality checks on **marked outputs only**, k/k. Attack outputs are reported separately | open | I |
| M2E.4 | E | Private mark-record schema with example and rejection fixtures. Fields: original and marked digests, profile/config digest, seed/key reference (never key bytes). Stored outside the checkout by default. `validate` checks it | open | S |
| M2E.5 | E | Controls measured, each with at least 1 case and a denominator: unmarked, wrong mark/key, removal by full cheap normalization, transplant, partial fragment | open | I |
| M2E.6 | R | Each declared M2E.1(b) transformation reaches the survival rate frozen in M2E.1(e), measured with denominators. Met only if every rate holds; otherwise negative-result | open | I |
| M2E.7 | E | Mark-only, fingerprint-only and combined detection compared on the same held-out cases at the M3.0 budget | open (needs M3) | I |

### M3 — Measure usefulness

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M3.0 | O | Operational false-alarm budget and its unit (per repository search) recorded | **met**: budget 1 in 20 per repository search. The unit is one unordered repository pair as defined in [m3-eval-draft-3](research/drafts/evaluation-protocol.md#141-m30-the-false-alarm-budget): 132 held-out negative searches, and M3.6 is met when alarms ≤ 6. Follow-up: 1 in 100 is tested on a larger corpus only if this passes. Decision record: [owner decisions of 2026-11-23](#owner-decisions-2026-11-23) | S |
| M3.1 | E | Corpus manifest gives, per entry: pinned revision, licence, redistribution permission and split group. Excludes the census repositories. A script verifies every field | open | I |
| M3.2 | E | Split file digest committed; groups disjoint (script check) | open | I |
| M3.3 | E | The commits freezing thresholds/config and splits are **git ancestors** of the first held-out result commit. Ancestry is checked, not timestamps | open | I |
| M3.4 | E | Held-out report: recall by transformation × fragment-size bucket; false alarms per repository search; abstentions; candidate volume; runtime; peak memory. Every figure has a denominator | open | I |
| M3.5 | E | A second person reruns M3.4 and gets identical counts. Runtime and memory may differ within the tolerance stated in the report | open | I |
| M3.6 | R | Computed usefulness verdict, not chosen. Met when measured false alarms per repository search, at the frozen M3.3 configuration on held-out data, are at or below the budget frozen at M3.0; above it, recorded as negative-result (the M3.4 report remains valid evidence). No recall floor is set; recall is reported without a pass line | open | S |

### M4 — Verify evidence

| ID | Type | Verifiable criterion | Status / evidence | Owner |
| --- | --- | --- | --- | --- |
| M4.1 | R | Pinned Go/Rust DSSE libraries interoperate on the existing statement: 4 producer/consumer pairs, no network | met: committed in `0bc4e23`. [results.json](research/experiments/signing-interop/results.json) holds 66 outcomes = 4 × 16 for the 4 producer/consumer pairs (Go→Go, Go→Rust, Rust→Go, Rust→Rust) plus 2 unpaired on the existing 762-byte statement, with `network_denied: true`. Network denial in the recorded run rests on that recorded flag: a non-author rerun could not nest `sandbox-exec`, so its flag was false; libraries pinned in the committed `go.sum` and `Cargo.lock` ([results](research/lanes/signing-interop-results.md)). Recorded results checked in this change; the harness was not rerun | S |
| M4.2 | R | Independent Go/Rust commitment code reproduces `test-vectors/commitment.json` and rejects changed openings | met: committed in `0bc4e23`. [policy-results.json](research/experiments/signing-interop/policy-results.json) holds 50 native commitment outcomes: Go and Rust both reproduce the `test-vectors/commitment.json` value `f4df04ab…c4a9`, and changed openings (catalogue bit flip, trailing whitespace, nonce bit flip, reserialization) give different commitments in both; invalid nonce lengths are rejected ([results](research/lanes/signing-policy-results.md)). Recorded results checked in this change; the harness was not rerun | S |
| M4.3 | E | Negative cryptographic vectors (tampered payload, type or signature; untrusted key; malformed or duplicate-key payload; subject mismatch), each with a distinct reason code. `validate` checks them | open | S |
| M4.4 | E | Two implementations, each with its own strict parser and key-hint policy, produce identical bytes and reason codes on every M4.3 vector | open | I |
| M4.5 | E | in-toto adapter accept/reject fixtures, checked by `validate`. A trust-policy document. A recorded decision on the optional timestamp adapter | open | S |
| M4.6 | E | Commitment/disclosure design reviewed by a named non-author. Report in `docs/reviews/`; every finding has a disposition | open | S |

### M5 — Candidate release

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M5.1 | E | M1.5 rules applied to every MUST in `spec/` and `profiles/`; unmapped 0 | open | S |
| M5.2 | E | Claims are every sentence of the README outside a script-defined exclusion list (headings, link-only lines, code blocks). The non-author checker, not the author, approves the exclusion list. Each claim sentence maps to a fixture, benchmark row or review. Unmapped 0 (TW-07) | open | S |
| M5.3 | E | A non-author reproduces the demo offline after dependency fetch: clean clone → pinned implementation | open | S+I |
| M5.4 | E | Release notes list every unresolved limit and state (a) whether embedding is included, citing M2E.0 if omitted, and (b) whether signing is included. Claiming cryptographic verification requires all M4 E gates met; otherwise the release is labelled unsigned detector-only | open | S |
| M5.5 | E | Versioned spec, migration notes and a conformance matrix (feature × level × implementation) | open | S |

## Owner-blocked gates

These cannot close until the owner acts:

- **M2E.0:** select a carrier or omit embedding.
- **Image mark study (IMG.1–IMG.5), owner-gated parts only:** any real-image set; any weight with a non-commercial or unclear licence; any GPU spend. Synthetic images and permissively licensed weights are approved ([owner decision on image marks and C2PA](#owner-decision-2026-11-23-image-marks-and-c2pa)).
- **IMGF.6:** any real image set for an at-scale false-match measurement.
- **TXT.0, TXT.5 (and so TXT.6):** UC-8 wording; the PAN-PC-10 download.
- **TXT.8:** any new text-mark experiment.

Approved on 2026-11-23 and awaiting execution: promotion of the drafts (M1.1, M1.2, M1.3, M1.6, M2.6), in progress in another lane; the re-vendor and strict pin check in the implementation repository against the public branch (M1.4; pin correctness in M2.2 and M2.4); corpus acquisition (M3.1). See the [decision records](#owner-decisions-2026-11-23).

## Owner decisions, 2026-11-23

On 2026-11-23 the coordinator put four decisions to the owner, with recommendations. The owner delegated these decisions to the coordinator. This record is as relayed by the coordinator. The recommendations, now decided:

1. **False-alarm budget (M3.0, met).** 1 in 20 per repository search on the current 48-repository corpus. The unit is one unordered repository pair as defined in [`m3-eval-draft-3`](research/drafts/evaluation-protocol.md#141-m30-the-false-alarm-budget): 132 held-out negative searches, and M3.6 is met when alarms ≤ 6. Follow-up: 1 in 100 is tested on a larger corpus only if this passes.
2. **Corpus acquisition (M3.1) approved.** This covers the 48 proposed repositories and their mechanical replacements under the protocol, cloned at depth 1. They are stored at `~/traceweave-eval` (`TRACEWEAVE_EVAL_DIR`), outside every working tree. The licence recheck fails closed. M3.1 itself stays open until its manifest criterion is met.
3. **Promotion approved.** The reviewed contract drafts are promoted into `spec/` (the two contracts), `test-vectors/`, `schemas/` and `profiles/` on the local branch. Another lane is doing this; M1.2, M1.3, M1.6 and M2.6 are not marked until it lands.
4. **Push approved.** `roadmap-v2` is pushed to `origin` as a branch, not `main`, after a hygiene check. **Done 2026-11-23**: the verified public rewrite of this branch is `roadmap-v2` at public commit `dec460e`, from source commit `409d486` on the local branch ([public history map](research/public-history-map.md); [promotion and push review](research/reviews/promotion-and-push-review.md#public-branch-verification-2)). `origin/main` is untouched, and the CI run is pending.

   **Standing rule:** the local branch is never pushed. Only regenerated public history is pushed, and only as fast-forwards. No pin-dependent gate (M1.4; pin correctness in M2.2 and M2.4) is marked met until the implementation repository must first re-vendor from the promoted paths at a pushed public commit and pass its strict pin check.
5. **Decided-in-draft items confirmed** by the coordinator under the same delegation:
   - extraction bounds (`k`, `window`, `maxInputBytes`);
   - OD-C5, the boilerplate catalogue bound by digest;
   - distinct-hash minimum evidence;
   - comparison bounds;
   - nesting depth 64;
   - the A5–A8 behavioural rules;
   - the `ts-tokens` stage-1 decisions;
   - the `text-plain` stage-1 decisions.

   M2.10 and M2.11 are met on that basis, with every other clause already satisfied according to the I2 review.

## Owner decision, 2026-11-23: image marks and C2PA

On 2026-11-23 the owner approved two openings. Both are recorded here in paraphrase, as relayed by the coordinator.

**The image embedded-mark study, on child lanes.** This includes downloading model weights once their licences have been checked.
- IMG.0 becomes "approved; use-case wording being drafted". It is met only when the UC-7 use case is merged into `docs/use-cases.md` and counted as worded.
- IMG.1–IMG.5 are no longer owner-blocked for synthetic images and permissively licensed weights.
- Still owner-gated: any real-image set; any weight with a non-commercial or unclear licence; any GPU spend; and IMGF.6.

**The C2PA mapping work.** C2PA.1–C2PA.3 are in progress. This overrides their sequencing: the delivery sequence had placed C2PA after M4. Core M1–M3 gates keep priority under the supervision rule.


## Progress count

Counted on 2026-11-23 from the status columns above. In the later-profile table, a row is open unless its criterion carries a **Status: met** note; IMGF.2–IMGF.4 and IMG.0–IMG.4 are met.

| Gates | Total | Met | Negative-result | Open |
| --- | --- | --- | --- | --- |
| Core M0–M5 | 47 | 11 (M0.1, M0.2, M0.3, M0.4, M2.5, M2.8, M2.10, M2.11, M3.0, M4.1, M4.2) | 0 | 36 |
| Later profiles, EXT and RC | 48 | 8 (IMGF.2, IMGF.3, IMGF.4, IMG.0, IMG.1, IMG.2, IMG.3, IMG.4) | 0 | 40 (WEB.0–WEB.6 planned) |

M0.1 is met on the second non-author recount (`3a640b3`). M2.5 and M2.8 are met on the [I2 review](research/reviews/implementation-merge-i2-review.md) (`de9a5b7`) of implementation `82b02ab`.

**What the remaining M1/M2 gates wait for.** Each open M1/M2 status names its remaining clause:
- **(a) Owner-approved, execution pending** ([owner decisions of 2026-11-23](#owner-decisions-2026-11-23)):
  - promotion of the drafts to `spec/` (the two contracts), `test-vectors/`, `schemas/` and `profiles/` is in progress in another lane, and closes M1.2, M1.3 and M1.6;
  - the push is done (`dec460e`, 2026-11-23); M1.4 closes only after the implementation repository must first re-vendor from the promoted paths at a pushed public commit and pass its strict pin check.
  M2.10 and M2.11 are met.
- **(b) Engineering still to do:**
  - the `scripts/offline` wrapper (M2.1);
  - the frozen fixture manifest (M2.2);
  - the vendor control class (M2.3, M2.6);
  - the B10 rebuild-from-clean-clone check (M2.4);
  - review packets (M2.7, not started);
  - the candidate-generation record keyed by `bodySha256` (M2.9);
  - the requirement map (M1.5);
  - the M1.1 item map.

  M1.1, M2.2, M2.4 and M2.6 also have an (a) clause.
- **(c)** Nothing else.

The SYN records are research records and are not counted. Evidence for M4.1 and M4.2 is committed in `0bc4e23`.

## Later profiles and sequence

```
M0 ─► M1 ─► M2 ──┬─► M3 ─► M5 ─► EXT ─► RC (1.0 candidate)
      │    M2E ──┘          ▲ M4 required only if the release claims signatures
      └─► M4 ─ ─ ─ ─ ─ ─ ─ ─┘
I0 ► I1 ► I2 ► I3;  I4 after I0;  I5a after I2 and M2E.1 met;  I5b after I3
Now, by owner override (research and fingerprint-only): TS, IMGF, TXT.0–TXT.4, TXT.7, TXT.8
Now, by owner decision of 2026-11-23: IMG.0–IMG.5 (synthetic images, permissive weights), C2PA.1–C2PA.3
Owner-gated: TXT.5–TXT.6 (corpus download)
After I2: SK   After M3.4: BIN, RES, STRUCT, KEYED, WEB (planned)
```

**Implementation track status (2026-11-22).** The implementation repository is `<implementation repo>`; its `main` is at `82b02ab`, unpushed.
- **I1:** two independent extractors (Rust and Go, hand-written lexers) are merged. Reviewed at `ce97ed9` in the [I1 review](research/reviews/implementation-merge-i1-review.md) (`9c03c95`): 9.89 M differential cases agree, and both reproduce every vendored vector and record. Its exit gate is not complete: `check-spec-pin --strict` fails by design until a spec commit is pushed. Feeds M1.4 and M1.6.
- **I2:** two independent catalogue, comparison and report implementations are merged at `82b02ab`. Reviewed in the [I2 review](research/reviews/implementation-merge-i2-review.md) (`de9a5b7`): 76/76 report bodies, 5,000/5,000 clean-room pairs and 10,311/10,311 differential cases agree. Its exit gate is not complete: `scripts/offline` is missing, and M2.1–M2.4, M2.6, M2.7 and M2.9 are open. The A6 behavioural rules B1–B10 are adopted on a later implementation branch, not yet on `main` or reviewed.
- **I3–I5:** not started.

**Owner override of the M3.4 ordering (recorded 2026-11-22).** Asked about TypeScript, images and text, the owner approved all three. Coordinator reading, recorded here as the decision:

- **Approved targets:** the TypeScript/JavaScript, still-image and text/document profiles.
- **May start now, before M3.4:** their evidence research and fingerprint-only work. That covers extraction profiles, hand-derived vectors, two-implementation agreement, and experiments that need no download beyond what is already in the repository: TS.1–TS.3, IMGF.1–IMGF.5 (synthetic images only; IMGF.6 is owner-gated) and TXT.0–TXT.4, TXT.7, TXT.8.
- **Still needs the owner:** any text-mark experiment under TXT.8; for image marks, only the parts named in the [owner decision on image marks and C2PA](#owner-decision-2026-11-23-image-marks-and-c2pa); any model-weight or dataset download (TXT.5); and any real, non-synthetic image set (IMGF.6). The IMGF package install was approved; see the record below.
- **Unchanged:** BIN, RES, STRUCT and KEYED still wait for M3.4.

**Owner decision record: fingerprint-only image experiment (2026-11-22).** Earlier that day, the owner approved TypeScript, images and text. Later, the coordinator asked for approval of the fingerprint-only image experiment and its project-local install of Pillow, NumPy and iscc-core, with no model weights and no real images. The owner approved the experiment. This record is as relayed by the coordinator. It approves that install and the synthetic-image run (`e-img-f-2`) only. It does not approve model weights, real image sets (IMGF.6) or any mark study (IMG.0–IMG.5).

The owner may narrow this reading. Core M1–M3 gates keep priority under the supervision rule: these lanes do not close or replace any core gate. Evidence: [lane 09](research/lanes/09-evidence-review.md) (text) and [lane 10](research/lanes/10-evidence-review.md) (image). The implementation-track gate mapping is in [the plan](docs/implementation-repo-plan.md#milestones).

| ID | Type | Verifiable criterion | Owner |
| --- | --- | --- | --- |
| **TS — second code profile (TypeScript/JavaScript)** | | | |
| TS.1 | E | Profile covers the M1.1 list plus ASI, regex vs division, template literals, JSX/TSX, and `.d.ts`/generated/minified exclusions | S |
| TS.2 | E | Hand-derived vectors cover the M1.2 classes plus the TS.1 classes | S |
| TS.3 | E | Two implementations without a shared lexer match the TS.2 expected bytes | I |
| TS.4 | E | Own M3 split, reported separately and not pooled | I |
| **IMGF — still images, fingerprint-only first** ([lane 10](research/lanes/10-evidence-review.md)) | | | |
| IMGF.1 | E | An image extraction profile answers every item in lane 10's "Extraction contract (fingerprints)" list, with 0 TBDs. The items are: decoder and version, EXIF orientation, colour conversion, alpha flattening, multi-frame policy, luminance formula, resize filter and size, border crop, hash algorithm and bit length, quality abstention threshold, dihedral variants and distance metric **Status: open.** The draft-2 profile ([extraction-profile-image.md](research/drafts/extraction-profile-image.md) §11) maps all 12 items, but two things remain. (1) The ISCC resize and grey steps (§5 steps 2–3) are still defined by Pillow's `BICUBIC` and rounding code rather than by a formula, which the review flagged as implementer discretion. (2) No non-author has counted the 12-item map for draft-2. | S |
| IMGF.2 | E | **PDQ, exact:** on identical decoded RGB arrays, the profile's PDQ implementation equals the vendored ThreatExchange Python reference (commit `9f627fb1…`) in all 8 dihedral hashes and the quality score, k/k. This holds on the 30 pinned `pdq/data` files and on every input that a measured run cross-checks (protocol V4, `e-img-f-2`). **PDQ, vendor tolerance:** on the profile decode path, every hash is within 10 bits of the ThreatExchange C++ `reg_test` output for each vector with published quality ≥ 80 (the vendor README criterion), k/k. Every hash is within 16 bits of each comparable published Python output (the vendor unit-test criterion), k/k. Published quality scores are equal, k/k. Exact equality with published hashes is not required, because the vendor's own reference sets differ by up to 8 bits on identical files. **ISCC:** the hash core equals iscc-core 1.5.0 `data.json` `gen_image_code_v0`, k/k; the normalization steps are not covered by any published vector and are not claimed by this gate. A C++ reference build is not needed for this gate, but it is required for IMGF.5 and before any claim of exact interoperability. Wording from the [image protocol review](research/reviews/image-profile-protocol-review.md#imgf2-for-pdq-reproduced-with-proposed-gate-text) **Status: met** (frozen `6f39e50`, results `0c7523c`, [results recheck](research/reviews/image-profile-protocol-review.md#results-recheck-e-img-f-2) `dbd109b`). PDQ exact: port equals the vendored reference on 30/30 vector files and 1,400/1,400 extractions in each run. Tolerance: C++ within 10 bits 8/8; Python within 16 bits 12/12 and 18/18; published quality equal 8/8 (C++) and 12/12 (README). ISCC core 3/3. | I |
| IMGF.3 | E | Protocol `e-img-f-2` (the contract-and-record conformance run in lane 10's ["After the report audit"](research/lanes/10-evidence-review.md#after-the-report-audit)) is frozen. Its digest is recorded in the protocol file and in `research/experiments/image-fingerprint/README.md`. A non-author reviews it before the first result commit. The result commit descends from the frozen commit (`git merge-base --is-ancestor`). The harness logs its identity checks: clean tree, HEAD equals the frozen commit, and a fresh reference-vector check. The package install (Pillow, NumPy, iscc-core into a project-local environment) has owner approval (decision record of 2026-11-22 above). Design record: on 2026-11-22, before any result, the coordinator chose `e-img-f-2`; the 2,000-image `e-img-f-1` was retired unrun ([image protocol review](research/reviews/image-profile-protocol-review.md), B2) **Status: met** (frozen `6f39e50`, protocol digest `44a67a14…`; non-author review `835f6c0` is an ancestor of results `0c7523c`; [results recheck](research/reviews/image-profile-protocol-review.md#results-recheck-e-img-f-2) `dbd109b` confirms `codeIdentity.ok` and the logged clean tree, HEAD and vector check; install approved 2026-11-22). | I |
| IMGF.4 | R | On 200 seeded synthetic images with the 12 defined edits, under network denial (`sandbox-exec` deny-network or `scripts/offline`, with the harness network probe failing first), met when all of these hold: (a) the reference-vector checks pass with the IMGF.2 exact and tolerance counts, k/k; (b) two full runs are byte-identical; (c) every result validates against the shared record/catalogue form, with 0 invalid. Negative-result if any of (a)–(c) fails. False-match and missed-match counts are reported with their denominators and **no pass line**. Cross-host agreement is recorded as not tested. False-match rates at scale, and crop and screenshot failure, come from the external benchmark preprint X1 cited in the [lane 10 report audit](research/lanes/10-report-audit.md). That preprint is unreplicated, and its results are not our measurement. A non-author rechecks the counts **Status: met** (results `0c7523c`, [results recheck](research/reviews/image-profile-protocol-review.md#results-recheck-e-img-f-2) `dbd109b`). (a) vector checks 7/7 k/k; (b) `full-1` and `full-2` byte-identical; (c) 0 invalid catalogue and query records; the network probe was refused first under `sandbox-exec`. **Headline counts, synthetic-image contract check only, no pass line.** Enrolment: PDQ 98/100 (2 `low-quality`), ISCC 100/100. Negatives within threshold: 0/100 for each extractor. PDQ correct per edit (out of 100): flip, jpeg50, jpeg75, jpeg90, png, resize25 and resize50 98 each; jpeg30 98; crop90 2; crop75 0; crop50 0; screenshot 0. ISCC correct per edit (out of 100): crop90 69; crop75 5; crop50 0; the other 9 edits (screenshot included) 100 each. Wrong-entry matches 0/1,200 for each extractor. Cross-host: not tested. These counts are not a false-match rate, and they say nothing about natural images. | I |
| IMGF.5 | E | Two implementations produce identical PDQ hashes and quality scores on the IMGF.2 vectors and the full frozen synthetic set. A ThreatExchange C++ reference build is one of the comparisons | I |
| IMGF.6 | R | Any at-scale false-match measurement of our own: a held-out real image set, a frozen threshold, and per-query false matches against a stated catalogue size, each with its denominator. Owner-gated (real image sets); open until approved and run | I |
| **IMG — image marks, later and owner-gated** ([lane 08](research/lanes/08-evidence-review.md), [lane 10](research/lanes/10-evidence-review.md)) | | | |
| IMG.0 | O | Owner approves UC-7 ("a creator marks images they publish and later checks a candidate"), written like UC-6, and the TrustMark weight download. **This is a prerequisite of IMG.1–5**, which also start only after IMGF.4 closes. The 2026-11-22 override does not cover mark studies **Status: met** (`3147237`). The owner approved the study and the weight download on 2026-11-23 ([owner decision on image marks and C2PA](#owner-decision-2026-11-23-image-marks-and-c2pa)); the lane 12 licence check cleared the weights. Under the owner's delegation of routine decisions, the coordinator accepted the reviewed UC-7 wording. It is merged as [UC-7](docs/use-cases.md#uc-7-recognize-a-marked-image), written like UC-6, and counted in the capability index (14 rows: the 13 M0.1 capabilities plus UC-7). | S |
| IMG.1 | E | Pin record: TrustMark code commit; weight SHA-256; code, weight and dependency licences; licensed non-private image set Not owner-blocked for synthetic images and permissively licensed weights. Real-image sets, non-commercial or unclear-licence weights, and GPU spend stay owner-gated. **Status: met** (pins and licences: lane 12, re-verified at run time in results `a78aace`: 84/84 sources, 6/6 weight SHA-256, 0 environment deviations; [results recheck](research/reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2) `d3d4788`). Coordinator decision, 2026-11-23: the deterministic, project-generated synthetic image set satisfies the "licensed non-private image set" clause for this study. Any real-image set stays owner-gated. | I |
| IMG.2 | E | Embed and detect pass with network denied after provisioning. Either `sandbox-exec` deny-network or `scripts/offline` (implementation repository) is acceptable, together with the harness network probe, which must fail first. This matches IMGF.4 ([image mark protocol review](research/reviews/image-mark-protocol-review.md), M3) **Status: met** (results `a78aace`; [results recheck](research/reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2) `d3d4788`). Steps ran under `sandbox-exec` deny-network, with the probe refused first; P1 was 100/100 for both learned schemes. | I |
| IMG.3 | E | Frozen and committed before running: transformation list (JPEG, resize, crop, ReMark, and VAE regeneration only if its weight licence is accepted), PSNR floor, threshold, a `dwtDct` no-key negative control and a residual-transplant arm **Status: met** (frozen `d3af1ee`, protocol `e-img-m-2`, digest `cba36673…`; results `a78aace` descend from it, and code identity was verified; [results recheck](research/reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2) `d3d4788`). | I |
| IMG.4 | R | Whole-message success per transformation; unmarked and wrong-key false detections; transplant result. Each has a denominator **Status: met** (results `a78aace`, frozen `d3af1ee`, [results recheck](research/reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2) `d3d4788`). **Headline counts, synthetic images only, out of 100 per condition, TrustMark-Q / PixelSeal.**
- Clean: 100 / 100.
- ReMark: 1 / 99.
- JPEG quality 10: 48 / 18.
- Residual transplant accepted: 82 / 90.
- Keyless re-embed accepted: 100 / 100.
- Wrong key, unmarked and wrong entry: 0 accepts (10,000, 20,000 and 9,900 comparisons per scheme).

Removal and forgery counts are lower bounds on what an attacker can do. Full counts are in the recheck. | I |
| IMG.5 | E | IMGF and IMG results fit the lane-08 container fields, or a schema change goes through CONTRIBUTING **Status: open.** One decision remains: where the six detection-record fields with no home in the lane-08 container should live. They are model digests, the statistic with its n, the threshold basis, the key and derivation id, embedding quality, and which bit positions are tested. The options are a container extension or a profile-specific record, under CONTRIBUTING. | S |
| **TXT — text and documents** ([lane 09](research/lanes/09-evidence-review.md); proposed [UC-8](docs/use-cases.md#proposed-uc-8-find-reused-passages-in-prose)) | | | |
| TXT.0 | O | Owner accepts the wording of proposed UC-8 in `docs/use-cases.md`, or amends it. Not a prerequisite of TXT.1–TXT.4 under the override | S |
| TXT.1 | E | A text extraction profile answers every item of lane 09's "How the extraction contract could host a text profile", with 0 TBDs. Items: format front end (`plain`/`markdown`, pinned CommonMark version); BOM policy; the fold over pinned Unicode 17.0.0 files (NFKC, full case folding, delete Default_Ignorable_Code_Point, White_Space mapping, optional confusable channel pinned by `confusables.txt` digest); token rule, including scripts written without spaces; `exact` and `folded` channels with no stemming or stop words; span mapping of every folded token to its original half-open UTF-8 byte span; k and w in the config bytes; a closed error list; and a hash-framing string | S |
| TXT.2 | E | Hand-derived vectors (`derivation: hand`), at least 1 for each class: empty; below `k+w-1`; BOM; CRLF; NFD input; NFKC expansion (U+FB01); case-fold expansion (U+00DF); zero-width inside a word; listed confusable; other Default_Ignorable; Markdown syntax; invalid UTF-8; NUL. Each vector gives expected tokens and original byte spans, and each positive vector has a paired rejection vector | S |
| TXT.3 | E | Two implementations, each using its own Unicode normalization and case-folding code pinned to the profile's Unicode version, equal the TXT.2 expected bytes on every vector | I |
| TXT.4 | R | Stage 1, no download. Input: the repository's own CC BY 4.0 prose (the 11 files under `docs/`, `spec/` and `profiles/` at a pinned commit) plus TXT.2. Lane 09's transformations are applied to every file. Negatives: all 110 ordered file pairs and the boilerplate set. Protocol frozen as an ancestor commit; run under `scripts/offline`; a non-author rechecks the counts. Negative-result if any lane 09 failure criterion holds: (i) the implementations differ on any vector; (ii) any reported span does not equal the original bytes of the matched tokens; (iii) any transformed positive keeps an unchanged folded run of at least `k+w-1` tokens yet shares 0 fingerprints. Negatives are reported as matches/110 | S/I |
| TXT.5 | O | Owner approves the PAN-PC-10 download (Zenodo record 3250123, 1,773,941,212 bytes, CC BY 4.0 on the record), licence acceptance and storage location | S |
| TXT.6 | E | Stage 2, only after TXT.4 met and TXT.5 recorded. Frozen before running: a seeded sample of 200 cases for each of 5 obfuscation classes (1,000 positives) and 200 suspicious documents without plagiarism; k, w and the boilerplate catalogue. Report per class: detection under the PAN measures, abstentions, and negatives with any match (out of 200), each with its denominator. No rate is claimed beyond n (0/200 bounds only below about 1.5%) | I |
| TXT.7 | E | The profile and release notes list the limits: paraphrase; translation; fragments shorter than `k+w-1` tokens; scripts without spaces, if unmeasured. Each limit cites a TXT.4 or TXT.6 count or a lane 09 source. A non-author counts 0 uncited limits | S |
| TXT.8 | R | Research question: does any embedded mark in existing text survive the cheapest declared fold? [Lane 09](research/lanes/09-evidence-review.md#embedded-marks-in-existing-text) finds homoglyph and zero-width carriers erased by one published fold (NFKC + UTS #39 skeleton + delete Default_Ignorable), and rejects the AWT lexical rewriter. Status open: recorded as negative-result for Unicode carriers only after a non-author confirms that reading against the cited sources. Any new text-mark experiment needs the owner | S |
| **BIN — binary/compiled artifacts** | | | |
| BIN.1 | R | Primary-source review of source-to-binary mark survival and binary similarity, in the lanes 06–08 format | S |
| BIN.2 | O | Decision record citing BIN.1: a binary profile with its own gates, or out of scope | S |
| **RES — resolver threat model** | | | |
| RES.1 | E | Threat model: query leakage, enumeration, catalogue inference, membership disclosure, abuse. Public registration stays optional | S |
| RES.2 | R | The adversary query model and the leakage metric are named and committed before running; then measured on synthetic catalogues with denominators | S/I |
| RES.3 | E | Independent review filed, with every finding dispositioned | S |
| **C2PA — mapping with interop fixtures** (`traceweave.org`, registered 2026-11-23, provides the owned namespace the mapping draft said was missing; the draft itself is updated by its own lane) | | | |
| C2PA.1 | E | Mapping pinned to one C2PA version; each field mapped, unmapped or conflicting **Status: in progress** (2026-11-23 override of the after-M4 sequencing). | S |
| C2PA.2 | E | Fixtures from a pinned open-source C2PA tool round-trip through a Traceweave adapter in both directions **Status: in progress.** | I |
| C2PA.3 | E | README makes no compatibility claim until C2PA.2 passes **Status: in progress.** | S |
| **SK — agent skill** | | | |
| SK.1 | E | Wraps only stable I2 commands; diagnostics pass through unchanged | I |
| SK.2 | E | Canary strings seeded into catalogues, paths and keys appear 0 times in model-visible transcripts across all fixture runs | I |
| **Later matching methods** (ROADMAP "Later") | | | |
| STRUCT.1 | R | Structural/semantic matching compared with the token baseline on the M3 corpus and budget | I |
| KEYED.1 | R | Keyed feature selection evaluated separately from embedding on the M3 corpus and budget | I |
| **WEB — browser tool and testing page** (requested by the owner on 2026-11-23; **planned; not started; no lane assigned**). Purpose, as the owner described it: to make Traceweave accessible, not to earn revenue. It is free to use, with no accounts and no uploads | | | |
| WEB.0 | O | The owner decides when to start WEB and where it is hosted. The sequence places WEB after M3.4, because a public tool should not come before the measurement; the owner can override this. WEB covers only implemented profiles: Go and Rust today; TypeScript, text and Python when implemented. A timestamping or transparency-log service is out of scope for WEB and belongs with M4. **Status: planned** | S |
| WEB.1 | E | The Rust implementation compiles to WebAssembly. For every vendored extraction, record, catalogue and matching vector of the profiles it implements, the in-browser build's output is byte-identical to the command-line build's, k/k, run headless in CI. **Status: planned** | I |
| WEB.2 | E | Nothing leaves the browser. The page works with the network denied after load. A test asserts 0 network requests during fingerprinting and comparison. No analytics, no uploads, and no storage beyond explicit user downloads. **Status: planned** | I |
| WEB.3 | E | Three flows must reproduce the command-line results. **Fingerprint:** dropped files yield a downloadable catalogue byte-identical to the command-line catalogue for the same inputs and config. **Compare:** two catalogues, or a catalogue and files, produce a report body with the same `bodySha256` as the command-line tool. **Verify:** loading a report re-runs it and shows whether the digest reproduces. Each flow is checked on a fixed fixture set, k/k. **Status: planned** | I |
| WEB.4 | E | A testing page shows the sample and the transformed copy side by side. A sample or dropped file is edited by hand or by named transformations: reformat, rename identifiers, reorder declarations, copy a fragment, embed in unrelated code, insert tokens at the evasion interval. The matched regions and the outcome update live. The page shows the documented misses as plainly as the matches: a fixed set of at least 6 demonstrations, at least half ending in no match or below-minimum-evidence. A self-check confirms that identical input matches fully and that an unrelated sample does not match. **Status: planned** | I |
| WEB.5 | E | The page states its experimental status. It says that a fingerprint or a match is not proof of ownership, authorship or copying. It also says that a catalogue made today says nothing about when the content existed; timestamped, signed records are M4. A non-author checks every sentence on the page against the README claim map (M5.2): 0 unmapped. **Status: planned** | S+I |
| WEB.6 | E | Accessibility and performance budgets are decided by counts. Each flow can be completed keyboard-only (k/k flows). A stated maximum input size applies, with a clear refusal above it, tested at the limit and one byte over. Further budgets are frozen before WEB.1 starts. **Status: planned** | I |
| **EXT and RC** | | | |
| EXT.1 | E | Named non-contributors review the spec, M3 methodology and M4 crypto (may reuse M4.6 if that reviewer qualifies). Reports filed; every finding dispositioned | S |
| RC.1 | E | Every E gate in M1–M5 met; every R gate met or negative-result; every O gate recorded; EXT.1 met. If M2E.0 records that embedding is omitted, M2E.2–M2E.5 and M2E.7 are exempt | S |
| RC.2 | E | Two implementations pass conformance levels 1–4 for every profile marked stable. Whether they need different implementers is an owner decision ([plan](docs/implementation-repo-plan.md#needs-the-owner)) | S+I |
| RC.3 | E | Scope statement covering media, embedding (M2E.0) and signing (M5.4) | S |

## Backlog and its gates

1. **TW-01: Choose the first deployment.** Use UC-1, UC-2 and UC-6 in the use-case guide. Inventory intended languages and artifact types using authorized local repositories; publish only a synthetic inventory. Proposed starting scope: source files in one language, local comparison, no remote resolver. Acceptance: a short decision record names the language, supported syntax, artifact boundary, excluded generated/vendor files, and search unit. Go and Rust are selected as pilot languages; exact source subsets and eligible regions remain to be measured. Gates: M1.1, M1.2. Status: open.
2. **TW-02: Specify extraction completely.** Define encoding, parser/grammar revision, failure handling, token channels, hash bytes, k/window parameters, rightmost-minimum ties, duplicates and byte coordinates. Acceptance: hand-checkable vectors for empty, short, Unicode, malformed, repeated and equal-minimum inputs. Parameters begin as experimental choices, not accuracy promises. Gates: M1.1, M1.2. Status: open.
3. **TW-03: Define catalogue and report contracts.** Add schemas with profile/config binding and artifact digests. Separate comparison from exact/signature/trust/time results. Acceptance: schemas, valid examples, rejection fixtures and version notes move together. Gates: M1.3. Status: open.
4. **TW-04: Build the smallest end-to-end reference.** Implement extract → catalogue → compare → localized report in the implementation repository (amended from "existing Python tooling"; the Python tooling stays the spec repository validator). Acceptance: a documented offline synthetic walkthrough is reproducible, with no private material in the checkout. Gates: I2, M2.1–M2.11. Status: open.
5. **TW-05: Establish an evaluation corpus.** Record provenance, permitted redistribution, split groups and transformations; retain a test set that tuning never sees. Acceptance: evaluation protocol and corpus manifest are frozen before threshold selection is evaluated on held-out data. Gates: M3.1–M3.3. Status: open.
6. **TW-06: Add cryptographic verification.** Choose maintained upstream libraries and pin versions after checking their current interfaces/security notes. Acceptance: the M4 negative tests and interoperability gate pass; schema validation never stands in for verification. Gates: M4.3–M4.5, I4. Status: open (bounded synthetic evidence exists; see the gate tables).
7. **TW-08: Research and prototype embedding/detection.** Begin alongside TW-02. Compare candidate marking methods against the intended language and transformations; record primary sources before choosing a method. Specify mark payload/identity, any key and randomness handling, embedding capacity, detector access assumptions, output localization, and transplant limitations. Acceptance: M2E fixtures plus quality/performance checks; separate mark-only, fingerprint-only and combined evaluation at the same false-alarm budget. No callbacks, planted defects or hidden telemetry. Gates: M2E.0–M2E.7. Status: open (bounded synthetic evidence exists; see the gate tables).
8. **TW-07: Review the release claims.** Map each README claim to a fixture, benchmark or external review. Acceptance: unmeasured claims remain goals and incompatible changes receive new identifiers. Gates: M5.2. Status: open.

These are local backlog IDs, not published GitHub issues. The gate tables above carry the acceptance criteria; the gate IDs after each item are the ones the item feeds. M0 and initial discovery work are done except where a gate below is still open.

## Needs the owner

These stay with the owner. No agent or supervision loop decides them or does them unasked:

- Pushing or publishing anything beyond what is approved. Approved on 2026-11-23: `roadmap-v2` to `origin` as a branch (not `main`), after a hygiene check; pushed as public commit `dec460e`. Only regenerated public history is pushed, as fast-forwards; the local branch never is.
- Creating GitHub repositories, and choosing their visibility. Also the Go module path.
- Normative format changes beyond the approved promotion. Approved on 2026-11-23: promoting the reviewed extraction, catalogue and report drafts and their vectors into `spec/` (the two contracts), `schemas/`, `profiles/` and `test-vectors/`.
- New diagrams.
- Paid services.
- Corpus acquisition beyond the approved 48 repositories and their mechanical replacements (approved 2026-11-23).
- Any change to the false-alarm budget (M3.0 recorded 2026-11-23: 1 in 20; 1 in 100 only on a larger corpus if that passes).
- Whether to omit embedding from the next release, or select a candidate (M2E.0). The M2E.1(c) payload minimum is also approved by the owner.
- For the image mark study (approved 2026-11-23 for synthetic images and permissively licensed weights; protocol basis in the [lane 06–08 checkpoint](research/research-06-08-checkpoint.md)): any real image set (including IMGF.6), any weight with a non-commercial or unclear licence, and any GPU spend. The IMGF package install was approved on 2026-11-22.
- Text: UC-8 wording (TXT.0), the PAN-PC-10 download (TXT.5) and any text-mark experiment (TXT.8). The 2026-11-22 override covers fingerprint-only TS, image and text work only.
- Also: licence split, hosted CI, the EXT reviewers, whether implementers must be independent people, and any contract option not yet decided (OD-C5 and the decided-in-draft items were confirmed 2026-11-23).

## How work is accepted

Use one reviewable change per decision or capability. Explain the use case, source support, normative delta, fixtures, measured result and known failures. Update [conformance](spec/conformance.md) whenever supported behavior changes. Run the repository validator and tests. Keep source revisions and implementation dependencies reproducible. Record disagreements as decisions with alternatives and revisit conditions.

Open choices: safe subsets within Go and Rust; representative authorized corpus; operational false-alarm budget; supported trust/key distribution model; and the second implementation/reviewer. None prevents completing this plan, and none should be guessed into a stable standard.
