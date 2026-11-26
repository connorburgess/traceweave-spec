# Local-first agent design: author disposition and evidence map

Prepared 2026-11-26 against exact **`afca82c41d54d363c28a49fff76a99718e7bb996`** (published identical tree at **`d66e4b942c8ca7da1585cc5f19932456a82f5f1d`**). Companion: [research design supplement](../drafts/agent-registration-local-first.md). This is a reviewable author record, **not a non-author review, acceptance or gate closure**. Only these two new research Markdown files are proposed. The normative registration/trust specifications, schemas, fixtures, checkers, existing reviews, ROADMAP and counts remain byte-identical to the base.

## SK.3 clause/evidence map

| Existing criterion clause | Existing pinned evidence | Supplement / remaining review |
| --- | --- | --- |
| A design exposes registration and verification as agent-callable skills | [Registration §19](../../spec/registration-record.md#19-registration-at-creation-time-and-agent-interoperability); [local A2A card](../../test-vectors/registration/fixtures/a2a-card-local-registrar.json) names both skills; [MCP register fixture](../../test-vectors/registration/fixtures/mcp-tool-register.json) | Supplement §§2–5/7 maps both operations, including verification's explicit local policy and absence of signing capability. Independent review remains required; no new MCP verify schema is claimed. |
| Local-first before any hosted signer | §19.2(a)/19.4 MCP stdio recommendation | §§1–4: no listener, local key consent/store, both operations local; no implicit network fallback. Proposed behavior only. |
| Only digests go on the wire | §19.3 hop table, signature-digest target; negative wire fixtures | §6 separates content-derived digest payloads from auth/protocol/IP metadata and returned evidence. Initial off-machine contact is held. Local stdio paths/bytes cannot be forwarded to a remote model/bridge. |
| Non-author review filed; every finding dispositioned | Prior reviews cover portions of registration, not current SK.3 completeness | This author table is not that evidence. Reviewer must assess the exact submitted design commit and record dispositions; no sublane was launched. |
| Design cited once it exists | ROADMAP narrative mentions A2A section; SK.3 row lacks direct citation | Both research documents supply a reviewable target. An eventual citation/status change remains a separate authorized coordinator action; ROADMAP is not edited here. |

## Disposition of audit topics

| Topic | Proposed disposition and location | Evidence boundary |
| --- | --- | --- |
| Incomplete local operation map | §§3/4 map explicit inputs, policy/store access, consent, output/result projection, local errors, retries/cancellation for **both** skills | No adapter/CLI invocation contract or executable schema is added. Full result meanings remain registration §10. |
| Unsettled signing identity/default | §2 requires explicit key capability/full key anchor, policy snapshot and scoped host consent; §9 keeps RD4/§17/§19.7 owner choices open | No key generation, I0/I0′ default, I2 login or agent-owned key default selected. |
| Local paths and model-visible outputs | §§1/2/3/5 separate host-local resolution, opaque handles and sanitized projection from full local diagnostics/results | An opaque ID alone grants no store access. No runtime privacy enforcement or SK.2 canary results claimed. |
| Missing/invalid policy and signing trust | §§2–5 require explicit local policy; invalid policy fails input validation; valid policy may mark selected key untrusted | A signature is not trust, and the caller cannot smuggle policy through a bundle. |
| Optional time contact versus §19.2 wording | §§1/3/6 apply the already adopted [timestamp adapter decision §2](../../docs/decisions/timestamp-adapter-decision.md#2-decision) | Local signed statement may have no evidence; `none-valid`/claimed-only or `not-compared` stays visible. No TSA/calendar/witness contact or queued submission authorized. |
| N1: “two” versus three notices | §8 names exact stale §19.5 phrase and recommends replacing “two” with “three”; §7 retains all three plus agent notice | Normative file unchanged. Existing checker already requires three result notices. |
| N1 related skill-description scope | §8 records `check_card`'s limited `SENTENCE_FIRST` check and proposes conservative description/template/check alignment for later adoption | Current skill-description fixtures are not certified to enforce all notices; actual result rendering is never exempted. No proposed REG.5 criterion adopted. |
| N2: request text-part mismatch | §8 names `check_wire_parts`/`check_request` static branches and proposes exact hosted-request one-data-part restriction plus later negative directions | No runtime reproduction, checker fix, fixture edit or conformance claim. Generic A2A text messages are not globally banned by this local research proposal. |
| Witness versus backing-TSA independence | §6 inherits §6.3 union-find groups and resolved S4 | Shared TSA counts once. No witness deployment or new trust root. |
| Creation/agent/time claims | §7 inherits §11/§19.5 notices, per-key bounds and §4.7 self-declaration limits; §6 retains resolved S8 clock distinction | No human/agent origin, creation-order or ownership evidence asserted. |
| A2A/MCP source pins and validation | §7 carries exact recorded source commits/version distinction | No fresh upstream lookup; proto-derived shape checks and historical MCP validation do not replace SK.4. |
| SK.4/5 dependencies | §9 explicitly preserves existing criteria and owner decisions | Generated-schema wording remains proposed; independent client run absent; hosting and namespaces unapproved. |

## Existing independent reviews and fixture locators

- [Initial registration review](registration-record-review.md): explicitly excluded §19 because it was unavailable. It is not SK.3 acceptance.
- [Registration confirmation](registration-record-draft-2-review.md): reviews §19-related S4/S8, marks those resolved in its draft-3 confirmation; S13 gate wording remained a proposal. Reuse those findings/dispositions without treating them as complete SK.3 approval.
- [Promotion review](promotion-m4-py-review.md): acceptance for M4.3/M4.6/PY.1/PY.2 and move integrity, not SK.3/SK.4/SK.5.
- [Commitment/disclosure review](../../docs/reviews/commitment-disclosure-review.md): inherited privacy/selective-disclosure limits, not local adapter approval.
- [Fixture README](../../test-vectors/registration/README.md): declares A2A fixtures not validated against a published A2A schema; records illustrative MCP schema validation. These are recorded claims, not checks rerun here.
- Positive fixtures: local/hosted cards, witness request/task, MCP register tool, agent rendering, witness evidence and shared/independent-TSA result pairs. All under [registration fixtures](../../test-vectors/registration/fixtures/).
- Negative fixtures: `neg-a2a-shape`, `neg-mcp-tool-shape`, `neg-agent-authorship`, `neg-agent-notice-missing`, `neg-content-on-wire`, `neg-fingerprints-on-wire`, `neg-hosted-plain-http`, `neg-witness-authorship`, `neg-witness-shape`, `neg-witness-shared-tsa`, `neg-witness-wrong-digest`, under [registration negative fixtures](../../test-vectors/registration/negative/).
- [Checker](../../test-vectors/registration/check_registration.py): static source inspection of `check_card`, `check_wire_parts`, `check_request`, `check_task`, `check_mcp_tool` and rendering constants supports N1/N2 descriptions. This author task executed none of them.

## Review questions and authorization boundary

The independent reviewer should determine whether the proposed local capability/consent boundary and result projection are coherent, whether both skill semantics are complete enough for SK.3 design, and whether N1/N2 recommendations preserve inherited rules. New local orchestration choices are proposals to review, not statements that the existing implementation supports them. Review should record exact commit, each finding and disposition, and distinguish remaining owner policy choices from missing design evidence.

No request to close a gate, alter a criterion, implement a client/adapter, operate a service or publish a namespace is made by these documents. The smallest subsequent step is independent review of this exact two-file submission. SK.4 implementation/conformance and SK.5 decisions remain outside this design task. The 48-repository M3 evaluation remains held.

## Validation

Document checks passed for this two-file research addition: all-repository local Markdown links, tree hygiene, staged whitespace, and a Git scope assertion that existing tracked bytes equal the base. These checks do not execute protocol clients, fixture checkers, builders or experiments and do not demonstrate schema/client conformance. No source acquisition, download, service, listener, adapter, implementation, push, gate/count change or subagent is included.
