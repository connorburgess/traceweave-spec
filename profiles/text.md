# Draft text extraction profile: `text-plain` and `text-markdown`

Status: experimental draft, normative for conformance of this draft version; decided-in-draft items confirmed by the owner's delegation on 2026-11-23.

Profiles in this document: **`text-plain` is frozen for stage-1 implementation** (draft-1). **`text-markdown` is a draft and is not normative** until it is re-reviewed.

Revision status (before promotion): **revised after the [clean-room review](../research/reviews/extraction-profile-text-review.md), 2026-11-22. `text-plain` is version `draft-1`, staged first and frozen for stage-1 implementation (§17); `text-markdown` is version `draft-2` and stays a draft until it is re-reviewed.** Both are decided in draft, pending owner confirmation. Roadmap gates TXT.1 (profile) and TXT.2 (hand-derived vectors), started under the 2026-11-22 owner override for fingerprint-only text work. It serves the proposed [UC-8](../docs/use-cases.md#proposed-uc-8-find-reused-passages-in-prose), whose wording still awaits the owner (TXT.0). The evidence comes from [lane 09](../research/lanes/09-evidence-review.md).

This document is normative for conformance of this draft version, as stated in its status line. "MUST" describes what this draft proposes for an implementation claiming to follow it. Nothing here is a registered algorithm. The vectors, checker, tables and cross-check are in [extraction-text/](../test-vectors/extraction-text/README.md).

**What it is.** A deterministic extractor that turns UTF-8 prose into word tokens, gives each token an exact value, a folded value and a confusable skeleton, and winnows k-grams of each channel. Every token carries the half-open byte span of its **original** bytes. It extracts a fingerprint and does not embed or detect a mark. Lane 09 found no text mark ready to test.

## 1. Relation to the draft extraction contract

The profile is a new lexer front end hosted by the [draft extraction contract](../spec/extraction.md) (revision draft-1, amended). Lane 09 [listed](../research/lanes/09-evidence-review.md#how-the-extraction-contract-could-host-a-text-profile) what such a front end must specify.

**Reused unchanged:**
- **Outcomes** ([§2](../spec/extraction.md#2-outcomes)): `ok` (at least k tokens), `insufficient-tokens` (abstention, not an error) and `error`. There are no partial results and no repair, and no catch-all error code exists.
- **Processing order and error offsets** ([§2](../spec/extraction.md#2-outcomes), [§3](../spec/extraction.md#3-processing-order-and-input-bytes)): configuration, then size, then strict UTF-8 (Unicode 17.0.0 D92), then forbidden code points, then tokens. The size check happens before reading where possible.
- **Spans:** half-open `[start, end)` byte offsets into the original input, never splitting a UTF-8 sequence.
- **k-gram hashing** ([§7](../spec/extraction.md#7-k-grams-and-hashing)): the same length-prefixed layout and `sha256-first8-u64be`, unkeyed. Only the domain string and the class string differ (§9).
- **Winnowing** ([§8](../spec/extraction.md#8-winnowing-selection)): rightmost minimum, a partial window when 1 ≤ m < w, every selected position kept.
- **The record's logical fields** ([§9](../spec/extraction.md#9-extraction-record-logical-fields)), including the `null` rules for `unsupported-config` and `input-too-large`. The record bytes are the catalogue and report contract's canonical extraction record ([§2a](../spec/catalogue-report.md#2a-extraction-record-traceweave-extraction-record-draft-1)) with this profile's declared channel list ([§2b, amendment A3](../spec/catalogue-report.md#2b-declared-channel-lists-amendment-a3)); see §10.
- **Configuration bytes, validation steps 1–5 and 8, and bounds** ([§10](../spec/extraction.md#10-configuration-record), [§10a](../spec/extraction.md#10a-resource-bounds-and-complexity)): `k ≤ 16`, `window ≤ 128`, `maxInputBytes ≤ 8 MiB`, linear time and memory.

**Different from the code profiles, deliberately:**
- A BOM is accepted (§3).
- An isolated CR is not an error.
- There are three channels, `exact`, `folded` and `skeleton`, instead of `exact` and `normalized` (§8).
- The contract and domain strings are new (§9, §11).

## 2. Scope and profiles

**In scope:** UTF-8 plain text and Markdown prose in any script, as reference or candidate documents for UC-8.

**Out of scope:**
- Other encodings, which are rejected as `invalid-utf8`, not transcoded.
- HTML, PDF, word-processor and other rich formats. A converter may produce UTF-8 text first, but the spans then refer to the converter's output, not to the original file.
- Code. Use the code profiles. Fenced code inside Markdown is masked (§5).
- Paraphrase, translation, cross-language matching, stemming and stop words (§13).

**Two profiles, one per front end:**

| Profile | Front end | Use |
| --- | --- | --- |
| `text-plain` | None: every code point is text | `.txt` and any prose where `<`, `&` and `](` are content |
| `text-markdown` | The Markdown masks of §5, then the same tokenizer | `.md`, and any document compared with a Markdown one |

The profile name is inside every k-gram hash, so fingerprints from different profiles never match. **To compare a Markdown document with plain text, extract both with `text-markdown`.** Plain prose rarely contains the masked constructs, so this costs little. Vectors `md-syntax` and `md-stripped` (its plain rendering) give identical hashes in every channel under `text-markdown`. `plain-md-syntax` shows the same bytes under `text-plain`, where the URLs, tag names and entity names become tokens.

## 3. Input rules

Processing follows contract §3 steps 0–2 unchanged. Step 3 (forbidden code points) is replaced by the following:

- **U+0000 is forbidden**: `nul` at the earliest NUL. Text never contains it, and this keeps binary files out. Order is still encoding first: `plain-err-nul-then-invalid` (NUL at 0, invalid byte at 7) is `invalid-utf8`@7.
- **The BOM is accepted** (decided in draft as OD-T4′ (a), pending owner confirmation; the rejected alternative was to reject it as `bom`, like the code profiles). U+FEFF is Default_Ignorable_Code_Point, so at offset 0 it never starts a token, and inside a word it is transparent (§7). Spans keep original offsets, so the first token after a BOM starts at 3 (`plain-bom`), and the token sequence equals the BOM-less file's (pair with `plain-reflow-a`). Text editors write BOMs routinely (lane 09), and rejecting them would make many real files unusable. The code profiles reject a BOM (contract OD-1) because there it can shift offsets in a lexer. Here nothing shifts, because spans index the original bytes.
- **CR, CRLF and every other C0/C1 control except NUL** are separators (§6). There is no `isolated-cr` error.
- **Noncharacters, private-use and unassigned code points** are accepted as separators. Unassigned code points inside Default_Ignorable ranges (for example U+2065) are ignorable (§6).

**Closed error list:** `invalid-utf8`, `nul` and `input-too-large`, plus `unsupported-config` from §11. Offsets follow contract §2: `input-too-large` is at 0, `nul` at the NUL, and `unsupported-config` is `null`. The `invalid-utf8` offset is the first byte of the first maximal subpart of an ill-formed subsequence (Unicode 17.0.0 §3.9, D92/D93b): the byte at which a strict left-to-right decoder first fails. So a lone continuation byte, an overlong lead, the lead of an encoded surrogate and the lead of a truncated sequence are each reported at their own first byte (`plain-err-lone-continuation`@4, `-overlong`@0, `-surrogate`@3, `-truncated`@4, `-above-max`@0). The Markdown front end and the tokenizer cannot fail: every well-formed, NUL-free input yields `ok` or `insufficient-tokens`. **Abstention** is `insufficient-tokens`, meaning fewer than k tokens, including zero. The tokens are still listed.

## 4. Pinned Unicode data

Everything is evaluated with **Unicode 17.0.0** data, the version the contract pins (§3a). The authority is these six files; the first four are the contract's files and digests:

| File | SHA-256 | Used for |
| --- | --- | --- |
| `ucd/UnicodeData.txt` | `2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c` | General_Category (§6); canonical decompositions and combining classes (NFD, NFC) |
| `ucd/DerivedCoreProperties.txt` | `24c7fed1195c482faaefd5c1e7eb821c5ee1fb6de07ecdbaa64b56a99da22c08` | Default_Ignorable_Code_Point (§6) |
| `ucd/DerivedNormalizationProps.txt` | `71fd6a206a2c0cdd41feb6b7f656aa31091db45e9cedc926985d718397f9e488` | **NFKC_CF** (the fold mapping, §8); Full_Composition_Exclusion (NFC) |
| `ucd/CompositionExclusions.txt` | `2f239196ef3b5b61db5cc476e9bd80f534d15aa1b74e1be1dea5d042a344c85f` | Checked to be a subset of Full_Composition_Exclusion |
| `ucd/PropList.txt` (new) | `130dcddcaadaf071008bdfce1e7743e04fdfbc910886f017d9f9ac931d8c64dd` | Ideographic (§6); White_Space (checked to be all separators) |
| `security/confusables.txt` (new) | `091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a` | Skeleton prototypes (UTS #39 §4, §8) |

The UCD files are under [unicode.org/Public/17.0.0/ucd](https://www.unicode.org/Public/17.0.0/ucd/), and `confusables.txt` is under [unicode.org/Public/17.0.0/security](https://www.unicode.org/Public/17.0.0/security/). The second copy of `confusables.txt` at `Public/security/latest/` already differs (dated 2026-08-06, SHA-256 `6ed3ee96…`). That is the data instability UTS #39 §4 warns about, and the reason the version and digest are pinned rather than "latest".

[`harness/gen_text_tables.py`](../test-vectors/extraction-text/harness/gen_text_tables.py) refuses files with other digests and derives [`text-tables-17.0.0.json`](../test-vectors/extraction-text/text-tables-17.0.0.json) byte for byte (SHA-256 `49eb0304ece1f9351f4db79ddf853fdc3bce353d4a833f7c4f9424bf80ae53f4`). It holds the three class sets, White_Space, combining classes, canonical decompositions, Full_Composition_Exclusion, the NFKC_CF mapping and the confusable prototypes.

An implementation MUST use tables generated from these files, or the committed derived table. **It MUST NOT use a runtime's or library's case folding or normalization unless that is shown to equal these tables.** The cross-check (§14) found:
- **golang.org/x/text v0.39.0 `cases.Fold` differs from NFKC_CF on all 86 Cherokee small letters**, U+13F8–U+13FD and U+AB70–U+ABBF. UCD 17.0.0 folds them to the capitals; x/text leaves them unchanged. Vector `plain-cherokee` pins this.
- **Python 3.14.6's `unicodedata` is Unicode 16.0.0.** It is unusable here, and the checker does not import it.
- **The Rust `caseless` 0.2.2 crate is Unicode 16.0.0.** It is unusable here.
- **Go x/text `norm` has 17.0.0 tables only under the `go1.27` build tag** (the contract notes the 15.0.0 fallback).

## 5. Markdown front end (`text-markdown` only)

**Decided in draft, pending owner confirmation (OD-T1′ (a), the reviewer's recommendation): a fixed set of masks, not a CommonMark parse.** This section is `text-markdown` **draft-2**: the list-item fence and BOM rules below changed from draft-1 (§18).
- **Masked ranges** are byte ranges of the original input. Every code point in them is treated as a separator (§6). Nothing is deleted, decoded or rewritten.
- **Reference.** [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/) is the pinned reference: it names the constructs below, and the deviations from it are listed in this section.
- **Why not a parser.** A full parse would make the token stream depend on two parsers agreeing over the whole CommonMark grammar. It would also need a source-span rule for every rendered text node, including decoded entities, which CommonMark does not define.
- **What the masks cover.** All other Markdown syntax is ASCII punctuation, so it is already a separator under §6. That covers emphasis, headings, block-quote markers, list bullets, table pipes and alignment rows, thematic breaks, backslash escapes, and code-span backticks. Code-span contents are scanned like any other inline text: words in them are tokens, and the masks below still apply inside them (a stated deviation, below).

**Lines.** A line is a maximal run of bytes without LF. Its *content* is the line without one trailing CR; the rules below match against content. **Masking a line** masks all of its bytes, including a trailing CR, but not the LF that ends it. "Up to 3 spaces" means 0–3 U+0020 characters; a TAB does not count as indentation.

The masks are applied in this order:

1. **MD-1 front matter.** The content of the first line, after skipping one leading U+FEFF if present, must be exactly `---`. The mask then starts after the BOM, at offset 3 (`md-bom-front-matter`); draft-1 did not skip the BOM. If a later line's content is exactly `---` or `...`, mask from the start of the `---` (offset 0, or 3 after a BOM) through the end of that line, including its CR but not its LF (`md-front-matter-crlf`). Otherwise there is no front matter, and `---` is punctuation (`md-front-matter`, `md-front-matter-unclosed`).
2. **Line scan** over the remaining lines, with a state that is either *normal* or *in fence (c, n)*:
   - **MD-2 fenced code.** In *normal* state, at a line start, a line whose content matches this pattern opens a fence: up to 3 spaces; then optionally a **list marker** (`-`, `*` or `+`, or 1–9 ASCII digits followed by `.` or `)`) followed by 1–4 spaces; then a run of n ≥ 3 backticks or n ≥ 3 tildes. A backtick fence additionally requires no backtick in the rest of the line. Let e be 0 without a list marker, and otherwise the number of bytes before the fence run on the opening line. The whole opening line, including any list marker, is masked, and the state becomes *in fence (c, n, e)*. In that state every line is masked. A line whose content is at most 3 + e spaces, a run of c with length ≥ n, then only spaces and tabs, closes the fence; it is masked too. An unclosed fence masks to end of input (`md-fence`, `md-fence-unclosed`, `md-list-fence`). Draft-1 had no list marker and e = 0, which inverted masking in lists: the indented closing line opened a fence that masked the rest of the document (review M1).
   - **MD-3 link reference definition.** In *normal* state, at a line start, a line whose content matches up to 3 spaces, `[`, a first label character that is neither `]` nor `^`, any further characters other than `]`, then `]:`, is masked whole. Footnote definitions (`[^…]:`) are not masked (`md-link-reference`).
   - **Inline scan** of any other line, left to right from its start, or from a resume point. At each position the first matching rule applies:
     - **MD-4 HTML comment.** `<!--`: find the first `-->` starting at or after the position plus 4, anywhere later in the input. If found, mask through it and resume after it. If that is on a later line, continue that line's inline scan without the line-start rules. If not found, the `<` is ordinary, and no later `<!--` can close either (`md-html-comment`, `md-html-comment-unclosed`).
     - **MD-5 tag or autolink.** `<`, an optional `/`, then an ASCII letter. Scan forward on the same line to the first `<`, `>` or end of line. If that is `>`, mask from `<` through `>`. This covers HTML tags and autolinks such as `<https://example.org/x>` (`md-angle-brackets`).
     - **MD-6 link or image destination.** `](`: mask from the `(` through its matching `)`. Matching uses depth counting of `(` and `)` on the same line, without escape handling. If the `(` is not closed on its line, nothing is masked (`md-link-nested-parens`).
     - **MD-7 character reference.** `&` followed by `[A-Za-z][A-Za-z0-9]{0,31};`, `#[0-9]{1,7};` or `#[xX][0-9A-Fa-f]{1,6};` is masked. It is **not decoded** (`md-entities`).
     - Otherwise advance one code point.
3. **Result.** The masked ranges are sorted and merged. Vectors list them as `masked`.

**Complexity.** The pass is linear:
- MD-4 remembers a failed `-->` search.
- MD-5 stops at the next `<`, so every byte is scanned a bounded number of times.
- MD-6 can be computed with one stack per line that pairs each `(` with its `)`.

**Deviations from CommonMark 0.31.2.** These are measured against pulldown-cmark 0.13.5's text content in §14: 11 of 19 Markdown vectors give the same folded token sequence. Each of the 8 that differ is explained by an item below.
- Ordered-list numbers are tokens (`1. First item` gives `1`; `md-syntax`, `md-stripped`, `md-list-fence`). CommonMark renders the number as list markup.
- Autolinks are masked (`md-syntax`). CommonMark renders the URL as the link text.
- Reference-style link labels are tokens (`[guide][g]` gives `g`; `md-link-reference`).
- Character references are masked, not decoded, so `Caf&eacute;` gives `caf`, not `café` (`md-entities`).
- Indented code blocks are not recognized (`md-indented-code`).
- HTML blocks are masked only tag by tag, so text between tags remains (`md-html-block`). CommonMark hides the whole block through the next blank line; this profile keeps prose that sits between tags.
- Front matter is not CommonMark at all. pulldown-cmark's metadata extension does not recognize it after a BOM, while MD-1 does (`md-bom-front-matter`).
- Code-span contents are not literal: in `` `&amp;` ``, `` `<b>` `` and `` `[x](../research/drafts/y)` `` the entity, tag and destination are masked (review M3).
- `<script>` and `<style>` bodies are tokenized; only the tags are masked.
- Fences inside block quotes (`> ````) are not recognized.
- `<!-->` and `<!--->` are not complete comments: the `-->` search starts 4 bytes after `<`. CommonMark 0.31.2 accepts them.
- A link reference definition with a blank label (`[ ]:`) is masked; CommonMark does not accept a blank label. Multi-line definitions are masked on their first line only.
- Fences indented 4 or more spaces without a list marker on the same line are not recognized, and a list item's fence closer may be indented up to 3 more spaces than the opener's fence column, where CommonMark measures from the list item's content column.
- Setext and other block structure is irrelevant, since its syntax is punctuation.

## 6. Character classes

Each code point of the original input is in exactly one class, from the pinned tables:

| Class | Definition (in this order) |
| --- | --- |
| **I** ignorable | Default_Ignorable_Code_Point = Yes (4,174 code points, including ZWSP, ZWNJ, ZWJ, WORD JOINER, SOFT HYPHEN, U+FEFF, CGJ, variation selectors, TAG characters, bidi marks, embeddings, overrides and isolates, Hangul fillers, U+180E) |
| **C** ideograph | Not I, and Ideographic = Yes (110,943 code points: Han, CJK compatibility ideographs, Tangut, Nushu, Khitan, U+3006, U+3007, U+3021–U+3029, …) |
| **W** word | Not I and not C, and General_Category in Lu, Ll, Lt, Lm, Lo, Mn, Mc, Me, Nd, Nl or No (38,929 code points) |
| **S** separator | Everything else: White_Space, P\*, S\*, Z\*, Cc, Cf not in I, Co, Cn not in I; and every code point inside a Markdown mask |

The generator asserts that every White_Space code point is S. The underscore (Pc), apostrophes, hyphens, U+00B7 and U+2044 FRACTION SLASH are S. Combining marks are W, including virama and Indic vowel signs. Kana, Hangul and Thai letters are W, and so is U+02BC MODIFIER LETTER APOSTROPHE.

## 7. Token rule

Scan the input's code points left to right:
- **S or I:** skip it.
- **C:** emit a one-code-point token and continue after it.
- **W:** start a token. Extend it over any following W, also crossing I code points when a W follows them. In effect a token is the regular expression `W (I* W)*`, taken longest. Its span runs from the first W's first byte to the last W's last byte. I code points inside a token are part of its span and exact text. Leading and trailing ones are not.

Every token is class `word`. A W token never contains S or C, and a C token is exactly one code point.

**Consequences, each with a vector.**

| Case | Behavior | Vector |
| --- | --- | --- |
| White space, line wrapping and reflow (any White_Space, CRLF, tabs, runs) | Separators only: the token sequence is identical, spans differ | `plain-reflow-a`/`-b`, `plain-crlf` (identical hashes in every channel) |
| Zero-width and other Default_Ignorable inside a word | Transparent: one token; exact text keeps them, folded deletes them | `plain-zero-width`, `plain-other-ignorable`, `plain-bom` |
| ZWSP used *as* a word separator | Joins the words (`alpha`+ZWSP+`beta` is one token) | `plain-zwsp-as-separator` (limit) |
| A format character that is not Default_Ignorable (U+FFFB, U+0600, …) inside a word | Splits it, since it is S | `plain-format-char-split` (limit) |
| Apostrophes, ASCII `'` and U+2019 | Separate: `it’s` and `it's` both give `it`, `s` | `plain-punct-a`/`-b` (identical hashes in every channel) |
| Hyphens and dashes | Separate: `well-known` gives `well`, `known` | `plain-punct-a` |
| Hyphenation at a line end (`exam-`, LF, `ple`) | Two tokens `exam`, `ple`, unlike the reflowed `example`. A SOFT HYPHEN is transparent instead | `plain-hyphenation-wrap` (limit) |
| Numbers | Digit runs; `.`, `,` and `-` separate: `3.14` gives `3`, `14`; `1,000` and `1.000` both give `1`, `000`; dates give three tokens | `plain-numbers` |
| Non-ASCII digits | Word characters, not mapped to ASCII (NFKC keeps Arabic-Indic digits) | `plain-numbers` |
| Scripts with spaces (Latin, Greek, Cyrillic, Arabic, Hebrew, Devanagari, Hangul, …) | Words as delimited by spaces and punctuation; marks stay in the word | `plain-greek`, `plain-rtl-and-indic`, `plain-hangul` |
| Han and other Ideographic characters | One token per ideograph | `plain-chinese`, `plain-japanese` |
| Kana between ideographs | One token per run (`しています`) | `plain-japanese` |
| Thai, Lao, Khmer, Myanmar and other scripts without spaces or ideographs | One token per space- or punctuation-delimited run; no dictionary segmentation | `plain-thai` (limit) |
| A combining mark after a separator | Starts a token (`́abc`) | `plain-combining-a` |
| Mixed direction | Spans are in logical (memory) order; bidi controls are ignorable | `plain-bidi` |

**Why not UAX #29.** Lane 09 offered "UAX #29 word boundaries or a simpler declared rule (maximal letter/number runs)", and this rule is the simpler one, chosen for these reasons:
1. It needs only three pinned properties (General_Category, Default_Ignorable_Code_Point and Ideographic) rather than the Word_Break property, ExtendedPictographic and the 17 WB rules.
2. Apostrophes (MidNumLet) and decimal separators (MidNum) separate. So straight and curly apostrophes give identical tokens, and `1,000` equals `1.000`. UAX #29 keeps `it’s` and `3.14` whole.
3. It handles ideographs explicitly. UAX #29 leaves runs of Thai and similar scripts unsegmented, which is the same limit this rule has.
4. Default_Ignorable code points are transparent everywhere. UAX #29 WB4 ignores only Extend/Format/ZWJ after a character.

UAX #29 (unicode-segmentation 1.13.3, Unicode 17.0.0) gives the same spans on 31 of 44 plain-profile vectors. §14 lists the 13 that differ, and each follows from the points above.

## 8. Channels and the fold

Every token has three values. They share one token stream and one span list:

| Channel | Value |
| --- | --- |
| `exact` | The original text, `input[start:end]`, including any internal ignorables |
| `folded` | `fold(exact)` |
| `skeleton` | `skeleton(folded)` |

**fold(x)**, decided in draft (OD-T9 (a)), over code point sequences with the §4 tables:
1. `d = NFD(x)`.
2. `m` = the concatenation of `NFKC_CF(c)` for each code point c of d. NFKC_CF is the DerivedNormalizationProps.txt mapping; omitted code points map to themselves.
3. `v = NFC(m)`.
4. Delete every code point of v whose class (§6) is S. NFKC can produce separators: U+00BD ½ gives `1⁄2` with FRACTION SLASH, U+2474 ⑴ gives `(1)`, and U+013F gives `l·`. 100 W code points do this.
5. `fold(x) = NFC` of the result.

NFKC_CF is NFKC, full case folding and deletion of Default_Ignorable_Code_Point, closed under repetition. The UCD's own warning for strings is to apply NFC after the per-character mapping. Step 1 adds NFD first, so that canonically equivalent inputs fold identically. With U+0345 COMBINING GREEK YPOGEGRAMMENI out of canonical order (`α`, U+0345, U+0301), mapping without NFD gives `αί`, not `άι`. Vectors `plain-combining-a`/`-b` pin this, and their paired rejection is exactly that wrong answer.

No W or C code point folds to the empty string under these tables, even after step 4: a one-off computation with the checker's functions over all 149,872 of them found none, and 100 that contain separators before step 4. Since NFC never deletes code points, every token has a non-empty folded value.

**What the fold does, by example:**

| Input | Folded | Vector |
| --- | --- | --- |
| `ﬁnal` (U+FB01) | `final` | `plain-nfkc-ligature` |
| `ＦＵＬＬＷＩＤＴＨ` | `fullwidth` | `plain-nfkc-compat` |
| `x²`, `Ⅻ`, `½`, `⑴`, `①②③` | `x2`, `xii`, `12`, `1`, `123` | `plain-nfkc-compat` |
| `Straße`, `GROẞ` | `strasse`, `gross` | `plain-casefold-expansion` |
| `ΟΔΟΣ`, `οδός` | `οδοσ`, `οδόσ` (final sigma folds) | `plain-greek` |
| `café` in NFD | `café` in NFC | `plain-nfd` |
| `pas`+ZWSP+`sages` | `passages` | `plain-zero-width` |
| Cherokee `ꮳꮃꭹ` | `ᏣᎳᎩ` (capitals) | `plain-cherokee` |

**skeleton(y)** follows [UTS #39](https://www.unicode.org/reports/tr39/tr39-32.html) §4 with the pinned `confusables.txt`, **applied exactly once** (not iterated to a fixed point):
1. NFD.
2. Delete Default_Ignorable code points.
3. Replace each code point by its prototype, if it has one.
4. NFD.

Single application matters: U+048B folds to itself, its prototype is U+0439 U+0326, and step 4 gives U+0438 U+0326 U+0306. Iterating would map U+0438 again, to U+1D0E (`plain-skeleton-single-pass`).

It is applied to the folded value, so case is already gone. The skeleton is a comparison key, not text: it maps `m` to `rn`, `0` to `O` and `1` to `l`, Cyrillic `а` to Latin `a`, and Greek `σ` to `o`. So Latin `oo` and Greek `σο` collide in this channel (§13). Vector `plain-confusable-cyrillic` substitutes Cyrillic а с о р in 8 of 17 words. Its folded hashes share nothing with the Latin sentence, and its skeleton hashes are identical.

**No stemming, stop words, transliteration or language-specific casing** (for example Turkish dotless i). `İstanbul` folds to `i̇stanbul`, keeping U+0307.

**Spans are never folded.** Each folded and skeleton value maps to its token's original half-open byte span, whatever the length change. `ﬁnal` has span 4–10 (3 + 3 bytes) and folded value `final`. `Straße` has span 4–11 and folded value `strasse`. The checker verifies `input[span] == exact` for every token.

**Which channel to compare** is a comparison decision (M2), not an extraction one:
- `folded` is the "normalized" channel for prose: case, compatibility forms and invisible characters do not matter.
- `skeleton` additionally neutralizes listed homoglyphs, at the cost of cross-script collisions.
- `exact` is for verbatim evidence.

## 9. k-grams and hashing

These are contract §7 with these constants:

```
LP("traceweave/text-kgram/draft-1") || LP(profile) || LP(profileVersion) || LP(channel) || uint32be(k)
  || LP("word") || LP(value_i) || … || LP("word") || LP(value_{i+k−1})
```

- `profile` is `text-plain` or `text-markdown`.
- `profileVersion` is `draft-1`.
- `channel` is `exact`, `folded` or `skeleton`.
- `value` is the channel's UTF-8 value.

The class field is the constant `word`, which keeps the contract's byte layout, so one hasher serves both contracts. The domain string differs from the code contract's `traceweave/token-kgram/draft-1` (OD-T6 (a)). Profile names already separate the families, and the distinct domain also makes the hash family explicit. The hash is SHA-256, first 8 bytes, unsigned big-endian, rendered as 16 lowercase hex digits. **It is unkeyed and gives no privacy.**

Winnowing, `windowSelections`, `partialWindow` and the fingerprints follow contract §8 per channel. In `plain-repeated` (20 × `na`), all 13 hashes are equal, and each of the 6 windows selects its last position: fingerprints 7–12. In `plain-ties` (`red green blue` × 8), the hashes have period 3 (`94cc44d3…`, `0f73842e…`, `8d1ce22a…`, …). The folded selections are `[7, 7, 7, 10, 10, 10, 13, 13, 13, 16]`, and the paired rejection breaks ties leftmost.

**Locality.** An unchanged folded token run of at least `k + w − 1` tokens shares at least one fingerprint under identical configuration bytes. `plain-partial-host` holds 17 consecutive source tokens, capitalized and rewrapped, and shares 2 folded fingerprints with `plain-partial-source`. That is the winnowing guarantee restated, not a detection rate.

## 10. Record

**Declared channel list (catalogue and report contract §2b, A3): `["exact","folded","skeleton"]`, in that order, for both profiles.** The configuration's `channels` equals it, which binds it into `configSha256`. Comparisons run on all three channels. Comparing a subset, for example `folded` only, is not allowed yet: that is the contract's OD-C27, so OD-T5′ resolves to (a), three channels.

**Record bytes (`text-plain`).** The canonical record is contract [§2a](../spec/catalogue-report.md#2a-extraction-record-traceweave-extraction-record-draft-1) with no profile-specific fields:
- **Envelope:** `recordVersion` `traceweave-extraction-record-draft-1`, `profile`, `profileVersion`, `configSha256`, `inputSha256`, `inputLength`, `result`.
- **`result`:**
  - Errors are `{"status":"error","error":{"code","offset"}}`.
  - Otherwise the keys are `status`, `tokenCount`, `tokens` and `channels`.
- **Tokens:** each token is `class`, `text`, `span`, and `class` is always `word`. There are no per-token folded or skeleton fields; those are the channel values.
- **Channels:** `channels` has the blocks `exact` (`kgrams`, `windowSelections`, `partialWindow`, `fingerprints`), then `folded` and `skeleton` (each `values` first, then the same four keys). `values` has one entry per token; this profile declares no exclusions, so there is no `tokenIndices`.
- **Serialization:** contract §2a: fixed key order, no insignificant whitespace, raw UTF-8 for non-ASCII, one final LF.

[`records-text-plain.json`](../test-vectors/extraction-text/records-text-plain.json) gives the expected record bytes and their SHA-256 for every `text-plain` and limit vector, plus 2 `unsupported-config` records: 60 records. The vector files carry the same `result` objects.

**Unchanged by alignment.** k-gram hashing already used the class string `word` (§9) and the same values, so no hash, selection or fingerprint changed. All 79 vectors' tokens, spans, values, k-grams and fingerprints are identical to the previous commit, so the profile versions stay (`text-plain` `draft-1`, `text-markdown` `draft-2`).

**`text-markdown`: `masked` placement is open, for its re-review.** Its vectors put `masked` (the merged masked byte ranges) in `result` after `tokens` and before `channels`, which is the proposed placement. Contract §2a has no such key yet, so no `text-markdown` record vectors are given.

## 11. Configuration

The canonical bytes have the contract's §10 shape: one line, keys in order and a final LF.

```
{"contract":"traceweave-text-winnow-draft-1","profile":"text-plain","profileVersion":"draft-1","channels":["exact","folded","skeleton"],"k":8,"window":8,"hash":"sha256-first8-u64be","maxInputBytes":1048576}
```

The configuration digests are:
- `text-plain`: `35c1f63cc2f669a54acb5f9792614721431943b2fd626ffb88982e53bd37323e`;
- `text-markdown` (differs in `profile` and `"profileVersion":"draft-2"`): `3bf7760a91297a5077f9fb0de3c119cb0a5d14b163190d640814a8735de23203`. The draft-1 digest, `0be5e93c…b7c4`, is superseded;
- the limit-vector configuration (`text-plain` with `maxInputBytes` 16): `16d15b33a3b0a117a155d1919f4331e94fce37af7cfbf285952f20fc22f4ac2a`.

Validation is contract §10 steps 1–4 and 8 unchanged, and the steps below. `channels` is the declared channel list of §10.
- **5.** `k` is an integer in `1 … 16`, `window` in `1 … 128` and `maxInputBytes` in `1 … 8388608` (8 MiB), each written in decimal without a sign, leading zeros or exponent. These are contract §10a's bounds, restated here.
- **6.** `channels` is exactly `["exact","folded","skeleton"]`.
- **7.** `contract` is `traceweave-text-winnow-draft-1`, `hash` is `sha256-first8-u64be`, and `(profile, profileVersion)` is `(text-plain, draft-1)` or `(text-markdown, draft-2)`.

There is no `format` key: the front end is the profile. [`config-negative-text.json`](../test-vectors/extraction-text/config-negative-text.json) has 13 configurations that MUST be rejected, each with its `expectedResult`. They include the code channels, two channels, reordered channels, the code contract string, `text-html`, `text-plain`/`draft-2`, the superseded `text-markdown`/`draft-1`, k = 17, `window` = 0, the size bound plus 1, whitespace, a missing LF and an extra `format` key. It also has 2 boundary configurations that MUST be accepted.

A new `profileVersion` is minted on any change to any channel's bytes for some input, as the amended contract §10 now says: classes, the fold, the skeleton data or procedure, the masks, the token rule, errors or tables. That includes any move to Unicode 18.0.0. This is why the draft-1 → draft-2 Markdown changes give `text-markdown` a new version, even though no previously shipped Markdown vector's tokens or masks changed (§18).

### k and window

**Decided in draft, pending owner confirmation (OD-T7): k = 8 word tokens, window = 8, so the locality threshold `k + w − 1` is 15 tokens. These are named experimental values inside `configSha256`, not accuracy promises.** The rationale uses only lane 09's sources:
- **k = 8 is near both published reference points.**
  - P's corpus rationale cites 8-word shingles.
  - W used k = 50 characters on web text. Estimating about 6 bytes per English word including the space, which is an inference and was not measured, 50 characters is roughly 8 words.
  - Shorter k-grams collide on common phrases, and longer ones break under every edit within them.
- **w = 8** gives a guaranteed match for any shared run of 15 words, about one sentence. The expected density is `2/(w+1)` ≈ 0.22 selected k-grams per k-gram (W §3).
  - K found lexical retrieval fails below about 20-word queries and plateaus near 50 tokens. That measured BM25 retrieval of model paraphrases, not winnowing, so it only suggests that 15-token runs are near the lower edge of usefulness.
  - TXT.4 and TXT.6 measure it on prose. Any other value is a new configuration with a new digest, chosen on development data and frozen before held-out evaluation.

The vectors use these defaults, so they also test them. `plain-exact-k` has 8 tokens and one partial window. `plain-below-kw1` has 12 tokens and a partial window. `plain-at-kw1` has 15 tokens, a single full window and no partial flag.

## 12. Complexity

For a fixed configuration, time and working memory MUST be O(N) in the input length (contract §10a):
- **Masks:** one pass (§5).
- **Tokens:** one pass.
- **Fold and skeleton:** per token. Canonical reordering MUST be linear, by a stable counting sort by combining class (the cross-check measured a quadratic sort at 126 s on 1 MiB).

**Value sizes**, bounded per code point from the pinned tables:
- The folded value is at most 10 bytes per input byte (U+FDFA gives 3 → 30 bytes).
- The skeleton is at most 7 bytes per folded byte.
- So `V_exact ≤ N`, `V_folded ≤ 10N` and `V_skeleton ≤ 70N`. The product is not attained by one character, but no lower bound is claimed.

**Hashing.** Following the contract's derivation:
- Each k-gram hashes a prefix of at most 77 bytes, plus 12 + |value| bytes per token.
- Each token is in at most k k-grams, and T ≤ N.
- So the three channels hash at most `231N + k(36N + 81N)` message bytes, plus at most 216N bytes of SHA-256 padding. The total is **`(447 + 117k)·N` compressed bytes**:
  - about 1.35 GiB at the shipped k = 8 and N = 1 MiB;
  - about 18.1 GiB at the bounds k = 16 and N = 8 MiB, about 6.5 s at the 3 GB/s the contract measured.

These are derived bounds for adversarial input, not measurements. Prose is far below them.

## 13. Limits: what the profile cannot detect or claim

TXT.7 requires a citation for each limit. Those below cite a vector or a lane 09 source. TXT.4 and TXT.6 counts do not exist yet.

- **Paraphrase.** Expected misses: any edit inside every window of k + w − 1 tokens removes the guarantee. No reviewed source measures winnowing recall under paraphrase. K measures BM25 retrieval, not k-grams, and P's validation shows n-gram similarity falling under obfuscation (lane 09, "Paraphrase and translation limits").
- **Translation and cross-language reuse.** Not detectable: tokens are compared within one language and script (lane 09; P's translated cases are expected misses).
- **Fragments shorter than `k + w − 1` = 15 tokens.** No guarantee. Shorter shared runs may or may not share a fingerprint (contract §8; `plain-below-kw1`).
- **Scripts without spaces other than ideographs.** Thai, Lao, Khmer and Myanmar text gives phrase-sized tokens. Any re-spacing changes them (`plain-thai`), and recall on such text is unmeasured. Japanese kana runs depend on where ideographs fall (`plain-japanese`).
- **ZWSP as a separator** joins words (`plain-zwsp-as-separator`).
- **Invisible format characters that are not Default_Ignorable split words.** 32 code points are General_Category Cf but not Default_Ignorable_Code_Point, so they are class S: U+0600–U+0605, U+06DD, U+070F, U+0890–U+0891, U+08E2, U+FFF9–U+FFFB, U+110BD, U+110CD and U+13430–U+1343F. Several of them, U+FFF9–U+FFFB and U+13430–U+1343F in particular, commonly render invisibly in Latin text. So `pas`+U+FFFB+`sages` gives `pas`, `sages` in every channel, and inserting them is a zero-width evasion that the fold does not undo. "Zero-width insertion cannot split words" (OD-T8) holds only for Default_Ignorable code points. This is a stated limit, not a rule change (OD-T14): reclassifying them as ignorable would also merge words where the visible ones, such as the Arabic number signs (Prepended_Concatenation_Mark) and U+06DD END OF AYAH, are used as intended (`plain-format-char-split`; review §5).
- **Distractor insertion.** Measured by the clean-room review on `docs/use-cases.md` (3,639 tokens, `text-markdown`, folded channel, 807 distinct fingerprint hashes and 3,617 distinct k-gram hashes), inserting one unrelated word every N tokens leaves this much shared with the original:

  | N | Words added | Fingerprint hashes shared | k-gram hashes shared |
  | --- | --- | --- | --- |
  | 30 | +121 | 582/807 | 2773/3617 |
  | 15 | +242 | 349/807 | 1938/3617 |
  | 14 = w + k − 2 | +259 | 326/807 | 1815/3617 |
  | 8 = k | +454 | 67/807 | 454/3617 |
  | 7 = k − 1 | +519 | 0 | 0 |

  Spacing distractors at w + k − 2 = 14 tokens defeats the *guarantee*, yet still leaves 326 of 807 fingerprint hashes (40%) shared. Removing every shared k-gram needs an edit in every run of k tokens: here one inserted word per 7 tokens (+14%). The numbers are the reviewer's and were not re-run for this revision. The lane 09 text that calls w + k − 2 the "cheapest removal" overstates it; that file belongs to another lane, and the coordinator has been told.
- **Line-end hyphenation** splits words (`plain-hyphenation-wrap`).
- **Typography that NFKC does not unify.** Examples: U+02BC (a letter) against U+2019 (punctuation) as an apostrophe; non-ASCII digits against ASCII digits; vulgar fractions against `1/2` (`plain-nfkc-compat`: `½` gives `12`, `1/2` gives `1`, `2`).
- **Markdown deviations** (§5): entities are not decoded, list numbers and reference labels are kept, indented code is tokenized, text inside HTML blocks and `<script>`/`<style>` bodies is tokenized, and code-span contents are not literal.
- **Homoglyphs not listed in the pinned `confusables.txt`** survive the skeleton. The skeleton also merges distinct words across scripts, for example Greek `σοφοσ` and Latin `ooɸoo`-like strings, so skeleton matches need the exact or folded channel as context (UTS #39 §4; `plain-greek`).
- **Common phrases and boilerplate match.** Licence text, front matter that is not masked, and stock phrases are expected matches unless suppressed by an explicit boilerplate catalogue (lane 09, citing W §5.1–5.2; [catalogue contract](../spec/catalogue-report.md) OD-C5 (b); roadmap M2.10). Suppression is advisory and selection-dependent.
- **No ownership, authorship, permission or direction-of-copying inference.** A shared fingerprint is a shared folded word run, nothing more (UC-8; contract §12).
- **No calibrated false-alert or detection rate.** Nothing has been measured. Any later rate must be computed over the whole search, all windows and catalogue entries, with thresholds frozen before held-out data (lane 07 review; TXT.6: 0/200 bounds a rate only below about 1.5%).
- **No absence claim.** No match means insufficient evidence, not absence.
- **No privacy.** The hash is unkeyed, and anyone holding a fingerprint can test guessed sentences against it.
- **No embedded mark.** Lane 09 found Unicode carriers erased by one published fold, NFKC plus skeleton plus deletion of Default_Ignorable. That is exactly this profile's `skeleton` channel, so marks of that kind are invisible to it by construction (TXT.8 is still open).

## 14. Checks and cross-checks

The tools are in [extraction-text/](../test-vectors/extraction-text/README.md):
- **[`check_text_vectors.py`](../test-vectors/extraction-text/check_text_vectors.py):** standard library only, reading only the pinned table.
- **[`harness/crosscheck_text.py`](../test-vectors/extraction-text/harness/crosscheck_text.py):** a Go oracle and a Rust oracle, built offline.

**Checker, run 2026-11-22.** It recomputes every result from the input bytes:
- configuration validation;
- size, UTF-8 and NUL;
- the masks;
- classes and the token rule;
- NFD, NFKC_CF, NFC, the separator filter and the skeleton;
- k-gram bytes, hashes and winnowing.

It compares token by token and names the first failing layer. It then runs two self-tests:
- the **paired rejections**: wrong expected results, each rejected at its declared layer;
- the **wrong-implementation self-test**: 14 whole alternative extractors, each run over every vector input, at least one of whose results must differ.

The wrong implementations are:
- the five the clean-room review found the draft-1 checker accepted: Unicode 16.0 library data, an iterated skeleton, CommonMark-style HTML blocks, a BOM that disables front matter, and fences after a list marker not recognized;
- the non-ignorable format characters treated as ignorable;
- a BOM stripped with offsets taken from the stripped text;
- seven variants the review already found rejected: x/text Cherokee, no leading NFD, no separator filter, skeleton before fold, ZWSP as separator, ideograph runs, and apostrophe joins.

Restricted to the 71 draft-1 vectors, 6 of the 14 are accepted: the five from the review and the format-character variant. With the new vectors, all 14 are rejected. The Unicode 16.0 variant uses Python's `unicodedata` (16.0.0 here) only to *be* the wrong implementation, and it reports "not applicable" on an interpreter whose data is 17.0.0.

```
PASS config-negative-text.json: 13/13 invalid configurations rejected, 2/2 boundary configurations accepted
PASS text-plain.json vectors=55 tokens=625 errors=9 masked-ranges=0 fingerprints(all channels)=227 partial-windows=57 tie-windows=48
PASS text-markdown.json vectors=21 tokens=234 errors=2 masked-ranges=35 fingerprints(all channels)=72 partial-windows=30 tie-windows=0
PASS limits-text.json vectors=3 tokens=3 errors=2 …
PASS pairs=18 classes=28 total-vectors=79
PASS rejections.json: 70/70 corruptions rejected at their declared layer (error=5, fold=14, hash=1, markdown=14, segmentation=25, skeleton=6, status=3, winnow=2); positive vectors with a paired rejection: 66/66
PASS wrong-implementation self-test: rejected 14/14
PASS records-text-plain.json: 60 text-plain records recomputed byte for byte from (configuration, input) with SHA-256; 58 equal their source vector's result
PASS record corruption self-test: rejected 12/12
PASS record bytes accepted by matching/check_matching.py check_record_bytes + record.schema.json: 51/60; refused only because that checker has no text-plain profile registered (error-code lookup): 9; other refusals: 0
PASS NormalizationTest.txt (17.0.0): NFC and NFD checks 120204/120204
```

**Records.** The checker writes each record with its own serializer and compares it with the bytes and SHA-256 in `records-text-plain.json`. The builder writes those with Python's `json.dumps`, a separate serializer. A consumer-side check then parses each record and re-serializes it. It also checks the A3 structure: the declared channel order, `class` `word`, `tokenCount`, one value per token, no `values` in `exact`, and the null rules.

The 12 record corruptions must fail that check without the expected bytes:
- per-token `folded`;
- reordered channels;
- a wrong `tokenCount`;
- class not `word`;
- `values` in `exact`;
- a dropped `skeleton` channel;
- escaped non-ASCII;
- a missing final LF;
- whitespace;
- `inputBytes`;
- sorted keys;
- an `unsupported-config` record with a profile.

The catalogue and report contract's own `check_record_bytes` and `record.schema.json`, written by another author, accept 51 of the 60 records. The 9 it refuses are exactly the `text-plain` error records, because that checker has no `text-plain` profile registered for its closed-error-code lookup. Registering it there is the catalogue and report contract author's change.

**Cross-check, run 2026-11-22 on the revised vectors.** Versions read from the built binaries:
- Go oracle: `unicode=17.0.0 norm=17.0.0 cases=17.0.0`.
- Rust oracle: `unicode-normalization=17.0.0 unicode-segmentation=17.0.0 pulldown-cmark=0.13.5`.

| Comparison | Reference | Result |
| --- | --- | --- |
| Classes W/C/I/S, every scalar value | Go 1.27 `unicode` tables (DI derived from its Other_DICP, Cf, Variation_Selector, White_Space, Prepended_Concatenation_Mark) | 1,112,064 / 1,112,064 agree |
| Fold of every scalar value | Go x/text: repeat NFKC → `cases.Fold` → delete DI until stable, then NFC | 1,111,978 / 1,112,064. The 86 differences are all Cherokee small letters; 0 unexplained |
| Token fold (with the separator filter), every W/C scalar value | Same | 149,786 / 149,872; the same 86 Cherokee letters; 0 unexplained |
| Fold of every NormalizationTest.txt 17.0.0 string (37,671 distinct) | Same | 37,671 / 37,671 agree |
| Token fold of every vector token | Same | 861 / 862; the 1 difference is the Cherokee token in `plain-cherokee` |
| Token rule and fold on every plain-profile vector, independent Go tokenizer | Same | 46 / 47; the 1 difference is `plain-cherokee` |
| NFC and NFD, every scalar value and every NormalizationTest string | Rust unicode-normalization 0.1.25 | 1,149,735 / 1,149,735 agree, both forms |
| UAX #29 words vs profile tokens (informative) | Rust unicode-segmentation 1.13.3 | Equal spans on 33 / 47 plain vectors |
| CommonMark text content vs Markdown masks (informative) | Rust pulldown-cmark 0.13.5 | Equal folded token sequences on 11 / 19 Markdown vectors; each difference is a listed deviation (§5) |

The 14 vectors where UAX #29 differs are `plain-zero-width`, `plain-zwsp-as-separator`, `plain-other-ignorable`, `plain-nfkc-compat`, `plain-punct-a`/`-b`, `plain-numbers`, `plain-japanese`, `plain-thai`, `plain-combining-a`/`-b`, `plain-bidi`, `plain-format-char-split` and `plain-md-syntax`.

**Unusable references.** Python `unicodedata` (16.0.0) and Rust `caseless` 0.2.2 (16.0.0) were not used, because their Unicode version differs from 17.0.0. No local reference implements the UTS #39 skeleton, so the skeleton is checked only by the checker against `confusables.txt`. No local reference implements this token rule; the Go tokenizer above was written separately from the checker by the same author, so it is not independent in the TXT.3 sense.

**Hand derivation.** The checker's first run against the hand-written expectations found 3 discrepancies:
- a Devanagari vowel sign I had written as `l`, confusing it with Arabic alef;
- a "17-byte" limit input that was 16 bytes;
- a builder defect that located the token `an` inside a masked `</span>`.

The first two were hand errors and were corrected. For the third, the builder now skips hand-listed masked ranges when locating spans. Before that run, my own re-reading had caught 6 missing `m` → `rn` skeleton mappings.

The 8 vectors added in this revision matched the checker on the first run. One wrong-implementation switch did not: the HTML-block switch first masked only lines starting with a tag, which is not what CommonMark does, and the checker accepted it. It was corrected to mask through the next blank line, as CommonMark does; no vector changed.

## 15. Decisions

**Decided in draft, pending owner confirmation.** Each changes tokens, values, hashes or accept/reject, and the vectors encode them. The coordinator adopted the clean-room review's recommendations for OD-T1′, OD-T3′, OD-T4′, OD-T5′, OD-T8′ and OD-T12. None was found wrong, so all are taken as recommended:

| ID | Decision | Reason |
| --- | --- | --- |
| OD-T1′ | (a) The Markdown front end is the masks of §5, with the review's M1 (list-item fences) and M2 (BOM before front matter) fixed in `text-markdown` draft-2 | Deterministic and linear. A CommonMark parser would need a span rule per rendered node, which no reference supplies |
| OD-T2 | (a) Ordered-list numbers and reference labels stay tokens; autolinks, destinations, tags, comments, entities, front matter and fences are masked | Fewest rules that make `md-stripped` equal `md-syntax` |
| OD-T3′ | (a) One token per Ideographic code point; other scripts without spaces get no segmentation, a stated TXT.7 limit to be measured | Pinned property only; no dictionary data |
| OD-T4′ | (a) Accept a BOM; it is ignorable; MD-1 skips it | Common in text files; offsets are unaffected |
| OD-T5′ | (a) Always three channels, the declared list `exact`, `folded`, `skeleton` (contract §2b, A3). Comparing a subset waits for the contract's OD-C27 | The homoglyph class needs the skeleton. A3 defines records, catalogues, modes and reports over the declared list |
| OD-T6 | (a) Domain `traceweave/text-kgram/draft-1`; class constant `word`; contract `traceweave-text-winnow-draft-1` | Keeps the §7 layout; an explicit family name |
| OD-T7 | (a) k = 8, w = 8, experimental | §11 |
| OD-T8′ | (a) Default_Ignorable code points, ZWSP included, are transparent inside words, plus the stated limit for non-ignorable format characters (§13) | Zero-width insertion must not split words; lane 09 transformation |
| OD-T9 | (a) Fold = NFC(NFKC_CF over NFD), delete separators, NFC | Canonical-equivalence-safe; one stream with 1:1 spans |
| OD-T10 | (a) Errors: `invalid-utf8`, `nul`, `input-too-large`, `unsupported-config` | No front-end or token failure exists |
| OD-T12 | Keep the result-mutation rejections, and add a rejected *input* wherever one exists. `plain-reflow-a` is paired with `plain-err-reflow-nul` and `plain-err-reflow-invalid` (relation `input-rejected`). No positive vector has a rejected BOM input under OD-T4′ (a) | Both readings of TXT.2's "paired rejection vector" are covered |
| OD-T15 | Skeleton applied once (§8) | UTS #39 §4 defines one pass; pinned by `plain-skeleton-single-pass` |
| Staging | `text-plain` first, frozen for stage-1 implementation (§17); `text-markdown` stays a draft until re-reviewed | Coordinator decision, following the review |

**Still open, with options:**
- **`text-markdown` record:** where `masked` goes in the contract §2a record. Proposed: in `result`, after `tokens` and before `channels`, as the vectors already have it. To be settled in its re-review, together with a contract §2a amendment.
- **OD-T2′ Markdown details** (each is a one-rule change and a new version):
  - mask ordered-list markers;
  - mask reference labels;
  - keep autolink URLs as tokens;
  - decode character references, giving a span over the whole reference;
  - treat HTML blocks as CommonMark does;
  - recognize block-quote fences.
- **OD-T6′ Domain string:**
  - (a) new (current);
  - (b) reuse `traceweave/token-kgram/draft-1`.
- **OD-T11 Line-end hyphenation:**
  - (a) none (current);
  - (b) join `-`+LF+lowercase letter, which risks joining real compounds such as `well-` LF `known`.
- **OD-T13 Unicode 18.0.0:** when to move, as a new `profileVersion`.
- **OD-T14 Non-ignorable format characters:**
  - (a) a stated limit (current);
  - (b) class the invisible ones (U+FFF9–U+FFFB, U+13430–U+1343F) as I. That is a rule change and a new version for both profiles.
- **OD-20 analogue:** whether this profile's bounds and identifiers follow any later change of the code contract's OD-20.

OD-T7 is settled only by TXT.4 and TXT.6 measurements.

## 16. TXT.1 and TXT.2 checklists

**TXT.1** (lane 09's items):

| Item | Where |
| --- | --- |
| Format front end, `plain`/`markdown`, CommonMark version | §2, §5 (reference CommonMark 0.31.2, deviations listed) |
| BOM policy | §3 |
| Fold over the pinned 17.0.0 files: NFKC, full case folding, delete Default_Ignorable_Code_Point | §8 (NFKC_CF, DerivedNormalizationProps.txt) |
| White_Space mapping | §6: every White_Space code point is a separator (asserted) |
| Optional confusable channel pinned by `confusables.txt` digest | §4, §8 (`skeleton`) |
| Token rule, including scripts without spaces | §7 |
| `exact` and `folded` channels, no stemming or stop words | §8 |
| Span mapping of every folded token to its original span | §8, §10 |
| k and w in the configuration bytes | §11 |
| Closed error list | §3 |
| Hash-framing string | §9 |

**TXT.2** (13 classes; derivation `hand`; tokens and spans listed in every non-error vector; every positive vector paired with a rejection):

| Class | Vectors |
| --- | --- |
| Empty | `plain-empty`, `plain-whitespace-only`, `plain-punctuation-only`, `md-empty`, `md-syntax-only` |
| Below `k+w−1` | `plain-short` (below k), `plain-exact-k`, `plain-below-kw1` (`plain-at-kw1` is the boundary) |
| BOM | `plain-bom`, `md-bom-front-matter`, and U+FEFF inside words in `plain-other-ignorable` |
| CRLF | `plain-crlf`, `md-front-matter-crlf` |
| NFD input | `plain-nfd`, `plain-hangul-jamo`, `plain-combining-b` |
| NFKC expansion (U+FB01) | `plain-nfkc-ligature`, `plain-nfkc-compat` |
| Case-fold expansion (U+00DF) | `plain-casefold-expansion`, `plain-greek`, `plain-cherokee` |
| Zero-width inside a word | `plain-zero-width`, `plain-zwsp-as-separator` |
| Listed confusable | `plain-confusable-cyrillic` (pair `plain-confusable-latin`) |
| Other Default_Ignorable | `plain-other-ignorable`, `plain-bidi`; the non-ignorable format characters in `plain-format-char-split` |
| Markdown syntax | `md-*` (19 non-error vectors), `plain-md-syntax` |
| Invalid UTF-8 | `plain-err-lone-continuation`, `-overlong`, `-surrogate`, `-truncated`, `-above-max`, `plain-err-nul-then-invalid`, `plain-err-reflow-invalid`, `md-err-invalid-utf8` |
| NUL | `plain-err-nul`, `plain-err-reflow-nul`, `md-err-nul` |

The vectors also cover ties, reflow, case, punctuation, numbers, hyphenation, partial copy, non-Latin scripts, combining sequences, mixed direction, Unicode 17.0-new characters, the single-pass skeleton and the size limit: 79 vectors in 28 tagged classes.

## 17. Staging and the `text-plain` freeze

**Decided in draft, pending owner confirmation:** `text-plain` draft-1 is frozen for stage-1 implementation (TXT.3, TXT.4). The frozen inputs are below. No existing `text-plain` or limit vector changed in this revision: all 53 are byte-identical to commit `6fbf11b`, and 5 were added.

| Item | SHA-256 |
| --- | --- |
| `config-text-plain.json` | `35c1f63cc2f669a54acb5f9792614721431943b2fd626ffb88982e53bd37323e` |
| `config-text-plain-limit16.json` | `16d15b33a3b0a117a155d1919f4331e94fce37af7cfbf285952f20fc22f4ac2a` |
| `text-tables-17.0.0.json` | `49eb0304ece1f9351f4db79ddf853fdc3bce353d4a833f7c4f9424bf80ae53f4` |
| `text-plain.json` (55 vectors, §2a `result` shape) | `8690f5aea12a26e37ba3aa944107671075edf0103cd72db640b437042e195cb8` |
| `limits-text.json` (3 vectors) | `cb869b751ec98c4269fb517433e8f53dad665e6f40b09b541cdd9949dc99500e` |
| `records-text-plain.json` (60 canonical records with SHA-256) | `4b58fba3ceaa8234e50db50a1a1bdcec2bfe2e7f465ed395fc3e638a77a78208` |

The two vector-file digests changed from the previous freeze (`3888ee6f…`, `29ec0cc7…`) only because their `result` objects now use the contract §2a layout; no value or hash in them changed. The freeze now covers record bytes too: a stage-1 implementation MUST emit exactly the 60 records of `records-text-plain.json` for their configuration and input bytes. Any change to a `text-plain` channel's bytes for any input needs `draft-2` and a new configuration digest. `text-markdown` draft-2 is **not** frozen: the review's M1 and M2 and the previously unlisted CommonMark differences are fixed or listed here, but they await re-review.

## 18. Change log

**Record alignment (catalogue and report contract A3, commit `51ba163`):**
- **Layout:**
  - The declared channel list is `exact`, `folded`, `skeleton`.
  - Vector `result` objects now use the contract §2a shape: `tokenCount`, tokens as `class` `word`/`text`/`span`, and `folded`/`skeleton` values only in the channels.
  - The provisional fixture layout is gone.
- **New:** `records-text-plain.json`, 60 canonical records with SHA-256.
- **Checker additions:**
  - the record writer and the consumer-side record check;
  - a record corruption self-test (12/12);
  - validation of the records by the matching checker.
- **Unchanged:** all hashes and values, and both profile versions.
- **Changed digests:** `text-plain.json`, `limits-text.json` and `text-markdown.json`, for layout only.


**This revision (after the clean-room review at `c6e8f2a`):**
- **`text-plain` stays `draft-1`. No rule changed:**
  - The single-pass skeleton (T-G4), the invalid-UTF-8 offset (T-G3) and the configuration bounds (T-G2) are now stated rather than implied.
  - The record layout is marked provisional (T-G1).
  - New vectors: `plain-unicode17-new`, `plain-skeleton-single-pass`, `plain-format-char-split`, `plain-err-reflow-nul` and `plain-err-reflow-invalid`.
  - New limits: non-ignorable format characters and distractor insertion.
- **`text-markdown` becomes `draft-2`:**
  - Rule changes: MD-1 skips a leading BOM, and MD-2 accepts a list marker before a fence, with the closer indentation allowance e.
  - The deviations list is completed.
  - The new configuration digest is `3bf7760a…23203`; `text-markdown`/`draft-1` is now an `unsupported-config` (negative `cfg-text-markdown-draft-1`).
  - **Changed vectors:** 11 Markdown vectors with k-grams changed only their hashes, k-gram hashes and fingerprints, because `profileVersion` is in every hash. Their tokens, spans, values and masks are unchanged. They are `md-syntax`, `md-stripped`, `md-fence`, `md-front-matter`, `md-front-matter-crlf`, `md-front-matter-unclosed`, `md-html-comment`, `md-html-comment-unclosed`, `md-link-reference`, `md-link-nested-parens` and `md-angle-brackets`.
  - **Unchanged:** the 7 others, which are errors or have fewer than k tokens.
  - New vectors: `md-html-block`, `md-bom-front-matter` and `md-list-fence`.
- **Checker:**
  - draft-2 Markdown rules;
  - a `(profile, version)` table;
  - the `input-rejected` pair relation;
  - the wrong-implementation self-test (14/14).
