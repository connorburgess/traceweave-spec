# Independent M5 re-review — e7e7149

Exact reviewed commit: **`e7e714987aced74569294bfe6aa11a072ed43372`**, `m5-readiness`, 2026-11-26. This non-author review compares the [author resolution](../../docs/release/m5-review-resolution.md) with F1–F6 of the [original independent review](m5-readiness-7dccedd-review.md). Applicable AGENTS.md instructions were read. No reviewed implementation or test code was edited by this reviewer.

**Disposition: one remaining medium blocker, confined to M5.1. M5.2, M5.4 and M5.5 are eligible for integration on this exact revision; no gate status is changed here.** Passing suites do not override the display-oracle counterexamples below. This is not approval to release or closure of M5.3.

## F1–F6 dispositions

| Original finding | Disposition on e7e714987aced74569294bfe6aa11a072ed43372 | Independent evidence |
| --- | --- | --- |
| F1: incorrect TypeScript wire version | **Closed.** | Matrix now selects `ts-tokens/draft-2`; release notes line 7 enumerate all five exact pairs and reject the superseded TS draft-1 interpretation. Migration rule 2 distinguishes the changed configuration digest. The actual TS config validator accepts committed draft-2 and rejects the otherwise identical draft-1 bytes in the executed test. |
| F2: minimal-core/native/WASM conformance overstatement | **Closed.** | Matrix separates extraction records, minimal-core adapter, registration form, references and links/rendering. Minimal-core native evidence is unverified; tested WASM registration API refusal is explicit. WASM opening, policy, key-event and link coverage is sampled/unverified rather than full 86/147 parity. Scope matches implementation source at `5b9a881` and the pinned `51f29d7` WASM review's 5 reference / 4 verify-render cases. Shelf remains unverified for complete flows, without implying capability absence. |
| F3: inadequate radix/compound-policy failing-test mappings | **Closed for the original findings.** | New M5-020 oracle tests 48 malformed and 12 valid literals across all six prefixes, separators and suffix/class rules. All seven committed one-rule mutations are killed. Independently substituting the original radix-membership mutant into the actual cited `test_radix_literals` produces an assertion failure; the old empty case still rejects while `0xG` is accepted by that mutant. M5-085 covers seven policy categories with 35 object variants and five strict-JSON negatives; bypassing `check_policy` independently causes all 35 evidence-access traps to fail. Compound opening and time-refusal introductions now cite their constituent negative cases. |
| F4: executable requirements classified as untestable | **Partially closed; R1 below remains.** | CLI, filesystem, build, diagnostic, size, selection and display obligations now have executable mappings. Native source tests assert refusal, absence/unchanged contents, cleanup and canary-free output. Nine Go and four Rust tests were independently rerun, plus six raw-process cases per binary. Resource and wrapper-identity tests exercise actual checker functions. However, the new display oracle accepts two violating outputs, so its M5-058 mapping is not yet adequate. |
| F5: accessible alt claims excluded | **Closed; revised exclusions approved for this exact README.** | All four complete alt descriptions are now mapped compound claims. The original unsupported-ownership mutation, even with exclusions regenerated, is rejected. Current inventory is 77 units (42 prose/fragments, 31 table rows, four alt descriptions); all assertions in each compound unit are retained. Five exclusion categories now remove only current headings, navigation, fenced commands, inert picture markup and table labels/separators. |
| F6: release notes omit documented text limits | **Closed.** | Release notes lines 28–36 explicitly summarize text-profile §13, including all four TXT.7 categories, distractor/ambiguity counts, tokenization/normalization/Markdown/skeleton limitations, boilerplate, rights/absence/rate boundaries, fingerprint guessability and no embedded text mark. Profile §13 is linked as the exact authority, with result/vector/source locators. Scope remains synthetic/unmeasured; embedding omission cites M2E.0 and signing/M4 prerequisites remain explicit. |

## R1 — Medium: display adapter accepts an incorrect floor and a negated minimum label

Locations: **`tests/test_release_requirements.py:67–71`**, negatives at **lines 211–216**; mapped by **M5-058 clauses 1 and 2**, `test-vectors/requirements/requirement-map.json:1140`. Blocks **M5.1**, under M1.5's requirement that the cited test fail when the MUST is violated. This is an oracle defect, not evidence that Shelf or a native renderer emits either output.

