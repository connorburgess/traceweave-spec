# Draft extraction vectors (revision draft-1, amended)

Status: experimental draft, normative for conformance of this draft version; decided-in-draft items confirmed by the owner's delegation on 2026-11-23.

Revision status (before promotion): draft for review, 2026-11-22. These vectors accompany the [draft extraction contract](../../spec/extraction.md), revised after the [clean-room review](../../research/reviews/extraction-contract-review.md). They are research fixtures, not files in `test-vectors/`, and they make no detection-accuracy claim.

## Files

| File | Contents |
| --- | --- |
| `config-go.json`, `config-rust.json` | Exact configuration bytes (contract §10), 1 MiB limit. Do not reformat: the digest covers the trailing LF. |
| `config-go-limit16.json`, `config-rust-limit16.json` | The same with `maxInputBytes` 16, used by the limit files |
| `config-negative.json` | `negatives`: 28 configuration byte strings that MUST be rejected, each with its `expectedResult` (`unsupported-config`, offset `null`). `boundaryPositives`: 3 configurations at the §10 bounds that MUST be accepted |
| `go.json` | 49 vectors for `go-tokens`/`draft-1`: 16 accepted inputs and 33 errors (15 of them paired rejections added for M1.2) |
| `rust.json` | 118 vectors for `rust2024-tokens`/`draft-1`: 42 accepted inputs and 76 errors (40 of them paired rejections added for M1.2) |
| `exclusion-rule.json`, `config-exclusion-test.json` | 10 vectors (5 positives and their 5 paired rejections) for the shared normalized-stream exclusion rule (contract §6, OD-23), using the **test-only** synthetic profile `go-tokens-exclusion-test`: Go lexing with `punct` `;` excluded from `normalized`. Not a profile to implement |
| `limits-go.json`, `limits-rust.json` | 3 vectors each: exactly the limit, over the limit, and over the limit plus another defect, showing the size check runs first |
| `unicode-17.0.0-tables.json` | Pinned identifier tables derived from UCD 17.0.0 (contract §3a), SHA-256 `9363b97e…3ac29f` |
| `check_vectors.py` | Independent checker, standard library only (`--list-tests` prints its self-test names) |
| `requirement-map.json` | Gate M1.5 requirement map for `spec/extraction.md`, checked by `tools/check_requirement_map.py` (section 4) |
| `harness/` | Toolchain cross-check: Go oracle, Rust oracle with `Cargo.lock`, the driver `crosscheck.py`, the table generator `gen_unicode_tables.py`, and `build_vectors.py`, which writes every vector and configuration file from hand-written token streams |

Every vector has an `id`, `tags`, a `description`, `inputBase64` (the authoritative bytes) and `inputText`. `inputText` is the readable text, or `null` when the bytes are not UTF-8, in which case `inputDisplay` shows a backslash-escaped form. The `result` object holds one of the following:

- **`status: "error"`** with `error.code` and `error.offset`, and nothing else.
- **`status: "ok"` or `"insufficient-tokens"`** with:
  - `tokens`: each has `class`, `text` and a half-open byte `span`, and Go adds `inserted: true` for automatic semicolons;
  - one object per channel, `exact` and `normalized`. Each holds `kgrams` (position, 16-hex-digit hash, span), `windowSelections`, `partialWindow` and `fingerprints`. `normalized` also lists the normalized `values`.

## Amendment (2026-11-22): what changed for re-vendoring

Contract identifiers, profile versions, configuration files and digests, and the Unicode table are **unchanged**. Every previously shipped vector is byte-identical; this was checked against the previous commit, and no ID was changed or removed. The changes below are additions and the `config-negative.json` format.

**New vectors: 40.**
- **Go (5):**
  - `go-q9-unassigned`
  - `go-q11-imag-binary-digit`
  - `go-q11-imag-octal-digit`
  - `go-q12-line-directive`
  - `go-escapes-vt-raw`
- **Rust, contract questions (26):**
  - Q1: `rust-q1-raw-extra-hash`, `rust-q1-raw-extra-pounds`
  - Q2: `rust-q2-open-then-unterminated`, `rust-q2-open-then-illegal`, `rust-q2-unclosed-innermost`
  - Q3: `rust-q3-byte-unclosed`
  - Q4: `rust-q4-cstring-xff`, `rust-q4-cstring-x00`, `rust-q4-cstring-u-zero`
  - Q5: `rust-q5-raw-lifetime-hash`
  - Q6: `rust-q6-lifetime-nfc-first`, `rust-q6-lifetime-zwj-before-hash`
  - Q7: `rust-q7-unterminated-escape`, `rust-q7-closed-bad-escape`, `rust-q7-raw-byte-unterminated`
  - Q8: `rust-q8-shebang-outer-line-doc`, `rust-q8-shebang-inner-line-doc`, `rust-q8-shebang-outer-block-doc`, `rust-q8-shebang-inner-block-doc`, `rust-q8-not-shebang-four-slashes`, `rust-q8-not-shebang-empty-block`, `rust-q8-not-shebang-three-stars`
  - Q8b: `rust-q8b-shebang-lookahead-nel`, `rust-q8b-bare-shebang`
  - Q9: `rust-q9-unassigned`
  - Q11: `rust-q11-shebang-first-line-only`
- **Rust, literal then digit (S1/Q11, 7):** `rust-s1-string-digit`, `rust-s1-char-digit`, `rust-s1-bytestring-digit`, `rust-s1-rawstring-digit`, `rust-s1-cstring-digit`, `rust-s1-byte-digit`, `rust-s1-string-digit-expr`
- **Rust, harness regression inputs (2):** `rust-shebang-unresolved-body`, `rust-doc-comment-bracket`

**Configuration files.**
- New negatives `cfg-k-above-bound` (k = 17), `cfg-window-above-bound` (129) and `cfg-max-above-bound` (8388609).
- New `boundaryPositives` list: `cfg-bounds-min`, `cfg-bounds-max`, `cfg-rust-bounds-max`.
- Every negative now carries `expectedResult`.

