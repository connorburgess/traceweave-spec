# Review: implementation repository `merge-i2` at 82b02ab (I2 catalogue, comparison and report)

Status: non-author confirmation, 2026-11-22. Repository `<implementation repo>`, branch `merge-i2` at `82b02ab`; `main` `b43caa9` is an ancestor (`git merge-base --is-ancestor` true), so the merge is a fast-forward. The contract is spec `roadmap-v2` `15a4b2d` (draft-2 plus A1–A5).
I worked only in a scratch clone (`$TMPDIR/i2`, at `82b02ab`) and modified no worktree; scratch code is in `$TMPDIR/cr2/`, `m28.sh`, `priv.sh` and `my_sabotage*.py`. Every command ran in a sandbox with no network hosts allowed.

**Verdict: `main` may fast-forward to `82b02ab`.** Nothing found blocks the merge. Findings F1–F4 below are follow-ups. Gates M2.1, M2.2, M2.3 and M2.9 remain open, as worded (§7).

## 1. `scripts/check` and sabotages

**`scripts/check` exits 0 offline** (1 min 57 s). Every stage passed: coverage and precedence; fmt, clippy and tests; Rust conformance (76/76 bodies, 168 catalogue sides, 7/7 builds from records, 6/6 refusals, two runs identical); Go conformance (76/76 bodies, 168/168 digests); the extraction smoke (0 divergence classes); and the I2 smoke (2,147/2,147 cases agree, 117/117 vendored expectations in each lane).

**`scripts/sabotage-selftest`: every expectation holds** (exit 0). The baseline passes, and all 25 listed sabotages fail at their expected stage. That covers 4 coverage/precedence, 9 lexer (3 of them caught only by the differential smoke), the I2 comparison and validator cases, the A5 bounds in both lanes, and rustfmt/gofmt.

**My sabotages, three per lane** (each a one-line edit in a fresh clone, then the full `scripts/check`; "stage" is the last `==` stage printed):

| Sabotage | Caught at | First failure |
| --- | --- | --- |
| R1 Rust: suppression ignored inside modes (`distinctHashes` still reported) | Rust conformance | `go-boilerplate-suppressed`, `rv-below-over-common(-reversed)` bodies differ |
| R2 Rust: evidence counts seeds, not distinct hashes | Rust conformance | `go-repeated-hash-self`, `go-output-caps`, `go-periodic-distinct` |
| R3 Rust: ambiguity counted only among regions under the cap | Rust conformance | a panic at `compare.rs:167`, caused by my edit's map lookup, so a crash rather than a body diff |
| G1 Go: suppression ignored inside modes | `go test` | `TestMatchingVectors` |
| G2 Go: evidence counts seeds | `go test` | `TestMatchingVectors` |
| G3 Go: below-minimum ranked above ambiguous | `go test` | `FuzzCompareSources` seed #0 |

My first R1/R3 edits were not rustfmt-formatted, so `cargo fmt --check` caught them first. I re-ran both with `cargo fmt` applied after the edit; the table shows those runs. **`cargo test` caught none of the three Rust sabotages:** Rust's comparison rules are pinned only by the conformance vectors, while Go has unit and fuzz tests as well.

## 2. Clean room against both CLIs

**Update to 15a4b2d.** My draft-2 clean-room program (from the earlier contract review) reproduced 50 of the 76 vendored vectors unchanged; the other 26 failed only in amended areas. I updated it from the 15a4b2d text alone: declared channel lists and `mode-mismatch` (A3), the registered-profile table (A4), `input-too-large` entries with `null` digest and length (A1), and A5 (K1 extraction bounds in step 6, K3 lone surrogates, K4 depth 64, comparison bounds 10⁷/10⁵). After the update, 76/76 bodies and every catalogue digest are byte-identical to the vectors; 22/22, 5/5 and 4/4 comparison-config negatives are rejected and the 4 bound positives accepted. (The channel-negatives file holds **5** entries; contract §2b says six.)

**Vendored vectors through the CLIs:**

| Check | Go | Rust |
| --- | --- | --- |
| Report bodies equal to mine | 76/76 | 71/71 |
| Catalogue builds equal to mine (sources or records) | 121/121 | 110/110 |

Rust's CLI has no switch for TEST-ONLY profiles (only its conformance runner does), so it skips 5 vectors and 11 builds. Its conformance runner covers those, and `scripts/check` passes.

