# Independent review: TypeScript/JavaScript token profile (`ts-tokens`, `tsx-tokens`)

> Path note: the profile and vectors reviewed here were promoted on 2026-11-23 to [profiles/typescript.md](../../profiles/typescript.md) and [test-vectors/extraction-typescript/](../../test-vectors/extraction-typescript/README.md); the review text below keeps the paths of the time (`research/drafts/...`). See the [promotion map](../promotion-map.md).

Reviewed 2026-11-22 at commit fb09039: [extraction-profile-typescript.md](../../profiles/typescript.md) and [extraction-vectors-typescript/](../../test-vectors/extraction-typescript/). I wrote none of it and re-ran everything myself. Scratch code lived in `$TMPDIR` only. Tools: Python 3.14.6, Node 22.23.2, and TypeScript 6.0.3 from the harness's pinned `node_modules`.

## 1. Clean room (before reading `check_vectors.py` or `tslex.py`)

I wrote a ~330-line lexer for both profiles from the profile text and the contract alone. It covers the §3 pre-checks, the `exprEnd` flag, the delimiter/template/JSX stack, the generic look-ahead, tag and children modes, numbers, strings, templates and regexes. It reads Unicode data only from the pinned `unicode-17.0.0-tables.json` plus the 23/19 deltas listed in §3.2. I also wrote a separate k-gram/winnowing recomputation using contract §7 draft-1, which hashes `LP(profile) || LP(profileVersion)`.

| File | Tokens or error (code + offset) | Hashes, windows, fingerprints |
| --- | --- | --- |
| ts.json | **61/61 match** | 34/34 |
| tsx.json | **25/25 match** | 16/16 |
| limits-ts.json | **3/3 match** | 1/1 |

All four config digests match §10. Everything matched on the first run. I still had to guess in these places, each of which is an ambiguity:

- **A1. Generic look-ahead (§5.2:245-251).**
  - Is trivia skipped between `const` and the second name?
  - May N1 contain `\u` escapes?
  - Is the second name after `const` checked against the reserved words?
  - Is "the next word is `extends`" a whole-word match (`extendsX` is not)?
  - An unterminated comment *after* `extends` hits two rules at once: "unterminated comment → JSX" (line 253) and "anything else … → generic" (line 250). This one is a real conflict, not just a gap.
- **A2.** §4.5:150 says NonOctalDecimal takes "no separators". It is unclear whether that also covers the fraction and exponent. ES2026 allows `08.1_1`, and TypeScript tokenizes it as one number. I allowed it.
- **A3.** §5.3:264 does not give the offset of the `illegal-character` after a self-closing `/`. I guessed the offending character, which matched `tsx-err-self-closing`.
- **A4.** §5.3:262 says "directly after an `=` token". I assumed trivia may sit in between.
- **A5.** §4.2:106 leaves `exprEnd` unset after a `}` that pops `jbrace`. As far as I can tell this is unobservable, but it should be stated.
- **A6.** The text implies, without saying it, that tag-mode `/` and `>` are emitted as `punct` tokens.

## 2. Cross-check against TypeScript 6.0.3

I wrote my own oracle (`createSourceFile` plus a leaf walk). It converts UTF-16 offsets to bytes, merges adjacent `>` tokens into the longest punctuator (the declared `gt-merge`), trims JsxText with the §3.1 character set, and treats keyword and ident as one class. Each input was compared on class, text and byte span.

The 268 inputs focus on context, giving **536 runs**:
- regex vs division in 86 contexts, including `)` of non-control parentheses, `}`, `return/typeof/yield/await/in/case/void/new`, class bodies, arrow bodies, `!`, `++`, `--` and decorators;
- 21 template nesting cases;
- 62 JSX vs generics/comparison cases;
- 13 `>>` cases, 28 contextual keywords, 26 Unicode identifiers, 16 line-terminator cases, 29 numbers and 18 miscellaneous inputs.

**Results:**
- **422 identical streams** (14 of them after gt-merge).
- **39 identical streams** where TypeScript also reports a syntax diagnostic. The tokens agree; examples are `08.5`, `\8`, `-->`, `a ?? b ??= c` and `<a/>\n<b/>`.
- **47 rejected by both.**
- **28 lexical differences**, broken down below.