`validate_display` matches the required prefix with `startswith` and searches for the substring `at the minimum`. It does not delimit the numeric floor or validate the equality label. I independently passed the following body and outputs to the committed function; **both were accepted without exception**:

```python
body = {'minRegionDistinctHashes': 2, 'regions': [
    {'status': 'reportable', 'distinctHashes': 3, 'distinctCommonHashes': 1},
    {'status': 'reportable', 'distinctHashes': 4, 'distinctCommonHashes': 0}]}

# Incorrect displayed floor 20 instead of 2:
validate_display(body, [
    'region 0: evidence 2; minimum 20; at the minimum',
    'region 1: evidence 4; minimum 2'])

# Equality falsely described as NOT at the minimum:
validate_display(body, [
    'region 0: evidence 2; minimum 2; NOT at the minimum',
    'region 1: evidence 4; minimum 2'])
```

The five committed negative outputs all reject, but none exercises either bypass. Since this is an explicitly chosen test-only grammar, exact field parsing/anchored matching and an exact equality-label field are appropriate. Add these two negative outputs and require their rejection while retaining the existing valid equality/non-equality outputs and negatives. Do not add a product renderer or connect Shelf as part of this fix; that is unnecessary feature work. Re-review the corrected oracle and its exact new commit before recommending M5.1 closure.

## Executed checks and mutation evidence

On the reviewed tree, with its pinned development environment, these commands exited **0**:

- `.venv/bin/python tools/validate.py` (includes the release-requirement suite).
- `.venv/bin/python -m unittest discover -s tests -v`: **28/28 tests**, no failures.
- `.venv/bin/python tools/validate.py --links-all`.
- `.venv/bin/python tools/check_hygiene.py`.
- `TW_IMPL_REPO=<existing implementation checkout> .venv/bin/python tools/check_requirement_map.py`: **157 occurrences, zero syntactically unmapped; 100 testable, 13 implementation-test, 27 inspection, 17 definitional/quoted**. All pinned external source locators resolve. This command checks locators, not external execution.

The following independent in-memory mutations exercised actual tests, not inventory counts:

| Mutation/probe | Observed result |
| --- | --- |
| Original radix-membership mutant substituted as default lexer for cited `test_radix_literals` | Test fails with one assertion failure; no exception-class mismatch. All seven committed radix mutations also run and pass their kill assertions. |
| `check_policy` replaced with unconditional success | Cited policy test fails in all 35 object variants on trapped evidence access. The five strict parsing negatives independently reject duplicate/escaped-collision keys and nonfinite constants. |
| Catalogue cap check removed from the hashing function while keeping the declared cap constant unchanged | Cited cap test fails with `ValueError not raised`. Original 1 MiB exact-byte digest succeeds and one byte over refuses; link path refuses oversize before hashing. Raising the cap constant to 2 MiB was separately rejected too. |
| Artifact hashing replaced with an unbounded `stream.read()` | Cited guarded-stream test fails. Inspected actual subject, possession and result hashing call sites use the bounded helper. This does not establish bounded loading of arbitrary production files. |
| Report wrapper reserialized, then wrapper hash substituted as body identity | Existing actual link-checker test accepts reserialization and rejects the wrong identity. |
| Unsupported ownership assertion inserted into alt text, exclusions regenerated only | README checker rejects unmapped/stale claim text. All four new ALT entries' substantive sources were read; proposed embedding stays research rather than origin evidence. |
| Added/deleted requirement, arbitrary raw `checker:...:import json` locator and nonexistent unittest method | Executed contract tests reject these cases. Registry/AST resolution is stronger locator validation, not proof of semantic relevance. |
| Wrong floor `20` / negated minimum label | **Both accepted: R1.** |

### Native execution reproduced independently

Exported implementation **`5b9a881`** with `git archive` to a fresh temporary directory; no existing implementation checkout was modified. Built with cached dependencies, Go's `GOPROXY=off GOTOOLCHAIN=local` and Cargo's `--locked --offline`. The plain Rust archive build correctly warns that it is unstamped. No new OS-level network-denial run is claimed.

