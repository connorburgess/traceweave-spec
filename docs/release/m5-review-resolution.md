# M5 review finding resolutions

Author disposition of [non-author review `4d4e98d`](../../research/reviews/m5-readiness-7dccedd-review.md), based on `67f7b5d` including its deferred CI signing/trailer roadmap addition. This record requests a new exact-commit review; it does not close a gate. The roadmap addition is preserved with no implementation. No held M3 corpus/evaluation, acquisition, push or delegated lane was used.

## F1 — TypeScript release wire version

The matrix and notes now enumerate `go-tokens/draft-1`, `rust2024-tokens/draft-1`, **`ts-tokens/draft-2`**, `py-tokens/draft-1` and `text-plain/draft-1`. Migration guidance explicitly rejects reinterpretation of TS draft-1 output. `ReleaseRequirementTests.test_ts_draft1_is_not_the_frozen_wire_version` validates the committed draft-2 configuration with the real TypeScript checker and requires the otherwise identical draft-1 configuration to fail. Authority: [config-ts.json](../../test-vectors/extraction-typescript/config-ts.json) and [profile](../../profiles/typescript.md).

## F2 — Adapter and WASM conformance overstatement

The [matrix](conformance-matrix.md) separates minimal-core restricted statements/adapter from registration-draft-5. The 4/26 adapter fixtures are Python checker evidence; native minimal-core coverage is unverified, and the tested WASM registration API refuses the minimal form as `predicate-type` per the independent F2 probe. Native 86/147 registration fixture reproduction is not applied to the minimal-core form.

WASM entries now distinguish the pinned `51f29d7` review's full stated extraction/record/catalogue/matching vector cases from **5 reference cases and 4 verify/render cases**. Changed-opening adversarial probes are labelled samples; full WASM opening, key-event, report-link and adapter suites remain unverified. Shelf remains unverified for complete flows; capability absence is not inferred. The review/source objects at implementation `51f29d7` and `5b9a881` were read without modifying that checkout. No new WASM/full adapter parity is claimed. Release notes use the same narrower language.

## F3 — Radix and compound-policy failing-test mappings

M5-020 now cites a complete radix oracle: **48 malformed cases** cover all six prefixes, invalid digits, empty runs, separator positions and suffix errors; **12 valid cases** check separators and number/bigint classes. Seven one-rule lexer mutants are killed. The reviewer’s radix-membership mutant still accepts the old `0x` negative but fails the new `0xG` case, explicitly reproduced by the mutation test.

M5-085 now maps all seven policy-refusal categories, not just negative lookback. **35 malformed policy variants** cover integer constraints, all recovery fields, hint lists, root/confirmation/checkpoint fields and UTC time; **five strict-JSON negatives** cover duplicate/escaped-collision keys and nonfinite values. Each malformed policy is given to the actual `check_result` with evidence file access trapped: continuing past policy validation fails the test. These tests found that calendar-invalid times passed regex-only checks; the fixture checker now parses verification/recovery timestamps as actual UTC dates before evidence access and enforces production Bitcoin checkpoint/confirmation shape even when `headerFile` is absent. Historical explicitly simulated placeholder fixtures retain their labelled test-only exception. Compound opening, producer-hint and evidence-refusal introductions also cite their executable subrequirement tests.

Expanded-map references now use an explicit [checker-test registry](../../test-vectors/requirements/checker-tests.json) or AST-resolved `unittest` IDs. The reviewed extraction map retains its existing format. Replacing a release reference with arbitrary checker source text (`import json`) or a nonexistent unittest method is rejected by dedicated regression tests. Locator existence remains distinct from semantic adequacy; the reviewer must still assess the mappings.

## F4 — Executable process, display and size requirements

No testable requirement was changed to untestable. Nineteen former inspection-only occurrences now have fixture/adaptor or pinned process tests. The complete inventory remains **157 occurrences, 0 unmapped**: **100 testable, 13 implementation-test, 27 inspection-only, 17 definitional/quoted** (including the unchanged extraction map).

- Unknown options/faults, private-path refusal, stale-temporary cleanup, provenance/build stamping and canary diagnostics map to concrete negative Go/Rust tests and numbered process checklist items at implementation `5b9a881`. Each implementation-test clause now lists explicit negative cases. Historical byte retention, asymptotic/internal properties and open-ended semantic/deployment judgements retain stated inspection boundaries.
- The new [native probe](../../tools/check_native_m5.py) also executes six targeted negative process cases per caller-supplied native binary: unknown options, unknown-key diagnostics, record-build diagnostics, source-text diagnostics, private-path refusal and stale-temporary cleanup. It does not build, fetch data or run evaluation.
- Size/resource tests exercise the Python registration checker itself: catalogue commitments accept the local 1 MiB boundary and refuse one byte over; hashing uses 64 KiB reads, with a guarded stream that kills unbounded reads. The checker uses that streaming helper for artifact verification and enforces the catalogue cap on links too. This is specification-checker coverage, not new Go/Rust resource certification.
- Region display tests have an explicit text-output fixture adapter. Five violating renderings omit a region, separate evidence from its floor, misstate unsuppressed evidence/floor or drop “at the minimum”. Selector fixtures similarly reject missing/duplicate input accounting and ordinary lexical rejection of JSX-in-JS. These are executable conformance oracles that can reject violating outputs, not claims that a product renderer/selector or Shelf is connected to the adapters.
- A real report-link checker probe accepts a differently serialized wrapper while rejecting use of its wrapper hash as body identity. Production placeholder outcomes are separately required to carry no counted time.