**My generated pairs: 5,000/5,000 report bodies byte-identical across my program, Rust and Go; 0 divergences.** Inputs (seeds 77001–82000) are random winnowing-shaped catalogues on the `go-tokens` and `text-plain` configurations: copied, edited and repeated hash segments; `input-too-large`, lexical-error and insufficient-tokens entries; random `minRegionDistinctHashes` 1–3, `mergeGap` 1–6 and small seed and region caps; optional suppression catalogues, wrong bindings, wrong modes and lightly corrupted catalogues. Coverage: 4,412 compared, 243 `malformed-catalogue`, 220 `suppression-catalogue-mismatch`, 125 `mode-mismatch`; mode outcomes 7,779 match, 5,155 ambiguous, 5,934 seed-limit-exceeded, 17,194 below-minimum, 4,363 common-only, 3,737 no-shared.

## 3. I2 differential with my seed

`python3 -I xcheck/xcheck_i2.py --seed 4242017`: **10,311/10,311 cases agree** (rate 1.0, 80 s), 117/117 vendored expectations equal in both lanes, no known-divergence entries. The README's "about 20,000 cases per seed" needs `--scale 2`; the default gives about 10,000.

## 4. Vendored files and manifest

All 43 files in `spec.lock` are byte-identical to `git show 15a4b2d:<path>` and match their digests. No vendored file is unlisted, and no JSON file under the four vendored directories at 15a4b2d is missing (harness files excluded). `scripts/check-spec-pin --strict --mirror` reports 43/43 equal, then fails **by design** because the commit is unpushed (`repository: null`). `conformance/not-implemented.json` lists all 43 files and the 13 test-only records; `implementationGaps` is `[]` and the Rust skips equal it. **No silent gaps.**

## 5. M2.8 end to end (both CLIs; `$TMPDIR/m28.sh`)

- **Default location, outside any checkout** (HOME a scratch directory, no path option, current directory inside a fresh `git init` checkout): Rust wrote `~/Library/Application Support/traceweave/private/catalogues/m28.catalogue.json`, Go `~/.local/share/traceweave/private/catalogues/m28.json`; same SHA-256 (`aa15c0c3…`), directories 0700, files 0600.
- **Zero files under the checkout:** a file listing plus `git status --porcelain --ignored` is unchanged.
- **Refusals (exit 2), with the checkout still unchanged:** HOME inside the checkout, `--out`/`-out` inside it, and Go `-out -` from inside it.
- **Faults, 3/3 per lane:** before-open, SIGKILL after a partial write, rename failure. Each leaves the previous catalogue byte-identical with nothing partial at the final path, and a normal run afterwards replaces it. After SIGKILL, a dot-prefixed temporary file holding half a catalogue (0600) stays in the private directory (F2).

## 6. Privacy

**Probe.** I built, compared and validated with sources containing marker identifiers, a string, a comment and a lexical error under a marker directory and file name, plus refused builds, malformed catalogues and tampered records.

**Result.** No marker text and no source path appears in any catalogue, report body, report document, provenance block or private directory. stdout/stderr carry only the paths and ids the operator passed and the output paths; no message quotes file content. Provenance is `{bodySha256, comparisonConfigSha256, implementation{commit 82b02ab…, name, version}, specCommit 15a4b2d…}`, with no free text in either lane. Two weaknesses: Go's record-schema error echoes an unknown **key name** from a record (`$.zzSecretKeyLEAK: unknown field`; F3), and Go writes `-out -` to a **file named `-`** in the current directory where Rust writes stdout (F1; refused inside a checkout).

## 7. Roadmap gates (spec `ROADMAP.md` at `roadmap-v2` HEAD `55e190a`; I mark nothing)

