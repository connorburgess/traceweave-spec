# E-IMG-F protocol: contract check of the still-image fingerprint profile

Protocol version: `e-img-f-2`. Status: **frozen for review, 2026-11-22; not yet run.** Roadmap gate IMGF.3, preparing IMGF.4 and IMGF.5 ([roadmap](../../ROADMAP.md), later-profile table). Profile under test: [extraction-profile-image.md](extraction-profile-image.md), version `draft-2`. Harness: [research/experiments/image-fingerprint/](../experiments/image-fingerprint/README.md). Evidence: [lane 10](../lanes/10-evidence-review.md), including "After the report audit"; the [report audit](../lanes/10-report-audit.md); and the [non-author review of `e-img-f-1`](../reviews/image-profile-protocol-review.md).

Protocol digest (SHA-256, self-excluding): `44a67a14c6e4c3028bd20a093896390c308a89cf92fc2d521c788346ad6b90c4`

The digest is the SHA-256 of this file's bytes with the 64 hex digits above replaced by 64 zeros. The README repeats it. `run_experiment.py full` recomputes it and refuses to start if it differs. It also refuses unless the code identity holds (§8).

This is a research protocol. It changes nothing in `spec/`, `schemas/`, `profiles/` or `test-vectors/`. Nothing here is normative.

## 0. Design decision and version history

| Date | Event |
| --- | --- |
| 2026-11-22 | `e-img-f-1` frozen at commit `4714735` (digest `b7e4856b…`): 2,000 images, pass lines F1–F3 on false matches and recall |
| 2026-11-22 | Non-author review of `e-img-f-1` ([review](../reviews/image-profile-protocol-review.md), commit `bd7f094`). Blocking items: B1 code identity, B2 design choice, B3 roadmap wording |
| 2026-11-22, **before any result existed** | **Coordinator decision, in writing:** the design is `e-img-f-2`, the 200-image contract check with no pass line on false matches, following the lane 10 report audit. `e-img-f-1` is **retired unrun**. ROADMAP IMGF.2–IMGF.4 were reworded to match (commit `fe14421`) |
| 2026-11-22 | `e-img-f-2` (this file) frozen. It addresses every review finding (§13) |

No measured run of either version has been made. No seed in either version's experiment range has been generated or hashed by any test or dry run: 0–1,999 for `e-img-f-1`, 0–199 here.

**Freeze rule.**
- The **frozen commit** is the commit that adds this file with its digest filled in. A file cannot contain its own commit id, so the frozen commit id is recorded outside this file: in the coordinator report and in a later README note. The runner passes it as `--frozen-commit`.
- The harness refuses to run `full` unless HEAD equals that commit and the work tree is clean (§8).
- The first commit containing a measured result MUST descend from the frozen commit (`git merge-base --is-ancestor`), and its summary MUST carry this digest.
- Changes listed in §12 make a new version, and a result obtained under an earlier version stays reported.

## 1. Question, and what the run does and does not show

**Question.** Is the draft profile a reproducible, conformant and recordable contract on this host? The run answers it with three checks:
- The extractors reproduce the published reference vectors under the IMGF.2 criteria.
- Two runs give byte-identical records.
- Every output fits the image catalogue record and the query record.

**What it shows if it passes:**
- On one macOS arm64 host with the pinned environment, the profile's decode and both hashes are deterministic across runs.
- The NumPy PDQ port equals the vendored ThreatExchange reference on every input, and the published vectors fall within the vendor's own tolerances.
- ISCC matches iscc-core's conformance outputs.
- Each of the 1,400 records validates.

**What it does not show:**
- **How well PDQ or ISCC match images.**
- **Any false-match rate, and anything about natural images.**
- **Robustness to crop, screenshot or adversarial edits; equality across hosts or decoders; equality with iscc-sdk's own outputs.**

