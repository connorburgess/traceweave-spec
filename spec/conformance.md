# Conformance levels

Version: 0.1.0-draft.1. Only the first level currently has local validation tooling.

1. **Record structure:** validate the draft predicate and restricted statement schemas, reject unknown fields, and preserve exact referenced bytes. Passing a schema does not validate external claims or algorithm support.
2. **Commitment opening:** recompute the specified exact-byte commitment with its private nonce. This proves correspondence to that opening, not authenticity or chronology.
3. **Attestation verification (planned):** verify a real envelope under an explicit trust policy, reporting identity and independent time results separately.
4. **Profile reproduction (planned):** independently reproduce extraction and matching vectors for a supported profile.
5. **Detection evaluation (planned):** report a measured failure envelope and false-alarm unit for the full search pipeline.

The repository checks levels 1–2 for synthetic fixtures and DSSE framing only. It has no complete DSSE signer/verifier, token extractor, resolver, or benchmark corpus. Claiming conformance MUST name the draft version, level, profile versions, and tested implementation.

Stable profiles require two implementations that agree on positive and negative vectors. Experimental profile documents are not approved algorithm registrations. CLI names and agent workflows are optional implementation interfaces, not core conformance requirements.
