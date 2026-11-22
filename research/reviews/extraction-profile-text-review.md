# Review: text extraction profile (`text-plain`, `text-markdown`, draft-1)

Status: independent clean-room review, 2026-11-22, of [extraction-profile-text.md](../drafts/extraction-profile-text.md) and [extraction-vectors-text/](../drafts/extraction-vectors-text/README.md) at commit `6fbf11b` (branch `roadmap-v2`). I wrote neither and did not trust their self-reported checks. Scratch code (`clean.py`, `variants.py`, `runvar.py`) is in `$TMPDIR/tx/`, not in the repository.

**Verdict: ready after listed fixes.** Implement `text-plain` first. `text-markdown` needs the list-item fence decision (M1) before implementation. Neither profile can enter a catalogue or report until the contract amendment in §4 exists.

## 1. Clean room

**Method.** I wrote a roughly 400-line extractor from the profile text and the six pinned Unicode 17.0.0 files only (fetched from unicode.org; all six SHA-256 digests match profile §4). It covers classes, the token rule, the Markdown masks, NFD/NFC with Hangul, NFKC_CF over NFD, the separator filter, the UTS #39 skeleton, contract §7–§8 hashing and winnowing, configuration validation and the input checks. I did not open `check_text_vectors.py`, `harness/build_vectors.py` or the derived table until the results below were recorded.

**Result: 71/71 vectors identical on the first run** (50 plain, 18 Markdown, 3 limits): status, error code and offset, tokens (text, span, folded, skeleton), `masked`, and all three channel blocks. 12/12 negative configurations are rejected and 2/2 boundary configurations accepted. My NFC/NFD agree with all 20,034 lines of `NormalizationTest.txt` 17.0.0. The text is precise enough to reproduce the vectors without the author's code; that is the main positive finding.

**Guesses. Each is an ambiguity finding, even though it matched.**
- **T-G1 (matters): the record wire format is not in the profile** (§10: "the wire names belong to TW-03"). I took it from the vector README: top-level channel blocks, no `tokenCount`, no token `class`, per-token `folded`/`skeleton`. TW-03 has since fixed a different canonical record (A1; see §4).
- **T-G2:** the bounds `k ≤ 16`, `window ≤ 128`, `maxInputBytes ≤ 8 MiB` are cited from contract §10a, not restated, though validation step 5 needs them.
- **T-G3:** I read the invalid-UTF-8 offset as the maximal-subpart start (D92/§3.9); the surrogate, overlong and truncated vectors agree.
- **T-G4:** the skeleton is applied once (steps 1–4), not until stable. No vector distinguishes the two (§2).

Everything else, including the Markdown edge cases in §3, is decided by the text.

## 2. Wrong-but-plausible implementations against the checker

Each variant's results replaced every vector result in a copy of the vector directory, and the unmodified checker ran on it. **25 variants: 20 rejected, 5 accepted.**

