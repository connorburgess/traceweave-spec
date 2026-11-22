# Draft extraction profile: still-image fingerprints (`traceweave-image-fingerprint`, `draft-2`)

Status: **draft for review, 2026-11-22.** Roadmap gate IMGF.1 ([roadmap](../../ROADMAP.md), later-profile table), with the reference-output evidence for IMGF.2. Evidence: [lane 10](../lanes/10-evidence-review.md) and its [report audit](../lanes/10-report-audit.md). The contract check that tests this profile is frozen separately in [image-experiment-protocol.md](image-experiment-protocol.md) (`e-img-f-2`). Code: [research/experiments/image-fingerprint/](../experiments/image-fingerprint/README.md).

**Versions.**
- `draft-1`, at commit `4714735`, was reviewed in [image-profile-protocol-review.md](../reviews/image-profile-protocol-review.md).
- `draft-2` removes the implementer discretion that review listed. It does this either by explicit formulas or by declaring an input out of scope (§3, §5).
- On the experiment's inputs (8-bit RGB PNG and baseline JPEG), draft-1 and draft-2 decode identically. The configuration digest changes.

This is research material, not a normative change. It does not modify `spec/`, `schemas/`, `profiles/` or `test-vectors/`. "MUST" describes what this draft proposes for an implementation claiming to follow it. No threshold here is calibrated. Every threshold is labelled **experimental** and carries no pass line.

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
| PDQ, fast path | `twimg/pdq_np.py`, a NumPy port that repeats the vendor's floating-point operations in the same order. It is a faithful copy, not an independent implementation | 30/30 vector images, and every run image (protocol V4) |
| ISCC | iscc-core 1.5.0, Apache-2.0, wheel SHA-256 `3bc10908…15f1` | `requirements.txt`; conformance data shipped in the wheel |
| ISCC normalization | re-implemented following iscc-sdk 0.9.7 `image_normalize` defaults, commit `cc11f771e4efbf0a600f196c7e9155b529ad7598` (Apache-2.0; its `LICENSE` is kept in `vendor/`; the commit ships no `NOTICE` file). Equality with iscc-sdk's own outputs is **not tested** | unit tests; iscc-sdk itself is not installed |
| NumPy | 2.5.5 (BSD-3-Clause and others) | `check_environment()` |

