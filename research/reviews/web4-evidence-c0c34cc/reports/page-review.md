> Portable adaptation of dated original review/record; original SHA-256 `8305145d89c91a714641bfc1c6f1a4447f7fe3674d58c2e537ba0fce7497e081`, 14053 bytes. Retained citations are rebased; unretained private attachments are identified explicitly. Private locations, provider account/deployment targets/identifiers and selected private-checkout preservation metadata are omitted. Historical findings, outcomes and limits remain historical. This does not independently accept this new retention package.

# Independent WEB.4 testing-page review

2026-11-27. **Changes requested for WEB4-P1, a reproduced cancellation race.** Exact reviewed Shelf commit **`f934efeed7f6bd4db930ca22a5e3fa9247f50ac0`**, parent accepted `99a1a8bce5382a0345fa7e19d9bfd44575f9c016`. The fixed numerical evidence and normal live editor/download paths pass; bounded code acceptance is blocked by the race. **Full WEB.4 eligibility is separately unestablished by the fixed-recipe-only transformation implementation.** No gate/count changes or fixes were made. M3 HOLD.

## WEB4-P1 — Cancel during recipe loading is undone by the pending fetch

**Medium; blocker to bounded lifecycle acceptance.** TestingPageTab.tsx:25 (original private attachment not included in this package) unconditionally calls `setPaused(false)` when the recipe/config fetch completes. `cancel()` invalidates worker jobs and sets paused true, but it neither aborts nor invalidates that fetch effect. The fetch's `active` flag changes only when the recipe/retry effect is cleaned up; cancellation does not change either dependency.

Reproduced with the real built app, real worker and loopback fixture responses, independently of the existing held-WASM test:

1. Complete D1, then select D2 while holding its two source-file responses on the owned server.
2. Click Cancel live comparison. Observe “Cancelled.” and no Download live body button.
3. Release the pending D2 source responses without further user input.
4. Within 1.4 seconds, the app starts a new live computation, replaces cancellation with **“Live browser result updated.”**, reproduces D2's native digest and restores Download live body.

[Exact observation](../results/page-cancel-race.json): `cancelledBeforeRelease: true`, `unexpectedDownload: true`, `nativeExpectationReproduced: true`. The appended deterministic probe is in browser-independent.mjs (original private attachment not included in this package). The unchanged author browser cases pass because they cancel after recipe loading, while the WASM asset is held; that different seam remains correct.

**Minimum fix:** make recipe-load completion respect cancellation generation/pause state; cancellation must abort or invalidate its ability to auto-resume computation. If fixture bytes are allowed to finish loading, preserve paused state and permit only an explicit edit/retry to resume. Do not leave the editors permanently loading/disabled on the cancelled path. Add a regression holding recipe responses, cancelling, then releasing them and asserting no worker/result/download appears until a new user action. Keep the existing worker/epoch and file-read guards. No fixture/config/outcome change is needed.

## Exact immutable evidence and numerical checks

Author worktree `[private source location omitted]` was clean at the exact tip. Reviewed the full 55-path delta, helper/worker/component/styles, both runners, docs, fixture manifests and the prior accepted WEB4 fixture/checker reviews. Only package.json's added test command and ShelfApp's minimal navigation/import/render modify preexisting tracked files. The accepted Fingerprint/Compare/Replay, storage/signing, global CSS, engine assets, registry and lockfile remain byte-identical to parent.

Independently verified all **44 copied fixture files** against **Git object bytes and blob IDs at spec `cc4fc4d5b3ade41ed754828b418c0f0d027f5e16`** and their manifest SHA-256 values. The upstream Apache-2.0 license also matches its pinned Git object/hash. Nothing was regenerated or relabelled. Configs remain extraction `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2`, comparison `39345e9c8de2b566d19943563326062a46edd38e429a4a96f169307b15147333`: Go draft-1, k=5, w=4, minimum 2 distinct hashes, merge gap 4, no suppression.