### Newly executed native evidence

Source snapshot: implementation **`5b9a881`**, exported read-only with `git archive` into a temporary scratch directory. Builds used local Go 1.27.3 and Cargo 1.97.1, `GOPROXY=off`, `GOTOOLCHAIN=local`, `--locked --offline`; dependencies were already cached. No existing implementation worktree or spec pin was changed. No OS-denied network run is claimed for these new builds/tests.

| Suite | Exact test scope | Result |
| --- | --- | --- |
| Go CLI | `TestPrivateDefault`, `TestFaultInjection`, `TestProvenanceCommitRule`, `TestBodyOnlyAndCommitRequired`, `TestCheckoutDestinationRefused`, `TestVersion` | 6/6 passed, no skipped tests |
| Go storage/schema | `TestCheckDestination`, `TestTemporaries`, `TestErrorsDoNotEchoKeys` | 3/3 passed |
| Rust CLI integration | `build_time_provenance`, `version_json_of_a_plain_build`, `three_faults_keep_previous_catalogue`, `no_files_under_checkout_and_expected_digest_at_private_default` | 4/4 passed |
| New raw-process probe | `tools/check_native_m5.py` against Go built from the archive and Rust `target/debug/traceweave` built by the integration tests | Go 6/6, Rust 6/6 passed |

Reproduction after exporting that pin to `$M5_SCRATCH` (no acquisition):

```sh
# Inside the exported go/ directory:
GOPROXY=off GOTOOLCHAIN=local go test ./cmd/traceweave-go ./internal/store ./internal/schema -run 'Test(FaultInjection|PrivateDefault|CheckoutDestinationRefused|ProvenanceCommitRule|BodyOnlyAndCommitRequired|Version|CheckDestination|Temporaries|ErrorsDoNotEchoKeys)$' -count=1 -v
# Inside the export root:
CARGO_NET_OFFLINE=true cargo test --locked --offline -p traceweave --test storage --test provenance
# Build Go from exported go/; Rust binary is built by the integration suite:
GOPROXY=off GOTOOLCHAIN=local go build -o ../target/m5-traceweave-go ./cmd/traceweave-go
# From this spec checkout:
python tools/check_native_m5.py --go "$M5_SCRATCH/target/m5-traceweave-go" --rust "$M5_SCRATCH/target/debug/traceweave"
```

Broader pinned Rust checklist items (including nested/dirty build variants) and the skill canary transcript suite were inspected and mapped, but **not rerun as complete suites**. `TW_IMPL_REPO` verifies those exact source locators; it is not execution evidence. The new native probes do not close M5.3 or certify all process behavior.

## F5 — Accessible diagram claims

All four complete `img alt` descriptions are now separate compound claims, including every assertion. The HTML parser decodes attributes before the picture-markup exclusion is applied. Updating only the excluded-text inventory after inserting the review’s “cryptographically proven ownership” assertion still fails because the mapped alt claim changes. This exact bypass is a regression test.

The [claim map](readme-claim-map.md) now has **77 mapped units**: 42 prose sentences/fragments, 31 table data rows and 4 alt descriptions, with zero unmapped. There are 59 source-line markup/navigation/code exclusions; four markup lines also supply the separately mapped descriptions, so their alt content is not excluded. The old review approved the other four categories for that exact README, not for arbitrary future substantive headings/tables/commands. Re-review of the revised policy/inventory remains required. README also separates dependency fetch from the offline validation commands.

## F6 — Complete text-limit inventory

The notes now explicitly enumerate every bullet in [text profile §13](../../profiles/text.md#13-limits-what-the-profile-cannot-detect-or-claim), with exact vector/result/source references: unmeasured paraphrase and translation; the 15-token guarantee boundary; non-space scripts; repeated-structure ambiguity; distractor intervals; ZWSP joining; non-ignorable format splitting; line-end hyphenation; NFKC typography gaps; Markdown deviations; skeleton collisions; common phrases/boilerplate; no rights/direction, calibrated-rate or absence inference; unkeyed-fingerprint guessability/no confidentiality; and no embedded text mark. The 11-file synthetic counts remain explicitly bounded rather than detection-rate claims.

## Validation and re-review request

All required checks passed with the pinned development environment: `tools/validate.py`, `tools/validate.py --links-all`, unittest discovery (**28/28 tests**) and `tools/check_hygiene.py`. The requirement checker also passed with `TW_IMPL_REPO` set to verify every mapped external source locator; this is not a complete external-suite execution. The new requirement suite also runs through the validator. The roadmap and all four M5 gate statuses are unchanged. Request non-author re-review of the new fixes commit, including adequacy of the new process and fixture-adapter mappings, the alt exclusion policy, scope cells and full limit inventory.
