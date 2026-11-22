# Non-author review: M3 evaluation protocol `m3-eval-draft-1` and corpus proposal

Reviewed 2026-11-22 at commit `067be17` on `roadmap-v2`: [evaluation-protocol.md](../drafts/evaluation-protocol.md) and [evaluation-corpus/](../drafts/evaluation-corpus/README.md). Read against ROADMAP M3.0–M3.6, [lane 07](../lanes/07-evidence-review.md), the [catalogue and report contract](../drafts/catalogue-report-contract.md) and the implementation at `<implementation repo>` `main` (`82b02ab`). I did not write any of them.

Network use was read-only GitHub API metadata (12 root-tree requests). I downloaded and cloned nothing, and fetched no source or licence text. Scripts are in `$TMPDIR/m3/`.

## What I ran

| Check | Result |
| --- | --- |
| `python3 -I verify_manifest.py` | `VALID: 48 entries; split digest 146acfc2…dce3; 264 held-out negative searches; 20 labelled same-domain`, exit 0 |
| `verify_manifest.py --self-test` | 34 broken manifests rejected with the expected code, 0 failures, exit 0 |
| My own walk re-derivation (`walk.py`, independent of the checker): order by `SHA-256(salt ‖ lowercase(full_name))`, prefilter rules 1–3, recorded fact verdicts, stop at 24 | Go: 29 walked, the same order and verdicts as recorded, 24 accepted = the entries. Rust: 39 walked, the same, 24 accepted = the entries. 12/12 held-out groups per language reproduce. The split digest recomputes to `146acfc2…dce3` |
| Six broken manifests of my own (`broken.py`) | rejected, exit 1: unsorted licence expression (`E-LICENCE-EXPRESSION`); uppercase revision in entry and walk (`E-SCHEMA`); eligible bytes 21,000,000 in both places (`E-SIZE`); one changed digest character (`E-SPLIT-DIGEST`); target 23 with 24 entries (`E-WALK`). **Accepted, exit 0:** a licence-file SHA-256 changed consistently in entry and walk (see M5) |
| Spot check of 10 entries (every 5th): GitHub `git/trees/<revision>` | 10/10 pinned revisions exist, none truncated. 10/10 root licence files are present with the recorded git blob SHA-1. The recorded expression agrees with GitHub's detected licence in 9/10. For `seanmonstar/reqwest`, GitHub says Apache-2.0 and the manifest records `Apache-2.0 AND MIT` from two files, which is the protocol's conservative reading. All 10 are permissive, so `permitted-with-notice` is justified. Licence text and SHA-256 were not checked; that would need the content |
| Exact binomial bounds (my code) | see §4 |

## Findings, most severe first

**F1 (blocking before freeze). Several generation rules are not mechanical.** Two implementers following §6 would produce different case files, so M3.5's "byte-identical `cases-*.jsonl`" would rest on one implementation's choices. **`rename`, Rust:** `syn` has no name resolution. Name the occurrence rule. For example: every identifier token in the unit whose text equals a collected binding, except after `.` or `::`, in field-init shorthand (`Foo { x }`), and inside macro bodies and format strings. **`rename`, Go:** `go/ast` objects are deprecated and resolve only within one file. Partial units cannot be parsed alone. State the parse context (the whole source file) and whether fields, methods and labels are renamed. **`partial` units (§6.1):** "a maximal run of consecutive statements … whose token count falls in the bucket" does not define the candidate list. Define it, for example: all (block, first statement, last statement) runs in the bucket, sorted by (path, start offset, end offset). **`split-mix`:** "the statement boundary nearest its middle token" needs a tie rule.

**F2 (blocking). `fmt` will mostly fail to generate for Go.** "An unchanged file is `generation-failed`". Most Go repositories are gofmt-clean, and a gofmt-clean unit inserted with one `\n` on each side is usually left unchanged by `gofmt -s`. The Go `fmt` cell, and the `fmt` step of `compound`, would then be largely empty or self-selected. Fix: define "unchanged" against the pre-format bytes with markers, and either count an unchanged output as a valid `fmt` case (identity formatting) or de-format first (apply `ws`) before formatting. Rust `fmt` uses `--edition 2021` while the profile is `rust2024-tokens`. Use 2024, or the crate's declared edition, and pin which.

