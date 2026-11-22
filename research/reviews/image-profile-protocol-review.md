# Non-author review: image fingerprint profile, E-IMG-F protocol `e-img-f-1` and harness

Reviewed 2026-11-22 at commit `4714735` on `roadmap-v2`: [extraction-profile-image.md](../drafts/extraction-profile-image.md), [image-experiment-protocol.md](../drafts/image-experiment-protocol.md) and `research/experiments/image-fingerprint/`. Read against ROADMAP.md IMGF.1–IMGF.5, [lane 10](../lanes/10-evidence-review.md) (including "After the report audit") and the [report audit](../lanes/10-report-audit.md). I did not write any of these files. I did not run `full` mode, and I generated no seed in 0–1,999.

## What I ran

All of it ran offline, with the existing project-local `.venv` (CPython 3.14.6). I installed nothing. The shared checkout's working tree has **uncommitted edits** to `run_experiment.py`, `tests/test_harness.py` and `twimg/profile.py` (see B1). So I ran everything on an exact export of the commit: `git archive 4714735 … | tar -x -C $TMPDIR/imgf-c`, with `vectors/pdq-data` symlinked to the existing pinned downloads.

| Check | Result |
| --- | --- |
| Protocol digest: SHA-256 with the one 64-hex occurrence replaced by zeros | `b7e4856b…da9d07`, equal to the recorded value. The plain file SHA-256 is `8ce9e15a…db97`, as expected for a self-excluding digest |
| `.venv/bin/python -I check_vectors.py` (the export writes its own copy of `check-results.json`) | files 30/30; port vs vendored 30/30; C++ reg-test exact 0/8, max 8, quality 8/8; README profile path 4/12, max 12; README thumbnail path 9/12, max 2; unittest profile path 8/18, max 12; unittest thumbnail path 17/18, max 10; ISCC 3/3 compiled and 3/3 pure |
| Regenerated `check-results.json` vs the committed file | equal in every top-level key (environment, deviations `[]`, inputs, port, published sets, ISCC) |
| `.venv/bin/python -m unittest discover -s tests -t .` | 24 tests, OK |
| Vendored PDQ: SHA-256 and git blob SHA-1 of the 11 files in `PROVENANCE.md` | 11/11 match |
| Comparison counts in §5 | 1,000×500×8 = 4,000,000; 6,000×499×8 = 23,952,000; selection 250×250×8 + 3,000×249×8 = 6,476,000. All correct |
| C++ vs Python published hashes of the same file (`bridge-1-original.jpg` = `bridge-mods/aaa-orig.jpg`, same SHA-256 `b5b07996…`) | 8 bits apart, both quality 100. The author's claim is confirmed |

## Findings, most severe first

**B1 (blocking, operational). The harness does not check that it is the frozen code, and the working tree is not the frozen code right now.**
- §2 freezes "every file under `image-fingerprint/` at the protocol commit". `run_experiment.py full` checks only the protocol file's digest, the environment and a stored vector-results file. It checks neither code identity nor `PROTOCOL_VERSION` against the protocol file.
- The uncommitted working-tree harness says `PROTOCOL_VERSION = "e-img-f-2"` and `full` = "200 images (100 enrolled, 100 never enrolled) … counts have no pass line". The protocol file still carries the `e-img-f-1` digest.
- Run today from this checkout, it would start a different design under the `e-img-f-1` digest.

Fix, with no protocol change: run from a clean export or worktree of `4714735`, or of a descendant whose `research/experiments/image-fingerprint/` and protocol file are byte-identical. Log for the non-author recheck: `git rev-parse HEAD`; `git diff --exit-code 4714735 -- research/experiments/image-fingerprint research/drafts/image-experiment-protocol.md research/drafts/extraction-profile-image.md`; and an empty `git status --porcelain` for that tree.

A built-in check would change harness code, which §2 freezes, so it belongs in the next version.

