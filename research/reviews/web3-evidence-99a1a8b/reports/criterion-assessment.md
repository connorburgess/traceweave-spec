> Portable adaptation of the dated original review/record; original SHA-256 `610510113ffe29d0576f191a37ccaa023163a5575b65353d1748dd7a578d5efd`, 14812 bytes. Historical verdicts remain historical. Local links are rebased; unretained attachment links and private locations/lane/deployment identifiers are omitted. This retention does not independently re-review the new package.

# Independent WEB.3 criterion assessment

2026-11-27. **Compare and report-replay have direct bounded criterion evidence. Fingerprint has strong fixed-fixture/core and chooser-download evidence, but the supplied accepted evidence stops its drop job at readiness rather than checking that job's downloaded bytes. Recommend one narrow drop-to-download comparison before a literal WEB.3 closure decision.** This is an evidence gap, not a demonstrated product defect. Do not automatically close the gate from publication, engine agreement or these reports' individual implementation acceptances.

Read-only assessment of existing evidence; no tests rerun, browser/native execution, acquisition, source edits, publication or gate/count changes. M3 remains HOLD. New WEB4 work is separate and unused.

## Exact criterion and accepted chain

ROADMAP at spec `dd927025aee41bfa260570bf252a49a94160c961`, line 340, WEB.3 remains planned:

> Three flows must reproduce the command-line results. **Fingerprint:** dropped files yield a downloadable catalogue byte-identical to the command-line catalogue for the same inputs and config. **Compare:** two catalogues, or a catalogue and files, produce a report body with the same `bodySha256` as the command-line tool. **Verify:** loading a report re-runs it and shows whether the digest reproduces. Each flow is checked on a fixed fixture set, k/k.

Accepted Shelf chain: `86036c4` → Fingerprint `1dfaf7fb3638cf825c49661e2119677d0d89725f` → FP-1 fix `bfa8f5c320d30cda5a7bbdce4766befb4162629c` → Compare `fdac8bc571ac05b9c5a2ed2c338e27e1ae37a824` → Replay/published tip **`99a1a8bce5382a0345fa7e19d9bfd44575f9c016`**, tree `220d6436a1c6a8118ed6e91d5aaa6b1ba39985e3`.

The original Fingerprint review requested changes; **it is not a clean acceptance by itself**. The Compare review explicitly accepts FP-1's exact filename-grammar fix and Compare. Replay accepts the combined successor. Integration preserved the chain with no code merge delta. Independently checked all **55/55 accepted source-file hashes against local Git objects**, and fixed expected manifests against retained measured rows. No current engine execution is inferred from those static checks.

## Clause-by-clause coverage

| Criterion clause | Measured fixed coverage in retained evidence | Assessment |
| --- | --- | --- |
| Fingerprint exact catalogue for same inputs/config | **9/9** complete helper/WASM catalogue byte comparisons against CLI and **9/9** deterministic repeats; five profiles plus boundary/error inputs. Real browser chooser path: **1/1** Go catalogue/config download, completed downloads, exact CLI comparison. Synthetic drop path: **1/1** reaches catalogue-ready state; that job's download/CLI equality was **not measured** in the inspected script. | Core/output and chooser path supported; one narrowly missing direct drop-to-download binding for literal wording. Do not call 9/9 browser drops or report an unperformed test as a failure. |
| Compare two catalogues | Part of **17/17** helper/WASM full body-byte and SHA-256 comparisons/repeats; five-profile catalogue path. Real worker/download: **1/1** Go two-catalogue fixture exact CLI body bytes. | Eligible at report-body scope. |
| Compare reference catalogue plus files | Same 17-case set includes five-profile source path, building exact candidate bytes. Real worker/download: **1/1** Go source-path fixture exact CLI body bytes and candidate catalogue download. | Eligible; browser path count is **2/2 total**, not 17/17 UI flows. |
| Verify loading a report reruns and displays digest reproduced/mismatch | **20/20** expected replay cases/full native body-byte and digest comparisons/repeats, plus **9/9** invalid-loaded-input refusals. Browser: **2/2** body/full-report format replays with exact recomputed-body download; changed-config mismatch also observed. | Eligible through **Replay report**, distinct from registration Verify. Requires explicit dependencies; no automatic dependency discovery is claimed. |
| Fixed fixture set, k/k | Versioned expected manifests contain the exact 9, 17, 20 rows; Replay's invalid set has nine further rows. Fixed browser scenarios are separately counted above. | Present and reproducible from retained manifests; do not sum layers into one population or infer full UI matrix from core tests. Final drop-specific byte case is the suggested evidence supplement. |

The criterion supplies no minimum k, platform matrix or requirement that every helper fixture traverse the browser. I do **not** invent a five-profile UI rerun requirement. The suggested single drop test closes the literal input-route evidence gap; it is not a demand for a new general suite.

### What each k means

