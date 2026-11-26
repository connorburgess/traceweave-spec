# Combined profile closure integration

Recorded 2026-11-26. Merges exact reviewed branch tip **`631e71e22994dc5a8e16f2f6eee73ed94b1e54cd`** into private `roadmap-v2` at **`c402191166e9224d54d819433112b8ff68bc579d`**, preserving both branch histories. Exact author evidence **`73b6d5cfd116a1d13a2463638e4e2448280db958`** was independently reviewed in **`ca8fb4f51df75250cd82ea4e6a86b0f3e48aa9ae`** ([review](ts2-73b6d5c-independent-review.md)); the [five-gate closure](img-ts-txt-five-gate-closure-73b6d5c.md) supplies IMG.5, TS.1/TS.2 and TXT.1/TXT.2. The preceding [IMGF.1 integration](imgf1-integration-303b966.md) and [scoped closure](imgf1-gate-closure-db2848c.md) remain intact.

## Counts and evidence reconciliation

Independent parsing of individual gate rows, normalizing Markdown emphasis and treating missing/planned/draft-only statuses as open, gives:

| Group | Total | Met | Negative-result | Open |
| --- | ---: | ---: | ---: | ---: |
| Core M0–M5 | 47 | 34 | 0 | 13 |
| Later profiles, EXT and RC | 55 | 27 | 2 | 26 |

The met-ID sets exactly equal the summary-table lists. All 47 core rows are byte-identical to the first parent. The sole extension row changes against that parent are IMG.5, TS.1, TS.2, TXT.1 and TXT.2, each open to met; criterion text before status annotations is unchanged. IMGF.1 remains met with its research-only evidence. TXT.4 and TXT.8 remain the two negative results. Core open IDs remain M2E.1–M2E.7 and M3.1–M3.6.

Count/claim conflicts combine both closure sets rather than choosing either branch's older total. README-007 quotes 27/55 and cites the exact current ROADMAP row plus both reviewed closure sets. No other parsed claim changes. All 77 IDs/order, 59 excluded source lines and the five exclusion rules are unchanged. The Markdown count sentence equals the JSON sentence; all exact evidence locators validate. Current scope text is reconciled; historical snapshots and review records retain their dated counts and holds.

## Preservation and merged checks

Actual Git comparisons confirm unchanged frozen spec/profile/schema files, TS/TSX frozen vector bytes and text fixtures, draft-2 image profile/protocol and the whole frozen image-fingerprint tree against `1c8f09a`. The incoming independent TS review, closure, historical recount/manifest/results are byte-identical to `631e71e`; the already integrated image review/closure and draft-3 conformance suite are unchanged. New selection evidence is supplemental and does not relabel frozen configurations or outputs.

Local checks on the integrated tree all passed using already installed environments, without dependency acquisition:

- Repository validator, **29/29 unit tests**, all local Markdown links, exact README claim map and tree/history hygiene.
- Explicit TS selection checker: **55 decisions, 24/24 wrong selectors rejected, 47/47 in-stage rejection pairs and two supplemental inputs**. The repository test includes all 14 evidence-corruption subcases.
- TS checker: **77 TS, three limits, 33 deferred TSX**, 19 config negatives; 28 corruptions and 15 wrong lexers rejected. Deferred fixture consistency is not TSX support.
- Text checker: **55 plain, three limits, 21 deferred Markdown**, 70 result mutations, 14 wrong implementations, 60 records and 12 record corruptions. Result pairing is not per-positive rejected-input pairing.
- IMG.5 finding-aid checker: **five valid, 24 invalid and 17 required-field deletions**.
- Portable arithmetic recount output equals the committed historical JSON. Its older 45/47 original TS pair count remains historical; supplemental evidence supplies the other two.
- Existing pinned Pillow target under OS network denial: **15/15 finite draft-3 normalization cases**, both resize mutations and the exact grey half-tie mutation detected; all four checker self-tests pass.

Whitespace and staged-state checks complete the merge verification. These are local checks, not remote workflow or downstream implementation results. Publication preparation is separate and does not authorize a push or release.

## Scope retained

IMG.5 closes draft-schema accommodation; TS and text close only frozen stage-1 `ts-tokens` and `text-plain`. JSX knowledge is declared fixture data, not a detector or complete production selector. No exclusion/deferral overlap precedence is invented. TSX extraction and Markdown masking remain deferred. IMGF.1 remains a research arithmetic contract with finite single-host evidence and the recorded upstream C-source limitation; no universal equivalence or normative promotion follows. IMGF.5/IMGF.6 and M3 remain open/held. No held evaluation, corpus acquisition, feature expansion or release approval is included.
