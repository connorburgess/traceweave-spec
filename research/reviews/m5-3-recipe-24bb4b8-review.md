# Independent M5.3 recipe review

Exact reviewed specification commit: **`24bb4b8483dc86966cb7c8277130bb816b0c6b3f`**, `m5-readiness`, 2026-11-26. Applicable AGENTS.md instructions were read. This reviewer did not author the [designated recipe](../../docs/release/offline-demo.md) or its [original reproduction record](m5-3-offline-demo-review.md). This change adds only the present independent review; no gate or progress count changes.

**Disposition: M5.3 eligible on this exact commit, with no blocking findings.** ROADMAP's actual criterion is “A non-author reproduces the demo offline after dependency fetch: clean clone → pinned implementation.” The committed recipe now designates the existing synthetic native walkthrough, supplies its executable entry points and exact pins, distinguishes dependency preparation from enforced offline execution, and states the limits. Independent execution below establishes more than agreement with the author's reported success. It does not approve a release or imply held-out usefulness.

## Recipe and evidence assessment

The recipe's implementation pin is **`dcaa0d42e9de63d23aa113d9306134de9b28942c`**. Its actual lock and both resulting binary version outputs identify specification pin **`9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`**, version `0.1.0-draft.1`. Toolchain instructions agree with `rust-toolchain.toml` (Rust/Cargo 1.97.1) and `go/go.mod` (Go toolchain 1.27.3). It correctly warns against using the implementation README's stale prose pin.

The first shell block creates a clean full-history clone and fresh dependency/build caches, then performs the explicit network-enabled `scripts/ci-fetch`. Inspection confirms that this script fetches the two locked Cargo dependency sets and verifies the two standard-library-only Go modules. The second block uses the unchanged implementation `scripts/offline` before the lock check, each stamped build, each native walkthrough and each version check. Those seven commands cover extraction → catalogue → comparison → emitted stamped report → validation. An unstamped report refusal is explicitly distinguished from successful report emission; the designated commands supply stamped binaries.

I inspected both walkthrough implementations and the denial wrapper. Rust checks the expected body digest, all four expected manifest spans, emitted report acceptance, implementation/spec provenance and body/config binding. Go's stamped branch emits and validates the report; it does not substitute the default unstamped refusal. The wrapper proves a working outside loopback control and refused confined loopback/public connections, then executes the requested command under the same confinement profile. This is OS denial, not just `--offline` application behavior.

The author's private evidence manifest verified **63/63 listed file hashes**, including retained outputs and logs. Both original reports contain the stated implementation/spec pins and expected body digest. The subsequent verbatim-recipe confirmation log also shows the stamped report paths succeeding. These are supporting evidence, not substitutes for the independent run below. The committed portable record supplies pins, commands, observations and limitations without private filesystem paths; a clean clone can execute the recipe without access to the original thread storage.

## Independent reproduction

Host: macOS Darwin 25.4.0 arm64, preinstalled Rust/Cargo 1.97.1, Go 1.27.3 and Python 3.14.6. I created **another full-history local clone with `--no-hardlinks`**, checked it out detached at the exact implementation pin and asserted an empty initial Git status. No original implementation checkout or author binary/build output was reused or modified.

To respect the no-acquisition scope, I copied already-fetched Cargo dependency-cache material into a new isolated Cargo home. Go build/module caches and temporary/build/output directories were separate and initially absent. I independently ran `scripts/offline scripts/ci-fetch` with `CARGO_NET_OFFLINE=true`, `GOPROXY=off` and `GOTOOLCHAIN=local`; both locked Cargo sets and Go modules revalidated successfully without fetching. This is **cached dependency revalidation**, not a claim to have rerun upstream dependency acquisition or the recipe's first shell block verbatim. The author's successful fresh-fetch evidence was inspected separately.

I extracted the **second shell block verbatim from the exact reviewed Git object** and executed it with shell error checking in that new clone, using the documented environment and newly built outputs. It exited **0** in 28.74 seconds. Every one of its seven wrapper invocations reported outside loopback connected and inside loopback/public refused with `Operation_not_permitted`. All binaries and commands remained under the wrapper; none was run unconfined to get past a failure.

| Independent operation | Observed result |
| --- | --- |
| Clean local clone → detached exact implementation | Initial and final Git status empty. |
| Cached dependency revalidation under denial | Exit 0; no new acquisition. |
| Ordinary pin check | 356 vendored files match lock digests. |
| Rust stamped build and Go stamped build | Both exit 0; no reused author binaries. |
| Rust walkthrough | Exit 0; `spans: 4/4`, valid stamped report/provenance, valid candidate-generation record, `walkthrough: passed`. |
| Go walkthrough with supplied stamped binary | Exit 0; report-document step and all steps passed. |
| Both version checks | `stamp: "stamped"`, exact implementation and spec pins above. |
| Separate retained-output verification | Canonical bodies byte-identical; each report's embedded body equals its corresponding body file; provenance body/config digests and implementation/spec pins agree. |
| Optional strict pin check under denial against an existing local spec mirror | Exit 0; **356/356** vendored files equal `git show` bytes at the locked spec commit. No fetch occurs in this checker. |

Expected and independently observed body SHA-256:

```text
081d860084af229d77137e32dedd9f40f7d0bbeca6b18424b6d51cc1d89ed3be
```

Both report/body comparison-config bindings are:

```text
39345e9c8de2b566d19943563326062a46edd38e429a4a96f169307b15147333
```

The report wrappers differ in implementation name/version as expected; wrapper-byte equality is not claimed. Raw reviewer logs, result JSON and retained synthetic Go/Rust output copies are preserved privately as `m53-independent-24bb4b8/`, with a **26-file SHA256SUMS** manifest. They are not committed to this repository. The separate cached-fetch and strict-pin commands also proved denial, in addition to the seven proofs in the verbatim block.

## Limits and regression scope

The criterion does not require a public remote clone, Linux reproduction, every profile, full `scripts/check`, registration/signing, Shelf/browser execution or a detection benchmark. The recipe explicitly limits the result to one synthetic Go-source fixture through two native implementations. Upstream repository access and toolchain installation remain untested; local-clone use is disclosed. No packet trace was taken, and refusal does not establish zero attempted network syscalls. The existing wrapper uses a public-IP confinement probe; no live registration, timestamp or paid service was used.

The implementation's locked spec revision predates the recipe/release-documentation revision. Strict pin comparison proves the stated locked bytes, not conformity to every later specification change. This limitation is explicit at recipe line 94 and does not prevent reproduction of the designated pinned demo under the actual M5.3 criterion. It must not be promoted into a blanket new conformance claim.

The reviewed commit adds the recipe/portable record and links them from the release notes and matrix. It changes no normative wire bytes, feature cells, README claims or approved exclusion policy. The new links and declared limitations do not invalidate the earlier M5.1/M5.2/M5.4/M5.5 reviews. M3 remains open/held and deferred CI/CD signing remains deferred.

Repository checks on the reviewed tree passed: `tools/validate.py`, **28/28 unit tests**, `tools/validate.py --links-all`, `tools/check_hygiene.py` and `git diff --check`. Links/hygiene were checked again with this review record staged.

**M5.3 remains open in the tree as instructed.** This record recommends eligibility for a separate closure/integration change. No count edits, push, feature work, sublane, corpus acquisition or held evaluation were performed.
