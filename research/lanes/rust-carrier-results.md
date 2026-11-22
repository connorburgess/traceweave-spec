# Rust synthetic carrier results

Executed 2026-11-18. The bounded experiment supports deterministic source-state recovery under its exact grammar and formatter configuration. It also demonstrates valid canonicalization removal for both carriers. It establishes no identity authentication, useful-code coverage or robustness guarantee.

Implementation: [experiment.py](../experiments/rust-carrier/experiment.py); machine-readable counts, states, digests and refusal reasons: [results.json](../experiments/rust-carrier/results.json). The earlier `carrier.rs` smoke checks remain unchanged. All inputs are generated synthetic examples; no private application was inspected. No production embedder, normative format or payload size was selected.

## Reproduce and boundary

From the repository root:

```sh
python3 research/experiments/rust-carrier/experiment.py --output research/experiments/rust-carrier/results.json
```

Requires Python 3.9+ and the recorded `rustc`/`rustfmt` on PATH. The command checks its assertions, writes JSON and exits nonzero on failure. Temporary Rust sources and executables are removed afterward. Generated functions are renamed uniquely only in the trusted compilation harness; extraction operates on the original standalone sources.

Executed tools: Python 3.14.6; `rustc 1.97.1 (8bab26f4f 2026-07-14)`, full commit `8bab26f4f68e0e26f0bb7960be334d5b520ea452`, LLVM 22.1.6; `rustfmt 1.9.0-stable` from the same commit; host/target `aarch64-apple-darwin`. Rust edition and formatting style edition are explicitly 2021. Compilation uses `--test`, either `-C opt-level=0 -C overflow-checks=yes` or `-C opt-level=3 -C overflow-checks=no`. No Cargo dependencies, features or build scripts are involved.

The whole-input grammar accepts one private `fn specimen() -> [u32; N]` with N from 0 through 4, immutable declarations named with distinct letters `a`–`d`, explicitly suffixed in-range decimal `u32` literals, and a final array using every binding exactly once. It rejects all trailing source. Literal spellings must be decimal without leading zeroes, either without separators or with exactly one underscore before the last digit. No regex scan skips unsupported syntax. This is a deliberately closed fixture grammar, not a Rust parser or a general eligibility analyzer.

An explicit synthetic boundary manifest excludes generated/vendor inputs, macros/proc macros, cfg/features, build scripts and source observers. This is a supplied precondition: the harness cannot establish that arbitrary source has no external readers. A changed manifest is refused. The grammar excludes references, lifetimes, moves of resource-owning values, custom Drop, shadowing, calls, mutation, unsafe/FFI, trait operators, API/visibility changes, attributes and nested items. Primitive `u32` cannot be shadowed within the accepted whole source. Inputs are retained source bytes before expansion; no extraction from compiled artifacts is implemented.

## Mapping, eligibility and counts

Order state is the zero-based lexicographic rank of the names' permutation, holding each name/value pair and final array order fixed. Spelling state is a little-endian bit mask over eligible names in ASCII-sorted order; zero selects plain digits and one selects the permitted separator. Neither family is keyed. Extraction requires the synthetic reference and checks its name/value set and returned-name sequence against the candidate before reading state. A value/reference mismatch or unexpected spelling returns an erasure with a reason, never an implicit zero. No original source digest alone substitutes for reading the modified source.

| Measurement (unit: one requested source/state) | Declaration order | Literal spelling |
| --- | ---: | ---: |
| Eligible base functions / five N=0…4 functions | 3/5 | 4/5 |
| State-sweep requests | 34 | 31 |
| Completed / positive-capacity requests | 32/32 | 30/30 |
| Changed source / completed | 29/32 | 26/30 |
| Already matching / completed | 3/32 | 4/30 |
| Zero-capacity refusals / sweep requests | 2/34 | 1/31 |
| Additional refusal controls, all byte-identical | 25/25 | 26/26 |
| Exact clean raw-state recovery / completed | 32/32 | 30/30 |
| End-to-end recovery / all requests including controls | 32/59 | 30/57 |
| Wrong decoded clean states / completed | 0/32 | 0/30 |
| Clean extraction erasures / completed | 0/32 | 0/30 |

All 65 state-sweep calls repeated deterministically, including refused zero-capacity cases. Every refused embedding returns the exact supplied string, with byte equality asserted; no partial output or rollback is needed. There were zero validation failures among completed cases. Already-matching state zero decodes successfully but supplies no evidence of intentional insertion.

Refusal controls per family comprise 17 source fixtures (Drop item, borrow, dependent initializer, shadowing, call, macro definition, macro invocation, attribute macro, cfg attribute, unsafe function, operator expression, lifetime, visibility change, unexpected spelling, and malformed lists `[a,, b]`, `[,a,b]`, `[ab]`), five changed boundary manifests, and three request controls (negative state, out-of-range state, unknown family). Spelling additionally refuses an otherwise valid single-digit function with no spelling sites. Invalid refusal fixtures are not compiled or counted as behavior-preserving attack attempts. Two extraction controls per family return erasures: an unchanged-value unexpected spelling and a changed value against the original reference. Wrong key/identity controls are unavailable because no identity protocol exists.

