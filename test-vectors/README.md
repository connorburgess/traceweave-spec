# Test vectors

`dsse-pae.json` includes the upstream DSSE hello-world framing example, a UTF-8 byte-length case, and an empty-input framing case. It tests framing, not signature verification or permission to use empty payload types in a higher-level protocol.

`commitment.json` fixes a synthetic nonce and catalogue bytes for the proposed exact-byte commitment. The nonce is intentionally public. Do not reuse it in real evidence.

Negative contract cases live in `tests/test_contract.py`. They cover malformed statement types, unsupported record versions, empty subjects, truncated digests, secret fields, ambiguous JSON, and changed commitment openings. No detection-accuracy claim follows from these tests.
