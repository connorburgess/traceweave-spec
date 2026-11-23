# Clean-room review: Python token profile `py-tokens` draft-1

Reviewed 2026-11-23 at commit `1c5c06a` on `roadmap-v2`: [extraction-profile-python.md](../drafts/extraction-profile-python.md) and [extraction-vectors-python/](../drafts/extraction-vectors-python/README.md). The model is the [TypeScript profile review](extraction-profile-typescript-review.md). I did not write any of it.

**Order kept.** I read the profile text, `spec/extraction.md` §2–§3 and §6–§8, and the field layout of `py.json`, then wrote my lexer and ran it on the vectors. Only after that did I open `check_vectors.py`; I never opened `pylex.py` or the harness sources. My scripts are in `$TMPDIR/pyrev/`. No downloads were made. The interpreter is CPython **3.14.6** with `unicodedata.unidata_version` 16.0.0, as the profile pins.

## 1. Clean-room lexer (`mylex.py`, about 300 lines, iterative, explicit stack)

**Result: every vector reproduced on the first run.**

| File | Vectors | Matched | What was compared |
| --- | --- | --- | --- |
| `py.json` | 95 (52 ok, 8 insufficient-tokens, 35 errors) | **95/95** | status; every token (class, text, span); error code and offset; per channel `kgrams` (position, hash, span), `windowSelections`, `partialWindow`, `fingerprints`, and normalized `values` |
| `limits-py.json` | 3 (1 ok, 2 errors) | **3/3** | the same |

