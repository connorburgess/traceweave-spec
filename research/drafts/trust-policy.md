# Verifier trust policy specification (draft)

Status: working draft for core gate M4.5, aligned with [attestations](../../spec/attestations.md) and [registration-record.md](registration-record.md) (draft-5). Not legal advice.

## 1. Purpose and scope

This document specifies the **verifier-local trust policy** for evaluating Traceweave in-toto/DSSE attestations and registration bundles.

Trust is strictly a verifier policy decision, never a property of the artifact or an assertion inside the signed payload:
- Cryptographic signature validity, signer trust, subject digest matching, possession verification, time-bound quorum, and claimed fields MUST be evaluated and reported as **separate outcomes**.
- A valid signature under a trusted key with quorum time evidence establishes only that *exact bytes named by the statement existed, and that key signed the statement, no later than bound `T`*.
- Verification **never** establishes authorship, originality, first-creation, ownership, or permission (`notShown`: `authorship`, `originality`, `first-creation`, `ownership`, `permission`). **First to register is not first to create.**

## 2. Policy structure and fail-closed validation

A verifier policy is a local JSON configuration object with exact fields:

```json
{
  "quorum": 2,
  "trustedKeys": ["<64 lowercase hex SHA-256 of raw 32-byte Ed25519 public key>"],
  "recoveryKeys": [
    {
      "keySha256": "<64 hex>",
      "recovers": "<64 hex>",
      "notBefore": "2026-11-29T00:00:00Z"
    }
  ],
  "timeRoots": [
    {
      "anchorSha256": "<64 hex>",
      "kind": "tsa-certificate-chain",
      "independenceGroup": "tsa-operator-a",
      "policyOids": ["..."],
      "accuracySeconds": 1,
      "rootCertificate": "<local path>"
    },
    {
      "anchorSha256": "<64 hex>",
      "kind": "bitcoin-proof-of-work",
      "independenceGroup": "bitcoin",
      "headerFile": "<local path>",
      "minConfirmations": 6,
      "checkpoint": {
        "height": 12,
        "headerSha256": "<64 hex>"
      }
    }
  ],
  "revocationData": [
    {
      "anchorSha256": "<64 hex>",
      "source": "<retained local CRL/OCSP description or path>",
      "asOf": "2026-11-24T12:00:00Z",
      "revocations": [
        {
          "certificateSha256": "<64 hex>",
          "revokedAt": "2026-11-24T00:00:00Z",
          "reasonCode": "keyCompromise"
        }
      ]
    }
  ],
  "compromiseLookbackSeconds": 2592000,
  "verificationTime": "2026-11-24T12:00:00Z"
}
```

### Fail-closed policy checks

