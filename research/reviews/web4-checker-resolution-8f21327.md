# WEB.4 checker resolution for review 8f21327

Author response to the two nonblocking checker gaps in [independent review](web4-demo-fixture-review-d2dd3df.md), exact review **`8f21327635bafb1e1736fed65e79269c3c96ff3e`** of original author **`d2dd3dfdffabf70d47d1249c42c30b133af15daf`**. This change owns only the package checker/tests and this note. Original fixture/artifact/run evidence, runner, incident disclosure and reviewer record are unchanged. It does not close WEB.4 or alter any gate, protocol, budget, queue or M3 hold.

## Finding 1: empty CLI metadata accepted

The former `for ... in run['cli'].values()` accepted an empty mapping. Both `check()` and static `verify_replay()` now require exactly `rust` and `go`, complete version/digest entries, exact reviewed implementation/spec pins, implementation names/versions, `stamp: stamped` and the measured binary SHA-256 identities. Missing identities/fields, extra labels, substituted digests, wrong stamp/name/commit/spec fail with `ValueError`.

The pinned hashes remain Rust `5d22a4d37d6403c595f8ccab04172a496ca74368a52d5ee89a3b7e1b918308a3` and Go `0219f19b4222ff71733d3709a57116aae0756f2fd0bba0d6f1e9251e025052b1`. A different-platform build is not automatically accepted by this focused exact-binary evidence checker: its identity needs separate review. No binary was read/executed or rebuilt for this fix; the identities are the already independently reviewed constants.

## Finding 2: 160 duplicate command records accepted

Counting successful entries alone did not establish operation coverage. The checker now derives the complete ordered plan from the eight case slots, both native CLIs, both sides, exact configurations, expected stdin and retained artifact identities: extract/validate-record/build/validate-catalogue for each side, then compare/validate-body. It requires all **160** slots with exact native label/argv, explicit output routing, integer exit zero, required metadata and lowercase SHA-256 fields. Extract/catalogue/compare stdout digests bind to their specific retained artifact; Go extraction stdin binds to that case/side's input digest. Validation operations must name the corresponding artifact and succeed. The same check runs on static replay evidence.

This catches replacing the entire list with 160 copies of its first entry, a single duplicate replacement at unchanged count, substituted case blocks with unchanged argv patterns but different expected outputs, reordered/missing operations, wrong CLI, omitted stdout flags, wrong stdin and changed output hashes. Legitimate identical operation records across cases remain valid in their expected slots. Static records cannot prove physical executions or distinguish substitution of a byte-identical record in an otherwise identical valid slot; validator diagnostic stdout/stderr hashes are checked for shape, not re-executed or treated as attestations. The checker is still not a standalone provenance attestation.

## Regression evidence and static checks

The package now has **five test methods**: valid retained-package acceptance, valid static-replay acceptance, the original ten corruption probes, **13 new CLI metadata corruptions** and **15 new command corruptions**. All 28 new corruptions are rejected through both `check()` and `verify_replay()` without executing a native process. Total distinct corruption cases: **38**.

Sensitivity was checked by loading the exact old checker from review commit `8f21327` in memory and applying both demonstrated bypasses to scratch package copies. It returned 3 for `{}` CLI metadata and for 160 first-record copies, confirming the new regressions distinguish the old implementation. Current tests reject both; the valid package remains accepted with 3/6 both-mode misses and both controls intact.

Passed using the existing pinned development Python, with bytecode writing disabled:

- `python -B -I research/drafts/web4-demo-fixtures/test_fixtures.py`: **5/5**, including all 38 corruption cases.
- `python -B research/drafts/web4-demo-fixtures/check.py`: valid retained package accepted.
- `python -B tools/validate.py --links-all`: local Markdown links pass.
- `python -B tools/check_hygiene.py` and `git diff --check`: pass.

Git comparison to the exact review baseline verifies preservation outside the two checker/test files and this note, including all 80 artifacts, the original run/configs/recipes/expectations, `run.py`, failure account, author incident disclosure and independent review. The review's version-call isolation limitation remains as recorded; no runner change or private-storage inspection/restoration occurred. No numeric replay, build, acquisition, study, service, browser, push or sublane was used. Focused independent re-review is required before integration.