Retained upstream native identities remain implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c` / spec `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`, Rust SHA-256 `5d22a4d37d6403c595f8ccab04172a496ca74368a52d5ee89a3b7e1b918308a3`, Go `0219f19b4222ff71733d3709a57116aae0756f2fd0bba0d6f1e9251e025052b1`. **No native CLI, version probe or fixture generator was invoked in this review.** The already accepted immutable native output files were the byte oracle. Native/WASM shared ancestry means agreement is finite wrapper-preservation evidence, not an independent mathematical implementation or universal conformance proof.

The unchanged committed core suite passed (core.log (original private attachment not included in this package)): **8/8 full canonical body bytes/digests, 16/16 complete source-built catalogue bytes, eight deterministic repeats**, correct per-mode outcomes, controls, UTF-8 mapping, metadata size boundary, invalid UTF-8/config refusal and changed custom digest. The frozen denominator remains six demos, three both-mode misses, plus two separate controls:

| Case | Exact | Normalized |
|---|---|---|
| D1 Reformat | match | match |
| D2 Rename identifiers | no-match | match |
| D3 Reorder declarations | abstain / ambiguous | abstain / ambiguous |
| D4 Insert at evasion interval | no-match | no-match |
| D5 Unrelated replacement | no-match | no-match |
| D6 Tiny fragment in unrelated host | no-match | no-match |
| C-identical | match, full nonzero containment both directions | same |
| C-unrelated | no-match | no-match |

D2's exact-only miss and D3's ambiguity do not inflate 3/6. D6 is actual no-shared-fingerprints, not an invented below-minimum-evidence result. D5 is unrelated replacement, not a standalone fragment demonstration. The identity control's “fully” means complete distinct-fingerprint containment, consistent with the engine; it does not require highlighting ignored whitespace/comments or every source byte.

## Live flow, mapping and adversarial verification

Checks ran only in a disposable exact Git export with APFS copies of existing dependencies. **Fresh `next build --webpack` passed**, including TypeScript, under OS network denial and telemetry disabled (build.log (original private attachment not included in this package)); this is a local build, not CI or a new native toolchain build. The author's lint/default-build logs were inspected but are not labelled as independently rerun lint/default builds.

Owned isolated Chrome **158.0.8127.89** and loopback server ran the author's complete bounded browser script plus explicit independent probes. [Browser results](../results/page-browser-projection.json), log (original private attachment not included in this package), executed extended runner (original private attachment not included in this package). The eight live downloads all equal their exact retained native bodies; full copies are retained under `browser-evidence/{id}.downloaded.body.json`. This is **8/8 real browser byte cases**, including both controls, distinct from the 16 catalogue/core checks. Both self-checks show live PASS.

Passed normal paths: hand edits recompute and remove the applicable native-expectation label; synthetic drop recomputes with fixed `sample.go`/`transformed.go` IDs; oversized selection refuses before File.arrayBuffer; invalid UTF-8 refuses; input/recipe changes remove stale exports; held-WASM cancellation and saved old-error callback are ignored; 503 failure/retry recovers. The independently observed recipe-fetch cancellation failure is WEB4-P1, not an all-clear implied by the browser runner's exit zero. No page exception was observed.

Independent DOM verification for D3 compared **both source panes' full text and every marked segment** with separately byte-sliced engine spans in **both channels**; all agree ([mapping results](../results/page-highlight-mapping.json)). Ambiguous and below-evidence listed spans are shown, with the relevant caveat. Unicode-comment mutations (`é中🙂` plus HTML-like text) preserve correct UTF-8 span slicing on both sides/channels; text is rendered through React text nodes, not HTML injection. Desktop D3 and narrow/dark D4 screenshots were independently inspected: side-by-side desktop regions, both labelled outcome columns on narrow layouts, and D4–D6 misses visible. This is scoped visual observation, not a complete accessibility/design audit.

Additional helper probes (script (original private attachment not included in this package), [results](../results/page-extra-core.json), limit log (original private attachment not included in this package)) computed a valid 65,536-byte Go comment-padded fixture and rejected 65,537 bytes; checked Unicode regions; and confirmed malformed Go yields `not-compared / unsupported-input / candidate-extraction-error`, with no invented match modes. An injected 8,388,609-byte output is refused and clearOutput runs. The output test uses a stub comparison seam, not a naturally generated maximum output or memory budget. Repeated fixture checks are repeats of the same eight cases, not new independent populations.

WASM SHA-256 `3001cdcd5f29412cdf32131b5755364c704ac54915cd1ab397817eb52c18d61c` and loader `6785a5e2fff23ca4722d419722b7e2f84a52dd9613b3152f7963729d3bc01f7b` are unchanged. Canonical bodies are engine-validated, downloaded unchanged and contain no fabricated provenance envelope. Listed spans are mapped from engine UTF-8 bytes; unhighlighted text is not represented as a verdict about origin. Experimental, non-proof, no-chronology and insufficient-evidence notices remain visible.

## WEB4-G1 — full criterion coverage remains distinct from code correctness

Read the **current public** ROADMAP from `traceweave-spec-public-wt` at **`184b74b072a7fdc4f79d385d512f542e8c32ab8a`**, WEB.4 line 341; exact bytes and hash are retained in public-ROADMAP.md (original private attachment not included in this package) / setup.json (original private attachment not included in this package). The initial similarly named private checkout was identified and not used as the authority for this assessment. The operative clause is:

> A sample or dropped file is edited by hand or by named transformations: reformat, rename identifiers, reorder declarations, copy a fragment, embed in unrelated code, insert tokens at the evasion interval.

**Satisfied bounded portions:** side-by-side sample/transformed panes; live hand editing and dropped-file computation; live region/outcome updates; six immutable demonstrations with three both-mode misses; separate identity/unrelated self-checks. Misses are displayed as plainly as matches. The fixed recipe labels are honest: selecting a named recipe resets both editors to recorded bytes, and the page explicitly says this does not transform arbitrary dropped code. Custom inputs have no retained native expectation. No fabricated generic transform support was found.

**Not established:** named transformations acting on the currently selected sample/dropped code. Recipe loading replaces the input rather than transforming that input. D6 supplies one precomputed composite tiny-fragment-in-host outcome; it provides neither a current-input copy-fragment action nor a separately inspectable fragment→embedding sequence. D5's unrelated replacement cannot substitute for those operations. Thus full eligibility cannot be inferred by silently narrowing the named-transformation clause to “load these preset pairs.” Hand editing demonstrates the manual branch; it does not prove that missing named actions exist.

The exact text does **not** specify a universal Go AST transformer, a minimum fixture count per operation, separate buttons, or two additional independent fixture IDs for fragment versus embedding. I do not add those requirements. A composed sequence could demonstrate copying then embedding, with the stages identifiable and correctly evaluated. Likewise it is not necessary to alter the accepted six-demo denominator or force D6 into a different outcome class.

**Minimum functional completion recommendation:** retain all immutable demonstrations/expectations and add clearly scoped named operations on current editor input, including an observable copy-fragment then embed operation (which may be one staged sequence), with explicit supported-input/refusal semantics and deterministic verification of the new operation outputs. Exercise a dropped input through the supported named path. Do not promise universal semantics preservation or generic arbitrary-code support. Until that operational clause is demonstrated or its interpretation is explicitly dispositioned by the criterion owner, this review does **not** recommend full WEB.4 closure. This is a documented implementation/criterion gap, not deception in the current UI and not a new numerical finding against the accepted fixtures.

## Preservation and limits

Author tree/source/fixtures remain unchanged and clean at the exact tip; old accepted files are unchanged except the declared package/nav additions. Final preservation (original private attachment not included in this package) records before/after hashes. New writes are only reviewer storage and owned scratch; no code fix, push, deployment, status/count/gate edit, acquisition, signing, corpus/M3, sublane or production data.

Setup issues are retained separately: the first extended browser attempt failed because the reviewer had not created its new evidence-copy destination; the first supplemental invalid-Go assertion used “skipped” instead of the engine's actual “not-compared” label. Those reviewer-harness errors were corrected without changing product code, fixture/config bytes, native expectations or acceptance thresholds. Final actual observations are retained alongside the initial logs.

Browser resolver/background-network restrictions are not OS network-denial/zero-attempt/privacy proof. Core/build ran under deny-network sandbox; browser work used an owned disposable profile/process/server with only loopback navigation. CDP substitutes for chooser; drop is synthetic DOM input. No full keyboard/AT/physical-device/zoom/reduced-motion acceptance, active synchronous-core cancellation timing, offline reload, naturally generated output boundary, WEB.6 formal baseline/performance/memory or broader conformance certification. Input cap is a product limit; output cap is after construction. **Disposition: request the WEB4-P1 fix and focused re-review; preserve the positive fixed/live evidence; full WEB.4 eligibility remains separately open under WEB4-G1. M3 HOLD.**
