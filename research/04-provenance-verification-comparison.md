# Private provenance: paired report review

Reviewed 2026-11-18. Both provider reports are preserved unchanged in ignored local provider directories. This is a targeted review, not a cryptographic audit, library certification or adopted protocol. See the [initial review](04-provenance-verification-initial-review.md) for the Perplexity findings.

## Decision

Both reports support testing offline verification with established signature envelopes, exact artifact digests, private commitments and separate trust decisions. Google supplies a more concrete negative-test matrix and identifies RFC 5816, but also replaces existing draft choices without demonstrating compatibility. Neither report establishes a working Go/Rust interoperability pair.

Proceed with a small signing interoperability experiment using synthetic byte fixtures and public test-only keys. It can run independently of carrier research. No production embedder, timestamp service or new normative schema is required to begin.

## Corrections before implementation

1. **Retain the existing commitment for the first experiment.** [Core](../spec/core.md) defines SHA256(D || R || L || C), a fixed domain, exactly 32 nonce bytes, an explicit length and exact catalogue bytes. Google's replacement prefixes and mark-payload scheme are new proposals. A salted hash is not a proof that a hidden mark was correctly embedded. The current opening reveals the entire catalogue; selective disclosure and zero-knowledge verification are not provided.
2. **Define artifact roles without silently changing the adapter.** The current adapter has one subject. Google's mandatory original/marked positional pair is incompatible with it and is not required by [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md). Record which artifact is attested and separately design any original-to-marked relationship. Subject names inside the signed payload are authenticated claims; they are not unauthenticated DSSE key hints. Artifact matching uses digests, while names can have policy semantics. An exact digest mismatch on edited content must remain separate from any later empirical comparison.
3. **DSSE does not eliminate parser vulnerabilities.** [DSSE v1.0.2](https://github.com/dsse-lf/dsse/blob/v1.0.2/protocol.md) authenticates payload type and serialized body using PAE. Preserve those bytes. Envelope parsing and base64 decoding still precede signature verification; authenticated payloads also require safe parsing. Resource limits and duplicate-key handling need explicit implementation tests. JCS is not automatically required by DSSE. [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html) preserves Unicode string data; its source-ledger description as normalization is misleading.
4. **Timestamp evidence is optional and has a precise target.** [RFC 3161](https://www.rfc-editor.org/rfc/rfc3161.html) supports prior-existence assertions, not an exact signing-time measurement. Hashing decoded signature bytes is a candidate target; hashing the envelope's base64 text is different. Specify the selected signature if there are several. Include [RFC 5816](https://www.rfc-editor.org/rfc/rfc5816) and chain, purpose, policy, imprint and historical trust checks. A timestamp before a revocation cutoff is not by itself a complete compromise analysis. A TSA can observe request timing and network/account metadata, so zero metadata leakage is not a defensible claim.
5. **Keep independent outcomes.** Google's sequential table makes optional timestamps and private openings mandatory and stops before detection on exact mismatch. Preserve signature validity, signer trust, exact binding, opening consistency, time evidence and empirical findings separately, including unavailable or not-checked states. Overall policy may reject a record without erasing valid component results. Mark detection remains fallible. Neither a signature nor a similarity score establishes ownership.
6. **Treat library names and budgets as hypotheses.** Version ranges ending in '+' are not reproducible pins. Identify and test actual DSSE and timestamp-verification APIs in each implementation; a collection of signing, CMS and binary-parsing libraries is not evidence of an integrated verifier. The proposed 50 ms and 32 MiB gates have no measured basis. Its 8 MiB decoded payload expands beyond its 10 MiB envelope cap even before JSON overhead. Establish coherent limits and measure performance on declared hardware.

The report's lane numbering, proposed namespace and private-application fixture names are not adopted. Use neutral synthetic fixtures. No hardware-backed key requirement, universal Jaccard threshold, mandatory public log or binary carrier follows from this review.

## Smallest testable increment

- Pin a Go/Rust DSSE implementation pair and one supported signature algorithm after checking APIs and licenses.
- Cross-verify the same raw payload in both directions, using the current single-subject adapter and existing commitment vectors.
- Test payload/type/signature mutations, untrusted keys, candidate mismatch, valid envelope reserialization, duplicate keys, resource limits and full commitment opening as distinct cases.
- Run verification without network access. Do not execute candidate content or fetch embedded references automatically.
- Add timestamp interoperability separately, with explicit byte-level target and test trust roots, only after bare-envelope verification works.

No new signing experiment was executed for this review. The report comparison completes discovery lane 4; implementation feasibility remains unmeasured.
