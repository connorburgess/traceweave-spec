# Independent review of queue reconciliation at 09359ac

Reviewed 2026-11-26: exact commit **`09359acc2dd53022963b1e2046368dff49cf7fe3`** on `research/queue-reconciliation-20261126`, based on private **`afca82c41d54d363c28a49fff76a99718e7bb996`** and published **`d66e4b942c8ca7da1585cc5f19932456a82f5f1d`**. Located the isolated worktree through `git worktree list`; HEAD equalled the requested commit and the worktree was clean before review. This reviewer did not author the queue reconciliation. Only this new review record is written by the review lane.

**Verdict: eligible for integration as queue maintenance; no blocking findings or required author-file fixes.** No gate is closed by this review. The queue removes obsolete assignments while retaining all open gates, current holds and the distinction between historical approval, completed evidence and permission to execute. Publication remains a separately authorized action.

## Exact scope and preservation

Compared the complete [queue diff](../work-queue.md), [author reconciliation](work-queue-reconciliation-afca82c.md), unchanged [ROADMAP](../../ROADMAP.md), cited decisions/reviews, and the recent local WEB.3–WEB.6 and SK.3–SK.5 audit inventories. Those audit inventories are context, not gate acceptance or service authorization. Checked their underlying WEB/SK clauses against the committed sources rather than importing their recommendations as requirements.

The published/private checkpoints have the same Git tree, **`7a6dfb10d7547f9a5daa346310dfef37103fd291`**. Against that base, the exact reviewed commit changes only:

- `research/work-queue.md`;
- `research/reviews/work-queue-reconciliation-afca82c.md`.

ROADMAP is byte-identical at both checkpoints and the reviewed commit; SHA-256 **`2c1f441baa10858657d5f8ca59d489ab6644fdbea7ebd8a59c2f2cd4e38ca267`**. The replaced queue's SHA-256 **`f87975327da3cab53ebf6320fd99ec5ef1e01dd18ecb6cb7cf17ae240f829618`** also matches the author record. Thus no criterion, gate status/count, normative contract/profile, fixture, test, claim map, public history map or publication procedure changed. The old queue remains available at the base commit; dated context and research checkpoint links remain in the replacement.

## Counts and completeness

Independently parsed individual ROADMAP gate rows, using the actual status column for core gates and explicit status notes for extension gates, with Markdown emphasis normalized. Missing/planned status remains open. Then expanded the queue's ID ranges and compared sets, without taking its printed totals as the source of truth.

| Partition | Independently counted result | Queue comparison |
| --- | --- | --- |
| Core M0–M5 | **47 total, 34 met, 0 negative-result, 13 open** | Exact totals and open-ID set match. Open: M2E.1–M2E.7 and M3.1–M3.6. |
| Extensions, EXT and RC | **55 total, 27 met, 2 negative-result, 26 open** | Exact totals and open-ID set match. TXT.4/TXT.8 remain negative-result. IMGF.1 is already met in the integrated baseline. |
| Open dependency table | **39 distinct IDs** | Exactly the 13 + 26 open ROADMAP IDs, with no duplicate or missing gate. |
| Completed evidence table | **63 distinct IDs** | Exactly 34 + 27 met IDs and the two negative-result IDs, with no duplicate or missing gate. |

This is the integrated baseline partition, not the earlier isolated five-gate closure's 26/55 met count. Source commit IDs for the recent profile closures/reviews/integration resolve through the retained [public history map](../public-history-map.md); implementation-repository IDs remain implementation evidence, not spec-history IDs.

## Assignment and dependency review

