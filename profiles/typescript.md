# Draft extraction profile: TypeScript and JavaScript (`ts-tokens`, `tsx-tokens`)

Status: experimental draft, normative for conformance of this draft version; decided-in-draft items confirmed by the owner's delegation on 2026-11-23.

Profiles in this document: **`ts-tokens` is frozen for implementation** (draft-2). **`tsx-tokens` is a deferred draft and is not normative**: no implementation is expected to support it until it is reviewed and frozen.

Revision status: **draft for review, revision draft-2, 2026-11-22.** Roadmap items TS.1 and TS.2. TS.3 (two implementations) and TS.4 (own M3 split) are implementation gates and are not claimed here. Draft-2 resolves the [clean-room review](../reviews/extraction-profile-typescript-review.md) of draft-1 (F1–F6, A1–A6). The dispositions are in §15 and the output changes in §16.

**`ts-tokens` `draft-2` is frozen for stage-1 implementation, pending owner confirmation of the decided-in-draft items** (§17 lists the frozen files and digests).

**Staging** (decided in draft, pending owner confirmation, TSOD-1): **`ts-tokens` is stage 1** and is the frozen profile. It also takes plain `.js`, `.mjs` and `.cjs`. **`tsx-tokens` is deferred.** §5 and its vectors are kept as a draft, but they are not frozen until a real `.tsx`/`.jsx` corpus measures TSOD-8.

This is research material, not a normative change. It does not modify `spec/`, `schemas/`, `profiles/`, `test-vectors/` or the [extraction contract](extraction-contract.md). "MUST" describes what this draft proposes for an implementation claiming to follow it. Nothing here is a registered algorithm.

**How it plugs in.** This document adds two profile sections in the shape of contract §4 (Go) and §5 (Rust). Every shared part of the contract applies unchanged. The profile also uses the contract's normalized-stream exclusion rule (contract §6, OD-23) to drop `;` from the normalized stream (§6 below, TSOD-5b). The shared parts are:
- §2 outcomes, the no-repair rule and the error-offset rules;
- §3 processing order: configuration, size, UTF-8, then U+FEFF (`bom`) and U+0000 (`nul`). This profile adds no forbidden code point, so a lone CR is legal;
- §3a Unicode 17.0.0 data, plus two small deltas derived from the same digest-pinned file (§3.2);
- §6 serializations, with `normalizedExclusions` declared in §6 below; §7 k-gram hashing, §8 winnowing and §9 record fields;
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

| Input | Profile | Stage | Reason |
| --- | --- | --- | --- |
| `.ts`, `.mts`, `.cts` | `ts-tokens` | 1 | No JSX: `<` at expression start is a type assertion or a generic |
| `.js`, `.mjs`, `.cjs` | `ts-tokens` | 1 | Valid JavaScript without JSX lexes identically under both profiles, because `<` at expression start is not valid JavaScript outside JSX (vectors `ts-plain-js` and `tsx-plain-js`). JSX in such a file usually becomes an explicit error (`ts-err-jsx-in-js`) |
| `.tsx`, `.jsx` | `tsx-tokens` | deferred | JSX recognized (§5) |

**JSX in a `.js` file under `ts-tokens` is not always rejected.** Any element with a closing tag or with text makes `</` start a regular expression that runs to the end of the line. That gives `unterminated-literal` unless the line happens to contain another `/` (`ts-err-jsx-in-js`). A text-free self-closing element such as `x = <br/>;` lexes as the punctuators `< br / > ;` and is fingerprinted (`ts-jsx-selfclosing-in-js`, D-16). **`.js` files containing JSX are deferred to stage 2** (decided in draft, pending owner confirmation). The selecting tool (TW-01/TW-03) MUST record each such file as **deferred to stage 2**, whether it detects the JSX before extraction or meets it as an extraction error. It MUST NOT drop such files silently, and MUST NOT count them as ordinary lexical rejections. Text-free self-closing elements are a **known stage-1 misread (D-16)**: they are fingerprinted as punctuators and cannot be told apart lexically from comparison and type syntax. A repository with JSX in `.js` should map those files to `tsx-tokens` once stage 2 exists.

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
10. **`(`, `[`, `{`:** `punct`, pushed onto the stack, `exprEnd` false. A `(` whose previous token is the `keyword` `if`, `while`, `for` or `with` is marked as a **header**. A `{` whose previous token is `punct` `=>` is marked as an **arrow body**.
11. **`)`, `]`, `}`:**
    - `}` with `${` on top pops it and continues a template (§4.7).
    - `}` with `jbrace` on top pops it and emits `punct` `}` (§5).
    - Otherwise the closer must match the top (`(`, `[` or `{`); if it does not, or the stack is empty, the result is `unbalanced-delimiter` at the closer.
    - After a matching closer, `exprEnd` is true, except after a `)` that closes a header or a `}` that closes an arrow body, where it is false.
12. **Punctuator:** the longest match from §4.4, class `punct`.
    - After `!`, `++` or `--`, `exprEnd` is false if a line terminator lies between the previous token and this one. This includes a line terminator inside a block comment, and does not count the hashbang. Otherwise `exprEnd` is unchanged (§4.9).
    - After any other punctuator, `exprEnd` is false.
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
   - Otherwise it is a NonOctalDecimalIntegerLiteral. Its integer part takes no separators, and it takes no `n`. It may take a fraction and an exponent as in step 4, **with** separators there: ES2026 uses DecimalDigits[+Sep] and ExponentPart[+Sep] after any DecimalIntegerLiteral. So `08.1_1e1_0` is one number (vector `ts-nonoctal-separators`).
