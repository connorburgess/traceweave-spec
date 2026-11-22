# Independent review: draft extraction contract and vectors

Reviewed 2026-11-22: [extraction-contract.md](extraction-contract.md) and [extraction-vectors/](extraction-vectors/). I wrote none of these files, and I re-ran everything rather than relying on their self-reported verification. Scratch programs lived in `$TMPDIR` only. Toolchains used: go1.27.3, rustc 1.97.1, proc-macro2 1.0.107 built `--offline` from the local cargo cache, and Python 3.

## 1. Clean-room recomputation (done before reading check_vectors.py)

I wrote a ~50-line program from §6–§8 alone. It reads each recorded token stream and recomputes status, normalized values, the LP-encoded k-gram bytes, SHA-256 first-8 hashes, k-gram spans, rightmost-minimum winnowing, `partialWindow` and fingerprints, then compares each field with the vectors.

- **go.json: 12/12 accepted vectors match in every field. rust.json: 15/15 match.** Both config files hash to the digests stated in §10.
- I also confirmed the pinned-source digests: `go_spec.html` and all 7 Reference pages hash to the values in the README. The Reference pages came from the `stable` toolchain directory, which is rustc 1.97.1.

Places where I had to guess:

- **A1.** `partialWindow` when m = 0. §8 is silent. I guessed `false`, which matches the vectors.
- **A2.** Whether inserted `;` tokens are exempt from `text == input[span]`. §6 implies they are exempt, but §13:271 claims the rule holds for "all ok vectors". My first run flagged 10 Go vectors on this point before I exempted them.
- **A3.** `profileId` is the config's `profile` string. Implied, not stated.
- **A4.** In the partial case, `windowSelections` is a one-element list. Implied by "one window".

## 2. Lexing against the real toolchains

**Go (own harness, go/scanner mode 0).** For all 12 accepted vectors I compared class, text and `[start,end)` of every token. Inserted `;` was compared by kind and order only. **All 12 agree.** Error vectors: 7 of 8 are also go/scanner errors at the same offset. The exceptions are `0x` and `\q`, where go/scanner reports offset 7 and the vector says 5 (OD-13), and the BOM vector, which go/scanner accepts (OD-1). `unicode.Version` is 17.0.0.

**Rust (own proc-macro2 harness).** I mapped `'`+Ident (Joint) to `lifetime`, flattened groups, blanked the shebang line while keeping offsets, and compared class, text and both offsets. Number classes were not compared, because proc-macro2 does not expose them. **All 15 agree.** For `rust-doc-comment`, the 6 real tokens agree once proc-macro2's synthesized `#[doc]` tokens are removed. Five error vectors fail at the same offset. BOM, NUL, isolated CR, non-NFC and `f"x"` are accepted by proc-macro2, which is expected. rustc_lexer was not available offline, so I did not use it.

**Edge-case probes** (about 90 inputs through go/scanner, proc-macro2 and rustc in a `macro_rules!` wrapper, compared with the contract text):

| Case | Contract decides? | Note |
| --- | --- | --- |
| Go `;` after comments, CRLF, EOF, `/*\n*/` | Yes (§4.3) | Matches go/scanner kind and order |
| Go hex float without `p`, `0x.p1`, `1p3`, `0b1.0`, `1e+`, `08i`, `0_7`, `1..2`, `.5i` | Yes (EBNF + §4.4) | No vector covers hex-float errors |
| Go raw string with CR, `'\x80'`, `'\400'`, `''`, `~`, `&^=`, `<-`, `...`, generics, mid-file BOM, U+000B/U+000C | Yes (§3, §4.2, §4.5, OD-9) | No vector for CR in a raw string or a mid-file BOM |
| Rust lifetimes vs chars (`'r#a`, `'r#a'`, `'a#`, `'1`, `'fn`), nested/doc comments, shebang vs `#![`, CRLF, frontmatter `---` | Yes (§5.2, §5.3, OD-5) | Raw lifetime has no vector |
| Rust raw strings `r##"a"#b"##`, `r"a"#`, `r#`, `br#x`, `rb"x"`, `c'x'`, `k#x`, `##x`, `#"x"` | Yes | All agree with rustc acceptance |
| Rust numbers `1.max`, `2.e3`, `1.0.1`, `0x1.0`, `0b1e3`, `1e_`, `1_e`, `1e3f32`, `0x1f32` | Yes | Contract and rustc agree; proc-macro2 is laxer |
| Rust `\u{…}` with underscores, 7 digits, C-string `\0`, byte `\u` | Yes | — |
| **Rust literal followed by a lone `_` (`"x"_`, `'a'_`)** | **Decided wrongly** | See F2 |
| **Unicode category edges (U+2160, U+00B7, U+0345, U+2E2F, U+0660, ZWJ)** | Decided, but untested | See F3 |
| Shebang followed by an unterminated comment (`#!/*x\n[`) | **No** | rustc treats it as a shebang. The checker happens to match |

