# Results: E-IMG-F `e-img-f-2` (measured run, 200-image contract check)

Executed once as frozen and reviewed: two full runs, no reruns, nothing looked at or tuned between them. The counts below have no pass line. Protocol: [image-experiment-protocol.md](../../../../drafts/image-experiment-protocol.md), version `e-img-f-2`, digest `44a67a14c6e4c3028bd20a093896390c308a89cf92fc2d521c788346ad6b90c4` (recorded and recomputed equal in both summaries). Frozen commit `6f39e50f33026c9f1d9526c2a566d6a447219667`. Run in a detached git worktree at that commit (`<run worktree>`), HEAD equal to the frozen commit, status empty before, between and after. Files: `full-1/` and `full-2/` (`summary.json`, `queries.jsonl`, `catalogue.json`) and [transcript.txt](transcript.txt) (every command, stdout, exit code).

## Validity conditions (protocol §6)

| Condition | Result | Count / exit code |
| --- | --- | --- |
| V1 reference vectors | **pass** | fresh `check_vectors.py` in each run, `vectorChecks.pass: true`: files 30/30; PDQ port = vendored reference 30/30; C++ within 10 bits 8/8 and quality equal 8/8; Python within 16 bits 12/12 and 18/18; ISCC 3/3 |
| V2 run-to-run | **pass** | `compare out/full-1 out/full-2` exit 0: `resultsSha256 equal: True; record files byte-identical: True`; `resultsSha256` `f4808162da6d9a1eb08f1b64b7abd6744bdfcbb7e2b849389ec61b861f92c546` in both |
| V3 cross-host | **not tested** | one host (macOS arm64, CPython 3.14.6) |
| V4 port = vendor on every run image | **pass** | 1,400/1,400 extractions equal, 0 mismatches, both runs |
| V5 records fit | **pass** | 0 catalogue errors, 0 query errors; 100 catalogue entries and 1,300 query lines checked, both runs |

Also in both runs: unit tests 30/30 OK under network denial (exit 0); both full runs exit 0, `status: completed`.

## Counts with denominators (no pass line)

Catalogue 100 images. Queries 1,300 = 12 edits × 100 positives + 100 negatives. Thresholds are the fixed §5 values (PDQ 31 of 256 bits, abstain at quality ≤ 49; ISCC 7 of 64 bits), not calibrated. "Missed" counts are `no match` plus `abstained`. A "false match" is a wrong catalogue entry as top match (or any entry within the threshold, for negatives).

Enrollment: PDQ enrolled 98/100 (2 abstained, low quality); ISCC enrolled 100/100. The catalogue is the same in both runs.

### PDQ

| edit | n | correct match | no match | abstained (low quality) | ambiguous | wrong top match | any wrong entry within threshold |
|---|---|---|---|---|---|---|---|
| crop50 | 100 | 0 | 90 | 10 | 0 | 0 | 0 |
| crop75 | 100 | 0 | 96 | 4 | 0 | 0 | 0 |
| crop90 | 100 | 2 | 96 | 2 | 0 | 0 | 0 |
| flip | 100 | 98 | 0 | 2 | 0 | 0 | 0 |
| jpeg30 | 100 | 98 | 1 | 1 | 0 | 0 | 0 |
| jpeg50 | 100 | 98 | 0 | 2 | 0 | 0 | 0 |
| jpeg75 | 100 | 98 | 0 | 2 | 0 | 0 | 0 |
| jpeg90 | 100 | 98 | 0 | 2 | 0 | 0 | 0 |
| png | 100 | 98 | 0 | 2 | 0 | 0 | 0 |
| resize25 | 100 | 98 | 0 | 2 | 0 | 0 | 0 |
| resize50 | 100 | 98 | 0 | 2 | 0 | 0 | 0 |
| screenshot | 100 | 0 | 100 | 0 | 0 | 0 | 0 |
| all 12 edits | 1200 | | | | | 0 | 0 |

Negatives: 0/100 negative queries had any catalogue entry within the threshold; outcomes {'abstain-low-quality': 1, 'no-match': 99}.

### ISCC Image-Code v0

| edit | n | correct match | no match | abstained (low quality) | ambiguous | wrong top match | any wrong entry within threshold |
|---|---|---|---|---|---|---|---|
| crop50 | 100 | 0 | 100 | 0 | 0 | 0 | 0 |
| crop75 | 100 | 5 | 95 | 0 | 0 | 0 | 0 |
| crop90 | 100 | 69 | 31 | 0 | 0 | 0 | 0 |
| flip | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| jpeg30 | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| jpeg50 | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| jpeg75 | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| jpeg90 | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| png | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| resize25 | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| resize50 | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| screenshot | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| all 12 edits | 1200 | | | | | 0 | 0 |