The complete package list with versions, licences and hashes is in the [experiment README](../experiments/image-fingerprint/README.md#environment). The pins are platform-locked to macOS arm64.

## 2. Configuration bytes

The extraction configuration and the matching configuration are separate records, as in the token baseline. Their exact bytes are `canonical(...)` in `twimg/profile.py`: sorted keys, no whitespace, one final LF.

| Record | SHA-256 of the exact bytes |
| --- | --- |
| Extraction configuration (`draft-2`) | `c740e92de69a47904fa81bb3614c086194717be856fa6a44d89ad6fdba3bb927` |
| Matching configuration | `fe3fa0395d3701fa5b1b55839063998eba528851d4f9e3dcaca62d3a0f6c97ac` |

Extraction configuration bytes:

```
{"alpha":"flatten-white-(c*a+255*(255-a)+127)//255","decoder":{"jpegDraft":false,"libjpegTurbo":"3.2.0","library":"Pillow","version":"13.0.0","zlib":"1.3.1.zlib-ng"},"exifOrientation":"apply-jpeg-only","formats":["JPEG","PNG"],"icc":"ignore-and-record","iscc":{"algorithm":"image-code-v0","bits":64,"dihedral":"catalogue-orig-query-8-on-32x32","implementation":"iscc-core-1.5.0","normalization":"following-iscc-sdk-0.9.7-cc11f771-pillow-13.0.0","qualityFloor":"none"},"jpeg":{"blockSmoothing":true,"cmykYcck":"abstain","dctMethod":"islow","fancyUpsampling":true,"outColorSpace":"rgb-or-grayscale"},"maxBytes":67108864,"maxPixels":50000000,"minSide":32,"modes":["L","LA","P","RGB","RGBA"],"multiFrame":"abstain","pdq":{"bits":256,"dihedral":"catalogue-orig-query-8","hexWordOrder":"vendor","implementation":"threatexchange-python-9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2","luma":"0.299R+0.587G+0.114B-float64","preResize":"none","qualityFloor":50},"png":{"bitDepth":"8; palette indices 1-8","colourChunks":"ignore-gAMA-cHRM-sRGB-iCCP"},"profile":"traceweave-image-fingerprint","profileVersion":"draft-2"}
```

Matching configuration bytes (`parameterStatus` is `experimental`):

```
{"distance":"hamming-min-over-query-dihedral","iscc":{"comparison":"le","threshold":7},"matching":"traceweave-image-nearest-draft-1","parameterStatus":"experimental","pdq":{"comparison":"le","threshold":31},"tie":"abstain-ambiguous"}
```

Changing any value is a new profile or matching version with a new digest.

## 3. Shared decode stage

Bytes in; an RGB array of 8-bit values, or an abstention. Implementation: `twimg/decode.py`. Steps in order; the first failure decides the code. After step 8, every conversion is a stated formula or table lookup. Pillow's `convert`, `paste` and `exif_transpose` are not used.

1. **Size.** More than 67,108,864 bytes: `input-too-large`.
2. **Open.** `PIL.Image.open` on the bytes. Any exception: `undecodable`.
3. **Format.** Pillow's detected format MUST be `JPEG` or `PNG`. Anything else, including GIF, WebP, TIFF and MPO: `unsupported-format`. The format comes from the file signature, never a file name.
4. **PNG bit depth.** For PNG, read the IHDR chunk directly from the bytes: bit depth is byte 24 and colour type is byte 25.
   - Accepted: bit depth 8 for colour types 0 (grey), 2 (RGB), 4 (grey + alpha) and 6 (RGBA); bit depth 1, 2, 4 or 8 for colour type 3 (palette indices).
   - Anything else gives `unsupported-bit-depth`. This covers 16-bit PNGs, which Pillow 13 opens silently as mode `RGB` (checked), and 1/2/4-bit grey, which Pillow rescales.
   - A PNG without a valid IHDR at offset 8 is `undecodable`.
5. **Multi-frame.** More than one frame, for example an animated PNG: `multi-frame`.
6. **Pixel count.** Width × height above 50,000,000: `too-many-pixels`.
7. **Mode.** Pillow's mode MUST be one of `L`, `LA`, `P`, `RGB`, `RGBA`. **Out of draft-2 scope, giving `unsupported-mode`:** `CMYK` and `YCCK` JPEGs (Adobe-inverted ones included), mode `YCbCr`, `1`, `PA`, and 16-bit or float modes.
8. **Decode.** `Image.load()`; any exception (for example a truncated file): `undecodable`.
   - **JPEG.** libjpeg-turbo 3.2.0, called by Pillow 13.0.0 with no draft and no scaling. Pillow then leaves libjpeg's defaults unchanged (Pillow `src/libImaging/JpegDecode.c` at tag 13.0.0 changes `dct_method` and `do_fancy_upsampling` only in draft mode). That means:
     - `JDCT_ISLOW` integer IDCT;
     - fancy upsampling on, so merged upsampling is not used;
     - block smoothing on, which matters for progressive files only.
   - **JPEG output colour space.** `JCS_RGB` for colour JPEGs, which libjpeg-turbo converts from YCbCr with its JFIF fixed-point transform. `JCS_GRAYSCALE` for grey JPEGs.
   - **PNG.** Decompressed by zlib-ng 1.3.1. PNG decoding is exact.
9. **EXIF orientation, JPEG only.** Tag 0x0112 is read from the JPEG APP1 Exif segment (Pillow `getexif()`). Values 2–8 are applied with the EXIF transposes:
   - 2 mirror left-right; 3 rotate 180°; 4 mirror top-bottom;
   - 5 transpose; 6 rotate 270° counter-clockwise; 7 transverse; 8 rotate 90° counter-clockwise.

   1, a missing tag or any other value is the identity. **For PNG, orientation is never applied**, whether it comes from an `eXIf` chunk or a raw-profile text chunk; the record shows 1. The recorded `exifOrientation` is the value applied. All later coordinates are those of the oriented image.
10. **To RGB.** Per mode, with integer arithmetic:
    - `RGB`: as decoded.
    - `L`: R = G = B = L.
    - `P`: palette lookup `RGB = palette[index]`. If the file has transparency (`tRNS`), the alpha for each index is the `tRNS` entry, or 255 past its end, and the result is flattened as below.
    - `RGBA`, `LA`, and `P` with transparency: flattened onto white per channel, `out = (c·a + 255·(255 − a) + 127) // 255`. This equals Pillow's `paste` with an alpha mask on 4,096 random pixels (unit test) and on 90,000 in a separate check.
11. **Colour management.** None.
    - The 8-bit values are used as decoded, treated as sRGB-encoded, with no linearization.
    - An embedded ICC profile (JPEG APP2 or PNG `iCCP`) is **ignored and recorded** (`iccPresent`).
    - PNG `gAMA`, `cHRM` and `sRGB` chunks are **ignored**.
12. **Minimum size.** If the shorter side of the oriented image is below 32 pixels: `too-small`.

The result is an H×W×3 array of `uint8`, row-major, channels R, G, B.

## 4. PDQ (main extractor)

Implementation: the vendored ThreatExchange Python code is the reference; `twimg/pdq_np.py` is the port used for speed. Both run on the same inputs and MUST agree bit for bit.

1. **Luminance.** Per pixel, in float64: `L = (0.299·R + 0.587·G) + 0.114·B`. This is the vendor's formula and its evaluation order. No gamma step is applied.
2. **No pre-resize.** The full oriented image is used. The vendor's Python tool first calls Pillow `thumbnail((512, 512))`, with JPEG draft decoding. That step is not part of this profile:
   - On the vendor's C++ vectors, full-resolution hashes are at least as close as thumbnail-path hashes on every one of the 8 images (distances 2–8 against 4–8; §7).
   - Draft decoding makes the decoded pixels depend on the target size.

   This choice was made from vendor vectors only.
3. **Blur.** Two X-then-Y passes of a 1-D box filter (Jarosz). The window along rows is `⌈cols/128⌉`, and along columns `⌈rows/128⌉`. The vendor's four-phase running sum is used, so edges are averaged over the in-image part of the window.
4. **Decimation to 64×64.** Cell `(i, j)` takes the blurred value at row `⌊(i + 0.5)·rows/64⌋` and column `⌊(j + 0.5)·cols/64⌋`.
5. **Quality.** Over the 64×64 grid, sum `|trunc((u − v)·100/255)|` for every vertical and every horizontal neighbour pair. Then `quality = min(100, ⌊sum/90⌋)`.
6. **DCT.** `D[i][j] = √(2/64)·cos(π/128·(i+1)·(2j+1))`, for `i` in 0..15 and `j` in 0..63. `B = D·A·Dᵀ` is 16×16, so the DC term is excluded. Sums are accumulated over `k` from 0 to 63, in order.
7. **Bits.** `m` is the median of the 256 values, found by the vendor's Torben routine. For 256 values it returns the 128th smallest; this was checked on 200 random matrices. Bit `16·i + j` is 1 if and only if `B[i][j] > m`.
8. **Output bytes.** 16 words of 16 bits. Word `w` holds bits `16w … 16w+15`, with bit `16w + k` as its bit `k`. The hex form is the words from `w = 15` down to `w = 0`, each as 4 lowercase hex digits: 64 characters, the vendor's `Hash256.toHexString`. The 32 output bytes are that hex decoded big-endian. The record also stores `quality`.
9. **Quality abstention.** Quality ≤ 49 gives `low-quality`, for an entry being enrolled and for a query. This is the vendor's starting recommendation, not calibrated.
10. **Dihedral variants.** A catalogue entry stores only the `orig` hash. A query computes all 8 variants from its `B` by the vendor's sign and transpose rules: `orig`, `rot90`, `rot180`, `rot270`, `flipx`, `flipy`, `flipp`, `flipm`. No minimal variant is ever selected. The distance to an entry is the **minimum over the 8 query variants**, so any calibration MUST count 8 comparisons per entry.
11. **Distance and threshold.** Hamming distance over 256 bits; within threshold when distance ≤ `T_pdq = 31` (experimental; vendor starting value).

## 5. ISCC Content-Code Image v0 (second extractor)

iscc-core does not normalize images; it leaves that to the caller. Steps 1–3 follow iscc-sdk 0.9.7's defaults. They are re-implemented, and equality with iscc-sdk outputs is untested: no published vector covers normalization. **The defining implementation of steps 2–3 is Pillow 13.0.0.** An implementation that does not reproduce those Pillow functions bit for bit is outside draft-2 scope for ISCC, and the profile claims no second ISCC implementation (IMGF.5 covers PDQ).

1. **Border trim**, the iscc-sdk `image_trim_tolerant` rule (tolerance 16, at most 16 passes). Each pass works as follows:
   - The reference is the pixel at (0, 0).
   - A pixel differs if any channel differs from the reference by more than 16.
   - The bounding box of differing pixels is computed with Pillow `point` and `getbbox`.
   - If there is no differing pixel, or the box is the whole image, trimming stops.
   - If the box would cut exactly one side, the pass is applied only when the box computed at tolerance 8 is identical; otherwise trimming stops.
   - Otherwise the image is cropped to the box.
2. **Grey.** `L = (19595·R + 38470·G + 7471·B + 32768) >> 16` (Pillow `convert("L")`). The formula is checked exactly by a unit test. It differs from PDQ's luma.
3. **Resize.** Pillow 13.0.0 `resize((32, 32), Image.Resampling.BICUBIC)` with `reducing_gap=None`. This is Pillow's separable convolution resampler: a cubic kernel with a = −0.5, support widened by the downscale factor, and Pillow's fixed-point coefficients. It is defined by that pinned implementation, not by a formula in this document.
4. **Pixels.** 1,024 `uint8` values, row-major.
5. **Hash.** iscc-core 1.5.0 `soft_hash_image_v0(pixels, bits=64)`:
   - a row DCT and then a column DCT (`iscc_core.alg_dct`; the compiled module and the pure-Python `dct.py` agree on all conformance vectors);
   - the top-left 8×8 block, DC included;
   - its `statistics.median` (the mean of the two middle values);
   - bit `n` is 1 if and only if value `n` is above the median, row-major, most significant bit first.
6. **Output bytes.** The 8-byte digest, recorded as 16 lowercase hex digits. The ISCC string (`ISCC:` followed by the base32 of header CONTENT, IMAGE, V0, 64 bits, plus the digest) can be derived from it and is never the comparison input.
7. **Quality.** ISCC defines none, so the profile has none. Featureless images give degenerate codes; an all-black image gives all-zero bits (OD-I5).
8. **Dihedral variants.** The 8 variants are taken on the 32×32 array: NumPy `rot90` by 1, 2 and 3; top-bottom and left-right mirrors; transpose; anti-transpose. The catalogue stores `orig`, and the query distance is the minimum over 8.
9. **Distance and threshold.** Hamming over 64 bits; within threshold when distance ≤ `T_iscc = 7`. That is PDQ's fraction scaled to 64 bits (⌊64·31/256⌋), experimental, and not an ISCC recommendation.

## 6. Matching and outcome classes

For each query and each extractor separately, against the enrolled entries of one catalogue:

| Level | Class | Codes | Meaning |
| --- | --- | --- | --- |
| Input | `abstain` | `input-too-large`, `undecodable`, `unsupported-format`, `unsupported-bit-depth`, `multi-frame`, `too-many-pixels`, `unsupported-mode`, `too-small` | Decode stage (§3); applies to both extractors |
| Extractor | `abstain` | `low-quality` | PDQ only, quality ≤ 49 |
| Query | `no-match` | `no-match` | No enrolled entry within threshold |
| Query | `match` | `match` | Exactly one entry has the smallest distance, and that distance is within threshold. The result names the entry and the distance |
| Query | `abstain` | `ambiguous` | Two or more entries share the smallest distance within threshold |

Every query result lists **all** entries within threshold, sorted by (distance, id), and their count. No list is truncated.

**Enrollment.** An entry that abstains is kept in the catalogue with its code. It is not enrolled for that extractor.

**Two extractors.** PDQ and ISCC results are reported side by side. There is **no combined verdict**. Distances are never added, multiplied or turned into a joint score (lane 08 rule).

**`no-match`** means "no entry within threshold under this configuration". It never means "not derived".

## 7. Reference-output conformance (IMGF.2 evidence)

Run by `check_vectors.py`; results in `vectors/check-results.json`. The inputs are 30 ThreatExchange `pdq/data` files pinned by commit, git blob id and SHA-256. The roadmap's reworded IMGF.2 has three parts: PDQ exact on identical pixels, PDQ within vendor tolerance, and the ISCC hash core.

| Check (IMGF.2 part) | Result |
| --- | --- |
| Vector files present and matching their pins | 30/30 |
| **PDQ exact:** NumPy port against the vendored Python reference on identical decoded pixels, all 8 dihedral hashes and quality | **30/30** |
| **PDQ tolerance:** profile path within 10 bits of the C++ `reg_test` output (8 vectors, all published quality 100) | **8/8**; distances 6, 8, 6, 2, 2, 8, 6, 6 |
| **PDQ tolerance:** published quality equal (C++ 8, Python README 12) | **8/8** and **12/12** |
| **PDQ tolerance:** profile path within 16 bits of the Python README outputs (12) and the unit-test outputs (18 usable; the 19th names `misc-images/b.jpg`, absent at the commit) | **12/12** (max 12) and **18/18** (max 12) |
| **ISCC:** Image-Code v0 against iscc-core `data.json` `gen_image_code_v0` (64, 128 and 256 bits) | **3/3** with the compiled DCT; 3/3 with the pure-Python DCT |
| Not required: exact equality with published PDQ hashes | C++ 0/8 (also 0/8 for the 8 dihedral hashes of `bridge-1`); README 4/12 on the profile path, 9/12 on the vendor thumbnail path; unit test 8/18 and 17/18 |

**What this shows.**
- The PDQ arithmetic is reproduced exactly, but only against the code the port was copied from. An independent check (a C++ build fed identical pixels) is IMGF.5.
- The vendor's own reference sets differ by up to 8 bits on identical files (`bridge-1-original.jpg`: C++ against Python, 8 bits), so exact equality with published hashes cannot be the criterion.
- ISCC's published vectors start from 32×32 pixels. They test the hash core, not §5 steps 1–3.

## 8. Records

### 8.1 Catalogue (`traceweave-image-catalogue-draft-1`)

The conventions are those of the [catalogue contract](catalogue-report-contract.md) §3:
- canonical JSON: sorted keys, no insignificant whitespace, no trailing newline;
- integers, strings and booleans only;
- artifacts sorted by `id`, unique ids and unique artifact bytes;
- every examined artifact listed, including abstentions;
- no pixels or file paths.

The harness's `validate_catalogue()` checks these rules.

| Field | Content |
| --- | --- |
| `catalogueVersion` | `traceweave-image-catalogue-draft-1` |
| `profile` | `{configSha256, id, version}` |
| `extractionConfig` | the parsed extraction configuration. Re-serialized by §2, it MUST hash to `profile.configSha256` |
| `matchingConfigSha256` | digest of the matching configuration in force |
| `artifacts[].id`, `sha256`, `byteLength` | opaque label; SHA-256 and length of the original file bytes |
| `artifacts[].decode` | `{status: ok, format, sourceMode, width, height, exifOrientation, iccPresent}`, or `{status: abstain, code}`. Width and height are after orientation |
| `artifacts[].pdq` | `{status: ok, hash (64 hex), quality}`, or `{status: abstain, code[, quality]}` |
| `artifacts[].iscc` | `{status: ok, hash (16 hex)}`, or `{status: abstain, code}` |

The fields `split`, `artifacts[].seed` and `artifacts[].pixelSha256` are experiment-only.

### 8.2 Query record

There is one canonical JSON line per query, with the closed field set of protocol §10, checked by `validate_query()`. Per extractor it holds the outcome, the matched entry and distance, the full list of entries within threshold and its count, all 8 query hashes, and the true-source and nearest-wrong distances for positives.

### 8.3 Mapping to the lane 08 shared record

| Lane 08 shared field | Image record |
| --- | --- |
| artifact digest and role | `sha256`; role = catalogue entry or query |
| profile, configuration and model digests | `profile.configSha256`, `matchingConfigSha256`; there is no model |
| region with coordinate system | whole image, in pixels at `width × height` after the stated orientation |
| raw value / decoded payload / statistic | raw value = the hash; there is no payload; statistic = the Hamming distance, with the threshold from the matching configuration |
| record resolution, signature validity, trust | outside this profile |
| confidence | empty: nothing is calibrated |

**Differences from the token catalogue contract.**
- There are no positions or spans; abstention is per extractor.
- There is no schema file and no consumer-validation order like contract §3.6 yet (OD-I6). `validate_catalogue()` is the harness's own check, not a published validator.

**Privacy class: private.** Hashes are unkeyed. A catalogue holder can confirm a guessed image by `sha256`, or a near-copy by distance. Keep catalogues local.

**C2PA mapping, for the later C2PA.1 gate.** ISCC maps to `c2pa.soft-binding` with the registered `io.iscc.v0`. The PDQ id is open (OD-I7). The artifact `sha256` corresponds to the mandatory hard binding.

## 9. What the profile does not claim

- **Crops.** Deep crops are not covered. Audit source X1, an author-run unreplicated preprint, measured PDQ at 0% Recall@1 for a crop keeping 70% of each side; that is not our measurement.
- **Screenshots.** No screenshot claim; X1 reports 0% for every hash on screenshot templates.
- **Geometry.** No rotation outside the dihedral set (X1: 15° gives PDQ 0%), no perspective change, no overlay and no regeneration.
- **Adversarial robustness.** None. Black-box evasion of PDQ succeeded on 99.9% of attempts (lane 10 F2).
- **Calibrated false-match rate.** None. X1 measured 1.00% per-query false bindings for PDQ on a natural-image product catalogue; that is not our measurement. A synthetic contract check bounds nothing about natural images.
- **Ownership, authorship, licence or ancestry.**
- **Equality across decoders, hosts, or with iscc-sdk's own ISCC outputs** (§5, §7). Cross-host is untested here; X1 reports PDQ and ISCC bit-identical across x86 and arm64 on 200 PNGs, which is not our measurement.

## 10. Open decisions

| ID | Question | Draft-2 position |
| --- | --- | --- |
| OD-I1 | IMGF.2 wording for PDQ | **Settled** by the coordinator's ROADMAP rewording (commit `fe14421`); §7 follows it |
| OD-I2 | ICC and colour management | Ignore and record, as before |
| OD-I3 | Multi-frame files | Abstain |
| OD-I4 | Pre-resize for PDQ | None |
| OD-I5 | Featureless images for ISCC | No abstention |
| OD-I6 | Catalogue schema and consumer validation order | Not written; the harness validator is the interim check |
| OD-I7 | PDQ soft-binding id in a C2PA export | Undecided (C2PA.1) |
| OD-I8 | Thresholds | Experimental only (`T_pdq = 31`, `T_iscc = 7`), with no pass line. A profile value needs a natural-image calibration and owner approval for real images |
| OD-I9 | Dihedral matching | Query-side 8 variants with min distance |
| OD-I10 | Formats | JPEG and PNG only |
| OD-I11 | Platform | macOS arm64 only. Cross-host is recorded as untested, which the reworded IMGF.4 accepts |
| OD-I12 (new) | Out-of-scope inputs (CMYK, YCCK and YCbCr JPEG; 16-bit and low-bit grey PNG; PNG orientation) | They abstain in draft-2. Supporting any of them needs a stated formula and a new version |
| OD-I13 (new) | ISCC normalization against iscc-sdk | Untested. Add a vector check against iscc-sdk 0.9.7 outputs before claiming SDK-equal codes |

## 11. IMGF.1 item map

IMGF.1 lists twelve items. Each is answered above, with 0 TBDs:

| Item | Section |
| --- | --- |
| Decoder and version | §1, §3 step 8 (libjpeg-turbo settings named) |
| EXIF orientation | §3 step 9 |
| Colour conversion | §3 steps 8, 10 and 11 |
| Alpha flattening | §3 step 10 (formula) |
| Multi-frame policy | §3 step 5 |
| Luminance formula | §4 step 1 (PDQ); §5 step 2 (ISCC) |
| Resize filter and size | PDQ: none, then blur and decimation to 64×64 (§4 steps 2–4); ISCC: Pillow BICUBIC to 32×32 (§5 step 3) |
| Border crop | PDQ: none; ISCC: tolerant trim (§5 step 1) |
| Hash algorithm and bit length | PDQ 256 bits (§4); ISCC Image-Code v0, 64 bits (§5) |
| Quality abstention threshold | PDQ ≤ 49 (§4 step 9); ISCC none (§5 step 7) |
| Dihedral variants | §4 step 10; §5 step 8 |
| Distance metric | Hamming, minimum over 8 query variants (§4 step 11; §5 step 9) |

The input bit-depth rule (§3 step 4) and the out-of-scope modes (§3 step 7) are additional to IMGF.1's list.
