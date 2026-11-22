# Draft TypeScript/JavaScript extraction vectors (revision draft-1)

Status: draft for review, 2026-11-22. These vectors go with the [draft TypeScript/JavaScript profile](../extraction-profile-typescript.md), which plugs into the [extraction contract](../extraction-contract.md). They are research fixtures, not files in `test-vectors/`, and they make no detection-accuracy claim.

## Files

| File | Contents |
| --- | --- |
| `config-ts.json`, `config-tsx.json` | Exact configuration bytes (contract §10) for `ts-tokens` and `tsx-tokens`, 1 MiB limit. Do not reformat: the digest covers the trailing LF |
| `config-ts-limit16.json` | `ts-tokens` with `maxInputBytes` 16, used by `limits-ts.json` |
| `config-negative-typescript.json` | 14 configuration byte strings that MUST be rejected as `unsupported-config` (base64) |
| `ts.json` | 61 vectors for `ts-tokens`/`draft-1`: 34 accepted, 27 errors |
| `tsx.json` | 25 vectors for `tsx-tokens`/`draft-1`: 16 accepted, 9 errors |
| `limits-ts.json` | 3 vectors: exactly the limit, over it, and over it with a BOM (size is checked first) |
| `tslex.py` | The checker's lexer, written from the profile text |
| `check_vectors.py` | Checker, standard library only |
| `harness/vector_sources.py` | **The hand-derived token streams and error results**, token by token |
| `harness/build_vectors.py` | Adds spans, k-grams, hashes and winnowing to the hand-written streams. It does not lex |
| `harness/derive_deltas.py` | Re-derives the ID/XID deltas and Zs from the digest-pinned UCD 17.0.0 files |
| `harness/crosscheck.js`, `harness/lex_json.py` | Cross-check against TypeScript 6.0.3 |
| `harness/package.json`, `harness/package-lock.json` | Pin `typescript@6.0.3` for the cross-check. `node_modules/` is git-ignored |

The Unicode identifier table is the shared, read-only [unicode-17.0.0-tables.json](../extraction-vectors/unicode-17.0.0-tables.json) (SHA-256 `9363b97e…3ac29f`), which `tslex.py` checks by digest.

**Vector format.** The format is the same as the [Go/Rust vectors](../extraction-vectors/README.md). Each vector has these fields:
- `id`, `derivation: "hand"`, `tags` and `description`;
- `inputBase64` (authoritative) and `inputText`;
- a `result`: either `status: "error"` with `error.code` and `error.offset`, or `status: "ok"` / `"insufficient-tokens"` with `tokens` (class, text, byte span) and the `exact` and `normalized` channels (k-grams, `windowSelections`, `partialWindow`, fingerprints, and normalized `values`).

Every accepted vector names a `pairedRejection`: an error vector that exercises the same rule.

**Coverage**

| Case | Vectors |
| --- | --- |
| Empty / below k / exactly k / repeated with ties | `ts-empty`, `ts-short`, `ts-exact-k`, `ts-repeated` |
| Comment/whitespace pairs (CRLF, LS, block comment); rename pair | `ts-format-a/b`, `tsx-format-a/b`; `ts-rename-a/b` |
| Regex vs division | `ts-regex-after-header`, `ts-division-after-paren`, `ts-regex-class-slash`, `ts-regex-after-keyword`, `ts-nonnull-division`, `ts-postfix-division`, `ts-type-assertion`, `tsx-plain-js`, `tsx-regex-in-container`, `ts-err-unterminated-regex`, `ts-err-regex-class` |
| Templates | `ts-template-nested`, `ts-template-escapes`, `tsx-template-in-jsx`, `ts-err-unterminated-template`, `ts-err-unterminated-substitution` |
| JSX vs type arguments and comparison | `tsx-element`, `tsx-text-comment-keywords`, `tsx-attr-keyword-names`, `tsx-fragment-nested`, `tsx-comparison-vs-jsx`, `tsx-generic-arrow`, `tsx-generic-arrow-const`, `tsx-extends-attribute`, `tsx-text-whitespace`, `tsx-attr-element-value`, `tsx-comment-container`, `tsx-err-*` |
| `>` `>>` `>>>` | `ts-generics-gt`, `ts-shift-ops` |
| Hashbang; HTML-like comments; no ASI | `ts-hashbang`, `ts-err-hashbang-not-first`; `ts-html-comment`, `tsx-err-html-comment`; `ts-no-asi` |
| Numbers, separators, BigInt, legacy octal | `ts-numbers`, `ts-bigint`, `ts-legacy-octal`, `ts-err-number-ident`, `-separator`, `-bigint-fraction`, `-legacy-bigint`, `-number-dot-ident`, `-hex-empty` |
| Private names; optional chaining; decorators | `ts-private-names`, `ts-err-private-bad-escape`, `ts-err-hash`; `ts-optional-chaining`; `ts-decorators` |
| Unicode escapes; boundaries; LS/PS | `ts-unicode-escape-ident`, `ts-err-ident-escape-digit`, `ts-err-surrogate-escape`; `ts-unicode-boundary` (U+2160, U+00B7, U+0345, U+200D, U+309B, U+00A0), `ts-err-u2e2f`, `ts-err-u180e`; `ts-line-terminators` |
| Keywords, contextual words, property names | `ts-contextual-keywords`, `ts-property-keywords` |
| Strings | `ts-strings`, `ts-err-unterminated-string`, `ts-err-string-bad-hex`, `ts-err-unterminated-before-malformed` |
| Encoding, size, delimiters, comments | `ts-err-invalid-utf8`, `-bom`, `-nul`, `ts-limit-*`, `ts-err-unbalanced-closer`, `ts-err-unclosed`, `ts-err-unterminated-comment`, `ts-err-backslash` |
| Known limitation | `tsx-err-generic-type-position` |