| Variant | Checker | First vector that differs (or why it passes) |
| --- | --- | --- |
| UAX #29-style words: MidLetter/MidNumLet/MidNum joins, `_` joins, ZWSP splits | rejected | `plain-zero-width`, `plain-punct-a/-b`, `plain-numbers` |
| NFKC without case folding | rejected | 45 vectors (`plain-short`) |
| NFKC + simple lowercase (no full folding) | rejected | `plain-casefold-expansion`, `plain-greek`, `plain-cherokee` |
| Library drift: x/text-style Cherokee left unfolded | rejected | `plain-cherokee` only |
| **Library drift: Python `unicodedata` 16.0 NFKC + `str.casefold`** | **ACCEPTED** | Equals the pinned fold on every 16.0-assigned W/C code point, but 4,699 W/C code points are new in 17.0, and no vector contains one |
| Confusables applied before NFKC_CF (skeleton of `exact`, then fold) | rejected | 17 vectors (`plain-upper`: `survlve`) |
| **Skeleton iterated to a fixed point** | **ACCEPTED** | Differs only on code points such as U+048B, which folds to itself (single pass `й̦`, iterated `ᴎ̦̆`). No vector contains one |
| ZWSP as a separator (OD-T8′ b) | rejected | `plain-zero-width`, `plain-zwsp-as-separator` |
| Every ignorable splits words | rejected | `plain-zero-width`, `plain-other-ignorable`, `plain-bidi` |
| Ideograph runs as one token | rejected | `plain-chinese`, `plain-japanese` |
| Apostrophe joins (`it’s`) / hyphen joins / decimal joins (`3.14`) | rejected ×3 | `plain-punct-a`, `plain-numbers`, `plain-hyphenation-wrap` |
| Fold without the leading NFD / without the separator filter | rejected ×2 | `plain-combining-a` / `plain-nfkc-compat` |
| CommonMark-like: entities and autolinks rendered, not masked | rejected | `md-syntax`, `md-entities` |
| CommonMark indented code blocks masked | rejected | `md-indented-code` |
| **CommonMark HTML blocks: a line starting with a tag masked whole** | **ACCEPTED** | No vector has text on a line that starts with a tag (§5 lists the deviation but pins it nowhere) |
| Fence closes only on equal length / unclosed fence masks nothing | rejected ×2 | `md-fence` / `md-fence-unclosed` |
| Front matter ignored / link reference definitions ignored | rejected ×2 | `md-front-matter`, `md-link-reference` |
| BOM rejected as `bom` (OD-T4′ b) | rejected | `plain-bom` |
| **BOM stripped before the Markdown masks** | **ACCEPTED** | No vector combines a BOM with Markdown front matter (§3) |
| **CommonMark list-item fences (`1. ```` opens a fence)** | **ACCEPTED** | No vector has a fence after a list marker (§3) |

**Fixes, one vector each:** a word containing a 17.0-new letter such as U+0C5C (16.0 data classes it S and splits the word) plus a 17.0-new ideograph; U+048B for the single-pass skeleton; `<div>` LF `text` LF `</div>`; a BOM before `---` front matter; a list-item fence. The 64 shipped rejections mutate a vector's own result, so they cannot catch an implementation that is wrong only on inputs no vector contains.

## 3. Markdown: is a fixed mask list deterministic and adequate?

**Deterministic: yes.** The text decided all 17 inputs I constructed: nested fences of different lengths (inner ```` ``` ```` does not close ```` ```` ````); `~~~` inside a backtick fence; indented code (tokenized); tab indentation; multi-line link reference definitions (the first line masked, URL and title on the next line tokenized); `[a\]b]:` (not a definition) and `[ ]:` (masked); unknown entity names and `&#1234567;` (masked); a `-->` on a later line, including one that swallows a fence opener; an unclosed `<!--` followed by a later comment; CR-only line endings (one line, so no front matter); TOML `+++` (not front matter); tags split across lines (not masked). Literal implementers will agree. Disagreement comes from implementers who "fix" the text toward CommonMark, which is what the accepted variants in §2 do.

**Adequate: not yet.** These are decided but wrong for real documents:
- **M1 (high): list-item fences invert masking.** In `1. ```` LF `   code` LF `   ```` LF prose, the opener is not a fence, because a list marker precedes it. The code is tokenized, and the indented closing ```` ``` ```` (3 spaces) *opens* a fence that masks the rest of the document. Fenced code inside numbered or bulleted lists is common in READMEs. Fix: allow an optional list marker (`[-*+]` or `[0-9]{1,9}[.)]`, then spaces) before the opener, and add the vector. Or declare the inversion as a limit with a vector; I do not recommend that.
- **M2 (medium): a BOM disables front matter** (`plain-bom` accepts a BOM, but MD-1 requires the first line to be exactly `---`). A BOM'd Markdown file therefore has its YAML tokenized. Fix: MD-1 skips a leading U+FEFF.
- **M3 (low): code-span contents are not literal.** In `` `&amp;` ``, `` `<b>` `` and `` `[x](y)` `` the entity, tag and destination are masked. §5 says code-span contents are "kept as prose", which these cases contradict. State it as a deviation.
- **M4 (low, unlisted deviations):** `<script>`/`<style>` bodies are tokenized; blockquote fences (`> ````) are not recognized; `<!-->` is not a complete comment (it is in CommonMark 0.31.2); `[ ]:` with a blank label is masked. Add them to the §5 list.

## 4. Three values against the shared contract and the canonical record

It does **not** fit without amendment. The catalogue and report contract (draft-2 with A1, [catalogue-report-contract.md](../drafts/catalogue-report-contract.md)) hard-codes the code channels:
- **Record (A1):** "`channels` is `exact` then `normalized` … the normalized channel has `values` first". Tokens are `class`, `text`, `span`, and `tokenCount` is required. The text vectors have top-level channel blocks, no `tokenCount`, no `class`, extra per-token `folded`/`skeleton` and, for Markdown, `masked`. So A1 records cannot be derived from them "without new hand work".
- **Catalogue §3.2 and `catalogue.schema.json`:** `channels` must hold exactly `exact` and `normalized`; `extractionConfig.channels` and `.contract` are constants; the §3.6 step 5 profile list has only the two code profiles; error codes follow extraction §4.8/§5.9.
- **Comparison config §4 and report schema:** `modes` is exactly `["exact","normalized"]`, and the mode object keys and `suppression.distinctHashes` keys are fixed.