**B2 (blocking, decision). Choose which design governs IMGF.4 before running.**
- §1 and §13 state this honestly: `e-img-f-1` keeps the roadmap's 2,000-image design with F1–F3, and adds the audit's conditions as validity conditions.
- The uncommitted edits show the 200-image audit design (`e-img-f-2`) being built in parallel.
- The owner or coordinator should pick one in writing first. Running `e-img-f-1` and then switching would be choosing a design after seeing results.
- If `e-img-f-2` is chosen, it needs its own frozen protocol and its own review; this review covers `e-img-f-1` only.

**B3 (blocking, roadmap wording, not protocol). The IMGF.4 offline wording and IMGF.2 for PDQ.** IMGF.4 names `scripts/offline`, which this repository does not have (§8 step 2). Edit IMGF.4 to accept `sandbox-exec` deny-network with the harness probe, or IMGF.4 cannot be met by this run. IMGF.2: see the proposed text below.

**M1. C1 reads a stored file rather than a fresh on-host check.** `full` reads the committed `vectors/check-results.json` and gates on its counts. §8 step 3 runs `check_vectors.py` first, but nothing ties the run to that step. `check_vectors.py` also rewrites a tracked file. Fix, operational: in the clean tree, run `check_vectors.py` and then require `git status --porcelain` to stay empty. This proves the on-host results are byte-identical to the committed ones, as they were in my export. Log it with B1's checks.

**M2. The PDQ pass is close to certain by construction, so it carries little evidence.**
- F3 `png` re-encodes identical pixels. It fails only if enrollment abstains, so it is a determinism control, as §4 itself says.
- `jpeg75` at ≤ 31 bits, and F1 on 1,000 independently drawn random-shape images, are very likely to pass.
- The protocol states what a pass does not mean (§1, §7). The summary should also state that PDQ passing F1–F3 was expected, and that the informative outputs are the limit rows (crops, screenshot, `jpeg30`, `resize25`), the distance histograms and the ISCC selection-rule outcome.

This is a reporting rule and needs no new version.

**M3. Errata in the frozen text.** None changes a metric or verdict. They need no new version; record them in the results commit.
- **Extraction count (§9):** "11,750 (750 originals + 11,000 queries)" should be 11,000 extractions (750 enrolled originals plus 10,250 queries, the 1,250 negatives included). The smoke figures confirm this: 8 + 108 = 116. The "101×" scale factor is therefore about 95×, so the budget overestimates slightly, which is harmless.
- **Within-threshold list (§10):** §10 says "entries within threshold", and profile §6 says "all". `decide()` truncates `withinThreshold` to 20, though `withinThresholdCount` and `wrongWithinThreshold` use the full list, so F1/F2 are unaffected.

**L1. The network probe makes a real connection when the network is allowed.** When the network is not denied, as in smoke runs outside the sandbox, the probe completes a TCP handshake with `1.1.1.1:443`. No data is sent, but it is still a connection to a third party. Next version: probe a TEST-NET address (`192.0.2.1`), or rely on the bind refusal.

**L2. The generator prose is not enough to reimplement it.** §3 omits the draw order, the distributions (uniform colours and angles, line width `w//200…w//40`) and the polygon vertex rule. Reproduction rests on the frozen code and the 3 golden digests, which is acceptable for a research generator. State that the code, not the prose, is normative.

**Determinism and leakage: no problem found.**
- The selection split is fully scored and `selection-threshold.json` is written before any evaluation query is scored (`run()`, the selection branch). The rule has no free parameter.
- Smoke seeds (≥ 1,000,000) are disjoint from experiment seeds. The author's disclosed look at the smoke data (one `crop50` line, the quality range) does not touch a frozen parameter.
- The PDQ port uses element-wise NumPy and an explicit summation order, with no BLAS matrix product. ISCC bits are passed explicitly, so `ISCC_CORE_*` environment variables and `iscc-core.env` cannot change them. Iteration is over sorted ids.
- There is no network or file access beyond the code, the vectors and the output directory. C3 (two runs, `compare`) and C2 (vendor cross-check on 2,600 inputs) catch what reading the code cannot.

