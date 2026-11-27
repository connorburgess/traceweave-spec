# WEB.4 synthetic demonstration preparation

Status: **author fixture evidence for independent review**, 2026-11-27. Base spec `7e329055d75a31f4bfd22e14480e0a46ea582cfa`. This package resolves native outcomes for the six planned D recipes in the [candidate protocol](../web6-baseline-protocol-v1/README.md#6-r-commit-aware-cases-and-separate-d-scope), plus two distinct controls. It does not edit that protocol/ledger, run WEB.6 performance/baseline/freeze/conformance work, implement a testing page, or close WEB.4. All existing gates and candidate budget decisions remain unchanged.

## Measured cases

The same committed extraction/comparison bytes apply to every case: `go-tokens` draft-1, k=5, window=4; `minRegionDistinctHashes=2`, mergeGap=4, no suppression. These are the existing pinned matching configurations, not thresholds chosen to force misses. Names, source vector IDs, exact source-file identities and sample/transformed hashes are in [recipes.json](recipes.json). All samples are existing synthetic Go vectors or specified deterministic derivatives.

| ID | Transformation | Exact outcome | Normalized outcome |
| --- | --- | --- | --- |
| D1 | Existing whitespace/comment reformat pair | match | match |
| D2 | Existing systematic identifier renaming pair | no-match / no-shared-fingerprints | match |
| D3 | Swap two existing synthetic function declarations | abstain / ambiguous | abstain / ambiguous |
| D4 | Insert `break ;` after every fourth original expected token, serialize tokens explicitly | no-match / no-shared-fingerprints | no-match / no-shared-fingerprints |
| D5 | Replace function with unrelated type declaration | no-match / no-shared-fingerprints | no-match / no-shared-fingerprints |
| D6 | Append five-token copied prefix to unrelated type host | no-match / no-shared-fingerprints | no-match / no-shared-fingerprints |
| C-identical | Independent identical-input comparison | match; full fingerprint containment | match; full fingerprint containment |
| C-unrelated | Independent unrelated pair, distinct from D5 | no-match / no-shared-fingerprints | no-match / no-shared-fingerprints |

Exactly **3/6 demonstrations** are misses across **both** displayed modes. D2's exact-only miss does not inflate that count. D3 ambiguity is preserved and not relabelled no-match/below-minimum. D6 was intended as a below-minimum-length fragment demonstration but actually shares no selected fingerprints; its observed no-match is retained. Five copied tokens are below the unchanged-run locality threshold `k+w-1=8`; no detection guarantee applies. No measured case is labelled below-minimum-evidence when its actual code says otherwise.

D3 preserves function-body bytes but changes adjacency. D4 is a lexical evasion illustration: its arbitrary inserted control-flow tokens are not a functionality-preserving or syntactically valid Go-program transformation. D6's fragment may likewise be syntactically incomplete. The extractor accepts tokenizable fragments; no compiler/runtime/behavior test is claimed. Reformat/rename robustness here is finite synthetic evidence. The identical control's “full” result means 100% distinct-fingerprint containment in each direction, not that a displayed region covers every byte, comment or delimiter. Original region spans are retained in the bodies.

## Exact native identities and retained evidence

Both existing stamped CLIs identify implementation **`dcaa0d42e9de63d23aa113d9306134de9b28942c`**, pinned spec **`9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`**. Binary SHA-256:

- Rust `traceweave` 0.0.1: `5d22a4d37d6403c595f8ccab04172a496ca74368a52d5ee89a3b7e1b918308a3`.
- Go `traceweave-go` 0.2.0-dev: `0219f19b4222ff71733d3709a57116aae0756f2fd0bba0d6f1e9251e025052b1`.

[expected.json](expected.json) separates full body-file SHA-256 from canonical `bodySha256`, and records outcomes, denominators and region counts. The comparison produces canonical body bytes, so those two hashes agree here; no report-wrapper hash is substituted. [evidence/run.json](evidence/run.json) records actual version responses, host/Python, binary identities and all **160 data-path command results** with portable argv, stdout/stderr hashes and Go stdin hashes. Each case retains both extraction records, both catalogues and the comparison body for each native CLI: **80 artifact files**. Catalogue and body identities bind the exact source/configuration inputs.

Two complete runs (320 successful data-path CLI commands, plus separate recorded version responses) yielded identical artifact bytes, command records and native results. The second run lived in temporary thread storage; its artifact hash manifest matched the retained run exactly. No elapsed-time, peak-memory, browser/device, transport or performance measurement was taken. Native outputs are not a claim of UI/WASM/Shelf equivalence or conformance to every spec change after the CLI pin.

## Reproduce with already available stamped CLIs

No dependency installation or acquisition is part of these commands. Supply existing binaries with the identities above. The package uses Python's standard library; the recorded runs used the existing pinned development Python 3.12.14.

```sh
: "${RUST_CLI:?Set the existing stamped Rust CLI path}"
: "${GO_CLI:?Set the existing stamped Go CLI path}"
WEB4_ROOT=$(mktemp -d)
python3 research/drafts/web4-demo-fixtures/run.py \
  --rust "$RUST_CLI" --go "$GO_CLI" --out "$WEB4_ROOT/run"
python3 research/drafts/web4-demo-fixtures/check.py --replay "$WEB4_ROOT/run"
python3 -I research/drafts/web4-demo-fixtures/test_fixtures.py
```

`run.py` refuses unstamped/wrong-commit/wrong-spec CLIs, uses an isolated temporary `TRACEWEAVE_PRIVATE_DIR`, passes explicit stdout output flags and adapts the pinned CLIs' distinct argument conventions. It records every command and validates records/catalogues/bodies through their native validators. A different-platform rebuild can have a different binary hash; its exact bytes must be recorded and reviewed rather than represented as the measured binary. The replay checker requires the same stamped version identities and exact retained artifact hashes.

`check.py` verifies the eight-case partition, fixed configuration, input/body/record/native identities, actual positive and negative expectations, bounds on original UTF-8 regions, source bindings, derived transformation recipes and separate controls. `test_fixtures.py` contains two test methods, including ten negative corruption probes: missing/duplicate cases, altered input hash, false D2 or D3 classification, changed threshold, unstamped identity, failed/missing command and divergent native artifact hash. These checks need no CLI execution. They are package-local and do not modify the repository's validator or shared tests.

## Retained harness failures

[failures.json](failures.json) preserves four initial harness-interface failures, including the first omitted output flag, the second omitted comparison output flag, Go stdin extraction and Go flag-based validation. These were harness errors, not detector misses. The first probe wrote a synthetic catalogue to the CLI's default private catalogue location before isolation was added; any previous content there was not established or restored. Subsequent probes/runs use temporary isolated storage. See the [author report](../../reviews/web4-demo-fixture-author-report.md) for this limitation. No existing default-private data was inspected as fixture input.
