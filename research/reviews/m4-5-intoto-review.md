# Independent non-author review: `m4-5-intoto` (`0476cec`)

Reviewed 2026-11-25 against branch `m4-5-intoto` at commit `0476cec` (branched from `roadmap-v2` at `52b0702`). I wrote none of the reviewed deliverables.

**Verdict: `merge after fixes`.**

[trust-policy.md](../drafts/trust-policy.md) and [timestamp-adapter-decision.md](../drafts/timestamp-adapter-decision.md) align cleanly with [registration-record.md](../drafts/registration-record.md) (draft-5), [attestations.md](../../spec/attestations.md), and [13-timestamp-evidence-review.md](../lanes/13-timestamp-evidence-review.md), with zero contradictions. All existing repository validators, unit tests, link checks, and hygiene checks pass, and [build_fixtures.py](../drafts/intoto-adapter-fixtures/build_fixtures.py) reproduces all 4 accept and 21 reject fixtures byte-identically. However, adversarial probing of [check_intoto_adapter.py](../drafts/intoto-adapter-fixtures/check_intoto_adapter.py) surfaced **two blocking defects** in the adapter checker:

1. **B1 (Authorship/origin smuggling bypass in non-`aiUse` predicate strings and `subject[].name`, plus unconstrained `contentKind` in registration mode).** `_scan_smuggling()` checks predicate string values only against the 7-phrase `SMUGGLED_VALUE_PHRASES` regex rather than `AUTHORSHIP_DENY`, and skips `subject[].name`. Combined with registration-mode `predicate.contentKind` accepting any non-empty string (`check_intoto_adapter.py` line 591), adversarial statements smuggling `"authored by Bob"`, `"proves authorship"`, or `"first to create"` in `predicate.contentKind` (registration mode), `predicate.implementation.name`, or `subject[0].name` (core mode) are accepted.
2. **B2 (`predicate.possession` order/index mismatch in `validate_statement()`).** Lines 604–619 allow `predicate.possession` entries in any permutation of `subjectIndex` (`0..len(subjects)-1`), whereas lines 678–682 index `pred["possession"][idx]` by list position rather than matching `entry["subjectIndex"] == idx`. A multi-subject registration with `possession` ordered `[1, 0]` passes when `artifacts` are omitted, and fails with `possession-mismatch` when `artifacts` are supplied even when digests match by `subjectIndex`.

---

## 1. Checks executed

The worktree has no local `.venv`, so Python checks ran using the sibling checkout's Python 3.12 virtual environment (`../traceweave-spec/.venv/bin/python`). All repository scripts resolve paths relative to `__file__` inside this worktree.

| Check | Outcome | Notes |
| --- | --- | --- |
| `check_intoto_adapter.py --verbose` (`-I`) | **PASS** (exit 0) | `4 accept, 21 reject, 17/17 reject codes covered, self-tests passed` |
| `build_fixtures.py` clean-room rebuild (temp copy) | **PASS** | Byte-identical across all 4 `accept/*.json` and 21 `reject/*.json` fixtures |
| `tools/validate.py` | **PASS** (exit 0) | Includes `in-toto adapter fixtures (M4.5)` in `VECTOR_CHECKERS` |
| `tools/validate.py --links-all` | **PASS** (exit 0) | All local Markdown links valid |
| `python -m unittest discover -s tests -v` | **PASS** (exit 0) | `Ran 11 tests in 14.493s`, `OK` (includes `test_intoto_core_accept_fixtures_match_statement_schema`) |
| `tools/check_hygiene.py` | **PASS** (exit 0) | Tree clean |
| `tools/check_hygiene.py --messages 52b0702..0476cec` | **PASS** (exit 0) | Tree and commit message clean |

---

## 2. Deliverable review

### 2.1 Trust-policy fidelity (`research/drafts/trust-policy.md`)

