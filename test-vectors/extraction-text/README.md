# Draft text-profile vectors (`text-plain` draft-1, `text-markdown` draft-2)

Status: experimental draft, normative for conformance of this draft version; decided-in-draft items confirmed by the owner's delegation on 2026-11-23.

Vector status: **`text-plain` vectors are frozen** (draft-1). **`text-markdown` vectors (`text-markdown.json`, `config-text-markdown.json`) are a draft and are not normative.**

Revision status (before promotion): revised after the [clean-room review](../../research/reviews/extraction-profile-text-review.md), 2026-11-22. `text-plain` draft-1 is frozen for stage-1 implementation (profile §17: digests listed there); `text-markdown` draft-2 is still a draft. These are the hand-derived vectors (roadmap gate TXT.2) for the [draft text extraction profile](../../profiles/text.md). They are research fixtures, not files in `test-vectors/`, and they make no detection-accuracy claim.

## Files

| File | Contents |
| --- | --- |
| `config-text-plain.json`, `config-text-markdown.json` | Exact configuration bytes (profile §11), k = 8, w = 8, 1 MiB; `text-plain`/`draft-1` and `text-markdown`/`draft-2`. Do not reformat: the digest covers the trailing LF |
| `config-text-plain-limit16.json` | `text-plain` with `maxInputBytes` 16, used by `limits-text.json` |
| `config-negative-text.json` | 13 configurations that MUST be rejected, each with its `expectedResult`, and 2 boundary configurations that MUST be accepted |
| `text-plain.json` | 55 vectors (46 accepted, 9 errors) and 17 pair relations |
| `text-markdown.json` | 21 vectors (19 accepted, 2 errors) and 1 pair relation |
| `limits-text.json` | 3 vectors: exactly the limit, over it, and over it with an invalid byte (the size check runs first) |
| `records-text-plain.json` | 60 canonical extraction records (catalogue and report contract §2a, A3) with SHA-256: every `text-plain` and limit vector, plus 2 `unsupported-config` records. Each names its configuration (`configFile` or `configBase64`, plus `configSha256`) |
| `rejections.json` | 70 paired rejections: one deliberately wrong expected result for each of the 66 accepted vectors, plus 4 for error vectors |
| `text-tables-17.0.0.json` | Derived Unicode 17.0.0 data (profile §4), SHA-256 `49eb0304…80ae53f4` |
| `check_text_vectors.py` | Independent checker, standard library only |
| `harness/gen_text_tables.py` | Regenerates the table from the six pinned files and refuses any other digests |
| `harness/build_vectors.py` | Writes every vector, configuration and rejection file from the hand-written expectations |
| `harness/crosscheck_text.py`, `harness/go/`, `harness/rust/` | Cross-check against Go x/text and Rust Unicode crates, offline, with `go.sum` and `Cargo.lock` |

**Record shape.** Each vector's `result` is the `result` of the canonical extraction record ([contract §2a](../../spec/catalogue-report.md#2a-extraction-record-traceweave-extraction-record-draft-1)), with the declared channel list `exact`, `folded`, `skeleton` ([§2b, A3](../../spec/catalogue-report.md#2b-declared-channel-lists-amendment-a3)). For `text-plain`, the full record bytes are in `records-text-plain.json`. For `text-markdown`, `masked` sits after `tokens` as a proposed placement, which is open for its re-review (profile §10), so no Markdown records are given.

**Vector fields.** Every vector has `id`, `tags` (its `class:` labels), `description`, `derivation` (always `hand`), `config` (the file whose bytes apply), `inputBase64` (the authoritative bytes) and `inputText`. `inputText` is `null` when the bytes are not UTF-8; `inputDisplay` then gives an escaped form. The `result` is one of these:
- **`status: "error"`** with `error.code` and `error.offset`, and nothing else.
- **`status: "ok"` or `"insufficient-tokens"`** with:
  - `tokenCount`;
  - `tokens`: each is `class` (always `word`), `text` (exact) and a half-open byte `span` into the original input;
  - for `text-markdown` only, `masked`: the merged masked byte ranges (proposed placement);
  - `channels`, in order `exact`, `folded`, `skeleton`. `exact` holds `kgrams` (position, 16-hex-digit hash, span), `windowSelections`, `partialWindow` and `fingerprints`. `folded` and `skeleton` put `values`, one per token, first and then the same four keys. The folded and skeleton value of token i is entry i of the channel's `values`.

