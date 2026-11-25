# Independent non-author review: `media-c2pa-av` (`5a224bd`)

Reviewed 2026-11-25 against branch `media-c2pa-av` at commit `5a224bd` (branched from `roadmap-v2` at `7941c47`). I wrote none of the reviewed work.

**Verdict: `merge after fixes`.**

The three deliverables (`IMG.5` finding-aid schema/fixtures, `C2PA.1–C2PA.3` registration-link mapping/fixtures, and Lane 15 audio/video scoping) are well-structured and cleanly isolated from promoted `spec/` and `profiles/` contracts, and all existing checkers and tests pass. However, adversarial testing surfaced **two blocking items** that should be fixed before merging into `roadmap-v2`:

1. **B1 (`IMG.5` non-origin boundary bypass in free-text fields + missing semantic invariants in `check_finding_aid.py`).** Structural non-origin fields (`provesOrigin: false`, `provesAuthorship: false`, `keylessCopyPossible: true`, `decodedPayload.decisive: false`, `confidence: null`) are locked down by the schema, and malformed/mismatched `tw1-` references are rejected. However, free-text fields (`registrationLink.note`, `threshold.basis`, `testedBits.excludedNote`, `threshold.calibrationId`) accept explicit origin/authorship-claim wording (`"Proves origin and authorship of creator."`) without rejection in `check_finding_aid.py` or a negative fixture, and three semantic cross-field invariants are unchecked.
2. **B2 (`15-audio-video-scoping.md` FFmpeg `signature` filter licence conflict).** Section 2.2 classifies ISCC Video-Code v0 (`iscc-core`, Apache-2.0) as using FFmpeg's `signature` filter with "build configuration and LGPL-2.1+ compliance must be verified on pinned FFmpeg", while §2.3 requires "excluding ... `--enable-gpl`/`--enable-nonfree` if redistribution matters". Upstream FFmpeg's `signature` filter (`libavfilter/vf_signature.c`) is **GPL-2.0+** and requires `--enable-gpl`; it is not present in an LGPL-only FFmpeg build.

---

## 1. Checks executed

The worktree at `media-c2pa-av` has no local `.venv`, so checks ran using the sibling checkout's Python 3.12 virtual environment (`../traceweave-spec/.venv/bin/python`). All repository checkers resolve paths via `__file__` relative to the worktree root.

| Check | Outcome | Notes |
| --- | --- | --- |
| `check_finding_aid.py` (`-I`) | **PASS** (exit 0) | `5 valid, 18 invalid, 17/17 required-field deletions rejected` |
| `check_fixtures.py --verbose` (`-I`) | **PASS** (exit 0) | `7 fixtures, 22 negative fixtures, mapping-document drift 0; all as expected` |
| `tools/validate.py` | **PASS** (exit 0) | Includes `IMG.5` and `C2PA.1/C2PA.3` in `VECTOR_CHECKERS` |
| `tools/validate.py --links-all` | **PASS** (exit 0) | All local Markdown links valid |
| `python -m unittest discover -s tests -v` | **PASS** (exit 0) | `Ran 10 tests in 15.798s`, `OK` (includes `test_image_mark_finding_aid_schema_and_boundary`) |
| `tools/check_hygiene.py` | **PASS** (exit 0) | Tree clean |
| `tools/check_hygiene.py --messages 7941c47..5a224bd` | **PASS** (exit 0) | Commit message and tree clean |

---

## 2. Track-by-track review

### 2.1 `IMG.5`: image-mark finding-aid record

