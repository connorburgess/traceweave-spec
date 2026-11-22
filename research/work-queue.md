# Active research work queue

Updated 2026-11-22. This queue operationalizes the [roadmap](../ROADMAP.md) by gate ID. It lists open gates and current assignments, not free-standing phases. A component finishing is not the project finishing: a gate closes only according to its type (E met; R met or negative-result; O decision recorded), with committed evidence.

## Loop rule

1. A supervision loop declares the gate IDs it works on and may be marked complete only when each is closed by type, citing committed evidence.
2. Checkpoints, evidence reviews and "bounded phase complete" notes are progress records. A loop that changes no gate status ends as **paused** or **blocked** and names the gate.
3. A status changes in the same change as its evidence, so someone else can recheck it.
4. When blocked on the owner, ask once, then move to another open gate. Do not invent a phase to have something to close.



## Current assignments

Updated 2026-11-22 after the I1 and I2 integrations. Implementation repository: `<implementation repo>`, with `main` at `82b02ab` (unpushed).

| Gates | Work | State |
| --- | --- | --- |
| I1 (M1.4, M1.6) | Go and Rust extractors, hand-written lexers | Merged; [I1 review](reviews/implementation-merge-i1-review.md) `9c03c95`. Open on owner items only: the pushed spec commit and promotion of the M1.2 vectors |
| I2 (M2.1–M2.11) | Catalogue, comparison and report, two implementations | Merged at `82b02ab`; [I2 review](reviews/implementation-merge-i2-review.md) `de9a5b7`. M2.5 and M2.8 met |
| Post-I2 integration | The A6 behavioural rules B1–B10 ([contract](drafts/catalogue-report-contract.md) §6.8) and the [behaviour checklist](drafts/matching-vectors/behaviour-checklist.md) | In progress on implementation branches (`i2-rust` and others); not yet on `main` or reviewed. Next engineering for M2:<br>- `scripts/offline` wrapper (M2.1)<br>- frozen fixture manifest (M2.2)<br>- vendor control class (M2.3, M2.6; OD-C19)<br>- B10 rebuild-from-clean-clone check (M2.4)<br>- review packets (M2.7, not started)<br>- candidate-generation record keyed by `bodySha256` (M2.9)<br>- the I2 review's follow-ups F1–F4 |
| Behavioural follow-up rulings | A6 rulings OD-C39–OD-C47 | Decided in draft, pending owner confirmation |
| M1.1, M1.5 | Item map against `profiles/code.md`; requirement map of MUSTs to failing checks | Open, engineering |
| M3.0–M3.3 | M3 evaluation protocol draft | In progress. The budget (M3.0) and corpus acquisition (M3.1) need the owner |
| TS.1–TS.3, TXT.1–TXT.3 | `ts-tokens` and `text-plain` profiles | Frozen for stage 1 and registered in the draft contract. Not yet implemented in the implementation repository |
| IMGF.1, IMGF.5 | Image profile item map; second implementation with a C++ reference build | Open. IMGF.2–IMGF.4 met (`ec0cf67`) |
| M2E.0, M2E.1 | Select a carrier or omit embedding | Open. [Lane 06](lanes/06-evidence-review.md) found no ready candidate |
| Owner | Draft promotion; pushed spec commit; OD-C5 and distinct-hash confirmation; M3.0 budget; A6 rulings | Would close M1.2, M1.3, M1.4, M1.6, M2.10 and M2.11, and the (a) clauses of M1.1, M2.2, M2.4 and M2.6 (see the roadmap progress section) |

Closed with evidence: M0.1–M0.4, M2.5, M2.8, M4.1, M4.2, and IMGF.2–IMGF.4. Everything else is open.

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
