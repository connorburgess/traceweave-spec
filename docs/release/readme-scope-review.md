# README scope and navigation audit

Author audit for M5.2, 2026-11-26; not the non-author exclusion approval or an independent implementation review. This review checks descriptive/navigation claims against repository contents. Runtime/detection claims need the separate fixtures and recorded reviews in the claim map.

Historical snapshot: the counts and pending-review statements below describe the earlier author audit on 2026-11-26, before independent closure. At the earlier four-gate closure, status was M5.1/M5.2/M5.4/M5.5 met, core 33/47 met and 14 open, on review of exact commit `07c98cad440e3797d0ddc0c4b8c2bfb06a36dbd7` ([re-review](../../research/reviews/m5-readiness-e7e7149-review.md) `1df04f9`; [final confirmation](../../research/reviews/m5-readiness-07c98ca-review.md) `6ded8a3`; [closure recount](../../research/reviews/m5-gate-closure-07c98ca.md)). M5.3 was then open; M3.1–M3.6 remained open/held. The earlier audit's exact evidence quotations are retained below.

Current status after independent M5.3 recipe review: M5.1–M5.5 met, core **34/47 met and 13 open**. M5.3 cites exact recipe commit `24bb4b8483dc86966cb7c8277130bb816b0c6b3f` and [independent review](../../research/reviews/m5-3-recipe-24bb4b8-review.md) `284ce4e`; see the [M5.3 closure recount](../../research/reviews/m5-3-gate-closure-24bb4b8.md). M3.1–M3.6 remain open/held, and no release approval is implied. The preceding IMGF.1 integration recorded 22/55 met, two negative results and 31 open; the combined current count follows.

Prior integrated later-profile snapshot after the [five scoped closures](../../research/reviews/img-ts-txt-five-gate-closure-73b6d5c.md): **27/55 met, 2 negative-result, 26 open**, on exact evidence `73b6d5c` and independent review `ca8fb4f`. IMG.5 closes the reviewed draft schema route; TS.1/TS.2 cover frozen stage-1 `ts-tokens`; TXT.1/TXT.2 cover frozen stage-1 `text-plain` with documented result-rejection pairing. The scoped research-only [IMGF.1 closure](../../research/reviews/imgf1-gate-closure-db2848c.md) is included. TSX/Markdown remain deferred, and the dated audit below is unchanged.

Dated later-profile snapshot after the [SK.3 design-only closure](../../research/reviews/sk3-design-gate-closure-4fa00c7.md): **28/55 met, 2 negative-result, 25 open**, based on exact design `4fa00c7` and independent review `12a1459`. This adds design evidence only, with I1–I4 unresolved and C1 a nonblocking next-design clarification. SK.4/SK.5, owner defaults/namespace decisions and all contact/acquisition/publication holds remain; M3 stays held. Core remains **34/47 met, 13 open**. Prior dated snapshots are retained.

Dated status after the 2026-11-27 [bounded WEB.3 closure](../../research/reviews/web3-bounded-gate-closure-99a1a8b.md): **29/55 met, 2 negative-result, 24 open**; core remains **34/47 met, 13 open**. Only WEB.3 is newly met, on exact Shelf `99a1a8b` and the retained independent review chain. WEB.4/5/6, privacy/native chooser/AT and WEB.6 performance limits remain open; claim inventory/exclusions and all other holds are unchanged.

Current status after the [bounded WEB.4 closure](../../research/reviews/web4-bounded-gate-closure-c0c34cc.md): **30/55 met, 2 negative-result, 23 open**; core **34/47 met,13open**. Only WEB.4 is newly met at Shelf `c0c34cc`, within retained Go/refusal/fixture limits. WEB.5/6 and all other holds remain; inventory/exclusions unchanged.

## Governance and scope

