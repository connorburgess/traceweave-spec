# Draft extraction vectors (revision draft-1)

Status: draft for review, 2026-11-22. These vectors accompany the [draft extraction contract](../extraction-contract.md), revised after the [clean-room review](../extraction-contract-review.md). They are research fixtures, not files in `test-vectors/`, and they make no detection-accuracy claim.

## Files

| File | Contents |
| --- | --- |
| `config-go.json`, `config-rust.json` | Exact configuration bytes (contract §10), 1 MiB limit. Do not reformat: the digest covers the trailing LF. |
| `config-go-limit16.json`, `config-rust-limit16.json` | The same with `maxInputBytes` 16, used by the limit files |
| `config-negative.json` | 25 configuration byte strings that MUST be rejected as `unsupported-config` |
| `go.json` | 29 vectors for `go-tokens`/`draft-1`: 14 accepted inputs and 15 errors |
| `rust.json` | 43 vectors for `rust2024-tokens`/`draft-1`: 20 accepted inputs and 23 errors |
| `limits-go.json`, `limits-rust.json` | 3 vectors each: exactly the limit, over the limit, and over the limit plus another defect, showing the size check runs first |
| `unicode-17.0.0-tables.json` | Pinned identifier tables derived from UCD 17.0.0 (contract §3a), SHA-256 `9363b97e…3ac29f` |
| `check_vectors.py` | Independent checker, standard library only |
| `harness/` | Toolchain cross-check: Go oracle, Rust oracle with `Cargo.lock`, the driver `crosscheck.py`, and the table generator `gen_unicode_tables.py` |

Every vector has an `id`, `tags`, a `description`, `inputBase64` (the authoritative bytes) and `inputText`. `inputText` is the readable text, or `null` when the bytes are not UTF-8, in which case `inputDisplay` shows a backslash-escaped form. The `result` object holds one of the following:

- **`status: "error"`** with `error.code` and `error.offset`, and nothing else.
- **`status: "ok"` or `"insufficient-tokens"`** with:
  - `tokens`: each has `class`, `text` and a half-open byte `span`, and Go adds `inserted: true` for automatic semicolons;
  - one object per channel, `exact` and `normalized`. Each holds `kgrams` (position, 16-hex-digit hash, span), `windowSelections`, `partialWindow` and `fingerprints`. `normalized` also lists the normalized `values`.

The table shows which case each vector covers:

| Case | Go | Rust |
| --- | --- | --- |
| Empty / shorter than k / exactly k | `go-empty`, `go-short`, `go-exact-k` | `rust-empty`, `rust-short`, `rust-exact-k` |
| Unicode identifiers, multi-byte literals | `go-unicode` | `rust-unicode` |
| Identifier boundaries (§3a) | `go-unicode-boundary` (U+2E2F, U+0660 accepted); `go-err-u2160`, `-u00b7`, `-u0345`, `-u200d`, `-nd-start` | `rust-unicode-boundary` (U+2160, U+00B7, U+0345 accepted); `rust-err-u2e2f`, `-u200d`, `-non-nfc-*` |
| Repeated tokens, equal-minimum ties | `go-repeated`, `go-equal-minimum` | `rust-repeated`, `rust-equal-minimum` |
| Comment/whitespace pair; rename pair | `go-format-a/b`; `go-rename-a/b` | `rust-format-a/b` (CRLF, nested comment); `rust-rename-a/b` |
| Language specifics | `go-literals`, `go-semicolon-comments`, `go-raw-string-cr` | `rust-literals`, `rust-literal-suffixes`, `rust-lifetimes-chars`, `rust-raw-lifetime`, `rust-cstring-escapes`, `rust-shebang`, `rust-shebang-unterminated-comment`, `rust-inner-attribute`, `rust-doc-comment` |
| Encoding errors | `go-err-invalid-utf8`, `-bom`, `-mid-bom`, `-nul` | `rust-err-invalid-utf8`, `-bom`, `-mid-bom`, `-nul`, `-isolated-cr`, `-cr-in-literal` |
| Lexical errors | `go-err-unterminated-*`, `-illegal-character`, `-malformed-number`, `-invalid-escape`, `-hex-float-no-exponent` | `rust-err-unterminated-*`, `-unbalanced`, `-char-two-codepoints`, `-reserved-prefix`, `-reserved-raw-lifetime`, `-pounds`, `-*-underscore-suffix`, `-cstring-nul-escape`, `-raw-too-many-hashes` |

**Hand-check example** (`go-equal-minimum`, input `x++\nx++\nx++\nx++\n`, tokens `x ++ ;` repeated four times, exact channel). The 8 k-gram hashes repeat with period 3: `55e1d04e…`, `d4aafb7b…`, `1d99e08d…`, and so on. The window at positions 2–5 holds `1d99e08d…` at both 2 and 5. The rightmost rule selects 5. The selections are `[2, 2, 5, 5, 5]`, so the fingerprints are at `[2, 5]`.

## 1. Checker: `check_vectors.py`

```
python3 -I research/drafts/extraction-vectors/check_vectors.py
```

Output on 2026-11-22 (Python 3.14.6, `unicodedata` 16.0.0):

