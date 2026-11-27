> Portable adaptation of dated original review/record; original SHA-256 `27a19bbfda48bac69061848bed2e6614a2374440143fdc4746d1d614df8dba4a`, 13584 bytes. Retained citations are rebased; unretained private attachments are identified explicitly. Private locations, provider account/deployment targets/identifiers and selected private-checkout preservation metadata are omitted. Historical findings, outcomes and limits remain historical. This does not independently accept this new retention package.

# Independent WEB4-G1 current-input operation review

2026-11-27. **Accept exact `c0c34cc407e39b80b293ccec6e255db0207acd4a`; no blocking finding. WEB4-G1 is resolved for the explicitly advertised bounded Go operations.** Parent is independently accepted P1 fix `58452ca38d9af21708e899a3c15d1be53f797ce5`. The combined accepted page/fixture/lifecycle evidence now supports **eligibility for the coordinator's WEB.4 criterion disposition**; this report does not edit or automatically close a gate. M3 HOLD.

Reviewed the exact seven-path delta, author handoff, helper, component, worker, docs and both operation/browser runners. Clean owned worktree: `[private source location omitted]`. Setup and seven source pins (original private attachment not included in this package); before inventory (original private attachment not included in this package). Important new helper SHA-256 `0f9166f90908672fa9d9c6f7bba1e2795ac6d82b756142690c832287e8842d26`; component `111cd3264e22fbd185cf05b3f98266cf61cf8cec1d0385a1830e2efb09e75c0b`; worker `cfdd2f3ff7b9dd9918e8ecd7f461a6651ea4bf9a04193a3f697da8d38be36dd1`.

## Operation semantics and lexical review

The six named actions operate on the selected **current Sample or Transformed copy**, including dropped text, and write transformed-copy bytes. They do not replace both sides with a fixed recipe. Source-side selection allows explicit chaining. Recipe loading remains a distinct, honestly labelled operation.

Tokenization comes from `tw.extract`'s pinned extraction record: actual token text/class, original UTF-8 byte spans and inserted semicolons. The wrapper maps byte offsets to JS code-point boundaries before slicing; it does not implement a second Go lexer. Independently checked the source pin for `crates/tw-lex-go/src/lib.rs` at implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c`: SHA-256 `935b3a5de61b5e2e626f2dc8531043faab0b52ecca809d47f7faeeb2a7575199`. `tw-core::Token` defines half-open original byte spans and zero-width inserted semicolons with text `;`. Engine source pins (original private attachment not included in this package).

The advertised subset is substantive and bounded:

- **Reformat:** collapses horizontal whitespace in gaps while preserving newlines, comments and literal/token spelling; not gofmt and may be a no-op. Comment scanning is applied only to extractor-confirmed gaps. It neither reparses string contents as comments nor removes separator whitespace.
- **Rename:** replaces exact ASCII identifier tokens, including selectors, not substrings/comments/literals. Blank, keyword, predeclared/constraint names, absent names, unchanged/colliding targets and names over 64 characters refuse. Lexical replacement does not claim scope/type or behavior preservation.
- **Reorder:** reverses 2–32 bare named function chunks. Structural delimiter balancing ignores literals and relies on extractor comment exclusion; exact function chunk bytes survive. Simple signature/return patterns are bounded explicitly; package/imports, outer comments, methods, generics, tuple/complex signatures and unsupported boundaries refuse. No universal AST/parser support is implied.
- **Copy fragment:** slices the selected current source using a 1-based whole-token range; inserted semicolons count but cannot start the range. Unicode spans map without changing source spelling. Incomplete fragments are allowed, not promised to compile.
- **Embed:** consumes the visible captured snapshot, retains that stage-1 snapshot and prefixes the fixed synthetic Web4Host bytes. It does not silently reselect a recipe or read a later edited source. Incidental overlap and syntactic/semantic invalidity are disclosed; this is not a promise that the fixed host is unrelated to every possible input.
- **Evasion insertion:** serializes actual token text, materializes implicit semicolons, removes comments and inserts `break ;` after every fourth token. It exactly reproduces the accepted D4 output on its original source; other input results are observed computations, without a borrowed expected outcome or evasion guarantee.