**The PDQ checks on synthetic images are weak by construction**, and this protocol says so in advance:
- `png` re-encodes identical pixels, so its true-source distance is 0 unless enrollment abstains.
- `jpeg90`, `jpeg75` and `flip` (with dihedral matching) are expected to match.
- Random-shape negatives are expected to sit far from every entry.
- The port-against-vendor check (V4) shows the port is a faithful copy of the vendor's arithmetic. It does not show the arithmetic is independently right: the port deliberately repeats the vendor's operation order. That independent check is IMGF.5's C++ comparison.

**What carries information:**
- the determinism and record checks;
- the deep-edit rows (`crop50`, `crop75`, `screenshot`, `jpeg30`, `resize25`);
- the distance histograms.

None of these has a pass line.

**Why the scope is small.** The audit's source X1 (§1a) already measured false matches, crop failures and screenshot failures for both hashes, on natural images and at a scale synthetic images cannot reach. A larger synthetic run would mostly reproduce known direction. Lane 10's 12 edit definitions are kept so that the contract and record are exercised on every edit.

## 1a. What the cited benchmark measured (not our measurement)

Kazempourradi, Mojtahedi and Mohseni, *Watermarks and Fingerprints as Soft Bindings for Content Provenance*, [arXiv:2610.04151v1](https://arxiv.org/abs/2610.04151v1), 2026-10-02.

**What kind of source it is.** It is an **author-run, unreplicated preprint**. Its authors work for a provenance vendor that registered PDQ-family C2PA soft-binding ids. The figures below are as the [report audit](../lanes/10-report-audit.md) checked them against the paper.

| What X1 measured | Figure (X1 location) |
| --- | --- |
| PDQ false bindings | 267 of 26,820 held-out never-registered queries (1.00% per query) against a 98,985-item registry dominated by product near-copies, at a pair-level 10⁻⁷ threshold fixed on held-out negatives (§5.2) |
| Crop | a crop keeping 70% of each side drops PDQ to 0% Recall@1 (§5.1) |
| Rotation | 15° rotation: PDQ 0% (§5.1) |
| Screenshots | every hash scores 0% on screenshot templates (§5.1) |
| Dihedral matching | PDQ 54.6% with dihedral variants against 49.5% plain, at pair-level 10⁻⁷ (§5.1) |
| Cross-host | PDQ and the ISCC codes bit-identical across x86 and arm64 hosts on 200 PNG files (§5.7) |
| Watermarking moves fingerprints | ISCC changed in 62.0% of watermarked images, PDQ in 0.3% (§6) |

**None of these is our measurement.** This protocol neither confirms nor refutes them. Synthetic-image counts from this run are not comparable to them: the population, catalogue size, threshold and unit all differ.

## 2. What is frozen

| Item | Frozen value |
| --- | --- |
| Profile | `traceweave-image-fingerprint` `draft-2`. Extraction configuration SHA-256 `c740e92de69a47904fa81bb3614c086194717be856fa6a44d89ad6fdba3bb927`; matching configuration SHA-256 `fe3fa0395d3701fa5b1b55839063998eba528851d4f9e3dcaca62d3a0f6c97ac` |
| Code | every file under `research/experiments/image-fingerprint/`, plus this file and the profile, at the frozen commit. The harness enforces this (§8) |
| Environment | CPython 3.14.x on macOS arm64; the 19 packages in `requirements.txt` plus setuptools 84.2.1 from `requirements-build.txt`, installed with `--require-hashes`; Pillow 13.0.0 with libjpeg-turbo 3.2.0 and zlib-ng 1.3.1. `check_environment()` MUST report no deviation |
| Generator | `traceweave-synth-draft-1` (§3); golden pixel digests for three smoke seeds are checked by the unit tests |
| Seeds | §3 |
| Edits | the 12 in §4 |
| Thresholds | PDQ: distance ≤ 31, abstain at quality ≤ 49. ISCC: distance ≤ 7. Both are experimental and carry no pass line (§5) |
| Validity conditions | §6 V1–V5 |
| Abort rule | §9 |

## 3. Images

**Generator `traceweave-synth-draft-1`.** The prose below and `twimg/generator.py` describe the same procedure. If they ever disagree, the code at the frozen commit and its three golden digests decide, because only the code is executed. Every random draw comes from one stream, in exactly this order.

**Stream and notation.**
- The stream is `numpy.random.Generator(PCG64(SeedSequence([0x7477696D, seed])))`, with NumPy 2.5.5. `0x7477696D` is the ASCII bytes "twim".
- Seeds are integers in 0 … 2³²−1.
- `U()` is `Generator.random()`, uniform on [0, 1).
- `I(a, b)` is `Generator.integers(a, b)`, uniform on the integers a … b−1.
- `C()` is `Generator.integers(0, 256, size=3)`, three channel values.

**Steps.**
1. **Size.** `(W, H)` = `(512, 512)`, `(1024, 768)` or `(1920, 1080)` for `seed mod 3` = 0, 1 or 2. No draw is used.
2. **Background.** Draw `c0 = C()`, `c1 = C()` and `θ = 2π·U()`. For each pixel (x, y) let `p = x·cos θ + y·sin θ`, and `t = (p − min p)/(max p − min p)` over the image. Then the colour is `c0·(1−t) + c1·t` per channel, in float64, rounded half-to-even (`numpy.rint`), clipped to 0–255 and stored as `uint8`.
3. **Shapes.** Draw `n = I(6, 15)`. For each of the n shapes, in this draw order:
   - `kind = I(0, 4)`;
   - `colour = C()`;
   - `cx = U()·W`, `cy = U()·H`;
   - `rx = (0.05 + 0.30·U())·W`, `ry = (0.05 + 0.30·U())·H`.

   The box is `[int(cx−rx), int(cy−ry), int(cx+rx), int(cy+ry)]`, where `int` truncates toward zero. Each shape is drawn with Pillow 13.0.0 `ImageDraw`, filled, without antialiasing:
   - kind 0: `rectangle(box)`;
   - kind 1: `ellipse(box)`;
   - kind 2: draw `m = I(3, 7)`, then m angles `2π·U()`, sorted ascending. The vertices are `(int(cx + rx·cos a), int(cy + ry·sin a))`, drawn with `polygon`;
   - kind 3: draw `width = I(max(2, W//200), max(3, W//40))` and draw `line([box[0], box[1], box[2], box[3]], width)`.
4. **Texture.** Draw `cells = I(8, 33)` and `amp = 8 + 16·U()`. For each channel R, G, B in order:
   - draw a `cells × cells` grid `2·U() − 1` (row-major draws), cast to float32;
   - resize it to `(W, H)` with Pillow `BILINEAR` on mode `F`;
   - add `amp` times the result to that channel, in float64.
5. **Noise.** Draw `σ = 1 + 5·U()`. Then draw `Generator.normal(0, σ, size=(H, W, 3))` and add it.
6. **Output.** Round half-to-even, clip to 0–255 and store as `uint8` RGB. Identity: `pixelSha256` = SHA-256 of the ASCII `"{W}x{H}x3:"` followed by the row-major array bytes.
7. **Encoding.** Originals are encoded as PNG with Pillow (`compress_level` 6, `optimize=False`, no metadata). The profile decodes those bytes.

**Seed plan**, decided before any image in it was generated:

| Role | Seeds | Images |
| --- | --- | --- |
| Catalogue, enrolled | 0–99 | 100 (34 at 512×512, 33 at 1024×768, 33 at 1920×1080) |
| Negatives, never enrolled | 100–199 | 100 (the same 34/33/33 split) |
| Smoke (never part of a result) | 1,000,000–1,000,019 | 20 |

**Counts.**
- 1,200 positive queries (100 originals × 12 edits) and 100 negative queries, against a 100-entry catalogue.
- **Extractions: 1,400** = 100 enrolled originals + 1,200 edited queries + 100 negative queries. The originals are enrolled, never queried.
- The smoke set has the same shape: 10 + 120 + 10 = 140.

## 4. The 12 edits

These are unchanged from `e-img-f-1` and lane 10 (`twimg/transforms.py`). Each edit takes the decoded original (RGB `uint8`) and produces file bytes, which the profile then decodes like any input. Encoders are Pillow 13.0.0 with its bundled codecs. No EXIF, ICC or text metadata is written.

| Name | Exact definition | Output |
| --- | --- | --- |
| `jpeg90`, `jpeg75`, `jpeg50`, `jpeg30` | `save(format="JPEG", quality=q, subsampling=2 (4:2:0), optimize=False, progressive=False)` | baseline JPEG |
| `resize50` | `resize((W//2, H//2), LANCZOS)`, then `resize((W, H), BICUBIC)` | PNG, level 6 |
| `resize25` | the same with `W//4, H//4` | PNG, level 6 |
| `crop90`, `crop75`, `crop50` | centre crop to area fraction a: side factor s = √a; `cw = ⌊W·s + 0.5⌋`, `ch = ⌊H·s + 0.5⌋`, `left = ⌊(W − cw)/2⌋`, `top = ⌊(H − ch)/2⌋`. The kept side fractions are about 94.9%, 86.6% and 70.7% | PNG, level 6 |
| `flip` | horizontal mirror, `transpose(FLIP_LEFT_RIGHT)` | PNG, level 6 |
| `png` | lossless PNG round trip at `compress_level` 1 instead of 6. Pixels are identical by construction | PNG, level 1 |
| `screenshot` | **screenshot simulation**: paste onto a `(W+80)×(H+80)` canvas of RGB (240, 240, 240) at offset (40, 40); then `resize` with `BICUBIC` to `(⌊0.8·(W+80) + 0.5⌋, ⌊0.8·(H+80) + 0.5⌋)`, computed in integers as `(2·4·x + 5) // 10` | PNG, level 6 |

The screenshot simulation has none of the following: window chrome, display colour management, sub-pixel text, device-pixel-ratio scaling or a lossy screenshot codec. It is not a screenshot. Unit tests check the output sizes for all three resolutions (screenshot: 474×474, 883×678 and 1600×928).

## 5. Thresholds

Both thresholds exist only so that match counts can be written down. Neither is calibrated, neither is tuned on any data in this run, and no pass line uses them.
- **PDQ.** Match when the min-over-dihedral Hamming distance is ≤ 31 of 256 bits; abstain `low-quality` at quality ≤ 49. These are the vendor's starting values (lane 10 F1).
- **ISCC.** Match when distance is ≤ 7 of 64 bits. That is PDQ's bit fraction scaled to 64 bits, ⌊64 · 31/256⌋ = 7, fixed by that rule before any ISCC distance on experiment images existed. It is not an ISCC recommendation; none was found in the inspected sources.

The histograms (§6) allow the counts to be re-read at any other threshold without re-running.

## 6. Validity conditions, and counts without a pass line

The run is judged **only** on V1, V2 and V5, together with V4, which is the in-run half of V1. V3 is recorded as not tested. These conditions follow ROADMAP IMGF.4: (a) is V1 and V4, (b) is V2, and (c) is V5.

| ID | Condition | How it is checked |
| --- | --- | --- |
| V1 | **Reference vectors**, the IMGF.2 counts, k/k. All of: (a) the 30 vector files are present and verified; (b) the PDQ port equals the vendored ThreatExchange Python reference on identical decoded pixels (8 dihedral hashes and quality, 30/30); (c) on the profile decode path, PDQ is within 10 bits of the C++ `reg_test` output on 8/8 (all published quality 100, so the vendor's quality ≥ 80 criterion applies to all), with published quality equal on 8/8; (d) within 16 bits of each comparable published Python output, 12/12 and 18/18; (e) ISCC Image-Code v0 equals iscc-core 1.5.0 `data.json`, 3/3 | `full` re-runs `check_vectors.py` **fresh** on the run host before any image is generated, then requires `git status --porcelain` to stay empty: the regenerated `vectors/check-results.json` must be byte-identical to the committed one. The verdict comes from the fresh results (`vector_verdict()`) |
| V2 | **No difference between runs.** Two complete runs, in separate processes, give byte-identical `catalogue.json` and `queries.jsonl` and equal `resultsSha256` | `run_experiment.py compare` |
| V3 | **No difference between hosts.** **Not tested**: one host, macOS arm64, with arm64-only pins. The record cites X1 §5.7 (§1a), which is not our measurement | `crossHost: not-tested` in every summary |
| V4 | **Port equals reference on every run image**: 1,400/1,400 extractions, all 8 dihedral hashes and quality | in the harness; `vendorCrossCheck` lists **every** mismatching id |
| V5 | **Records fit.** The catalogue is canonical JSON in the profile §8 field set and binds both configuration digests. Every query line has the closed field set of §10, an outcome from the closed list, in-range distances, and a `withinThreshold` list whose length equals `withinThresholdCount` | `validate_catalogue()` and `validate_query()`; `recordValidation` lists **every** error |

**Exact equality with the published PDQ hashes is not part of V1.** The vendor's own reference sets differ by up to 8 bits on identical files, and the C++ luma arrays are not published (review, IMGF.2 section). The exact counts are reported beside V1 in profile §7: C++ 0/8, README 4/12, unit test 8/18.

**Verdict.**
- V1, V2, V4 and V5 hold, and the start conditions (§8) were logged as met: the contract check is **met**, within §1's statement of what that shows.
- Any of them fails: the run is a **negative result** for the contract, and the failing condition is reported.

There is no other verdict. Counts never change it.

**Counts reported without a pass line.** Each is a count with its denominator, per extractor (`compute_metrics()`):

| Count | Denominator |
| --- | --- |
| Per edit: correct match, wrong-top match, ambiguous, no-match, abstentions by code, queries with any wrong entry within threshold | 100 positives of that edit |
| All edits: queries with any wrong entry within threshold; wrong-top matches | 1,200 |
| Negatives with any entry within threshold; negative outcomes by class | 100 |
| Enrollment: entries enrolled, and abstentions by code | 100 |
| Histograms: true-source distance per edit; nearest-wrong distance over all positives; nearest-entry distance over negatives | as above, minus abstentions |
| Runtime and peak resident memory | one run |

**Reporting rule.** The results note MUST repeat §1's paragraph on weak PDQ checks next to any PDQ count. It MUST present the deep-edit rows and histograms as limits, not as successes or failures.

## 7. Statistical limits

All bounds are exact binomial (Clopper–Pearson) one-sided 95% bounds, and they assume independent trials. The trials are not independent: the 12 edits of one original are correlated, and all images come from one generator family.

| Observation | What it bounds at most |
| --- | --- |
| 0 of 100 negatives within threshold | per-query rate below 2.95%, for this generator, this 100-entry catalogue and the 8-variant search |
| 0 of 1,200 positives with a wrong entry within threshold | below 0.25% per query if independent; counted by the 100 sources, below 2.95% per source |
| k of 100 correct for one edit | a 95% interval roughly ±4 to ±10 percentage points wide, depending on k |

None of these is a natural-image rate. The natural-image figure that exists is X1's 1.00% per query (§1a), which is not our measurement.

## 8. Execution, code identity, offline proof and order of steps

The commands are in the [README](../experiments/image-fingerprint/README.md#running-the-measured-experiment). In order:

1. **Online, once.** Fetch the wheels (`fetch_wheels.py`, matched to the `requirements*.txt` hashes) and the 30 PDQ vector files (`fetch_pdq_vectors.py`, pinned by commit, git blob id and SHA-256). Create `.venv` and install with `--no-index --require-hashes`. `.venv`, `wheelhouse/`, `vectors/pdq-data/` and `out/` are git-ignored, so they do not dirty the tree.
2. **Clean tree at the frozen commit.** Create a dedicated work tree checked out at the frozen commit: `git worktree add <dir> <frozen-commit>`. The shared checkout carries other lanes' uncommitted work and cannot pass the clean-tree check. Then run steps 1–3 inside it.
3. **Offline from here.** Every later step runs under `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'`. That is the substitute for `scripts/offline` that ROADMAP IMGF.4 accepts.
4. The unit tests.
5. `run_experiment.py full --frozen-commit <40-hex> --require-network-denied --out out/full-1`. Before generating any image, the harness:
   - **(i)** logs and checks its **code identity** (`codeIdentity` in `summary.json`):
     - `git rev-parse HEAD` equals `--frozen-commit`;
     - `git status --porcelain --untracked-files=all` is empty for the whole work tree;
     - `git diff --exit-code <frozen> -- research/experiments/image-fingerprint research/drafts/image-experiment-protocol.md research/drafts/extraction-profile-image.md` exits 0;
     - `git merge-base --is-ancestor <frozen> HEAD` succeeds;
     - the protocol file's version line equals the harness's `PROTOCOL_VERSION` (`e-img-f-2`).
   - **(ii)** checks that the protocol digest matches and that `check_environment()` reports no deviation.
   - **(iii)** runs the network probe. It binds `127.0.0.1:0` and connects to `127.0.0.1` port 1, where nothing listens. Both MUST be refused with EPERM or EACCES. With the network allowed, the connect is refused by design with ECONNREFUSED. **No packet leaves the host in either case.**
   - **(iv)** re-runs `check_vectors.py` fresh and requires the work tree to stay clean (V1).

   Any failure refuses the run, with exit status 2. After the run, `git status` is logged again (`statusAfterRun`); it MUST be empty.
6. The same command with `--out out/full-2`, as a separate process.
7. `run_experiment.py compare out/full-1 out/full-2` (V2).
8. Copy `out/full-1`, the compare output and the two `codeIdentity` logs to `results/e-img-f-2/`, and commit. That commit MUST descend from the frozen commit.
9. A non-author rechecks the counts, the validity conditions and the identity log from the committed records (IMGF.4).

## 9. Budget and abort rule

The figures are measured on smoke runs of this version (§11): 140 extractions, all cross-checked against the vendored PDQ. They ran on the author's laptop: Apple Silicon, macOS 26.4, CPython 3.14.6.
- **Smoke runs:** 77.9 s, 74.5 s and 76.0 s.
- **Unit costs** (from a profiled `e-img-f-1` smoke run): about 0.10 s per profile extraction and 0.82 s per pure-Python vendor cross-check.

| Resource | Estimate per measured run | Basis |
| --- | --- | --- |
| Extractions | 1,400, each cross-checked (V4) | §3 |
| Wall clock | about 13 min (10 × a smoke run); up to about 40 min under heavy machine load. Two runs are needed (V2), plus about 10 s for the fresh vector check | smoke runs |
| Peak memory | about 0.7 GB (smoke: 651–657 MiB) | ru_maxrss |
| Disk, transient | none for images: images are generated in memory and never written | design |
| Disk, outputs | about 2 MB of `queries.jsonl` plus the catalogue, per run; under 5 MB committed | smoke record size |
| Disk, environment | `.venv` 87 MB, `wheelhouse` 15 MB, vector images 6.8 MB (all git-ignored) | measured |
| Network | none after step 1 | §8 |

**Abort rule.**
- A run whose elapsed time exceeds **1 h**, about 4.5 times the estimate, stops at the next image. It writes only `summary.json` with status `aborted-time-limit` and no counts, and exits with status 3.
- An aborted run is not a result. It may be repeated under the same version on a less loaded machine.
- If two consecutive runs abort, the owner decides what to do, and any change is a new version.
- A run that fails for memory is reported as failed.

## 10. What is recorded

Per run, in the output directory:

| File | Content |
| --- | --- |
| `catalogue.json` | profile §8 catalogue record, canonical bytes |
| `queries.jsonl` | one canonical JSON line per query, with the closed field set below |
| `summary.json` | protocol version and digest (recorded and recomputed); `codeIdentity` (frozen commit, HEAD, porcelain status lines, diff exit code and stat, ancestry, protocol version in file); `statusAfterVectorCheck` and `statusAfterRun`; configuration digests; environment; network probe; the V1 verdict with every count; thresholds; enrollment; `recordValidation` with every error; `vendorCrossCheck` with every mismatch id; `crossHost: not-tested` with the X1 citation; `resultsSha256`; elapsed seconds; peak RSS; the §6 counts with `passLine: none`; the validity map |

**Query line fields.** No list is truncated: `withinThreshold` holds every entry within threshold.
- **Top level:** `id`, `split`, `kind` (`positive` or `negative`), `source`, `transform`, `sha256` and `byteLength` of the query bytes, `decode`, `pdq`, `iscc`, and `pixelSha256` for negatives.
- **Per extractor:**
  - always: `status`, `outcome`;
  - when it abstains: `code`, plus `quality` for a PDQ low-quality abstention;
  - when it does not abstain: `quality` (PDQ only), all 8 `hashes`, `withinThreshold` (all `[entry, distance]` pairs) and `withinThresholdCount`;
  - on a `match`: `entry`; on any outcome with an entry within threshold: `distance`;
  - for positives: `trueDistance`, `wrongWithinThreshold` and `nearestWrong`; for negatives: `nearest`.

Timing, memory, identity and status logs are excluded from `resultsSha256`. Images are never stored. The mapping to the lane 08 shared record is in profile §8.

## 11. Dry tests before freezing (not results)

All dry tests ran on 2026-11-22 on the code of this version, from the shared checkout, whose tree was not clean. No seed in 0–199 was generated or looked at.

- **Vector checks.** V1 passes: the files 30/30; the port 30/30; C++ within 10 bits on 8/8 and quality on 8/8; Python within 16 bits on 12/12 and 18/18; ISCC 3/3, compiled and pure DCT.
- **Unit tests.** 30 of 30 pass. They cover:
  - the generator: goldens and determinism;
  - PDQ: the port against the vendor;
  - ISCC: conformance vectors and variants;
  - the edits: sizes and determinism;
  - decode: abstentions (16-bit PNG and 2-bit grey PNG as `unsupported-bit-depth`, CMYK JPEG as `unsupported-mode`); the alpha formula equal to Pillow's paste; palette lookup with `tRNS`; the grey formula; EXIF applied for JPEG and ignored for PNG;
  - matching: the threshold boundary, ties and min-over-variants;
  - harness plumbing: the probe and identity shapes, the self-excluding digest, the vector verdict, and catalogue and query validation.
- **Smoke runs.** 20 images, seeds 1,000,000–1,000,019, run in `smoke` mode.
  - Two consecutive runs were byte-identical (`resultsSha256` `9e83ee10be5805acbfd7ee5b5fecbd5d35ca4bae973397713ad35c32ebd07eb3`).
  - A third run under `sandbox-exec` deny-network was byte-identical to them. Its probe reported `bind refused errno 1; loopback connect refused errno 1 (EPERM)`. Outside the sandbox, the same probe reports `bind allowed; loopback connect refused errno 61 (ECONNREFUSED)`.
  - Vendor cross-check 140/140 in each run; 0 catalogue and 0 query record errors.
  - The smoke summary withholds counts by design.
- **Identity log, smoke run c.** `ok: false`, as expected: the shared tree had 18 porcelain lines from other lanes, and the protocol file still carried `e-img-f-1`. `full` mode was **not** run.
- **What the author saw.** Under `e-img-f-1`, one smoke query line (a `crop50` `no-match`) was read while checking the record format, and the PDQ quality range of the 20 smoke originals (58–100) was checked as a property of the generator. No parameter of this version was chosen from any smoke output. The ISCC threshold follows the fixed rule in §5.

## 12. Changes that need a new protocol version

Any change to:
- the seed plan, image counts or generator code;
- an edit's definition or encoder settings;
- the decode stage, either extractor, or the configuration digests (thresholds included);
- V1–V5 or the identity checks;
- the record field sets;
- package versions or hashes, Python minor version, or platform;
- the vendor cross-check scope;
- the abort rule.

These do **not** need a new version: notes **outside** the frozen paths; re-running after an abort; added analyses that are labelled post hoc and leave the verdict unchanged. A README edit after the frozen commit is outside the run, because the run uses a work tree at the frozen commit, but it changes the frozen paths at HEAD. Record the frozen commit id elsewhere, or accept that `git diff` against later commits is non-empty for that file.

## 13. Disposition of the non-author review of `e-img-f-1`

| Finding | Disposition in `e-img-f-2` |
| --- | --- |
| B1: no code-identity check | §8 step 5(i): the harness refuses `full` unless HEAD equals `--frozen-commit`, the tree is clean, the frozen paths do not differ and the protocol version matches. Every check is logged in `codeIdentity` |
| B2: choose the design in writing | §0: the coordinator chose `e-img-f-2` on 2026-11-22, before any result; `e-img-f-1` was retired unrun |
| B3: roadmap wording for IMGF.2 and IMGF.4 | Done by the coordinator in ROADMAP (commit `fe14421`). V1 implements the reworded IMGF.2; §6 maps V1–V5 to IMGF.4 (a)–(c) |
| M1: C1 read a stored file | §8 step 5(iv): `full` re-runs `check_vectors.py` fresh and requires `git status` to stay empty, both after the vector check and after the run |
| M2: PDQ pass close to certain | §1 states it plainly; §6 adds a reporting rule |
| M3: extraction-count erratum | `e-img-f-1` §9 said 11,750; the correct figure was 11,000 (750 enrolled + 10,250 queries). Here: 1,400 = 100 + 1,200 + 100 (§3), and the smoke set is 140 |
| M3: `withinThreshold` truncated to 20 | No list is truncated anywhere: `withinThreshold`, record errors and mismatch ids. V5 requires the list length to equal the count |
| L1: probe made a real outbound connection | The probe connects only to `127.0.0.1` port 1, refused by design (§8 step 5(iii)) |
| L2: generator prose incomplete | §3 gives every draw in order, with its distribution |
| Profile discretion (colour, JPEG settings, 16-bit PNG, EXIF sources, ISCC grey and resize, SDK-equality claim) | Tightened in profile `draft-2` §3 and §5, or declared out of scope: explicit formulas; named libjpeg-turbo settings; PNG bit-depth rule; JPEG-only EXIF; CMYK and YCbCr out of scope; ISCC resize defined by Pillow 13.0.0; the iscc-sdk equality claim withdrawn |
| Licences: NOTICE and "copied" wording | iscc-sdk at `cc11f771` ships no `NOTICE` file (top-level listing checked); its `LICENSE` is kept. The code now says "re-implemented following" |

## 14. Needs the owner or coordinator

- **Install approval.** The roadmap lists the IMGF package install as owner-gated. The install was made on the coordinator brief's statement that the owner allowed it.
- **Cross-host (V3).** Needs an x86 host, its own wheel hashes and a new version.
- **Review.** A non-author review of `e-img-f-2` before the measured run, as IMGF.3 requires. The measured run has not been started.

## 15. Recorded for the deferred mark study (not part of this protocol)

Nothing in this section is run or frozen here. It records preconditions for the owner-gated image mark study (IMG.0–IMG.5).

- **A TrustMark decode is not presence evidence.** In X1 Table 8 (85 unmarked source images, any of four decodes), TrustMark returned a BCH-valid code on 5.9–15.3% of unmarked images depending on variant. For example, variant Q gave 8 of 85 (upper bound 0.18) and variant C gave 13 of 85 (upper bound 0.25). This is X1's author measurement, not ours.
- **Decision rule.** A mark study MUST test decoded bits against the payload the verifier **expects** (k of n matching bits), never accept "a valid code decoded". X1 used k = 74 of 100 for TrustMark and observed 0 of 340 false matches. A study MUST record k with both bounds: its analytic per-key false-match bound, and its observed per-source bound. With N catalogue keys searched, the per-query bound is min(1, N × the per-key bound).
- **Other carried-over preconditions** are in the [lane 06–08 checkpoint](../research-06-08-checkpoint.md#deferred-proposal-note-post-hoc-image-study) and [lane 10](../lanes/10-evidence-review.md): weight licence and download, a quality floor, a no-key negative control and a transplant arm. PixelSeal is now a co-candidate.
