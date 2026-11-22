# Draft extraction profile: still-image fingerprints (`traceweave-image-fingerprint`, `draft-1`)

Status: **draft for review, 2026-11-22.** Roadmap gate IMGF.1 ([roadmap](../../ROADMAP.md), later-profile table), with the reference-output evidence for IMGF.2. Evidence: [lane 10](../lanes/10-evidence-review.md) and its [report audit](../lanes/10-report-audit.md). The experiment that would test this profile is frozen separately in [image-experiment-protocol.md](image-experiment-protocol.md). Code: [research/experiments/image-fingerprint/](../experiments/image-fingerprint/README.md).

This is research material, not a normative change. It does not modify `spec/`, `schemas/`, `profiles/` or `test-vectors/`. "MUST" describes what this draft proposes for an implementation claiming to follow it. No threshold here is calibrated. Every threshold is labelled **experimental**: it is fixed for one experiment run and is not frozen for the profile.

The profile has two extractors over one shared decode stage:
- **PDQ**, the main extractor: a 256-bit DCT perceptual hash with a 0–100 quality score (Meta ThreatExchange).
- **ISCC Content-Code Image v0**, the second extractor: a 64-bit DCT hash on a normalized 32×32 grey image (ISO 24138:2024, implemented by iscc-core).

Neither extractor inserts anything into an image. A fingerprint describes pixels; it carries no payload and no identity. The identity in any result is the catalogue entry it was matched to.

## 1. Pins

| Item | Pin | Where it is checked |
| --- | --- | --- |
| Python | CPython 3.14.x (3.14.6 used) | `twimg/profile.py` `check_environment()` |
| Decoder | Pillow 13.0.0, wheel SHA-256 `d9b0a2be…271d` (macOS arm64, CPython 3.14), with its bundled libjpeg-turbo 3.2.0 and zlib-ng 1.3.1 | same; [requirements.txt](../experiments/image-fingerprint/requirements.txt) |
| PDQ | ThreatExchange pure-Python PDQ at commit `9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2`, BSD licence, vendored unmodified under `vendor/threatexchange_pdq/` and checked file by file against the commit's git blob ids | `vendor/threatexchange_pdq/PROVENANCE.md` |
| PDQ, fast path | `twimg/pdq_np.py`, a NumPy port that repeats the vendor's floating-point operations in the same order | 30/30 vector images and every run image checked against the vendored code (§7, protocol §8) |
| ISCC | iscc-core 1.5.0, Apache-2.0, wheel SHA-256 `3bc10908…15f1` | `requirements.txt`; conformance data shipped in the wheel |
| ISCC normalization | the caller-side steps of iscc-sdk 0.9.7 (`image_normalize` defaults), commit `cc11f771e4efbf0a600f196c7e9155b529ad7598`, Apache-2.0, re-implemented with the same Pillow calls in `twimg/iscc_img.py` and `twimg/decode.py` | unit tests; iscc-sdk itself is not installed |
| NumPy | 2.5.5 (BSD-3-Clause and others) | `check_environment()` |

