# Active research work queue

Updated 2026-11-23. This queue operationalizes the [roadmap](../ROADMAP.md) by gate ID. It lists open gates and current assignments, not free-standing phases. A component finishing is not the project finishing: a gate closes only according to its type (E met; R met or negative-result; O decision recorded), with committed evidence.

## Loop rule

1. A supervision loop declares the gate IDs it works on and may be marked complete only when each is closed by type, citing committed evidence.
2. Checkpoints, evidence reviews and "bounded phase complete" notes are progress records. A loop that changes no gate status ends as **paused** or **blocked** and names the gate.
3. A status changes in the same change as its evidence, so someone else can recheck it.
4. When blocked on the owner, ask once, then move to another open gate. Do not invent a phase to have something to close.



## Current assignments

Updated 2026-11-23 after the owner decisions of that day. Implementation repository: `<implementation repo>`, with `main` at `82b02ab` (unpushed).

| Gates | Work | State |
| --- | --- | --- |
| I1 (M1.4, M1.6) | Go and Rust extractors, hand-written lexers | Merged; [I1 review](reviews/implementation-merge-i1-review.md) `9c03c95`. The spec branch is public at `dec460e` (2026-11-23; [public history map](public-history-map.md)). Next: re-vendor from the promoted paths at a pushed public commit and pass `check-spec-pin --strict`; M1.4 is not met until then ([owner decisions of 2026-11-23](../ROADMAP.md#owner-decisions-2026-11-23)) |
| I2 (M2.1–M2.11) | Catalogue, comparison and report, two implementations | Merged at `82b02ab`; [I2 review](reviews/implementation-merge-i2-review.md) `de9a5b7`. M2.5 and M2.8 met |
| Post-I2 integration | The A6 behavioural rules B1–B10 ([contract](../spec/catalogue-report.md) §6.8) and the [behaviour checklist](../test-vectors/matching/behaviour-checklist.md) | In progress on implementation branches (`i2-rust` and others); not yet on `main` or reviewed. Next engineering for M2:<br>- `scripts/offline` wrapper (M2.1)<br>- frozen fixture manifest (M2.2)<br>- vendor control class (M2.3, M2.6; OD-C19)<br>- B10 rebuild-from-clean-clone check (M2.4)<br>- review packets (M2.7, not started)<br>- candidate-generation record keyed by `bodySha256` (M2.9)<br>- the I2 review's follow-ups F1–F4 |
| Behavioural follow-up rulings | A5–A8 rules, including OD-C39–OD-C47 | Confirmed 2026-11-23 by the coordinator under the owner's delegation ([owner decisions of 2026-11-23](../ROADMAP.md#owner-decisions-2026-11-23)) |
| M1.1, M1.5 | Item map against `profiles/code.md`; requirement map of MUSTs to failing checks | Open, engineering |
| M3.1–M3.3 | M3 evaluation protocol (`m3-eval-draft-3`) and corpus acquisition | M3.0 met: 1 in 20, met at 132 searches if alarms ≤ 6. Acquisition of the 48 repositories into `~/traceweave-eval` is approved, with the licence recheck failing closed. Next: acquire, freeze splits and config, run ([owner decisions of 2026-11-23](../ROADMAP.md#owner-decisions-2026-11-23)) |
| TS.1–TS.3, TXT.1–TXT.3 | `ts-tokens` and `text-plain` profiles | Frozen for stage 1 and registered in the draft contract. Not yet implemented in the implementation repository |
| IMGF.1, IMGF.5 | Image profile item map; second implementation with a C++ reference build | Open. IMGF.2–IMGF.4 met (`ec0cf67`) |
| M2E.0, M2E.1 | Select a carrier or omit embedding | Open. [Lane 06](lanes/06-evidence-review.md) found no ready candidate |
| IMG.0–IMG.5 | Image embedded-mark study | IMG.0–IMG.4 met: UC-7 accepted (`3147237`); run `e-img-m-2`, with results `a78aace`, frozen `d3af1ee` and [recheck](reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2) `d3d4788`. Finding: a finding aid, not evidence of origin (marks transfer without the key). Open: IMG.5, which needs a decision on where the six detection-record fields live. Real-image sets stay owner-gated |
| C2PA.1–C2PA.3 | C2PA mapping pinned to one version; round-trip fixtures; no compatibility claim until they pass | In progress; sequencing override of 2026-11-23 ([owner decision on image marks and C2PA](../ROADMAP.md#owner-decision-2026-11-23-image-marks-and-c2pa)) |
| Lane 11 | External feedback audit (`research/lanes/11-report-audit.md`, brief `research/prompts/11-external-feedback.md`) | In progress; a progress record, not a gate |
| I3 (M3.1–M3.5) | Evaluation harness in the implementation repository: manifest and licence checks, frozen splits and config, held-out run | Started. Corpus acquisition is approved (owner decisions of 2026-11-23) |
| Spec CI | The repository validator and tests as a reproducible workflow for the first push | In progress |
| Implementation CI | `scripts/check` as a hosted workflow in the implementation repository | In progress. Enabling hosted CI follows the push decision |
| Owner | M2E.0; TXT.0, TXT.5, TXT.8; IMGF.6; for image marks, real-image sets, non-commercial or unclear-licence weights and GPU spend | Still owner-blocked. Push done: public `roadmap-v2` at `dec460e`, with CI pending. Pending execution: the implementation re-vendor and strict pin check. The local branch is never pushed; only regenerated public history is, as fast-forwards ([owner decisions of 2026-11-23](../ROADMAP.md#owner-decisions-2026-11-23); [owner decision on image marks and C2PA](../ROADMAP.md#owner-decision-2026-11-23-image-marks-and-c2pa)) |

Closed with evidence: M0.1–M0.4, M2.5, M2.8, M2.10, M2.11, M3.0, M4.1, M4.2, IMGF.2–IMGF.4 and IMG.0–IMG.4. Everything else is open.

## Planned items

- **WEB.0–WEB.6 (browser tool and testing page).** Requested by the owner on 2026-11-23 as a roadmap item, not for building yet. Planned; not started; no lane assigned. It follows M3.4 unless the owner overrides, and the owner decides when it starts and where it is hosted (WEB.0). See the [roadmap](../ROADMAP.md#later-profiles-and-sequence).

## Completed evidence (progress records)

- Initial four discovery lanes and the supplementary architecture comparison; see the [discovery checkpoint](discovery-checkpoint.md).
- Synthetic Go/Rust insertion, raw recovery, formatter and removal baselines, and bare DSSE Go/Rust compatibility: [experiment checkpoint](experiment-checkpoint.md).
- Fragment/transplant controls and signing policy with independent commitments: [coordinator reconciliation](fragment-policy-checkpoint.md).
- Public-code eligibility census over four repositories: [census checkpoint](public-census-checkpoint.md). No safe embedding capacity was established.
- Lanes 06–08 evidence reviews and report audits: [reconciliation checkpoint](research-06-08-checkpoint.md).
- Independent reviews of the roadmap, plan, contracts and checkpoints: [research/reviews](reviews/).

These are the SYN research records and M0/M4 evidence in the roadmap, not completion of any milestone. Existing carriers fail cheap normalization; no robust identity payload or population error claim follows.

## Promoted contracts

On 2026-11-23 the owner approved promoting the reviewed contracts: [extraction contract](../spec/extraction.md), [catalogue and report contract](../spec/catalogue-report.md), [TypeScript profile](../profiles/typescript.md) and [text profile](../profiles/text.md), with their vectors under `test-vectors/` and the three schemas under `schemas/`. See the [promotion map](promotion-map.md). The image profile, image protocol and evaluation protocol remain drafts in `research/drafts/`.

## Operating rules

Continue independent work when one gate is blocked. Keep measured outcomes and unresolved questions separate. Preserve local raw reports, which stay untracked and ignored. No automatic publication, normative format change, private application inspection, paid services or new diagram. The [roadmap](../ROADMAP.md) lists what needs the owner.
