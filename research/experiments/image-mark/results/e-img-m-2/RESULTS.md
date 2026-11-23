# Results of the measured run `e-img-m-2`

Protocol: [image-mark-protocol.md](../../../../drafts/image-mark-protocol.md), version `e-img-m-2`, frozen at commit `d3af1ee07595bde53ff53fcce0f3880ad04fb62c`, digest `cba3667307941766f19b2ff9141e89c154b1f9b53a01e11391135ffe8ab64110` (recomputed equal to the recorded value in both runs). Review: [confirmation pass](../../../../reviews/image-mark-protocol-review.md), commit `2f58436`. This commit descends from both.

Run on 2026-11-23 in a detached worktree at the frozen commit, following the reviewed command sequence. One host: macOS 26.4 arm64, CPython 3.14.6, torch 2.11.0 on CPU. Every number below is read from the committed records. Nothing was inspected or tuned between runs, and each full run was made once. Two full runs were made; `compare` reported them identical, so there is no invalid pair.

Files: `run-1/` and `run-2/` hold each run's `summary.json`, `entries.jsonl` and `queries.jsonl`, byte for byte as the harness wrote them. `transcript.txt` holds every command, its output and its exit code, with paths redacted to `<wt>` (the worktree) and `<main>`. The two `summary.json` files differ only in `elapsedSeconds`, `peakRssMiB` and `schemeSeconds`, which are excluded from `resultsSha256`.

**What this is and is not.** The 100 marked images and 100 hosts are **synthetic** (shapes, gradients, low-frequency texture and noise). Nothing here says anything about natural images, a false-accept rate, authentication, ownership or ancestry. Counts below are on 100 entries per scheme with exact denominators; no pass line applies to them.

## Validity checks W1–W6

| ID | Result | Count or exit code |
| --- | --- | --- |
| W1 inputs | **pass** | weights 6/6 (`weights.errors` empty); sources 84/84 (`sources.errors` empty); `environment.deviations` empty (49 pinned distributions); `runtime.deviations` empty and `runtimeAfterRun.deviations` empty; generator goldens 3/3 |
| W2 offline | **pass** | `networkProbe.denied` true in both runs: `bind refused errno 1; loopback connect refused errno 1 (EPERM)`; `full` was run with `--require-network-denied` |
| W3 determinism | **pass** | `compare` exit 0: `entries.jsonl identical`, `queries.jsonl identical`, "resultsSha256 and results equal", "W3: identical". `resultsSha256` `6d87d2ccee6519dff43e9e8fe0c90abd360bca1f796f13d8aed4da53eb1a70bb` in both runs |
| W4 records | **pass** | `recordValidation.errors` empty (0 errors) in both runs |
| W5 payload round trip | **pass** | 100/100 for each of `tm`, `ps` and `dw` (`payloadRoundTrip.ok` = `of`) |
| W6 code identity | **pass** | `codeIdentity.ok` true in both runs; exit code of `full` 0 in both |

Other commands: `fetch_sources.py` 84/84 exit 0; the venv and the hash-pinned offline install exit 0; `fetch_weights.py --verify` under deny-network 6/6 exit 0; `git rev-parse HEAD` equals the frozen commit; `git status --porcelain --untracked-files=all` empty before the run and after `compare`; the unit tests, 22 of 22, exit 0 in 48.4 s; `full` run 1 exit 0; run 2 exit 0; `compare` exit 0. All with exit codes in `transcript.txt`.

## Pass lines P1–P4 (candidates only)

P1 is a premise check. **P2–P4 are implementation checks** (protocol §6): with HMAC payloads an accept needs a decoded string to hit a pseudorandom target, so zero accepts is close to guaranteed by construction whatever the images or schemes do. They do not measure a false-accept rate, say anything about natural images, or show resistance to forgery. There are two fixed public keys and clustered decoder outputs, so the comparisons are far fewer independent chances than their number suggests.

| Line | `tm` TrustMark-Q | `ps` PixelSeal |
| --- | --- | --- |
| P1: clean marked images correctly matched, at least 95 of 100 | **100/100, pass** | **100/100, pass** |
| P2 (implementation check): unmarked inputs accepted for any entry, 0 required | 0 in 20,000 comparisons, pass | 0 in 20,000, pass |
| P3 (implementation check): clean marked images accepted under the wrong key, 0 required | 0 in 10,000, pass | 0 in 10,000, pass |
| P4 (implementation check): clean marked images accepted for a wrong entry, 0 required | 0 in 9,900, pass | 0 in 9,900, pass |
| Protocol verdict (`met`) | **met** | **met** |

