# Rust fragment, alignment and transplant results

Executed 2026-11-21. The synthetic decoder localizes a complete copied function and its raw symbols inside a closed host grammar. It abstains on incomplete/ambiguous anchors. A same-context signal-only transfer also decodes: raw-state extraction does not authenticate identity or establish the host's ancestry.

Files: [fragment_experiment.py](../experiments/rust-carrier/fragment_experiment.py), [regression tests](../experiments/rust-carrier/test_fragments.py), [full generated inputs, expected outcomes, byte spans and results](../experiments/rust-carrier/fragment-results.json). This extends [the initial carrier experiment](rust-carrier-results.md) without changing its files or payload choices. All inputs are synthetic; no private applications were inspected.

## Scope and alignment rule

The original four-binding function grammar, public raw-state mapping and source-observer boundary remain in force. The only added container syntax is a fixed optional `// café` banner, one exact unrelated `host_value` function, and modules containing one `specimen` function apiece. Module names come from the explicit synthetic allowlist `copied, fragment, left, right, moved, origin, partial, other`; duplicate module names are refused. A same-task direct-return array of canonical in-range suffixed decimal literals is permitted as a control with no carrier. The decoder validates the whole closed host instead of scanning arbitrary Rust for apparent functions. Macros, attributes, arbitrary comments, additional items and non-ASCII outside the fixed banner remain unsupported. There is no general Rust host parser or assurance that arbitrary external source readers are absent: the boundary manifest is a caller-supplied synthetic precondition.

An anchor consists of the sorted local-name/value pairs and ordered returned-name sequence. The function name and return type are fixed by grammar. Literal separators and declaration order are omitted from this key so the carrier can vary. All matches are counted before an optional context constraint: zero yields `no_complete_reference_anchor`, multiple matches yield `ambiguous_reference_anchors` without choosing the first, and a unique match at the wrong requested module label yields `context_mismatch`. The optional expected label `origin` is supplied by the experiment, not signed or authenticated. An attacker can reproduce it.

For a unique complete anchor, the original reference-assisted decoder returns a permutation rank or spelling mask. Output includes a candidate SHA-256, function byte interval and localized raw symbols. Order emits one rank covering the declaration run; spelling emits one bit per literal token, sorted by local name. All coordinates are UTF-8 byte offsets in the **original candidate**, using `[start,end)`, before normalization or insertion of compilation wrappers. The fixed non-ASCII banner makes character indices differ from byte offsets. Tests verify exact slices for the function, declaration run and literal tokens; no symbol region includes host wrappers. Abstentions contain no raw symbols or accepted span.

The incomplete-run fixture removes binding `d` from each actual donor and its final array, adjusts the length to three, and preserves the surviving declaration order and literal spelling. It is a partial-copy control with 3/4 bindings remaining, not a semantics-preserving rewrite of the original four-value function. This decoder deliberately does not recover a partial permutation rank or partial spelling mask, even when three spelling sites survive. The cut excerpt lacks the function/container boundary entirely.

## Executed matrix and denominators

Three donor states per family: order `0,1,23` out of 24 raw states; spelling `0,1,15` out of 16. Donor embedding completed 6/6 requests: four changed and two already matching, with no refusals. State zero supplies no evidence of intentional insertion. Each donor is queried in twelve scenarios; these **72 dependent fixture queries** are not independent statistical trials. The earlier experiment covers exhaustive small state spaces; this matrix samples context cases.

Each table cell covers three queries **per family**, so each row covers six queries total:

| Scenario | Result per family |
| --- | --- |
| Whole copied function in unrelated host | 3/3 return donor state and localized symbols |
| Incomplete donor run, 3/4 bindings | 3/3 abstain: no complete anchor |
| Cut declaration/body excerpt | 3/3 abstain: unsupported container |
| Two identical matching anchors | 3/3 abstain: ambiguous |
| Two anchors with conflicting raw states | 3/3 abstain: ambiguous |
| Changed context, unconstrained decoder | 3/3 return donor state |
| Changed context, expected label `origin` | 3/3 abstain: context mismatch |
| Fresh same-task binding implementation, natural spelling/order | 3/3 return raw zero |
| Same-task direct-return array | 3/3 abstain: no carrier anchor |
| Signal-only transfer, same context and anchor values | 3/3 return donor state |
| Signal-only transfer with changed literal values | 3/3 abstain: anchor mismatch |
| Unexpected but value-equivalent literal spelling | 3/3 abstain: unexpected spelling |

