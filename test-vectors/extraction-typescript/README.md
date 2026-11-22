# Draft TypeScript/JavaScript extraction vectors (revision draft-2)

Status: experimental draft, normative for conformance of this draft version; decided-in-draft items confirmed by the owner's delegation on 2026-11-23.

Vector status: **`ts-tokens` vectors are frozen** (draft-2). **`tsx-tokens` vectors (`tsx.json`, `config-tsx.json`) are a deferred draft and are not normative.**

Revision status: draft for review, 2026-11-22, **draft-2**. Draft-2 resolves the [review](../../reviews/extraction-profile-typescript-review.md) of draft-1, and the changes are listed in [profile §16](../extraction-profile-typescript.md#16-changes-from-draft-1-to-draft-2). These vectors go with the [draft TypeScript/JavaScript profile](../extraction-profile-typescript.md), which plugs into the [extraction contract](../extraction-contract.md). **`ts-tokens` (`ts.json`, `limits-ts.json`) is stage 1 and frozen for stage-1 implementation, pending owner confirmation of the decided-in-draft items. The digests are in [profile §17](../extraction-profile-typescript.md#17-freeze-record-ts-tokens-draft-2). `tsx-tokens` (`tsx.json`) is deferred:** it is kept as a draft and is not to be frozen yet (profile TSOD-1). They are research fixtures, not files in `test-vectors/`, and they make no detection-accuracy claim.

## Files

| File | Contents |
| --- | --- |
| `config-ts.json`, `config-tsx.json` | Exact configuration bytes (contract §10) for `ts-tokens` and `tsx-tokens`, 1 MiB limit. Do not reformat: the digest covers the trailing LF |
| `config-ts-limit16.json` | `ts-tokens` with `maxInputBytes` 16, used by `limits-ts.json` |
| `config-negative-typescript.json` | 19 configuration byte strings that MUST be rejected as `unsupported-config` (base64) |
| `ts.json` | 77 vectors for `ts-tokens`/`draft-2`: 46 accepted, 31 errors |
| `tsx.json` | 33 vectors for `tsx-tokens`/`draft-2` (deferred): 21 accepted, 12 errors |
| `limits-ts.json` | 3 vectors: exactly the limit, over it, and over it with a BOM (size is checked first) |
| `tslex.py` | The checker's lexer, written from the profile text. Its policy methods are the rule choices that wrong-lexer variants override |
| `check_vectors.py` | Checker, standard library only |
| `harness/vector_sources.py` | **The hand-derived token streams and error results**, token by token |
| `harness/build_vectors.py` | Adds spans, k-grams, hashes and winnowing to the hand-written streams. It does not lex |
| `harness/derive_deltas.py` | Re-derives the ID/XID deltas and Zs from the digest-pinned UCD 17.0.0 files |
| `harness/crosscheck.js`, `harness/lex_json.py` | Cross-check against TypeScript 6.0.3 |
| `harness/semi_survival.py` | Measures normalized-fingerprint survival of a semi→no-semi reformat (profile §4.10) |
| `harness/package.json`, `harness/package-lock.json` | Pin `typescript@6.0.3` for the cross-check. `node_modules/` is git-ignored |

The Unicode identifier table is the shared, read-only [unicode-17.0.0-tables.json](../extraction-vectors/unicode-17.0.0-tables.json) (SHA-256 `9363b97e…3ac29f`), which `tslex.py` checks by digest.

**Vector format.** The format is the same as the [Go/Rust vectors](../extraction-vectors/README.md). Each vector has these fields:
- `id`, `derivation: "hand"`, `tags` and `description`;
- `inputBase64` (authoritative) and `inputText`;
- a `result`: either `status: "error"` with `error.code` and `error.offset`, or `status: "ok"` / `"insufficient-tokens"` with `tokens` (class, text, byte span) and the `exact` and `normalized` channels (k-grams, `windowSelections`, `partialWindow`, fingerprints, and normalized `values`).

**The normalized channel omits `;`** (profile §6, which declares `normalizedExclusions` `punct` `;` under contract §6 / OD-23; each vector file repeats the declaration in its header). `channels.normalized.tokenIndices` lists the indices into `tokens` that it keeps, and its `values`, k-gram positions and fingerprint positions refer to that filtered stream. `status` still counts all tokens, so `ts-exact-k` is `ok` with an empty normalized channel.

Every accepted vector names a `pairedRejection`: an error vector that exercises the same rule.

**Coverage**

| Case | Vectors |
| --- | --- |
| Empty / below k / exactly k / repeated with ties | `ts-empty`, `ts-short`, `ts-exact-k`, `ts-repeated` |
| Comment/whitespace pairs (CRLF, LS, block comment); rename pair; semicolon-style pair | `ts-format-a/b`, `tsx-format-a/b`; `ts-rename-a/b`; `ts-semi-a/b` |
| `exprEnd` rows and documented departures (profile §4.9) | `ts-object-class-division`, `ts-arrow-body-regex`, `ts-newline-prefix-regex`, `ts-newline-prefix-cr-ls-ps`, `ts-yield-await-regex`, `tsx-element-division`; departures `ts-function-decl-division`, `ts-class-decl-division`, `ts-err-await-identifier` |
| JavaScript under `ts-tokens` (stage 1) | `ts-plain-js`, `ts-err-jsx-in-js`, `ts-jsx-selfclosing-in-js` (limitation D-16) |
| Regex vs division | `ts-regex-after-header`, `ts-division-after-paren`, `ts-regex-class-slash`, `ts-regex-after-keyword`, `ts-nonnull-division`, `ts-postfix-division`, `ts-type-assertion`, `tsx-plain-js`, `tsx-regex-in-container`, `ts-err-unterminated-regex`, `ts-err-regex-class` |
| Templates | `ts-template-nested`, `ts-template-escapes`, `tsx-template-in-jsx`, `ts-err-unterminated-template`, `ts-err-unterminated-substitution` |
| JSX vs type arguments and comparison (deferred) | `tsx-nbsp-text`, `tsx-attr-element-space`, `tsx-generic-const-reserved`, `tsx-extends-word`, `tsx-element`, `tsx-text-comment-keywords`, `tsx-attr-keyword-names`, `tsx-fragment-nested`, `tsx-comparison-vs-jsx`, `tsx-generic-arrow`, `tsx-generic-arrow-const`, `tsx-extends-attribute`, `tsx-text-whitespace`, `tsx-attr-element-value`, `tsx-comment-container`, `tsx-err-*` |
| `>` `>>` `>>>` | `ts-generics-gt`, `ts-shift-ops` |
| Hashbang; HTML-like comments; no ASI | `ts-hashbang`, `ts-err-hashbang-not-first`; `ts-html-comment`, `tsx-err-html-comment`; `ts-no-asi` |
| Numbers, separators, BigInt, legacy octal | `ts-numbers`, `ts-bigint`, `ts-legacy-octal`, `ts-nonoctal-separators`, `ts-err-zero-separator`, `ts-err-number-ident`, `-separator`, `-bigint-fraction`, `-legacy-bigint`, `-number-dot-ident`, `-hex-empty` |
| Private names; optional chaining; decorators | `ts-private-names`, `ts-err-private-bad-escape`, `ts-err-hash`; `ts-optional-chaining`; `ts-decorators` |
| Unicode escapes; boundaries; LS/PS | `ts-unicode-escape-ident`, `ts-err-ident-escape-digit`, `ts-err-surrogate-escape`; `ts-unicode-boundary` (U+2160, U+00B7, U+0345, U+200D, U+309B, U+00A0), `ts-err-u2e2f`, `ts-err-u180e`; `ts-line-terminators` |
| Keywords, contextual words, property names | `ts-contextual-keywords`, `ts-property-keywords` |
| Strings | `ts-strings`, `ts-err-cr-in-string`, `ts-err-unterminated-string`, `ts-err-string-bad-hex`, `ts-err-unterminated-before-malformed` |
| Encoding, size, delimiters, comments | `ts-err-invalid-utf8`, `-bom`, `-nul`, `ts-limit-*`, `ts-err-unbalanced-closer`, `ts-err-unclosed`, `ts-err-unterminated-comment`, `ts-err-backslash` |
| Known limitation | `tsx-err-generic-type-position` |

## 1. Checker

```
python3 -I research/drafts/extraction-vectors-typescript/check_vectors.py
```

Output on 2026-11-22 (Python 3.14.6):

```
PASS config-negative-typescript.json: 19/19 invalid configurations rejected
PASS ts.json profile=ts-tokens/draft-2 config=aeeed14177cd3be8... vectors=77 tokens=648 kgrams=469 fingerprints=292 tie-windows=22 errors=31 (code and offset re-derived) pairs=3 classes=12
PASS tsx.json profile=tsx-tokens/draft-2 config=4f121891d73b98b5... vectors=33 tokens=422 kgrams=338 fingerprints=254 tie-windows=0 errors=12 (code and offset re-derived) pairs=1 classes=9
PASS limits-ts.json profile=ts-tokens/draft-2 config=94403dd3e71a8105... vectors=3 tokens=7 kgrams=3 fingerprints=2 tie-windows=0 errors=2 (code and offset re-derived) pairs=0 classes=3
PASS every accepted vector has derivation=hand and a pairedRejection that is an error vector
PASS mutation self-test: 28/28 corruptions rejected (24 lexical)
PASS wrong-lexer self-test: 15/15 wrong lexers rejected (the review's 8 accepted variants V1 V5 V25 V22 V11 V21 V13 V26, plus 7 more)
```

**What it checks.**
- **Configuration:** contract §10 validation, including the §10a bounds, the shipped digests, and rejection of the 19 negatives.
- **Shared pre-lexing checks:** size, UTF-8, BOM and NUL, recomputed from the input bytes.
- **Re-lexing:** every input is lexed with `tslex.py`. Class, text and byte span of every token, and the code and offset of every error, must be identical.
- **Invariants on the recorded stream,** independent of `tslex.py`:
  - closed class and error-code lists;
  - `keyword` only for the 46 listed words, never after `.` or `?.`, and a reserved word classed `ident` only in a property position (`ts-tokens`);
  - punctuator membership and longest match, with the `?.`+digit exception;
  - regex, template, number and `jsx-text` token shapes;
  - `text == input[span]`, and ordered non-empty spans.
- **Fingerprints:** the normalized `;` filter and `tokenIndices`, normalized values, LP-encoded k-gram bytes, SHA-256 first-8 hashes, and winnowing by a sort on `(hash, −position)`. This is a different formulation from the builder's loop.
- **Pairs:** format pairs have equal streams and exact hashes. The rename and semi pairs have equal normalized hashes and different exact hashes.
- **Metadata:** `derivation: hand`, and every `pairedRejection` exists and is an error vector.

**Mutation self-test.** Each corruption is rehashed, so only the targeted layer is wrong. The lexical corruptions are:
- a regex relabelled as division;
- a nested template merged into one token;
- a substitution closed at an object literal's `}`;
- JSX text tokenized as identifiers;
- untrimmed JSX text;
- `>>` split in an expression, and in generics;
- `return` as ident; `type`, `.catch`, `if` and JSX `class` as keyword;
- `?.5` as `?.` `5`; `07.5` as one number;
- a tokenized hashbang; `<!--` as a comment; an inserted ASI `;`;
- split regex flags; a template-head relabelled;
- U+309B rejected;
- an invented error code, a moved offset, and malformed before unterminated.

Draft-2 adds a corruption that treats `++` after a line break as postfix. The four non-lexical corruptions are a leftmost tie, a flipped hash bit (both left unrehashed), a normalized channel that keeps `;`, and `tokenIndices` omitted.

**Wrong-lexer self-test** (new in draft-2). Vector corruptions cannot reveal a rule choice that no vector exercises, which the review showed with 8 accepted wrong lexers. Each wrong lexer is a `tslex.Lexer` subclass with one rule changed, substituted for the profile's lexer, and the checker must fail on the shipped vectors:
- the review's 8: V1 `}` always followed by a regex, V5 `await`/`yield` end an expression, V25 most keywords end an expression, V22 `exprEnd` false after a JSX element, V11 ASCII-only JSX trimming, V21 `<` anywhere in a tag, V13 a lone CR not ending a string, V26 `0_1` accepted;
- 7 more: the draft-1 newline rule, an LF-only newline rule (the review's W5), the draft-1 arrow-body rule, escapes in the look-ahead, no separators in a NonOctalDecimal fraction, no header marking, and `!` resetting the flag.

All 15 are rejected, each by the vector added for it. `WExtendsComment` is shipped but not counted: it is observationally equivalent to the profile (profile §5.2).

**Limits.** The hand-written streams, `tslex.py` and the wrong-lexer variants were written by the same author from the same text. The review's independent lexer reproduced the 89 draft-1 vectors and, in its confirmation pass, all 112 draft-2 vectors. `ts-newline-prefix-cr-ls-ps` was added afterwards. Their agreement shows the profile text was applied consistently. It does not show that two independent readers would agree; that is TS.3.

## 2. Cross-check against TypeScript 6.0.3

```
cd research/drafts/extraction-vectors-typescript/harness
npm ci --ignore-scripts          # installs typescript@6.0.3 into ./node_modules (git-ignored)
node crosscheck.js --corpus --probes [--json OUT]
```

If the user npm cache is not writable, add `--cache "$TMPDIR/npmcache"`. No global install is needed.

**Method.** The oracle is TypeScript's **parser**, `createSourceFile` with `ScriptKind.TS` or `TSX`, whose leaf tokens are compared by coarse class and byte span. The bare scanner cannot be the oracle, because it does not decide regex versus division, template continuation or JSX by itself. Inputs for which TypeScript reports parse diagnostics are compared against the raw scanner instead. Declared adjustments, each counted:
- **`gt-merge`:** TypeScript's separate `>` tokens are merged where the profile has `>>` and the like.
- **`jsx-trim`:** TypeScript's JsxText is trimmed with the profile's trivia set.
- **`word`:** keyword and ident compare as one class, because the profile's class is textual (§4.1).

Run on 2026-11-22, draft-2 (Node 22.23.2, TypeScript 6.0.3). Vectors tagged `departure` must diverge and are counted separately:

| Part | Result |
| --- | --- |
| Accepted vectors (68) | **59 agree with the parser** and 7 with the raw scanner (TypeScript reports syntax or strict-mode diagnostics: `ts-html-comment`, `ts-legacy-octal`, `ts-unicode-escape-ident`, `ts-strings`, `ts-nonoctal-separators`, `ts-jsx-selfclosing-in-js`, `tsx-generic-const-reserved`). 2 documented divergences (`ts-function-decl-division`, `ts-class-decl-division`). 2 `gt-merge` |
| Lexical error vectors (40) | 37 also rejected by TypeScript: 17 at the same offset, 20 at another offset (TypeScript reports at the failing character, the profile at the token start, OD-13). 3 documented divergences accepted by TypeScript: `ts-err-await-identifier` (D-15), `tsx-err-generic-type-position` (D-11), `tsx-err-lookahead-escape` (D-14) |
| Pre-lexing error vectors (5) | Not compared. TypeScript accepts the BOM and NUL inputs (D-9) |
| Corpus: all `lib/*.d.ts` and `lib/*.js` of the pinned package, all as `ts-tokens` | **119/119 files agree**: 19,799,782 bytes, 2,478,321 tokens, 71 `gt-merge`. Compiler-emitted code and declaration files only, no JSX |
| Probes (55 inputs in `crosscheck.js`) | 35 agree as expected, 20 diverge exactly as documented, **0 unexpected** |
| Unicode sweep (every scalar value) | Identifier start: 8,949 code points differ; identifier part: 9,132. All accepted by the profile (Unicode 17.0.0) and rejected by TypeScript's older tables (D-8). White space: U+0085 and U+200B (D-6). Line terminators: 0 |

**Semicolon survival** (`python3 -I harness/semi_survival.py harness/node_modules/typescript/lib/_tsc.js [42043]`). This measures the share of distinct normalized fingerprint hashes that survive deleting each `;` that ends a line:

| Input | draft-1 (`;` kept) | draft-2 (`;` dropped) |
| --- | --- | --- |
| first 42,043 tokens (the review's size; the review reports 61.1%) | 62.5% (1,769/2,831) | 100% (3,077/3,077) |
| whole file, 874,387 tokens | 67.3% (7,782/11,557) | 100% (14,177/14,177) |

**Deliberate divergences** are listed with reasons in [profile §9](../extraction-profile-typescript.md#9-deliberate-divergences) (D-1 to D-16), and every one that a probe can show is a probe in `crosscheck.js`.

**Harness defects found and fixed during this run:**
- Zero-width `OmittedExpression` nodes (array holes) were first reported as divergences in `_tsc.js` and `typescript.js`. They are now skipped.
- The checker's own lexer had a header-flag bug (the flag aliased the token list), found by a sanity input before the vectors existed.

## 3. Rebuilding

```
python3 -I harness/build_vectors.py          # rewrites ts.json, tsx.json, limits-ts.json and the three configs
python3 -I harness/derive_deltas.py UCD_DIR  # UCD 17.0.0 UnicodeData.txt and DerivedCoreProperties.txt
```

The builder is deterministic. Edit token streams only in `harness/vector_sources.py`, then re-run the checker and the cross-check.
