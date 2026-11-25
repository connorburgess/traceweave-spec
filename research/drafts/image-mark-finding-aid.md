# Draft resolution for IMG.5: profile-specific image-mark finding-aid record (`traceweave-image-mark-finding-aid-draft-1`)

Status: **draft proposal for review, 2026-11-25.** Resolves roadmap gate [IMG.5](../../ROADMAP.md#later-profiles-and-sequence) under [CONTRIBUTING](../../CONTRIBUTING.md) (`schemas/`, draft design note, positive and negative fixtures, and checker wired into `tools/validate.py`). Does not alter `spec/`, `profiles/`, or any promoted `M1`/`M2` contract.

## 1. Decision: profile-specific finding-aid record, not a Lane 08 container extension

[Lane 08](../lanes/08-evidence-review.md#shared-interface-boundary-proposal-only) proposed a minimal cross-media interface boundary, and [protocol `e-img-m-2`](image-mark-protocol.md#12-records-and-the-shared-evidence-record-img5) plus its [non-author review](../reviews/image-mark-protocol-review.md) identified **six fields** present in image-mark detection that have no home in the generic container or in the image-fingerprint catalogue ([`extraction-profile-image.md`](extraction-profile-image.md#83-mapping-to-the-lane-08-shared-record)):

1. **Model digests** (weights and model configs pinned by SHA-256, plus code commit).
2. **Statistic and `n`** (`expected-payload-agreement`, matched bits `m` of `n` per accepted entry).
3. **Threshold basis** (`k`, analytic binomial tail basis `P(Bin(n, 1/2) >= k) <= 1e-6`, protocol/calibration digest, and `searchScope` over catalogue size and key count).
4. **Key and payload-derivation id** (`keyId`, `derivationId`; never secret key bytes).
5. **Embedding quality** (PSNR in dB, floor in dB, `belowFloor`, cover/marked pixel and file digests when the cover reference is available locally, or explicit `unavailable` on blind queries).
6. **Tested bit positions** (half-open slice `[start, end)` of `rawBitCount` that carries direct keyed-hash output, excluding ECC and fixed version bits per review B1).

**Why a profile-specific record rather than extending the generic container:**
- Fingerprint-only profiles (`go-tokens`, `ts-tokens`, `text-plain`, `traceweave-image-fingerprint`) have no model weights, no secret key or payload-derivation ID, no embedding PSNR floor, and no tested bit slice. Adding those six fields to the shared container forces unused nulls or optionality onto every non-mark profile.
- The Lane 08 shared fields (artifact digest/role, profile, whole-image pixel region after EXIF orientation, raw bits, non-decisive decoded payload, outcome/abstention, and `confidence: null`) remain cleanly aligned inside [schemas/image-mark-finding-aid.schema.json](../../schemas/image-mark-finding-aid.schema.json).

## 2. Explicit separation from origin proof and `tw1-` registration linkage

On the `e-img-m-2` evidence ([results recheck](../reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2)), public decoders and encoders allow keyless re-embedding (`100/100`) and residual transplant (`82/100` for TrustMark-Q, `90/100` for PixelSeal). Therefore:

- **`findingAidBoundary`** is mandatory in every record and fixes:
  - `role: "finding-aid-only"`
  - `provesOrigin: false`
  - `provesAuthorship: false`
  - `keylessCopyPossible: true`
  - `originEvidenceSource: "separate-registration-record"`
- **`decodedPayload.decisive`** is fixed to `false` (a blind BCH decode is never presence evidence).
- **`confidence`** is fixed to `null` (no natural-image calibration exists).
- **`registrationLink`** is explicitly separated from the mark test. When present, it points to an M4 registration record ([`registration-record.md`](registration-record.md#91-text-reference-normative-frozen-2026-11-24)) using **both**:
  - `textReference`: the frozen `tw1-` reference (26 Crockford base32 characters over the first 130 bits of `statementSha256` plus 1 Luhn mod 32 check character), and
  - `statementSha256`: the full 256-bit statement digest (avoiding the 2^65 birthday-equivocation margin of 130-bit references alone),
  together with `subjectDigestMatchesCandidate` (false whenever a candidate has been edited or recompressed after registration) and `verificationStatus` (`"unverified-reference-only"` or `"verified-separately"`, never inferred from the mark).

## 3. Mapping of the six IMG.5 fields and Lane 08 fields

| Concept | Schema path (`image-mark-finding-aid.schema.json`) | Notes |
| --- | --- | --- |
| Artifact & decode | `/artifact` (`sha256`, `byteLength`, `role`, `decode`) | Whole-file digest; `orientationBasis: "after-exif-orientation"` when `status: "ok"` |
| Profile & protocol | `/profile` (`id`, `version`, `protocolVersion`, `protocolSha256`) | Binds the mark protocol digest (`e-img-m-2`: `cba36673…4110`) |
| **1. Model digests** | `/carrier` (`algorithm`, `variant`, `codeCommit`, `models[]`) | Each model entry carries `id`, `role`, and `sha256`; learned schemes require >= 1 model |
| Region | `/region` (`unit`, `basis`, `scope`, `x`, `y`, `width`, `height`, `imageWidth`, `imageHeight`) | `null` on decode abstention; integer pixels after EXIF orientation |
| Raw & decoded | `/raw`, `/decodedPayload` | Separate; `decodedPayload.decisive` is always `false` |
| **6. Tested bit positions** | `/testedBits` (`basis`, `start`, `end`, `count`, `rawBitCount`, `excludedNote`) | E.g. TrustMark-Q `[0, 61)` of `100` (excludes 35 BCH + 4 version bits); PixelSeal `[1, 257)` of `257` |
| **4. Key / derivation id** | `/keyReference` (`keyId`, `derivationId`) | Closed object; raw key bytes are rejected |
| **2. Statistic + `n`** | `/statistic` (`name`, `n`, `matchedBits`, `acceptedEntries[]`, `maxOtherBits`, `maxOtherEntryId`) | `n == testedBits.count`; every accepted entry above `k` is listed |
| **3. Threshold basis** | `/threshold` (`k`, `basis`, `perComparisonFalseAcceptBound`, `calibrationId`, `searchScope`) | Records `catalogueEntries`, `keysSearched`, and `perQueryUpperBound` |
| **5. Embedding quality** | `/embeddingQuality` (`status: "measured" | "unavailable"`, `psnrDb`, `floorDb`, `belowFloor`, …) | Measured PSNR and cover/marked digests when cover is held; explicit `unavailable` on blind query |
| Outcome | `/outcome` (`class`, `code`) | `match`, `no-match`, or `abstain` (`ambiguous`, `undecodable`, `unsupported-mode`, `too-small`) |
| Origin boundary | `/findingAidBoundary` | Enforces `provesOrigin: false`, `provesAuthorship: false`, `keylessCopyPossible: true` |
| Registration link | `/registrationLink` (`null` or `{registrationVersion, textReference, statementSha256, subjectDigestMatchesCandidate, verificationStatus, note}`) | `tw1-` check character and 130-bit `statementSha256` prefix verified by checker |
| Confidence | `/confidence` (`null`) | Always `null` without natural-image calibration |

## 4. Schema, fixtures, and validation

- Schema: [schemas/image-mark-finding-aid.schema.json](../../schemas/image-mark-finding-aid.schema.json)
- Fixtures and checker: [image-mark-finding-aid/](image-mark-finding-aid/README.md) (`check_finding_aid.py`, wired into `tools/validate.py`)
- Positive fixtures use committed `e-img-m-2` records (`tm:m2000000:jpeg90` with `tw1-` link where `subjectDigestMatchesCandidate: false`; `tm:m2000000` marked-entry with measured embedding quality; `ps:m2000000:clean` with `registrationLink: null`, illustrating the full 257-bit decoder output with unkeyed detection bit `preds[0, 0]` prepended to the 256 tested bits logged in `e-img-m-2/queries.jsonl`; `tm:m2000000:cover` as `no-match`; plus a decode-abstention `too-small` case).
- Negative fixtures (24 cases) cover missing/corrupted instances of all 6 IMG.5 fields, origin-proof violations (`provesOrigin: true`, `provesAuthorship: true`, `keylessCopyPossible: false`, `decodedPayload.decisive: true`), free-text origin/authorship/ownership/first-creation wording across `registrationLink.note`, `threshold.basis`, `testedBits.excludedNote`, and `threshold.calibrationId`, secret key injection, invalid `tw1-` check characters and `statementSha256` mismatches, bit-slice inconsistencies, cross-field inconsistencies (non-empty `acceptedEntries` on `abstain`/`too-small`, `statistic.matchedBits` disagreeing with `acceptedEntries[0].matchedBits` on `match`, partial coordinates under `region.scope: "whole-image"`), non-null `confidence`, and required-field deletion self-tests.