Source/input/output caps are 65,536 UTF-8 bytes; 4096 tokens are checked after extraction. Unpaired surrogates refuse. Expansion is checked before publishing operation output, after construction; no preallocation or peak-memory guarantee is claimed. Config remains exact Go draft-1, k=5/window=4/minimum 2/merge gap 4/no suppression.

## Independent checks and denominators

All execution used a fresh exact Git export and existing locally copied dependencies. Core/build processes had an outer temporary `TRACEWEAVE_PRIVATE_DIR`, deny-network sandbox and disabled build telemetry. **No native Traceweave binary, version/help probe, generator or signing operation was invoked.** Existing immutable native expected artifacts were used for the original fixture checks.

| Evidence layer | Independently observed result |
|---|---|
| Committed operation suite | Six exact deterministic operation outputs, six repeats and six repeated actual-WASM comparison-body cases; **30/30 refusal cases**. [Log](../results/g1-operations.json) |
| Existing immutable page suite | **8/8 full retained-native body byte/digest cases, 16/16 catalogue byte comparisons, eight repeats**. Log (original private attachment not included in this package) |
| Fresh local web build | `next build --webpack` and included TypeScript passed; existing Next 16.4.6, no acquisition. Log (original private attachment not included in this package) |
| Full committed browser suite | Existing eight real-worker body downloads/controls pass; all six current-input operations plus one copy-editor chaining step; P1 and operation cancellation/replacement/unmount regressions pass. [Results](../results/g1-browser-projection.json), [operation rows](../results/g1-named-browser-steps.json), [P1 regressions](../results/p1-regressions.json), log (original private attachment not included in this package) |
| Additional independent adversarial checks | Eleven grouped exact-output/boundary checks plus surrogate-refusal assertions passed. Script (original private attachment not included in this package), [results](../results/g1-adversarial.json), log (original private attachment not included in this package) |
| Additional independent browser mapping | **7/7 operation/chaining steps** bind actual source/copy bytes, downloaded body and rendered normalized-channel text/marks; direct operation-to-operation supersession ignores old success/error callbacks. [Results](../results/g1-mapping.json), script (original private attachment not included in this package), log (original private attachment not included in this package) |

The adversarial checks include identifier prefixes versus exact occurrences, lexical selectors around Unicode, unchanged comment/string/raw/rune content, tabs within multiline comments/raw literals, nested function/map/slice delimiters and quoted/comment closing delimiters, Unicode fragment boundaries, implicit-semicolon range ends, exact token serialization around literals/comments, 4096-token admission, and actual 65,536-byte embedding output versus one byte over. Malformed Go lexical forms and unsupported structural inputs refuse rather than publishing altered text. These are fixed small correctness probes, not a corpus or independent Go compiler/conformance suite.

The new browser scenario drops a distinct two-function synthetic source, then applies reformat, rename, copy-editor reformat chaining, reorder, copy fragment, embed and evasion insertion. Each completed body download's reference/candidate SHA-256 is checked against the actual editor text, and literal editor output assertions are independent of the operation implementation. The custom sample SHA-256 is `4e6becb2fa9b4fd67f5d25ba82df15eca2551b6eecf9a70fb7a6ee01acb60672`. This is **one current-input scenario with seven steps, representing six actions**; it is not seven new immutable demonstrations or a native-oracle expansion.

Stage 1 is visibly captured as `func alpha(a int`, placed into the copy editor, recomputed and downloaded. Stage 2 embeds precisely that snapshot, keeps it visible, recomputes and downloads different actual bytes. Manual editor/file/recipe replacement clears capture by source inspection. The six actions retain custom/edited-input labelling, without fabricated native expectations.

The additional browser run retains full per-step sample/copy/body bytes in [operation-artifacts/](../operations/). Independently byte-sliced engine spans agree with **both panes' full rendered text and every marked segment** in all seven normalized-channel results, including zero-region fragment/evasion results and multiple reordered regions. Prior accepted D3 both-channel mapping remains unchanged. Operation-to-operation supersession was tested with two actual workers held on WASM loading; releasing both and injecting the retired first worker's success/error cannot replace the second result or create an alert.

