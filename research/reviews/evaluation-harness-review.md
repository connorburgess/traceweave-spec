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


## Confirmation pass (i3-eval d4502e0 on main e41f200; protocol m3-eval-draft-6, a17fc22)

**Method.** Scratch clones only, free space checked first (11–17 GB; the harness's own 20 GB margin had to be lowered to 9 GB for the synthetic runs). Binaries: stamped e41f200, plus a second stamped pair at d4502e0 for N3. I re-ran my generator, with its two bugs fixed, against the draft-6 text. Roadmap-v2 is already at **draft-7** (e3bac86, O1–O8), while the harness still says `m3-eval-draft-6`.

**Earlier findings.**
- **Resolved:** **B1** (commit read from each binary's report-document provenance, one stamped commit for both; `twe/impls.py:20-72`); **B3** (`verify_manifest.py` exits 0 on my acquired manifest with a too-few rejection); **B6** (batched timing: estimate 381 s, actual 291 s); **B8** (check rates verified from ids, fold-S list checked, builder refuses non-fold-S).
- **B2 resolved,** with a residual: bare repositories, isolated git, https only, timeouts, `cat-file` with SHA-1 recomputed, unsafe and case-colliding paths excluded (`twe/corpus.py:34-110,131-209`). Materialized copies are re-verified only in `twe/state.py:37-42,104` and the held-out run, not in eligibility, the pilot or catalogue builds (N1).
- **B4 partial:** the watchdog polls and includes the harness (`twe/common.py:379-394`), but large-search splitting is not implemented, so a large k5 search is killed, not split.
- **B5 not resolved in effect:** the batch is checked reference files × checked candidate files (`twe/grid.py:70-107`). With 1-in-50 pair sampling that is 53%, 86% and 97% of a 64², 128² and 200² search, under every configuration, while `pilot.py`'s `estimate` charges only `configs × checked`, about 25–48× too little.
- **B7 resolved except one hole:** the verdict reads committed records with `git show`, refuses a dirty tree, recomputes and cross-checks every summary (`m36-verdict.py:81-208`); uncommitted or later edits give exit 2. But a doctored, fully consistent **first** result commit gives **"met", exit 0, when `TRACEWEAVE_EVAL_DIR` is unset or empty**, because the body check is skipped silently. It is caught when the bodies are reachable.
- **A26** implemented, with collateral hashes reported (Go: 1 fallback file, 132 exact).

**Sabotages.**
- **Caught:** S-b (symmetry skipped before the freeze: `heldout-run.py` exit 2, 0 of 2); S-c (suppression from S plus E: builder exit 1).
- **Caught late:** S-a (abstentions not counted) silently froze `Tnone` instead of `T2`, and was caught only at M3.6 by the independent body alarm rule. N1 (`.rs` materialized as CRLF): eligibility, split and pilot ran on the altered bytes; tuning case generation stopped with exit 1.
- **Not caught:** N2 (a fold-E file added as a fallback: exit 0 through the freeze, and M3.5 reruns the same code); N3 (pilot and tuning on stamped d4502e0 binaries, freeze on e41f200: `pilot.json` and `tuning-table.json` record the other commit, and nothing compares it).

**My corpus.** Every predicted count matched: the findings (Go dependency, too-few, licence; Rust dependency); the final sets and split; the acquired manifest valid; branch 288; `k5-w4-m6-T2` by rule 2; A = 4 of 12, each pair in its predicted modes; symmetry 2 of the 2 predicted; 27 caching checks, 0 differences; 2 of 56 excluded per language; **negative-result, exit 3**. Not predicted, but explained by my generator: pair-level `ambiguous` abstentions inside searches that already alarm, and rustfmt, `rename` and `compound` generation failures.

**Safety.** Network only to `https://github.com/<fullName>`; writes only under `TRACEWEAVE_EVAL_DIR` and `eval/`; no repository code runs; hostile paths, symlinks, submodules and case collisions excluded.

**Cost on the real corpus** (22–48 ms per pair over 12 settings, both CLIs):
- **With the current batching:** pilot 26–58 h (outcome count 4–9 h plus 22–49 h of checks); tuning 40–80 h at 192 configurations or 60–130 h at 288; held-out 1–10 h.
- **With a per-reference-file sample:** pilot about 5–10 h, tuning 6–15 h.
- **What happens:** the estimate says about 6–12 h, so the 24-hour rule will **not** trigger, but the **3× wall-time abort will stop tuning**, and large k5 searches may hit the watchdog.
- **Disk:** derived data 10–45 GB (catalogues 2–3 GB, bodies 2–17 KB per pair). With the 20 GB margin the run needs **about 65 GB free; this machine has 11–17 GB, not enough**.

**Verdict: remaining blocking items.** Before the pilot: (1) a per-reference-file check sample, or batches of only the checked pairs, with an honest estimate (a §5.3/§5.5 change); (2) reference-batch splitting; (3) about 65 GB free. Before the freeze: (4) refuse the verdict unless every body is re-checked; (5) the freeze checks that pilot, suppression and tuning used the acquisition lexing commit; (6) record each fallback file's repository and SHA-256 and check it is fold S; (7) verify materialized bytes at every read; (8) align with draft-7. Acquisition may start after (8) and once the disk is freed.

**Sequence.** The **operator** (a non-author of the harness) builds both binaries with `tools/stamped-build` and `go/tools/stampbuild` from one clean commit C, then runs `acquire`, `licence-recheck` (exit 1 needs owner re-approval), `eligibility` and `group-split`, committing after each. A **non-author** runs `verify_manifest.py` and `shasum -c` (M3.2). **Operator:** `pilot`, then a **non-author** checks the branch and the reduction. **Spec author:** fills in the digest at the final draft. **Operator:** `generate-cases` (tuning), `build-suppression`, `tune`, then `freeze` with the labellers the **coordinator** names, committing `tuning-table.json` and `freeze.json` together; then `generate-cases` (held-out), `heldout-run` and `counts` as one commit; then `ancestry` and `m36-verdict --record` with the bodies reachable, committing `verdict.json`. The **labellers** label after `alarm-audit items`, and the operator commits `alarm-audit record`. A **second person** runs `reproduce` in a clean clone with a fresh root (M3.5).


## Confirmation pass 2 (i3-eval 75b84eb; protocol text at e3bac86, draft-7)

**Method.** Scratch only, about 12–13 GB free, with the margin lowered to 9 GB for the synthetic runs. Binaries: stamped e41f200 (X), stamped 75b84eb (for N3) and stamped 6d35308 (for main).

**Claims.**
- **Resolved:** direct check of exactly the selected pairs, one compare per checked reference file and configuration, with a pair-count check (`twe/grid.py:116-146`). The freeze checks the checked count against the ids, which caught N5. Measured over estimated on my run: tuning 341/373 s (0.91), held-out 13/29 s (0.45); re-verification against blob ids at every stage that reads (`twe/state.py:38-49`; N1 is now caught at acquisition); the verdict exits 2 without the bodies unless `--bodies-unavailable` is given (`m36-verdict.py:13,120,144`; checked: an empty root gives one error per missing body); the binary commit of every stage is checked (`freeze.py:108-112`; N3 is caught at the pilot); fallback provenance (`freeze.py:124-130`; N2 is caught by the builder); a relocated root is resolved through symlinks (`twe/common.py:154,170`).
- **Not resolved:** batching (`twe/batching.py:49-73`) assembles chunks without checking that the body holds exactly references × candidates distinct pairs (N4).
- **Disk claim** (2–5.5 GB, about 26 GB free): consistent with the README's stage table; not measured on data. **This machine has 12–13 GB free, which is not enough.**
- **Version lag:** the harness says `m3-eval-draft-7` (`twe/common.py:17`), but roadmap-v2 is now **draft-8** (a405f67). Draft-8 rules the 75b84eb behaviour and adds a 10 GB minimum margin, so the harness needs a version bump. Draft-8 also says the unbatched held-out caching check "is what checks batching", but that check covers positive cases only, while N4 is in negative searches.

**My corpus, end to end.** Every predicted count matched again: 4 findings; the acquired manifest valid; branch 288; `k5-w4-m6-T2` by rule 2; A = 4 of 12 (the copy in exact and normalized, the near-duplicate in normalized only), with all 12 bodies re-checked; symmetry 2 of the 2 predicted; 27 caching checks, 0 differences; 2 of 56 excluded per language; negative-result, exit 3.

**Sabotages.**
- **Caught:** S-a (abstentions not counted) at the start of tuning (exit 2: the two alarm rules disagree on fixed vectors); S-b (symmetry skipped) by the held-out run (exit 2); S-c and N2 (fold-E sources) by the builder (exit 1); N1 (CRLF) at acquisition (exit 1); N3 (binaries of another commit) at the pilot (exit 1).
- **New, caught:** N5 (direct check selecting zero pairs in negative searches) at the freeze (exit 1: 240 checked, 324 selected).
- **New, not caught: N4**, a batch boundary appending one pair, run with `--max-pairs-per-comparison 40` (24 tuning and 34 held-out batched comparisons). Compared negative pairs went from 1,093 to 1,131 per language, and `pairs.jsonl.gz` gained 76 duplicates, yet freeze, held-out run, counts and the verdict all passed (exit 3). A dropping variant could hide an alarm.

**Main 6d35308.** The stamped binaries are read correctly and the unit tests pass (0 failures). Since e41f200 the CLIs changed only vendored test paths, so a rebase and binaries built there suffice. The published spec pin (`c06b214`) carries protocol draft-5, so `--protocol` and `--spec-repo` must name the spec commit that freezes the final draft, not the pin.

**Cost on the real corpus.** Inputs: 22–48 ms per pair over 12 settings for both CLIs, and about 31 ms of process start per one-file compare (the pilot's `startMs`). Direct checks are about 110 reference files per fold-E search and 135 per fold-S search, each × configurations × 31 ms.

| Stage | Estimate |
| --- | --- |
| Pilot | 7–12 h (outcome count 4–8.5 h, direct checks about 3 h) |
| Tuning, 192 configurations | 12–17 h (comparisons 4.5–10 h, direct checks about 7 h) |
| Tuning, 288 configurations | 15–20 h (direct checks about 10 h) |
| Held-out | 1.5–17 h, depending on the frozen k (unbatched caching checks up to about 5.5 h at k 5) |

The 24-hour rule should not trigger, and is close only at the top of the 288 range. The 3× abort should not fire, given ratios of 0.45–0.91.

**Verdict: remaining blocking items.** (1) Before the pilot, in `twe/batching.py`, check that the assembled pairs equal the reference × candidate set with no duplicates, in every search, with N4 as a test. (2) Bump the harness to draft-8, with the 10 GB minimum. (3) Free about 26 GB on the run machine. Then acquisition and the pilot may start, on binaries built at the rebased commit.

**Sequence (who commits).** The **operator** (not the harness author) builds both binaries with `tools/stamped-build` and `go/tools/stampbuild` at one clean commit C, then runs `acquire`, `licence-recheck` (exit 1 needs owner re-approval), `eligibility` and `group-split`, committing after each. A **non-author** runs `verify_manifest.py` and `shasum -a 256 -c eval/splits.tsv.sha256` (M3.2). **Operator:** `pilot`, then commit; a **non-author** checks the grid branch and the reduction. The **spec author** fills in the protocol digest at the final draft and commits. **Operator:** `generate-cases --namespace tuning` and `build-suppression`, committing each; `tune` (left uncommitted); then `freeze` with the labellers the **coordinator** names, committing `tuning-table.json` and `freeze.json` together. **Operator:** `generate-cases --namespace held-out`, `heldout-run` and `counts` as **one** commit; then `ancestry`, and `m36-verdict --record` with the bodies present; commit `verdict.json`. The **labellers** label after `alarm-audit items`; the operator commits `alarm-audit record`. A **second person** runs `reproduce` in a clean clone with a fresh root (M3.5).


## Final pass (i3-eval 07621b8 on main af3af2b; protocol m3-eval-draft-10, 41628be)

**Method.** Free space varied between 12 and 30 GB over the pass (other sessions share the disk); my scratch peaked at about 0.3 GB and is deleted. Binaries were built by RUNBOOK's setup at af3af2b (stamped), plus plain builds (unstamped) and a stamped Go at 720141d. I used scratch clones only, at a 10 GB margin. Faults were injected by an inert patch committed before step 0 and switched by environment variables: one pair appended, dropped or swapped (ids exchanged), in a negative search or a positive case, with one, two or three layers disabled.

**(1) N4.**
- **One layer disabled at a time:** all 24 combinations (3 faults × 2 places × 4 settings) are caught. The original N4, an appended pair at a batch boundary with 40 pairs per comparison, is `heldout-run.py` exit 2 ("assembled from 7 batches"), and so is a drop.
- **Runner off:** In negative searches, `counts.py` alone (exit 1) and the verdict alone (exit 2) each catch append, swap and a faithfully recorded drop. In positive cases, the verdict alone catches all three. **`counts.py` alone misses the swap** (exit 0, negative-result): `counts.py:428` compares counts, not the id digest. **Fix:** compare the whole record, as `m36-verdict.py:109` does. A drop that positive-case assembly needs dies as an unnamed `KeyError` (`heldout-run.py:205`, exit 1). With all three layers off, the faults pass, as expected.

**(2) Earlier findings.**
- On my corpus, run end to end through RUNBOOK on draft-10, **every predicted count matched**: 4 findings; the manifest valid; `k5-w4-m6-T2` by rule 2 (288 configurations); A = 4 of 12; symmetry 2/2; caching 27/0; 2 of 56 excluded per language; negative-result exit 3. Pair completeness held for 61 comparisons and 1,265 cases (22,964/22,964 pairs). Measured over estimated: tuning 260/349 s, held-out 12.9/27 s. The verdict still refuses without bodies and on a dirty tree (exit 2).
- The author's suite on my binaries: **213 of 216, 3 failed** (S19, N4c, N4d). In each, a setup stage exited 2 where 0 was expected (tuning after 957 s; held-out runs of 75–77 s against about 3 s elsewhere). This looks like the wall-time abort under load on a shared machine. It is **unconfirmed**: my rerun was stopped by the time limit at S05. My own N4c/N4d equivalents pass.

**(3) Margin rule and version gate.** Margins of 9, 9.99 and `abc` are refused (exit 2), and so is 50 GB on 14.8 GB free.; margin set 0.35 GB below free space, then an 0.8 GB fill: the pilot aborts mid-run (exit 2) and leaves nothing uncommitted.; `identity.json` records `freeSpaceMarginGb: 10`. **Version gate:** draft-9 (85b1690) and draft-5 (c06b214, the published pin) are refused, exit 1, by `tune.py` and `freeze.py`; draft-10 passes. **(4) Stamps** (`twe/impls.py:84-150`). The stamped pair reads as af3af2b. Refused, exit 1: an unstamped Rust or Go binary; af3af2b with 720141d ("different commits"); binaries swapped (wrong `name`).

**(5) RUNBOOK, followed literally** (only `--url-template file://…` and `--allow-file-urls` added, for local bare repositories). Steps 0–3, 5, 7–17 worked: alarm audit 49/49; M3.5 reproduced in 26 s.
- **Wrong (R1):** 4a's `shasum -a 256 -c eval/splits.tsv.sha256` fails from the repository root; it must run in `eval/`. **Ambiguous:** (R2) "a clean checkout of C (main, af3af2b or later)", but `eval/` is only on `i3-eval`: say which checkout holds the harness and records, and what C is. (R3) `<M3.0>` names no commit.
- **Missing:** (R4) step 16's label format, location and author (only `--help` has them). (R5) Step 17 elides the `--verify-manifest` path. **Inconsistent (R6):** step 17's time "as 1–13" overstates it, since it skips the pilot and tuning. README:277 says about 40 GB free, against 26 GB in README:47 and RUNBOOK.

**(6) Cost, real corpus (48 repositories); draft-10 adds only per-pair Python checks.**
- **Wall time:** acquire 10–30 min; eligibility and split < 1 h; pilot 7–12 h; tuning 12–20 h; held-out 1.5–17 h; counts and verdict 2–5 min each (4–28 GB of raw JSON); reproduction 2–18 h. **Disk:** at most 0.7, 0.1, 0.9, 0.2 and 0.3–3.5 GB per stage; bodies measured at 2.6 KB raw and 0.17 KB gzip per pair. 2–5.5 GB in all, so 16 GB free at the 10 GB margin, or 26 GB at 20.

**(7) Go/no-go before step 1.**
1. draft-10 is declared final; a later draft would change the harness mid-sequence. Its digest is filled at step 6 in the spec commit that `SPEC`, `--protocol` and `--spec-repo` name (not `c06b214`). 2. The M3.0 commit is named; R2 is decided; both binaries are stamped at C and agree. 3. At least 16 GB free (margin 10) or 26 GB (margin 20), held for the whole run, on an unsynchronized volume. 4. One named machine that stays awake through the 7–12 h and 12–20 h runs. 5. Named people: the operator (not the harness author); the non-author for 4a and the pilot check; the spec author for the digest; L1 and L2 (coordinator's choice, not the author); the M3.5 second person; the owner for a licence-recheck exit 1. 6. R1 fixed.

**Verdict: acquisition and the pilot may start once this checklist holds.** Blocking now: steady free disk (item 3), R1, R2 and M3.0, and the named people and machine. Before the freeze: the `counts.py` positive-case record check, and a clean rerun of S19, N4c and N4d.
