# Go fragment, alignment and transplant results

Executed 2026-11-21. [New regression harness](../experiments/go-carrier/fragment_test.go), [full validation log](../experiments/go-carrier/fragment-validation.log), [previous carrier results](go-carrier-results.md). Whole-function source copies recovered localized raw states in synthetic unrelated hosts. Incomplete excerpts and duplicate matching anchors abstained. Same-context signal-only transfers also recovered: this is an explicit limit of raw-state evidence, with no identity or host-ancestry inference.

## Implemented boundary

Reuses the existing literal-binding/return-array grammar, `go/types` binding resolution, lexicographic declaration-order mapping and role-specific two-name codebook. New cases use n=3, order raw state 5 of 6, and names raw state 7 of 8; shortened functions use n=2. These are test states, not identity payloads or a selected production carrier size. Eight setup embedding requests (two donors, two same-context transfers, two other-context transfers, two shortened runs) changed source and validated; none was already matching or refused. Host construction itself copies/renames function source or independently regenerates recipient syntax; it is not an additional embedding request.

The new extractor reads one in-memory `package main` file, with no imports or package-level non-function declarations. It parses and type-checks the full host before inspecting functions individually. Unsupported helper functions are counted/skipped. Supported functions retain the old grammar; only their top-level function name may differ. Ordinary comments outside functions allow a non-ASCII prefix control. Comments inside the function and raw build/compiler/line directives are unsupported. There is no package/configuration loader, free-standing fragment repair, import resolution or source-observer guarantee.

For grammar checking only, each function is printed into the existing fixed-name wrapper. Matching requires exactly the reference's vector of literal values in return-role order. All matching anchors are collected **before raw decoding**. Multiple matching functions cause `ambiguous_anchor`, even if only one uses decodable codebook spellings. A unique name-carrier candidate additionally checks alternatives against resolved objects throughout the original host: unrelated function identifiers can cause `host_codebook_collision`. Wrapper normalization therefore cannot conceal this collision.

Each recovery reports one function-level state plus definition-local symbols: return-role index and source declaration position for order, or return-role index and binary alternative for names. Order positions are not independently encoded bits. Abstentions expose no selected state or symbols; ambiguous cases retain all matching intervals. The result is source-local evidence only.

