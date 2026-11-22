# Active research work queue

Updated 2026-11-22. This queue operationalizes the [roadmap](../ROADMAP.md) by gate ID. It lists open gates and current assignments, not free-standing phases. A component finishing is not the project finishing: a gate closes only according to its type (E met; R met or negative-result; O decision recorded), with committed evidence.

## Loop rule

1. A supervision loop declares the gate IDs it works on and may be marked complete only when each is closed by type, citing committed evidence.
2. Checkpoints, evidence reviews and "bounded phase complete" notes are progress records. A loop that changes no gate status ends as **paused** or **blocked** and names the gate.
3. A status changes in the same change as its evidence, so someone else can recheck it.
4. When blocked on the owner, ask once, then move to another open gate. Do not invent a phase to have something to close.



## Current assignments

| Gates | Work | State |
| --- | --- | --- |
| I1 (feeds M1.4, M1.6) | Token-fingerprint extractors for Go and Rust source in the implementation repository (`<implementation repo>`), hand-written lexers in both | Extractors exist on local branches there (`i0-i1-rust`, `impl-go`, `xcheck`); not merged to its `main`. Differential test between the two extractors in progress. M1.4 stays open until its criterion is met |
| I2 (feeds M2.1–M2.5, M2.7–M2.11) | Catalogue, matcher, localized-report CLI and offline walkthrough | Next. Needs M1.3 schemas and M2.6 matching vectors from the spec side; the [draft contracts](drafts/catalogue-report-contract.md) and [matching vectors](drafts/matching-vectors/README.md) are the starting point |
| M0.1 | Non-author recount of the 13 capabilities and their verification plans | Ready: plans are merged into [use cases](../docs/use-cases.md) and [implementation patterns](../docs/implementation-patterns.md). Not marked met until someone other than the author recounts |
| M1.1–M1.3, M1.5 | Profile document, vectors, schemas and requirement map in this repository | Open. The [extraction contract](drafts/extraction-contract.md) and [vectors](drafts/extraction-vectors/README.md) are drafts; promoting them needs the owner |
| M2E.0, M2E.1 | Select a carrier or omit embedding | Open. [Lane 06](lanes/06-evidence-review.md) found no ready candidate; see the [lane 06–08 checkpoint](research-06-08-checkpoint.md). No new carrier experiment without a candidate read in primary form that plausibly meets the bar |
| M3.0 | False-alarm budget and unit | Open, owner |

Closed with evidence: M0.2, M0.3, M0.4, M4.1 and M4.2 (see the roadmap for the evidence). Everything else in the gate tables is open.

## Completed evidence (progress records)

- Initial four discovery lanes and the supplementary architecture comparison; see the [discovery checkpoint](discovery-checkpoint.md).
- Synthetic Go/Rust insertion, raw recovery, formatter and removal baselines, and bare DSSE Go/Rust compatibility: [experiment checkpoint](experiment-checkpoint.md).
- Fragment/transplant controls and signing policy with independent commitments: [coordinator reconciliation](fragment-policy-checkpoint.md).
- Public-code eligibility census over four repositories: [census checkpoint](public-census-checkpoint.md). No safe embedding capacity was established.
- Lanes 06–08 evidence reviews and report audits: [reconciliation checkpoint](research-06-08-checkpoint.md).
- Independent reviews of the roadmap, plan, contracts and checkpoints: [research/reviews](reviews/).

These are the SYN research records and M0/M4 evidence in the roadmap, not completion of any milestone. Existing carriers fail cheap normalization; no robust identity payload or population error claim follows.

## Drafts pending the owner

[Extraction contract and vectors](drafts/extraction-contract.md) and the [catalogue and report contract with matching vectors](drafts/catalogue-report-contract.md) stay in `research/drafts/` until the owner approves promotion to `spec/`, `schemas/`, `profiles/` or `test-vectors/`.

## Operating rules

Continue independent work when one gate is blocked. Keep measured outcomes and unresolved questions separate. Preserve local raw reports, which stay untracked and ignored. No automatic publication, normative format change, private application inspection, paid services or new diagram. The [roadmap](../ROADMAP.md) lists what needs the owner.
