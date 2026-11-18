# Attestations and interoperability

Status: proposed adapter, not a shipping signing implementation.

## in-toto and DSSE

The draft in-toto adapter uses `_type: https://in-toto.io/Statement/v1`, one subject with a SHA-256 digest, and the predicate identifier defined in the statement schema. This is a deliberately restricted Traceweave adapter, not a complete validator for arbitrary in-toto statements. Draft predicate identifiers under the project GitHub URL are provisional; they are not standards registrations.

For DSSE, `payloadType` is `application/vnd.in-toto+json`. Sign the actual decoded payload bytes using the upstream pre-authentication encoding:

```text
PAE(type, body) = "DSSEv1" + SP + LEN(type) + SP + type + SP + LEN(body) + SP + body
```

Lengths count bytes, encoded as ASCII decimal without leading zeroes. `SP` is the ASCII space byte. The payload's base64 text is not the signing input. Retain the verified byte sequence through parsing. Reject ambiguous JSON (including duplicate keys) under a documented parsing policy. Key identifiers are lookup hints, not proof of identity. [DSSE protocol](https://github.com/dsse-lf/dsse/blob/master/protocol.md), [in-toto statement](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md).

A signed statement can remain intact while a derived artifact changes. In that case the statement signature may verify while the subject digest fails. Report both results separately; a soft match does not repair that digest.

## Trust and time

Verifiers need a configured trust policy identifying accepted keys or issuers and subjects, algorithms, certificate validation rules, and compromise handling. Identity strings inside a signed payload are assertions, not independent identity authentication. Signing someone else's public content does not establish ownership.

Self-managed signing and private evidence storage are design targets. Sigstore is an optional integration, not a mandatory public log. Its bundle format supports verification material including keys, certificates, timestamps, and transparency entries. Short-lived certificate verification needs appropriate signed time evidence; it does not require every deployment to use both Rekor and RFC 3161. [Sigstore bundle format](https://docs.sigstore.dev/about/bundle/).

An RFC 3161 integration must preserve and verify the signed token, message imprint, algorithm, TSA signature, trust chain and applicable time policy. An ISO date string is not a timestamp token. The exact object timestamped must be specified. Long-term archival verification also needs retained trust material and an algorithm-renewal strategy; a timestamp alone does not guarantee decades of validity. [RFC 3161](https://www.rfc-editor.org/rfc/rfc3161).

## C2PA mapping remains open

Traceweave should reuse existing content-provenance infrastructure where possible. No C2PA compatibility is claimed yet. A future mapping must specify hard bindings, soft-binding discovery, assertion transport, signer trust, private disclosure, and independent test artifacts. Referencing C2PA terminology does not establish interoperability.
