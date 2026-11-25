# E-TXT-1 protocol: Stage 1 prose evaluation (TXT.4)

Protocol version: `e-txt-1`. Status: **frozen for independent review, 2026-11-25; not yet run.** Roadmap gate [TXT.4](../../../ROADMAP.md) (Type `R`, started under the 2026-11-22 owner override for fingerprint-only text work). Profile under test: [`text-plain`](../../../profiles/text.md#17-staging-and-the-text-plain-freeze) (`draft-1`). Harness: [harness.py](harness.py). Primary evidence: [lane 09](../../lanes/09-evidence-review.md) and the [text profile review](../../reviews/extraction-profile-text-review.md).

Protocol digest (SHA-256, self-excluding): `642bb221f18b0a4efb1097ecbafa5da4f3f089dca018525b452db7e1cc5de2ce`

The digest above is the SHA-256 of this file's exact UTF-8 bytes with the 64 lowercase hex digits replaced by 64 zeros (`0`). `harness.py` recomputes this digest before running and refuses (exit `2`) on any mismatch.

This is a research protocol. It changes nothing in `spec/`, `schemas/`, `profiles/`, or `test-vectors/`. Nothing here makes a detection-accuracy or false-alarm-rate claim beyond the bounded Stage 1 contract check.

## 1. Freeze rule and measurement discipline

1. **Pinned source commit:** `7941c473d9a245c0c1023b29eccd61aa36ecdc1d` (local branch `roadmap-v2`), fixing the exact bytes of all 11 CC BY 4.0 prose files, the 6 repository boilerplate files, and the 10 TXT.2 vector/table files listed below.
2. **Frozen protocol commit:** the commit on `roadmap-v2` that commits this file (with its self-excluding SHA-256 digest populated) and `harness.py` without measured results.
3. **No measured run before independent review:** dry-run checks use `harness.py smoke` on TXT.2 vectors plus synthetic smoke prose completely disjoint from the 11 repository files, tagged `SMOKE RUN - NOT A RESULT`. Measured `full` execution MUST happen only after an independent non-author review of this frozen protocol is filed.
4. **Clean-worktree execution (`full` mode):** `harness.py full --frozen-commit <40-hex> --require-network-denied` refuses (exit `2`) unless:
   - `git status --porcelain --untracked-files=all` is empty;
   - `HEAD` descends from `--frozen-commit` (`git merge-base --is-ancestor`);
   - none of `PROTOCOL.md`, `harness.py`, `profiles/text.md`, `test-vectors/extraction-text/`, the 11 prose files, or the 6 boilerplate files differs from `--frozen-commit`;
   - every pinned SHA-256 digest in §3–§5 matches;
   - active OS network denial is proven;
   - both Rust (`traceweave`) and Go (`traceweave-go`) CLIs report `"stamp": "stamped"` with identical 40-hex `implementation.commit` and `specCommit`.
5. **Two-run determinism:** the measured run executes twice (`full-1`, `full-2`) and verifies byte-identical `summary.json` via `harness.py compare`.

## 2. Profile, extraction configuration, and comparison configurations

1. **Extraction profile:** `text-plain` (`draft-1`), hosted by [the extraction contract](../../../spec/extraction.md) and frozen in [`profiles/text.md`](../../../profiles/text.md#17-staging-and-the-text-plain-freeze). Parameters: `k = 8`, `window = 8` (`k + w - 1 = 15`), `maxInputBytes = 1048576`, `channels = ["exact","folded","skeleton"]`, `hash = "sha256-first8-u64be"`, `contract = "traceweave-text-winnow-draft-1"`.
2. **`text-markdown` (`draft-2`) status:** not normative and not implemented; both CLIs MUST reject `config-text-markdown.json` as `unsupported-config`. Per the [text profile review](../../reviews/extraction-profile-text-review.md#6-open-decisions-staging-and-fixes), Stage 1 extracts `.md` files with `text-plain`.
3. **Comparison configurations ([catalogue and report contract §4](../../../spec/catalogue-report.md#4-comparison-configuration), `traceweave-seed-merge-draft-2`):**
   - **Primary (`minRegionDistinctHashes = 1`, `mergeGap = 8`, unsuppressed):**
     ```json
     {"comparison":"traceweave-seed-merge-draft-2","modes":["exact","folded","skeleton"],"minRegionDistinctHashes":1,"mergeGap":8,"maxSeedsPerMode":100000,"maxRegionsPerMode":1000,"suppressionCatalogueSha256":"none"}
     ```
     Canonical LF-terminated bytes SHA-256: `91b3b2039a7ec3015a6d2f79c8207e4a95b0beab602bb81deb6c3b9c02b51e64`. `minRegionDistinctHashes = 1` is required so an excerpt of exactly `k + w - 1 = 15` tokens (which can yield a single selected fingerprint) is reportable (`match`), and `mergeGap = 8` matches the window size `w = 8`.
   - **Secondary negative diagnostic (`minRegionDistinctHashes = 2`, `mergeGap = 8`, unsuppressed):**
     ```json
     {"comparison":"traceweave-seed-merge-draft-2","modes":["exact","folded","skeleton"],"minRegionDistinctHashes":2,"mergeGap":8,"maxSeedsPerMode":100000,"maxRegionsPerMode":1000,"suppressionCatalogueSha256":"none"}
     ```
     Canonical LF-terminated bytes SHA-256: `4bbfe685752022a6e5b7120af2b78381197f903eefc62b44210a66bd1992beb4`. Reported as an informative secondary count on the 110 negative pairs alongside the primary `minRegionDistinctHashes = 1` count.
   - **Boilerplate-suppressed (`minRegionDistinctHashes = 1`, `mergeGap = 8`):** identical to Primary except `suppressionCatalogueSha256` equals the SHA-256 of the deterministic `text-plain` catalogue built from the 6 pinned boilerplate files (§5).

## 3. Pinned TXT.2 vectors and tables

All 10 JSON files under [`test-vectors/extraction-text/`](../../../test-vectors/extraction-text/README.md) are pinned at commit `7941c473d9a245c0c1023b29eccd61aa36ecdc1d`:

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| `test-vectors/extraction-text/config-negative-text.json` | 9409 | `dbe0347d83c185966ed9b3b2989a4a58d0e0033ccaa779911ea9c2be8d78da59` |
| `test-vectors/extraction-text/config-text-markdown.json` | 210 | `3bf7760a91297a5077f9fb0de3c119cb0a5d14b163190d640814a8735de23203` |
| `test-vectors/extraction-text/config-text-plain-limit16.json` | 202 | `16d15b33a3b0a117a155d1919f4331e94fce37af7cfbf285952f20fc22f4ac2a` |
| `test-vectors/extraction-text/config-text-plain.json` | 207 | `35c1f63cc2f669a54acb5f9792614721431943b2fd626ffb88982e53bd37323e` |
| `test-vectors/extraction-text/limits-text.json` | 2249 | `cb869b751ec98c4269fb517433e8f53dad665e6f40b09b541cdd9949dc99500e` |
| `test-vectors/extraction-text/records-text-plain.json` | 211182 | `4b58fba3ceaa8234e50db50a1a1bdcec2bfe2e7f465ed395fc3e638a77a78208` |
| `test-vectors/extraction-text/rejections.json` | 61225 | `f806d5e092a659ee07728b04a9fc601fa258aa481654477a6878b2c9b45ab97e` |
| `test-vectors/extraction-text/text-markdown.json` | 114894 | `26c76d7a2572f2a33c277e0820fbfb4ddb62269895d1638d5d6a39c45f6df47b` |
| `test-vectors/extraction-text/text-plain.json` | 318505 | `8690f5aea12a26e37ba3aa944107671075edf0103cd72db640b437042e195cb8` |
| `test-vectors/extraction-text/text-tables-17.0.0.json` | 378149 | `49eb0304ece1f9351f4db79ddf853fdc3bce353d4a833f7c4f9424bf80ae53f4` |

`harness.py` executes all **154** TXT.2 CLI cases (`text-plain.json`: 55; `limits-text.json`: 3; `records-text-plain.json`: 60; `config-negative-text.json`: 15; `text-markdown.json`: 21 rejected as `unsupported-config`) against both CLIs and verifies byte-for-byte agreement, exact expectation match, and token/k-gram/fingerprint byte spans.

## 4. Pinned corpus: exact 11 CC BY 4.0 prose files

No external download is performed. The corpus is the exact 11 top-level CC BY 4.0 ([LICENSE.md](../../../LICENSE.md)) Markdown prose files under `docs/`, `spec/`, and `profiles/` identified in [lane 09](../../lanes/09-evidence-review.md#proposed-first-bounded-experiment-unexecuted-needs-the-owner) (11 files, `11 × 10 = 110` ordered negative pairs), pinned at commit `7941c473d9a245c0c1023b29eccd61aa36ecdc1d`:

| # | Path | Bytes | SHA-256 |
| ---: | --- | ---: | --- |
| 1 | [docs/evaluation.md](../../../docs/evaluation.md) | 2122 | `7b659397c555b033ce7e28314ec7f2f1571f36c5e8ce2d27615c4b7a56d71b20` |
| 2 | [docs/implementation-patterns.md](../../../docs/implementation-patterns.md) | 11894 | `2fe9e3d08737eb19d2ab23bf0886bdb78bac74bf5571bb495fe41089232d746a` |
| 3 | [docs/implementation-repo-plan.md](../../../docs/implementation-repo-plan.md) | 15368 | `45cdb901c7daa70f8e8f4ce6e14658e66b3c3365b3587cb2b57eb01e77a1c0ef` |
| 4 | [docs/sources.md](../../../docs/sources.md) | 10239 | `f00e86568b3d8b009e20c409a67084e586e5229aa5a9d44258e7b539c553ab9f` |
| 5 | [docs/use-cases.md](../../../docs/use-cases.md) | 33324 | `0920225ec819bb3c58b81908e972792d16e6f7fad4abf28edd14dd2e7399f4ef` |
| 6 | [profiles/README.md](../../../profiles/README.md) | 1702 | `a85c9b69e2e7a222eb213a7ff215d88af4c24cd907515c39ad5314536b9d9f08` |
| 7 | [profiles/code.md](../../../profiles/code.md) | 12763 | `83b5eca2f12916b2cfb889e9247d2d99836bbd32633b99e318213bb9022ea6b7` |
| 8 | [spec/attestations.md](../../../spec/attestations.md) | 3141 | `56dc82ffbf21d049635ca68c523d334f8642c9911b4fe1b50a4455669ed49aff` |
| 9 | [spec/conformance.md](../../../spec/conformance.md) | 2650 | `4e3249938643e8209dc3227f8c82b5035e427f3d278c4e5eaf543b730423af77` |
| 10 | [spec/core.md](../../../spec/core.md) | 4773 | `2cdec134b60fefc136899f78f75bf73f04de178514d7759a2701f3640d31b449` |
| 11 | [spec/threat-model.md](../../../spec/threat-model.md) | 2237 | `136e81ebf9b719876c3bf4d85ee27936ec253dc3bffa265ced41517f7038322b` |

**Scope exclusion note:** `docs/reviews/initial-draft-review.md` (review under `docs/reviews/`), `docs/figures/embedded-mark-workflow.svg` (SVG diagram), and the four specification/profile files promoted on 2026-11-23 (`profiles/text.md`, `profiles/typescript.md`, `spec/catalogue-report.md`, `spec/extraction.md`) are excluded so the Stage 1 corpus remains the exact 11 files (`110` ordered negative pairs) specified in lane 09 and `ROADMAP.md` TXT.4.

**Canonical catalogue artifact IDs:** because `traceweave-catalogue-draft-2` restricts artifact IDs to `^[a-z0-9][a-z0-9._-]{0,63}$`, each path is mapped deterministically by replacing `/` with `__` and lowercasing (`docs/evaluation.md` → `docs__evaluation.md`; transformed positive `<base>--<tx_name>`; suppression control `<base>--with-bp`).

## 5. Pinned boilerplate set and suppression controls

The Stage 1 boilerplate set consists of the repository's 6 licence, notice, and governance text files, pinned at commit `7941c473d9a245c0c1023b29eccd61aa36ecdc1d`:

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| [CONTRIBUTING.md](../../../CONTRIBUTING.md) | 4453 | `3d55f9a0c56bd2c91372cd0e988edb444474062874de3b8773289df9df09e1f5` |
| [LICENSE.md](../../../LICENSE.md) | 1698 | `a04847c3339a695fd97bb2de12fbac881a400a7c8d25bcafb36d728e23337ebd` |
| [LICENSES/Apache-2.0.txt](../../../LICENSES/Apache-2.0.txt) | 11358 | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| [LICENSES/CC-BY-4.0.txt](../../../LICENSES/CC-BY-4.0.txt) | 18656 | `9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94` |
| [LICENSES/Unicode-3.0.txt](../../../LICENSES/Unicode-3.0.txt) | 1995 | `e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96` |
| [SECURITY.md](../../../SECURITY.md) | 1091 | `b2b255af6659a3a65e26c6ee17410e26fcebe932023fd9f690dff0b7818cdaec` |

Boilerplate evaluation runs three checks:
1. **Cross-pairs (unsuppressed):** compare the 11-file corpus catalogue against the 6-file boilerplate catalogue (`11 × 6 = 66` ordered pairs) with `suppressionCatalogueSha256 = "none"`, reported separately per channel as `matches / 66`.
2. **Boilerplate-suppressed inter-file negatives:** compare the 110 ordered negative pairs with `suppressionCatalogueSha256` bound to the boilerplate catalogue's SHA-256, reported alongside the primary unsuppressed `matches / 110`.
3. **Suppression control:** append `CONTRIBUTING.md` (first sorted boilerplate item) to the first sorted corpus file (`docs/evaluation.md`), compare against `CONTRIBUTING.md` unsuppressed (expect `match`) and suppressed with the boilerplate catalogue (expect `common-only`, confirming explicit-catalogue suppression per M2.10).

## 6. Lane 09 deterministic transformations

Each of the 13 deterministic transformations below is applied to every one of the 11 prose files (`11 × 13 = 143` transformed positive inputs), implemented identically in `harness.py`:

| # | Transform ID | Deterministic rule | Criterion (iii) expectation |
| ---: | --- | --- | --- |
| 1 | `reflow` | Normalize line endings to LF; split paragraphs on blank lines; collapse intra-paragraph whitespace to single `' '`; greedily wrap at 60 chars on spaces; join with `\n\n` | Unchanged `folded` sequence → MUST match in `folded` |
| 2 | `crlf` | Normalize `\r\n` → `\n`, then replace `\n` with `\r\n` | Unchanged `folded` sequence → MUST match in `folded` |
| 3 | `nfc` | Apply Unicode 17.0.0 NFC via pinned `text-tables-17.0.0.json` (identity on already-NFC files; non-trivial NFD→NFC is pinned by TXT.2 `plain-nfd`/`plain-nfc`) | Unchanged `folded` sequence → MUST match in `folded` |
| 4 | `nfkc` | Apply NFKC (`unicodedata.normalize("NFKC", text)` strictly as external input transform; changes compatibility glyphs in `docs/use-cases.md` and `docs/implementation-repo-plan.md`) | Unchanged `folded` sequence → MUST match in `folded` |
| 5 | `case-change` | Apply `text.upper()` | Unchanged `folded` sequence → MUST match in `folded` |
| 6 | `zero-width-10` | Scan code points left to right; insert `U+200B` (ZWSP) at every 10th intra-word gap between consecutive class-`W` code points (`text-tables-17.0.0.json`) | Unchanged `folded` sequence → MUST match in `folded` |
| 7 | `confusable` | Replace ASCII `a,c,e,o,p,x` with pinned `confusables.txt` Cyrillic lookalikes `а,с,е,о,р,х` (`U+0430, U+0441, U+0435, U+043E, U+0440, U+0445`) | `folded` changes (no unchanged folded run ≥ 15); **`skeleton`** stays unchanged → MUST match in `skeleton` (and in `folded` if any run ≥ 15 remains) |
| 8 | `markdown-strip` | Strip YAML front matter, fence delimiters, HTML comments/tags, link/image destinations (`[label](url)` → `label`), reference link definitions, table separator rules, heading/quote/list prefixes, `*`/`_`/`~~`/`` ` `` markers, and backslash escapes | Verified dynamically: any file retaining an unchanged `folded` run ≥ 15 tokens MUST match in `folded` |
| 9 | `smart-quotes` | Replace paired `"` with `“`/`”` (`U+201C`/`U+201D`), `'` with `’` (`U+2019`), and `--` with `—` (`U+2014`) | Unchanged `folded` sequence → MUST match in `folded` |
| 10 | `host-20x` | Embed the unmodified file at the midpoint of an unrelated synthetic host (`>= 20×` byte length) built from disjoint `hst[a-z]{5}` tokens seeded deterministically from `0x54585434 ^ (file_index * 100003)` | Unchanged `folded` run = full file → MUST match in `folded` |
| 11 | `excerpt-kw1` | Slice exact UTF-8 bytes `[tokens[0].span[0] : tokens[14].span[1]]` covering the first `k + w - 1 = 15` tokens | Unchanged `folded` run of exactly 15 tokens → MUST share ≥ 1 `folded` fingerprint and `match` |
| 12 | `distractor-kw2` | Insert `" zq"` after every `(k + w - 2) = 14`-th token | **Recorded limit** (defeats guarantee; sharing ≥ 0 fingerprints is valid) |
| 13 | `distractor-k1` | Insert `" zq"` after every `(k - 1) = 7`-th token | **Recorded limit** (breaks every k-gram; expected 0 shared fingerprints) |

## 7. Ordered negative pairs (110 pairs)

All `11 × 10 = 110` ordered `(reference, candidate)` pairs with `reference != candidate` over the 11 files in §4 are compared in canonical lexicographical path order. Outcomes are reported per channel (`exact`, `folded`, `skeleton`) as `matches / 110` (both unsuppressed `minRegionDistinctHashes = 1` and boilerplate-suppressed `minRegionDistinctHashes = 1`), alongside `sharedFingerprintPairs / 110` (`seedCount > 0`) and `matches_min2 / 110` (`minRegionDistinctHashes = 2`). No pass/fail threshold is imposed on the negative-match rate in Stage 1 (`ROADMAP.md` TXT.4).

## 8. Offline confinement and CLI requirements

1. **Offline execution:** the measured run MUST be invoked under `scripts/offline` (implementation repository) or `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'` with `--require-network-denied`. Before invoking any CLI, `harness.py` executes an active socket probe (`bind 127.0.0.1:0`, `connect 127.0.0.1:1`, `connect 1.1.1.1:443`) and refuses (exit `2`) unless all three are denied by the OS.
2. **Stamped CLIs:** both Rust `traceweave` and Go `traceweave-go` MUST report `"stamp": "stamped"` in `--version-json` with matching 40-hex `implementation.commit` and `specCommit`.
3. **No checkout pollution:** all temporary inputs, records, catalogues, and report bodies live in a `tempfile.mkdtemp()` directory outside the git checkout (`TRACEWEAVE_PRIVATE_DIR` set inside that temp directory).

## 9. Pass and negative-result criteria (ROADMAP TXT.4)

The Stage 1 verdict is **`negative-result`** (harness exits `3`) if ANY of the three failure criteria from `ROADMAP.md` TXT.4 holds:
- **(i) Cross-implementation agreement:** Rust `traceweave` and Go `traceweave-go` differ in exit code or output bytes on any TXT.2 vector (154 cases), any extraction record, any catalogue build/validation, or any comparison body/validation, OR disagree with any committed TXT.2 expectation.
- **(ii) Byte-span fidelity:** any reported span — token `[start, end)`, k-gram/fingerprint `[start, end)`, or comparison region `referenceSpan`/`candidateSpan` and underlying seed spans — does not equal the exact original UTF-8 byte offsets of the matched tokens in the input bytes.
- **(iii) Winnowing locality guarantee:** any transformed positive that retains at least one unchanged `folded` token run of length `>= k + w - 1` (`15` tokens) shares `0` fingerprints in `folded` (or fails to produce `match` in `folded` under `minRegionDistinctHashes = 1, mergeGap = 8`). Additionally, `confusable` (which targets `skeleton` while altering `folded`) MUST share `>= 1` `skeleton` fingerprint and produce `match` in `skeleton` whenever an unchanged `skeleton` run `>= 15` tokens is retained.

The Stage 1 verdict is **`met`** (harness exits `0`) when all §1 and §8 preconditions hold, none of (i)–(iii) occurs, two clean-tree runs (`full-1`, `full-2`) are byte-identical (`harness.py compare`), all negative (`matches / 110`) and boilerplate (`matches / 66`) denominators are reported, and a named non-author rechecks the counts.