The complete package list with versions, licences and hashes is in the [experiment README](../experiments/image-fingerprint/README.md#environment). The pins are platform-locked: the hashes are for macOS arm64 wheels. Another platform needs its own hash list, and the protocol treats that as a new version.

## 2. Configuration bytes

The extraction configuration and the matching configuration are two separate records, as in the token baseline. Their exact bytes are `canonical(...)` in `twimg/profile.py`: sorted keys, no whitespace, one final LF.

| Record | SHA-256 of the exact bytes |
| --- | --- |
| Extraction configuration | `56c0d63ae0c3047d447d883c704cb47a1d1760dfc9719fb879413ca6b1f71315` |
| Matching configuration | `3925a95bc9f08bad07f788da784a1e50005f42e32a26fa43848b33108e9258dd` |

Extraction configuration bytes:

```
{"alpha":"flatten-white-iscc-sdk-0.9.7","decoder":{"jpegDraft":false,"libjpegTurbo":"3.2.0","library":"Pillow","version":"13.0.0","zlib":"1.3.1.zlib-ng"},"exifOrientation":"apply","formats":["JPEG","PNG"],"icc":"ignore-and-record","iscc":{"algorithm":"image-code-v0","bits":64,"dihedral":"catalogue-orig-query-8-on-32x32","implementation":"iscc-core-1.5.0","normalization":"iscc-sdk-0.9.7-cc11f771","qualityFloor":"none"},"maxBytes":67108864,"maxPixels":50000000,"minSide":32,"modes":["1","CMYK","L","LA","P","RGB","RGBA","YCbCr"],"multiFrame":"abstain","pdq":{"bits":256,"dihedral":"catalogue-orig-query-8","hexWordOrder":"vendor","implementation":"threatexchange-python-9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2","luma":"0.299R+0.587G+0.114B-float64","preResize":"none","qualityFloor":50},"profile":"traceweave-image-fingerprint","profileVersion":"draft-1"}
```

Matching configuration bytes (`parameterStatus` is `experimental`):

```
{"distance":"hamming-min-over-query-dihedral","iscc":{"comparison":"le","threshold":"selection-rule-1"},"matching":"traceweave-image-nearest-draft-1","parameterStatus":"experimental","pdq":{"comparison":"le","threshold":31},"tie":"abstain-ambiguous"}
```

Changing any value is a new profile or matching version with a new digest. The ISCC threshold is named by its selection rule, not by a number: the number is produced by the rule on the selection split of a given run and recorded in that run's `selection-threshold.json` (protocol §5).

## 3. Shared decode stage

Bytes in; an RGB array of 8-bit values, or an abstention. Implementation: `twimg/decode.py`. Steps in order; the first failure decides the code.

1. **Size.** More than 67,108,864 bytes (64 MiB): `input-too-large`.
2. **Open.** `PIL.Image.open` on the bytes. Any exception: `undecodable`.
3. **Format.** Pillow's detected format MUST be `JPEG` or `PNG`. Anything else, including GIF, WebP, TIFF and MPO: `unsupported-format`. The decision uses the file signature as Pillow reads it, never a file name.
4. **Multi-frame.** More than one frame (for example an animated PNG): `multi-frame`. The profile does not pick a first frame. A first-frame policy would make one file stand for several images, so it is left as open decision OD-I3.
5. **Pixel count.** Width × height above 50,000,000 before orientation: `too-many-pixels`.
6. **Mode.** Pillow's mode MUST be one of `1`, `L`, `LA`, `P`, `RGB`, `RGBA`, `CMYK`, `YCbCr`. Anything else, including 16-bit and float modes (`I;16`, `I`, `F`): `unsupported-mode`.
7. **Decode.** `Image.load()`. Any exception, including a truncated file: `undecodable`. JPEG is decoded at full size: no `draft()` and no `reduce`, so the decoded pixels never depend on a later target size. libjpeg-turbo runs with the settings Pillow 13.0.0 passes by default.
8. **EXIF orientation.** `PIL.ImageOps.exif_transpose`. Tag 0x0112 values 2–8 are applied, and 1 or a missing tag is the identity. The recorded value is the tag as read (`exifOrientation`, 1 when absent). All later coordinates are those of the oriented image.
9. **Alpha flattening.** The iscc-sdk 0.9.7 `image_fill_transparency` function with the same Pillow calls. `RGBA` and `LA` are pasted onto a white `(255, 255, 255)` RGB canvas with the alpha channel as mask. A `P` image with a `transparency` entry is converted to `RGBA` and pasted the same way. Other modes are converted with `convert("RGB")`.
10. **Colour.** The 8-bit component values are used as decoded. They are treated as sRGB-encoded, with no colour management, no linearization and no ICC transform. An embedded ICC profile is **ignored and recorded** (`iccPresent`). `CMYK`, `YCbCr`, `P`, `L` and `1` reach RGB through Pillow 13.0.0's own `convert("RGB")`. Proper ICC handling is OD-I2.
11. **Minimum size.** If the shorter side of the oriented image is below 32 pixels: `too-small`.

The result is an H×W×3 array of `uint8`, row-major, channels R, G, B.

## 4. PDQ (main extractor)

Implementation: the vendored ThreatExchange Python code is the reference; `twimg/pdq_np.py` is the port used for speed. Both are run on the same inputs and MUST agree bit for bit (§7).

1. **Luminance.** Per pixel, in float64: `L = (0.299·R + 0.587·G) + 0.114·B`. This is the vendor's formula and its evaluation order. The vendor's own comment calls it the ITU-R BT.601 "Y" weights. No gamma step is applied.
2. **No pre-resize.** The full oriented image is used. The vendor's Python tool first calls Pillow `thumbnail((512, 512))`, which for JPEG also enables draft decoding. That step is not part of this profile, for three reasons:
   - On the vendor's C++ regression vectors, full-resolution hashes are at least as close as thumbnail-path hashes on every one of the 8 images (distances 2–8 against 4–8; §7).
   - Draft decoding makes the decoded pixels depend on the target size.
   - It removes a resampling filter from the contract.

   This choice was made from vendor vectors only, before any experiment image was hashed.
3. **Blur.** Two X-then-Y passes of a 1-D box filter (Jarosz). The window along rows is `⌈cols/128⌉`, and along columns `⌈rows/128⌉`. The vendor's four-phase running sum is used, so edges are averaged over the part of the window inside the image.
4. **Decimation to 64×64.** Output cell `(i, j)` takes the blurred value at row `⌊(i + 0.5)·rows/64⌋` and column `⌊(j + 0.5)·cols/64⌋`. There is no interpolation.
5. **Quality.** Over the 64×64 grid, sum `|trunc((u − v)·100/255)|` for every vertical and every horizontal neighbour pair. Then `quality = min(100, ⌊sum/90⌋)`, an integer from 0 to 100.
6. **DCT.** `D` is the 16×64 matrix with `D[i][j] = √(2/64)·cos(π/128·(i+1)·(2j+1))`, for `i` in 0..15 and `j` in 0..63. `B = D·A·Dᵀ` is 16×16, so the DC term is excluded. Sums are accumulated over `k` from 0 to 63, in that order.
7. **Bits.** `m` is the median of the 256 values of `B`, found by the vendor's Torben routine (for 256 values it returns the lower middle value). Bit `16·i + j` is 1 if and only if `B[i][j] > m`.
8. **Output bytes.** 256 bits as 16 words of 16 bits. Word `w` holds bits `16w … 16w+15`, with bit `16w + k` as its bit `k`. The hex form is the 16 words from `w = 15` down to `w = 0`, each as 4 lowercase hex digits: 64 characters, which is the vendor's `Hash256.toHexString`. The 32 output bytes are that hex string decoded big-endian. The record also stores the integer `quality`.
9. **Quality abstention.** Quality ≤ 49 gives `low-quality`, both for an entry being enrolled and for a query. Quality ≥ 50 is eligible. This is the vendor's starting recommendation ("discard ≤ 49"; lane 10 F1), not a calibrated value.
10. **Dihedral variants.** A catalogue entry stores only the `orig` hash. A query computes all 8 variants from its `B` by the vendor's sign and transpose rules (`dct16OriginalTo*`). Their names are `orig`, `rot90`, `rot180`, `rot270`, `flipx`, `flipy`, `flipp` and `flipm`. No "minimal" variant is ever selected: the vendor README warns that selection is inconsistent across rotations. The distance to an entry is the **minimum over the 8 query variants**. A query is therefore compared 8 times with every entry, and any false-match calibration MUST count all 8 comparisons.
11. **Distance and threshold.** Hamming distance over 256 bits. A query is within threshold of an entry when distance ≤ `T_pdq`. `T_pdq = 31` is **experimental**: it is the vendor's starting value, used unchanged by the first experiment, and it is not frozen for the profile.

## 5. ISCC Content-Code Image v0 (second extractor)

iscc-core does not normalize images; its module docstring leaves that to the caller. The profile uses the iscc-sdk 0.9.7 defaults, so its codes are the ones the reference SDK would produce. Steps 1 and 2 are the shared decode stage (§3 steps 8–9).

1. **Border trim.** The iscc-sdk `image_trim_tolerant` rule, with tolerance 16 and at most 16 passes. Each pass works as follows:
   - The reference colour is the pixel at (0, 0).
   - A pixel differs if any channel differs from the reference by more than 16.
   - The image is cropped to the bounding box of differing pixels.
   - A pass that would cut only one side is applied only if, at tolerance 8, the bounding box is the same, so smooth gradients are kept.
   - Passes stop when nothing is cut.
2. **Grey.** Pillow `convert("L")`. This is Pillow's integer ITU-R 601-2 transform (`L = R·299/1000 + G·587/1000 + B·114/1000`, with Pillow's rounding). It is a different luma computation from PDQ's.
3. **Resize.** Pillow `resize((32, 32), BICUBIC)`, with the default `reducing_gap` (none). Pillow's bicubic widens its support when downscaling, so this is an antialiased resample.
4. **Pixels.** 1,024 `uint8` values, row-major.
5. **Hash.** iscc-core 1.5.0 `soft_hash_image_v0(pixels, bits=64)`:
   - a row DCT and then a column DCT (`iscc_core.alg_dct`, the compiled module shipped in the wheel);
   - the top-left 8×8 block of the result, DC term included;
   - its median, by `statistics.median` (the mean of the two middle values);
   - bit `n` is `1` if and only if value `n` is above the median, in row-major order, most significant bit first.
