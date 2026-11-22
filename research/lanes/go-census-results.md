# Go public-code eligibility census

Executed 2026-11-21; stopped after the two pinned repositories. **No current eligibility was established, no whole-function structural shape matched, and the only five primary structural runs were singletons.** The reviewed grammar offers no demonstrated usable sites in this convenience sample. Keep these carriers as synthetic weak baselines; do not proceed to identity framing on these results.

[Scanner and commands](../experiments/go-census/README.md), [manifest](../experiments/go-census/manifest.json), [library aggregates](../experiments/go-census/go-spew-summary.json), [application aggregates](../experiments/go-census/hey-summary.json), [independent checks](../experiments/go-census/verification.json). Per-file count distributions are included in the aggregate files. Downloaded source, archives, detailed digests/byte spans and audit notes remain in ignored `.local/go-census/`; no upstream source excerpts were added to this repository.

## Corpus, provenance and frozen rules

Selected two small historical tagged snapshots from different maintainers: a debugging library and an HTTP load-generator application. This is a defensible bounded convenience sample, not a representative or current-ecosystem sample. All regular `.go` files were inspected recursively; first-party non-generated implementation files form the primary denominator. Test, testdata and vendor classes remain separate. No builds, tests, generators, dependency installations or commands from either candidate ran; only the original standard-library scanner and its synthetic tests were compiled/executed.