A verifier MUST refuse the policy and abort verification before inspecting evidence if any of the following hold:
1. **Strict JSON parsing fails:** duplicate object keys (including JSON-escaped collisions) or non-finite numbers (`NaN`, `Infinity`, `-Infinity`) are present.
2. **Invalid `quorum`:** not an integer or `< 1` (recommended default: `2`).
3. **Invalid `compromiseLookbackSeconds`:** not an integer or `< 0` (fixture default: `2592000`, i.e., 30 days; policy choice trading late-theft discovery against historical stability).
4. **Hint-based key lists:** `trustedKeys`, `recoveryKeys`, or any policy field identifies keys by 16-hex `keyid` hints or carries deprecated `trustedKeyids` (`key-identity-by-hint`).
5. **Malformed `recoveryKeys`:** missing `keySha256`, `recovers`, or `notBefore`, non-64-hex key digests, or invalid RFC 3339 UTC `notBefore` timestamp.
6. **Malformed `timeRoots`:** missing `anchorSha256`, `kind`, or `independenceGroup`; non-64-hex `anchorSha256`; or for `bitcoin-proof-of-work`, `minConfirmations < 1` or missing/malformed `checkpoint` (`height`, `headerSha256`).
7. **Missing or invalid `verificationTime`:** not a valid RFC 3339 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`).

## 3. Zero reliance on unverified hints

Verifiers MUST NOT treat producer-supplied metadata or envelope hints as authoritative:

| Input surface | Allowed role | Forbidden reliance |
| --- | --- | --- |
| DSSE `signatures[i].keyid` | Lookup hint to select a candidate key from `verificationMaterial.publicKeys`; missing or unmatched hint yields `unknown-key` (no trial verification) | Never used to grant signer trust or evaluate key events (`key-identity-by-hint`). Full identity is `SHA-256(raw 32-byte public key)`. |
| Key-event `predicate.keyid` | Consistency check only: MUST equal the first 16 lowercase hex chars of `subject[0].digest.sha256` (`key-event-shape`) | Never used as event target or signer identity. |
| Evidence `root.anchorSha256` and producer labels | Lookup key only; MUST be recomputed by the verifier from local pinned material (`rootCertificate` DER bytes, local header chain first header, or raw witness/log key) | Producer-written names, URLs, or claimed anchor hashes are never trusted (`root-not-anchored`). |
| Bitcoin `blockTime` | Read exclusively from the verifier's own pinned header source up to `checkpoint` | Any `blockTime` carried in an evidence object is ignored or rejected if mismatched. |
| `claims.createdAt` / `recordedAt` | Echoed and compared as `claimed-only` against trusted signatures' earliest `notAfterAnyRoot` (or `not-compared` if no trusted signature) | Never reported as proved time (`claimed-as-proved`). |
| `claims.aiUse` | Echoed verbatim as `declared-not-checked` (or `{"status": "not-declared"}` when absent) | Never verified and never allowed to alter trust, time, key-event, or digest outcomes (`ai-use-affected-outcome`). |
| DSSE `payload` base64 text | Transport encoding only (standard or URL-safe base64 MUST be accepted) | Never hashed or signed directly; PAE signs exact decoded payload bytes (`signature-invalid`). |

## 4. Trusted signer keys, key events, and recovery keys

### 4.1 Strict signature and parsing rules

- **Strict JSON:** Reject duplicate keys recursively (in envelope, statement, and policy) and reject non-finite numbers before cryptographic or schema checks.
- **DSSE PAE:** Verify signatures over `PAE(payloadType, raw_decoded_payload_bytes)` with `payloadType == "application/vnd.in-toto+json"`. Retain the verified `raw_decoded_payload_bytes` through statement parsing and digest checks.
- **Ed25519 rule set:** Follow RFC 8032 §5.1.7 cofactorless equation `[S]B = R + [k]A`, rejecting keys not equal to 32 bytes, signatures not equal to 64 bytes, `S >= L`, non-canonical encodings of `A` or `R` (`y >= p`, or `x = 0` with sign bit set), and public keys `A` of small order (`[8]A == identity`).

### 4.2 Signer trust evaluation

A signature at index `i` by key `D` (identified by `keySha256`) is evaluated against `trustedKeys`, `recoveryKeys`, and verified `keyEvents` using **quorum bounds only**:
1. **No quorum bound:** If any applied or disputed key event targets `D` or names `D` as successor, and signature `i` has no quorum bound (`below-quorum` or `none-valid`), signer trust MUST be `disputed` (never `trusted`). Single-source time cannot resolve key-event ordering.
2. **Trusted roots:** `D` is initially trusted if `D in trustedKeys` (valid for all bounds), or if `D` is listed in `recoveryKeys` with `recovers in trustedKeys` and `notBefore <= B` (where `B` is the signature's `notAfterQuorum`; recovery keys are never retroactive and never sign events for the key they recover).
3. **Key-event standing (Pass 1) and disputes (Pass 2):**
   - Each key-event envelope MUST carry **exactly one** signature (`key-event-signatures`), is identified by `SHA-256(payload || signature)`, and requires its own quorum time bound `E` (otherwise `ignored-no-proved-time`).
   - **Pass 1 (standing):** Process events in ascending order of `E` (tie-breaking by event identity, never input list order). An event is authorized only if signed by its target key `K` or by the successor named in an earlier-`E` applied rotation of `K` (even if disputed). The first applied `rotated` or `retired` event for `K` supersedes `K`: later non-`compromised` events signed by `K` and later rotations/retirements of `K` by any signer are `ignored-superseded`. Pass 1 never consults disputes.
   - **Pass 2 (disputes):** Two distinct supersessions of `K` at the same `E` are both `disputed`. An applied `compromised` event with claimed `Tc` and proved time `E` sets `start = max(Tc, E - compromiseLookbackSeconds)` and disputes every applied rotation/retirement of `K` with `E_rot >= start`, **except** the appointment rotation(s) of `K` to the report's own signer (twin statements at the same `E_rot` are treated as one appointment). Disputes never feed back into Pass 1.
4. **Trust propagation and restriction:**
   - Trust flows forward only through an applied, **undisputed** rotation proved strictly after its signer became trusted (`E_rot > T_trusted`), granting trust to the successor for `B >= E_rot`.
   - For an applied `compromised` event on `D`: bounds `B < start` keep prior trust; `start <= B < E` become `disputed`; `B >= E` become `untrusted`.
   - For an applied `retired` or `rotated` event on `D` (disputed or not): bounds `B >= E` become `untrusted`.

## 5. Time roots, independence groups, and quorum

- **Anchor-keyed roots:** Every accepted time source MUST be listed in `timeRoots` by its verifier-computed `anchorSha256` and `kind`:
  - `tsa-certificate-chain`: SHA-256 of the pinned DER root certificate.
  - `bitcoin-proof-of-work`: SHA-256 of the first block header in the verifier's own header source.
  - `witness-service-key`: SHA-256 of the witness's raw public key.
  - `log-key` (`rekor-v2`): inclusion/discoverability only; carries **no time bound** (`log-time-claimed` if time is claimed).
- **Independence groups:** Each `timeRoots` entry declares a verifier-assigned `independenceGroup`. Two TSAs sharing the same root CA or the same `independenceGroup` count as one source. If a single time evidence relies on multiple anchors (for example, `traceweave-witness` depends on both `witness-service-key` and its backing `tsa-certificate-chain`), all co-occurring groups in that evidence are merged via union-find across the bundle.
- **Per-signature bounds and quorum:**
  - Only valid non-renewal time evidence targeting signature `i` (by SHA-256 of raw decoded signature bytes) contributes to signature `i`. Co-signers never inherit bounds (`key-bound-misattributed`).
  - Within each merged independence class, take the minimum `notAfter`. Sort class minima ascending.
  - `notAfterAnyRoot` is the smallest class minimum (`distinctRoots >= 1`).
  - `notAfterQuorum` is the `quorum`-th smallest class minimum (`quorum-met` when `distinctRoots >= quorum`; `below-quorum` when `1 <= distinctRoots < quorum`; `none-valid` when `distinctRoots == 0`). Both bounds and `distinctRoots` are always reported.

## 6. Explicit refusal of untrusted or unpinned roots

A verifier MUST refuse (never count toward `distinctRoots` or bounds):
1. **Unlisted or unpinned roots:** Any evidence whose computed `anchorSha256` is absent from `timeRoots` for its `kind` MUST receive outcome `untrusted-root`.
2. **Test-only / synthetic anchors:** Public fixture roots (such as `research/drafts/registration-fixtures/real-format/`) MUST NEVER be placed in a production trust policy.
3. **Unpinned OpenTimestamps chains:** An `opentimestamps` proof without a local header source and pinned `checkpoint` (`minConfirmations >= 1`) MUST receive `unsupported`; a proof whose attested height fails `height <= checkpoint.height - minConfirmations` or does not link back from `checkpoint` through `prevBlockHash` MUST receive `insufficient-confirmations`. Pending proofs MUST receive `pending` and never count (`pending-counted`).
4. **Invalid RFC 3161 paths or disallowed policy OIDs:** Tokens failing RFC 5280 validation at `genTime` (non-CA issuer, expired intermediate, non-critical or missing `id-kp-timeStamping` EKU, mismatched `ESSCertID`/`ESSCertIDv2`, bad signature/imprint) MUST be refused (`path-invalid`, `tsa-*`), and tokens whose policy OID is absent from `timeRoots[].policyOids` MUST receive `wrong-policy`. Unsupported cryptographic algorithms (such as ECDSA or RSA-PSS where only RSA PKCS #1 v1.5 + SHA-256 is supported) MUST be reported as `unsupported`, never accepted.
5. **Placeholder evidence:** Any evidence with `placeholder: true` or `PLACEHOLDER` token prefix MUST be refused in production verification.

## 7. Revocation freshness and offline-first evaluation

- **Offline-first execution:** Verification MUST execute with zero network access against locally retained material: the bundle, pinned `rootCertificate` files, token-embedded intermediate certificates, retained `revocationData`, and the verifier's local Bitcoin header file + `checkpoint`.
- **Mandatory revocation data for RFC 3161:** Every `tsa-certificate-chain` root MUST have a `revocationData` entry specifying `source` and `asOf`. If revocation data is missing for a token's anchor, the token MUST receive `no-revocation-data` and MUST NOT count toward quorum.
- **Explicit "as of" validity:** Every RFC 3161 evidence result reports `revocationDataAsOf`. Offline verification holds **only as of `asOf`**: a subsequent `keyCompromise` or reasonless revocation can invalidate past tokens retroactively (RFC 3161 §4 items 1–2).
- **Certificate-level revocation semantics:** Revocations name individual signing or intermediate certificates (`certificateSha256`), never the root anchor.
  - Reasonless revocation or `keyCompromise` invalidates **all** tokens on paths containing that certificate, regardless of `genTime` (`revoked`).
  - Retaining reason codes (`unspecified`, `affiliationChanged`, `superseded`, `cessationOfOperation`) preserve tokens with `genTime < revokedAt` and reject tokens at or after `revokedAt`.
- **Expiry and renewal:** If `verificationTime` is after the TSA certificate's `notAfter`, the token receives `expired-unrenewed` unless covered by a valid RFC 3161 renewal targeting the earlier token's raw bytes (`kind: "evidence-token"`) with `notAfter <= expiredCert.notAfter` (and the earlier certificate was not revoked with `keyCompromise` or without a reason code).
