# Five scoped profile closures and branch progress recount

Recorded 2026-11-26 following the instruction to record **IMG.5, TS.1, TS.2, TXT.1 and TXT.2** met in this isolated branch. Exact evidence reviewed: **`73b6d5cfd116a1d13a2463638e4e2448280db958`**. Independent review: **`ca8fb4f51df75250cd82ea4e6a86b0f3e48aa9ae`**, [review record](ts2-73b6d5c-independent-review.md). The latter is the pre-closure branch baseline. It found no blocking findings and recommended the five closures only in the scopes below. The [older portable recount](img-ts-txt-criterion-recount.md) and its manifest/results remain unchanged historical evidence; this closure does not rewrite its earlier TS.2 hold.

## Closure evidence and binding scopes

All five ROADMAP criteria are preserved byte for byte before their status annotations. Each status cites the exact evidence commit, independent review and this closure record. These are evidence/documentation closures, not release approval, normative promotion, product conformance or detection-rate claims.

| Gate recorded met | Precise evidence and scope carried into the status |
| --- | --- |
| IMG.5 | **Reviewed draft schema-change route under CONTRIBUTING.** [IMGF profile §8.3](../drafts/extraction-profile-image.md#83-mapping-to-the-lane-08-shared-record) maps shared fields; [finding-aid proposal](../drafts/image-mark-finding-aid.md) and [schema](../../schemas/image-mark-finding-aid.schema.json) host the IMG fields plus model digests, statistic/n, threshold basis/search scope, key/derivation reference, embedding quality and tested-bit positions. Versioned schema, rationale, fixtures and integrated checker form the reviewed package; [earlier review and final resolution](media-c2pa-av-review.md) remain supporting evidence. **5 valid, 24 invalid, 17/17 field deletions** checked. This closes draft accommodation only, not origin/authorship proof, C2PA interoperability, publication or normative promotion. |
| TS.1 | **Frozen stage-1 `ts-tokens` draft-2.** [Profile](../../profiles/typescript.md) and [extraction contract](../../spec/extraction.md) answer the M1.1 registration list, ASI, regex/division, templates and declaration/generated/minified selection. JSX/TSX is explicitly covered as a deferred boundary, including known D-16 self-closing JSX in `.js`; it is not approved extraction support. |
| TS.2 | **Frozen stage-1 `ts-tokens` draft-2, including the TS.1 selection classes and stronger in-stage input-rejection pairing reading.** [Frozen vectors](../../test-vectors/extraction-typescript/ts.json), [limits](../../test-vectors/extraction-typescript/limits-ts.json), [55 hand selection decisions](../../test-vectors/extraction-typescript/selection-decisions.json) and [supplemental rejection map](../../test-vectors/extraction-typescript/stage1-rejection-pairs.json). All seven M1.2 classes and stage-1 additions are represented; **24/24 wrong selectors** have actual decision disagreements; **47/47 positives** have stage-1 rejected-input partners, with the two supplemental malformed suffixes checked at byte offsets 12 and 33. The independent oracle agrees with **31 extract, 19 exclude, 5 defer** decisions. |
| TXT.1 | **Frozen stage-1 `text-plain` draft-1.** [Profile](../../profiles/text.md) answers every listed clause: format split and CommonMark reference, BOM, pinned Unicode fold/ignorables/whitespace/confusables, token rules including scripts without spaces, channels, original spans, k/window, closed errors and hash framing. No stage-1 TBD remains. Markdown masking remains unfrozen and deferred. |
| TXT.2 | **Frozen stage-1 `text-plain` draft-1 under the documented result-rejection convention (OD-T12).** [Plain vectors](../../test-vectors/extraction-text/text-plain.json), [limits](../../test-vectors/extraction-text/limits-text.json) and [result rejections](../../test-vectors/extraction-text/rejections.json) cover all 13 classes and all **47/47 stage-1 positive result-rejection pairs**. `plain-md-syntax` covers Markdown syntax as plain text. This is not a claim of 47 rejected-input partners or Markdown masking conformance. |

**TSX and Markdown remain deferred. No JSX detection or exclusion/deferral overlap precedence is claimed.** `jsxKnown` is declared fixture knowledge, not a detector. Selection fixtures avoid unspecified overlaps, unsupported filename policies and directory rules delegated to TW-01/TW-03. They do not establish a complete production selector. Original frozen profile/vector/configuration bytes and historical cross-profile pointers remain unchanged; the supplemental map supplies in-stage partners without editing them.

## Independent recount against this branch baseline

Counted individual core rows using their status column, and later-profile/EXT/RC rows using their explicit status annotations, normalizing Markdown emphasis rather than assuming one bold-marker spelling. Missing status and planned rows count as open. Summary ID sets were checked against the resulting met-row sets, not used as the source of the recount.

| Group | Baseline `ca8fb4f` | Closure tree |
| --- | --- | --- |
| Core M0–M5 | **47 total: 34 met, 0 negative-result, 13 open** | **Unchanged: 34 met, 0 negative-result, 13 open** |
| Later profiles, EXT and RC | **55 total: 21 met, 2 negative-result, 32 open** | **55 total: 26 met, 2 negative-result, 27 open** |

Exactly the five authorized rows change from open to met. The complete new met set is **TS.1, TS.2, TS.3, PY.1, PY.2, PY.3, IMGF.2, IMGF.3, IMGF.4, IMG.0, IMG.1, IMG.2, IMG.3, IMG.4, IMG.5, TXT.1, TXT.2, TXT.3, TXT.7, RES.1, C2PA.3, SK.1, SK.2, WEB.0, WEB.1, WEB.2**. The two negative-result rows remain **TXT.4 and TXT.8**.

The 27 open later rows are **TS.4, PY.4, IMGF.1, IMGF.5, IMGF.6, TXT.0, TXT.5, TXT.6, BIN.1, BIN.2, RES.2, RES.3, C2PA.1, C2PA.2, SK.3, SK.4, SK.5, STRUCT.1, KEYED.1, WEB.3, WEB.4, WEB.5, WEB.6, EXT.1, RC.1, RC.2, RC.3**. **IMGF.1 remains open in this isolated branch**; the parent owns reconciliation of the parallel image closure. Core open rows remain **M2E.1–M2E.7 and M3.1–M3.6**. No M3 work was performed.

## Dependent claims and preservation

README changes only `21 of 55` to `26 of 55`. README-007 in the JSON/Markdown claim maps carries the revised sentence, exact current ROADMAP summary quotation, independent review evidence and scoped rationale. Approval metadata links this narrow reconciliation. The scope audit adds a current-status paragraph while preserving every dated audit statement and quotation.

Ad hoc comparisons against `ca8fb4f` verified **77 mapped units, identical claim IDs/order, the same five exclusion rules and exact 59 excluded source lines**. Every parsed claim entry except README-007 is unchanged, including README-006's core 34/47 statement. No other current claim quotation references one of the five edited rows. Older 21/55, 29/47 and 33/47 snapshots remain dated evidence. The historical recount/review/manifest/results files are untouched.

All individual gate rows except the five named rows compare byte-identically to baseline, including IMGF.1 and all core statuses. Criteria before status annotations are unchanged. No `spec/`, `profiles/`, schemas, vector/checker/test files, requirement-map JSON, image draft or publication recipe changes are part of this closure. Release/matrix/demo text has no affected numerical quote requiring an edit; their existing behavior and evidence remain unchanged.

## Validation

Validation uses the already installed pinned Python 3.12.14 environment, with bytecode writing disabled. No dependency install or network acquisition is needed. Results are local closure-tree checks, not new implementation runs or remote workflow claims.

All checks passed on the closure tree:

- `python -B tools/validate.py`: schemas, examples, digests, framing, links, requirement/claim maps and integrated vector checkers pass.
- `python -B -m unittest discover -s tests -v`: **29/29 tests pass**, including the 14 TS.2 evidence-corruption subcases.
- `python -B tools/validate.py --links-all`: all local Markdown links pass.
- `python -B tools/check_readme_claims.py`: **77 mapped, 0 unmapped; 59 excluded source lines**.
- `python -B tools/check_hygiene.py` and `git diff --check`: pass.
- Independent ad hoc assertions: baseline and closure row counts, exact five-row status delta, progress-summary met-ID set equality, unchanged core rows, unchanged criterion wording, README's sole numerical substitution, identical inventory/exclusions and all parsed claim entries except README-007: pass.

The full validator invokes the already reviewed TS selection, TS/text extraction and IMG.5 finding-aid checkers; those fixture results are not substituted with a downstream implementation result. No repeat study or native walkthrough was needed for these status/count-only edits.

## Remaining boundaries

The independent review's finite-fixture, source-pin, selector and result-rejection limitations carry forward. No full study, corpus/compiler cross-check, raw Unicode re-derivation, builder regeneration, M3 evaluation, external service, download, push, subagent or parallel-lane integration was performed. Parent reconciliation of separate image/publication work remains outside this branch's closure.
