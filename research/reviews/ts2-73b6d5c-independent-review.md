# Independent review of TS.2 evidence and five criterion recommendations

Reviewed 2026-11-26: exact commit **`73b6d5cfd116a1d13a2463638e4e2448280db958`**, parent `9eab88fe34eb36606c9d958446fda26eb8649b3f`. Review performed in an isolated worktree initially clean at that exact commit. This review did not author the selection adapter, fixtures, supplemental partners or portable recount. Only this new review record is changed by the review lane.

**Verdict: no blocking findings. Recommend lifting the previous TS.2 evidence hold for frozen stage-1 `ts-tokens` draft-2.** The missing selection classes and the stronger within-stage input-rejection pairing requirement now have evidence. This is a scoped recommendation, not a gate/status/count edit, implementation agreement result, or approval of deferred profiles.

## Exact criteria and eligibility

Criterion wording below is from [ROADMAP.md](../../ROADMAP.md) at the reviewed commit. The [portable recount](img-ts-txt-criterion-recount.md) remains a historical review of older evidence; its TS.2 hold is superseded only within the scope stated here.

| Gate | Criterion, without scope deletions | Recommendation at the reviewed commit |
| --- | --- | --- |
| IMG.5 | IMGF and IMG results fit the lane-08 container fields, or a schema change goes through CONTRIBUTING | **Eligible through the reviewed draft schema-change alternative.** IMGF mapping plus the profile-specific IMG finding-aid schema accommodate the fields. No normative promotion, publication, origin proof or C2PA interoperability is inferred. |
| TS.1 | Profile covers the M1.1 list plus ASI, regex vs division, template literals, JSX/TSX, and `.d.ts`/generated/minified exclusions | **Eligible for frozen stage-1 `ts-tokens` draft-2.** JSX/TSX is covered as an explicit deferred boundary, including the `.js` self-closing misread; this recommendation grants no TSX support. |
| TS.2 | Hand-derived (definition) vectors cover the M1.2 classes plus the TS.1 classes | **Eligible for frozen stage-1 `ts-tokens` draft-2**, including selection classes and 47/47 within-stage rejected-input partners. The criterion is not reduced to lexical classes. Deferred JSX/TSX boundary judgments are included; deferred TSX extraction conformance is not established. |
| TXT.1 | A text extraction profile answers every item of lane 09's “How the extraction contract could host a text profile”, with 0 TBDs. Items: format front end (`plain`/`markdown`, pinned CommonMark version); BOM policy; the fold over pinned Unicode 17.0.0 files (NFKC, full case folding, delete Default_Ignorable_Code_Point, White_Space mapping, optional confusable channel pinned by `confusables.txt` digest); token rule, including scripts written without spaces; `exact` and `folded` channels with no stemming or stop words; span mapping of every folded token to its original half-open UTF-8 byte span; k and w in the config bytes; a closed error list; and a hash-framing string | **Eligible for frozen stage-1 `text-plain` draft-1.** The profile states the plain/Markdown split and CommonMark 0.31.2 reference, but Markdown masking remains unfrozen and deferred. |
| TXT.2 | Hand-derived (definition) vectors (`derivation: hand`), at least 1 for each class: empty; below `k+w-1`; BOM; CRLF; NFD input; NFKC expansion (U+FB01); case-fold expansion (U+00DF); zero-width inside a word; listed confusable; other Default_Ignorable; Markdown syntax; invalid UTF-8; NUL. Each vector gives expected tokens and original byte spans, and each positive vector has a paired rejection vector | **Eligible for frozen stage-1 `text-plain` draft-1 under its documented result-rejection convention.** All 13 input classes occur without relying on deferred Markdown fixtures. All 47 stage-1 positives have mutated-result rejection partners; this does not mean 47 rejected-input partners or Markdown conformance. |

These scope qualifications must travel with the recommendations. If a gate status cannot express them, this record does not authorize an unqualified closure that implies stage-2 support. The roadmap's recorded owner confirmation of the stage-1 decisions supplies the staging context; the review does not amend criterion wording.

## Selection contract, hand derivation and oracle independence