Totals per family: **12/36 raw-state results, 24/36 abstentions, 36/36 expected outcomes**. Exact raw-state correctness is 12/12 returned states; wrong decoded states are 0/12, separately from the 24 abstentions. All 72 queries repeated deterministically. Order localizes 12 rank symbols; spelling localizes 48 bits. No recovered symbol is assigned to an incomplete run. These are localization checks against fixture text, not a corpus localization precision/recall estimate.

The natural same-task controls return zero even when their associated donor used a nonzero state: four of six differ from that donor, as expected. They are not decoding mistakes, and raw zero is not a negative identity verdict. Fresh functions are constructed from fixed task values and different layout; no empirical independence or historical ancestry is asserted.

Signal-only transfer reconstructs the function from fixed values while transferring only name order or separator choices from the donor. Same-context acceptance is **6/6**, including four nonzero states and two already-zero states. This is a demonstrated extraction limitation, not an identity-verification error rate. Changing task values to `[13,24,35,46]` while retaining the same pattern gives **0/6 returned states, 6/6 anchor-mismatch abstentions**. This contrasts reference alignment with authentication: exact anchor values and a copied label are reproducible by an adversary.

## Behavior checks, reproducibility and limits

Only the harness's generated trusted fixtures are compiled. `align()` reads strings and invokes no subprocess, filesystem read or candidate execution; a regression test mocks the command runner to enforce that separation. There is no CLI option to compile a supplied candidate. Sixty-six complete generated hosts compile and pass **78 function-output checks per profile**, 156 total in debug and optimized profiles. The six cut excerpts are intentionally incomplete and are not compiled. Unexpected-spelling controls are generated, safe literal programs and compile despite decoder abstention. Compilation/runtime failures and timeouts are zero.

The fixed behavior oracle for complete donor/transfer functions is `[12,23,34,45]`; incomplete and changed-value controls have explicitly different fixed oracles. Expected outputs are recorded by fixture category and never inferred solely from transformed source. A regression test corrupts a donor value and confirms that validation rejects it before invoking a compiler. Passing these fixture checks is bounded output evidence, not a proof for broader Rust transformations. Incomplete or changed-value controls are not counted as behavior-preserving evasion attacks.

Run from repository root:

```sh
python3 -m unittest discover -s research/experiments/rust-carrier -p test_fragments.py -v
python3 research/experiments/rust-carrier/fragment_experiment.py --output research/experiments/rust-carrier/fragment-results.json
python3 research/experiments/rust-carrier/experiment.py
.venv/bin/python tools/validate.py
.venv/bin/python -m unittest discover -s tests -v
```

Actual validation: 21 fragment regression tests passed; the original carrier experiment passed again without rewriting its prior result file; repository validator and six contract tests passed. The fragment run used Python 3.14.6 and `rustc 1.97.1 (8bab26f4f 2026-07-14)`, full commit `8bab26f4f68e0e26f0bb7960be334d5b520ea452`, LLVM 22.1.6, target `aarch64-apple-darwin`, edition 2021. The harness records compiler output and uses debug `opt-level=0, overflow-checks=yes` and optimized `opt-level=3, overflow-checks=no`, both with `--test`. Matching-version semantic sources remain those cited in the initial results report. Fragment wall time including compilation was 1.248852 seconds; peak memory and separate extraction/search latency were not measured.

The next blocker is the protocol decision about reference alignment, context binding and partial-copy recovery. Exact names/values limit coverage; requiring the complete anchor discards surviving bits; optional module labels reject benign moves yet are easy to reproduce. Identity framing, wrong-key/identity controls, signatures, blind multi-reference search and query-level false-alert calibration remain unavailable. This experiment measures no ownership, permission, whole-host ancestry, binary recovery or transplant resistance guarantee. Preserve these cases as baselines before widening syntax or choosing payload/redundancy sizes.