The release label is `0.1.0-draft.1`. The project describes its operation as open and non-commercial; this is a project-scope statement, not an additional restriction on CC BY or Apache licensed reuse. [LICENSE.md](../../LICENSE.md) assigns Markdown prose to CC BY 4.0, schemas/examples/vectors/code/configuration to Apache 2.0, and the two Unicode-derived tables to Unicode License v3. It explicitly limits the licensing split to this repository, rather than content an implementation fingerprints. [CONTRIBUTING.md](../../CONTRIBUTING.md) welcomes independent implementations and evidence-based corrections; [SECURITY.md](../../SECURITY.md) gives the disclosure route. Proposed mechanisms, measured results and normative requirements remain distinct.

[ROADMAP.md](../../ROADMAP.md) is the gate/owner decision ledger, not a detection benchmark. At this audit its progress table records core 29/47 and profiles/extensions 21/55 with two negative results. M5 remains open pending non-author review. The [M2E.0 decision](../decisions/code-embedding-decision.md) includes local fingerprinting and offline-first registration and omits source-code embedding. The specification is a reproducible-evidence proposal, with planned image/audio profiles; successful recognition of arbitrary transformed work is not established.

## Navigation claims checked against the linked documents

| README destination | Content inspected |
| --- | --- |
| Core / attestations / registration / trust policy | Exact subjects, salted private commitments and possession; DSSE/in-toto forms; draft-5 registrations, key events, time evidence, `tw1-`; verifier-local groups and revocation policy. The M4 promotion and adapter reviews supply substantive review evidence. |
| Timestamp adapter decision | Optional RFC 3161 and OTS offline verification; live-service and hosted-witness deferrals. |
| Threat model / conformance | Adversaries, false claims and privacy boundaries; levels 1–5, with level 5 planned and fixture checks distinct from implementation conformance. |
| Extraction / catalogue-report / code profile | Deterministic tokens, k-grams, original spans and configuration binding; catalogues, suppression and reports; profile registration/reproducibility checklist. |
| TypeScript / Python / text profiles | Stage-1 `ts-tokens`, `py-tokens` and `text-plain`; deferred TSX and draft Markdown. These are separate from transformation-recall evidence. |
| Other content profiles | Still-image, audio, video and binary research scope, not registered perceptual algorithms for all media. |
| Schemas / vectors / examples | JSON Schema Draft 2020-12 formats; commitment, DSSE, adapter, registration and per-profile/matching vectors; synthetic unsigned examples with known artifact bytes. |
| Use cases / implementation patterns | UC-1–UC-7 plus proposed UC-8, walkthroughs, architecture alternatives and an assertion/example matrix. These describe workflows, not successful production deployments. |
| Evaluation / sources | Transformation attack matrix and planned false-positive calibration; a primary technical source register. Neither is a measured detection-rate report. |
| Roadmap / initial draft review | Verifiable gates, counts and owner decisions; blocking and major corrections to the original supplied design. |

The figures describe proposed local extraction/comparison and separate cryptographic registration, plus a research embedding workflow. Figure 3 permits insufficient evidence; it is not a standardized marking method or an origin claim. All four complete accessible alt descriptions and the Figure 3 caption are mapped; only inert picture/source markup is excluded.

## Local validation instructions

The supported floor is Python 3.11, also the lowest version selected by [.github/workflows/validate.yml](../../.github/workflows/validate.yml). Dependency installation/fetch precedes offline checks. `tools/validate.py` uses a local schema registry without a retrieval callback, exact fixture digest checks, and isolated local checker subprocesses; `--links-all` checks local Markdown destinations. The commands check synthetic fixtures and recorded outputs, not production identities or a held-out detection corpus. Registration real-format fixtures deliberately use public test-only roots; successful fixture cryptography is not trust in a production timestamp authority. The release adds the complete requirement map, README map and boundary probes to this checker list.

This audit does not claim an OS-denied rerun of the complete validator or independent approval of the exclusion list. The non-author reviewer should check all five exclusion categories (picture markup only), verify every accessible description, and sample exact evidence quotations and the 27 remaining inspection MUSTs before approving M5.1/M5.2.