3. **`.` followed by a digit:** consume `.` and a digit run under the separator rules, then an exponent (step 4).
4. **Otherwise (a decimal):** consume `0`, or a nonzero digit followed by a digit run under the separator rules.
   - If `n` follows immediately, consume it (`bigint`).
   - Otherwise, if `.` follows, consume it and an optional digit run under the separator rules.
   - Then, if `e` or `E` follows, consume it, an optional `+` or `-`, and a non-empty digit run under the separator rules.
5. **After the literal,** the next character MUST NOT be an IdentifierStartChar, an ASCII digit or `\` (§12.9.3: "must not be an IdentifierStart or DecimalDigit").

Any violation is `malformed-literal` at the literal start: `3in`, `1__0`, `1.5n`, `07n`, `08n`, `0x`, `0b2`, `1.toString`, `1e+` and `0_1` (a `0` alone is followed by `_`, an IdentifierStartChar; vector `ts-err-zero-separator`). Legacy octal and NonOctalDecimal literals are lexically valid: they are part of the main ES2026 grammar, and rejecting them is a strict-mode early error, not a lexical one (D-4).

### 4.6 String literals (§12.9.4)

From `'` or `"`, scan in two passes.

**First, find the end.** A `\` consumes itself and the next character; CR LF after `\` counts as one character (a line continuation). An unescaped U+000A or U+000D, or the end of input (including right after a `\`), is `unterminated-literal` at the opening quote. LS and PS are allowed in strings.

**Then validate the escapes.** Each `\x` needs two hex digits, and each `\u` must be a valid escape (§3.2, any code point including surrogates). Any other escape is lexically valid, including `\8`, `\9`, `\0`, legacy octal `\012` and identity escapes such as `\q`. A violation is `malformed-literal` at the opening quote.

**Termination is decided first,** so `'\u{110000}` followed by a newline is `unterminated-literal` (vector `ts-err-unterminated-before-malformed`). A lone CR ends nothing either: `'a⏎b'` with CR is `unterminated-literal` (vector `ts-err-cr-in-string`).

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

ECMAScript chooses between InputElementDiv and InputElementRegExp from the syntactic context (§12). This profile replaces the parser with the `exprEnd` flag, which is maintained exactly as in §4.2 (TSOD-3, decided in draft). The full rule:

| Previous token | Next `/` is | Vectors |
| --- | --- | --- |
| (none) | regex | |
| `ident`, `privatename`, `number`, `bigint`, `string`, `template`, `template-tail`, `regex` | division | `ts-division-after-paren` |
| keyword `this`, `super`, `null`, `true`, `false` | division | |
| any other keyword (`return`, `typeof`, `in`, `case`, `do`, `else`, `throw`, `yield`, `await`, …) | regex | `ts-regex-after-keyword`, `ts-yield-await-regex` |
| `)` closing a header `(` (after `if`, `while`, `for`, `with`) | regex | `ts-regex-after-header` |
| `}` closing an arrow body (`{` right after `=>`) | regex | `ts-arrow-body-regex` |
| any other `)`, `]`, `}` | division | `ts-object-class-division` |
| `!`, `++`, `--` with a line terminator before it | regex | `ts-newline-prefix-regex` |
| `!`, `++`, `--` without one | unchanged from before it | `ts-nonnull-division`, `ts-postfix-division` |
| `template-head`, `template-middle`, any other punctuator | regex | |
| end of a JSX element in normal mode (`tsx-tokens`) | division | `tsx-element-division` |

**Why these rows match ECMAScript without a parser.**
- **Arrow body `}`.** An ArrowFunction is an AssignmentExpression, so it cannot be the left operand of `/`. A `/` after an arrow body's `}` is therefore never division.
- **`!`, `++` and `--` after a line terminator.** Postfix `++` and `--` are restricted productions with "[no LineTerminator here]". TypeScript's non-null `!` likewise requires no preceding line break. After a line break the operator can only be prefix, and the line break is an ASI point (`a⏎++/re/.lastIndex` is `a; ++/re/.lastIndex`).

**Known departures from ECMAScript** (D-10, D-15). These are the complete list of classes found by the review's 536 context runs and this revision's probes. Each is pinned by a vector or a probe:

| Input class | ECMAScript / TypeScript | Profile | Pinned by |
| --- | --- | --- | --- |
| Regex after the `}` of a block statement (`if (x) {}⏎/re/`, `{}⏎/re/`) | regex | division | probe |
| Regex after the `}` of a **function declaration** | regex | division | `ts-function-decl-division` |
| Regex after the `}` of a **class declaration** | regex | division | `ts-class-decl-division` |
| Regex after contextual `of` (`for (m of /x/g…)`) | regex | division | probe |
| Regex after the `)` of `for await (…)` | regex | division | probe |
| **`await` or `yield` used as an identifier** (script code, non-async, non-generator: `x = await / 2`) | division | regex, usually `unterminated-literal` | `ts-err-await-identifier` |
| `@dec /re/` (a syntax error either way) | regex | division | — |

