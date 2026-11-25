# Independent non-author review: TXT.4 Stage 1 prose evaluation protocol (`e-txt-1`)

Reviewed 2026-11-25 against [ROADMAP.md](../../ROADMAP.md) (`TXT.4` criterion) and [lane 09](../../research/lanes/09-evidence-review.md) at local commit `c708b20` (`c708b203165f3b1ea21e7205e3e1d91c16f946a4`) on `roadmap-v2`. I wrote none of [PROTOCOL.md](../experiments/text-stage1/PROTOCOL.md) or [harness.py](../experiments/text-stage1/harness.py), edited neither file, and ran all sabotage and simulation checks in memory or temporary clones/directories without modifying tracked files.

**Verdict: `ready to run`.** Blocking items: **none.** Four low-severity non-blocking observations (`F1`–`F4`) are recorded below for the non-author results recheck and any future revision.

---

## 1. Protocol fidelity

1. **Pinned 11 CC BY 4.0 prose files (`PROTOCOL.md` §4 vs `ROADMAP.md` TXT.4 & lane 09):**
   - Verified against `git ls-tree` at lane 09's commit (`c57fc226`) and pinned source commit `7941c473d9a245c0c1023b29eccd61aa36ecdc1d`. At `c57fc226`, `docs/`, `spec/`, and `profiles/` held 13 files: the exact 11 CC BY 4.0 Markdown prose files plus `docs/reviews/initial-draft-review.md` and `docs/figures/embedded-mark-workflow.svg`.
   - `PROTOCOL.md` §4 scope note explicitly excludes those two files plus the four 2026-11-23 promoted specification/profile files (`profiles/text.md`, `profiles/typescript.md`, `spec/catalogue-report.md`, `spec/extraction.md`), keeping the Stage 1 corpus at the exact 11 files (`11 × 10 = 110` ordered negative pairs) required by `ROADMAP.md` TXT.4 and lane 09.
   - Verified via `LICENSE.md` that prose/Markdown documentation is CC BY 4.0.
   - Verified via `shasum -a 256` and `wc -c` (and `git diff --stat 7941c473..HEAD` showing only `PROTOCOL.md` and `harness.py` added) that all 11 prose files, all 6 boilerplate files (`PROTOCOL.md` §5), and all 10 TXT.2 files (`PROTOCOL.md` §3) match their pinned byte lengths and SHA-256 digests.

