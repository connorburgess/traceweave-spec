# Draft extraction profile: TypeScript and JavaScript (`ts-tokens`, `tsx-tokens`)

Status: **draft for review, revision draft-1, 2026-11-22.** Roadmap items TS.1 and TS.2. TS.3 (two implementations) and TS.4 (own M3 split) are implementation gates and are not claimed here.

This is research material, not a normative change. It does not modify `spec/`, `schemas/`, `profiles/`, `test-vectors/` or the [extraction contract](extraction-contract.md). "MUST" describes what this draft proposes for an implementation claiming to follow it. Nothing here is a registered algorithm.

**How it plugs in.** This document adds two profile sections in the shape of contract §4 (Go) and §5 (Rust). Every shared part of the contract applies unchanged:
- §2 outcomes, the no-repair rule and the error-offset rules;
- §3 processing order: configuration, size, UTF-8, then U+FEFF (`bom`) and U+0000 (`nul`). This profile adds no forbidden code point, so a lone CR is legal;
- §3a Unicode 17.0.0 data, plus two small deltas derived from the same digest-pinned file (§3.2);
- §6 serializations, §7 k-gram hashing, §8 winnowing and §9 record fields;
- §10 configuration bytes and validation. This profile only adds two `(profile, profileVersion)` pairs (§10 below).

The vectors are in [extraction-vectors-typescript/](extraction-vectors-typescript/README.md). Decisions are in §12. Items marked "decided in draft" are pending owner confirmation.

## 1. Authority and pins

