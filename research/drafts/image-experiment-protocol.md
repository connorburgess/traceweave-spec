# E-IMG-F protocol: PDQ and ISCC Image-Code on seeded synthetic images

Protocol version: `e-img-f-1`. Status: **frozen for review, 2026-11-22; not yet run.** Roadmap gate IMGF.3, preparing IMGF.4 and IMGF.5 ([roadmap](../../ROADMAP.md), later-profile table). Profile under test: [extraction-profile-image.md](extraction-profile-image.md). Harness: [research/experiments/image-fingerprint/](../experiments/image-fingerprint/README.md). Evidence: [lane 10](../lanes/10-evidence-review.md) and its [report audit](../lanes/10-report-audit.md).

Protocol digest (SHA-256, self-excluding): `b7e4856bdd1a2d4eaaea478f18bd0f8d197fd2349733e5f14a65e31130da9d07`

The digest is the SHA-256 of this file's bytes with the 64 hex digits above replaced by 64 zeros. `run_experiment.py full` recomputes it and refuses to start if it differs. The README repeats it.

**Freeze rule.** The commit that adds this file and the harness is the protocol commit. The first commit containing any measured result MUST have the protocol commit as an ancestor (IMGF.3), and its summary MUST carry the same digest. Any edit to this file changes the digest. Before the first result, a changed protocol becomes version `e-img-f-2`. After a result exists, a change is a new protocol version, and the earlier result stays reported. §12 lists what counts as a change.

This is a research protocol. It changes nothing in `spec/`, `schemas/`, `profiles/` or `test-vectors/`. Nothing here is normative.

## 1. Question and scope

Does the draft profile's PDQ extractor, at the vendor's starting threshold, behave as lane 10 requires on whole-image light edits of procedurally generated images? Specifically:
- every unrelated image stays unmatched;
- edited copies are matched to the right catalogue entry and to no wrong one;
- JPEG quality 75 and a lossless PNG round trip are recalled.

The same is asked of ISCC Image-Code v0, at a threshold chosen on a separate selection split. In both cases the run also tests the profile's contract and record: whether every output is reproducible, conforms to the reference code, and fits the catalogue record.

**What a pass would not mean.** It gives no false-match rate for natural images, no crop or screenshot coverage, and no adversarial robustness (§7). The images are synthetic and clustered by generator design. The report audit's source X1, an author-run preprint, already measured PDQ on natural images at 1.00% per-query false bindings on a product catalogue. This run cannot confirm or refute that.

**Relation to lane 10's post-audit note.** That note proposes a smaller run: 200 images, no pass line on false matches, and failure only on vector mismatch, non-determinism, a cross-host difference or a record misfit. The roadmap gates IMGF.3 and IMGF.4 still state the 2,000-image design and its failure criteria, and this lane was asked to follow them unless a change is justified. This protocol therefore keeps the roadmap design (§3, §6 F1–F3) and adds the post-audit failure conditions as validity conditions (§6 C1–C6). Its 2,000 images contain the 200-image run. Which design governs IMGF.4 is for the owner or coordinator (§13).

## 2. What is frozen

| Item | Frozen value |
| --- | --- |
| Profile | extraction configuration SHA-256 `56c0d63ae0c3047d447d883c704cb47a1d1760dfc9719fb879413ca6b1f71315`; matching configuration SHA-256 `3925a95bc9f08bad07f788da784a1e50005f42e32a26fa43848b33108e9258dd` |
| Code | every file under `research/experiments/image-fingerprint/` at the protocol commit, the vendored PDQ included |
| Environment | CPython 3.14.x on macOS arm64; the 19 packages in `requirements.txt` plus setuptools 84.2.1 from `requirements-build.txt`, all installed with `--require-hashes`; Pillow 13.0.0 with libjpeg-turbo 3.2.0 and zlib-ng 1.3.1. `check_environment()` MUST report no deviation |
| Decoder | Pillow 13.0.0 at the versions above; JPEG at full size, with no draft mode |
| Generator | `traceweave-synth-draft-1` (§3), with golden pixel digests for three smoke seeds checked by the unit tests |
| Seeds and splits | §3 |
| Edits | the 12 in §4 |
| Thresholds | PDQ: match when distance ≤ 31, abstain when quality ≤ 49. ISCC: `selection-rule-1` (§5) |
| Metrics, criteria and validity conditions | §6 |
| Abort rule | §9 |