A parser-free rule that tells a statement-level `}` (block, function or class declaration) from an expression-level one (object literal, function or class expression) has to infer statement position. It would need ASI after expression ends, the `function`/`class` name rule, and return-type and type-parameter object literals. That is a second, larger state machine, and the review counts every such rule as a new place for two implementers to diverge. A regex statement right after a declaration (`/re/.test(s);` as a statement) has no effect unless the regex has side effects, so the departure is kept and documented. `await` and `yield` stay keywords because TypeScript code is module or async code, where `await /re/` and `yield /re/` are the real uses.

**Evidence and its limits.** The 2.48 million corpus tokens (§11) produced no departure. That corpus is compiler-emitted JavaScript and declaration files: it has no JSX and few regex statements. The claim therefore says nothing about hand-written or `.tsx` code. The review's 536 targeted runs found only the classes above. TypeScript's own classifier makes the same `}` choice: its `noRegexTable` (in `typescript.js` 6.0.3) lists `CloseBraceToken`.

### 4.10 Automatic semicolon insertion and `;` (§12.10)

**No tokens are inserted** (decided in draft, TSOD-5a). Unlike Go's rule, ECMAScript ASI is defined by the syntactic grammar ("offending token", restricted productions), so it cannot be computed lexically. `let a = 1⏎let b = a⏎(b)` stays a call (vector `ts-no-asi`).

**`;` is kept in the exact stream and dropped from the normalized stream** (decided in draft, pending owner confirmation, TSOD-5b option (c); §6). Without this, a Prettier `semi: false` reformat defeats the channel meant to survive surface edits.

Measurements, with each `;` that is followed by spaces or tabs and then a line terminator deleted:
- **The review:** 61.1% of normalized fingerprints survive on 42,043 tokens of TypeScript 6.0.3's `lib/_tsc.js` when `;` stays, and 100% when it is dropped.
- **This revision**, using [harness/semi_survival.py](extraction-vectors-typescript/harness/semi_survival.py) and counting distinct fingerprint hashes:
  - the same 42,043-token prefix: 62.5% (1,769/2,831) under draft-1 and 100% (3,077/3,077) under draft-2;
  - the whole file (874,387 tokens, 49,866 `;` removed): 67.3% and 100%.

The two measurements count slightly differently, and both show the same gap. Vectors `ts-semi-a` and `ts-semi-b` (with and without semicolons) have different exact hashes and identical normalized hashes, and the checker enforces that as a pair invariant. The cost is that `for (;;)` loses its separators in `normalized`.

### 4.11 Hand check

`s = ` followed by `` `a${b + `c${d}e`}f${ {g: 1}.g }h` `` and `;` lexes to 18 tokens (vector `ts-template-nested`):

```
s = `a${ b + `c${ d }e` }f${ { g : 1 } . g }h` ;
```

The classes, in order: `ident punct template-head ident punct template-head ident template-tail template-middle punct ident punct number punct punct ident template-tail punct`. The object literal's `}` is `punct`, because `{` is on top of the stack, and the next `}` pops `${`. Under draft-2, exact-channel window selections are `[3, 3, 3, 6, 6, 6, 6, 8, 8, 12, 12]` and the fingerprints are at `[3, 6, 8, 12]`. The normalized stream drops the final `;`: 17 tokens, 13 k-grams, selections `[2, 2, 2, 3, 4, 8, 8, 8, 8, 11]`.

## 5. JSX (`tsx-tokens` only; deferred)

This section is a draft for stage 2 (TSOD-1). It is complete enough for the vectors in `tsx.json` and the checker, but it is not frozen. The TSOD-8 limitation (§5.5) must be measured on a real `.tsx`/`.jsx` corpus first.

### 5.1 Trigger

In normal mode, a `<` with `exprEnd` false opens a JSX tag, unless §5.2 says it is a generic arrow. The scanner emits `punct` `<` and pushes `tag`.

A `<` with `exprEnd` true is the less-than or type-argument operator. That covers `a < b`, `f<T>(x)` and `useState<string>()` (vector `tsx-comparison-vs-jsx`).

### 5.2 Generic-arrow look-ahead

This mirrors TypeScript 6.0.3's `isParenthesizedArrowFunctionExpressionWorker`, JSX branch. A **name** here is an IdentifierName written without any `\u` escape. Starting after the `<`:

