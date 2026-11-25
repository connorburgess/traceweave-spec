# Test vectors

`dsse-pae.json` includes the upstream DSSE hello-world framing example, a UTF-8 byte-length case, and an empty-input framing case. It tests framing, not signature verification or permission to use empty payload types in a higher-level protocol.

`commitment.json` fixes a synthetic nonce and catalogue bytes for the proposed exact-byte commitment. The nonce is intentionally public. Do not reuse it in real evidence.

Negative contract cases live in `tests/test_contract.py`. They cover malformed statement types, unsupported record versions, empty subjects, truncated digests, secret fields, ambiguous JSON, and changed commitment openings. No detection-accuracy claim follows from these tests.

Promoted experimental vector sets, each with a checker that must exit 0 (`tools/validate.py` runs them):

| Directory | Contents | Contract or profile |
| --- | --- | --- |
| [extraction](extraction/README.md) | Go and Rust token-fingerprint vectors, configurations, Unicode tables, checker and cross-check harness | [Extraction contract](../spec/extraction.md) |
| [matching](matching/README.md) | Catalogue, comparison and report vectors, extraction records, behaviour checklist, checker (with self-tests) and builder | [Catalogue and report contract](../spec/catalogue-report.md); schemas in [schemas](../schemas/README.md) |
| [extraction-typescript](extraction-typescript/README.md) | `ts-tokens` vectors (frozen); `tsx-tokens` vectors (deferred draft) | [TypeScript/JavaScript profile](../profiles/typescript.md) |
| [extraction-python](extraction-python/README.md) | `py-tokens` vectors (frozen, `draft-1`) | [Python profile](../profiles/python.md) |
| [extraction-text](extraction-text/README.md) | `text-plain` vectors (frozen); `text-markdown` vectors (draft) | [Text profile](../profiles/text.md) |
| [intoto-adapter](intoto-adapter/README.md) | Restricted in-toto Statement v1 / DSSE adapter accept and reject fixtures (`0.1.0-draft.1` and `registration-draft-5`) | [Attestations](../spec/attestations.md); [trust policy](../spec/trust-policy.md) |
| [registration](registration/README.md) | Offline-first registration, key-event, time-evidence, real-format RFC 3161 / OpenTimestamps, `tw1-`, and `claims.aiUse` fixtures | [Registration record](../spec/registration-record.md); [trust policy](../spec/trust-policy.md) |

The mapping from the earlier `research/drafts/` locations, with SHA-256 digests before and after, is in the [promotion map](../research/promotion-map.md).
