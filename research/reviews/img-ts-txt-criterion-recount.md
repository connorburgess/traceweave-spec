# Non-author criterion recount: IMG.5, TS.1/TS.2, TXT.1/TXT.2

Reviewed 2026-11-26 at committed spec revision **`24bb4b8483dc86966cb7c8277130bb816b0c6b3f`**. Every repository path below means that exact revision, not a later working-tree state. `profile-criterion-recount/evidence-manifest.json` records Git blob IDs, SHA-256 and last-change commits for 42 evidence files; all 42 working copies equalled the committed snapshot when checked. I did not author the image finding-aid, TS or text profiles/vectors being recounted. Previous promotion and downstream implementation results were not used as substitutes for criterion evidence.

## Verdicts

| Gate | Verdict | Scope / missing evidence |
| --- | --- | --- |
| IMG.5 | **Eligible**, through the schema-change alternative | Existing IMGF field mapping plus the reviewed profile-specific IMG draft-1 schema/fixtures accommodate the fields. This is not normative promotion, C2PA compatibility, origin proof or a claim that every raw experiment line was converted. |
| TS.1 | **Eligible for frozen stage-1 `ts-tokens` draft-2** | All registration items and named constructs have decided rules; JSX/TSX is explicitly covered as a deferred fork, not granted support. No stage-2 eligibility. |
| TS.2 | **Not eligible for unqualified closure as worded** | All seven M1.2 lexical classes and stage-1 lexical additions are represented. No fixtures encode expected `.d.ts`/generated/minified exclusion decisions, despite “plus the TS.1 classes.” Stage-1-only input pairing also has two cross-profile exceptions. See the precise criterion interpretation below; do not silently narrow the gate. |
| TXT.1 | **Eligible for frozen stage-1 `text-plain` draft-1** | Every listed item has a concrete answer. Markdown is specified as a separate, unfrozen/non-normative front end, excluded from this verdict. |
| TXT.2 | **Eligible for stage-1 `text-plain` draft-1** | All 13 classes appear in the plain/limit fixtures, including Markdown syntax treated as plain text. All 47 positives have paired mutated-result rejection fixtures under the established text-vector convention. This does not grant Markdown masking conformance. |

These are review recommendations only. No gates, counts, shared files or refs were changed. If a status line cannot express the stage-1 scope, the two scoped profile recommendations must not be turned into unqualified stage-2 closures.

## IMG.5: exact criterion and evidence

> IMGF and IMG results fit the lane-08 container fields, or a schema change goes through CONTRIBUTING

`research/lanes/08-evidence-review.md` “Shared interface boundary (proposal only)” has five field groups. `research/drafts/extraction-profile-image.md` §8.3 maps IMGF results; `research/drafts/image-mark-protocol.md` §12 identifies the extra IMG needs. The draft resolution `research/drafts/image-mark-finding-aid.md` §§1–4 chooses a profile-specific record rather than silently extending the generic container.

| Criterion component / source field | Recounted evidence |
| --- | --- |
| “IMGF ... results fit ... fields” | Image profile §8.3 maps artifact digest/role; profile/configuration and no-model case; whole-image pixel coordinates after orientation; raw hash/no payload/Hamming statistic; signature/trust outside extraction; unavailable confidence. Catalogue/query forms are §8.1/§8.2. The old missing consumer-schema decision OD-I6 remains an image-profile limit; this gate does not require replacing the whole fingerprint catalogue contract. |
| “IMG ... results fit ... fields” | Mark protocol §12 maps original entries/queries/summary fields. Finding-aid draft §3 and schema properties host artifact/decode, profile/protocol, region, raw/decoded evidence, outcome and null confidence; cryptographic verification remains a separate registration result. |
| Additional model digests | Schema `/carrier`: code commit and models with SHA-256, learned schemes require models. |
| Statistic and n | `/statistic`: name, n, matchedBits, acceptedEntries; checker binds n to tested bit count and matches outcome fields. |
| Threshold/calibration/search scope | `/threshold`: k, basis, calibrationId, perComparisonFalseAcceptBound and searchScope. No calibrated natural-image confidence asserted. |
| Key and derivation reference | `/keyReference`: keyId/derivationId, closed object, no key material. |
| Embedding quality | `/embeddingQuality`: measured PSNR/floor/cover-marked digests, or explicit unavailable. |
| Tested bit positions | `/testedBits`: half-open start/end, count/rawBitCount, excludedNote; ECC/version bits separated. PixelSeal fixture explicitly illustrates 257 raw bits versus 256 tested bits. |
| “or a schema change goes through CONTRIBUTING” | `CONTRIBUTING.md` requires use case, affected sections/delta, sources, schema/examples/negative cases/version together and review. Evidence package: draft rationale and source/result links; `schemas/image-mark-finding-aid.schema.json` with draft-1 record/schema identifiers; five examples and 24 negatives; checker integrated in `tools/validate.py`; committed non-author `research/reviews/media-c2pa-av-review.md`, confirmation at `a4ea8d4`, accepts B1/B2 and A1–A3 resolutions. This substantiates the local reviewed draft schema route, not publication or a new stable contract. No GitHub PR execution was inferred from that local review. |

