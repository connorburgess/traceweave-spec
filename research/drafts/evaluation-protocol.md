# M3 evaluation protocol: token-fingerprint baseline on Go and Rust

Protocol version: `m3-eval-draft-1`. Status: **draft for review, 2026-11-22. Not frozen, not run. No corpus has been acquired.** Roadmap gates M3.0–M3.6 and backlog item TW-05 ([roadmap](../../ROADMAP.md#m3--measure-usefulness)). Corpus proposal: [evaluation-corpus/](evaluation-corpus/README.md).

This is a research protocol. It changes nothing in `spec/`, `schemas/`, `profiles/` or `test-vectors/`, and it decides nothing the roadmap reserves for the owner. Every owner decision it needs is listed in [§14](#14-decisions-that-need-the-owner) with options; none is assumed.

It fixes, before any result exists, what is measured and how each pass/fail becomes an exit code or a count. Where this draft leaves a number open, the number is chosen by a stated mechanical rule on the tuning split, never by looking at held-out data.

## 0. What is measured

The system under test is the token-fingerprint baseline:
- extraction per the [extraction contract](extraction-contract.md) (profiles `go-tokens` and `rust2024-tokens`, `draft-1`; channels `exact` and `normalized`);
- catalogues and comparison per the [catalogue and report contract](catalogue-report-contract.md) (`traceweave-catalogue-draft-2`, `traceweave-seed-merge-draft-2`, `traceweave-report-draft-2`): seeds, regions, minimum evidence counted in distinct non-common hashes (§5.6), the suppression catalogue bound by digest (§5.2), the closed outcome codes (§6.4), and the caps `maxSeedsPerMode` and `maxRegionsPerMode` (§5.4, §5.7).

The question is the one M3 states: which transformations does this baseline detect, at what fragment sizes, and at what cost in false alarms, abstentions, candidate volume, runtime and memory. Embedded marks are out of scope here; M2E.7 later reuses the same held-out cases and the same budget.

The baseline is not a calibrated detector ([extraction §12](extraction-contract.md#12-what-the-baseline-does-not-claim), [report §8](catalogue-report-contract.md#8-what-the-report-must-not-claim)). This protocol measures it; it does not turn a measured rate into a probability for a single result.

## 1. Units

**Artifact.** One eligible source file (§3.4) of one corpus repository at its pinned revision. Its catalogue id is opaque (`f` followed by a decimal index, contract §3.2); the id-to-path map stays local.

**Repository catalogue.** One catalogue per (repository, language, configuration) holding every eligible artifact of the repository. Duplicate file contents inside one repository keep the bytewise-first path only, because a catalogue forbids repeated `sha256` (OD-C9); the dropped paths are counted.

**Repository search.** One comparison body produced from:
- the reference catalogue of one repository *R* (the "protected" code, UC-1's authorized reference snapshot);
- the candidate catalogue of one repository *C* (the "larger project" being checked);
- the frozen comparison configuration and suppression catalogue of that language.

A search compares every reference artifact with every candidate artifact in both modes (contract §5.3). It is the unit of the false-alarm budget (M3.0). *R* and *C* are always in the same language and the same split, and never in the same split group.

**Alarm.** A search raises an alarm when at least one pair has mode outcome `match` in **either** mode (`exact` or `normalized`). The union is the primary rule because an operator reads both modes of one report. Per-mode alarm counts are reported beside it.

**False alarm.** An alarm in a **negative search** (§7). Every such alarm counts, whatever caused it. A post-hoc audit may label it (boilerplate, real shared provenance, unexplained), but labels never remove it from the M3.6 count.

**Positive case.** One mechanically generated insertion of transformed held-out source into a different-group host repository (§6). Each case is evaluated by exactly one search: reference = the source repository, candidate = the host repository with the case applied.

**Hit.** For a case and a mode, a hit requires all of:
1. the ground-truth pair (reference artifact = the source file, candidate artifact = the modified host file) has mode outcome `match`;
2. at least one listed region of that pair and mode has status `reportable`, `ambiguous: false`, a `candidateSpan` overlapping a ground-truth candidate segment by at least one byte, and a `referenceSpan` overlapping the corresponding source segment by at least one byte.

A case is **detected** when it is a hit in either mode. Misses are classified by the first matching rule: `extraction-error`, `insufficient-tokens`, `seed-limit-exceeded`, `ambiguous`, `below-minimum-evidence`, `common-only`, `no-shared-fingerprints`, `truncated` (outcome `match` but the overlapping region is not listed because of `maxRegionsPerMode`), `mislocalized` (outcome `match` with no overlapping listed region).

**Abstention.** A pair outcome `insufficient-tokens`, or a mode outcome `ambiguous` or `seed-limit-exceeded` (contract §6.4). Abstentions are counted, never folded into hits or misses silently.

## 2. Order of work

Each step is a commit. Gate IDs in brackets.

| Step | Content | Needs |
| --- | --- | --- |
| 1 | M3.0 budget recorded in the spec repository | owner [M3.0] |
| 2 | Manifest frozen; acquisition approved | owner [M3.1] |
| 3 | Acquisition: shallow fetch of each pinned revision; file inventory; acquisition-time checks (§3.6) | step 2 |
| 4 | Groups merged by the acquisition-time rules; split file and its digest committed | step 3 [M3.2] |
| 5 | Tuning: suppression catalogues, grid, selection rule (§5), on tuning data only | steps 1, 4 |
| 6 | Freeze file committed (§8) | step 5 [M3.3] |
| 7 | Held-out positives generated; held-out extraction, comparison and metrics | step 6 |
| 8 | Held-out report and counts committed (the "first held-out result commit") | step 7 [M3.4] |
| 9 | Independent rerun | step 8 [M3.5] |
| 10 | Verdict computed | steps 1, 8 [M3.6] |

Before step 6, **no held-out file is extracted, catalogued or compared**, and no held-out positive case is generated. Steps 3 and 4 read held-out files only to compute byte lengths, SHA-256 digests, the generated-file test (§3.4) and dependency declarations (§4.2).

## 3. Corpus

### 3.1 Selection rule

The rule is mechanical. Its inputs are a committed **pool snapshot** and a committed **walk record**; rerunning the GitHub query later returns a different pool (stars and pushes change), so the snapshot, not the query, is what a reviewer reproduces.

1. **Pool query** (GitHub repository search, sorted by stars, descending, first 100 results, retrieved once per language and committed verbatim in the manifest):
   `language:<Go|Rust> stars:>=2000 fork:false archived:false size:<=50000 created:<2023-11-22 pushed:>=2025-11-22`
   This asks for maintained, non-fork, non-archived repositories whose primary language is the target, at most 50,000 KiB including history, created at least three years before the snapshot.
2. **Order.** Sort the pool by `SHA-256("traceweave-m3-select-v1\n" || lowercase(full_name))` as lowercase hex, ascending. Popularity therefore admits a repository to the pool but does not order the sample.
3. **Walk.** Visit repositories in that order and give each exactly one verdict, applying the first rule that fires:
   1. owner in the exclusion list (§3.5) → `excluded-owner-census` or `excluded-owner-development-exposed`;
   2. repository name or a topic contains `awesome` → `list-repository`;
   3. owner already accepted → `owner-already-selected` (one repository per owner);
   4. default-branch head not resolvable → `revision-unresolved`;
   5. pinned tree listing truncated by the API → `tree-truncated`;
   6. licence check (§3.2) fails → `licence-file-missing`, `licence-unclassified` or `licence-not-allowed`;
   7. fewer than 10 eligible paths → `too-few-eligible-files`; eligible bytes above 20 MiB → `eligible-bytes-over-limit` (§3.3);
   8. otherwise `accepted`.
4. **Stop** when 24 repositories per language are accepted (the proposed size; scale is an owner choice, §14.4).

The walk record lists every visited repository with its verdict and the facts the verdict rests on. [`verify_manifest.py`](evaluation-corpus/verify_manifest.py) recomputes the order, the rule-1–3 verdicts and the stopping point from the snapshot, and checks that the accepted set equals the manifest entries.

**Pinned revision.** The 40-hex commit of the default-branch head, resolved with `git ls-remote https://github.com/<owner>/<repo> refs/heads/<branch>` on the snapshot date and recorded with its resolution time. No floating reference is ever used again.

### 3.2 Licence and redistribution, from the licence file

**Licence files** are the root entries of the pinned tree whose names match `^(licen[cs]e|copying|unlicense)([-._][a-z0-9.-]+)?$`, case-insensitively. Each is fetched at the pinned revision and recorded with its path, git blob SHA-1, SHA-256 and byte length.

**Classification** (classifier `m3-licence-classifier-v1`): whitespace is collapsed, text lowercased and `*` and `#` removed. A file is classified as an identifier when it contains every required phrase of that identifier and of no other. More than one identifier, or none, is `licence-unclassified`; the classifier never guesses.

| Identifier | Required phrases (after normalization) | Allowed |
| --- | --- | --- |
| MIT | "permission is hereby granted, free of charge, to any person obtaining a copy"; "the above copyright notice and this permission notice shall be included" | yes |
| Apache-2.0 | "apache license"; "version 2.0, january 2004" | yes |
| BSD-3-Clause | "redistribution and use in source and binary forms, with or without modification, are permitted"; "endorse or promote products derived from this software" | yes |
| BSD-2-Clause | the first BSD phrase, without the endorsement phrase | yes |
| ISC | "permission to use, copy, modify, and"; "distribute this software for any purpose with or without fee is hereby granted"; "provided that the above copyright notice and this permission notice appear in all copies" | yes |
| 0BSD | the first two ISC phrases, without the third | yes |
| Unlicense | "this is free and unencumbered software released into the public domain" | yes |
| Zlib | "altered source versions must be plainly marked as such" | yes |
| GPL-2.0, GPL-3.0, AGPL-3.0, LGPL-3.0, MPL-2.0, EUPL, CC | version header phrases | no |

**Licence expression.** The identifiers of all licence files joined with ` AND `, sorted. Where upstream offers a choice (for example `MIT OR Apache-2.0`), recording `AND` is the conservative reading: the project complies with every file. A choice could only be recorded from evidence outside the licence files, which this rule does not read.

**Redistribution.** Every allowed licence permits redistribution: with notice retention (`permitted-with-notice`: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Zlib) or without conditions (`permitted`: 0BSD, Unlicense). The project nonetheless **redistributes no corpus source**: only the manifest, digests, byte offsets, counts and reports are committed. Catalogues and report bodies of corpus code stay private by default (contract OD-C14).

The classifier is a screening rule, not a legal opinion. It checks the root licence files only; files under other licences inside a repository (vendored code, nested `LICENSE` files) are excluded from evaluation by the eligible-file rule, not cleared by it.

### 3.3 Size limits

- GitHub `size` at most 50,000 KiB (pool query).
- At least 10 and at most 20 MiB of eligible paths (§3.4), counted from the pinned tree listing.
- Per file: larger than 1,048,576 bytes is `oversize`, excluded and counted. This equals the shipped `maxInputBytes`, so no evaluated file can produce `input-too-large`.

### 3.4 Eligible files (generated and vendored code excluded by rule)

**Go.** A path is eligible when it ends in `.go`, does not end in `_test.go` or `.pb.go`, its file name does not start with `.` or `_`, and no directory component is `vendor`, `testdata`, `third_party`, `third-party`, `examples`, `example`, `test`, `tests` or `node_modules`, or starts with `.` or `_`. At acquisition, a file is also excluded as **generated** if any line before the first line that is neither blank nor a comment matches `^// Code generated .* DO NOT EDIT\.$` (the Go convention).

**Rust.** A path is eligible when it ends in `.rs`, is not named `build.rs`, and no directory component is `target`, `vendor`, `testdata`, `third_party`, `third-party`, `examples`, `example`, `test`, `tests`, `benches`, `fuzz` or `node_modules`, or starts with `.`. At acquisition, a file is also excluded as **generated** if its first 1,024 bytes contain `@generated`, or a line there matches `(?i)^\s*//.*\b(auto-?generated|generated by|do not edit)\b`.

**Both.** Symbolic links, submodules and non-UTF-8 paths are excluded. Every exclusion is counted by reason per repository. Inline Rust `#[cfg(test)]` modules stay in, because removing them needs a parser; this is stated in every Rust result.

### 3.5 Exclusions

- **Census repositories** ([census checkpoint](../public-census-checkpoint.md)): `davecgh/go-spew`, `rakyll/hey`, `dtolnay/itoa`, `sharkdp/hexyl`. Because split groups follow owners (§4), the whole owner is excluded: `davecgh`, `rakyll`, `dtolnay`, `sharkdp`. This also keeps out, for example, `sharkdp/fd`, which is in the Rust pool.
- **Development-exposed code:** owners `golang` and `rust-lang`. The I2 cross-check built catalogues from the Go and Rust standard libraries, including identical, partial, renamed and reformatted copies (`xcheck/HISTORY-I2.md` on `merge-i2`), so that code has been seen by the project.
- **Private applications** and the project's own repositories are never in the pool.
- **Forks.** Excluded by the query (`fork:false`) and rechecked in the snapshot.

### 3.6 Acquisition (after owner approval only)

For each entry: `git init`, `git fetch --depth 1 https://github.com/<owner>/<repo> <revision>`, `git checkout --detach FETCH_HEAD`, inside the corpus root (§14.3). Git verifies every object's SHA-1 against the pinned commit. No build, test, build script, macro, package manager or acquired program is run; formatters run only on generated positive cases (§6.3). Then, per repository, before any split is computed:

1. record the root licence files again and require identical blob SHA-1s to the manifest;
2. record every path's SHA-256, byte length and eligibility reason;
3. compute dependency declarations (§4.2) from every `go.mod` and `Cargo.toml` outside excluded directories;
4. compute the cross-repository duplicate test (§4.2) from eligible-file digests;
5. rerun the walk with the acquisition-time rules added; replacements, if any, are taken from the continuing walk order and recorded.

## 4. Groups and splits

### 4.1 Group

A split group starts as the lowercase owner login. Groups are merged (union of the two) when, at the pinned revisions:
1. **dependency ancestry:** a `go.mod` `require` path or a `Cargo.toml` dependency (any table, including `[dev-dependencies]`, `[build-dependencies]`, `[workspace.dependencies]` and target tables, matched by `git`/`repository` URL, or by crate name equal to a crate defined in the other repository's `Cargo.toml` files) points at another corpus repository;
2. **duplicate content:** the two repositories share at least one eligible file of at least 1,024 bytes with equal SHA-256;
3. **fork network:** either is recorded as a fork of the other or of a common source.

A merged group's id is the bytewise-smallest member owner. Instead of merging, acquisition step 5 **rejects** a repository that would merge into another owner's group (`dependency-linked`, `duplicate-content`), and the walk continues. This keeps groups one-owner and keeps "unrelated" negatives unrelated by construction. Pairs that share a third-party dependency outside the corpus are kept; they are the same-stack negatives (§7).

### 4.2 Split assignment

Per language, sort groups by `SHA-256("traceweave-m3-split-v1\n" || language || "\n" || group)` ascending. The first ⌊G/2⌋ groups are `held-out`, the rest `tuning`. A group therefore lies in exactly one split, and near-duplicates (same owner, dependency edge, shared files, fork network) never straddle splits.

### 4.3 Split file and digest (M3.2)

The split file is UTF-8, one line per repository, sorted bytewise, each line `language TAB split TAB group TAB owner/repo TAB revision LF`. Its SHA-256 is the **split digest**. The manifest proposal carries the digest of its provisional split; the M3.2 digest is the one computed after acquisition step 5 and committed with the split file. `verify_manifest.py` recomputes it and checks group disjointness.

## 5. Tuning (tuning split only)

### 5.1 Folds

Per language, sort tuning groups by `SHA-256("traceweave-m3-fold-v1\n" || language || "\n" || group)`. The first half is fold **S** (suppression source), the rest fold **E** (tuning evaluation). Fold S is never compared; fold E never contributes to a suppression catalogue.

### 5.2 Suppression catalogue construction

For a threshold *T*, a hash of channel *c* is **frequent** when it appears among the fingerprints of eligible files from at least *T* distinct fold-S groups. For each frequent hash, take its first occurrence in (group, path, position) order and cut the k-gram's span from that file into a **snippet artifact**: exactly the bytes of the k-gram span. Extract the snippet; keep it only if its fingerprints in channel *c* include the hash (Go semicolon insertion at a cut can change the last token), otherwise count it as `snippet-dropped`. The suppression catalogue is the catalogue of kept snippets, built by the ordinary builder (§3.8 of the contract), so its digest binds into the comparison configuration as `suppressionCatalogueSha256`. Snippet bytes stay local; the catalogue is private.

Suppression stays advisory (contract §5.2): it removes only hashes winnowing selected in fold S.

### 5.3 Grid

Fixed in advance; 144 configurations per language:

| Parameter | Values |
| --- | --- |
| `k` | 5, 8, 12 |
| `window` | 4, 8, 16 |
| `minRegionDistinctHashes` | 2, 3, 4, 6 |
| suppression threshold *T* | none, 2, 3, 5 |
| `mergeGap` | equal to `window` |
| `maxSeedsPerMode`, `maxRegionsPerMode` | 1,000,000 and 1,000, fixed |
| `maxInputBytes` | 1,048,576, fixed |

All values are inside the extraction and comparison bounds (extraction §10, OD-21; contract §4, OD-C33).

### 5.4 Selection rule

On fold E, generate positive cases with the §6 generator (salt namespace `tuning`) and run all ordered fold-E negative searches. For each configuration compute: *a* = false alarms per negative search (union rule), and *r* = the unweighted mean, over transformation × bucket cells with at least 10 cases, of detected/cases.

1. Eligible configurations: *a* ≤ budget / 2 (the M3.0 budget, halved as a margin for tuning-to-held-out drift).
2. Choose the eligible configuration with the largest *r*. Ties, in order: smaller *a*; smaller `k`; larger `minRegionDistinctHashes`; smaller `window`; *T* in the order none, 5, 3, 2.
3. If none is eligible, choose by smallest *a*, then the same ties.

The selection runs as a script whose exit status is 0 when it selected by rule 2, 3 when by rule 3. Either way the selected configuration is frozen; rule 3 is reported.

## 6. Positive set (held-out sources, generated after the freeze)

### 6.1 Units and size buckets

Units are taken from held-out source repositories:
- **file:** a whole eligible file;
- **function:** a whole top-level function, from the first byte of `func`/`fn` (after any attributes, visibility or qualifiers that belong to the item: Rust `pub`, `async`, `const`, `unsafe`, `extern "…"`; doc comments excluded) to the end of its closing `}`. Go uses `go/parser`; Rust uses `syn` with span locations; both pinned in the freeze;
- **partial:** a maximal run of consecutive statements inside one block of a function body whose exact-channel token count falls in the bucket being filled.

The **size bucket** is the unit's exact-channel token count on the source side (extraction §2, `tokenCount`):

| Bucket | B0 | B1 | B2 | B3 | B4 | B5 | B6 | B7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tokens | 4–7 | 8–15 | 16–31 | 32–63 | 64–127 | 128–255 | 256–1,023 | ≥ 1,024 |

Buckets are fixed independently of `k` and `window`, so B0 shows the floor below the shipped locality threshold `k + w − 1 = 8`.

**Targets per language:** file units 30 (bucketed after selection); function units 30 per bucket B2–B6; partial units 30 per bucket B0–B5. At most 3 units per source repository per (unit kind, bucket). A cell that cannot be filled is reported with its actual count; nothing is relaxed to fill it.

### 6.2 Deterministic choice

Every choice uses `u(id, j) = uint64be(SHA-256("tw-m3-gen-v1|" || namespace || "|" || id || "|" || decimal j)[0:8])` and picks item `u mod n` from a list sorted bytewise. The namespace is `tuning` or `held-out`. Source repositories are visited round-robin in split-hash order. The host is a repository of the same split and language in a **different group**, and the host file and insertion boundary are chosen by `u`. Each unit is sampled once and **every applicable transformation is applied to the same unit** (a paired design, §11).

### 6.3 Transformations

Each is a function of the unit bytes and the case seed. Every one of them is defined lexically or by a pinned formatter; none is checked for compilation.

| ID | Applies to | Definition |
| --- | --- | --- |
| `verbatim` | file, function, partial | Unit bytes unchanged. Placement as in §6.4 |
| `ws` | all | In every gap between two tokens that holds only whitespace: a gap containing a line break gets one extra `\n` after its last line break; any other gap is doubled. Never adds a line break to a gap without one, so Go semicolon insertion is unchanged; the token stream is identical |
| `comments-strip` | all | Every comment is replaced by `""` (line comments) or by `" "`, or by `"\n"` when a Go general comment contains a line break. Token stream identical |
| `comments-add` | all | After every 10th token (positions 9, 19, …) insert ` /* tw */ ` into the following gap. Token stream identical |
| `fmt` | all | After placement, run the pinned formatter on the whole host file: Go `gofmt -s`; Rust `rustfmt --edition 2021 --config max_width=50,tab_spaces=2`. These can change tokens (Go `-s` simplifications; rustfmt trailing commas and reflow). The unit is wrapped in the marker comments `/*tw-begin*/` and `/*tw-end*/` before formatting; the ground truth is the byte range between them after formatting, then both markers are deleted and spans adjusted. A non-zero formatter exit, a lost or reordered marker, or an unchanged file is `generation-failed` |
| `rename` | all | Identifiers *declared inside the unit* are renamed consistently to `twv1`, `twv2`, … in order of first occurrence. Go: `go/ast` objects whose declaration lies in the unit. Rust: `syn` bindings in `let`, function and closure parameters, `for`, `match` and `if let` patterns, and the function name itself. All other identifiers are unchanged. Zero renamable identifiers is `generation-failed` (not applicable) |
| `reorder` | file | Top-level declarations (Go: all after the import block; Rust: all items) in reverse order, each declaration's bytes (with its leading comments) unchanged. Ground truth is one segment per declaration. Files with fewer than 2 declarations are not applicable |
| `split-mix` | function, partial | The unit is cut at the statement boundary nearest its middle token; the two halves are inserted, in order, at two different boundaries of the host file chosen by `u`. Two ground-truth segments |
| `compound` | function, partial | `comments-strip`, then `rename`, then `fmt` |

### 6.4 Placement

- **file units** under `verbatim`, `ws`, `comments-*`, `rename`, `fmt`, `reorder`: written as a **new file** in the host repository at `tw_eval/<case id>.go` or `.rs`.
- **function units:** inserted into an existing host file at a top-level declaration boundary.
- **partial units:** inserted into an existing host function body at a statement boundary.

Insertion adds exactly one `\n` before and after the inserted bytes. Every host-side byte outside the insertion is unchanged, except under `fmt` and `compound`, where the formatter rewrites the whole host file.

### 6.5 Ground truth record

One JSON line per case in `cases-<language>-<namespace>.jsonl`, committed (offsets and digests only, no source bytes):

`caseId`, `language`, `namespace`, `unitKind`, `bucket`, `tokenCount`, `transformation`, `sourceRepo`, `sourceRevision`, `sourcePath`, `sourceSha256`, `hostRepo`, `hostRevision`, `hostPath` (or `tw_eval/…`), `hostSha256Before`, `candidateSha256`, `segments` (list of `{source: [start, end), candidate: [start, end)}` in UTF-8 bytes, half-open), `seedId`, `generator` (commit), `status` (`generated` or `generation-failed` with reason).

Failed generations stay in the file, so the per-cell denominators "attempted" and "generated" are both reported.

## 7. Negative set

Every ordered pair (*R*, *C*) of held-out repositories of the same language from different groups is one negative search, with no planted content. With 12 held-out repositories per language that is 12 × 11 = 132 searches per language, 264 in all. Searches carry labels that are reported separately but all count toward M3.6:

| Label | Definition (mechanical) |
| --- | --- |
| `unrelated` | Every negative search |
| `same-domain` | *R* and *C* share at least one GitHub topic in the snapshot, other than the language name (`go`, `golang`, `rust`, `rustlang`) and `hacktoberfest` |
| `same-stack` | *R* and *C* declare at least one common direct dependency at their pinned revisions (§3.6 step 3) |

Common boilerplate enters in two ways: naturally, inside every negative search (licence headers, `if err != nil { return err }`, CLI scaffolds), and as the `same-stack` label, where shared frameworks produce shared idioms. The only boilerplate *catalogue* is the §5.2 suppression catalogue, built from tuning fold S only. Positive-case host repositories are also searched unmodified as negatives; a positive search's matches outside the ground truth are reported as `spurious` and do not enter M3.6.

## 8. Freeze and git ancestry (M3.3)

The **freeze commit** in the implementation repository adds `eval/freeze.json` containing:
- the manifest digest and the M3.2 split digest;
- per language: the extraction configuration bytes (Base64) and SHA-256; the comparison configuration bytes and SHA-256, including `minRegionDistinctHashes`, `mergeGap`, both caps and `suppressionCatalogueSha256`; the suppression catalogue SHA-256 and *T*;
- the alarm rule (§1, union) and hit rule (§1), by protocol version and digest;
- the M3.0 budget as a rational `numerator/denominator`, and the spec-repository commit that recorded it;
- the implementation commit used for extraction and comparison; the generator commit; `gofmt` and `rustfmt` version strings; the `go/parser` and `syn` versions;
- this protocol's SHA-256;
- the M3.5 tolerance (§13).

**When.** After the §5.4 selection, before step 7. Nothing in `freeze.json` changes afterwards; a change is a new protocol version and voids held-out results produced under the old one.

**Ancestry check** (from a clean clone of the implementation repository):

```
FIRST=$(git log --reverse --format=%H -- eval/results/heldout | head -n 1)
FREEZE=$(git log --reverse --format=%H -- eval/freeze.json | head -n 1)
SPLIT=$(git log --reverse --format=%H -- eval/splits.tsv | head -n 1)
git merge-base --is-ancestor "$FREEZE" "$FIRST" && git merge-base --is-ancestor "$SPLIT" "$FIRST"
git diff --quiet "$FREEZE" "$FIRST" -- eval/freeze.json eval/splits.tsv eval/manifest.json
```

M3.3 is met when every command exits 0. Timestamps are never consulted. The held-out runner also refuses to start unless HEAD descends from `FREEZE` and the work tree is clean, and the generator refuses the `held-out` namespace on the same condition.

## 9. Running the held-out evaluation

Pair outcomes depend only on the two artifacts, the configuration and the suppression catalogue (contract §5.2, invariance). A runner may therefore compute each (reference file, candidate file) pair once and assemble searches from cached pairs, provided the assembled body is byte-identical to a direct comparison; a 1-in-50 sample of searches, chosen by `u(search id, 0) mod 50 = 0`, is recomputed directly and must match byte for byte (exit status 0).

Resource measurement: every extraction batch and every search runs under `/usr/bin/time` (`-l` on macOS, `-v` on Linux), recording wall time and maximum resident set size, with operating system, architecture, CPU model, core count and memory recorded once per run.

## 10. Metrics (M3.4): every figure with its denominator

| Figure | Numerator | Denominator | Breakdown |
| --- | --- | --- | --- |
| Recall | detected cases | generated cases | language × transformation × bucket; per mode and union; plus attempted, generated and distinct source repositories per cell |
| Miss reasons | cases per miss class (§1) | generated cases | as recall |
| False alarms per repository search | negative searches with an alarm | negative searches | language; label; per mode and union |
| Pair-level false matches | negative pairs with a `match` mode | compared negative pairs | language; mode |
| Abstentions | pairs or pair-modes per abstention code | pairs or compared pair-modes | language; negative versus positive searches |
| Extraction outcomes | files per status/error code | eligible files | language; repository |
| Candidate volume | `match` pairs and reportable regions | searches (negative; positive) | mean, median, 95th percentile, maximum |
| Spurious matches in positive searches | positive searches with a `match` outside ground truth | positive searches | language |
| Runtime | wall seconds | extraction batches; searches | median, 95th percentile, maximum, total |
| Peak memory | maximum RSS | as runtime | median, maximum |

Counts are written to `eval/results/heldout/counts.json` (canonical JSON: sorted keys, no insignificant whitespace, integers only). Runtime and memory go to a separate `resources.json`, because they are not expected to reproduce exactly.

## 11. Intervals, dependence and what the sample can bound

**Dependence between cases.**
- Negative searches share repositories: each held-out repository appears in 22 of the 264 negative searches (11 as reference, 11 as candidate), and *R*→*C* and *C*→*R* compare the same file pairs in swapped roles.
- Positive cases share source repositories (up to 3 units per repository per cell), host repositories, and, by design, units: all transformations of one unit are paired. Overlapping k-grams and windows are correlated observations ([lane 07](../lanes/07-evidence-review.md); [evaluation](../../docs/evaluation.md)).

**Reported intervals.**
- *Recall per cell:* Wilson 95% interval on detected/generated, plus the number of distinct source repositories, plus the **leave-one-repository-out range** (minimum and maximum recall after dropping each source repository's cases in turn). Cells under 10 cases are reported and marked "fewer than 10 cases".
- *False alarms per search:* (a) the point estimate *a* = alarms / searches; (b) the Clopper–Pearson 95% interval treating searches as independent, labelled **"assumes independence, which does not hold"**; (c) the **disjoint-search bound**: per language, pair held-out repositories in split-hash order (1st→2nd, 3rd→4th, …), so that each repository is used once, and give the one-sided Clopper–Pearson 95% upper bound on those searches only. That subset is independent if repositories are independent draws from the pool. With 12 per language it has 12 searches in all.
- Transformation comparisons use the paired design: discordant-pair counts (detected under A and not B, and the reverse) on shared units, not differences of independent proportions.

**What the proposed sample can and cannot bound** (one-sided 95% upper bound with zero alarms, 1 − 0.05^(1/N)):

| Independent searches N | 12 | 24 | 50 | 100 | 300 | 1,000 | 3,000 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Upper bound | 0.221 | 0.117 | 0.058 | 0.030 | 0.0099 | 0.0030 | 0.0010 |

So the proposed 48-repository corpus can **measure** a false-alarm count over 264 searches and compare it with the budget, which is what M3.6 asks. It **cannot demonstrate** a rate below about 0.2 with independent-search confidence, nor below 0.011 even if all 264 searches were independent (0 alarms in 264 gives 0.0113). Demonstrating 0.01 at 95% needs about 300 independent searches, roughly 600 repositories under the disjoint design. Recall cells of 30 cases have Wilson half-widths up to about ±0.17. These limits are stated in the report and in every rendering of M3.6.

## 12. What M3.6 computes

Inputs: `counts.json` (held-out), the budget `p/q` from the M3.0 record named in `freeze.json`.

- `A` = negative searches with an alarm under the union rule; `N` = negative searches.
- **met** when `A × q ≤ p × N` (exact integer arithmetic); **negative-result** otherwise.
- `N = 0`, a missing or mismatched freeze, or a failed M3.3 check is an error, not a verdict.

The script exits 0 for met, 3 for negative-result, 2 for an error. No recall floor is applied; recall is reported without a pass line. The verdict uses the point estimate, as M3.6 states; the intervals of §11 are printed beside it and do not change it.

## 13. Reproduction (M3.5)

A second person, on a machine of their choice:

1. Clone the implementation repository at the first held-out result commit; run the §8 ancestry commands (exit 0).
2. Acquire the corpus from `eval/manifest.json` into their own corpus root (§3.6); acquisition verifies every revision and every licence blob.
3. Rebuild the split file; `sha256sum eval/splits.tsv` equals the M3.2 digest.
4. Rebuild the tuning-fold suppression catalogues; their SHA-256 equal `freeze.json`. (The selection grid need not be rerun.)
5. Regenerate held-out cases; `cases-*-held-out.jsonl` byte-identical (`cmp`, exit 0).
6. Run the held-out evaluation; `cmp` their `counts.json` with the committed one (exit 0).
7. Compare resources with the committed `resources.json` using the tolerance script.

**Tolerance (proposed).** Counts: identical, no tolerance. Resources, only when the operating system and architecture match the original run: total wall time ratio in [0.5, 2.0] and maximum peak RSS ratio in [0.8, 1.25]. On a different OS or architecture, resources are recorded and not compared. The tolerance is frozen in `freeze.json`.

M3.5 is met when steps 1–6 exit 0 and step 7 exits 0 or reports "not comparable" for a different platform.

## 14. Decisions that need the owner

The owner decides each of these; this draft records options and a recommendation only.

### 14.1 M3.0: the false-alarm budget

Unit: false alarms per repository search (§1), counting any `match` in either mode. Expected alarms are budget × searches, for an operator searching one reference repository against that many candidate repositories:

| Option | Budget | 10 searches (targeted check) | 100 (one project's dependency tree) | 1,000 (ecosystem sweep) | 10,000 (registry sweep) | What M3.6 then means on the proposed 264 held-out searches |
| --- | --- | --- | --- | --- | --- | --- |
| A | 1 in 20 (`1/20`) | 0.5 | 5 | 50 | 500 | met with at most 13 alarms |
| B | 1 in 100 (`1/100`) | 0.1 | 1 | 10 | 100 | met with at most 2 alarms |
| C | 1 in 1,000 (`1/1000`) | 0.01 | 0.1 | 1 | 10 | met only with 0 alarms; the corpus cannot show the rate is that low (§11) |

Each alarm costs a person a review of localized evidence (UC-1, UC-2). Option A suits a targeted check of a handful of candidates and is cheap to meet; it allows 50 reviews per 1,000-repository sweep. Option C is what an ecosystem sweep would want, but on this corpus it reduces M3.6 to "zero alarms observed", which can be met by luck and cannot be demonstrated. **Recommendation: B**, because it is the tightest budget this corpus can meaningfully test, it gives about one review per 100 candidate repositories, and it is still decided by a count (≤ 2 of 264). Whatever is chosen is recorded as an exact fraction before tuning starts (§2 step 1), because the tuning rule uses it.

### 14.2 Acquisition approval (M3.1)

- **What:** the 48 repositories in [manifest-proposal.json](evaluation-corpus/manifest-proposal.json), 24 Go and 24 Rust, by shallow fetch of the pinned revisions. No dependencies, submodules, releases or build outputs.
- **Size:** GitHub reports 621,386 KiB (about 607 MiB) summed over the 48 repositories, *including full history*; this is an upper bound. A depth-1 fetch transfers a compressed snapshot, normally a fraction of that. Eligible source is 58,768,417 bytes (about 56 MiB) in 6,254 paths (3,314 Go and 2,940 Rust), counted from the pinned tree listings before the generated-file rule.
- **Licences**, verified from the root licence files at the pinned revisions: MIT only (30 repositories), Apache-2.0 only (9), both MIT and Apache-2.0 files, recorded `Apache-2.0 AND MIT` (7, all Rust), BSD-3-Clause (1) and BSD-2-Clause (1). All permit redistribution with notice retention; the project redistributes none.
- **Recommendation:** approve as proposed, after a non-author has rerun `verify_manifest.py`.

### 14.3 Where the corpus is stored

Outside every repository and every version-controlled working tree (contract B1 markers), in an absolute directory named by `TRACEWEAVE_EVAL_DIR`, with `corpus/`, `derived/` (catalogues, report bodies: private), `cases/` (case bytes) and `logs/`. Options: (a) a directory under the owner's home, such as `~/traceweave-eval`; (b) an external or encrypted volume; (c) a separate private storage service (paid services need the owner anyway). **Recommendation: (a)**, local disk, never synchronized to a public location, with the runner refusing a location inside a working tree as the contract's B1 rule does for private output.

### 14.4 Corpus scale and licence allowlist

- **Scale.** 24 per language (proposed) gives 264 negative searches and the bounds in §11. 100 per language would give about 4,950 ordered searches per language and a 50-search disjoint bound per language (0.058 at zero alarms), at roughly four times the acquisition. **Recommendation:** start at 24, because M3.6 is decidable at that size and the pool and walk extend mechanically.
- **Allowlist.** The permissive list of §3.2 only. Adding MPL-2.0 or CC0-1.0 would admit a few more pool repositories (for example a CC0 Rust command runner); copyleft is excluded because the project does not want to argue use conditions for corpus code. **Recommendation:** keep as proposed.

### 14.5 Already decided elsewhere, restated

No push or publication; the manifest and results live in the implementation repository (`I` owner column) and the M3.0 record and M3.6 verdict in this one (`S`). Formatter and toolchain versions are pinned, not installed globally.

## 15. Risks and limits

- **The pool is a popularity sample.** Starred, maintained, permissively licensed repositories of 2020-era or earlier projects. It says nothing about private code, small projects or other languages.
- **Same-domain and same-stack counts may be small.** They are labels on the 264 searches, not a designed sample: the provisional split labels 20 searches `same-domain` (by shared topic), too few to say anything separately.
- **Real reuse among negatives.** Popular repositories copy snippets from each other and from documentation. Those alarms count as false alarms (§1); the audit labels them without removing them. The budget therefore measures alarms, not proven non-reuse.
- **Acquisition-time rules can change the selection.** Dependency, duplicate and generated-file checks need the files, so the provisional split in the proposal can change at step 5. The walk replaces rejected repositories mechanically, and the M3.2 digest is the one after step 5.
- **Path counts are not content checks.** Some proposed repositories have few, large eligible files (for example `benfred/py-spy`: 39 paths, 4.2 MB), which suggests generated bindings, and `rui314/mold` is listed under Rust by GitHub. The generated-file rule (§3.4) and the eligible-path minimum are applied again at acquisition, and a repository that falls below 10 eligible files is replaced by the walk.
- **Licence classifier.** Phrase rules can reject a valid licence with unusual wording (for example `XAMPPRocky/tokei`'s Apache file is `licence-unclassified`). They are conservative by design; they are not a legal review.
- **Transformation realism.** `rename` covers declared identifiers only; `fmt` uses one non-default style per language; `compound` is one fixed chain. None is an adversarial evasion budget (that is M2E.6 and later work).
- **Grid size versus tuning data.** About 30 tuning negative searches per language cannot separate configurations by false alarms at a 1/200 margin; ties will usually be broken by recall, then by the fixed order.
- **Cost.** I2 measured 8 M seeds at 1.9 s and 1.4 GiB (Rust lane) and 4.2 s and 3.1 GiB (Go lane), with work growing as reference × candidate artifacts ([contract §5.7](catalogue-report-contract.md#57-ambiguity-and-the-output-cap)). The largest proposed repositories have about 500 eligible files, so a search between two of them is about 250,000 file pairs per mode. Pair caching (§9) makes that tractable; without it the positive set (about 5,700 searches: 30 file units × 7 transformations, 150 function and 180 partial units × 8, per language) is not.

## 16. Gate mapping

| Gate | Evidence this protocol defines | Pass/fail as |
| --- | --- | --- |
| M3.0 | Owner record of `p/q` (§14.1) | record exists |
| M3.1 | Manifest; `verify_manifest.py` | exit 0; self-test rejects every broken manifest |
| M3.2 | Split file and digest; disjointness | `verify_manifest.py` exit 0; digest equality |
| M3.3 | §8 commands | all exit 0 |
| M3.4 | `counts.json`, `resources.json`, report (§10) | every figure has a denominator (schema check) |
| M3.5 | §13 steps | `cmp` exit 0; tolerance script exit 0 |
| M3.6 | §12 script | exit 0 met, 3 negative-result |
