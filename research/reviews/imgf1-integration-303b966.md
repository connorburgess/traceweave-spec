# IMGF.1 private integration check

Recorded 2026-11-26. Integrates reviewed image branch tip **`303b966fe20f03e346b00732f0fd05ed17ede4b9`** into private `roadmap-v2` at **`4c7c61bab7c2faf250401b9ccc3c3d7000021d34`**, preserving branch history. The exact arithmetic follow-up is `db2848c1e8ec7c8465c066f5bff26863a803d440`; independent review and closure remain in [the arithmetic review](image-normalization-draft3-review.md) and [scoped closure](imgf1-gate-closure-db2848c.md).

The sole merge conflict was the ROADMAP progress block. The integrated version retains all M5 closures and adds only IMGF.1 to the extension met set. README and its JSON/Markdown claim map now quote the integrated extension count. The current scope-review note and draft-3 experiment status link the scoped closure. Historical review/count snapshots are retained, including the image branch's explicitly branch-local 33/47 baseline.

## Independent reconciliation

Parsed individual gate rows rather than relying on summary totals, then compared the met-ID sets with the progress table. Against the private first parent, all 47 core rows are identical; the only changed extension row is IMGF.1. Counts are:

| Group | Total | Met | Negative-result | Open |
| --- | ---: | ---: | ---: | ---: |
| Core M0–M5 | 47 | 34 | 0 | 13 |
| Later profiles, EXT and RC | 55 | 22 | 2 | 31 |

The core open set remains M2E.1–M2E.7 and M3.1–M3.6. The extension negative set remains TXT.4 and TXT.8. Pending TypeScript/text closures are not included. The README inventory retains all 77 IDs, 59 excluded source lines and the identical exclusion policy; only README-007's sentence and count evidence change. Exact evidence quotations validate, including the current ROADMAP row and the scoped IMGF.1 closure.

Git comparison against `24bb4b8483dc86966cb7c8277130bb816b0c6b3f` confirms the draft-2 image profile, experiment protocol and whole frozen `image-fingerprint/` tree are unchanged. Both incoming independent image review/closure records are byte-identical to the reviewed branch tip. No normative spec, profile, schema, promoted vector or historical experiment output changes. The private public-history map is unchanged; public regeneration awaits the separate pending integration.

## Local validation

All checks exited 0 on the integrated tree:

- Repository validator, all 28 repository unit tests and all local Markdown links.
- Requirement map (157 MUSTs), exact README claim/evidence map (77 mapped, zero unmapped, 59 excluded), tree/history hygiene and whitespace checks.
- Explicit draft-3 image checker using the existing pinned CPython 3.14.6 / Darwin arm64 environment and Pillow 13.0.0 wheel, under OS network denial. The checker verifies the wheel digest and loaded wrapper/compiled-target bytes; all 15 finite synthetic cases agree on grey, first-pass and final output. Both resize mutations have five witnesses; exact grey half-tie mutation has one fixture witness.
- All four image checker self-tests, including injected wrong pass order, final-only rounding and ties-to-even grey conversion, plus byte-identical fixture regeneration in memory.

This is a merged consistency check, not a new full image study or independent upstream C-source acquisition. The committed provenance and finite-domain limitations remain. IMGF.5/IMGF.6 remain open; M3 remains held. No release approval, public regeneration, remote mutation or push is included.