## 3. Images

**Generator** (`twimg/generator.py`). Image `seed` depends only on the seed, NumPy 2.5.5 and Pillow 13.0.0. Nothing is read from disk, the network or the clock.

1. **Random stream.** `PCG64(SeedSequence([0x7477696D, seed]))`.
2. **Size.** `(512, 512)`, `(1024, 768)` or `(1920, 1080)` (width, height), chosen by `seed mod 3`.
3. **Background.** A linear gradient between two random RGB colours along a random angle, rounded to `uint8` with `numpy.rint`.
4. **Shapes.** 6–14 filled shapes drawn with Pillow `ImageDraw`: rectangle, ellipse, polygon with 3–6 vertices, or a thick line. Each has a random colour, centre and radii of 5–35% of the image side.
5. **Texture.** Per channel, a random grid of 8–32 cells per side in [−1, 1], resized to full size with Pillow `BILINEAR` on mode `F` and scaled by an amplitude of 8–24 grey levels.
6. **Noise.** Gaussian, with σ between 1 and 6 grey levels.
7. **Output.** Clipped and rounded to `uint8` RGB. Identity: `pixelSha256` = SHA-256 of `"{W}x{H}x3:"` followed by the row-major array bytes.
8. **Encoding.** Catalogue originals and negatives are encoded as PNG (Pillow, `compress_level` 6, no metadata), and those bytes are what the profile decodes.

**Seed plan.** Splits are contiguous seed ranges, decided before any image was generated:

| Split | Role | Seeds | Images |
| --- | --- | --- | --- |
| Selection | catalogue, enrolled | 0–249 | 250 |
| Selection | negatives, never enrolled | 250–499 | 250 |
| Evaluation | catalogue, enrolled | 500–999 | 500 |
| Evaluation | negatives, never enrolled | 1000–1999 | 1,000 |
| Smoke (never part of a result) | dry tests only | 1,000,000 and up | 20 used |

This keeps lane 10's 2,000 images split 500/500/1,000 by seed. Lane 10 does not say how the 500 selection images are used. Here they are halved into a 250-entry catalogue and 250 negatives, so the ISCC threshold can be chosen on both edited copies and never-enrolled images (§5).

**Query counts.** Every catalogue image gets the 12 edits of §4:

| Split | Positive queries | Negative queries | Catalogue entries |
| --- | --- | --- | --- |
| Selection | 3,000 (250 × 12) | 250 | 250 |
| Evaluation | 6,000 (500 × 12) | 1,000 | 500 |

The originals themselves are enrolled, never queried.

## 4. The 12 edits

Each edit takes the decoded original (RGB `uint8`) and produces file bytes (`twimg/transforms.py`). The query is then decoded by the profile like any input. Encoders are Pillow 13.0.0 with its bundled codecs. No EXIF, ICC or text metadata is written.

| Name | Exact definition | Output |
| --- | --- | --- |
| `jpeg90`, `jpeg75`, `jpeg50`, `jpeg30` | `save(format="JPEG", quality=q, subsampling=2 (4:2:0), optimize=False, progressive=False)` | JPEG |
| `resize50` | `resize((W//2, H//2), LANCZOS)`, then `resize((W, H), BICUBIC)` | PNG, level 6 |
| `resize25` | the same with `W//4, H//4` | PNG, level 6 |
| `crop90`, `crop75`, `crop50` | centre crop to area fraction a: side factor s = √a; `cw = ⌊W·s + 0.5⌋`, `ch = ⌊H·s + 0.5⌋`, `left = ⌊(W − cw)/2⌋`, `top = ⌊(H − ch)/2⌋`. The kept side fractions are about 94.9%, 86.6% and 70.7% | PNG, level 6 |
| `flip` | horizontal mirror, `transpose(FLIP_LEFT_RIGHT)` | PNG, level 6 |
| `png` | lossless PNG round trip: re-encoded at `compress_level` 1 instead of 6. Pixels are identical by construction, so this is a pipeline-determinism control | PNG, level 1 |
| `screenshot` | **screenshot simulation**: paste onto a canvas `(W+80)×(H+80)` filled with RGB (240, 240, 240) at offset (40, 40); then `resize` to `(⌊0.8·(W+80) + 0.5⌋, ⌊0.8·(H+80) + 0.5⌋)` with `BICUBIC`, computed in integers as `(2·4·x + 5) // 10` | PNG, level 6 |

