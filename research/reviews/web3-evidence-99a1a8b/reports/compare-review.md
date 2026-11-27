> Portable adaptation of the dated original review/record; original SHA-256 `eedbde072e530785ccf38edf0c092b82eff0a0ab2d4dd94e5a709f03534fbd7f`, 14073 bytes. Historical verdicts remain historical. Local links are rebased; unretained attachment links and private locations/lane/deployment identifiers are omitted. This retention does not independently re-review the new package.

# Independent Catalogue Compare review and FP-1 re-review

**Separate verdicts:**

- **FP-1 resolved; accept exact fix `bfa8f5c320d30cda5a7bbdce4766befb4162629c`** for the focused filename-admission correction to `1dfaf7fb3638cf825c49661e2119677d0d89725f`.
- **Accept exact Compare `fdac8bc571ac05b9c5a2ed2c338e27e1ae37a824`** for the bounded two-path canonical **report-body** implementation. Its immediate parent is that exact FP-1 fix. No new blocking findings or additional finding IDs.

Neither verdict closes WEB.3 or certifies WEB.5/WEB.6. There is no full report provenance envelope or report-replay Verify flow here. No gates, counts, criteria, holds or M3 authorizations change.

Read the handoff, FP-1 fix report, ancestor/repository instructions, complete diffs, helper/worker/UI code, implementation notes and portable test runners. Author tree was clean at the exact Compare revision before/after review. All execution used a disposable archive of that revision, APFS copies of provisioned dependencies and existing tools. No author files or original independent review artifacts were edited; only thread-storage review artifacts and disposable scratch were written. No sublane, download, service contact, push or deployment.

## Focused FP-1 disposition

The [original finding](fingerprint-review.md) said metadata admission accepted names the pinned engine could not use as catalogue IDs, announcing readiness before later job refusal. The fix changes `src/lib/fingerprint.ts:33–39` to exact `^[a-z0-9][a-z0-9._-]{0,63}$` and case-sensitive matching extensions, and updates UI/docs to publish the same 1–64 lowercase ASCII rule and rename instruction. No name mapping, case conversion, truncation or collision policy was introduced. Names such as `x..go` remain valid opaque IDs under the actual contract and are not treated as paths.

Independent API/worker probe (original attachment not retained), results (original attachment not retained): five valid filename classes (numeric-leading, internal punctuation, repeated internal dots and exact 64-character boundary) pass both Fingerprint and candidate-source admission; 16 invalid cases, including uppercase, spaces, non-ASCII, leading punctuation, 65 characters, path separators, equals, HTML-like text, NUL and terminal CR/LF, fail. Duplicate IDs fail. A real WASM catalogue using the exact valid 64-character name equals the retained native CLI output, SHA-256 `21fdd43745abf686f37626f1961b9edebd122b2d419227210045e9517667d0dd`.

Real browser recheck refuses the five original FP-1 name classes plus a literal-backslash name before worker creation: no readiness, Start disabled, both old exports unavailable. No worker can enter its source read path in these refused selections. This does not instrument all browser IO. The exact FP-1 product files/worker are byte-identical between the fix commit and Compare tip; the latter's successful build/browser execution therefore exercises those same fixed files. The unrelated full nine-case Fingerprint suite was not repeated; its previously reviewed evidence and unchanged expected vectors/engine remain separate.

## Compare byte and rejection evidence

17-case reproduction (original attachment not retained) independently executes the committed runner against the retained stamped CLI. **17/17 full canonical body byte comparisons and SHA-256 comparisons, plus 17/17 deterministic repeats pass.** The expected case records in `tests/catalogue-compare/expected.json` match, including exact input/config/catalogue/body digests, status, rejection and native exit code.

- Ten cases cover both paths for all five existing profiles: Go, Rust, TypeScript, Python and plain text. Native source-built catalogue bytes agree; source-path candidate IDs remain exact. No profile/config inference, rewriting or promotion occurs.
- Seven additional cases cover unrelated Go content, required-but-absent suppression, profile mismatch, malformed comparison config/reference, invalid UTF-8 candidate and a raw tampered HTML-like artifact ID. Canonical engine rejection bodies agree with native output rather than becoming fabricated successful matches. A completed rejected comparison remains explicitly labelled rejected and downloadable; application/read/asset failures offer no output.
- The browser executes both real worker paths and downloads complete body bytes equal to the retained CLI, SHA-256 `e6701a097f37abca4d4f797986d7ca96fc1a98747fc4e391e0b5273618154d27`. Source-path candidate download also equals native catalogue bytes. Each download waits for its own completed event before bytes are read.

