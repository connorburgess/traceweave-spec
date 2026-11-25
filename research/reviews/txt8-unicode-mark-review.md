# Independent non-author review: TXT.8 Unicode carrier and AWT source verification

Reviewed 2026-11-25 against [ROADMAP.md](../../ROADMAP.md) (`TXT.8` criterion), [lane 09](../lanes/09-evidence-review.md#embedded-marks-in-existing-text), [docs/sources.md](../../docs/sources.md), and [profiles/text.md](../../profiles/text.md) at local commit `52b0702` on `roadmap-v2`. No new text-mark experiment was designed or executed (owner-gated per [ROADMAP.md](../../ROADMAP.md#owner-blocked-gates)).

**Verdict: `negative-result` confirmed for Unicode carriers.** Lane 09's reading that homoglyph and zero-width Unicode carriers are erased by the declared deterministic fold (`NFKC` + UTS #39 `skeleton` + delete `Default_Ignorable_Code_Point`) and that AWT post-hoc lexical rewriting is rightly rejected is independently confirmed. Any new text-mark experiment remains owner-blocked.

---

## 1. Source coverage check (`docs/sources.md`, `profiles/text.md`, Lane 09)

1. **Citation locations:**
   - [docs/sources.md](../../docs/sources.md) currently covers `W` (Winnowing), DSSE/in-toto/Sigstore/RFC 3161/C2PA, and AI-origin / classifier sources (SynthID-Text, Anthropic, OpenAI, EU Regulation 2024/1689 + Code of Practice, IPTC, WaterPark, Liang/Weber-Wulff/RAID). It does **not** yet list the three Lane 09 text-carrier source families `U` (Unicode 17.0.0 UAX #15, UTS #39, UAX #29), `N` (Nemecek et al., `arXiv:2610.36432v1`), or `A` (Abdelnabi & Fritz, `arXiv:2009.03015v2`).
   - Instead, `U` is pinned with exact file SHA-256 digests in [profiles/text.md](../../profiles/text.md#4-pinned-unicode-data) (§4, §8), and `U`, `N`, and `A` are catalogued in [lane 09's source ledger](../lanes/09-evidence-review.md#source-ledger).
   - **Non-blocking observation (`S1`):** Add `U`, `N`, and `A` (or a pointer to Lane 09's ledger) to [docs/sources.md](../../docs/sources.md) before candidate release so the central source register covers all negative-result text-mark authorities.

---

## 2. Verification of Unicode carriers (`U`, `N`, and `profiles/text.md`)

1. **UTS #39 `skeleton` and UAX #15 `NFKC` (`U`):**
   - Verified against Unicode Technical Standard #39 (rev. 32, §4) and [profiles/text.md](../../profiles/text.md#8-channels-and-the-fold) §8: `skeleton(X)` applies `NFD`, deletes all code points with `Default_Ignorable_Code_Point = Yes`, maps each remaining code point via `confusables.txt` to its prototype, and reapplies `NFD`. Under UAX #15, `NFKC` decomposes compatibility variants (such as ligatures, fullwidth forms, and mathematical alphanumerics).
   - Independently verified against the repository's pinned Unicode 17.0.0 derived table [text-tables-17.0.0.json](../../test-vectors/extraction-text/text-tables-17.0.0.json) (SHA-256 `49eb0304…`, `4,174` `Default_Ignorable_Code_Point` entries and `6,565` `confusables` mappings) via [check_text_vectors.py](../../test-vectors/extraction-text/check_text_vectors.py):
     - **Zero-width insertion track (`U+200B` ZWSP, `U+200C` ZWNJ, `U+200D` ZWJ, `U+2060` WORD JOINER, plus `U+FEFF`, `U+00AD`, `U+034F`):** All four insertion characters used in `N` are classified `I` (`Default_Ignorable_Code_Point`) and map to empty (`[]`) under `NFKC_CF`, so `fold("ab" + cp + "cd")` returns `"abcd"` and `skeleton("abcd")` returns `"abcd"` (100% erased). Confirmed in [text-plain.json](../../test-vectors/extraction-text/text-plain.json) (`plain-zero-width`, `plain-other-ignorable`).
     - **Compatibility and listed homoglyph substitution track:** Compatibility glyphs (`ﬁnal`, fullwidth `ＦＵＬＬＷＩＤＴＨ`, math bold `𝐡𝐞𝐥𝐥𝐨`) collapse identically under `fold()` (`plain-nfkc-ligature`, `plain-nfkc-compat`). Listed cross-script substitutions (Cyrillic `а, с, о, р, е, х` vs Latin `a, c, o, p, e, x`) collapse identically under `skeleton(folded)` (`plain-confusable-cyrillic` and `plain-confusable-latin` produce identical skeleton hash `0324ac23ec4edf6b`).
     - **Verified nuances (non-blocking, do not alter negative result):**
       1. [profiles/text.md](../../profiles/text.md#8-channels-and-the-fold) applies `skeleton` *after* `fold` (which case-folds), whereas `N`'s canonical fold runs compatibility decomposition + `skeleton` without prior case folding; for example, uppercase Greek `Β` is a confusable of `B` in `skeleton(exact)` but lowercases to `β` → `ß` in `skeleton(folded)`. Either pipeline still erases both the `Default_Ignorable` insertion track and the listed-confusable / compatibility substitution tracks.
       2. As noted in [profiles/text.md](../../profiles/text.md#13-limits-what-the-profile-cannot-detect-or-claim) §13, `32` non-ignorable `General_Category = Cf` code points (such as `U+FFFB`, `plain-format-char-split`) are class `S` and split words instead of being deleted, and unlisted visual lookalikes outside `confusables.txt` are unmapped. Neither offers a viable watermark carrier under standard text handling.

2. **Nemecek et al. (`N`, `arXiv:2610.36432v1`):**
   - Independent check confirms `N` (*No Tokenizer, Still a Gap: Cross-Lingual Fairness of Homoglyph and Invisible-Character Watermarking*) evaluates post-hoc homoglyph substitution and invisible-character insertion across 40 language varieties / 24 scripts, reporting that script choice drives ~96% of capacity variance and that ordinary copy-paste strips invisible insertions (widening detection requirements from ~2 code points in English/Persian to ~93 in Lao).
   - Lane 09's summary of `N` §§4, 6–7 and Appendix E — that `NFKC` alone preserves most cross-script pairs (93% in `N` §6; corrected against the NotebookLM audit in [09-report-audit.md](../lanes/09-report-audit.md)), whereas the combined canonical fold (`NFKC` + UTS #39 `skeleton` + delete `Default_Ignorable`) erases the mark across all tested languages, and that keying on raw unnormalized characters failed under attack — accurately matches both the primary source and the "cheap normalization erases the signal" failure mode (`M2E.1`, `SYN.3`).

---

## 3. Verification of AWT lexical rewriting rejection (`A`)

- Independent check of Abdelnabi & Fritz (*Adversarial Watermarking Transformer: Towards Tracing Text Provenance with Data Hiding*, IEEE S&P 2021, `arXiv:2009.03015v2`, `S-Abdelnabi/awt`) confirms:
  1. **Alters author wording:** AWT uses an end-to-end transformer encoder-decoder to make automated word substitutions on existing prose (evaluated on WikiText-2 with 4-bit binary messages over ~80-word segments, with SBERT and METEOR used to measure meaning/fluency changes and ~49.9% decoder bit accuracy on unmarked text).
  2. **Low unauthenticated raw capacity:** ~4 raw bits per ~80 words (~50 bits per 1,000 words) before error-correction, versioning, or authentication framing leaves negligible capacity for a verifiable provenance payload.
  3. **Licensing and external model dependencies:** `S-Abdelnabi/awt` has no formal open-source `LICENSE` file in its repository root and relies on external pre-trained checkpoints (AWD-LSTM, InferSent/GloVe, SBERT). (Minor detail noted during source verification: `S-Abdelnabi/awt` documents downloading those base checkpoints from upstream repositories in addition to author-hosted weights; this does not change the rejection.)
- **Conclusion on `A`:** Lane 09's rejection of AWT as an embedded-mark candidate is sound.

---

## 4. Gate `TXT.8` conclusion

- **Unicode carriers (`N`, `U`):** Confirmed **`negative-result`**. The declared deterministic fold (`NFKC` + UTS #39 `skeleton` + delete `Default_Ignorable_Code_Point`) erases homoglyph and zero-width carriers by construction.
- **Lexical rewriting (`A`):** Rejection confirmed.
- **Owner gate:** No new text-mark experiment was executed; any future text-mark experiment remains owner-blocked in [ROADMAP.md](../../ROADMAP.md#owner-blocked-gates).