| Divergence class (smallest input) | Runs | Profile decides? | Documented? |
| --- | --- | --- | --- |
| Regex after a block `}`: `{}\n/re/.test(s)`, `if (x) {}\n/re/` | 4 | Yes, division (§4.9:206) | Yes (D-10) |
| Regex after the `}` of a **function declaration, class declaration or arrow body**: `function f(){}\n/re/g.test(s)`, `x = (a) => {}\n/re/.test(s)` | 6 | Yes, division | **No.** §4.9:212 names only block statements |
| `for (m of /x/g…)`, `for await (…) /re/` | 4 | Yes, division | Yes (D-10) |
| **ASI before a prefix `++`/`--`: `a\n++/re/.lastIndex`** (TypeScript: regex) | 2 | Yes: `++` passes `exprEnd` through, so division | **No** |
| **`await` or `yield` used as an identifier in script code: `x = await / 2`.** TypeScript: division; profile: `unterminated-literal` | 2 | Yes (keyword) | **No** |
| `@dec /re/` (a syntax error either way) | 2 | Yes | No (harmless) |
| U+0085, U+200B | 4 | Yes | D-6 |
| `.tsx` generic in a type position: `type F = <T>(x: T) => T`, `let f: <T>() => void`, `interface I { <T>(x: T): T }` | 3 | Yes (reject) | D-11 |
| Merge-conflict markers | 1 | Yes | D-7 |

The other context-dependent areas show no lexical differences:
- **Templates:** all 42 runs agree, including `${ {} }`, `${'}'}`, `${ /}/ }`, a three-deep nest and `` `${ `}` }` ``.
- **`>>`:** all 26 agree under gt-merge.
- **Contextual keywords:** all 56 agree, including `a. if`, `a?.\nif` and `#if`.
- **Line terminators:** all 32 agree (LS/PS/CR in comments, strings, regex and hashbang).
- **Unicode:** all 52 agree apart from D-6. None of my code points hit the table gaps that D-8 describes.
- **JSX vs generics:** the `<T,>`, `<const T,>`, `<T extends unknown>`, `<T extends {}>`, `<T>(a)</T>` and `<in/>` cases all agree.

**TSOD-8 frequency.** I found **no real `.tsx`/`.jsx` sources** in the harness's `node_modules`, `~/.npm/_npx` or the Homebrew node toolchain directory (0 files), so the rejection rate on real `.tsx` code is unmeasured. As a proxy only, I lexed TypeScript's 110 `lib/*.d.ts` files as `tsx-tokens`: **7 (6.4%) are rejected**. One cause is not listed in §5.5: **construct signatures, `new <T>(…)`**, as in `lib.es2015.iterable.d.ts`, alongside `: <T>(…)` positions. These are declaration files, which are excluded in practice, so the proxy only shows that the pattern is common in type-heavy code.

## 3. Wrong-but-plausible lexers vs the checker

I built 26 variants by patching my lexer and ran the **shipped `check_vectors.py` with each one substituted for `tslex.lex`**. With my unpatched lexer substituted, the checker passes everything, so its re-lex is reproducible independently. **It accepts 8 of the 26 wrong variants**, because no vector separates them from the profile:

| Accepted wrong lexer | Example input where it diverges (from my probes) |
| --- | --- |
| V1 `}` always followed by regex (ECMAScript-like for statements) | `x = {} / 2`, `x = class{} / 2` |
| V5 `await`/`yield` end an expression | `x = await / 2` |
| V25 every keyword except `return/typeof/case/in/…` ends an expression | `x = yield /a/` |
| V22 `exprEnd` false after a JSX element | `x = <div>a</div> / 2` |
| V11 JSX text trimmed with ASCII white space only (not Zs/NBSP) | `<div> a </div>` |
| V21 attribute-value `<` allowed anywhere in a tag | `<a <b/> />` |
| V13 a lone CR does not end a string | `'a\rb'` |
| V26 `0_1` accepted | `x = 0_1` (§4.5:158 lists it as an error, but no vector has it) |

The checker rejects the other 18. Examples: no header marking, `!`/`++` reset the flag, `}` closes a substitution anywhere on the stack, `>>` split, no `?.` digit look-ahead, regex classes not tracked, keyword after `.`, look-ahead without `extends`, XID instead of ID, legacy-octal fraction, no hashbang, escaped keyword, contextual words as keywords, `//` ending only at LF, `>` allowed in JSX text, `${` at EOF reported as `unbalanced-delimiter`, and error offset at the failing character. That is a strong record. **The 25/25 mutation self-test does not measure this kind of gap**: it corrupts vectors, whereas these are rule choices that no vector exercises.

## 4. Judgement

**Is the `exprEnd` flag deterministic and implementable identically in Rust and Go?** Yes. It is a pure function of the previous emitted token class and text, the header bit stored on the `(` stack entry, and the `!`/`++`/`--` passthrough. It needs no backtracking or parser. The generic look-ahead is bounded and reads ahead only, so it is just as portable once A1 is fixed. The risk is not non-determinism. It is (a) undocumented departures from ECMAScript, which mislead users about what "division" means, and (b) the 8 rule choices above, which vectors do not pin. Two careful implementers could each pick a different one and both pass.