The complete committed suite also passes held-operation Cancel, late output after recipe replacement, operation unmount/remount and all accepted P1 real/nonabortable recipe-response success/failure tests, same-turn selection/Cancel and recovery. Source guards combine mounted state, epoch and exact job identity; unmount cleanup now explicitly terminates operation workers even while normal comparison is paused. Refusal clears the old result/export and preserves editor bytes. No page exceptions were observed.

Installed isolated Chrome 158.0.8127.89 used owned profiles/processes and loopback servers only. Scoped desktop/narrow screenshots were inspected; native labels/controls and wrapped operation layout are readable. This is not full visual/accessibility acceptance. Author lint/default-build results were inspected; only the fresh webpack build/type checking above is represented as independently rerun.

## Fixture preservation and WEB.4 eligibility

All **46 files under public/testing-fixtures/** remain byte-identical to the accepted parent: 44 copied evidence files plus provenance/license. Accepted source is still spec `cc4fc4d5b3ade41ed754828b418c0f0d027f5e16`; no config, recipe, expectation or outcome was regenerated. Same **six demonstrations, three both-mode misses, two separate controls**. D2's exact-only miss is not added to the 3/6 count; D3 remains abstain/ambiguous; D6 remains no-shared-fingerprints. Both controls still pass. New operation observations are separate from that immutable denominator.

WASM remains SHA-256 `3001cdcd5f29412cdf32131b5755364c704ac54915cd1ab397817eb52c18d61c`; loader `6785a5e2fff23ca4722d419722b7e2f84a52dd9613b3152f7963729d3bc01f7b`. Registry, old flows, storage/signing, styles/global CSS, lockfile and dependencies are unchanged by this delta. The only additional package script is the operation test.

Exact current public criterion authority was ROADMAP WEB.4 line 341 at **`184b74b072a7fdc4f79d385d512f542e8c32ab8a`**, retained in public-ROADMAP.md (original private attachment not included in this package). It lists reformat, rename identifiers, reorder declarations, copy a fragment, embed in unrelated code and insertion at the evasion interval, plus live regions/outcomes, six demonstrations/half misses and identity/unrelated checks. It does **not** require universal arbitrary-Go AST support, semantic preservation, separate new fixture IDs for each action or additional populations.

**Bounded code acceptance:** no new blocker; the six explicitly supported operations act on current input with tested outputs/refusals and lifecycle guards.

**WEB4-G1 disposition:** closed. Current dropped/editor transformation and observable fragment→embed stages are now directly measured, rather than inferred from preset loading. The accepted P1 correction remains intact.

**Full WEB.4 criterion recommendation:** the combined accepted page + immutable six-demo/three-miss/two-control evidence + these actual current-input actions now supports eligibility under the unchanged wording, within the disclosed Go subset. No remaining G1 functional completion is requested. This is a review recommendation for coordinator disposition, **not a gate/status edit, new deployment acceptance or universal robustness guarantee**.

## Limits and preservation

Native/WASM share engine ancestry; exact agreement is finite preservation evidence, not an independently implemented matching oracle. New operation strings have independently asserted deterministic outputs and observed WASM bodies, not invented native reference results. No parser/compiler, syntax/type/behavior preservation, universal evasion, generalized unrelatedness or source-provenance claim.

Caps apply after encoding/extraction/construction where stated; no WEB.6 memory/timing/baseline certification. CDP/synthetic drop substitutes for chooser/physical drag; no full keyboard/AT/device audit or measured active synchronous-core interruption. Browser resolver/background restrictions are not OS network-denial/zero-attempt/offline-reload/privacy proof. Core/build ran under OS network denial. No external navigation, acquisition, corpus/M3, production data, signing, CI, service/deployment, push, gate/count edit or sublane.

An initial check-launch attempted to read setup metadata while its dependency-copy process was still finishing; it stopped before tests. Execution proceeded only after setup completed; no product/expectation adjustment was involved. All subsequently recorded checks above passed.

Final preservation (original private attachment not included in this package), source copies and `evidence-sha256.json` retain exact identities. Author tree stays clean at the exact reviewed tip and all prior independent review records remain preserved. **Disposition: bounded code accepted; G1 resolved; WEB.4 eligible for coordinator disposition on the combined evidence, with all stated limits and M3 HOLD retained.**
