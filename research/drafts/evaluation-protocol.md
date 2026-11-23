# M3 evaluation protocol: token-fingerprint baseline on Go and Rust

Protocol version: `m3-eval-draft-9`. Status: **ready to freeze; frozen by the commit that precedes the first tuning run** (2026-11-23). Not run. No corpus has been acquired yet; acquisition is approved (§14.2). Roadmap gates M3.0–M3.6 and backlog item TW-05 ([roadmap](../../ROADMAP.md#m3--measure-usefulness)). Corpus proposal: [evaluation-corpus/](evaluation-corpus/README.md).

Protocol digest (SHA-256, self-excluding): `0000000000000000000000000000000000000000000000000000000000000000` (all zeros: **not frozen yet**). The protocol is frozen by the spec-repository commit that fills in this digest, and that commit must precede the first tuning run (§2 step 6). The digest is the SHA-256 of this file's bytes with those 64 hex digits replaced by 64 zeros; the tuning runner and `freeze.json` (§8) repeat it, and both refuse to run if this file's digest differs.

This is a research protocol. It changes nothing in `spec/`, `schemas/`, `profiles/` or `test-vectors/`. The owner decisions it needs are recorded in [§14](#14-decisions-that-need-the-owner): decided on 2026-11-23 (M3.0 budget **1/20**, acquisition approved, storage `~/traceweave-eval`), with the options and both recommendations kept as history. The harness scripts are listed in [IMPLEMENTING.md](evaluation-corpus/IMPLEMENTING.md).

It fixes, before any result exists, what is measured and how each pass/fail becomes an exit code or a count. Where this draft leaves a number open, the number is chosen by a stated mechanical rule on the tuning split, never by looking at held-out data.

**Changes from `m3-eval-draft-8`**: a pair-completeness rule for every batched comparison, negative searches and positive cases alike (§9), correcting draft-8's claim that the caching check covers batching ([harness review, confirmation pass 2](../reviews/evaluation-harness-review.md), commit `ff907ac`, finding N4: it covers positive cases only). Budget, verdict rule, corpus and split unchanged.

**Changes from `m3-eval-draft-7`**: the 1-in-50 seed-sharing direct check compares exactly the selected pairs (one `compare` per checked reference file and configuration), replacing the per-search batch, which covered 53–97% of each search and made the estimate 25–48 times too low (§5.5); the held-out caching check stays unbatched and is what checks batching (§9); disk figures and the free-space margin, default 20 GB, minimum 10 GB (§5.5). Budget, verdict rule, corpus and split digest unchanged; rows in §19 (harness `i3-eval` commit `75b84eb`).

**Changes from `m3-eval-draft-6`**: rulings on the harness author's open points O1–O8 (`traceweave` `i3-eval` commit `d4502e0`, `eval/README.md`), added to [§19](#19-harness-rulings-m3-eval-draft-6). Budget, verdict rule, corpus and split digest are unchanged. Two new path exclusions (`path-unsafe`, `path-case-collision`, §3.4); the stamp may be read from report-document provenance until the Go CLI has a version command (an implementation change, §8); per-pair records may be committed as deterministic gzip, compared decompressed (§10, §13); an optional body cross-check in the verdict (§12); fixed git timeouts (§3.6); cells continue past a slot where every repository is skipped (§6.2); a fixed per-comparison cost and a match-heavy per-pair allowance in the estimates (§5.5).

**Changes from `m3-eval-draft-5`**: rulings on the harness author's 40 recorded ambiguities (A1–A40, `traceweave` `i3-eval` commit `c91ee91`, `eval/README.md`) and on the [non-author harness review](../reviews/evaluation-harness-review.md) (commit `20162a8`, B1–B8 and S-a–S-c). Every item is mapped to its section in [§19](#19-harness-rulings-m3-eval-draft-6). Budget, verdict rule, corpus and split are unchanged. The material ones:
- **all measured bytes are committed blob contents at the pinned revision**, read with `git cat-file` under an isolated git environment, never working-tree bytes (§3.6);
- **suppression (A26):** a frequent hash whose snippet cannot be extracted falls back to the whole fold-S file it first occurs in, so every frequent hash is suppressed in both languages; the effect on alarms is monotone and reported (§5.2);
- the `u()` strings are fixed (§6.2), `rename` numbers by first binding site (§6.3), Go top-level boundaries need `(`-depth 0 (§6.1), and units do not repeat within a cell (§6.2);
- lexing held-out files through `extract` with fingerprints discarded unread satisfies §2 (A1);
- the verdict is recomputed from per-search records in the committed first held-out result commit (§12);
- per-pair time is measured on batched comparisons, the estimate includes the direct checks, and a memory watchdog kills at 75% (§5.5);
- the checker accepts an acquired manifest and the acquisition-time `too-few-eligible-files` rejection through a new fact (§3.1, A25).

**Changes from `m3-eval-draft-4`**, from the [lane 11 audit](../lanes/11-report-audit.md) of two external design reviews (commit `d32b25c`, "Combined ranked list", items 1–3, and its follow-up list). Budget `1/20`, the verdict rule and the manifest are unchanged:
- the timing pilot becomes the **fold-S outcome count**: outcome classes on all fold-S searches with no suppression catalogue, for every (`k`, `window`), reported as a table; a pre-declared rule adds `minRegionDistinctHashes` 8 and 12 to the grid if the most conservative configuration alarms on more than half of either language's fold-S searches (§5.5); fold S still never reaches held-out data or configuration selection;
- `k` = 16, the extraction bound, is added: 192 configurations, 12 (`k`, `window`) settings; the run-budget reduction keeps both ends of `k` (§5.3, §5.5);
- the per-configuration fold-E table is committed with `freeze.json`, and the held-out alarm-audit procedure is fixed before the freeze (§5.4, §8, §12a);
- new §18 lists follow-up measurements on the same frozen corpus, none part of M3.6;
- the wording of what 132 searches bound follows the audit: 0.0224 at 0 alarms, 0.0877 one-sided at 6 (§11, §14.1).

**Changes from `m3-eval-draft-3`** (owner decisions of 2026-11-23, delegated to the coordinator):
- §14 records the decisions: M3.0 budget option A, `1/20` per unordered repository search (met when at most 6 of 132 alarm); `1/100` to be tested on a larger corpus only if this passes; acquisition of the 48 repositories and the mechanical replacements approved; storage `~/traceweave-eval` (`TRACEWEAVE_EVAL_DIR`); licence recheck failing closed;
- the budget is fixed where it enters: the tuning rule (§5.4, at most 0 fold-E alarms in 30), the freeze (§8) and the M3.6 script (§12);
- status: ready to freeze; the protocol is frozen by the commit that fills in its digest before the first tuning run (§2, §8);
- an implementer brief lists every harness script in order ([IMPLEMENTING.md](evaluation-corpus/IMPLEMENTING.md)).

**Changes from `m3-eval-draft-2`**, resolving the review's [confirmation pass](../reviews/evaluation-protocol-review.md#confirmation-pass-m3-eval-draft-2) (commit `1df11d3`):
- Go `rename` takes a name after `func` only from the unit's own head `func`, so a function literal's parameter types are never bindings (§6.3);
- an inserted Go `;` is never a run start, and `}` followed by an inserted `;` is one statement end, which removes byte-identical duplicate runs (§6.1);
- eligibility cannot hide alarms: the acquisition lexer commit must equal the frozen lexing commit, excluded files are counted per repository and reason in `counts.json`, the metrics and beside the verdict, and more than 5% excluded is an error, not a verdict (§3.4, §10, §12);
- the report states that Rust `rename` renames types and variants and misses inner pattern bindings (§6.3);
- Go function units whose body `{` follows `struct` or `interface` are skipped (§6.1);
- §14.1 presents both budget recommendations, and §14.4 the cost of 100 repositories per language.

**Changes from `m3-eval-draft-1`**, resolving the [non-author review](../reviews/evaluation-protocol-review.md) (commit `b7282bf`); each is listed with its finding in [§17](#17-review-dispositions):
- case generation is purely lexical and fully specified, so a second implementer regenerates byte-identical cases (F1);
- Go `fmt` is dropped as a cell and Go `compound` no longer formats; Rust `fmt` uses edition 2024 and counts identity output separately (F2);
- in a negative search, abstentions and every other non-result outcome are alarms (F3);
- the search unit is the **unordered** repository pair, evaluated once, with a runner symmetry check; every budget option is restated in that unit with exact binomial figures (F4);
- grouping and rejection rules are complete, including Go module paths, the tie rule, the replacement order and limit, and a token-digest duplicate rule (F5);
- a cost model, seed sharing across the tuning grid, a timing pilot on the tuning split only, a run budget and abort rules (F6);
- acquisition rechecks licence SHA-256 and classification on fetched text and fails closed (M5);
- covered-fraction reporting (F7), the limits of the ancestry check and a runner identity record (F8), and the low items.

## 0. What is measured

The system under test is the token-fingerprint baseline:
- extraction per the [extraction contract](../../spec/extraction.md) (profiles `go-tokens` and `rust2024-tokens`, `draft-1`; channels `exact` and `normalized`);
- catalogues and comparison per the [catalogue and report contract](../../spec/catalogue-report.md) (`traceweave-catalogue-draft-2`, `traceweave-seed-merge-draft-2`, `traceweave-report-draft-2`): seeds, regions, minimum evidence counted in distinct non-common hashes (§5.6), the suppression catalogue bound by digest (§5.2), the closed outcome codes (§6.4), and the caps `maxSeedsPerMode` and `maxRegionsPerMode` (§5.4, §5.7).

The question is the one M3 states: which transformations does this baseline detect, at what fragment sizes, and at what cost in false alarms, abstentions, candidate volume, runtime and memory. Embedded marks are out of scope here; M2E.7 later reuses the same held-out cases and the same budget.

The baseline is not a calibrated detector ([extraction §12](../../spec/extraction.md#12-what-the-baseline-does-not-claim), [report §8](../../spec/catalogue-report.md#8-what-the-report-must-not-claim)). This protocol measures it; it does not turn a measured rate into a probability for a single result. Generated cases are **not compilable copies** (§6.3); recall here describes lexical robustness only.

## 1. Units

**Artifact.** One eligible source file (§3.4) of one corpus repository at its pinned revision. Its catalogue id is opaque (`f` followed by a decimal index, contract §3.2); the id-to-path map stays local.

**Repository catalogue.** One catalogue per (repository, language, configuration) holding every eligible artifact of the repository. Duplicate file contents inside one repository keep the bytewise-first path only, because a catalogue forbids repeated `sha256` (OD-C9); the dropped paths are counted.

**Repository search (the M3.0 unit).** One **unordered** pair {*R*, *C*} of repositories of the same language and split, in different groups, evaluated by **one** comparison body: the repository earlier in split-hash order (§4.2) is the reference, the other the candidate, under the frozen comparison configuration and suppression catalogue of that language. A search compares every reference artifact with every candidate artifact in both modes (contract §5.3).

Why unordered: under the contract, a pair-mode **outcome** does not depend on which side is the reference. Seeds are the same hash matches with roles swapped; on one diagonal a gap in reference positions equals the gap in candidate positions, so the same seeds merge into the same regions; distinct-hash evidence, common hashes and ambiguity ("another reportable region uses any of its reference or candidate positions") are symmetric; the cap truncates the listing but the outcome is decided from all regions (§5.7–§5.8). So *R*→*C* and *C*→*R* alarm together, and counting both would double-count. The runner checks this (§9); if any checked pair differs, M3.6 is an error and the protocol must be revised.

**Alarm.** A search raises an alarm when **any** of the following appears in its body:
- a pair with mode outcome `match` in either mode;
- a pair with mode outcome class `abstain` (`ambiguous` or `seed-limit-exceeded`) in either mode;
- a pair with status `not-compared` for any reason (`reference-extraction-error`, `candidate-extraction-error`, `insufficient-tokens`);
- a `rejected` body.

In words: anything other than "compared, `no-match` in both modes" on every pair is an alarm. An operator would have to look at it, and a configuration must not pass M3.6 by abstaining. Eligibility (§3.4) admits only files that lex without error and have at least 16 tokens (the largest `k` in the grid), so the third bullet cannot fire for an eligible file under any grid configuration; if it fires, it counts. Alarm counts are reported per reason and per mode beside the total.

**False alarm.** An alarm in a **negative search** (§7). Every such alarm counts, whatever caused it. A post-hoc audit may label it (boilerplate, real shared provenance, unexplained), but labels never remove it from the M3.6 count.

**Positive case.** One mechanically generated insertion of transformed held-out source into a different-group host repository (§6). Each case is evaluated by exactly one comparison: reference = the source repository, candidate = the host repository with the case applied.

**Hit.** For a case and a mode, a hit requires all of:
1. the ground-truth pair (reference artifact = the source file, candidate artifact = the modified host file) has mode outcome `match`;
2. at least one listed region of that pair and mode has status `reportable`, `ambiguous: false`, a `candidateSpan` overlapping a ground-truth candidate segment by at least one byte, and a `referenceSpan` overlapping the same segment's source span by at least one byte.

A case is **detected** when it is a hit in either mode. Because one byte of overlap is lenient, every detected case also reports its **covered fraction**: the bytes of ground-truth candidate segments covered by the union of the `candidateSpan`s of qualifying regions, divided by the total bytes of those segments (§10). Misses are classified by the first matching rule: `extraction-error`, `insufficient-tokens`, `seed-limit-exceeded`, `ambiguous`, `below-minimum-evidence`, `common-only`, `no-shared-fingerprints`, `truncated` (outcome `match` but the overlapping region is not listed because of `maxRegionsPerMode`), `mislocalized` (outcome `match` with no overlapping listed region).

**Abstention.** A pair outcome `insufficient-tokens`, or a mode outcome `ambiguous` or `seed-limit-exceeded` (contract §6.4). In positive cases they are miss reasons; in negative searches they are alarms.

## 2. Order of work

Each step is a commit. Gate IDs in brackets.

| Step | Content | Needs |
| --- | --- | --- |
| 1 | M3.0 budget recorded in the spec repository: **done**, `1/20`, §14.1 (2026-11-23) | owner [M3.0] |
| 2 | Manifest frozen; acquisition approved, covering the mechanical replacements of §4.3: **approval done** (2026-11-23, §14.2) | owner [M3.1] |
| 3 | Acquisition: shallow fetch of each pinned revision; inventory; licence recheck; acquisition-time rules (§3.6) | step 2 |
| 4 | Groups and rejections by the acquisition-time rules; split file and its digest committed | step 3 [M3.2] |
| 5 | Fold-S outcome count and timing pilot (§5.5); pre-declared grid rule applied; run budget fixed | step 4 |
| 6 | Protocol digest filled in and committed (this file frozen); then tuning: suppression catalogues, grid, selection rule (§5), on tuning data only | steps 1, 5 |
| 7 | Freeze file, tuning table and alarm-audit procedure committed together (§8, §12a) | step 6 [M3.3] |
| 8 | Held-out positives generated; held-out extraction, comparison and metrics | step 7 |
| 9 | Held-out report and counts committed (the "first held-out result commit") | step 8 [M3.4] |
| 10 | Independent rerun | step 9 [M3.5] |
| 11 | Verdict computed | steps 1, 9 [M3.6] |

Before step 7, **no held-out file is fingerprinted, catalogued or compared**, and no held-out positive case is generated. Steps 3 and 4 read held-out files only to compute byte lengths, SHA-256 digests, the generated-file test, the token count and lexing status (§3.4), the token digest (§4.1) and dependency declarations (§4.1). Lexing is the profile's tokenizer only. **Ruling A1:** the implementations have no lex-only command, so lexing runs `extract` (with the shipped configuration, `k` 5, `window` 4) and keeps only the status, error code, token count and token digest; fingerprints, k-grams and window selections are discarded unread, never written to a committed or derived file, and the child's output passes only through temporary files under `TRACEWEAVE_EVAL_DIR/tmp`, deleted after reading. This satisfies "no k-gram, hash or window is computed" in its purpose: nothing derived from them exists after the step.

## 3. Corpus

### 3.1 Selection rule

The rule is mechanical. Its inputs are a committed **pool snapshot** and a committed **walk record**; rerunning the GitHub query later returns a different pool (stars and pushes change), so the snapshot, not the query, is what a reviewer reproduces.

1. **Pool query** (GitHub repository search, sorted by stars, descending, first 100 results, retrieved once per language and committed verbatim in the manifest):
   `language:<Go|Rust> stars:>=2000 fork:false archived:false size:<=50000 created:<2023-11-22 pushed:>=2025-11-22`
   This asks for maintained, non-fork, non-archived repositories whose primary language is the target, at most 50,000 KiB including history, created at least three years before the snapshot.
2. **Order.** Sort the pool by `SHA-256("traceweave-m3-select-v1\n" || lowercase(full_name))` as lowercase hex, ascending. Popularity admits a repository to the pool but does not order the sample.
3. **Walk.** Visit repositories in that order and give each exactly one verdict, applying the first rule that fires:
   1. owner in the exclusion list (§3.5) → `excluded-owner-census` or `excluded-owner-development-exposed`;
   2. repository name or a topic contains `awesome` → `list-repository`;
   3. owner already accepted → `owner-already-selected` (one repository per owner);
   4. default-branch head not resolvable → `revision-unresolved`;
   5. pinned tree listing truncated by the API → `tree-truncated`;
   6. licence check (§3.2) fails → `licence-file-missing`, `licence-unclassified` or `licence-not-allowed`;
   7. fewer than 10 eligible paths → `too-few-eligible-files`; eligible bytes above 20 MiB → `eligible-bytes-over-limit` (§3.3);
   8. *at acquisition only:* the acquisition-time rules of §4.1 → `dependency-linked`, `duplicate-content`; the licence recheck of §3.6 → acquisition stops (no verdict, see there); fewer than 10 eligible files after the content rules of §3.4 → `too-few-eligible-files`, recorded with the walk fact `eligibleFileCountAfterContentRules` (counted after the content rules and before the within-repository duplicate rule; ruling A25, A30). An acquired manifest records that fact for every repository that passed the path rules, and `verify_manifest.py` derives the verdict from it;
   9. otherwise `accepted`.
4. **Stop** when 24 repositories per language are accepted (the proposed size; scale is an owner choice, §14.4).

The walk record lists every visited repository with its verdict and the facts the verdict rests on (revision, resolution time, licence files, path counts), including repositories rejected at acquisition. [`verify_manifest.py`](evaluation-corpus/verify_manifest.py) recomputes the order, the rule 1–3 verdicts, the fact-based verdicts and the stopping point from the snapshot, and checks that the accepted set equals the manifest entries.

**Pinned revision.** The 40-hex commit of the default-branch head, resolved with `git ls-remote https://github.com/<owner>/<repo> refs/heads/<branch>` on the snapshot date and recorded with its resolution time. No floating reference is ever used again.

### 3.2 Licence and redistribution, from the licence file

**Licence files** are the root entries of the pinned tree whose names match `^(licen[cs]e|copying|unlicense)([-._][a-z0-9.-]+)?$`, case-insensitively. Each is fetched at the pinned revision and recorded with its path, git blob SHA-1, SHA-256 and byte length.

**Classification** (classifier `m3-licence-classifier-v1`, implemented in `verify_manifest.py`): the text is decoded as UTF-8 (invalid bytes replaced), lowercased, `*` and `#` removed and whitespace runs collapsed to one space. A file is classified as an identifier when it contains every required phrase of that identifier; BSD-3-Clause hides BSD-2-Clause and ISC hides 0BSD. Exactly one identifier is the classification; none is `unrecognized`; more than one is `multiple:…`. The classifier never guesses.

| Identifier | Required phrases (after normalization) | Allowed |
| --- | --- | --- |
| MIT | "permission is hereby granted, free of charge, to any person obtaining a copy"; "the above copyright notice and this permission notice shall be included" | yes |
| Apache-2.0 | "apache license"; "version 2.0, january 2004" | yes |
| BSD-3-Clause | "redistribution and use in source and binary forms, with or without modification, are permitted"; "endorse or promote products derived from this software" | yes |
| BSD-2-Clause | the first BSD phrase | yes |
| ISC | "permission to use, copy, modify, and"; "distribute this software for any purpose with or without fee is hereby granted"; "provided that the above copyright notice and this permission notice appear in all copies" | yes |
| 0BSD | the first two ISC phrases | yes |
| Unlicense | "this is free and unencumbered software released into the public domain" | yes |
| Zlib | "altered source versions must be plainly marked as such" | yes |
| GPL-2.0, GPL-3.0, AGPL-3.0, LGPL-3.0, MPL-2.0, EUPL, CC | version header phrases (in the classifier) | no |

**Licence expression.** The identifiers of all licence files joined with ` AND `, sorted. Where upstream offers a choice (for example `MIT OR Apache-2.0`), `AND` is the conservative reading: the project complies with every file. A choice could only be recorded from evidence outside the licence files, which this rule does not read.

**Redistribution.** Every allowed licence permits redistribution: with notice retention (`permitted-with-notice`: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Zlib) or without conditions (`permitted`: 0BSD, Unlicense). The project nonetheless **redistributes no corpus source**: only the manifest, digests, byte offsets, counts and reports are committed. Catalogues and report bodies of corpus code stay private by default (contract OD-C14).

The classifier is a screening rule, not a legal opinion. It checks the root licence files only; files under other licences inside a repository (vendored code, nested `LICENSE` files) are excluded from evaluation by the eligible-file rule, not cleared by it.

### 3.3 Size limits

- GitHub `size` at most 50,000 KiB (pool query).
- At least 10 and at most 20 MiB of eligible paths (§3.4), counted from the pinned tree listing, and at least 10 eligible files after the content rules at acquisition.
- Per file: larger than 1,048,576 bytes is `oversize`, excluded and counted. This equals the shipped `maxInputBytes`, so no evaluated file can produce `input-too-large`.

### 3.4 Eligible files (generated and vendored code excluded by rule)

**Go paths.** A path is eligible when it ends in `.go`, does not end in `_test.go` or `.pb.go`, its file name does not start with `.` or `_`, and no directory component is `vendor`, `testdata`, `third_party`, `third-party`, `examples`, `example`, `test`, `tests` or `node_modules`, or starts with `.` or `_`.

**Rust paths.** A path is eligible when it ends in `.rs`, is not named `build.rs`, and no directory component is `target`, `vendor`, `testdata`, `third_party`, `third-party`, `examples`, `example`, `test`, `tests`, `benches`, `fuzz` or `node_modules`, or starts with `.`.

**Content rules, at acquisition**, in this order, each exclusion counted by reason:
1. **Generated, Go:** any line before the first line that is neither blank nor a comment matches `^// Code generated .* DO NOT EDIT\.$` (the Go convention). **Generated, Rust:** the first 1,024 bytes contain `@generated`, or a line there matches `(?i)^\s*//.*\b(auto-?generated|generated by|do not edit)\b`.
2. **Lexing:** the profile's tokenizer (extraction §4–§5, `maxInputBytes` 1,048,576) returns `error` → `lex-error`.
3. **Too short:** fewer than 16 tokens → `under-16-tokens`.

**Eligibility cannot hide alarms.** Rules 2 and 3 remove files that would otherwise give `not-compared` pairs, which count as alarms (§1). So:
- the lexer used at acquisition is the implementation's lexer at a recorded commit (the **acquisition lexing commit**, written into the split file's companion `eval/acquisition.json`), and it must equal the lexing commit frozen in `freeze.json` (§8); a difference is an M3.3 failure;
- excluded files are counted per repository and per reason (`generated`, `lex-error`, `under-16-tokens`, `oversize`, and the path rules), with the repository's eligible-path count as denominator, in `counts.json`, in the metrics (§10) and beside the M3.6 verdict (§12);
- **bound:** if, over the held-out split of a language, `lex-error` plus `under-16-tokens` exclusions exceed **5%** of the files passing the path and generated rules, or exceed 25% in any single held-out repository, M3.6 is an error, not a verdict.

Symbolic links, submodules and non-UTF-8 paths are excluded. **Unsafe and colliding paths** (ruling O2): a path with a `..` component or a component that is a version-control directory name (`.git`, `.hg`, `.svn`, `.jj`, `.bzr`, `_darcs`) is `path-unsafe`; and when two or more paths of one repository that pass the other path rules are equal after Unicode default full case folding (Unicode 17.0.0, as extraction §3a), **all** of them are excluded as `path-case-collision`, because eligible files are written out as plain files and would collide on a case-insensitive volume. Both are path rules, counted per repository, and lie outside the A30 exclusion-bound denominator; acquisition counts can therefore differ from the manifest's path counts, which is recorded and does not fail (A4). **Oversize** (ruling A4): `eligiblePathCount` and `eligiblePathBytes` exclude files over 1,048,576 bytes, which are counted in `oversizePathCount`; this is the convention the proposal manifest used. Inline Rust `#[cfg(test)]` modules stay in, because removing them needs a parser; this is stated in every Rust result.

### 3.5 Exclusions

- **Census repositories** ([census checkpoint](../public-census-checkpoint.md)): `davecgh/go-spew`, `rakyll/hey`, `dtolnay/itoa`, `sharkdp/hexyl`. Because split groups follow owners (§4), the whole owner is excluded: `davecgh`, `rakyll`, `dtolnay`, `sharkdp`. This also keeps out, for example, `sharkdp/fd`, which is in the Rust pool.
- **Development-exposed code:** owners `golang` and `rust-lang`. The I2 cross-check built catalogues from the Go and Rust standard libraries, including identical, partial, renamed and reformatted copies (`xcheck/HISTORY-I2.md` on `merge-i2`), so that code has been seen by the project. Copies of standard-library code *inside* corpus repositories are not excluded (exclusion is by owner). That exposed the developers, not the frozen parameters, since the grid and rules are fixed in advance; the report states it.
- **Private applications** and the project's own repositories are never in the pool.
- **Forks.** Excluded by the query (`fork:false`) and rechecked in the snapshot.

### 3.6 Acquisition (after owner approval only)

For each repository visited by the walk at acquisition, in walk order: `git init --template=`, `git fetch --depth 1 --no-tags https://github.com/<owner>/<repo> <revision>`, inside the corpus root (§14.3). Git verifies every object's SHA-1 against the pinned commit.

**All measured bytes are committed blob contents at the pinned revision.** Every byte the evaluation hashes, measures, lexes, fingerprints, classifies or transforms (source files, licence files, `go.mod` and `Cargo.toml`) is read as the blob content of the pinned commit's tree with `git cat-file blob <sha1>` (or `--batch`), and its SHA-1 is checked against the tree entry. Working-tree bytes are never used, so a repository's `.gitattributes` (`ident`, `eol`, filters), the operator's `core.autocrlf` and case-insensitive file systems cannot change them; a checkout, if made at all, is for human inspection only. Paths come from `git ls-tree -r -z` of the pinned commit. **Git environment** (review B2): `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_TERMINAL_PROMPT=0`, `protocol.allow=never` with `protocol.https.allow=always` (`file` only in the harness's own tests), hooks and LFS filters disabled, no submodule recursion, and a timeout on every git call: **1,800 s per fetch, 120 s per `ls-remote`, 600 s per local command** (ruling O6); a timeout exits 2. No build, test, build script, macro, package manager or acquired program is run; formatters run only on generated positive cases (§6.3). Then, per repository:

1. **Licence recheck, failing closed (M5).** List the root licence files again; each must exist with the recorded blob SHA-1; recompute each file's SHA-256 from the checked-out bytes and rerun `m3-licence-classifier-v1` on them (`verify_manifest.py --licence-dir`). Any difference in the set of files, a SHA-1, a SHA-256 or a classification makes acquisition **exit 1 and stop**. The manifest must then be revised and approved again; a mismatch is never resolved by replacement.
2. Record every path's SHA-256, byte length and eligibility reason (§3.4), and the eligible files' token digests (§4.1).
3. Record dependency declarations (§4.1) from every `go.mod` and `Cargo.toml` outside excluded directories.
4. Apply the acquisition-time rules (§4.1, §3.4) against the repositories accepted earlier in the walk; a rejected repository is recorded with its facts, and the walk continues (§4.3).

## 4. Groups and splits

### 4.1 Acquisition-time rules

Each repository *X* reached by the walk is compared with every repository *Y* **already accepted** earlier in the walk, in the same language. If any rule links them, *X* (the later one in walk order) is rejected and *Y* stays. Groups therefore stay one owner each, and "unrelated" negatives are unrelated by construction.

1. **Dependency, Go** (`dependency-linked`). Let *Mods(Y)* be the `module` paths declared in the `go.mod` files of *Y* (outside excluded directories). *X* is linked to *Y* when a `require` path in any `go.mod` of *X* equals some *M* ∈ *Mods(Y)* or begins with *M* followed by `/`, and symmetrically from *Y* to *X*. Paths are compared exactly as written, including vanity paths (`google.golang.org/grpc` matches only if a corpus `go.mod` declares it) and major-version suffixes (`…/v5` is part of the path). `replace` and `exclude` directives are ignored.
2. **Dependency, Rust** (`dependency-linked`). Let *Crates(Y)* be the `[package] name` values in the `Cargo.toml` files of *Y*. *X* is linked to *Y* when any dependency entry of *X* (any table: `[dependencies]`, `[dev-dependencies]`, `[build-dependencies]`, `[workspace.dependencies]`, `[target.*.…]`) has a crate name (its `package = "…"` value if present, otherwise its key) in *Crates(Y)*, or a `git` URL that, lowercased and stripped of a trailing `/` and `.git`, equals `https://github.com/<Y>`; and symmetrically.
3. **Duplicate content** (`duplicate-content`). *X* and *Y* share an eligible file of at least 1,024 bytes with equal SHA-256, **or** share an eligible file with at least 64 tokens whose **token digest** is equal. The token digest is SHA-256 over the concatenation, for every token of the exact stream in order, of `LP(class) || LP(value)` (extraction §7 notation), so whitespace and comments (removed by the profile's own lexer) and reformatting that changes no token do not change it.
4. **Fork network.** Either is recorded by GitHub as a fork of the other (the pool excludes forks, so this is a check).

Pairs that share a third-party dependency outside the corpus are kept; they are the same-stack negatives (§7).

**Residual leak, stated.** Edited copies (a vendored router whose lines were changed, a translated port) share neither digest and are not caught. A rule that would catch them is fingerprint similarity, which would run the system under test on held-out data before the freeze; this protocol does not do that.

### 4.2 Group and split assignment

After §4.1 every group is one owner, so the group id is the lowercase owner login. Per language, sort groups by `SHA-256("traceweave-m3-split-v1\n" || language || "\n" || group)` ascending. The first ⌊G/2⌋ groups are `held-out`, the rest `tuning`. A group lies in exactly one split.

### 4.3 Replacements and what approval covers

A repository rejected at acquisition is replaced by continuing the walk in the committed order, with the same rules; the replacement's facts (revision, licence files and their digests, path counts) are recorded in the walk like any other. Replacements can change the split assignment of other groups, because the split is computed over the final groups.

**Owner approval of M3.1 covers the listed entries and these mechanical replacements**, up to **8 replacements per language**. A ninth stops acquisition for that language and returns to the owner. Known consequences from public dependency information, to be confirmed from the pinned `Cargo.toml` and `go.mod` files: in Rust, `seanmonstar/reqwest` and `tokio-rs/axum` depend on `hyper`, and `hyperium/hyper` is earlier in the walk, so both are likely replaced; in Go, `micro/go-micro` likely requires `google.golang.org/grpc`, so the later `grpc/grpc-go` is likely replaced. The pool holds 71 further Go and 61 further Rust repositories beyond the current walks.

### 4.4 Split file and digest (M3.2)

The split file is UTF-8, one line per repository, sorted bytewise, each line `language TAB split TAB group TAB owner/repo TAB revision LF`. Its SHA-256 is the **split digest**. The manifest proposal carries the digest of its provisional split; the M3.2 digest is the one computed after acquisition and committed with the split file. `verify_manifest.py` recomputes it and checks group disjointness.

## 5. Tuning (tuning split only)

### 5.1 Folds

Per language, sort tuning groups by `SHA-256("traceweave-m3-fold-v1\n" || language || "\n" || group)`. The first half is fold **S** (suppression source, fold-S outcome count and timing pilot), the rest fold **E** (tuning evaluation). Fold S is never used for configuration selection or to measure detection; its false-alarm counts (§5.5) feed only the pre-declared grid rule and the report. Fold E never contributes to a suppression catalogue.

### 5.2 Suppression catalogue construction

For a threshold *T*, a hash of channel *c* is **frequent** when it appears among the fingerprints of eligible files from at least *T* distinct fold-S groups. For each frequent hash, take its first occurrence in (group, path, position) order and cut the k-gram's span from that file into a **snippet artifact**: exactly the bytes of the k-gram span. Extract the snippet; keep it if its fingerprints in channel *c* include the hash.

**Fallback (ruling A26).** A snippet can fail: Go semicolon insertion at a cut can change the last token, and in Rust a k-gram with an unbalanced `(`, `[` or `{` does not lex at all (`unbalanced-delimiter`). The review measured 8 of 15 Rust frequent snippets dropped at `k` 5, `window` 4 and 44 of 81 at `k` 16, and real Rust boilerplate such as `) -> Result<…> {` is unbalanced. For each frequent hash whose snippet fails, the **whole fold-S file** of its first occurrence is added to the suppression catalogue instead (once per file), as an ordinary artifact from its real extraction record. That file's fingerprints include the hash by construction, so **every frequent hash is suppressed in both languages**.

**Why this choice, and its effect on the false-alarm side.** Without the fallback, roughly half of Rust boilerplate could never be suppressed while Go's could, so the Rust result would measure a defect of the snippet mechanism rather than the method. The fallback has a cost: the added files' other hashes (**collateral hashes**, not frequent) also become common. Adding common hashes can only lower or keep a region's evidence (contract §5.6); it cannot create a reportable region, so for any pair it can turn an alarm into no alarm but never the reverse. **Alarms are therefore monotone non-increasing and recall is non-increasing as suppression grows**, at every *T*. Two safeguards follow: the selection rule (§5.4) maximizes recall among configurations within the fold-E bound, so collateral suppression that costs recall is penalized; and every suppression catalogue's counts are reported (frequent hashes, kept snippets, fallback files, collateral hashes per channel) in the tuning table, the freeze and beside the M3.6 verdict, so a verdict that rests on heavy collateral suppression is visible as such. Whole-file catalogues built from all fold-S files were rejected: they would make every fold-S hash common (in effect *T* = 1), which suppresses far more than boilerplate.

**Empty catalogues and small folds** (A6). If no hash is frequent, the builder refuses an empty catalogue and that *T* acts as no suppression (`"none"` in the comparison configuration, recorded as `empty`); ties then prefer `none`. A *T* larger than the number of fold-S groups is always empty.

The suppression catalogue is the catalogue of kept snippets and fallback files, built by the ordinary builder (contract §3.8), so its digest binds into the comparison configuration as `suppressionCatalogueSha256`. It is built from **fold S only**: the builder refuses any other repository, and the fold-S list is recorded in `freeze.json` and checked by `tune` and at the freeze (review S-c, B8). Snippet bytes stay local; the catalogue is private. Suppression stays advisory (contract §5.2).

### 5.3 Grid

Fixed in advance; 192 configurations per language (288 if the §5.5 pre-declared rule fires):

| Parameter | Values |
| --- | --- |
| `k` | 5, 8, 12, 16 (16 is the extraction bound) |
| `window` | 4, 8, 16 |
| `minRegionDistinctHashes` | 2, 3, 4, 6; plus 8 and 12 only if the §5.5 rule fires |
| suppression threshold *T* | none, 2, 3, 5 |
| `mergeGap` | equal to `window` |
| `maxSeedsPerMode`, `maxRegionsPerMode` | 1,000,000 and 1,000, fixed |
| `maxInputBytes` | 1,048,576, fixed |

All values are inside the extraction and comparison bounds (extraction §10, OD-21; contract §4, OD-C33). For orientation (lane 11 audit): under the shipped comparison the smallest possible `match` covers k + 1 tokens (two adjacent selected k-grams with distinct hashes) and the guaranteed one 2·w + k − 1 tokens (two disjoint full windows that merge under `mergeGap` = w). With `minRegionDistinctHashes` 2 the grid's floor k + 1 runs from 6 tokens (`k` 5) to 17 (`k` 16).

**Seed sharing.** Seeds, diagonals and regions depend only on the two catalogues, which depend only on (`k`, `window`), and on `mergeGap` = `window` and the fixed caps. `minRegionDistinctHashes` and *T* act after regions are formed: *T* decides which hashes are common, which changes `distinctCommonHashes`, region status, ambiguity among reportable regions and the outcome, but not the seeds or regions. So the runner computes, per (`k`, `window`) and file pair, the regions with their distinct-hash sets once, and derives the 16 (`minRegionDistinctHashes`, *T*) bodies (24 if the §5.5 rule fires) from them. **Check:** for each (`k`, `window`), file pairs with `u(pair id, 1) mod 50 = 0` (§6.2) are also compared directly under all of those configurations, and every derived body must equal the direct body byte for byte; any difference stops tuning (exit 2).

### 5.4 Selection rule

On fold E, generate positive cases with the §6 generator (namespace `tuning`) and run all fold-E negative searches. For each configuration compute: *a* = false alarms per negative search (§1 alarm rule, unordered searches), and *r* = the unweighted mean, over transformation × bucket cells with at least 10 cases, of detected/cases.

**Pooling (ruling A28).** One configuration is selected for both languages: *a* and *r* are pooled over Go and Rust; cells are language × transformation × bucket with unit kinds merged; suppression catalogues stay per language (one *T* for both).

1. Eligible configurations: *a* ≤ budget / 2, the M3.0 budget halved as a margin for tuning-to-held-out drift. With the decided budget `1/20` this is *a* ≤ `1/40`, evaluated in integers as `alarms × 40 ≤ N_E` over the N_E fold-E searches of both languages together.
2. Choose the eligible configuration with the largest *r*. Ties, in order: smaller *a*; smaller `k`; larger `minRegionDistinctHashes`; smaller `window`; *T* in the order none, 5, 3, 2.
3. If none is eligible, choose by smallest *a*, then the same ties.

The selection runs as a script whose exit status is 0 when it selected by rule 2, 3 when by rule 3. Either way the selected configuration is frozen; rule 3 is reported.

**Tuning table, committed with the freeze.** The script writes `eval/tuning-table.json`: one row per configuration with *a* (alarms and N_E, per language and pooled, per alarm reason), *r* and its cell counts, reportable regions per search (mean and maximum), and the rule that selected. It is committed **in the same commit as `freeze.json`** (§8), so every rejected configuration stays visible, grouped by `k`.

**What the margin means at this size.** Fold E has about 6 groups per language, so 15 unordered searches per language and 30 in all. With `1/40` and N_E = 30, rule 1 means **zero alarms** on fold E (any budget option of §14.1 would have meant the same). That is mechanical and harmless, and it is the honest reading of how little the tuning split can say about false alarms.

### 5.5 Cost model, timing pilot, run budget and abort rules

**Pair counts** from the manifest's eligible-path counts (provisional split; acquisition can change them):

| Workload | File pairs per configuration | Configurations | Pair comparisons |
| --- | --- | --- | --- |
| Held-out negatives (66 unordered searches per language) | 685,911 Go + 968,312 Rust = 1.65 M | 1 | 1.65 M |
| Held-out positives (about 2,500 Go and 2,850 Rust cases; only the modified host file is new) | about 0.6 M | 1 | 0.6 M |
| Fold-S outcome count (15 unordered searches per language, no suppression) | 495,756 Go + 141,233 Rust = 0.64 M | 12 (`k`, `window`), seeds shared | 7.6 M |
| Fold-E negatives (15 unordered searches per language) | 245,933 Go + 185,952 Rust = 0.43 M | 12 (`k`, `window`), seeds shared | 5.2 M |
| Fold-E positives (fewer cases: at most 3 units × 6 source repositories per cell) | about 0.3 M | 12 | 3.6 M |

Pair caching (§9) makes positives cheap: a positive comparison differs from an unmodified host comparison only in the pairs that involve the modified host file. Without seed sharing the fold-E rows are 16 times larger (about 141 M pair comparisons). In all, about 18.7 M pair comparisons; at the review's assumed 1 ms per pair, about 5 hours.

**Fold-S outcome count and timing pilot (step 5), tuning split only.** This answers the external reviews' question whether `k` = 5 alarms on unrelated code (lane 11, R1), inside tuning and before the protocol digest is filled in.
- **Searches:** all unordered fold-S searches of each language (about 15 per language), as defined in §1, with **no suppression catalogue** (*T* none). Fold S is otherwise only the suppression source; it is never used for configuration selection (§5.4 uses fold E) and never touches held-out data.
- **Settings:** every (`k`, `window`) of the grid (12), and for each, every `minRegionDistinctHashes` value of the grid (seed sharing, §5.3).
- **Recorded:** per language and configuration, the number of searches with an alarm (§1) and the counts per outcome class and code (`match`, `ambiguous`, `seed-limit-exceeded`, `not-compared`, `no-match` codes), per mode. Also, on 1,000 file pairs per language chosen with `u("pilot|" || language, j) mod n` (j = 0…999) over the bytewise-sorted list of all fold-S searches' file pairs (A35), the per-pair time and peak RSS. **Per-pair time (ruling B6, replaces A19's single-pair timing):** the sampled pairs are grouped by search and compared as **one batched `compare` per search** (reference catalogue of the sampled reference files, candidate catalogue of the sampled candidate files), by both implementations; *t* is the batch wall time divided by the number of pairs in the batch, recorded per setting as the median and 95th percentile over batches. Process start is thereby included once per batch, as in the real runs.
- **Output:** `eval/pilot.json` and a report table "fold-S alarms by `k`, `window` and `minRegionDistinctHashes`", committed before step 6. The `k` = 5 rows are reported as the direct answer to R1, whatever they show.

**Pre-declared grid rule (the only data-dependent grid change allowed).** Written here before the pilot runs. Let the most conservative configuration be `k` 16, `window` 16, `minRegionDistinctHashes` 6, *T* none. If it raises an alarm in **more than half** of the fold-S searches of **either** language (alarms × 2 > searches), `minRegionDistinctHashes` **8 and 12** are added to the grid (288 configurations), before the protocol digest is filled in and before any fold-E outcome is computed. Otherwise the grid stands at 192. No other grid value, rule or threshold may change in response to the pilot; `pilot.json` records which branch was taken.

**Run budget.** Estimated tuning time = Σ over the 12 settings of (fold-E pair comparisons × that setting's 95th-percentile *t*) + extraction. If it exceeds **24 hours** on the pilot machine, the grid is reduced **before any fold-E outcome is computed**, by removing, in this order, `window` 16, then `k` 8, then `k` 12, then `window` 8, until the estimate fits; so `k` 5 and `k` 16, both ends, survive any reduction. The reduction is recorded in `pilot.json` and the freeze. Estimated held-out time is computed the same way and recorded.

**Fixed cost and match-heavy pairs (ruling O8).** Every estimate also adds, per expected comparison, a measured **process start** (a one-file comparison, both implementations). Positive comparisons and their direct checks use a **match-heavy per-pair time**: the pilot also compares, on fold S only, each timed search's sampled reference catalogue against itself, and uses the 95th percentile of that per-pair time for positives. Both are measured in the pilot and recorded in `pilot.json`.

**Estimate contents (ruling B5, amended in draft-8).** Every estimate includes both implementations (A2); the 1-in-50 direct checks of §5.3, which **compare exactly the selected pairs**: per reference file with a selected pair and per configuration, one `compare` of that file's single-artifact catalogue against a catalogue of its selected candidate files (two catalogue builds per such file and setting, one comparison per configuration); and, for held-out, the slowest setting (A19), because the frozen one is not yet known. The selection (`u(pair id, 1) mod 50 = 0`) and the pair ids of §6.2 are unchanged; every selected pair's direct body bytes must equal its derived bytes. The draft-6 wording, one `compare` per search and configuration over all checked files' catalogues, is withdrawn: it compared 53–97% of each search rather than 1 in 50 of its pairs, and made the estimate 25–48 times too low. If the grid does not fit after all four reductions, tuning refuses (exit 2).

**Disk (draft-8).** Per stage on the proposed corpus, from the harness's own accounting (`i3-eval` `75b84eb`): acquisition ≤ 0.6 GB of bare depth-1 repositories plus 0.06 GB of plain files; the pilot ≤ 0.9 GB of fold-S catalogues; tuning ≤ 0.2 GB at a time (each setting's fold-E catalogues are deleted when it is done); held-out ≤ 0.2 GB of catalogues plus the negative report bodies, kept **gzip-compressed** for the audit and the verdict's body check (O4), 0.2–3.5 GB (3.3–28 GB uncompressed; 18× compression measured on synthetic bodies, 8× assumed for the upper bound). **In all 2–5.5 GB of data at the end.** Bodies that no later stage needs (positive-only, symmetry, direct-check) are deleted, and a deleted catalogue is rebuilt from the verified corpus if needed. **Free-space margin:** every stage refuses to start (exit 2) with less than the margin free on the corpus root's volume, and long runs recheck it every 50 child processes; falling below it mid-run is an abort (exit 2, no verdict, as §5.5's other aborts). The margin is `TRACEWEAVE_EVAL_MIN_FREE_GB`, **default 20 GB**, and the operator may lower it to a **minimum of 10 GB**, recorded in `identity.json`. Why 10: it covers the 5.5 GB upper bound of all data still to be written, plus 4.5 GB, which absorbs the largest uncertainty, body compression, down to about 4× (half the assumed 8×; at 4× the bodies are 7 GB and the total about 9 GB). Below 10 GB a compression shortfall could fill the volume mid-run; moving the corpus root to another volume (§14.3) is the remedy instead.

**Memory (ruling B4).** A watchdog samples the resident set size of every child process and of the harness process at least once per second, and kills the run the moment the sum exceeds 75% of physical memory. To stay under it, a runner may split one search into batches of reference files: pair outcomes are independent of other artifacts (contract §5.2), so the assembled body is the same, and the 1-in-50 caching check covers it.

**Abort rules.** Tuning or the held-out run stops with exit 2 and **no verdict** if: its wall time exceeds 3 times its recorded estimate; the memory watchdog fires; or a seed-sharing or pair-caching check differs. An abort writes `identity.json` and `run.json` with `status: aborted` (A34). An aborted held-out run is reported as aborted; resuming requires a protocol revision.

For orientation only: I2 measured 8 M seeds at 1.9 s and 1.4 GiB (Rust lane) and 4.2 s and 3.1 GiB (Go lane) per mode, worst-case periodic input ([contract §5.7](../../spec/catalogue-report.md#57-ambiguity-and-the-output-cap)). The harness review measured batched comparisons on standard-library code outside the corpus: at `k` 5, `window` 4 about 3.6–4.1 ms per pair (Rust CLI) and 5.9–8.7 ms (Go CLI); at `k` 8, `window` 8 0.7 and 1.4 ms; at `k` 16, `window` 16 0.3–0.4 and 0.6–0.7 ms. With both implementations and the direct checks batched, its estimates are 4–8.5 hours for the fold-S count, 4.5–10 hours of tuning comparisons plus the batched direct checks, and 1–10 hours held-out, depending on the frozen `k`. Peak memory at `k` 5 was about 0.6 MB per pair in the Rust CLI, so large searches need the batching above. Report bodies were 2–17 KB per pair; bodies of pairs that are `no-match` in both modes need not be kept once the per-pair record (§10) is written, which keeps derived data near the §14.2 estimate. The pilot replaces all of these with measurements on the corpus.

## 6. Positive set (held-out sources, generated after the freeze)

All case generation is **lexical**: it uses only the token stream that the profile's own lexer produces (extraction §4–§5: class, exact text, byte span, and Go's inserted `;`), plus a formatter for Rust `fmt`. No parser or name resolution is used, so a second implementer with the same lexer regenerates the same bytes.

### 6.1 Definitions on the token stream

Write *tokens* for the exact stream of a file. **Depth** of a token is the number of unclosed `{` before it; `(`/`[` depth likewise, counted separately.

- **Function unit.**
  - **Go:** a `func` token at `{`-depth 0 and `(`-depth 0. Its body opens at the first later `{` with `(`-depth and `[`-depth equal to those at `func`; the unit ends at the matching `}`. A `func` token with no such `{` before the next `;` at `{`-depth 0 is skipped, and so is one whose chosen `{` is immediately preceded by `struct` or `interface` (a struct or interface type in the signature, rare; skipping is deterministic).
  - **Rust:** a `fn` token immediately followed by an `ident`, at any `{`-depth (so methods in `impl` blocks count). Its body opens at the first later `{` with `(`-depth and `[`-depth equal to those at `fn`; if a `;` with those depths comes first, it is a declaration and skipped. The unit starts at the `fn` token extended backwards over the longest run of immediately preceding tokens from {`pub`, `(`, `)`, `crate`, `super`, `self`, `in`, `async`, `const`, `unsafe`, `extern`, `default`, a `string` token}; it ends at the matching `}`. Nested function units inside a unit are not separate candidates.
  - The unit's bytes are from the first byte of its first token to the last byte of its last token.
- **Statement end.** A `;` token (Go: explicit or inserted; Rust: explicit) or a `}` token, whose `{`-depth after it is ≥ 1 (that is, inside some block). **Go:** a `}` immediately followed by an inserted `;` is not itself a statement end; the inserted `;` is, so the pair counts once.
- **Partial unit.** Inside a function unit's body, a token run [*i*, *j*] such that: token *i* is the first token after a `{` or after a statement end; token *j* is a statement end; `{`, `(` and `[` are each balanced over [*i*, *j*]; and every token in [*i*, *j*] has `{`-depth at least that of token *i*. The candidate list for a (file, bucket) is **every** such run whose token count is in the bucket, sorted by (path bytes, start offset, end offset). **Go:** token *i* is never an inserted `;` (the run starts at the next real token), so every run starts at a real token's first byte. For an inserted Go `;` as token *j*, the end offset is the end of the preceding token. Together with the statement-end rule, a run ending at `}` and the same run ending at its inserted `;` cannot both occur, so no two candidates are byte-identical.
- **File unit.** A whole eligible file.
- **Top-level boundary** (host insertion for function and file units). The byte after the first `\n` at or after the end of a token that ends a top-level item: Go, a `;` at `{`-depth 0 **and `(`-depth 0** (explicit or inserted; ruling A10, so a `;` inside `import ( … )` or `var ( … )` is not a boundary); Rust, a `;` or `}` after which the `{`-depth is 0. End of file counts as a boundary. The `\n` is searched in the raw bytes, so a boundary can fall inside a block comment or a multi-line raw string; that is accepted as written (A12). A statement end with no later `\n` gives no statement boundary.
- **Statement boundary** (host insertion for partial units). The byte after the first `\n` at or after the end of a statement end inside a function unit.

**Size bucket.** The unit's exact-channel token count on the source side (extraction §2):

| Bucket | B0 | B1 | B2 | B3 | B4 | B5 | B6 | B7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tokens | 4–7 | 8–15 | 16–31 | 32–63 | 64–127 | 128–255 | 256–1,023 | ≥ 1,024 |

Buckets are fixed independently of `k` and `window`, so B0 shows the floor below the shipped locality threshold `k + w − 1 = 8`.

**Targets per language:** file units 30 (bucketed after selection); function units 30 per bucket B2–B6; partial units 30 per bucket B0–B5. At most 3 units per source repository per (unit kind, bucket). A cell that cannot be filled is reported with its actual count; nothing is relaxed to fill it.

### 6.2 Deterministic choice

Every choice uses `u(id, j) = uint64be(SHA-256("tw-m3-gen-v1|" || namespace || "|" || id || "|" || decimal j)[0:8])` and picks item `u mod n` from a list sorted bytewise.

**Exact id strings (ruling A7).** `<Language>` is `Go` or `Rust`; repositories are `owner/repo` as in the manifest; artifact ids are catalogue ids `f<index>` over the bytewise-sorted eligible paths, and a file-unit case's new file is `f<N>` with N the number of original artifacts (A31).
- cell: `<Language>|<unitKind>|<bucket>` with `unitKind` in `file`, `function`, `partial`; the file cell is `<Language>|file|file` (one selection cell, bucket assigned after selection, A15);
- slot id: `<cell>|<s>` (decimal s);
- case id: `<lang>-<namespace>-<kind>-<bucket>-s<slot>-<transformation>`, lowercase;
- namespace `tuning`: sources and hosts are fold-E repositories, in split-hash order; namespace `held-out`: held-out repositories;
- pilot sample: namespace `tuning`, id `pilot|<Language>`;
- seed-sharing check pair id: `<Language>|<ref repo>|<cand repo>|<ref id>|<cand id>` for negatives, `<Language>|positive|<source repo>|<ref id>|<candidate sha256>` for positives;
- search id: `<Language>|<reference repo>|<candidate repo>` (reference first in split-hash order);
- caching check id: the case id.

**Cells continue past empty slots (ruling O7).** If at slot *s* every source repository is skipped (no room, no candidates, or every candidate of the chosen file already used), the cell moves on to slot *s* + 1; slot numbers in case ids are therefore not necessarily consecutive. A cell ends when it reaches its target or when no source repository with room has an unused candidate left.

**No repeated unit in a cell (ruling A27).** The unit candidates for slot *s* exclude units already chosen in the same cell (same source file and the same byte range); if none remains in the chosen file, that source repository is skipped for the slot as when it has no candidates. The namespace is `tuning` or `held-out`. For cell (language, unit kind, bucket), slot *s* = 0, 1, …: the source repository is the (*s* mod R)-th of the split's R source repositories in split-hash order, skipping any that already have 3 units in the cell or no candidates; the source file is chosen by `u(cell|s, 0)` among its files with candidates; the unit by `u(cell|s, 1)` among that file's candidates; the host repository by `u(cell|s, 2)` among same-split, same-language repositories of other groups; the host file by `u(cell|s, 3)` among its eligible files that have at least one boundary of the needed kind; the boundary by `u(cell|s, 4)`. `split-mix` uses `u(cell|s, 5)` for its second boundary among the remaining ones, and the two halves go in boundary order. Each unit is sampled once and **every applicable transformation is applied to the same unit** (a paired design, §11).

### 6.3 Transformations

| ID | Applies to | Definition |
| --- | --- | --- |
| `verbatim` | file, function, partial | Unit bytes unchanged. Placement as in §6.4 |
| `ws` | all | In every gap between two consecutive tokens that holds only whitespace: a gap containing a line break gets one extra `\n` after its last line break; any other non-empty gap is doubled. Never adds a line break to a gap without one, so Go semicolon insertion is unchanged; the token stream is identical |
| `comments-strip` | all | Every comment is replaced by `""` (line comments, whose span excludes the line break) or by `" "`, or by `"\n"` when a Go general comment contains a line break. Token stream identical (Rust doc comments are trivia in the profile) |
| `comments-add` | all | After tokens 9, 19, 29, … (0-based) insert ` /* tw */ ` at the start of the following gap. Token stream identical |
| `fmt` | **Rust only** | After placement, run `rustfmt --edition 2024 --config max_width=50,tab_spaces=2` (pinned version) on the whole host file, the unit wrapped in `/*tw-begin*/` and `/*tw-end*/` comments. Edition 2024 matches the `rust2024-tokens` profile; the crate's declared edition is ignored. The ground truth is the byte range between the markers after formatting; then both markers are deleted and spans adjusted. A non-zero exit or a lost, duplicated or reordered marker is `generation-failed`. If the bytes between the markers equal the pre-format unit bytes, the case is kept and flagged `identity`; identity cases are reported as their own count and recall is reported with and without them |
| `rename` | all | **Bindings** are collected from the unit's tokens. Go: every `ident` in a maximal run `ident (, ident)*` immediately followed by `:=`; every `ident` immediately after `var` or `const`; and, for function units only, the name of the unit itself: the `ident` immediately after the unit's **first** token `func`, or, if that `func` is followed by a receiver `( … )`, the `ident` immediately after the receiver's closing `)`. Later `func` tokens in the unit (function literals such as `g := func(x int) int {…}`) contribute no binding, so a type name is never a binding. Rust: every `ident` immediately after `let`, `let mut`, `fn`, `for`, `mut` or `ref`. The texts `_`, `self` and `Self` are never bindings. Bindings are numbered in order of their **first binding site** (the token index of the first position where the collection rule fires for that text; ruling A8, which replaces "first occurrence": the two differ when a name is used before it is bound) and renamed `tw_v1`, `tw_v2`, …. **Occurrences:** every `ident` token in the unit whose exact text equals a binding is renamed, except one immediately preceded by `.`, or (Rust) by `::`, that is by two consecutive `:` tokens, since the profile lexes punctuation as single characters (A9). Tokens inside macro invocations are renamed like any others; string and character literals (including Rust format strings) and comments are never changed. A unit with no binding, or containing an `ident` that starts with `tw_v`, is `generation-failed` |
| `reorder` | file | **Segments:** the file is cut after each top-level boundary (§6.1); a segment is the bytes from one cut to the next, so leading comments and attributes travel with the item after them. Segments whose first token is `package` or `import` (Go), or `use`, `mod`, `extern` or `#` followed by `!` (Rust), stay in place at the start; the other segments are written in reverse order. Ground truth is one segment per moved segment. Fewer than 2 moved segments is not applicable |
| `split-mix` | function, partial | Let *n* be the unit's token count and the **cut candidates** its statement ends with at least one token before and after them. Cut after the candidate *b* minimizing \|*b* − ⌊*n*/2⌋\| (token index), **ties to the smaller *b***. The two halves are inserted at two different boundaries of the host file (§6.2). Two ground-truth segments. No candidate is not applicable |
| `compound` | function, partial | Rust: `comments-strip`, then `rename`, then `fmt`. Go: `comments-strip`, then `rename`, then `ws` |

**Go formatting, dropped as a cell.** Go has one canonical format and most Go repositories are gofmt-clean, so a `gofmt` run over an inserted gofmt-clean unit almost never changes it, and `gofmt -s` changes only the few units it can simplify. A cell made of those would be small and self-selected. Layout changes that leave tokens intact are covered by `ws` and `comments-*`; the Go formatter is not used. The report states that Go has no formatter cell.

**Rust `rename` is coarse, stated in the report.** The rule takes the token after `let`, `mut`, `for` or `ref`. In `let Some(n) = v` it collects `Some` and misses `n`; in `&mut Vec<u8>` it collects `Vec`. Types and enum variants can therefore be renamed and inner pattern bindings left alone. The rule stays as written, because it is mechanical; the report says so beside every Rust `rename` and `compound` figure.

**Not compilable.** `comments-strip` removes Go `//go:build`, `//go:embed` and cgo preambles; `reorder` can break Rust `macro_rules!` textual order; `split-mix` leaves unbalanced braces; `rename` can break field shorthand, struct literal keys, format-string captures and shadowing. The lexers accept all of these. Recall describes lexical robustness only.

### 6.4 Placement

- **file units:** written as a **new file** in the host repository at `tw_eval/<case id>.go` or `.rs`.
- **function units:** inserted at a top-level boundary of an existing host file.
- **partial units:** inserted at a statement boundary of an existing host file.

Insertion adds exactly one `\n` before and after the inserted bytes. Every host-side byte outside the insertion is unchanged, except under Rust `fmt` and `compound`, where the formatter rewrites the whole host file.

### 6.5 Ground truth record

One JSON line per case in `cases-<language>-<namespace>.jsonl`, committed (offsets and digests only, no source bytes), serialized as canonical JSON (sorted keys, no insignificant whitespace) with a final LF:

`caseId`, `language`, `namespace`, `unitKind`, `bucket`, `tokenCount`, `transformation`, `sourceRepo`, `sourceRevision`, `sourcePath`, `sourceSha256`, `hostRepo`, `hostRevision`, `hostPath` (or `tw_eval/…`), `hostSha256Before`, `candidateSha256`, `segments` (list of `{source: [start, end), candidate: [start, end)}` in UTF-8 bytes, half-open), `slot`, `generator` (commit), `formatter` (version string or null), `identity` (Rust `fmt`/`compound` only), `status` (`generated` or `generation-failed` with reason).

Failed generations stay in the file, so the per-cell denominators "attempted" and "generated" are both reported.

## 7. Negative set

Every unordered pair {*R*, *C*} of held-out repositories of the same language from different groups is one negative search, with no planted content. With 12 held-out repositories per language that is 66 searches per language, **132 in all**. Searches carry labels that are reported separately but all count toward M3.6:

| Label | Definition (mechanical) |
| --- | --- |
| `unrelated` | Every negative search |
| `same-domain` | *R* and *C* share at least one GitHub topic in the snapshot, other than `go`, `golang`, `rust`, `rustlang` and `hacktoberfest` |
| `same-stack` | *R* and *C* declare at least one common direct dependency at their pinned revisions (§3.6 step 3) |

Common boilerplate enters in two ways: naturally, inside every negative search (licence headers, `if err != nil { return err }`, CLI scaffolds), and as the `same-stack` label, where shared frameworks produce shared idioms. The only boilerplate *catalogue* is the §5.2 suppression catalogue, built from tuning fold S only. Positive-case host repositories are also searched unmodified as negatives; a positive comparison's matches outside the ground truth are reported as `spurious` and do not enter M3.6.

## 8. Freeze and git ancestry (M3.3)

The **freeze commit** in the implementation repository adds `eval/freeze.json` containing:
- this protocol's self-excluding digest (filled in this file at step 6, before the first tuning run) and the spec-repository commit holding it, which must be an ancestor of the spec commit current when tuning started;
- the manifest digest and the M3.2 split digest;
- per language: the extraction configuration bytes (Base64) and SHA-256; the comparison configuration bytes and SHA-256, including `minRegionDistinctHashes`, `mergeGap`, both caps and `suppressionCatalogueSha256`; the suppression catalogue SHA-256 and *T*;
- the M3.0 budget as a rational, **`1/20`**, and the spec-repository commit that recorded it (§14.1); any other value is refused by the freeze script;
- the implementation commit used for lexing, extraction and comparison, which must equal the acquisition lexing commit of `eval/acquisition.json` (§3.4); the generator commit; the `rustfmt` version string;
- the pilot record digest, the grid-rule branch taken and any grid reduction (§5.5); the run-time estimates;
- the digest of `eval/tuning-table.json` (§5.4), committed in the same commit;
- the alarm-audit procedure of §12a, by protocol section and digest, and the name of the assigned labeller;
- the M3.5 tolerance (§13).

**When.** After the §5.4 selection, before step 8. Nothing in `freeze.json` changes afterwards; a change is a new protocol version and voids held-out results produced under the old one.

**Ancestry check** (from a clean clone of the implementation repository):

```
FIRST=$(git log --reverse --format=%H -- eval/results/heldout | head -n 1)
FREEZE=$(git log --reverse --format=%H -- eval/freeze.json | head -n 1)
SPLIT=$(git log --reverse --format=%H -- eval/splits.tsv | head -n 1)
git merge-base --is-ancestor "$FREEZE" "$FIRST" && git merge-base --is-ancestor "$SPLIT" "$FIRST"
git diff --quiet "$FREEZE" "$FIRST" -- eval/freeze.json eval/splits.tsv eval/manifest.json eval/acquisition.json
```

and a script check that the lexing commit in `freeze.json` equals the one in `eval/acquisition.json` (exit 0).

M3.3 is met when every command exits 0. Timestamps are never consulted.

**Generator identity (ruling A17).** The generator commit in `freeze.json` is the harness HEAD at the freeze; held-out generation refuses if any harness file changed since then. **Binaries (A2, B1).** Both implementations run every extraction, catalogue and comparison and must agree byte for byte (a disagreement is exit 1). Both binaries are clean stamped builds of one commit, read from each binary's own stamped output: its version command where it has one, otherwise the provenance of a report document it writes for a tiny synthetic catalogue, which only stamped builds produce; an unstamped binary is refused (ruling O1). A `traceweave-go --version` in the Rust format is an **implementation change to `main`** (owner: the implementation repository's Go lane), after which both are read the same way; that commit is the acquisition lexing commit and the frozen lexing commit. **Fold-S list (B8).** `freeze.json` records the fold-S and fold-E repository lists; `tune` and the freeze check the suppression catalogues' sources against them. **Tuning table (A39).** `freeze` runs with `tuning-table.json` uncommitted so that both files enter one commit; any other uncommitted file is refused. **Non-empty check (A16).** Each ancestry variable must be non-empty.

**What ancestry does not prove.** It shows commit order only. It cannot show that nobody ran held-out data before the freeze. The controls for that are procedural: the generator refuses the `held-out` namespace, and the held-out runner refuses to start, unless HEAD descends from `FREEZE`, the work tree is clean and the protocol digest in `freeze.json` matches. The first held-out result commit carries the runner's **identity record** (`eval/results/heldout/identity.json`: HEAD, clean-tree status, `freeze.json` digest, protocol digest, implementation and generator commits, start and end times, host OS and architecture). The report states this limit.

## 9. Running the held-out evaluation

Pair outcomes depend only on the two artifacts, the configuration and the suppression catalogue (contract §5.2, invariance). A runner may therefore compute each (reference file, candidate file) pair once and assemble comparisons from cached pairs, provided the assembled body is byte-identical to a direct comparison; comparisons with `u(search id, 0) mod 50 = 0` are recomputed directly and must match byte for byte. **This caching check is never batched** (draft-8): it compares the whole reference catalogue against the whole candidate catalogue in one `compare`, so it checks pair caching and, for the comparisons it samples, batching. If the watchdog stops it, the run aborts (no verdict) rather than batching it. It does **not** check batching in general: it samples positive cases only (review N4), so a batch boundary that appends or drops a pair in a negative search would go unchecked. That is covered by the next rule.

**Pair completeness wherever a comparison is batched (draft-9).** Whenever a comparison (a negative search, a positive case, a tuning or pilot search, or a direct check) is split into batches of reference files, or assembled from cached pairs, the **expected pair set** is computed independently of the batches, from the two catalogues' artifact lists: every (reference artifact id, candidate artifact id) pair, in the contract §5.3 order. The assembled result must contain **every expected pair id exactly once** and no other: no pair missing, duplicated or foreign. The runner records, per comparison, the expected and assembled pair counts and a SHA-256 over the sorted assembled pair ids; any difference is an error, exit 2, **no verdict**. `counts.json` carries these records for held-out negative searches and positive cases, and the M3.6 script recomputes the expected sets from the committed catalogue artifact lists (the per-repository eligible-file records) and compares them with the recorded counts and digests; a mismatch is exit 2.

**Symmetry check (F4).** For negative searches with `u(search id, 2) mod 10 = 0`, the runner also runs the swapped comparison (*C* as reference). For every file pair and mode, the outcome class and code, `seedCount`, `regionCounts` and `truncatedRegions` must be equal with roles swapped. Any difference makes M3.6 an error (exit 2) and requires a protocol revision; it does not silently switch the unit.

**Check counts are verified (review B8, S-b).** The run records the ids it checked for symmetry, caching and seed sharing; the counts script recomputes, from the search and case ids, which ids satisfy each modulus, and any difference (a missing or extra check) is exit 1. The moduli are fixed here and not read from configuration. **Clean tree (A18).** The held-out runner and counts script accept uncommitted files under `eval/results/heldout/` only, so that the first held-out result commit holds them together.

Resource measurement (ruling A3): every extraction batch and every comparison is a child process whose wall time and maximum resident set size are read from `wait4(2)` resource usage (the counters `/usr/bin/time` prints), plus the watchdog samples of §5.5, with operating system, architecture, CPU model, core count and memory recorded once per run.

## 10. Metrics (M3.4): every figure with its denominator

| Figure | Numerator | Denominator | Breakdown |
| --- | --- | --- | --- |
| Recall | detected cases | generated cases | language × transformation × bucket; per mode and union; plus attempted, generated and distinct source repositories per cell; Rust `fmt` with and without identity cases |
| Covered fraction | — (distribution) | detected cases | per cell: minimum, quartiles, maximum; no pass line |
| Miss reasons | cases per miss class (§1) | generated cases | as recall |
| False alarms per repository search | negative searches with an alarm (§1) | negative searches (unordered) | language; label; per alarm reason; per mode |
| Repositories in alarms | distinct repositories appearing in alarmed negative searches | held-out repositories | language |
| Pair-level false matches | negative file pairs with any alarm reason | compared negative file pairs | language; reason; mode |
| Abstentions | pairs or pair-modes per abstention code | pairs or compared pair-modes | language; negative versus positive comparisons |
| Excluded files | files per exclusion reason (path rules, `generated`, `lex-error`, `under-16-tokens`, `oversize`) | paths with the language's extension | language; repository; split; checked against the §3.4 bound |
| Extraction outcomes | files per status/error code | eligible files | language; repository |
| Candidate volume | `match` pairs and reportable regions | comparisons (negative; positive) | mean, median, 95th percentile, maximum |
| Spurious matches in positive comparisons | positive comparisons with a `match` outside ground truth | positive comparisons | language |
| Symmetry and caching checks | checked comparisons that differ | checked comparisons | must be 0 |
| Runtime | wall seconds | extraction batches; comparisons | median, 95th percentile, maximum, total |
| Peak memory | maximum RSS | as runtime | median, maximum |

Counts are written to `eval/results/heldout/counts.json` (canonical JSON: sorted keys, no insignificant whitespace, integers only), with the per-search records `searches.jsonl` (§12) and, per compared file pair, a record of its outcome codes per mode. **Per-pair records (ruling O3)** may be committed as `eval/results/heldout/pairs.jsonl.gz`: canonical JSON lines, gzip with header mtime 0 and no file name; reproduction compares the **decompressed** bytes, because compressed bytes depend on the compressor's version. **Miss reasons (A13):** for the union of modes, a missed case takes the first reason in §1 order over both modes; `truncated` needs outcome `match`, no qualifying listed region and `truncatedRegions > 0`, otherwise `mislocalized`. **Spurious (A14):** any other pair with `match` in either mode, or a reportable region of the ground-truth pair that overlaps no ground-truth candidate segment. **Exclusion-bound denominator (A30):** files passing the path rules, the size limit and the generated rule. Runtime and memory go to a separate `resources.json`, because they are not expected to reproduce exactly.

## 11. Intervals, dependence and what the sample can bound

**Dependence between cases.**
- Negative searches share repositories: each held-out repository appears in 11 of its language's 66 searches. Alarms are driven by repository properties (boilerplate density, generated-looking code), so one noisy repository can alarm in up to 11 searches; the effective sample is nearer 24 repositories than 132 searches. Under the recommended budget one repository can flip the verdict. That is a property of this corpus, and the report states it.
- Positive cases share source repositories (up to 3 units per repository per cell), host repositories, and, by design, units: all transformations of one unit are paired. Overlapping k-grams and windows are correlated observations ([lane 07](../lanes/07-evidence-review.md); [evaluation](../../docs/evaluation.md)).

**Reported intervals.**
- *Recall per cell:* Wilson 95% interval on detected/generated, the number of distinct source repositories, and the **leave-one-repository-out range** (minimum and maximum recall after dropping each source repository's cases in turn). Cells under 10 cases are reported and marked "fewer than 10 cases".
- *False alarms per search:* (a) the point estimate *a* = alarms / searches; (b) the exact Clopper–Pearson 95% interval treating searches as independent, labelled **"assumes independence, which does not hold"**; (c) the **leave-one-repository-out range** of *a* (drop each held-out repository and all its searches in turn); (d) the **disjoint-search bound**: per language, pair held-out repositories in split-hash order (1st with 2nd, 3rd with 4th, …), so each repository is used once, and give the one-sided Clopper–Pearson 95% upper bound on those 12 searches only (0.221 at 0 alarms, 0.339 at 1).
- Transformation comparisons use the paired design: discordant-pair counts (detected under A and not B, and the reverse) on shared units, not differences of independent proportions.

**What the sample can and cannot bound** (one-sided 95% upper bound with zero alarms, 1 − 0.05^(1/N)):

| Independent searches N | 12 | 24 | 66 | 132 | 300 | 1,000 | 3,000 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Upper bound | 0.221 | 0.117 | 0.044 | 0.022 | 0.0099 | 0.0030 | 0.0010 |

So the proposed 48-repository corpus can **measure** a false-alarm count over 132 searches and compare it with the budget, which is what M3.6 asks. It **cannot demonstrate** a rate below about 0.2 with independent-search confidence (the disjoint bound). Even treating all 132 searches as independent, which they are not: 0 alarms gives a one-sided 95% upper bound of **0.0224** (the rule of three gives 0.0227); 6 alarms, the largest passing count (observed 0.0455), gives **0.0877** one-sided and 0.0963 two-sided (97.5%). A "met" verdict at 6 alarms is therefore compatible with a true rate near 9%. Demonstrating 0.01 at 95% needs about 300 independent searches, roughly 600 repositories under the disjoint design. Recall cells of 30 cases have Wilson half-widths up to about ±0.17. The report and every rendering of M3.6 state these limits and print the operating characteristics of §14.1 beside the verdict.

## 12. What M3.6 computes

Inputs: the per-search records and `counts.json` as committed in the **first held-out result commit** (read with `git show`, not from the working tree), and `freeze.json`, whose budget must be `p/q` = **`1/20`** (§14.1); any other value is an error. The script refuses a dirty work tree (exit 2).

**Derived, not copied (ruling B7).** `eval/results/heldout/searches.jsonl` holds one canonical line per negative search: search id, language, labels, and per alarmed pair and mode the alarm reason. The script recomputes `A` and `N` from those lines, recomputes the exclusion bound from `eligibility.json`, and requires both to equal the summary in `counts.json` and the per-language figures there; any difference is exit 2. Editing a summary number therefore cannot change the verdict. **Body cross-check (ruling O4):** where the private report bodies are present, the script also re-classifies each negative search from its body; a disagreement with `searches.jsonl` is exit 2. Absent bodies are not an error; the verdict then rests on `searches.jsonl`, as above.

- `A` = unordered negative searches with an alarm (§1); `N` = unordered negative searches.
- **met** when `A × 20 ≤ N` (exact integer arithmetic; with N = 132 that is A ≤ 6); **negative-result** otherwise.
- `N = 0`, a pair-completeness difference (§9), a missing or mismatched freeze, a failed M3.3 check (including the lexing-commit equality), exclusions above the §3.4 bound, a non-zero symmetry or caching difference, or an aborted run is an error, not a verdict.

The script exits 0 for met, 3 for negative-result, 2 for an error. No recall floor is applied; recall is reported without a pass line. The verdict uses the point estimate, as M3.6 states; the intervals of §11, the operating characteristics of §14.1, the excluded-file counts per repository and reason, and the frozen suppression catalogue's counts (frequent hashes, kept snippets, fallback files, collateral hashes; §5.2) are printed beside it and do not change it.

## 12a. Alarm audit (fixed before the freeze; never changes the verdict)

Every held-out negative-search alarm is labelled **after** the M3.6 script has printed its verdict, so the labels cannot influence it.
- **Who.** A labeller named in `freeze.json`, assigned by the coordinator, who did not write the harness. A second person, also named there, relabels every alarm if there are at most 6, otherwise a sample of `u(search id, 3) mod 4 = 0`; agreement is reported as a count.
- **Unit.** One label per (search, file pair, mode) with an alarm reason, plus one label per search: the label of its first labelled pair in (reference id, candidate id, mode) order.
- **Labels**, exactly one each, from the report's spans and the two source files only:
  - `real-shared-code`: the matched regions are the same code in both files beyond the token run itself (shared identifiers, comments or string literals in or around the span, a copied or vendored file, or a stated common origin);
  - `boilerplate`: licence or file headers, generated-looking code, framework or language-required idioms (for example `if err != nil { return err }`), or code the labeller finds in the language's standard library or a common dependency;
  - `accidental`: none of the above; the shared tokens are a coincidence of common syntax;
  - `abstention`: the alarm reason is `ambiguous`, `seed-limit-exceeded`, `not-compared` or a rejected body; a sub-label from the three above describes the underlying regions where there are any.
- **Record.** `eval/results/heldout/alarm-audit.jsonl`: search id, pair ids, mode, alarm reason, label, one-line reason, labeller. Committed after the verdict.
- **Effect.** Labels **never** change A, N, the M3.6 exit status or any §10 figure. They are reported as counts beside the verdict and feed the follow-up work of §18.

## 13. Reproduction (M3.5)

A second person, on a machine of their choice:

1. Clone the implementation repository at the first held-out result commit; run the §8 ancestry commands (exit 0).
2. Acquire the corpus from `eval/manifest.json` into their own corpus root (§3.6), including the licence recheck (exit 0).
3. Rebuild the split file; its SHA-256 equals the M3.2 digest.
4. Rebuild the tuning-fold suppression catalogues; their SHA-256 equal `freeze.json`. (The selection grid need not be rerun.)
5. Regenerate held-out cases with their own generator implementation if they wish, from §6 alone; `cases-*-held-out.jsonl` byte-identical (`cmp`, exit 0).
6. Run the held-out evaluation; `cmp` their `counts.json` with the committed one (exit 0), and the decompressed `pairs.jsonl.gz` with the committed one decompressed (exit 0).
7. Compare resources with the committed `resources.json` using the tolerance script.

**Tolerance (proposed).** Counts: identical, no tolerance. Resources, only when the operating system and architecture match the original run: total wall time ratio in [0.5, 2.0] and maximum peak RSS ratio in [0.8, 1.25]. On a different OS or architecture, resources are recorded and not compared. The tolerance is frozen in `freeze.json`.

M3.5 is met when steps 1–6 exit 0 and step 7 exits 0 or reports "not comparable" for a different platform.

## 14. Decisions that need the owner

The owner decides each of these. All were decided on 2026-11-23, delegated to the coordinator; each subsection keeps its options and recommendations as history and ends with the decision.

### 14.1 M3.0: the false-alarm budget

**Unit:** false alarms per repository search, where a search is one **unordered** pair of repositories (§1) and an alarm is any `match`, any abstention or any other non-result outcome in either mode (§1). Expected alarms are budget × searches; an operator checking one reference repository against *n* candidate repositories makes *n* searches:

| Option | Budget | 10 searches (targeted check) | 100 (one project's dependency tree) | 1,000 (ecosystem sweep) | 10,000 (registry sweep) |
| --- | --- | --- | --- | --- | --- |
| A | 1 in 20 (`1/20`) | 0.5 | 5 | 50 | 500 |
| B | 1 in 100 (`1/100`) | 0.1 | 1 | 10 | 100 |
| C | 1 in 1,000 (`1/1000`) | 0.01 | 0.1 | 1 | 10 |

**What each means on the proposed 132 held-out searches** (exact binomial, treating searches as independent, which overstates the information, §11):

| Option | M3.6 met iff alarms ≤ | One-sided 95% upper bound at that count | P(met) if true rate = ½ budget | = budget | = 2 × budget |
| --- | --- | --- | --- | --- | --- |
| A `1/20` | 6 | 0.0877 | 0.951 | 0.508 | 0.018 |
| B `1/100` | 1 | 0.035 | 0.858 | 0.619 | 0.257 |
| C `1/1000` | 0 | 0.022 | 0.936 | 0.876 | 0.768 |

Each alarm costs a person a review of localized evidence (UC-1, UC-2).
- **A** separates half from double the budget sharply (0.95 against 0.02), but 1 alarm in 20 searches is 50 reviews per 1,000-repository sweep.
- **B** is a usable operator target (about one review per 100 candidates) and is decided by a count (at most 1 alarmed pair of 132), but it separates ½× from 2× only moderately (0.86 against 0.26), and a single noisy repository can decide it.
- **C** is what a registry sweep would want, but on this corpus the verdict means little: it is met with probability 0.77 even when the true rate is twice the budget, and the corpus cannot bound a rate near 1/1000.

**Decision (2026-11-23).** The owner delegated the choice to the coordinator, who chose **option A: `1/20` false alarms per unordered repository search on the current 48-repository corpus**, so M3.6 is met when at most 6 of the 132 held-out searches alarm. `1/100` is to be tested on a larger corpus (about 100 repositories per language, §14.4) **only if this passes**; that would be a new protocol version with its own M3.0 record. The text below is kept as the history of the choice.

**Two recommendations (history).**
- **Author: B**, with the operating characteristics printed beside the verdict. It is the operator target that matters (about one review per 100 candidate repositories) and is still decided by a count. Its weakness at this size is stated: it separates ½× from 2× the budget only moderately (0.86 against 0.26), and one noisy repository can decide it.
- **Reviewer (confirmation pass): A at this corpus size, or B only with about 100 repositories per language.** If M3.6 is meant as evidence, the verdict should be unlikely to come out "met" when the true rate is twice the budget; A does that here (0.018), B does not (0.257).

**The same options on a 100-per-language corpus** (about 50 held-out repositories and 1,225 unordered searches per language, 2,450 in all; same assumptions):

| Option | M3.6 met iff alarms ≤ | One-sided 95% upper bound at that count | P(met) if true rate = ½ budget | = budget | = 2 × budget |
| --- | --- | --- | --- | --- | --- |
| A `1/20` | 122 | 0.058 | 1.000 | 0.506 | 0.000 |
| B `1/100` | 24 | 0.014 | 0.999 | 0.513 | 0.000 |
| C `1/1000` | 2 | 0.0026 | 0.874 | 0.557 | 0.133 |

At that size B separates ½× from 2× as sharply as A does at 48 repositories. Its cost is in §14.4. Whatever is chosen is recorded as an exact fraction before tuning starts (§2 step 1). On the tuning fold every option means zero alarms at 24 per language (§5.4), so the choice does not change tuning there.

### 14.2 Acquisition approval (M3.1)

- **What:** the 48 repositories in [manifest-proposal.json](evaluation-corpus/manifest-proposal.json), 24 Go and 24 Rust, by shallow fetch of the pinned revisions, **plus the mechanical replacements of §4.3 from the continuing walk, at most 8 per language**. No dependencies, submodules, releases or build outputs. Likely replacements (from public dependency information, confirmed only at acquisition): `seanmonstar/reqwest` and `tokio-rs/axum` (both depend on `hyper`), and `grpc/grpc-go` (likely required by `micro/go-micro`).
- **Size:** GitHub reports 621,386 KiB (about 607 MiB) summed over the 48 repositories, *including full history*; this is an upper bound, and the review estimates 100–250 MB for depth-1 fetches. Eligible source is 58,768,417 bytes (about 56 MiB) in 6,254 paths (3,314 Go and 2,940 Rust), counted from the pinned tree listings before the content rules. Derived private data is 2–5.5 GB at the end of the run (§5.5, Disk); the corpus root's volume needs that plus the free-space margin, about 26 GB at the default 20 GB margin and about 16 GB at the 10 GB minimum.
- **Licences**, verified from the root licence files at the pinned revisions: MIT only (30 repositories), Apache-2.0 only (9), both MIT and Apache-2.0 files, recorded `Apache-2.0 AND MIT` (7, all Rust), BSD-3-Clause (1) and BSD-2-Clause (1). All permit redistribution with notice retention; the project redistributes none. Acquisition rechecks every licence file's SHA-256 and classification and stops on any difference (§3.6).
- **Recommendation (history):** approve as proposed, including the replacement rule, after a non-author has rerun `verify_manifest.py`.
- **Decision (2026-11-23):** approved, delegated to the coordinator: the 48 repositories and the mechanical replacements of §4.3 (at most 8 per language), with the licence recheck of §3.6 failing closed.

### 14.3 Where the corpus is stored

Outside every repository and every version-controlled working tree (contract B1 markers), in an absolute directory named by `TRACEWEAVE_EVAL_DIR`, with `corpus/`, `derived/` (catalogues, report bodies: private), `cases/` (case bytes) and `logs/`. Options: (a) a directory under the owner's home, such as `~/traceweave-eval`; (b) an external or encrypted volume; (c) a separate private storage service (paid services need the owner anyway). **Recommendation (history): (a)**, local disk, never synchronized to a public location, with the runner refusing a location inside a working tree as the contract's B1 rule does for private output. **Decision (2026-11-23):** (a), `~/traceweave-eval`, named by `TRACEWEAVE_EVAL_DIR` (an absolute path; a relative or empty value is a usage error, as contract B4–B5).

### 14.4 Corpus scale and licence allowlist

- **Scale.** 24 per language (proposed) gives 132 unordered negative searches and the figures in §14.1. 100 per language gives about 50 held-out repositories and 1,225 unordered searches per language, and a 50-search disjoint bound in all (0.058 at zero alarms). Its cost, scaled from the proposed manifest under the §5.5 model (averages per repository; nothing measured):

  | | 24 per language (proposed) | 100 per language |
  | --- | --- | --- |
  | GitHub size including history (upper bound on download) | 607 MiB | about 2.5 GiB |
  | Eligible source | 56 MiB | about 235 MiB |
  | Held-out negative file pairs | 1.65 M | about 31 M (×18.6, from 66 to 1,225 searches per language) |
  | Fold-E negative file pairs per (`k`, `window`) | 0.43 M | about 8.6 M (25 instead of 6 groups per language) |
  | Pair comparisons in all, 12 (`k`, `window`) settings (positives about the same) | about 18.7 M | about 290 M |
  | Runtime at the review's assumed 1 ms per pair | about 5 h | about 80 h (held-out about 9 h, fold-S count and tuning about 70 h) |
  | Derived private data | 4–5 GB | about 17–20 GB |

  At 100 per language the tuning estimate exceeds the 24-hour budget of §5.5, so the grid would shrink by its fixed rule. The pool would also need to grow: the first 100 search results per language yielded 24 acceptances from 29 (Go) and 39 (Rust) visits, so 100 acceptances need about the first 300 results per language (three search pages), a change to §3.1 that needs a new snapshot. **Author recommendation (history):** start at 24 and choose A, or approve 100 per language with B; do not combine B with 24 if M3.6 is meant as evidence. **Decision (2026-11-23):** 24 per language with A; 100 per language with B only if A passes.
- **Allowlist.** The permissive list of §3.2 only. Adding MPL-2.0 or CC0-1.0 would admit a few more pool repositories (for example a CC0 Rust command runner); copyleft is excluded because the project does not want to argue use conditions for corpus code. **Recommendation (history):** keep as proposed. **Decision (2026-11-23):** kept, as part of the acquisition approval.

### 14.5 Already decided elsewhere, restated

No push or publication; the manifest and results live in the implementation repository (`I` owner column) and the M3.0 record and M3.6 verdict in this one (`S`). The formatter and toolchain versions are pinned, not installed globally.

## 15. Risks and limits

- **The pool is a popularity sample.** Starred, maintained, permissively licensed repositories created before 2023-11-22. It says nothing about private code, small projects or other languages.
- **Same-domain and same-stack counts are small.** They are labels on the 132 searches, not a designed sample: the provisional split labels 10 searches `same-domain` (by shared topic), too few to say anything separately.
- **Real reuse among negatives.** Popular repositories copy snippets from each other and from documentation. Those alarms count as false alarms (§1); the audit labels them without removing them. The budget therefore measures alarms, not proven non-reuse.
- **Strict alarm rule.** Counting abstentions and non-results as alarms (§1) makes M3.6 harder to meet than counting matches alone; it is the price of not rewarding abstention.
- **Acquisition can change the selection.** Dependency, duplicate, generated-file, lexing and token-count checks need the files, so the provisional split can change at acquisition. Replacements are mechanical and bounded (§4.3); the M3.2 digest is the one after acquisition.
- **Residual leaks.** Edited (not just reformatted) copies across owners and copies of standard-library code are not caught (§4.1, §3.5).
- **Path counts are not content checks.** Some proposed repositories have few, large eligible files (for example `benfred/py-spy`: 39 paths, 4.2 MB), which suggests generated bindings, and `rui314/mold` is listed under Rust by GitHub. The content rules and the eligible-file minimum are applied at acquisition, and a repository that falls below 10 eligible files is replaced.
- **Licence classifier.** Phrase rules can reject a valid licence with unusual wording (for example `XAMPPRocky/tokei`'s Apache file is `licence-unclassified`). They are conservative by design; they are not a legal review.
- **Transformation realism.** `rename` is lexical and covers simple bindings only; Go has no formatter cell; Rust `fmt` uses one non-default style; `compound` is one fixed chain. None is an adversarial evasion budget (that is M2E.6 and later work).
- **Tuning data.** Fifteen fold-E searches per language cannot separate configurations by false alarms (§5.4); ties will usually be broken by recall, then by the fixed order.
- **Cost is estimated, not measured.** The pilot (§5.5) measures it on tuning data before the freeze; the grid can shrink by a fixed rule, and runs abort by a fixed rule.

## 16. Gate mapping

| Gate | Evidence this protocol defines | Pass/fail as |
| --- | --- | --- |
| M3.0 | Decision record of `p/q` = `1/20` (§14.1, 2026-11-23) | record exists (in this file; the roadmap status is the coordinator's to change) |
| M3.1 | Manifest; `verify_manifest.py`, and `--licence-dir` at acquisition | exit 0; self-test rejects every broken manifest |
| M3.2 | Split file and digest; disjointness | `verify_manifest.py` exit 0; digest equality |
| M3.3 | §8 commands | all exit 0 |
| M3.4 | `counts.json`, `resources.json`, identity record, report (§10) | every figure has a denominator (schema check); symmetry and caching differences 0 |
| M3.5 | §13 steps | `cmp` exit 0; tolerance script exit 0 |
| M3.6 | §12 script | exit 0 met, 3 negative-result |

## 17. Review dispositions

| Finding | Disposition |
| --- | --- |
| F1 non-mechanical generation | All units, boundaries, `rename` bindings and occurrences, partial-unit candidate lists and the `split-mix` cut with its tie rule are defined on the profile's token stream (§6.1–§6.3); no parser or name resolution is used. Choices are fixed per slot (§6.2) |
| F2 `fmt` | Go `fmt` dropped as a cell, with the reason (§6.3); Go `compound` ends in `ws`. Rust `fmt` uses edition 2024 (the profile's edition) and keeps identity output as flagged cases, reported with and without them |
| F3 abstention passes M3.6 | Alarm = any `match`, abstention, `not-compared` pair or rejected body (§1). Eligibility (lexes, ≥ 16 tokens) removes the deterministic `not-compared` sources (§3.4) |
| F4 double counting | Unordered pairs, one comparison each (§1); runner symmetry check with error on difference (§9); thresholds and operating characteristics restated for N = 132 (§14.1) |
| F5 grouping | Go module-path and Rust crate/URL matching, later-in-walk rejected, replacement order and limit of 8 per language, approval covers replacements (§4.1, §4.3). Token-digest duplicate rule closes reformatted copies; edited copies stated as residual (§4.1) |
| Lane 11 items 1–3 | Fold-S outcome count with the pre-declared grid rule (§5.5); `k` = 16 and a reduction order keeping both ends of `k` (§5.3, §5.5); tuning table with the freeze and alarm audit fixed before it (§5.4, §8, §12a); follow-ups (§18); bound wording (§11, §14.1) |
| F6 cost | Pair-count model, seed sharing with a byte-identical check, timing pilot on fold S only, 24-hour budget with a fixed grid reduction, abort rules (§5.3, §5.5) |
| F7 lenient hit | Covered fraction reported per cell (§1, §10) |
| F8 ancestry | Limit stated; refusals and the runner identity record in the first result commit (§8) |
| Confirmation (1) Go `rename` scope | Unit head `func` only (§6.3) |
| Confirmation (2) inserted Go `;` | Never a run start; `}` + inserted `;` is one statement end (§6.1) |
| Confirmation (3) eligibility dodge | Lexing-commit equality, excluded counts per repository and reason, 5% / 25% bound (§3.4, §8, §10, §12) |
| Confirmation (a) Rust `rename` | Coarseness stated in the report rules (§6.3) |
| Confirmation (b) Go struct/interface braces | Such units skipped (§6.1) |
| Confirmation (c) budget | Both recommendations and the 100-per-language figures and cost (§14.1, §14.4) |
| M5 licence values | Acquisition recomputes SHA-256 and reruns the classifier, exit 1 and stop on difference (§3.6); `verify_manifest.py --licence-dir` implements it |
| Low: protocol digest | Self-excluding digest line, filled at the freeze (header, §8) |
| Low: replacement facts | Rejected-at-acquisition repositories carry facts in the walk; the checker requires them (§3.1) |
| Low: `mold`, `py-spy` | Kept or replaced by rule at acquisition (§15) |
| §4 statistics (dependence) | Leave-one-repository-out range and repositories-in-alarms count added (§10, §11) |
| §5 compilability | Stated (§0, §6.3) |
| §1 tuning margin | Stated: zero fold-E alarms under every option (§5.4) |

## 18. Follow-up measurements on the same frozen corpus (not part of M3.6)

These run after M3.4, on the same frozen corpus, budget `1/20` and unit, as separate records. None changes the M3.6 verdict, and none may start before the first held-out result commit. Each needs its own protocol amendment or gate before it runs.

| Follow-up | What it measures | Needs |
| --- | --- | --- |
| Adversarial transformations | Recall under deliberate evasion: one token inserted every k − 1 tokens (breaks every k-gram analytically), dead-code insertion, statement reordering within blocks | Lexical definitions as in §6; the insertion result is known analytically and is reported as a check |
| LLM-rewrite arm | Recall when a model rewrites held-out units (prompt, model and version recorded; functional validity checked separately) | **Owner decision on using an external model** and on sending corpus code to it |
| Bag-of-tokens second method | A different system under test (multiset of tokens per unit) compared with the frozen winnowing baseline on the same cases and negatives | Roadmap STRUCT.1 |
| Keyed fingerprints | Whether per-relationship keyed hashes change any outcome (expected none) and their cost | Roadmap KEYED.1 and RES.1 |
| Existing open winnowing scanner | A side-by-side run of an existing open-source winnowing scanner (SCANOSS-style) on the same held-out cases and negatives, at the same alarm rule | A pinned, licensed scanner version; no network calls from it during the run |

## 19. Harness rulings (`m3-eval-draft-6`)

The O1–O8 rows were added in `m3-eval-draft-7`; the heading keeps its name so links stay valid. Each item of the harness author's list (A1–A40, `traceweave` `i3-eval` `c91ee91`, `eval/README.md`) and of the [harness review](../reviews/evaluation-harness-review.md) (`20162a8`) is ruled here. "Adopted" means the interim choice is now protocol text; "changed" means the harness must change. The last column lists what the harness changes.

| Item | Ruling | Section | Harness change |
| --- | --- | --- | --- |
| A1 lex-only | Adopted: `extract` with fingerprints discarded unread satisfies §2; temporaries under `TRACEWEAVE_EVAL_DIR/tmp` | §2 | move child-output temporaries from the system temp directory |
| A2 both CLIs | Adopted: every output from both, byte-identical | §8 | none |
| A3 resources | Adopted: `wait4` rusage replaces `/usr/bin/time` | §9 | none |
| A4 oversize | Adopted: path counts exclude oversize files | §3.4 | none |
| A5 odd folds | Adopted: fold S is the first ⌊n/2⌋ | §5.1 | none |
| A6 empty catalogue | Adopted; a *T* above the fold-S group count is always empty | §5.2 | none |
| A7 `u()` strings | Adopted verbatim | §6.2 | none |
| A8 rename numbering | Changed text to the harness's choice: first binding site | §6.3 | none |
| A9 `::` | Adopted: two `:` tokens | §6.3 | none |
| A10 reorder | Segments as the harness has them; **changed**: a Go top-level boundary also needs `(`-depth 0 | §6.1 | add the `(`-depth condition and a vector |
| A11 comments | Adopted (profile comment spans; shebang skipped) | §6.3 | none |
| A12 boundary in comment | Adopted, letter as written | §6.1 | add a vector |
| A13 miss reasons | Adopted | §10 | none |
| A14 spurious | Adopted | §10 | none |
| A15 file cell | Adopted | §6.2 | none |
| A16 ancestry | Adopted: non-empty check | §8 | none |
| A17 generator commit | Adopted | §8 | none |
| A18 result commit | Adopted | §9 | none |
| A19 pilot estimates | Changed: batched per-pair time (B6), direct checks in the estimate (B5), slowest setting for held-out kept | §5.5 | batch timing and checks |
| A20 r with no 10-case cell | Adopted: r = 0, ties decide | §5.4 | none |
| A21 not applicable vs failed | Adopted | §6.3 | none |
| A22 replacement facts | Adopted; licence of replacements classified from blob text; reproduction replays recorded revisions | §3.6, §4.3 | read blobs (B2) |
| A23 replacement limit | Adopted | §4.3 | none |
| A24 rule order | Adopted: dependency, then duplicate, then too few files, each over all earlier accepted repositories | §4.1 | none |
| A25 verifier | **Fixed in the spec**: `eligibleFileCountAfterContentRules` fact; `status` may be `acquired`; acquisition-time rejections allowed only when acquired | §3.1 | write the fact for every repository that passed the path rules, set `status: acquired` on the updated manifest and its entries, copy the draft-3 manifest |
| A26 Rust snippets | **Changed**: whole-file fallback for failed snippets; collateral counts reported | §5.2 | implement fallback and counts |
| A27 repeated units | **Changed**: no repeat within a cell | §6.2 | exclude used units |
| A28 pooling | Adopted | §5.4 | none |
| A29 tuning positives | Adopted | §5.4, §9 | none |
| A30 bound denominator | Adopted | §10 | none |
| A31 catalogue ids | Adopted | §6.2 | none |
| A32 manifest parsing | Adopted | §4.1 | none |
| A33 `fmt` ground truth | Adopted | §6.3 | none |
| A34 aborts | Adopted | §5.5 | none |
| A35 pilot sampling | Adopted | §5.5 | none |
| A36–A38 audit | Adopted | §12a | none |
| A39 table in freeze commit | Adopted | §8 | none |
| A40 estimate excludes the count | Adopted | §5.5 | none |
| Blob bytes | **Changed**: all measured bytes are committed blob contents at the pinned revision | §3.6 | read via `git cat-file`, verify SHA-1 |
| B1 stamp reader | Commit read from each binary's stamped version output | §8 | a supported Go reader (with a main change) |
| B2 git isolation | **Changed** | §3.6 | environment, protocols, timeouts |
| B3 = A25 | as A25 | §3.1 | as A25 |
| B4 memory | **Changed**: watchdog at 75% including the harness; batching of large searches allowed | §5.5 | watchdog |
| B5 direct checks | **Changed**: batched and estimated | §5.5 | batch |
| B6 per-pair time | **Changed**: batched timing | §5.5 | batch timing |
| B7 verdict | **Changed**: recomputed from per-search records in the committed result commit; clean tree | §12 | `searches.jsonl`, recompute, `git show` |
| B8 check counts, fold-S list | **Changed** | §5.2, §8, §9 | verify counts; record and check the lists |
| S-a abstention sabotage | Test required: an end-to-end abstaining search must alarm | §1 | add the test |
| S-b check-rate sabotage | Covered by B8 | §9 | add the test |
| S-c suppression source | Covered by B8 (builder refuses non-fold-S) | §5.2 | add the test |
| Suite scratch space | The harness documents its 6–8 GB need | — | TESTING.md |
| O1 Go stamp reader | Adopted for now: commit read from report-document provenance where no version command exists; unstamped refused. **Implementation change, owner: the implementation repository (Go lane on `main`)**: add `traceweave-go --version` in the Rust format | §8 | switch to `--version` for both once `main` has it |
| O2 case collisions | Adopted, plus `path-unsafe`; all colliding paths excluded; Unicode 17.0.0 full case folding | §3.4 | use full case folding if it does not already |
| O3 per-pair records | Adopted: deterministic gzip allowed; reproduction compares decompressed bytes | §10, §13 | none |
| O4 verdict body check | Adopted as an additional check; a disagreement is exit 2; absent bodies are not an error | §12 | none |
| O5 large searches | No protocol change: batching stays optional; until the harness implements it, a search over the memory line aborts the run (no verdict) by the watchdog | §5.5 | implement reference-file batching before the held-out run if the pilot shows any search near the line |
| O6 git timeouts | Adopted: 1,800 s fetch, 120 s `ls-remote`, 600 s local | §3.6 | none |
| O7 cell after a skip | Adopted: continue to the next slot; end at target or when no repository with room has an unused candidate | §6.2 | none |
| O8 fixed cost | Adopted: per-comparison process start and a match-heavy per-pair time for positives, both measured on fold S | §5.5 | none |
| Direct check shape (draft-8, `75b84eb`) | Adopted the author's wording: exactly the selected pairs, one `compare` per checked reference file and configuration; the per-search batch is withdrawn | §5.3, §5.5 | none (already implemented) |
| Caching check (draft-8) | Confirmed unbatched: whole reference against whole candidate catalogue; it is the check on caching and batching | §9 | none |
| N4 pair completeness (draft-9, review `ff907ac`) | **Changed**: the caching check covers positive cases only; every batched or cache-assembled comparison must contain every expected pair id exactly once, expected set computed from the two catalogues' artifact lists; difference is exit 2, no verdict; counts and digests recorded and recomputed by the verdict | §9, §12 | record expected/assembled counts and the pair-id digest per comparison; recompute in `m36-verdict` |
| Disk and margin (draft-8) | Figures recorded (2–5.5 GB of data); margin default 20 GB, operator may lower to 10 GB minimum, recorded in `identity.json`; below the margin mid-run is an abort | §5.5, §14.2 | refuse a margin below 10 GB (exit 2) and record the margin used |

**What changes materially.** A26 changes Rust results: more hashes are common, so Rust alarms and recall can only fall or stay at a given *T* (§5.2); the counts beside the verdict show by how much the suppression rests on collateral hashes. A10 and A27 change which cases are generated, not how they are scored. B7, B8 and the blob rule change no correct result; they remove ways a wrong one could pass.
