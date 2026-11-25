# Draft mapping: Traceweave records and C2PA 2.5 structures

Status: **research draft, 2026-11-23. Not normative, not reviewed, and no compatibility claim.** Roadmap gates C2PA.1–C2PA.3 ([roadmap](../../ROADMAP.md), later-profile table). This draft does not change `spec/`, `schemas/`, `profiles/`, `test-vectors/` or the roadmap. The fixtures and their checker are in [c2pa-fixtures/](c2pa-fixtures/README.md).

**What was run.** All sources below were read over read-only HTTP on 2026-11-23. The fixture builder and checker in `c2pa-fixtures/` were run (results in §8). **No C2PA implementation was available locally**, and none was installed. No fixture was serialized to CBOR or JUMBF, signed, or read by any C2PA tool. **C2PA.2 therefore stays open** on its clause "fixtures from a pinned open-source C2PA tool round-trip through a Traceweave adapter in both directions".

**Shared terminology is not compatibility.** This document uses C2PA terms to say where a Traceweave field could go. It does not say that any C2PA tool would accept the result.

## 0. Pins

| ID | Source and version | Sections used |
| --- | --- | --- |
| C1 | C2PA [Technical Specification 2.5](https://spec.c2pa.org/specifications/specifications/2.5/specs/C2PA_Specification.html) ("2.5 - October 2026" in Appendix F; the URL is a living page, pinned by its version path) | 5.1 compatibility; 8.2 labels and namespaces; 8.6 assertion store; 8.8 redaction; 10.2 claim (`created_assertions`, `gathered_assertions`, attribution); 10.3.2.4 signing (COSE_Sign1, detached); 11.5.1 assertion content types; 11.5.3.1 unknown boxes are skipped; 12.1 hash list; 12.2 hard and soft bindings; 12.3.1 signature algorithms; 13.3.6 trusted manifest; 13.4 trust lists; 14.10.4 assertion validation; 16.3.1 data hash; 16.3.7 soft binding, algorithm list, resolution; 16.4.1.5 watermarking; 16.4.1.10 soft-binding lookup; 16.4.2 external reference; 16.5.3 ingredient relationships; 16.9.2 regions of interest; A.8 unstructured text; A.9 structured text |
| C2 | C2PA [Soft Binding API 2.5](https://spec.c2pa.org/specifications/specifications/2.5/softbinding/Decoupled.html), OpenAPI `info.version` 2.5.0, route base `/v1` | 1.2 usage flows; 1.4 routes; OpenAPI `/matches/byBinding`, `c2pa.softBindingQueryResult`, `c2pa.bindings` |
| C3 | C2PA [Implementation Guidance](https://spec.c2pa.org/specifications/specifications/2.2/guidance/Guidance.html) (the version the 2.5 index links; no 2.5 guidance page exists, HTTP 404) | 4.2.5 implementation guidance; 4.2.6 watermarks; 4.2.7 trust and privacy; 4.2.8 algorithm list |
| C4 | Soft-binding algorithm list at [`b445c12f`](https://github.com/c2pa-org/softbinding-algorithm-list/blob/b445c12ff537346dd7e4bd79524898b23814a89a/softbinding-algorithm-list.json), file SHA-256 `1ed28231…58d1`; its [README](https://github.com/c2pa-org/softbinding-algorithm-list/blob/b445c12ff537346dd7e4bd79524898b23814a89a/README.md) and [schema](https://github.com/c2pa-org/softbinding-algorithm-list/blob/b445c12ff537346dd7e4bd79524898b23814a89a/softbinding-algorithm-list.schema.json). `sbal.c2pa.org` now redirects to a mirror in the `c2pa-org/specifications` repository; at its commit `05dbf10b` the file is byte-identical | 79 entries (19 fingerprint, 60 watermark), identifiers 1–80 with 59 unused, none deprecated |
| C5 | ISCC [IEP-0020 "ISCC C2PA Conformance"](https://ieps.iscc.codes/iep-0020/), status Draft, updated 2026-10-28; source at [`b6a5b669`](https://github.com/iscc/iscc-ieps/blob/b6a5b66920d7590ea6a7f86a5e291c190525ce1e/ieps/iep-0020.md) | §4 value; §4.3 assertion; §5 generation; §6 matching; §7 resolution API |
| C6 | in-toto Attestation Framework at [`50bf0171`](https://github.com/in-toto/attestation/blob/50bf01716982189898823e90586075f37cd9bb7d/spec/v1/statement.md): Statement v1 and [ResourceDescriptor](https://github.com/in-toto/attestation/blob/50bf01716982189898823e90586075f37cd9bb7d/spec/v1/resource_descriptor.md); [DSSE v1.0.2](https://github.com/dsse-lf/dsse/blob/v1.0.2/protocol.md) | subject matching by digest; ResourceDescriptor needs one of `uri`, `digest`, `content`; PAE |
| C7 | c2pa-rs, tag `c2pa-v0.92.2`, commit [`d8d5e0ff`](https://github.com/contentauth/c2pa-rs/tree/d8d5e0ffb0adba8b163b8efdbd06993dbd8e0b6b) (latest release on 2026-11-16) | named as the candidate tool for C2PA.2 only; not downloaded, built or run. Its licence was not rechecked at this tag (lane 10 read MIT/Apache-2.0 at an earlier commit) |
| C8 | [RFC 8949](https://www.rfc-editor.org/rfc/rfc8949) (CBOR, diagnostic notation §8), [RFC 9052](https://www.rfc-editor.org/rfc/rfc9052) (COSE_Sign1). JUMBF is ISO/IEC 19566-5:2023, named and not read | only as far as the fixtures' notation needs |

Traceweave inputs: [core](../../spec/core.md), [attestations](../../spec/attestations.md), [catalogue and report contract](../../spec/catalogue-report.md) (§3 catalogue, §6 report, §6.6 provenance, §6.8 behavioural rules, §7–§8 separation and claims), the [image profile draft](extraction-profile-image.md), lanes [08](../lanes/08-evidence-review.md) and [10](../lanes/10-evidence-review.md), and the [signing-interop results](../lanes/signing-interop-results.md).

**Version choice.** Lane 10 read C2PA 2.4. This draft pins **2.5**, the current version. In 2.5 the binding sections moved: lane 10's §9.1 and §9.3 are §12.2.1 and §12.2.3 here. The roadmap asks for one version, so 2.4 is not used anywhere below (open decision D1).

## 1. Field-by-field mapping

### 1.1 How to read the tables

Each Traceweave field has one status. The **pointer** column is the JSON pointer the fixtures use; [mapping-rules.json](c2pa-fixtures/mapping-rules.json) holds the same rows, and the checker fails if a rule pointer is missing from this document.

- **mapped:** carried in a C2PA location that has C2PA-defined meaning, with a stated conversion.
- **lossy:** carried only where C2PA gives it no meaning (for example `bindingMetadata`, which a validator "should not use", C1 16.3.7.3.1), or carried with information lost.
- **opaque:** carried byte-for-byte inside a Traceweave assertion or predicate. C2PA stores it but defines no meaning, and validators ignore it.
- **unmapped:** no home on the C2PA side.
- **conflicting:** a C2PA field exists, but its meaning differs from ours in a way that needs a stated conversion (§4).

Type notation: `bstr` is a CBOR byte string, written `h'…'` or `'…'` in diagnostic form; `tstr` is a CBOR text string; `tdate` is CBOR tag 0 (C1 8.9); floats are CBOR floats.

### 1.2 Image catalogue entry → C2PA (fixture f1, round trip f5)

Source: one entry of `traceweave-image-catalogue-draft-1` ([profile](extraction-profile-image.md) §8.1), entry `s0000000` of the committed `e-img-f-2` catalogue, with its catalogue-level fields. The experiment-only fields `seed`, `pixelSha256` and `split` are left out.

| Traceweave pointer | C2PA location | Conversion | Status | Notes |
| --- | --- | --- | --- | --- |
| `/artifact/pdq/hash` | `/assertions/c2pa.soft-binding/blocks/0/value`, with `alg` set | 64 hex digits → 32-byte `bstr` | mapped | No `alg` value is ours to use (§2.1); the fixture uses `org.traceweave.pdq.draft-2`, a proposed identifier, not registered anywhere |
| `/artifact/sha256` | `/assertions/c2pa.hash.data/hash` | hex → 32-byte `bstr`, `alg` `sha256` | mapped only for a **sidecar** manifest whose data hash has no `exclusions` | Otherwise conflicting (§4.1). JPEG and PNG normally use `c2pa.hash.boxes`, which has no single whole-file value |
| `/artifact/pdq/quality` | `bindingMetadata` custom member | integer | lossy | The quality floor (`≤ 49` abstains) has no C2PA meaning |
| `/profile` | `bindingMetadata` custom member | map | lossy | `alg` names an algorithm, not a profile triple bound to configuration bytes |
| `/matchingConfigSha256` | `bindingMetadata` custom member | hex text | lossy | Threshold, dihedral policy and tie rule. C2PA leaves matching to "the manner prescribed by the specified algorithm" (16.3.7.5.1) |
| `/artifact/decode/width`, `/artifact/decode/height` | not written (whole-image scope is `{}`) | — | lossy | A region would need them; a whole-image binding has none |
| `/artifact/decode/exifOrientation` | none stated | — | conflicting | The hash is computed after the profile's orientation step; a soft-binding value states no orientation basis (§4.3) |
| `/catalogueVersion`, `/artifact/id`, `/artifact/byteLength` | — | — | unmapped | `instanceID` names an asset version, not a catalogue entry; a data hash carries no length |
| `/artifact/pdq/status` | — | — | unmapped | An abstaining entry (for example `low-quality`, entry `s0000049`) yields no soft binding and leaves no trace |
| `/artifact/iscc` | — | — | unmapped | The 64-bit Image-Code body without an ISCC header is not an `io.iscc.v0` value (§2.2) |
| `/artifact/decode/status`, `/artifact/decode/format`, `/artifact/decode/sourceMode`, `/artifact/decode/iccPresent` | — | — | unmapped | C2PA records no decoder view |

Forbidden in this export: a `scope.region` on the whole-image binding (`/assertions/c2pa.soft-binding/blocks/0/scope/region`). The round trip (f5) keeps exactly two of 20 leaf fields: the PDQ hash, and the artifact digest (sidecar case only).

### 1.3 Token catalogue entry → C2PA (fixture f6)

Source: the `sum.go` entry of the reference catalogue in `go-function-in-host` (`traceweave-catalogue-draft-2`, [contract](../../spec/catalogue-report.md) §3). The catalogue is **private** (§3.7): exporting it into a manifest publishes unkeyed hashes of source code. The fixture shows what the mapping would be, not that it should be done (D6).

| Traceweave pointer | C2PA location | Conversion | Status |
| --- | --- | --- | --- |
| `/artifact/channels/exact/fingerprints/*/hash` | `/assertions/c2pa.soft-binding/blocks/*/value` | 16 hex → 8-byte `bstr`, one block per fingerprint, in position order | mapped (proposed, unregistered `alg`) |
| `/artifact/channels/normalized/fingerprints/*/hash` | `/assertions/c2pa.soft-binding__1/blocks/*/value` | the same, in a second assertion (multiple instances, C1 8.4) | mapped (proposed, unregistered `alg`) |
| `/artifact/sha256` | `/assertions/c2pa.hash.data/hash` | as in §1.2 | mapped (sidecar only) |
| `/artifact/channels/exact/fingerprints/*/position`, `/artifact/channels/normalized/fingerprints/*/position` | block order | number lost, order kept | lossy |
| `/profile`, `/extractionConfig` | `bindingMetadata` | map | lossy |
| `/artifact/channels/exact/fingerprints/*/span`, `/artifact/channels/normalized/fingerprints/*/span` | none | — | conflicting (§4.2) |
| `/catalogueVersion`, `/artifact/id`, `/artifact/byteLength`, `/artifact/status`, `/artifact/tokenCount`, `/artifact/channels/exact/kgramCount`, `/artifact/channels/exact/partialWindow`, `/artifact/channels/normalized/kgramCount`, `/artifact/channels/normalized/partialWindow` | — | — | unmapped |

### 1.4 Comparison report → custom assertion (fixture f2)

Source: [example-report.json](../../test-vectors/matching/example-report.json), whose body hashes to its `bodySha256` (`081d8600…d3be`, re-checked by the checker). Label: `org.traceweave.comparison-report`, the reverse-domain form of the project domain `traceweave.org` that C1 8.2.1 requires for entity-specific namespaces. It is a proposed identifier, not registered anywhere (D3).

| Traceweave pointer | C2PA location | Conversion | Status |
| --- | --- | --- | --- |
| `/body` | `/assertions/org.traceweave.comparison-report/body` | the exact canonical body bytes (§3.3 of the contract) as one `bstr`, so `bodySha256` stays reproducible. A JSON content box (C1 11.5.1) could hold the same bytes; no tool was tested for re-serialization | mapped (bytes) |
| `/provenance/bodySha256` | `/assertions/org.traceweave.comparison-report/bodySha256` | hex → `bstr`; the checker verifies it against the carried bytes | mapped |
| `/provenance/comparisonConfigSha256` | `/assertions/org.traceweave.comparison-report/comparisonConfigSha256` | hex → `bstr` | mapped |
| `/provenance/implementation/name`, `/provenance/implementation/version`, `/provenance/implementation/commit` | `/assertions/org.traceweave.comparison-report/producer/name`, `/assertions/org.traceweave.comparison-report/producer/version`, `/assertions/org.traceweave.comparison-report/producer/commit` | text | mapped. **Not** `claim_generator_info`: the program that ran the comparison is not the claim generator |
| `/provenance/specCommit` | `/assertions/org.traceweave.comparison-report/specCommit` | text | mapped |
| `/provenance/generatedAt` | `/assertions/org.traceweave.comparison-report/generatedAt` | text → `tdate` (tag 0) | mapped; still a claimed time, not a time-stamp |
| `/body/pairs/*/modes/*/outcome`, `/body/pairs/*/outcome`, `/body/rejection` | inside the body bytes | — | **opaque**: C2PA has no outcome classes, abstention reasons or rejection sides |
| `/body/pairs/*/modes/*/regions/*/status`, `/body/comparison/minRegionDistinctHashes` | inside the body bytes | — | opaque: minimum evidence has no C2PA meaning |
| `/body/inputs/suppressionCatalogueSha256`, `/body/suppression` | inside the body bytes | — | opaque: the suppression catalogue digest has no C2PA meaning |
| `/body/pairs/*/modes/*/containment`, `/body/pairs/*/modes/*/similarity` | inside the body bytes | — | opaque: raw counts. They must never become a resolution-API `similarityScore` |
| `/body/pairs/*/candidate/sha256` | compared with the manifest's `c2pa.hash.data` | — | conflicting (§4.1) |
| `/body/pairs/*/modes/*/regions/*/candidateSpan` | none | — | conflicting (§4.2) |

The assertion goes in `gathered_assertions`, because `created_assertions` "are attributed to the signer" (C1 10.2.2). It moves to `created_assertions` only when the manifest signer ran the comparison. Forbidden: deriving a `/assertions/c2pa.soft-binding` from a report.

### 1.5 Comparison report → in-toto statement referencing a manifest (fixture f3)

The report becomes the predicate, unchanged. The subject is the candidate artifact by SHA-256, because in-toto matches subjects "purely by digest" (C6). The predicate type `https://traceweave.org/predicate/comparison-report/draft-2` is a proposed identifier, not registered anywhere; no report predicate is defined or published yet, and the URL is an identifier, not a page.

| Traceweave pointer | Statement location | Conversion | Status |
| --- | --- | --- | --- |
| `/body` | `/predicate/body` | JSON, unchanged; `bodySha256` re-derivable by JCS | mapped, lossless |
| `/provenance` | `/predicate/provenance` | unchanged | mapped |
| `/provenance/bodySha256` | `/predicate/bodySha256` | unchanged | mapped |
| `/body/pairs/0/candidate/sha256` | `/subject/0/digest/sha256` | unchanged | mapped |
| `/body/pairs/0/candidate/id` | `/subject/0/name` | unchanged | mapped |

The manifest reference is `predicate.c2paManifest`: `manifestId` (`urn:c2pa:…`), `manifestStoreSha256` (null in the fixture, because no store was serialized; a real statement must carry it, D8), the manifest's hard binding (`label`, `alg`, `hash`, `exclusions`), and a `relation` from a closed list: `same-bytes`, `bytes-minus-exclusions` or `found-by-soft-binding`. The checker rejects a `same-bytes` relation whose hard binding has exclusions or another digest.

A report with several candidate artifacts needs one statement per candidate, or a subject that is the report body itself. The current core adapter allows exactly one subject (D2).

### 1.6 Mark-detection record → C2PA (fixture f4)

A draft profile-specific schema now exists for image-mark finding aids: [schemas/image-mark-finding-aid.schema.json](../../schemas/image-mark-finding-aid.schema.json) (see [image-mark-finding-aid.md](image-mark-finding-aid.md), IMG.5). Fixture `f4` uses the earlier Lane 08 shared-container shape with invented values (no mark was embedded or detected in this fixture). **A detection is a verifier result.** The C2PA structures it can map to are the ones the *embedder's* manifest would hold; all six IMG.5 fields (model digests, statistic with `n`, threshold basis, key/derivation id, embedding quality, tested bit positions) and any `tw1-` registration pointer remain unmapped in C2PA `c2pa.soft-binding`.

| Traceweave pointer | C2PA location | Conversion | Status |
| --- | --- | --- | --- |
| `/decoded/payloadHex` | `/assertions/c2pa.soft-binding/blocks/0/value` | hex → `bstr` | mapped, and conflicting: the byte layout is algorithm-specific (16.3.7.4) and was not checked against the TrustMark page |
| `/carrier/variant` | `/assertions/c2pa.soft-binding/alg` | `com.adobe.trustmark.` + variant | mapped (registered ids C, Q, P, F) |
| `/region` | `/assertions/c2pa.soft-binding/blocks/0/scope/region` | integer pixels → spatial rectangle, `unit` `pixel`, float coordinates | mapped |
| `/region/imageWidth`, `/region/imageHeight` | — | — | lossy: a rectangle does not record the image size it refers to |
| `/region/basis` | — | — | conflicting (§4.3) |
| `/statistic`, `/outcome`, `/searchScope`, `/confidence` | — | — | unmapped: presence statistic, threshold, calibration id, decision and search scope have no C2PA home |
| `/raw`, `/decoded/status`, `/decoded/ecc` | — | — | unmapped: raw bits and error correction |
| `/recordKind`, `/artifact`, `/carrier/algorithm`, `/carrier/codeCommit`, `/carrier/weightSha256` | — | — | unmapped: the queried artifact is not the asset the embedder's manifest binds, and the algorithm entry pins no code or weights |

`c2pa.watermarked.bound` needs a `c2pa.soft-binding` assertion in the same manifest; otherwise validation fails with `assertion.action.softBindingMissing` (14.10.4.2.4). `c2pa.watermarked` is deprecated (16.4.1.5). The 2.2 guidance (C3 4.2.6) still names `c2pa.watermarked`.

### 1.7 C2PA → Traceweave

| C2PA structure (C1 section) | Traceweave home | Status |
| --- | --- | --- |
| Manifest store, active manifest, `urn:c2pa:` manifest id (11, 14.5) | None. A statement may *reference* one (§1.5) | unmapped |
| Claim `instanceID` (10.2.2) | None; not an artifact `id` | unmapped |
| `claim_generator_info` (10.2.3) | None; not `provenance.implementation` | unmapped |
| `created_assertions` versus `gathered_assertions` (10.2.2) | None. Attribution to a signer is outside the report (contract §7) | unmapped |
| `redacted_assertions`, `c2pa.redacted` (8.8) | None. Traceweave has no selective disclosure (core) | unmapped |
| Claim signature: COSE_Sign1_Tagged, detached, `x5chain` label 33 (10.3.2.4, 13.5) | Signature validity and signer trust, kept separate (core interpretation). The DSSE adapter uses Ed25519 with raw keys, not X.509 | conflicting |
| Validator states well-formed, valid, trusted; C2PA Trust List; EKU `c2pa-kp-claimSigning` (13.3, 13.4) | Trust policy of [attestations](../../spec/attestations.md) | conflicting: different trust anchors and identity model |
| Time-stamp: RFC 3161 countersignature (10.3.2.5) | Separate timestamp result; `generatedAt` and `recordedAt` are claimed times | conflicting |
| Hard bindings: `c2pa.hash.data`, `.boxes`, `.bmff.v3`, `.collection.data`, `.segment` (12.2.2, 16.3) | Artifact `sha256` only for a whole-file data hash without exclusions | conflicting (§4.1) |
| `c2pa.soft-binding` `alg`, `blocks[].value` (16.3.7) | An image-catalogue hash, only if `alg` is a Traceweave-defined algorithm with known bytes | lossy: the importer gets a hash, without profile, configuration, quality or threshold |
| `blocks[].scope.timespan`, `alg-params`, `pad`, `name` (16.3.7.2) | None (still images and source text have no timespan) | unmapped |
| `bindingMetadata` (16.3.7.3.1) | Informational only; never used as evidence | lossy |
| Ingredient `relationship`: `parentOf`, `componentOf`, `inputTo` (16.5.3) | None. Traceweave never infers ancestry or direction (contract §8) | unmapped |
| Ingredient `softBindingsMatched`, `softBindingAlgorithmsMatched`, `activeManifest` (16.4.1.10) | None. A lookup result is not a comparison result | unmapped |
| Ingredient `validationResults` (16.5.13) | None | unmapped |
| Actions: `c2pa.created`, `c2pa.opened`, `c2pa.placed`, `c2pa.watermarked.bound`, `digitalSourceType` (16.4.1) | None. A mark-embedding record could cite `c2pa.watermarked.bound` | unmapped |
| Regions of interest: spatial, temporal, frame, textual, identified (16.9.2) | Pixel regions after orientation, or byte spans | conflicting (§4.2, §4.3) |
| `c2pa.external-reference`, hashed `location` (16.4.2) | A pointer to a DSSE envelope (§3, option C) | mapped only as a pointer |
| Resolution API `similarityScore` 0–100 (C2 OpenAPI) | **None, by design**: the report has no score field (contract §8) | unmapped; an importer must not store it as evidence |

### 1.8 M4 registration record → C2PA sidecar custom assertion (`org.traceweave.registration-link`, fixture f7)

Source: [statement.json](registration-fixtures/fixtures/statement.json) (`traceweave-registration-draft-5`, [design](registration-record.md)), whose canonical JCS bytes hash to `statementSha256` (`3f308f18…c93e`) and yield the frozen §9.1 text reference `tw1-7WR8Y61HYTR7RJE0NN5W52C8TAN` ([text-reference-three-roots.json](registration-fixtures/fixtures/text-reference-three-roots.json)).

A C2PA **sidecar** manifest (`c2pa.hash.data` with no `exclusions`) or custom assertion links cleanly to a Traceweave M4 registration record via `org.traceweave.registration-link` under the `org.traceweave` namespace (`traceweave.org`). It carries **both** the `tw1-` reference (for human-readable lookup) and the full `statementSha256` (avoiding the 2^65 birthday equivocation margin of 130-bit references alone, [registration design §9.1](registration-record.md#91-text-reference-normative-frozen-2026-11-24)). It stays in `gathered_assertions` unless the manifest signer is the registrant (`signerIsRegistrant: true`).

| Traceweave pointer | C2PA location | Conversion | Status | Notes |
| --- | --- | --- | --- | --- |
| `/statementSha256` | `/assertions/org.traceweave.registration-link/statementSha256` | hex → 32-byte `bstr` | mapped | Must match the 130-bit prefix of `textReference` |
| `/textReference` | `/assertions/org.traceweave.registration-link/textReference` | `tstr` | mapped | Frozen `tw1-` Crockford base32 + Luhn mod 32 check character |
| `/statement/predicate/registrationVersion` | `/assertions/org.traceweave.registration-link/registrationVersion` | `tstr` | mapped | `traceweave-registration-draft-5` |
| `/statement/predicateType` | `/assertions/org.traceweave.registration-link/predicateType` | `tstr` | mapped | `https://traceweave.org/predicate/registration/draft-5` |
| `/statement/subject/0/digest/sha256` | `/assertions/org.traceweave.registration-link/subjectSha256` and `/assertions/c2pa.hash.data/hash` | hex → 32-byte `bstr` | mapped | `c2pa.hash.data` equality holds only when `relation` is `same-bytes` (sidecar, no exclusions) |
| `/relation` | `/assertions/org.traceweave.registration-link/relation` | `tstr` | mapped | Closed list: `same-bytes`, `bytes-minus-exclusions`, `derived-copy` |
| `/statement/predicate/claims/createdAt` | `/assertions/org.traceweave.registration-link/claimedCreatedAt` | text → `tdate` | lossy | Claimed creation time only; not a trusted C2PA `sigTst2` (C1 8.9) |
| `/notShown` | `/assertions/org.traceweave.registration-link/notShown` | array of `tstr` | **opaque** | Disclaims authorship, originality, first-creation, ownership, permission; ignored by C2PA validators |
| `/statement/_type`, `/statement/subject/0/name`, `/statement/predicate/contentKind` | — | — | unmapped | Envelope/coarse labels; `subject/0/name` is not `instanceID` |
| `/statement/predicate/nonce`, `/statement/predicate/possession`, `/statement/predicate/catalogue` | — | — | unmapped | Kept private in the registration statement/bundle; never disclosed in a public C2PA manifest |
| `/statement/predicate/implementation`, `/statement/predicate/specCommit` | — | — | unmapped | Statement producer metadata; not `claim_generator_info` |
| `/timeEvidenceSummary` | none (`sigTst2` is separate) | — | **conflicting** | Registration RFC 3161 / OpenTimestamps roots stamp the DSSE signature and cannot be reused as C2PA `sigTst2` over the claim signature ([registration design §15 S12](registration-record.md#15-roadmap-mapping-and-proposed-roadmapmd-text-s13-roadmapmd-is-not-changed-here)) |

Note on `claims.aiUse` ([registration design §4.7](registration-record.md#47-self-declared-ai-use-normative-owner-decision-2026-11-24)): if a registration carries `aiUse.declared`, `generated` and `modified` correspond to the IPTC URIs `trainedAlgorithmicMedia` and `compositeWithTrainedAlgorithmicMedia`, while `no-generative-ai` has **no** IPTC/C2PA term (unmapped/conflicting; never emit a negative claim as an IPTC URI, and never render either as Traceweave-verified). Forbidden in `org.traceweave.registration-link`: deriving `/assertions/c2pa.soft-binding` from a registration link, or adding `/assertions/c2pa.hash.data/exclusions` when `relation` is `same-bytes`.

## 2. Fingerprints as soft bindings

### 2.1 Registered algorithm identifiers today (C4)

| Traceweave extractor | Closest registered entries | Can Traceweave values use it? |
| --- | --- | --- |
| PDQ (image profile §4) | `com.originalpictures.pdq.1` (id 74). Video only: `com.originalpictures.tmk-pdqf.1`, `com.originalpictures.vpdq.1`. No entry by the PDQ maintainers | **No.** Entry 74 is one vendor's deployment: a float32 port of the C++ PDQ at ThreatExchange `baefb4ed`, a dihedral match at Hamming distance ≤ 34 calibrated on its own benchmark, and "matching is done only by Original Pictures' own verification". Our values come from the Python reference port with an experimental threshold of 31, and vendor reference sets differ by up to 8 bits on identical files (IMGF.2). Writing their `alg` would assert their algorithm and parameters. Lane 10 called these "third-party PDQ ids"; this draft agrees |
| ISCC Image-Code v0 (image profile §5) | `io.iscc.v0` (id 3), specified by IEP-0020 (C5) | **Not with the current profile output** (§2.2) |
| Token fingerprints (code) | None. Text entries exist: `com.writerslogic.text-minhash.1` (MinHash of word 5-gram shingles with LSH bands), `com.writerslogic.text-fingerprint.1`, `com.writerslogic.text-structure.1`, `com.encypher.text.fingerprint.1` (SHA-256 of NFC-normalized visible text, an exact key) and the ISCC Text-Code | **No.** None is winnowing over a profile's token channels. Each defines its own normalization, and none carries positions or spans |
| Text profile (`text-plain`) | The same text entries | No, for the same reason |
| TrustMark (deferred mark study) | `com.adobe.trustmark.Q`, `.C`, `.P`, `.F` (identifiers 4, 5, 13 and 55) | Yes, as `alg` strings. Registration is not evaluation. Lane 10 listed three variants; the list at the same commit has four |

**Discrepancy in the sources.** The 2.5 specification prints the entry schema with `oneOf` (decoded *or* encoded media types, never both; 16.3.7.4). The list repository's own schema uses `anyOf`. 25 of the 79 entries, entry 74 among them, carry both kinds, which the printed schema forbids and the repository schema allows. This mapping does not validate list entries; the point matters only if Traceweave ever submits one.

### 2.2 ISCC: what `io.iscc.v0` requires

Lane 10 (finding 6) and the image profile (§8.3) say that ISCC "maps to `c2pa.soft-binding` with the registered `io.iscc.v0`", needing no new algorithm id. That is true of the id, but IEP-0020 (draft, C5) now constrains the value, and **the profile's output does not meet it**:

- The value is an ISCC-SEQ of ISCC-UNITs, each an ISCC-HEADER followed by its body (§4). The profile stores a bare 64-bit body as 16 hex digits.
- The assertion holds an ISCC-SEQ of **256-bit** units (§4.3), and matching **ignores** any unit shorter than 256 bits (§6). The profile's 64-bit Image-Code would be ignored.
- Each soft binding **shall** include the Data-Code and the Instance-Code of the source (§5). The profile computes neither.
- It shall not include a **featureless** Image-Code (§5). The profile does not abstain on featureless images (OD-I5).
- `blocks[].scope` shall be an empty map (§4.3), so no region can be stated. `bindingMetadata` shall contain `io.iscc.generator` with `name` and `version`.

To export ISCC, the profile would have to compute 256-bit Image-Codes (iscc-core 1.5.0 can, per IEP-0020 §9), add Data-Code and Instance-Code over the file bytes, add the featureless test, and encode the sequence. That is a new profile version with new vectors (D5). IEP-0020 is a draft and can change.

### 2.3 What registering a new identifier would require

From C1 16.3.7.4, C3 4.2.8 and the list README (C4):

1. **A namespace the project owns.** `alg` must begin with an Internet domain name of the entity, reversed (C1 8.2.1). The project owns `traceweave.org` (registered 2026-11-23, as relayed by the coordinator; not independently checked here), so the namespace `org.traceweave` meets this item. Every `org.traceweave.*` label and `alg` in this draft is a proposed identifier, not registered anywhere (D3).
2. **An entry** with `identifier` (assigned on entry), `alg`, `type` `fingerprint`, either `decodedMediaTypes` (`image` or `text`) or `encodedMediaTypes` (for example `text/x-go`), and `entryMetadata` with `description`, `dateEntered`, a **contact email**, and an `informationalUrl` that resolves to documentation of the algorithm and the byte format of `value`. `softBindingResolutionApis` is optional, and any URL in it must resolve.
3. **One entry per algorithm version.** `identifier`, `alg` and `type` never change afterwards. A profile, configuration or threshold change would be a new entry.
4. **A pull request** by someone affiliated with the algorithm's owner, or by a maintainer of the open-source algorithm or its fork. The C2PA Technical Working Group approves it under its own process and may remove entries.
5. **A stated purpose of manifest recovery:** "The algorithm covered by the entry shall support embedding, extracting, or both, of a soft binding identifier for the purpose of manifest recovery" (README). A Traceweave comparison profile is not built for manifest recovery, so an entry would have to describe that use, which Traceweave does not run.

Item 1 is now met by `traceweave.org`. Items 2 (a public contact), 4 and 5 remain open and are disclosures and owner decisions.

### 2.4 What the resolution API expects (C2)

- `GET /matches/byBinding?alg=…&value=…&maxResults=…`, where `value` is the base64 of one soft-binding value. `POST /matches/byBinding` takes `{alg, value}` in a body for large values. `POST /matches/byContent` uploads the asset; `POST /matches/byReference` sends a URL. A service implements at least one query route plus `GET /manifests/{activeManifestId}`.
- The result is `{matches: [{manifestId, endpoint?, similarityScore?}]}`, where `similarityScore` is an integer from 0 to 100, "if appropriate". For `io.iscc.v0`, IEP-0020 §7 makes the score 100 for an exact Instance-Code match, and otherwise the best unit similarity, capped at 99.
- Store routes `POST /manifests` and `POST`/`PUT /bindings {bindingValue, manifestId}` register a value against a stored manifest.

**What this means for Traceweave.**
- A query sends a fingerprint, and `byContent` sends the asset itself, to a resolver operator. The core requires no remote resolver, and resolver leakage is the RES gates' subject. The guidance (C3 4.2.7) itself recommends computing the soft binding on the client side.
- `similarityScore` is a score with no stated calibration. The report contract forbids scores (§8), so nothing in a report maps to it.
- A token catalogue has many values per artifact, while a query carries one value.

### 2.5 The semantic gap

| | C2PA soft binding | Traceweave comparison |
| --- | --- | --- |
| Question | Which manifest belongs to this asset, now that the manifest is missing or suspect? | How much of party B's catalogue overlaps party A's, under a fixed configuration? |
| Parties | One asset and its own manifest, in a repository the asset's signer chose | Two catalogues, usually from two parties; no repository |
| Cardinality | One value, or a few, per asset; "all soft binding assertions in the located manifest" must match (16.3.7.5.1) | Many fingerprints per artifact, many artifacts, pairwise; partial containment is the normal result |
| Result | A manifest id, perhaps with a 0–100 score; the hard binding then usually fails for the query asset (16.4.1.10) | Outcome classes (`match`, `no-match`, `abstain`) with closed codes, minimum evidence, ambiguity and raw-count fractions |
| Absence | No manifest found | `no-match` means insufficient evidence, never "not derived" |
| Privacy | Manifests are meant to be found | Catalogues and reports are private by default |

**Consequence.** A soft binding can at most let a Traceweave fingerprint *find* a manifest. It cannot carry a comparison. Treating a soft-binding hit as a Traceweave `match`, or a Traceweave `match` as a reason to attach someone's manifest, would break core's separation of results.

## 3. Where a report can travel

| | A. Custom assertion inside a manifest (f2) | B. Separate in-toto/DSSE statement (f3) | C. Both: B, plus a hashed pointer from a manifest |
| --- | --- | --- | --- |
| Subject | The manifest's one asset (exactly one hard binding, 12.2.1); a report covers two catalogues | Any artifact by SHA-256, or the report body | As B |
| Who signs | The claim generator, with an X.509 chain carrying the `c2pa-kp-claimSigning` EKU (13.4.1, 13.5), algorithm from 12.3.1 (Ed25519 is allowed) | The report producer, under DSSE (measured Go↔Rust, Ed25519 raw keys) | Both, separately |
| Attribution | `created_assertions` binds the signer to the report; `gathered_assertions` is part of the claim but "not attributed to the signer" (10.2.2) | The statement signer only | Each signer for its own object |
| Trust | C2PA Trust List or user-configured anchors; "Trusted" means `signingCredential.trusted` (13.3.6) | The trust policy of [attestations](../../spec/attestations.md) | Two independent decisions, reported separately |
| Privacy | Travels with the asset and is readable by anyone who has it. Redaction happens only when the asset is later used as an ingredient (8.8) | Published only when the holder chooses | The pointer discloses that a report exists |
| What C2PA validates | Hashes and well-formedness. An unknown assertion is carried, not understood (5.1; 11.5.3.1 for boxes) | Nothing | Hash of the pointed-to bytes, if retrieved (16.4.2) |
| Bytes | `bodySha256` survives only if the canonical bytes are carried as a `bstr` or JSON box and no tool re-serializes them (untested) | Unchanged JSON; signing interop measured | As B |
| Dependencies | CBOR, JUMBF, COSE and X.509; none exists in Traceweave | Exists (DSSE experiment) | As B, plus a manifest writer for the pointer |

**Recommendation: B**, with C's pointer as a later, optional, owner-gated addition. Reasons:

1. **Subject mismatch.** A report is about two catalogues and many artifact pairs. A manifest is about one asset (C1 12.2.1).
2. **Attribution.** In `created_assertions`, a manifest signer would vouch for a comparison it may not have run. In `gathered_assertions`, the report rides along unattributed, with no signature of its own.
3. **Privacy.** Reports are private by default (contract §6.7). A manifest embedded in an asset is public wherever the asset goes.
4. **Signing and trust.** Option A needs an X.509 claim-signing certificate. To be "Trusted" rather than only "Valid", that certificate must chain to the C2PA Trust List, or to anchors each validator's user adds. B reuses the DSSE path already measured. Neither option establishes signer identity or comparison truth.
5. **No validation gain.** C2PA validators skip what they do not understand, so A adds integrity, not meaning.
6. **Option C costs little later.** A manifest owner who wants to point at a report can add a `c2pa.external-reference` with a hashed `location` (`alg`, `hash`, `url`) to `gathered_assertions` (16.4.2). An embedded-data assertion holding the DSSE envelope bytes (16.6.6) is another form, not tested here. Either way the report keeps its own signature.

**Strongest alternative:** A, for a party that already signs C2PA manifests and wants one artifact to carry everything. It is acceptable only in `gathered_assertions`, with the body carried as exact bytes, and only for reports the holder chose to publish.

## 4. Coordinates and identity

### 4.1 Artifact digest versus hard binding

A Traceweave artifact `sha256` is the SHA-256 of the exact bytes compared. The two values agree only in one case: a **sidecar or remote manifest whose `c2pa.hash.data` has no exclusions**. In every other case they differ in meaning, even when the digests happen to be equal:

- **Embedded manifests** change the file. The data hash excludes the manifest's byte range (16.3.1), so the file as distributed hashes differently from the file as compared.
- **JPEG and PNG** normally use `c2pa.hash.boxes` (12.2.2.2): per-box hashes with no single whole-file value.
- **Structured text, which includes source code** (A.9): the manifest block is a comment line, and its byte range is excluded (A.9.5.1). If the block is inserted at the start of an unchanged file, the hard-binding digest equals the digest of the original. Its byte set and offsets differ, though, and every byte span after the block shifts by the block length. Fixture f2 shows this case.
- **Unstructured text** (A.8): the hash is taken after removing the exclusions and **normalizing to NFC**, so it is not a digest of any stored byte sequence.

Rule used by the fixtures: never write a Traceweave digest into a hard binding, and never read one back from it, unless the binding is whole-file with no exclusions. A statement records the relation explicitly (`same-bytes`, `bytes-minus-exclusions`, `found-by-soft-binding`). A soft binding "shall not be used as a hard binding" (12.2.3.1), and core says the same of soft matches and exact digests.

### 4.2 Byte spans versus regions of interest

Traceweave spans are half-open `[start, end)` UTF-8 **byte** offsets into the original artifact bytes (contract §3.2). C2PA has no byte-range region. Its candidates are:

- **textual** (16.9.2.2.5): a fragment identifier (RFC 3023 or ISO 32000-2 Annex O) plus **character** offsets with an **inclusive** end. The specification does not say whether a character is a code point, a UTF-16 unit or a grapheme. A conversion needs the text itself (which a catalogue does not hold), a fragment-identifier scheme for source files, and that definition.
- **frame** (pages) and **identified** (container items): no fit for code.

Two further shifts apply. A structured-text manifest block (A.9) moves every later offset by the block length. NFC normalization (A.8) changes offsets in text that was not already NFC. So spans stay **conflicting**: fixture f6 does not write them, and fixture f2 carries them only inside the opaque body.

### 4.3 The conflict lane 10 found: pixel coordinates and orientation

Lane 10 noted that "C2PA's region-map coordinates versus our pixel coordinates after orientation need a stated conversion". Read against 2.5, this goes further than a conversion formula:

- A spatial `shape` has `unit` `pixel` or `percent`, and **float** coordinates (16.9.2.3). It states **no orientation basis** (before or after EXIF orientation) and no reference image size. The specification's only hint of an origin is the example prose "10 pixels down from the top and left" (16.9.2.4).
- Traceweave image regions are integer pixels at `width × height` **after** the profile's orientation step (image profile §8.3; lane 08 container).
- `io.iscc.v0` forbids any scope at all (§2.2).

The conversion in fixture f4 writes integers as floats with `unit` `pixel`. It declares the orientation basis and the image size as conflicting and lossy. The checker rejects an integer coordinate and an undeclared basis. A real export needs a stated convention (D9), because a consumer cannot recover the basis from the region.

### 4.4 Identifiers

| Traceweave | C2PA | Relation |
| --- | --- | --- |
| Artifact `id` (opaque catalogue label) | `instanceID` (asset version, xmp:iid preferred) | None |
| `bodySha256`, region key (reference id, candidate id, mode, p, q) | Manifest URN, hashed JUMBF URIs | None; a region key has no C2PA form |
| Profile triple with `configSha256` | Soft-binding `alg` (one string per algorithm version) | Many profiles and configurations would share one `alg` unless each version is registered |

## 5. Requirements that do not cross

**What C2PA requires that Traceweave cannot satisfy today**
1. A claim signature as COSE_Sign1 over CBOR, with an X.509 chain in `x5chain` (10.3.2.4, 13.5). To reach "Trusted", the chain needs a trust anchor from the C2PA Trust List or one the user configures (13.4). Traceweave has DSSE with raw Ed25519 keys and no certificates.
2. Exactly one hard binding per manifest (12.2.1). A report has no single asset.
3. In a standard manifest, an actions assertion whose first action is `c2pa.created` or `c2pa.opened`, with ingredient assertions for opened assets (16.4.1.2). A comparison tool creates and opens no asset.
4. ~~Labels and `alg` ids under an owned Internet domain (8.2.1).~~ **Closed:** the project owns `traceweave.org`, and the drafts use `org.traceweave.*`. The identifiers are proposed only; registering them (item 5) is still open.
5. For a registered soft binding: a public contact, documentation of the value format, an approved pull request, and a manifest-recovery purpose (§2.3).
6. For `io.iscc.v0`: 256-bit units including the Data-Code and Instance-Code, and no featureless codes (§2.2).
7. CBOR (deterministic encoding for the claim, C1 10.1), JUMBF boxes, salted assertion hashing (8.6, 9.4.2.3), and hashed URIs. Traceweave has none of these.
8. Manifests that are found, shared and redacted only on ingredient use, against Traceweave's private-by-default records.

**What Traceweave requires that C2PA cannot carry, except as opaque bytes**
1. Outcome classes and the closed code list: `match`, `no-match`, `abstain`, and the pair, mode and report rejection sides (contract §6.4).
2. Minimum evidence (`minRegionDistinctHashes`, distinct-hash evidence), ambiguity, and the "at the minimum" rendering rule (contract §5.6–§5.7, §8).
3. Abstention reasons: `insufficient-tokens`, `seed-limit-exceeded`, `ambiguous`, and the image `low-quality` and decode codes. An abstaining entry leaves no trace in C2PA.
4. The suppression catalogue digest and its advisory meaning (contract §5.2).
5. Raw-count containment and Jaccard fractions, never reduced and never a score. The C2PA side offers only a 0–100 `similarityScore`.
6. Byte spans and region keys (§4.2).
7. Binding of the profile triple and configuration digest. In C2PA this survives only in `bindingMetadata`, which validators should not use.
8. Catalogue commitments, opening rules and privacy classes (core).
9. Detector threshold, calibration identifier, search scope and the separation of presence, payload and identity (lane 08).
10. Absence semantics: `no-match` is "insufficient evidence", not "not derived".

## 6. Open decisions

| ID | Question | Options | Draft position |
| --- | --- | --- | --- |
| D1 | Which C2PA version C2PA.1 pins | 2.5 (current, October 2026); 2.4 (lane 10's reading) | 2.5. Check whether the C2PA.2 tool supports 2.5 before freezing |
| D2 | How a report travels | A, B or C (§3) | B now; C optional and owner-gated |
| D3 | Namespace for labels, `alg` ids and the report predicate type | **Domain settled:** `traceweave.org` (2026-11-23). Open: which names to fix (`org.traceweave.comparison-report`, `org.traceweave.pdq.draft-2`, `org.traceweave.go-tokens.<channel>.draft-1`, predicate `https://traceweave.org/predicate/comparison-report/draft-2`), and whether to publish documentation at those URLs | Use `org.traceweave.*` as proposed identifiers; register or publish nothing until the owner decides |
| D4 | PDQ soft-binding id | Register a Traceweave entry (needs D3 and a public contact); ask the PDQ maintainers for a neutral entry; reuse `com.originalpictures.pdq.1` | Do not export PDQ until decided. Reuse is not recommended (§2.1) |
| D5 | ISCC export | New profile version emitting IEP-0020 sequences (256-bit Image-Code, Data-Code, Instance-Code, featureless test); no ISCC export | No export until a profile version and vectors exist |
| D6 | Token-catalogue export | Never into manifests (privacy, §1.3); only keyed fingerprints after KEYED; register a code-token algorithm | Never into public manifests |
| D7 | C2PA.2 tool | c2pa-rs `c2pa-v0.92.2` built project-locally under the network-denied harness; c2pa-python; c2patool | c2pa-rs (two languages already in the implementation track; MIT/Apache-2.0 to recheck). The download and build need owner approval |
| D8 | How a statement binds a manifest | SHA-256 of the serialized manifest store; hash of the claim signature box; hashed URI of the active manifest | Manifest store SHA-256 plus the manifest URN; decide when a store can actually be serialized |
| D9 | Image region convention for an export | State "after EXIF orientation, origin top-left, pixel units, image size in a companion field"; export no regions | No regions in exports until C2PA states a basis or the owner accepts a convention |
| D10 | C2PA.2 wording | Keep "round-trip … in both directions"; reword to "every mapped field survives a round trip through the tool and the adapter, and every lossy, opaque, unmapped or conflicting field is declared" | Reword. A lossless round trip is impossible for soft bindings (f5 keeps two of 20 fields), so the current wording cannot pass as written |
| D11 | Resolver use | None; client-side `byBinding` queries only; `byContent` uploads | None, until the RES gates |

## 7. Before any "compatible" or "interoperable" wording

C2PA.3 forbids a compatibility claim until C2PA.2 passes. A claim needs **all** of the following statements, each with a recorded command and result:

1. **Tool pin:** name, version, commit, licence and build hashes of an open-source C2PA implementation, built and run offline (D7).
2. **Tool reads our output:** each C2PA-side fixture, serialized to real CBOR and JUMBF and signed with a test certificate under a test-only trust anchor, is read by the tool. The tool's validation status codes are recorded per fixture, separately for well-formed, valid and trusted.
3. **We read the tool's output:** manifests written by the tool (hard binding, soft binding, gathered custom assertion, external reference) pass through a Traceweave adapter. Every mapped field is recovered, and every lossy, opaque, unmapped or conflicting field is reported.
4. **Round-trip record:** for each fixture, the fields that survived and the fields that were lost, both directions, with the checker passing.
5. **Scope:** C2PA version, assertion labels, media types, manifest placement (embedded or sidecar) and validator state. "Trusted" is claimed only with a real trust-list signer.
6. **Soft-binding status:** for each exported `alg`, either the registered entry and its commit, or the statement "proposed identifier, not registered anywhere".
7. **Review:** a non-author recheck of the mapping (C2PA.1) and of statements 1–6.

**Wording allowed until then** (exact):

> Traceweave has a draft, unreviewed mapping between its records and C2PA 2.5 structures, with illustrative fixtures. No C2PA implementation has read or written any Traceweave fixture. Traceweave makes no C2PA compatibility or interoperability claim.

Not allowed: "compatible", "interoperable", "compliant", "conformant", "certified", "supports C2PA", "C2PA-ready", "works with Content Credentials", or a C2PA logo or "CR" mark. Even after C2PA.2 passes, wording stays bounded: "interoperates with <tool> <version> for <listed fixtures>", never an unqualified claim.

## 8. Fixtures and checker

[c2pa-fixtures/](c2pa-fixtures/README.md) holds seven positive fixtures (`f1`–`f7`). Each C2PA side is written by hand in JSON diagnostic form, labelled illustrative, and unsigned.

| Fixture | Case | Checker result |
| --- | --- | --- |
| f1 | Image PDQ fingerprint as a soft-binding assertion beside a whole-file hard binding | no failure |
| f2 | Report as a gathered custom assertion carrying the exact body bytes | no failure; body digest re-derived |
| f3 | Report as an in-toto statement referencing the candidate's manifest | no failure |
| f4 | Invented mark-detection record against the embedder's soft binding and `c2pa.watermarked.bound` | no failure |
| f5 | Round trip of f1: 2 of 20 leaf fields survive, 18 are listed as lost | no failure |
| f6 | Go token-catalogue entry as two soft-binding assertions | no failure |
| f7 | Sidecar manifest linking to an M4 registration statement via `tw1-` reference and `statementSha256` | no failure; `tw1-` check and prefix re-derived |

Twenty-two negative fixtures each change one thing in a positive fixture and must be rejected with exactly their expected code. They include a lossy field silently dropped (`neg-lossy-dropped`, `lossy-undeclared`), a claim of compatibility (`neg-compatibility-claim`, `claim-wording`), and four registration-link negatives (`neg-reg-tw1-bad-check`, `neg-reg-tw1-statement-mismatch`, `neg-reg-same-bytes-exclusions`, `neg-reg-created-attribution`). The checker also fails if any rule pointer is missing from this document. Commands and the full code list are in the [fixtures README](c2pa-fixtures/README.md).

**C2PA tool availability.** No `c2patool` is on the path, no `c2pa` Python module can be imported, and the local Cargo and Go module caches hold no C2PA crate or module. Nothing was installed (no global installs; any download needs the owner). **No fixture was validated by a C2PA implementation.** The fixtures check this mapping's own rules, not C2PA conformance.

## 9. Gate status

| Gate | Status after this draft |
| --- | --- |
| C2PA.1 | **Audited & complete for non-author review (2026-11-25).** Pinned to C2PA 2.5, uses the owned `traceweave.org` (`org.traceweave.*`) namespace, classifies every field (mapped / lossy / opaque / unmapped / conflicting) across catalogues, reports, mark detection, and M4 `tw1-` registration linkage (§1.2–§1.8), with `check_fixtures.py` wired into `tools/validate.py`. Needs non-author review and D1 |
| C2PA.2 | **Open.** No C2PA tool was available or run; no adapter exists; the fixtures are hand-written. D7 (tool download) and D10 (wording) need the owner |
| C2PA.3 | **Met and enforced (2026-11-25):** `README.md` makes no C2PA claim, `spec/attestations.md` states "No C2PA compatibility is claimed yet", `docs/sources.md` cites C2PA 2.5 without claiming compatibility, and `check_fixtures.py` enforces `claimWordsPattern` in `tools/validate.py` |

**Needs the owner:** D3 (fixing the `org.traceweave.*` names, any public contact for a list entry, and anything published under `traceweave.org`), D4 and D6 (whether fingerprints may leave the private catalogue at all), D7 (downloading and building a C2PA tool), D10 (the C2PA.2 wording), and any registration pull request.