All coordinates are half-open **UTF-8 byte offsets in the original candidate**, using its AST and `FileSet.PositionFor(..., false).Offset`. No wrapper/printer offsets are emitted. [Go token position API, go1.27.3](https://pkg.go.dev/go/token@go1.27.3#FileSet.PositionFor). The wrapper is not used to recover missing declarations or infer omitted symbols.

## Main cases and denominators

One query per family per row, always against the original three-role reference:

| Case | Order result | Names result |
| --- | --- | --- |
| Whole copied function beside unrelated helper | state 5 | state 7 |
| Renamed/relocated function after Unicode prefix | state 5 | state 7 |
| Changed unrelated host helper | state 5 | state 7 |
| One binding deleted, return still references it | host type error | host type error |
| Bare declaration excerpt without package/function | host parse error | host parse error |
| Reconstituted two-role subset function | no anchor | no anchor |
| Two matching functions, one outside names codebook | ambiguous anchor | ambiguous anchor |
| Changed function literal values to 11,12,13 | no anchor | no anchor |
| Independently constructed same-task function | state 0 | raw unavailable: names outside codebook |
| Signal-only transfer onto independent same-context function | state 5 | state 7 |
| Signal-only transfer onto values 11,12,13 | no anchor | no anchor |
| Unrelated host function occupies `roleab` | state 5 | host codebook collision |

Results: order 6/12 recoveries and 6/12 abstentions; names 4/12 recoveries and 8/12 abstentions. Combined: **10/24 recovered, 14/24 abstained**, with zero wrong raw states among the 10 recovered decisions. These fractions describe deliberately mixed cases, not a recall estimate. All 24 extraction inputs remained byte-identical. Four queries intentionally supplied non-compilable/incomplete material; their parse/type failures are included in the query denominator.

The 20/24 parse/type-valid host queries contained 32 function declarations: 22 satisfied the carrier grammar and 10 were skipped helpers. This constructed eligibility count is not an application capacity estimate. A shortened run can satisfy the grammar but fail reference alignment. No partial-symbol output was attempted for unsupported fragments.

Localization checks passed for 10/10 recovered function intervals and 30/30 emitted definition intervals. The Unicode prefix is 80 UTF-8 bytes but 70 code points. In that candidate the order function interval was `[80,183)` and the names function interval `[80,181)`; emitted definition intervals were respectively `[104,110)`, `[117,123)`, `[130,136)` and `[103,109)`, `[116,122)`, `[129,135)`. Tests check exact original function substring boundaries, definition text, role/value association and raw symbol meaning. These observations establish the tested whole-function/definition scope; they do not establish localization recall for arbitrary fragments.

Two additional queries use the other-context recipients' **own** references and recover state 5/state 7 (2/2). The earlier no-anchor outcomes are reference-alignment decisions, not transplant prevention. The same-context transfer constructs an independent recipient with its own locals, then applies only the donor's raw rank/digits through the public mapping. With this tiny grammar, names can regenerate the same carrier syntax; source similarity cannot determine the construction history.

Twelve further guard queries all abstained: nine boundary/zero-capacity cases, two reversed duplicate-anchor cases and one invalid reference. Across the two primary duplicate cases and two reversed cases, ambiguity occurred 4/4 times, without selecting the first or the decodable anchor. Total new extraction invocations are 38: 24 main + 2 own-reference + 12 guards. Identity, wrong-key/identity, false alerts and ownership metrics remain unavailable. Dependent synthetic cases cannot justify rare-event bounds.

## Validity and actual execution

The experiment distinguishes valid host construction from behavior-preserving attacks. The missing-binding/excerpt cases are intentionally invalid/incomplete source (4/24 queries); they were never executed. The shortened/literal-changed functions are valid generated programs but do not preserve the original function's return contract. They are alignment controls, not counted as successful valid evasion. Same-context transfers and independent same-task controls return the same arrays, but raw decoding still carries no attribution meaning.

Only trusted fixture generators feed the compile step. The extractor itself invokes no command, callback or candidate execution. All declarations from the 20 well-formed generated hosts were combined, with unique top-level function names, into a 4,511-byte executable package. It compiled and passed **22/22 known return-array checks**, including both functions in duplicate hosts. Original hosts had already passed complete-host type checking. There is no claim of runtime equivalence for unrelated arbitrary Go functions or identical compiled artifacts.

During development, the directive regression caught use of `CommentGroup.Text`, which removes directive comments. The guard was corrected to inspect raw comment tokens and covered with build/compiler/line tests. [Go AST API, go1.27.3](https://pkg.go.dev/go/ast@go1.27.3#CommentGroup.Text). An initial test invocation from repository root also failed because the experiment is a separate module; the commands below use its directory. Subsequent targeted and full runs passed.

## Reproduction and limits

Toolchain/formatter: `go1.27.3 darwin/arm64`, module language `go 1.27`, `CGO_ENABLED=0`, `GOTOOLCHAIN=local`, empty `GOFLAGS`/`GOEXPERIMENT`, no custom tags. Only standard-library tooling and generated fixtures were used.

```sh
cd research/experiments/go-carrier
env CGO_ENABLED=0 GOTOOLCHAIN=local GOFLAGS= GOEXPERIMENT= go test -v -count=1 -run 'TestSyntheticFragmentsAndTransplants|TestSyntheticHostAlignmentGuards' ./...
env CGO_ENABLED=0 GOTOOLCHAIN=local GOFLAGS= GOEXPERIMENT= go test -v -count=1 ./...
```

The recorded full run prefixed the second command with `/usr/bin/time -l` and redirected both streams to `fragment-validation.log`: all six top-level tests passed, including the four prior tests. New main experiment: 0.520136 s including aggregate compilation/execution. Full command: 2.71 s wall time, package time 2.193 s, maximum resident set size reported as 120,717,312 bytes. One timed invocation, shared machine/caches, no per-phase memory measurement or stable runtime claim. Previous exhaustive carrier denominators and compiled checks also remained passing (62 completed raw states; 248 behavior variants).

The next decision is whether useful fragment support can be specified without ambiguous alignment or silent reference completion. Current support stops at a uniquely aligned, complete narrow function. Content/context binding and identity authentication, partial-run synchronization, realistic authorized-corpus eligibility, full-search calibration and source/build boundary expansion remain blockers. Public algorithms and local/private verification remain compatible with this harness; keys, identities, fingerprints and a combined detector are not implemented here. No private apps, normative files, diagrams, commits or pushes were changed; pre-existing work was preserved.
