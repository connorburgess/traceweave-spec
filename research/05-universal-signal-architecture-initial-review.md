# Universal signal architecture: initial review

Reviewed 2026-11-18. Perplexity's report (local input: `perplexity/05-universal-signal-architecture.md`; not distributed) is preserved unchanged. This is a design review, not adoption of its TIP schema or empirical validation. This initial review predates the Google report; see [the subsequent comparison](05-universal-signal-architecture-comparison.md).

## Useful conclusion

A shared record/interface with medium-specific carriers is a sensible hypothesis. Embedded marks remain first-class, with fingerprints as supplementary discovery. Semantic resemblance must not become a derivation claim. This complements lane 2's evaluation of attacks against particular carriers.

The standards comparison checks out at a high level. [C2PA guidance](https://spec.c2pa.org/specifications/specifications/2.4/guidance/Guidance.html) distinguishes soft discovery bindings from mandatory hard bindings and warns about false matches. [ISO's ISCC description](https://committee.iso.org/standard/77899.html?browse=ics) describes content-dependent identification across media. Neither establishes a universal robust embedder.

## Corrections before adoption

1. **Incomplete citations.** Exported `[web:1]` markers have no URL mapping. Verify decisive references and edition dates before a sourced architecture decision. The report's C2PA 2.4 date remains unverified.
2. **Payload versus record.** Signatures, issuer details and commitments can live outside the carrier. Even a 64-bit pointer is not demonstrated in our Go/Rust pilot. Capacity, redundancy, collision risk and lookup scale must determine the embedded representation.
3. **Fingerprint versus hard binding.** Signing a fingerprint authenticates a statement; it does not give that fingerprint exact-hash security or prove ancestry. C2PA soft bindings must not replace hard bindings.
4. **Hash/mark ordering.** Embedding changes content. Specify original bytes, final marked bytes, exclusions or canonicalization. One candidate flow embeds a record ID, then signs a record containing the final artifact hash. That still needs recovery/transplant tests and does not authenticate arbitrary edited descendants.
5. **Misleading outcome name.** `not_derived` cannot mean insufficient evidence. Use `inconclusive` or `no_evidence_found`. Separate record retrieval, signature validity, signer trust, exact binding, soft match and fragment scope.
6. **Distinct assets.** Code and an image can share a collection/work reference, but need separate asset identities and bindings. Giving both the same content-bound TIP makes the proposed experiment ambiguous.
7. **Insufficient experiment size.** One asset per medium demonstrates plumbing, not false-positive rates or robustness. Use multiple assets/keys, independent same-meaning controls and held-out calibration/evaluation data. Compare mark-only, fingerprint-only and combined outcomes on the same corpus. Combining mechanisms can increase false associations.
8. **Unproven rankings and gaps.** Hybrid is not automatically strongest for fragments, privacy or recovery. The report does not establish that C2PA cannot support local/private workflows. Assess interoperability and disclosures before claiming a standards gap or mandating a replacement record format.

## Proposed direction

Keep a common identity/evidence interface, with Go/Rust carriers first and TypeScript/JavaScript next. Make payload size and detection guarantees capability-specific. Evaluate C2PA mapping and ISCC discovery without mandating either prematurely.

A second-medium demonstration can later test interface generality. It need not delay useful code embedding. A fingerprint baseline winning one experiment is reason to improve or narrow the carrier, not abandon the embedded-mark objective. No universal-invariance claim, normative spec change or new diagram is adopted here.