**F3 (blocking). Abstentions lower the false-alarm count, so M3.6 can be passed by abstaining.** An alarm is any mode outcome `match` (§1). A pair whose reportable regions are all `ambiguous`, or that hits `seed-limit-exceeded`, is an abstention and raises no alarm, though an operator would still see candidate regions to review. A configuration that abstains more passes more easily. The §5.4 selection rule cannot catch this either, because it maximizes recall only among configurations with *a* ≤ budget/2. Fix: count a search as alarmed when any pair-mode is `match` **or** `abstain`/`ambiguous`. Count `seed-limit-exceeded` in a negative search as an alarm too (conservative), or make M3.6 an error when it occurs. Report the per-reason split beside it.

**F4 (blocking). The 264 ordered searches likely double-count.** Under contract §5.5–§5.8 the mode outcome appears symmetric in (R, C): seeds, distinct-hash evidence, ambiguity over either side's positions, and suppression. If so, R→C and C→R alarm together, and the data are 132 unordered pairs counted twice. Under option B, "≤ 2 of 264" would then mean "≤ 1 unordered pair". I did not test symmetry on the implementation. Fix: add a symmetry test to the runner. If outcomes are symmetric, define N as unordered pairs (132) and recompute the §14.1 thresholds. If not, keep the ordered pairs but say which directional quantities differ.

**F5 (high). The acquisition-time grouping rules are underspecified, and they will change this split.** **Go dependency edges** are said to point at "another corpus repository", but Go `require` paths are module paths, often vanity paths (`google.golang.org/grpc` for `grpc/grpc-go`, `gorm.io/gorm`, `/vN` suffixes). Define the match: the require path equals, or has as a `/`-prefix, a `module` path declared in a `go.mod` of another corpus repository. **Rejection tie rule:** §4.1 rejects "a repository that would merge into another owner's group" but does not say which of the two. State it: the one later in walk order. **Known effects:** in Rust held-out, `seanmonstar/reqwest` and `tokio-rs/axum` both depend on `hyperium/hyper`. In Go tuning, `micro/go-micro` very likely requires `google.golang.org/grpc`. The owner's M3.1 approval should therefore name the walk continuation, not only the 48 entries.