Read [TypeScript profile §2](../../profiles/typescript.md#2-inputs-in-scope-and-why-two-profiles), all 55 [selection fixtures](../../test-vectors/extraction-typescript/selection-decisions.json), [adapter](../../test-vectors/extraction-typescript/check_selection.py), [author resolution](ts2-exclusion-pairing-resolution.md), and the added contract tests. The selector is test tooling, not the extractor or a product implementation. Filename selection and deferral do not become lexical errors. An `extract` judgment denotes selection eligibility even when those particular bytes would fail lexing.

Independently expanded every `inputParts` sequence and recomputed the decision from the frozen text. The review oracle used case-sensitive filename glob matching, byte positions and marker lengths, and a character walk accumulating UTF-8 line byte lengths. It did not call the adapter's `content` or `decision` to derive expectations, use the adapter's regular-expression line splitting, or use a lexer/compiler to generate expected decisions. Result: **55/55 agree: 31 extract, 19 exclude, 5 defer.** Manual examination also checked the rationales against the predicates:

| Contract clause | Verified boundary evidence |
| --- | --- |
| Declaration exclusions | `.d.ts`, `.d.mts`, `.d.cts`, `*.d.*.ts`, including multiple intermediate components. Case and near-pattern counterexamples remain selected; the `.d.tsx` near-pattern is deferred. |
| First 2048 bytes contain either generated marker | Both literal markers at start, ending at 2048, crossing to 2049 and starting after 2048. Case/partial near misses remain selected. A 1024-character `é` prefix occupies 2048 bytes and leaves the following marker outside the window. |
| Minified suffixes | All three specified suffixes exclude. `.min.ts`, uppercase, extended suffix and `minimum` cases do not acquire an unstated exclusion. |
| Any line longer than 4096 bytes | 4096/4097 and multibyte boundaries agree. LF, CR, CRLF, LS and PS separate at-limit lines, while an over-limit second line still excludes. |
| Deferred stage | `.tsx`, `.jsx`, known JSX in `.js`, including self-closing D-16, defer. A TS type assertion does not acquire JSX status by guessing from angle brackets. |

The expected decisions and supplemental errors are literal hand judgments, not output emitted by the adapter. The existing lexical source lists are separate from `tslex.py`; the arithmetic builder locates declared tokens and computes downstream values rather than choosing token classes. This is the repository's hand-derivation definition, not a claim of two independently implemented selectors or lexers. The separate review oracle supplies an additional check against a shared author misunderstanding of selection rules.

## Mutation sensitivity

The shipped checker reports **24/24 wrong selectors rejected**. The review separately evaluated each mutant on every fixture, using the independently verified expectations. **Every mutant has at least one actual decision disagreement**, so no mutant's sensitivity depends solely on an exception or missing fixture assertion. Counts below are decision disagreements, not exception counts.

| Wrong selector | Disagreements | Example witness |
| --- | ---: | --- |
| `no-declaration` | 5 | `declaration.d.ts` |
| `no-d-mts` | 1 | `declaration.d.mts` |
| `no-d-cts` | 1 | `declaration.d.cts` |
| `broad-declaration` | 2 | `near-module.d.css.mts` |
| `no-declaration-pattern` | 2 | `declaration.d.css.ts` |
| `window2047` | 2 | `generated-end2048` |
| `window2049` | 2 | `generated-end2049` |
| `character-window` | 2 | `generated-unicode-boundary` |
| `all-file-marker` | 6 | `generated-end2049` |
| `no-generated` | 4 | `generated-start` |
| `no-at-generated` | 2 | `generated-start` |
| `no-do-not-edit` | 2 | `do-not-edit-start` |
| `casefold-marker` | 2 | `near-marker-@Generated` |
| `partial-marker` | 4 | `generated-end2049` |
| `no-minified-suffix` | 3 | `minified.min.js` |
| `broad-minified-suffix` | 3 | `near-minified-m.min.ts` |
| `lf-only` | 4 | `split-cr` |
| `no-lf` | 2 | `split-lf` |
| `no-ls` | 1 | `split-ls` |
| `no-ps` | 1 | `split-ps` |
| `character-lines` | 1 | `utf8-line4097` |
| `inclusive-line` | 7 | `line4096` |
| `no-line-limit` | 7 | `line4097` |
| `no-defer` | 5 | `near-module.d.tsx` |

`broad-declaration` additionally throws for the `.d.tsx` fixture because it invents an exclusion/deferral overlap. That exception is not counted in the two disagreements above. The 14 committed evidence-corruption subcases also passed: wrong decisions, removed boundary, duplicate ID, source digest mismatch, wrong rejection code/offset, removed override and deferred partner all fail cleanly. Mutation coverage establishes sensitivity to these rule choices, not exhaustive selector correctness.

## Paired rejection semantics

Independently walked all positives in `ts.json` and `limits-ts.json` and resolved the supplemental map against errors in those same stage-1 files plus the two new inputs. **46 + 1 = 47 positives; 45 original in-stage partners + 2 supplemental overrides = 47/47.** No deferred TSX error contributes to this count. The original historical pointers remain unchanged.

| Accepted source | Supplemental partner relation | Hand error checked |
| --- | --- | --- |
| `ts-html-comment` | Exact original UTF-8 bytes followed by `/*` | `unterminated-comment`, byte offset **12**, the appended opener |
| `ts-type-assertion` | Exact original UTF-8 bytes followed by `)` | `unbalanced-delimiter`, byte offset **33**, the appended unmatched closer |

The base64 and text forms equal those byte concatenations. The block comment has no closing delimiter; the second base input ends with no open delimiter for the appended closer. Both expected errors follow the frozen rules and are re-lexed by the existing checker. The adapter requires both override keys, no unused supplemental errors, exact suffix relationships, exact codes/offsets, and stage-1 partners. This supports even the stronger reading importing M1.2's within-stage input-rejection pairing obligation into TS.2, although TS.2 expressly imports its classes.

Text pairing has a different documented meaning ([profile OD-T12](../../profiles/text.md#15-decisions), vector README and checker): **47/47 stage-1 positives have source-keyed result mutations that the checker rejects at a declared layer**. Two additional rejected-input relations do not convert that into a per-positive rejected-input guarantee. Error vectors specify code/offset rather than partial tokens. TS selection decisions are not counted as extraction positives requiring fabricated lexical rejection partners.

## Remaining gate evidence and preservation

For TS.1, checked the M1.1 registration map against the profile and inherited contract: grammar/Unicode authority, tokenization, no scope resolution, encoding/prechecks, closed lexical errors/no repair, comment handling, whitespace/ASI, generated-file selection, serialization, hash framing, k/window, rightmost ties and original byte coordinates. Raw strings/templates, non-nesting comments, shebang, BOM/CRLF and regex/division are decided. The seven M1.2 classes remain represented by empty/short, Unicode, malformed, repeated/tie and CRLF/BOM fixtures; ASI, regex context and nested templates have explicit cases. The newly added selection evidence closes the earlier TS.2 omission without exempting the TS.1 selection classes.

For TXT.1, checked the plain/Markdown split and pinned CommonMark reference; BOM acceptance; six Unicode source pins and derived-table digest; NFKC_CF/full folding/ignorable deletion and whitespace separation; optional single-pass confusable skeleton; W/C/I/S tokenization including scripts without spaces; exact/folded values without stemming/stop words; original UTF-8 spans; k/window configuration; closed errors and hash framing. There is no stage-1 TBD. TXT.2's 13 classes are independently represented by `plain-empty`, `plain-below-kw1`, `plain-bom`, `plain-crlf`, `plain-nfd`, `plain-nfkc-ligature`, `plain-casefold-expansion`, `plain-zero-width`, `plain-confusable-cyrillic`, `plain-other-ignorable`, `plain-md-syntax`, `plain-err-lone-continuation` and `plain-err-nul`. Markdown syntax here is processed as plain text, not masked.

For IMG.5, checked the IMGF §8.3 mapping and the IMG finding-aid schema route against CONTRIBUTING and the existing non-author review's final resolution. Artifact/profile/region/raw evidence/outcome/confidence fields and the six additions (model digests, statistic/n, threshold basis/search scope, key/derivation reference, embedding quality and tested-bit positions) have homes. Schema/version/examples/negative cases/checker and reviewed rationale travel together. Existing checks enforce the non-origin boundary and separate registration pointer. This review does not repeat the separate image experiment or publication lane.

Preservation checks compared actual Git blobs and SHA-256 values, not just metadata labels:

- Both new sidecars' five source digests match the actual files at their declared source revision **`1c8f09a62faabfa2304b14315ee80d1b324304d7`** and at the reviewed commit. The shipped adapter checks current source hashes; the review additionally verified the historical revision binding.
- All six TS §17 frozen artifacts (including negative configs and shared Unicode table), deferred TSX fixtures/config, all `profiles/`, `spec/`, `schemas/` and text fixture files are unchanged from the source revision and the recount revision `24bb4b8483dc86966cb7c8277130bb816b0c6b3f`. No output, configuration digest or profile version changed.
- **39/42** entries in the old recount manifest still match current Git blobs and SHA-256. The three expected differences are `ROADMAP.md` (the intervening M5.3 closure in the source baseline), the TS README and `tools/validate.py` (this evidence addition). The manifest is historical, not an exact whole-tree manifest for `73b6d5c`. The five gate criteria themselves are unchanged.
- The reviewed commit changes exactly seven author files: resolution, TS README, selector checker, two sidecars, contract tests and validator integration. This review changes only this record. No gate/count edits are made here.

## Executed checks and limits

Used the already installed sibling spec virtual environment: Python **3.12.14**, `jsonschema 4.23.0`, `attrs 26.1.0`, `jsonschema-specifications 2025.9.1`, `referencing 0.37.0`, `rfc3339-validator 0.1.4`, `rpds-py 2026.9.1`, matching the existing requirements pins. No installation or download. Commands below use `python` to denote that existing interpreter; these are local results on the exact reviewed commit, not remote run claims.

| Command / check | Result |
| --- | --- |
| `python -B tools/validate.py` | Exit 0; schemas/examples/digests/framing/links and integrated vector checkers pass, including TS selection. |
| `python -B tools/validate.py --links-all` | Exit 0; all local Markdown links pass. |
| `python -B -m unittest discover -s tests -v` | **29/29 pass**, including all 14 new corruption subcases. |
| `python -B -I test-vectors/extraction-typescript/check_selection.py` | **55 decisions, 24/24 wrong selectors, 47/47 pairs, 2 supplemental inputs**; exit 0. |
| `python -B -I test-vectors/extraction-typescript/check_vectors.py` | 77 TS + 3 limits + 33 deferred TSX; 19/19 config negatives; **28/28 corruptions, 15/15 wrong lexers** rejected; exit 0. |
| `python -B -I test-vectors/extraction-text/check_text_vectors.py` | 55 plain + 3 limits + 21 deferred Markdown; **70/70 result mutations, 14/14 wrong implementations, 60/60 records, 12/12 record corruptions** checked; exit 0. |
| `python -B -I research/drafts/image-mark-finding-aid/check_finding_aid.py` | **5 valid, 24 invalid, 17/17 required-field deletions** checked; exit 0. |
| Portable `profile-criterion-recount/check_arithmetic.py` | Parsed output equals committed `arithmetic-results.json`: **1,283 token spans, 1,908 k-grams, 521 fingerprints**. Its unchanged 45/47 original TS pairing count is historical; the sidecar supplies the remaining two. |
| Independent selection and pairing audits described above | 55/55 decisions, actual decision witnesses for all 24 mutants, 47/47 stage-1 pairs, exact supplemental byte relations/offsets; pass. |
| `python -B tools/check_hygiene.py`; `git diff --check` | Pass. |

No blocking or required-fix finding remains in this review scope. Evidence limits remain explicit: the selector adapter accepts basenames and UTF-8 fixture strings, uses declared `jsxKnown` knowledge rather than detecting JSX, and deliberately avoids unspecified exclusion/deferral overlaps, unsupported filenames and directory policies. The frozen profile delegates path rules to TW-01/TW-03. These fixtures neither invent precedence nor demonstrate a complete production selector. Metadata and finite mutation tests alone cannot prove historical authorship or exhaustive correctness.

TSX extraction and Markdown masking remain deferred. Their existing checker runs test draft consistency only. No raw upstream Unicode re-derivation, compiler corpus cross-check, builder regeneration, full study, services, M3 evaluation, downloads, push, subagents, image-tree changes or publication-tree changes were performed. No downstream implementation result substitutes for the criterion evidence. The sole deliverable is this committed independent review record.