The screenshot simulation is a uniform UI-grey frame plus a downscale. It has none of the following: window chrome, display colour management, sub-pixel text rendering, device-pixel-ratio scaling or a lossy screenshot codec. A result on it says nothing about real screenshots.

Sizes after each edit for the three resolutions are fixed by these rules, and unit tests check them for 512×512, 1024×768 and 1920×1080 (screenshot: 474×474, 883×678 and 1600×928).

## 5. Thresholds and the selection rule

- **PDQ.** Fixed in advance at the vendor's starting values. A query matches an entry when the min-over-dihedral Hamming distance is ≤ 31 of 256 bits. An image with quality ≤ 49 abstains `low-quality`, whether it is a catalogue original or a query. These are not tuned on any split.
- **ISCC, `selection-rule-1`.** On the selection split only:
  - **Null comparisons:** for each non-abstaining selection negative, its min-over-dihedral distance to every enrolled selection entry; for each non-abstaining selection positive, its distance to every enrolled entry other than its source.
  - **d_min** is the smallest of all of those.
  - **T_iscc = d_min − 1**, used with ≤. If d_min is 0, T_iscc is −1 and ISCC matches nothing in that run.
- **Order.** The harness processes the whole selection split first, writes `selection-threshold.json`, and only then scores evaluation queries. Evaluation data cannot reach the rule.
- **Why this rule, and its known weakness.** It has no tuning knob: it is the loosest threshold that produced zero false matches on the selection split. The evaluation search is larger: 4,000,000 negative comparisons and 23,952,000 wrong-entry comparisons, against 6,476,000 null comparisons on the selection split. Its minimum null distance is therefore expected to fall lower, so an ISCC failure of F1 or F2 below is a plausible outcome of this rule. That would be a finding about the rule, recorded as such, and not grounds to re-run with a different rule under this version.
- **No other parameter** is chosen from data.

## 6. Metrics, failure criteria and validity conditions

**Unit of a query.** For each query and each extractor separately, the outcome is one of the profile §6 classes: `match` (with entry and distance), `no-match`, `abstain-ambiguous`, or an input or quality abstention. The query result also lists every entry within threshold.

**Metrics.** Every figure is a count with its denominator, per split and per extractor. They come from `compute_metrics()` in `run_experiment.py`.

| Metric | Denominator |
| --- | --- |
| Per edit: **correct match** (outcome `match` naming the source entry) | 500 positives of that edit (evaluation); 250 (selection) |
| Per edit: wrong-top match, ambiguous, no-match, each abstention code | same |
| Per edit: **queries with any wrong entry within threshold** | same |
| All edits: queries with any wrong entry within threshold; wrong-top matches | 6,000 (evaluation); 3,000 (selection) |
| **Negatives with any entry within threshold** | 1,000 (evaluation); 250 (selection) |
| Negative outcomes by class | same |
| Enrollment: entries enrolled, and abstentions by code | 500 (evaluation); 250 (selection) |
| Histograms: true-source distance per edit; nearest-wrong distance over all positives; nearest-entry distance over negatives | the counts in each histogram sum to the stated denominators, minus abstentions |
| Runtime (s) and peak resident memory (bytes) | one run |

Recall is reported over **all 500** positives of an edit. A query that abstains, or whose source failed enrollment, counts as not recalled. Recall among non-abstaining queries can be derived from the counts and is not the criterion.

**Failure criteria** (roadmap IMGF.4 and lane 10). They are evaluated on the evaluation split, for each extractor:

| ID | The extractor fails if |
| --- | --- |
| F1 | **1 or more** of the 1,000 negatives has any enrolled entry within threshold |
| F2 | **more than 5** of the 6,000 positives have any wrong entry within threshold |
| F3 | correct matches for `jpeg75` < 475/500, or for `png` < 475/500 (recall below 95%) |

Results for `crop90`, `crop75`, `crop50`, `screenshot` and `jpeg30` are **recorded as limits, not failures**. So are the other edits (`jpeg90`, `jpeg50`, `resize50`, `resize25` and `flip`), which carry no pass line in lane 10.

**Verdict.**
- **PDQ fails any of F1–F3:** E-IMG-F is a **negative result** under IMGF.4, and the profile is not proposed with PDQ as main extractor at this threshold.
- **PDQ passes, ISCC fails:** PDQ's result stands. ISCC is recorded as failing under `selection-rule-1` and is dropped as the second extractor of this profile version.
- **Both pass:** the result supports the profile only within §7's limits.

**Validity conditions.** If any of C1–C6 fails, the run is **invalid**. An invalid run is not a result: it is reported as invalid, the cause is fixed, and the fix is a new protocol version.

| ID | Condition |
| --- | --- |
| C1 | `check_vectors.py` on the run host: PDQ core port vs vendored 30/30; ISCC `data.json` 3/3 |
| C2 | Vendor cross-check during the run: the vendored pure-Python PDQ equals the port (8 dihedral hashes and quality) on every catalogue original, every negative (2,000 images) and all 12 edits of the first 50 evaluation entries by id (600 queries) |
| C3 | Two complete runs give byte-identical `catalogue-*.json`, `queries.jsonl` and `selection-threshold.json`, with equal `resultsSha256` (`run_experiment.py compare`) |
| C4 | `check_environment()` reports no deviation; the protocol digest matches |
| C5 | Network denied (§8): the harness's probe reports both a local bind and an outbound connect refused |
| C6 | Every catalogue is canonical JSON in the profile §8 field set and binds the frozen configuration digests |

The post-audit note's cross-host condition (x86 against arm64) is **not** part of this version. Only macOS arm64 is pinned, and no x86 host is available to this lane. It is listed for the owner in §13.

## 7. Statistical limits

All bounds below are exact binomial (Clopper–Pearson) bounds, and they assume independent trials. That assumption is **weaker** than it looks:
- The 12 edits of one original are strongly correlated, so the effective sample for positives is closer to 500 sources than to 6,000 queries.
- All images come from one generator family, so the negatives are 1,000 draws from that family, not from any natural-image population.

| Observation | What it bounds |
| --- | --- |
| 0 of 1,000 negatives within threshold | per-query rate below 0.30% (one-sided 95%), for **this generator**, this 500-entry catalogue and the 8-variant search. Not a natural-image rate, and not a rate for other catalogue sizes |
| 0 of 250 selection negatives | below 1.19% |
| 0 of 6,000 positives with a wrong entry within threshold | below 0.050% per query if queries were independent. Counted by the 500 sources instead, 0 of 500 bounds the per-source rate below 0.60% |
| 5 of 6,000 (the F2 line) | upper bound 0.18% per query (one-sided 95%) |
| 475 of 500 correct (the F3 line) | 95% interval 92.7%–96.7%. The F3 line is a point-estimate rule. To show recall ≥ 95% at one-sided 95% confidence would need 484/500 or more, and the protocol does not claim that |
| 500 of 500 correct | recall above 99.4% (one-sided 95%), for this generator and edit |

The raw comparison counts (4,000,000 negative and 23,952,000 wrong-entry comparisons per extractor in evaluation) are not independent trials. No per-comparison rate is reported. No rate is stated beyond what n supports, as IMGF.4 requires.

## 8. Execution, offline proof and order of steps

