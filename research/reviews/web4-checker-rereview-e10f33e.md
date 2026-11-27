# Focused independent WEB.4 checker rereview

2026-11-27. Exact reviewed author tip: `e10f33ecbe9381fa30cc709cc6e31ce9b73080e7`, tree `d23cf67fc385176711ff13d3d5bfb0a28d99e3c2`, following [independent review 8f21327](web4-demo-fixture-review-d2dd3df.md) of `d2dd3dfdffabf70d47d1249c42c30b133af15daf`. Reviewed the checker/test delta and [author resolution](web4-checker-resolution-8f21327.md). No native executable was invoked or replay repeated.

**Verdict: both earlier checker findings closed; eligible for evidence-only integration. No new blocking finding.** This is checker validation of the retained fixture package, not physical execution attestation, WEB.4 closure, a browser test, WEB.6 baseline/freeze or new measurement. Gates/counts and M3 hold remain unchanged.

## Finding dispositions

1. **Empty CLI metadata accepted — closed by e10f33e.** Both `check()` and `verify_replay()` now require exactly Rust and Go, exact metadata fields, reviewed implementation/spec pins, names/versions, stamped status and the two exact measured binary hashes. Missing/empty/extra labels and incomplete/substituted metadata no longer pass. Constants match the prior independently reproduced evidence: Rust `5d22a4d37d6403c595f8ccab04172a496ca74368a52d5ee89a3b7e1b918308a3`; Go `0219f19b4222ff71733d3709a57116aae0756f2fd0bba0d6f1e9251e025052b1`. Different-platform binaries require separate reviewed identity; a claimed stamp is not execution proof.
2. **160 copies of one command accepted — closed by e10f33e.** The new ordered plan requires all eight cases × two CLIs × ten operation slots. For each side it requires extraction, record validation, catalogue construction and catalogue validation, followed by compare/body validation. CLI, exact argv/config/source/artifact paths, explicit stdout flags, integer-zero exit, metadata fields and digest syntax are checked. All 80 data-producing stdout hashes bind to their retained artifact; 16 Go extraction stdin hashes bind to actual case/side inputs. Validator operations must name the appropriate artifact and record success. Identical records are legitimate only where the expected slot/bindings are identical; “unique slots” does not mean 160 distinct argv strings.

Both original counterexamples were independently reapplied to scratch copies: empty CLI map and same-count 160-first-record replacement each fail through both public entry points. The author suite also rejects single duplicate replacement, swapped operations and same-count case-block substitution. No count reduction or relabelling was used to close the gap.

## Independent static verification

The package passes five test methods, with 38 distinct author corruption cases: ten original, thirteen CLI-metadata and fifteen command mutations. All 28 new cases test both `check()` and `verify_replay()`; the total is distinct corruptions, not a claim of 76 separate cases or native runs.

Beyond that suite, I independently indexed retained commands by `case_index*20 + cli_index*10`, checked each ten-operation layout, recomputed all 80 stdout bindings from physical artifact bytes, and recomputed all 16 Go stdin bindings from physical input bytes. I then made 256 separate in-memory corruptions against `check_commands`: append an unexpected argv element at each of 160 positions, replace each of 80 producer stdout hashes, and replace each of 16 Go stdin hashes. Every mutation is rejected. This checks sensitivity at every affected slot, rather than assuming the helper's generated plan is correct because the supplied package passes.

Reproducible package/repository checks, using existing local Python only:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -I research/drafts/web4-demo-fixtures/test_fixtures.py
PYTHONDONTWRITEBYTECODE=1 python3 -B research/drafts/web4-demo-fixtures/check.py
python tools/validate.py --links-all
python3 -I tools/check_hygiene.py --messages 8f21327..HEAD
git diff --check 8f21327 HEAD
git diff --name-only 8f21327 e10f33e
```

For independent mutation reproduction, load `evidence/run.json` and `recipes.json`, deepcopy the run per alteration, and require `check_commands` to raise `ValueError`. Producer positions within each ten-slot block are 0/2/4/6/8 (sample record/catalogue, transformed record/catalogue, body); Go stdin positions are 0/4. For original bypass reproduction, mutate only run.json in a scratch package copy and require both `check(copy)` and `verify_replay(copy/evidence)` to raise. These operations do not execute the runner or a CLI. All listed checks pass, with links/hygiene checked again including this record.

Reviewed-file SHA-256:

| File | SHA-256 |
| --- | --- |
| check.py | `5dcd55aefba49b97f29d1e259616c8ae0a05607d9c173fa2fc2b443f8ec98d32` |
| test_fixtures.py | `2514c0950349906f867bb728432ef3b9eeeac66992f711b9163f95b93fb4d21c` |
| author resolution note | `1a1b7e271375206147ae32477588c99b502ece2ed885018fda640e3a8898c8f4` |

## Preservation and remaining limits

The author delta changes exactly checker, tests and resolution note. Independent byte comparison to `8f21327` confirms preservation of every other original package file, including all 80 artifacts/run, inputs, config/recipes/expectations, runner, failure account, author incident disclosure and prior independent review. This review adds only this addendum. No normative/shared/protocol/queue/gate change occurred.

Static metadata still cannot prove physical execution or distinguish substitution of a byte-identical record in an otherwise identical slot. Validator diagnostic stdout/stderr and producer stderr are checked for digest shape, not reconstructed content or diagnostic attestation; data-producing stdout and Go source stdin are the explicit byte bindings. The author's resolution states these limits accurately. The earlier exact-binary replay remains the execution evidence; this rereview did not reproduce it again.

The default-private write incident and unknown prior contents/loss remain disclosed, unresolved historically and untouched. Runner version calls still precede its internal temporary-storage wrapper. Any future native replay/probe must set an explicit outer temporary `TRACEWEAVE_PRIVATE_DIR`, including version/help/failure calls where relevant, as recorded in the prior review. This static rereview made no native calls and no default-private inspection or change.

Finite synthetic limits remain unchanged: exactly 3/6 both-mode misses, separate full-fingerprint-identity/unrelated controls, D3 ambiguity and potentially noncompiling lexical fragments. No live page, hand-edit behavior, browser equivalence, performance, universal robustness, private-storage recovery, acquisition, push or sublane follows. WEB.4 remains planned/open and M3 remains held.