| Gate | Reading as worded |
| --- | --- |
| M2.1 | **Not met.** There is no `scripts/offline` wrapper and no network-denial probe; `scripts/` has `check`, `conformance`, `check-spec-pin`, `vector-coverage`, `check-vector-precedence`, `sabotage-selftest`. The walkthrough commands work, but the clause is the wrapper |
| M2.2 | **Not met as worded:** there is no frozen manifest. The substance is present: vendored vectors for exact (`go-identical`), fragment in host (`go-function-in-host`), rename/shadowing (`go-renamed`, `go-shadowing`), Unicode/repeated/tiny (`go-non-ascii-shift`, `go-repeated-hash-self`, `go-insufficient-tokens`), with spans N/N in both lanes. Remaining clause: the manifest. The cases live in `research/drafts`, at an unpushed commit |
| M2.3 | **Not met.** The vendor class is absent (contract OD-C19 still open). Independent same-task, boilerplate, unrelated and malformed are present, with candidate counts and denominators in the body |
| M2.4 | **Met in substance.** Two runs give identical bodies (conformance runs twice; my 2 × 2 runs, 4/4 equal); `comparisonConfigSha256` is in `inputs`; provenance commit `82b02ab` and spec pin `15a4b2d` are present (tests `crates/traceweave/tests/provenance.rs`, Go `TestSpecCommitMatchesLock`). "Correct" for the pin is checkable only against the **unpushed** spec commit |
| M2.5 | **Met:** `go-function-in-host` has reference-in-candidate 14/14 against Jaccard 14/39, in both lanes. The fixture lives in `research/drafts` |
| M2.8 | **Met for both CLIs** (§5) |
| M2.9 | **Not met.** Neither lane records candidate generation in a separate record keyed by `bodySha256`, and no index exists, so the "2 fixtures, two retrieval paths" clause is open. Present: rank and score fields are rejected by both validators (my test); Go `TestRankFieldsRejected`/`TestCandidateOrderIrrelevant` (Rust has no M2.9 test); order irrelevance holds structurally (§5.3 id order) |
| M2.10 | **Met, conditional on OD-C5:** `go-boilerplate-suppressed`, `go-invariance-three-references`/`-plus-unrelated`, `go-suppression-digest-mismatch`, both lanes; sabotages R1/G1 are caught. The vectors live in `research/drafts` |
| M2.11 | **Met, conditional on the contract decision:** `go-repeated-hash-self` gives below-minimum in both modes; at exactly the minimum, `rv-gap-equal` and 5 more give match, in both lanes; sabotages R2/G2 are caught |

**Blocked only by the unpushed spec commit or by vectors in `research/drafts`:** M2.4 (pin correctness), M2.5, M2.10 and M2.11 (their vectors are not in `test-vectors/`, which only M2.6 requires), and the M2.2 manifest's source.

## 8. README and commits

**Commits.** The 23 commits `b43caa9..82b02ab` (single author) carry no AI trailer or attribution (the one "cursor" hit is a JSON cursor), the diff (89 files, +16,280) has no secrets, keys or tokens, and no `/Users/…` or scratch path appears in tracked files or results.

**README claims are limited** (no detection, calibration, privacy or stable-pin claims) but have four inaccuracies (F4): line 30 says "amendments A1–A4" though the code implements A5; "every JSON file (42)" where `spec.lock` has 43; "Layout" omits `tw-json`, `tw-catalogue`, `tw-compare`, `tw-store`; and "about 20,000 cases per seed" (§3).

## Findings

All are low severity and none blocks the fast-forward.
- **F1 (Go CLI).** `-out -` writes a file named `-` in the current directory, while Rust's `--out -` means stdout. Fix: treat `-` as stdout in Go, or refuse it.
- **F2 (both).** A killed atomic write leaves `.<name>.tmp.*` holding partial private content in the private directory. M2.8 allows this, since nothing partial reaches the final path. Fix: remove stale temporary files on the next write, or document them.
- **F3 (Go).** Record-schema errors echo unknown key names from the input record to stderr. Fix: report only the path depth or a count, as Rust does.
- **F4 (README).** Change "A1–A4" to A1–A5, 42 files to 43, add the four I2 crates to "Layout", and give the I2 case count per scale.
- **Spec nit.** Contract §2b says six channel negatives; `comparison-config-negative-channels.json` has 5.
- **Test gap (Rust).** Add unit tests for suppression, distinct evidence and ambiguity before the cap, so that `cargo test` catches R1–R3 without the vendored vectors.

## Confirmation: post-i2

Branch `post-i2` at `f955fc1` (contract A6–A9 through spec `f0da1f0`); `82b02ab` is an ancestor. Scratch clones only; probes are `<scratch>/post.sh` and `post2.sh`. **Verdict: listed fixes first.** Fix P1 and P2 below; everything else holds.

