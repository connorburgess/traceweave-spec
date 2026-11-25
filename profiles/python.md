# Extraction profile: Python (`py-tokens`)

Status: experimental draft, normative for conformance of this draft version (promoted 2026-11-25 from `research/drafts/extraction-profile-python.md`); **`py-tokens` `draft-1` is frozen for stage-1 implementation** (§17).

Revision status (before promotion): experimental draft, revision draft-1, 2026-11-23. The [clean-room review](../research/reviews/extraction-profile-python-review.md) of the first text (commit `1c5c06a`) reproduced all 98 vectors from the text alone. Its findings are resolved in §16. None of them changed a token, a hash or an existing vector, so the version stays `draft-1`.

This document defines the Python profile that plugs into the [extraction contract](../spec/extraction.md) without changing any of its shared parts. It follows the shape of the [TypeScript profile](typescript.md). "MUST" describes what this profile specifies for an implementation claiming to follow it. The decisions recorded in §12 were frozen for stage-1 implementation (`58c25a9`).

**How it plugs in.** Every shared part of the contract applies unchanged:
- §2 outcomes, the no-repair rule and the error-offset rules (OD-13: the first byte of the token, comment or literal being scanned);
- §3 processing order: configuration, size, UTF-8, then U+FEFF (`bom`) and U+0000 (`nul`). This profile adds no forbidden code point, so a lone CR is legal;
- §3a Unicode 17.0.0 data: the pinned `xid_start` and `xid_continue` tables, with no deltas;
- §6 serializations, with an **empty** `normalizedExclusions` list (§7); §7 k-gram hashing; §8 winnowing; §9 record fields;
- §10 configuration bytes and validation. The profile only adds the pair `(py-tokens, draft-1)`.

The only feature of the contract this profile leans on that Go, Rust and TypeScript use less is the **empty span**: NEWLINE, INDENT and DEDENT are zero-width tokens whose text is the empty string, so `text == input[span]` holds for every token with no exception (§4.5). The contract already allows this. Go's inserted `;` is the only token whose text is not its span's bytes, and this profile adds no second one.

The vectors, checker and harnesses are in [test-vectors/extraction-python/](../test-vectors/extraction-python/README.md).

## 1. Authority and pins