| Role / repository | Pinned commit | Acquisition UTC | Upstream license |
| --- | --- | --- | --- |
| Library: [davecgh/go-spew v1.1.1](https://github.com/davecgh/go-spew/tree/8991bc29aa16c548c550c7ff78260e27b9ab7c73) | `8991bc29aa16c548c550c7ff78260e27b9ab7c73` | 2026-11-21 13:11:44.463864 | [ISC](https://github.com/davecgh/go-spew/blob/8991bc29aa16c548c550c7ff78260e27b9ab7c73/LICENSE) |
| Application: [rakyll/hey v0.1.4](https://github.com/rakyll/hey/tree/af177063f85bd935c55f1f2ee59c2898d9654f82) | `af177063f85bd935c55f1f2ee59c2898d9654f82` | 2026-11-21 13:11:45.927833 | [Apache-2.0](https://github.com/rakyll/hey/blob/af177063f85bd935c55f1f2ee59c2898d9654f82/LICENSE) |

Commit pins were resolved with `git ls-remote` before collection; annotated library tag was peeled to its commit. Root license texts/hashes were checked before downloading snapshots. All first-party Go headers identify the corresponding license. Hey also contains vendored Go net/text BSD-3-Clause license files, checked and hashed separately; vendor code was excluded from primary eligibility. Licenses/paths/hashes, archive hashes and acquisition URLs/times are recorded in the manifest. Archive SHA-256 values are `69fb08bf0b0d09d1d40ed1c010fc1c5f65ed3db3f8e6b2021eddcd8ec9c50394` (library) and `fb48701e6840c10f140873b7d8e9da842bbd3af628405e720f631be385707ce7` (application).

The scanner was frozen at `2026-11-21T13:10:46Z`, SHA-256 `03c2e9343e8522324d8e203427fc952647dfae09d59bb4f3da4820a6cb6e2a5f`, before either scan. Both outputs bind that same hash. The rule inventory separates:

- **Exact current eligibility:** unsupported because complete source/build/scope/type preconditions have not been established by this AST-only study. `ExactEligible=0` means zero demonstrated sites, not proof that no implementation could mark these sources. Fixed function/package and file-boundary conditions are recorded as additional, nonexclusive gates. There is no invented filename requirement: `fixture.go` was only the harness parser label.
- **Whole-function shape:** the reviewed parameterless, non-method, nongeneric literal-binding/array-return syntax, with fixed function/package names ignored for this structural measurement only. Comments/imports/build constraints and scope/type validity still do not become accepted. This isolates substantive syntax scarcity from names/boundary exclusions.
- **Potential runs:** maximal adjacent direct block statements with one lower-case identifier `:=` one nonnegative decimal integer literal within signed 32 bits. No calls, alternate literal spellings or multi-bindings count. They can occur within larger methods/control flow. Names/dependency/uses/freshness/scope/effects are not analyzed, so they are not markable sites. Singletons may motivate a name-carrier investigation; order needs at least two independently movable bindings.

## Measured counts

Functions mean declared functions/methods; anonymous functions are counted separately (14 primary: one library, 13 application).

| Corpus class | Files parsed / selected | Bytes | Declared functions | Exact demonstrated eligible | Whole-function shape matches | Potential runs: singleton / >=2 |
| --- | --- | --- | --- | --- | --- | --- |
| Library primary | 8/8 | 69,266 | 63 | 0/63 | 0/63 | 2 / 0 |
| Application primary | 6/6 | 29,184 | 32 | 0/32 | 0/32 | 3 / 0 |
| Library tests | 9/9 | 125,381 | 75 | 0/75 | 0/75 | 6 / 0 |
| Library testdata | 1/1 | 3,284 | 7 | 0/7 | 0/7 | 0 / 0 |
| Application tests | 2/2 | 5,405 | 9 | 0/9 | 0/9 | 0 / 0 |
| Application vendor | 65/65 | 1,773,777 | 925 | 0/925 | 0/925 | 16 / 0 |

Both repositories, including zero-result classes, remain in denominators: 91/91 Go files parsed, 2,006,297 bytes and 1,111 declared functions overall. Primary total: **14/14 files, 98,450 bytes, 95 functions, five singleton runs, zero >=2 runs**. No generated first-party files were identified. Ten generated-header files are nested in the 65-file dependency class, counted by independent overlap verification rather than silently treated as first-party code. There were zero unreadable files, parser failures, filesystem traversal failures, symlinks or skipped special archive members.

Exclusive substantive shape refusals are signature (library 62, application 29) and result shape (library one, application three). They account for all 95 primary functions even after name/package relaxation. Nonexclusive exact-boundary gates additionally affected all 95 for function name, comment/import/single-file shape and unestablished preconditions; package-name mismatch affected 89/95. Do not add gate counts together. Build constraints occur in three primary files; unsafe imports in two. Two application filename configurations remain unresolved; underscore filename flags are conservative observations, not target selection. All platform alternatives were parsed, not built or merged into a capacity estimate.

No raw state count, log2 capacity, formatter survival or normalization survival is assigned to potential runs. Exact eligibility was not established, and the five singletons cannot encode order. Currently demonstrated authenticated payload bits are zero; key/identity/framing/synchronization/redundancy costs and dependable capacity remain unavailable. No rewrites or candidate behavior checks were performed.

## Audit and independent checks

Manual audit covered all five primary potential runs and seven primary refusal samples: first two per observed category per repository (the library has only one result-shape refusal). The library's two singleton counters participate in mutable pointer traversals; the application's candidates initialize a mutable histogram maximum, a mutable percentile index and a bucket count used with allocations/computation. These surrounding bodies differ substantially from the reviewed function grammar. The audit establishes syntax/classification observations, not effects/scope safety. No exact accepted units existed to audit.

The available Unicode-offset control was audited in the application's report source: the first run begins at byte 5,884 but code-point index 5,882; the second at byte 6,281 versus code-point index 6,279. Exact spans/file digests and deterministic sample choices stay local. Boundary/license headers and exclusion classifications were also checked. Tests additionally exercise a Unicode prefix, parser failure, generated/test/vendor/testdata separation and nontraversal of a symlink pointing outside the synthetic scanner fixture.

Independent archive/file/byte inventories agreed with all 91 files and source digests, including content comparison to archive entries. A line-oriented declaration inventory agreed exactly with primary and test counts. Vendor regex counting found 927 apparent function lines versus 925 AST declarations; the two extra lines were manually confirmed inside a raw-string generator template, not real declarations. That generator was not run. Three original scanner tests passed on `go1.27.3 darwin/arm64`; dependency retrieval was disabled with `GOPROXY=off`, `GOSUMDB=off`, `GOTOOLCHAIN=local`, `GOWORK=off`. This is not an OS-level network-isolation claim.

## Decision and limits

Stop this census at the two repositories. The source-only unknowns alone prevent exact acceptance, but the independent absence of any full-function shape and >=2 literal run also shows that merely relaxing fixed names would not make the present grammar useful here. Recommend rejecting the present whole-function grammar as a practical carrier for these snapshots, while retaining its synthetic counterexamples. Do not broaden syntax simply to obtain a nonzero result or begin payload framing from singleton counts.

A future name-carrier proposal would require a separately reviewed scope/type/build boundary, capture/collision and all-use analysis, source-observer restrictions, local quality constraints and fresh removal/transplant tests. This report adopts no extension. These convenience snapshots are excluded from any future held-out accuracy corpus. No detection, false-positive, ownership, license-rights determination, binary-survival or population-capacity claim follows. Existing shared work was preserved; no private apps, normative files, diagrams, commits or pushes were changed.
