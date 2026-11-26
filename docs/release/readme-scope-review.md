# README scope and navigation audit

Author audit for M5.2, 2026-11-26; not the non-author exclusion approval or an independent implementation review. This review checks descriptive/navigation claims against repository contents. Runtime/detection claims need the separate fixtures and recorded reviews in the claim map.

Historical snapshot: the counts and pending-review statements below describe the earlier author audit on 2026-11-26, before independent closure. At the earlier four-gate closure, status was M5.1/M5.2/M5.4/M5.5 met, core 33/47 met and 14 open, on review of exact commit `07c98cad440e3797d0ddc0c4b8c2bfb06a36dbd7` ([re-review](../../research/reviews/m5-readiness-e7e7149-review.md) `1df04f9`; [final confirmation](../../research/reviews/m5-readiness-07c98ca-review.md) `6ded8a3`; [closure recount](../../research/reviews/m5-gate-closure-07c98ca.md)). M5.3 was then open; M3.1–M3.6 remained open/held. The earlier audit's exact evidence quotations are retained below.

Current status after independent M5.3 recipe review: M5.1–M5.5 met, core **34/47 met and 13 open**. M5.3 cites exact recipe commit `24bb4b8483dc86966cb7c8277130bb816b0c6b3f` and [independent review](../../research/reviews/m5-3-recipe-24bb4b8-review.md) `284ce4e`; see the [M5.3 closure recount](../../research/reviews/m5-3-gate-closure-24bb4b8.md). M3.1–M3.6 remain open/held, and no release approval is implied. Profiles/extensions now record **22/55 met, two negative results and 31 open**, including the scoped research-only [IMGF.1 closure](../../research/reviews/imgf1-gate-closure-db2848c.md); its historical count snapshot below is unchanged.

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
