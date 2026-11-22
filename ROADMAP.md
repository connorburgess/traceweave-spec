# Traceweave roadmap

Status: active research roadmap, version 2, updated 2026-11-22. The 0.1.0-draft.1 scaffold validates record shapes and synthetic vectors. Separate experimental harnesses recover synthetic carrier states and cross-verify Go/Rust signatures; production reuse detection remains unimplemented. No dates and no detection guarantees are promised. See the [measured checkpoint](research/experiment-checkpoint.md), the [active work queue](research/work-queue.md) and the [implementation repository plan](docs/implementation-repo-plan.md).

Start with [use cases](docs/use-cases.md), then [implementation patterns](docs/implementation-patterns.md) and the [source register](docs/sources.md). These planning documents do not change normative wire formats. The [independent review](research/reviews/roadmap-v2-review.md) of this version is kept with the other reviews.

## Pilot languages

Initial experimentation uses synthetic Go and Rust source code, with planned expansion to multiple media types. TypeScript/JavaScript is a later code-profile candidate. Private applications are outside the current experimental scope. Shared evidence formats stay language-independent; transformations, safety conditions and build-pipeline tests are profile-specific. Python research tooling does not select Python as the marked language. See the [feasibility investigation](research/02-carrier-feasibility.md).

## Core tracks