Negatives: 0/100 negative queries had any catalogue entry within the threshold; outcomes {'no-match': 100}.

Distance histograms are in each `summary.json` and allow other thresholds to be read without a rerun.

## Elapsed time and disk

| | Run 1 | Run 2 |
| --- | --- | --- |
| `elapsedSeconds` | 856.4 | 841.4 |
| Peak RSS (bytes) | 755826688 | 818282496 |

Both are under the 3,600 s abort limit (protocol §9), so neither run was aborted. Disk: images are generated in memory and never written, so there is no transient disk use. The measured sizes after both runs were: outputs 2,028 KB per run (4,056 KB for `out/`), `.venv` 89,124 KB, `wheelhouse` 15,128 KB, vector images 6,984 KB. I did not obtain a reliable sampled peak during the runs (the sampling attempt could not see the other process from inside the agent sandbox), so "peak disk" is the final total, about 115 MB in the worktree, all git-ignored.

## Code-identity and network-denial excerpts (identical in both summaries)

```json
"codeIdentity": {"diffAgainstFrozen": {"exitCode": 0, "stat": []}, "frozenCommit": "6f39e50f33026c9f1d9526c2a566d6a447219667", "frozenIsAncestorOfHead": true, "head": "6f39e50f33026c9f1d9526c2a566d6a447219667", "ok": true, "protocolVersionInFile": "e-img-f-2", "statusPorcelain": []}
"statusAfterVectorCheck": [], "statusAfterRun": []
"networkDenied": {"denied": true, "probe": "bind refused errno 1; loopback connect refused errno 1 (EPERM)"}
"protocolDigest": {"computed": "44a67a14c6e4c3028bd20a093896390c308a89cf92fc2d521c788346ad6b90c4", "recorded": "44a67a14c6e4c3028bd20a093896390c308a89cf92fc2d521c788346ad6b90c4"}
"environmentDeviations": []
"validity": V1 true, V3 not-tested, V4 true, V5 true, start-code-identity true, start-network-denied true, work-tree-clean-after-vector-check-and-run true
```

## What this does and does not show (required by the protocol)

The PDQ checks on synthetic images are weak by construction: `png` re-encodes identical pixels, `jpeg90`, `jpeg75` and `flip` are expected to match, and the random-shape negatives are expected to sit far from every entry. V4 shows the port repeats the vendor's arithmetic, not that the arithmetic is independently right; that check is IMGF.5's C++ comparison. This run shows nothing about match quality on natural images or any false-match rate. False-match rates at scale, and crop and screenshot figures, come from the external benchmark X1 (arXiv:2610.04151v1, an author-run, unreplicated preprint cited in the lane 10 report audit) and are not our measurement. The synthetic crop and screenshot rows above are not evidence about real crops or screenshots.

## Roadmap criteria, as worded (gates not marked here)

- **IMGF.3.** Satisfied as worded on the points this run can show: the digest is recorded in the protocol file and the README and recomputes equal; the harness logged clean tree, HEAD equal to the frozen commit and a fresh vector check (`codeIdentity.ok: true`, empty status lists); the result commit descends from the frozen commit (checked with `git merge-base --is-ancestor` at commit time); package install was done in a project-local `.venv` under the owner's approval for this task. The non-author review precedes the result commit (review commit `835f6c0`); I did not verify who authored it.
- **IMGF.4.** (a) reference-vector checks pass with the IMGF.2 exact and tolerance counts, k/k: met. (b) two full runs byte-identical: met. (c) every result validates, 0 invalid: met. Both runs were under `sandbox-exec` deny-network with the probe refused first. False-match and missed-match counts are reported above with denominators and no pass line; cross-host is recorded as not tested. The criterion "a non-author rechecks the counts" is not done by this record: the run lane executed the harness and copied its counts but did not independently recompute them.

## Deviations from the reviewed sequence

- `compare` ran under the deny-network `sandbox-exec` profile (as in the review's sequence).
- Provisioning ran `fetch_wheels.py` and `fetch_pdq_vectors.py` with `python3`, creating `.venv` with `/opt/homebrew/bin/python3.14`, as in the README; `pip` also put a locally built `data-url` wheel in `~/Library/Caches/pip`, outside the worktree.
- Unit tests were run with `-s tests -t .` as in the review.
- The first command in the run directory (`fetch_wheels.py`) was first tried in the agent sandbox and failed with `PermissionError` on creating `wheelhouse/`; that failed attempt is in the transcript and wrote nothing.