1. **`scripts/offline scripts/check` exits 0** (1 min 26 s). The wrapper proved the denial first (loopback and 1.1.1.1 refused inside its sandbox), and the behaviour comparison reports 61/61 in both runners plus the one-harness item 61.
   Under my own outer sandbox the wrapper refused (exit 2, "denial NOT proven"): it fails closed, so I ran it outside my sandbox. **P3 (low):** in a detached-HEAD clone, the Go runner `go/tools/behaviourcheck` fails (`git clone`: "Remote branch HEAD not found") and all 61 Go items show MISSING. It passed once I put the clone on a branch.
2. **Checklist items I ran myself against both CLIs, same result in each:**
   - **43:** a stamped build writes a document naming `f955fc1` with body `998c64c2…`; a run-time commit option exits 2.
   - **44:** `DOC` exits 2 with no document for dirty-src and dirty-doc (Rust `cargo build`; Go `stampbuild` refuses with exit 1, and its plain build exits 2); the bodies are identical; `go run` writes no document.
   - **45, 55, 59:** an archive export built outside any repository, untracked inside another repository, or inside that repository's ignored folder: no document, identical body (Go `stampbuild` exit 1, plain build and `-buildvcs=false` exit 2).
   - **60:** a plain `go build` or `go run` in a clean clone writes no document.
   - **54:** `TRACEWEAVE_BUILD_COMMIT` and `TRACEWEAVE_IMPL_COMMIT` are ignored. **39:** `-` means stdout, and no file named `-` is created.
   - **23, 24:** with the `_FOSSIL_` and `.fslckout` markers present, both exit 2 and write no file.
   - **47, 48:** after SIGKILL one `TMP(OUT)` file remains; the next normal build removes it and leaves `.other.json.tw-tmp-x` untouched.
   - **51:** a symlink target is replaced by a regular file and the victim is unchanged. **52:** a symlink into a checkout gives exit 2. **57:** the canary key appears in no output.
