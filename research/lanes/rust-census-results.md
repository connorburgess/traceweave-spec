# Rust public-code eligibility census

Completed 2026-11-21, source inspection only. **No exact eligibility was established, and the frozen narrow potential patterns found zero sites in both repositories.** This convenience sample does not reject integer-spelling or statement-order carriers generally. It gives no usable capacity evidence for the current reviewed profile and does not justify designing its identity payload.

Published artifacts: [pinned manifest](../experiments/rust-census/manifest.json), [scanner freeze and rules](../experiments/rust-census/freeze.json), [aggregate counts/provenance and file distribution](../experiments/rust-census/aggregate.json), [scanner](../experiments/rust-census/scanner.py), [acquisition helper](../experiments/rust-census/acquire.py), [summary helper](../experiments/rust-census/summarize.py), [regression tests](../experiments/rust-census/test_scanner.py). Downloaded code, license text, complete tree inventories, token offsets and audit offsets remain under ignored `.local/rust-census/`; no upstream source excerpts are published here. Existing research files were preserved.

## Selection, license and provenance

These small projects provide a numeric library and a terminal application under different maintainer/project owners. Selection is for tractable source review, not representativeness or a held-out evaluation set.

| Repository | Kind | Pinned commit | Acquisition UTC |
| --- | --- | --- | --- |
| [dtolnay/itoa](https://github.com/dtolnay/itoa/tree/9339ca99a43c550b5ee36e2afe524d1c90413461) | Integer-formatting library | `9339ca99a43c550b5ee36e2afe524d1c90413461` | `2026-11-21T13:12:30.445877+00:00` |
| [sharkdp/hexyl](https://github.com/sharkdp/hexyl/tree/6ecc29b9c8c84d08a7e860f7f69c22b113b480ea) | Command-line hex viewer | `6ecc29b9c8c84d08a7e860f7f69c22b113b480ea` | `2026-11-21T13:12:36.252557+00:00` |

Upstream root license files were read and SHA-256 checked before source collection: itoa [MIT](https://github.com/dtolnay/itoa/blob/9339ca99a43c550b5ee36e2afe524d1c90413461/LICENSE-MIT) and [Apache](https://github.com/dtolnay/itoa/blob/9339ca99a43c550b5ee36e2afe524d1c90413461/LICENSE-APACHE); hexyl [MIT](https://github.com/sharkdp/hexyl/blob/6ecc29b9c8c84d08a7e860f7f69c22b113b480ea/LICENSE-MIT) and [Apache](https://github.com/sharkdp/hexyl/blob/6ecc29b9c8c84d08a7e860f7f69c22b113b480ea/LICENSE-APACHE). Their pinned Cargo declarations are respectively `MIT OR Apache-2.0` and `MIT/Apache-2.0`; both declare edition 2021. Full license/Cargo hashes are in the manifest/aggregate. No nested license files or submodules were listed in either complete tree. This checks this sample's upstream declarations, not every dependency's license; dependencies were not acquired or redistributed.

The first collector attempt stopped before hexyl source because its Cargo license spelling differed from the expected string. After reviewing the pinned metadata and already-verified license files, only the collector expectation was corrected. Scanner/rules stayed unchanged and no census had run; the freeze records this acquisition event.

GitHub's complete pinned recursive trees supplied the independent source inventory. Rust files under `src/`, `tests/`, `benches/`, `examples/`, and `fuzz/` were selected; vendor/generated/target/third-party paths and symlinks would be excluded. All 12 Rust paths in these two trees fell inside the selected roots. Each download was checked against its Git blob SHA-1 and size, then retained with SHA-256. Assets/non-Rust fixtures and dependency sources were not collected. No generated-banner, symlink or other-Rust exclusions were encountered. A first-ten-line generated-banner heuristic is an exclusion aid, not certification of first-party provenance.

Inventory SHA-256: itoa `05c334ba661189bcdae071d73849cbaf30629af2bacb0c092716028c7c280a71`; hexyl `e4648ea1e3899d8c9949f34254229a695e148f08f38b2c9db3c9e955f37cf3ae`. Raw tree and scan digests are retained in the aggregate. Reacquisition preserves pinned source bytes but produces a new acquisition timestamp/inventory digest.

## Frozen rules and results

Scanner SHA-256, frozen before collection and both scans: `e31b9372ca21c03c10f834bd979c53156229038019d18a65e5b8ef8f85c2cdc1`. The imported reviewed carrier hash is `8354dbc8a5210ed10e8517e863452f63ee7336ca42785048baccc8f97f7afa05`. The scan refuses mismatched frozen revisions. No scanner widening occurred after seeing results.

The scanner removes comments, nested block comments and opaque normal/raw/byte strings and characters from token observations. It counts **lexical `fn` keyword tokens**, including tokens inside macro bodies, traits and types; it does not parse Rust functions, expand macros, resolve names/types, evaluate cfg or establish effects. Rust parsed-function counts are unavailable. An independent raw function-definition-like line heuristic also found 20 itoa and 123 hexyl lines, matching total lexical counts here; neither heuristic validates the other as a parser.

Two exact-current barriers are separate:

1. All 12 inspected files fail the reviewed **whole-file grammar shape**, which requires the fixed synthetic function/local names and literal-only body. This was checked separately from build assumptions.
2. Source/build-observer preconditions remain unestablished for both repositories and all selected files. `exact_eligible=0` records **no eligibility established** under that unknown boundary, not proof that marking is impossible. Absence of a root `build.rs` in either tree does not establish absence of dependency proc macros or other source observers.

Potential-only patterns are much narrower than general numeric opportunities: canonical in-range decimal `u32` spelling tokens with at least two digits; explicitly annotated `let name: u32 = <canonical literal>;` declarations (including single-digit values); and token-adjacent runs of two or more such declarations. They carry no scope, purity, macro, borrowing, Drop or source-observer safety claim. General unsuffixed/inferred integers, other types, floats and radix forms are excluded. Broader number-token counts are not alternative capacity counts.

| Stratum | Files inspected / selected | Bytes | Lexical `fn` tokens | Number-like tokens | Potential spelling / declarations / runs | Exact grammar shape / established eligible files |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| itoa `src/` | 2/2 | 18,028 | 16 | 138 | 0 / 0 / 0 | 0 / 0 |
| itoa tests | 1/1 | 1,310 | 2 | 13 | 0 / 0 / 0 | 0 / 0 |
| itoa benches | 1/1 | 1,193 | 2 | 4 | 0 / 0 / 0 | 0 / 0 |
| itoa fuzz source | 1/1 | 1,350 | 0 | 0 | 0 / 0 / 0 | 0 / 0 |
| hexyl `src/` | 5/5 | 85,748 | 75 | 312 | 0 / 0 / 0 | 0 / 0 |
| hexyl integration tests | 1/1 | 50,821 | 47 | 9 | 0 / 0 / 0 | 0 / 0 |
| hexyl example | 1/1 | 692 | 1 | 31 | 0 / 0 / 0 | 0 / 0 |

Totals: 12/12 files inspected, 159,142 bytes, 143 lexical `fn` tokens and 507 number-like tokens. Unreadable/UTF-8/lexical failures: **0/12**. Every file's grammar refusal is `outside whole-input function grammar`; parser failures are not a metric because no Rust parser ran.

The `src/` stratum is **not production-only**. Hexyl's `src/tests.rs` contributes 5,996 bytes, five lexical `fn` tokens and 40 numbers, and its `src/lib.rs` also has inline-test markers. Removing only that dedicated test file leaves four hexyl source files, 79,752 bytes and 70 lexical `fn` tokens, still including inline tests. Test/cfg markers are published per file; no claim of complete test-region separation follows. The distribution includes both zero-result repositories and every auxiliary file.

There are zero established independent runs/sites from which to report factorial/order or binary/spelling capacity. Demonstrated authenticated payload bits remain zero. No overlapping potential counts were added; no formatter or normalization survival was measured or inferred from this census. The previous synthetic normalization failures remain separate evidence.

## Audit and reproducibility

Fixed manual sample: lexically first/last `src/` paths and first auxiliary path per repository: itoa `src/lib.rs`, `src/u128_ext.rs`, `benches/bench.rs`; hexyl `src/colors.rs`, `src/tests.rs`, `examples/simple.rs`. Review covered the single observed grammar-refusal category, unknown boundary, test separation, macro/cfg/unsafe exclusions and ordinary effectful/typed code outside the literal-only grammar. No accepted potential sites existed to audit; positive-pattern behavior is covered by synthetic scanner tests. A separate raw-text suffixed-decimal-`u32` search found zero matches across all 12 files, agreeing with the narrow spelling result without implying anything about unsuffixed literals.

Actual Unicode-offset samples in itoa `src/lib.rs` and hexyl `src/lib.rs` were checked against original bytes: the `fn` slices matched and character offsets differed. File hashes and exact offsets remain in local `audit-offsets.json`, with no source excerpt published. Independent filesystem enumeration matched all 5/5 itoa and 7/7 hexyl tree-listed downloaded files and their 21,881/137,261 byte totals. The coordinator independently reran both frozen scans and confirmed the primary counts.

From repository root, with Python 3.11+ (executed with Python 3.14.6):

```sh
git check-ignore -v .local/rust-census/ignore-probe.rs
python3 -m unittest discover -s research/experiments/rust-census -p test_scanner.py -v
python3 research/experiments/rust-census/acquire.py --manifest research/experiments/rust-census/manifest.json --freeze research/experiments/rust-census/freeze.json --local-root .local/rust-census
python3 research/experiments/rust-census/scanner.py --root .local/rust-census/itoa --freeze research/experiments/rust-census/freeze.json --output .local/rust-census/itoa/scan.json
python3 research/experiments/rust-census/scanner.py --root .local/rust-census/hexyl --freeze research/experiments/rust-census/freeze.json --output .local/rust-census/hexyl/scan.json
python3 research/experiments/rust-census/summarize.py --local-root .local/rust-census --manifest research/experiments/rust-census/manifest.json --output research/experiments/rust-census/aggregate.json
```

Acquisition and scanning reject absolute/parent paths and symlink components, including ancestors; no symlinks are traversed. Ignore checks confirmed `.gitignore`'s existing `.local/` rule covers both source trees and local audits. Only the original scanner/collector, own synthetic tests and repository validators ran. **No candidate builds, programs, tests, build scripts, macros, formatter, dependency installation or upstream commands were executed.**

Validation completed: all eight census regression tests passed; the repository validator and all six contract tests passed. Frozen scanner/carrier/manifest/collector digests were checked again after reporting; the two scans used the same scanner revision.

Recommendation: reject the current fixed synthetic grammar as a deployable carrier for these samples and stop this bounded census. Its zero result combines a deliberately unsuitable whole-file boundary with real scarcity of its explicit suffixed-`u32` patterns; it is not a conclusion about broader Rust marking. Any broader profile would require a new safety argument and a separately frozen study before identity framing, not reinterpretation of these potential counts as markability. No robustness, false-alert, ownership or legal-rights conclusion follows.