**Protocol completeness (point 1).**
- Every pass/fail is decided before any result and by a count or an exit code: F1 (≥ 1 of 1,000), F2 (> 5 of 6,000), F3 (< 475/500), C1–C6 (counts, the `compare` exit code, the probe result, the validator), and abort (> 4 h gives exit 3 and no metrics).
- The 12 edits, encoder settings and output sizes are fully specified. So are the counts, splits and selection rule. The abort rule is complete.
- The audit's scope changes are stated honestly: the contract and record checks became C1–C6; false-match counts without a pass line are left to the owner (§13); cross-host is "not part of this version" (§6, §13).

## IMGF.2 for PDQ: reproduced, with proposed gate text

Exact equality with published outputs is not achievable and should not be the gate:
- **Decoders differ.** The C++ tool uses its own decoder; Pillow 13's libjpeg-turbo differs.
- **The vendor's own sets disagree.** On identical file bytes, the C++ and Python hashes differ by 8 bits.
- **Even the vendor's own Python path misses its README.** Run with Pillow 13, it reaches only 9/12 of its own README values.

What is exact is the arithmetic on identical decoded pixels (30/30). The tolerance figures are the vendor's published criteria, not values chosen after seeing distances: README ≤ 10 bits against C++ at quality ≥ 80 (all 8 C++ vectors have quality 100), and unit test ≤ 16 bits. Measured: 8/8 within 10 (max 8); 30/30 Python outputs within 16 (max 12); quality equal on 20/20 where published.

Proposed replacement for ROADMAP IMGF.2:

> IMGF.2 | E | **PDQ, exact:** on identical decoded RGB arrays, the profile's PDQ implementation equals the vendored ThreatExchange Python reference (commit `9f627fb1…`) in all 8 dihedral hashes and the quality score, k/k, on the 30 pinned `pdq/data` files, and on every input a measured run cross-checks (protocol C2). **PDQ, vendor tolerance:** on the profile decode path, every hash is within 10 bits of the ThreatExchange C++ `reg_test` output for each vector with published quality ≥ 80 (the vendor README criterion), and within 16 bits of each comparable published Python output (the vendor unit-test criterion), k/k; published quality scores are equal, k/k. Exact equality with published hashes is not required, because the vendor's own reference sets differ by up to 8 bits on identical files. **ISCC:** the hash core equals iscc-core 1.5.0 `data.json` `gen_image_code_v0`, k/k; the normalization steps are not covered by any published vector and are not claimed by this gate | I

**Is a C++ reference build needed?** Not for this run or this gate.
- The vendored Python is the vendor's own reference, and the run compares hashes within one pipeline.
- The port is not independent of the vendored Python: it repeats the vendor's operation order. A C++ build fed identical luma arrays is the natural independent arithmetic check for IMGF.5.
- A C++ build is required before any claim of exact interoperability with hash lists made by other PDQ deployments, such as a C2PA soft-binding export (OD-I7). Add that condition to IMGF.5, or to a later interop gate.

## Profile: implementer discretion (point 4)

Most of these do not affect this run, because every experiment input is an 8-bit RGB PNG or a baseline JPEG written by the pinned Pillow. They do affect IMGF.1's "0 TBD" claim and IMGF.5.
- **Colour conversion (§3 step 10).** `CMYK`, `YCbCr`, `P`, `L` and `1` reach RGB "through Pillow 13.0.0's own `convert`". That defines the result only by reference to Pillow, so a non-Pillow implementation cannot reproduce it, and inverted (Adobe) CMYK JPEGs are not addressed. PNG `gAMA`, `cHRM` and `sRGB` chunks are not mentioned; say they are ignored.
- **JPEG decode (§3 step 7).** "The settings Pillow passes by default" should be named: the DCT method, fancy upsampling and whether merged upsampling is used. Results differ across these.
- **High bit depth.** State the rule for 16-bit-per-channel colour PNG, which Pillow may present as mode `RGB`/`RGBA` rather than rejecting it as with `I;16`. Verify Pillow 13's behaviour before writing the rule.
- **ISCC grey and resize (§5 steps 2–3).** "Pillow's rounding" and Pillow's `BICUBIC` (support widening when downscaling) are defined by Pillow's code, not by a formula. The trim rule's "single-side cut" condition is paraphrased from iscc-sdk. The profile's claim that its codes are "the ones the reference SDK would produce" is untested, because iscc-sdk is not installed and no vector covers normalization. Add a check against iscc-sdk 0.9.7 outputs before that claim is used.
- **EXIF orientation (§3 step 8).** For PNG it depends on where Pillow finds EXIF (the `eXIf` chunk or a raw-profile text chunk). Name the accepted sources.