## 1. Checker

```
python3 -I research/drafts/extraction-vectors-typescript/check_vectors.py
```

Output on 2026-11-22 (Python 3.14.6):

```
PASS config-negative-typescript.json: 14/14 invalid configurations rejected
PASS ts.json profile=ts-tokens/draft-1 config=69d1e98bc8e0d52c... vectors=61 tokens=460 kgrams=329 fingerprints=238 tie-windows=23 errors=27 (code and offset re-derived) pairs=2 classes=12
PASS tsx.json profile=tsx-tokens/draft-1 config=6a7f8184ff2ab1d1... vectors=25 tokens=353 kgrams=289 fingerprints=213 tie-windows=0 errors=9 (code and offset re-derived) pairs=1 classes=9
PASS limits-ts.json profile=ts-tokens/draft-1 config=b4f9f6347726610e... vectors=3 tokens=7 kgrams=3 fingerprints=2 tie-windows=0 errors=2 (code and offset re-derived) pairs=0 classes=3
PASS every accepted vector has derivation=hand and a pairedRejection that is an error vector
PASS mutation self-test: 25/25 corruptions rejected (23 lexical)
```

**What it checks.**
- **Configuration:** contract §10 validation, the shipped digests, and rejection of the 14 negatives.
- **Shared pre-lexing checks:** size, UTF-8, BOM and NUL, recomputed from the input bytes.
- **Re-lexing:** every input is lexed with `tslex.py`. Class, text and byte span of every token, and the code and offset of every error, must be identical.
- **Invariants on the recorded stream,** independent of `tslex.py`:
  - closed class and error-code lists;
  - `keyword` only for the 46 listed words, never after `.` or `?.`, and a reserved word classed `ident` only in a property position (`ts-tokens`);
  - punctuator membership and longest match, with the `?.`+digit exception;
  - regex, template, number and `jsx-text` token shapes;
  - `text == input[span]`, and ordered non-empty spans.
- **Fingerprints:** normalized values, LP-encoded k-gram bytes, SHA-256 first-8 hashes, and winnowing by a sort on `(hash, −position)`. This is a different formulation from the builder's loop.
- **Pairs:** format pairs have equal streams and exact hashes. The rename pair has equal normalized hashes and different exact hashes.
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

The other two are a leftmost tie and a flipped hash bit, left unrehashed.

**Limits.** The hand-written streams and `tslex.py` were written by the same author from the same text. Their agreement shows the profile text was applied consistently. It does not show that two independent readers would agree; that is TS.3.

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

Run on 2026-11-22 (Node 22.23.2, TypeScript 6.0.3):

| Part | Result |
| --- | --- |
| Accepted vectors (51) | **51 agree**: 47 against the parser, 4 against the raw scanner (`ts-html-comment`, `ts-legacy-octal`, `ts-unicode-escape-ident`, `ts-strings`, where TypeScript reports syntax or strict-mode diagnostics); 2 `gt-merge` |
| Lexical error vectors (33) | 32 also rejected by TypeScript: 16 with a diagnostic at the same offset, 16 at another offset (TypeScript reports at the failing character; the profile at the token start, OD-13). 1 accepted by TypeScript: `tsx-err-generic-type-position` (profile D-11) |
| Pre-lexing error vectors (5) | Not compared. TypeScript accepts the BOM and NUL inputs (profile D-9) |
| Corpus: all `lib/*.d.ts` (`ts-tokens`) and `lib/*.js` (`tsx-tokens`) of the pinned package | **119/119 files agree**: 19,799,782 bytes, 2,478,321 tokens, 71 `gt-merge`. The corpus is compiler-emitted JavaScript and declaration files, with no JSX |
| Probes (39 inputs in `crosscheck.js`) | 25 agree as expected, 14 diverge exactly as documented (D-3, D-4, D-6 to D-11), 0 unexpected |
| Unicode sweep (every scalar value) | Identifier start: 8,949 code points differ; identifier part: 9,132. All are accepted by the profile (Unicode 17.0.0) and rejected by TypeScript's older tables (D-8). White space: U+0085 and U+200B (D-6). Line terminators: 0 |

**Deliberate divergences** are listed with reasons in [profile §9](../extraction-profile-typescript.md#9-deliberate-divergences) (D-1 to D-13), and every one that a probe can show is a probe in `crosscheck.js`.

**Harness defects found and fixed during this run:**
- Zero-width `OmittedExpression` nodes (array holes) were first reported as divergences in `_tsc.js` and `typescript.js`. They are now skipped.
- The checker's own lexer had a header-flag bug (the flag aliased the token list), found by a sanity input before the vectors existed.

## 3. Rebuilding

```
python3 -I harness/build_vectors.py          # rewrites ts.json, tsx.json, limits-ts.json and the three configs
python3 -I harness/derive_deltas.py UCD_DIR  # UCD 17.0.0 UnicodeData.txt and DerivedCoreProperties.txt
```

The builder is deterministic. Edit token streams only in `harness/vector_sources.py`, then re-run the checker and the cross-check.