**Lane impact.** The Rust lane's current results differ from these vectors on the `rust-q8-shebang-*` doc-comment cases (D1). The Go lane's results match all 28 report-proposed inputs. Both lanes need the new configuration bounds.

## Amendment (2026-11-22): normalized-stream exclusions

This amendment adds `exclusion-rule.json` and its configuration. Nothing else changed: `harness/build_vectors.py` regenerates every Go/Rust vector, limit and configuration file byte-identically.

The 5 new vectors:
- `excl-semi-newlines` and `excl-semi-explicit`: a pair where exact differs and normalized is identical.
- `excl-ok-normalized-empty`: an `ok` result with an empty normalized channel.
- `excl-insufficient`: an `insufficient-tokens` result that still records `tokenIndices`.
- `excl-partial-window`: a normalized k-gram whose span covers excluded bytes.

In these vectors the normalized channel carries `tokenIndices` before `values`. Go and Rust vectors never do, and the checker rejects one that does.

The table shows which case each vector covers:

| Case | Go | Rust |
| --- | --- | --- |
| Empty / shorter than k / exactly k | `go-empty`, `go-short`, `go-exact-k` | `rust-empty`, `rust-short`, `rust-exact-k` |
| Unicode identifiers, multi-byte literals | `go-unicode` | `rust-unicode` |
| Identifier boundaries (§3a) | `go-unicode-boundary` (U+2E2F, U+0660 accepted); `go-err-u2160`, `-u00b7`, `-u0345`, `-u200d`, `-nd-start` | `rust-unicode-boundary` (U+2160, U+00B7, U+0345 accepted); `rust-err-u2e2f`, `-u200d`, `-non-nfc-*` |
| Repeated tokens, equal-minimum ties | `go-repeated`, `go-equal-minimum` | `rust-repeated`, `rust-equal-minimum` |
| Comment/whitespace pair; rename pair | `go-format-a/b`; `go-rename-a/b` | `rust-format-a/b` (CRLF, nested comment); `rust-rename-a/b` |
| Contract questions (Q1–Q12) and S1 | `go-q9-*`, `go-q11-*`, `go-q12-*` | `rust-q1-*` … `rust-q11-*`, `rust-s1-*` |
| Language specifics | `go-literals`, `go-semicolon-comments`, `go-raw-string-cr` | `rust-literals`, `rust-literal-suffixes`, `rust-lifetimes-chars`, `rust-raw-lifetime`, `rust-cstring-escapes`, `rust-shebang`, `rust-shebang-unterminated-comment`, `rust-inner-attribute`, `rust-doc-comment` |
| Encoding errors | `go-err-invalid-utf8`, `-bom`, `-mid-bom`, `-nul` | `rust-err-invalid-utf8`, `-bom`, `-mid-bom`, `-nul`, `-isolated-cr`, `-cr-in-literal` |
| Lexical errors | `go-err-unterminated-*`, `-illegal-character`, `-malformed-number`, `-invalid-escape`, `-hex-float-no-exponent` | `rust-err-unterminated-*`, `-unbalanced`, `-char-two-codepoints`, `-reserved-prefix`, `-reserved-raw-lifetime`, `-pounds`, `-*-underscore-suffix`, `-cstring-nul-escape`, `-raw-too-many-hashes` |

**Hand-check example** (`go-equal-minimum`, input `x++\nx++\nx++\nx++\n`, tokens `x ++ ;` repeated four times, exact channel). The 8 k-gram hashes repeat with period 3: `55e1d04e…`, `d4aafb7b…`, `1d99e08d…`, and so on. The window at positions 2–5 holds `1d99e08d…` at both 2 and 5. The rightmost rule selects 5. The selections are `[2, 2, 5, 5, 5]`, so the fingerprints are at `[2, 5]`.

## M1.2 metadata (2026-11-23): derivation, classes and paired rejections

**What changed.** Metadata fields were added, plus 60 new rejection vectors. No input, expected token, span, k-gram, hash, window selection, fingerprint, error code or offset of any existing vector changed. Configuration files and the Unicode table are byte-identical. This is proven by `harness/compare_outputs.py 437d619` (see below). Digests for re-vendoring are in [research/extraction-vector-metadata-map.md](../../research/extraction-vector-metadata-map.md).

**Header fields** (every file in this directory):
- `metadataRules: "m1.2"` switches on the checks below.
- `derivationRule` states what `derivation: hand` means (next paragraph). In `config-negative.json` it is the ROADMAP definition alone. In the five vector files it is the definition followed by how it applies to them.

**Per-vector fields:**
- `derivation: "hand"` on every vector and every configuration entry. The values are 183 vectors and 31 configurations, all `hand`; no other value occurs.
- `vectorClasses`: the M1.2 classes the vector belongs to.
- `pairedRejection` on every positive vector, naming a rejection in the same file. The rejection names it back with `pairedPositive`.
- `derivationNote` on three vectors. On `rust-err-invalid-utf8`, the offset was first written as 9; the first toolchain cross-check showed the byte is at 10, and the value was recounted by hand. On `rust-s1-string-digit-expr-rej` and `rust-q11-shebang-first-line-only-rej`, the results were corrected by hand after the non-author review (below).