**The 11 open decisions.** None has to be *settled* before the run, if the run is read as testing `draft-1` exactly as encoded in the configuration digest.
- OD-I2, I3, I4, I5, I8, I9 and I10 already have the draft value written into the configuration bytes. OD-I2, I3 and I10 cannot affect synthetic RGB PNG/JPEG inputs. OD-I4, I5, I8 and I9 do affect outcomes; changing any later is a new profile version, and this run's result then covers `draft-1` only.
- **Needed before the result is used:** OD-I1 (IMGF.2 wording, above) and the B2 design choice. OD-I11 must be recorded as an accepted limit (single platform, cross-host untested), because the audit design treats cross-host difference as a failure.
- OD-I6 and OD-I7 can wait: C6 uses the harness's own field set, and C2PA is later.

## Licences (point 5)

- **Vendored PDQ.** ThreatExchange BSD licence, kept as `vendor/threatexchange_pdq/LICENSE` with provenance and blob ids. This fits [LICENSE.md](../../LICENSE.md), under which third-party material keeps its own notice. It is not relicensed as Apache-2.0, and nothing should say it is.
- **ISCC normalization.** Re-implemented from iscc-sdk 0.9.7 (Apache-2.0), with its licence text kept in `vendor/iscc-sdk-LICENSE.txt`. If iscc-sdk ships a `NOTICE` file, Apache-2.0 §4(d) requires carrying it. Check whether it does, and say "re-implemented following" rather than "copied" for `twimg/iscc_img.py`.
- **Pinned packages.** All 19 plus setuptools are permissive: MIT-CMU, MIT, BSD-2/3, PSF-2.0, Apache-2.0, CC0/Apache, 0BSD, Zlib. None is copyleft. Wheels and the virtual environment are git-ignored, so nothing is redistributed. `uvarint`'s licence field says "UNKNOWN" and rests on a classifier; acceptable for local research use.

## Verdict

**The run may start as frozen (`e-img-f-1`, commit `4714735`) after the listed fixes. None of them changes the frozen protocol, so no new protocol version is needed**, provided the run uses the committed tree byte for byte.

Fixes required before starting:
1. B1: run from a clean tree identical to `4714735` and log the identity checks.
2. B2: a written owner or coordinator choice of `e-img-f-1` over the 200-image `e-img-f-2`.
3. B3: amend IMGF.4 to accept `sandbox-exec` with the probe, and replace IMGF.2 with the text above. These are roadmap edits only.
4. M1: rerun `check_vectors.py` in the clean tree, with `git status --porcelain` staying empty.

Not blocking: the M2 reporting rule and M3 errata go in the results commit; L1, L2 and a built-in code-identity check go in the next version; the profile discretion items go in IMGF.1 and IMGF.5 before those gates are claimed.

## Confirmation pass: e-img-f-2

Checked 2026-11-22 on a `git archive` export of the frozen commit `6f39e50f33026c9f1d9526c2a566d6a447219667`, offline, using the existing `.venv` with nothing installed. I did not run `full` and generated no seed in 0–199.

**Reruns.** The self-excluding digest recomputes to `44a67a14…6b90c4`, equal to the recorded value. `check_vectors.py` gives: files 30/30; port 30/30; C++ within 10 bits 8/8 (exact 0/8), quality 8/8; Python within 16 bits 12/12 and 18/18; ISCC 3/3 compiled and 3/3 pure. The regenerated `check-results.json` is byte-identical to the committed one. Unit tests (`-s tests -t .`): 30 OK.