**F6 (high). The cost of the tuning grid is not estimated, and it dominates.** §15 costs only the held-out positives. Fold E is about 6 repositories per language: about 0.88 M (Go) + 0.43 M (Rust) ordered file pairs per configuration (my estimate from the manifest's eligible-path counts). The grid has 144 configurations, so about 190 M pair comparisons in both modes, plus the fold-E positives. `minRegionDistinctHashes` and *T* act after seeds are formed, so seeds could be shared across the 16 configurations per (k, w): 9 × 1.3 M pairs. Fix: specify that sharing, validated by a byte-identical sample as in §9, and add a run budget and abort rule like the image protocol's. See §6 for the numbers.

**F7 (medium). The hit rule is lenient.** One byte of overlap on each side counts as detection, so a region that is mostly host code next to the inserted unit can count. Report the distribution of covered fraction per cell (matched candidate bytes ÷ ground-truth bytes) beside recall, without a pass line.

**F8 (medium). M3.3 ancestry proves commit order only.** It cannot show that held-out data were not run before the freeze. The runner and generator refusals are the real control. State this limit in the report. Log, in the first held-out result commit, the runner's identity record (HEAD, clean status, freeze digest), as the image harness does.

**M5 (medium). The checker cannot detect licence SHA-256 values that are internally consistent but wrong** (my sixth broken manifest). Acquisition step 1 rechecks only the blob SHA-1. Fix: acquisition also recomputes the SHA-256 and reruns `m3-licence-classifier-v1` on the fetched file, with exit 1 on any difference.

**Low.** The freeze names "this protocol's SHA-256", but the protocol is a mutable draft. Freeze it with a self-excluding digest first. §3.6 step 5 replacements need the same licence and size facts recorded in the walk. `rui314/mold` (C++ upstream, 201 `.rs` paths) and `benfred/py-spy` (4.2 MB in 39 paths) are flagged by the authors. They stay in or out by rule, which is correct.

## 1. Pass/fail decided in advance

Every gate maps to an exit code or a count: M3.1 and M3.2 via `verify_manifest.py`, M3.3 via the §8 commands, M3.5 via `cmp` plus a tolerance script, M3.6 via integer `A×q ≤ p×N` (exit 0, 3 or 2). **Fixed in advance:** the 144-point grid, the selection rule (exit 0 or 3), tie order, suppression construction, fold split and freeze contents. **Left open:** only the items in F1–F3. **The budget barely affects tuning.** With about 30 fold-E searches per language, "*a* ≤ budget/2" means 0 alarms for all three budget options (1/40, 1/200, 1/2000 are all below 1/30). That is mechanical and harmless; say so.

## 2. Leakage

**Ruled out:** The suppression catalogue uses fold S only; selection uses fold E only. Namespaces `tuning` and `held-out` salt separately. Held-out reads before the freeze are limited to digests, lengths, generated-file tests and dependency declarations. Groups are owners, and a split is per group. The census owners and `golang`/`rust-lang` are excluded; the checker enforces this. I found no corpus repository named anywhere in the implementation repository (`git grep` on `main`).

**Constructed leak paths:** **(a) Modified copies across owners.** The duplicate rule catches only byte-identical files of ≥ 1,024 bytes. A modified or reformatted copy of held-out code inside a tuning repository is not caught. Candidates: router trees derived from `httprouter` in `gin-gonic/gin` (held-out) and Go routers in tuning (`go-chi/chi`, `kataras/iris`). Such code can enter fold-S suppression or fold-E positives, so held-out content shapes frozen choices. Cheap fix that needs no extraction: also merge or reject on equal SHA-256 of each file's bytes with whitespace and comments removed by the profile's own trivia rules (a lexical pass, not fingerprinting). **(b) Standard-library copies.** Code copied from the Go or Rust standard library inside corpus repositories was seen in the I2 cross-check, but the exclusion is by owner only. This exposed the developers, not the frozen parameters, since the grid is fixed in advance. It is acceptable if stated.

Neither path is severe at 24 repositories per language, but (a) should be closed by rule.

## 3. Selection rule

The pool snapshot, the order, the prefilter verdicts and the stopping point reproduce exactly, from my own script (above). Fact-based verdicts rest on recorded facts, and 10/10 sampled facts (revision, licence blob) match GitHub metadata. The rule order is correct: `XIU2/CloudflareSpeedTest` (8 eligible paths, GPL-3.0) is rejected for licence (rule 6) before size (rule 7).

## 4. Statistics

These are exact Clopper–Pearson bounds under independence. "P(met)" is the probability the M3.6 verdict is met when the true per-search rate is the given value, for N = 264.

| Budget | met iff A ≤ | One-sided 95% UB at that A | P(met) at ½ budget | P(met) at budget | P(met) at 2× budget |
| --- | --- | --- | --- | --- | --- |
| A 1/20 | 13 | 0.077 | 0.993 | 0.551 | 0.002 |
| B 1/100 | 2 | 0.024 | 0.853 | 0.508 | 0.101 |
| C 1/1000 | 0 | 0.011 | 0.876 | 0.768 | 0.589 |

Other bounds: 0/264 gives 0.0113 and 0/132 gives 0.0224. The disjoint subset (6 per language, 12 total) gives 0.221 at 0 alarms and 0.339 at 1. All of these match §11.

**Independence fails more than the draft says.** Alarms are driven by repository properties such as boilerplate density, so one noisy repository can alarm in up to 22 searches. The effective sample is nearer 24 repositories than 264 searches. Add a leave-one-repository-out range for false alarms (as for recall), and the count of distinct repositories involved in alarms. Under B, a single repository can flip the verdict. That is a property of the corpus, and it should be stated.

**Alarm unit.** "Any `match` in either mode, per repository search" is the right operator unit, since one alarm means one review. With F3's fix it also covers ambiguous regions. Report pair-level false matches beside it (already planned).

**Positives.** Targets of 30 per cell are attainable: 12 held-out source repositories × at most 3 = 36. Wilson half-widths up to about ±0.17 are adequate for a report with no pass line. The paired design, with discordant counts, is the right comparison.

## 5. Transformations

**Token-stream claims.** **Correct:** `ws`, `comments-strip` and `comments-add` leave the stream identical. Rust doc comments are dropped by extraction OD-5. Go general comments with a line break become `\n`, so semicolon insertion holds. **Spans:** ground-truth spans are well defined for `verbatim`, `ws`, `comments-*`, `reorder` and `split-mix` (offset bookkeeping), and for `fmt`/`compound` through the markers.

**Changes to behaviour or compilation.** `comments-strip` removes Go `//go:build`, `//go:embed` and cgo preambles. `reorder` breaks Rust `macro_rules!` textual order. `split-mix` leaves unbalanced braces, which the profile's lexers accept. Rust `rename` (F1) can break field shorthand and format-string captures.

None of this matters for a lexical baseline, but the report must say that cases are not compilable copies, and that recall describes lexical robustness only.

## 6. Can a metric be gamed; what M3.1–M3.5 still need

- **Gaming:** M3.6 via abstention (F3); recall via one-byte hits (F7); empty Go `fmt` cells (F2). Otherwise every figure has a denominator, and attempted/generated counts expose generation failures. **M3.1 as worded** (per-entry revision, licence, redistribution, split group; census excluded; a script checks it): met by the proposal's form. **M3.2:** met by the plan, once the post-acquisition split exists. **M3.3:** commands defined (note F8). **M3.4:** every listed figure is present. **M3.5:** requires the F1 fixes, or the regenerated cases will not be byte-identical across implementers.

## 7. Cost on one laptop

**Download.** GitHub reports 621,386 KiB including history, which is an upper bound. A depth-1 fetch should be a fraction of that, an estimate of roughly 100–250 MB. Eligible source is 58.8 MB.

**Catalogues.** The measured catalogue size is about 70 bytes per fingerprint (1.2 GB for 2 × 8.4 M). At window 4 that gives about 0.8 GB per (k, w) for the whole corpus. Tuning needs 9 (k, w) settings on the tuning half and held-out needs one, so about 4–5 GB of private derived data. That fits.

**Memory.** Per comparison it stays far below the measured worst case (3.6 GiB at the extraction bounds), because real files are under 1 MiB.

**Runtime.** No measured cost exists for a real file pair; the shipped measurements are worst cases and one 0.8 MiB self-compare (0.16 s, process start included). Assuming 1 ms per pair (both modes):

| Workload | Estimate at 1 ms per pair |
| --- | --- |
| Held-out negatives (1.37 M + 1.94 M ordered pairs) | about 1 h |
| Held-out positives with pair caching | minutes |
| Tuning grid without seed sharing | about 50 h |
| Tuning grid with seed sharing (F6) | about 3–4 h |

**Verdict on cost:** it fits one laptop only with seed sharing. Measure the per-pair cost first, on non-corpus code (for example the implementation's own sources), and record it in the protocol.

## Budget recommendation (the owner chooses)

**B (1/100), provided F3 and F4 are fixed** (if outcomes are symmetric, B means at most 1 unordered alarmed pair out of 132). **Why not C:** the verdict would mean nothing. It is met with probability 0.59 even when the true rate is *twice* the budget, and the corpus cannot bound a rate near 1/1000. **Why not A:** it is the only option whose verdict sharply separates half and double the budget (0.993 against 0.002). But 1 alarm per 20 searches is 50 reviews per 1,000-repository sweep, which is weak operationally. **Why B:** it gives a usable operator target (about 1 review per 100 candidates). It still separates ½× from 2× moderately (0.85 against 0.10), and it is decided by a count. **Condition:** the M3.6 rendering should print the operating characteristics above beside the verdict. **If the owner wants a verdict that luck cannot pass,** choose A, or keep B and raise the scale to 100 per language (§14.4).

## Verdict

**Ready after listed fixes.** The owner can decide M3.0 (budget), the corpus storage location (§14.3) and the scale now; none of them depends on the fixes. M3.1 approval should wait for F5, so that it covers the walk's replacements.

Fixes before the protocol is frozen:
1. **F1:** make `rename` (both languages), the partial-unit list and the `split-mix` tie mechanical.
2. **F2:** define `fmt` so Go cells are not emptied by "unchanged"; set the Rust edition.
3. **F3:** count ambiguous and seed-limit abstentions as alarms in M3.6.
4. **F4:** test outcome symmetry; if symmetric, count unordered searches and restate the thresholds.
5. **F5:** define Go module-path matching and the rejection tie rule; widen the duplicate rule to trivia-stripped digests.
6. **F6:** add the tuning-cost estimate, seed sharing with a byte-identical check, and a run budget with an abort rule.
7. **M5:** recheck licence SHA-256 and classification at acquisition.

F7, F8 and the low items are reporting and wording fixes.
