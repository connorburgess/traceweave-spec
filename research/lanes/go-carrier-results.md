# Go synthetic carrier results

Executed 2026-11-18. [Harness](../experiments/go-carrier/synthetic_test.go), [module](../experiments/go-carrier/go.mod), [plan](go-carrier-plan.md), [checkpoint](checkpoint.md). This implements deterministic **raw-state** transformation and reference-assisted extraction for two tiny source carriers. All tested completed states survived formatting and retained their return values. Both carriers collapsed under valid source canonicalization. Identity/authentication capacity and detection accuracy remain unavailable.

## Executable boundary and mappings

The harness accepts only its synthetic single-file package: fixed filename `fixture.go`, `package main`, one `sample` function, no imports/comments/other declarations, receiver, generics, parameters or named results. The body is 0–4 single-name `x := N` declarations and a return-array literal listing each local object exactly once. `N` must be nonnegative decimal, without separators/alternate bases, fitting signed 32 bits. The return/signature types are explicit `[n]int`. Local identifiers match `[a-z][a-z0-9]*`. Main exhaustive fixtures use role values `1..n`.

This is an in-memory fixture boundary, **not a repository loader**: it cannot certify other package files, platform filename suffixes, assembly, generated files, embedded assets, dependencies or configurations. No application was inspected. All comments, including build/cgo/embed/compiler directives, are refused. Additional package declarations, aliases, pointer/mutable operations, calls, closures, concurrency, fields, shadowing and mixed short declarations fail the shape checks. Externally named APIs are never transformed; the function/package/type names stay fixed.