6. **Output bytes.** The 8-byte digest. The record stores its 16 lowercase hex digits. The ISCC string, `ISCC:` followed by the base32 encoding of header (CONTENT, IMAGE, V0, 64 bits) plus digest, can be derived from it and is never the comparison input.
7. **Quality.** ISCC defines no quality score, so the profile has none. Featureless images give degenerate codes; an all-black image gives all-zero bits, as in iscc-core's own test `test_0000_all_black_64`. Whether to abstain on them is OD-I5.
8. **Dihedral variants.** The 8 variants are taken on the 32×32 normalized array: NumPy `rot90` by 1, 2 and 3; top-bottom and left-right mirrors; transpose; anti-transpose. The catalogue stores `orig`, and the query distance is the minimum over its 8 variants, as for PDQ.
9. **Distance and threshold.** Hamming distance over 64 bits; within threshold when distance ≤ `T_iscc`. `T_iscc` is **experimental** and is produced by `selection-rule-1` on the selection split of a run (protocol §5). It is not frozen for the profile.

## 6. Matching and outcome classes

For each query and each extractor separately, against the enrolled entries of one catalogue:

| Level | Class | Codes | Meaning |
| --- | --- | --- | --- |
| Input | `abstain` | `input-too-large`, `undecodable`, `unsupported-format`, `multi-frame`, `too-many-pixels`, `unsupported-mode`, `too-small` | Decode stage (§3); applies to both extractors |
| Extractor | `abstain` | `low-quality` | PDQ only, quality ≤ 49 |
| Query | `no-match` | `no-match` | No enrolled entry within threshold |
| Query | `match` | `match` | Exactly one entry has the smallest distance, and that distance is within threshold. The result names the entry and the distance |
| Query | `abstain` | `ambiguous` | Two or more entries share the smallest distance within threshold. The profile does not choose between them |

