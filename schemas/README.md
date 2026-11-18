# Draft schemas

`evidence.schema.json` defines the shared predicate. `statement.schema.json` defines a restricted in-toto v1 adapter with one exact SHA-256 subject and that predicate.

Schema dialect: JSON Schema 2020-12. IDs are provisional project URLs. Consumers should resolve schemas from a pinned local checkout rather than fetch arbitrary references from untrusted evidence.

These schemas deliberately exclude raw private fingerprints, keys, and nonce openings from the public predicate. They do not enforce the secrecy of the host storage, authenticate an author, or validate algorithm implementations. Validation uses a date-time format checker, but `recordedAt` remains an untrusted claimed time.
