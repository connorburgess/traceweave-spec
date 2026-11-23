# Implementing the M3 evaluation harness

Brief for whoever builds the harness in the implementation repository (`traceweave`, owner column `I`), against protocol [`m3-eval-draft-10`](../evaluation-protocol.md). The protocol governs; this list only orders the work. Decided on 2026-11-23: budget **`1/20`** per unordered repository search, acquisition approved with mechanical replacements, corpus root `~/traceweave-eval` named by `TRACEWEAVE_EVAL_DIR`.

**Conventions for every script.**
- Exit status: 0 success, 1 a checked condition failed (invalid input, mismatch, refusal), 2 usage, environment, I/O or abort. M3.6 adds 3 (negative-result).
- `TRACEWEAVE_EVAL_DIR` must be absolute, and outside every version-controlled working tree (contract B1 markers); otherwise exit 2.
- Committed outputs go under `eval/` in the implementation repository and contain no corpus source bytes. Corpus files, catalogues, report bodies and case bytes stay under `TRACEWEAVE_EVAL_DIR`.
- JSON outputs are canonical: sorted keys, no insignificant whitespace, integers only where counts, and a final LF.
- Every script records its own commit and refuses a dirty work tree when writing a committed output.

## Scripts, in order

| # | Script | Inputs | Outputs | Protocol | Pass/fail observable |
| --- | --- | --- | --- | --- | --- |
| 1 | `acquire` | `eval/manifest.json` (copy of `manifest-proposal.json`), network to `github.com` | `$DIR/corpus/<lang>/<owner>/<repo>/` at each pinned revision (depth 1), `eval/acquisition.json` (per repository: revision, fetch time, path inventory with SHA-256 and length, acquisition lexing commit) | §3.6 | exit 0; every checkout's `HEAD` equals the manifest revision |
| 2 | `licence-recheck` | corpus checkouts, manifest | copies of root licence files under `$DIR/licences/<owner>/<repo>/`, then `verify_manifest.py --licence-dir` | §3.2, §3.6 step 1 | exit 0; **any** missing file, blob SHA-1, SHA-256, length or classification difference exits 1 and stops acquisition (fail closed, no replacement) |
| 3 | `eligibility` | corpus checkouts, acquisition lexing commit | per file: eligibility reason (path rules, `generated`, `lex-error`, `under-16-tokens`, `oversize`), token count, token digest; `eval/eligibility.json` with excluded counts per repository and reason and their denominators | §3.4 | exit 0; lexing commit equals the one in `acquisition.json`; the 5% per language / 25% per repository bound is checked again at script 11 |
| 4 | `group-split` | manifest walk and pool, `eligibility.json`, every `go.mod` and `Cargo.toml` outside excluded directories | walk continued with `dependency-linked` / `duplicate-content` rejections and replacements (with facts), updated manifest, `eval/splits.tsv`, split digest | §4.1–§4.4 | `verify_manifest.py` exit 0 on the updated manifest; at most 8 replacements per language (a ninth exits 1 and returns to the owner); `sha256sum eval/splits.tsv` equals the recorded digest (M3.2) |
| 5 | `pilot` (fold-S outcome count and timing) | all fold-S repositories, no suppression catalogue, the 12 (`k`, `window`) settings × every `minRegionDistinctHashes` (seed-shared) | `eval/pilot.json`: per configuration and language, searches with an alarm and counts per outcome class and code per mode; per-pair time median and 95th percentile and peak RSS on 1,000 pairs per language; the grid-rule branch (192 or 288 configurations); estimates and any grid reduction (order: `window` 16, `k` 8, `k` 12, `window` 8); report table "fold-S alarms by `k`, `window`, `minRegionDistinctHashes`" | §5.5 | exit 0; the grid rule is applied exactly as written (`k` 16, `window` 16, `minRegionDistinctHashes` 6: alarms × 2 > searches in either language adds 8 and 12); refuses to read fold-E or held-out files (exit 1) |
| 6 | `generate-cases` | source and host repositories of one split, namespace (`tuning` or `held-out`), generator salt | `cases-<lang>-<namespace>.jsonl` (offsets and digests), case bytes under `$DIR/cases/` | §6 (one function per transformation: `verbatim`, `ws`, `comments-strip`, `comments-add`, `fmt` (Rust only, `rustfmt --edition 2024 --config max_width=50,tab_spaces=2`), `rename`, `reorder`, `split-mix`, `compound`) | exit 0; a second implementation from §6 alone gives byte-identical `cases-*.jsonl` (`cmp`); `held-out` refused (exit 1) unless HEAD descends from the freeze commit and the tree is clean |
| 7 | `build-suppression` | fold-S eligible files, `k`, `window`, threshold *T* ∈ {2, 3, 5} | suppression catalogue per (language, `k`, `window`, *T*), its SHA-256, `snippet-dropped` count | §5.2 | exit 0; the catalogue validates (contract §3.6); rebuilding gives the same SHA-256 |
| 8 | `tune` | protocol digest (filled in, committed), `pilot.json`, fold-E catalogues for 12 (`k`, `window`) settings (fewer after a reduction), fold-E cases and searches, suppression catalogues, budget `1/20` | `eval/tuning-table.json` (one row per configuration of the 192 or 288: *a* per language, pooled and per alarm reason; *r* and cell counts; reportable regions per search; selecting rule); selected configuration | §5.3–§5.4 | refuses to start (exit 2) unless the protocol file's self-excluding digest equals the committed one; seed-sharing check on `u(pair id, 1) mod 50 = 0` pairs is byte-identical (else exit 2); exit 0 selected by rule 2 (`alarms × 40 ≤ N_E`), 3 by rule 3 |
| 9 | `freeze` | selection, `tuning-table.json`, split digest, manifest digest, configurations, suppression digests, pilot (with grid branch), tolerance, protocol digest, M3.0 commit, alarm-audit labeller and second labeller | `eval/freeze.json`, committed **in the same commit** as `tuning-table.json` | §5.4, §8, §12a | exit 0; refuses any budget other than `1/20` (exit 1); lexing commit equals `acquisition.json`'s; `tuning-table.json` digest recorded and the file present in the commit |
| 10 | `heldout-run` | `freeze.json`, held-out catalogues at the frozen configuration, held-out cases (script 6 after the freeze) | report bodies under `$DIR/derived/`, `eval/results/heldout/identity.json`, `resources.json` | §8, §9 | refuses to start (exit 1) unless HEAD descends from the freeze commit, the tree is clean and digests match; pair-caching check (1 in 50) and symmetry check (1 in 10) show 0 differences, else exit 2; abort rules of §5.5 exit 2 |
| 11 | `counts` | report bodies, `cases-*-held-out.jsonl`, `eligibility.json` | `eval/results/heldout/counts.json` (every §10 figure with numerator and denominator, excluded counts per repository and reason), report tables | §10, §11 | exit 0; schema check that every figure has a denominator; exclusion bound of §3.4 checked (over the bound is recorded and makes script 12 an error) |
| 12 | `m36-verdict` | `counts.json`, `freeze.json`, the §8 ancestry commands | printed verdict with *A*, *N*, `1/20`, intervals, operating characteristics, excluded counts | §12 | **exit 0 met** (`A × 20 ≤ N`; with N = 132, A ≤ 6), **exit 3 negative-result**, **exit 2 error** (N = 0, budget ≠ `1/20`, failed ancestry or lexing-commit check, exclusions over the bound, symmetry or caching difference, aborted run) |
| 12a | `alarm-audit` | report bodies and source files of alarmed held-out searches, labeller entries | `eval/results/heldout/alarm-audit.jsonl` (label `real-shared-code`, `boilerplate`, `accidental` or `abstention` per alarmed pair-mode and per search; second-labeller sample and agreement count) | §12a | runs only after script 12 has printed and recorded the verdict (exit 1 otherwise); exit 0 when every alarm has exactly one label; never writes `counts.json` or the verdict |
| 13 | `reproduce` | a clean clone at the first held-out result commit, a fresh `TRACEWEAVE_EVAL_DIR` | reruns scripts 1–4, 7 (frozen *T* only), 6 (`held-out`), 10, 11; resource comparison | §13 | exit 0 when the ancestry commands, licence recheck, split digest, suppression digests, `cases-*-held-out.jsonl` and `counts.json` all match byte for byte (`cmp`) and resources are within tolerance or "not comparable" on another platform |