**Is the two-profile split right?** Yes. JSX is the only token-level fork, and `ts-tokens` / `tsx-tokens` with `.js` → `tsx-tokens` is the minimal correct split.

**Is staging wiser?** Yes, and I agree with §13. Freeze `ts-tokens` first, and let stage 1 run plain `.js/.mjs/.cjs` through `ts-tokens` as well: a JSX-bearing `.js` file then fails explicitly instead of being mis-lexed. Defer `tsx-tokens` until a real `.tsx` corpus measures TSOD-8. The proxy above and the missing `new <T>` case suggest the rejection rate will not be negligible.

**Should `;` remain a token?** I simulated a semi → no-semi reformat on 42,043 tokens of `lib/_tsc.js` by dropping each `;` that is followed by a newline. Only **61.1% of `normalized` fingerprints survive**. On the same simulation, dropping `;` from `normalized` keeps 100%. Go needs no such rule, because its inserted `;` already makes the stream style-independent. A Prettier `semi` flip is a one-option transform, so leaving it to defeat the channel meant to survive surface edits would be a design hole.

**TSOD decisions:**
- **TSOD-5b: settle now as (c), drop `;` from `normalized` only.** Keep it in `exact`. The cost is that `for(;;)` loses its separators in `normalized`, which is minor.
- **TSOD-3 (a): settle now.** Keep the rule, but list every departure class found in §2 and add vectors that pin V1, V5/V25 and V22.
- **TSOD-8: settle now as (a) for `tsx-tokens`, and stage.** Options (b)/(c) need corpus numbers first. Add `new <T>(` and construct/call signatures to §5.5.
- **TSOD-2b: settle as (a) now.** It changes hashes, and `ctxword` can come later as a new profile version.
- **Leave as decided in draft:** TSOD-1, -4, -5a, -6, -9 and -10. TSOD-7 is a file-selection rule (TW-01/03) and does not block the extractor.
- **Can wait:** TSOD-11 (Ecma PDF, before promotion), TSOD-12 (TypeScript 7 oracle; the oracle is a cross-check, not the authority) and TSOD-7 thresholds.

## 5. Findings, most severe first

- **F1 (high): vectors do not pin 8 rule choices** (§3 table; profile §4.9:199-209, §4.2:96, §5.3:262, §5.4:280, §3.1, §4.5:158). Fix: add vectors for:
  - `x = {} / 2` vs `x = class{} / 2`;
  - `x = await / 2` (expected error) and `x = yield /a/`;
  - `<div>a</div> / 2`;
  - NBSP-bordered JSX text;
  - `<a <b/> />` (error);
  - `'a\rb'` (error);
  - `0_1` (error).
- **F2 (medium): §4.9's departure list is incomplete** (lines 211-216). Add the function, class and arrow-body `}` cases, `a\n++/re/` and `await`/`yield` used as identifiers. Also qualify the claim "never departed" in line 216: it rests on a corpus without JSX, and almost all of that corpus is compiler output.
- **F3 (medium): the generic look-ahead is underspecified** (A1). State whether trivia and escapes are allowed, whether the second name is checked against reserved words and whether `extends` must be a whole word. Resolve the unterminated-comment-after-`extends` conflict between lines 250 and 253.
- **F4 (medium): TSOD-5b as drafted (`;` kept)** makes the normalized channel style-dependent, losing about 39% of fingerprints in the simulation. Adopt (c) before freezing the hashes.
- **F5 (low): §5.5:286 under-lists the TSX limitation.** Construct signatures (`new <T>(`) and `|`/`(`/`,` positions are missing. The proxy rejection rate is 6.4% of TypeScript's lib `.d.ts` files.
- **F6 (low):** fill in A2–A6 (separator scope, self-closing offset, "directly after `=`", `exprEnd` after a `jbrace` `}`, tag tokens are `punct`).

## Verdict

**Ready to implement after the listed fixes, staged: `ts-tokens` first.** The hash layer, the pre-checks and the lexing rules for `ts-tokens` are precise enough that my independent lexer reproduced all 89 vectors byte for byte. Before two implementations start: add the F1 vectors, correct the §4.9 list (F2), settle TSOD-5b as (c) and settle TSOD-3/-2b. `tsx-tokens` additionally needs F3 and a real `.tsx` corpus measurement for TSOD-8 before it is frozen.

## Confirmation pass (draft-2: bdbc19d, d955ee6; contract OD-23: c81be10)

**Method.** I updated my clean-room lexer from the draft-2 text only: arrow-body `{` marking and its `}` (profile lines 107, 112), a line terminator before `!`/`++`/`--` (line 114), and escape-free look-ahead names with an unterminated comment meaning JSX (275–285). I extended my hash code with the contract §6 exclusion rule, `tokenIndices` and per-channel counts. I read `check_vectors.py` and `tslex.py` only afterwards, to plug in the variants.

