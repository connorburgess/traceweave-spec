> Portable adaptation of the dated original review/record; original SHA-256 `e3f7e4698fa1123a54640ea34ac629a75c9dd750068b9969a670601f2123b98b`, 13125 bytes. Historical verdicts remain historical. Local links are rebased; unretained attachment links and private locations/lane/deployment identifiers are omitted. This retention does not independently re-review the new package.

# Independent WEB.3 Fingerprint review

**Verdict: changes requested for FP-1 (medium, blocking the bounded flow's acceptance).** Exact reviewed revision: `1dfaf7fb3638cf825c49661e2119677d0d89725f`, parent reviewed Shelf `86036c43394e94c1431ca335195a86e7754da6df`, branch `feature/web3-fingerprint-20261127`. The fixed valid-ID cases and lifecycle checks pass. No other blocking finding identified. This is not WEB.3 three-flow completion, WEB.5 certification, WEB.6 baseline/performance acceptance or M3 clearance.

Read the author handoff, repository/ancestor instructions, implementation notes, complete nine-file diff, worker, shared admission/build functions, component and both test runners. The author tree was clean at the exact tip before and after review. Only review artifacts and disposable scratch files were written; no author source, dependencies, user files, gate or protocol changed. No push or sublane.

## FP-1 — admission and published filename limits disagree with the frozen catalogue ID contract

Location: src/lib/fingerprint.ts:33 (original attachment not retained), passed unchanged as `id` at line 67; FingerprintTab.tsx:27 (original attachment not retained) / line 99; `docs/fingerprint-flow.md:3`.

`admitSources` permits names up to 255 UTF-8 bytes, rejecting selected path/control characters but permitting uppercase, spaces, non-ASCII, leading punctuation and names over 64 characters. Extension admission is case-insensitive. These same names are then used verbatim as catalogue IDs. The pinned engine requires `^[a-z0-9][a-z0-9._-]{0,63}$`, as also specified by `spec/catalogue-report.md:136` at the CLI's spec pin `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`.

Reproduced in **real worker / headless Chrome**, using an otherwise grammar-valid Go source:

1. Select Go and drop `Foo.go`, `two words.go`, or `"a".repeat(62) + ".go"` (65 characters).
2. The form lists the file and announces readiness, with Start enabled.
3. Start loads the engine and reads the file, then fails with `catalogue refused: artifact id ... does not match ^[a-z0-9][a-z0-9._-]{0,63}$`.
4. No catalogue or configuration download is offered.

The independent API probe reproduces the same admitted-then-refused mismatch for those names, `--flag.go`, `é.go` and `<img>.go`. A 64-character lowercase ID builds; 65 characters fail. Browser evidence is under `adversarial.unsupportedNames` in browser-results.json (original attachment not retained). API cases and boundaries are in probe-final.log (original attachment not retained) and probe-final.mjs (original attachment not retained).

Impact: the documented admission conditions allow ordinary filenames that cannot be represented by the unchanged catalogue contract. Such a selection cannot produce the promised catalogue even when its source is valid and within every size limit. This is a functional/admission mismatch, not output corruption or injection: engine refusal is correctly propagated and export remains unavailable.

Smallest correction: align metadata admission, explanatory filename copy and tests with the existing catalogue-ID grammar, explicitly telling users how to rename incompatible filenames before worker start. Preserve the contract and exact IDs; silently lowercasing, truncating or normalizing names would introduce different identity/collision semantics and needs its own explicit design. Recheck a valid 64-character name and early refusal of uppercase/space/non-ASCII/65-character examples with no file read or stale download.

## Independently reproduced checks

Product code was built from a disposable `git archive` of the exact revision with APFS copies of existing provisioned dependencies. Author files were not built into or edited. The only adjustment to the copied author fixed-fixture runner was replacing CLI stdout output with an explicit temporary output file and reading those bytes; product source and fixture expectations were unchanged. Browser test extensions live in this review directory.

Every CLI invocation, including `--version-json`, inherited an **outer temporary `TRACEWEAVE_PRIVATE_DIR`**. Every catalogue invocation used explicit temporary config/source/output paths. None used default private storage. The retained binary was located via the prior offline-demo handoff; no compilation or acquisition was needed.

| Identity | Verified value |
| --- | --- |
| CLI stamp | `stamped`, implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c`, spec `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191` |
| CLI SHA-256 | `7fc12a524c454d8e5769cb397c64c4a65f237b3c8d207ce73fa78605afb66ec5` |
| Unchanged WASM SHA-256 | `3001cdcd5f29412cdf32131b5755364c704ac54915cd1ab397817eb52c18d61c` |
| Unchanged loader SHA-256 | `6785a5e2fff23ca4722d419722b7e2f84a52dd9613b3152f7963729d3bc01f7b` |

- Fixed-fixture reproduction (original attachment not retained): 9/9 complete catalogue byte comparisons against that native CLI and 9/9 repeated-call equality, with the original expected hashes/outcomes. Covers all five exposed profiles, nonsorted multi-file IDs, CRLF, empty/insufficient-token input, invalid UTF-8, Go lexical failure and a valid exact-1-MiB source. Original nine metadata refusal classes, 32-file admission, aggregate exact-L/L+1 predicates, oversized refusal before read and 262,144-byte read chunk bound also pass. These are bounded implementation cases, not acceptance/performance populations.
- Independent API probe (original attachment not retained): 16 path/control/extension/overlength-name refusals; five invalid size predicates; five unsupported/prototype-like profiles; duplicate-name refusal; reader-error propagation; native/WASM equality for an additional original-CRLF case (catalogue SHA-256 `2fdedb32edede7adee251c2df895ab9a3c91d9e43eb564c10477d1f2d60b2bda`), including original input digest and final-newline config hash. Identical bytes under two valid IDs are correctly refused by the engine's existing duplicate-digest rule; no deduplication or silent record drop occurs.
- Output/error unit seams: exact 8-MiB synthetic output retained by identity; L+1 refused before validation; invalid validation result, malformed UTF-8, invalid JSON and engine throws propagate; `clearOutput` runs on all six success/failure paths. The size-boundary seam uses a stub engine and valid padded JSON, **not naturally produced engine catalogues or a memory bound proof**.
- Lint (original attachment not retained), typecheck (original attachment not retained), production build (original attachment not retained), and exact-diff whitespace checks pass. Build telemetry disabled. These are independently run local checks, not remote CI or deployed behavior.

The API checks are reproducible with the retained environment locator (original attachment not retained) and final script, setting the outer temporary private directory before `node probe-final.mjs`. The fixed test is `node tests/fingerprint/check.mjs` in the disposable archive with `TRACEWEAVE_CLI` and the same outer private directory, using the described output-file adapter. Source identities and runner/log hashes are retained in evidence-identities.json (original attachment not retained).

## Worker, race, download and browser results

Final runner: browser-final.mjs (original attachment not retained); log (original attachment not retained); results (original attachment not retained). Installed Chrome `158.0.8127.89`, disposable temporary profile, static export served only on loopback, DNS rule denying other hosts and a dead loopback proxy for non-loopback destinations. Final launch also uses basic password storage/mock keychain and disables crash reporting; no shared browser/user profile or native user keystore is used for the tested flow. Server, Chrome and profile are disposed by the runner. This isolation setup is not a comprehensive network-denial/zero-attempt privacy proof.

Observed passes:

- Real worker builds a catalogue; explicit downloaded catalogue bytes equal the retained CLI result using downloaded exact config. Catalogue SHA-256 `4e69c80eafc44ca2448f8a6d6e75fa5c7d442eb50e193086328147deebb2205a`. Both downloads complete before reading. Synthetic drop path completes a job. The native chooser is substituted by CDP file injection.
- Tab/Enter smoke reaches file control, Start and both downloads; label/description relationships exist. No complete keyboard/AT accessibility acceptance is inferred.
- Oversized selection is refused and both stale exports disappear. A new valid selection and profile change also invalidate both downloads. Profile change clears selection and disables Start. No automatic profile inference or config widening is introduced.
- Controlled local asset delay permits cancellation and navigation while a job is pending. Unmount terminates its actual worker; remount has no old files/result. Restart after cancel succeeds. A local asset 503 produces an alert and no export; a later job recovers.
- Deterministic adversarial callbacks: the runner wraps the actual Worker solely to retain its installed callbacks, then directly invokes a terminated job's saved callback after navigation and after cancellation/restart, supplying an earlier real result and a stale phase; it also invokes the old error callback. The identity guard ignores all of them: no stale download, phase or alert. This is forced stale-delivery coverage, not an assertion that Chromium naturally delivered a post-termination message.
- Two synchronous Start clicks create exactly one worker. Delayed asset responses released after several terminated/restarted jobs produce only the current job's `new.go` outcome. No old-ID result appears.
- Untrusted `<img>.go` is displayed as text, not a DOM image, then correctly fails the engine grammar (FP-1); traversal filename is refused by metadata admission. Download names come from the fixed profile registry, never from raw filename or returned catalogue content. No uploaded configuration or untrusted output JSON import exists in this flow.
- No uncaught page exceptions in final run. Existing signing/trust/storage logic, Compare/Verify components, profile/config registry, engine assets and lockfile are unchanged by this commit; ShelfApp changes only integrate the new tab.

Source reasoning: each Start owns one disposable worker; cancel/unmount terminates and clears its ref; handlers check worker identity before any update; finish terminates before clearing running state. Engine output is copied by the loader before later validation/hash calls and cleared afterward; catalogue export uses those returned bytes without JSON reserialization. Configuration export UTF-8 encodes the same config string whose exact bytes/hash produced the catalogue. Worker reads raw `File` slices and performs no source decoding/newline normalization. Asset/read/engine/validation errors cannot reach a result/export branch.

## Notices and remaining limits

The new surface states experimental status, the ownership/authorship/copying non-proof triad, and catalogue-today versus prior existence/M4 before action. It discloses filename/digest/fingerprint export, separates implementation caps from unfrozen WEB.6 budgets, identifies error/insufficient-token entries, and avoids progress percentages, signature verification or complete privacy claims. Source support is explicit Go/Rust/TS/Python/plain-text selection and the existing frozen configurations. Extension admission is limited to `.go/.rs/.ts/.py/.txt`; TSX/Markdown and JSX detection are not added or claimed. This review is not a new exhaustive page-wide claim-map census.

Unperformed: native OS chooser keyboard behavior, AT/physical-device/zoom/reduced-motion/visual layout review, active-core-phase cancellation/deadline measurements, naturally produced output-L/L+1 fixtures, complete all-limits full-flow execution, memory/long-task measurements, cache/offline reload, comprehensive network/privacy enforcement, deployed asset/source identity, complete three-flow WEB.3 parity, WEB.4 demonstrations, WEB.5 certification, WEB.6 frozen-budget/baseline execution and M3 evaluation/acquisition. The 1-MiB cap and aggregate/output limits are product admission rules only. Loopback HTTP asset-delay tests provide no latency or performance evidence.

Earlier harness attempts are retained: the first independent browser output-file adapter incorrectly assumed a successful CLI would write no status text to stdout; this assertion was removed while continuing to compare the explicit output file. The first API adversarial run exposed FP-1, and another attempted two identical artifacts and received the expected existing duplicate-digest refusal. These are recorded separately from final passing harness checks; no product expectation or fixture output was relaxed. Browser v2 and the final mock-keychain launch both reproduce FP-1 and passing lifecycle checks. No fix was made to author files.

**Eligibility:** do not accept this exact revision as the completed bounded Fingerprint implementation until FP-1 is dispositioned. The tested valid-ID byte path and lifecycle/error safeguards have positive evidence within the above scope. No gate/status/count/hold change is recommended. M3 remains held.