**Pairs.** Each pair names two vectors, a list of channels and a relation:
- `identical-hashes`: equal, non-empty k-gram hash lists;
- `different-hashes`: no k-gram hash in common;
- `shares-fingerprint`: at least one fingerprint hash in common;
- `input-rejected`: an accepted input paired with a rejected variant of it (OD-T12). The channel list is empty.

**Rejections.** Each rejection names a vector, a declared `layer` and a `mutation`. The checker applies the mutation, recomputes k-grams, hashes and winnowing from the mutated tokens so that only the declared layer is wrong, and requires the checker to fail at exactly that layer. The layers are `segmentation`, `fold`, `skeleton`, `markdown`, `status`, `hash`, `winnow` and `error`. Together with the `input-rejected` pairs, this is how TXT.2's "each positive vector has a paired rejection vector" is read (OD-T12 in the profile).

**Wrong implementations.** Paired rejections only mutate a vector's own result, so they cannot catch an implementation that is wrong only on inputs no vector contains. The checker therefore also runs 14 whole alternative extractors over every vector input, and each must differ on at least one vector. On the 71 draft-1 vectors, 6 of them were accepted: Unicode 16.0 data, an iterated skeleton, CommonMark HTML blocks, a BOM that disables front matter, list-item fences not recognized, and ignorable format characters. The vectors `plain-unicode17-new`, `plain-skeleton-single-pass`, `md-html-block`, `md-bom-front-matter`, `md-list-fence` and `plain-format-char-split` now reject them.

## How the expectations were derived

`derivation: hand` means:
- For every accepted vector, the token texts, folded values, skeleton values and Markdown masked substrings were written by hand in `harness/build_vectors.py`.
- They follow the profile rules and per-character lookups of the NFKC_CF and `confusables.txt` rows for the non-ASCII characters used.

`build_vectors.py` does **not** segment, fold or skeletonize. It does three things:
1. It locates each hand-written token text in the input, left to right, skipping hand-listed masked ranges, to get its byte span.
2. It computes k-gram hashes and winnowing.
3. It writes JSON with every non-ASCII character escaped.

The checker recomputes all of it independently from the input bytes.

The checker's first run against these expectations reported 3 discrepancies:
- a Devanagari vowel sign written as `l`;
- a limit input that was 16 bytes, not 17;
- a builder span-location defect: `an` was located inside a masked `</span>`.

All three were fixed, two in the hand values and one in the builder. The 8 vectors added after the review matched the checker on the first run. Before that run, re-reading had caught 6 missing `m` → `rn` skeleton mappings. No expectation was copied from checker output.

## Coverage

| Class (tag) | Vectors |
| --- | --- |
| `empty` | `plain-empty`, `plain-whitespace-only`, `plain-punctuation-only`, `md-empty`, `md-syntax-only` |
| `short`, `below-kw1` | `plain-short` (5 tokens, insufficient); `plain-exact-k` (8, m = 1, partial); `plain-below-kw1` (12, partial); `plain-at-kw1` (15 = k + w − 1, one full window) |
| `ties` | `plain-ties` (period-3 cycle), `plain-repeated` (all hashes equal) |
| `reflow`, `crlf`, `bom` | `plain-reflow-a`, `plain-reflow-b`, `plain-crlf`, `plain-bom`: identical hashes in every channel; `md-front-matter-crlf` |
| `case`, `casefold-expansion` | `plain-upper`, `plain-casefold-expansion` (U+00DF, U+1E9E), `plain-greek` (final sigma), `plain-cherokee` (small letters fold to capitals) |
| `nfd`, `nfkc`, `combining` | `plain-nfc`/`plain-nfd`, `plain-hangul`/`plain-hangul-jamo`, `plain-nfkc-ligature` (U+FB01)/`plain-nfkc-ascii`, `plain-nfkc-compat`, `plain-combining-a`/`-b` |
| `zero-width`, `default-ignorable` | `plain-zero-width`, `plain-zwsp-as-separator`, `plain-other-ignorable`, `plain-bidi` |
| `confusable` | `plain-confusable-latin`/`plain-confusable-cyrillic`: skeleton identical, folded and exact share no hash |
| `punctuation`, `numbers`, `hyphenation` | `plain-punct-a`/`-b` (identical in every channel), `plain-numbers`, `plain-hyphenation-wrap` |
| `partial-copy` | `plain-partial-source`/`plain-partial-host`: 17 shared tokens, at least one shared folded and skeleton fingerprint |
| `non-latin`, `no-spaces`, `bidi` | `plain-greek`, `plain-rtl-and-indic`, `plain-japanese`, `plain-chinese`, `plain-thai`, `plain-hangul`, `plain-cherokee`, `plain-numbers`, `plain-bidi` |
| `markdown` | `md-syntax`/`md-stripped` (identical in every channel), `plain-md-syntax`, `md-fence`, `md-fence-unclosed`, `md-list-fence`, `md-html-block`, `md-bom-front-matter`, `md-front-matter`, `md-front-matter-crlf`, `md-front-matter-unclosed`, `md-html-comment`, `md-html-comment-unclosed`, `md-link-reference`, `md-link-nested-parens`, `md-angle-brackets`, `md-entities`, `md-indented-code` |
| `invalid-utf8`, `nul` | `plain-err-lone-continuation`, `-overlong`, `-surrogate`, `-truncated`, `-above-max`, `-nul`, `-nul-then-invalid`, `md-err-invalid-utf8`, `md-err-nul` |
| `limit-size` | `limit-exact`, `limit-over`, `limit-over-invalid` |
| `limit` (stated limits) | `plain-zwsp-as-separator`, `plain-format-char-split`, `plain-hyphenation-wrap`, `plain-thai`, `md-entities`, `md-indented-code` |
| `unicode-version`, `confusable` | `plain-unicode17-new` (U+0C5C, U+A7CE/U+A7CF, CJK Extension J), `plain-skeleton-single-pass` (U+048B) |
| paired rejected inputs | `plain-err-reflow-nul`, `plain-err-reflow-invalid` (`input-rejected` pairs with `plain-reflow-a`) |

