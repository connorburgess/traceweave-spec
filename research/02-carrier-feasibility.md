# Carrier feasibility: Go and Rust pilots

Status: preliminary investigation, 2026-11-18. Includes executed synthetic checks and a read-only repository language inventory. No application was marked, no detector was implemented, and no real-world capacity or false-positive claim follows from these results.

## Decision and scope

Use Go and Rust as the initial marked languages because Looptender and TalkQTE are actively developed pilot applications. TypeScript/JavaScript follows for web code. The implementation language of a research tool does not determine the content language. Both submitted lane-1 reports defaulted to Python without first establishing this product fit.

Keep the shared evidence core small. Separate language-specific embedding, extraction and detector profiles from signature/trust/time adapters. Expansion into new languages or media requires independent safety, capacity, attack and interoperability evidence. More specification pages are not evidence of maturity.

## Pilot selection

The initial targets reflect the maintainer's active Go and Rust applications. Private checkout identifiers and inventory counts are intentionally omitted. No application source was copied into the public fixtures and no pilot checkout was changed.

The experiments below are synthetic. A future authorized corpus census must use pinned inputs, separate production/test/generated/vendor code, retain exclusions and report unsupported constructs. It must not publish private application details.

## What primary sources actually support

- [SrcMarker, v2](https://arxiv.org/html/2309.00860v2), sections III-B, IV-A and V: evaluated languages are C, C++, Java and JavaScript. Python is discussed as an extension limitation, not established as the obvious first target. The paper explicitly acknowledges transformation soundness edge cases. Its learned transformation selection does not validate our proposed hand-written permutation carrier.
- [SrcMarker implementation](https://github.com/YBRua/SrcMarker): public implementation with an MIT license. Availability is verified; dependencies, bundled components and a reproducible run have not been audited or executed. Do not infer support for Rust, Go or TypeScript from its JavaScript support.
- [CodeMark](https://arxiv.org/abs/2305.12461): an actual variable-based learned marking method, relevant as an identifier-channel comparison. Its existence does not validate arbitrary renaming in either pilot.
- [CLASP v2](https://arxiv.org/abs/2510.11251v2): the abstract describes training-free LLM-assisted transformations and reference retrieval/differential extraction. This confirms a relevant reference-assisted approach; no CLASP results were reproduced here.
- [Robustness study v4](https://arxiv.org/abs/2403.17983v4): studies watermarks on LLM-generated Python code. It motivates removal tests, but its attack results must not be treated as a direct benchmark of an unimplemented Go/Rust post-hoc marker.

These source checks narrow the recommendation; they do not complete the remaining bibliography audit from lane 1.

## Executed Go experiment

Source: [Go carrier checks](experiments/go-carrier/carrier_test.go). Standard-library-only module; executed with `go1.27.3 darwin/arm64`.

The experiment constructs all 24 permutations of four fresh local integer-literal bindings and a fixed return array. It compiles and runs only those synthetic functions. It also parses each formatted fixture to inspect declaration order.

Results:

- 24/24 permutations returned the same `[1 2 3 4]` value.
- 24/24 preserved declaration order through `go/format`.
- Sorting those restricted declarations by name collapsed all 24 orders to one canonical order. That erases distinctions used to encode a payload; it does not measure the response of a detector, because none exists.
- A separate counterexample passed: reordering assignments to different locals changes observable behavior when their RHS functions have side effects.

Four freely usable statements provide at most 24 states, or four fixed-length binary payload bits without overhead. This is not an entropy estimate for natural code and not a false-positive bound. Error correction, synchronization, context binding and repeated marks consume capacity. Formatting survival is therefore a weak gate, not robustness against removal.

The restricted fixture excludes calls, aliasing, mutable inputs, shared state, tracing/debug-location guarantees and compiler-binary equivalence. It is not a safety analyzer for general Go. See the [Go specification](https://go.dev/ref/spec#Order_of_evaluation), [parser](https://pkg.go.dev/go/parser) and [formatter](https://pkg.go.dev/go/format).

Reproduce from `research/experiments/go-carrier`:

```sh
go test -v -count=1 ./...
```

## Executed Rust experiment

Source: [Rust carrier checks](experiments/rust-carrier/carrier.rs). Executed with `rustc 1.97.1 (8bab26f4f 2026-07-14)`, edition 2021.

Two tests passed: two orders of four fresh integer bindings returned the same array, and reordering bindings with custom destructors changed the observed destruction order. This is a counterexample to using compilation or borrow checking alone as an equivalence test. The [Rust Reference](https://doc.rust-lang.org/reference/destructors.html#drop-scopes) specifies reverse declaration-order drops for variables leaving their scope.

The Rust test is a two-order smoke check, not the exhaustive Go permutation experiment. `rustfmt` formatted the fixture; automatic order-preservation checks under Rust formatting or refactoring have not been implemented. No Rust marking capacity is measured on application code.

Reproduce, placing the binary outside the source tree:

```sh
rustc --edition 2021 --test research/experiments/rust-carrier/carrier.rs -o /tmp/traceweave-rust-carrier-tests
/tmp/traceweave-rust-carrier-tests --nocapture
```

## What to do next

1. Specify the exact behavior contract and build boundaries for each pilot: Go source reuse versus compiled artifacts, Rust source before/after macros and conditional compilation. Do not infer cross-language or binary survival.
2. Build read-only, syntax/type-aware eligibility counters over pinned snapshots. Start with deliberately restrictive candidates; enumerate reasons for skipping functions. Counts are opportunities to investigate, not certification of safety.
3. Compare at least two independently motivated carrier families. Statement order alone is not a robust default given the trivial normalization demonstrated here. Identifier choice is a useful weak baseline, not a guaranteed fallback.
4. Measure usable capacity, partial-fragment synchronization, normal-tool survival, deliberate normalization/removal and transplant attacks before selecting a payload or claiming reliable identity recovery.
5. Keep key-assisted/reference-assisted mark detection separate from public signature verification. Lane 3 owns calibration of the complete search; lane 4 owns trust and evidence binding.

The investigation supports Go/Rust pilot selection and rejects a shortcut from “AST transformation” to “safe, robust mark.” Realistic corpus measurements remain the next research step, not a completed outcome of these synthetic checks.