Every query result also lists **all** entries within threshold, sorted by (distance, id), together with their count. A `match` with other entries inside the threshold is visible as such.

**Enrollment.** An entry that abstains is kept in the catalogue with its code. It is not enrolled for that extractor, and queries are not compared with it.

**Two extractors.** PDQ and ISCC results are reported side by side. The profile has **no combined verdict**. Their distances are never added, multiplied or converted into a joint score, following the lane 08 rule that mark, fingerprint and signature evidence are never multiplied. Agreement or disagreement between the two is reported as observed.

**`no-match`** means "no entry within threshold under this configuration". It does not mean the image was not derived from a catalogue image: deep crops and black-box perturbations defeat both hashes (lane 10 findings 2 and 3; audit X1).

## 7. Reference-output conformance (IMGF.2 evidence)

Run by `check_vectors.py`. The results are in `vectors/check-results.json`, and the inputs are 30 ThreatExchange `pdq/data` files pinned by commit, git blob id and SHA-256.

| Check | Result |
| --- | --- |
| Vector files present and matching their pins | 30/30 |
| PDQ hash core: NumPy port against the vendored Python, same decoded pixels, all 8 dihedral hashes and quality | **30/30** equal |
| PDQ against the vendor's C++ regression output (`pdq/cpp/reg_test/expected/out`, 8 images), profile path | **0/8** exactly equal; distances 6, 8, 6, 2, 2, 8, 6, 6 (max 8); quality 8/8 equal |
| Same, vendor Python thumbnail path | 0/8 equal; max distance 8 |
| PDQ against the C++ dihedral hashes of `bridge-1-original.jpg` (8) | 0/8 equal; max distance 8 |
| PDQ against the vendor Python README outputs (12), profile path | 4/12 equal; max distance 12; quality 12/12 equal |
| Same, vendor Python thumbnail path | **9/12** equal; max distance 2 |
| PDQ against the vendor Python unit-test outputs (18 usable; the 19th names `misc-images/b.jpg`, absent at the commit) | profile path 8/18, max 12; thumbnail path **17/18**, max 10 |
| ISCC Image-Code v0 against iscc-core `data.json` `gen_image_code_v0` (3 vectors: 64, 128 and 256 bits) | **3/3** with the compiled DCT; 3/3 with iscc-core's pure-Python `dct.py` |