- **Language.** *The Python Language Reference*, chapter 2 "Lexical analysis", as shipped in the CPython source at tag `v3.14.6`: `Doc/reference/lexical_analysis.rst`, SHA-256 `fcec0275b9935e412b5f79e34e0cc7b4ca1fdd60e7d4828c416441e5994be723`. The online copy, [docs.python.org/3.14/reference/lexical_analysis.html](https://docs.python.org/3.14/reference/lexical_analysis.html), is mutable. Cited sections: Line structure (physical and logical lines, comments, encoding declarations, explicit and implicit line joining, blank lines, indentation, whitespace between tokens), Other tokens, Names (keywords, soft keywords, non-ASCII characters in names), Literals (strings, prefixes, escape sequences, bytes, raw strings, f-strings, t-strings, formal grammar for f-strings), Numeric literals, and Operators and delimiters. Where this profile restates the reference, the reference governs, except where §9 lists a deliberate departure.
- **Grammar.** `Grammar/Tokens` at `v3.14.6` (SHA-256 `df3d2cdd8228a17594316b6feda01e3ea5c3fc2c679778cd7864398540bb3423`) and `Grammar/python.gram` (SHA-256 `34f0f9b2e8a22760ca4e6e7e56857cb22f4c73e0853e5452b7e93e48ddb17361`). `Lib/keyword.py` (SHA-256 `18c2be738c04ad20ad375f6a71db34b3823c7f40b0340f5294d0e89f3c9b093b`) gives the 35 keywords and 4 soft keywords; the local interpreter's copy has the same digest.
- **Reference tokenizer (cross-check oracle, not the authority).** CPython **3.14.6**, the interpreter available locally, whose C tokenizer is `Parser/lexer/lexer.c` at `v3.14.6` (SHA-256 `1d863687835cc5aad4b2e1f20eb9bbae8a9b3c1ed147259b963f4da51cd604a8`). The cross-check drives it through `tokenize._generate_tokens_from_c_tokenizer(..., extra_tokens=False)` (the parser's own tokenizer, with identifier and numeric-literal checks on) and `tokenize.generate_tokens` (the same tokenizer in extra-tokens mode, for positions). Pinned version and local version are the same, so nothing in the cross-check is a version difference except the Unicode tables (§3.2). **Line terminators are judged against `compile()`, not against the `tokenize` path**: the readline-driven tokenizer does not treat a lone CR as a line terminator (`x\ry\r` comes out as `x` and an OP `\ry`). `compile()` reads source with universal newlines (CR LF and lone CR become LF), and that is the behaviour the reference describes and this profile follows. The cross-check therefore applies the same translation itself before calling the tokenizer, with an offset map back to the original bytes (D-18).
- **Unicode.** 17.0.0, per contract §3a. CPython 3.14.6 ships Unicode 16.0.0 (`unicodedata.unidata_version`).

The sources were retrieved on 2026-11-23 from the `v3.14.6` tag of the CPython repository (an immutable reference) and are not committed.

## 2. Inputs in scope

The extractor never sees file names (contract §1). Mapping files to this profile is a file-selection rule for TW-01/TW-03. TS.1 required these rules for TypeScript; the same are proposed here as decided in draft (PYOD-1, PYOD-2).

| Input | Decision | Reason |
| --- | --- | --- |
| `.py`, `.pyw` | `py-tokens` | Python source |
| `.pyi` (stubs) | Lexes identically under `py-tokens`, **excluded by selection** | Type surfaces, highly repetitive (`def f(x: int) -> str: ...`); the same reasoning as `.d.ts` (TSOD-7). Can be included later with no profile change |
| Python 2 code | **Out of scope**, not detectable by name | See below |
| Notebooks (`.ipynb`) | Out of scope by extension | JSON, not Python. Extracting code cells needs a cell-joining rule, which is a separate adapter (TW-01), not a lexer |
| Cython (`.pyx`, `.pxd`, `.pxi`) | Out of scope by extension | Different language (`cdef`, `ctypedef`, C types) |
| Extensionless scripts with a Python shebang | Out of scope (decided in draft) | Selection would have to read content; can be added later as a selection rule |
| Generated files | Excluded: the first 2048 bytes contain `@generated` or `DO NOT EDIT` | Same rule as TSOD-7; catches protobuf `_pb2.py` output |
| A PEP 263 declaration naming a non-UTF-8 encoding, and a byte ≥ 0x80 | Excluded by selection, recorded as "non-UTF-8 source" | §3.1. With only ASCII bytes the file is extracted normally |
| Starts with a UTF-8 BOM | Recorded as "BOM" by selection, not extracted | The contract rejects it (`bom`, OD-1); recording it before extraction keeps it out of the lexical-error count |

**Python 2.** No lexical rule can tell Python 2 from Python 3 without a parser: `print "x"` and `exec code` lex as a name followed by a string or name. A Python 2 file is therefore lexed by the Python 3.14 rules. Most lex and are fingerprinted with Python 3 token classes (`print` is `ident`). Some fail with an ordinary lexical error: backticks (`illegal-character`), `ur''` (`malformed-literal`), `0777` and `1L` (`malformed-literal`), and tab/space mixtures (`inconsistent-indentation`). This is the "unavoidable" case: the selecting tool SHOULD exclude a repository whose metadata declares Python 2 (for example `python_requires` below 3), and MUST NOT silently drop files that fail.

Excluded files are not extracted. Exclusion is never an extraction result or error code.

## 3. Before tokens

### 3.1 Source encoding (reference "Encoding declarations")

The contract requires UTF-8. The reference allows other encodings through a PEP 263 declaration (`coding[=:]\s*([-\w.]+)` in a comment on line 1, or on line 2 after a comment-only line 1).

- **A declaration is a comment and nothing more.** The extractor never decodes in another encoding (contract §2, no repair). Bytes that are not UTF-8 give `invalid-utf8` at the first bad byte, whatever the declaration says (vector `py-err-coding-latin1-bytes`; CPython 3.14.6 accepts that file, D-2).
- **An all-ASCII file with a non-UTF-8 declaration is extracted normally** (`py-coding-latin1-ascii`). ASCII bytes mean the same in every encoding CPython accepts in a declaration. CPython rejects declarations of ASCII-incompatible codecs such as `utf-16` and `cp037` on such files (both checked on 3.14.6), so the token streams agree. The one edge left is `utf-7`, where `+` changes meaning; such files are not known to exist and would need a selection rule.
- **Selection rule** (§2): a non-UTF-8 declaration together with any byte ≥ 0x80 excludes the file, recorded as "non-UTF-8 source".
- **Which declared names count as UTF-8** (decided in draft, PYOD-2): lowercase the declared name and replace `_` by `-`. It is UTF-8 if it equals `utf-8` or starts with `utf-8-` (CPython's tokenizer shortcut, which also covers `utf-8-sig`), or if it is one of `utf8`, `u8`, `utf`, `cp65001`, `utf8-ucs2` or `utf8-ucs4`, the CPython 3.14.6 codec aliases that resolve to UTF-8. Any other name is non-UTF-8. This list reproduces what CPython 3.14.6 decodes as UTF-8; it is a selection rule and never reaches the extractor. In the 3.14.6 standard library 3 files fail UTF-8 and 1 starts with a BOM, all of them deliberate test data (`test/encoded_modules/*`, `test/tokenizedata/*`).
- **BOM.** The reference ignores an initial UTF-8 BOM. The contract rejects it at any offset (`bom`, OD-1), and this profile cannot change a shared rule (D-1, `py-err-bom`).

### 3.2 Identifier characters (reference "Names", "Non-ASCII characters in names")

The reference grammar is `NAME: name_start name_continue*`, where `name_start` is an ASCII letter, `_` or any non-ASCII character, followed by validation: a valid name starts with a character in `xid_start` (XID_Start plus `_`) and continues with `xid_continue`. This profile states the same set directly:

- a name starts with an ASCII letter, `_`, or a non-ASCII code point in the pinned `xid_start` table;
- it continues with ASCII letters, digits and `_`, and non-ASCII code points in the pinned `xid_continue` table, as far as possible (maximal munch).

A non-ASCII character that is not in `xid_start` at a token start, or that stops a name, is `illegal-character` at its own offset. This is the same accept/reject decision and the same offset as CPython's "invalid character" error, which also points at the first invalid character of the name candidate (`py-err-u2e2f`, `py-err-nbsp`). The reference's "documented extra characters" (Other_ID_Start, Other_ID_Continue) are already inside XID_Start and XID_Continue; the only addition is `_` as a start.

**Unicode version.** The pinned tables are Unicode 17.0.0 (contract §3a). CPython 3.14.6 uses Unicode 16.0.0. The sweep (§11) finds that the profile accepts 4,647 name-start and 4,699 name-continue code points that CPython rejects, all of them characters new in 17.0.0, and that CPython accepts none that the profile rejects (D-8, `py-unicode-17` with U+A7CE). An implementation MUST NOT use its runtime's `str.isidentifier` or `unicodedata` unless shown identical to the pinned table (the contract's library rule). The wrong-lexer self-test includes exactly that variant (`WPythonUnicode`).

**NFKC.** The language converts every name to NFKC while parsing, so `ﬁle` and `file`, or `𝐱` and `x`, are the same name to Python. This profile does **not** normalize and does **not** check normalization:
- the exact value is the original bytes (contract OD-9), so the exact channel distinguishes NFKC-equal spellings;
- the normalized channel erases every name, so it is unaffected;
- the contract has no NFC requirement for this profile; NFC is checked only for Rust identifiers (contract OD-3), and nothing here adds one.

Keywords are matched on the raw text, as CPython does: the fullwidth spelling `ｉｆ` is `ident` (`py-unicode-names`). CPython 3.14.6 compiles `ｉｆ = 1` and binds the name `if`, so this matches the language, not just the tokenizer (D-12).

## 4. Line structure

### 4.1 Physical lines and line terminators

A line terminator is LF, CR LF (one terminator) or a lone CR, as in the reference ("Physical lines"). Offsets and token text keep the original bytes. A lone CR ends a comment and a single-quoted string exactly like LF (`py-cr-lines`, `py-err-cr-in-string`). No other character is a line terminator: VT, FF, U+0085, U+2028 and U+2029 are not, even though Python's `str.splitlines` treats them as line breaks.

### 4.2 Explicit and implicit line joining

- **Explicit.** Outside literals and comments, `\` MUST be immediately followed by a line terminator, and that line terminator MUST NOT be the last thing in the input. Then `\` and the terminator are skipped and the next physical line continues the logical line; its leading white space is ordinary white space. Anything else is `illegal-character` at the `\`: a stray backslash (`py-err-backslash-stray`), and a continuation that ends the input (`py-err-backslash-eof`; CPython: "unexpected EOF"). `\` CR LF is one continuation (`py-crlf-continuation`). A backslash inside a comment is part of the comment and does not continue it.
- **Implicit.** While a bracket `(`, `[` or `{`, or an f/t-string replacement field (§6), is open, line terminators, comments and blank lines produce no NEWLINE, and no indentation is measured (`py-implicit-join`, `py-fstring-multiline-expr`).

### 4.3 Comments and blank lines

`#` outside a literal starts a comment that runs to the next line terminator, exclusive, or to the end of input. Comments are trivia. Type comments (`# type: int`), shebang lines and encoding declarations are ordinary comments (`py-type-comment`, `py-shebang-coding`). Python has no block comment, so there is no `unterminated-comment`.

A **blank line** is a logical line that holds only spaces, tabs, form feeds and possibly a comment, before its line terminator or the end of input. It produces no token and does not take part in indentation (`py-blank-comment-lines`, `py-comment-only`). This holds at any indentation, including a comment at column 0 inside a block. **A `\` continuation in the leading white space does not change this:** if the physical line after the continuation holds only white space, a comment, or nothing before its terminator, the logical line is blank, as in CPython (`py-continuation-then-blank`).

### 4.4 Indentation (reference "Indentation")

At the start of each logical line, when no bracket or field is open, measure the leading white space with two counters, starting at 0:
- a space adds 1 to both;
- a tab sets `col` to the next multiple of 8 and adds 1 to `alt` (tab size 1);
- a form feed sets both to 0.

The reference says a form feed at line start is ignored and elsewhere in leading white space has "an undefined effect (for instance, they may reset the space count to zero)". This profile pins the reset, which is what CPython does (`py-formfeed-indent`). Between tokens a form feed is white space (`py-formfeed-between`).

**Backslash in the indentation.** If a `\` continuation occurs in the leading white space, the indentation is `(col, alt)` **at the first backslash**; white space after the continuation does not count, and **later continuations in the same leading white space are skipped** (each still MUST be a valid continuation, §4.2). This is the reference's sentence "the whitespace up to the first backslash determines the indentation" (`py-backslash-indent`, `py-continuation-twice-indent`). CPython 3.14.6 departs when the backslash is at column 0 (it then counts the following line's spaces) and copies `col` into `alt` (D-3, `py-backslash-col0`).

If the line is blank (§4.3), stop. Otherwise compare `(col, alt)` with the top of a stack that starts as `[(0, 0)]`:
- **Equal `col`.** If `alt` differs, the result is `inconsistent-indentation`.
- **Greater `col`.** If `alt` is not greater than the top's `alt`, `inconsistent-indentation`. Otherwise push and emit one INDENT.
- **Smaller `col`.** Pop while `col` is smaller than the top's `col`, emitting one DEDENT per pop. Then if `col` differs from the new top's `col`, the result is `unmatched-dedent`. If `alt` differs from the new top's `alt`, `inconsistent-indentation` (`py-err-tab-dedent-alt`).

Indentation errors are reported at the first byte of the line's first token. This two-width comparison is CPython's implementation of the reference's "mixes tabs and spaces in a way that makes the meaning dependent on the worth of a tab in spaces" (vectors `py-err-tab-vs-spaces`, `py-err-tab-indent-alt`, `py-err-tab4-dedent`, `py-tabs-consistent`, `py-err-unmatched-dedent`).

**No depth limit.** CPython stops at 100 indentation levels; the reference states no limit, and neither does this profile (D-9).

**Fragments.** Input can be a fragment (contract §1). A fragment whose first line is indented starts with INDENT (`py-first-line-indented`). A fragment that later dedents below its first line's level to a column not on the stack is `unmatched-dedent`. Snippet cutting (M2) must therefore cut at logical-line boundaries that keep the indentation consistent.

### 4.5 NEWLINE, INDENT and DEDENT tokens

These three tokens carry Python's block structure and are kept in the token list and the exact channel (classes `newline`, `indent`, `dedent`). Each is **zero-width with empty text**, so its exact and normalized value is `""` and only the class enters the hash:

| Token | Emitted | Span |
| --- | --- | --- |
| `newline` | At a line terminator that ends a logical line holding at least one token, with no bracket or field open; and at end of input if the last logical line holds a token and has no terminator | `[p, p)` at the first byte of that line terminator (after any trailing comment), or at the input length |
| `indent` | §4.4 | `[p, p)` at the first byte of the line's first token |
| `dedent` | §4.4, and at end of input once per stack entry above `(0, 0)`, after the final `newline` | `[p, p)` at the first byte of the line's first token, or at the input length |

CPython's ENDMARKER, NL and COMMENT tokens are not emitted. CPython's INDENT has the white space as its text and NEWLINE has `"\n"`; here both are empty, so the white-space width, the tab-or-space choice and CR LF versus LF never reach a hash (D-14).

**Why zero-width.** With empty text, re-indenting a file (4 spaces to 2, spaces to tabs) leaves **both** channels' hashes unchanged, while block structure still changes them: only the number and order of INDENT and DEDENT tokens count. Line-joining style is invisible too, because a continuation produces no token (`py-linejoin-a/b`, `py-reindent-a/b`, both pairs checked to have identical exact and normalized hashes). This is consistent with the other profiles, whose exact channels also ignore white space.

**Layout-only k-grams and empty spans.** Because these tokens are zero-width, a k-gram made only of layout tokens can have an **empty span**. At the default k = 5 this happens whenever a file ends four or more blocks deep: the last k-gram is NEWLINE followed by four DEDENTs, all at the input length, so its span is `[n, n)`, and it can be selected as a fingerprint (`py-empty-span-fingerprint`: span `[35, 35)`; the checker requires an empty-span fingerprint there). Layout-only k-grams inside a file have non-empty spans that cover only white space and comments. Such k-grams are identical across unrelated files and will be common hashes. **What the catalogue contract must say:** an empty span is a valid fingerprint span for `py-tokens` at every k, not only at k = 1, so a catalogue MUST store and a report MUST carry `[n, n)` unchanged, and a consumer MUST NOT treat it as an error or drop it. How M2 localization and suppression should treat layout-only k-grams belongs to the matching contract.

### 4.6 White space between tokens

Space, tab and form feed. Every other character outside a literal or comment either starts a token or is `illegal-character`, including VT (`py-err-vt`), U+00A0 (`py-err-nbsp`), U+0085 and the other control characters.

## 5. Tokens

### 5.1 Token classes (closed list)

`keyword`, `ident`, `punct`, `int`, `float`, `imag`, `string`, `bytes`, `fstring-start`, `fstring-middle`, `fstring-end`, `tstring-start`, `tstring-middle`, `tstring-end`, `newline`, `indent`, `dedent`.

`int`, `float` and `imag` are the reference's `integer`, `floatnumber` and `imagnumber`. `bytes` is a string literal whose prefix contains `b`. The f- and t-string classes are the reference's FSTRING_START/MIDDLE/END and TSTRING_START/MIDDLE/END (§6).

### 5.2 Names, keywords and soft keywords

A name (§3.2) is `keyword` if its text is one of the 35 keywords of the reference ("Keywords"): `False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield`. Otherwise it is `ident`.

**Soft keywords are `ident` in every position** (decided in draft, PYOD-3): `match`, `case`, `type` and `_`. The reference says the distinction "is done at the parser level, not when tokenizing", and no lexical rule can tell `match x:` from `match = re.match(...)` (vector `py-soft-keywords` has both). This parallels Go's predeclared identifiers (contract OD-7) and TypeScript's contextual words (TSOD-2). Python 2 words such as `print` and `exec` are `ident`.

### 5.3 String and bytes literals, and prefixes

**Prefix.** When a name (§3.2) is immediately followed by `'` or `"`, and its text, compared case-insensitively, consists only of the letters `b`, `r`, `u`, `f`, `t` with no letter repeated, it is a prefix. The letter set MUST be one of {b}, {r}, {u}, {f}, {t}, {b, r}, {f, r}, {t, r}, in any order and case; any other set (`ur`, `ub`, `bf`, `bt`, `ft`, three letters) is `malformed-literal` at the prefix start. CPython 3.14 made these combinations tokenizer errors (`py-err-prefix-ur`, `py-err-prefix-fb`). A name with any other letter, or a repeated letter, is an ordinary name followed by a separate string: `uu'x'`, `rr"y"`, `print'z'`, `bx'w'` (`py-prefix-ident`). Only ASCII letters count, so a fullwidth `ｆ` is a name.

A prefix with `f` or `t` starts an f-string or t-string (§6). Otherwise the token is `bytes` if the prefix has `b`, else `string` (`py-string-prefixes`).

**Body** (the reference's formal `STRING` grammar, which validates nothing beyond termination):
- A triple-quoted literal (`'''` or `"""` right after the prefix) ends at the first three consecutive unescaped quotes of its kind. Line terminators are allowed.
- A single-quoted literal ends at the next unescaped quote of its kind. An unescaped line terminator (LF, CR, or CR LF) is `unterminated-literal` at the first byte of the token, prefix included.
- `\` takes the next character into the literal, CR LF counting as one character. **This holds in raw literals too**, which is why `r'\''` is one string and `r'\'` cannot end (`py-raw-backslash`, `py-err-raw-odd-backslash`).
- End of input inside the literal is `unterminated-literal` at the token start (`py-err-unterminated-triple`).

**Content is not checked** (decided in draft, PYOD-5). Invalid `\x`, `\u`, `\U` or `\N{...}` escapes, and non-ASCII characters in bytes literals, are accepted as written (`py-string-content-not-checked`). They are not in the reference's formal lexical grammar; CPython rejects them only when it decodes the literal value after tokenizing (D-4). The exact value is the original bytes, so nothing here needs the decoded value.

**Adjacent literals stay separate tokens.** `'a' 'b'` is two `string` tokens; concatenation is the parser's job (`py-implicit-concat`).

### 5.4 Numeric literals

At an ASCII digit, or at `.` followed by an ASCII digit, take the **longest match** of the reference `NUMBER` grammar (`integer | floatnumber | imagnumber`, including `zerointeger`, leading zeros in float and imaginary digit parts, and `_` only between digits or after a radix prefix). The class is the production that matched (`py-numbers`, `py-dots`, `py-number-dot`).

Then check what follows. Each failure is `malformed-literal` at the literal start:
1. **Radix prefix without a digit.** If the literal is the single character `0` and the next character is `b`, `B`, `o`, `O`, `x` or `X`, the prefix has no digit of its base. This covers `0or` (`py-err-radix-empty`), which CPython rejects as "invalid octal literal" although `or` follows.
2. **What may follow.** If the next character is an ASCII letter, ASCII digit or `_`, the literal is accepted only if one of these follows:
   - the two letters `if`, `in` or `is`, whatever comes after them;
   - one of the whole words `and`, `else`, `for`, `not` or `or`, where the next character is not an ASCII letter, digit or `_` and not a non-ASCII character.

   This is CPython 3.14's `verify_end_of_number`, which gives a SyntaxWarning instead of an error in exactly these cases, so `1if x else 2` and `0x1for w in v` stay valid (`py-number-keyword`), while `1orx` is an error but `1ifx` is not (`py-err-number-whole-word`). A non-ASCII character after a number ends it without error (`1é` is an int and a name), as in CPython.

Examples of errors: `1abc`, `0777` (leading zeros in a non-zero integer), `1__0`, `1_`, `1e`, `1e+`, `1.real`, `1j2`, `0x`, `0b2`, `0o8` (`py-err-*` number vectors). Legacy forms are rejected because the grammar has no rule for them, not by a special case.

### 5.5 Operators and delimiters

The 48 tokens of the reference "Operators and delimiters" grammar, longest match, class `punct`:

```
+= -= *= **= /= //= %= &= |= ^= <<= >>= @= :=   & | ^ ~ << >>   <= >= < > == !=   ( ) [ ] { }
, : ! ; = ->   + - ** * // / %   ...   . @
```

(`py-operators`, `py-dots`). Longest match has one exception, inside f/t-string fields (§6.2). `<>` is not in the list, so it lexes as `<` `>` (D-5, `py-ltgt`). `!` alone is a token everywhere, as in the 3.14 tokenizer.

**Brackets.** `(`, `[` and `{` push onto the stack; a closer must match the top, otherwise `unbalanced-delimiter` at the closer (`py-err-unbalanced-closer`). At end of input, an open bracket on top of the stack is `unbalanced-delimiter` at the innermost opener (`py-err-unclosed`). CPython's limit of 200 nested brackets is not adopted (D-9).

### 5.6 Characters that are errors

`$`, `?` and `` ` `` (the reference: "Error (outside string literals and comments)"), every control character other than TAB, LF, CR and FF, and every non-ASCII character that cannot start or continue a name at that position: `illegal-character` at its offset. CPython's tokenizer returns OP for `$`, `?` and `` ` `` and leaves the rejection to the parser (D-7, `py-err-dollar`).

### 5.7 Nesting: explicit stack required

Brackets, f/t-strings, replacement fields and nested format-spec fields nest without a depth limit (D-9), so the only bound is `maxInputBytes`: about 350,000 levels within 1 MiB, 2.8 million within the 8 MiB contract bound. **An implementation MUST track nesting with an explicit stack, in memory linear in the input size (contract §10a). Recursion with one call per nesting level is non-conformant**, because it fails by stack overflow on inputs within `maxInputBytes`, which is a state the contract does not allow (contract §2: no result for an undecided state). Indentation levels are a stack too and fall under the same rule. Vectors `py-deep-brackets` (1,000 levels) and `py-deep-fstrings` (200 nested f-strings) are inside every allowed size limit; the review ran both lexers to about 349,000 levels.

## 6. f-strings and t-strings (PEP 701)

### 6.1 Structure

A prefix with `f` (or `t`) and its opening quote, one or three characters, form one `fstring-start` (`tstring-start`) token, and the f-string is pushed onto the stack. The scanner is then in **literal mode** for it. t-strings follow exactly the rules of f-strings with the `tstring-*` classes (reference "t-strings": "These strings follow the same syntax rules"; `py-tstring`).

In literal mode, scan characters:
- **The closing quote(s)** end the f-string: any pending literal text becomes one `fstring-middle`, then the quote(s) are `fstring-end`, and the f-string is popped.
- **`{{` and `}}`** are literal text. One `fstring-middle` token covers the whole run of literal text between two other tokens, escapes included (`py-fstring-basic`: `b{{c}}` is one token). CPython splits such runs; the cross-check merges them (D-15).
- **`{`** (not doubled) emits any pending middle, then `punct` `{`, pushes a **replacement field**, and switches to normal mode.
- **A single `}`** is `malformed-literal` at the f-string start (`py-err-fstring-single-brace`).
- **`\`** handling (§6.3).
- **A line terminator** in a single-quoted f-string, or end of input, is `unterminated-literal` at the f-string start (`py-err-fstring-unterminated`). In a triple-quoted one, line terminators are literal text.

An empty literal run produces no token (`f''` is two tokens).

### 6.2 Replacement fields

Inside a field the scanner is in normal mode (§4, §5): any token, including strings with the **same quote** as the enclosing f-string and nested f-strings (`py-fstring-nested-quotes`), comments, line terminators (implicit joining, even in a single-quoted f-string: `py-fstring-multiline-expr`) and `\` continuations. Brackets nest as usual. With the field itself on top of the stack, that is with no bracket open inside it:
- **`:` starts the format spec**, and this is checked **before** longest match, so `{z:=10}` is `:` then the spec `=10` (`py-fstring-debug-walrus`). A `:` inside brackets in the field (`{(w:=1)}`, `{x[1:2]}`, `{ {1: 2} }`) is ordinary punctuation. `lambda x: x` unparenthesized therefore starts a spec, as in CPython.
- **`}`** emits `punct` `}`, pops the field and returns to the mode of the enclosing f-string (literal mode) or enclosing field (spec mode).
- **`=`** (the debug specifier) and **`!`** (before a conversion) are ordinary punctuation, and the conversion letter is an `ident`. `!=` is one token by longest match.
- A closer that does not match, such as `)` with the field on top, is `unbalanced-delimiter` at the closer (`py-err-fstring-mismatch`).

**Spec mode** scans like literal mode, with three differences: the text is emitted as `fstring-middle`; **`{` always opens a nested field and `}` always closes the field** (no `{{`/`}}` escapes in a format spec: `py-fstring-spec-brace`, where `{{z}}` is a nested field holding a set display); and meeting the enclosing f-string's **closing delimiter** (one quote, or three for a triple-quoted f-string) before the `}` is `unterminated-literal` at the f-string start (`py-err-fstring-spec-quote`). Single quote characters inside the spec of a triple-quoted f-string are spec text (`py-fstring-triple-spec-quotes`). A line terminator in the spec of a single-quoted f-string is `unterminated-literal` at the f-string start (`py-err-fstring-spec-newline`); in a triple-quoted one it is spec text (`py-fstring-triple-spec`).

CPython agrees with "no escapes in a spec" until a nested field has appeared in the spec, after which it treats `{{` as an escape (D-6, `py-fstring-spec-brace-after-field`). CPython also limits fields nested through specs to depth 2 ("expressions nested too deeply") and f-string nesting to 150; this profile has no limit (D-9).

### 6.3 Backslashes in literal text and specs

In literal mode and spec mode, `\` and the next character are literal text, with these cases:
- `\` before `{` or `}`: the backslash is text and the brace is processed normally, so `f'\{x}'` has a field (`py-fstring-backslash-brace`);
- `\` before a line terminator: both are text (CR LF as one);
- in a **non-raw** f/t-string, `\N{` starts a named escape: the next `}` is literal text and ends it. Inside it, `{` still opens a field (`py-fstring-named-escape-field`), and **that field ends the named escape**: after the field closes, a `}` is an ordinary literal-text brace (`f'\N{A{x}B}'` is `malformed-literal`, `py-err-fstring-named-escape-ended`). The closing delimiter and a line terminator act as usual inside the escape, as in CPython. In a **raw** f-string `\N` is two characters of text and `{` opens a field (`py-fstring-named-escape`).

The escape's validity is not checked (§5.3).

### 6.4 End of input and errors inside f-strings

At end of input, if a field is the innermost open construct, the result is `unterminated-literal` at the start of its f-string, not at the field's `{` (`py-err-fstring-eof-field`). If a bracket inside the field is innermost, it is `unbalanced-delimiter` at that bracket (contract §3 step 4). An error inside a field is reported where it occurs: `f'{x'` is `unterminated-literal` at the inner quote, offset 4 (`py-err-fstring-expr-unclosed`), where CPython reports "f-string: expecting '}'".

### 6.5 Normalized stream

Every f/t-string class is a literal class, so its normalized value is `""` (§7). The tokens of the expressions in fields keep their own classes and values: names are erased, keywords and punctuation kept. A renamed variable inside an f-string therefore leaves the normalized channel unchanged, while a structural change inside a field (an added call, a different operator) changes it.

**No staging of f-string internals.** Finding the end of an f-string under PEP 701 already requires lexing the fields completely: same-quote strings, comments that may contain quotes and braces, nested f-strings and brackets. An opaque single-token f-string would therefore save no state and would misread `f"{x["a"]}"`, which the wrong-lexer self-test shows (`WFStringPlain`, rejected by 14 vectors). The internals are stage 1 (§13).

## 7. Serializations and `normalizedExclusions`

Contract §6 applies unchanged. The value is `""` for `ident` and every literal class: `int`, `float`, `imag`, `string`, `bytes` and the six f/t-string classes. `keyword` and `punct` keep their text. The layout classes have empty text, so their value is `""` in both channels.

**`normalizedExclusions` is empty** (decided in draft, PYOD-4 (a)). Both channels contain every token, and no `tokenIndices` is recorded (contract §6).

**The measurement** ([harness/layout_survival.py](../test-vectors/extraction-python/harness/layout_survival.py), CPython 3.14.6). It applies source rewrites that keep the AST identical (checked with `ast.dump`), and counts the share of each file's distinct normalized fingerprint hashes (k = 5, w = 4) that survive. Sample: the 155 top-level standard-library modules that lex, 634,869 tokens; for semicolons, every standard-library file with a `;` statement separator.

| Rewrite | Files | No exclusion | `;` | `;` + `newline` | `;` + all layout |
| --- | --- | --- | --- | --- | --- |
| Re-indent to 2 spaces | 147 | 100.00% | 100.00% | 100.00% | 100.00% |
| Re-indent to tabs | 147 | 100.00% | 100.00% | 100.00% | 100.00% |
| Split `a; b` onto two lines (whole stdlib: 15 files, 29 separators) | 15 | 99.57% (10,105/10,149) | 99.98% | 100.00% | 100.00% |
| Expand `if x: y` into a block | 31 | 98.78% (21,006/21,266) | 98.78% | 98.85% | 100.00% |
| **Control:** move a block's last statement out of the block (changes the program) | 136 | 3 of 136 files blind | 3 | 3 | **136 of 136 blind** |

"Blind" means the normalized fingerprint set is unchanged although the program changed.

**Reading the table.**
- Zero-width layout tokens (§4.5) already make re-indentation and line-joining style invisible in both channels, with no exclusion at all. That is the effect the TypeScript `;` exclusion bought for its channel, obtained here by construction.
- Excluding INDENT and DEDENT would make the normalized channel blind to block structure in every control file. This is ruled out.
- Excluding `;` and `newline` would make semicolon splitting invisible. But PEP 8 discourages `;`, and black and ruff remove it; the standard library has 29 such separators in 1,847 files. The gain is 0.43% of fingerprints in the 15 files that have them.
- Keeping both channels identical in membership avoids the `tokenIndices` machinery and one more place for implementations to diverge.

The semicolon pair `py-semi-a/b` is shipped as a **negative** pair: the checker requires both channels to differ, which pins this decision. Option (b), excluding `punct ;` and `newline`, stays open in §12 with these numbers.

## 8. Errors

**Error codes** (closed list): `invalid-utf8`, `bom`, `nul`, `input-too-large`, `illegal-character`, `unterminated-literal`, `malformed-literal`, `unbalanced-delimiter`, `inconsistent-indentation` and `unmatched-dedent`, plus `unsupported-config` (contract §10).

**Order.** Contract §3 order applies first. Lexical errors are found in scan order and the first one is reported. Where one position could fail in more than one way:

| Situation | Result |
| --- | --- |
| A logical line's indentation is bad, and its first token is also bad | The indentation error, at the first token: indentation is checked before the token is scanned |
| An incompatible prefix on a literal that is also unterminated (`ur'abc`) | `malformed-literal` at the prefix start: the prefix is decided before the body |
| A literal whose content is invalid and which is unterminated | `unterminated-literal`; content is never checked (§5.3) |
| A number followed by a name character | `malformed-literal` at the literal start, never `illegal-character` |
| An invalid non-ASCII character inside a name | `illegal-character` at that character (the name before it is a complete token) |
| `\` followed by anything but a line terminator, or by one that ends the input | `illegal-character` at the `\` |
| End of input with a bracket innermost | `unbalanced-delimiter` at that bracket |
| End of input with an f/t-string field innermost, or in its literal text or spec | `unterminated-literal` at the f/t-string's first byte (its prefix) |
| An unterminated string inside a field | `unterminated-literal` at that string's start |
| A wrong closer before end of input | `unbalanced-delimiter` at the closer (scan order) |
| End of input inside a string while brackets are open | The string's error; the bracket check runs only after scanning succeeds (contract Q2) |

**Offsets** follow contract OD-13: the first byte of the token, comment or literal being scanned. For indentation errors that is the first token of the line. CPython often reports elsewhere, for example at the failing digit or at the newline in a spec. Of the 31 lexical error vectors, 17 share CPython's offset, 13 are rejected by CPython at another offset, and `py-err-dollar` is rejected by CPython's parser only (D-7).

## 9. Deliberate departures

"Reference" is the 3.14.6 language reference; "CPython" is the 3.14.6 tokenizer, the cross-check oracle.

| ID | Construct | Reference | CPython 3.14.6 | This profile | Why |
| --- | --- | --- | --- | --- | --- |
| D-1 | Initial UTF-8 BOM | ignored | ignored | `bom` | Shared contract rule OD-1 |
| D-2 | Non-UTF-8 coding declaration | decodes in that encoding | decodes | lexes as UTF-8; non-UTF-8 bytes are `invalid-utf8`; selection excludes such files (§3.1) | Contract: no decoding in another encoding |
| D-3 | `\` continuation in leading white space at column 0; a tab before that `\` | indentation = white space up to the first `\` | counts the next line's spaces (INDENT); copies `col` into `alt` | follows the reference (`py-backslash-col0`) | The reference is the authority, and the CPython behaviour is an implementation quirk |
| D-4 | Invalid `\x`, `\u`, `\U`, `\N{}` escapes; non-ASCII in bytes | values undefined; prose says bytes are ASCII | rejected when the value is decoded (after tokenizing) | accepted | Not in the formal lexical grammar; values are never decoded |
| D-5 | `<>` | not a token | one OP (for `barry_as_FLUFL`) | `<` `>` | Reference operator list |
| D-6 | `{{` in a format spec after a nested field (`f'{x:{y}{{z}}}'`) | grammar lists `{{` in FSTRING_MIDDLE generically | escape, but only after a nested field | always a nested field | One rule for the whole spec; CPython's behaviour depends on a flag cleared by the nested field |
| D-7 | `$`, `?`, `` ` `` | "Error" | OP; the parser rejects | `illegal-character` | Reference; accept/reject agrees after parsing |
| D-8 | Name characters new in Unicode 17.0.0 (4,647 start, 4,699 continue) | the `unicodedata` of the release | rejected (Unicode 16.0.0) | accepted | Contract §3a |
| D-9 | Depth limits: 100 indentation levels, 200 brackets, 150 nested f-strings, field depth 2 inside specs | none stated, except "nested fields may not include more deeply nested replacement fields" | errors | no limits; an explicit stack is required (§5.7) | Implementation limits, not lexical rules (`py-deep-brackets`, `py-deep-fstrings`) |
| D-10 | Error offsets | — | usually at the failing character | token start | Contract OD-13 |
| D-11 | Closing quote inside a format spec (`f'{x:abc'`, `f'{x:abc' + y}`) | — | the tokenizer ends the f-string there and accepts the second example once a later `}` balances; the compiler rejects both ("expecting '}', or format specs") | `unterminated-literal` at the f-string start | The input is not valid Python either way; this names the cause at the lexical level |
| D-12 | NFKC-equal names (`ﬁle`/`file`), `ｉｆ` | same name after NFKC; keywords on raw text | same | different exact values; `ｉｆ` is `ident` | Exact value is the original bytes (OD-9); normalized erases names |
| D-13 | Type comments | comments | TYPE_COMMENT tokens only with a compile flag | comments | The default tokenizer agrees |
| D-14 | NEWLINE, INDENT, DEDENT text; ENDMARKER, NL, COMMENT tokens | token types only | text `"\n"`, white space; extra tokens | empty text, zero-width; no ENDMARKER/NL/COMMENT | Layout-independent hashes (§4.5) |
| D-15 | f-string literal runs with `{{`, `}}`, `\N{...}` | one FSTRING_MIDDLE per run in the grammar | split into several FSTRING_MIDDLE tokens, and the escaped brace is dropped from the text | one `fstring-middle` with the original bytes | `text == input[span]`; matches the grammar |
| D-16 | `\` at end of input, or `\` + terminator at end of input | — | "unexpected EOF" | `illegal-character` at `\` | Names the cause; both reject |
| D-17 | Form feed inside leading white space | "undefined effect" | resets both counts | resets both counts | Pins the undefined case to CPython |
| D-18 | Lone CR, through the `tokenize` readline path | a line terminator | `compile()`: a line terminator (universal newlines); `tokenize` readline: not one (`x\ry\r` gives OP `\ry`) | a line terminator | Follows the reference and `compile()`. The cross-check translates CR LF and CR to LF itself before calling the tokenizer (§1) |

## 10. Configuration

Contract §10 applies, including the §10a bounds. The canonical bytes ([config-py.json](../test-vectors/extraction-python/config-py.json)) are:

```
{"contract":"traceweave-token-winnow-draft-1","profile":"py-tokens","profileVersion":"draft-1","channels":["exact","normalized"],"k":5,"window":4,"hash":"sha256-first8-u64be","maxInputBytes":1048576}
```

Digests: `py-tokens` `365ba7be82646f6505cc339a15b3f5c50632244001eee2e08c558ce22c77b016`; with `maxInputBytes` 16: `02dd6c5790677df8175faada9fdb938613e26dc6ed886ec597fc642aea64c562`.

**Profile identifier.** `py-tokens`, without an interpreter version, following contract §10 versioning: a Python release that changes lexing (as 3.12 did for f-strings and 3.14 for t-strings and prefix errors) needs a new `profileVersion`, and a release that does not is accepted by re-running the cross-check. [config-negative-python.json](../test-vectors/extraction-python/config-negative-python.json) lists 20 rejections, among them `python-tokens`, `py3-tokens`, `py314-tokens`, version `draft-2`, an exact-only channel list, and a `normalizedExclusions` key (exclusions are profile text, not configuration). k = 5 and w = 4 are contract OD-10.

## 11. Requirement-to-check map and verification

| Requirement | Check |
| --- | --- |
| Config bytes, pair and bounds (§10) | Checker validates two configs and rejects 20 negatives, each with its `expectedResult` |
| Contract §3 order | `py-err-invalid-utf8`, `-bom`, `-nul`, `py-err-coding-latin1-bytes`, `py-limit-*`; recomputed by the checker |
| Every token (class, text, byte span) and every error (code, offset) | Checker re-lexes each input with [pylex.py](../test-vectors/extraction-python/pylex.py) and requires identity |
| NEWLINE/INDENT/DEDENT (§4) | Checker re-derives all layout tokens **without pylex**, from the input bytes and the recorded non-layout tokens (bracket depth from the stream; line ends, comments and continuations from the gaps; the two-width indentation rule); `py-reindent-a/b`, `py-linejoin-a/b`, `py-format-a/b` pairs |
| Keywords and soft keywords (§5.2) | Checker: `keyword` iff one of the 35 words, independent of pylex; `py-soft-keywords`, `py-unicode-names` |
| Operators, longest match (§5.5, §6.2 exception) | Checker invariant, independent of pylex |
| Numbers (§5.4) | Checker: each literal matches its production, is the longest numeric match, and is followed by an allowed character (the §5.4 rules restated) |
| Prefixes (§5.3) | Checker: prefix letter set valid, class determined by the prefix, and no name of distinct prefix letters directly before a quote |
| f/t-strings (§6) | Vectors tagged `fstring`/`tstring`; pylex re-lex; cross-check against CPython |
| Unicode (§3.2) | Pinned table digest; `py-unicode-17`, `py-err-u2e2f`; cross-check sweep |
| Normalized values, hashes, winnowing, ties, pairs (§7) | Checker recomputation with sort-based selection; tie windows in `py-repeated` and the deep-nesting vectors; an empty-span fingerprint required in `py-empty-span-fingerprint`; format, re-indent, line-join and rename pairs equal where required; semicolon pair required to differ |
| Toolchain agreement | [harness/crosscheck.py](../test-vectors/extraction-python/harness/crosscheck.py): vectors, standard library, Unicode sweep, differential fuzz |

**Results, draft-1 after the review fixes, 2026-11-23** (Python 3.14.6, the only interpreter used).

- **Checker:** PASS. `py.json`: 107 vectors (68 accepted, 39 errors), 3,548 tokens of which 158 are layout tokens, 3,285 exact k-grams, 5,118 fingerprints, 5,580 tie windows (almost all in the two deep-nesting vectors), 5 pairs, all 17 classes. The 95 vectors of the reviewed text are byte-identical; the 12 added ones are listed in §16. `limits-py.json`: 3 vectors. All 20 negative configurations rejected.
- **Vector-corruption self-test: 32 of 32 rejected**, 28 of them lexical. Each corrupted vector is rehashed so only the targeted layer is wrong. Examples: a dropped final DEDENT, DEDENT at the line start, NEWLINE before a trailing comment, NEWLINE inside brackets, blank-comment-line INDENT/DEDENT, `match` as keyword, `None` as ident, fullwidth `if` as keyword, `**=` and `->` split, `<>` merged, `..` merged, `0x_fF` as float, `09.5` split, `1if` merged, `b'w'` as string, `uu'x'` as one string, a whole f-string as one string, `{{c}}` split, `:=` taken inside a field, a t-string relabelled, wrong code, moved offsets, an invented code, a leftmost tie, a flipped hash bit, a `;` exclusion, and `tokenIndices` on a profile without exclusions.
- **Wrong-lexer self-test: 29 of 29 rejected** (24, plus the 5 the review found accepted). Each is a `pylex.Lexer` subclass with one rule changed. The vectors that reject each one:

  | Wrong lexer | Rejected by |
  | --- | --- |
  | tabs to the next multiple of 4 | `py-err-tab-vs-spaces`, `-tab-indent-alt`, `-tab4-dedent` |
  | no tab-size-1 check | the same 3 |
  | no DEDENT at end of input | 14 vectors, e.g. `py-format-a`, `py-eof-dedent` |
  | comment-only lines take part in indentation | `py-comment-only`, `py-format-b`, `py-blank-comment-lines` |
  | brackets do not suppress NEWLINE | `py-format-b`, `py-implicit-join`, `py-implicit-concat` |
  | f-strings lexed as plain strings | 14 f/t-string vectors |
  | soft keywords as keywords | `py-soft-keywords` |
  | raw strings: `\` does not take the next character | `py-raw-backslash`, `py-err-raw-odd-backslash` |
  | a lone CR is not a line terminator | `py-cr-lines`, `py-err-cr-in-string` |
  | CR LF counted as two terminators | `py-crlf-continuation` |
  | form feed counts as a column | `py-formfeed-indent` |
  | CPython's column-0 backslash quirk | `py-backslash-col0` |
  | `{{` escapes inside a format spec | `py-fstring-spec-brace`, `-spec-brace-after-field` |
  | no keyword exception after numbers | `py-number-keyword` |
  | exception words matched as prefixes | `py-err-number-whole-word` |
  | `0777` accepted | `py-err-legacy-octal` |
  | `0or` accepted | `py-err-radix-empty` |
  | incompatible prefixes accepted | `py-err-prefix-ur`, `-prefix-fb` |
  | lowercase-only prefixes | `py-string-prefixes`, `py-err-prefix-fb`, `py-tstring` |
  | `\N{` honoured in raw f-strings | `py-fstring-named-escape` |
  | INDENT/DEDENT at the line start | 14 vectors |
  | NEWLINE at the end of the last token | `py-format-b`, `py-continuation-blank`, `py-newline-after-comment`, `py-type-comment` |
  | the interpreter's Unicode 16.0.0 name tables | `py-unicode-17` |
  | `:=` wins over the spec `:` inside a field | `py-fstring-debug-walrus` |
  | review W03: no tab-size-1 check after a dedent | `py-err-tab-dedent-alt` |
  | review W12: a non-ASCII character after a number is malformed | `py-number-nonascii-follow` |
  | review W15: the closing quote inside a spec ends the f-string | `py-err-fstring-spec-quote` |
  | review W17: `{` inside `\N{...}` is text | `py-fstring-named-escape-field` |
  | review W19: end of input in a field reported at the field's `{` | `py-err-fstring-eof-field` |

- **Cross-check, vectors** (CPython 3.14.6). Of the 68 accepted vectors, 62 agree token for token and 6 diverge as tagged departures (`py-backslash-col0`, `py-unicode-17`, `py-ltgt`, `py-fstring-spec-brace-after-field`, and `py-deep-brackets` and `py-deep-fstrings` against CPython's depth limits, D-9). Of the 35 lexical error vectors, 18 are rejected by CPython at the same offset, 16 at another offset, and 1 (`py-err-dollar`, D-7) only by CPython's parser. 4 pre-lexing vectors are not compared. **0 undocumented divergences.**
- **Cross-check, standard library** of the same interpreter: 1,852 `.py` files, 36.0 MB. **1,847 of 1,847 lexable files agree token for token** (5,909,005 tokens, with 76 middle-run merges and 39 dropped empty middles). 4 files fail the pre-lexing checks: 3 `invalid-utf8`, 1 `bom`, all deliberate test data. 1 file (`test/tokenizedata/badsyntax_3131.py`) is rejected by both at the same offset.
- **Differential fuzz:** mutated standard-library snippets plus random concatenations of f-string, prefix, number and layout fragments, compared on accept/reject and token streams. Seed 11, 400,000 cases: 5,332 divergences, every one in a documented class (D-7 2,973, D-5 1,485, D-8 848, D-3 25, D-11 1); no other class. The full run's figures are in the [README](../test-vectors/extraction-python/README.md#2-cross-check-against-cpython-3146). While writing the lexer, earlier fuzz runs found two real rule errors, both since fixed and pinned by vectors: `0or` (`py-err-radix-empty`) and whole-word matching for `and/else/for/not/or` (`py-err-number-whole-word`).
- **Unicode sweep:** name start differs on 4,647 code points and continue on 4,699; all are accepted by the profile and rejected by CPython (D-8). None go the other way.

**Limits.** The hand-written streams, `pylex.py`, the independent checks and the wrong-lexer variants are by one author from one text. Their agreement, and the CPython agreement, show the text was applied consistently and that it matches CPython. The [clean-room review](../research/reviews/extraction-profile-python-review.md) then reproduced all 98 vectors of the reviewed text from the text alone, with four ambiguities and five unpinned rule choices, all resolved in §16. Two independent implementations (§13) remain the next gate. The standard library is well-formed Python; the fuzz covers malformed input only as far as its fragment list reaches.

## 12. Decisions

**Decided in draft, pending owner confirmation** (each changes tokens, hashes or accept/reject, and the vectors encode it):

| ID | Decision | Reason |
| --- | --- | --- |
| PYOD-1 | One profile `py-tokens` for `.py`/`.pyw`. `.pyi` is excluded by selection; notebooks, Cython and extensionless scripts are out of scope by selection; Python 2 is out of scope but not detectable (§2) | Same split as `.d.ts` (TSOD-7); nothing lexical distinguishes stubs |
| PYOD-2 | Encoding: declarations are comments; non-UTF-8 declaration plus non-ASCII bytes excluded by selection; BOM recorded by selection (§3.1) | Contract no-repair rule; no extraction error where selection can see it first |
| PYOD-3 | Soft keywords `match`, `case`, `type`, `_` are `ident` | Parser-level distinction (reference); rename robustness |
| PYOD-4 | (a) NEWLINE, INDENT, DEDENT are zero-width tokens with empty text in both channels; `normalizedExclusions` empty | §7 measurement: re-indentation 100% surviving with no exclusion; dropping INDENT/DEDENT blinds 136 of 136 control files |
| PYOD-5 | String content not validated; escapes and bytes' ASCII rule are value-level (D-4) | Not in the formal lexical grammar; fewer rules to agree on |
| PYOD-6 | Indentation by the reference's backslash sentence, not CPython's column-0 quirk (D-3); form feed resets (D-17) | Authority first; the undefined case pinned to CPython |
| PYOD-7 | Numbers: longest grammar match plus CPython 3.14's follow rule, including the radix check and whole-word exceptions (§5.4) | Accepts exactly what 3.14 accepts; no new behaviour invented |
| PYOD-8 | Format spec: no `{{`/`}}` escapes; closing quote inside a spec is `unterminated-literal` (D-6, D-11) | One rule per mode |
| PYOD-9 | No depth limits (D-9); nesting MUST use an explicit stack, not recursion (§5.7) | Limits are implementation details; the stack rule keeps every input within `maxInputBytes` decidable |
| PYOD-10 | f/t-string internals in stage 1 (§6.5, §13) | Finding the end needs the full field lexer anyway |

**Must be settled before implementation:**
- **PYOD-4 (b) or (a)**: whether to also exclude `punct ;` and `newline` from the normalized channel. Recommendation: keep (a), no exclusions. The gain is 0.43% of fingerprints in the rare files with `;`, and (a) keeps one fewer mechanism. If the owner prefers (b), it is a new `profileVersion` before freezing; the vectors and checker change in one place (`EXCLUSIONS`, the semicolon pair).
- **PYOD-6**: follow the reference (current) or CPython for a backslash at column 0 in leading white space. Recommendation: the reference. It produced no divergence in the 1,847 standard-library files; only the fuzz reached it.
- **PYOD-1 for `.pyi`**: exclude (current) or include. Recommendation: exclude for evaluation corpora, like `.d.ts`; it costs nothing to include later.
- **Owner confirmation of PYOD-2, -3, -5, -7, -8**, which change accept/reject or tokens.

**Can wait:** k and w for this profile (TW-05, contract OD-10); re-running the cross-check on each CPython 3.14.x patch release (contract §10 versioning); a notebook adapter; an independent clean-room review.

## 13. Staging

**Stage 1 is the whole profile** for `.py` and `.pyw`, f-strings and t-strings included. Nothing is deferred inside the lexer: the f-string mode machine agrees with CPython on every standard-library file and on the fuzz, and staging it would not remove any state (§6.5).

**What stage 1 misreads, compared with the language:**
- the departures D-3, D-5, D-6 and D-8, which give different tokens from CPython on input CPython accepts; none produced a divergence in the standard library;
- soft-keyword statements (`match`, `case`, `type`), which are lexed as names;
- NFKC-equal spellings of one name, which the exact channel treats as different (D-12);
- block structure in a fragment cut mid-block, which can fail with `unmatched-dedent` (§4.4);
- `;`-joined and one-line compound statements, which give different normalized fingerprints from their reformatted versions (§7: about 0.4% and 1.2% of fingerprints in the affected files).

**Deferred outside the lexer:** notebooks (a cell adapter), `.pyi` (a selection change only), Python 2 (no plan).

## 14. How hard is agreement, compared with Go, Rust and TypeScript

**Harder than Go and Rust by a clear margin; about as hard as `ts-tokens`, with a different risk profile.**

- **Go and Rust** are nearly context-free at the token level, apart from Go's one-flag semicolon rule and Rust's nested comments and shebang. Python has three pieces of state:
  - the indentation stack with two widths, the form-feed reset and the backslash rule;
  - a stack that mixes brackets, f/t-strings and replacement fields, with literal, spec and normal modes;
  - CPython's number-follow rule, which is a lookahead quirk.
- **TypeScript's main risk is a guess.** Regex versus division needs a parser, so the `exprEnd` flag has documented departures on real code (`}` of declarations, `await` as a name). **Python has no such guess.** Every rule here is decidable lexically, and the reference tokenizer itself is lexical. The only departures are deliberate choices about edge cases (D-3, D-6) and tables (D-8), and none of them produced a divergence in 1,847 standard-library files.
- **Python has a better oracle.** CPython's parser-mode tokenizer is callable directly, with identifier and number checks on. The cross-check needs only two declared adjustments (middle merge and empty middles), against TypeScript's three, which included parser re-scanning.
- **Where two implementations will most likely differ:**
  - f-string literal and spec modes: `\N{`, a backslash before a brace, `{{` in specs, a quote in a spec, a line terminator in a single-quoted spec;
  - indentation edge cases: form feeds, a backslash in leading white space, `alt` comparisons on dedent;
  - the number-follow lookahead (`1ifx` valid, `1orx` invalid, `0or` invalid).

  These are exactly where the vectors and wrong-lexer variants are densest, and two of them (`0or`, whole-word `or`) were found by the fuzz in the author's own lexer during this draft. That is evidence the text is subtle there, not that it is now complete.

**Recommendation:** freeze after a clean-room review reproduces the vectors from this text alone. Before two implementations start, run an M1.4-style differential (random token streams with mutations), aimed at the f-string modes and at indentation with tabs, form feeds and continuations.

## 15. "Before registering a profile" checklist ([profiles/code.md](code.md))

| Item | Where |
| --- | --- |
| Language and grammar revision | §1: reference and grammar at `v3.14.6` (digests); CPython 3.14.6 oracle; Unicode 17.0.0 |
| Tokenizer rules | §3–§6 |
| Scope resolution | None: the normalized channel is lexical and not scope-aware (contract §12) |
| Encodings | §3.1: UTF-8 only, no BOM, no NUL; declarations are comments; lone CR is legal |
| Parser error behavior | No parser. Lexical errors in §8; syntactically invalid but lexically valid input is fingerprinted (for example a first line that is indented) |
| Comments and docstrings | Comments dropped (§4.3). Docstrings are `string` tokens and are erased in the normalized channel only |
| Significant whitespace | §4: zero-width NEWLINE/INDENT/DEDENT; width and tab choice never hashed |
| Macros and generated code | No macros. Generated files excluded by the `@generated`/`DO NOT EDIT` rule (§2) |
| Token serialization | §7, contract §6 |
| Hash parameters, window sizes, tie-breaking | Contract §7–§8 and OD-10 (k = 5, w = 4, rightmost minimum) |
| Coordinate units | UTF-8 byte offsets, half-open (contract §3). The cross-check converts CPython's line/column code-point positions, after its CR LF/CR translation, back to the original input |

## 16. Review dispositions

The [clean-room review](../research/reviews/extraction-profile-python-review.md) of commit `1c5c06a` (review commit `0db8b44`) found:

| Finding | Resolution |
| --- | --- |
| §3 W03, W12, W15, W17, W19: five wrong lexers the checker accepted (blocking) | One vector each, and the five variants added to the wrong-lexer self-test, which now rejects 29 of 29: `py-err-tab-dedent-alt` (W03), `py-number-nonascii-follow` (W12), `py-err-fstring-spec-quote` (W15, D-11), `py-fstring-named-escape-field` (W17), `py-err-fstring-eof-field` (W19) |
| A1 does a field end a `\N{` named escape (blocking) | Yes (§6.3); `py-err-fstring-named-escape-ended` |
| A2 continuation in leading white space followed by an empty or comment-only line (blocking) | The logical line is blank (§4.3); `py-continuation-then-blank` |
| A3 a second continuation in the same leading white space (blocking) | Skipped; the indentation is fixed at the first (§4.4); `py-continuation-twice-indent` |
| A4 a single quote in the spec of a triple-quoted f-string (blocking) | Only the closing delimiter, one or three quotes, counts (§6.2); `py-fstring-triple-spec-quotes` |
| L2 recursion bounded only by input size (blocking) | §5.7: an explicit stack is required and per-level recursion is non-conformant; `py-deep-brackets` (1,000 levels) and `py-deep-fstrings` (200 levels) |
| C2 oracle entry point for lone CR | §1 and D-18: judged against `compile()`; the cross-check translates CR LF and CR itself before calling the tokenizer |
| L1 layout-only k-grams with empty spans | §4.5 note with what the catalogue contract must say; `py-empty-span-fingerprint`, whose empty-span fingerprint `[35, 35)` the checker requires |
| L3 which encoding names count as UTF-8 | §3.1 list (PYOD-2) |

**No token, hash or existing vector changed**: the 95 earlier vectors are byte-identical, the configuration digests are unchanged, and the version stays `draft-1`. `py-err-fstring-spec-quote` is not tagged `departure`, because CPython's tokenizer also rejects that input; D-11 applies only when a later `}` balances the field.

## 17. Freeze record: `py-tokens` `draft-1`

**Frozen for stage-1 implementation, pending owner confirmation of the decided-in-draft items** (§12: PYOD-1 to PYOD-10). Implementations target these exact bytes. Any change to them needs a new `profileVersion` (contract §10 versioning).

| File (in [test-vectors/extraction-python/](../test-vectors/extraction-python/README.md)) | SHA-256 |
| --- | --- |
| `py.json` (107 vectors) | `85de9fdf8c2469447bd20da890498d203013545f4f402802c218520118e2813a` |
| `limits-py.json` (3 vectors) | `94b6d7b2f0c498be5bbafff3c92ecdcdac9de1beb6a5781b0cf8d5c5d7ff666a` |
| `config-py.json` (= `configSha256`) | `365ba7be82646f6505cc339a15b3f5c50632244001eee2e08c558ce22c77b016` |
| `config-py-limit16.json` | `02dd6c5790677df8175faada9fdb938613e26dc6ed886ec597fc642aea64c562` |
| `config-negative-python.json` (20 negatives) | `509203a14b281cb87d4f80298b6f0b20cc25b53ee75dee43b82cd06218ba8522` |
| `../test-vectors/extraction/unicode-17.0.0-tables.json` (shared, contract §3a) | `9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f` |

**The normative text** is this document's §1–§10, with `normalizedExclusions` empty. Its digest is the git blob at the commit that adds this record. `check_vectors.py`, `pylex.py` and the harness are verification tooling, not frozen artifacts. They may change without a version bump as long as the frozen bytes above still pass. The open decisions in §12 that must be settled before implementation (PYOD-4, PYOD-6, PYOD-1) are settled as currently written unless the owner rules otherwise; a different ruling is a new `profileVersion`.