| Suite | Result and meaningful observations |
| --- | --- |
| Go CLI selected tests: PrivateDefault, FaultInjection, ProvenanceCommitRule, BodyOnlyAndCommitRequired, CheckoutDestinationRefused, Version | **6/6 passed, no skips**. Actual process exits, expected body/catalogue hashes, default filesystem location, modes, refusal and provenance behavior are asserted. |
| Go store/schema: CheckDestination, Temporaries, ErrorsDoNotEchoKeys | **3/3 passed**. Wrong overrides/linked tree destinations refuse; same-output stale temporary disappears while other-output material remains; secret key names do not enter errors. |
| Rust `cargo test --locked --offline -p traceweave --test storage --test provenance` | **4/4 passed**, no ignored tests. Plain-build provenance and storage/fault behavior exercised through native CLI. |
| `tools/check_native_m5.py` against binaries from that export | **Go 6/6 and Rust 6/6 passed**: unknown option, key/build/source canaries, private path and stale cleanup. |

These reproduce the author's **13 native tests / 12 raw-process probes** claim. Complete build-forgery checklist and skill transcript suites were not newly executed; their pinned source assertions and historical reviews are the evidence for broader cases. M5.3's independent full offline demo remains separate.

## Non-testable sample, claims and regression scope

For the new revision I rechecked **11 remaining inspection clauses**: M5-008/1, M5-009/1, M5-011/1–2, M5-014/1, M5-015/2, M5-019/1, M5-025/1, M5-036/1, M5-065/1 and M5-095/1. This exceeds M1.5's minimum 10. The unchanged normative passages and the original review's supporting profile/source reviews remain applicable: stack/linear resource proofs; full pinned Unicode table equality/provenance; constant-time/randomness internals; future profile declaration; historical exact-byte retention; production exclusion of public fixture roots. Their stated inspection boundaries are justified. M5-065's executable cap clause is now separately mapped; the retained lifecycle clause does not waive it. No production primitive or deployment-policy certification is granted. The 17 definitions/quotations retain their original applicability dispositions; hosted-witness quotations do not establish an included service.

The revised 77-unit README inventory preserves current prose sentence boundaries, version dots, links, captions and every table data cell. All evidence quotations resolve, and the four new ALT descriptions were compared with the substantive review/decision sections. Current exclusion counts remain 14 headings, eight navigation lines, seven fenced-code lines, 20 picture-markup lines and ten table-header/separator lines: **59 source lines**, with four alt descriptions extracted before their markup is excluded. Approval is specific to this reviewed README and does not preapprove future substantive claims hidden in headings, commands or table labels. Dependency fetch is now explicitly separated from offline checks.

Versioned specification and migration documents remain coherent with the corrected matrix. No `spec/`, `profiles/` or schema wire bytes changed in the fixes commit. All historical registration fixtures continue to pass after the checker changes for real-date validation, production checkpoint shape and resource caps. Simulated placeholder fixtures remain explicitly test-only; their success is not production policy conformance. No additional blocking regression was demonstrated outside R1.

ROADMAP's deferred CI/CD signing idea at line 361 is unchanged from `67f7b5d`: it approves no implementation, trailer format, service, default or new gate. No such feature work is present in this revision. All four M5 statuses remain open.

## Integration eligibility

| Gate | Recommendation on exact reviewed commit | Remaining blocker |
| --- | --- | --- |
| M5.1 | **Not eligible yet.** Literal coverage and inspection sample pass; mapping adequacy still fails. | R1 / residual F4: display oracle. |
| M5.2 | **Eligible.** Current splitting, evidence mapping and revised exclusions independently approved. | None demonstrated for this revision. |
| M5.4 | **Eligible.** Scope, embedding decision, signing/M4 prerequisites and documented limit categories are stated. | None demonstrated for this revision. |
| M5.5 | **Eligible.** Version/migration guidance and bounded feature × level × implementation matrix are present and accurate within the recorded evidence. | None demonstrated for this revision. |

Only this review record is committed locally. No gates marked met, push, feature work, sublane, held M3 evaluation or acquisition was performed. Eligibility of three documentation gates does not imply candidate-release completion.
