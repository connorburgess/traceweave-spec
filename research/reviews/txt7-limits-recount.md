# Independent non-author recount: TXT.7 limits in `profiles/text.md` §13

Reviewed 2026-11-25 against [ROADMAP.md](../../ROADMAP.md) (`TXT.7` criterion) at local commit `b193376` on `roadmap-v2`. I wrote none of [profiles/text.md](../../profiles/text.md), [RESULTS.md](../experiments/text-stage1/results/e-txt-1/RESULTS.md), or [lane 09](../lanes/09-evidence-review.md).

**Verdict: `met` (`0` uncited limits out of `18` recounted limit items; all 4 required TXT.7 categories present).**
Note on release notes: the repository has no release-notes file yet (pre-release state; release notes are gated by `M5.4`, which remains `open`). All profile-side `TXT.7` requirements in [profiles/text.md](../../profiles/text.md#13-limits-what-the-profile-cannot-detect-or-claim) §13 are satisfied with zero uncited limits.

---

## 1. Required TXT.7 categories check

| Required category (`ROADMAP.md` TXT.7) | Present in `profiles/text.md` §13 | Citations verified |
| --- | --- | --- |
| Paraphrase | Yes (bullet 1, line 338) | `W` §3, `K` (§5.3, Table 2, Fig. 6b), `P` (§3–§4, Fig. 1) via [lane 09](../lanes/09-evidence-review.md#paraphrase-and-translation-limits); `e-txt-1` (`143` transforms on `11` files; `TXT.6` owner-gated) |
| Translation | Yes (bullet 2, line 339) | `P` Table 5 (`14%` `de/es→en` cases) via [lane 09](../lanes/09-evidence-review.md#paraphrase-and-translation-limits); `e-txt-1` (`11/11` English prose files) |
| Fragments shorter than `k+w-1` tokens | Yes (bullet 3, line 340) | `W` §3 via [lane 09](../lanes/09-evidence-review.md#verdict-table); contract §8; `e-txt-1` `excerpt-kw1` (`11/11`); vectors `plain-below-kw1` (`12` tokens), `plain-short` (`5` tokens, `0` k-grams) |
| Scripts without spaces, if unmeasured | Yes (bullet 4, line 341) | `U` UAX #29 WB rules via [lane 09](../lanes/09-evidence-review.md#tokenization-and-normalization), [lane 09](../lanes/09-evidence-review.md#how-the-extraction-contract-could-host-a-text-profile); `plain-thai`, `plain-japanese`; `e-txt-1` (`11/11` English prose files; recall unmeasured) |

---

## 2. Item-by-item recount of `profiles/text.md` §13

Every bullet in [profiles/text.md](../../profiles/text.md#13-limits-what-the-profile-cannot-detect-or-claim) §13 (lines 338–365; line 336 is the introductory citation-scope sentence) was recounted and cross-checked against [e-txt-1 summary.json](../experiments/text-stage1/results/e-txt-1/summary.json), [e-txt-1 RESULTS.md](../experiments/text-stage1/results/e-txt-1/RESULTS.md), [text-plain.json](../../test-vectors/extraction-text/text-plain.json), [extraction-profile-text-review.md](extraction-profile-text-review.md), [09-evidence-review.md](../lanes/09-evidence-review.md), and [09-report-audit.md](../lanes/09-report-audit.md).

| # | Line(s) | Limit item | Cited `e-txt-1` (`TXT.4`) / vector / review counts | Cited Lane 09 / spec source | Recount verification | Uncited? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 338 | Paraphrase | `e-txt-1`: `143` deterministic transforms on `11` repository files (`TXT.6` owner-gated) | `W` §3, `K` (§5.3, Table 2, Fig. 6b), `P` (§3–§4, Fig. 1) via lane 09 | `11 × 13 = 143` in `summary.json`; `W`/`K`/`P` locations match lane 09 | No |
| 2 | 339 | Translation and cross-language reuse | `e-txt-1`: `11/11` English repository prose files | `P` Table 5 (`14%` `de/es→en`) via lane 09 | `11` English prose files in `summary.json`; `14%` matches lane 09 line 22 | No |
| 3 | 340 | Fragments shorter than `k + w − 1` = 15 tokens | `e-txt-1` `excerpt-kw1` `11/11` across all 3 channels; `plain-below-kw1` (`12` tokens), `plain-short` (`5` tokens, `0` k-grams) | `W` §3 via lane 09; contract §8 | `excerpt-kw1` `11/11/11` in `summary.json`; `text-plain.json` confirms `12` and `5`/`0` | No |
| 4 | 341 | Scripts without spaces other than ideographs | `plain-thai`, `plain-japanese`; `e-txt-1` (`11/11` English prose files; recall unmeasured) | `U` UAX #29 WB rules via lane 09; lane 09 host checklist | Matches lane 09 lines 24, 30, 63; `plain-thai` (`2` tokens), `plain-japanese` (`14` tokens) in `text-plain.json` | No |
| 5 | 342 | Repeated-structure `ambiguous` outcomes on long prose | `e-txt-1`: `35/143` misses (`49`–`1,169` shared fps): `32` `folded` (`8` × `4`: `docs/sources.md` `323`, `docs/use-cases.md` `1,169`/`1,167`, `profiles/README.md` `49`, `profiles/code.md` `423`) + `3` `skeleton` (`339`, `1,138`, `407`); self-pairs `8/11`, `7/11`, `8/11` (`min=1`) vs `9/11`, `10/11`, `10/11` (`min=2`) | `catalogue-report.md` §5.7–§5.8; `e-txt-1` `RESULTS.md`; `text-stage1-protocol-review.md` | Every count independently verified in `summary.json` (`failureCriteria`, `transformations.*.details`, `negativesUnsuppressedMin1/2.selfPairMatches`) | No |
| 6 | 343–353 | Distractor insertion at intervals `w + k − 2` and `k − 1` | `e-txt-1`: `distractor-kw2` (`0/11`, `11/11`, `11/11`), `distractor-k1` (`0/11`, `0/11`, `0/11`); clean-room review §5 (`3,639` tokens, `807` fps, `3,617` k-grams; rows `30`/`15`/`14`/`8`/`7`) | Lane 09 (`#after-the-report-audit`); `09-report-audit.md` (`#what-survives`); `extraction-profile-text-review.md` §5 | Every table cell and `40%` (`326/807 = 40.4%`) verified against `summary.json` and `extraction-profile-text-review.md` lines 78–90 | No |
| 7 | 354 | ZWSP as a separator | `plain-zwsp-as-separator` | `U` UAX #29 WB4 via lane 09 | Verified `U+200B` in `Default_Ignorable_Code_Point` (`I`) and `plain-zwsp-as-separator` (`8` tokens) | No |
| 8 | 355 | Invisible format characters not `Default_Ignorable` split words | `plain-format-char-split`; `32` `Cf` non-`Default_Ignorable` code points; `extraction-profile-text-review.md` §5 | Unicode 17.0.0 `DerivedCoreProperties.txt` (`U` via lane 09); OD-T14 | Listed ranges sum to `6+1+1+2+1+3+1+1+16 = 32` code points; `plain-format-char-split` (`7` tokens, `insufficient-tokens`) verified | No |
| 9 | 356 | Line-end hyphenation | `plain-hyphenation-wrap`; `e-txt-1` (transform not included) | `W` §5.2 via lane 09 | `plain-hyphenation-wrap` (`11` tokens) verified in `text-plain.json` | No |
| 10 | 357 | Typography that NFKC does not unify | `plain-nfkc-compat`, `plain-numbers`, `plain-punct-a`; `e-txt-1`: `nfkc` changed `2/11` files; `smart-quotes` kept `11/11` folded sequences unchanged | `U` UAX #15 §1.2 via lane 09 | Verified via `harness.tx_nfkc` (`docs/implementation-repo-plan.md`, `docs/use-cases.md` = `2/11`) and `summary.json` `smart-quotes` (`11/11` `unchangedFoldedRunCount`) | No |
| 11 | 358 | Markdown deviations | `extraction-profile-text-review.md` §3; `e-txt-1` (`21/21` `unsupported-config` on `text-markdown.json`; `.md` inputs run under `text-plain`) | `W` §5.2 via lane 09; `text-markdown` draft-2 §5 | Verified `text-markdown.json: 21` in `summary.json` and `RESULTS.md` | No |
| 12 | 359 | Unlisted homoglyphs and cross-script skeleton collisions | `plain-greek` (`σοφοσ` → `ooɸoo`); `e-txt-1` `confusable`: `6` Cyrillic letters, `11/11` `sharedFingerprints > 0` in `skeleton`, `8/11` `match` + `3/11` `ambiguous`, vs `2/11` in `exact`/`folded` | `U` UTS #39 §4 via lane 09 | Verified `CONFUSABLE_MAP` has `6` entries in `harness.py`, `plain-greek` skeleton value `ooɸoo` in `text-plain.json`, and `8/11` + `3/11` vs `2/11` in `summary.json` | No |
| 13 | 360 | Common phrases and boilerplate match | `e-txt-1`: `2/110` (`exact`), `4/110` (`folded`), `4/110` (`skeleton`) at `min=1`; `2/110`, `0/110`, `0/110` at `min=2`; `0/66` boilerplate cross-pairs; `CONTRIBUTING.md` + `docs/evaluation.md` `match` → `common-only` | `W` §5.1–§5.2 via lane 09; `catalogue-report.md` OD-C5(b); `ROADMAP.md` M2.10 | Every negative and boilerplate count verified in `summary.json` | No |
| 14 | 361 | No ownership, authorship, permission or direction-of-copying inference | `e-txt-1` (tests byte-span fidelity and locality, not origin) | `W`, `B`, `M`, `K` in lane 09 (`#claim-audit-checklist-for-the-incoming-notebooklm-report`); `UC-8`; contract §12 | Citations match lane 09 line 115 and `e-txt-1` scope | No |
| 15 | 362 | No calibrated false-alert or detection rate | `e-txt-1` (`2/110`, `4/110`, `4/110` at `min=1`); `TXT.6` (`0/200` ~`1.5%`) | `W`, `B`, `M`, `P` via lane 09 (`#calibration-evidence`); [lane 07](../lanes/07-evidence-review.md) | Counts verified in `summary.json`; `3/200 = 1.5%` matches lane 09 line 78 and lane 07 full-search calibration rule | No |
| 16 | 363 | No absence claim | `e-txt-1` `distractor-k1` (`0/11` matches across all 3 channels) | `K`, `P` Table 5 via lane 09 (`#paraphrase-and-translation-limits`) | Verified `0/11` across all 3 channels in `summary.json` | No |
| 17 | 364 | No privacy | — (non-empirical property of unkeyed SHA-256) | Lane 09 (`#how-the-extraction-contract-could-host-a-text-profile`); `09-report-audit.md`; contract §7, §12 | Citations match lane 09 line 68 and `09-report-audit.md` line 35 | No |
| 18 | 365 | No embedded mark | `e-txt-1`: `zero-width-10` `11/11` `folded` `sharedFingerprints > 0`; `confusable` `11/11` `skeleton` `sharedFingerprints > 0` | Lane 09 (`N` §§6–7, App. E; `U` UAX #15, UTS #39 §4; `A` §V); `txt8-unicode-mark-review.md` | Verified `11/11` in `summary.json` and citations in `txt8-unicode-mark-review.md` | No |

---

## 3. Summary counts

- **Total limit items in `profiles/text.md` §13:** `18`
- **Cited items (cites `TXT.4`/`e-txt-1`, lane 09 primary source, or both):** `18`
- **Uncited limits:** `0`
- **TXT.7 status:** **met** (profile requirement satisfied; release-notes requirement remains tracked under `M5.4`).
