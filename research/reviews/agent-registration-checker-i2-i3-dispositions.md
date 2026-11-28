# Agent registration checker I2/I3: author dispositions and review handoff

2026-11-28. Bounded offline correction against curated source
`f9f166e1ad9ed5fe595fedafc7389e5d56cfee56`, with published counterpart
`25959874d25704730c1e8ca008f65d93f3d3f5b1`. The original checker, builder,
registration specification and local-first design bytes are identical at those two
pins. The [independent review](agent-registration-local-first-4fa00c7-review.md)
was read in full; I2/I3 were still present, so this does not duplicate a later fix.
This record is the implementation author's disposition, not independent acceptance.

## Finding dispositions

| Finding | Change or explicit unresolved choice | Evidence and limits |
| --- | --- | --- |
| I2: descriptions only checked First-to-register | Card skills (both local operations and the illustrative witness) and the MCP tool description now require each complete §11 sentence plus the §19.5 agent sentence. Existing illustrative descriptions and their inherited shape negatives carry all four. | Conservative enforcement of existing required language; no discovery-description exemption, new notice wording, normative count correction or REG.5 adoption. Eight focused tests include deleting each of four notices in each of four descriptions, incomplete punctuation, non-string text and notices present elsewhere but absent in the target skill. |
| I3: hosted request permits extra text | Hosted requests require exactly one structurally valid data part. Text/raw/URL content is rejected alone, before or after valid data, and with count/payload faults. Same-part mixed content fails one-of. Exact payload version/kind and full 64-lowercase-hex string remain required, followed by the existing signature-digest target check. | Ten new illustrative negatives (four description, six request) plus dynamic mutations. Wrong digest retains `evidence-wrong-target`; fingerprints retain `forbidden-field`; generic task/text handling is unchanged. No service/client ran. |
| I1: §19.5 says two fixed sentences, §11/checker use three | **Proposed correction only:** replace “the two fixed §11 sentences” with “the three fixed §11 sentences” in §19.5. | Normative file unchanged. Existing three result notices and agent notice remain intact. No permission to omit a notice is inferred. |
| I4: §19 prose/examples use witness draft-1, checker/fixtures use draft-5 | **Unresolved normative choice**, detailed below. Current draft-5 checker/fixture identifiers and draft-1 extension URI are retained. | A regression records current draft-5 request acceptance and draft-1 rejection; that is a description of checker behavior, not a declaration that the normative discrepancy is resolved. No witness format or signed evidence was changed. |
| C1: projection list omits key-event outcomes | Named “separate per-key-event outcomes” explicitly in the design's §3 list. | Existing “each §10 dimension” rule, §10 step3, design §4 event evaluation and full result already require these. No outcome, schema, API or key-event behavior was added or changed. |

## Hosted request first-failure precedence

This is a deterministic fixture-checker diagnostic rule, not a new protocol error
namespace or a claim about any client adapter. Each stage returns before later stages:

1. Outer envelope/message fields, role/extension; parts must be an array and every
   part must have exactly one allowed content variant and no unknown part fields:
   `a2a-shape`. Thus data+text in one part is malformed one-of even when another
   part contains raw data.
2. Any well-shaped text/raw/URL part: `content-on-wire`, including an extra part and
   a combination with a duplicate data/count or bad digest/version fault.
3. Exactly one part, with an object data body: otherwise `a2a-shape`.
4. Forbidden fields in data: `forbidden-field`, ahead of payload/target faults.
5. Existing request-version/presented-object/kind/digest shape: `a2a-shape`.
   Digest must be a string matched in full; trailing-newline and numeric false
   accepts are rejected under the existing 64-hex-string requirement.
6. Digest is compared with SHA-256 of the referenced DSSE signature bytes:
   `evidence-wrong-target` for a shaped but wrong target.

The generic `check_wire_parts`/task behavior is unchanged, including generic text
parts. This is not an exhaustive protocol metadata/privacy validator. Auth identity,
message IDs and transport/IP/timing metadata remain distinct from content-derived
payloads, as the existing design says. No network, hosted witness, listener, adapter
or protocol client is operated or contacted.

## I4 exact choices held for separate normative review

- **Proposed alignment A:** change §19.2's proposed witness predicate URI from
  `https://traceweave.org/predicate/witness/draft-1` to
  `https://traceweave.org/predicate/witness/draft-5`, and §19.3's request example
  from `traceweave-witness-request-draft-1` to
  `traceweave-witness-request-draft-5`. Review the witnessVersion description in
  the same alignment. This preserves current illustrative checker/evidence bytes.
  The separate `https://traceweave.org/a2a/ext/registration/draft-1` extension
  identifier is not silently renamed by this choice.