Fingerprint's nine are Go multi-file nonsorted IDs, Rust, TypeScript, Python, text, empty text, invalid-UTF8 text, Go lexical failure and exact-1-MiB Go. Catalogue error/insufficient-token outcomes are still exact catalogue outputs, not claims all source extraction succeeded. FP-1 later aligns metadata/UI with the frozen lowercase 1–64-character catalogue-ID contract; six early-refused browser names and the valid 64-character native/WASM case were rechecked. The full original nine-case run was not repeated after that fix. Final expected vectors and engine are unchanged; acceptance relies on the focused fix review plus preserved earlier evidence.

Compare's 17 are ten five-profile × two-path cases and seven additional cases (unrelated content, missing suppression, profile mismatch, malformed config/reference, invalid UTF8 candidate, HTML-like tampered ID). **11 produce compared bodies and six canonical rejected bodies.** All 17 agree with CLI output; rejected body agreement is not successful matching or absence-of-reuse proof. Deterministic repeats are 17 additional repeat checks, not 34 independent fixtures.

Replay's 20 contain **11 loaded bodies and nine full reports**. **13 reproduce and seven correctly mismatch**; therefore “20/20 digest reproduction” would be inaccurate. The denominator is expected recomputation/digest/disposition agreement, including changed config/candidate, malformed dependencies, supplied/missing suppression, reproduced rejection and self-consistent result tampering. Nine invalid loaded documents are separate refusal cases, not extra successful replays. Retained expected and measured case/invalid-input arrays match exactly.

## Exact tools/configuration/artifact pins

