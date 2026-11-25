# Decision Record: Omit Source-Code Embedding from the Next Release (M2E.0)

- **Gate:** `M2E.0` ([ROADMAP.md](../../ROADMAP.md))
- **Status:** Decided (owner confirmed 2026-11-26)
- **Scope:** Next experimental release (`0.1.0-draft.1` / `M5.4`)

## Decision

Traceweave **omits source-code embedded marking** from the next release. The next release covers:

1. **Deterministic local fingerprinting and comparison** (`spec/extraction.md`, `spec/catalogue-report.md`, frozen Stage-1 profiles `go-tokens`, `rs-tokens`, `ts-tokens`, `py-tokens`, and `text-plain`).
2. **Offline-first cryptographic registration and verification** (`spec/registration-record.md` `traceweave-registration-draft-5`, `spec/trust-policy.md`, `spec/attestations.md`).

## Rationale

- Prior evidence review ([lane 06](../../research/lanes/06-evidence-review.md)) found no source-code marking carrier ready to satisfy `M2E.1` under cheap formatting/normalization transforms without fragile syntax assumptions or unacceptable capacity/false-alarm trade-offs.
- Text-carrier experiments (`TXT.8`) likewise recorded a negative result under standard Unicode normalization and folding.
- Shipping deterministic fingerprinting and offline-first cryptographic registration cleanly — without an unverified embedding claim — preserves the specification's epistemic boundaries and satisfies `M5.4`'s requirement that any release omitting embedding cite `M2E.0`.

## Consequences

- `M2E.1`–`M2E.7` remain deferred and are not required for the next release.
- Release notes (`M5.4`) and scope statements (`RC.3`) will explicitly state that source-code embedding is omitted, citing this decision record.
- Research on still-image finding-aid marks (`IMG.0`–`IMG.5`) remains separate and explicitly bounded as a non-authoritative finding aid only.