Boundary checks include fixed `provesOrigin: false`, `provesAuthorship: false`, non-decisive decode/null confidence, free-text claim checks, separate `tw1-`/full-digest pointer, and semantic abstention/match/whole-image invariants. Existing checker rerun: **5 valid, 24 invalid, 17/17 required-field deletions rejected**, exit 0. Missing evidence for this gate's draft accommodation criterion: **none found**. Actual interoperability, full corpus conversion and cryptographic acceptance of a linked record are not claimed by this verdict.

## TS.1: exact criterion and clause recount

> Profile covers the M1.1 list plus ASI, regex vs division, template literals, JSX/TSX, and `.d.ts`/generated/minified exclusions

M1.1 also requires zero TBDs and token classes independent of lexer kinds, including the named raw-string/comment/shebang/BOM/CRLF constructs. `profiles/code.md` supplies the 13 registration items; `profiles/typescript.md` §§1–4, 6–7, 9–10 are frozen stage-1 normative text (§17), with §5 excluded.

| M1.1 registration item (exact item name) | Concrete profile/contract answer |
| --- | --- |
| Language and grammar revision | TS §1: ECMA-262 2026 HTML digest, profile authority for TS-only points, TypeScript 6.0.3 oracle integrity pin, Unicode 17.0.0. Formal Ecma PDF not retrieved (TSOD-11 historical follow-up); a grammar revision and digest already exist. This is a documented source-pin limitation, not an unspecified lexer rule. |
| Tokenizer rules | TS §§3–4 define scanning/classes and context, independent of TypeScript lexer enums. |
| Scope resolution | TS §14: none; lexical normalized channel. |
| Encodings | TS §14 -> extraction contract §3: UTF-8; reject BOM/NUL; lone CR allowed by TS §3.1. |
| Parser error behavior | TS §7 closed lexical codes/offsets, no parser/repair; syntactically invalid but lexically valid input accepted. |
| Comments/docstrings | TS §4.3: line and non-nesting block comments dropped, JSDoc included as trivia. |
| Significant whitespace | TS §3.1/§4.9/§4.10: exact line-terminator set, context effects, no ASI tokens. |
| Macro/generated code | No macros; TS §2 file-selection rules decide generated/declaration/minified exclusions. |
| Token serialization | TS §6 -> extraction contract §6; normalized `;` exclusions explicit. |
| Hash parameters | Extraction contract §7 + TS §10: length-prefix framing, profile/version/channel/k, SHA-256 first8 big-endian. |
| Window sizes | TS §10: k=5/window=4, contract bounds; configuration bytes and digests fixed. |
| Minimum-selection tie-breaking | Extraction contract §8 via TS §14: rightmost minimum, partial windows, distinct selected positions. |
| Coordinate units | TS §14/contract §3: original half-open UTF-8 bytes. |
| Raw strings | No additional Go/Rust-style raw-string class; TS §4.6 strings and §4.8 template literals state JS forms and escapes. |
| Nested comments | TS §4.3: not nested; first closing delimiter ends the comment. |
| Shebang | TS §4.3: hashbang only at offset 0; later hashbang rejected. |
| BOM / CRLF | BOM rejected by inherited precheck; TS §3.1 CRLF one line terminator, bytes retained. |
| ASI | TS §4.10: no inserted semicolons; literal `;` retained exact/dropped normalized. |
| Regex vs division | TS §4.9 deterministic exprEnd/header/arrow/newline rules and documented departures. |
| Template literals | TS §4.8 nested substitution/token classes and errors. |
| JSX/TSX | TS §2: `.tsx`/`.jsx` deferred; §5 draft fork, §5.5 known generic limitation; §17 excludes it from freeze. JSX in `.js` explicitly deferred, including known D-16 punctuator misread. Coverage of the boundary is present; supported TSX is not asserted. |
| `.d.ts`/generated/minified exclusions | TS §2: declaration suffix patterns; first 2048 bytes contain marker; minified suffixes or line >4096 bytes; selector, not extractor. Thresholds are decided experimental values, not TBDs/calibrated selection accuracy. |

