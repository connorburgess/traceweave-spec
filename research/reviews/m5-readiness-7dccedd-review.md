# Independent M5 readiness review

Reviewed commit: **`7dccedd6389762ea038b4b132a8479436a30f23d`**, branch `m5-readiness`, 2026-11-26. This is the non-author review of that exact tree against ROADMAP.md M5.1, M5.2, M5.4 and M5.5, including M5.1's incorporation of the exact M1.5 rules. The reviewer did not author the reviewed change. The supplied AGENTS.md instructions and the applicable parent AGENTS.md were read. This record changes no gate status.

**Disposition: changes required. None of the four gates is eligible to be marked met on this revision.** Passing inventory checks establishes syntactic coverage, not adequate mapping, justified exclusions or implementation conformance.

## Findings

Severity: **high** blocks the named release gate because an implementer can select an incompatible contract, rely on unsupported conformance, or miss a normative obligation. **medium** blocks the named audit criterion but does not demonstrate a production exploit.

### F1 — High: TypeScript wire version is wrong in the release inventory

Locations: [conformance-matrix.md:24](../../docs/release/conformance-matrix.md#feature--level--implementation), physical line 24; release notes physical line 7 (`docs/release/0.1.0-draft.1-release-notes.md`). Gates: **M5.5**, also **M5.4** release scope accuracy.

The matrix labels `ts-tokens / draft-1` as Recorded for Go, Rust and WASM; the notes group all five profiles as frozen Stage-1 without stating TypeScript's distinct version. The governing [profile](../../profiles/typescript.md) lines 5–9 and §10, [config-ts.json](../../test-vectors/extraction-typescript/config-ts.json), and `ts.json.profileVersion` say **draft-2**, including changed outputs from draft-1. The release's wire-version guidance must explicitly distinguish this profile from the four draft-1 profiles.

Runtime confirmation using Shelf's existing bundled WASM: the canonical TS config with `profileVersion: draft-1` returns `unsupported-config`; the unchanged `draft-2` config extracts `let x = 1;` successfully. Shelf's `src/lib/wasm.ts:167` also selects draft-2. Correct the matrix and enumerate exact profile/version pairs in release scope. The notes' generic phrase alone is not a claim that all versions are draft-1, but it fails to disambiguate the matrix's concrete error.

### F2 — High: minimal-core adapter conformance is attributed to implementations without supporting evidence

Location: `docs/release/conformance-matrix.md:20`; related WASM entries at lines 16–21. Gate: **M5.5**.

The combined “in-toto minimal-core and registration adapter” row says Go/Rust Recorded and WASM Recorded parity scope, citing the specification's 4 accept / 26 reject adapter fixtures. Those fixtures are checked by this repository's Python adapter checker. They do not establish native or WASM reproduction of the minimal-core adapter.

At the matrix's native registration pin `5b9a881`, Rust `crates/tw-reg/src/statement.rs:495` accepts only `PREDICATE_TYPE_REG_DRAFT5`; Go `go/registration/statement.go:413` likewise requires `RegistrationPredicateType`. Neither cited check establishes the distinct `evidence-0.1.0-draft.1` minimal-core form. A concrete probe wrapped the valid envelope/material from `accept-catalogue-core.json` in the otherwise valid registration bundle, removed its time evidence, and supplied a valid local policy to Shelf's WASM `verifyRegistration`: it refused with **status 1, `predicate-type`**. This does not invalidate registration support; it demonstrates why the combined row is misleading.

The pinned `web-wasm-review.md` at `51f29d7` reports only 5 reference cases and 4 registration verify/render cases (including two bundle examples and a simulated-rendering refusal). Its parity test does not run the complete adapter suite, changed catalogue openings, key-event suite or report-link suite. Native registration passing 86/147 fixtures is not evidence that every WASM API surface reproduces them. Split minimal-core from registration, and distinguish sampled WASM parity from complete feature-vector conformance. Mark unsupported/unverified cells accordingly unless an exact pinned test supplies the missing evidence.

### F3 — High: a cited vector does not catch a violation of the mapped MUST

Location: `test-vectors/requirements/requirement-map.json:370–384`, **M5-020**. Gate: **M5.1**.

The radix-literal MUST includes valid radix digits, separator placement and optional `n`; its only cited failing/negative fixture is `ts-err-hex-empty`. I changed only the reference lexer's radix-membership predicate to `False`, retaining empty-body and separator checks. The cited fixture still returned exactly `('error', 'malformed-literal', 4)` in both lexers. Yet `0xG` changed from `('error', 'malformed-literal', 0)` to `('ok', [('number', 0, 3)])`. Thus the cited test does not fail for this violation, as M1.5 explicitly requires. The full vector suite may catch the mutant elsewhere; that does not repair the specific mapping.

Expand the cited IDs to cover the constituent obligations rather than mapping only the easiest rejection. Also audit compound introductions, notably **M5-085** (`spec/trust-policy.md:71–78`): negative lookback alone does not demonstrate all seven fail-closed policy conditions or abort-before-evidence ordering. This review does not claim every compound mapping is defective; the demonstrated M5-020 counterexample is sufficient to block closure.

### F4 — Medium: executable requirements are classified as untestable merely because they are outside output fixtures

Locations: `test-vectors/requirements/requirement-map.json:548` (**M5-030**), `:1047` (**M5-058**), `:1182` (**M5-065**, second clause), `:1377` (**M5-074**, second clause); also M5-046/047/049. Gate: **M5.1**.

M1.5 allows listing MUSTs that *cannot be tested*. The new map instead defines untestable as not observable in recorded JSON bytes. Unknown-option exit 2, private-path refusal/temporary cleanup, canary-free diagnostics, rendering evidence beside its floor with “at the minimum”, and catalogue size-cap refusal all have concrete negative process/UI/boundary tests. A reason saying “requires a process probe” describes a test to map, not an impossibility of testing.

Existing `test-vectors/matching/behaviour-checklist.md` already specifies unknown-option/fault item 42 and diagnostic-canary item 57, as well as private output and cleanup cases. Map such requirements to pinned implementation tests and negative cases (as the existing `implementation-test` kind permits), or provide new test IDs. Genuine asymptotic proofs, constant-time internals, production deployment policy and historical retention obligations can retain reasoned non-fixture classifications. No production audit is implied by this distinction.

### F5 — Medium: picture exclusions remove substantive accessible claim sentences

Locations: `tools/check_readme_claims.py:63–65`, `docs/release/readme-claim-map.md:20`, README.md lines **4, 45, 60, 70**. Gate: **M5.2**.

The non-author **rejects exclusion of alt text**. The long alt attributes contain meaningful claims about local execution, canonical reports, registration/time policy and the embedded-mark workflow. The Figure 3 caption does not cover all the other diagrams' claims. Approve exclusion of picture/source markup, but extract and map alt descriptions or explicitly map each complete description as a compound claim including every assertion.

Adversarial check: replacing “four local steps” in line 45's alt text with “cryptographically proven ownership after four local steps”, and updating only that excluded-text inventory entry, still passed as **73 claims / 59 excluded lines**, without an evidence entry for the new assertion. This is an exclusion-policy failure, not a claim that the checker promised semantic evidence validation.

The other four exclusion categories are approved **for the reviewed README**: 14 heading lines, 8 link-only navigation lines, 7 fenced-code lines, and 10 table heading/separator lines. None of those current table headings adds an independent feature assertion. Prose/list splitting preserves the current assertions; inline version dots and link destinations stay intact, Figure 3's label is retained, and its three caption sentences are mapped. The 31 table data rows can be compound units because every cell is included. This approval does not authorize excluding future substantive heading/table/command claims without review.

### F6 — High: release notes omit already documented unresolved text limits

Location: release notes `docs/release/0.1.0-draft.1-release-notes.md:26–35`, especially line 27. Gate: **M5.4**.

M5.4 requires listing every unresolved limit. ROADMAP TXT.7 explicitly says the **profile and release notes** must list paraphrase, translation, fragments shorter than `k+w-1`, and scripts without spaces if unmeasured. The notes mention TXT.7 but do not list paraphrase, translation or non-space-script limitations; “short inputs” does not state the 15-token text guarantee boundary. The [text profile §13](../../profiles/text.md#13-limits-what-the-profile-cannot-detect-or-claim) also records fingerprint guessability/no confidentiality, ZWSP joining, non-ignorable format-character splitting, hyphenation, normalization gaps and skeleton collisions. These are not covered by a general disclaimer about semantic/model work or calibration.

In particular, “private catalogues” does not convey that anyone who obtains unkeyed fingerprints can test guessed sentences. List these limits with exact source/result references; a link to the complete roadmap is not the gate's required release-note inventory. The embedding omission cites M2E.0 correctly, signing inclusion is explicit, all six M4 gates are recorded met, and the unsigned-detector-only fallback is therefore not required on the roadmap evidence. Those portions pass; they do not cure missing limitations.

## Independent checks and evidence scope

After creating an ignored local virtual environment and fetching the pinned development dependencies, the following all exited **0** on the reviewed source tree (Python 3.14, Node 22.23.2):

- `.venv/bin/python tools/validate.py`
- `.venv/bin/python -m unittest discover -s tests` — **16 tests**.
- `.venv/bin/python tools/validate.py --links-all`
- `.venv/bin/python tools/check_hygiene.py`
- `TW_IMPL_REPO=<existing implementation checkout> .venv/bin/python tools/check_requirement_map.py` — **157 MUST occurrences, 0 syntactically unmapped; 90 testable, 4 implementation-test, 46 untestable, 17 definitional; all 6 external test locators found**. Locator existence is not a new execution of those implementation tests.
- `.venv/bin/python tools/check_release_boundaries.py` — **9/9** negative probes.

Independent added-file probes in both `spec/` and `profiles/` introduced a new unmapped MUST in memory; both were rejected. No source file was changed for these probes. The requirement scanner covers every literal uppercase whole-word MUST in those directories, including quotes and definitions; lowercase obligations and other keywords are outside the exact gate's scope. There is no demonstrated literal-MUST omission.

The inventory also accepted replacing M5-024's checker locator with `checker:test-vectors/registration/check_registration.py:import json` in both evidence lists. This confirms that arbitrary source text can count as a negative fixture; it does not itself show the existing base64 self-test is absent (it exists at checker lines 1802–1811). Human semantic review remains necessary, and stable test IDs would make this audit stronger.

### Stated non-fixture sample

The following **13 entries / 18 untestable clause occurrences** were independently spot-checked against their exact normative passages and inspection boundary. This exceeds the minimum sample of 10 without purporting to certify every implementation behavior.

| Entry / occurrence | Disposition and inspected evidence |
| --- | --- |
| M5-002 / 1 | Selection accounting is distinct from lexical bytes; Python profile's Python-2 discussion supports that distinction. Pipeline omission can nevertheless have process tests; no implementation certification granted. |
| M5-008 / 1 | Explicit-stack/linear-space reasoning needs source review beyond the two deep fixtures; implementation `docs/reviews/py-review.md` records deep indentation probes. Finite probes alone do not prove the asymptotic rule. |
| M5-011 / 1–2 | Full table identity requires derivation/full sweep rather than a handful of token vectors; text profile's pinned table and cross-check sections support the stated boundary. |
| M5-018 / 1–3 | JSX selection/deferral differs from lexical rejection; profile documents the self-closing-tag misread. Requires selection accounting; do not infer it from extractor parity. |
| M5-019 / 1 | Complete Unicode-table equality cannot be established by the one newer-character example; profile gives pinned derivation and scanner differences. |
| M5-025 / 1 | Constant-time behavior and OS randomness are internal properties; no deterministic nonce fixture proves these. Shelf uses WebCrypto and getRandomValues, but this is not a production primitive audit. |
| M5-030 / 1 | **Classification rejected**, F4: usage-error process test is possible; behavior-checklist item 42 exists. |
| M5-044 / 1 | Source/build state is distinct from a plausible provenance field; existing I2 review and behavior checklist supply relevant process evidence, which should be mapped rather than waived. |
| M5-046 / 1 | **Classification rejected**, F4: private-path refusal is a filesystem/process test; exact checklist already exists. |
| M5-058 / 1–2 | **Classification rejected**, F4: region-floor display and minimum labeling can be tested in rendering output. Shelf's unverified cell avoids claiming compliance. |
| M5-065 / 1–2 | Historical exact-byte retention is a lifecycle inspection; size-cap enforcement has a finite boundary refusal test, **second classification rejected**, F4. |
| M5-095 / 1 | Production root selection requires deployment-policy inspection; synthetic fixture acceptance does not establish it. Test-only warnings in policy/fixture documentation are appropriate. |
| M5-099 / 1 | Zero-network verification needs sandbox/tracing; fixture bytes alone are insufficient. Existing WEB.2 review records OS denial for the loader/core; no complete new offline demo was performed here. |

The 17 definitional/quoted occurrences were also checked by category: keyword definitions add no independent algorithm obligation; registration's quoted DSSE base64 rule is mapped locally in M5-024/089; the ESSCertID requirement is backed by the signing-certificate mismatch fixture; A2A/MCP hosted-witness quotations apply to deferred service design and do not establish an included service. No missing local obligation was established from those quotations.

### README evidence and implementation/Shelf comparison

All 73 entries' locators pass exact-quotation checks. Substantive evidence was compared for README-001–029 and README-062–073, plus the profile/maturity and navigation rows against their destination documents. Gate-count claims 29/47 and 21/55 + two negative results match ROADMAP's explicit status lists; extraction/matching parity is supported within the recorded vectors, not arbitrary transformations. Registration's 86 positive / 147 negative figures and adapter 4/26 match their committed inventories and the running checkers. Navigation and licensing assertions can reasonably use the author scope review plus inspection of the actual destinations; an author review is not independent runtime evidence. Some quotations are just section headings (for example README-018), so their supporting section must be read, not treated as evidence merely because the quoted string exists.

The README's “strictly offline” sentence is supportable for validation after dependency fetch; its immediately following code block includes `pip install`, so explicitly separating fetch from offline commands would improve clarity. No zero-network measurement of dependency installation is claimed by this review.

External local snapshots inspected read-only: implementation HEAD **`dcaa0d42e9de63d23aa113d9306134de9b28942c`**, also the matrix's pinned `5b9a881` and `51f29d7` source/review objects; Shelf HEAD **`303ef5a846d368fe293f32efe84477e23fe32d6b`**. These snapshots do not redefine the spec commit being reviewed. Shelf's bundled WASM has **zero imports**; the two TS-version probes and minimal-core refusal used that actual asset. Shelf has local signing, extraction/comparison and verification wrappers, but no independent complete conformance run is supplied here. Its verify wrapper does not expose all low-level auxiliary-file/opening/key-event inputs. Keeping Shelf cells **Unverified** is correct; lack of a code copy in this spec repository does not mean the app lacks those capabilities. Do not promote WASM parity to Shelf flow conformance. No external repository was modified or built.

## Gate-by-gate eligibility

| Gate | Exact criterion assessment | Eligibility / blockers |
| --- | --- | --- |
| M5.1 | Literal inventory complete; minimum independent sample recorded. M1.5's failing-test and negative-per-testable-MUST rules not yet satisfied. | **Not eligible** — F3, F4. |
| M5.2 | Current prose splitting adequate; locators exist; four exclusion categories approved, picture alt exclusion rejected. | **Not eligible** — F5. |
| M5.4 | Embedding omission/decision and signing/M4 prerequisites stated correctly. Required complete limitations inventory is incomplete. | **Not eligible** — F6; coordinate scope correction with F1. |
| M5.5 | Versioned documents and migration notes exist; feature × level × implementation structure exists. Wire-version and conformance cells are inaccurate. | **Not eligible** — F1, F2. |

M5.3 was not attempted and remains separate. No held 48-repository evaluation, corpus acquisition, sublane, push, release publication or gate-status edit was performed. Only this review record is intended for the local review commit. Fixes should be reviewed against their new exact commit before any gate is marked met.
