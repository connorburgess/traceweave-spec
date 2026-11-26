# Local-first agent registration design supplement (SK.3)

Status: **research proposal for independent review, 2026-11-26**. Evidence base: exact private commit **`afca82c41d54d363c28a49fff76a99718e7bb996`**, published as **`d66e4b942c8ca7da1585cc5f19932456a82f5f1d`** with identical tree `7a6dfb10d7547f9a5daa346310dfef37103fd291`. This supplements [registration-record.md §19](../../spec/registration-record.md#19-registration-at-creation-time-and-agent-interoperability) for a bounded local design; it changes no normative specification, schema, checker, fixture, ROADMAP criterion or gate status. The [disposition/evidence map](../reviews/agent-registration-local-first-dispositions.md) is author-prepared, not an independent acceptance.

## 1. Boundary and route

Recommend the existing §19.4 **MCP over stdio** route first: a local host launches a local tool process, passing references to explicitly selected files, key access, store and policy. No listener or network A2A agent is required by this design. The existing [illustrative local A2A card](../../test-vectors/registration/fixtures/a2a-card-local-registrar.json) exposes two conceptual skills, `register` and `verify`; the operation map below gives both local semantics. This is an A2A skill design mapping, not a claim that MCP implements A2A or that either protocol has been implemented or tested here.

The local host and tool are inside the same machine boundary; a remote model or remote MCP bridge is outside it. File paths, bytes, private key material, possession nonces, catalogues and detailed diagnostic/policy paths stay in that local boundary. The host must not forward these local tool inputs to a remote model. The model may select only opaque references already granted by the host; it cannot authorize a new file, key, policy or service. A future client integration must enforce this separation; it is not demonstrated by these documents or the old illustrative tool fixture.

All behavior below is **proposed local orchestration**, not a new registration wire format or an existing CLI/API signature. Field labels are design vocabulary, not a JSON Schema. The full registration and verification objects keep their existing versioned meanings. For the initial design, timestamp acquisition and all other outbound contact are **held**; there is no hidden provider, metadata lookup, fetch, public key discovery, revocation refresh or proof upgrade.

## 2. Explicit references, authority and store

| Local reference | Meaning and authority |
| --- | --- |
| Artifact selection | One to 64 locally authorized regular files for register; optional subject-to-file mapping for verify. Local host resolves names/paths within its approved scope. No URL, remote mount fetch or model-selected arbitrary path is introduced. Existing subject naming/digest rules remain §4.1; a local path is not automatically a public subject name. |
| `keyRef` | Explicit local signing capability selected by the person/organisation, bound to the full public-key SHA-256, not the 16-hex lookup hint. No private key bytes or credentials are passed in model-visible arguments. No automatic key generation, identity-provider login, default key selection or runtime-owned-key assumption. |
| `policyRef` | Explicit verifier-local policy snapshot, including quorum, roots/groups, trusted/recovery keys, revocation material, look-back and verification time as in [trust-policy.md](../../spec/trust-policy.md). Resolve only locally and record the exact snapshot used. Do not adopt policy from an untrusted bundle or agent message. Missing policy is a local input failure, not implicit trust. |
| `storeRef` | Explicit host-authorized private local store. Opaque bundle/result IDs resolve only in that store and caller context; they are not public URLs, global discovery keys or filesystem paths. Knowing an ID does not grant store access. |
| Consent | Host-mediated approval covering operation, selected artifacts/exact byte digests, signing key anchor, destination store and optional claims. Tool annotations and an agent's own message do not grant consent. Changed bytes/key/destination/claims invalidate that approval; reselect/reapprove instead of silently signing changed content. |

Registration should read and hash a bounded snapshot of authorized bytes, obtain consent tied to those digests, and sign exactly that snapshot. Unavailable or changed bytes abort rather than silently rebinding consent. The host chooses how to provide stable snapshots under its existing local access policy; no file-locking/sandbox implementation is asserted here. Private state is written atomically: a success ID becomes visible only after a complete bundle is persisted. Failed/canceled attempts expose no success ID. In-memory keys/nonces and local scratch state must not appear in model-visible errors. The storage implementation, quotas and platform permissions require later implementation review, not a new normative format in this draft.

For verify, no signing-key capability is needed. Consent is scoped to local reads, the selected policy and any optional result persistence. Verify neither changes a bundle/key/policy nor acquires fresh evidence. An opaque ID from another store/context is not silently resolved elsewhere.

## 3. Register operation

| Stage | Proposed local design |
| --- | --- |
| Inputs | Authorized artifact selections; explicit `keyRef`, `storeRef` and `policyRef`; host consent; optionally an already authorized exact catalogue opening and permitted self-declared claims. No implicit catalogue generation or new fingerprint study. Claims remain constrained by §4/§4.7; claimed creation time is not proved. |
| Local construction | Reuse registration §§4, 10 and 14: exact subject digests, OS-CSPRNG fresh nonce, salted possession values, optional exact-byte catalogue commitment and DSSE signature over the prescribed payload. The key is selected explicitly; its possession says nothing about who created the content. Preserve raw signed bytes and any exact catalogue bytes locally. |
| Time handling | Construct/sign without live time acquisition. Empty time evidence is permitted by the adopted [timestamp adapter decision §2](../../docs/decisions/timestamp-adapter-decision.md#2-decision). A valid signed statement is not a registration with proved time. Do not fabricate an evidence, queue a background submission, or infer a time bound from the operation clock. |
| Policy and preflight | Validate the supplied local policy and access/consent before committing private state. An explicitly supplied policy may classify the signing key untrusted; report it as such rather than editing policy. Local verification uses that snapshot and retained material only. |
| Persisted output | Complete signed bundle, exact payload/statement identity, private references to the selected artifact/catalogue material as appropriate, consent context, and the full §10 verification result/policy snapshot. Consent context/store index is local bookkeeping outside the signed versioned statement. No new statement claim or public identity field is added. |
| Agent-visible output | Opaque `bundleId` and `resultId`, `statementSha256`, per-signature public-key anchor and separate verification outcome projection, fixed `notShown`, plus the required notice/rendering. No content, private key, nonce, local path, catalogue or raw bundle is returned to a model. An ID is a local handle, not evidence by itself. |
| Repetition/cancellation | Each consented completed register invocation makes a new registration with a fresh nonce. It is not idempotent. Do not automatically retry an ambiguous signing/store response: inspect the local operation receipt through the host before offering a new registration. Cancellation before atomic commit gives no committed success; cancellation after commit must report that a local receipt exists, not pretend nothing happened. Exact request deduplication/transport signaling awaits the later adapter design. |

The agent-visible outcome projection preserves each §10 dimension, with no aggregate “verified” flag: envelope, signatures, signer trust, statement, subject/possession matches, catalogue opening, each time evidence, per-signature quorum/bounds, claimed-time status and declared-AI-use status. Full detailed results, raw diagnostics and policy data remain locally addressable by `resultId`; local-path/source-description values are not echoed into the projection. Missing supplied artifact bytes remain `not-supplied`; no time roots yields `none-valid`, and no trusted signature means claimed time is `not-compared` as specified. This projection is a proposed privacy-preserving view, not a replacement canonical verification result or a claim that an existing renderer implements it.

## 4. Verify operation

| Stage | Proposed local design |
| --- | --- |
| Inputs | Explicit `storeRef` and authorized `bundleId` (or a host-approved local bundle input), `policyRef`, and optional artifact bytes, exact catalogue opening and key-event bundles. The host resolves all references locally. Supplied bundles/events are untrusted data, not instructions or policy. No `keyRef` is requested. |
| Reads and checks | Reuse §10/§10.1 and [trust-policy.md](../../spec/trust-policy.md). Verify exact DSSE payload bytes, signature/key identities, statement, optional subject/possession values, catalogue, retained evidence and key events under the explicit policy. Use the verifier's retained header/checkpoint and revocation sources; never a bundle-selected network source. |
| Outcomes | Retain every independent result dimension listed in §3 above, including rejected/unsupported evidence and per-key bounds. Subject `mismatch`, signature `invalid`, signer `untrusted`, `below-quorum` and `none-valid` are meaningful results, not generic execution failure. No signature or time outcome upgrades any other. |
| Store/output | Return the same sanitized separate-outcome view and notices as register, plus an opaque `resultId` if the host consents to result persistence. Verification is read-only with respect to the bundle, key and policy; optional local result recording is a separately disclosed write, not a claim that the complete operation has no writes. No result export/publication is implicit. |
| Retry/cancellation | With identical bundle bytes, optional inputs and policy snapshot/verification time, semantic results should agree; no run-to-run byte identity is claimed here. A canceled computation supplies no completed verification result. A retry never renews evidence, signs, modifies policy or calls a service. |

If the bundle cannot be resolved/read or the policy is invalid, return an operation error rather than a fabricated result. If parsing can produce the normative malformed outcome, preserve that outcome and its existing diagnostic code; do not recast it as a valid bundle. Missing optional artifacts must not prevent verification of the signature/evidence that can be evaluated.

## 5. Errors and diagnostics for both calls

These are proposed **conditions**, not new normative rejection-code strings or transport mappings. A later adapter must map them to its chosen protocol without losing existing registration outcomes. Existing checker codes are evidence about the specification fixtures, not implemented tool errors.

| Condition | Proposed response / effect |
| --- | --- |
| Missing/invalid reference; wrong store context; unauthorized path/store/key; absent policy | Refuse before signing or disclose no success ID. Give a bounded model-visible category and a local diagnostic reference; no private path/secret echo. |
| Consent absent/denied, selected bytes changed, key identity changed | Stop; require fresh host consent. Never fall back to another key, artifact or destination. |
| Local read/resource failure, nonce source failure or signing capability failure | Abort register before commit; no weak randomness or unsigned-success fallback. Verify reports operation failure for unavailable required inputs; optional absence is represented by §10. |
| Persistence failure or interrupted reply | Preserve a host-local operation receipt sufficient to distinguish a committed bundle from no commit. Do not claim success before commit or invite blind signing retries. No distributed exactly-once guarantee is claimed. |
| Invalid signature, malformed/unsupported statement, wrong target, rejected key event, untrusted root or unavailable retained revocation data | Report the corresponding existing distinct §10 outcomes/codes where evaluable; do not stop unrelated checks or claim trust from validity alone. |
| Any requested network/time acquisition, public lookup/export or hosted route | Refuse/defer outside this initial scope. Register may proceed only as a separately consented local-only operation, with no proved time invented. Verify never performs network fallback. |
| Claim of authorship, origin, creation priority or disallowed AI-use claim | Apply existing statement/rendering rules; do not create a new creator/agent field or paraphrase it as a verified property. |

Retain original underlying diagnostics locally for review. A sanitized projection does not alter their meaning or demonstrate SK.1 diagnostic pass-through or SK.2 canary conformance. Secrets and source paths should not enter model-visible output at all; runtime enforcement and leak tests belong to later implementation work.

## 6. Off-machine data and optional evidence

“Only digests go on the wire” describes **off-machine content-derived request payloads**, not every byte of a protocol exchange. Local stdio inputs may contain paths/bytes but must not be relayed to a remote host/model. The initial route performs no outbound contact.

| Possible later hop | Content-derived value | Other exposure / dependency |
| --- | --- | --- |
| Local tool → approved RFC 3161 TSA | SHA-256 imprint of the raw decoded DSSE signature; not the artifact digest, statement digest or envelope text | Request nonce, algorithm/policy fields, IP, timing, TLS/HTTP metadata. Returned token/certificates are evidence bytes, not just digests. Explicit service/provider/terms authorization remains required. |
| Local tool → approved OpenTimestamps calendar | Signature digest, with the timestamp client's nonce processing | IP/timing; permanent public Merkle root commitment; upgrade/header sources remain separately controlled. No such submission occurs here. |
| Local tool → optional hosted witness | Exactly the §19.3 signature-digest presentation payload | Authentication identity, message ID, protocol metadata, IP/time; signed witness artifact returns identity and evidence. No raw content, URL/text content, fingerprints or possession nonce. SK.5 remains undecided. |

A bare artifact/content digest is not substituted for the randomized statement's signature digest: it would permit guessed-file confirmation. Publishing a bundle/statement/catalogue later has the disclosure consequences of registration §5, including related subjects/catalogue entries; a local opaque ID does not authorize that publication. Digest-only remote submission does not erase caller metadata or prove anonymity.

Offline verification accepts only retained material under the selected policy, as of its recorded dates. If witness evidence is supplied locally, apply §6.3: the witness key and backing TSA anchors join their independence groups. A witness backed by TSA A plus a direct TSA A token is **one** class, not a quorum of two. Reuse the resolved S4 review and shared/independent witness fixtures. Witness `receivedAt` is a claimed clock reading; proved bounds derive from its TSA, not that clock (resolved S8).

## 7. Skill mapping and required language

| Conceptual A2A skill | Initial local operation | What existing illustrative evidence shows |
| --- | --- | --- |
| `register` | §3 operation, proposed local MCP register capability over stdio | Local A2A card names the skill; [MCP register fixture](../../test-vectors/registration/fixtures/mcp-tool-register.json) illustrates path input and opaque bundle output. It lacks this supplement's explicit reference/consent contract and describes time requests; it does not implement the held-contact route. |
| `verify` | §4 operation, proposed local verification capability over stdio | Local A2A card describes separate outcomes against local files/policy. There is no matching MCP verify fixture in the pinned evidence. This document supplies design semantics, not a schema/tool registration. |

Keep A2A tag `v1.0.1`, source commit `3303592588e388e62e0f69f701af531d2f4e3991`, and wire Major.Minor `1.0` distinct. Registration §19 records MCP commit `862397cec702e8f828713071da501cf56158e8fc`, revision `2026-07-28`. These are inherited source pins, not a new check of latest upstream. The proposed registration extension URI remains a proposal; no discovery endpoint is published. No generated/published A2A JSON Schema validation or independent-client interoperability is claimed. Existing proto field-list checks and recorded MCP schema checks do not satisfy SK.4 by substitution.

Every user-facing presentation of a registration result keeps §11's allow-listed lines, per-key bounds/no-proved-time line as appropriate and these **three** fixed sentences, plus the agent notice:

> It does not show who created the content, that it is original, that the registrant was first to create it, who owns it, or that its use is permitted.
> First to register is not first to create.
> Comparing the times of two registrations does not show which was made first.
> A registration made by or through an agent shows which key signed it and, for a hosted witness, which authenticated caller presented the digest; it does not show whether a person or an agent created the content, or on whose behalf.

The word “hosted” in the notice describes a conditional case, not an enabled feature. Agent and person keys do not establish human/agent creation or delegated creation. Any optional AI-use claim remains self-declared/not checked under §4.7; a missing declaration is not “no AI.” Production rendering must refuse simulated results; illustrative renderings retain the simulated marker. Raw discovery metadata and an actual result rendering need a consistent notice policy; the proposed correction in §8 makes that distinction explicit for independent review, without weakening result notices.

## 8. Two static inconsistencies and recommended corrections

**N1 — fixed-sentence count and description scope.** At the pinned base, registration §19.5 says “two fixed §11 sentences,” whereas current §11 requires three. The rendering checker already uses three plus `AGENT_SENTENCE`; `rendering-agent.json` contains all four. Recommended exact text correction in a separately authorized normative patch: replace **“the two fixed §11 sentences”** with **“the three fixed §11 sentences”**. This proposal retains all three now; the source contract is not edited here.

Related scope: §§19.1/19.7 say skill descriptions carry required sentences, but `check_card` checks only `SENTENCE_FIRST`. Recommend explicitly distinguishing discovery descriptions from result rendering: discovery describes the operation and its limits without presenting a registration; all actual registration presentations still follow §11/§19.5. For a conservative future fixture revision, include all three fixed sentences plus the agent notice in both local skill descriptions and the tool description, then strengthen the dedicated description checks only after the wording is reviewed/adopted. This is a proposed reconciliation, not a claim existing descriptions/checkers fully enforce it, and not adoption of REG.5.

**N2 — witness request text parts.** At the pinned base, §19.3 specifies one data part and §19.4 says a `text` part is unsupported. `check_wire_parts` rejects `raw` and `url` but permits `text`; `check_request` counts one data payload without rejecting additional text parts. Thus an extra text part is not explicitly rejected by those static branches. No mutation request was executed in this task. Recommended separately authorized checker correction: in the **hosted request validator**, require exactly one part, that part's sole content variant to be `data`, and validate its existing request shape. Return the checker’s `content-on-wire` for `text`/`raw`/`url` content; retain `a2a-shape` for malformed one-of/part count/shape. A later adapter would map unsupported content to `ContentTypeNotSupportedError` as §19.4 states. Add one-data-plus-text and text-only negatives in that later patch. Do not globally prohibit all text parts in generic A2A handling or weaken the signature-digest target check. No checker/fixture/error table is changed or certified here.

## 9. Dependencies and review exit

A focused independent SK.3 review should assess both operations, consent/store/privacy/error boundaries, held-contact behavior, the notice policy and N1/N2 recommendations against the pinned §19 evidence, and disposition every finding. This is a design submission; it is not that review. Only a later authorized coordinator change may cite/accept it for SK.3.

Owner choices remain explicit: person/organisation versus agent-runtime-held keys; I0 versus per-work I0′ and whether I2 is offered; policy defaults/recovery choices; namespace publication; external providers/contact; and any adopted SK/REG wording. This design requires an explicit selected key/policy and therefore does not resolve those defaults by implication. §7's displayed I0 default and the unresolved RD4/§17 list are inherited wording to reconcile through the owner, not permission to choose for them.

SK.4 still requires its existing schema/client evidence; §19.7's generated-schema alternative needs adoption before replacing “published schema.” SK.5 requires the owner's decision on operation, key custody, accountable operator and costs, with identity-provider, privacy/retention, availability and abuse requirements if hosting is chosen. No positive hosting decision is inferred. Neither gate is closed by local design work. M3 remains held. No services, listeners, adapters, downloads, experiments, implementation, normative promotion or gate changes are included.
