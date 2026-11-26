# SK.3 design-only closure and independent progress recount

Recorded 2026-11-26 on the isolated local-first design branch, at pre-closure HEAD **`12a1459c62e3539e02ef174e0fbf6d909b199eb4`**. Exact design reviewed: **`4fa00c7d00eb24c5a39866b05e8b6aeca27174b2`**, [supplement](../drafts/agent-registration-local-first.md) and [author evidence/disposition map](agent-registration-local-first-dispositions.md). The separate [independent review](agent-registration-local-first-4fa00c7-review.md), committed as `12a1459c62e3539e02ef174e0fbf6d909b199eb4`, found the proposed local-only design eligible with explicit limitations. The coordinator authorized this bounded metadata closure after that review.

The sole new met gate is **SK.3**, as a design/review/citation gate. Its existing criterion is preserved verbatim before the status annotation. This closure does not adopt the replacement SK/REG wording proposed in registration §19.7 or accept implementation conformance.

## Existing criterion and committed basis

| Existing SK.3 clause | Closure evidence |
| --- | --- |
| Design exposes registration and verification as agent-callable skills | Supplement §§1–5/7 maps both skills to proposed local MCP stdio semantics, with explicit inputs, authority, outputs, separate outcomes, errors, retries and cancellation; registration §19 supplies the conceptual local A2A skills. The independent review checks both. This is a design mapping, not an implemented A2A/MCP adapter. |
| Local-first before any hosted signer | Explicit host-authorized snapshots, signing capability, policy/store references and consent; no listener, hosted signer or implicit key fallback. Verification needs no signing capability. Initial outbound contact and timestamp acquisition are held. Valid untimestamped signed statements remain distinct from proved time. |
| Only digests go on the wire | Supplement §6 and registration §19.3 separate host-local content from potential content-derived outbound signature-digest requests. Artifact/statement/envelope bytes, fingerprints and possession nonce are not outbound payloads. Authentication, protocol/IP/timing metadata and returned evidence are described separately. Initial operations send nothing off-machine. Existing hosted checker enforcement is not certified. |
| Non-author review filed; every finding dispositioned | Exact-commit review `12a1459` records I1–I4 and C1 with explicit dispositions, including the inherited unresolved inconsistencies. Disposition is not a claim that they are fixed. |
| Design draft cited once it exists | The SK.3 row now directly cites exact `4fa00c7`, the supplement, registration §19, independent review `12a1459` and this closure record. |

## Unresolved findings and limits carried forward

| Review item | Current disposition, preserved by this closure |
| --- | --- |
| **I1, low — notice count** | **Unresolved.** Registration §19.5 still says two fixed §11 sentences; current §11 requires three plus the agent notice. The supplement preserves all four. The recommended normative correction has not been made. |
| **I2, medium — description enforcement** | **Unresolved.** Current card/tool checks enforce only `SENTENCE_FIRST`, while actual descriptions lack the other notices. The independent bounded card probe confirms acceptance. Proposed discovery/result scope distinctions are not adopted exemptions. Actual result presentations still require all current notices and rendering rules. |
| **I3, medium — hosted extra-text bypass** | **Unresolved.** The existing checker accepts a valid witness data request with an extra text part; raw/URL controls fail, text-only yields shape failure, and wrong digest remains rejected. No checker, fixture, adapter or service fix is included. Future hosted-request validation must address the full part restriction and error precedence. |
| **I4, medium — witness version drift** | **Unresolved.** Registration §19's draft-1 witness/request examples conflict with the draft-5 checker/fixture; the draft-1 request fails the independent bounded probe. Alignment is required before a hosted adapter or SK.4 conformance claim. No version choice, namespace publication or normative change is made here. |
| **C1, low — projection list clarity** | **Nonblocking next-design clarification, not fixed.** Explicitly naming per-key-event outcomes would make the supplement's list clearer. Its governing preservation of every §10 dimension, key-event evaluation, distinct rejected-event handling and full local result already require those outcomes. No permission to drop or merge them follows. |

I1–I4 remain implementation/specification limitations and C1 remains a future clarification. The author design, author disposition map, independent review and normative/checker/fixture files are unchanged. No additional-runtime/privacy, canary, schema or independent-client result is inferred from the design closure. Witness/TSA independence and clock limitations retain the earlier resolved S4/S8 rules; this closure does not repeat a cryptographic experiment.

**SK.4 and SK.5 remain planned/open.** No schema/client interoperability, hosting, service/operator commitment or default key/identity/policy selection is approved. Person/organisation versus agent-runtime custody, I0 versus I0′, I2 availability, policy/recovery defaults and namespace publication remain owner decisions. External providers/contact, timestamp acquisition, services, adapters, namespace publication and release/publication authorization remain held. No proposed replacement criteria or REG.5 are adopted. M3 remains held; this work authorizes no evaluation or acquisition.

## Independent row and claim recount

The individual gate rows are the source of the recount; the summary lists are checked against the resulting met-ID sets. Missing/planned/draft-only statuses count as open; Markdown emphasis is normalized.

| Group | Before `12a1459` | Closure tree |
| --- | --- | --- |
| Core M0–M5 | 47 total: 34 met, zero negative-result, 13 open | **Unchanged: 34 met, zero negative-result, 13 open** |
| Later profiles, EXT and RC | 55 total: 27 met, two negative-result, 26 open | **28 met, two negative-result, 25 open** |

The only changed individual gate row is SK.3, from planned/open to met in design scope. All 47 core rows and every other extension row, including SK.4/SK.5, are byte-identical to `12a1459`. The negative set remains TXT.4/TXT.8. Core open IDs remain M2E.1–M2E.7 and M3.1–M3.6.

The extension open set is TS.4, PY.4, IMGF.5, IMGF.6, TXT.0, TXT.5, TXT.6, BIN.1, BIN.2, RES.2, RES.3, C2PA.1, C2PA.2, SK.4, SK.5, STRUCT.1, KEYED.1, WEB.3–WEB.6, EXT.1 and RC.1–RC.3: 25 rows. The met-ID set equals the current progress-table list.

README changes only its extension count from 27/55 to 28/55. Its JSON/Markdown claim map updates README-007 with the exact current ROADMAP row, the independent design review and this scoped closure. All 77 claim IDs/order, all other claim entries, 59 excluded source lines and the five exclusion rules remain unchanged. Current scope text is reconciled while retaining earlier 27/55, 22/55 and other dated snapshots. No release behavior claim is added.

## Local validation and write boundary

Using existing dependencies under OS network denial, the repository validator, all 29 unit tests, all local Markdown links, exact README/requirement maps, tree/history hygiene and whitespace checks pass. All four existing vector builders reproduce unchanged vector bytes. Independent assertions verify gate counts and ID sets, the sole row/status change, unchanged criterion, unchanged inventory/exclusions and author/normative/checker/fixture bytes. These checks assess metadata consistency and existing fixture checks; they do not fix I1–I4 or establish SK.4/SK.5.

Only ROADMAP, README, its current release claim/scope metadata and this new closure record change. Private `roadmap-v2` and public history are not integrated or regenerated by this lane; the separate queue reconciliation at private `0075c8f394b31a946d279a358e2c71a47a7f60d9` is left to the coordinator for later integration. Historical records are unchanged. No push, deployment, listener, service, acquisition, new dependency, held evaluation or sublane is included.
