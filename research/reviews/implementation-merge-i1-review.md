# Non-author review: traceweave `merge-i1` at ce97ed9

Reviewed 2026-11-22. This was a read-only review of `<implementation repo>` branch `merge-i1` (ce97ed9). It integrates the Rust lane `i0-i1-rust` (297687e), the Go lane `impl-go` (320e93d) and `xcheck/`. I wrote none of it.

All work ran in a scratch clone under `$TMPDIR`. Build outputs and the Go cache also went to `$TMPDIR`, and no worktree was touched. Toolchains: go1.27.3, rustc 1.97.1, Python 3.14.6. Offline throughout: `CARGO_NET_OFFLINE=true`, `GOPROXY=off`.

## 1. `scripts/check` and sabotage

**Clean export: exit 0, all stages pass.** The stages are fmt, clippy, tests, the spec pin, Rust conformance, gofmt, vet, `go test`, Go conformance and the differential smoke.

Each sabotage was applied alone and then restored with `git checkout`:

| Sabotage | Result | Caught by |
| --- | --- | --- |
| Rust lexer: identifier + `#` no longer `reserved-token` (`tw-lex-rust/src/lib.rs:259`) | exit 101 | `cargo test`, `tests::reserved_and_raw` |
| Go lexer: `]` removed from the semicolon-insertion set (`go/internal/lexgo/lexgo.go:107`) | exit 1 | `go test`, go/scanner cross-check seeds and fuzz |
| One hash byte flipped in vendored `go.json` | exit 1 | spec pin: `DRIFT … go.json` |
| The same flip with `spec.lock` re-digested to match | exit 1 | Rust conformance: `FAIL go.json:go-exact-k` |
| Go `lexrust` raw-hash limit 255→256 (meant for the smoke) | exit 1 | `go test`, vector `rust-err-raw-too-many-hashes` |
| **Go `lexrust`: U+2029 removed from Rust white space (`lexrust.go:89`)** | **exit 0: every stage passes, smoke included** | **Only the full differential**: 4 Unicode-sweep cases, class D1 |

For the last row, I confirmed that the sabotaged Go binary returns `illegal-character@5` on `let a<U+2029>= 1;` while Rust returns `ok`. The full `xcheck/run.sh` with the same sabotage fails (`XCHECK FAIL`, 1 divergence class). The smoke samples only every 23rd code point, and no vector or unit test puts U+2029 in white-space position. The repository's own sabotage probe (`xcheck/probes/check-scripts-sabotage.txt`) used U+2028, which `TestLexCases` happens to cover, so it overstates what the smoke catches. **Finding F1.**

## 2. Vendored files and spec.lock

**All 14 files under `third_party/traceweave-spec/` equal `git show 38e8b25:<path>`** in the spec repository (`cmp`); `scripts/check-spec-pin --strict --mirror` on the spec checkout agrees (14/14), then fails on the expected open gate. `spec.lock` records commit `38e8b2597b29…`, status `local spec commit, not pushed`, `repository: null`, with 14 matching digests. No remote-tracking branch in the spec repository contains 38e8b25 (local refs only), consistent with "not pushed".

## 3. Lane diffs

- **Both merge commits are pure.** `6c028c7` equals the Rust tip's tree exactly. `dabd2ac`'s tree (`def7667…`) is identical to `git merge-tree 6c028c7 320e93d`, so no hand edits were made during either merge.
- **Every Go code change is a path change.** All edits since 320e93d come in integration commit 18ed7f1 (ce97ed9 touches only `xcheck/` reports and probes): test, generator and `go:generate` paths moved from `testdata/spec` to `../third_party/...`, docs and README notes, and the removal of `TestSpecLock` and its unused imports. No change to lexing, extraction or output.
- **`TestSpecLock` is covered by `scripts/check-spec-pin`** (`tw-conformance check-spec-pin`). It checks each file's SHA-256 (`DRIFT`) and flags any file not listed in the lock (`UNLISTED`). It prints the provisional status, and `--strict` fails while the pin is provisional. The only behaviour lost is the old test's assertion that the status note is present, which is a trivial difference.
- **Nothing was dropped.** No file of either lane is deleted except Go's private `go/testdata/spec/` copy. The 13 files that copy shares with `third_party` are byte-identical to it. Its `records.json` differs only by the `configFile`/`configSha256` fields added at 38e8b25; the 16 record texts, digests and inputs are identical. Outside `go/`, the Rust lane's files gained `extraction-rust.json`, records, the lock, README and `scripts/check`, and lost nothing.

## 4. Full differential, my seed 31415926

`xcheck/run.sh --seed 31415926` ran in 232 s: **9,887,008 cases, all agree, 0 divergence classes.** `vectors_vs_spec` is 163/163 for both, all 869 CLI-equivalence cases are equal, and 60,000 determinism cases are identical across reruns for both implementations.

The per-generator breakdown is: Unicode sweep 7,784,448; random 1,000,000; valid streams 500,000; NFC 300,000; mutations 199,985; shebang 50,000; go-stdlib 41,610; configs 5,114; rust-std 4,220; contract questions 1,104; vectors 317; repository 210. A clean run left the clone unmodified.

## 5. Vector and record reproduction (counts per file)