The commands are in the [README](../experiments/image-fingerprint/README.md#running-the-measured-experiment). In order:

1. **Online, once.** Fetch the wheels (`requirements*.txt` hashes) and the 30 PDQ vector files (`fetch_pdq_vectors.py`, pinned by commit, git blob id and SHA-256). Create `.venv` and install with `--no-index --require-hashes`.
2. **Offline from here.** Every later step runs under `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'`. The roadmap names `scripts/offline`; that script belongs to the implementation repository and does not exist in this one. The sandbox command plays its role here, and IMGF.4's wording needs to accept the substitute (§13).
3. `check_vectors.py` (C1), then the unit tests.
4. `run_experiment.py full --require-network-denied --out out/full-1`. The harness refuses to start unless the protocol digest, the environment pin, the vector results and the network probe all hold (C1, C4, C5). The probe binds `127.0.0.1:0` and connects to `1.1.1.1:443`. Both MUST be refused with EPERM or EACCES. An allowed connect is closed at once and no data is sent.
5. The same command again with `--out out/full-2`, as a separate process.
6. `run_experiment.py compare out/full-1 out/full-2` (C3).
7. Copy `out/full-1` and the compare output to `results/e-img-f-1/` and commit. That commit MUST descend from the protocol commit.
8. A non-author rechecks the counts from `queries.jsonl` (IMGF.4).

## 9. Budget and abort rule

The figures were measured on smoke runs (§11; 20 images, 116 extractions and 44 vendor cross-checks each) on the author's laptop: Apple Silicon, macOS 26.4, CPython 3.14.6. Other work was sometimes running at the same time.
- **Unit costs**, from one profiled run: about 0.10 s per profile extraction (both extractors, 8 variants each); 0.82 s per pure-Python vendor cross-check; 0.05 s per edit encode; 0.10 s per generated image.
- **Wall-clock per smoke run on the final code:** 25.7 s, 24.9 s and 23.3 s with the cross-check.
- **Earlier code:** 26.5 s, 98.5 s (under heavy load) and 57.4 s (profiled) with the cross-check; 35.2 s without it.
- **Scaling.** A measured run is about 74 times a smoke run: 63% of smoke time is the cross-check, scaled 59×, and the rest scales 101×.

| Resource | Estimate per measured run | Basis |
| --- | --- | --- |
| Profile extractions | 11,750 (750 originals + 11,000 queries) | §3 |
| Vendor cross-checks | 2,600 | C2 |
| CPU time | at most about 67 min (unit costs × counts; profiler overhead included) | profiled smoke run |
| Wall clock | about 30 min on an idle machine, up to about 2 h under the heaviest load seen; two runs are needed (C3) | smoke runs × 74 |
| Peak memory | about 0.7 GB measured on the smoke run; under 2 GB expected | ru_maxrss |
| Disk, transient | none for images: images are generated in memory and never written | design |
| Disk, outputs | about 17 MB of `queries.jsonl` (1.55 kB per query) plus catalogues, per run; under 50 MB committed | smoke record size |
| Disk, environment | `.venv` 87 MB, `wheelhouse` 15 MB, vector images 6.8 MB (all git-ignored) | measured |
| Network | none after step 1 | C5 |

**Abort rule.**
- A run whose elapsed time exceeds **4 h** stops at the next image. It writes only `summary.json` with status `aborted-time-limit` and no metrics, and exits with status 3.
- An aborted run is not a result. It may be repeated under the same version on a less loaded machine, because no metric was computed.
- If two consecutive runs abort, the owner decides whether to cut the vendor cross-check to originals only. That would be a new version.
- The harness does not enforce a memory limit. A run that fails for memory is invalid (§6) and is reported.

## 10. What is recorded

Per run, in the output directory:

| File | Content |
| --- | --- |
| `catalogue-selection.json`, `catalogue-evaluation.json` | profile §8 records, canonical bytes |
| `selection-threshold.json` | the null-comparison minimum and the resulting `T_iscc` (and, for reference, the PDQ minimum) |
| `queries.jsonl` | one canonical JSON line per query. Each line has: id, split, kind, source, edit; file SHA-256 and length; decode fields; and per extractor the status, quality, all 8 hashes, outcome, entry, distance, entries within threshold, true-source distance and nearest wrong entry (or nearest entry for negatives) |
| `summary.json` | protocol version and digest (recorded and recomputed); configuration digests; environment and package versions; network probe; vector-check counts; thresholds; enrollment counts; all §6 metrics and criteria; vendor cross-check counts; `resultsSha256` over the deterministic records; elapsed seconds; peak RSS; the label `MEASURED RUN` |

Timing and memory are excluded from `resultsSha256`, so C3 compares only deterministic content. Images and pixels are never stored; any image can be regenerated from its seed.

## 11. Dry tests before freezing (not results)

All dry tests ran on 2026-11-22, before this file was frozen. No experiment seed (0–1,999) was generated, hashed or looked at.

- **Vector checks** (`vectors/check-results.json`). PDQ core 30/30. ISCC 3/3 with compiled and with pure-Python DCT. Published PDQ outputs: not exactly reproduced (profile §7).
- **Unit tests.** 24 of 24 pass, covering generator goldens and determinism, port against vendor, ISCC vectors and variants, edit sizes and determinism, decode abstentions, EXIF and alpha, threshold boundary, ties, min-over-variants, the self-excluding digest, the criteria logic and catalogue validation.
- **Smoke runs.** 20 images from seeds 1,000,000–1,000,019, run in the harness's `smoke` mode. Each run did 116 extractions and 108 queries.
  - **On the committed code:** two consecutive runs were byte-identical (`resultsSha256` `57cb67b36fc6fe599539a3cd51bafaed5993ac5516ee35a9317fe5fba8b3e468`). A third run under `sandbox-exec` deny-network was byte-identical to them, and its probe reported bind and connect refused (errno 1).
  - Each run's vendor cross-check agreed 44/44, and both catalogues passed the C6 validation.
  - Earlier smoke runs had the same determinism and network results, on code whose catalogues did not yet embed `extractionConfig`. That format change is the only reason their digest differed (`03f33153…`).
  - The smoke summary withholds match metrics by design.
- **What the author saw.**
  - Smoke match outcomes were not tabulated. One smoke query line, a `crop50` query, was read while checking the record format; it was a `no-match` for both extractors.
  - PDQ quality of the 20 smoke originals ranged 58–100, so none fell below the floor. This was checked as a property of the generator: it confirms the generator is not producing featureless images.
  - No parameter in §2–§6 was changed after any smoke output was seen. The code changes made after the first smoke run were holding fewer images in memory, embedding the configuration in each catalogue, and adding the C6 validator. The memory change was checked: the output digest stayed the same. The other two touch only catalogue fields and the summary, so they leave hashes and outcomes unchanged by construction. The earlier query files were not kept, so that was not compared byte for byte.

## 12. Changes that need a new protocol version

Any change to:
- the seed plan, image counts, splits or generator code;
- an edit's definition or encoder settings;
- the decode stage, either extractor, or the configuration digests;
- the PDQ threshold or quality floor, or `selection-rule-1`;
- the metrics' definitions or denominators, F1–F3, C1–C6 or the verdict mapping;
- package versions or hashes, Python minor version, or platform;
- the vendor cross-check scope;
- the abort rule.

These do **not** need a new version: editorial fixes in the README; adding analyses that are labelled post hoc and leave the frozen metrics and verdict unchanged; re-running after an abort (§9).

## 13. Needs the owner or coordinator

- **Install approval.** The roadmap lists the IMGF package install as owner-gated (IMGF.3; "Owner-blocked gates"). This lane's brief from the coordinator says the owner allowed it, and the install described in the README was made on that basis. The roadmap text has not been updated.
- **Design.** Roadmap 2,000-image design (this protocol) or lane 10's post-audit 200-image conformance run (§1).
- **IMGF.2 wording for PDQ** (profile OD-I1). Exact equality with the published outputs is not achievable with Pillow decoding.
- **`scripts/offline`.** Accept `sandbox-exec` deny-network as its substitute for IMGF.4 in this repository, or wait for the implementation repository.
- **Cross-host check.** An x86 run would need its own wheel hashes and a protocol version.
- **Review.** A non-author review of this protocol before the first measured run, as the coordinator brief requires. The measured run has not been started.