3. **M2.4 as worded, with rule B10: met for both CLIs** on the normal build routes. A second fresh clean clone of `f955fc1`, rebuilt (Rust `cargo build --release`, Go `go run ./tools/stampbuild`), gives a byte-identical body (`998c64c2…`, equal to the vector's `bodySha256`) and the commit `f955fc1`. `comparisonConfigSha256` is in `inputs`. The commit's correctness is undermined only by P1 and P2.
4. **A document whose commit does not describe the code.** I changed `<= mergeGap` to `<` in `compare.rs`/`compare.go` of a clean clone and built:
   - **P1 (both lanes, blocking):** with `git update-index --assume-unchanged` or `--skip-worktree` on the edited files, `git status --porcelain` is empty. Rust `cargo build` and Go `stampbuild` then stamp **clean `f955fc1`**, and the documents name `f955fc1` while their body is `a6d7fd1c…`, not `998c64c2…`.
     - **Fix:** stop trusting index flags. Refuse when `git ls-files -v` shows any `h`/`S` (lower-case) entry, or compare `git hash-object` of every tracked file with `git ls-files -s`.
   - **P2 (Go, blocking):** `stampbuild` sets `GOFLAGS=` empty, so the go command falls back to the `GOENV` file. A `GOENV` file with `GOFLAGS=-overlay=…` that replaces `compare.go` yields a stamped `f955fc1` document with body `a6d7fd1c…`.
     - **Fix:** build with `GOENV=off` (and `GOFLAGS=`), or refuse when `go env GOFLAGS` is not empty.
   - Add both routes as checklist items.
5. **Earlier follow-ups:**
   - **F1, F2, F3 resolved:** items 39, 48 (stale temporary files cleaned up) and 57 (neither lane echoes the key).
   - **F4 mostly resolved:** the README now says A1–A9, 43 files and lists the I2 crates; "about 20,000 cases per seed" (line 62) still needs `--scale 2`.
   - **Rust test gap resolved:** `crates/tw-compare/tests/sabotage.rs` has 3 tests. I applied my R2 sabotage, and `cargo test --test sabotage` fails on `evidence_counts_distinct_hashes_not_seeds`.
6. **Commits:** the 29 commits `82b02ab..f955fc1` (single author; 53 files, +4,715/−567) carry no AI attribution or trailer, no secrets or keys, and no `/Users/…` or scratch paths.

**Gates, as worded:**
- **M2.1 met on macOS:** `scripts/offline` proves the denial, and `scripts/check` (extract, catalogue, compare and document steps across conformance and the checklist) passes under it. It refuses rather than run unconfined on other systems; a Linux equivalent is not provided.
- **M2.2 open:** no frozen manifest; the cases are in `research/drafts` at an unpushed commit. **M2.3 open:** the vendor class (OD-C19) is missing. **M2.7 open:** no review-packet record or schema exists.
- **M2.9 open:** there is no candidate-generation record keyed by `bodySha256` and no index; rank-field rejection and order irrelevance hold, as before.

## Confirmation 2: post-i2

Branch `post-i2` at `c05fe64` (B10 by content, spec `33e12f8`; checklist 64 items). Scratch clones only; probes `<scratch>/post3.sh`, `nd.sh`, `race.sh`. **Verdict: listed fixes first.** One Go route (G-R1) still produces a document whose commit does not describe the code; the fix is one line. Everything else holds.

1. **P1 and P2 re-run as before:**
   - **P1** (`--assume-unchanged`, `--skip-worktree` on `<=`→`<` mergeGap edits): Rust exits 2 with no document ("built from c05fe64 … with uncommitted changes"); Go `stampbuild` refuses.
   - **P2** (a `GOENV` file with `GOFLAGS=-overlay`): `stampbuild` refuses ("go env reports GOFLAGS"). Both closed.
   - **Control:** a clean clone gives a document naming `c05fe64` with body `998c64c2…`, the vector's `bodySha256`, in both lanes.
2. **New routes** (I read both route tables first; out-of-scope classes skipped):
   - **G-R1 (Go, not listed; FORGERY):** `stampbuild` resolves `head` with `rev-parse HEAD^{commit}` but lists the tree with `ls-tree … "HEAD"` (`go/tools/stampbuild/main.go:146`). I committed the edit as Y on a detached clone, left the working tree at Y, and flipped HEAD X↔Y with `git update-ref` during `stampbuild`. Outcome over 40 runs:
     - **2/40 wrote a document naming `c05fe64` (X) with body `a6d7fd1c…`** (Y's code);
     - 11 named Y honestly, and 27 were refused (HEAD moved, staged changes, content differs).
     - The end-of-build `head2 == head` check misses an X→Y→X flip. **Fix:** list and export the tree of the resolved id (`ls-tree <head>`, as Rust does at `build.rs:210`), so a mid-build HEAD change cannot mix ids. Add the route to `scripts/forgery-selftest`.
   - **R-R1 (Rust; closed):** after a clean build I added an untracked `crates/tw-compare/build.rs`, back-dated (`touch -t 2000…`) with the directory mtime restored. Cargo auto-discovers and runs it, and it rewrote `compare.rs` mid-build; I restored the tree afterwards. The stamp check still re-ran, and the binary refuses documents (exit 2).
   - **R-R2 (Rust; immune by construction):** the same HEAD flip cannot work, because Rust verifies the resolved commit's tree against the working tree.
   - **Not attempted, since the contract or lanes already class them:** another `GOROOT` or `rustc`, a tampered `target/`, edited registry sources, `cargo --config` source replacement, and edits during the build.
3. **P3 fixed:** in a detached-HEAD clone, `scripts/offline scripts/check` exits 0 (4 min 33 s; denial proven), with 64/64 items in both CLIs.
4. **`scripts/forgery-selftest`:**
   - `--rev f955fc1`: **12 FORGERY lines** (Rust 7, Go 5), exit 1.
   - at `c05fe64`: every route `ok`, "no forged document; every route exercised", exit 0.
   - G-R1 is not among its ten routes.
5. **Contract out-of-scope statement** (§6.8 B10, spec `33e12f8`): honest. It calls provenance "evidence about cooperative builds … not a security boundary" and defers adversarial binding to M4 attestation. It is not sufficient as worded: concurrent changes to repository state during the build are neither listed as out of scope nor closed in Go. Add them, or close G-R1 and say so.
   - **M2.4 as worded:** met for both CLIs on cooperative routes (a fresh clean clone of `c05fe64` gives an identical body, `bodySha256` and commit). It holds against the forgery routes except G-R1.
6. **Commits:** the 10 commits `f955fc1..c05fe64` (single author; 24 files, +1,910/−271) carry no AI attribution, secrets or local paths.