No undecided stage-1 extraction rule found in this recount. The old “pending owner confirmation” paragraphs are superseded by the profile status line and ROADMAP's 2026-11-23 confirmation of stage-1 draft decisions; no new decision inferred. Missing evidence for **stage-1 TS.1**: none. Deferral does not approve §5 or demonstrate TSX corpus rejection rates.

## TS.2: exact criterion and clause recount

> Hand-derived (definition) vectors cover the M1.2 classes plus the TS.1 classes

| Clause/class | Concrete committed evidence |
| --- | --- |
| Hand-derived | `harness/vector_sources.py` explicitly lists token classes/texts and error codes/offsets; `harness/build_vectors.py` locates spans and computes arithmetic, without lexing. `ts.json` 77/77 and `limits-ts.json` 3/3 have `derivation: hand`. Existing checker re-lexes against independent source lists and recomputes values. This recount additionally independently recomputed every stage-1 k-gram/window/fingerprint and token span. |
| Empty | `ts-empty` |
| Below `k+w-1` | `ts-short` (3<8); `ts-exact-k` (5<8, partial window). |
| Unicode | `ts-unicode-boundary`, `ts-unicode-escape-ident` |
| Malformed | `ts-err-invalid-utf8`, `ts-err-unclosed`, literal/comment errors with offsets |
| Repeated | `ts-repeated` |
| Equal-minimum ties | `ts-repeated`; 22 tie windows counted by existing checker. |
| CRLF/BOM | `ts-format-b` CRLF; `ts-err-bom` expected rejection. |
| ASI | `ts-no-asi`, `ts-semi-a/b`, newline-prefix cases |
| Regex vs division | `ts-regex-after-header`, `ts-division-after-paren`, object/class/arrow/departure cases |
| Template literals | `ts-template-nested`, `ts-template-escapes`, unterminated template/substitution errors |
| JSX/TSX boundary for stage 1 | `ts-err-jsx-in-js` and `ts-jsx-selfclosing-in-js` explicitly expose errors/known misread. `tsx.json` has 33 draft examples, but contributes no stage-1 conformance claim. |
| `.d.ts`/generated/minified exclusions | **Missing expected selection/exclusion fixtures.** TS vectors pass input bytes/config only, not filenames or an expected excluded decision. No vector carries declaration suffixes, generated-marker position boundaries or minified suffix/line-length selection outcomes. The TypeScript library cross-check includes declaration files; it is a lexer oracle corpus, not an exclusion decision fixture. |

**Why not eligible:** I read “plus the TS.1 classes” literally to include the named exclusion cases, not just lexer constructs. This is an explicit criterion interpretation, not a discovered lexer defect. The repository deliberately assigns selection to TW-01/TW-03, but the gate does not explicitly exempt it. The evidence supports the narrower **stage-1 lexical class subset**, not the complete wording. Before unqualified closure, resolve that coverage gap or record an explicit criterion scope decision; do not infer exemption from TS.3.

**Pairing observation, separately:** M1.2 also says each positive has a paired rejection, whereas TS.2 explicitly imports its *classes*. Across frozen TS files there are **47 positives**: **45** point to a stage-1 error vector, but `ts-html-comment -> tsx-err-html-comment` and `ts-type-assertion -> tsx-err-ts-type-assertion` point into deferred `tsx.json`. Globally all pointers resolve to error fixtures, so the shipped checker's pairing check passes. Those two errors must not be presented as stage-1 rejection requirements. If the intended gate imports the entire M1.2 pairing rule within stage 1, these are an additional gap; I have not silently imposed that stronger reading as the primary blocker.

## TXT.1: exact criterion and clause recount

