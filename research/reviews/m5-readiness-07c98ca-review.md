# Independent M5 display-oracle confirmation

Exact reviewed commit: **`07c98cad440e3797d0ddc0c4b8c2bfb06a36dbd7`**, `m5-readiness`, 2026-11-26. This non-author review addresses the remaining R1/F4 blocker from [the e7e7149 review](m5-readiness-e7e7149-review.md), using the [author resolution](../../docs/release/m5-display-oracle-resolution.md). Applicable AGENTS.md instructions were read. Only this review record is changed by the reviewer.

**Disposition: R1 and residual F4 closed. No remaining blocking findings demonstrated. M5.1, M5.2, M5.4 and M5.5 are eligible on this exact commit.** This recommendation does not mark gates met, authorize a push or establish complete candidate-release readiness; M5.3 remains separate.

## R1 / F4 disposition

The fix in `tests/test_release_requirements.py:68–84` replaces numeric-prefix and equality-label substring checks with full-record parsing and comparison of the complete expected reportable-region map. Region IDs, evidence and floors use canonical ASCII integer spellings. The equality marker is an exact parsed optional field and must agree with `evidence == floor`. Duplicate records are rejected before map comparison. Line ordering is intentionally immaterial.

Both mapped M5-058 clauses still cite the executable `ReleaseRequirementTests.test_rendered_region_floor`; the two updated `failsBecause` descriptions accurately describe that test. The adapter remains explicitly test-only, without imposing a product rendering format or claiming Shelf/native renderer conformance.

The two original bypasses were independently reproduced against the new function with the original two-region body (required floor 2, unsuppressed evidence 2 and 4):

| Output for region 0, with the valid region 1 line retained | New result |
| --- | --- |
| `region 0: evidence 2; minimum 20; at the minimum` | Rejected with `ValueError`: parsed floor disagrees with report. |
| `region 0: evidence 2; minimum 2; NOT at the minimum` | Rejected with `ValueError`: invalid display record. |

The committed test now exercises **34 named negative cases and four valid cases**. I inspected and executed the actual assertions: negatives include the original five cases, both bypasses, wrong non-equality floors, false equality labels, wrong evidence/IDs, missing/duplicate/extra regions, noncanonical numbers, negated/contradictory labels and suffix material. Valid cases cover equality and non-equality together, reversed lines, genuinely multi-digit values, and no reportable regions.

For regression sensitivity, I loaded the exact old `validate_display` function from `e7e714987aced74569294bfe6aa11a072ed43372` and substituted it into the expanded test in memory. It produced **18 negative-subtest failures, zero unexpected errors**, including both original bypasses. The corrected function passes the same test. This confirms the expanded test distinguishes the reported defect from the fix.

Additional independent adversarial checks, without source edits:

- Enumerated **9,604 numeric/label combinations** for the original body: each of the two displayed evidence values and floors ranged over `{0,1,2,3,4,20,21}`, with each equality marker present/absent. Exactly the one correct field/label combination was accepted; every other combination rejected.
- Added seven suffix variants to a valid equality record: carriage return, tab, space, zero-width space, semicolon, duplicated equality label and newline plus text. Every variant rejected. The committed test separately rejects trailing newline and NUL.
- Accepted a mixed report with 12 nonreportable entries followed by reportable indices 12 and 13, floor 12, equality evidence 12 and non-equality evidence 17, in reversed display order. Thus exact parsing preserves genuine multi-digit values, original region indices and non-equality behavior rather than rejecting all larger numbers.

No remaining numeric-prefix, label-negation or trailing-material bypass was demonstrated within this adapter's stated grammar. Invalid report-body schema validation and arbitrary natural-language product renderings remain outside its fixture-adapter scope.

## Validation and bounded-diff assessment

All of the following exited **0** on the reviewed tree:

- `.venv/bin/python tests/test_release_requirements.py`: **10/10 tests**.
- `.venv/bin/python tools/validate.py`.
- `.venv/bin/python -m unittest discover -s tests`: **28/28 tests**.
- `.venv/bin/python tools/validate.py --links-all`.
- `TW_IMPL_REPO=<existing implementation checkout> .venv/bin/python tools/check_requirement_map.py`: **157 MUST occurrences, zero syntactically unmapped; 100 testable, 13 implementation-test, 27 inspection-only, 17 definitional/quoted**. External source locators resolve; this is not a new execution of those external suites.
- `.venv/bin/python tools/check_hygiene.py` and `git diff --check`.

The fixes commit changes only the display adapter/test, two M5-058 explanation strings, and its author resolution document. The earlier independent review record is also present in the range from e7e7149. Byte comparisons confirm no change in README, its claim maps/extractor, release notes, conformance matrix, ROADMAP, normative `spec/` or `profiles/`, or schemas. Consequently the prior reviewed requirement inventory, inspection sample, native process evidence and F1–F3/F5–F6 dispositions remain applicable; only the demonstrated display defect required renewed execution here. The previous 13 native tests and 12 process probes were not rerun because neither native code nor those mappings changed.

M5.2's exact 77-unit claim inventory and approved exclusions remain intact. M5.4's complete documented limit categories and embedding/signing scope remain intact. M5.5's corrected version pairs, migration guidance and bounded implementation/Shelf matrix remain intact. No new regression invalidating those eligibility recommendations was found.

ROADMAP's CI/CD signing idea remains deferred, unchanged and unimplemented. No feature work, sublane, acquisition, held M3 evaluation, gate-status edit or push was performed.

## Gate eligibility for integration

| Gate | Exact-commit recommendation | Basis |
| --- | --- | --- |
| M5.1 | **Eligible** | Remaining R1/F4 display mapping now rejects the demonstrated violations and preserves valid cases; prior requirement coverage, negative/process evidence and independent inspection sample carry forward unchanged. |
| M5.2 | **Eligible, preserved** | Previously approved sentence/alt/table inventory and exclusions are unchanged. |
| M5.4 | **Eligible, preserved** | Previously reviewed limits, M2E.0 omission and signing/M4 prerequisites are unchanged. |
| M5.5 | **Eligible, preserved** | Previously corrected feature/version/implementation matrix and migration notes are unchanged. |

All original F1–F6 findings are now closed within the reviewed scope. This record recommends eligibility only; all gate statuses remain as found, and full release closure still requires its other gates.