| Queue treatment | Independent check / retained unfinished work |
| --- | --- |
| Retire I1/I2 active-lane and re-vendor TODOs | ROADMAP records all M1/M2 met at the reviewed implementation round-three integration, preserving M1.4's A16 caveat. The queue links the earlier core/I2 reviews without treating old findings as newly active tasks. The separate walkthrough helper mentioned in ROADMAP is not erased or claimed complete. |
| Retire registration draft-2/service-blocked and unimplemented TS/text/Python statements | M4.1–M4.6 and TS/TXT/PY engineering gates have the cited promotion/re-vendor/parity evidence. Offline registration completion does not authorize external timestamp acquisition or hosted operation. TS.4/PY.4 remain separate held evaluation dependencies. |
| Retain M5 and scoped profile closures | M5's committed review/closure records are cited as snapshots, not fresh remote results or release approval. TS/text remain frozen stage-1 only; TSX/Markdown masking remain deferred. IMG.5 remains the reviewed draft-schema route. IMGF.1's finite single-host research closure does not replace IMGF.5 exact interoperability or IMGF.6 natural-image measurement. |
| Supersede the former acquire/pilot/run instruction | The leading **M3 execution and acquisition HOLD** expressly includes the 48 repositories/replacements, pilot, tuning, measured freeze, held-out execution and reproduction. Historical acquisition approval is retained as history, not executable clearance. The final harness review at implementation `07621b8` / protocol `41628be` is conditional; disk/machine/people/runbook and exact-pin dispositions remain prerequisites after any future explicit hold lift. No stale finding is asserted still unfixed without rechecking. |
| Defer M2E.1–M2E.7 and CI/CD signing | [M2E.0 decision](../../docs/decisions/code-embedding-decision.md) and ROADMAP's owner-deferred CI/CD/trailer idea support the queue. Neither carrier selection nor signing automation becomes an assignment. RC.1's narrower enumerated embedding exemptions are not silently expanded by the queue. |
| Preserve text/image/resolver acquisition and sequence boundaries | TXT.0/TXT.5 stay owner decisions. TXT.6 requires TXT.4 **met**, which its negative-result closure does not establish. Real-image measurement, new corpus acquisition, unclear/non-commercial weights and GPU spend retain their boundaries. BIN/RES/STRUCT/KEYED still follow held M3.4; RES.1 is threat-model evidence, not a resolver operating approval. |
| Preserve C2PA unfinished decisions | Mapping §6 retains D1 for C2PA.1, D7 tool download/build and D10 round-trip wording for C2PA.2, plus namespace/publication/contact/disclosure decisions. The queue links that full decision table and distinguishes handwritten fixtures from external-tool interoperability. C2PA.3 remains only the no-premature-compatibility gate. No tool acquisition, submission, export or compatibility claim is approved. |
| Preserve SK.3–SK.5 | Registration §19 is an existing local-first design seed, not current SK.3 acceptance. The recent SK audit requires the local register/verify operation map and scoped non-author review/dispositions; proto field-list/MCP fixture checks do not establish SK.4's published-schema and independent-client clauses. Key/identity/gate-wording choices stay decisions. SK.5 service operation and external timestamps remain owner-held. The queue does not close these gates or make hosting a prerequisite of local design work. |
| Retire the obsolete WEB start-decision TODO while retaining WEB.3–WEB.6 | WEB.0's 2026-11-25 override already exists and WEB.1/WEB.2 engine proofs remain recorded. The recent WEB audit leaves full fixed-fixture flows, demonstrations/misses, page claims, keyboard/size/performance evidence open. Shelf registration verification is not comparison-report replay; sampled engine parity does not certify Shelf. The queue preserves the conformance-matrix distinction. |
| Retire Lane 11 as an active assignment | Its existing report is a completed progress audit, not a new gate or evidence that every surviving evaluation question is resolved. Its source link is retained; M3 and later research dependencies remain open. |
| Preserve EXT/RC and publication boundaries | External-review selection, independent-implementer choice, name clearance and remaining dependencies stay open. All M5 met does not imply RC completion, main-branch publication, deployment or release approval. Regenerated public-history publication still needs separate authorization; the local private branch is not pushed. |

## Non-blocking scope observations

The queue's WEB.6 instruction to check budget evidence is a dependency reminder, not a claim that a valid freeze has been located. The prior WEB inventory found **no pre-WEB.1 frozen budget record in the inspected local material**; its provenance gap remains unresolved. Neither the 16/17-byte engine boundary probe nor Shelf's later 1 MiB configuration proves the temporal freeze clause. Identifying an existing record or explicitly resolving that missed prerequisite remains separate from this queue maintenance. No new budget or inferred start restriction is introduced here.

The queue deliberately does not assign new lanes. SK's local design can be assembled/reviewed within an independently authorized scope; WEB's start override remains valid. A row listing future dependencies authorizes neither implementation nor execution on its own. These qualifications agree with both recent audit inventories; none requires an author-file correction before integrating this reconciliation.

## Validation and limitations

Executed with the existing pinned Python 3.12.14 environment, bytecode writing disabled:

- `python -B tools/validate.py --links-all`: pass for all local Markdown paths.
- Independent heading-fragment checks for every queue local anchor: pass, including final harness review, confirmation passes and the deferred-ideas section.
- Independent row/range/set recount and source-tree/hash assertions above: pass.
- `python -B tools/check_hygiene.py`; `git diff --check`: pass.

No executable code changes warrant a full implementation/test-suite rerun for this two-document maintenance. No claim is made about fresh remote jobs, current upstream standards/tools, current implementation main, study readiness or external service availability. Only local committed evidence and the current supplied owner holds were assessed. No experiment, download, corpus acquisition, service contact, push, subagent, gate change or other worktree mutation was performed. This review record is the only review-lane addition.