**What this shows.**
- The PDQ arithmetic is reproduced exactly: two implementations agree on identical decoded pixels.
- The published PDQ outputs are **not** reproduced exactly by any decode path in this environment.
  - The three vendor reference sets disagree with each other. For example, the C++ and Python hashes of `bridge-1-original.jpg` differ by 8 bits.
  - The vendor README defines correctness differently: exact equality only when the C++ luma arrays are fed in, and Hamming distance ≤ 10 against C++ when quality ≥ 80. The vendor's own Python test allows ≤ 16.
  - Against those definitions: the profile path is within 10 bits of C++ on 8/8, and within 16 bits of every comparable Python output (30/30).
- **IMGF.2 as worded ("equals … k/k") is therefore not met for PDQ.** It cannot be met by decoding the published JPEGs with Pillow: the C++ tool uses a different decoder, and the C++ luma arrays are not published. Two options for the gate (OD-I1):
  - reword it to the vendor's criteria plus exact port-versus-reference agreement;
  - build the C++ reference and feed it identical luma arrays, which is a new build dependency.
- ISCC meets IMGF.2 as worded on the 3 vectors iscc-core ships. Those vectors start from 32×32 pixel arrays, so they test the hash core and not the normalization in §5 steps 1–3. No published vector covers the normalization.

## 8. Catalogue record for images (`traceweave-image-catalogue-draft-1`)

The experiment writes these with `run_experiment.py`. The conventions are those of the [catalogue contract](catalogue-report-contract.md) §3:
- canonical JSON: sorted keys, no insignificant whitespace, no trailing newline;
- integers, strings and booleans only, with no floats;
- artifacts sorted by `id`;
- every examined artifact listed, including abstentions;
- no pixels or file paths stored.

| Field | Content |
| --- | --- |
| `catalogueVersion` | `traceweave-image-catalogue-draft-1` |
| `profile` | `{configSha256, id, version}`, the extraction configuration digest from §2 |
| `extractionConfig` | the parsed extraction configuration. Re-serialized by §2, it MUST hash to `profile.configSha256` |
| `matchingConfigSha256` | digest of the matching configuration in force |
| `artifacts[]` | one entry per examined image |
| `artifacts[].id`, `sha256`, `byteLength` | opaque label; SHA-256 and length of the **original file bytes** |
| `artifacts[].decode` | `{status: ok, format, sourceMode, width, height, exifOrientation, iccPresent}`, or `{status: abstain, code}`. Width and height are those after orientation, which is the pixel coordinate system of any later region field |
| `artifacts[].pdq` | `{status: ok, hash (64 hex), quality}`, or `{status: abstain, code[, quality]}` |
| `artifacts[].iscc` | `{status: ok, hash (16 hex)}`, or `{status: abstain, code}` |

**Experiment-only fields.** `split`, `artifacts[].seed` and `artifacts[].pixelSha256` (SHA-256 of `"{W}x{H}x3:"` followed by the raw RGB array) exist only because the images are generated. A profile catalogue would not have them.

**Differences from the token catalogue contract, stated plainly:**
- There are no fingerprint lists, positions or spans. An image entry has one hash per extractor and no regions. The lane 08 region field maps to "whole image, pixel coordinates after orientation".
- Abstention is per extractor. A token entry has a single status.
- There is no schema file and no consumer-validation order like contract §3.6 yet. The harness writes the record but does not validate one it receives (OD-I6).
- Duplicate artifact bytes are not rejected yet. Contract OD-C9 forbids them.

**Privacy class: private.** The hashes are unkeyed. Anyone holding a catalogue can confirm a guessed image through `sha256`, or a near-copy through PDQ or ISCC distance. The audit's source X1 (§5.6) reports that PDQ itself leaks some identifying information under inversion. Keep catalogues local; a hosted by-content lookup discloses the query image (lane 10 shortlist row "Safety").

**C2PA mapping, for the later C2PA.1 gate.** Each hash would be a `c2pa.soft-binding` with the registered `io.iscc.v0` algorithm for ISCC. For PDQ, the third-party ids on the list are not ours to reuse, so that is open decision OD-I7. The artifact `sha256` corresponds to the mandatory hard binding.

## 9. What the profile does not claim