## 3. Findings, most severe first

**F1 (high): check_vectors.py passes wrong token streams.** I built a corrupted go.json with five changes, recomputing hashes for each with my clean-room code:
- the final inserted `;` dropped from `go-literals`;
- `func` relabelled as `ident` in both format pairs and both rename pairs;
- `:=` split into `:` `=` in `go-unicode`;
- an inserted `;` placed after `,`, which §4.3 forbids;
- the error code changed to `made-up-code`.

The checker printed `PASS … mutations-rejected=5/5`. The causes are:
- `check_vectors.py:245` checks class membership only;
- `:247-251` checks where an inserted `;` sits but never whether one is required;
- `:224` accepts any lexical code string outside the closed list.

The README admits it cannot check lexing, but it never shows that the shipped artifacts cannot check it either. Lexing is the part most likely to diverge, and ROADMAP M1 requires every normative requirement to map to a check. **Fix:** ship the Go and proc-macro2 harnesses plus a driver as a repeatable cross-check (settle OD-15 as "yes"), with the declared adjustments written into code. In the checker:
- recompute Go semicolon insertion from the classes and the newlines/comments in each gap;
- enforce the closed error-code list per profile;
- check keyword/ident classes against the §4.2/§5.3 keyword lists.

**F2 (high): the Rust suffix rule drops the Reference's cut.** At `extraction-contract.md:155`, the Reference (tokens.html, digest-pinned) says `SUFFIX → _ ^ XID_Continue+ | …`, and `^` means no backtracking. The contract therefore makes `"x"_` and `'a'_` two tokens, `"x"` and the keyword `_`. rustc rejects both inputs, and proc-macro2 lexes each as one literal. An implementation built on `ra_ap_rustc_lexer` (repo plan option A) would disagree byte for byte with one written from the contract text. §5.4:140 also gives a different SUFFIX (`XID_Start XID_Continue*`). **Fix:** a literal followed by `_` and then no XID_Continue is `malformed-literal` at the literal start. Use the Reference SUFFIX / SUFFIX_NO_E in both sections, and add vectors.

**F3 (high): Unicode property data is named but not bound.** The cross-language plan puts a Go-profile lexer in Rust and a Rust-profile lexer in Go:
- Rust std has no General_Category (`char::is_alphabetic` is a different property).
- Go std has no XID_Start/XID_Continue.

My probes show the natural shortcuts disagree on U+2160, U+00B7, U+0345, U+2E2F and U+200D. Rust is fine with `xⅠ` and `x·y`, but Go rejects them as illegal characters. The ecosystem is already drifting:
- unicode-ident 1.0.26+ ships **Unicode 18**, and 1.0.24 ships 17.
- x/text v0.39 `norm` uses 17.0.0 tables only under `go1.27` and falls back to **15.0.0** otherwise.

No vector exercises a boundary code point: they use ä, ö, ß, λ, 世 and 名. **Fix:** name the UCD 17.0.0 files with digests (UnicodeData.txt, DerivedCoreProperties.txt, DerivedNormalizationProps.txt) as the authority for §4.2 step 4, §5.3 and NFC. Require generated or vendored tables. Add accept/reject vectors for the code points above, plus decomposed `é` in a suffix and in a raw identifier.

**F4 (medium): discretion and gaps in the outcome rules.**
- `extraction-contract.md:23`: `unsupported-input` "at the offset where it stopped" lets two conforming implementations disagree. Make it a non-conformant result that no vector may expect.
- `unsupported-config` (§10:242) is missing from the closed lists at §4.8/§5.9.
- Config validation is not ordered relative to §3.
- `channels` order and subsets are unspecified (§10:246).
- `k` is unbounded even though §7 encodes it as `uint32be`. Bound it to 1…2³²−1 and bound `maxInputBytes`.
- String escapes in the config are unspecified. Forbid them (values are `[a-z0-9.-]`).
- Add A1 to §8.