> A text extraction profile answers every item of lane 09's “How the extraction contract could host a text profile”, with 0 TBDs. Items: format front end (`plain`/`markdown`, pinned CommonMark version); BOM policy; the fold over pinned Unicode 17.0.0 files (NFKC, full case folding, delete Default_Ignorable_Code_Point, White_Space mapping, optional confusable channel pinned by `confusables.txt` digest); token rule, including scripts written without spaces; `exact` and `folded` channels with no stemming or stop words; span mapping of every folded token to its original half-open UTF-8 byte span; k and w in the config bytes; a closed error list; and a hash-framing string

All locations here are in `profiles/text.md`, checked against the actual rules, not only its §16 checklist.

| Exact listed clause | Answer |
| --- | --- |
| format front end (`plain`/`markdown`, pinned CommonMark version) | §2: plain has no masking; Markdown is a separate profile. §5 pins CommonMark 0.31.2 as a reference with explicit masking deviations. Status/§17 exclude unfrozen `text-markdown` draft-2 from stage 1. |
| BOM policy | §3: accepted; Default_Ignorable; bytes/spans remain original. |
| fold over pinned Unicode 17.0.0 files | §4 names six files and SHA-256 digests; committed derived table digest `49eb0304...53f4`. §8 specifies NFD -> NFKC_CF -> NFC -> separator deletion -> NFC. |
| NFKC, full case folding, delete Default_Ignorable_Code_Point | §8 explicitly defines NFKC_CF and treatment of ignorables, expansion and Cherokee differences. |
| White_Space mapping | §6: all White_Space are separators; tokenization preserves original positions. |
| optional confusable channel pinned by confusables.txt digest | §4 digest `091c7f82...22a`; §8 single-pass skeleton after fold. |
| token rule, including scripts written without spaces | §§6–7: W/C/I/S precedence; ideograph-by-ideograph; Kana runs; Thai/Lao/Khmer/Myanmar runs with explicit no-dictionary limit. |
| exact and folded, no stemming or stop words | §8 same tokens/spans, three named channels; §§2/13 explicitly exclude stemming/stop words. |
| span mapping to original half-open UTF-8 byte span | §§1/7/8/10: all channels share original token spans, length-changing fold does not replace coordinates. |
| k and w in config bytes | §11 exact canonical config, k=8/window=8, fixed digest. |
| closed error list | §3: unsupported-config, input-too-large, invalid-utf8, nul; specified precedence/offsets. BOM is accepted, not an omitted error. |
| hash-framing string | §9: `traceweave/text-kgram/draft-1`, length-prefixed profile/version/channel/k and word/value pairs; hash defined. |

No TBD in the stage-1 rules found. Missing evidence for **stage-1 TXT.1**: none. Markdown re-review/record-layout questions in §§17–18 remain outside this verdict. Proposed UC-8 owner acceptance (TXT.0) is explicitly not a prerequisite of TXT.1 under the roadmap override.

## TXT.2: exact criterion and clause recount

> Hand-derived (definition) vectors (`derivation: hand`), at least 1 for each class: empty; below `k+w-1`; BOM; CRLF; NFD input; NFKC expansion (U+FB01); case-fold expansion (U+00DF); zero-width inside a word; listed confusable; other Default_Ignorable; Markdown syntax; invalid UTF-8; NUL. Each vector gives expected tokens and original byte spans, and each positive vector has a paired rejection vector

Every example below is in the frozen `test-vectors/extraction-text/text-plain.json` except the additional size-boundary cases in `limits-text.json`; no `md-*` fixture is needed to cover these classes for stage 1.

