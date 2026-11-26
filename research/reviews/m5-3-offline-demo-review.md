# M5.3 independent offline synthetic demo reproduction

Date: 2026-11-26. Scope: the criterion “A non-author reproduces the demo offline after dependency fetch: clean clone → pinned implementation.” This record supplies evidence; it changes no gate status or count.

## Pins and method

Release documents inspected at specification commit `6ded8a3d6923b310f6b0abfab2a4037abfc3e467`: ROADMAP.md, README.md, conformance matrix and release notes. Implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c` was cloned from a local repository with `--no-hardlinks`, checked out detached, and remained clean. Its spec pin was `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191` (`0.1.0-draft.1`). Original implementation was not changed.

Host: macOS Darwin 25.4.0, arm64; preinstalled Rust/Cargo 1.97.1, Go 1.27.3, Python 3.14.6. Execution, new Cargo registry cache, Go module/build caches, binaries and scratch were isolated in temporary storage outside both source worktrees. Toolchain installation and upstream clone accessibility were not tested.

Authoritative executable instructions were the implementation README's stamped-build commands, `go/README.md`'s `go run ./tools/walkthrough [-bin BIN]`, and `docs/core-gates.md`'s `tw-conformance walkthrough --bin BIN`. Both sources identify `go-function-in-host`. The historical `scripts/walkthrough` reference names an absent wrapper; historical spec-override notes were unnecessary at this pin. The [designated release recipe](../../docs/release/offline-demo.md) consolidates the actual tested route.

## Observations

| Operation | Result |
| --- | --- |
| Fresh network-enabled `scripts/ci-fetch` | Exit 0; locked crates downloaded into a new cache, both Go modules verified; 5.70 s |
| Offline `scripts/check-spec-pin` | Exit 0; 356 vendored files match lock digests |
| Default Go walkthrough, unstamped | Exit 0; expected body; correctly refused report document emission |
| Offline Rust stamped build | Exit 0; exact implementation/spec pins; 9.33 s |
| Offline Go stamped build | Exit 0; exact implementation pin; 3.34 s |
| Offline Rust stamped walkthrough | Exit 0; expected body, 4/4 manifest spans, valid stamped report/provenance and candidate-generation record; 3.80 s |
| Offline Go stamped walkthrough | Exit 0; all steps including stamped report passed; 1.26 s |
| Offline strict pin check against separate local spec clone | Exit 0; 356/356 files equal `git show` bytes at pinned spec commit |
| Offline version output | Both stamped; implementation `dcaa0d42…`, spec `9cf78eec…` |
| Independent output comparison | Both retained canonical body files byte-identical; SHA-256 below |
| Final Git status | Empty in execution clone and original implementation |

Expected and observed canonical body SHA-256:

```text
081d860084af229d77137e32dedd9f40f7d0bbeca6b18424b6d51cc1d89ed3be
```

Every offline build/check/walkthrough/version command used the unmodified `scripts/offline`. Before each invocation, the outside loopback control connected; inside loopback and public-IP probes both failed with `Operation_not_permitted`. macOS `sandbox-exec` enforced `(version 1)(allow default)(deny network*)` for the command and descendants. Cargo offline flags and Go proxy/toolchain restrictions were additional controls. Denial was demonstrated at OS level; zero attempted network syscalls was not measured.

## Limits and disposition

The synthetic native demo succeeded; no execution blocker remains for the tested route. The missing designated release recipe is supplied by the linked document. This evidence does not establish remote repository availability, Linux reproduction, all-profile/full-suite conformance, registration/signing or browser reproduction, held-out detection usefulness, production provenance security or conformance to all later specification changes. The default unstamped refusal is not report emission; the two stamped runs actually emitted and validated reports.

Detailed command logs, executed runner/environment, retained inputs/outputs, original document snapshots, output hashes and final status evidence remain in the originating review thread's storage as `m53-offline/`, with a `SHA256SUMS` manifest. They are intentionally not copied into the repository. This concise record contains no private filesystem paths. No gate edits, held evaluation, corpus acquisition, external service use or implementation feature changes were part of reproduction.

## Recipe confirmation

After documenting the recipe, its two shell blocks were extracted verbatim and executed with a local implementation clone source, shell error checking, and another fresh temporary workspace/cache set. Both stamped walkthroughs and version checks exited 0 under the wrapper, final Git status was empty, and a separate comparison again confirmed identical canonical body bytes with the expected digest. The confirmation log is retained with the detailed thread-storage evidence.