**F5 (medium): Rust error precedence at the same offset is unordered** (§5.3:116-120). A decomposed `é` followed by `"` could be `reserved-token` or `non-nfc-identifier`, and a non-NFC name containing ZWJ could be either NFC code. The offset for a non-NFC raw identifier or suffix (`r#` vs the name) is also unspecified. **Fix:** state the order (NFC, then zero-width, then prefix) and say that offsets point at the token start.

**F6 (medium): OD-13 is marked open, but `go-err-malformed-number` and `go-err-invalid-escape` already encode option (a).** Settle it.

**F7 (low): consistency.**
- §13:271 vs §6 (A2).
- `spec/core.md:15` wants profile `id` *and* `version`. The contract folds the version into the id and adds a `contract` id; state the mapping.
- `profiles/code.md:7` asks for scope-aware normalization, which OD-7 honestly declines. That is acceptable for a control, but §12 should repeat the point.
- `conformance.md:13` needs negative vectors for stable profiles, and config negatives are absent (§13:284 says so).
- The shebang-plus-unterminated-comment case is undecided (§5.2:109). Say "an unterminated comment counts as comment", which matches rustc.

**F8 (low): coverage.** No vectors for `input-too-large`, mid-file BOM, Go hex-float errors, CR in a Go raw string, Rust raw lifetimes, `##`, C-string escapes, n > 255 hashes, or isolated CR inside a literal.

**Claims (§11–§12)** are properly limited. There is no ownership, authorship or calibrated false-alert claim, and locality is restated as the paper's guarantee only.

**Version pinning.** Freezing to go1.27 / Rust 1.97.1 Reference text plus Unicode 17 is workable, because the oracle is only a cross-check and is not the authority. Embedding `go1.27` in the profile id, however, forces a new profile every six months even when nothing lexical changes. Instead, identify profiles by lexical rules plus Unicode version, re-run the shipped cross-check on each new toolchain, and mint a new id only when tokens or tables change. That only works once F3's tables are pinned. Otherwise `cargo update` alone changes the Rust identifier set.

## 4. Open decisions

- **Settle before implementation** (the vectors or the config digest already encode them). Adopt each proposed default:
  - OD-1 (a), OD-2 (a), OD-4 (a), OD-5 (a), OD-6 (a), OD-8 (a), OD-9 (a), OD-11 (a, unkeyed and labelled as such), OD-13 (a), OD-16 (a), OD-18 (a).
  - **OD-3 (a)**, but only with F3's pinned NFC tables.
  - **OD-7 (a)**, and decide the sub-question now as "predeclared Go identifiers are erased", which is what the vectors do.
  - **OD-12 (a)**, plus UCD file digests.
  - **OD-17 (a)**, corrected for F2.
  - **OD-10 (a)**, frozen explicitly as experimental, because k and w are inside `configSha256`.

  Each of these changes token bytes, hashes or accept/reject.
- **Can wait:** OD-10 tuning (a new digest later, under TW-05), the OD-11 keyed option (keyed-selection gate) and OD-14 (TW-01/03). OD-15 does not block writing code, but F1 makes "yes" the right answer before anyone claims conformance.

## 5. check_vectors.py

Read after steps 1–4. The checker independently and correctly recomputes the config bytes, encoding-level errors, spans, normalization, hashing and winnowing. It reaches the same results as my clean-room code, and its sort-based selection is a genuinely different formulation. **It can pass on wrong vectors:** any self-consistent wrong token stream passes (see F1 for five demonstrated cases), and any lexical error code or offset passes. Its five self-mutations each target a property it obviously checks, so "5/5 rejected" says nothing about lexing.

## Verdict

**Ready to implement after the listed fixes.** The hash, winnowing and config layers can be implemented as written and reproduce exactly. Before two implementations start, fix F2 and F3 (they will otherwise diverge), F4–F6 (they leave discretion), and settle the decisions listed in §4. F1 must be closed before any byte-for-byte agreement claim.