## 1. Checker

```
python3 -I test-vectors/extraction-text/check_text_vectors.py [--normalization-test PATH/NormalizationTest.txt]
```

Output on 2026-11-22, with `--normalization-test` pointing at the UCD 17.0.0 file (SHA-256 `5019ffd5…8c64dd`). The 14 per-variant lines of the wrong-implementation self-test are omitted here:

```
PASS config-negative-text.json: 13/13 invalid configurations rejected, 2/2 boundary configurations accepted; config-text-plain.json=35c1f63cc2f669a5, config-text-markdown.json=3bf7760a91297a50, config-text-plain-limit16.json=16d15b33a3b0a117
PASS text-plain.json vectors=55 tokens=625 errors=9 masked-ranges=0 fingerprints(all channels)=227 partial-windows=57 tie-windows=48
PASS text-markdown.json vectors=21 tokens=234 errors=2 masked-ranges=35 fingerprints(all channels)=72 partial-windows=30 tie-windows=0
PASS limits-text.json vectors=3 tokens=3 errors=2 masked-ranges=0 fingerprints(all channels)=0 partial-windows=0 tie-windows=0
PASS pairs=18 classes=28 total-vectors=79
PASS rejections.json: 70/70 corruptions rejected at their declared layer (error=5, fold=14, hash=1, markdown=14, segmentation=25, skeleton=6, status=3, winnow=2); positive vectors with a paired rejection: 66/66
PASS wrong-implementation self-test: rejected 14/14
PASS records-text-plain.json: 60 text-plain records recomputed byte for byte from (configuration, input) with SHA-256; 58 equal their source vector's result
PASS record corruption self-test: rejected 12/12
PASS record bytes accepted by matching/check_matching.py check_record_bytes + record.schema.json: 51/60; refused only because that checker has no text-plain profile registered (error-code lookup): 9; other refusals: 0
PASS NormalizationTest.txt (17.0.0): NFC and NFD checks 120204/120204
```

**Records.** Each record is recomputed from its configuration and input bytes, written with the checker's own serializer (the builder uses `json.dumps`), and compared with `expectedRecordText` and `expectedRecordSha256`. A consumer-side check (strict parse, canonical re-serialization, A3 structure and null rules) must reject 12 record corruptions. The records are also passed to the catalogue and report contract's `check_record_bytes` with `record.schema.json`. It refuses the 9 error records only because it has no `text-plain` profile registered for its error-code lookup; that refusal is reported, not hidden.

**What it recomputes.** Everything is recomputed from the input bytes and the pinned table: configuration validation, the size, UTF-8 and NUL checks in order, the Markdown masks, character classes and the token rule, NFD, NFKC_CF, NFC, the separator filter, the skeleton, the k-gram bytes, the hashes, rightmost-minimum winnowing, partial windows, fingerprints, `input[span] == text` and the pair relations.

