> Portable adaptation of the dated original review/record; original SHA-256 `ae5f52c1a4625cf0e9ff9274b0780f509eac57bbf06b3d02909b6120af38b2a8`, 9244 bytes. Historical verdicts remain historical. Local links are rebased; unretained attachment links and private locations/lane/deployment identifiers are omitted. This retention does not independently re-review the new package.

# WEB.3 fixed-fixture drop-to-download supplement

2026-11-27. **PASS: 1/1 existing fixed fixture completed DROP → real worker → actual completed catalogue download → complete CLI-byte equality.** The exact configuration download also matches. This supplies the one direct route/output binding requested by the criterion reviewer; it does not itself close WEB.3 or change any gate. M3 HOLD.

## Exact app and fixture selection

Read the [criterion assessment](criterion-assessment.md) and its [fixture ledger](../fixture-ledger.json), hashes recorded in setup.json (original attachment not retained). Used only the clean accepted integration worktree `[private source path omitted]`, commit **`99a1a8bce5382a0345fa7e19d9bfd44575f9c016`**, tree `220d6436a1c6a8118ed6e91d5aaa6b1ba39985e3`. All 55 tracked files matched exact Git objects before use. This is the accepted/published source revision, tested locally; no current deployment interaction or WEB4 writer tree was used.

Selected unchanged `tests/fingerprint/expected.json` / accepted manifest **`results[0]`**, the nonsorted two-file Go case from the existing 9/9 Fingerprint set. Accepted expected manifest SHA-256 `f6201bba537af8eccb3043f7e2983788f1225fb6a8d2b60a3af17bdad487fad3`. [Selected accepted row](../drop/selected-accepted-fixture.json) is retained separately. No new dataset or expected output was invented.

| Input or expected output | Bytes | SHA-256 |
|---|---:|---|
| `z.go`, dropped first | 50 | `3be99f765d15f35569bf81b0ae75f01d215e3e11cbb235c4d5d074a28998159b` |
| `a.go`, dropped second | 50 | `5cc308e8ce4cb81a97110ab2dfdb6de93e1e93d615298639a88ae7cd1cb35e76` |
| Exact Go extraction config, including final LF | 200 | `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2` |
| Accepted CLI catalogue | 2,052 | `af2af05dc2f2ce0ae06b59dd14b825f42ac3415b93e7543d8c7098adda81daf2` |

Full fixed input bytes are retained in [fixture/](../drop/fixture/). Names and bytes were copied from the accepted fixture definition and checked against these pins before browser use. The old fixture runner deleted its temporary native catalogue; its expected byte length/hash remained retained. Therefore this supplement regenerated **only that one CLI catalogue**, using the pinned native tool and exact fixed inputs/config, and required the preexisting 2,052-byte/`af2af05d…` identity before starting the browser. It is retained as [expected-cli.catalogue.json](../drop/expected-cli.catalogue.json). This is regeneration against an unchanged accepted expectation, not generation of a new oracle or a rerun of the nine-fixture suite.