- **ECMAScript.** *ECMAScript® 2026 Language Specification* (ECMA-262, 17th edition), the HTML rendering at [tc39.es/ecma262/2026](https://tc39.es/ecma262/2026/), retrieved 2026-11-22, SHA-256 `0119d5a26afb504f4a7aba84d9d8288912044cc459c0552ea5f22f911cb87f40`. The online copy is mutable. The formal Ecma PDF was not retrieved and should be pinned before promotion. This profile cites these sections:
  - §12.1 format-control characters, §12.2 white space, §12.3 line terminators, §12.4 comments and §12.5 hashbang comments;
  - §12.6 tokens, §12.7 names and keywords (§12.7.2 ReservedWord), §12.8 punctuators;
  - §12.9.3 numeric, §12.9.4 string, §12.9.5 regular-expression and §12.9.6 template literals;
  - §12.10 automatic semicolon insertion, and Annex B.1.1 HTML-like comments.

  Where this profile restates ECMA-262, ECMA-262 governs, and a conflict is a profile defect. Every deliberate departure is listed in §9.
- **TypeScript.** No current TypeScript language specification exists: the last published one describes TypeScript 1.8 and is no longer maintained. For the four TypeScript-only lexical points, this profile's text is the authority: type-argument `<`/`>`, non-null `!`, the decorator `@` and the `.tsx` generic-arrow rule. **TypeScript 6.0.3** is the cross-check oracle (npm `typescript@6.0.3`, integrity `sha512-y2TvuxSZPDyQakkFRPZHKFm+KKVqIisdg9/CZwm9ftvKXLP8NRWj38/ODjNbr43SsoXqNuAisEf1GdCxqWcdBw==`, pinned in [harness/package-lock.json](extraction-vectors-typescript/harness/package-lock.json)).
  - 6.0.3 is the last release built on the JavaScript compiler with the public `createScanner`/`createSourceFile` API. The npm `latest` tag is 7.0.2, the native port, which does not ship that API in the package.
  - When TypeScript 7 exposes a scanner or parser API, re-run the cross-check (contract §10 versioning).
- **Unicode.** 17.0.0, per contract §3a.

## 2. Inputs in scope, and why two profiles

| Input | Profile | Reason |
| --- | --- | --- |
| `.ts`, `.mts`, `.cts` | `ts-tokens` | No JSX: `<` at expression start is a type assertion or a generic |
| `.tsx`, `.jsx` | `tsx-tokens` | JSX recognized (§5) |
| `.js`, `.mjs`, `.cjs` | `tsx-tokens` | TypeScript treats JavaScript files as JSX-capable. Valid JavaScript without JSX lexes identically under both profiles, because `<` at expression start is not valid JavaScript outside JSX (vector `tsx-plain-js`) |

**Why two profiles and not one or four.** At the token level TypeScript adds nothing to ECMAScript except `@`, which both profiles accept. JavaScript and TypeScript therefore need no separate grammars. JSX is the one real fork: `<T>x` is a type assertion in `.ts` and an element in `.tsx`, and no lexical rule can serve both (vectors `ts-type-assertion` and `tsx-err-ts-type-assertion` use the same input). Separate `js-tokens` and `jsx-tokens` profiles would duplicate these two with no lexical difference.

**The extractor never sees file names.** It receives configuration bytes and input bytes (contract §1). Mapping an extension to a profile, and the exclusions below, are file-selection rules that belong to TW-01/TW-03. TS.1 requires them, so they are proposed here as decided in draft (TSOD-1, TSOD-7):

- **Declaration files are excluded:** names ending `.d.ts`, `.d.mts` or `.d.cts`, or matching `*.d.*.ts` (for example `styles.d.css.ts`). They are mostly emitted by `tsc` or are type surfaces, and they repeat heavily.
- **Generated files are excluded:** the first 2048 bytes contain `@generated` or `DO NOT EDIT`.
- **Minified files are excluded:** a name ending `.min.js`, `.min.mjs` or `.min.cjs`, or any line longer than 4096 bytes. Lines are split at LF, CR, LS or PS.
- **Paths:** `node_modules/`, vendored and build-output directories are TW-01/TW-03 path rules (contract OD-14).

An excluded file is not extracted. Exclusion is never an extraction result or error code.

## 3. Before tokens

### 3.1 White space and line terminators (§12.2, §12.3)

- **White space:** U+0009, U+000B, U+000C, U+FEFF (unreachable, because §3 of the contract rejects it first), and General_Category Zs in Unicode 17.0.0. Zs is exactly these 17 code points: U+0020, U+00A0, U+1680, U+2000–U+200A, U+202F, U+205F and U+3000.
- **Line terminators:** U+000A, U+000D, U+2028 (LS) and U+2029 (PS). CRLF is one line terminator sequence. A lone CR is a line terminator, not an error. Offsets and token text keep the original bytes (contract OD-9).
- **Everything else is not white space.** U+0085 (NEL), U+180E and U+200B are `illegal-character` outside comments and literals. TypeScript 6.0.3 treats U+0085 and U+200B as white space (§9, D-6).

### 3.2 Identifier characters (§12.7.1)

ECMA-262 2026: IdentifierStartChar is UnicodeIDStart, `$` or `_`, and IdentifierPartChar is UnicodeIDContinue or `$`. These use **ID_Start/ID_Continue**, not the XID properties. The pinned table (contract §3a) holds `xid_start` and `xid_continue`, so this profile defines:

- `id_start` = `xid_start` ∪ {U+037A, U+0E33, U+0EB3, U+309B, U+309C, U+FC5E–U+FC63, U+FDFA, U+FDFB, U+FE70, U+FE72, U+FE74, U+FE76, U+FE78, U+FE7A, U+FE7C, U+FE7E, U+FF9E, U+FF9F} (23 code points);
- `id_continue` = `xid_continue` ∪ {U+037A, U+309B, U+309C, U+FC5E–U+FC63, U+FDFA, U+FDFB, U+FE70, U+FE72, U+FE74, U+FE76, U+FE78, U+FE7A, U+FE7C, U+FE7E} (19 code points).

These are exactly ID_Start − XID_Start and ID_Continue − XID_Continue in the digest-pinned UCD 17.0.0 `DerivedCoreProperties.txt`. In that file, XID ⊂ ID holds, U+200C/U+200D are in ID_Continue, and Zs is as listed in §3.1. [harness/derive_deltas.py](extraction-vectors-typescript/harness/derive_deltas.py) re-derives all of this and refuses other file digests. The library rule of contract §3a applies: an implementation MUST NOT use a runtime's `\p{ID_Start}` or the TypeScript scanner's tables unless they are shown identical. TypeScript 6.0.3's tables differ on 8,949 start and 9,132 part code points, all of them characters newer than its tables (§11).

**No NFC check.** ECMAScript does not normalize identifiers, so precomposed and decomposed `é` are different names. Unlike the Rust profile, there is no `non-nfc-identifier` error.

**Unicode escapes.** A `\u` escape is `\u` followed by exactly four hex digits, or `\u{` followed by one or more hex digits with value ≤ 10FFFF, then `}`. An escape in an IdentifierName is valid only if the code point it denotes is itself an IdentifierStartChar (first position) or IdentifierPartChar (later positions). Surrogate escapes are never combined, so `a𝐀` is invalid (§12.7.1.1).

### 3.3 Hashbang (§12.5)

If the input begins with `#!`, everything up to the first line terminator (exclusive), or to the end of input, is trivia. Because a BOM is already rejected, this is only possible at offset 0. `#!` anywhere else is `#` followed by `!`, which is `illegal-character` at the `#` (vector `ts-err-hashbang-not-first`).

## 4. Scanning, both profiles

### 4.1 Token classes and the keyword rule

**Classes** (closed list): `keyword`, `ident`, `privatename`, `punct`, `number`, `bigint`, `string`, `template`, `template-head`, `template-middle`, `template-tail`, `regex`, `jsx-text` and `jsx-string`. The last two occur only in `tsx-tokens`. The four template classes are the ECMAScript tokens NoSubstitutionTemplate, TemplateHead, TemplateMiddle and TemplateTail.

**`keyword`** is a fixed list of 46 words: the 38 ECMAScript ReservedWords (§12.7.2), `await break case catch class const continue debugger default delete do else enum export extends false finally for function if import in instanceof new null return super switch this throw true try typeof var void while with yield`, plus the 8 strict-mode reserved words, `implements interface let package private protected public static`. TypeScript code is module code and therefore strict. An IdentifierName is `keyword` if and only if all of these hold:
1. its text is in the list;
2. it is written without any `\u` escape (§12.7.2 Note 1: an escaped spelling cannot be a keyword);
3. the previous token is not `punct` `.` or `?.` (a property name);
4. it is not inside a JSX tag (§5.3).

Every other IdentifierName is `ident`. That covers every **TypeScript-only and contextual word**, such as `type`, `abstract`, `declare`, `readonly`, `namespace`, `module`, `keyof`, `infer`, `is`, `asserts`, `satisfies`, `as`, `async`, `of`, `get`, `set`, `accessor`, `override`, `using`, `any`, `number`, `string` and `unknown`. They are `ident` in every position, the way Go's predeclared identifiers are (contract OD-7). TypeScript's scanner gives them keyword kinds. The cross-check therefore compares keyword and ident as one class, and the checker enforces the list (§11). See TSOD-2 for the option of a separate class.

### 4.2 Scanning loop

The scanner keeps a **stack** whose entries are `(`, `[`, `{`, `${` and, in `tsx-tokens`, `tag`, `elem` and `jbrace` (§5). It also keeps a boolean **`exprEnd`** ("the previous token can end an expression"), which is false at the start of input. The stack top selects the mode: `elem` selects children mode (§5.4), `tag` selects tag mode (§5.3), and anything else selects normal mode.

In normal mode, after the hashbang (§3.3), at each position:

1. **Trivia:** white space and line terminators (§3.1), `//` comments to the next line terminator (exclusive) or end of input, and `/*` comments to the first following `*/`. Block comments do not nest. With no `*/`, the result is `unterminated-comment` at the `/`.
2. **`\` not followed by `u`** is `illegal-character` at the `\`.
3. **IdentifierName:** starts at an IdentifierStartChar or at `\`. Read IdentifierStart IdentifierPart\* (§3.2). Any `\` met while reading belongs to the name, and an invalid escape is `malformed-identifier` at the token start. The class follows §4.1. `exprEnd` becomes true, except that a `keyword` sets it true only for `this`, `super`, `null`, `true` and `false`.
4. **Number:** starts at an ASCII digit, or at `.` followed by an ASCII digit (§4.5).
5. **`'` or `"`:** a string (§4.6).
6. **`` ` ``:** a template (§4.7).
7. **`#`:** if the next character is an IdentifierStartChar or `\`, read `#` IdentifierName as `privatename`. An invalid escape there is `malformed-identifier` at the `#`. Otherwise the result is `illegal-character` at the `#`.
8. **`/`** (not a comment): when `exprEnd` is false, a regular expression (§4.8); otherwise punctuation.
9. **`<`** in `tsx-tokens` when `exprEnd` is false: JSX, unless the generic-arrow look-ahead (§5.2) says otherwise.
10. **`(`, `[`, `{`:** `punct`, pushed onto the stack, `exprEnd` false. A `(` whose previous token is the `keyword` `if`, `while`, `for` or `with` is marked as a **header**.
11. **`)`, `]`, `}`:**
    - `}` with `${` on top pops it and continues a template (§4.7).
    - `}` with `jbrace` on top pops it and emits `punct` `}` (§5).
    - Otherwise the closer must match the top (`(`, `[` or `{`); if it does not, or the stack is empty, the result is `unbalanced-delimiter` at the closer.
    - After a matching closer, `exprEnd` is true, except after a `)` that closes a header, where it is false.
12. **Punctuator:** the longest match from §4.4, class `punct`. After `!`, `++` or `--`, `exprEnd` is unchanged (§4.9). After any other punctuator it is false.
13. **Any other character** is `illegal-character` at its offset, for example U+2E2F, U+180E, U+0085 and `€`. (`@` is a punctuator, §4.4.)

**End of input.** If the stack is empty, scanning is done. If the top is `${`, the result is `unterminated-literal` at the start of the template-head or template-middle token that opened it. Otherwise the result is `unbalanced-delimiter` at the innermost unclosed opener: the `(`, `[`, `{`, or the `<` of a JSX tag or element.

### 4.3 Comments (§12.4, Annex B.1.1)

Single-line and multi-line comments are trivia. Comment content, including `/** … */` JSDoc, never produces tokens (compare Rust OD-5).

**Annex B HTML-like comments are not recognized** (decided in draft, TSOD-6). `<!--` lexes as `<` `!` `--`, and `-->` at the start of a line lexes as `--` `>` (vector `ts-html-comment`). The reasons:
- Annex B.1.1 applies only to the Script goal;
- TypeScript files are modules;
- TypeScript 6.0.3 does not recognize these comments either;
- recognizing them would require knowing the goal symbol, which the bytes do not reveal.

In `tsx-tokens`, `<!--` in expression position opens JSX, and the `!` is then `illegal-character` (vector `tsx-err-html-comment`).

**Merge-conflict markers** (`<<<<<<<`, `=======`, `>>>>>>>`) are not trivia. They lex as punctuators. TypeScript treats them as trivia with a diagnostic (D-7).

### 4.4 Punctuators (§12.8)

The punctuators are the ECMAScript OptionalChainingPunctuator, OtherPunctuator, DivPunctuator and RightBracePunctuator sets, plus `@`:

```
{ } ( ) [ ] . ... ; , < > <= >= == != === !== + - * % ** ++ -- << >> >>> & | ^ ! ~ && || ?? ? ?. :
= += -= *= %= **= <<= >>= >>>= &= |= ^= &&= ||= ??= => / /= @
```

`@` is the TypeScript decorator token (vector `ts-decorators`). ES2026 has no decorators.

**Longest match applies everywhere in normal mode**, with one exception, the ECMAScript lookahead: `?.` is not a token when a decimal digit follows, so `a?.5:1` is `? .5 : 1` (vector `ts-optional-chaining`).

**`>`, `>>` and `>>>` in generics** (decided in draft, TSOD-4). The `>` family follows longest match even where it closes type arguments: `Map<string, Array<number>>` ends with one `>>` token (vector `ts-generics-gt`). This is the ECMAScript lexical grammar applied without a parser. TypeScript's scanner always returns a single `>` and lets its parser re-scan in expressions. The cross-check accepts that as the declared `gt-merge` adjustment (71 occurrences in the corpus). The cost is that `Array<Array<T>>` and `Array<Array<T> >` differ by one token; the second form is rare after formatting. Option (b), always splitting the `>` family, is in TSOD-4.

### 4.5 Numeric literals (§12.9.3)

Starting at an ASCII digit, or at `.` followed by an ASCII digit, scan as follows. "Separator rules" means that `_` may appear only between two digits, so a leading `_`, a trailing `_` or `__` is an error.

1. **`0x`, `0X`, `0b`, `0B`, `0o` or `0O`:** consume the prefix, then the maximal run of IdentifierPartChars. The run MUST be one or more digits of the radix under the separator rules, optionally followed by `n` (class `bigint`; otherwise `number`).
2. **`0` followed by an ASCII digit:** consume the maximal run of ASCII digits.
   - If every digit is 0–7, the literal is a LegacyOctalIntegerLiteral. It ends there, with no fraction, exponent or `n`. So `07.5` is `07` then `.5` (vector `ts-legacy-octal`).
   - Otherwise it is a NonOctalDecimalIntegerLiteral. It may take a fraction and an exponent (step 4), but no separators and no `n`.
3. **`.` followed by a digit:** consume `.` and a digit run under the separator rules, then an exponent (step 4).
4. **Otherwise (a decimal):** consume `0`, or a nonzero digit followed by a digit run under the separator rules.
   - If `n` follows immediately, consume it (`bigint`).
   - Otherwise, if `.` follows, consume it and an optional digit run under the separator rules.
   - Then, if `e` or `E` follows, consume it, an optional `+` or `-`, and a non-empty digit run under the separator rules.
5. **After the literal,** the next character MUST NOT be an IdentifierStartChar, an ASCII digit or `\` (§12.9.3: "must not be an IdentifierStart or DecimalDigit").

Any violation is `malformed-literal` at the literal start: `3in`, `1__0`, `1.5n`, `07n`, `08n`, `0x`, `0b2`, `1.toString`, `1e+` and `0_1`. Legacy octal and NonOctalDecimal literals are lexically valid: they are part of the main ES2026 grammar, and rejecting them is a strict-mode early error, not a lexical one (D-4).

### 4.6 String literals (§12.9.4)

From `'` or `"`, scan in two passes.

**First, find the end.** A `\` consumes itself and the next character; CR LF after `\` counts as one character (a line continuation). An unescaped U+000A or U+000D, or the end of input (including right after a `\`), is `unterminated-literal` at the opening quote. LS and PS are allowed in strings.

**Then validate the escapes.** Each `\x` needs two hex digits, and each `\u` must be a valid escape (§3.2, any code point including surrogates). Any other escape is lexically valid, including `\8`, `\9`, `\0`, legacy octal `\012` and identity escapes such as `\q`. A violation is `malformed-literal` at the opening quote.

**Termination is decided first,** so `'\u{110000}` followed by a newline is `unterminated-literal` (vector `ts-err-unterminated-before-malformed`).

### 4.7 Template literals (§12.9.6)

From `` ` `` (or from a `}` that pops `${`), scan characters:
- `\` consumes itself and the next character, with CR LF counting as one.
- An unescaped `` ` `` ends the token. Opened by a backtick, it is `template`; opened by `}`, it is `template-tail`. `exprEnd` becomes true.
- `${` ends the token. Opened by a backtick, it is `template-head`; opened by `}`, it is `template-middle`. `${` is pushed and `exprEnd` becomes false.
- `$` not followed by `{` is ordinary content.
- Raw line terminators are allowed.

End of input inside a template token is `unterminated-literal` at that token's first byte: the backtick, or the `}` that continued it (vector `ts-err-unterminated-template`).

**Templates are never `malformed-literal`.** ES2026's NotEscapeSequence makes every escape lexically valid. An invalid escape in an *untagged* template is a syntax-level early error, which is out of scope (D-3).

**Nesting.** Braces inside a substitution push `{`, so only the `}` that matches `${` continues the template (vector `ts-template-nested`, with an object literal and a nested template).

### 4.8 Regular-expression literals (§12.9.5)

At a `/` that is not a comment and where `exprEnd` is false:
- Scan the body. `\` consumes itself and the next character, unless that character is a line terminator or the end of input.
- `[` opens a class, in which `/` does not terminate, until an unescaped `]`.
- An unescaped `/` outside a class ends the body.
- Then consume the flags: a maximal run of IdentifierPartChars.

A line terminator or the end of input before the closing `/` is `unterminated-literal` at the opening `/`. Neither the pattern grammar nor the flag set is checked (`/(/` and `/a/gg` are accepted): those are early errors, not lexical ones. TypeScript 6.0.3 also does not report them in its parser.

### 4.9 Regular expression or division: the `exprEnd` rule

ECMAScript chooses between InputElementDiv and InputElementRegExp from the syntactic context (§12). This profile replaces the parser with the `exprEnd` flag, which is maintained exactly as in §4.2. The full rule:

| Previous token | Next `/` is | Note |
| --- | --- | --- |
| (none) | regex | |
| `ident`, `privatename`, `number`, `bigint`, `string`, `template`, `template-tail`, `regex` | division | |
| keyword `this`, `super`, `null`, `true`, `false` | division | |
| any other keyword (`return`, `typeof`, `in`, `case`, `do`, `else`, `yield`, `await`, …) | regex | |
| `)` closing a header `(` (after `if`, `while`, `for`, `with`) | regex | `if (ok) /a+/.test(s)` |
| any other `)`, `]`, `}` | division | `(a + b) / 2` |
| `!`, `++`, `--` | unchanged from before them | postfix non-null `total! / n` stays division; prefix `!/re/` stays regex |
| `template-head`, `template-middle`, any other punctuator | regex | |
| end of a JSX element in normal mode | division | §5 |

**Known departures from ECMAScript** (TSOD-3). These are rare, and are recorded as cross-check probes:
- a regex right after the `}` of a block statement (`if (x) {}` newline `/re/`);
- a regex after the contextual `of` (`for (m of /x/g…)`);
- a regex after the `)` of `for await (…)`.

In each case the profile lexes division. TypeScript's own classifier makes the same `}` choice: its `noRegexTable` (in `typescript.js` 6.0.3) lists `CloseBraceToken`. In 2.48 million tokens of real code (§11) the rule never departed from the TypeScript parser.

### 4.10 Automatic semicolon insertion (§12.10)

**No tokens are inserted** (decided in draft, TSOD-5a). Unlike Go's rule, ECMAScript ASI is defined by the syntactic grammar ("offending token", restricted productions), so it cannot be computed lexically. Explicit `;` tokens are kept. `let a = 1⏎let b = a⏎(b)` stays a call (vector `ts-no-asi`).

The consequence: code written with and without semicolons ("semi" and "no-semi" styles) produces different streams, and the format pair invariant holds only within one style. TSOD-5b records the option of dropping `;` from both channels.

### 4.11 Hand check

`s = ` followed by `` `a${b + `c${d}e`}f${ {g: 1}.g }h` `` and `;` lexes to 18 tokens (vector `ts-template-nested`):

```
s = `a${ b + `c${ d }e` }f${ { g : 1 } . g }h` ;
```

The classes, in order: `ident punct template-head ident punct template-head ident template-tail template-middle punct ident punct number punct punct ident template-tail punct`. The object literal's `}` is `punct`, because `{` is on top of the stack, and the next `}` pops `${`. Exact-channel window selections are `[3, 3, 3, 3, 7, 8, 8, 8, 8, 11, 11]` and the fingerprints are at `[3, 7, 8, 11]`.

## 5. JSX (`tsx-tokens` only)

### 5.1 Trigger

In normal mode, a `<` with `exprEnd` false opens a JSX tag, unless §5.2 says it is a generic arrow. The scanner emits `punct` `<` and pushes `tag`.

A `<` with `exprEnd` true is the less-than or type-argument operator. That covers `a < b`, `f<T>(x)` and `useState<string>()` (vector `tsx-comparison-vs-jsx`).

### 5.2 Generic-arrow look-ahead

This mirrors TypeScript 6.0.3's `isParenthesizedArrowFunctionExpressionWorker`, JSX branch. After the `<`, skipping trivia:
1. Read an IdentifierName N1. If there is none, the `<` is JSX.
2. If N1 is `const` (unescaped), read a second IdentifierName; if there is none, the `<` is JSX. Otherwise, if N1 is one of the 38 ReservedWords (unescaped), the `<` is JSX.
3. Skip trivia and look at the next character c:
   - c is `,` → generic;
   - c is `=` not followed by `=` or `>` → generic;
   - the next word is an unescaped `extends`: skip trivia after it. Then a `=` not followed by `=` or `>`, a `>`, or a `/` not followed by `=` means JSX. Anything else, including the end of input, means generic;
   - anything else → JSX.

An unterminated comment during the look-ahead makes the `<` JSX, and tag mode then reports the comment. On a generic, the `<` is an ordinary punctuator and normal scanning continues. Vectors: `tsx-generic-arrow`, `tsx-generic-arrow-const` and `tsx-extends-attribute`.

### 5.3 Tag mode (stack top `tag`)

Trivia, including comments, is skipped as in normal mode. Then:
- **Name:** an IdentifierStartChar followed by IdentifierPartChars or `-` (JSXIdentifier) is `ident`. No `\u` escapes are allowed, and reserved words are `ident` here (`<label class=… for=…>`, vector `tsx-attr-keyword-names`).
- **`.`, `:` and `=`** are `punct`.
- **`"…"` or `'…'`** is `jsx-string`: no escapes, line terminators allowed, ending at the same quote. With no closing quote, the result is `unterminated-literal` at the opening quote.
- **`{`** is `punct`; push `jbrace` (normal mode, `exprEnd` false).
- **`<`**, only directly after an `=` token, opens an attribute-value element (push `tag`).
- **`/` as the first token after `<`** makes this a closing tag. The entry below `tag` MUST be `elem`; otherwise the result is `unbalanced-delimiter` at the tag's `<` (vector `tsx-err-stray-close`).
- **`/` later in an opening tag** marks it self-closing. The next non-trivia character MUST be `>`, otherwise `illegal-character` (vector `tsx-err-self-closing`).
- **`>`** is `punct`, and pops `tag`:
  - for a closing tag, it also pops the `elem` it closes;
  - for a self-closing tag, nothing more;
  - for an opening tag (including the fragment `<>`), it pushes `elem`.

  When this finishes an element and the new top is neither `tag` nor `elem`, `exprEnd` becomes true.
- **Anything else,** including `=`, `{`, a quote or `<` inside a closing tag, is `illegal-character`.

Tag names are not matched against each other (`<a></b>` is lexically fine; matching is syntax).

### 5.4 Children mode (stack top `elem`)

- `{` is `punct`; push `jbrace`.
- `<` is `punct`; push `tag`.
- `>` and `}` are `illegal-character` (JSXText excludes them; vectors `tsx-err-text-gt`, `tsx-err-brace-in-text`).
- Otherwise, the maximal run of characters up to `{`, `<`, `>`, `}` or end of input is JSX text. Leading and trailing white space and line terminators (§3.1) are trimmed and become trivia. If anything remains, one `jsx-text` token covers it, with inner white space kept. `//`, quotes and reserved words inside text are text (vector `tsx-text-comment-keywords`). Entities such as `&amp;` are text and are not decoded.

The end of input in children mode is `unbalanced-delimiter` at the element's `<`.

### 5.5 Known limitation (TSOD-8)

A generic signature written with a leading `<` in a position where an expression could also start is lexed as JSX. That covers `type F = <T>(x: T) => T`, `let f: <T>() => void` and call signatures `{ <T>(x: T): T }` in `.tsx`. Such an input usually ends in `illegal-character` at the `>` of `=>`, so the file is rejected rather than mis-fingerprinted (vector `tsx-err-generic-type-position`; TypeScript parses it). Telling these apart needs to know whether the position is a type or an expression, which is the parser's job. The size of this limitation on real `.tsx` code is unmeasured and belongs to TS.4.

## 6. Serializations

Contract §6 applies unchanged. In the `normalized` channel, the value is `""` for `ident` and for every literal class of this profile: `privatename`, `number`, `bigint`, `string`, the four template classes, `regex`, `jsx-text` and `jsx-string`. `keyword` and `punct` keep their text. Exact values are original bytes, so escapes are not decoded: `"A"` and `"\x41"` differ in `exact` and agree in `normalized`.

## 7. Errors

**Error codes** (closed list): `invalid-utf8`, `bom`, `nul`, `input-too-large`, `illegal-character`, `unterminated-comment`, `unterminated-literal`, `malformed-literal`, `malformed-identifier` and `unbalanced-delimiter`, plus `unsupported-config` (contract §10).

**Order.** Contract §3 order applies first. Lexical errors are found in scan order, and the first one is reported. Where one position could fail in more than one way, these rules decide:

| Situation | Result |
| --- | --- |
| String with both a bad escape and no terminator | `unterminated-literal` at the quote (§4.6) |
| Number followed by `\` or an IdentifierStartChar | `malformed-literal` at the literal start, never `illegal-character` or `malformed-identifier` |
| `\` at token start | `illegal-character` if `u` does not follow; `malformed-identifier` if the escape or its code point is invalid |
| `#` followed by `\` | private name: `malformed-identifier` at the `#` if the escape is invalid |
| End of input with `${` innermost | `unterminated-literal` at the template-head/middle start, not `unbalanced-delimiter` |
| End of input inside an unterminated block comment, template, string or JSX string | That token's error, not the stack check, which runs only after scanning succeeds |
| Wrong closer before end of input | `unbalanced-delimiter` at the closer (scan order) |
| `</` with no open element | `unbalanced-delimiter` at the `<` |
| Comment in the generic look-ahead is unterminated | JSX; the comment's `unterminated-comment` is reported by tag mode |

**Offsets** follow contract §2, OD-13: the first byte of the token, comment or literal being scanned. TypeScript usually reports later, at the failing character. 16 of 33 lexical error vectors share an offset with a TypeScript diagnostic, and 16 differ only in offset (§11).

## 8. What this profile does not cover

- Type checking, scope, module resolution and `tsconfig` settings (`jsx`, `target` and `module` do not change lexing here).
- The JSX pragma, embedded languages in tagged templates (`` css`…` ``, `` gql`…` ``) and source maps.
- The Annex B Script goal and other Script-only constructs (§4.3).

## 9. Deliberate divergences

| ID | Construct | ECMA-262 2026 | TypeScript 6.0.3 | This profile | Why |
| --- | --- | --- | --- | --- | --- |
| D-1 | `>>`, `>=`, … closing type arguments | longest match (no type syntax) | `>` single; parser re-scans | longest match | Lexical grammar without a parser; deterministic |
| D-2 | Escaped reserved word `if` | IdentifierName; not a keyword | `IfKeyword` with an escape flag | `ident` | §12.7.2 Note 1 |
| D-3 | Invalid escape in an untagged template | lexically valid (NotEscapeSequence); early error | diagnostic | accepted | Early error, not lexical |
| D-4 | Legacy octal `010`, `08.5`, `\01`, `\8` | lexically valid; strict-mode early error | diagnostic | accepted | Early error, not lexical |
| D-5 | Regex pattern and flags | early errors | checker diagnostic (not parser) | accepted | Early error, not lexical |
| D-6 | U+0085, U+200B | not white space | white space | `illegal-character` | Follows ECMA-262 |
| D-7 | Merge-conflict markers | punctuators | trivia plus diagnostic | punctuators | Follows ECMA-262 |
| D-8 | Identifier characters added after TypeScript's tables | ID_Start/ID_Continue of the Unicode version in use | invalid character | accepted (Unicode 17.0.0) | Contract §3a |
| D-9 | BOM, NUL | BOM is white space; NUL is allowed in literals | same | `bom`, `nul` | Shared contract OD-1 and §3 |
| D-10 | Regex after a block `}`, after `of`, after `for await (…)` | regex | regex (parser) | division | No parser (§4.9, TSOD-3) |
| D-11 | Generic function type or signature after `=`, `:` or `{` in `.tsx` | — | parsed | JSX, then an error | No parser (§5.5, TSOD-8) |
| D-12 | HTML-like comments | comments (Script goal only) | punctuators | punctuators | Module goal; matches TypeScript |
| D-13 | Error offsets | — | usually at the failing character | token start | Contract OD-13 |

## 10. Configuration

Contract §10 applies. The canonical bytes for `ts-tokens` are:

```
{"contract":"traceweave-token-winnow-draft-1","profile":"ts-tokens","profileVersion":"draft-1","channels":["exact","normalized"],"k":5,"window":4,"hash":"sha256-first8-u64be","maxInputBytes":1048576}
```

Digests: `ts-tokens` `69d1e98bc8e0d52c137f6203286a066437b136e9f38f021ca18920db7fb558fa`; `tsx-tokens` (same bytes with `"profile":"tsx-tokens"`) `6a7f8184ff2ab1d1eb5a75b5b87739acaf47b499fc7916e08c32da59c6f76ab5`; `ts-tokens` with `maxInputBytes` 16 `b4f9f6347726610ec242c970f1e53f26184ddced5a3bc928f66e65a44bf1373d`. [config-negative-typescript.json](extraction-vectors-typescript/config-negative-typescript.json) adds 14 rejections, among them `typescript-tokens`, `js-tokens`, `draft-2` and an escaped profile string. k = 5 and w = 4 are contract OD-10.

## 11. Requirement-to-check map and verification

| Requirement | Check |
| --- | --- |
| Config bytes and pairs (§10) | Checker validates three configs and rejects 14 negatives |
| Contract §3 order | `ts-err-invalid-utf8`, `-bom`, `-nul`, `ts-limit-*`; recomputed by the checker |
| Every token: class, text, byte span; every error: code and offset | Checker re-lexes each input with [tslex.py](extraction-vectors-typescript/tslex.py) and requires identity |
| Keyword list, property and JSX positions, escapes (§4.1, §5.3) | Checker invariants plus re-lex; `ts-contextual-keywords`, `ts-property-keywords`, `ts-unicode-escape-ident`, `tsx-attr-keyword-names`; corruptions: `return` as ident, `type`, `.catch`, `\u0069f` and JSX `class` as keyword |
| Longest match and `?.` (§4.4) | Checker invariant; `ts-shift-ops`, `ts-generics-gt`, `ts-optional-chaining`; corruptions: `>>` split in an expression and in generics, `?.5` as `?.` `5` |
| Numbers (§4.5) | `ts-numbers`, `ts-bigint`, `ts-legacy-octal`, 7 error vectors; corruption: `07.5` as one number |
| Strings, templates, regex (§4.6–§4.9) | Vectors tagged `strings`, `template`, `regex`, `division`; corruptions: regex as division, nested template merged, substitution closed at the wrong `}`, template-head relabelled, regex flags split |
| JSX (§5) | 16 accepted and 9 error vectors in `tsx.json`; corruptions: JSX text as identifiers, untrimmed JSX text |
| Hashbang, HTML-like comments, no ASI | `ts-hashbang`, `ts-html-comment`, `ts-no-asi`; corruptions: hashbang tokenized, `<!--` as a comment, an inserted `;` |
| Unicode (§3.1, §3.2) | `ts-unicode-boundary`, `ts-err-u2e2f`, `-u180e`; `derive_deltas.py` against UCD 17.0.0; crosscheck table sweep; corruption: U+309B rejected |
| Errors and precedence (§7) | 38 error vectors with exact offsets; corruptions: invented code, moved offset, malformed before unterminated |
| Hash, winnowing, ties, pairs | Checker recomputation; `ts-repeated` and others (23 tie windows), format and rename pairs; corruptions: leftmost tie, flipped hash bit |
| Toolchain agreement | [harness/crosscheck.js](extraction-vectors-typescript/harness/crosscheck.js): parser oracle, corpus, probes, table sweep |

**Results, 2026-11-22.** Python 3.14.6, Node 22.23.2, TypeScript 6.0.3.

- **Checker:** PASS for 89 vectors (61 `ts`, 25 `tsx`, 3 limits): 820 tokens, 38 errors, all with re-derived code and offset. The 14 negative configurations are rejected. **The mutation self-test rejects 25 of 25 corruptions, 23 of them lexical.** These include: a regex relabelled as division, a nested template merged, a substitution closed at the wrong `}`, JSX text tokenized as identifiers, untrimmed JSX text, `>>` split in an expression and in generics, a keyword or contextual word mis-classed, `?.5`, `07.5`, a tokenized hashbang, `<!--` as a comment, an inserted ASI `;`, split regex flags, U+309B rejected, an invented code, a moved offset, and malformed before unterminated.
- **Cross-check, vectors:** all 51 accepted vectors agree with TypeScript. 47 compare against the parser and 4 against the raw scanner, because TypeScript reports syntax (not lexical) diagnostics for them: `ts-html-comment`, `ts-legacy-octal`, `ts-unicode-escape-ident` and `ts-strings`. Two `gt-merge` adjustments were needed.
  - Of the 33 lexical error vectors, 32 are rejected by TypeScript too: 16 at the same offset and 16 at another offset. The remaining one is `tsx-err-generic-type-position` (D-11).
  - 5 pre-lexing vectors are not compared. TypeScript accepts the BOM and NUL inputs (D-9).
- **Cross-check, corpus:** every `lib/*.d.ts` file (as `ts-tokens`) and `lib/*.js` file (as `tsx-tokens`) in the pinned package: 119 files, 19.8 MB, 2,478,321 tokens. **All 119 agree**, with 71 `gt-merge` adjustments. This corpus is compiler-emitted or declaration code with no JSX. It does not represent hand-written `.tsx`.
- **Cross-check, probes:** 39 inputs. 25 agree as expected and 14 diverge exactly as §9 documents (D-3, D-4, D-6 to D-11). There are 0 unexpected outcomes.
- **Unicode sweep** over every scalar value: identifier start differs on 8,949 code points and identifier part on 9,132, all accepted by the profile and rejected by TypeScript's older tables (D-8). White space differs on 2 (D-6), and line terminators on 0.

**Limits.** The checker's lexer and the hand-written streams come from the same author and the same reading of this text. Agreement between them shows consistency, not independence; TS.3 needs two implementers. The cross-check covers only the shipped inputs, the probes and a corpus without JSX.

## 12. Decisions

**Decided in draft, pending owner confirmation** (each changes tokens, hashes or accept/reject, and the vectors encode it):

| ID | Decision | Reason |
| --- | --- | --- |
| TSOD-1 | (a) Two profiles, `ts-tokens` and `tsx-tokens`; `.js`, `.mjs`, `.cjs` and `.jsx` map to `tsx-tokens` | JSX is the only lexical fork (§2) |
| TSOD-2 | (a) `keyword` is the 46 ECMAScript reserved and strict-reserved words; TypeScript-only and contextual words are `ident` | Rename robustness, like Go OD-7; a textual rule that needs no parser |
| TSOD-3 | (a) The `exprEnd` rule of §4.9, with header `)` and `!`/`++`/`--` passing the state through | Deterministic, and agrees with TypeScript on every vector and the whole corpus; departures listed |
| TSOD-4 | (a) `>`-family longest match everywhere | ECMA-262 lexical grammar; TypeScript is adjusted in the cross-check |
| TSOD-5a | (a) No ASI tokens; explicit `;` kept | ASI is syntactic |
| TSOD-6 | (a) HTML-like comments and conflict markers are not trivia | Module goal; deterministic |
| TSOD-7 | (a) The exclusions in §2 (`.d.ts` family, `@generated`/`DO NOT EDIT` in the first 2048 bytes, `.min.*` or a line over 4096 bytes) | TS.1 needs a decidable rule. The thresholds are unmeasured |
| TSOD-9 | (a) `jsx-text` trimmed; white-space-only text dropped | Layout invariance (`tsx-format-a/b`) |
| TSOD-10 | (a) ID_Start/ID_Continue from the pinned UCD (§3.2), not XID; no NFC | ECMA-262 2026 |

**Must be settled before implementation:**

- **TSOD-5b `;` in the normalized channel.**
  - (a) Keep `;` (current).
  - (b) Drop every `;` token from both channels, so semi and no-semi styles match. Cost: `for (;;)` loses its structure tokens, and Go-style layout invariance would hold here and nowhere else.
  - (c) Drop `;` from `normalized` only.

  This changes hashes, so it must be decided before vectors are frozen.
- **TSOD-8 TSX generic signatures.**
  - (a) Accept the limitation and reject those inputs (current).
  - (b) Add one more look-ahead: after `:`, `=` (in a `type` alias) or `{`, treat `<` IdentifierName `>` `(` as generic. This leaves new ambiguities (`cond ? x : <T>(…)</T>`).
  - (c) Specify a minimal type/expression context tracker.

  Option (b) or (c) needs TS.4 corpus numbers first. If the limitation rejects more than a small share of real `.tsx` files, ship `ts-tokens` alone first.
- **TSOD-2b contextual words as a class.**
  - (a) `ident` (current).
  - (b) A separate `ctxword` class that keeps its text in `normalized` for a fixed list (`type`, `declare`, `namespace`, `abstract`, `readonly`, `as`, `satisfies`, `keyof`, `infer`, `is`, `async`, `of`, `get`, `set`, `accessor`, `override`, `using`). This preserves more TypeScript structure, but a variable named `type` then keeps its name.
- **TSOD-11 Ecma PDF pin.** Replace or supplement the tc39.es HTML digest with the formal Ecma publication.
- **TSOD-12 TypeScript 7.** Decide whether the oracle must be re-run on the native compiler before promotion, and how, since 7.0.2 ships no scanner API.

**Can wait:** TSOD-7 threshold tuning (TS.4 corpus); k and w for this profile (TW-05, contract OD-10).

## 13. How hard is agreement, compared with Go and Rust

**Harder, by a clear margin.**
- The Go and Rust profiles are context-free at the token level except for Go's semicolons, which are a one-flag rule.
- This profile needs three pieces of context: the `exprEnd` flag, a stack that carries template and JSX modes, and a look-ahead for TSX generics.
- Every one of these is a place where two careful implementers can read the same sentence differently. Examples: what "previous token" means after `!`, which `}` continues a template, where JSX text is trimmed, and what happens to an unterminated comment inside the look-ahead.

The M1.4 cross-check spent 9.88 million cases to find a single Rust divergence (shebang look-ahead over doc comments). That was a much smaller state space.

**In this profile's favour:**
- There is no NFC.
- Error classes are few, and offsets are token starts.
- The regex rule is a 12-row table, not a grammar.
- On 2.48 million real tokens the rule never disagreed with TypeScript's parser.

The risk is concentrated in JSX, where the profile admits a known gap (TSOD-8) and has no corpus evidence.

**Recommendation: stage it.**
1. **Stage 1:** register `ts-tokens` only (`.ts`, `.mts`, `.cts`, and JavaScript files without JSX). Run TS.3 and TS.4 on it.
2. **Stage 2:** add `tsx-tokens` after a `.tsx`/`.jsx` corpus measures how many files the TSOD-8 limitation rejects, and after TSOD-8 is settled.

The vectors are already split by profile, so stage 1 can freeze `ts.json` and `limits-ts.json` without touching `tsx.json`. Before TS.3, extend the M1.4-style differential: random token streams with mutations, and the `exprEnd`, template and JSX state spaces in particular.

## 14. "Before registering a profile" checklist ([profiles/code.md](../../profiles/code.md))

| Item | Where |
| --- | --- |
| Language and grammar revision | §1: ECMA-262 2026 (digest), TypeScript 6.0.3 (oracle), Unicode 17.0.0 |
| Tokenizer rules | §3–§5 |
| Scope resolution | None: the normalized channel is lexical and not scope-aware (contract §12) |
| Encodings | Contract §3: UTF-8 only, no BOM, no NUL; lone CR is legal (§3.1) |
| Parser error behavior | No parser. Lexical errors are listed in §7. Syntactically invalid but lexically valid input is fingerprinted |
| Comments and docstrings | §4.3: dropped, JSDoc included; JSX `//` text is text (§5.4) |
| Significant whitespace | Only in JSX text trimming (§5.4) and line terminators ending comments and strings; no ASI (§4.10) |
| Macros and generated code | No macros. Generated, minified and declaration files are excluded (§2, TSOD-7) |
| Token serialization | §6, contract §6 |
| Hash parameters, window sizes, tie-breaking | Contract §7–§8 and OD-10 (k = 5, w = 4, rightmost minimum) |
| Coordinate units | UTF-8 byte offsets, half-open (contract §3). The cross-check converts TypeScript's UTF-16 offsets |
