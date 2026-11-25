# Python extraction vectors (`py-tokens`, revision draft-1)

Status: experimental draft, normative for conformance of this draft version (promoted 2026-11-25 from `research/drafts/extraction-vectors-python/`).

Revision status: **`py-tokens` `draft-1` vectors are frozen for stage-1 implementation**; the digests are in [profile §17](../../profiles/python.md#17-freeze-record-py-tokens-draft-1). The [clean-room review](../../research/reviews/extraction-profile-python-review.md) fixes are in [profile §16](../../profiles/python.md#16-review-dispositions). These go with the [Python profile](../../profiles/python.md), which plugs into the [extraction contract](../../spec/extraction.md). They make no detection-accuracy claim.

## Files

| File | Contents |
| --- | --- |
| `config-py.json` | Exact configuration bytes (contract §10) for `py-tokens`/`draft-1`, 1 MiB limit. Do not reformat: the digest covers the trailing LF |
| `config-py-limit16.json` | The same with `maxInputBytes` 16, used by `limits-py.json` |
| `config-negative-python.json` | 20 configuration byte strings that MUST be rejected as `unsupported-config` (base64), each with its `expectedResult` |
| `py.json` | 107 vectors: 68 accepted, 39 errors |
| `limits-py.json` | 3 vectors: exactly the limit, over it, and over it with a BOM (size is checked first) |
| `pylex.py` | The checker's lexer, written from the profile text. Each rule choice is a method, so wrong-lexer variants can override one |
| `check_vectors.py` | Checker, standard library only |
| `harness/vector_sources.py` | **The hand-derived token streams and error results**, token by token |
| `harness/build_vectors.py` | Adds spans, k-grams, hashes and winnowing to the hand-written streams, and writes the configuration files. It does not lex |
| `harness/crosscheck.py` | Cross-check against the CPython 3.14.6 tokenizer: vectors, standard library, Unicode sweep, differential fuzz |
| `harness/layout_survival.py` | The normalized-channel measurement behind profile §7 (PYOD-4) |

The Unicode identifier table is the shared, read-only [unicode-17.0.0-tables.json](../extraction/unicode-17.0.0-tables.json), which `pylex.py` checks by digest.

**Vector format.** As for the [Go/Rust vectors](../extraction/README.md): `id`, `derivation: "hand"`, `tags`, `description`, `inputBase64` (authoritative), `inputText`, and a `result`, which is either `status: "error"` with `error.code` and `error.offset`, or `ok`/`insufficient-tokens` with `tokens` (class, text, byte span) and the `exact` and `normalized` channels. The profile declares no `normalizedExclusions` (each file repeats the empty list), so there is no `tokenIndices`. NEWLINE, INDENT and DEDENT are tokens with an empty span and empty text (profile §4.5). Every accepted vector names a `pairedRejection`, an error vector that exercises the same rule. Vectors tagged `departure` diverge from CPython on purpose (profile §9).

**Coverage**

| Case | Vectors |
| --- | --- |
| Empty, below k, exactly k, ties, comment-only | `py-empty`, `py-short`, `py-exact-k`, `py-repeated`, `py-comment-only` |
| Pairs: comment/white space, rename, re-indent, line joining, semicolon (must differ) | `py-format-a/b`, `py-rename-a/b`, `py-reindent-a/b`, `py-linejoin-a/b`, `py-semi-a/b` |
| Line terminators, joining, blank lines | `py-cr-lines`, `py-crlf-continuation`, `py-implicit-join`, `py-explicit-join`, `py-continuation-blank`, `py-blank-comment-lines`, `py-err-cr-in-string`, `py-err-backslash-stray`, `py-err-backslash-eof` |
| Indentation, tabs, form feed, backslash rule | `py-reindent-*`, `py-tabs-consistent`, `py-formfeed-indent`, `py-formfeed-between`, `py-backslash-indent`, `py-backslash-col0` (departure), `py-eof-dedent`, `py-dedent-position`, `py-first-line-indented`, `py-err-tab-vs-spaces`, `py-err-tab-indent-alt`, `py-err-tab4-dedent`, `py-err-unmatched-dedent` |
| Comments, encoding | `py-newline-after-comment`, `py-type-comment`, `py-shebang-coding`, `py-coding-latin1-ascii`, `py-err-coding-latin1-bytes`, `py-err-invalid-utf8`, `py-err-bom`, `py-err-nul` |
| Keywords, soft keywords, Unicode names | `py-keywords`, `py-soft-keywords`, `py-unicode-names`, `py-unicode-17` (departure), `py-err-u2e2f`, `py-err-nbsp`, `py-err-vt`, `py-err-dollar` (departure) |
| Operators | `py-operators`, `py-ltgt` (departure), `py-dots` |
| Numbers | `py-numbers`, `py-number-keyword`, `py-number-dot`, `py-err-number-ident`, `-legacy-octal`, `-number-underscore`, `-radix-empty`, `-number-whole-word`, `-exponent`, `-imag-digit`, `-number-dot-ident` |
| Strings and prefixes | `py-string-prefixes`, `py-string-escapes`, `py-string-content-not-checked`, `py-raw-backslash`, `py-triple-quoted`, `py-implicit-concat`, `py-prefix-ident`, `py-err-prefix-ur`, `-prefix-fb`, `-unterminated-string`, `-unterminated-triple`, `-raw-odd-backslash` |
| f- and t-strings | `py-fstring-basic`, `-nested-quotes`, `-debug-walrus`, `-multiline-expr`, `-named-escape`, `-backslash-brace`, `-triple-spec`, `-spec-brace`, `-spec-brace-after-field` (departure), `py-tstring`, `py-err-fstring-single-brace`, `-unterminated`, `-spec-newline`, `-expr-unclosed`, `-mismatch` |
| Brackets and deep nesting (explicit stack, profile §5.7) | `py-err-unbalanced-closer`, `py-err-unclosed`, `py-deep-brackets`, `py-deep-fstrings` (both departures, D-9) |
| Review additions | `py-err-tab-dedent-alt`, `py-number-nonascii-follow`, `py-err-fstring-spec-quote`, `py-fstring-named-escape-field`, `py-err-fstring-named-escape-ended`, `py-err-fstring-eof-field`, `py-continuation-then-blank`, `py-continuation-twice-indent`, `py-fstring-triple-spec-quotes`, `py-empty-span-fingerprint` (a fingerprint with span `[35, 35)`) |
| Size | `py-limit-exact`, `py-limit-over`, `py-limit-over-bom` |

## 1. Checker

```
python3 -I test-vectors/extraction-python/check_vectors.py [-v]
```

Output on 2026-11-23 (Python 3.14.6):

```
PASS config-negative-python.json: 20/20 invalid configurations rejected
PASS py.json profile=py-tokens/draft-1 config=365ba7be82646f65... vectors=107 tokens=3548 (layout 158) kgrams=3285 fingerprints=5118 tie-windows=5580 errors=39 (code and offset re-derived) pairs=5 classes=17
PASS limits-py.json profile=py-tokens/draft-1 config=02dd6c5790677df8... vectors=3 tokens=8 (layout 2) kgrams=4 fingerprints=2 tie-windows=0 errors=2 (code and offset re-derived) pairs=0 classes=3
PASS every accepted vector has derivation=hand and a pairedRejection that is an error vector
PASS mutation self-test: 32/32 corruptions rejected (28 lexical)
PASS wrong-lexer self-test: 29/29 wrong lexers rejected
```

With `-v` it lists, for each wrong lexer, every vector that rejects it (profile §11 has the table).

**What it checks.**
- **Configuration:** contract §10 validation and bounds, the shipped digests, and rejection of the 20 negatives, with their `expectedResult`.
- **Shared pre-lexing checks:** size, UTF-8, BOM and NUL, recomputed from the input bytes.
- **Re-lexing:** every input is lexed with `pylex.py`. Class, text and byte span of every token, and code and offset of every error, must be identical.
- **Rules checked on the recorded stream without `pylex.py`:**
  - layout: NEWLINE, INDENT and DEDENT are re-derived from the input bytes and the recorded non-layout tokens, using bracket depth from the stream, line ends, comments and continuations from the gaps, and the tab-size-8/tab-size-1 rule;
  - `keyword` exactly for the 35 keywords; soft keywords are `ident`;
  - operator membership and longest match (the only exception: a format-spec `:` followed by a middle token);
  - numeric shapes, longest numeric match, and what may follow a number;
  - prefix letter sets, the class implied by the prefix, and no missed prefix;
  - closed class and error-code lists, `text == input[span]`, and zero-width spans exactly for layout tokens.
- **Fingerprints:** normalized values, LP-encoded k-gram bytes, SHA-256 first-8 hashes, and winnowing by a sort on `(hash, −position)`, a different formulation from the builder's loop. `tokenIndices` is rejected, because the profile has no exclusions.
- **Pairs:** the format, re-indent and line-join pairs have equal streams and equal hashes in both channels. The rename pair has equal normalized and different exact hashes. The semicolon pair must differ in **both** channels (the PYOD-4 (a) decision).

**Mutation self-test.** 32 corruptions, each rehashed so only the targeted layer is wrong (profile §11 lists them).

**Wrong-lexer self-test.** 29 `pylex.Lexer` subclasses (the 24 of the reviewed text and the review's W03, W12, W15, W17, W19), each with one rule changed, substituted for the profile's lexer. Every one must fail on at least one shipped vector, and every one does.

**Limits.** The streams, `pylex.py`, the independent checks and the variants were written by one author from one text. Agreement shows consistency and agreement with CPython, not that an independent reader would reach the same streams; that needs a clean-room review.

## 2. Cross-check against CPython 3.14.6

```
cd test-vectors/extraction-python
python3 -I harness/crosscheck.py --vectors --stdlib --unicode [--fuzz N --seed S] [--json OUT]
```

Offline, standard library only. The script refuses any interpreter other than 3.14.6 unless `--any-version` is given. **Oracles:** the C tokenizer in parser mode (`tokenize._generate_tokens_from_c_tokenizer(..., extra_tokens=False)`) for accept/reject and error position, and `tokenize.generate_tokens` for token positions. CR LF and lone CR are translated to LF first, as CPython does, with an offset map back to the original input. Classes are compared coarsely: NAME, NUMBER, STRING. **Declared adjustments:** consecutive FSTRING_MIDDLE tokens are merged into one run (`fmid-merge`), and empty ones are dropped (`empty-fmid`).

Run on 2026-11-23 after the review fixes, CPython 3.14.6. Lone CR is judged against `compile()`; the readline path of `tokenize` does not treat it as a line terminator, so the harness translates CR LF and CR first (profile D-18).

| Part | Result |
| --- | --- |
| Accepted vectors (68) | 62 agree token for token. 6 diverge, all tagged `departure`: `py-backslash-col0` (D-3), `py-unicode-17` (D-8), `py-ltgt` (D-5), `py-fstring-spec-brace-after-field` (D-6), `py-deep-brackets` and `py-deep-fstrings` (D-9, CPython's depth limits) |
| Lexical error vectors (35) | 18 rejected by CPython at the same offset, 16 at another offset (OD-13 token start against CPython's failing character), 1 rejected only by CPython's parser (`py-err-dollar`, D-7, tagged `departure`) |
| Pre-lexing vectors (4) | Not compared |
| Undocumented divergences | **0** |
| Standard library of the interpreter: 1,852 `.py` files, 36,036,024 bytes | **1,847/1,847 lexable files agree**, 5,909,005 tokens, with 76 `fmid-merge` and 39 `empty-fmid` adjustments. 4 fail the pre-lexing checks (3 `invalid-utf8`, 1 `bom`; all deliberate test data). 1 (`test/tokenizedata/badsyntax_3131.py`) is rejected by both at the same offset |
| Unicode sweep, every scalar value | Name start differs on 4,647 code points and continue on 4,699: all of them unassigned in CPython's Unicode 16.0.0 and accepted by the pinned 17.0.0 tables (D-8). 0 accepted only by CPython |
| Fuzz, seed 11, 400,000 cases (201,073 mutated standard-library snippets, 198,927 fragment concatenations) | 5,332 divergences, all in documented classes: D-7 2,973, D-5 1,485, D-8 848, D-3 25, D-11 1 |
| Fuzz, seed 12, 400,000 cases | All divergences documented: D-7 2,858, D-5 1,565, D-8 821, D-3 28, D-11 1 |

In the fuzz, "both reject at another offset" is common and expected: the profile reports token starts and CPython the failing character. Error codes are not compared, because CPython has no matching closed list.

**Fuzz findings during drafting.** Two rule errors in the author's own first lexer were found by earlier fuzz runs and fixed in the profile text and lexer before these runs: `0or` is an error (a radix prefix with no digit), and `and`/`else`/`for`/`not`/`or` after a number must be whole words while `if`/`in`/`is` need not be. Both are pinned by vectors (`py-err-radix-empty`, `py-err-number-whole-word`) and by wrong-lexer variants.

## 3. Layout measurement

```
python3 -I harness/layout_survival.py            # top-level stdlib modules, four rewrites and the control
python3 -I harness/layout_survival.py --semi-corpus   # ';' splitting over the whole stdlib
```

The results are in profile §7. The script rewrites source in AST-preserving ways (checked with `ast.dump`), and reports the share of distinct normalized fingerprint hashes that survive under four `normalizedExclusions` variants. It also reports a program-changing control, for which a good channel must not stay blind. Runtime: about 3 minutes for each command on the machine used.

## 4. Rebuilding

```
python3 -I harness/build_vectors.py
python3 -I check_vectors.py
```

The builder rewrites `py.json`, `limits-py.json`, the two configuration files and `config-negative-python.json` from `harness/vector_sources.py`.