**Python's `unicodedata` is not used for any expected value.** It is Unicode 16.0.0 in the interpreter used here. It is imported only by the self-test, to act as the "Unicode 16.0 library" wrong implementation, which reports "not applicable" if the interpreter's data is 17.0.0. The checker's own NFD and NFC are verified against NormalizationTest.txt 17.0.0 when the file is supplied. That file is not committed (2,827,429 bytes); its digest is pinned in the checker.

**Limits.** The checker and the builder were written by the same author from the same profile text, so a misreading of the profile shared by both would not be caught. The cross-check below compares the Unicode parts with independent library code. TXT.3 still needs two independent implementations.

## 2. Tables

```
python3 -I test-vectors/extraction-text/harness/gen_text_tables.py UCD_AND_SECURITY_DIR OUT.json
```

The directory must contain `UnicodeData.txt`, `DerivedCoreProperties.txt`, `DerivedNormalizationProps.txt`, `CompositionExclusions.txt` and `PropList.txt` from `Public/17.0.0/ucd/`, and `confusables.txt` from `Public/17.0.0/security/`, with the digests in profile §4. A rerun on 2026-11-22 reproduced the committed table byte for byte.

## 3. Cross-check

```
python3 -I test-vectors/extraction-text/harness/crosscheck_text.py PATH/NormalizationTest.txt [--build-dir DIR]
```

It builds offline (`GOPROXY=off`, `cargo --offline --locked`) with:
- go1.27.3: `unicode` 17.0.0, golang.org/x/text v0.39.0 `norm` and `cases` 17.0.0;
- Rust: unicode-normalization 0.1.25 (17.0.0), unicode-segmentation 1.13.3 (17.0.0) and pulldown-cmark 0.13.5.

Results on 2026-11-22 (about 25 s):

```
classes W/C/I/S, every scalar value (Go unicode): 1112064/1112064 agree
fold, every scalar value (Go x/text NFKC+cases.Fold+DI loop, then NFC): 1111978/1112064 DIFFER
    attributed: 86 Cherokee small letters (U+13F8-13FD, U+AB70-ABBF): UCD NFKC_CF maps them to capitals, x/text cases.Fold leaves them; unexplained: 0
token fold (with separator filter), every W/C scalar value: 149786/149872 DIFFER
    attributed to Cherokee: 86; unexplained: 0
fold, NormalizationTest.txt strings: 37671/37671 agree
token fold, every vector token (Go): 861/862 DIFFER   (the Cherokee token of plain-cherokee)
plain token rule + fold, every plain-profile vector (Go): 46/47 DIFFER   (plain-cherokee)
NFC, every scalar value + NormalizationTest.txt strings (Rust unicode-normalization): 1149735/1149735 agree
NFD, every scalar value + NormalizationTest.txt strings (Rust unicode-normalization): 1149735/1149735 agree
Markdown masks vs CommonMark text content, folded token sequences (informative): 11/19 equal
UAX #29 word spans equal to profile token spans (informative, not required): 33/47 plain vectors
```

**Reading the results.**
- **Cherokee.** The only fold differences are the 86 Cherokee small letters. There, the pinned UCD 17.0.0 data (NFKC_CF, which follows CaseFolding.txt) and Go x/text `cases.Fold` disagree. The profile follows the UCD, and `plain-cherokee` makes the difference visible to any implementation.
- **Rows marked informative** measure where the profile deliberately differs from UAX #29 and from a CommonMark parse (profile §5 and §7). They are not agreement checks.
- **Unusable references.** Python `unicodedata` (16.0.0) and the Rust `caseless` crate 0.2.2 (16.0.0) were not used, because their Unicode version does not match.
- **The skeleton** has no local reference implementation, so only the checker checks it.

## Scope of these files

Nothing here is normative. Promoting the profile or vectors into `profiles/` or `test-vectors/` needs the owner. `text-tables-17.0.0.json` is derived from Unicode, Inc. data files whose headers point to the [Unicode terms of use](https://www.unicode.org/terms_of_use.html). Whether derived tables may be committed under those terms is not settled here, and the owner should confirm it together with the existing [extraction table](../extraction/unicode-17.0.0-tables.json).

Note on paths after promotion: the `profileDraft` field inside `text-plain.json`, `text-markdown.json` and `limits-text.json` still reads `research/drafts/extraction-profile-text.md`. It is a historical label that no checker reads; it was left unchanged so the frozen vector bytes and digests do not change. The profile is [profiles/text.md](../../profiles/text.md).