**Earlier findings: all resolved.**
- B1: `code_identity()` requires HEAD = `--frozen-commit`, an empty `status --porcelain --untracked-files=all`, a zero `git diff --exit-code` on the frozen paths, ancestry, and the version line `e-img-f-2`. All are logged; failure exits 2.
- B2 is recorded in §0 and IMGF.3. B3: IMGF.2 carries the proposed text, and IMGF.4 accepts `sandbox-exec` with the probe. M1: a fresh `check_vectors.run_checks()`, refused if `statusAfterVectorCheck` is non-empty. M2: §1 and the §6 reporting rule. M3: the erratum is in §13; now 1,400 extractions = 100 + 1,200 + 100.
- Truncation is gone, and V5 checks list length = count. L1: the probe now uses `127.0.0.1:1`, so no packet leaves. L2: §3 gives every draw, in order. Profile draft-2: `JDCT_ISLOW` and fancy upsampling named; IHDR bit-depth rule; EXIF for JPEG only; CMYK/YCbCr out of scope; gamma chunks ignored; iscc-sdk equality claim withdrawn; no NOTICE.

**Diff against `e-img-f-1`.**
- **Nothing passes trivially or was chosen from results.** No count has a pass line. `T_iscc = ⌊64·31/256⌋ = 7` comes from a fixed rule.
- **V1 is predictable.** Its counts come from the public vendor vectors and its tolerances are the vendor's. The real uncertainty is V2 and V5 on 1,400 extractions, as §1 says.
- **No experiment seed has been generated, as far as the repository and logs show.** The tests generate only seeds ≥ 1,000,000 (goldens 1,000,000–1,000,002). The `seed: i` at `tests/test_harness.py:332` is a fixture dictionary, not a generator call. All three `out/smoke-*` summaries are mode `smoke`, and no `results/` path exists in any commit.

**Conditions against IMGF.3/IMGF.4.** Each is decided by an exit code or a count, and each matches the gates as worded: V1, `vector_verdict()` with 7 k/k counts (IMGF.4(a)); V2, the `compare` exit code (IMGF.4(b)); V4, 0 mismatches with 1,400 compared (the in-run half of IMGF.2 "exact"); V5, 0 catalogue and 0 query errors (IMGF.4(c)). Editorial: IMGF.2's "(protocol C2)" should read "(protocol V4)".

**New discrepancy, non-blocking.** §9 sets the abort limit at 1 h, but `run_experiment.py:56` has `ABORT_SECONDS = 4 * 3600`. The protocol text governs, so the recheck treats `elapsedSeconds` > 3,600 as an aborted run. Align the code in the next version.

**Command sequence.** Run outside any agent sandbox, which blocks nested `sandbox-exec` and `.git/worktrees` writes. Both full runs are under network denial, so a third run is unnecessary (smoke c already recorded ECONNREFUSED with the network allowed).
```sh
FROZEN=6f39e50f33026c9f1d9526c2a566d6a447219667; SB='(version 1)(allow default)(deny network*)'
git worktree add --detach ../imgf-run "$FROZEN" && cd ../imgf-run/research/experiments/image-fingerprint
# provision git-ignored wheelhouse/ and vectors/pdq-data/ (fetch_*.py or copy; hash-checked); README install, --no-index --require-hashes
git rev-parse HEAD; git status --porcelain --untracked-files=all    # FROZEN, then nothing
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python -m unittest discover -s tests -t .
for r in 1 2; do /usr/bin/sandbox-exec -p "$SB" .venv/bin/python run_experiment.py full --frozen-commit "$FROZEN" --require-network-denied --out out/full-$r; echo "exit $?"; done
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python run_experiment.py compare out/full-1 out/full-2; echo "exit $?"
git status --porcelain --untracked-files=all                         # nothing
```
**Log in the results commit:** every command, with its stdout and exit code (all 0). From each `summary.json`: `codeIdentity.ok: true` with `frozenCommit` = HEAD = `6f39e50f…`; empty `statusAfterVectorCheck` and `statusAfterRun`; `networkDenied.denied: true` with the EPERM probe text; `vectorChecks` 7/7; the validity map; equal `resultsSha256`; `elapsedSeconds` ≤ 3,600. The results commit must pass `git merge-base --is-ancestor $FROZEN HEAD`.

**Verdict: the run may start.** No blocking items remain. The abort-limit reading and the C2→V4 wording are handled as stated above.
