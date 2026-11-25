# Lane 15: Audio and Video provenance and fingerprinting scoping note

Prepared 2026-11-25. Builds on [Lane 08](08-evidence-review.md) (`08-report-audit.md`), [Lane 10](10-evidence-review.md) (`10-report-audit.md`), [Lane 13](13-timestamp-evidence-review.md), the [06–08 checkpoint](../research-06-08-checkpoint.md), [profiles/README.md](../../profiles/README.md), the [M4 registration design](../drafts/registration-record.md), and the [C2PA 2.5 mapping draft](../drafts/c2pa-mapping.md).

**Scope boundary.** This is a non-normative scoping note. It changes no `spec/`, `schemas/`, or `profiles/` file, downloads no model weights or datasets, installs no media decoders, and runs no benchmark.

---

## 1. What works today via M4 registration (and optional C2PA link)

Traceweave's M4 registration design ([`registration-record.md`](../drafts/registration-record.md), draft-5) operates on **arbitrary exact byte sequences**, making it immediately applicable to audio and video assets without any media-specific decoder or fingerprint profile:

- **Exact-byte registration today.** Any audio or video file (WAV, FLAC, MP3, AAC, MP4, MOV, MKV, WebM) can be hashed by SHA-256 into an in-toto Statement v1 subject (`subject[0].digest.sha256`), paired with a fresh 256-bit nonce, a salted `possession` digest, and an optional private `catalogue` commitment (`sha256-salted-catalogue-v1`), signed via DSSE (Ed25519; Go/Rust interop verified in M4.1), and timestamped under independent roots (`RFC 3161` from two unrelated TSAs plus `OpenTimestamps`, §6 of the registration design).
- **Compact portable pointer (`tw1-`).** Frozen [design §9.1](../drafts/registration-record.md#91-text-reference-normative-frozen-2026-11-24) derives a 31-character Crockford base32 + Luhn mod 32 reference (`tw1-...`) from the first 130 bits of `statementSha256`. It can sit in show notes, podcast descriptions, video captions, or sidecar files alongside the full `statementSha256` (required when binding to a single record to avoid the 2^65 birthday-equivocation margin).
- **Optional C2PA 2.5 manifest link.** As specified in the [C2PA mapping §1.8](../drafts/c2pa-mapping.md#18-m4-registration-record--c2pa-sidecar-custom-assertion-orgtraceweaveregistration-link-fixture-f7), a sidecar C2PA manifest (`c2pa.hash.data`, whole-file, no exclusions) or an embedded ISOBMFF manifest (`c2pa.hash.bmff.v3` for MP4) can carry an `org.traceweave.registration-link` assertion (`tw1-` + `statementSha256` + `subjectSha256` + `relation`) in `gathered_assertions` (or `created_assertions` only when the signer is the registrant), or point to an external bundle via `c2pa.external-reference`.
  - **Strict boundaries:**
    1. Exact-byte registration (`relation: "same-bytes"`) breaks under any transcode, re-mux, trim, or metadata edit; derived or re-encoded files must declare `relation: "derived-copy"` or `"bytes-minus-exclusions"`, and comparison/similarity remains separate from registration ([core](../../spec/core.md)).
    2. Registration DSSE timestamps cannot be reused as C2PA `sigTst2` (which countersigns the C2PA claim signature), and C2PA compatibility remains **unclaimed** until `C2PA.2` passes ([attestations](../../spec/attestations.md)).
    3. A registration establishes only that someone holding those exact bytes signed/committed that digest by time `T`. It never proves authorship, originality, or first creation ([Lane 13](13-timestamp-evidence-review.md)).

---

## 2. Candidate open, offline, deterministic fingerprint methods

Unlike M4 registration, recognizing **re-encoded, trimmed, or re-packaged** audio and video requires deterministic extraction profiles (`AUD.*`, `VID.*`) that convert decoded media into compact, locally comparable hashes without uploading content.

### 2.1 Audio candidates

| Method | Mechanism & C2PA list note | Licence & dependencies | Offline / determinism | Transformation survival & limits |
| --- | --- | --- | --- | --- |
| **Chromaprint** (`acoustid/chromaprint`) | Downsamples audio to 11,025 Hz mono, bins spectrogram energy into 12 pitch-class (chroma) bands over overlapping windows (~0.37 s), emits 32-bit sub-fingerprints per frame. C2PA list has `com.originalpictures.chromaprint.1` (vendor-pinned; Traceweave would use its own config/namespace if ever exported) | Individual source files by Lukáš Lalinský are MIT, **but the library as a whole and `fpcalc` linked with FFmpeg are LGPL-2.1-or-later** (avoid GPL FFTW3; build against LGPL FFmpeg or Apple vDSP/KissFFT) | Fully local CPU; no neural weights; AcoustID web API is **not** used. Determinism requires pinning FFmpeg decode/resample flags and sample format before `chromaprint` | **High** survival under lossy codec/bitrate re-encodes (MP3/AAC) and crops ≥ 10–15 s with offset alignment; **poor** under playback speed/tempo shifts and **fails** pitch shifts (moves energy across chroma bins) and short excerpts (< 5 s). See [profiles/README.md](../../profiles/README.md) and X1 ([Lane 10 audit](10-report-audit.md): Chromaprint 67% vs AudioSeal 24% in X1's author setup) |
| **Audfprint** (`dpwe/audfprint`) | Spectral peak-pair (constellation landmark) hashing with time-delta offsets; offset-invariant index matching for short clips | **MIT** (`dpwe/audfprint`); relies on local audio decode (FFmpeg/PCM) | Fully local CPU; no weights; deterministic given pinned PCM decode and FFT/peak parameters | Better localization of **short excerpts** and moderate background noise than Chromaprint; higher hash volume per second; still sensitive to pitch/tempo warps unless multi-rate searched (multiplying false-alarm trials) |

### 2.2 Video candidates

| Method | Mechanism & C2PA list note | Licence & dependencies | Offline / determinism | Transformation survival & limits |
| --- | --- | --- | --- | --- |
| **vPDQ** (`meta/ThreatExchange`) | Extracts frames and computes 256-bit PDQ hashes + 0–100 quality scores per sampled frame with timestamps; supports sequence/subsequence Hamming matching. C2PA list has `com.originalpictures.vpdq.1` (vendor-pinned) | **BSD-2-Clause** (ThreatExchange); relies on FFmpeg for frame decode/sampling (keep FFmpeg LGPL-2.1+, no `--enable-gpl`/`--enable-nonfree`) | Local CPU; no weights; shares PDQ arithmetic already validated in `IMGF.2` (`e-img-f-2`). **Caveat:** video YUV→RGB decode can differ across hosts (X1 §4.6 Table 10 observed cross-host flips in H.264 video decode) | Handles **clipped excerpts inside longer videos**, frame-rate resampling, transcodes, and dihedral flips; **fails** deep spatial crops (70%-side crop drops PDQ to 0% in X1), non-dihedral rotations (15° → 0%), and heavy UI overlays |
| **TMK+PDQF** (`meta/ThreatExchange`) | Temporal Match Kernel pooling over PDQ frame features into a fixed-size video signature (~256 KB). C2PA list has `com.originalpictures.tmk-pdqf.1` (vendor-pinned) | **BSD-2-Clause** (ThreatExchange); relies on FFmpeg frame decode | Local CPU; no weights; deterministic given pinned FFmpeg decode + sampling rate | Optimized for **whole-video** near-duplicate detection across re-encodes, resolution scaling, and minor head/tail trims; **poor** at localizing short clips inside longer unrelated videos |
| **ISCC Video-Code v0** (`iscc-core`, ISO 24138:2024) | `soft_hash_video_v0` sums 380-integer MPEG-7 frame signatures across the video and applies Winner-Take-All (WTA) hashing to emit a 64–256 bit code (`io.iscc.v0` family) | `iscc-core` is **Apache-2.0**; MPEG-7 signature extraction uses FFmpeg's `signature` filter (build configuration and LGPL-2.1+ compliance must be verified on pinned FFmpeg) | Local CPU; no weights; deterministic only when FFmpeg `signature` filter inputs are pinned | Whole-video global similarity only (no subsequence/clip localization). Exporting to C2PA `io.iscc.v0` additionally requires 256-bit units + Data-Code + Instance-Code per IEP-0020 ([C2PA mapping §2.2](../drafts/c2pa-mapping.md#22-iscc-what-ioisccv0-requires)) |

### 2.3 Shared determinism bottleneck: demuxing and software decoding

Still images in [`extraction-profile-image.md`](../drafts/extraction-profile-image.md) §3 required pinning `libjpeg-turbo` settings, `EXIF` orientation, and alpha flattening to keep two runs deterministic. Audio and video containers introduce much larger cross-implementation surfaces: container demuxers, variable frame rates / B-frame PTS rounding, audio sample-format resampling (`swresample`), and YUV-to-RGB colour matrices (`BT.601`/`BT.709`, `swscale`). In X1 §4.6 Table 10 ([Lane 10 audit](10-report-audit.md)), H.264 YUV→RGB decoding differences between x86 and ARM caused bit flips in video even where still-image PNG hashes (`PDQ` and `ISCC`) were 200/200 bit-identical. Any `AUD.*` or `VID.*` profile MUST therefore pin:
1. A single software-only FFmpeg build (explicitly excluding hardware decoders and `--enable-gpl`/`--enable-nonfree` if redistribution matters);
2. Exact PCM output format (sample rate, mono downmix weights, `s16le`/`f32le` rounding) for audio, or exact pixel format (`rgb24`), colour-space conversion flags, and frame-sampling schedule for video; and
3. Separation of decoder conformance (pinned binary output on container files) from hash-core conformance (bit-identical hashes on identical decoded PCM/RGB frames, mirroring `IMGF.2` and `IMGF.5`).

---

## 3. Proposed gates (`AUD.1–3`, `VID.1–3`)

Following [ROADMAP.md](../../ROADMAP.md) gate conventions (**E** = engineering, **R** = research question; **S** = spec repo, **I** = implementation repo), audio and video profiles stay **unstarted** until prioritized after core M3 and owner clearance of any real media sets:

| ID | Type | Proposed verifiable criterion | Owner |
| --- | --- | --- | --- |
| **AUD.1** | E | Audio extraction profile specifies with 0 TBDs: pinned software decoder/FFmpeg version and LGPL build boundary, container/codec allowlist, mono/sample-rate downmix formula, minimum duration and silence abstention rules, window/hop framing, fingerprint serialization (Chromaprint and/or landmark baseline), and matching metric. | S |
| **AUD.2** | E | Under network denial on synthetic and CC-licensed audio fixtures, two runs produce byte-identical canonical catalogues/reports, and two implementations (or an independent hash-core check) reproduce identical sub-fingerprints on identical decoded PCM frames. | I |
| **AUD.3** | R | Held-out audio benchmark (owner-approved if non-synthetic) reports recall with explicit denominators across codec/bitrate re-encode, excerpt crops, speed/pitch changes, and unrelated/same-composition controls, plus per-query false-match counts at the frozen threshold (no pass line before M3-style calibration). | S+I |
| **VID.1** | E | Video extraction profile specifies with 0 TBDs: pinned software FFmpeg build and LGPL boundary, container/codec allowlist, YUV→RGB matrix/chroma flags, frame-sampling/timestamp policy, minimum duration/resolution abstention, per-frame/temporal hash (e.g. vPDQ / TMK+PDQF), and clip vs whole-video matching rule. | S |
| **VID.2** | E | Under network denial on synthetic video fixtures, two runs produce byte-identical canonical catalogues/reports, and cross-host (x86_64 vs arm64) YUV→RGB + hash divergence is explicitly measured and bounded separately from hash-core agreement. | I |
| **VID.3** | R | Held-out video benchmark (owner-approved if non-synthetic) reports recall with explicit denominators across transcode/bitrate, resize, clip-in-host localization, dihedral flip/letterbox, and spatial crop, plus unrelated/independent-shot controls and per-query false-match counts at the frozen threshold. | S+I |

---

## 4. Boundary on audio and video embedded watermarks

Embedded marks in audio ([Lane 08](08-evidence-review.md): **WavMark**, MIT code, Hugging Face checkpoint `M4869/WavMark`; [08 audit](08-report-audit.md): **AudioSeal**, MIT code `1496f76`) and video (**VideoSeal** / **PixelSeal**, MIT code/README weights `f12875a9`, SA-1B owner note in [Lane 12](12-image-mark-licences.md)) remain **finding aids only, never origin proof**:

1. **Keyless copying and transplant.** Just as `e-img-m-2` demonstrated `100/100` keyless re-embedding and `82–90/100` residual transplant on still images ([recheck](../reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2)), public/unkeyed audio and video decoders and encoders allow anyone to decode raw bits or copy a watermark into unrelated media without holding the creator's key.
2. **Capacity and false-accept limits.**
   - **AudioSeal** embeds 16-bit payloads (`2^-16 ≈ 1.53 × 10^-5` analytic random agreement), which **cannot** reach a `10^-6` per-comparison false-accept bound even for a single key and single window ([Lane 10 audit](10-report-audit.md)), and degrades linearly across catalogue entries `N`, keys `N_K`, and searched time windows `W`.
   - **WavMark** uses 32 raw bits per 1-second block (default 16 pattern + 16 payload bits; paper 10 + 22) and its README `1/2^16` assertion is a pattern-match heuristic rather than a calibrated full-file search error rate ([Lane 08](08-evidence-review.md)).
   - **Fragility.** Audio marks collapse or degrade under time-scale/speed shifts (`WavMark` 0.50 at 1.25× speed, [08 checkpoint](../research-06-08-checkpoint.md)) and generative/codec re-encoding; video marks face frame-dropping, spatial crop, and cross-host YUV→RGB bit flips (X1 Table 10).
3. **Mandatory record separation.** If any audio or video embedded-mark study is later authorized by the owner (covering weight downloads, model licences, SA-1B/training terms, and licensed test media), detections MUST follow the [IMG.5 finding-aid pattern](../drafts/image-mark-finding-aid.md) ([`image-mark-finding-aid.schema.json`](../../schemas/image-mark-finding-aid.schema.json)):
   - Record `provesOrigin: false`, `provesAuthorship: false`, `keylessCopyPossible: true`, and `confidence: null` in a profile-specific finding-aid record;
   - Pin all model digests, tested bit positions, statistic + `n`, threshold basis + search scope, key/derivation ID, and embedding distortion/quality (`SI-SNR`/`PESQ` or `PSNR`/`VMAF` floor); and
   - Point to a separate M4 registration record (`tw1-` reference + `statementSha256`) for any signed, timestamped existence claim.

---

## 5. Validation and handoff

This note synthesizes existing primary-source reviews in [Lane 08](08-evidence-review.md), [08 audit](08-report-audit.md), [Lane 10](10-evidence-review.md), [10 audit](10-report-audit.md), [Lane 12](12-image-mark-licences.md), and [Lane 13](13-timestamp-evidence-review.md), plus repository documentation for Chromaprint (`acoustid/chromaprint`, LGPL-2.1+ with FFmpeg), Audfprint (`dpwe/audfprint`, MIT), ThreatExchange `TMK+PDQF`/`vPDQ` (BSD-2-Clause), and `iscc-core` `soft_hash_video_v0` (Apache-2.0). No audio or video packages were installed, no media assets were acquired, and no experiments were run. **Owner-gated next steps:** prioritizing `AUD.1`/`VID.1` relative to M3/C2PA.2, approving any non-synthetic audio/video corpus, and approving any FFmpeg/decoder environment or model-weight download.