| Identity | Pin |
| --- | --- |
| Native CLI used by these WEB.3 reviews | SHA-256 `7fc12a524c454d8e5769cb397c64c4a65f237b3c8d207ce73fa78605afb66ec5`; stamped Rust `traceweave` 0.0.1, implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c`, spec `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`. **Not** the later WEB4/signing `5d22…` binary. |
| WASM | `3001cdcd5f29412cdf32131b5755364c704ac54915cd1ab397817eb52c18d61c` |
| Loader | `6785a5e2fff23ca4722d419722b7e2f84a52dd9613b3152f7963729d3bc01f7b` |
| Browser interaction environment | Local disposable Chrome `158.0.8127.89`; actual worker + downloads, CDP file injection and synthetic DragEvent; not physical OS chooser acceptance. |
| Browser fixed Go source | `case.go`, SHA-256 `3be99f765d15f35569bf81b0ae75f01d215e3e11cbb235c4d5d074a28998159b`, 50 bytes. |
| Browser catalogue / Compare+Replay reference/candidate | `4e69c80eafc44ca2448f8a6d6e75fa5c7d442eb50e193086328147deebb2205a` |
| Browser Go extraction config | `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2` |
| Browser comparison config | `39345e9c8de2b566d19943563326062a46edd38e429a4a96f169307b15147333` |
| Browser Compare/Replay canonical body | `e6701a097f37abca4d4f797986d7ca96fc1a98747fc4e391e0b5273618154d27` |

Frozen extraction configurations, exact final-newline bytes, are identified by their hashes (not recreated or normalized here):

| UI profile / engine profile | Version | Config SHA-256 |
| --- | --- | --- |
| `go-tokens` / `go-tokens` | `draft-1` | `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2` |
| `rs-tokens` / `rust2024-tokens` | `draft-1` | `64b34335e4a61383ada1403a2df97c2e45dba987bbf0c8ec21385e04104d1277` |
| `ts-tokens` / `ts-tokens` | `draft-2` | `aeeed14177cd3be8fea69e453c825e74f2fd301d03babbf49329bde0cc4754de` |
| `py-tokens` / `py-tokens` | `draft-1` | `365ba7be82646f6505cc339a15b3f5c50632244001eee2e08c558ce22c77b016` |
| `text-plain` / `text-plain` | `draft-1` | `35c1f63cc2f669a54acb5f9792614721431943b2fd626ffb88982e53bd37323e` |

All exact per-case source/config/catalogue/loaded-document/expected-body/actual-body pins are retained in [fixture-ledger.json](../fixture-ledger.json) and the copied **unmodified** [Fingerprint expected manifest](../fingerprint-expected.json), [Compare expected manifest](../catalogue-compare-expected.json), [Replay expected manifest](../report-replay-expected.json). These are evidence copies, not regenerated expectations. Alternate/malformed/suppression configs each have their own per-row hash; no one “default config” is substituted for them.

Manifest SHA-256: Fingerprint `f6201bba537af8eccb3043f7e2983788f1225fb6a8d2b60a3af17bdad487fad3`; Compare `c1547204957003f6fb913a714ed1645fd5cd9de1f11e30f8c2b339a2fbb6517e`; Replay `aa074fb7bc38a46b76729e946b103e9e06b84b3d1ddc278b30919a74a2b9950c`. Registry/helper `src/lib/wasm.ts` at final tip: `ebd2faeb9d9827c2971ecf6eeca9487ffb282785f9cf4197ce3ff0afad34a634`.

## Body/full-report and deployment boundaries

Compare exports canonical body bytes and uses native `--body-only` as the like-for-like oracle. **That satisfies WEB.3's explicit report-body clause**; a full provenance-envelope constructor/export is not demanded by this criterion. Do not add that as a closure blocker.

Replay accepts an explicit canonical body or full report with selected exact config/reference/candidate/optional suppression. Body input must be strict canonical bytes; a full report can have noncanonical document formatting, with body/provenance consistency validated and canonical body digest targeted. The UI shows digest equality independently from comparison status: a rejected body can reproduce. It neither reconstructs historical binaries nor authenticates producer/time/signature/ownership, and does not re-extract original sources. These are limits, not missing WEB.3 requirements. Registration Verify is a different unchanged flow and does not substitute for replay evidence.

The publication report binds exact `99a1a8b` to provider deployment `[provider deployment identifier omitted]`, plus static served HTML/scripts and exact loader/WASM hashes. It explicitly ran no live tab interaction or engine input. This supports published-source/asset association only. It cannot replace the retained local browser tests, repair a missing test, establish reproducibility of a deployment build, or prove current live behavior. This assessment makes no new network/current-deployment claim.

Native and WASM share implementation/spec ancestry: finite byte agreement is an execution oracle for web-wrapper preservation, not an independent mathematical implementation. Real worker and download checks prevent treating engine parity alone as a flow test. Forced stale callback, error, filename/admission and invalidation checks supplement flow correctness; mock seams are not counted as successful real engine/browser cases.

## Smallest next test / recommendation

For a literal closure record, add **one fixed valid drop fixture** at the accepted `99a1a8b` source: use existing first Fingerprint fixture's exact `z.go`/`a.go` bytes (drop in nonsorted order) and Go config pin `dfbc…`. After the actual drop handler and real worker complete, download **both** catalogue and exact config, wait for that job's download completion, then compare complete downloaded catalogue bytes to the retained CLI output for those exact names/bytes/config. Expected existing catalogue pin is `af2af05dc2f2ce0ae06b59dd14b825f42ac3415b93e7543d8c7098adda81daf2`, 2,052 bytes. Record exact source/config/native/WASM/browser/artifact pins and outcome **1/1 drop-to-download equality**. Invalidate/clear any earlier download so an old chooser result cannot satisfy the comparison. Preserve existing explicit native outputs/private isolation.

This test is **proposed, not authorized or run here**. No new corpus, profile, engine build, hosted/deployed runtime check, full UI matrix or criterion amendment is needed. If the coordinator accepts compositional drop-ready + chooser-download + shared-helper evidence as sufficient, state that inference explicitly rather than labelling the drop bytes independently measured. My conservative recommendation is to obtain the single missing direct binding before closure; Compare/Replay need no further criterion-specific test on the supplied record.

Do not widen this request to WEB.5 claim/privacy certification, WEB.6 performance/accessibility/budget baselines or unrelated visual/device tests. Those unperformed checks remain separate gates, not new WEB.3 conditions. No gate/status/count edit follows from this assessment. M3 HOLD preserved.

## Consumed report identities and checks

Exact report hashes:

| Record | SHA-256 |
| --- | --- |
| [web3-fingerprint-independent](fingerprint-review.md) | `e3f7e4698fa1123a54640ea34ac629a75c9dd750068b9969a670601f2123b98b` |
| [web3-compare-independent](compare-review.md) | `eedbde072e530785ccf38edf0c092b82eff0a0ab2d4dd94e5a709f03534fbd7f` |
| [web3-replay-independent](replay-review.md) | `2ec093fe30003b14d3694aacf994bb8a63eb63dae6513284666e6a4b7b95981b` |
| [web3-integration](integration-record.md) | `5f72e3535238ae68b8b8ee4e3962f22b4970fa16f36b5e9ecd7b4fd7cda889af` |
| [web3-publication](publication-record.md) | `10c29b1cea2399dd7bbfb2ffee8d69818d93c17c61124e586a05387b8ffb1b91` |

Complete consumed identities (original attachment not retained) pins selected reports/results/runners, manifest records, retained browser native outputs, deployment records and ROADMAP bytes. Read-only checks passed: all 314 Replay, eight integration and 22 publication manifest entries; 22 Fingerprint and 12 Compare review-artifact identities; all 55 accepted source Git-object hashes. Independent JSON recounts reproduce 9/17/20 fixture cardinalities and expected outcome partitions. No report or source was modified. An exploratory JSON lookup assumed Fingerprint used key `cases`; it was corrected to `results` before recounting; no output expectation changed. Links/hygiene and output hashes are checked separately. No new test execution is claimed.