| Exact class/clause | Evidence |
| --- | --- |
| hand-derived / derivation: hand | `harness/build_vectors.py` lists expected texts/folded/skeleton values and errors; it explicitly does not segment/fold/skeletonize. All 55 plain +3 limits carry `hand`. Checker independently derives from input/table; this recount independently rechecks spans and all arithmetic. |
| empty | `plain-empty` |
| below k+w-1 | `plain-short`, `plain-below-kw1` (12<15), `plain-at-kw1` boundary |
| BOM | `plain-bom`, first token starts at original offset 3 |
| CRLF | `plain-crlf` |
| NFD input | `plain-nfd`, `plain-combining-b` |
| NFKC expansion U+FB01 | `plain-nfkc-ligature`: ﬁnal -> final |
| case-fold expansion U+00DF | `plain-casefold-expansion`: Straße -> strasse |
| zero-width inside a word | `plain-zero-width` |
| listed confusable | `plain-confusable-cyrillic`, paired Latin reference |
| other Default_Ignorable | `plain-other-ignorable`, `plain-bidi` |
| Markdown syntax | `plain-md-syntax`: markup bytes treated as plain content (URLs/tag/entity names become words). This satisfies the input class without asserting masking or Markdown conformance. |
| invalid UTF-8 | `plain-err-lone-continuation`, overlong/surrogate/truncated/above-max errors |
| NUL | `plain-err-nul`, `plain-err-reflow-nul`; error precedence also tested |
| each vector gives expected tokens/original spans | Every non-error vector has token class/text/span plus channel values/hashes; error vectors instead have expected code/offset and no partial tokens, as the contract requires. Independent original-byte slice check passes for all 628 positive-fixture tokens. |
| each positive has paired rejection vector | `rejections.json` has 70 total mutations; every one of the **47 stage-1 positives** has a source-vector-keyed rejection, independently recounted. Existing checker requires the mutated answer to fail at its declared layer; all 70 pass rejection checking (66/66 positives across plain+limits+deferred Markdown). §12 OD-T12 and README “rejections.json is the checker's self-test” explicitly define this convention. Two additional input-rejected pairs in text-plain.json link `plain-reflow-a` to NUL/invalid-UTF8 inputs; this is not a claim that all 47 positives have distinct rejected-input partners. |

Missing evidence for the **stage-1 TXT.2 criterion under its documented rejection-vector convention**: none. If “paired rejection” were reinterpreted to require a rejected *input for each positive*, existing mutations would not establish that stronger statement; the documented convention is result-rejection fixtures, and no such reinterpretation was applied here.

## Checks and reproducibility

Ran with the existing pinned Python environment and bytecode writing disabled, no downloads or experiments:

- `python -B -I test-vectors/extraction-typescript/check_vectors.py`: exit 0, **77 TS +3 limits +33 deferred TSX**; 19 invalid configs rejected; 28/28 corruption self-tests, 15/15 wrong lexers rejected. TSX checks are draft fixture consistency only.
- `python -B -I test-vectors/extraction-text/check_text_vectors.py`: exit 0, **55 plain +3 limits +21 deferred Markdown**; 13 invalid configs rejected, 2 boundary configs accepted; 70/70 result rejections, 14/14 wrong implementations, 60/60 canonical plain records and 12/12 record corruptions. Markdown checks are draft fixture consistency only.
- `python -B -I research/drafts/image-mark-finding-aid/check_finding_aid.py`: exit 0, **5 valid /24 invalid /17 required-field deletions rejected**.
- Standalone read-only `profile-criterion-recount/check_arithmetic.py` reads only `git show <revision>:<path>`, imports no repository checker or builder, and verifies all frozen-stage-1 token byte slices, length-prefixed SHA-256 k-grams, rightmost-minimum windows and deduplicated fingerprints: **1,283 token spans, 1,908 k-grams, 521 fingerprints**, zero mismatches; details in `profile-criterion-recount/arithmetic-results.json`. This rechecks arithmetic over committed judgments; it is not a new lexer, mutation experiment or detection run. During script preparation an incorrect text domain spelling was corrected to the profile §9 value; the final recorded execution passes.

No full validator rerun was necessary to answer these five criteria; the relevant checkers passed. The original recount changed no repository files, gates, counts or refs and ran no builder regeneration, experiment, corpus acquisition, service contact, push or sublane. This portable evidence copy preserves that dated verdict; subsequent TS.2 fixture repairs require separate independent review. M5.3/public-history work was not duplicated. Queue reconciliation and IMGF.1 edits remain deferred to ownership handoff.

Concurrent-work snapshot check: HEAD advanced to `284ce4e1f3b2daf9eabd7700cabdc4b10865310d` during this read-only audit; all 42 manifest evidence blobs remain identical to the reviewed revision. Working tree was clean at completion.

Portable copy prepared from base `1c8f09a62faabfa2304b14315ee80d1b324304d7`. This record leaves IMG.5/TS.1/TXT.1/TXT.2 eligible only in the stated scopes, and TS.2 held. It does not change gate statuses or counts. The arithmetic checker reads current local files and verifies their identities against the recorded manifest before recomputation; it needs no historical checkout or external source.
