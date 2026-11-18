# Implementation patterns and examples

Status: design proposals. These interfaces and example names are not shipped APIs or CLI commands. See [use cases](use-cases.md) and the [roadmap](../ROADMAP.md).

## Embed and detect as an explicit pair

Proposed interface: original bytes + mark + embedding profile/config + any required secret/randomness → marked bytes + private embedding record. Validate the output before distribution. Record both original and marked digests; do not confuse their exact identities. Retain test randomness for reproducibility without reusing fixture secrets in production.

Detection consumes candidate bytes, a supported detection profile and the verification material that profile requires. Specify whether it is blind, reference-assisted or key-assisted. Return localized evidence, unsupported input, or insufficient evidence; do not hide detector assumptions behind a single confidence score.

Keep embedding, extracted matching and provenance verification independently testable. Compare mark-only, fingerprint-only and combined detection on the same held-out cases. A copied mark can be transplanted onto unrelated material, so bind the private record to artifact context and preserve this limitation even when cryptographic checks pass. The marking algorithm remains a research decision.

## Keep deterministic extraction separate from comparison

Use a small pure extraction core: artifact bytes + supported profile + exact config bytes → features, source spans and diagnostics. An unsupported profile is an explicit error. Parser errors must follow a specified policy; no silent tokenizer substitution. Source coordinates refer to original bytes, with a separately defined human-readable line/column conversion.

Start with literal-preserving tokens. Add identifier normalization as a separately versioned channel only when scope behavior is defined. Keep original spans through normalization. Pin grammar/tool versions; serialize tokens unambiguously before hashing. Whole-file hashes serve exact identity; fingerprint features serve candidate retrieval.

For winnowing, specify k, window width, hash representation, ordering, ties and deduplication. A hand-checkable selection example uses hash values `[8, 4, 4, 7, 2]` and window width 3. Rightmost minima select positions 2, 2, 4 (zero-based), so retained unique positions are `[2, 4]`. This illustrates selection only, not a production hash or detection threshold. The [original paper](sources.md) supplies the locality argument, not an empirical false-alarm guarantee.

## Treat storage as a boundary

Keep private catalogues and commitment openings outside the source checkout by default. Bind each catalogue to profile/version, config digest and exact artifact digests. Save exact bytes before computing a commitment; write atomically so interrupted writes cannot replace a valid opening with a partial file. Public demonstrations use synthetic material and obviously non-production fixtures.

Candidate retrieval should be a replaceable local index over features. Follow retrieval with span alignment and explicit scoring. Keep multiplicity, coverage denominator and common-feature policy visible. Index ranking is not the evidence report.

## Preserve independent verification results

A proposed internal result model has independent fields for exact subject, signature, signer trust, timestamp, comparison and rights-review state. Each can be passed, failed, not checked or unsupported where meaningful; comparison additionally distinguishes candidate and insufficient evidence. Do not collapse these into one green verification badge. Field names are subject to TW-03 schema design.

Example: a signed record describes artifact A, while candidate B is a modified derivative. The signature over the original record can pass, B's subject digest can fail, time can be unchecked, and comparison can return candidate spans. None of those results overrides another. Rights remain for separate review.

DSSE verification consumes exact decoded payload bytes with upstream PAE. Use a maintained cryptographic library for algorithms and key handling; keep trust policy explicit. Duplicate JSON keys, excessive input sizes and unsupported algorithms require documented rejection behavior. Parsing or reserialization must not replace the signed byte sequence. See the [source register](sources.md).

## Example matrix

Every implemented example should contain redistributable input bytes, frozen config, expected outputs, a reproduction command and an explanation of what it establishes. Never present a planned example as a measured result.

| Proposed fixture | Case | Expected assertion |
| --- | --- | --- |
| Marked round trip | UC-6 | Supported mark detected with its required material; output passes defined functional/quality checks |
| Unmarked / wrong mark or key | UC-6 | False detections measured; no assumed zero-error guarantee |
| Removal / transplantation / partial marked fragment | UC-6 | Survival and localization measured; transplant does not imply whole-artifact origin |
| Exact reference/candidate | UC-1 | Exact digest agreement and correct full span |
| Formatted fragment in a large host | UC-1 | Correct localized token match; separately reported containment and whole-file score |
| Identifier rename and shadowing | UC-1 | Channel-specific results; a scope-aware channel must distinguish shadowed bindings |
| Independent same-task implementation | UC-1/5 | Negative control retained in calibration; any match is counted, not silently removed |
| Common boilerplate/vendor region | UC-2/5 | Origin evidence and common-feature handling remain visible; no proprietary attribution |
| Historical permitted copy | UC-2 | Ancestry can match while rights review reaches a separate conclusion |
| Unsupported grammar / malformed source | UC-1 | Explicit unsupported/error outcome according to frozen parser policy |
| Unicode / repeated minima / tiny file | UC-1 | Stable spans, deterministic tie handling and documented insufficient-length behavior |
| Changed nonce, catalogue or length | UC-3 | Commitment opening rejected; unchanged synthetic opening accepted |
| Changed DSSE body/type/signature | UC-4 | Authentication fails under the selected verification contract |
| Valid signature from an untrusted key | UC-4 | Cryptographic validity cannot satisfy signer-trust policy |
| Valid signed record, changed subject | UC-4 | Signature and subject-digest outcomes stay separate |
| Missing/untrusted/wrong-imprint timestamp | UC-3/4 | No trusted-time success; reason preserved |
| Rewrite that destroys token overlap | UC-5 | Failure or abstention recorded; behavior validity assessed independently |

Existing fixtures in [examples](../examples/README.md) and [test vectors](../test-vectors/README.md) cover format/commitment/framing demonstrations only. Cryptographic negative tests and detection examples above are future work.

## Reproducible evaluation, then adapters

Record corpus identities and rights, group related versions before splitting, freeze thresholds before held-out tests, and measure the entire repository-search pipeline. Record candidate volume and runtime as well as accuracy. A unit test proves fixture behavior; a benchmark supports scoped performance claims; an independent implementation checks interoperability. These are different gates.

Choose optional CLI, agent and provenance adapters after the core data contract stabilizes. Wrappers must preserve diagnostic detail and private storage defaults. A resolver or public log needs a separate disclosure design; it is not part of the local extraction path.
