# Roadmap

## Present draft

- Separate exact evidence from similarity claims and rights analysis.
- Define a minimal private catalogue commitment record and optional in-toto adapter.
- Supply synthetic examples, schema checks, commitment vectors, and DSSE framing checks.
- Record the initial review and remove unvalidated numerical guarantees.

## Next: code baseline

1. Inspect the actual target repositories, languages, artifact types, ownership records, and license histories. Record region-level origins; do not infer rights from a single cutoff commit.
2. Specify one deterministic token profile: parser revisions, normalization channels, hash encoding, window selection, tie-breaking, spans, and partial-file containment.
3. Implement local catalogue creation and explainable matching. Compare exact, normalized, and structural baselines before adding secret feature selection.
4. Evaluate unrelated same-stack repositories and independently written same-specification functions. Freeze thresholds before held-out tests.

Gate: reproducible candidate spans and honest abstention, with measured false alarms per repository search. No required recall number has yet been established.

## Then: evidence verification

Implement real signing and trust policies using established libraries. Add negative cryptographic tests, key rotation and compromise handling, timestamp verification, and an independent second implementation. Distinguish private signing from optional public transparency. A current schema check is not a cryptographic verifier.

Gate: cross-implementation byte-level vectors and independent review of the commitment and disclosure design.

## Optional extensions

- Experimental local structural watermarking, only if it improves recall at the same false-alarm budget without behavior or performance regressions.
- An agent skill that invokes local tools without putting keys or private catalogues in model prompts.
- Text/image/audio/binary profiles with separate benchmarks, including partial reuse.
- A resolver only after a defined query privacy model and disclosure policy.
- C2PA interoperability with an explicit mapping and test fixtures.

These are proposals, not shipped features. The core remains usable without an agent, resolver, or public registry.
