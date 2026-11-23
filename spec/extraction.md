# Draft extraction contract: token-fingerprint comparison baseline

Status: experimental draft, normative for conformance of this draft version; decided-in-draft items confirmed by the owner's delegation on 2026-11-23.

Revision status (before promotion): **draft for review, revision draft-1 (amended), 2026-11-22.** Roadmap item TW-02, gating M1. This revision resolves the findings of the [clean-room review](../research/reviews/extraction-contract-review.md) (F1–F8, A1–A4). The amendment rules on the contract questions from the two-implementation cross-check (Rust and Go lanes, 9.9 M differential cases), bounds `k`, `window` and `maxInputBytes`, and states the required complexity. Every disposition is listed in [§15](#15-review-dispositions).

A second amendment (§6, OD-23) lets a profile exclude named tokens from the normalized stream; Go and Rust declare none.

**Identifiers are unchanged.** No previously shipped expected output changed: every existing vector's result is byte-identical. So the profile version stays `draft-1` and the configuration digests stay as they were. The amendment does narrow the set of valid configurations (§10 step 5); whether that alone warrants a new `contract` identifier is listed as OD-20.

This document is normative for conformance of this draft version, as stated in its status line. "MUST" and "MUST NOT" describe what this draft proposes for an implementation claiming to follow it. Profile versions are `draft-1`, and nothing here is a registered algorithm.

The contract is meant to be complete enough that someone in another repository can implement it and reproduce the [vectors](../test-vectors/extraction/README.md) byte for byte. Decisions the repository could not settle are recorded in [§14](#14-decisions). Each is either "decided in draft, pending owner confirmation", with the reason, or still open, with options.

## 1. What the baseline is

This is a comparison control, following the [public-census checkpoint](../research/public-census-checkpoint.md): a deterministic, synthetic token-fingerprint extractor with exact and normalized channels and original UTF-8 spans. It does not embed or detect a mark, and it is not a calibrated detector. Extraction is the step `exact configuration bytes + input bytes → tokens, fingerprints, spans, or an explicit error`. Catalogue and report formats belong to TW-03. Comparison and scoring belong to M2.

Extraction is lexical only. No parser, type checker, macro expander or build runs. An input can be a fragment: a Go input needs no `package` clause, and Rust items need not be complete. Lexically valid input that would fail to parse is still fingerprinted. Lexically invalid input is rejected.

## 2. Outcomes

Each extraction produces exactly one of these results:

| Status | Meaning | Tokens | Fingerprints |
| --- | --- | --- | --- |
| `ok` | At least `k` tokens | All | Per channel, §8 |
| `insufficient-tokens` | Fewer than `k` tokens (including zero) | All | None; this is abstention, not an error |

"Tokens" here means the full token stream, which is also the exact channel's stream. A profile's normalized-stream exclusions (§6) never change `status` or `tokenCount`.
| `error` | Configuration, input or lexing failure, with `code` and `offset` | None | None |

An error result MUST NOT carry partial tokens or fingerprints. An implementation MUST NOT repair input: it does not substitute a character, close an open literal, skip an illegal byte, retry with another lexer, normalize, or decode in another encoding.

Error codes form a closed list per profile (§4.8, §5.9), plus `unsupported-config` (§10). Every input either yields a result defined here or is a contract defect. **No catch-all code exists.** An implementation that reaches a state this contract does not decide is non-conformant for that input. It MUST NOT emit an extraction result for it and MUST surface the failure outside the result, for example as a process error. No vector expects such a state.

**Error offsets** (decided, OD-13 (a)):
- `input-too-large` is reported at offset 0.
- Encoding errors (§3) are reported at the first offending byte or code point.
- Lexical errors are reported at the first byte of the token, comment or literal being scanned when scanning fails. For an unbalanced delimiter that is the offending closer, or the innermost unclosed opener at end of input.
- `unsupported-config` has offset `null`.

## 3. Processing order and input bytes

These checks run in order. The first failure decides the result.

0. **Configuration.** Validate the configuration bytes (§10). On failure the result is `unsupported-config`, and the input is not examined.
1. **Size.** An input longer than `maxInputBytes` is `input-too-large` at offset 0. Where the input length is knowable before reading (a regular file's size, a declared content length), the check MUST be made before reading the content. Otherwise the implementation MUST stop reading after `maxInputBytes + 1` bytes and MUST NOT process any byte beyond `maxInputBytes`. Either way, the input's SHA-256 and length are not computed for an `input-too-large` result (§9).
2. **Encoding.** The input MUST be well-formed UTF-8 ([Unicode 17.0.0](https://www.unicode.org/versions/Unicode17.0.0/) §3.9, D92). This rules out overlong forms, encoded surrogates and values above U+10FFFF. On failure the result is `invalid-utf8`, at the first byte of the first ill-formed subsequence.
3. **Forbidden code points.** Search the whole input, including literals and comments, for U+FEFF (code `bom`) and U+0000 (code `nul`). The Rust profile also forbids U+000D not immediately followed by U+000A (code `isolated-cr`). Report the earliest offending code point.
4. **Lexing** runs left to right (§4, §5). The first lexical error in scan order is reported. Checks that can only be made at end of input, such as Rust's unclosed-delimiter check, apply only if scanning reached end of input without an error (Q2: `( "abc` is `unterminated-literal`@2, and `( [ x` is `unbalanced-delimiter` at the innermost opener, @2).

**Spans.** Every span is a half-open interval `[start, end)` of byte offsets into the original input. A span MUST NOT split a UTF-8 sequence. Every token's text equals the bytes at its span, except Go's inserted semicolons, which have empty spans and text `;` (§4.3). Line/column display is out of scope.

## 3a. Unicode data

Both profiles evaluate identifier character classes, and the Rust profile evaluates NFC, using **Unicode 17.0.0** data. This UCD data is the authority, and the [pinned tables](../test-vectors/extraction/unicode-17.0.0-tables.json) are generated from it (SHA-256 `9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f`):

| UCD 17.0.0 file (from [unicode.org/Public/17.0.0/ucd](https://www.unicode.org/Public/17.0.0/ucd/)) | SHA-256 | Used for |
| --- | --- | --- |
| `UnicodeData.txt` | `2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c` | General_Category (Go letters and digits); decomposition mappings and combining classes (NFC) |
| `DerivedCoreProperties.txt` | `24c7fed1195c482faaefd5c1e7eb821c5ee1fb6de07ecdbaa64b56a99da22c08` | XID_Start, XID_Continue (Rust) |
| `DerivedNormalizationProps.txt` | `71fd6a206a2c0cdd41feb6b7f656aa31091db45e9cedc926985d718397f9e488` | Full_Composition_Exclusion, NFC_QC (NFC) |
| `CompositionExclusions.txt` | `2f239196ef3b5b61db5cc476e9bd80f534d15aa1b74e1be1dea5d042a344c85f` | NFC composition exclusions |

The derived table holds:
- `go_letter`: General_Category Lu, Ll, Lt, Lm or Lo, plus U+005F;
- `go_digit`: Nd;
- `xid_start` and `xid_continue`;
- `assigned`: every code point not Cn. This property is **informative only** (Q9). No rule in this contract consults it: an unassigned code point is simply in no identifier class, so it is `illegal-character` (vectors `go-q9-unassigned`, `rust-q9-unassigned`). The checker uses it only to scope its NFC self-check.

[`harness/gen_unicode_tables.py`](../test-vectors/extraction/harness/gen_unicode_tables.py) regenerates it byte for byte from the four files and refuses inputs with other digests. NFC means Normalization Form C as defined in [UAX #15](https://www.unicode.org/reports/tr15/), computed from the 17.0.0 files above.

An implementation MUST use tables generated from these files, or the committed derived table. It MUST NOT rely on a language runtime's or library's built-in Unicode data unless that data is shown to be identical. The crosscheck's `tables` comparison is one way to show this. The ecosystem already drifts:
- Go 1.27's `unicode` package matches, and the shipped crosscheck verifies it.
- `unicode-ident` 1.0.24 matches, but 1.0.26 and later ship Unicode 18.
- Rust's `char::is_alphabetic` is a different property.
- `golang.org/x/text/unicode/norm` falls back to older tables depending on build tags.

Identifier boundaries where the two profiles differ are covered by vectors: U+2160, U+00B7, U+0345, U+2E2F, U+200D and U+0660.

## 4. Go profile `go-tokens`, version `draft-1`

**Authority.** *The Go Programming Language Specification*, "Language version go1.27 (May 26, 2026)", as shipped at `doc/go_spec.html` in go1.27.3 (SHA-256 `a249c493e0ad58ccfeac8081426d5b0e77f92b9761b95548f85c9e4d23d0a753`; online, mutable: [go.dev/ref/spec](https://go.dev/ref/spec)). It cites these sections: Source code representation, Characters, Letters and digits, Comments, Tokens, Semicolons, Identifiers, Keywords, Operators and punctuation, and Integer, Floating-point, Imaginary, Rune and String literals.

Character categories come from §3a, not from the Unicode 8.0 reference in the spec's prose. Where this section restates the spec, the spec governs, and a conflict is a contract defect. go/scanner (go1.27.3) is a cross-check oracle, not the authority.

### 4.1 Token classes

`keyword`, `ident`, `punct`, `int`, `float`, `imag`, `rune` and `string`. Interpreted and raw strings both belong to `string`.

### 4.2 Scanning loop

At each position, after the checks in §3:

1. **White space.** U+0020, U+0009, U+000D and U+000A are skipped. U+000A triggers the §4.3 check.
2. **`//` line comment.** Runs up to but not including the next U+000A, or to the end of input. It acts like a newline and triggers the §4.3 check.
3. **`/*` general comment.** Runs to the first following `*/`. Comments do not nest. With no `*/`, the result is `unterminated-comment` at the `/`. A general comment containing U+000A triggers the §4.3 check. One without a newline acts like a space.
4. **Identifier or keyword.** Starts with a character in `go_letter`. It continues with `go_letter` or `go_digit` characters as far as possible. The class is `keyword` if the text is one of the 25 keywords (`break case chan const continue default defer else fallthrough for func go goto if import interface map package range return select struct switch type var`), otherwise `ident`. Predeclared identifiers (`int`, `true`, `nil`, `len`, …) are `ident`.
5. **Number.** Starts at an ASCII digit, or at `.` immediately followed by an ASCII digit. See §4.4.
6. **`'`** starts a rune, **`"`** an interpreted string and **`` ` ``** a raw string. See §4.5.
7. **Operator or punctuation.** The longest match from: `+ & += &= && == != ( ) - | -= |= || < <= [ ] * ^ *= ^= <- > >= { } / << /= <<= ++ = := , ; % >> %= >>= -- ! ... . : &^ &^= ~`. Class `punct`.
8. **Any other character** is `illegal-character` at its offset. This includes characters outside `go_letter` such as U+2160, U+00B7, U+0345 and U+200D, a non-ASCII `go_digit` character at token start, `#`, `$`, `?`, `@`, `\` and U+00A0.

At end of input, run the §4.3 check once more.

### 4.3 Semicolon insertion

Keep a flag that is true when the last emitted token is one of these: an `ident`, a literal of any class, the keywords `break`, `continue`, `fallthrough` or `return`, or the operators `++`, `--`, `)`, `]` or `}`. When a newline, a line comment, a general comment containing a newline, or end of input is reached and the flag is true, emit `punct` `;` with `inserted: true`, then clear the flag. Every emitted token resets the flag according to that token.

The inserted token's span is empty, `[e, e)`, where `e` is the end of the token that triggered it. go/scanner reports a different position, so the crosscheck compares inserted semicolons by kind and order only. An inserted `;` serializes exactly like an explicit `;` (OD-6).

### 4.4 Numeric literals

Scanning mirrors go/scanner and is maximal munch over a candidate:

1. A `0` followed by `x`/`X`, `b`/`B` or `o`/`O` consumes the prefix and sets the base to 16, 2 or 8. Otherwise the base is 10, which covers legacy octal such as `0755`.
2. If the literal did not start with `.`, consume `[0-9a-fA-F_]` for base 16, otherwise `[0-9_]`.
3. If the next character is `.`, consume it and then the same run.
4. If the next character is `e`, `E`, `p` or `P`, consume it, an optional `+` or `-`, and `[0-9_]`.
5. If the next character is `i`, consume it.

The consumed text MUST match exactly one of the spec productions `int_lit`, `float_lit` or `imaginary_lit`. It is classified `int`, `float` or `imag`, and otherwise it is `malformed-literal` at the literal start. Examples: `0x`, `0b12`, `08` and `0x1.8` (a hex mantissa without `p`) are errors, while `08.5` and `08i` are valid. `0b2i` and `0o9i` are errors too (Q11), because neither `0b2` nor `0o9` is an `int_lit` or `decimal_digits`. cmd/compile agrees; go/scanner and gofmt accept them (vectors `go-q11-imag-binary-digit`, `go-q11-imag-octal-digit`). Scanning then resumes, so `0x1g` gives `0x1` and then the identifier `g`.

### 4.5 Rune and string literals

- **Rune.** From `'`, consume characters. A `\` consumes itself and the next character, unless that character is U+000A or end of input. An unescaped `'` ends the literal. Reaching U+000A or end of input first, escaped or not, gives `unterminated-literal` at the opening `'`. The body MUST be exactly one `unicode_value` or `byte_value`, otherwise the result is `malformed-literal` at the opening `'`. That covers an empty rune, more than one character, an unknown escape, `\"`, octal above `\377`, and a `\u`/`\U` surrogate or value above U+10FFFF.
- **Interpreted string.** Scanned and validated like a rune, with `"` as the delimiter. `\"` is allowed and `\'` is not. A body may hold any number of values.
- **Raw string.** From `` ` `` to the next `` ` ``. Newlines are allowed. End of input first gives `unterminated-literal`. The token text keeps CR bytes (OD-9). go/scanner strips them from its literal, which the crosscheck adjusts for explicitly.

### 4.6 Not covered

`//go:` and `//line` directives are comments, and so are `/*line …*/` general comments, whatever their content (Q12). go/scanner interprets and can reject line directives (`/*line :*/` → "invalid line number"); the contract does not (vector `go-q12-line-directive`, a listed crosscheck divergence). Build constraints, cgo preambles, generated-file markers and test files belong to TW-01/TW-03 (OD-14).

### 4.7 Hand check

`x := f(a,\n\tb) /* c\n */ y := 2 // end` lexes as `x := f ( a , b ) ;ins y := 2 ;ins` (vector `go-semicolon-comments`).

### 4.8 Go error codes

`invalid-utf8`, `bom`, `nul`, `input-too-large`, `illegal-character`, `unterminated-comment`, `unterminated-literal` and `malformed-literal`. These are in addition to `unsupported-config` (§10).

## 5. Rust profile `rust2024-tokens`, version `draft-1`

**Authority.** *The Rust Reference* as shipped with the rust-docs component of Rust 1.97.1 (`share/doc/rust/html/reference/`), edition 2024. It cites these chapters: Input format [input], Shebang [shebang], Whitespace [lex.whitespace], Comments [comments], Identifiers [ident], Keywords [lex.keywords] and Tokens [lex.token]. Page digests are in the [vector README](../test-vectors/extraction/README.md#pinned-sources), and the online copy is [doc.rust-lang.org/1.97.1/reference](https://doc.rust-lang.org/1.97.1/reference/tokens.html). Identifier classes and NFC follow §3a. proc-macro2 1.0.107 (with unicode-ident 1.0.24) and rustc 1.97.1 are cross-check oracles.

Deliberate deviations from the Reference: NUL and isolated CR are rejected (§3); non-NFC identifiers are rejected, not normalized; punctuation is single characters; doc comments are dropped (OD-2 to OD-5). rustc 1.97.1 also accepts U+200D in identifiers with only a lint, contrary to [ident.zero-width-chars]. This contract follows the Reference (OD-19).

### 5.1 Token classes

`keyword`, `ident`, `lifetime`, `punct`, `int`, `float`, `char`, `byte`, `string`, `rawstring`, `bytestring`, `rawbytestring`, `cstring` and `rawcstring`.

### 5.2 Before tokens

CRLF pairs are legal and are not rewritten: offsets and token text use original bytes, and CR before LF counts as white space or as part of a comment or literal.

**Shebang** (Q8, Q8b, Q11). A shebang is recognized only at offset 0, because a BOM is already rejected. The rule is the Reference's `SHEBANG` grammar, which rustc follows: if the input begins with `#!`, look ahead past white space, `LINE_COMMENT` and `BLOCK_COMMENT` only. If the first other content is `[`, there is no shebang and `#!` lexes as tokens. Otherwise everything from offset 0 through the first U+000A, or to end of input, is trivia.

- **White space** in the look-ahead is the 11 Pattern_White_Space characters of §5.3 (`rust-q8b-shebang-lookahead-nel`).
- **Doc comments are content, not comments, in the look-ahead.** These are `///` not followed by `/`, `//!`, `/**` not followed by `*` or `/`, and `/*!`. So `#!///x\n[a]` is a shebang followed by `[ a ]`, and `#!/** d */[a]` is a shebang to end of input with zero tokens. `////x`, `/**/` and `/***/` are ordinary comments: `#!////x\n[a]` lexes as `# ! [ a ]`. Vectors `rust-q8-*`. Outside the look-ahead, doc comments are still dropped as comments (OD-5).
- **An unterminated ordinary block comment** in the look-ahead counts as a comment extending to end of input, so the line is a shebang (`rust-shebang-unterminated-comment`).
- **A bare `#!`** is a shebang (`rust-q8b-bare-shebang`).
- **The shebang covers line 1 only**, even when a block comment opened on line 1 closes later. `#!/*\n*/ fn` lexes as `*` `/` `fn` (`rust-q11-shebang-first-line-only`), as rustc does.

### 5.3 Scanning loop

1. **White space.** The 11 Pattern_White_Space characters of [lex.whitespace]: U+0009–U+000D, U+0020, U+0085, U+200E, U+200F, U+2028 and U+2029.
2. **Comments.** `//` runs to U+000A or end of input. `/*` opens a nested block comment: each `/*` adds one level and each `*/` closes one, and an unclosed comment is `unterminated-comment` at the outermost `/`. Doc comments are dropped like other comments (OD-5).
3. **Identifier start** (`xid_start` or `_`). Read `IDENTIFIER_OR_KEYWORD` = (`xid_start` | `_`) `xid_continue`\*. Then apply these checks **in this order**, all reporting at the token start:
   1. The text MUST be NFC, otherwise `non-nfc-identifier`.
   2. It MUST NOT contain U+200C or U+200D, otherwise `malformed-identifier`.
   3. Branch on the character that follows:
      - **`r`, `br` or `cr` followed by `#` or `"`.** Count the `#` characters, n. If n > 255, the result is `malformed-literal`.
        - For `r` with n = 1 followed by `xid_start` or `_`, read a **raw identifier** `r#` + IDENTIFIER_OR_KEYWORD with class `ident`. Its name gets checks 1 and 2, still reported at the token start. Then, if the name is `_`, `crate`, `self`, `Self` or `super`, the result is `reserved-token`. No reserved-prefix check follows a raw identifier, so `r#let#foo` is three tokens.
        - If the n `#` characters (n ≥ 0) are followed by `"`, the token is a raw string (§5.5).
        - Anything else is `malformed-literal`.
      - **`b` followed by `'`** is a byte literal. **`b` or `c` followed by `"`** is a byte string or C string (§5.5).
      - **Any other identifier immediately followed by `"`, `'` or `#`** is `reserved-token` ([lex.token.reserved-prefix]).
      - **Otherwise** it is a plain identifier. Its class is `keyword` if it is a strict or reserved keyword of edition 2024: `_ as async await break const continue crate dyn else enum extern false fn for if impl in let loop match mod move mut pub ref return self Self static struct super trait true type unsafe use where while abstract become box do final gen macro override priv try typeof unsized virtual yield`. Otherwise the class is `ident`. Weak keywords (`union`, `macro_rules`, `raw`, `safe`) are `ident`.
4. **ASCII digit.** A number (§5.4).
5. **`'`.**
   - If the following characters form a CHAR_LITERAL, the token is `char`, with an optional suffix (§5.5).
   - Otherwise, `'r#` + IDENTIFIER_OR_KEYWORD not followed by `'` is a raw lifetime. Its name gets checks 1 and 2, the reserved names give `reserved-token`, and other names give `lifetime`. A raw lifetime followed by `#` is **not** reserved: `'r#a#` is `lifetime 'r#a` then `#` (Q5, `rust-q5-raw-lifetime-hash`; rustc accepts it).
   - Otherwise, `'` + IDENTIFIER_OR_KEYWORD not followed by `'` is a `lifetime`. The checks run in this order, all at the `'`: NFC (check 1), then zero-width (check 2), then `reserved-token` if `#` follows immediately (Q6: `'é#` with a decomposed é is `non-nfc-identifier`@0, and `'a`+ZWJ+`#` is `malformed-identifier`@0).
   - Anything else is `malformed-literal` at the `'`.
6. **`"`.** A string (§5.5).
7. **`#` immediately followed by `"` or `#`** is `reserved-token` ([lex.token.reserved-guards]).
8. **Single-character punctuation.** One of `! # $ % & ( ) * + , - . / : ; < = > ? @ [ ] ^ { | } ~`, class `punct`, one character per token (OD-4).
9. **Any other character** is `illegal-character`, for example U+2E2F, `` ` ``, `\`, `€` and emoji.

**Delimiters.** Push `(`, `[` and `{` onto a stack. A closer that does not match the top of the stack, or arrives when the stack is empty, is `unbalanced-delimiter` at the closer. If the stack is still non-empty at end of input, the result is `unbalanced-delimiter` at the innermost unclosed opener.

### 5.4 Numeric literals

1. **Prefixed literals.** `0b`, `0o` or `0x` consumes the run `[0-9_]`, or `[0-9a-fA-F_]` for hex. It is `malformed-literal` if:
   - the run has no digit valid for the radix, or a digit outside it;
   - a binary or octal literal is followed by `e` or `E`;
   - an unsuffixed literal is followed by `.` that is not itself followed by `.`, `_` or `xid_start`.
2. **Decimal literals.** Consume `[0-9_]`. Then:
   - If the next character is `.` and the one after it is not `.`, `_` or `xid_start`, consume the `.`. The literal is a `float`. If an ASCII digit follows, consume `[0-9_]*`; otherwise the literal ends at the `.` and takes no suffix.
   - Then, if the next character is `e` or `E`, consume it, an optional `+` or `-`, and `[0-9_]*`. That run MUST contain a digit, otherwise the result is `malformed-literal`. The literal is a `float`.
   - Otherwise the literal is an `int`.
3. **Suffix.** An optional SUFFIX follows (§5.5). Because digit runs absorb `_`, a numeric suffix always starts with `xid_start`. The suffix cannot start with `e`/`E`, because that path is the exponent (SUFFIX_NO_E). `3f32` and `0x1f32` are `int` (the hex run absorbs `1f32`), `1e3f32` is a `float`, and in `p.0.1` the `0.1` is a `float`.

### 5.5 Character, string and raw literals, and suffixes

These follow the Reference productions for CHAR_LITERAL, STRING_LITERAL, RAW_STRING_LITERAL, BYTE_LITERAL, BYTE_STRING_LITERAL, RAW_BYTE_STRING_LITERAL, C_STRING_LITERAL and RAW_C_STRING_LITERAL.

**Escapes.** Quote escapes are `\'` and `\"`. ASCII escapes are `\x` with an octal digit and a hex digit, `\n`, `\r`, `\t`, `\\` and `\0`. Unicode escapes are `\u{` followed by 1–6 hex digits with `_` allowed after the first, then `}`, and the value must be a scalar value. Byte forms allow the full `\xHH` range and no `\u`. String forms also allow `\` followed by LF (or CRLF) as a continuation.

**C strings** (Q4) take byte escapes and Unicode escapes: `\xHH` over the full range 00–FF and `\u{…}` for any scalar value, plus the other ASCII escapes. Any escape whose value is zero is `malformed-literal`, whatever its spelling: `\0`, `\x00`, `\u{0}`, `\u{00}`, `\u{0_0}`. So `c"\xff"` is valid, matching rustc (vectors `rust-q4-*`, `rust-err-cstring-nul-escape`).

**Content.** Char and byte literals exclude a raw TAB, LF or CR and must contain exactly one value. Byte forms are ASCII only.

**Termination and errors.** Termination is decided first, then content (Q7).
- **Finding the end.** A string literal's end is found by an escape-aware scan: `\` skips the next character, and the first unescaped `"` ends it. A raw string ends at the **first** `"` that is followed by n `#`. Any further `#` characters are lexed as ordinary tokens after it (Q1): `r#"a"##` is `rawstring r#"a"#` then `#`, and `r#"a"###` is `reserved-token`@6 because `##` follows.
- **No end found.** A string, byte string, C string or raw form with no end before end of input is `unterminated-literal` at its first byte, including any prefix. This holds whatever the content: `"\q` and `br"é` are both `unterminated-literal`@0.
- **Content.** Only after the end is found is the content validated. A violation is `malformed-literal` at the first byte: `"\q"` is `malformed-literal`@0.
- **Char and byte literals have no unterminated state** (Q3). Anything that is not a complete CHAR_LITERAL or BYTE_LITERAL is `malformed-literal` at its first byte, as for `'ab'`. `b'a` at end of input is `malformed-literal`@0 (`rust-q3-byte-unclosed`).

**Suffix** ([lex.token.literal.suffix]). After any literal except a float ending in `.`, apply SUFFIX → `_ ^ XID_Continue+ | XID_Start XID_Continue*`, where `^` means no backtracking:
- If the next character is `_`, at least one `xid_continue` character MUST follow, otherwise the result is `malformed-literal` at the literal start. So `"x"_` and `'a'_` are errors, matching rustc. They are not a literal followed by the keyword `_`.
- If the next character is `xid_start`, consume `xid_continue*`.
- Otherwise there is no suffix. In particular a digit cannot start a SUFFIX, so a literal directly followed by a digit is two tokens: `"x"0` is `string "x"` then `int 0`, and likewise `'a'0`, `b"x"0`, `r"x"0`, `c"x"0`, `b'a'0` and `"x"1 + y`. rustc accepts all of these (Q11/S1, vectors `rust-s1-*`).

The suffix is part of the token text, and any suffix is accepted lexically (OD-17). The suffix text gets checks 1 and 2 of §5.3, reported at the literal start, after the literal body has been validated.

### 5.6 Lifetimes and labels

The `lifetime` text includes the `'`, and the `r#` for a raw lifetime. `'static` and `'_` are recognized for normalization (§6). Loop labels are lifetimes lexically.

### 5.7 Not covered

Macro bodies are lexed but not expanded. Cargo-script frontmatter is not recognized, so a leading `---` lexes as punctuation. Inline tests, generated files and `build.rs` belong to TW-01/TW-03.

### 5.8 Hand check

`fn r#match<'a>(x: &'a str, y: &'static str) -> char { 'a' }` produces 24 tokens, including `r#match` (`ident`), three `lifetime` tokens and one `char`, with `->` as `-` `>` (vector `rust-lifetimes-chars`).

### 5.9 Rust error codes

`invalid-utf8`, `bom`, `nul`, `isolated-cr`, `input-too-large`, `illegal-character`, `unterminated-comment`, `unterminated-literal`, `malformed-literal`, `reserved-token`, `unbalanced-delimiter`, `non-nfc-identifier` and `malformed-identifier`. These are in addition to `unsupported-config` (§10).

## 6. Token serializations

§6–§8 run once per channel in the profile's declared channel list (§10 step 6). For Go, Rust and TypeScript that list is `exact`, `normalized`, the two channels described here. Each token is a pair `(class, value)` of UTF-8 strings. The exact channel's stream is the full token stream. The normalized channel's stream is the same tokens, minus any the profile excludes (below), in the same order. The channels also differ in `value`:

| Channel | `value` |
| --- | --- |
| `exact` | The token's original bytes (`input[start:end]`), including prefixes, suffixes, quotes and escapes as written. An inserted Go `;` has value `;`, the only token whose value is not its span's bytes. |
| `normalized` | Empty string `""` for class `ident` and every literal class, including Go predeclared identifiers (OD-7). For Rust `lifetime`, empty unless the text is `'static` or `'_`. Otherwise (`keyword`, `punct`, those two lifetimes) the exact value. |

The class is always kept, so a normalized identifier (`ident`, `""`) differs from a normalized string literal (`string`, `""`) and from a keyword.

**Normalized-stream exclusions** (decided in draft, pending owner confirmation, OD-23; requested by the TypeScript profile's TSOD-13). A profile MAY declare a list `normalizedExclusions` in its profile section. Each entry is either a class, or a class with an exact text. A token is excluded from the normalized stream if its class and exact text match an entry (a class-only entry matches every text of that class). The rule has four parts:
- **Scope.** Exclusion applies to the normalized channel only. The token stays in the record's token list, in `tokenCount`, in the exact channel, and in the status decision (§2).
- **Positions and spans.** In a channel with exclusions, k-gram positions, `windowSelections` and fingerprint positions index that channel's own stream (§7, §8). Spans are still the original half-open byte spans of the first and last kept tokens of each k-gram, so a span can cover an excluded token's bytes.
- **Counts.** A channel with n_C tokens has `max(0, n_C − k + 1)` k-grams. For the exact channel n_C = `tokenCount`. For the normalized channel it is the number of tokens not excluded. An `ok` input can therefore have an empty normalized channel: no k-grams, `windowSelections` `[]` and `partialWindow` `false`.
- **Recording.** When, and only when, the profile declares exclusions, the normalized channel records `tokenIndices` before `values`: the ascending indices into the token list of the kept tokens. `values` lists the kept tokens' normalized values only. A profile without exclusions MUST NOT emit `tokenIndices`.

**The Go and Rust profiles declare no exclusions** (`normalizedExclusions` is empty). For them both channels contain every token, and every existing Go/Rust vector, record and configuration digest is byte-identical to before this rule. The TypeScript profile `ts-tokens`/`tsx-tokens` `draft-2` declares `punct` `;`. The checker recomputes every accepted TypeScript vector under this rule with no differences. [exclusion-rule.json](../test-vectors/extraction/exclusion-rule.json) pins the shared arithmetic with a synthetic, test-only profile, `go-tokens-exclusion-test`: Go lexing with `punct` `;` excluded, so explicit and inserted semicolons are both dropped. No implementation is expected to support it as a profile.

**Why.** The exact channel preserves literals and names. The normalized channel survives renaming and literal edits, which is the usual purpose of a token-normalized baseline and is needed for the rename vectors. [profiles/code.md](../profiles/code.md) warns against erasing every identifier and literal in the *sole* representation, so the exact channel always runs alongside. The normalized channel is **not scope-aware** (see §12). Keywords and punctuation carry the remaining structure. An empty value cannot collide with real token text.

## 7. k-grams and hashing

K-grams are built per channel over that channel's stream (§6). For a stream of n tokens there are `m = max(0, n − k + 1)` k-grams. k-gram `i` (for `0 ≤ i < m`) covers stream tokens `i … i+k−1`. Its span is `[start(stream token i), end(stream token i+k−1))` in original bytes, which can include trivia and, with exclusions, excluded tokens. Without exclusions both streams are the full token list.

Write `LP(x)` for the 4-byte unsigned big-endian length of the byte string x, followed by x. The bytes hashed for k-gram i in channel C are:

```
LP("traceweave/token-kgram/draft-1") || LP(profile) || LP(profileVersion) || LP(C) || uint32be(k)
  || LP(class_i) || LP(value_i) || … || LP(class_{i+k−1}) || LP(value_{i+k−1})
```

`profile` and `profileVersion` are the configuration's string values (§10). All strings are UTF-8.

**Hash** (`sha256-first8-u64be`, decided, OD-11 (a)): SHA-256 ([FIPS 180-4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)). Take the first 8 digest bytes and read them as an unsigned 64-bit big-endian integer. Compare hashes as unsigned integers. Vectors render them as 16 lowercase hexadecimal digits, so string order equals numeric order. **The hash is unkeyed**, and anyone holding a fingerprint can test candidate token sequences against it. It gives no privacy (core, Privacy defaults). Keyed selection is a separate later gate.

## 8. Winnowing selection

The algorithm follows Schleimer, Wilkerson and Aiken, [*Winnowing*](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf), SIGMOD 2003: in each window select the minimum hash, and on ties the rightmost. Given hashes `h_0 … h_{m−1}` and window `w`:

- **Normal case (m ≥ w).** For each window start `s = 0 … m−w`, select the `p` in `[s, s+w)` with minimal `h_p`, **taking the largest `p` on ties**. `windowSelections` lists the `m − w + 1` selections in order.
- **Partial window (1 ≤ m < w).** Treat all m hashes as one window. `windowSelections` has exactly one element, its rightmost minimum, and `partialWindow` is `true` (OD-8).
- **m = 0.** `windowSelections` is `[]`, `partialWindow` is `false` and there are no fingerprints. Without exclusions this happens exactly when the status is `insufficient-tokens`. With exclusions, the normalized channel can be empty in an `ok` result (§6).
- **Fingerprints.** The distinct selected positions in ascending order, each with its hash and k-gram span. Different positions with equal hashes are all kept (OD-16).

The procedure runs independently for each listed channel.

**Vector example (`go-equal-minimum`, exact channel).** The window starting at 2 spans positions 2–5 and holds `1d99e08d…` at both 2 and 5. Position 5 is selected. The selections are `[2, 2, 5, 5, 5]` and the fingerprints are at `[2, 5]`. The [implementation-patterns](../docs/implementation-patterns.md) example `[8, 4, 4, 7, 2]` with `w = 3` gives fingerprints at `[2, 4]`.

**Locality.** In each channel, an unchanged run of at least `k + w − 1` tokens of that channel's own stream (§6; for a normalized channel with exclusions, kept tokens only) yields at least one shared fingerprint in that channel under identical configuration bytes. That is the paper's guarantee restated, not a detection rate.

## 9. Extraction record (logical fields)

The wire schema, including field names and any constant keys, belongs to TW-03. This contract fixes the values. An extraction MUST make these available:

- `profile`, `profileVersion` and `configSha256`
- SHA-256 and byte length of the input
- `status`
- for errors: `error.code` and `error.offset`
- tokens: class, exact text, span, and `inserted` for Go
- per listed channel, in list order: `partialWindow` and fingerprints (position, hash, span)
- for the normalized channel of a profile with exclusions (§6): `tokenIndices`, which gives that channel's token count, and so its k-gram count

K-gram lists and `windowSelections` are required in vectors and optional in production output.

**Values that are not computed** (Q10, decided in draft, pending owner confirmation):
- For `unsupported-config`, `profile` and `profileVersion` are `null`, because an unvalidated configuration names nothing. `configSha256` is the SHA-256 of the bytes supplied. The input SHA-256 and length are `null`, because the input is not examined (§3 step 0). The error offset is `null`.
- For `input-too-large`, the input SHA-256 and length are `null`, because the input is not read past the limit (§3 step 1).

The two implementations currently disagree on envelope names (`inputBytes` versus `inputLength`, and a constant `contract` key), and that choice is TW-03's. The extraction vectors carry `result` objects only. [config-negative.json](../test-vectors/extraction/config-negative.json) gives the expected `unsupported-config` result for each negative configuration.

## 10. Configuration record

**Bytes.** The configuration is identified by its exact bytes, and core requires `configSha256` over them. The canonical form is one line of JSON with no insignificant whitespace, these keys in exactly this order, and one trailing LF:

```
{"contract":"traceweave-token-winnow-draft-1","profile":"go-tokens","profileVersion":"draft-1","channels":["exact","normalized"],"k":5,"window":4,"hash":"sha256-first8-u64be","maxInputBytes":1048576}
```

The Rust configuration differs only in `"profile":"rust2024-tokens"`. Digests: Go `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2`, Rust `64b34335e4a61383ada1403a2df97c2e45dba987bbf0c8ec21385e04104d1277`.

**Mapping to core.** The core profile triple `id`, `version`, `configSha256` maps to `profile`, `profileVersion` and the SHA-256 of these bytes. `contract` names the algorithm family of §6–§8, and `hash` names the function of §7.

**Versioning.** Profile identifiers deliberately omit toolchain versions. A new `profileVersion` is minted only when tokens, classes, errors, Unicode tables, normalized values or `normalizedExclusions` change, that is, on any change to any channel's bytes. A new toolchain release is accepted for an existing version by re-running the shipped crosscheck and finding no new divergence.

**Validation**, which runs before any input check (§3 step 0). Apply these checks in order. The first failure is `unsupported-config`, offset `null`:

1. The bytes are UTF-8. The only line break is a single final LF, and there is no CR.
2. The bytes parse as JSON without duplicate keys, without non-integer numbers, and without constants such as `NaN`.
3. The top level is an object with exactly the keys above, in that order.
4. `contract`, `profile`, `profileVersion` and `hash` are strings matching `[a-z0-9.-]+`. No escapes are possible.
5. `k` is an integer in `1 … 16`, `window` in `1 … 128` and `maxInputBytes` in `1 … 8388608` (8 MiB), each written in decimal without a sign, leading zeros or exponent (bounds: §10a).
6. `channels` equals the profile's declared, ordered channel list, whose first entry is `exact` ([catalogue-report contract §2b](catalogue-report.md#2b-declared-channel-lists-amendment-a3)). Go, Rust and TypeScript declare exactly `["exact","normalized"]`. Subsets and other orders are rejected.
7. `contract` is `traceweave-token-winnow-draft-1`, `(profile, profileVersion)` is a pair the implementation implements, and `hash` is `sha256-first8-u64be`.
8. Re-serializing the parsed values in canonical form reproduces the bytes exactly.

An implementation MUST NOT fall back to another profile. [config-negative.json](../test-vectors/extraction/config-negative.json) lists 28 configurations that MUST be rejected, including one just above each bound, and 3 `boundaryPositives` at the bounds that MUST be accepted. Any `k`, `window` and `maxInputBytes` within bounds is a valid configuration with its own digest. The extraction vectors exercise k = 5, w = 4 and `maxInputBytes` of 1 MiB and 16.

## 10a. Resource bounds and complexity

**Decided in draft, pending owner confirmation (OD-21): `k ≤ 16`, `window ≤ 128`, `maxInputBytes ≤ 8,388,608`.** draft-1 allowed up to 2³² − 1 for all three. The cross-check measured hashing time growing as n·k: 64 KiB of `;` with k = 32,768 took 18 s (Go) and 60 s (Rust), and extrapolating to 1 MiB with k = 2¹⁹ gives about 77 min and 4 h.

**Rationale for each bound.**
- **`k ≤ 16`** covers the token k-gram lengths used in token-based plagiarism baselines and the k = 8–12 candidates under OD-10 tuning, with headroom.
- **`window ≤ 128`** allows a locality threshold `k + w − 1` of up to 143 tokens, several functions. Sparser selection than that belongs to comparison (M2), not extraction.
- **`maxInputBytes ≤ 8 MiB`** is 8× the shipped 1 MiB. Hand-written source files are far smaller, and larger files are generated or vendored (OD-14). The bound makes "maximum-size input" finite.

**Worst-case hashing work.** Let N be the input length in bytes and T the token count. For Rust T ≤ N. For Go T ≤ 2N, since real tokens are at most N and inserted `;` at most one per real token.

- **Per k-gram.** Each k-gram hashes a fixed prefix of at most 82 bytes, plus 8 + |class| + |value| per token. |class| is at most 13.
- **Per channel.** Each token is in at most k k-grams and Σ|value| ≤ N + T. So one channel hashes at most 82T + k·(22T + N) ≤ (164 + 45k)·N message bytes.
- **Both channels**, with SHA-256 padding (at most 72 bytes per message), compress at most **(616 + 90k)·N bytes**.

| Configuration | Worst-case SHA-256 input | At 3 GB/s |
| --- | --- | --- |
| Shipped (k = 5, N = 1 MiB) | about 1.0 GiB | about 0.4 s |
| Bounds (k = 16, N = 8 MiB) | about 16.1 GiB | about 6 s |

3 GB/s is single-core bulk SHA-256 measured on darwin/arm64 for this amendment. These worst cases need one-byte tokens such as `;;;;`. Real source code has multi-byte tokens and is far below them.

**Required complexity.** For a fixed configuration, an implementation's time and working memory MUST be O(N), linear in the input length. In particular:
- **Lexing** is a single left-to-right pass, plus the bounded look-aheads defined here: the shebang look-ahead, raw-string terminators of at most 255 `#`, and literal suffixes. Nested comments, unterminated literals and long identifiers MUST NOT cause rescanning.
- **NFC checking** MUST be linear in the identifier length. Canonical reordering of a run of non-starters MUST NOT be quadratic. A stable counting sort by combining class (0–255) is linear. An NFC_QC quick check may short-cut the common case. The cross-check measured a quadratic insertion sort at 126 s for a 1 MiB identifier.
- **Hashing** is O(k·N) as bounded above. Implementations SHOULD reuse one buffer per k-gram rather than retaining k-gram byte strings.
- **Selection** is O(m·w) by direct scan, or O(m) with a monotone deque. Working memory beyond the token and k-gram lists is O(w).
- **Output.** The record is O(N) in size. Implementations SHOULD stream it rather than build an in-memory tree; the cross-check measured 8.7 GiB peak memory on a 1 MiB input from a tree-building encoder.

## 11. Parameters k and window

**Decided in draft, pending owner confirmation (OD-10 (a)): k = 5 tokens and w = 4 k-grams, frozen as experimental values inside `configSha256`.** The locality threshold is 8 tokens.

They were chosen because they keep the vectors small enough to check by hand, and because eight tokens is roughly one short statement or signature, which suits localizing fragment copies in M2. In exchange, short k-grams are expected to collide on common code such as `if err != nil { return`. M2 must keep such matches visible.

**These are not accuracy promises.** No recall, false-alarm rate or threshold is implied. Other values are new configurations with new digests. Tuning follows [evaluation](../docs/evaluation.md) and TW-05: choose on development data and freeze before held-out evaluation.

## 12. What the baseline does not claim

- **No ownership or authorship inference.** A shared fingerprint is a shared normalized token run. It shows nothing about authorship, permission, infringement, training membership or direction of copying.
- **No calibrated false-alert rate.** Nothing has been measured. Following the [lane 07 evidence review](../research/lanes/07-evidence-review.md), any later rate must be calibrated over the complete search, not per k-gram.
- **No embedded mark or detector.** This is a control for M2/M2E comparisons.
- **Not scope-aware, and no semantic equivalence.** [profiles/code.md](../profiles/code.md) plans a *scope-aware* identifier-normalized channel. This baseline's normalized channel erases names lexically and is weaker. It cannot distinguish shadowed bindings, and it collapses distinct identifiers. No resilience to reordering, inlining or structural rewrites is claimed, and no match means "insufficient evidence".
- **No parser agreement.** Lexically valid but syntactically invalid fragments are fingerprinted.
- **No keyed or private fingerprints.** The hash is unkeyed (§7).
- **Lexing is verified only as far as §13 states.**

## 13. Requirement-to-check map

**Requirement map (gate M1.5).** [requirement-map.json](../test-vectors/extraction/requirement-map.json) maps every sentence of this document that uses the requirement keyword, the Go and Rust profiles included, to one of two things:
- vectors or self-tests that fail when the requirement is violated, with at least one negative fixture each;
- an "untestable" entry, with its reason.

`tools/check_requirement_map.py`, run by `tools/validate.py`, checks the map as follows:
- every keyword occurrence is mapped, with 0 unmapped;
- every mapped sentence is still in this document;
- every cited id exists.

The registration item map (gate M1.1) is in [profiles/code.md](../profiles/code.md#registration-item-map-go-and-rust-gate-m11).

The table below is the older, requirement-to-check overview.

Two tools check the vectors:
- **checker:** [`check_vectors.py`](../test-vectors/extraction/check_vectors.py), standard library only;
- **crosscheck:** [`harness/crosscheck.py`](../test-vectors/extraction/harness/crosscheck.py), which compares against go/scanner, proc-macro2 and rustc, offline.

| Requirement | Check |
| --- | --- |
| §10 configuration validation, bounds and canonical bytes | Checker validates the shipped configurations, rejects all 28 negatives (including one above each bound) and accepts the 3 boundary positives |
| §9 `unsupported-config` result | `expectedResult` on every negative configuration, checked by the checker |
| §3 order: size, then UTF-8, then forbidden code points | `*-limit-*`, `*-err-invalid-utf8`, `*-err-bom`, `*-err-mid-bom`, `*-err-nul`, `rust-err-isolated-cr`, `rust-err-cr-in-literal`; recomputed by the checker |
| Spans: half-open, character boundaries, `text == input[span]` except inserted `;` | Checker on every accepted vector; span-cut mutation |
| §3a pinned Unicode data | Checker verifies the table digest; the generator reproduces it from UCD digests; crosscheck matches it against Go `unicode` and unicode-ident 1.0.24 |
| Go identifiers, keywords, operators, numbers (§4.2, §4.4) | Checker per token: table classes and maximal munch, keyword list, operator longest match, candidate scan and literal productions; crosscheck token-for-token |
| Go semicolon insertion (§4.3) | Checker recomputes every inserted `;` from the gaps; crosscheck by kind and order |
| Rust identifiers, NFC, keywords, raw identifiers, reserved prefixes (§5.3) | Checker per token; crosscheck token-for-token; rustc acceptance |
| Rust numbers and literal suffixes, including the `_` cut (§5.4, §5.5) | Checker re-scans numbers and checks literal closure and the suffix; `rust-literal-suffixes`, `rust-err-*-underscore-suffix` |
| Trivia, nested comments, shebang look-ahead (Reference SHEBANG: doc comments are content) | Checker trivia scan with the §5.2 look-ahead; `rust-format-b`, `rust-shebang*`, `rust-q8-*`, `rust-q8b-*`, `rust-q11-shebang-first-line-only`, `rust-inner-attribute`, `rust-doc-comment*`; crosscheck (proc-macro2 with the shebang blanked; rustc with the shebang kept and the rest wrapped) |
| Rulings Q1–Q12 (§3, §3a, §4.4, §4.6, §5.2, §5.3, §5.5, §9) | At least one vector each (`*-q*-*`, `rust-s1-*`, config negatives for Q10); see §15 |
| §6 normalized-stream exclusions | `exclusion-rule.json` (synthetic `go-tokens-exclusion-test`, 5 vectors). Checker: `tokenIndices` against the declared exclusions; per-channel positions, spans and counts; status from the exact count; the exclusion pair (exact differs, normalized identical); an `ok` input with an empty normalized channel. It rejects 4 corruptions (exclusions ignored, normalized spans from exact positions, status from the normalized count, `tokenIndices` omitted) and rejects `tokenIndices` on Go/Rust. All accepted TypeScript draft-2 vectors are recomputed under the same rule |
| §10a complexity | Not machine-checked by these tools. The cross-check's adversarial inputs measure it; the bound is derived above |
| Delimiter balance | Checker (accepted vectors); `rust-err-unbalanced` |
| Closed error-code lists | Checker per profile; invented-code mutation |
| Lexical error offsets | Checker: the character at the offset can start that construct (plausibility). Crosscheck: equal to the toolchain offset, or a listed divergence with its reason |
| Normalization (§6), k-grams, hash, winnowing, ties, duplicates, partial window | Checker recomputes everything; `*-equal-minimum`, `*-repeated`, `*-empty`, `*-short`, `*-exact-k`; hash and tie mutations |
| Comment/whitespace invariance; rename behavior | `*-format-a/b` and `*-rename-a/b` pair invariants |

**Mutation self-test.** The checker must reject 13 Go and 14 Rust corruptions (each count includes `tokenIndices` emitted by a profile without exclusions). Hashes are recomputed so that only the targeted layer is wrong. The corruptions include the reviewer's five: a dropped inserted `;`, `func` relabelled `ident`, `:=` split, `;` after `,`, and an invented error code. They also include U+2160 accepted as a Go letter, `0b2i` accepted as imaginary, `"x"_` split into string plus `_`, `"x"0` as one suffixed string, `->` as one token, U+2E2F accepted as XID, a lifetime relabelled `char`, and a shebang look-ahead that skips `///`.

**Limits.** The checker validates given token streams and does not produce them. It cannot prove that a different, equally self-consistent tokenization is wrong where the contract's rules are not encoded in it: escape validity, raw-string termination and most error kinds. The crosscheck covers those only for the shipped inputs.

## 14. Decisions

**Decided in draft, pending owner confirmation.** Each of these changes token bytes, hashes or accept/reject, and the vectors encode them. These are the reviewer's recommended options:

| ID | Decision | Reason |
| --- | --- | --- |
| OD-1 | (a) Reject a BOM anywhere, including offset 0 | No offset shift, no repair; same rule for both profiles |
| OD-2 | (a) Rust rejects NUL and isolated CR | Uniform with Go; avoids CR-in-literal rules |
| OD-3 | (a) Reject non-NFC Rust identifiers, suffixes and lifetime names, using the pinned §3a NFC data | Normalizing would break `text == input[span]` |
| OD-4 | (a) Rust single-character punctuation | Matches rustc_lexer and proc_macro; white space never changes the stream. Cost: `&&` and `& &` collide |
| OD-5 | (a) Drop Rust doc comments | Documentation edits do not change fingerprints |
| OD-6 | (a) An inserted Go `;` is identical to an explicit `;` | Same token in the Go grammar; layout independence |
| OD-7 | (a) Normalized channel erases identifiers and literals and keeps the class; **Go predeclared identifiers are erased** | Rename robustness; the exact channel preserves names. Not scope-aware (§12) |
| OD-8 | (a) A partial window selects its rightmost minimum and sets the flag | Short fragments stay comparable and are flagged |
| OD-9 | (a) Exact text is original bytes | Keeps `text == input[span]` |
| OD-10 | (a) k = 5, w = 4, frozen as experimental | Inside `configSha256`; tuning means a new digest under TW-05 |
| OD-11 | (a) SHA-256 truncated to 64 bits, **unkeyed** and labelled as such | Standard and widely implemented |
| OD-12 | (a) Unicode 17.0.0, bound to UCD file digests (§3a) | Go 1.27 and the Reference agree; library drift is excluded |
| OD-13 | (a) Lexical errors report the token start | Already encoded by `go-err-malformed-number` and `go-err-invalid-escape` |
| OD-15 | Yes: harnesses shipped in `extraction/harness/` | Coordinator decision; needed for the F1 byte-agreement claim |
| OD-16 | (a) Keep every selected position | Multiplicity semantics belong to M2 |
| OD-17 | (a) Accept any lexically valid suffix, with the Reference `_` cut (F2) | Matches the Reference lexer and rustc |
| OD-18 | (a) `maxInputBytes` in the configuration, 1 MiB in the shipped configurations | Bounded; covered by the limit vectors |

| Q1–Q12 | The rulings in §15's second table | Each follows rustc, cmd/compile or the Reference grammar where they agree. Where they disagree, the authority (Reference or Go spec) wins and the oracle difference is a listed crosscheck divergence |
| OD-21 | `k ≤ 16`, `window ≤ 128`, `maxInputBytes ≤ 8 MiB`; linear time and memory for a fixed configuration (§10a) | Bounded worst case (about 16 GiB of SHA-256 input at the bounds); the cross-check showed unbounded `k` is a denial-of-service vector |
| OD-23 | Profiles may declare normalized-stream exclusions; per-channel streams, positions and counts; `tokenIndices` recorded only for such profiles (§6) | Lets `ts-tokens` drop `;` from `normalized` (TSOD-13, TSOD-5b (c)) without changing any Go/Rust byte. Smallest change: no new configuration key, no change for profiles without exclusions |
| OD-22 | `unsupported-config` and `input-too-large` leave the uncomputed values `null` (§9) | The input is not examined or not fully read; no implementation should read gigabytes just to report a limit |

**Still open:**

- **OD-10 tuning.** Which values follow 5/4, chosen on development data (TW-05). Each choice is a new configuration digest.
- **OD-11 keyed variant.** Options: (a) none; (b) HMAC-SHA-256 under a separate hash identifier. This waits for the keyed-selection gate in the [roadmap](../ROADMAP.md).
- **OD-14 eligible files.** Generated, vendor, test, `build.rs` and macro-heavy files. Belongs to TW-01/TW-03.
- **OD-20 Contract identifier after the bounds change** (new). Options:
  - (a) Keep `traceweave-token-winnow-draft-1` (current). No shipped expected output changed, and [matching vectors](../test-vectors/matching/README.md) pins the draft-1 configuration digests.
  - (b) Bump to `draft-2`. Configurations accepted by draft-1 but now rejected (k > 16, window > 128, `maxInputBytes` > 8 MiB) would then never meet two different outcomes under one identifier. All configuration digests would change, and the matching vectors would need regenerating.
- **OD-19 U+200D/U+200C in Rust identifiers** (new). Options:
  - (a) Follow the Reference [ident.zero-width-chars] and reject them (current draft).
  - (b) Follow rustc 1.97.1, which accepts them with an `uncommon_codepoints` warning.

  The authority and the oracle disagree, and the crosscheck lists this divergence.

## 15. Review dispositions

| Finding | Resolution |
| --- | --- |
| F1 | Harnesses shipped (`harness/go`, `harness/rust` with `Cargo.lock`, `harness/crosscheck.py`; offline run command in the [README](../test-vectors/extraction/README.md)). The checker now recomputes Go semicolon insertion, enforces closed code lists and keyword classes, and checks identifiers, operators, numbers and literal suffixes. It rejects the reviewer's five corruptions plus six more per language |
| F2 | §5.4 and §5.5 now use the Reference SUFFIX with the `_` cut. Vectors `rust-err-string-underscore-suffix`, `rust-err-char-underscore-suffix` and `rust-literal-suffixes` |
| F3 | §3a binds the UCD 17.0.0 files and the derived table by digest, forbids library defaults, and is backed by boundary vectors for U+2160, U+00B7, U+0345, U+2E2F, U+200D and U+0660, plus non-NFC suffix and raw-identifier vectors |
| F4 | Catch-all removed (§2). `unsupported-config` added, with ordering (§3 step 0), validation steps, bounds, charset and channel rule (§10). A1 and A4 resolved in §8 |
| F5 | Order NFC, then zero-width, then prefix, with token-start offsets (§5.3). Vector `rust-err-non-nfc-before-quote` |
| F6 | OD-13 decided (a) |
| F7 | A2 stated (§3, §6). `profileVersion` added and mapped to core (§10). Non-scope-awareness repeated in §12. Config negatives added. Shebang with unterminated comment decided (§5.2) |
| F8 | Vectors for `input-too-large` and its precedence, mid-file BOM, Go hex-float error, CR in a Go raw string, Rust raw lifetime and reserved raw lifetime, `##`, C-string escapes, more than 255 hashes, and isolated CR inside a literal |
| A3 | §7 names `profile`/`profileVersion` as the configuration strings |
| Version pinning | Adopted: profile ids omit toolchain versions; versions change only with lexical rules or tables (§10) |

**Amendment: two-implementation cross-check (Rust and Go lanes, 2026-11-22).** Both lanes reproduced every vector. Over 9.88 M differential cases they disagreed only on Q8. The rulings below are "decided in draft, pending owner confirmation" (row Q1–Q12 in §14). Every existing vector's expected result is unchanged.

| Question | Ruling | Vectors |
| --- | --- | --- |
| Q1 raw-string end | First `"` followed by n `#`; extra `#` lexed after it (§5.5) | `rust-q1-raw-extra-hash`, `rust-q1-raw-extra-pounds` |
| Q2 unclosed opener vs later error | Scan order; the end-of-input delimiter check applies only if scanning finished (§3 step 4) | `rust-q2-open-then-unterminated`, `-open-then-illegal`, `-unclosed-innermost` |
| Q3 `b'a` at end of input | Char and byte literals have no unterminated state: `malformed-literal` (§5.5) | `rust-q3-byte-unclosed` |
| Q4 C-string escapes | `\x01`–`\xFF` and nonzero `\u{…}` allowed; every zero spelling malformed (§5.5) | `rust-q4-cstring-xff`, `-x00`, `-u-zero`, `rust-err-cstring-nul-escape` |
| Q5 `'r#a#` | Not reserved: raw lifetime then `#` (§5.3 step 5) | `rust-q5-raw-lifetime-hash` |
| Q6 lifetime check order | NFC, then zero-width, then `#` (§5.3 step 5) | `rust-q6-lifetime-nfc-first`, `rust-q6-lifetime-zwj-before-hash` |
| Q7 unterminated vs malformed | Escape-aware end first, then content (§5.5) | `rust-q7-unterminated-escape`, `-closed-bad-escape`, `-raw-byte-unterminated` |
| Q8 shebang look-ahead over doc comments (the one divergence) | Reference SHEBANG and rustc: doc comments are content and end the look-ahead (§5.2). The Go lane's reading; the Rust lane must change | `rust-q8-shebang-outer-line-doc`, `-inner-line-doc`, `-outer-block-doc`, `-inner-block-doc`, `rust-q8-not-shebang-four-slashes`, `-empty-block`, `-three-stars` |
| Q8b look-ahead white space; bare `#!` | 11 Pattern_White_Space characters; bare `#!` is a shebang (§5.2) | `rust-q8b-shebang-lookahead-nel`, `rust-q8b-bare-shebang` |
| Q9 `assigned` table | Informative only; unassigned code points are `illegal-character` (§3a) | `go-q9-unassigned`, `rust-q9-unassigned` |
| Q10 `unsupported-config` record | `profile`, `profileVersion`, input digest and length `null`; offset `null`. Envelope names belong to TW-03 (§9) | `expectedResult` on all 28 negatives in `config-negative.json` |
| Q11 shebang line 1 only; literal then digit; `0b2i`/`0o9i` | Shebang ends at the first LF (§5.2); a digit cannot start a SUFFIX (§5.5); radix-imaginary forms malformed (§4.4) | `rust-q11-shebang-first-line-only`, `rust-s1-*` (7), `go-q11-imag-binary-digit`, `go-q11-imag-octal-digit` |
| Q12 Go `/*line :*/` | Plain comment (§4.6); listed go/scanner divergence | `go-q12-line-directive` |
| C1 unbounded `k`/`window` | Bounds and complexity (§10a, OD-21) | `cfg-k-above-bound`, `cfg-window-above-bound`, `cfg-max-above-bound`; `boundaryPositives` |
| R6 reading before the size check | Size checked before reading where knowable; never read past `maxInputBytes + 1` (§3 step 1) | `*-limit-*` (behavioral; reading is not observable in a vector) |
| S1 checker false rejection | `check_vectors.py` now forbids only a SUFFIX start (`_` or XID_Start) after an unsuffixed literal | `rust-s1-*`: the previous checker failed all 7; the current one passes them |
| TSOD-13 normalized-stream exclusions (TypeScript profile request) | §6 rule, per-channel streams in §7–§9 (OD-23); Go and Rust declare none, so their vectors, records and configuration digests are unchanged | `exclusion-rule.json` (`excl-*`, 5); the TypeScript draft-2 vectors are the real-profile evidence |
| S2 harness defects | (a) the Go oracle emits base64; (b) proc-macro2 tokens starting inside a doc comment are dropped; (c) rustc keeps the BOM and shebang line at file start and wraps only the rest | `go-escapes-vt-raw` (the old harness crashed on it), `rust-doc-comment-bracket` (the old filter kept a synthesized `]`), `rust-shebang-unresolved-body` and the `rust-q8-*` inputs (the old harness reported false rustc rejections) |