- **Crops.** Deep crops are not covered. Lane 10 F1 puts them out of PDQ's scope, and audit X1 measured PDQ at 0% Recall@1 for a crop keeping 70% of each side. The experiment's 50%-area crop keeps about 71% of each side. Crop results are recorded as limits.
- **Screenshots.** No screenshot claim. The experiment's "screenshot" is a defined border-and-rescale simulation, not a capture pipeline (protocol §4).
- **Geometry and regeneration.** No robustness to rotation outside the dihedral set (X1: a 15° rotation gives PDQ 0%), to perspective changes, to overlays, or to regeneration.
- **Adversarial robustness.** None. Black-box evasion of PDQ succeeded on 99.9% of attempts (lane 10 F2). Absence of a match never means "not derived".
- **Calibrated false-match rate.** None. A synthetic run bounds per-query rates only to about 3/n (protocol §7) and says nothing about natural images. On a natural-image product catalogue, X1 measured 1.00% per-query false bindings for PDQ at a strict threshold.
- **Ownership, authorship, licence or ancestry.** A match is the observation that two images' hashes are close. Which image came first, who made it, and whether it was copied all stay outside the profile.
- **Identity of a person or device**, and anything about signatures, timestamps or C2PA manifest validity.
- **Equivalence across decoders.** Hashes are defined for the pinned decoder. Another decoder can change bits (§7), so cross-decoder comparison needs its own measurement.

## 10. Open decisions

| ID | Question | Draft choice and reason |
| --- | --- | --- |
| OD-I1 | IMGF.2 wording for PDQ (§7) | Owner or coordinator: reword it to "port and reference agree exactly on identical pixels, and the published outputs lie within the vendor's stated tolerances", or add a C++ build to compare luma arrays |
| OD-I2 | ICC and colour management | Ignore and record. Converting to sRGB through LittleCMS adds a colour-engine pin, and the experiment has no ICC inputs |
| OD-I3 | Multi-frame files | Abstain. A first-frame policy needs a rule for which frame and for animated ISCC codes |
| OD-I4 | Pre-resize for PDQ | None (§4 step 2). Revisit only if speed requires it, and then pin the filter and target size |
| OD-I5 | Featureless images for ISCC | No abstention in draft-1. iscc-sdk has `is_featureless_image_code`; adopting it adds a rule to pin |
| OD-I6 | Catalogue schema and consumer validation order | Not written. Mirror catalogue contract §3.6 once the field list survives review |
| OD-I7 | PDQ soft-binding id in a C2PA export | Undecided; the C2PA.1 gate |
| OD-I8 | Thresholds | Experimental only. `T_pdq = 31` (vendor) and `T_iscc` from `selection-rule-1`. A profile value needs a calibration identifier and a natural-image measurement, which needs owner approval for any real image set |
| OD-I9 | Dihedral matching | Query-side 8 variants with min distance. It costs 8× the comparisons per entry. Dropping it gives up mirror and rotation recall in exchange for a smaller search |
| OD-I10 | Supported formats | JPEG and PNG only. WebP, HEIF and AVIF each add a decoder pin |
| OD-I11 | Platform-locked pins | macOS arm64 only. A second platform needs its own hashes, and the protocol treats that as a new version. Audit X1 reports PDQ and ISCC bit-identical across x86 and arm64 on 200 PNGs, but that is not our measurement |

## 11. IMGF.1 item map

IMGF.1 lists twelve items. Each is answered above, with 0 TBDs:

| Item | Section |
| --- | --- |
| Decoder and version | §1, §3 step 7 |
| EXIF orientation | §3 step 8 |
| Colour conversion | §3 step 10 |
| Alpha flattening | §3 step 9 |
| Multi-frame policy | §3 step 4 |
| Luminance formula | §4 step 1 (PDQ); §5 step 2 (ISCC) |
| Resize filter and size | PDQ: none, then Jarosz blur and decimation to 64×64 (§4 steps 2–4); ISCC: Pillow BICUBIC to 32×32 (§5 step 3) |
| Border crop | PDQ: none; ISCC: tolerant trim (§5 step 1) |
| Hash algorithm and bit length | PDQ 256 bits (§4); ISCC Image-Code v0, 64 bits (§5) |
| Quality abstention threshold | PDQ quality ≤ 49 abstains (§4 step 9); ISCC has none (§5 step 7) |
| Dihedral variants | §4 step 10; §5 step 8 |
| Distance metric | Hamming, minimum over the 8 query variants (§4 step 11; §5 step 9) |

Lane 10's list also names "vendor test vectors as conformance inputs"; see §7.