2. **Ordered negative pairs (`110`) and boilerplate controls (`PROTOCOL.md` §5, §7):**
   - `evaluate_corpus` (`harness.py:1165-1210`) compares the 11-file corpus catalogue against itself under three canonical `traceweave-seed-merge-draft-2` configs (`cc1`: `minRegionDistinctHashes=1, mergeGap=8`, unsuppressed, SHA-256 `91b3b2039a7ec3015a6d2f79c8207e4a95b0beab602bb81deb6c3b9c02b51e64`; `cc2`: `minRegionDistinctHashes=2, mergeGap=8`, unsuppressed, SHA-256 `4bbfe685752022a6e5b7120af2b78381197f903eefc62b44210a66bd1992beb4`; and `cc_supp`: `minRegionDistinctHashes=1, mergeGap=8` bound to `bp_cat_sha`).
   - Per [catalogue-report.md](../../spec/catalogue-report.md#53-pairs) §5.3, self-comparison produces all `11 × 11 = 121` ordered pairs; `eval_negatives` separates `off_diag` (`reference.id != candidate.id`, `110` ordered pairs) from the `11` self-pairs and reports `matches / 110` and `sharedFingerprintPairs / 110` per channel (`exact`, `folded`, `skeleton`), with no pass/fail threshold.
   - Boilerplate cross-pairs (`11 × 6 = 66` ordered pairs) and the `CONTRIBUTING.md` + `docs/evaluation.md` suppression control (unsuppressed `match` vs suppressed `common-only`) match `PROTOCOL.md` §5.

3. **Lane 09 transformations (`PROTOCOL.md` §6, `harness.py:578-818`):**
   - All 13 lane 09 transformations (`reflow`, `crlf`, `nfc`, `nfkc`, `case-change`, `zero-width-10`, `confusable`, `markdown-strip`, `smart-quotes`, `host-20x`, `excerpt-kw1`, `distractor-kw2`, `distractor-k1`) are defined in `PROTOCOL.md` §6 and implemented deterministically in `harness.py`.
   - Simulated extraction of all 11 pinned files (`status=ok`, `211` to `5,195` tokens) and all `11 × 13 = 143` transformed positives via [check_text_vectors.py](../../test-vectors/extraction-text/check_text_vectors.py) (`text-plain` draft-1) confirmed:
     - `reflow`, `crlf`, `nfc`, `nfkc`, `case-change`, `zero-width-10`, `markdown-strip`, `smart-quotes`, `host-20x`, `excerpt-kw1`: `11/11` files retain an unchanged `folded` run `>= 15` tokens and share `>= 1` `folded` fingerprint (`0` misses).
     - `confusable`: `0/11` retain an unchanged `folded` run `>= 15` (`9/11` share `0` `folded` fingerprints); `11/11` retain an unchanged `skeleton` run `>= 15` and share `>= 1` `skeleton` fingerprint (`0` misses).
     - `distractor-kw2` (interval `14 = k + w - 2`, recorded limit): `0/11` retain an unchanged `folded` run `>= 15`, yet `11/11` still share `>= 1` fingerprint across all 3 channels.
     - `distractor-k1` (interval `7 = k - 1`, recorded limit): `0/11` retain an unchanged run `>= 15`, and `11/11` share `0` fingerprints in `exact`, `folded`, and `skeleton`.
   - `tx_nfc` uses pinned `text-tables-17.0.0.json` (`Unicode17Tables`), verified against `plain-nfd` → `plain-nfc` and `plain-hangul-jamo` → `plain-hangul`. `unicodedata` (Python 16.0) is used strictly in `tx_nfkc` as an external input transform (`PROTOCOL.md` §6 #4).

4. **Pass / negative-result criteria (i)–(iii) (`PROTOCOL.md` §9 vs `ROADMAP.md` TXT.4):**
   - **(i) Cross-implementation agreement:** checks exit code and byte-for-byte output across all 154 TXT.2 CLI cases (`55 + 3 + 21 + 60 + 15`), committed TXT.2 expectations, and every Stage 1 extraction, catalogue build/validation, and comparison body/validation. No loopholes.
   - **(ii) Byte-span fidelity:** checks every token `[start, end)`, k-gram/fingerprint `[start, end)`, and comparison region `referenceSpan`/`candidateSpan` and underlying seed token values against original UTF-8 bytes. No loopholes.
   - **(iii) Winnowing locality guarantee:** checks every transformed positive with an unchanged `folded` run `>= 15` tokens for both `shared_folded_fp > 0` and `outcomes["folded"] == "match"` under `minRegionDistinctHashes=1, mergeGap=8`, plus `confusable` on `skeleton` whenever an unchanged `skeleton` run `>= 15` tokens is retained. Strictly faithful to `ROADMAP.md` TXT.4 with no loopholes.

---

## 2. Harness soundness, digests, and adversarial checks

1. **Self-test & independent digest checks:**
   - `python3 -I research/experiments/text-stage1/harness.py self-test`: **6/6 tests passed** (`0.019s`).
   - Independently verified `PROTOCOL.md` self-excluding SHA-256 equals `642bb221f18b0a4efb1097ecbafa5da4f3f089dca018525b452db7e1cc5de2ce`, all 27 pinned file digests (`11 + 6 + 10`) match `shasum -a 256`, `cc1`/`cc2` digests match, and all generated catalogue artifact IDs satisfy `^[a-z0-9][a-z0-9._-]{0,63}$`.

2. **Sabotage checks (in memory / temporary clones only; no tracked files modified):**
   - **Criterion (ii) span mismatch (mocked `CliPair` over smoke corpus):**
     - Shifting `tokens[0]["span"][1]` by `+1` during extraction tripped `criterionII_spanMismatchErrors` (`41` errors).
     - Shifting `regions[0]["referenceSpan"][1]` by `+1` in comparison bodies tripped `criterionII_spanMismatchErrors` (`256` errors).
   - **Criterion (iii) dropped fingerprint on `>= 15`-token unchanged run (mocked `CliPair` over smoke corpus):**
     - Dropping `folded` fingerprints on `excerpt-kw1` (15 tokens) tripped `criterionIII_localityMissErrors` (`3` errors).
     - Dropping `skeleton` fingerprints on `confusable` tripped `criterionIII_localityMissErrors` (`3` errors).
   - **Unconfined network-denied runs:**
     - `python3 -I research/experiments/text-stage1/harness.py full --frozen-commit c708b203165f3b1ea21e7205e3e1d91c16f946a4 --require-network-denied` exited **`2`** (`PRECONDITION FAILED: Network denial NOT proven: bind:allowed; loopback:errno=61(ECONNREFUSED); public:connected`).
     - `python3 -I research/experiments/text-stage1/harness.py smoke --require-network-denied --allow-unstamped` exited **`2`**.
     - Running `check_network_denied()` under `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'` returned `True` (`EPERM` on `bind`, `loopback`, and `public`).
   - **Ancestry, clean-tree, and digest preconditions (temp clone):**
     - Dirty untracked file, non-ancestor `--frozen-commit`, tampered `PROTOCOL.md` digest, and committed drift in `docs/evaluation.md` after `--frozen-commit` each exited **`2`**.

3. **Error handling and non-blocking findings (`F1`–`F4`):**
   - `harness.py` does **not** silently swallow errors or weaken ancestry/clean-tree checks.
   - **F1 (non-blocking robustness on failure path):** In `evaluate_corpus`, if `extract_both` fails on an original file (`harness.py:1051`), `records_by_id` omits that ID and line `1088` raises `KeyError` (exiting `1` without writing `summary.json` instead of returning exit `3` / `negative-result`); a similar `KeyError` can occur at `1215`/`1245` if `extract_both` fails on a boilerplate/control input while `build_catalogue_both` succeeds. Cannot produce a false `met` (exit `0`), and TXT.3 already verified both CLIs on `text-plain`.
   - **F2 (non-blocking stamp detail):** `_check_versions` (`harness.py:458-460`) checks `r_spec == g_spec` rather than regex-checking 40-hex on `specCommit` (`implementation.commit` is 40-hex checked at `452`). `cliVersions` is logged verbatim in `summary.json` for non-author recheck.
   - **F3 (non-blocking denominator assertion):** `eval_negatives` (`1177`) and `bp_cross` (`1218`) record `denominator` from `body["pairs"]` without asserting `110` and `66`; the non-author recheck (`PROTOCOL.md` §9) verifies those exact denominators in `summary.json`.
   - **F4 (non-blocking transform/comment nits):** `tx_markdown_strip` (`697`) strips `**`/`__`/`~~`/`*` rather than single `_` (preserves `snake_case`), and `tx_smart_quotes` (`717`) comment notes avoiding 3+ hyphens while replacing `--` greedily; both affect only separators, and all `11/11` files keep unchanged folded runs `>= 15`.

---

## 3. Repository checks

Run via `.venv/bin/python` (matching `ROADMAP.md` `validate` command; bare `python3` lacks `jsonschema`):
- `.venv/bin/python tools/validate.py` — **PASS** (exit `0`)
- `.venv/bin/python tools/validate.py --links-all` — **PASS** (exit `0`)
- `.venv/bin/python -m unittest discover -s tests` — **PASS** (exit `0`, `9` tests)
- `.venv/bin/python tools/check_hygiene.py` — **PASS** (exit `0`)