Native CLI SHA-256 **`7fc12a524c454d8e5769cb397c64c4a65f237b3c8d207ce73fa78605afb66ec5`**, the WEB.3 retained CLI, was checked before copying/execution. Version reports stamped implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c`, spec `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`, version 0.0.1. This is not the later WEB4/signing `5d22…` binary. Both native calls (version and one explicit-output catalogue build) inherited a fresh outer temporary `TRACEWEAVE_PRIVATE_DIR` and macOS deny-all-network sandbox. Exact argv are in native-commands.json (original attachment not retained); raw version/stdout/stderr are retained. No build, signing, install or acquisition.

## Browser execution and measured sequence

The integration's existing static export was copied into owned scratch without modifying or rebuilding author output. [static-assets.json](../drop/static-assets.json) pins all 119 copied files. The loopback server recorded exact bytes/hash for each response; result.json (original protocol attachment not retained; [labelled reduced projection](../drop/result-projection.json) retained) contains the served-request log and real worker URL. Critical pins:

- WASM: `3001cdcd5f29412cdf32131b5755364c704ac54915cd1ab397817eb52c18d61c`, 1,129,029 bytes.
- Loader: `6785a5e2fff23ca4722d419722b7e2f84a52dd9613b3152f7963729d3bc01f7b`, 9,655 bytes.
- Local static HTML: `efbb24aed89348378cad38aae098f6716e58df275cad5a297d84ab9816930735`, 14,973 bytes.
- Actual worker bootstrap `_next/static/chunks/turbopack-worker-1hrsqshz0gfey.js`: `cf3e52b25b4c37e2b5e8ddfe13b5cfda970faec44792881b195d518b691aa93d`, 927 bytes. Its loaded chunks are separately pinned in the complete inventory/served log.

Installed headless Chrome **158.0.8127.89** used a new owned profile, download directory and loopback-only server. No shared browser. Script drop-download.mjs (original attachment not retained), launch (original attachment not retained), log (original attachment not retained), and full observations (original protocol attachment not retained; [labelled reduced projection](../drop/result-projection.json) retained) are retained. The script did not call `DOM.setFileInputFiles`, trigger a chooser, substitute a worker result or invoke the Fingerprint helper directly.

Observed sequence:

1. Opened the local accepted app in the fresh profile and navigated to Fingerprint. Verified Go selected, no available catalogue download, empty download directory and no earlier result.
2. Constructed the **existing** two File objects from verified raw bytes, inserted them into DataTransfer in `z.go`, `a.go` order, and dispatched a bubbling/cancelable **drop** event to the real drop target. Browser-side File SHA-256/lengths matched the accepted fixture. The chooser input's FileList stayed empty.
3. Clicked Fingerprint files. One **real browser Web Worker** was constructed; an observing subclass forwarded its original constructor/postMessage and did not change responses. Its posted selection was exactly Go plus `z.go`, `a.go`, both 50 bytes.
4. Observed actual worker phases: Loading engine assets → Reading selected files → Building catalogue locally. One result arrived, then Catalogue ready. Readiness alone was not the success condition.
5. Clicked Download catalogue and Download exact configuration. Waited for each distinct Chrome `Browser.downloadWillBegin` GUID's **completed** `Browser.downloadProgress` and on-disk file before reading. Both started only after this drop job. Download events are retained in the result record.
6. Compared complete downloaded catalogue bytes to the retained pinned CLI expected catalogue, complete downloaded config bytes to the accepted exact config, and real worker result bytes/config to both. All matched. Canonical catalogue order is `a.go`, `z.go`; input drop order was intentionally nonsorted. No normalization or JSON reserialization was used for equality.

Full observed artifacts: [downloaded.catalogue.json](../drop/downloaded.catalogue.json), [downloaded.config.json](../drop/downloaded.config.json), [worker-result.catalogue.json](../drop/worker-result.catalogue.json), and [expected-cli.catalogue.json](../drop/expected-cli.catalogue.json). Catalogue comparison is full 2,052-byte equality, not just digest equality. Config comparison is full 200-byte equality. No page exception was observed; page network events stayed on the owned loopback origin/blob URLs. The own server, Chrome process/profile and temporary download directory were disposed after retaining these outputs.

## Preservation, interpretation and limits

The local integration export's HTML/chunk hashes are not identical to the separately retained production retrieval's build artifacts. Retained comparison (original attachment not retained) records that distinction; this test does not assert deployment-build reproducibility or current served-runtime identity. Exact accepted source association is the clean integration revision and its Git-object checks; engine/loader pins match the accepted assets. The full local app asset inventory and actual served bytes are explicit so this cannot be mistaken for a live production test.

This was a **synthetic DOM drag/drop through the real handler**, not a physical OS drag gesture. It is direct drop-to-worker-to-completed-download evidence, rather than chooser-route or readiness-only inference. Browser isolation uses disabled background features, mock/basic key storage, a dead loopback proxy for non-loopback destinations and resolver restrictions; it is not comprehensive OS network-denial, zero-attempt privacy or offline-reload certification. No complete keyboard/AT/visual/device assessment, WEB.6 baseline/performance/memory measurement, full WEB.3 matrix or new conformance claim.

Only **1/1 additional drop fixture** was measured. Existing Fingerprint 9/9 helper/native catalogue fixtures remain a separate denominator, not nine browser drops. If citing prior Replay evidence: **20/20 expected native recomputation/disposition checks = 13 reproduced + seven correct mismatches**, plus nine separate invalid-loaded-input refusals; it does not mean 20 digest reproductions. This supplement reran no Replay/Compare suite.

Final preservation (original attachment not retained) verifies all 55 integration source files, all 119 original static-export files, clean exact HEAD and original CLI bytes unchanged. Other author worktrees, including the active WEB4 writer, were unused. New writes are confined to reviewer storage and owned scratch. No code/gate/count changes, production data, signing, CI, dependency acquisition, external navigation, publication, push or sublanes. The criterion reviewer/coordinator owns any broader disposition. **Focused result: PASS, one missing direct drop-download byte case supplied; M3 HOLD.**