- **Alternative B:** retain the draft-1 witness/request normative identifiers and
  separately design the checker/fixture migration, version handling and any
  re-signed illustrative witness statements it requires. Do not relabel a signed
  payload or promote the old example as currently accepted checker input.

Neither option is adopted here. This portion stops at the explicit choice; a
normative decision/review is needed before a hosted adapter or SK.4 conformance
claim. I1's count correction and the older proposed discovery/result distinction
also remain separate proposals, not edits to the current normative contract.

## Fixture preservation and reproducibility

Only illustrative SK card/tool descriptions, their inherited card/tool shape
negatives, and ten new SK negatives change. All signed bundles/statements, evidence,
real-format vectors, task, request positive, renderings, key-event vectors and other
frozen sets remain unchanged. The builder's LIMIT composition is updated for future
reproduction; a pure `build_agent_checker_negatives` function reproduces the new
negative JSON from existing public inputs and is called by the existing builder.

No full fixture rebuild or builder key/signature-generation path was executed.
Existing checker cryptographic self-tests still execute on their already public
test values; no new key, credential or persistent signed material is produced. Materialized
changes use JSON description updates and AST-selected pure fixture writers only.
Tests execute only selected card/tool builders and the pure negative writer,
not the builder module's public-key setup or signing paths. The ten new negative
files are reproduced byte-for-byte in a tiny temporary fixture tree. Full validation checks existing recorded cryptographic
vectors offline; it does not create new registration material.

`tests/test_agent_registration.py` supplies eight focused tests, with mutation loops
for per-description notices, content permutations, one-of/count/body errors, multi-
fault precedence, malformed digest values, wrong signature target and current
version drift. The registration checker reports **86 positive /157 negative /46
wrong-implementation cases,57 codes exercised**, all as expected. These are fixture
counts, not roadmap gate counts or native implementation conformance.

Required repository checks use the existing pinned Python environment under OS
network denial: `tools/validate.py`, `tools/validate.py --links-all`,
`python -m unittest discover -s tests -v`, `tools/check_hygiene.py`, and
`git diff --check`. Results: repository validation passed; all Markdown links passed; all37 unit tests
passed (including the eight focused tests); hygiene and whitespace passed. Exact
commands and final source commit are also supplied in the handoff.

No normative `spec/`, schemas, profiles, ROADMAP gates/counts, namespace/default
policy, native CLI, browser, service, deployment, acquisition, corpus or M3 run is
changed or invoked. SK.4 is not closed; published-schema/client conformance is not
claimed. Batch B/formal WEB.6 remain separate; M3 HOLD.

## Exact changed paths

- `research/drafts/agent-registration-local-first.md`
- `research/reviews/agent-registration-checker-i2-i3-dispositions.md`
- `test-vectors/registration/README.md`
- `test-vectors/registration/build_fixtures.py`
- `test-vectors/registration/check_registration.py`
- `test-vectors/registration/fixtures/a2a-card-hosted-witness.json`
- `test-vectors/registration/fixtures/a2a-card-local-registrar.json`
- `test-vectors/registration/fixtures/mcp-tool-register.json`
- `test-vectors/registration/negative/neg-a2a-shape.json`
- `test-vectors/registration/negative/neg-card-notice-missing.json`
- `test-vectors/registration/negative/neg-hosted-plain-http.json`
- `test-vectors/registration/negative/neg-local-register-agent-notice.json`
- `test-vectors/registration/negative/neg-local-register-limit-notice.json`
- `test-vectors/registration/negative/neg-local-verify-order-notice.json`
- `test-vectors/registration/negative/neg-mcp-agent-notice.json`
- `test-vectors/registration/negative/neg-mcp-tool-shape.json`
- `test-vectors/registration/negative/neg-witness-duplicate-data.json`
- `test-vectors/registration/negative/neg-witness-empty-parts.json`
- `test-vectors/registration/negative/neg-witness-extra-text.json`
- `test-vectors/registration/negative/neg-witness-extra-url.json`
- `test-vectors/registration/negative/neg-witness-mixed-part.json`
- `test-vectors/registration/negative/neg-witness-text-only.json`
- `tests/test_agent_registration.py`