`go/types` checks the complete accepted package with `Defs`, `Uses`, `Scopes` and `Types`. Return position identifies each `*types.Var` role. Renaming edits definition/use nodes resolved to that object, then fresh parsing/type checking reestablishes a one-to-one role graph and unchanged role values. Every alternative spelling is checked against all identifiers in the file, keywords and universe objects; only uses/definition of its own target object are permitted to match. One occupied alternative causes the identifier family to refuse the complete request. These checks do not analyze general aliasing/effects. [go/types, go1.27.3](https://pkg.go.dev/go/types@go1.27.3#Info).

- **Order:** lexicographic permutations of return-role indices; rank is the raw state. Encoding changes actual declaration AST order. Return order and binding values stay fixed.
- **Names:** two disjoint alternatives per role: `roleaa`/`roleab`, `roleba`/`rolebb`, etc. Role zero is the least significant radix-two digit. Encoding changes resolved identifier nodes. Declaration order stays fixed.
- **Reference alignment:** require the same narrow grammar and identical literal-value vector in return-role order; derive the state entirely from candidate syntax. Reference values never fill missing symbols. An incompatible reference causes an error. This anchor is deliberately weak and can match independent equivalent code.

For this grammar, fresh scalar literal initialization has no side effects/aliases, and binding-preserving renaming/reordering leaves the returned values unchanged. That is the limited semantic argument; compiler/test success is additional finite validation. General evaluation-order rewrites, concurrent behavior, debug/source locations, runtime costs and binary survival are outside it. [Go specification, go1.27, scope](https://go.dev/ref/spec#Declarations_and_scope), [evaluation order](https://go.dev/ref/spec#Order_of_evaluation). No compiled-artifact mark extraction was attempted.

## Capacity and embedding denominators

| Bindings n | Order raw states / fixed binary bits | Names raw states / fixed binary bits |
| --- | --- | --- |
| 0 | 1 / 0 | 1 / 0 |
| 1 | 1 / 0 | 2 / 1 |
| 2 | 2 / 1 | 4 / 2 |
| 3 | 6 / 2 | 8 / 3 |
| 4 | 24 / 4 | 16 / 4 |

Bits are `floor(log2(states))` before framing, identity, keys, authentication, synchronization or redundancy. These n/alphabet values are test dimensions, not a selected payload/group size. Joint carrier capacity was not tested. A one-state carrier is zero-capacity: embedding refuses with original bytes, even though the grammar is valid.

All five main fixtures satisfy the grammar; positive capacity is 3/5 order fixtures and 4/5 name fixtures. The separately constructed 24 malformed/unsupported fixtures all refuse, so common grammar eligibility is 5/29 inputs in that deliberately constructed set; it estimates no real-code eligibility. The codebook-collision fixture is an additional grammar-eligible input: order accepts a nonzero state, names refuses all four requested states.

| Main exhaustive sweep | Order | Names |
| --- | --- | --- |
| Requested raw states across n=0..4 | 34 | 31 |
| Changed source, validated | 29/34 | 26/31 |
| Already matching, original bytes retained | 3/34 | 4/31 |
| Zero-capacity refusal, original bytes retained | 2/34 | 1/31 |
| Completed (changed + matching) | 32/34 | 30/31 |
| Exact clean raw recovery / completed | 32/32 | 30/30 |
| Exact clean raw recovery / all requests | 32/34 | 30/31 |
| Exact raw recovery after actual `gofmt -s` / completed | 32/32 | 30/30 |

The changed subsets recovered 29/29 and 26/26. All completed states had distinct output bytes within each n/family state space. Re-embedding each completed result at the same state returned `already_matching` with identical bytes: 62/62. There were zero observed post-edit validation failures/rollbacks and zero clean/formatted decoded-state errors among 62 completed cases; deliberately faulted rollback paths were not tested.

Refusal controls: 24 fixtures × two families = 48/48 requests refused with unchanged bytes; each was repeated to check deterministic reason/output. Additional codebook collisions: 4/4 refused unchanged. Out-of-range states: 4/4 refused unchanged. A names request starting with non-codebook locals `left`/`right` changed the resolved objects and recovered requested state 3. Control requests are reported separately from the exhaustive sweep.

## Actual source removal and behavioral validity

The order canonicalizer reorders **source declarations** by return role; the name canonicalizer rewrites **source identifiers** to each role's first spelling. Both emit full source, independent of the requested state. Their outputs pass fresh extraction/type checking and compiled behavior checks. This extends the older experiment, which only sorted an extracted list.

| Attack measure | Order | Names |
| --- | --- | --- |
| Valid canonicalized outputs / attempted | 32/32 | 30/30 |
| Nonzero states reset to zero / nonzero inputs | 29/29 | 26/26 |
| Already-zero states, unchanged bytes | 3/32 | 4/30 |
| Valid direct-return outputs / attempted | 32/32 | 30/30 |
| Direct-return carrier grammar unavailable / valid outputs | 32/32 | 30/30 |

Canonicalization erases the nonzero distinctions, but the raw decoder still returns **zero**, not an erasure/abstention. Counting the already-zero inputs as erased would inflate removal success. Direct-return rewriting replaces every local use with its literal and removes the declarations; extraction rejects the resulting unsupported grammar. This is valid carrier removal, not an invalid attack hidden behind a similarity gate. No attack execution/validity failures occurred in these 124 attempts (62 canonicalization + 62 direct-return).

One aggregate synthetic package contained 248 functions: clean, formatted, canonicalized and direct-return variants for each of 62 completed states. It passed `go/types`, compiled and ran; 248/248 return arrays matched the expected `[n]int{1,...,n}`. For these total parameterless fixtures this checks their entire declared return-value behavior. A shared-grammar argument supports each rewrite; this is not a proof for programs beyond the accepted subset.

Unmarked canonical source decoded raw state zero for both families (2/2 controls). A separately spelled, synthetic same-task function decoded zero for order and abstained outside the names codebook; neither outcome certifies ancestry. Both families rejected a reference with changed role values (2/2). No identity protocol exists, so wrong-key/identity results, false alerts, authenticated evasion and ownership inference are **unavailable**, not zero. Fragments, localization, copied/transplanted regions, blind catalogue search, fingerprints/combined rules and real-corpus capacity remain unimplemented.

## Reproduction and measured costs

Observed toolchain: `go1.27.3 darwin/arm64`; `go version` on the `gofmt` executable also reported `go1.27.3`. Host: Apple M5 Pro. Module directive is now `go 1.27`. Environment: `CGO_ENABLED=0`, `GOTOOLCHAIN=local`, empty `GOFLAGS`/`GOEXPERIMENT`; no custom tags. Standard-library-only harness; generated executable source lives in `t.TempDir()`. No network, private source or paid service was used.

From repository root:

```sh
cd research/experiments/go-carrier
env CGO_ENABLED=0 GOTOOLCHAIN=local GOFLAGS= GOEXPERIMENT= go test -v -count=1 ./...
```

All four top-level tests passed, including the two existing feasibility checks. Latest measured run used the command above prefixed with `/usr/bin/time -l`: 3.21 s wall time, Go package time 2.790 s, reported maximum resident set size 115,900,416 bytes. The new exhaustive test logged 0.780539 s total and 0.547945 s for its aggregate compile/run; its generated program was 40,604 bytes. One measured invocation, shared machine/caches, no per-phase memory or stable performance claim. A preceding run also passed before adding the n>4 refusal and non-codebook rename control.

Recommendation: retain both as transparent weak baselines. Next blockers are realistic eligible capacity under an authorized corpus boundary, reviewed expansion of safety rules, stronger reference alignment and fragment scope, then a concrete identity/key/framing protocol with negative full-search calibration. Cheap valid normalization already removes these source distinctions. A successful raw round trip supplies no robustness or false-positive guarantee. The coordinator owns integration; no normative files, diagrams, private pilots, commits or pushes were changed.