Cross-checked [trust-policy.md](../drafts/trust-policy.md) against [registration-record.md](../drafts/registration-record.md) (draft-5), [check_registration.py](../drafts/registration-fixtures/check_registration.py), and [attestations.md](../../spec/attestations.md). Zero contradictions found:

- **Separate outcomes and non-authorship scope (§1):** Keeps signature validity, signer trust, subject digest, possession, time bounds/quorum, and claims strictly separate, and fixes `notShown` (`authorship`, `originality`, `first-creation`, `ownership`, `permission`) and `"First to register is not first to create."`
- **Fail-closed policy validation (§2):** Matches `POLICY_KEYS` (`quorum`, `trustedKeys`, `recoveryKeys`, `timeRoots`, `revocationData`, `compromiseLookbackSeconds`, `verificationTime`), rejects duplicate JSON keys (including escaped collisions) and non-finite constants, requires `quorum >= 1` integer, `compromiseLookbackSeconds >= 0` integer, valid RFC 3339 UTC `verificationTime` and `recoveryKeys[].notBefore`, rejects hint-based trust lists (`keyid` / `trustedKeyids` -> `key-identity-by-hint`), and validates `timeRoots` including `minConfirmations >= 1` and `checkpoint` for `bitcoin-proof-of-work`.
- **Zero reliance on unverified hints (§3):** Confirms DSSE `signatures[i].keyid` is a lookup hint only (`unknown-key` on miss, no trial verification), key-event `predicate.keyid` must match the first 16 hex chars of `subject[0].digest.sha256` (`key-event-shape`), `root.anchorSha256` is recomputed from local pinned material (`rootCertificate` DER, first local header, or raw witness/log key -> `root-not-anchored`), Bitcoin `blockTime` comes exclusively from the verifier's pinned header chain, `claims.createdAt`/`recordedAt` remain `claimed-only` (or `not-compared` without a trusted signature), `claims.aiUse` is echoed as `declared-not-checked` / `not-declared` without altering outcomes (`ai-use-affected-outcome`), and PAE signs exact decoded payload bytes.
- **Two-pass key events and Ed25519 rule set (§4):** Matches §10.1 cofactorless Ed25519 (`[S]B = R + [k]A`, rejecting non-32B keys, non-64B signatures, `S >= L`, non-canonical `A`/`R` with `y >= p` or `x = 0` with sign bit set, and small-order `A` with `[8]A == identity`). Key-event evaluation matches draft-5 E1 verbatim: no-quorum touched signers are `disputed`, single-signature key-event envelopes (`key-event-signatures`) keyed by `SHA-256(payload || signature)` require quorum time `E`, Pass 1 (standing) processes in ascending `(E, eventSha256)` without consulting disputes and applies supersession, Pass 2 (disputes) resolves ties and `compromised` windows `[max(Tc, E - compromiseLookbackSeconds), E)` with the appointment-twin exemption, and trust flows forward only for undisputed rotations strictly after `T_trusted`.
- **Independence groups and quorum (§5):** Anchor-keyed roots (`tsa-certificate-chain`, `bitcoin-proof-of-work`, `witness-service-key`, `log-key` carrying no time bound), union-find merging across co-occurring anchors (e.g. `traceweave-witness`), per-signature non-renewal bounds (`notAfterAnyRoot`, `notAfterQuorum`, `quorum-met` / `below-quorum` / `none-valid`).
- **Explicit refusal of untrusted/unpinned roots and offline revocation freshness (§6–§7):** Refuses unlisted anchors (`untrusted-root`), test-only fixture roots, unpinned/insufficient-confirmation/pending OTS proofs (`unsupported`, `insufficient-confirmations`, `pending`), invalid RFC 3161 paths/OIDs/algorithms (`path-invalid`, `wrong-policy`, `unsupported`), and placeholder evidence. Executes strictly offline against retained `revocationData` (mandatory per TSA root -> `no-revocation-data`), reports `revocationDataAsOf`, enforces certificate-level `keyCompromise`/reasonless retroactive invalidation vs retaining-reason cutoff, and supports RFC 3161 token renewal (`expired-unrenewed` otherwise).

