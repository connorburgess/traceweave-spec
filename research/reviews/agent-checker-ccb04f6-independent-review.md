# Portable independent bounded agent-checker acceptance

Labelled adaptation of review of exact `ccb04f618be462dd26ee15ab83e1539f34510d4a`. Original SHA-256 `332efc3ec26df82859ccb4d22fd8ff53874b20fe0fde97012b0b7b37ee410211`, 11097 bytes; original remains unchanged privately. Local interpreter/worktree/policy locators are replaced by caller placeholders; original Markdown attachment links are inert. Remaining body is unchanged. Examples record the historical review method and are not new execution authority. This accepts the bounded original checker/evidence patch, not this adaptation or a later combined candidate. See [author dispositions](agent-registration-checker-i2-i3-dispositions.md), [identity](agent-checker-ccb04f6-independent-review.identity.json) and [current queue](../work-queue.md).

---

# Independent review: bounded agent-registration checker I2/I3 correction

**Reviewed exact `ccb04f618be462dd26ee15ab83e1539f34510d4a`. Verdict: eligible for bounded offline checker/evidence integration; no blocking finding. I2 and I3 are corrected within the declared scope; C1 is clarified. I1 and I4 remain proposed/unresolved normative work. No native implementation, published-schema/client, hosted-service, REG.5 or SK.4 acceptance follows. M3 HOLD.**

Author worktree was read-only. This review writes only its own thread-storage directory; no author file, gate, criterion, count, integration branch or remote was changed. No native Traceweave invocation, service, download, browser, corpus evaluation or sublane was used.

## Exact identity and scope

| Item | Identity |
| --- | --- |
| Commit | `ccb04f618be462dd26ee15ab83e1539f34510d4a` |
| Parent | `f9f166e1ad9ed5fe595fedafc7389e5d56cfee56` |
| Tree | `b3fe25182f89c6053b541140e8cf13b3eeb89194` |
| Binary-capable Git diff SHA-256 | `18ca9c9513cde56ca34caca5c19be2efaf6f0b6b2bdc59da1250b80d0f7f8ae7` |
| check_registration.py SHA-256 | `d7a3108568bd52cb3648c35f381b0df04fba42e523ad39d169511119a29c21b9` |
| tests/test_agent_registration.py SHA-256 | `a177577949d1f8c7930fabb74641d6b93d0bb75d8c4133907b3dc1b422889d63` |
| Author disposition record SHA-256 | `43d981059a6978a5b5a4351c013b8c8b57cbca3490356c963067083cc0f9d6ba` |
| Unchanged spec/registration-record.md SHA-256 | `3b3bb4c23188d513a60ea715ea5a1882b7e21d7f6e9fa629e5b9cf27f67b839b` |
| Unchanged ROADMAP.md SHA-256 | `7fc37658cff86aaa707530be920394473f132986d4b03e77a7fe669e0c9d3f82` |

The exact changed-path set has23 paths and equals the author record's inventory: supplement wording, author disposition, registration README/builder/checker, three illustrative card/tool positives, four inherited card/tool negatives, ten new description/request negatives and one new test module. No `spec/`, schema, profile, README gate-count summary or ROADMAP bytes change. Among pre-existing JSON modifications, all seven differ only in description values; the ten additions are negatives. All293 other parent registration paths are byte-identical, including signed bundles/statements, evidence/real-format vectors, task/request positive, rendering and key-event material. The old illustrative positives are not re-signed or silently relabelled.

## Finding dispositions

| Item | Independent evidence and disposition |
| --- | --- |
| **I2 description notice enforcement — closed, bounded checker scope** | `check_card` checks each individual skill; `check_mcp_tool` checks its own description. All three complete §11 strings plus the exact agent string must occur in a string value. Each local register/verify skill, hosted witness skill and MCP description is independently covered. Removing/truncating each sentence, placing it elsewhere, or substituting non-string text rejects with `notice-missing`. Correct positives carry all four. No discovery-description exemption or normative count repair is adopted. |
| **I3 additional hosted text/content part — closed, bounded request scope** | `check_request` now rejects unsupported text/raw/URL parts alone or appended/prepended to valid data. Structural allowed-key/one-of errors precede unsupported content; unsupported content precedes count/body faults; exactly one object data part is required. Forbidden nested data keys precede payload shape, then full string/version/kind/digest shape precedes signature-digest target mismatch. Wrong target remains `evidence-wrong-target`; fingerprints remain `forbidden-field`. Fullmatch plus explicit string type closes trailing-newline/numeric false accepts. |
| **C1 key-event outcome projection — clarified** | The supplement now explicitly names separate per-key-event outcomes. Its pre-existing “each §10 dimension” requirement, local full-result retention and verify event evaluation remain intact. No result schema, outcome semantics, trust calculation or callable API changes. |
| **I1 fixed-sentence count — intentionally unresolved** | Normative §19.5 still says “the two fixed §11 sentences”; §11/constants retain three plus the agent notice. The author proposes a separately reviewed two-to-three correction; this commit implements the stronger existing language in illustrative checks without editing the normative sentence. |
| **I4 witness/request version drift — intentionally unresolved** | Normative §19 retains draft-1 witness/request examples while existing checker/fixtures retain draft-5; extension URI remains separately draft-1. The new regression accepts current draft-5 and rejects draft-1. Checker version constants and signed evidence are unchanged. Alignment alternatives are proposals, not adoption or a licence to relabel signed payloads. This remains a dependency before hosted-adapter/SK.4 claims. |

