# Synthetic examples

`artifact.txt` contains exactly the three bytes `abc`, with no newline. `profile-config.json` and `catalogue.json` are synthetic fixture data, not a production extractor or a real private catalogue.

`statement.json` is an **unsigned** statement. It binds the exact artifact digest and exact configuration bytes to a commitment over the fixture catalogue. The opening uses the public test nonce recorded in `test-vectors/commitment.json`. Never use that nonce for real content.

The fixture catalogue uses the demonstration profile `exact-bytes-fixture`; it has no similarity detector. Its source bytes, config and nonce are public solely to make the vector reproducible. No genuine signing key, timestamp token or attestation is included.