The `dwtDct` control has no pass line. Tested bits and threshold: `tm` raw positions 0–60 (61 data bits), k = 49; `ps` 256 bits, k = 167; `dw` 32 bits, k = 30. The verdict "met" is as the protocol defines it (W1–W6 hold and P1–P4 pass). It says nothing about natural images.

## Counts, per scheme, accepted for the entry's own payload

Each cell is the number of the 100 entries whose query was a `match` for its own entry (`correctMatch`; for transplant, reembed and overwrite this is the attacker's success, `acceptedAsTrue`). Denominator 100, abstentions 0 everywhere. **Every cell for "accepted for a wrong entry" is 0 for every condition and scheme** (`wrongEntryAccepted`), and no query was `ambiguous`.

| Condition | `tm` | `ps` | `dw` (control) |
| --- | --- | --- | --- |
| `clean` | 100 | 100 | 42 |
| **12 edits** | | | |
| `jpeg90` | 100 | 100 | 1 |
| `jpeg75` | 100 | 100 | 0 |
| `jpeg50` | 100 | 100 | 0 |
| `jpeg30` | 100 | 98 | 0 |
| `resize50` | 100 | 100 | 51 |
| `resize25` | 100 | 100 | 3 |
| `crop90` | 100 | 100 | 0 |
| `crop75` | 100 | 100 | 0 |
| `crop50` | 14 | 100 | 0 |
| `flip` | 100 | 100 | 0 |
| `png` | 100 | 100 | 42 |
| `screenshot` | 51 | 100 | 0 |
| **5 removal attempts** | | | |
| `remark` (ReMark) | 1 | 99 | 42 |
| `regen` (model-free regeneration chain) | 100 | 74 | 0 |
| `jpeg10` | 48 | 18 | 0 |
| `noisejpeg` | 100 | 100 | 0 |
| `rotate5` | 25 | 100 | 0 |
| **Forgery and overwrite** | | | |
| `transplant` (residual copy, tested for the donor's entry) | 82 | 90 | 1 |
| `reembed` (keyless re-embed, tested for the donor's entry; `tm` used the BCH-corrected bits 100/100) | 100 | 100 | 17 |
| `overwrite`, original key-A payload still accepted | 0 | 0 | 0 |
| `overwrite`, key-B payload accepted for the overwrite | 100 | 100 | 47 |
| `wrongkey` (clean decodes searched against all 100 key-B payloads, any accept) | 0 | 0 | 0 |

Unmarked: covers 0 of 100 accepted and hosts 0 of 100 accepted for each scheme, with 100 distinct raw strings for `tm` and `ps` in each set; `dw` gave 65 distinct strings over covers and 69 over hosts. 0 of 200 unmarked sources bounds the per-source rate below 1.49% (one-sided 95%) for this generator only (§13).

TrustMark's blind BCH result is report-only. On `clean`, BCH was valid and equal to the true data bits for 100 of 100. On covers it was valid for 6 of 100 (hosts 0), which is why it never decides.

## Marked-image quality (PSNR against the cover, dB, floor 38.0)

| Scheme | min | 25th pct | median | 75th pct | max | below floor |
| --- | --- | --- | --- | --- | --- | --- |
| `tm` | 41.95 | 43.99 | 44.96 | 45.84 | 48.01 | **0** of 100 |
| `ps` | 49.96 | 51.01 | 51.55 | 52.18 | 55.94 | **0** of 100 |
| `dw` (control) | 30.45 | 33.43 | 34.33 | 35.58 | 39.75 | **96** of 100 |

Marked images below the floor were still tested. For `dw`, 40 of its 42 clean successes, 15 of its 17 `reembed` successes and its single `transplant` success come from below-floor images. For `tm` and `ps` no success comes from a below-floor image.

## What the counts do and do not show

- **Synthetic images only.** Nothing here shows behaviour on photographs. No direction is predicted.
- **Removal and forgery counts are lower bounds on what an attacker can do**, never evidence of resistance. The protocol omits learned forgers such as WmForger, VAE or diffusion regeneration, averaging or collusion over several marked images, optimisation against the public decoder, and adaptive combinations of the listed edits. A count of 100 of 100 survivals or forgeries here says nothing about what those would do. On TrustMark the removal attempts that left few or some marks accepted were `remark` (1 of 100, the authors' own remover), `rotate5` (25) and `jpeg10` (48); `regen` and `noisejpeg` left 100 of 100.
- **Anyone can copy a mark without the key.** `reembed` decoded each clean mark with the public decoder and embedded the recovered bits into a different image with the public encoder, using no key. It was accepted for the donor's entry 100 of 100 for both TrustMark-Q and PixelSeal (and 17 of 100 for the weak control). A detection therefore shows only that bits matching the expected payload are present in the candidate. It does not show who embedded them, or that the candidate is, or derives from, the original or its creator's image. A payload is a keyed locator, not a signature.
- **P2–P4 do not show** a false-accept rate, natural-image behaviour or forgery resistance (see above).
- **One host, one run pair**; cross-host equality is not tested (`crossHost: not-tested`).

## Time and memory

| | Run 1 | Run 2 |
| --- | --- | --- |
| `elapsedSeconds` | 4,295.2 (71.6 min) | 5,996.4 (99.9 min) |
| Per scheme (generation 86.2 s in run 1) | `tm` 1,002.7; `ps` 2,056.0; `dw` 1,150.0 | see `run-2/summary.json` |
| Peak RSS (`peakRssMiB`) | 3,425.0 | 3,305.7 |

Both are well under the 4 h (14,400 s) abort limit, so the abort rule did not apply. The protocol's estimate was about 83 min and about 2.1 GB for one run; run 2 took longer than that estimate and both runs used more memory than the estimate. No run failed for memory.

## Code identity and network denial (from both summaries)

```
codeIdentity.ok: true            head == frozenCommit == d3af1ee07595bde53ff53fcce0f3880ad04fb62c
diffAgainstFrozen: exitCode 0, stat []
frozenIsAncestorOfHead: true     protocolVersionInFile: e-img-m-2
fingerprintImportsUnchangedSince: 6f39e50, diffExitCode 0
statusPorcelain: []              statusAfterRun: []
protocolDigest: computed == recorded == cba36673…4110
networkProbe: denied true, "bind refused errno 1; loopback connect refused errno 1 (EPERM)"
weights: 6/6, errors []          sources: 84 files, errors []
environment.deviations: []       runtime.deviations: [] ; runtimeAfterRun.deviations: []
generatorGoldens: 3 of 3         recordValidation.errors: []
resultsSha256: 6d87d2ccee6519dff43e9e8fe0c90abd360bca1f796f13d8aed4da53eb1a70bb (runs 1 and 2)
```

`compare out/full-1 out/full-2`: exit 0, "W3: identical". `git status --porcelain --untracked-files=all` in the worktree is empty after the runs and after `compare`.

## What this evidence satisfies for IMG.1–IMG.5, as worded in ROADMAP

I do not mark any gate. This lists which clauses of each gate's wording the evidence in this directory covers.

- **IMG.1** (pin record: TrustMark code commit; weight SHA-256; code, weight and dependency licences; licensed non-private image set). **Covered:** the pins were re-verified at run time: 84/84 source files at the pinned commits, 6/6 weight files by size and SHA-256, 49 pinned distributions with 0 deviations (W1). **Not covered by this run:** the licence clauses (code, weight, dependency) come from lane 12, not from a measurement. The image set was synthetic and project-generated; whether that counts as a "licensed non-private image set" is for the coordinator and owner to decide, and no real-image set was used.
- **IMG.2** (embed and detect pass with network denied after provisioning; `sandbox-exec` deny-network is acceptable together with the harness probe, which must fail first). **Covered as worded:** all measured steps after provisioning ran under `sandbox-exec` deny-network; the probe was refused (EPERM) before any model was loaded in both runs (W2); embed and detect passed: P1 100/100 for both candidates. **Limit:** synthetic images only.
- **IMG.3** (frozen and committed before running: transformation list, PSNR floor, threshold, `dwtDct` no-key negative control, residual-transplant arm). **Covered:** the run executed with code identity verified against the frozen commit and the protocol digest (W6), and the frozen set contains each named item: the transformation list including ReMark, the 38.0 dB floor, the thresholds k = 49, 167 and 30, the `dwtDct` control and the `transplant` arm. VAE regeneration was not part of the freeze and was not run, which the wording permits ("only if its weight licence is accepted").
- **IMG.4** (whole-message success per transformation; unmarked and wrong-key false detections; transplant result; each with a denominator). **Covered:** the per-condition table above gives whole-message success for each of the 12 edits and 5 removal attempts, each out of 100; unmarked false detections are 0 of 200 sources (20,000 comparisons per scheme); wrong-key false detections are 0 of 100 searches (10,000 comparisons per scheme); the transplant result is 82, 90 and 1 of 100. The keyless re-embed and overwrite counts are given in addition. **Limit:** synthetic images; the false-detection zeros are implementation checks and bound no rate beyond §13.
- **IMG.5** (IMGF and IMG results fit the lane-08 container fields, or a schema change goes through CONTRIBUTING). **Not decided by this evidence.** The records carry the fields of protocol §12 and validated with 0 errors (W4), including the six items the protocol says have no home in the lane-08 container (model digests, statistic name with n, tested bit positions, threshold basis, key and derivation id, embedding quality). Whether that is a fit or a schema change is a decision for the coordinator and CONTRIBUTING, not a measurement.