```
PASS config-negative.json: 25/25 invalid configurations rejected
PASS go.json profile=go-tokens/draft-1 config=dfbc5fe3517e9da6... vectors=29 tokens=164 (inserted ';'=20) identifiers=60 kgrams=224 fingerprints=80 tie-windows=11 errors=15 (lexical offsets plausibility-only: 11) pairs=2 mutations-rejected=11/11
PASS rust.json profile=rust2024-tokens/draft-1 config=64b34335e4a61383... vectors=43 tokens=259 (inserted ';'=0) identifiers=90 kgrams=366 fingerprints=134 tie-windows=10 errors=23 (lexical offsets plausibility-only: 17) pairs=2 mutations-rejected=11/11
PASS limits-go.json profile=go-tokens/draft-1 config=aa86722255afbf50... vectors=3 tokens=8 (inserted ';'=1) identifiers=1 kgrams=8 fingerprints=2 tie-windows=0 errors=2 (lexical offsets plausibility-only: 0) pairs=0
PASS limits-rust.json profile=rust2024-tokens/draft-1 config=71d5ed27bea011f6... vectors=3 tokens=7 (inserted ';'=0) identifiers=2 kgrams=6 fingerprints=2 tie-windows=0 errors=2 (lexical offsets plausibility-only: 0) pairs=0
```

The checker verifies the following:
- **Configuration:** the §10 validation rules, the shipped digests, and rejection of every negative configuration.
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
  - literal prefix, closing delimiter and the suffix `_` cut;
  - delimiter balance.
- **Trivia:** every gap between tokens is whitespace, comments or a shebang, including the shebang rule with an unterminated look-ahead comment.
- **Fingerprints:**
  - normalized values, k-gram bytes and the SHA-256 first-8 hash;
  - winnowing as a sort-based selection by `(hash, −position)`;
  - the partial-window flag and fingerprint deduplication;
  - the comment/whitespace and rename pair invariants;
  - coverage of every required case.

**Mutation self-test.** The checker corrupts copies of the data, recomputing hashes so that only the targeted layer is wrong, and requires every copy to be rejected. Per language, these are the corruptions:

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
  - U+2160 accepted as a Go letter.
- **Rust only:**
  - `"x"_` split into string and `_`;
  - `->` as one token;
  - U+2E2F accepted as XID;
  - lifetime relabelled `char`.

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
python3 -I research/drafts/extraction-vectors/harness/crosscheck.py [--build-dir DIR]
```

**Requirements.** go 1.27.x and cargo/rustc 1.97.x on PATH. proc-macro2 1.0.107 and unicode-ident 1.0.24 must already be in the local cargo registry cache.

**What it runs.** It builds `harness/go` with `GOTOOLCHAIN=local` and `harness/rust` with `cargo build --offline --locked`, into `DIR`, which defaults to a new temporary directory. Nothing is downloaded or installed, and the repository is not written. It then performs these comparisons:

- **Tables:** Go's `unicode` package (letter + `_`, Nd) and `unicode-ident` 1.0.24 (XID) are compared with `unicode-17.0.0-tables.json` over every code point.
- **go/scanner** (mode 0), for every Go vector:
  - Class, text and start offset of each token are compared.
  - Declared adjustments: inserted `;` is compared by kind and order only, and CR is removed from raw strings because go/scanner strips it.
- **proc-macro2** fallback lexer, for every Rust vector:
  - Class (literal classes excluded), text, start and end offsets are compared.
  - Declared adjustments: a `'` followed by an adjacent identifier becomes a lifetime; tokens whose source bytes differ from their text (synthesized from doc comments) are dropped; a shebang is blanked to spaces with offsets kept.
- **rustc `--edition 2024`:**
  - Each input is wrapped in a `macro_rules!` invocation, or compiled unwrapped if it starts with `#!` or a BOM.
  - This checks lexical acceptance only.
- **Errors:** every error vector must fail in each tool at the same offset, or appear in the `EXPECT` table with a reason. An unlisted difference, or an expectation that no longer happens, fails the run.

Output on 2026-11-22 (go1.27.3 darwin/arm64, rustc 1.97.1):

```
tables: go unicode + unicode-ident 1.0.24 vs pinned 17.0.0 tables: MATCH
  go accepted agree: 15
  go error agree: 11
  go error expected: 6
  rust accepted proc-macro2 agree: 21
  rust accepted rustc accepts: 21
  rust error proc-macro2 agree: 9
  rust error proc-macro2 expected: 16
  rust error rustc agree: 15
  rust error rustc expected: 10
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
  - `"x"_` and `'a'_` (F2).
- **Different offsets** (OD-13, where the contract reports the token start):
  - go/scanner reports `0x`, `\q` and `0x1.8` at the following bytes (7, 7, 10);
  - proc-macro2 reports CR-in-literal at the literal start (8), while the contract's forbidden-code-point scan reports the CR (10);
  - go/scanner reports the 0xFF byte (6) in `go-limit-precedence`, where the size check applies first.
- **`maxInputBytes`** has no toolchain counterpart (the limit vectors).

### Self-test of the driver

A copy of the vectors with `:=` split in `go-unicode` and `"x"_a` truncated in `rust-literal-suffixes` made the driver report both mismatches under `PROBLEMS`.

### History

The first, unshipped cross-check resolved proc-macro2's `unicode-ident` dependency to 1.0.27, which is Unicode 18. `Cargo.toml` now pins `=1.0.24`, and `Cargo.lock` (SHA-256 `02e4a101…d7b201`) records it. In the first revision, the cross-check also caught a wrong offset in `rust-err-invalid-utf8` (9 → 10).

**Scope limit.** Agreement on these inputs does not validate the contract's lexer description in general. Constructs with no vector include most individual escapes, Go octal/hex escape bounds and Rust byte-string escape limits.

## 3. Unicode tables: `harness/gen_unicode_tables.py`

```
python3 -I research/drafts/extraction-vectors/harness/gen_unicode_tables.py UCD_DIR OUT.json
```

`UCD_DIR` must contain the four UCD 17.0.0 files named in contract §3a, downloaded from <https://www.unicode.org/Public/17.0.0/ucd/>. The script refuses any file whose SHA-256 differs. On 2026-11-22 it reproduced `unicode-17.0.0-tables.json` byte for byte. The UCD files are not committed: they are public and pinned by digest.

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