**Guesses.** I logged 12 guesses while writing (`GUESSES` in `mylex.py`). Eight turned out to be decided by the text once read closely: §6.3 for `\` before a quote, §6.1 for empty middles, §5.4 for the follow rule on every number class (so `1f'x'` is `malformed-literal`), §8/§6.4 for end-of-input precedence, §6.2 for a `)` closer with a field on top, and §5.2 for soft keywords. **Four are genuine ambiguities.** None changed a vector:
- **A1 (§6.3, `\N{`).** "Inside it, `{` still opens a field." The text does not say whether the named escape is still open after that field closes, that is, whether a later `}` is still escape text. CPython ends the escape at the field: `f'\N{A{x}B}'` is "single '}' is not allowed". My lexer also ends it, but only because my implementation happened to; I had guessed the other way. **Fix:** add "the field ends the named escape", plus a vector.
- **A2 (§4.3/§4.4).** A `\` continuation in leading white space followed by an empty or comment-only physical line. Is the logical line blank? I treated it as blank, which agrees with CPython (`x = 1\n\\\n\ny = 2\n` compiles). **Fix:** state it.
- **A3 (§4.4).** A second `\` continuation in the same leading white space. "Up to the first backslash" implies later ones are ignored, and I froze `(col, alt)` at the first. **Fix:** one sentence, "later continuations in the same leading white space are skipped".
- **A4 (§6.2 spec mode).** Does a single quote character inside the spec of a **triple-quoted** f-string end it? I read "the enclosing f-string's closing quote" as the full three-quote delimiter; CPython agrees (`f'''{x:a'b}'''` and `f'''{x:a''b}'''` compile). **Fix:** say "closing delimiter (one or three quotes)".

## 2. Independent cross-check against CPython 3.14.6 (my inputs, 463 cases)

**Method.** I drove CPython through `tokenize._generate_tokens_from_c_tokenizer(readline, extra_tokens=False)`, mapping NAME to keyword or ident and NUMBER to int, float or imag. Layout tokens were compared by class only, and each run of FSTRING_MIDDLE was compared as one middle. Where either side rejected, I compared accept/reject only, not offsets. Lone-CR cases were also checked with `compile()` (see C2).

| Area | Cases | Agree | Divergences, each with its smallest input |
| --- | --- | --- | --- |
| Indentation: tabs, form feeds, blank and comment-only lines, continuations, end of input without newline | 40 | 39 | `if x:\n\ty\n\t\\\n  z\n`: CPython TabError (it copies col into alt), profile accepts. **D-3, decided** |
| Implicit joining | 8 | 8 | — |
| f/t-strings: nested quotes, nested f-strings, fields, specs, `=`, `!r`, backslashes, triple-quoted multi-line fields, comments in fields, `\N{` | 71 | 69 | `f'{x:{y}{{z}}}'` (**D-6**); `f'{x:{y:{z:{w}}}}'` CPython "nested too deeply" (**D-9**). Three apparent differences on `{{`/`}}` were my adapter's middle-merge, not divergences (D-15) |
| Prefixes: 52 spellings × 3 quote forms (every case combination of b/r/u/f/t and the invalid sets) | 156 | 156 | — |
| Numbers: radixes, `_`, exponents, imaginary, legacy octal, and what may follow (`1if`, `1orx`, `1else 2`, `0x1for`, `1é`, `1j2`, `1.real`) | 84 | 84 | — |
| Soft keywords and Python 2 words | 10 | 10 | — |
| Unicode names (NFKC forms, fullwidth `ｉｆ`, middle dot, U+2E2F, combining marks, U+A7CD) | 29 | 29 | — |
| Line terminators (CR, CR LF, lone CR, VT, FF, U+0085, U+2028) | 15 | 11 → 15 | See C2: all 4 differences are a property of the oracle path, and `compile()` agrees with the profile on every one |
| NUL and encoding declarations (latin-1, cp037 and utf-16 declarations on ASCII files) | 6 | 6 | — |
| Plain strings, raw backslashes, triple quotes | 19 | 19 | — |
| Operators | 25 | 21 | `a<>b` (**D-5**); `$`, `?`, `` ` `` (**D-7**) |

**Unicode sweep, re-derived from the pinned table.** Name start: 4,647 code points accepted by the profile and rejected by CPython; continue: 4,699; none the other way. This equals §11 (**D-8**).

**No undocumented token divergence.** One oracle note:
- **C2 (oracle path, not a profile defect).** The C tokenizer reached through `tokenize` readline does **not** treat a lone CR as a line terminator: `x\ry\r` tokenizes as `x` and an OP `\ry`. `compile()`, which reads source with universal newlines, accepts `x\ry\r`, `if x:\r  y\r` and `# c\rx` as the profile does, and rejects `'a\rb'` and `f'a\rb'` as unterminated, as the profile does. So §4.1 is right against the compiler.
- **Fix:** add a D-row naming the oracle entry point. The §1 cross-check claim ("converts CPython's … positions after its CR LF/CR translation") should say which path translates.

## 3. Wrong-but-plausible lexers against the real checker

I wrote 24 single-rule mutations of **my** lexer, not of `pylex.py`, and routed the checker's `pylex.lex` to each one. That way `check_vectors.check_vector` judges every shipped vector with its own independent invariants. My correct lexer is rejected by 0 vectors. **19 of 24 are rejected; 5 are accepted, which means the vectors miss them:**

| Variant | Rejected by |
| --- | --- |
| W01 form feed in leading white space ignored | `py-formfeed-indent` |
| W02 tab adds 8 columns instead of the next multiple of 8 | `py-err-tab4-dedent` |
| W04 no alt check at equal col | `py-err-tab-vs-spaces`, `-tab4-dedent` |
| W05 NEWLINE at a trailing comment's start | `py-newline-after-comment`, `py-type-comment` |
| W06 final DEDENTs before the final NEWLINE | `py-eof-dedent` |
| W07 lone CR allowed in a single-quoted string | `py-err-cr-in-string` |
| W08 `\` + terminator at end of input accepted | `py-err-backslash-eof` |
| W09 `uu'x'` treated as a malformed prefix | `py-prefix-ident` |
| W10 `rb'…'` classed `string` | `py-string-prefixes` |
| W11 `if`/`in`/`is` after a number must be whole words | `py-number-keyword` |
| W13 `<>` one token | `py-ltgt` |
| W14 `$`, `?`, `` ` `` as punct | `py-err-dollar` |
| W16 `\{` makes the brace text | `py-fstring-backslash-brace` |
| W18 `:` inside brackets in a field starts the spec | `py-fstring-debug-walrus` |
| W20 indentation errors at the line start, not the first token | 4 tab/dedent error vectors |
| W21 `...` not an operator | `py-operators`, `py-dots` |
| W22 line terminator in a single-quoted f-string field is an error | `py-fstring-multiline-expr` |
| W23 `00` and `0_0` rejected | `py-numbers` |
| W24 name-continue uses `xid_start` | `py-unicode-names` |
| **W03 no alt check on dedent** | **accepted.** `if a:\n\tif b:\n\t\tc\n        d\n`: profile `inconsistent-indentation`@25 (CPython TabError); W03 accepts |
| **W12 non-ASCII after a number is malformed** | **accepted.** `x = 1é`: profile int then ident (CPython agrees); W12 `malformed-literal`@4 |
| **W15 closing quote inside a spec ends the f-string** | **accepted.** `f'{x:abc'`: profile `unterminated-literal`@0 (D-11); W15 accepts. D-11 has no vector |
| **W17 inside `\N{…}`, `{` is text** | **accepted.** `f'\N{BULLET{x}'`: profile and CPython open a field; W17 does not |
| **W19 end of input in a field reported at the field's `{`** | **accepted.** `f'{x`: profile `unterminated-literal`@0; W19 @2 |

**Fix (blocking).** Add five vectors with those inputs, so that each accepted variant is rejected, and add them to the self-test list.

## 4. Design decisions

**Zero-width NEWLINE/INDENT/DEDENT, no `normalizedExclusions`: sound.**
- **Re-derived independently:** I rewrote 60 standard-library modules to two spaces per block level, changing only logical-line starts (the AST stayed identical). Both channels kept identical fingerprint sets in **60/60** files.
- **Author harness re-run** (`layout_survival.py --limit 40`): re-indent and tabs survive 100.00%; the control is blind in 0/34 files with no exclusion and 34/34 with all layout excluded. That matches §7.
- **Positions are fully determined:**
  - NEWLINE sits at the first byte of the terminator, or at the input length.
  - INDENT and DEDENT sit at the first byte of the line's first token, prefix included.
  - Order at one offset is layout before the token, and at end of input NEWLINE then DEDENTs.
- **Text, hashing, record:** `text == input[span]` holds, and hashing sees only `LP(class)‖LP("")`. I found no way for two implementations to place them differently once A2 and A3 are fixed.
- **One effect not stated (L1).** At k = 5, a file that ends four or more blocks deep yields a k-gram made only of NEWLINE and DEDENTs, with an **empty span** `[n, n)`. It is also a fingerprint: `if a:\n if b:\n  if c:\n   if d:\n    x` has a fingerprint at `[35, 35)`. Similar layout-only k-grams across a dedent cover only white space and comments, and they repeat across files as common hashes.
  - The catalogue contract allows empty spans (OD-C16), but it argued them only for k = 1. No `py-tokens` vector has one.
  - **Fix:** a vector, plus one sentence in §4.5 that layout-only k-grams and empty spans occur at the default configuration. Their effect on M2 localization is for the matching contract.

**Full f-string lexing in stage 1: agree.** My implementation is one iterative state machine with a stack of bracket, f-string and field entries and no parser. It ports directly to Rust and Go. The opaque alternative cannot find the end of `f"{x["a"]}"`.

**No depth limits: acceptable, with one sentence added (L2).**
- **The contract makes nesting finite but not small.** It bounds input size (§10a) and requires O(N) time and memory, so depth is bounded by N but can be about 350,000 within 1 MiB.
- **Both lexers handle the extreme:** about 1 MiB of `(`, 349,000 nested `f'{`, and 260,000 spec-nested fields each finish in 2–6 s with the same result and offset in my lexer and in `pylex`.
- **But a recursive implementation would overflow its stack** at that depth, and the profile does not forbid recursion. **Fix:** "nesting MUST be tracked with an explicit stack; recursion per nesting level is non-conformant on inputs within `maxInputBytes`".

**Soft keywords as `ident`: agree.** This is lexically forced, and it matches CPython and the Go and TypeScript precedents.

**Excluding non-UTF-8 sources by selection: agree, with one gap (L3).**
- **The gap:** §2 and §3.1 name the declaration pattern but not which names count as UTF-8. Selection tools in two languages need the list. `utf8`, `UTF-8`, `utf_8`, `utf-8-sig` and Python's other aliases are all spelled differently.
- **Fix:** normalize the name (lowercase, `_` to `-`), treat `utf-8`, `utf8` and `utf-8-sig` as UTF-8, and treat anything else as non-UTF-8.

## 5. Open decisions and staging

**Settle before implementation:**
- **PYOD-4:** keep (a), no exclusions. The measurement and my re-derivation agree.
- **PYOD-6:** follow the reference. D-3 never occurs in the standard library, and the rule is now testable (`py-backslash-col0`).
- **PYOD-1:** `.pyi` excluded by selection.
- **Owner confirmation of PYOD-2, -3, -5, -7, -8, -9:** I agree with each as drafted, with L2 added to PYOD-9 and L3 added to PYOD-2.

**Staging: one stage, as §13 proposes.** Nothing inside the lexer would shrink if deferred.

## Verdict

**Ready after listed fixes.** None changes a token, a hash or an existing vector, so `draft-1` can stay the version.

Blocking:
1. Five vectors for the accepted wrong lexers W03, W12, W15, W17 and W19 (§3).
2. Text for A1–A4 (§1).
3. The explicit-stack requirement (L2).

Non-blocking:
- the C2 oracle-path D-row;
- an empty-span layout vector and its note (L1);
- the UTF-8 alias list for selection (L3).