**Reproduction: all 112 vectors match byte for byte** (tokens or error code and offset): ts.json 76/76, tsx.json 33/33, limits-ts.json 3/3. Hashes, windows, fingerprints, `tokenIndices` and the `tokenIndices`-before-`values` key order match for all 67 accepted vectors (45 + 21 + 1). The three config digests match §10. My unpatched draft-1 lexer fails exactly 3 vectors (`ts-arrow-body-regex`, `ts-newline-prefix-regex`, `tsx-err-lookahead-escape`), so each new rule is pinned. My one new guess: "the previous token" for the line-terminator rule when no token precedes. This is unobservable, because `exprEnd` is already false at the start of input.

**Wrong lexers.** I ran the shipped checker with my lexer substituted, under 36 variants: the 26 earlier ones plus 10 suggested by draft-2 (arrow-body `}` followed by division; every `{…}` after `)` followed by a regex; block-comment line terminators ignored; the newline rule for `++`/`--` only; the newline rule counting LF only; `ts-tokens` rejecting `<`+name; `.js` lexed with JSX rules; a reserved-word check after `const`; `extends` as a prefix; escapes decoded in the look-ahead). **The checker rejects 35 of 36**, including all 8 that draft-1 accepted. **It still accepts W5: only LF counts as a line terminator before `!`/`++`/`--`**, because no vector puts CR, LS or PS there. My unpatched lexer still passes everything.

**TypeScript 6.0.3 on the new rules.** 24 new probes: arrow bodies (`async`, single parameter, typed return, a function type returning `{…}`, inside a call), `a\n--/re/`, a line terminator inside `/* */`, CR, LS, `// c\n!`, `if (x)\n!/re/`, and JSX in `.js` under `ts-tokens`. Every probe agrees, except the documented D-16 shape (`<br/>`, `f(<br/>)`), where TypeScript in `.ts` mode reports syntax errors. On the original 536 runs, the lexical differences fall from 28 to 24, and every remaining one is in §4.9:223-233 or §9.

**Earlier findings:**

| Finding | Status | Where (profile line numbers) |
| --- | --- | --- |
| F1 unpinned rule choices | Resolved, apart from W5 (N2) | Vectors at 525; checker run above |
| F2 departure list, corpus claim | Resolved | Rules 107/112/114; table 205–217; departures 223–235; claim qualified 237; D-10/D-15 391, 396 |
| F3 / A1 look-ahead | Resolved (tsx, deferred) | 275–287, D-14 395 |
| F4 `;` in normalized | Resolved | 243–251, 336–348; contract §6 |
| F5 TSX limitation list | Resolved | 321–330 |
| A2–A6 | Resolved | 156, 298, 296, 313, 291 |

**New problems:**
- **N1 (medium, contract): versioning skips normalized-only changes.** `extraction-contract.md:325` mints a new `profileVersion` "only when tokens, classes, errors or Unicode tables change". Draft-2 changed neither tokens nor classes; it changed `normalizedExclusions`, and with it every normalized hash. Read literally, that line would not require a new version. Add "normalized values or exclusions" to the list.
- **N2 (low): no vector for a non-LF line terminator before a prefix operator.** Add one such as `a⏎++/re/.lastIndex` with LS, and `a⏎!/re/` with CR, to close W5.
- **N3 (low): stale text.** Line 492 says "12-row table", but the table at 205–217 has 11 rows. Line 493 still makes the unqualified "never disagreed" claim. D-11 at line 392 lists only `=`, `:` and `{`, while §5.5 lists more positions. §7 at line 370 still says "16 of 33", which differs from §11 at line 445.
- **N4 (low, file selection, not the extractor):** React projects often keep JSX in `.js`. Under stage 1 those files mostly fail, and text-free elements are fingerprinted as punctuators (D-16, line 40). TW-01/TW-03 should count such failures as "deferred to stage 2", not drop them silently.

**Is OD-23 well defined?** Yes for what two implementations must agree on. Matching is by class and exact text, and Go's inserted `;` is pinned by `exclusion-rule.json`. Positions, windows and fingerprint positions index the filtered stream, and spans come from the first and last kept tokens (contract 253–257). Status comes from the exact count, and an empty normalized channel is defined (contract 256, 284). `tokenIndices` is emitted if and only if the profile declares exclusions. My independent recomputation agreed on every field. The only gaps are N1 and the locality sentence at contract line 291, which should say the run is counted in the channel's own stream (kept tokens for `normalized`).

**Verdict for `ts-tokens` stage 1: ready to freeze and implement once N1 (a one-line contract fix) and N2 (two vectors) are done.** N3 and N4 do not block. The remaining condition is owner confirmation of the items marked "decided in draft".