The unchanged historical SK.3 closure/review and roadmap reference exact older source; they are not rewritten to claim these corrections existed at that old pin. The new author disposition and this exact-commit review describe the later checker correction. Historical native86/147 evidence is likewise not converted into a native86/157 result. SK.4 and SK.5 statuses/criteria/counts remain unchanged.

## Independent adversarial checks and precedence

probes.py (original independent review attachment; not retained) uses explicit expected diagnostic sets and pinned fixture data rather than regenerating expected results from the new helper. It recorded146 bounded probes, including valid controls and a deliberately accepted metadata-limit control. Cases cover all four descriptions × four complete notices; deletion, truncation and elsewhere placement; non-string values; text/raw/URL permutations and combinations with payload/count/forbidden faults; malformed part lists/one-of/unknown keys/non-object data; nested forbidden keys; lowercase/length/type/newline/Unicode digest errors; wrong targets; and invalid outer role/extension/envelope/message fields.

The documented first failure is confirmed:

1. Envelope/message/role/extension and part allowed-key/one-of structure: `a2a-shape`.
2. Any well-shaped text/raw/URL part: `content-on-wire`, even with duplicate data or later faults.
3. Count or non-object data: `a2a-shape`.
4. Nested forbidden data keys: `forbidden-field`.
5. Version/presented/kind/full64-lowercase-hex-string shape: `a2a-shape`.
6. Shaped wrong referenced signature digest: `evidence-wrong-target`.

Controls ran the unchanged parent Python module on the same in-memory inputs: it accepts12 of the missing-notice combinations (the three previously unchecked sentences across four descriptions), and accepts valid data plus extra text. The new checker rejects these. Thus agreement is not just shared builder/checker behavior or a replay of the author's expected codes. Generic `check_wire_parts` text handling remains accepted, as intended; the stronger text restriction is hosted-request-specific.

Checked every parent positive through the new checker. The83 non-description positives remain accepted without changes; the three old incomplete-description objects now correctly return only `notice-missing`. Their revised, complete-description positives pass. The current suite passes all86 positives. This is intentional tightening of deficient illustrative descriptions, not unexplained positive compatibility loss.

**Retained boundary, not a new blocker:** this is not a complete protocol schema/type/privacy validator. Allowed protocol metadata can still hold unchecked values: a request with a `metadata.content` string is accepted. That probe establishes the documented limitation; it is not runtime leak evidence or proof of a hosted implementation. Do not describe I3 closure as “all on-wire fields contain only digests” or complete metadata/privacy enforcement. It closes the specified message-part/content/payload bypass. Other inherited structural type limitations and generic task text remain outside this bounded patch. The author explicitly disclaims exhaustive protocol metadata/privacy validation and client conformance.

## Reproduced offline validation

Used existing `$PINNED_PYTHON` only. Commands ran under the retained OS policy (original independent review attachment; not retained): deny all network and deny writes to the author worktree and shared Git metadata. Top-level Python used `-B`; the OS policy also prevents child isolated-mode imports from creating author-tree bytecode. No full fixture builder or its key/signature-generation path ran. The test module AST-selects only pure illustrative builders/writers and reproduces the ten negatives in a temporary directory. Existing checker RFC/public-test cryptographic self-tests execute on their already-public test values; no credential or persistent signed registration is produced.

| Check | Result |
| --- | --- |
| registration/check_registration.py | **86 positive /157 negative /46 wrong-implementation cases; all57 codes exercised; all expected** |
| tools/validate.py | PASS, schemas/examples/promoted vector checkers |
| tools/validate.py --links-all | PASS, every local Markdown link |
| unittest discover -s tests -v | **37 tests passed**, including eight focused tests with mutation loops |
| tools/check_hygiene.py --messages HEAD^..HEAD | PASS, tree and changed commit message |
| git diff --check HEAD^ HEAD | PASS |
| Independent146 probes/scope/frozen/positive compatibility checks | PASS |

run-checks.py (original independent review attachment; not retained), command results (original independent review attachment; not retained), registration output (original independent review attachment; not retained), full validation output (original independent review attachment; not retained), unit output (original independent review attachment; not retained), independent probe results (original independent review attachment; not retained) and probe output (original independent review attachment; not retained) retain commands and outcomes. The all-links invocation is a links-only code path, so full validation was separately executed; it is not inferred from the links pass. The full-validator command was:

```sh
cd $REVIEWED_WORKTREE
/usr/bin/sandbox-exec -f $OFFLINE_POLICY $PINNED_PYTHON -B tools/validate.py
```

To repeat the independent adversarial/scope review, run the same sandbox prefix with this directory's `probes.py`. The script imports the current and parent Python checker definitions only, never the fixture builder's top-level initialization/driver. Every tracked file (1062) was hashed before checks and remained unchanged; final author status is clean. Final integrity is recorded alongside this review.

## Bounded eligibility

Accept exact `ccb04f618be462dd26ee15ab83e1539f34510d4a` as an offline illustrative-checker correction and C1 design clarification. No author fix is required. Carry I1/I4 into their separate normative decision/review and preserve the metadata/schema/client/runtime limitations above. These are fixture/evidence counts, not roadmap gate counts or native conformance. No hosted operation, signing identity/policy/default choice, criterion change or SK.4 closure is supplied. **M3 remains HOLD.**