**Amendment needed, stated exactly:**
1. **Record:** `channels` lists the configuration's channels in configuration order, each non-`exact` channel with `values` first. A token is `class`, `text`, `span` (class `word` for text). Either drop the per-token `folded`/`skeleton` (they duplicate channel `values`) or add them to A1. `tokenCount` is required; `text-markdown` adds `masked` after `tokens`.
2. **Catalogue:** `extractionConfig.contract` is `traceweave-token-winnow-draft-1` or `traceweave-text-winnow-draft-1`, each fixing its channel list. Artifact `channels` keys equal `extractionConfig.channels`. Step 5 adds `text-plain`/`draft-1` and `text-markdown`/`draft-1`, with errors `invalid-utf8`, `nul`, `input-too-large`.
3. **Comparison:** `modes` is a non-empty ordered subset of the catalogues' channels (e.g. `["folded"]` or all three). §5.3 rule 4 becomes "each mode runs on the channel of the same name". The report's `modes` and `suppression.distinctHashes` keys follow `modes`. The configuration bytes change, so this needs a new comparison id.

The alternative is to rename `folded` to `normalized` and drop the skeleton. That changes every text hash, loses the homoglyph channel (OD-T5), and is not recommended.

## 5. k = 8, w = 8 and the stated limits against lane 09

**The rationale is honest.** P's 8-word shingles and W's 50 characters (≈ 8 words, labelled an inference) are reference points, not measurements; K is correctly qualified as BM25 retrieval; the values are named experimental inside `configSha256`, pending OD-T7. On `docs/use-cases.md` (3,639 tokens) my extractor selects 808 of 3,632 folded k-grams (0.222), matching `2/(w+1)`. The §13 limits cite vectors or sources, and none claims a rate.

**Insertion-interval evasion (09 audit, "insert a distractor every w + k − 2 words").** I inserted `zq` every N tokens into `docs/use-cases.md` and extracted with `text-markdown`:

| N | Words added | Distinct folded fingerprint hashes shared | Distinct folded k-gram hashes shared |
| --- | --- | --- | --- |
| 30 | +121 | 582/807 | 2773/3617 |
| 15 | +242 | 349/807 | 1938/3617 |
| **14 = w + k − 2** | +259 | **326/807** | 1815/3617 |
| 8 = k | +454 | 67/807 | 454/3617 |
| **7 = k − 1** | +519 | **0** | **0** |

Spacing at w + k − 2 removes only the *guarantee*: 40% of fingerprints are still shared. Removing every shared k-gram needs an edit in every run of k tokens, here one inserted word per 7 (+14%). Profile §13 ("removes the guarantee") is correct. [09-evidence-review.md](../lanes/09-evidence-review.md) line 124 and the 09 audit's "What survives" item 2 call w + k − 2 the "cheapest removal", which overstates it; fix both to "defeats the guarantee; full removal needs spacing ≤ k − 1", and record this table under TXT.7.

**A new evasion the limits miss.** 32 format characters are `Cf` but not Default_Ignorable, hence class S: U+0600–0605, U+06DD, U+070F, U+0890–0891, U+08E2, U+FFF9–FFFB, U+110BD, U+110CD, U+13430–1343F. `pas`+U+FFFB+`sages` gives `pas`, `sages` in every channel, and U+FFF9–FFFB and U+13430–1343F commonly render invisibly in Latin text. So "zero-width insertion cannot split words" (OD-T8) holds only for Default_Ignorable code points. Fix: a §13 limit with a vector, or class the invisible ones as I (a profile change).

## 6. Open decisions, staging, and fixes

**Settle before implementation (my recommendation in brackets):**
- **OD-T1′** [(a) masks, with M1 and M2 fixed; a CommonMark parser needs a span rule per rendered node, which no reference supplies]; **OD-T3′** [(a), with Thai/Lao/Khmer/Myanmar a measured TXT.7 limit]; **OD-T4′** [(a) accept, with the M2 fix].
- **OD-T5′** [(a) always three channels, if the §4 amendment lets comparisons choose modes; otherwise (b)]; **OD-T8′** [(a), plus the §5 Cf limit].
- **OD-T12** [keep result-mutation rejections, and add a rejected *input* wherever one exists: NUL, invalid UTF-8, a BOM under OD-T4′ b].
- **New:** the §4 contract amendment (blocking for any catalogue or report); the single-pass skeleton pinned with U+048B; a 17.0-new-character vector so a Unicode 16.0 library cannot pass.

OD-T6′, OD-T11 and OD-T13 can wait; OD-T7 waits for TXT.4/TXT.6 by design.

**Stage `text-plain` first: yes.** It has no Markdown rules, was reproduced exactly from the text, and its only accepted wrong variants (Unicode 16.0 drift, iterated skeleton) are closed by two vectors. Profile names separate the hashes, so adding `text-markdown` later breaks nothing; until then `.md` files extracted as plain text keep URLs and tag names as tokens (`plain-md-syntax`), acceptable for Stage 1.

**Blocking:** the §4 amendment; the M1 list-item fence rule and its vector, before `text-markdown`; the five vectors of §2. **Non-blocking:** the M2–M4 deviations, the Cf limit, the lane 09 wording, and restating the §10a bounds in profile §11 (T-G2).