Tool identities were independently checked: native CLI SHA-256 `7fc12a524c454d8e5769cb397c64c4a65f237b3c8d207ce73fa78605afb66ec5`; stamped implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c`, spec `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`. Unchanged WASM SHA-256 `3001cdcd5f29412cdf32131b5755364c704ac54915cd1ab397817eb52c18d61c`; loader `6785a5e2fff23ca4722d419722b7e2f84a52dd9613b3152f7963729d3bc01f7b`. These prove finite native/WASM output agreement using the provisioned identities, not a new independent algorithm oracle, engine rebuild or source/binary equivalence proof.

Every native process, including version queries, ran with an outer temporary `TRACEWEAVE_PRIVATE_DIR`; every catalogue/compare command used explicit temporary config/source/output paths. Owning runners create/remove their own outer private directories before/after native execution. The separate independent probe uses the review's disposable outer directory. No default private storage was used. Environment locator (original attachment not retained) retains existing CLI/scratch locations for local recheck.

## Bounds, read ordering and error seams

Source and executed checks agree on these **implementation** limits: 4,194,304 bytes and 1,000 entries/catalogue; 65,536 bytes/config; 1,048,576 bytes/source or the lower selected config cap; 32 sources; 8,388,608 combined input bytes including configs/source IDs; 8,388,608 body output bytes checked after construction. These are not frozen WEB.6 budgets or memory guarantees.

The 17-case runner checks missing/oversize documents/configs, duplicate/invalid source IDs, aggregate refusal, exact individual metadata limits, no-read oversize refusal, invalid extraction configuration and lower effective cap. Additional independent probe checks:

- Exact aggregate L accepted and L+1 refused on **both input paths**, 32 source IDs accepted/33 refused, and five invalid/oversize source-size predicates refused.
- Actual engine catalogue with 1,000 distinct insufficient-token artifacts accepted; 1,001 refused by the product limit. Malformed untrusted catalogues remain bounded raw engine inputs; only validated fields are used for the product entry-count check.
- Reader preserves bytes across chunk boundary and never requests over 262,144 bytes; oversize reader entry is refused before `slice`.
- Transpiled exact worker executes with a mock asset loader returning the real pinned WASM and counted file-read seams. Invalid ID: zero loader/document/source reads. Lower-cap case with a small first source and oversized second source: three config/catalogue document reads, **zero source reads** before refusal. Invalid extraction config: also zero source reads. This is deterministic worker-path instrumentation, not OS/browser disk tracing.
- Stub engine output at exactly 8 MiB retains byte identity/hash, preview truncates to 20,000 characters with a flag, L+1 refuses before body validation, failed body validation refuses export, and cleanup runs on success/refusal/error. These are JavaScript seam tests with padded JSON, **not naturally generated engine output-limit fixtures** or a preallocation/peak-memory proof.

## Lifecycle, invalidation and escaping

Independent extended browser runner (original attachment not retained), log (original attachment not retained), results (original attachment not retained) use installed Chrome `158.0.8127.89`, a disposable profile with basic password storage/mock keychain, loopback-only static server, DNS denial for non-loopback hosts and a dead loopback proxy for non-loopback destinations. No shared browser/user profile is attached. Server/browser/profile cleanup belongs to the runner. This setup is ordinary local correctness isolation, not comprehensive OS network-denial, zero-attempt or privacy certification.

Observed passes:

- Real navigation while the asset response is held terminates the old Compare worker. Returning to the tab has no prior selections/results. Cancel/restart works; two synchronous Start clicks create exactly one worker.
- A wrapper retains the **actual installed callbacks**. Directly invoking a terminated job's saved result/phase callback after navigation, and its result/error callbacks after cancel/restart, cannot publish a stale result, phase, alert or download. Late release of old asset responses leaves only the current job's output. Forced callback injection exercises identity guards; it is not a claim that Chromium naturally delivered messages after termination.
- Every document input (comparison config, reference, candidate, extraction config), source selection and path switch invalidates old output. Both download types disappear. An actual 4-MiB+1 catalogue selection refuses before read. Missing selections, worker/asset failure and cancellation cannot preserve old exports. Local HTTP 503 failure is recoverable on a subsequent job.
- Canonically rejected untrusted input creates no HTML in the preview. A **synthetic current-worker result seam** also places literal image/script markup into the preview field: React displays it as text, creates no image/script nodes and runs no injected handler. This distinguishes UI escaping proof from what the real canonical engine includes in its rejection body. Truncation logic is independently checked at the helper seam; downloaded bytes are never replaced by preview text.
- Enter/Tab smoke covers navigation, Start, body/candidate download and Cancel; CDP substitutes only for the native chooser. No uncaught page exceptions occurred.

Source reasoning supports these observations: controls disable during a job, the worker ref guards duplicate Start, cancel/unmount terminates/clears it, handlers compare exact worker identity, and finish terminates before publishing idle state. Raw inputs/config bytes are passed unchanged. The loader copies returned output before validation/hash operations; only that original byte array is transferred/downloaded. `clearOutput` does not invalidate the copied bytes. Preview parsing happens in the worker and React uses text rendering, not raw HTML.

## Body-only contract and preservation

The current `tw.compare` API exposes canonical **body bytes**, not the native full provenance envelope. UI/docs accurately name the body-only download and its `bodySha256`, state that it is not a signed/timestamped record, and disclose the missing envelope constructor. No JavaScript producer/stamp/time wrapper is fabricated, and native comparison uses `--body-only` for like-for-like evidence. This is accepted as the requested bounded body-flow implementation; it does not satisfy a full report-envelope requirement by implication. A future full-envelope interface or report-replay Verify implementation requires its own authorized design and review.

Experimental, non-proof and catalogue-age/M4 notices precede action. Missing suppression is disclosed and produces canonical rejection. Failed/insufficient-evidence comparison is not presented as proof of no reuse. Downloads disclose identifiers/digests/spans/fingerprints. No signing, registration verification, trust, storage, pasted-text Compare, engine assets, profile registry, lockfile or criteria changes were introduced. TSX/Markdown and JSX detection are not added or claimed.

Independent local lint (original attachment not retained), typecheck (original attachment not retained), production build (original attachment not retained) and exact-diff whitespace checks pass. Build uses existing dependencies with telemetry disabled in the disposable archive; no unrelated suites or new engine builds were run. The initial independent 64-ID digest assertion used whitespace-different synthetic Go source; native/WASM already agreed on those bytes. The probe was corrected to the handoff's exact source bytes, retained in initial diagnostic (original attachment not retained), and now matches the recorded boundary digest. No product code or expected fixture output was relaxed.

## Reproduction and residual limits

Recheck exact source with `TRACEWEAVE_CLI=<retained binary> node tests/catalogue-compare/check.mjs` from a disposable archive and an outer temporary private-directory environment; the committed runner itself supplies isolated explicit-output native invocations. Additional deterministic cases are in `probe.mjs` (use the outer directory in `review-env.json`). The extended browser runner operates on that archive's static build, using `CATALOGUE_COMPARE_EVIDENCE_DIR` for retained results and existing Chrome. Evidence identities (original attachment not retained) records exact source and review artifact hashes. Author tree/HEAD and unchanged dependency/source assets were checked again after execution.

Not performed: native chooser operation, complete keyboard-only/AT/physical-device/zoom/reduced-motion/visual audit, active-core cancellation/deadline or performance/peak-memory measurement, natural output-L/L+1 catalogues/bodies, complete all-limit full-flow execution, browser/OS IO audit, comprehensive network/privacy proof, cache/offline reload, deployed asset/source identity, full three-flow WEB.3 acceptance, page-wide WEB.5 claim-map recertification, WEB.6 frozen-budget/baseline/conformance execution or M3 acquisition/evaluation. Suppression input, full provenance export and replay Verify remain absent as disclosed.

**Eligibility:** FP-1 is resolved at the exact fix; Compare is eligible for acceptance only at the bounded two-path body-output scope above. No further finding IDs. WEB.3/WEB.5/WEB.6 remain open/uncertified as applicable; M3 remains held. No push/deploy or gate/count change follows.