Capacity is raw, before any authentication, identity, synchronization, redundancy or context binding:

| N | Order states / floor(log2 states) | Spelling states / raw bits |
| --- | --- | --- |
| 0 | 1 / 0 (refused) | 1 / 0 (refused) |
| 1 | 1 / 0 (refused) | 2 / 1 |
| 2 | 2 / 1 | 4 / 2 |
| 3 | 6 / 2 | 8 / 3 |
| 4 | 24 / 4 | 16 / 4 |

Each spelling fixture has N eligible two-digit values. Exhaustive order tests include all n! states, including states beyond a power-of-two coding subset. These dimensions are test coverage, not a carrier or payload choice. The cases share one fixture family and are dependent; they support no population error bound.

## Formatter, behavior and removal

Each completed marked source was deliberately rendered on one compact line, then formatted twice using `rustfmt --edition 2021 --config style_edition=2021`. State recovery passed for 32/32 order and 30/30 spelling cases; the first formatting changed all 62 sources, and the second formatting was byte-idempotent for all 62. Other rustfmt settings, editions, lint fixes and refactor tools were not tested.

For every completed state the experiment constructed actual marked, formatted and canonicalized `.rs` function text. Every stage was compiled in the same generated test crate and its returned array checked. All **186/186 stage/function checks passed in each of debug and optimized profiles**, 372 checks total. Compilation failures, runtime failures and timeouts were zero. This validates fixture outputs; it does not prove general Rust semantic equivalence or preservation of binary bytes, timing, diagnostics, layout or debug observations.

| Canonicalization measurement | Declaration order | Literal spelling |
| --- | ---: | ---: |
| Attack: actual source rewrite | Sort declarations by name | Strip literal separators |
| Compiled/output-valid attacks / attempts | 32/32 | 30/30 |
| Source changed / valid attacks | 29/32 | 26/30 |
| Already canonical / valid attacks | 3/32 | 4/30 |
| Nonzero original state collapsed to zero / nonzero states | 29/29 | 26/26 |
| Original state retained / valid attacks | 3/32 | 4/30 |
| Extraction erasures after attack / valid attacks | 0/32 | 0/30 |

These valid removals erase the distinction used by every tested nonzero state. The decoder still accepts the canonical source and returns zero: this is a **wrong decoded state** for 29/32 order attacks and 26/30 spelling attacks, rather than a parser erasure or abstention. For the already-zero cases, equality survives normalization and no inserted distinction is demonstrated. Conditional raw-state loss and end-to-end raw-state loss coincide here because all attacks were valid. An identity-evasion rate cannot be calculated from these raw-state results.

The narrow semantic argument is that integer separator removal leaves the same typed literal value, while permutations only move independent literal initialization of primitive values with no destructor effects. Passing tests alone would not justify expanding this to borrowing, Drop, trait calls or arbitrary effectful expressions.

## Limits and next decision

Whole-run reference alignment only is implemented. There is no fragment localization, partial-copy synchronization, transplantation defense, key/identity framing, signature/trust check, fingerprint baseline or combined decision. Full-query false-alert rates, wrong-identity acceptance, ownership and ancestry conclusions are unavailable, not zero. Unmarked state-zero sources are already-matching controls; independently written same-task negatives need the later identity/search evaluation.

The final run took 4.019303 seconds wall time including subprocesses, as recorded in JSON; this small run does not isolate eligibility, embedding or extraction latency and does not measure peak memory. Temporary-file compilation is a fixture validation step, never a requirement to execute untrusted candidates. No binary recovery was attempted. The repository validator and all six contract tests also passed after implementation; these do not validate carrier robustness.

Recommendation: retain both as weak synthetic baselines. Separator spelling has the smaller safety argument, and both channels fail inexpensive public normalization. Before widening scope, add an explicit alignment/identity protocol and independent source controls; measure useful-code eligibility only on an authorized corpus. The present experiment supplies no reason to pick a production payload length or promise resistance to removal.

Matching-version primary sources fetched and checked during this run: [Rust Reference 1.97.1 integer literal rules](https://doc.rust-lang.org/1.97.1/reference/expressions/literal-expr.html#integer-literal-expressions), [drop scopes](https://doc.rust-lang.org/1.97.1/reference/destructors.html#drop-scopes), [declarative macro hygiene](https://doc.rust-lang.org/1.97.1/reference/macros-by-example.html), and [procedural macros and source access](https://doc.rust-lang.org/1.97.1/reference/procedural-macros.html). These reconcile the plan's older reference baseline with the inspected compiler; they support the stated restrictions, not a general transformation proof.
