# Provenance and omitted proof

Upstream ThreatExchange pin: `9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2`.
The original raw Git commit body was 1,135 bytes, SHA-256 `7882c170759184eddf668891bb1311f65f7a214e00816b9a78e1e787eaf48079`; its Git commit identity was the pin. It is retained privately, unchanged, and is absent from this package in every representation.

Historical private verification recomputed that commit identity and bound its tree header to root `dbd86e307c396ab13c3d261126732be72163295e`. **The published package cannot reproduce the commit-to-root binding.** The pin, size and digest identify the omitted bytes; they do not replace them. `original-provenance-verification.json` is an unchanged historical report, not a new public proof. Its 207-tree verification count and API signature report describe the earlier private check. Local signature authentication was not performed; no signer identity, immutable acquisition chronology or parent-chain authenticity is established here.

The published `source-tree-proof.json` supplies six complete immediate-child tree listings. The public inspector recomputes those six Git tree identities, checks their chain to the supplied root, and checks membership of the 17 source-subset leaves declared by `acquisition.json`. This establishes internal consistency relative to the supplied root, independently of the missing commit body. Optional provisioned-source verification additionally hashes actual leaf bytes. Tree listings alone do not supply those bytes or prove the root belongs to the pinned commit.

`original-artifact-identities.json` identifies historical artifacts by digest and size; those original artifacts are not thereby included. `python-source.json` identifies the 13-path frozen Python export at `6f39e50f33026c9f1d9526c2a566d6a447219667`. The comparison records a historical run under reported network denial. Rechecking its stored hash/quality accounting does not repeat that run or prove the recorded environment.