Reviewed [schemas/image-mark-finding-aid.schema.json](../../schemas/image-mark-finding-aid.schema.json), [image-mark-finding-aid.md](../drafts/image-mark-finding-aid.md), [check_finding_aid.py](../drafts/image-mark-finding-aid/check_finding_aid.py), and [fixtures.json](../drafts/image-mark-finding-aid/fixtures.json) against [ROADMAP.md](../../ROADMAP.md) (`IMG.5`), [image-mark-protocol.md §12](../drafts/image-mark-protocol.md#12-records-and-the-shared-evidence-record-img5), [image-mark-protocol-review.md](../reviews/image-mark-protocol-review.md), and [e-img-m-2](../experiments/image-mark/results/e-img-m-2/RESULTS.md).

- **Six detection-record fields:** All six missing fields from Lane 08 / `e-img-m-2` are cleanly hosted outside the generic container:
  1. Model digests -> `/carrier` (`algorithm`, `variant`, `codeCommit`, `models[]` with `id`, `role`, `sha256`; `check_finding_aid.py` requires non-empty `models` for `trustmark`/`pixelseal`).
  2. Statistic and `n` -> `/statistic` (`name: "expected-payload-agreement"`, `n`, `matchedBits`, `acceptedEntries[]`, optional `maxOtherBits`/`maxOtherEntryId`).
  3. Threshold basis -> `/threshold` (`k`, `basis`, `perComparisonFalseAcceptBound`, `calibrationId`, `searchScope`).
  4. Key and payload-derivation id -> `/keyReference` (`keyId`, `derivationId`, `additionalProperties: false`).
  5. Embedding quality -> `/embeddingQuality` (`measured` with `psnrDb`, `floorDb`, `belowFloor`, digests; or `unavailable` with `reason` and `floorDb`).
  6. Tested bit positions -> `/testedBits` (`basis: "direct-keyed-output"`, `[start, end)`, `count`, `rawBitCount`, `excludedNote`).
- **Committed `e-img-m-2` data cross-check:** `protocolSha256` (`cba36673…4110`), model weights SHA-256s in [weights.json](../experiments/image-mark/weights.json), and `tm:m2000000:jpeg90`, `tm:m2000000` (entry), and `tm:m2000000:cover` hashes/counts match `e-img-m-2/run-1/{entries,queries,summary}`. For `ps:m2000000:clean`, `queries.jsonl` recorded 256 bits (`b6c9…`, since `twmark/schemes.py` slices `preds[0, 1:]`), while `fixtures.json` prepends a `"1"` bit (`1b6c…`, `bitCount: 257`) to illustrate `testedBits` `[1, 257)` excluding `preds[0, 0]`.
- **Adversarial probes run against schema + `check_finding_aid.py`:**
  - `findingAidBoundary.provesOrigin: true`, `provesAuthorship: true`, `keylessCopyPossible: false`, `role: "origin-proof"`, `decodedPayload.decisive: true`, `confidence: 0.99`, and extra `keyReference.keyHex`: **all rejected** by schema (`ValidationError`).
  - Malformed `tw1-` references (`tw2-` prefix, short length, look-alike `I`, lowercase, corrupted Luhn mod 32 check char): **all rejected** by schema regex and `check_finding_aid.py` (`reference-shape`, `reference-check`).
  - Mismatched `statementSha256` (zeroed or mismatched against `textReference`): **rejected** by `check_finding_aid.py` (`reference-mismatch`).
  - **Bypass found (B1):**
    1. Putting `"Proves origin and authorship of creator."` in `registrationLink.note`, `"Proves origin with 99.9% certainty"` in `threshold.basis`, or `"Proves authorship"` in `testedBits.excludedNote` **passes both schema and `check_finding_aid.py`**.
    2. An `abstain` / `too-small` record carrying non-empty `statistic.acceptedEntries` **passes** both schema and `check_finding_aid.py`.
    3. A `match` record with `statistic.matchedBits = 0` (disagreeing with `acceptedEntries[0].matchedBits = 61`) **passes** both schema and `check_finding_aid.py`.
    4. A `region` with `scope: "whole-image"` and partial coordinates (`x: 10, width: 100`) **passes** both schema and `check_finding_aid.py`.
  - **Minor fixture note:** `valid-decode-abstain-too-small` sets `artifact.role: "query"` alongside `embeddingQuality.reason: "abstain-before-embed"`, whereas a query record would ordinarily carry `reason: "no-cover-reference"`.

### 2.2 `C2PA.1–C2PA.3`: mapping, registration link, and fixtures

Reviewed [c2pa-mapping.md](../drafts/c2pa-mapping.md), [c2pa-fixtures/README.md](../drafts/c2pa-fixtures/README.md), [mapping-rules.json](../drafts/c2pa-fixtures/mapping-rules.json), [build_fixtures.py](../drafts/c2pa-fixtures/build_fixtures.py), [check_fixtures.py](../drafts/c2pa-fixtures/check_fixtures.py), `f6-token-soft-binding.json`, `f7-sidecar-registration-link.json`, the 4 new `neg-reg-*` fixtures, [docs/sources.md](../../docs/sources.md), [spec/attestations.md](../../spec/attestations.md), and [README.md](../../README.md).

- **Version pins:** Pinned to **C2PA Technical Specification 2.5** (`C1`, October 2026) and **Soft Binding API 2.5.0** (`C2`, OpenAPI `info.version` 2.5.0), with `C3` (2.2 guidance), `C4` (79-entry list at `b445c12f`), `C5` (IEP-0020), `C6` (in-toto/DSSE), `C7` (`c2pa-rs` `c2pa-v0.92.2`), and `C8` (RFC 8949/9052).
- **`org.traceweave.registration-link` (`f7-sidecar-registration-link.json`, §1.8):**
  - Uses owned `org.traceweave.*` namespace (`traceweave.org`), binds both `tw1-7WR8Y61HYTR7RJE0NN5W52C8TAN` and full `statementSha256` (`3f308f18…c93e`), verifies `subjectSha256 == c2pa.hash.data/hash` (no exclusions) for `relation: "same-bytes"`, keeps `claims.createdAt` as `lossy`, `notShown` as `opaque`, private `nonce`/`possession`/`catalogue` as `unmapped` (never disclosed), and `timeEvidenceSummary` as `conflicting` (cannot be reused as C2PA `sigTst2`). Placed in `gathered_assertions` when `signerIsRegistrant` is `false`.
  - All `sourceRef` SHA-256 digests match the current repository files, including rebuilt `f6-token-soft-binding.json` (`79ce61ab…0fa0` for `test-vectors/matching/matching.json`).
  - All 4 new negative fixtures (`neg-reg-created-attribution`, `neg-reg-same-bytes-exclusions`, `neg-reg-tw1-bad-check`, `neg-reg-tw1-statement-mismatch`) trigger their exact expected failure codes, and `doc_drift` is `0`.
- **`C2PA.3` (no premature compatibility claim):**
  - Confirmed `README.md`, `spec/attestations.md`, and `docs/sources.md` make no compatibility or interoperability claim.
  - **Minor wording inaccuracy (A1):** [ROADMAP.md](../../ROADMAP.md) (`C2PA.3`) and [c2pa-mapping.md §9](../drafts/c2pa-mapping.md#9-gate-status) write that `check_fixtures.py` enforces `claimWordsPattern` inside `tools/validate.py`. In fact, `check_fixtures.py` enforces `claimWordsPattern` on the C2PA JSON fixtures only; it does not scan `README.md`, `spec/attestations.md`, or `docs/sources.md`, and `claimWordsPattern` omits `"supports C2PA"` / `"works with Content Credentials"` listed as forbidden in §7.

### 2.3 Lane 15: audio and video scoping

Reviewed [15-audio-video-scoping.md](../lanes/15-audio-video-scoping.md) and [profiles/README.md](../../profiles/README.md) against [08-evidence-review.md](../lanes/08-evidence-review.md), [08-report-audit.md](../lanes/08-report-audit.md), [10-report-audit.md](../lanes/10-report-audit.md), [12-image-mark-licences.md](../lanes/12-image-mark-licences.md), and [13-timestamp-evidence-review.md](../lanes/13-timestamp-evidence-review.md).

- **Licences & offline feasibility:**
  - `acoustid/chromaprint`: accurately distinguishes MIT on individual source files by Lukáš Lalinský from **LGPL-2.1-or-later** for the library/`fpcalc` with FFmpeg, warns against GPL FFTW3 (prefer LGPL FFmpeg or Apple vDSP / KissFFT), and notes offline/resampling determinism and pitch/tempo/short-clip limits.
  - `dpwe/audfprint`: **MIT**, offline CPU, accurate on short-clip landmark localization vs multi-rate false-alarm multiplication.
  - `meta/ThreatExchange` `vPDQ` and `TMK+PDQF`: **BSD-2-Clause**, LGPL-2.1+ FFmpeg frame decoding, accurate on cross-host H.264 YUV→RGB bit flips (X1 §4.6 Table 10), 70%-side crop collapse, and clip vs whole-video scope.
  - **`iscc-core` `soft_hash_video_v0` (B2):** `iscc-core` itself is **Apache-2.0**, and IEP-0020 requirements are cited accurately, **but** FFmpeg's `signature` filter (`libavfilter/vf_signature.c`) is **GPL-2.0+** and requires `--enable-gpl`. It cannot be built into an LGPL-only FFmpeg binary (`--enable-gpl` excluded in §2.3 item 1).
- **Watermark honesty:** Correctly classifies **WavMark** (MIT code, HF checkpoint), **AudioSeal** (MIT code `1496f76`; 16-bit payload `2^-16 ≈ 1.53 × 10^-5` cannot reach `10^-6`), and **VideoSeal / PixelSeal** (MIT code/README weights `f12875a9`, SA-1B owner note) as **finding aids only, never origin proof**, preserving the IMG.5 finding-aid record separation and M4 `tw1-` registration pointer.
- **Proposed gates (`AUD.1–3`, `VID.1–3`):** Appropriately kept non-counted and unstarted pending M3/owner clearance, with explicit cross-host YUV→RGB divergence bounding (`VID.2`) and no pass line before calibration (`AUD.3`, `VID.3`).

---

## 3. Required and advisory fixes before merge

### Blocking

1. **B1 (`check_finding_aid.py` & `fixtures.json`):**
   - Enforce an origin/authorship-claim wording check across free-text fields (`registrationLink.note`, `threshold.basis`, `testedBits.excludedNote`, `threshold.calibrationId`) in `check_finding_aid.py` (analogous to `claimWordsPattern` in `c2pa-fixtures/check_fixtures.py` and the §11 deny-list in `registration-record.md`), and add at least one negative fixture testing rejection of origin-claim wording in free text.
   - Tighten `semantic_errors()` in `check_finding_aid.py`: (a) require `acceptedEntries == []` and `matchedBits is None` when `outcome["class"] == "abstain"` and `decode["status"] == "abstain"`; (b) when `outcome["class"] == "match"`, require `stat["matchedBits"] == accepted[0]["matchedBits"]`; and (c) when `region` is present with `scope == "whole-image"`, require `x == 0`, `y == 0`, `width == imageWidth`, and `height == imageHeight`.
2. **B2 (`research/lanes/15-audio-video-scoping.md`):**
   - Correct the `ISCC Video-Code v0` row (§2.2) and §2.3 to state explicitly that FFmpeg's MPEG-7 `signature` filter (`vf_signature`) is **GPL-2.0+** and requires `--enable-gpl`, so it is unavailable in an LGPL-only FFmpeg build (if redistribution under LGPL/permissive terms is required, it must either be excluded or isolated as a GPL-licensed subprocess).

### Advisory (non-blocking)

- **A1 (`ROADMAP.md` `C2PA.3`, `c2pa-mapping.md` §9, `mapping-rules.json`):** Clarify that `check_fixtures.py` enforces `claimWordsPattern` on the C2PA JSON fixtures (not on `README.md`, which was verified by inspection)—or add an automated check over `README.md` and include `"supports C2PA"` / `"works with Content Credentials"` from §7 in `claimWordsPattern`.
- **A2 (`fixtures.json`):** In `valid-decode-abstain-too-small`, align `embeddingQuality.reason` (`"no-cover-reference"` for `role: "query"`, or switch `role` to `"marked-entry"` if testing pre-embed abstention), and optionally note in `fixtures.json` / `image-mark-finding-aid.md` that `valid-pixelseal-clean-no-registration` includes the unkeyed detection bit `preds[0, 0]` (`257` bits) whereas `e-img-m-2/queries.jsonl` logged only the `256` tested bits (`preds[0, 1:]`).
- **A3 (`ROADMAP.md` gate status):** Once B1 and B2 are addressed and confirmed, `IMG.5` and `C2PA.1` (subject to owner decision D1 on C2PA 2.5 vs 2.4) can be updated with this review reference.

---

## 4. Confirmation pass (`a4ea8d4`)

Re-checked 2026-11-25 against commit `a4ea8d4` on `media-c2pa-av`.

**Verdict: `merge`.** All blocking items (`B1`, `B2`) and advisory notes (`A1`–`A3`) are resolved cleanly.

- **B1 resolved ([check_finding_aid.py](../drafts/image-mark-finding-aid/check_finding_aid.py), [fixtures.json](../drafts/image-mark-finding-aid/fixtures.json)):** `ORIGIN_CLAIM_TEXT` now rejects origin, authorship, ownership, creation, copyright, and proof wording across `testedBits.excludedNote`, `threshold.basis`, `threshold.calibrationId`, and `registrationLink.note`; `semantic_errors()` enforces empty `acceptedEntries` and `matchedBits is None` on decode abstention, `statistic.matchedBits == acceptedEntries[0].matchedBits` on `match`, and full-image bounds (`x == 0`, `y == 0`, `width == imageWidth`, `height == imageHeight`) when `region.scope == "whole-image"`. Six new negative fixtures exercise every added rule (`5 valid, 24 invalid, 17/17 required-field deletions rejected`).
- **B2 resolved ([15-audio-video-scoping.md](../lanes/15-audio-video-scoping.md)):** Sections 2.2 and 2.3 now state accurately that FFmpeg's MPEG-7 `signature` filter (`libavfilter/vf_signature.c`) is **GPL-2.0+** and requires `--enable-gpl`, so it is unavailable in an LGPL-only FFmpeg build and must be omitted from an LGPL bundle or isolated behind a separate GPL-licensed subprocess boundary.
- **A1–A3 resolved:** [mapping-rules.json](../drafts/c2pa-fixtures/mapping-rules.json) extends `claimWordsPattern` with `supports\s+c2pa` and `works\s+with\s+content\s+credentials`; [ROADMAP.md](../../ROADMAP.md) (`C2PA.3`) and [c2pa-mapping.md §9](../drafts/c2pa-mapping.md#9-gate-status) distinguish prose inspection from fixture-level `claimWordsPattern` enforcement; [fixtures.json](../drafts/image-mark-finding-aid/fixtures.json) and [image-mark-finding-aid.md](../drafts/image-mark-finding-aid.md) align `valid-decode-abstain-too-small` (`reason: "no-cover-reference"`) and document the 257-bit PixelSeal decoder illustration against `queries.jsonl`.
- **Re-run checks on `a4ea8d4`:** `check_finding_aid.py` (`5 valid, 24 invalid, 17/17 required-field deletions rejected`), `check_fixtures.py` (`7 fixtures, 22 negative fixtures, mapping-document drift 0`), `tools/validate.py`, `tools/validate.py --links-all`, `unittest discover -s tests -v` (`10 tests, OK`), and `tools/check_hygiene.py` all passed (exit 0) using the sibling checkout's `.venv/bin/python`.