The §8 ancestry check (M3.3) is the five shell lines in the protocol plus the lexing-commit equality; it can be a small script of its own, run by scripts 12 and 13.

## Order of commits

1. Scripts 1–4 and their outputs (`acquisition.json`, `eligibility.json`, updated manifest, `splits.tsv`): M3.1 and M3.2 evidence.
2. Script 5 output (`pilot.json`, with the fold-S table and the grid branch).
3. In this spec repository: the protocol digest filled in (the protocol freeze). Nothing tunes before this commit.
4. Scripts 6 (`tuning`), 7 and 8; then scripts 8 and 9 outputs (`tuning-table.json` and `freeze.json`) in one commit: M3.3.
5. Scripts 6 (`held-out`), 10 and 11 outputs: the first held-out result commit (M3.4).
6. Script 13 by a second person (M3.5); script 12 (M3.6), recorded in this repository; then script 12a (alarm audit).

Follow-up measurements (protocol §18: adversarial transformations, an LLM-rewrite arm, bag-of-tokens, keyed fingerprints, an existing open winnowing scanner) are **not** part of this harness and start only after the first held-out result commit.

## Changes the harness must make for draft-6

From the rulings in [protocol §19](../evaluation-protocol.md#19-harness-rulings-m3-eval-draft-6). In order of the stages they touch:

1. **Git and bytes (blob rule, B2).** Read every measured byte (source, licence, `go.mod`, `Cargo.toml`) with `git cat-file` from the pinned commit's tree, verifying each SHA-1; list paths with `git ls-tree -r -z`; never hash, lex or transform working-tree bytes. Run git with `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0`, `protocol.allow=never`, `protocol.https.allow=always` (`file` only in tests) and a timeout per call.
2. **Binaries (B1).** Read the commit from each binary's stamped version output, including a supported reader for the Go binary built by `stampbuild`; document the stamped build commands.
3. **Temporaries (A1).** Child output goes through files under `TRACEWEAVE_EVAL_DIR/tmp`, deleted after reading, not the system temp directory.
4. **Manifest (A25).** Copy the draft-3 `manifest-proposal.json`. After acquisition, write `eligibleFileCountAfterContentRules` in the walk facts of every repository that passed the path rules, and set `status: "acquired"` on the manifest and every entry; `verify_manifest.py` then accepts acquisition-time `too-few-eligible-files` rejections.
5. **Cases.** Go top-level boundaries require `(`-depth 0 (A10); no repeated unit within a cell (A27); add vectors for both and for a boundary inside a block comment (A12).
6. **Suppression (A26, S-c).** For a frequent hash whose snippet fails, add the whole fold-S file of its first occurrence (once per file). Record per catalogue: frequent hashes, kept snippets, fallback files, collateral hashes per channel. Refuse any non-fold-S source; record the fold-S and fold-E lists in `freeze.json` and check them in `tune`.
7. **Pilot and estimates (B5, B6).** Time batched comparisons (one `compare` per search over the sampled files); run the 1-in-50 direct checks on exactly the selected pairs (one `compare` per checked reference file and configuration; draft-8 replaces the per-search batch first ruled here); include both CLIs and the direct checks in every estimate.
8. **Memory (B4).** A watchdog sampling every child and the harness process at least once per second, killing at 75% of physical memory; optional batching of large searches by reference files.
9. **Checks (B8, S-b).** Record checked ids; `counts` recomputes the expected ids from the fixed moduli and exits 1 on any difference.
10. **Verdict (B7).** Write `eval/results/heldout/searches.jsonl`; `m36-verdict` reads it, `counts.json` and `eligibility.json` from the first held-out result commit with `git show`, recomputes A, N and the exclusion bound, cross-checks the summaries (difference: exit 2), refuses a dirty tree, and prints the suppression counts.
11. **Tests.** Add S-a (an abstaining search must alarm end to end), S-b and S-c; state the 6–8 GB scratch need in TESTING.md.

## Changes for draft-7

From the O1–O8 rows of [protocol §19](../evaluation-protocol.md#19-harness-rulings-m3-eval-draft-6). Most adopt what the harness already does at `d4502e0`. Remaining work:
- **O1:** once `main` has `traceweave-go --version` (owner: the implementation repository's Go lane), read both binaries' commits from `--version`; until then, report-document provenance as now.
- **O2:** confirm `path-case-collision` uses Unicode 17.0.0 full case folding and excludes every colliding path; keep `path-unsafe`.
- **O5:** implement reference-file batching of large searches before the held-out run if the pilot shows any search near the 75% memory line; otherwise such a search aborts the run.

## Changes for draft-8

- **Direct check:** exactly the selected pairs, one `compare` per checked reference file and configuration, as implemented at `75b84eb`; no change.
- **Caching check:** stays unbatched (whole reference against whole candidate catalogue); no change.
- **Disk:** refuse `TRACEWEAVE_EVAL_MIN_FREE_GB` below 10 (exit 2); record the margin used in `identity.json`; falling below it mid-run is an abort (exit 2).

## Changes for draft-9

- **Pair completeness (review N4):** for every batched or cache-assembled comparison (negative searches, positive cases, tuning, pilot, direct checks), compute the expected pair set from the two catalogues' artifact lists, require every expected pair id exactly once, and record expected and assembled counts plus a SHA-256 over the sorted pair ids; a difference is exit 2. `counts.json` carries these for held-out negatives and positives, and `m36-verdict` recomputes the expected sets from the committed eligible-file records (exit 2 on a mismatch).

## Changes for draft-10

- **Pair-id digest:** the protocol now fixes the form the harness already uses (`<reference id>` TAB `<candidate id>` LF per pair, UTF-8, sorted bytewise, lowercase hex SHA-256; empty set hashes the empty string); no change.