| File | Rust | Go |
| --- | --- | --- |
| go.json | 34/34 | 34/34 |
| rust.json | 78/78 | 78/78 |
| limits-go.json / limits-rust.json | 3/3, 3/3 | 3/3, 3/3 |
| matching-vectors/extraction-go.json | 15/15* | 15/15 |
| matching-vectors/extraction-rust.json | 2/2* | 2/2 |
| records.json | 16/16 (bytes and SHA-256) | 16/16 |
| config-negative.json | 28/28 negatives, 3/3 boundary positives, 4/4 shipped configs | covered by `go test` and the 163-case xcheck |

\* Rust's `scripts/conformance` does not run these two files. I reproduced them with `traceweave extract --result-only`, and `xcheck` covers them inside its 163 cases. **Finding F2.**

## 6. README, licence, hygiene

- **README is accurate.** It states experimental, local-only status, not a detector or registered algorithm. It lists what is not claimed (no detection, ownership, authorship, copying-direction or infringement claim; no calibrated rate; no privacy; no scope awareness; no stable pin) and marks the pin provisional with the strict gate open. Its counts match mine, including about 9.9 M cases per seed.
- **Licence is consistent.** `LICENSE` is byte-identical to `LICENSES/Apache-2.0.txt`, every Rust crate inherits `Apache-2.0`, and both READMEs say Apache-2.0. The prose split and the Go module path are open owner decisions.
- **Hygiene.** No secrets (grepped for private keys, tokens, `sk-`, `AKIA`, `password=`, `api_key`) and no terms specific to the private pilot applications. **No AI attribution in any of the 22 commit messages on `merge-i1`** (full bodies grepped for Claude, Anthropic, Co-Authored-By, "generated with", Codex, Cursor, OpenAI, GPT, Copilot); one author identity.
- **Absolute local paths, including the home directory, are committed** in `xcheck/results/summary.json:11,23` and `seed-20261123/summary.json:23`. **Finding F4.**

## 7. M1.4 precedence (ROADMAP line 70)

The commits that first add each extractor are Rust `9dd4368` (lock at the root `spec.lock`, status "provisional: spec working tree, uncommitted") and Go `633beaa` (`go/testdata/spec/spec.lock`, same status). Both locks hold the same 10 digests. Each was compared with the same file at spec 38e8b25:

| File | Digest in both first-extractor locks | At 38e8b25 | Verdict |
| --- | --- | --- | --- |
| config-go.json, config-rust.json, both limit16 configs, limits-go.json, limits-rust.json, unicode-17.0.0-tables.json | aa867222…, 64b34335…, dfbc5fe3…, 71d5ed27…, 0d5d243e…, 61ad316e…, 9363b97e… | identical | **equal** |
| go.json | 061d9c29… | f81fede1… | **later change** |
| rust.json | d5c8ae16… | 21f3360c… | **later change** |
| config-negative.json | 17e6a28f… | 413661ca… | **later change** |

All three first-extractor digests equal spec commit **6f75d55**. The changes came in spec **2fa2b58**, the contract-question rulings. I checked them vector by vector. go.json went from 29 to 34 vectors and rust.json from 43 to 78; no existing vector changed or was removed, and the headers are identical. config-negative.json kept all 25 old configurations, gained 3 more, added `expectedResult` to each, and added 3 `boundaryPositives`. So the file-level digest rule is **not met for these 3 files**, and the recorded-decision rule applies. The decision record exists: the 2fa2b58 rulings, lane commits 944a1b7 ("40 added, none changed") and b58e088, the `go/docs/verification.md` addendum, and the "Ruled (2fa2b58)" rows in `docs/contract-questions.md`.

The `check-vector-precedence` script that ROADMAP M1.4 names does not exist in the repository; I did this check by hand. **Finding F3.** The 4 matching-vector files first appear after both extractor commits, so they are later additions and are pinned only at 38e8b25.

## Findings

- **F1 (medium, check coverage):** `scripts/check` passes a real Go-side regression, U+2029 dropped from Rust white space; only the full differential catches it. Fix: add a vector or unit case for each of the 11 Rust Pattern_White_Space characters in white-space position, in both lexers; make the smoke include white-space positions deterministically; correct the sabotage probe's implied coverage.
- **F2 (low):** Rust's `scripts/conformance` does not gate `matching-vectors/extraction-{go,rust}.json`. Add them to `VECTOR_FILES`.
- **F3 (low, governance):** `check-vector-precedence` is missing. Either add it or record this manual check, including the 6f75d55 → 2fa2b58 additions-only finding.
- **F4 (low):** committed absolute home-directory paths in `xcheck/results/*summary.json`. Write paths relative to the repository instead.
- **F5 (low):** `scripts/check` says "Offline: nothing is downloaded", but its cargo calls use `--locked` without `--offline`. Add `--offline` or `CARGO_NET_OFFLINE=true`, as `xcheck/run.sh` already does.

## Verdict

**main may fast-forward to ce97ed9.** The integration is faithful: the merges are pure, the Go changes are path-only, nothing is lost, and the vendored copy is byte-identical to 38e8b25. Both implementations reproduce every vendored vector and all 16 records. The full differential agrees on 9.89 M cases with a fresh seed. None of the findings is a defect in the code at ce97ed9. F1 should be fixed before the smoke is cited as a regression gate. F2–F5 are follow-ups. M1.4 stays open as the roadmap says: it needs a pushed spec commit and the recorded decision for the three files changed at 2fa2b58.
