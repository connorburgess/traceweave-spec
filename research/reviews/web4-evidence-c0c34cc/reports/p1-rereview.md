> Portable adaptation of dated original review/record; original SHA-256 `3918ced6a9e36930b31a9dfbee14693c4c4344bf5c2fee03db851dfae28cef3b`, 7842 bytes. Retained citations are rebased; unretained private attachments are identified explicitly. Private locations, provider account/deployment targets/identifiers and selected private-checkout preservation metadata are omitted. Historical findings, outcomes and limits remain historical. This does not independently accept this new retention package.

# Focused independent WEB4-P1 re-review

2026-11-27. **WEB4-P1 closed at exact `58452ca38d9af21708e899a3c15d1be53f797ce5`; bounded implementation accepted with no remaining P1 blocker.** This reviews the final fix, not preliminary `879ad85`. Parent is `f934efeed7f6bd4db930ca22a5e3fa9247f50ac0`. **WEB4-G1 remains separate and unresolved; full WEB.4 eligibility is not established. M3 HOLD.**

Reviewed the clean owned worktree `[private source location omitted]`, final author handoff, exact three-file diff, complete component and committed browser regression. Source pins:

- `src/components/TestingPageTab.tsx`: SHA-256 `737476cde550a64c8d50b9a02a751ae3e9520c53f5a997b36b77608b6af39c8c`.
- `tests/testing-page/browser.mjs`: `4beaf257929237f3736f3ab46b46ee44ef29e280053baecee2a0353f664bbd76`.
- `docs/testing-page.md`: `fb05007de0a2f6cd154b5e846d2dbdf09680082c8c77d4f0f2d4aba241394349`.

## Source reasoning and fix scope

Recipe loading now has an independent operation generation/controller and requested-operation flag. Invalidating operations retire the load owner before worker invalidation. A success or failure completion must satisfy requested, active, mounted, un-aborted and exact-generation checks before changing any state. There is **no finally callback** that can unconditionally clear a newer loading state or restore work.

Cleanup aborts its lexical controller and retires only its own generation. It cannot clear a newer controller/generation. The generation/requested/active checks remain effective when AbortSignal propagation and abort itself are disabled, rather than depending solely on transport cancellation. Same-turn selection followed by Cancel leaves requested false before a pending effect can begin.

Cancel immediately enables editors, removes output and pauses computation. A previously loaded config is retained because all immutable recipes use the same fixed config bytes. Explicit edits after cancellation can therefore compute the retained editor bytes, while the cancelled load cannot install its incoming recipe bytes. Cancelling before any config exists directs Retry/reset; edits in that state explicitly name the missing configuration. Explicit retry requests a fresh load. Existing worker epoch/identity and file-read guards are unchanged. No fixture/helper/worker/style or transformation behavior was added.

## Independent execution and regression sensitivity

Fresh exact Git export, existing locally copied dependencies, no acquisition or author-tree build. Setup (original private attachment not included in this package) identifies the final export and a separate old-version control. All Node launches received an outer temporary `TRACEWEAVE_PRIVATE_DIR`. No native Traceweave CLI/version/probe was invoked.

- **Core suite passed**: eight complete retained-native body byte/digest cases, sixteen catalogue byte equalities and eight deterministic repeats, with the existing outcome/Unicode/limits checks. Core log (original private attachment not included in this package). Same fixture population, not new numerical expectations.
- **Fresh `next build --webpack` passed**, including TypeScript, with telemetry disabled under macOS deny-network sandbox. Build log (original private attachment not included in this package). This is a local web build, not CI or a native toolchain build. Author lint/default-build results were read, not represented as newly rerun lint/default builds.
- **Final committed browser suite passed unmodified** on owned disposable Chrome 158.0.8127.89/profile and loopback server. Log (original private attachment not included in this package), [results](../results/p1-browser-projection.json), [regression flags](../results/p1-regressions.json), exact launches (original private attachment not included in this package). All eight existing real-worker downloads still match retained native bytes; normal edit/drop/error/size/asset-cancellation behavior and both self-checks pass, with zero page exceptions.

The focused browser cases independently observed:

1. Hold both real recipe source responses, Cancel, release success: after 1.5 seconds no new worker, result or export; cancellation remains and editors are enabled. Retry recovers.
2. Disable fetch signal propagation **and replace abort with a no-op** at the browser test seam: late HTTP success still cannot change cancelled editor bytes/status/workers/output. Explicit edit resumes the already loaded fixed config.
3. Under the same ineffective-abort seam, late 503 failure cannot create a stale alert, change cancellation or restore output.
4. A newer D5 selection survives old late success and late failure: editor bytes, live native digest, status, download and worker count remain those of D5.
5. Pending-load unmount and remount/initial-load Cancel cannot resurrect output; initial cancellation points to Retry/reset, which recovers.
6. Selection and Cancel in the same turn do not start an operation afterward.

**Sensitivity control:** ran the identical final browser runner against the prior review's retained exact-`f934efeed…` build, copied into a separate disposable control directory with the same unchanged public fixtures. It completed the earlier numerical/browser portion, then **failed at the first `stayedCancelled` assertion after held D2 source responses were released**: status no longer contained “Cancelled.” Old-version failure log (original private attachment not included in this package) and launch record (original private attachment not included in this package) retain exit 1 and the precise assertion. The final build passes that same check and all later ineffective-abort/supersession/recovery checks. This demonstrates sensitivity to the reported regression, rather than a test that passes both versions. The old control is not preliminary `879ad85` and no author branch was reverted.

The first control attempt failed earlier because the reviewer had not created its screenshot evidence directory; setup-error log (original private attachment not included in this package) is preserved. The missing directory was created and the same runner rerun. That infrastructure failure is not the sensitivity result. No product expectation, code, fixture or threshold was changed.

## Preservation and remaining boundaries

Compared all 108 tracked files with the prior independent parent snapshot: only the three declared files changed. **All 46 files under public/testing-fixtures/** (44 copied evidence files, manifest and license) are byte-identical; configs, six-demo outcomes/miss count and controls are untouched. Helpers, workers, styles, engine assets and all other product files are outside the fix. WASM remains SHA-256 `3001cdcd5f29412cdf32131b5755364c704ac54915cd1ab397817eb52c18d61c`; loader `6785a5e2fff23ca4722d419722b7e2f84a52dd9613b3152f7963729d3bc01f7b`.

All author tracked files and clean exact HEAD were checked again afterward. The original independent review remains SHA-256 `8305145d89c91a714641bfc1c6f1a4447f7fe3674d58c2e537ba0fce7497e081`; prior evidence is preserved. Final preservation (original private attachment not included in this package), source copies and `evidence-sha256.json` record exact identities.

The requested operation gap WEB4-G1 is unchanged: recipe resets are not current-input named transformations, and D6 remains a fixed composite rather than an observable current-input fragment→embedding sequence. This focused acceptance neither closes that gap nor changes the six-demo denominator, three both-mode misses, D3 ambiguity or full WEB.4 status.

Finite synthetic lifecycle evidence; no measured synchronous-core interruption, timing/performance/memory baseline, full keyboard/AT/physical-device audit, OS browser network-denial/zero-attempt/offline-reload/privacy certification or broader conformance. Browser actions use owned isolated profiles/loopback only, with CDP/synthetic input limitations. No source edits, push/deploy, gates/counts, dependencies/acquisition, services, signing, production data, M3 execution or sublanes. **Disposition: accept final fix and close WEB4-P1; retain WEB4-G1 and existing limits.**