**What `hand` means.** It means exactly the definition in [ROADMAP.md, Definitions](../../ROADMAP.md#definitions). Each file states it verbatim in `derivationRule`, and `tools/check_requirement_map.py` fails if the two texts differ. Applied here:
- **(a) Judgments written by a person.** Every token class and text, every inserted `;`, every outcome status, every error code and every defect position is written by hand in `harness/build_vectors.py` from the contract text.
- **(b) Arithmetic computed and rechecked.** The arithmetic over those judgments is computed by this specification's own builder, `harness/build_vectors.py`, not by an implementation under test. That covers byte spans, normalized values, k-gram hashes, window selections and fingerprints, plus each new rejection's offset as the index of its hand-chosen defect. `check_vectors.py` recomputes all of it independently, and the clean-room review recomputed all 65 output-producing vectors and agrees.
- **Spans.** A token's span is located by searching for its hand-written text in source order. The exception is vectors marked `spanStarts: hand`, whose start offsets are hand-written because a search would land on the wrong text. Only one vector is marked, `rust-q11-shebang-first-line-only` (`#!/*⏎*/ fn`): a search for `*` finds the `*` inside the skipped shebang line at offset 3, but the token is at 5. The checker enforces the rule both ways. In an unmarked vector, the search must reproduce every start. A marked vector must contain at least one start the search would mislocate.

**No vector's lexical layer was first produced by a tool.** No expected output was copied from go/scanner, proc-macro2, rustc or either implementation; toolchains and implementations were run only afterwards, as checks.

**Two hand errors found by the non-author review**, `rust-s1-string-digit-expr-rej` and `rust-q11-shebang-first-line-only-rej`:
- **The error.** Both were first recorded as `unterminated-literal`, because I missed the reserved-prefix rule. proc-macro2 lacks that rule and happened to agree, so the cross-check passed them.
- **The correction.** Both were re-derived by hand from §5.3 step 3: an identifier or keyword directly followed by `"` is `reserved-token` at its start. The correct results are `reserved-token`@7 and `reserved-token`@8. Each carries a `derivationNote`.

**Paired rejections, one to one.**
- **Coverage.** All 65 positive vectors are paired: Go 16, Rust 42, the two limit files 1 each, and the exclusion file 5. The 3 boundary-positive configurations pair with 3 negative configurations.
- **New rejections.** 60 are new. Each is the positive's own input with one hand-chosen defect, and its description names the defect.
- **Reused rejections.** 5 existing rejections already were such a defect and are reused: `go-err-nul` for `go-short`, `go-limit-over`, `rust-limit-over`, `rust-q1-raw-extra-pounds` and `rust-q4-cstring-x00`.
- **Unpaired rejections.** Error vectors without a `pairedPositive` remain standalone rejections.

**The seven M1.2 classes**, labelled in `vectorClasses` and derived from content:

| Class | Definition (checked by the checker) |
| --- | --- |
| `empty` | Input has zero bytes |
| `below-k+w-1` | Accepted, with fewer than `k + w − 1` (8) tokens |
| `unicode` | Input contains a byte above 0x7F |
| `malformed` | Result is an error |
| `repeated` | Tagged `repeated` (repeated token runs, duplicate hashes kept) |
| `equal-minimum` | Tagged `equal-minimum`; the checker requires an actual tied window |
| `crlf-bom` | Input contains CRLF or the UTF-8 BOM bytes |

**Enforcement.** `check_vectors.py`, run by `tools/validate.py`, enforces all of the following:
- `derivation` is `hand` on every vector and configuration entry;
- `vectorClasses` equals the recomputed classes;
- every positive's `pairedRejection` names an error vector in the same file that pairs back, and no rejection is shared;
- `go.json` and `rust.json` each contain all seven classes;
- every file in this directory declares `metadataRules`.

Metadata self-tests add 7 corruptions per vector file and 3 per configuration file. Each must be rejected:
- per vector file: derivation removed, derivation `computed`, pair removed, a shared rejection, a rejection that does not pair back, the `spanStarts` mark removed or added, a class label dropped;
- per configuration file: derivation removed, a positive without its pair, two positives sharing a negative.

The two cases the gate names, a vector without `derivation` and a positive without its pair, also fail the CLI on a standalone corrupted `go.json` (exit 1).

**How the hole was closed.** `check_vectors.py`, run by `tools/validate.py`, now applies two contract rules itself, instead of trusting a toolchain's agreement:
- **The reserved-prefix rule.** If the character at a Rust error offset is `"`, `'` or `#` and directly follows a plain identifier or keyword, the result must be `reserved-token` at that identifier's start. Raw identifiers, literal prefixes, literal suffixes and lifetime names are excluded.
- **Prefix consistency for every paired rejection.** Every token of the positive that ends at or before the recorded error, over bytes the two inputs share, must still pass the per-token lexical checks in the rejection's input. If one no longer does, the first error is at or before that token.

Both old records are now **wrong-lexer cases** in the self-test ("wrong lexer without the reserved-prefix rule", 2 of Rust's 22 corruptions), and they are rejected. `harness/crosscheck.py` also re-applies the contract's error-offset rules to every Rust error vector, so agreement with proc-macro2 alone no longer confirms a result. It lists proc-macro2's missing reserved-prefix rule for these two vectors as an expected divergence.

**Exact error offsets (confirmation pass).** A `reserved-token` offset moved by one inside the failing token used to pass. The prefix check skipped tokens that end after the offset, and the per-code checks only tested plausibility. Two changes close this:
- **Per-code derivation.** For each error code, `check_vectors.py` now derives the start of the failing unit from the input and the contract rule. It also applies a pair rule: an error offset never lies strictly inside a token of the paired positive over bytes the two inputs share. A closer that matched its opener in those shared bytes cannot be the unbalanced one.
- **Shift self-test.** Every lexical error offset is shifted by −1 and +1, and every shift must be rejected: 151 of 151 (Go 40, Rust 107, exclusion file 4). `harness/crosscheck.py` applies the same local and pair rules.

| Code | How the checker places the offset |
| --- | --- |
| `input-too-large`, `invalid-utf8`, `bom`, `nul`, `isolated-cr` | **Exact**: recomputed from the input bytes |
| `reserved-token` | **Exact in unit**: one of the §5.3 forms starts exactly at the offset. The forms are an identifier or keyword directly followed by `"` `'` `#` (outside the exemptions), `r#` plus a reserved name, a lifetime followed by `#` or `'r#` plus a reserved name, and `#` followed by `#` or `"` that is not part of a raw-string terminator and not preceded by a `#` of the same run |
| `unterminated-literal` | **Exact in unit**: a string-like literal, including its prefix, starts at the offset and has no end, and no identifier character before the offset extends its prefix |
| `unterminated-comment` | **Exact in unit**: `/*` at the offset opens a comment with no end, and no earlier `/*` is unterminated. If an earlier `/*` sits inside a literal or line comment, this can over-reject, but it never over-accepts |
| `malformed-literal` | **Exact in unit**: a literal starts at the offset and does not continue from the previous character. Whether the literal is malformed is the hand judgment, checked further by the per-token rules |
| `non-nfc-identifier`, `malformed-identifier` | **Exact in unit**: an identifier, raw identifier, lifetime or suffixed literal starts at the offset, and its own identifier run is non-NFC or contains a zero-width joiner |
| `illegal-character` | **Exact in unit**: the character at the offset cannot start any token |
| `unbalanced-delimiter` | **Bounded**: a delimiter is at the offset. Which delimiter is unmatched needs bracket matching over a lexed stream. For paired rejections the pair rules decide it; in this set they reject all 20 shifts, and local rules alone reject 18 |

"Exact in unit" means an offset moved anywhere inside or next to the failing unit is rejected. For every lexical code, whether an earlier unit fails first is bounded rather than derived, because proving it needs a full lexer. That property is covered by three things: the paired positive's prefix checks, both implementations (which reproduce every Go and Rust error vector), and the cross-check.

**Re-audit of all 60 new rejections**, by three independent means:
1. **The two new checker rules**, run over the pre-fix vectors: of 118 error vectors, they flagged exactly these two.
2. **Both implementations**, built from their repository at `af3af2b` into a scratch directory and run on every vector: they produced the expected result for all 168 Go and Rust vectors, including all 55 new Go and Rust rejections. Their records were compared with the expected `result` objects. The 10 vectors of the test-only `go-tokens-exclusion-test` profile are not supported there by design. Its 5 new rejections are covered by go/scanner and by the checker rules instead.
3. **A manual re-reading** of each new rejection's defect against the rule that decides it first in scan order, with particular attention to appended characters that follow an identifier.

No other outcome had come from a toolchain, and no other outcome changed.

**Toolchain agreement for the new rejections.**
- **Go:** 16 of the 20 new rejections fail in go/scanner at the same offset. The other 4 are listed: a BOM (OD-1), and three offsets after the token start (OD-13).
- **Rust:** rustc rejects 31 of the 40 new rejections. The other 9 are listed: BOM (OD-1), isolated CR and NUL (OD-2), non-NFC (OD-3), and ZWJ (OD-19). proc-macro2 agrees with 20 of the 40 at the same offset. The rest are listed where it lacks a contract rule: reserved prefixes, the `_` suffix cut and exponent digits.

**Before/after proof:**

```
python3 -I test-vectors/extraction/harness/compare_outputs.py 437d619
compare_outputs: files=12, identical-bytes=6, vectors-compared=123, vectors-added=60, configs-compared=31, configs-added=0
PASS: every expected output present at 437d619 is unchanged; only vectors, configuration entries and the metadata fields ['derivation', 'derivationNote', 'derivationRule', 'metadataRules', 'pairedPositive', 'pairedRejection', 'vectorClasses'] were added
```

## 1. Checker: `check_vectors.py`

```
python3 -I test-vectors/extraction/check_vectors.py
```

Output on 2026-11-22 (Python 3.14.6, `unicodedata` 16.0.0):

```
PASS config-negative.json: 28/28 invalid configurations rejected, 3/3 boundary configurations accepted
PASS go.json profile=go-tokens/draft-1 config=dfbc5fe3517e9da6... vectors=49 tokens=170 (inserted ';'=21) identifiers=61 kgrams=228 fingerprints=82 tie-windows=11 errors=33 (lexical offsets checked by rule: 27) pairs=2 positives=16 paired-one-to-one mutations-rejected=20/20 offset-shifts-rejected illegal-character=11/11 malformed-literal=16/16 unterminated-comment=7/7 unterminated-literal=6/6
PASS rust.json profile=rust2024-tokens/draft-1 config=64b34335e4a61383... vectors=118 tokens=322 (inserted ';'=0) identifiers=103 kgrams=384 fingerprints=146 tie-windows=10 errors=76 (lexical offsets checked by rule: 63) pairs=2 positives=42 paired-one-to-one mutations-rejected=23/23 offset-shifts-rejected illegal-character=5/5 malformed-identifier=5/5 malformed-literal=27/27 non-nfc-identifier=11/11 reserved-token=17/17 unbalanced-delimiter=20/20 unterminated-comment=6/6 unterminated-literal=6/6
PASS limits-go.json profile=go-tokens/draft-1 config=aa86722255afbf50... vectors=3 tokens=8 (inserted ';'=1) identifiers=1 kgrams=8 fingerprints=2 tie-windows=0 errors=2 (lexical offsets checked by rule: 0) pairs=0 positives=1 paired-one-to-one mutations-rejected=7/7
PASS limits-rust.json profile=rust2024-tokens/draft-1 config=71d5ed27bea011f6... vectors=3 tokens=7 (inserted ';'=0) identifiers=2 kgrams=6 fingerprints=2 tie-windows=0 errors=2 (lexical offsets checked by rule: 0) pairs=0 positives=1 paired-one-to-one mutations-rejected=7/7
PASS exclusion-rule.json profile=go-tokens-exclusion-test/draft-1 config=65ae9f23f38b060e... vectors=10 tokens=36 (inserted ';'=4) identifiers=15 kgrams=24 fingerprints=9 tie-windows=0 errors=5 (lexical offsets checked by rule: 3) pairs=0 positives=5 paired-one-to-one mutations-rejected=11/11 offset-shifts-rejected illegal-character=2/2 unterminated-literal=2/2
```

The checker verifies the following:
- **Configuration:** the §10 validation rules including the bounds `k ≤ 16`, `window ≤ 128` and `maxInputBytes ≤ 8388608`; the shipped digests; rejection of every negative configuration with its `expectedResult`; acceptance of every boundary positive.
- **Encoding errors** (size, UTF-8, BOM, NUL, isolated CR), recomputed from the input bytes.
- **Error codes:** each must be in the profile's closed list. For lexical errors, the character at the offset must be able to start the failing construct.
- **Go tokens:**
  - identifier characters and maximal munch from the pinned tables;
  - keyword versus `ident` class;
  - operator longest match;
  - the numeric candidate scan and literal productions;
  - delimiters;
  - semicolon insertion, recomputed from the newlines and comments in each gap.
- **Rust tokens:**
  - XID identifier characters, NFC, and the absence of zero-width joiners;
  - keyword and raw-identifier classes;
  - reserved prefixes;
  - single-character punctuation;
  - lifetimes versus chars;
  - the numeric scan;
  - literal prefix, closing delimiter and the suffix `_` cut. After a literal without a suffix, only a SUFFIX start (`_` or XID_Start) is forbidden, so a following digit is allowed (S1 fix);
  - delimiter balance.
- **Trivia:** every gap between tokens is whitespace, comments or a shebang, including the shebang rule with an unterminated look-ahead comment.
- **Fingerprints:**
  - normalized values, k-gram bytes and the SHA-256 first-8 hash;
  - winnowing as a sort-based selection by `(hash, −position)`;
  - the partial-window flag and fingerprint deduplication;
  - the comment/whitespace and rename pair invariants;
  - coverage of every required case.

**Mutation self-test** (13 Go, 14 Rust, 4 exclusion-rule). Go and Rust each also reject `tokenIndices` on a profile without exclusions. The checker corrupts copies of the data, recomputing hashes so that only the targeted layer is wrong, and requires every copy to be rejected. Per language, these are the corruptions:

- **Both languages:**
  - flipped hash digit;
  - leftmost-minimum tie rule;
  - span cutting a UTF-8 character;
  - dropped token;
  - wrong invalid-UTF-8 offset;
  - invented error code;
  - `func`/`fn` relabelled `ident` in both pairs.
- **Go only:**
  - final inserted `;` dropped;
  - `:=` split into `:` `=`;
  - inserted `;` after `,`;
  - U+2160 accepted as a Go letter;
  - `0b2i` accepted as imaginary.
- **Rust only:**
  - `"x"_` split into string and `_`;
  - `->` as one token;
  - U+2E2F accepted as XID;
  - lifetime relabelled `char`;
  - `"x"0` as one suffixed string;
  - shebang look-ahead that skips `///`.

**S1 fix verified.** The previous checker (the parent commit) failed each of the 7 `rust-s1-*` inputs with "literal or suffix not maximal". The current checker passes them.

Separately, the review's five corruptions were each written into a standalone `go.json` and passed to the CLI, which failed on every one (exit 1):

```
dropped-inserted-semicolon   FAIL go.json:go-literals: inserted semicolons differ from those recomputed by contract section 4.3
func-relabelled-ident        FAIL go.json:go-format-a: 'func': class must be keyword
colon-equals-split           FAIL go.json:go-unicode: ':': not the longest operator at char 6
semicolon-after-comma        FAIL go.json:go-semicolon-comments: inserted semicolons differ from those recomputed by contract section 4.3
invented-error-code          FAIL go.json:go-err-unterminated-string: error code 'made-up-code' is not in the closed list for this profile
```

**What the checker cannot do.** It validates a given token stream and does not produce one. It does not encode:
- escape validity;
- raw-string termination beyond delimiter matching;
- the exact offsets of lexical errors, beyond plausibility.

Some wrong tokenizations in those areas would still pass. The crosscheck covers them for the shipped inputs only.

**NFC.** NFC uses Python's `unicodedata`, which is version 16.0.0 here, so the checker refuses any character that is unassigned in 16.0. By the Unicode normalization stability policy, NFC of a string made only of characters assigned in 16.0 is unchanged in 17.0. Implementations must still use the 17.0.0 data (contract §3a).

## 2. Toolchain cross-check: `harness/crosscheck.py`

```
python3 -I test-vectors/extraction/harness/crosscheck.py [--build-dir DIR]
```

**Requirements.** go 1.27.x and cargo/rustc 1.97.x on PATH. proc-macro2 1.0.107 and unicode-ident 1.0.24 must already be in the local cargo registry cache.

**What it runs.** It builds `harness/go` with `GOTOOLCHAIN=local` and `harness/rust` with `cargo build --offline --locked`, into `DIR`, which defaults to a new temporary directory. Nothing is downloaded or installed, and the repository is not written. It then performs these comparisons:

- **Tables:** Go's `unicode` package (letter + `_`, Nd) and `unicode-ident` 1.0.24 (XID) are compared with `unicode-17.0.0-tables.json` over every code point.
- **go/scanner** (mode 0), for every Go vector:
  - Class, text and start offset of each token are compared. The oracle emits literals and messages as base64 (fix S2a: the previous `strconv.Quote` output was mis-parsed for `\x` escapes and crashed on U+000B).
  - Declared adjustments: inserted `;` is compared by kind and order only, and CR is removed from raw strings because go/scanner strips it.
- **proc-macro2** fallback lexer, for every Rust vector:
  - Class (literal classes excluded), text, start and end offsets are compared.
  - Declared adjustments: a `'` followed by an adjacent identifier becomes a lifetime; tokens whose span starts inside a doc comment are dropped. proc-macro2 synthesizes them as `#[doc = …]` (fix S2b: the previous text-comparison filter kept a synthesized `]` for `/// a]`); a shebang is blanked to spaces with offsets kept.
- **rustc `--edition 2024`:**
  - A leading BOM and the shebang line, as §5.2 decides it, stay at file start. Everything after them is wrapped in a `macro_rules!` invocation, so name resolution never runs (fix S2c: whole-file compilation of `#!` inputs reported false rejections).
  - This checks lexical acceptance only.
- **Accepted vectors** must be accepted by every tool, unless `EXPECT` lists a `rejects` entry (tool offset and reason) and the tokens still agree.
- **Errors:** every error vector must fail in each tool at the same offset, or appear in the `EXPECT` table with a reason. An unlisted difference, or an expectation that no longer happens, fails the run.

Output on 2026-11-22 (go1.27.3 darwin/arm64, rustc 1.97.1):

```
tables: go unicode + unicode-ident 1.0.24 vs pinned 17.0.0 tables: MATCH
  go accepted agree: 21
  go accepted expected: 1
  go error agree: 28
  go error expected: 12
  rust accepted proc-macro2 agree: 43
  rust accepted rustc accepts: 43
  rust error proc-macro2 agree: 41
  rust error proc-macro2 expected: 37
  rust error rustc agree: 59
  rust error rustc expected: 19
PASS: no unexpected divergence
```

### Expected divergences

The script prints all of these with reasons:

- **Contract stricter than the tools by decision:**
  - BOM (OD-1; both tools);
  - NUL and isolated CR (OD-2; proc-macro2 and rustc);
  - non-NFC identifier, suffix and raw identifier (OD-3; proc-macro2 and rustc);
  - U+FEFF inside a Rust string (proc-macro2 and rustc);
  - U+200D in a Rust identifier (OD-19; proc-macro2 and rustc). rustc 1.97.1 accepts it with only an `uncommon_codepoints` warning, contrary to Reference [ident.zero-width-chars].
- **proc-macro2 laxer than rustc, where the contract follows rustc:**
  - edition 2021 reserved prefixes, including the non-NFC-before-quote case;
  - edition 2024 `##`;
  - `"x"_` and `'a'_` (F2);
  - `r#"a"###` (Q1, reserved pounds).
- **Go toolchain versus the Go spec productions** (Q11, Q12): go/scanner accepts `0b2i` and `0o9i`, which cmd/compile and the contract reject. go/scanner rejects `/*line :*/` at offset 8, which the contract treats as a comment (an accepted vector with a listed `rejects` entry).
- **Different offsets** (OD-13, where the contract reports the token start):
  - go/scanner reports `0x`, `\q` and `0x1.8` at the following bytes (7, 7, 10);
  - proc-macro2 reports CR-in-literal at the literal start (8), while the contract's forbidden-code-point scan reports the CR (10);
  - go/scanner reports the 0xFF byte (6) in `go-limit-precedence`, where the size check applies first.
- **`maxInputBytes`** has no toolchain counterpart (the limit vectors).

### Self-test of the driver

A copy of the vectors with `:=` split in `go-unicode` and `"x"_a` truncated in `rust-literal-suffixes` made the driver report both mismatches under `PROBLEMS`.

### Harness fixes verified

The previous harness (the parent commit), run on the amended vectors, reproduced all three defects:
- **(a)** It crashed with `JSONDecodeError` on `go-escapes-vt-raw`.
- **(b)** It kept proc-macro2's synthesized `]` at [5,6) in `rust-doc-comment-bracket`.
- **(c)** It reported rustc rejecting 8 accepted inputs: the `rust-q8-*` look-ahead cases, `rust-q8b-shebang-lookahead-nel`, `rust-q11-shebang-first-line-only` and `rust-shebang-unresolved-body`.

The current harness passes them all. Because the shebang line is kept at file start and the rest is wrapped, the rustc check confirms lexical acceptance of the remainder. It does not independently confirm where rustc ends the shebang; that evidence comes from the cross-check report's toolchain probes.

### History

The first, unshipped cross-check resolved proc-macro2's `unicode-ident` dependency to 1.0.27, which is Unicode 18. `Cargo.toml` now pins `=1.0.24`, and `Cargo.lock` (SHA-256 `02e4a101…d7b201`) records it. In the first revision, the cross-check also caught a wrong offset in `rust-err-invalid-utf8` (9 → 10).

**Scope limit.** Agreement on these inputs does not validate the contract's lexer description in general. Constructs with no vector include most individual escapes, Go octal/hex escape bounds and Rust byte-string escape limits.

## 3. Unicode tables: `harness/gen_unicode_tables.py`

```
python3 -I test-vectors/extraction/harness/gen_unicode_tables.py UCD_DIR OUT.json
```

`UCD_DIR` must contain the four UCD 17.0.0 files named in contract §3a, downloaded from <https://www.unicode.org/Public/17.0.0/ucd/>. The script refuses any file whose SHA-256 differs. On 2026-11-22 it reproduced `unicode-17.0.0-tables.json` byte for byte. The UCD files are not committed: they are public and pinned by digest.

## 4. Requirement map (gate M1.5): `requirement-map.json`

[requirement-map.json](requirement-map.json) maps every occurrence of the requirement keyword in [spec/extraction.md](../../spec/extraction.md) to clauses. Each clause is one of:
- **testable:** it names vectors that fail when the requirement is violated (`failsOn`), at least one negative fixture, the violation, and why it fails. A negative fixture is an error vector, a negative configuration, or a self-test that rejects a violating corruption. Where it names `codes`, every cited rejection carries one of them.
- **implementation test:** it is not decidable from vector bytes, but a process or timing test in the implementation repository fails when the requirement is violated. Tests are cited as `impl:<rev>:<path>:<name>`, at `af3af2b`. `tools/check_requirement_map.py` verifies each citation when `TW_IMPL_REPO` names a checkout of that repository; in CI they are reported as unverified external citations.
- **untestable:** it gives the reason, and is marked for spot-check.
- **definitional:** it defines the keyword itself.

`tools/check_requirement_map.py` is run by `tools/validate.py`. It checks:
- every keyword occurrence is mapped (**unmapped 0**);
- every mapped sentence is still verbatim in the document;
- every cited id exists;
- every `derivationRule` equals the ROADMAP definition;
- the M1.1 item map is complete.

Its self-test of 6 map corruptions must all be rejected.

```
python3 -I tools/check_requirement_map.py
PASS M1.5 requirement map: MUST occurrences=28 unmapped=0 testable=17 implementation-test=4 untestable=5 definitional=2 marked-for-spot-check=10 self-test-corruptions-rejected=6/6; implementation tests verified=0 unverified=6 (set TW_IMPL_REPO to verify)
PASS M1.2 derivationRule: 6 files state the ROADMAP.md definition of hand-derived verbatim, the 5 vector files with its application
PASS M1.1 item map: 13 registration items and 6 named constructs, each answered for Go and Rust with links to existing sections of spec/extraction.md
```

With `TW_IMPL_REPO` set to the implementation checkout, all 6 implementation-test citations were verified at `af3af2b` on 2026-11-23.

**Counts.** 28 keyword occurrences in 24 sentences:
- 17 testable clauses;
- 4 implementation-tested clauses: EX-05a and EX-05b in both implementations, EX-22 and EX-23 in Go only, because no Rust timing test exists at `af3af2b`;
- 5 untestable clauses (EX-03a, EX-03b, EX-04, EX-20, EX-21);
- 2 definitional clauses.

| Clause | Section | Requirement | Kind | Fails on (first 3) | Negative fixtures (first 3) |
| --- | --- | --- | --- | --- | --- |
| EX-00a | status | MUST | definitional | — | — |
| EX-00b | status | MUST NOT | definitional | — | — |
| EX-01 | §2 | MUST NOT carry partial tokens or fingerprints | testable | `rust-q2-open-then-unterminated`, `go-err-unterminated-string`, `rust-err-unbalanced` (+1) | `rust-q2-open-then-unterminated`, `go-format-a-rej` |
| EX-02 | §2 | MUST NOT repair input | testable | `go-err-bom`, `rust-err-bom`, `go-err-unterminated-string` (+4) | `go-err-bom`, `rust-err-non-nfc-identifier`, `go-err-unterminated-string` |
| EX-03a | §2 | MUST NOT emit an extraction result | **untestable** | — | — |
| EX-03b | §2 | MUST surface the failure outside the result | **untestable** | — | — |
| EX-04 | §3 | MUST be made before reading the content | **untestable** | — | — |
| EX-05a | §3 | MUST stop reading after maxInputBytes + 1 bytes | implementation test | `go/cmd/traceweave-go/main_test.go:TestStreamingAndExitStatus`, `crates/tw-extract/src/lib.rs:read_input_stops_at_limit` | — |
| EX-05b | §3 | MUST NOT process any byte beyond maxInputBytes | implementation test | `crates/tw-extract/src/lib.rs:uncomputed_values_are_null`, `go/cmd/traceweave-go/main_test.go:TestStreamingAndExitStatus` | — |
| EX-06 | §3 | MUST be well-formed UTF-8 | testable | `go-err-invalid-utf8`, `rust-err-invalid-utf8`, `excl-partial-window-rej` | `go-err-invalid-utf8`, `rust-err-invalid-utf8`, `excl-partial-window-rej` |
| EX-07 | §3 | MUST NOT split a UTF-8 sequence | testable | `go-unicode`, `rust-unicode`, `go-unicode-boundary` (+1) | `selftest:go.json:span cuts a UTF-8 character`, `selftest:rust.json:span cuts a UTF-8 character` |
| EX-08 | §3a | MUST use tables generated from these files, or the committed derived table | testable | `go-unicode-boundary`, `go-err-u2160`, `go-err-u00b7` (+6) | `go-err-u2160`, `rust-err-u2e2f`, `selftest:go.json:U+2160 accepted as a Go letter` (+1) |
| EX-09 | §3a | MUST NOT rely on a language runtime's or library's built-in Unicode data unless that data is shown to be identical | testable | `go-unicode-boundary`, `go-err-u2160`, `go-err-u0345` (+3) | `go-err-u0345`, `rust-err-u2e2f` |
| EX-10 | §4.4 | MUST match exactly one of int_lit, float_lit or imaginary_lit | testable | `go-literals`, `go-err-malformed-number`, `go-err-hex-float-no-exponent` (+4) | `go-err-malformed-number`, `go-q11-imag-binary-digit`, `go-literals-rej` (+1) |
| EX-11 | §4.5 | MUST be exactly one unicode_value or byte_value | testable | `go-unicode`, `go-unicode-rej` | `go-unicode-rej` |
| EX-12 | §5.3 | MUST be NFC | testable | `rust-err-non-nfc-identifier`, `rust-err-non-nfc-suffix`, `rust-err-non-nfc-raw-ident` (+3) | `rust-err-non-nfc-identifier`, `rust-unicode-rej` |
| EX-13 | §5.3 | MUST NOT contain U+200C or U+200D | testable | `rust-err-u200d`, `rust-q6-lifetime-zwj-before-hash`, `rust-unicode-boundary-rej` | `rust-err-u200d`, `rust-unicode-boundary-rej` |
| EX-14 | §5.4 | MUST contain a digit | testable | `rust-literals`, `rust-literals-rej` | `rust-literals-rej` |
| EX-15 | §5.5 | at least one xid_continue character MUST follow | testable | `rust-err-string-underscore-suffix`, `rust-err-char-underscore-suffix`, `rust-literal-suffixes-rej` (+3) | `rust-err-string-underscore-suffix`, `rust-s1-char-digit-rej`, `selftest:rust.json:'"x"_' split into string and '_'` |
| EX-16 | §6 | MUST NOT emit tokenIndices | testable | `go-unicode`, `rust-unicode`, `go-format-a` (+1) | `selftest:go.json:tokenIndices emitted without exclusions`, `selftest:rust.json:tokenIndices emitted without exclusions` |
| EX-17 | §9 | MUST make these available | testable | `go-unicode`, `rust-unicode`, `record:rec-go-ok` (+2) | `checker:test-vectors/matching/check_matching.py:record corruption self-test` |
| EX-18 | §10 | MUST NOT fall back to another profile | testable | `cfg:cfg-unknown-profile`, `cfg:cfg-unknown-profile-version` | `cfg:cfg-unknown-profile`, `cfg:cfg-unknown-profile-version` |
| EX-19a | §10 | MUST be rejected | testable | `cfg:cfg-whitespace`, `cfg:cfg-key-order`, `cfg:cfg-unknown-key` (+25) | `cfg:cfg-whitespace`, `cfg:cfg-key-order`, `cfg:cfg-unknown-key` (+25) |
| EX-19b | §10 | MUST be accepted | testable | `cfg:cfg-bounds-min`, `cfg:cfg-bounds-max`, `cfg:cfg-rust-bounds-max` | `cfg:cfg-k-zero`, `cfg:cfg-k-above-bound`, `cfg:cfg-window-above-bound` |
| EX-20 | §10a | MUST be O(N) | **untestable** | — | — |
| EX-21 | §10a | MUST NOT cause rescanning | **untestable** | — | — |
| EX-22 | §10a | MUST be linear in the identifier length | implementation test (Go only) | `go/internal/unidata/unidata_test.go:TestNFCLinearTime` | — |
| EX-23 | §10a | MUST NOT be quadratic | implementation test (Go only) | `go/internal/unidata/unidata_test.go:TestNFCLinearTime` | — |

**Spot-check sample for a non-author** (10 clauses):
- the 5 untestable clauses;
- the 4 implementation-tested ones, which cannot be confirmed from this repository alone;
- EX-09, which the vectors test only in part.

| Clause | Section | Requirement | Kind | Note |
| --- | --- | --- | --- | --- |
| EX-03a | §2 | MUST NOT emit an extraction result | untestable | applies only to states the contract does not decide; by construction no vector can expect one (a vector would decide it) |
| EX-03b | §2 | MUST surface the failure outside the result | untestable | process behavior outside the record; not observable in vector bytes |
| EX-04 | §3 | MUST be made before reading the content | untestable | whether bytes are read is not visible in the result; vectors fix only the outcome. The implementations' over-limit regular-file test would still pass if the file were read, so it does not fail on violation |
| EX-05a | §3 | MUST stop reading after maxInputBytes + 1 bytes | implementation-test | process tests: an endless stdin must still end in input-too-large (it never ends if read past the limit), and the reader returns exactly limit bytes |
| EX-05b | §3 | MUST NOT process any byte beyond maxInputBytes | implementation-test | process tests: the record for the first limit+1 bytes equals the record for the whole input, and its digest and length are null |
| EX-09 | §3a | MUST NOT rely on a language runtime's or library's built-in Unicode data unless that data is shown to be identical | testable | only differences at the tested boundary code points are caught; harness/crosscheck.py compares the full tables with Go's unicode package and unicode-ident 1.0.24 |
| EX-20 | §10a | MUST be O(N) | untestable | performance is not observable in vector bytes; the implementations' adversarial probe measures time and memory at the bounds but asserts no limit, so no test fails on violation |
| EX-21 | §10a | MUST NOT cause rescanning | untestable | performance; the adversarial probe times nested comments, unterminated literals and 8 MiB identifiers but asserts no limit |
| EX-22 | §10a | MUST be linear in the identifier length | implementation-test | Go only: timing test, 1 MiB adversarial identifiers must finish within 5 s (a quadratic insertion sort took 126 s). No Rust timing test exists at af3af2b (crates/tw-unicode/src/nfc.rs has only the correctness test basic()); the Rust lane is measured, not tested, by xcheck/probes/adversarial.py |
| EX-23 | §10a | MUST NOT be quadratic | implementation-test | Go only: timing test over runs of non-starters ('a' + (U+0301 U+0316)*, 1 MiB) with a 5 s bound. No Rust timing test exists at af3af2b; the Rust lane is measured, not tested, by xcheck/probes/adversarial.py |

**What a reviewer should confirm:**
- For each untestable clause, that vector bytes really cannot decide it.
- For each implementation test, that it fails when the requirement is violated:
  - EX-05a: an endless stdin must terminate;
  - EX-05b: the record for a prefix equals the record for the whole input;
  - EX-22 and EX-23: a 1 MiB adversarial identifier must stay under 5 s.
- For EX-04, that no current test fails if a regular file is read before the size check.

## Pinned sources

SHA-256 of the local copies cited by the contract:

| Source | SHA-256 |
| --- | --- |
| go1.27.3 `doc/go_spec.html` ("Language version go1.27 (May 26, 2026)") | `a249c493e0ad58ccfeac8081426d5b0e77f92b9761b95548f85c9e4d23d0a753` |
| Rust 1.97.1 rust-docs `reference/input-format.html` | `aba8fb37ae53b0ab9f5420fd0aee0288e3ad59a640acec6c91918dad43a23adb` |
| `reference/shebang.html` | `0dc236835c5f36b4afd30efacedb8697b99b7d2351966a6d842b5defbba05004` |
| `reference/whitespace.html` | `7d3f56ad35a250385116bd4f369737ba3bdf23eaea3d0e7fec3f7d6cb49eaf45` |
| `reference/comments.html` | `9f1b66e694e14b6dafb2800fcdd83cbcf8e5719f9e209cb3210c3c1da3a09f6d` |
| `reference/identifiers.html` | `bbff1fd709c5be0b4c7b1071eaa424d3e71c8a9956aa27e544632b02e96ec761` |
| `reference/keywords.html` | `9a119411835f21af7b1a15b74680942c6fcf729f28012006b852e9dffb67eecb` |
| `reference/tokens.html` | `a3c9235c4bb631aa7049634a1fdbcbcb4f5b975bfca3e7ddd206610861dd245e` |
| UCD 17.0.0 files and the derived table | Contract §3a |
| `harness/rust/Cargo.lock` | `02e4a1012b12a9e1c3d0d746850c1521f09a51df24719c9a52f917a9a9d7b201` |

The online pages are mutable and were not compared byte for byte with these copies.

Unicode data notice: `unicode-17.0.0-tables.json` is derived from the Unicode Character Database 17.0.0 files `UnicodeData.txt`, `DerivedCoreProperties.txt`, `DerivedNormalizationProps.txt` and `CompositionExclusions.txt` (digests in `harness/gen_unicode_tables.py`). Those data files are Copyright © 1991-2026 Unicode, Inc. and are used under the Unicode License v3; see [LICENSES/Unicode-3.0.txt](../../LICENSES/Unicode-3.0.txt) and [LICENSE.md](../../LICENSE.md).