### 2.2 Timestamp adapter decision (`research/drafts/timestamp-adapter-decision.md`)

Verified [timestamp-adapter-decision.md](../drafts/timestamp-adapter-decision.md) against [ROADMAP.md](../../ROADMAP.md) (M4.5), [13-timestamp-evidence-review.md](../lanes/13-timestamp-evidence-review.md), [registration-record.md](../drafts/registration-record.md), and [trust-policy.md](../drafts/trust-policy.md):

- Accurately keeps timestamping an **optional** adapter: untimestamped DSSE statements remain valid signed statements, reporting `none-valid` for per-signature time outcomes and `claimed-only` (or `absent` / `not-compared` when no trusted signature exists) for `claims.createdAt`/`recordedAt`, never upgrading claimed dates (`claimed-as-proved`).
- Accurately captures **offline-first verification** of RFC 3161 (retained DER roots, RFC 5280 path validation at `genTime`, retained `revocationData` with `revocationDataAsOf`, RFC 4998-style renewal) and upgraded OpenTimestamps (verifier's own header source and pinned `checkpoint` with `minConfirmations >= 1`, `notAfter = blockTime + 7200s` under the stated honest-majority assumption, `pending` never counted), plus the recommended two-unrelated-TSA + OpenTimestamps baseline at `quorum = 2`.
- Accurately records **`REG.3` owner-gating** for any live external TSA, OpenTimestamps calendar, transparency log, or witness contact (zero outbound network calls in `validate.py`, offline verifiers, or CI; even a single synthetic test digest requires owner approval covering provider terms, IP/timing metadata exposure, and permanent Bitcoin Merkle root anchoring).

### 2.3 in-toto adapter checker & fixtures (`research/drafts/intoto-adapter-fixtures/`)

Reviewed [README.md](../drafts/intoto-adapter-fixtures/README.md), [check_intoto_adapter.py](../drafts/intoto-adapter-fixtures/check_intoto_adapter.py), [build_fixtures.py](../drafts/intoto-adapter-fixtures/build_fixtures.py), [tools/validate.py](../../tools/validate.py), and [tests/test_contract.py](../../tests/test_contract.py).

- **Adversarial input probes (run in memory against unmodified `check_intoto_adapter.py`):**
  - *Ed25519 canonicality & strictness:* `S >= Q` malleated signature, non-canonical `R` (`y >= P`), non-canonical `R` (`x = 0` with sign bit set, both `y = 1` and `y = P - 1`), small-order `A` (identity and order-2 point `(0, P - 1)` with `R = A, S = 0`), non-canonical `A` (`y >= P`), and 63-byte signatures all returned `['signature-invalid']`.
  - *`claims.aiUse.tool` and nested smuggling:* `HumanMade`, `NoAIUsed`, `Penned-by-Bob`, `AI-free`, `Not.AI`, `100pct-Human`, `writtenByAlice`, `organicModel`, `original-v1`, `author-bot`, nested `claims.aiUse.creator`, nested `claims.Originality`, and `implementation.name = "Created by Alice"` all returned `['authorship-claim']`; `tool` with `declared: "no-generative-ai"` returned `['statement-shape']`. (Lowercase unseparated tokens `"nonhuman"` / `"humanwritten"` pass `token_parts()`, matching `registration-record.md` §4.7.)
  - *B1 bypasses observed (without `expectedRoundTrip`):* `predicate.contentKind = "authored by Bob"`, `predicate.implementation.name = "proves authorship"`, `subject[0].name = "written by Alice"` (core mode), and `subject[0].name = "authored by Alice"` (core mode) all returned `[]` (`accepted=True`).
  - *B2 bug observed (without `expectedRoundTrip`):* Swapping `predicate.possession` to `[subjectIndex: 1, subjectIndex: 0]` on `accept-registration-ai-use` returned `['possession-mismatch']` with `artifacts` present, and `[]` (`accepted=True`) if `artifacts` were omitted.
  - *Duplicate keys & non-finite JSON:* Nested duplicate key (`predicate.specVersion`) and JSON unicode-escaped duplicate key (`\u005ftype` vs `_type`) both returned `['duplicate-key']`; `NaN` in payload returned `['statement-shape']`.
  - *Missing/extra fields & wrong types:* Missing/extra fields in `predicate.profile`, `subject[0]`, and `subject[0].digest`, wrong `_type`, arbitrary `predicateType`, `payloadType` with `; charset=utf-8`, and subject digest mismatch on subject 1 of multi-subject registration all returned their expected rejection codes.
- **In-memory sabotage probes (mutating `check_intoto_adapter.py` in memory against committed fixtures):**
  - Caught (exit 1): ignoring duplicate keys, signing base64 text instead of decoded payload bytes, and skipping subject digest verification.
  - **Missed (exit 0, see Advisory A1):**
    1. Disabling `s >= Q or _equal(_mul(8, a), IDENTITY)` -> exit 0.
    2. Bypassing `_decompress(sig[:32])` canonical-`R` rejection -> exit 0.
    3. Disabling `tool_has_origin_claim(tool)` -> exit 0 (because `reject-authorship-smuggling-value.json` uses `"human-written-by-alice"`, which already matches `SMUGGLED_VALUE_PHRASES`).
    4. Checking trust by 16-hex `keyid` hint (`hint in {k[:16] for k in trusted_set}`) -> exit 0.

---

## 3. Required and advisory fixes before merge

### Blocking

1. **B1 (`check_intoto_adapter.py`):**
   - Restrict registration-mode `predicate.contentKind` to a closed vocabulary (matching `registration-record.md` / `check_registration.py` `{"text", "source-code", "image", "other"}`, or core's `CORE_CONTENT_KINDS` if shared) rather than any non-empty string.
   - Check string values inside `predicate` (and `subject[].name` in core mode) against `AUTHORSHIP_DENY` as well as `SMUGGLED_VALUE_PHRASES` in `_scan_smuggling()`, and add a negative fixture verifying that authorship wording such as `"proves authorship"` or `"authored by Bob"` is rejected outside `claims.aiUse.tool` too.
2. **B2 (`check_intoto_adapter.py`):**
   - Fix `validate_statement()` lines 678–682 so `possession` matching looks up the entry with `entry["subjectIndex"] == idx` instead of indexing `pred["possession"][idx]` by list position (or enforce `entry["subjectIndex"] == i` at lines 604–619, matching `check_registration.py` line 535).

### Advisory (non-blocking)

- **A1 (`check_intoto_adapter.py` / `build_fixtures.py` regression coverage):** Add reject fixtures or `run_self_test()` cases covering (a) a `claims.aiUse.tool` value caught specifically by `tool_has_origin_claim()` (e.g., `"Penned-by-Bob"` or `"NoAIUsed"` rather than `"human-written-by-alice"`, which overlaps `SMUGGLED_VALUE_PHRASES`), (b) non-canonical Ed25519 `S >= Q`, non-canonical `R`, and small-order `A`, and (c) an untrusted key whose 16-hex `keyid` collides with a trusted key's hint (or a self-test mutating `hint` to verify full `pub_sha` trust).
- **A2 (`trust-policy.md` §4.2 item 2 & `ROADMAP.md` M4.5):** In `trust-policy.md` §4.2 item 2, note explicitly that a `recoveryKeys` entry applies when its `recovers` target is in `trustedKeys` (matching `check_registration.py` line 1064). Keep `ROADMAP.md` M4.5 `open` until B1–B2 are resolved and confirmed.