1. Skip trivia. Read a name N1. If there is none (including a `\` or an escape inside the name), the `<` is JSX.
2. If N1 is `const`, skip trivia and read a second name. If there is none, the `<` is JSX. The second name is **not** checked against reserved words (vector `tsx-generic-const-reserved`), as in TypeScript, which skips that token unchecked. Otherwise, if N1 is one of the 38 ReservedWords, the `<` is JSX.
3. Skip trivia and look at the next character c:
   - c is `,` → generic;
   - c is `=` not followed by `=` or `>` → generic;
   - a name that is exactly `extends` starts at c (whole word, so `extendsX` does not count, vector `tsx-extends-word`): skip trivia after it. Then a `=` not followed by `=` or `>`, a `>`, or a `/` not followed by `=` means JSX. Any other character, including the end of input, means generic;
   - anything else → JSX.

**An unterminated comment anywhere in the look-ahead makes the `<` JSX.** That includes one after `extends`, and this rule takes precedence over "any other character … means generic". The choice is not observable: in either mode the same comment is scanned next and fails with `unterminated-comment` at the same offset (vector `tsx-err-extends-comment`). The checker ships the opposite reading as a lexer variant and confirms it gives identical results.

On a generic, the `<` is an ordinary punctuator and normal scanning continues. Vectors: `tsx-generic-arrow`, `tsx-generic-arrow-const`, `tsx-extends-attribute` and `tsx-err-lookahead-escape`. TypeScript decodes escapes, so `<\u0054,>` is a generic arrow there and JSX here (D-14).

### 5.3 Tag mode (stack top `tag`)

Trivia, including comments, is skipped as in normal mode. Every token emitted in tag mode is `punct` (`<`, `/`, `>`, `.`, `:`, `=`, `{`), `ident` (names) or `jsx-string`. Then:
- **Name:** an IdentifierStartChar followed by IdentifierPartChars or `-` (JSXIdentifier) is `ident`. No `\u` escapes are allowed, and reserved words are `ident` here (`<label class=… for=…>`, vector `tsx-attr-keyword-names`).
- **`.`, `:` and `=`** are `punct`.
- **`"…"` or `'…'`** is `jsx-string`: no escapes, line terminators allowed, ending at the same quote. With no closing quote, the result is `unterminated-literal` at the opening quote.
- **`{`** is `punct`; push `jbrace` (normal mode, `exprEnd` false).
- **`<`**, only when the previous token is `=`, opens an attribute-value element (push `tag`). Trivia may come between them (vector `tsx-attr-element-space`). Anywhere else in a tag, `<` is `illegal-character` (vector `tsx-err-attr-lt`).
- **`/` as the first token after `<`** makes this a closing tag. The entry below `tag` MUST be `elem`; otherwise the result is `unbalanced-delimiter` at the tag's `<` (vector `tsx-err-stray-close`).
- **`/` later in an opening tag** marks it self-closing. The next non-trivia character MUST be `>`, otherwise `illegal-character` at that character (vector `tsx-err-self-closing`).
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
- A `}` that pops `jbrace` (in normal mode, §4.2 step 11) leaves `exprEnd` unchanged. The flag is not consulted in tag or children mode, and it is set again before normal mode next reads a `/` or `<`: false on every `jbrace` push, true when an element ends in normal mode.
- `>` and `}` are `illegal-character` (JSXText excludes them; vectors `tsx-err-text-gt`, `tsx-err-brace-in-text`).
- Otherwise, the maximal run of characters up to `{`, `<`, `>`, `}` or end of input is JSX text. Leading and trailing white space and line terminators (§3.1, the full set including U+00A0 and the other Zs; vector `tsx-nbsp-text`) are trimmed and become trivia. If anything remains, one `jsx-text` token covers it, with inner white space kept. `//`, quotes and reserved words inside text are text (vector `tsx-text-comment-keywords`). Entities such as `&amp;` are text and are not decoded.

The end of input in children mode is `unbalanced-delimiter` at the element's `<`.

### 5.5 Known limitation (TSOD-8)

A generic signature or generic function type written with a leading `<` in a position where an expression could also start is lexed as JSX. In `.tsx` (D-11), these include:
- `type F = <T>(x: T) => T` (after `=`);
- `let f: <T>() => void` (after `:`);
- call signatures `{ <T>(x: T): T }` (after `{` or `;`);
- **construct signatures `new <T>(x: T): T`** (after keyword `new`);
- function types after `(`, `|`, `&`, `,` or `<` in type positions, such as `A | (<T>() => T)` and `f<(<T>(x: T) => T)>(g)`.

Such an input usually ends in `illegal-character` at the `>` of `=>`, or in `unbalanced-delimiter`, so the file is rejected rather than mis-fingerprinted (vector `tsx-err-generic-type-position`; probes for the construct-signature and `(` cases). Telling these apart needs to know whether the position is a type or an expression, which is the parser's job.

**Frequency is unmeasured on real `.tsx` code.** The review found no `.tsx`/`.jsx` sources available offline. As a proxy only, 7 of TypeScript's 110 `lib/*.d.ts` files (6.4%) are rejected when lexed as `tsx-tokens`, partly because of construct signatures. Declaration files are excluded in practice, so the proxy only shows that the pattern is common in type-heavy code. This measurement is the condition for freezing `tsx-tokens`.

## 6. Serializations

Contract §6 applies, with one change.

**Declared normalized-stream exclusions** (contract §6, OD-23):

```
normalizedExclusions: [ {class: "punct", text: ";"} ]
```

This holds for both `ts-tokens` and `tsx-tokens` `draft-2` (TSOD-5b (c), §4.10). The contract's rule then applies unchanged:
- Every `;` stays in the token list, `tokenCount`, the exact channel and the status decision.
- Normalized k-gram positions, window selections and fingerprint positions index the filtered stream. Spans are the byte spans of the first and last kept tokens.
- The normalized channel records `tokenIndices` (ascending indices of the kept tokens) before `values`.
- An `ok` input can have an empty normalized channel. For example, `ts-exact-k` (`let a = b;`) has one exact k-gram and none in `normalized`.

The vector files repeat the declaration as `normalizedExclusions`, and the checker requires it to equal this one.

**Normalized values.** The value is `""` for `ident` and for every literal class of this profile: `privatename`, `number`, `bigint`, `string`, the four template classes, `regex`, `jsx-text` and `jsx-string`. `keyword` and `punct` keep their text. Exact values are original bytes, so escapes are not decoded: `"A"` and `"\x41"` differ in `exact` and agree in `normalized`.

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

**Offsets** follow contract §2, OD-13: the first byte of the token, comment or literal being scanned. TypeScript usually reports later, at the failing character. Of the 40 lexical error vectors, 17 share an offset with a TypeScript diagnostic, 20 are rejected by TypeScript at another offset, and 3 are documented divergences that TypeScript accepts (§11).

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
| D-10 | Regex after the `}` of a block statement, function declaration or class declaration; after `of`; after `for await (…)` | regex | regex (parser) | division | No parser (§4.9, TSOD-3) |
| D-11 | Generic function type, call signature or construct signature (`new <T>(…)`) with a leading `<` in a type position in `.tsx`: after `=`, `:`, `{`, `;`, `new`, `(`, `\|`, `&`, `,` or `<` | — | parsed | JSX, then an error | No parser (§5.5, TSOD-8) |
| D-12 | HTML-like comments | comments (Script goal only) | punctuators | punctuators | Module goal; matches TypeScript |
| D-13 | Error offsets | — | usually at the failing character | token start | Contract OD-13 |
| D-14 | Escaped name in the `.tsx` generic look-ahead (`<\u0054,>`) | — | escape decoded; generic | JSX (then `illegal-character` at `\`) | Escape-free names keep the look-ahead textual (§5.2) |
| D-15 | `await`/`yield` as identifiers in script code (`x = await / 2`) | division | division | regex | TypeScript code is module or async code (§4.9) |
| D-16 | Text-free self-closing JSX in a `.js` file under `ts-tokens` (`<br/>`) | — | JSX element (`.js` is JSX-capable) | punctuators, accepted | Stage 1 routes `.js` to `ts-tokens` (§2) |

## 10. Configuration

Contract §10 applies, including the draft-2 bounds of contract §10a (k ≤ 16, window ≤ 128, maxInputBytes ≤ 8 MiB). The canonical bytes for `ts-tokens` are:

```
{"contract":"traceweave-token-winnow-draft-1","profile":"ts-tokens","profileVersion":"draft-2","channels":["exact","normalized"],"k":5,"window":4,"hash":"sha256-first8-u64be","maxInputBytes":1048576}
```

**Digests:**
- `ts-tokens`: `aeeed14177cd3be8fea69e453c825e74f2fd301d03babbf49329bde0cc4754de`;
- `tsx-tokens` (the same bytes with `"profile":"tsx-tokens"`): `4f121891d73b98b51032e4f3bcb823a215b3edc6afaee6493ea9025a2a8564e6`;
- `ts-tokens` with `maxInputBytes` 16: `94403dd3e71a8105a9dcec894fc0d05d09cb771efaada28802dcf43ecd08f8d6`.

`draft-1` is no longer accepted. [config-negative-typescript.json](extraction-vectors-typescript/config-negative-typescript.json) lists 19 rejections, among them both superseded `draft-1` pairs, `typescript-tokens`, `js-tokens`, one value just above each contract bound, and an escaped profile string. k = 5 and w = 4 are contract OD-10.

## 11. Requirement-to-check map and verification

| Requirement | Check |
| --- | --- |
| Config bytes, pairs and bounds (§10) | Checker validates three configs and rejects 19 negatives |
| Contract §3 order | `ts-err-invalid-utf8`, `-bom`, `-nul`, `ts-limit-*`; recomputed by the checker |
| Every token: class, text, byte span; every error: code and offset | Checker re-lexes each input with [tslex.py](extraction-vectors-typescript/tslex.py) and requires identity |
| Keyword list, property and JSX positions, escapes (§4.1, §5.3) | Checker invariants plus re-lex; `ts-contextual-keywords`, `ts-property-keywords`, `ts-unicode-escape-ident`, `tsx-attr-keyword-names`; corruptions: `return` as ident, `type`, `.catch`, `\u0069f` and JSX `class` as keyword |
| Longest match and `?.` (§4.4) | Checker invariant; `ts-shift-ops`, `ts-generics-gt`, `ts-optional-chaining`; corruptions: `>>` split in an expression and in generics, `?.5` as `?.` `5` |
| Numbers (§4.5) | `ts-numbers`, `ts-bigint`, `ts-legacy-octal`, `ts-nonoctal-separators`, 7 error vectors; corruption `07.5` as one number; wrong lexers V26, WNonOctalSep |
| Strings, templates, regex (§4.6–§4.8) | Vectors tagged `strings`, `template`, `regex`; corruptions: nested template merged, substitution closed at the wrong `}`, template-head relabelled, regex flags split; wrong lexer V13 |
| `exprEnd` (§4.9), every row and every departure | The vectors named in the §4.9 tables; corruptions: regex as division (twice); wrong lexers V1, V5, V25, V22, WNewline, WArrow, WHeader, WBang |
| `;` excluded from normalized (§6, contract OD-23) | Checker: declared `normalizedExclusions` equals the profile's; `tokenIndices` against it, placed before `values`; `ts-semi-a/b` pair invariant, `ts-exact-k`; corruptions: normalized keeps `;`, `tokenIndices` omitted |
| JSX (§5, deferred) | 21 accepted and 12 error vectors in `tsx.json`; corruptions: JSX text as identifiers, untrimmed JSX text; wrong lexers V11, V21, V22, WEscape |
| Hashbang, HTML-like comments, no ASI | `ts-hashbang`, `ts-html-comment`, `ts-no-asi`; corruptions: hashbang tokenized, `<!--` as a comment, an inserted `;` |
| Unicode (§3.1, §3.2) | `ts-unicode-boundary`, `ts-err-u2e2f`, `-u180e`, `tsx-nbsp-text`; `derive_deltas.py` against UCD 17.0.0; crosscheck table sweep; corruption: U+309B rejected |
| Errors and precedence (§7) | 45 error vectors with exact offsets; corruptions: invented code, moved offset, malformed before unterminated |
| Hash, winnowing, ties, pairs | Checker recomputation; 22 tie windows; format, rename and semi pairs; corruptions: leftmost tie, flipped hash bit |
| Toolchain agreement | [harness/crosscheck.js](extraction-vectors-typescript/harness/crosscheck.js): parser oracle, corpus, probes, table sweep |

**Results, draft-2, 2026-11-22** (Python 3.14.6, Node 22.23.2, TypeScript 6.0.3).

- **Checker:** PASS for 113 vectors: 77 `ts`, 33 `tsx` and 3 limits. That is 1,077 tokens and 45 errors, all with re-derived code and offset. The 19 negative configurations are rejected.
- **Vector-corruption self-test:** 28 of 28 rejected, 24 of them lexical.
- **Wrong-lexer self-test (new):** **15 of 15 wrong lexers rejected.** Each is `tslex.Lexer` with one rule choice changed, substituted for the profile's lexer, and the checker must fail on the shipped vectors. Each fails on the vector added for it:
  - all **8 variants the review found accepted**: V1 `}` always followed by a regex, V5 `await`/`yield` end an expression, V25 most keywords end an expression, V22 `exprEnd` false after a JSX element, V11 ASCII-only JSX trimming, V21 `<` anywhere in a tag, V13 a lone CR not ending a string, and V26 `0_1` accepted;
  - 7 more: the draft-1 newline rule, an LF-only newline rule (the review's W5, rejected by `ts-newline-prefix-cr-ls-ps`), the draft-1 arrow-body rule, escapes in the look-ahead, no separators in a NonOctalDecimal fraction, no header marking, and `!` resetting the flag.

  A 15th variant (unterminated comment after `extends` read as generic) is observationally equivalent to the profile (§5.2), so it is shipped but not counted.
- **Cross-check, vectors:**
  - Of the 68 accepted vectors, 59 agree with TypeScript's parser and 7 with its raw scanner (TypeScript reports syntax or strict-mode diagnostics for those). 2 diverge as documented: `ts-function-decl-division` and `ts-class-decl-division`, both tagged `departure`.
  - Of the 40 lexical error vectors, 17 are rejected by TypeScript at the same offset and 20 at another offset. 3 are accepted by TypeScript, as documented: `ts-err-await-identifier`, `tsx-err-generic-type-position` and `tsx-err-lookahead-escape`.
  - The 5 pre-lexing vectors are not compared.
  - There are 0 undocumented divergences.
- **Cross-check, corpus:** every `lib/*.d.ts` and `lib/*.js` file of the pinned package, all as `ts-tokens`: 119 files, 19.8 MB, 2,478,321 tokens. **All 119 agree**, with 71 `gt-merge` adjustments. The corpus is compiler-emitted code and declaration files with no JSX.
- **Cross-check, probes:** 55 inputs. 35 agree as expected and 20 diverge exactly as §9 documents. There are 0 unexpected outcomes.
- **Unicode sweep:** unchanged from draft-1. Identifier start differs on 8,949 code points and identifier part on 9,132 (D-8), white space on 2 (D-6) and line terminators on 0.

**Limits.** The hand-written streams, `tslex.py` and the wrong-lexer variants come from one author. The review's independent lexer reproduced all 89 draft-1 vectors byte for byte. The review's confirmation pass independently reproduced all 112 draft-2 vectors. The N2 vector `ts-newline-prefix-cr-ls-ps` was added afterwards. The cross-check covers only the shipped inputs, the probes and a corpus without JSX.

## 12. Decisions

**Decided in draft, pending owner confirmation** (each changes tokens, hashes or accept/reject, and the vectors encode it):

| ID | Decision | Reason |
| --- | --- | --- |
| TSOD-1 | (b, revised in draft-2) Staged: `ts-tokens` (stage 1) takes `.ts`, `.mts`, `.cts`, `.js`, `.mjs` and `.cjs`. `tsx-tokens` (`.tsx`, `.jsx`) is deferred, kept as a draft and not frozen until a `.tsx` corpus measures TSOD-8 | Coordinator decision after the review. JSX in `.js` usually fails explicitly (§2, D-16) |
| TSOD-2 | (a) `keyword` is the 46 ECMAScript reserved and strict-reserved words; TypeScript-only and contextual words are `ident` | Rename robustness, like Go OD-7; a textual rule that needs no parser |
| TSOD-2b | (a) No separate class for contextual words. A `ctxword` class can come later as a new profile version | The review recommends settling now, because the choice changes hashes |
| TSOD-3 | (a) The `exprEnd` rule of §4.9, with header `)`, arrow-body `}`, and `!`/`++`/`--` passing the state through unless a line terminator precedes them. Departure list completed | Coordinator decision. Deterministic and portable; the remaining departures are listed and pinned |
| TSOD-4 | (a) `>`-family longest match everywhere | ECMA-262 lexical grammar; TypeScript is adjusted in the cross-check |
| TSOD-5a | (a) No ASI tokens | ASI is syntactic |
| TSOD-5b | (c) `;` kept in `exact`, dropped from `normalized` | Coordinator decision. Measured survival on a semi→no-semi reformat: 61.1% (review) or 62.5%–67.3% (this revision) with `;`, and 100% without (§4.10) |
| TSOD-6 | (a) HTML-like comments and conflict markers are not trivia | Module goal; deterministic |
| TSOD-7 | (a) The exclusions in §2 (`.d.ts` family, `@generated`/`DO NOT EDIT` in the first 2048 bytes, `.min.*` or a line over 4096 bytes) | A file-selection rule (TW-01/TW-03), not an extractor rule. The thresholds are unmeasured |
| TSOD-8 | (a) for the deferred `tsx-tokens`: accept the §5.5 limitation and reject those inputs | Options (b) and (c) need corpus numbers first |
| TSOD-9 | (a) `jsx-text` trimmed with the full trivia set; white-space-only text dropped | Layout invariance (`tsx-format-a/b`, `tsx-nbsp-text`) |
| TSOD-10 | (a) ID_Start/ID_Continue from the pinned UCD (§3.2), not XID; no NFC | ECMA-262 2026 |

**Closed:** TSOD-13 (normalized-stream exclusions) is settled by contract OD-23 at roadmap-v2 c81be10. §6 declares `punct` `;`, and every accepted vector is recomputed under the contract rule.

**Must be settled before `tsx-tokens` leaves deferral:**
- **TSOD-8 frequency** on a real `.tsx`/`.jsx` corpus, then the choice between (a), (b) one more look-ahead and (c) a minimal type/expression context tracker.

**Can wait:** TSOD-11 (the Ecma PDF pin, before promotion), TSOD-12 (re-running the TypeScript 7 oracle; the oracle is a cross-check, not the authority), TSOD-7 threshold tuning (TS.4 corpus), and k and w for this profile (TW-05, contract OD-10).

## 13. How hard is agreement, compared with Go and Rust

**Harder, by a clear margin.**
- The Go and Rust profiles are context-free at the token level except for Go's semicolons, which are a one-flag rule.
- This profile needs three pieces of context: the `exprEnd` flag, a stack that carries template and JSX modes, and a look-ahead for TSX generics.
- Every one of these is a place where two careful implementers can read the same sentence differently. Examples: what "previous token" means after `!`, which `}` continues a template, where JSX text is trimmed, and what happens to an unterminated comment inside the look-ahead.

The M1.4 cross-check spent 9.88 million cases to find a single Rust divergence (shebang look-ahead over doc comments). That was a much smaller state space.

**In this profile's favour:**
- There is no NFC.
- Error classes are few, and offsets are token starts.
- The regex rule is an 11-row table, not a grammar.
- On 2.48 million corpus tokens the rule never disagreed with TypeScript's parser. That corpus is compiler-emitted JavaScript and declaration files without JSX, so this says nothing about hand-written or `.tsx` code (§4.9). The review's 536 targeted runs found only the documented departure classes.

The risk is concentrated in JSX, where the profile admits a known gap (TSOD-8) and has no corpus evidence.

**Recommendation: staged, now decided in draft (TSOD-1).**
1. **Stage 1:** freeze `ts-tokens` (`.ts`, `.mts`, `.cts`, `.js`, `.mjs`, `.cjs`); TSOD-13 is closed by contract OD-23. Run TS.3 and TS.4 on it.
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
| Significant whitespace | JSX text trimming (§5.4); line terminators end comments and strings and turn a following `!`, `++` or `--` into a prefix operator (§4.9); no ASI tokens, and `;` is dropped from `normalized` (§4.10, §6) |
| Macros and generated code | No macros. Generated, minified and declaration files are excluded (§2, TSOD-7) |
| Token serialization | §6, contract §6 |
| Hash parameters, window sizes, tie-breaking | Contract §7–§8 and OD-10 (k = 5, w = 4, rightmost minimum) |
| Coordinate units | UTF-8 byte offsets, half-open (contract §3). The cross-check converts TypeScript's UTF-16 offsets |

## 15. Review dispositions

The [clean-room review](../reviews/extraction-profile-typescript-review.md) of draft-1 (commit fb09039) found:

| Finding | Resolution |
| --- | --- |
| F1: vectors did not pin 8 rule choices | Vectors added: `ts-object-class-division` (V1), `ts-err-await-identifier` and `ts-yield-await-regex` (V5, V25), `tsx-element-division` (V22), `tsx-nbsp-text` (V11), `tsx-err-attr-lt` (V21), `ts-err-cr-in-string` (V13), `ts-err-zero-separator` (V26). The checker's new wrong-lexer self-test runs all 8 variants plus 6 more and rejects 14/14 |
| F2: §4.9's departure list was incomplete; "never departed" overclaimed | Two rules changed where a parser-free rule matches ECMAScript exactly: the arrow-body `}` and `!`/`++`/`--` after a line terminator (`ts-arrow-body-regex`, `ts-newline-prefix-regex`). Function and class declaration `}` and `await`/`yield` as identifiers are documented departures, pinned by `ts-function-decl-division`, `ts-class-decl-division` and `ts-err-await-identifier`, with the reason for not tracking statement position (§4.9). The corpus claim is now qualified |
| F3 / A1: the generic look-ahead was underspecified | §5.2 now covers trivia (skipped everywhere), escapes (none allowed; D-14), no reserved-word check on the name after `const`, `extends` as a whole word, and the unterminated-comment conflict (JSX, which is observationally equivalent). Vectors `tsx-generic-const-reserved`, `tsx-extends-word`, `tsx-err-lookahead-escape`, `tsx-err-extends-comment` |
| F4: `;` made the normalized channel style-dependent | TSOD-5b (c): `;` excluded from `normalized` (§6, §4.10), `ts-semi-a/b`, and the survival figures. The contract amendment (TSOD-13) is in place as contract OD-23 |
| F5: §5.5 under-listed the limitation | Construct signatures `new <T>(…)` and the `(`, `\|`, `&`, `,` and `<` positions added, with the 6.4% proxy. Probes for the construct-signature, `(` and type-argument cases |
| A2: separators in a NonOctalDecimal fraction | Allowed in the fraction and exponent, not in the integer part (§4.5, `ts-nonoctal-separators`) |
| A3: offset after a self-closing `/` | The offending character (§5.3) |
| A4: "directly after `=`" | The previous token is `=`, and trivia may come between them (§5.3, `tsx-attr-element-space`) |
| A5: `exprEnd` after a `jbrace` `}` | Unchanged, and unobservable (§5.4) |
| A6: tag-mode token classes | Stated in §5.3 |
| Review §4: stage, with `.js` through `ts-tokens` | TSOD-1 (b); `ts-plain-js`, `ts-err-jsx-in-js`, and limitation D-16 `ts-jsx-selfclosing-in-js` |
| Review §4: settle TSOD-2b | (a), decided in draft |

## 16. Changes from draft-1 to draft-2

**Version bump.** The `profileVersion` is now `draft-2` in both profiles, because the normalized channel changed. All three configuration digests changed (§10). The profile version is part of every k-gram hash input (contract §7), so **every k-gram hash of every accepted vector changed**.

**Token streams and error results:** unchanged for all 89 draft-1 vectors. The new rules (arrow body, line terminator before `!`/`++`/`--`, escape-free look-ahead, NonOctalDecimal separators) are not exercised by any draft-1 input.

**Normalized channel changed** (`;` dropped) in 46 vectors:
- every accepted `ts.json` vector except `ts-empty`, `ts-short`, `ts-html-comment`, `ts-no-asi` and `ts-line-terminators`;
- every accepted `tsx.json` vector;
- `ts-limit-exact`.

**23 vectors added:**
- **`ts.json`:** `ts-semi-a`, `ts-semi-b`, `ts-object-class-division`, `ts-arrow-body-regex`, `ts-function-decl-division`, `ts-class-decl-division`, `ts-newline-prefix-regex`, `ts-yield-await-regex`, `ts-nonoctal-separators`, `ts-plain-js`, `ts-jsx-selfclosing-in-js`, `ts-err-jsx-in-js`, `ts-err-await-identifier`, `ts-err-cr-in-string`, `ts-err-zero-separator`;
- **`tsx.json`:** `tsx-element-division`, `tsx-nbsp-text`, `tsx-attr-element-space`, `tsx-generic-const-reserved`, `tsx-extends-word`, `tsx-err-attr-lt`, `tsx-err-lookahead-escape`, `tsx-err-extends-comment`.

**Tags.** `tsx-err-generic-type-position` and `tsx-err-lookahead-escape` gained the `departure` tag, which the cross-check uses to expect a divergence.

The review's confirmation pass (draft-2) added N1–N4:
- **N1:** the contract's versioning sentence must also cover normalized values and exclusions. That is a contract change, owned by the coordinator.
- **N2:** vector `ts-newline-prefix-cr-ls-ps` (CR, LS and PS before `++`, `!` and `--`), plus the `WLFOnly` wrong lexer, which the checker now rejects.
- **N3:** the §7 offset counts, the D-11 position list, the §13 row count and the §13 corpus claim are corrected.
- **N4:** the deferral rule for `.js` files containing JSX is in §2.

N2 adds one vector and changes no existing output, so `profileVersion` stays `draft-2`.

## 17. Freeze record: `ts-tokens` `draft-2`

**Frozen for stage-1 implementation, pending owner confirmation of the decided-in-draft items** (§12: TSOD-1 to TSOD-10 and TSOD-2b). Implementations target these exact bytes. Any change to them needs a new `profileVersion` (contract §10 versioning). `tsx.json`, `config-tsx.json` and §5 are **not** frozen (deferred, TSOD-8).

| File (in [extraction-vectors-typescript/](extraction-vectors-typescript/README.md)) | SHA-256 |
| --- | --- |
| `ts.json` (77 vectors) | `be290174a694e3124c510518203220ab6675ac5d44081f89980c08b594f4dc81` |
| `limits-ts.json` (3 vectors) | `b9db6d79758873db321cee28b7b5161465337666b4c3db18e1efd390f018eb9f` |
| `config-ts.json` (= `configSha256`) | `aeeed14177cd3be8fea69e453c825e74f2fd301d03babbf49329bde0cc4754de` |
| `config-ts-limit16.json` | `94403dd3e71a8105a9dcec894fc0d05d09cb771efaada28802dcf43ecd08f8d6` |
| `config-negative-typescript.json` (19 negatives) | `3965135bae03ab40e244a604e0393247fb750ba326c12eeb68be880f947a291c` |
| `../extraction-vectors/unicode-17.0.0-tables.json` (shared, contract §3a) | `9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f` |

**The normative text** is this document's §1–§4, §6, §7, §9 and §10, with `normalizedExclusions` `punct` `;`. Its digest is the git blob at the commit that adds this record. The checker (`check_vectors.py`) and `tslex.py` are verification tooling, not frozen artifacts. They may change without a version bump as long as the frozen bytes above still pass.
