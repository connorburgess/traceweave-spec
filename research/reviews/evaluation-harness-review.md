# Non-author review: M3 evaluation harness (`eval/`, traceweave `i3-eval` at c91ee91)

Reviewed 2026-11-23 against protocol `m3-eval-draft-5` and `evaluation-corpus/IMPLEMENTING.md` (roadmap-v2). I wrote none of the harness. All work ran in scratch clones under `$TMPDIR`: no worktree was modified, nothing was fetched from the network, and nothing ran on corpus data. Binaries: clean stamped builds of 82b02ab (the harness's base) and of current main e41f200 (§8). Toolchain: rustfmt 1.9.0 from Rust 1.97.1, Python 3.14.

**Verdict: listed fixes first.** B1–B3 must be fixed before acquisition, and B4–B6 before the pilot (see the last section).

## 1. Conformance, section by section

**Conforms** (code read; items marked † were also exercised by my own corpus, §3):
- Walk and replacements: rules 1–3 replayed, at most 8 replacements per language †. Licence recheck fails closed on the file set, blob SHA-1, SHA-256, length and classification.
- Eligibility: path, generated and lexing rules; within-repository duplicates; the 5%/25% exclusion bound † (it tripped).
- Grouping: Go `require` exact † and prefix; Rust `package =` and git URLs, normalised by lowercasing and stripping `.git` and `/` †; SHA-256 and token-digest duplicates † (a byte-identical ≥ 1,024-byte file was rejected and replaced).
- Split, fold and selection salts. Suppression from fold S only †.
- Pilot: fold-S outcome table and the pre-declared rule † (it fired, giving 288 configurations).
- Tuning: the 192/288 grid with seed sharing and the 1-in-50 direct check; the §5.4 rule (`alarms × 40 ≤ N_E`) and its tie order.
- Freeze contents per §8; ancestry commands plus a non-empty check; held-out refusals; the identity record.
- Held-out: pair caching (1 in 50) and symmetry (1 in 10); abstentions and `not-compared` pairs as alarms (`twe/bodies.py:140-151`).
- Abort rules; counts with Wilson, Clopper–Pearson, leave-one-repository-out and disjoint bounds; exit codes 0/3/2; the audit only after a committed verdict; reproduction.

**Does what the protocol does not say.** Each is acceptable, but must be written into the protocol before its digest is filled in: every output from both CLIs (A2); `wait4` instead of `/usr/bin/time` (A3); the pilot's own 1-in-50 check; `extract` computes held-out fingerprints before the freeze and discards them unread, against the letter of §2 (A1); held-out generation refuses if `eval/` changed since the freeze (A17); this caught my post-freeze sabotage, so it is a good rule; the `u()` strings and namespaces (A7), which change bytes M3.5 must reproduce.

**Omits or departs:**
- **Memory abort (§5.5):** checked from `ru_maxrss` only after a child exits (`twe/common.py:290`), so a runaway comparison is never stopped; the harness's own Python process is never measured.
- **Check rates (§9):** `checkModuli` is a recorded constant; nothing verifies that the number of checked searches matches the ids (S-b, §4).
- **Run budget (§5.5):** the estimate uses single-pair process timings and leaves out the direct checks (A19, §6).
- **`rename` numbering:** by first binding site (A8), where §6.3 says "first occurrence"; the two differ when a name is used before it is bound. Needs a ruling.

## 2. Leakage

**Held-out data into tuning or the freeze: no new path found.** The author's garbage-checkout leak test passed in my run. By code reading, held-out data reaches tuning outputs only through `pilot.py:150-164`: held-out file counts set `estimates.heldoutSeconds`, which `freeze.json` records. The grid reduction uses only the tuning estimate, so the configuration cannot change. The split depends on held-out content through the acquisition-time rules, as intended.

**The verdict changes without the counts changing: demonstrated.** `m36-verdict.py:40-41` takes A and N from `counts.json`'s `verdictInputs`. It does not cross-check them against the per-language figures in the same file, does not require a clean tree, and does not read the committed file. On my end-to-end clone I set `verdictInputs.alarmedSearches` to 0 and `exclusionBoundExceeded` to false, uncommitted, while `languages.*.negative` still said 1 + 1 alarms and the bound exceeded. The script printed "M3.6: met" and exited 0. Only M3.5 would catch this, after the fact.

## 3. My own synthetic corpus (independent generator; counts predicted before the run)

The generator (scratch, not committed) builds 13 Go and 11 Rust local repositories: each repository has its own marker (a Go operator or a Rust keyword) in every 5-token window, with non-periodic statement shapes; a token-stream check found no adjacent shared normalized 5-grams across repositories; every repository has a boilerplate file with the same normalized stream but different identifiers, so the duplicate rule does not catch it; held-out: a verbatim function copy and a renamed, re-indented near-duplicate; walk: an exact-`require` link; a git-URL link written `https://github.com/<OWNER>/<repo>.git/`; MIT plus a GPL `COPYING` among the replacements; exclusions: invalid UTF-8, NUL, an unterminated string, an unbalanced delimiter, generated files, path rules and a file under 16 tokens.

**Two predictions were wrong, both through my generator.** A "too few eligible files" repository still had 10 files that lex, so it was accepted. My Rust planted file had no framing, so it was byte-identical to its source and was rightly rejected as `duplicate-content` and replaced.

**After recomputing from the actual walk, every count matched:** 4 acquisition findings (Go dependency, Go licence, Rust dependency, Rust duplicate); grid branch 288, because the conservative configuration alarms in 1 of 1 fold-S searches per language; T = 3 and 5 empty, T = 2 non-empty; `k5-w8-m6-T2` selected by rule 2; held-out A = 2 of N = 12: the Go copy alarms in exact and normalized, the Rust near-duplicate in normalized only, and the boilerplate is fully suppressed; per-repository exclusions all as planted; Go lex-error plus under-16 = 4 of 55 (7.3%), so **M3.6 is an error (exit 2)**, as predicted; 28 caching checks and 1 symmetry check, 0 differences; ancestry exit 0.

**A26 is material.** Rust T = 2 suppression dropped 8 of 15 frequent snippets at k5-w4 and 44 of 81 at k16-w4. A frequent k-gram with an unbalanced `(` or `{` cannot be suppressed, and real Rust boilerplate (`) -> Result<…> {`) is like that.

## 4. Author tests and my sabotages

**Author suite (82b02ab binaries): 131 checks passed, 0 failed.** That is 60 unit checks, 52 end-to-end, 2 determinism, 1 leak, and the control plus sabotages S01–S11c. The run then died in sabotage setup with ENOSPC (the volume was full), so **S12–S25 were not verified by me**. The suite needs about 6–8 GB of scratch space, which TESTING.md does not say. `test_units.py` alone passes with 0 failures on both the 82b02ab and the e41f200 binaries.

| # | Sabotage (not in the author's list) | Result |
| --- | --- | --- |
| S-a | Abstentions not counted as alarms (`twe/bodies.py:149`) | **Not caught.** Unit tests pass; no end-to-end assertion covers an abstaining search |
| S-b | Symmetry sampled 1 in 10,000, committed **before** the freeze (`heldout-run.py:89`) | **Not caught.** `symmetry.checked` = 0 while the recorded moduli still say 10. After the freeze the same edit is refused (A17) |
| S-c | Suppression from fold S plus fold E (`build-suppression.py:135`) | **Not caught before the freeze.** The selection moves from `T2` to `T3` with exit 0; only M3.5's `--frozen` rebuild would differ, after held-out results exist |

## 5. Acquisition safety (`acquire.py`, `twe/corpus.py`, `licence-recheck.py`, `group-split.py`)

- **Network:** only `https://github.com/<fullName>`, through `git fetch --depth 1 --no-tags` and `git ls-remote` for replacements; no API calls and no timeouts.
- **Writes:** only `TRACEWEAVE_EVAL_DIR` (absolute and outside every working tree, enforced) and the `eval/` records. Child stdout, which includes extraction records with corpus tokens, also passes through unlinked files in the system temp directory (`twe/common.py:275`).
- **Execution:** no repository code can run. Hooks go to `/dev/null`, the template is empty, LFS filters are emptied, fsmonitor is off, submodules are not recursed, rustfmt gets an empty `--config-path`, and the CLIs only lex.
- **Checked-out bytes, not committed blobs, are hashed, lexed and fingerprinted** (`twe/corpus.py:96,113,179,315`). A repository's own `.gitattributes` changes them: I reproduced this with `ident` (a 30-byte blob read as 73 bytes) and `eol=crlf`. The operator's global `core.autocrlf` changes them too, which breaks M3.5 across machines, and a CRLF rule on a LICENSE file gives a false fail-closed stop.
- **Other git problems:** no isolation from the operator's global and system configuration (`url.insteadOf`, credential helpers, `filter.*.process`, proxies); `protocol.allow=always` (`twe/corpus.py:17`) permits every transport, `ext::` included; no `GIT_TERMINAL_PROMPT=0`, so a deleted repository can hang on a prompt; reads go through the working tree, so a case-insensitive symlink collision could redirect one.
- Hostile paths, filenames and sizes are otherwise handled: `-z` listings, non-UTF-8 paths and symlinks excluded, per-file size bounded by GitHub's limits.

## 6. Cost on one laptop

Per-pair cost of a batched `compare`, measured on standard-library code that is not in the corpus: two Go standard-library directories, about 10,000 pairs, on a 48 GiB machine with 18 cores.

| Setting | Rust CLI | Go CLI | Peak RSS (Rust / Go CLI) |
| --- | --- | --- | --- |
| k5 w4 | 3.6–4.1 ms per pair | 5.9–8.7 ms per pair | 5.9 / 10.8 GiB at 10,000 pairs; 2.7 / 8.2 GiB at 4,455 |
| k8 w8 | 0.7 ms | 1.4 ms | 0.5 / 1.4 GiB |
| k16 w16 | 0.3–0.4 ms | 0.6–0.7 ms | under 0.2 GiB |

The protocol assumes 1 ms per pair; with both CLIs, k5 w4 costs about 10–13 ms. Over the 12 settings that comes to an estimated 22–48 ms per pair. Report bodies measured about 17 KB per pair at k8 w8.

| Stage | Estimate |
| --- | --- |
| Pilot | 4–8.5 h of fold-S comparisons (0.64 M pairs), plus about 6 h of direct checks (154 k pairs × 6 configurations × about 25 ms; `twe/grid.py:69` runs one compare per configuration per pair) |
| Tuning | 4.5–10 h of comparisons (0.73 M fold-E pairs), plus **20 h (192 configurations) or 29 h (288)** of direct checks |
| Held-out | 1–10 h, depending on the frozen k |
| Memory | Rust CLI about 0.6 MB per pair at k5 w4, so an average Go fold-S search of about 33 k pairs needs about 20 GB. The largest searches can cross the 75% line (36 GiB here; certainly on a 16–32 GB laptop). Measured on related code; unrelated repositories will produce fewer seeds |
| Disk | Catalogues about 5× source at k5. Held-out bodies are kept: 2–17 KB per pair × 2.25 M pairs is 5–38 GB, against the protocol's 5–6 GB |

**Will the 24-hour rule trigger? Yes, for the wrong reason.** The pilot times single pairs including process start; the author measured 24–39 ms per pair on synthetic code, so the estimate is about 0.73 M × 12 × 30 ms ≈ 73 h. That removes window 16, k 8 and k 12, and probably window 8. The real comparison cost would fit in 24 h; the direct checks, which the estimate omits, are what exceed it. The inflated estimate also means the 3× wall-time abort will practically never fire.

## 7. The author's recorded ambiguities

- **Agree:** A1 (record the ruling in the protocol), A2, A3, A5, A9, A13, A16, A17, A18, A20, A21, A28, A30, A36.
- **A6:** agree; with 3 fold-S groups, T = 3 and 5 are always empty, so the protocol should say so.
- **A7:** the strings must go into the protocol before its digest is filled in.
- **A8:** a departure from §6.3; needs a ruling.
- **A10, A12:** accept the letter as written, with vectors.
- **A19:** wrong in effect (§6).
- **A25:** blocks M3.2 if any repository falls below 10 files after the content rules (likely for `py-spy`-like repositories); `verify_manifest.py` needs a post-content-rule count fact.
- **A26:** accept, and report the dropped counts per T.

## 8. Running on current main (e41f200)

- **Build:** use `python3 -I tools/stamped-build/stamped-build --release --out BIN/traceweave` and, from `go/`, `GOENV=off GOFLAGS= GOTOOLCHAIN=local go run ./tools/stampbuild -o BIN/traceweave-go`. A plain build is unstamped.
- **Go commit reader:** `stampbuild` builds with `-buildvcs=false -ldflags "-X main.buildCommit=…"`, so `go version -m` shows no `vcs.revision`. `twe/impls.py:35` then exits 2 on every stage; I confirmed this with an e41f200 build. A supported reader is needed, for example a `traceweave-go --version` in the Rust format. The Rust reader works as is.
**Compatibility:** the unit tests pass with e41f200 binaries, so the commands the harness drives are unchanged. **Pinning:** rebase `i3-eval` onto main, and build both binaries from one clean checkout of the chosen commit; that commit becomes the acquisition lexing commit.

## Blocking, and the sequence through the freeze

| # | Fix | Owner |
| --- | --- | --- |
| B1 | Go stamp reader and stamped build steps (§8) | harness author, with a main change |
| B2 | Read blobs with `git cat-file` (verifying SHA-1), not the working tree. Run git with `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0`, `protocol.allow=never`, `protocol.https.allow=always` (`file` only in tests) and timeouts | harness author |
| B3 | A25: a post-content-rule count fact in `verify_manifest.py` | spec |
| B4 | Kill a child the moment it crosses 75% (a watchdog), not after it exits; measure the harness process too | harness author |
| B5 | Batch the direct checks (one compare per search and configuration over the checked files' catalogues) and include them in the estimate | harness author |
| B6 | Time batched comparisons in the pilot (or subtract measured process start); a protocol ruling on "per-pair time" | harness author, then spec |
| B7 | `m36-verdict.py` recomputes A, N and the bound from the per-search records, reads `counts.json` from the first held-out result commit, and refuses a dirty tree | harness author, before the freeze |
| B8 | Verify the checked-search counts against the ids; tests for S-a, S-b and S-c; record the fold-S list in the freeze and check it | harness author |

Then, with `TRACEWEAVE_EVAL_DIR=~/traceweave-eval` and the git environment from B2:
1. Build both binaries from one clean commit C. Copy `manifest-proposal.json` to `eval/manifest.json` and commit it (operator: not the harness author).
2. `acquire.py`; commit `acquisition.json` (operator).
3. `licence-recheck.py --verify-manifest …`; commit `licence-recheck.json` (operator). Exit 1 stops acquisition and needs the owner's re-approval.
4. `eligibility.py`; commit (operator).
5. `group-split.py`; commit the manifest, `splits.tsv`, `splits.tsv.sha256` and `group-split.json` (operator). A non-author runs `verify_manifest.py` on the updated manifest and `shasum -a 256 -c eval/splits.tsv.sha256`, and records exit 0 (M3.2).
6. `pilot.py` with 1,000 pairs; commit `pilot.json` and `pilot-fold-s.md` (operator). A non-author checks the grid branch and the reduction against the rule.
7. Spec repository: write the A1, A7 and A8 rulings and the cost corrections into the protocol, then fill in and commit its digest (spec author; reviewed by a non-author).
8. `generate-cases.py --namespace tuning`, then `build-suppression.py`, committing after each; then `tune.py`, **without** committing its table yet (operator).
9. `freeze.py … --budget-commit <M3.0> --labeller L1 --second-labeller L2`; commit `tuning-table.json` and `freeze.json` together (operator). L1 and L2 are named by the coordinator, are not the harness author, and do nothing until the verdict is committed.