Embedded marking and detection are a first-class research track alongside extracted fingerprint matching. Provenance verification supports both. A baseline matcher is useful for comparison, but does not satisfy the embedding use case. No marking method is standardized yet.

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
| M0.1 | E | The capability list is exactly: UC-1…UC-6 and walkthroughs W-1, W-2 from `docs/use-cases.md`, plus one row per `##` heading of `docs/implementation-patterns.md` except "Example matrix" (13 rows today). A non-author recounts it from those documents. Each row needs a verification plan, merged into `docs/`, whose pass/fail is a command exit code or a count, with no judgment words. Met when every recounted row has such a plan | open: plans not yet merged into `docs/` | S |
| M0.2 | E | Five discovery lanes are reviewed against both provider reports | met: [discovery-checkpoint.md](research/discovery-checkpoint.md) | S |
| M0.3 | E | Example matrix: each row names its use case and expected assertion | met: [example matrix](docs/implementation-patterns.md#example-matrix) | S |
| M0.4 | E | `validate` exits 0 with 6 tests | met: [validate.py](tools/validate.py), rerun 2026-11-22 | S |

### M1 — Freeze one code experiment (token-fingerprint profile, Go and Rust)

| ID | Type | Verifiable criterion | Status | Owner |
| --- | --- | --- | --- | --- |
| M1.1 | E | A profile document answers every item in "Before registering a profile" in [profiles/code.md](profiles/code.md), with no TBDs. Token classes are defined independently of any lexer's token kinds: raw strings, nested comments, shebang, BOM, CRLF | open | S |
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
| M2.4 | E | Two runs produce an identical **canonical report body**, which excludes the provenance block. The comparison-config digest is in the body inputs, as the [draft contract](research/drafts/catalogue-report-contract.md) places it. The provenance block is checked separately: implementation commit and spec pin present and correct | open | I |
| M2.5 | E | Fragment containment and whole-file similarity are separate fields, shown in a large-host fixture where they diverge | open | S+I |
| M2.6 | E | Hand-derived matching vectors in `test-vectors/` (`derivation: hand`). They cover at least the M2.2 positive classes and the M2.3 control classes, give expected spans, containment and similarity, and `validate` checks them. These are the vectors I2 uses to complete conformance level 4 | open | S |
| M2.7 | E | UC-2 origin and dependency links live in a **separate review-packet record**, never in the comparison report. The record references the report's `bodySha256` and a region key: reference id, candidate id, mode, first seed. A spec schema with at least 1 valid example and 1 rejection fixture per required field, checked by `validate`. A rejection fixture whose region key is absent from the referenced body fails the semantic check. At least 3 valid fixtures: own-origin region; vendored/dependency region with an archived licence-text digest; historical permitted copy. The record has no rights-verdict field | open | S+I (I2) |
| M2.8 | E | Storage boundary (P-3). With no path option, a fixture run inside a temporary git checkout writes 0 files under it. The catalogue written to the documented private default has the expected catalogue SHA-256, so writing nothing cannot pass. Fault injection, 3/3, each leaving the previous valid catalogue byte-identical and no partial file at the final path: (1) an injected error before the temporary file opens; (2) SIGKILL after a partial write of the temporary file; (3) an injected rename failure. Keys are added to this gate only when M4 produces any | open | I (I2) |
| M2.9 | E | Index ranking is not evidence (P-5). Candidate generation (`exhaustive`, or the SHA-256 of the selected candidate-id set) is recorded in a **separate record keyed by the report's `bodySha256`**, never in the report body. In at least 2 fixtures, a fixed candidate catalogue gives a byte-identical canonical body whatever retrieval path (exhaustive or one index) or order produced it. A different candidate set is expected to change the candidate catalogue digest, the candidate count and the pairs. A rejection fixture adding a rank, score or index field fails the report schema | open | S+I (I2) |
| M2.10 | E | Common-code suppression uses an explicit boilerplate catalogue bound by its SHA-256 in the comparison config ([draft contract](research/drafts/catalogue-report-contract.md) OD-C5 option b; decision pending). Vectors, at least 1 each: suppression driven only by the boilerplate catalogue; an invariance case whose starting reference set **already holds at least 2 files sharing the idiom**, where adding 1 more reference file (sharing the idiom, or unrelated) leaves every pair's outcome unchanged, so document-frequency suppression fails it; a config whose boilerplate digest mismatches is rejected with its code. Both implementations match | open | S+I (I2) |
| M2.11 | E | Minimum evidence counts **distinct** non-common hashes, not seeds (decision pending in the contract). At least 1 vector where one hash repeats in at least 2 seeds: below-minimum-evidence in both modes. At least 1 vector at exactly the minimum: match. Both implementations match | open | S+I (I2) |

### M2E — Embed and detect (per candidate carrier)

**Research record: candidate SYN** (existing synthetic Go/Rust carriers). Not counted in progress.

| Record | Result | Status / evidence |
| --- | --- | --- |
| SYN.1 | Deliberate insertion recovers after the formatter: **55/55** nonzero insertions per language. The 62/62 total includes 7 already-zero states, which show decoding only | measured; evidence exists, uncommitted: [experiment-checkpoint.md](research/experiment-checkpoint.md) |
| SYN.2 | Functionality checks on marked outputs only: Go 124/124 (clean + formatted); Rust 124/124 per build profile, 248 across two. Attack outputs excluded | measured; evidence exists, uncommitted: [Go](research/lanes/go-carrier-results.md), [Rust](research/lanes/rust-carrier-results.md) |
| SYN.3 | Nonzero states survive cheap canonicalization | negative-result measured; evidence exists, uncommitted: 55/55 reset per language |
| SYN.4 | Signal transplant is not decoded as same-context evidence | negative-result measured; evidence exists, uncommitted: transfers decode, [fragment-policy-checkpoint.md](research/fragment-policy-checkpoint.md) |
| SYN.5 | Safe eligible sites in the 4-repository census, narrow patterns | inconclusive: no eligible site established; 5 Go singletons unassessed, [census](research/public-census-checkpoint.md) |

**Counted gates for the next candidate C:**

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
| M4.1 | R | Pinned Go/Rust DSSE libraries interoperate on the existing statement: 4 producer/consumer pairs, no network | open: evidence exists, uncommitted (66 outcomes, [signing-interop-results.md](research/lanes/signing-interop-results.md)) | S |
| M4.2 | R | Independent Go/Rust commitment code reproduces `test-vectors/commitment.json` and rejects changed openings | open: evidence exists, uncommitted ([signing-policy-results.md](research/lanes/signing-policy-results.md)) | S |
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

## Later profiles and sequence

```
M0 ─► M1 ─► M2 ──┬─► M3 ─► M5 ─► EXT ─► RC (1.0 candidate)
      │    M2E ──┘          ▲ M4 required only if the release claims signatures
      └─► M4 ─ ─ ─ ─ ─ ─ ─ ─┘
I0 ► I1 ► I2 ► I3;  I4 after I0;  I5a after I2 and M2E.1 met;  I5b after I3
After M1: TS   After I2: SK   After M4: C2PA
After M3.4 (or a recorded owner override): IMG, BIN, RES, STRUCT, KEYED
```

Media and resolver lanes wait for M3.4. Starting them earlier repeats the earlier drift, when work went to external research lanes instead of the baseline, and [lane 08](research/lanes/08-evidence-review.md) names deferral as the strongest alternative. The implementation-track gate mapping is in [the plan](docs/implementation-repo-plan.md#milestones).

| ID | Type | Verifiable criterion | Owner |
| --- | --- | --- | --- |
| **TS — second code profile (TypeScript/JavaScript)** | | | |
| TS.1 | E | Profile covers the M1.1 list plus ASI, regex vs division, template literals, JSX/TSX, and `.d.ts`/generated/minified exclusions | S |
| TS.2 | E | Hand-derived vectors cover the M1.2 classes plus the TS.1 classes | S |
| TS.3 | E | Two implementations without a shared lexer match the TS.2 expected bytes | I |
| TS.4 | E | Own M3 split, reported separately and not pooled | I |
| **IMG — first non-code profile: images** ([lane 08](research/lanes/08-evidence-review.md)) | | | |
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

- Pushing or publishing anything, including a spec commit for the implementation repository to pin.
- Creating GitHub repositories, and choosing their visibility. Also the Go module path.
- Normative format changes, including promoting the draft extraction, catalogue and report contracts and their vectors from `research/drafts/` into `spec/`, `schemas/`, `profiles/` or `test-vectors/`.
- New diagrams.
- Paid services.
- Corpus acquisition (M3.1).
- The false-alarm budget and its unit (M3.0).
- Whether to omit embedding from the next release, or select a candidate (M2E.0). The M2E.1(c) payload minimum is also approved by the owner.
- The post-hoc image study after M3 (IMG.0 and the protocol in the [lane 06–08 checkpoint](research/research-06-08-checkpoint.md)).
- Also: licence split, hosted CI, the EXT reviewers, whether implementers must be independent people, and the draft contract's pending options (OD-C5).

## How work is accepted

Use one reviewable change per decision or capability. Explain the use case, source support, normative delta, fixtures, measured result and known failures. Update [conformance](spec/conformance.md) whenever supported behavior changes. Run the repository validator and tests. Keep source revisions and implementation dependencies reproducible. Record disagreements as decisions with alternatives and revisit conditions.

Open choices: safe subsets within Go and Rust; representative authorized corpus; operational false-alarm budget; supported trust/key distribution model; and the second implementation/reviewer. None prevents completing this plan, and none should be guessed into a stable standard.
