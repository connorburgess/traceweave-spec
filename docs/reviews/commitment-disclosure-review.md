# Independent non-author review: Commitment and selective-disclosure design (M4.6)

Reviewed 2026-11-25 against [ROADMAP.md](../../ROADMAP.md) (`M4.6` criterion) at local commit `b193376` on `roadmap-v2`. I wrote none of the reviewed specifications, drafts, vectors, or harnesses.

**Scope inspected:**
- [spec/attestations.md](../../spec/attestations.md)
- [spec/core.md](../../spec/core.md#private-catalogue-commitment), [spec/catalogue-report.md](../../spec/catalogue-report.md#37-commitment-and-privacy-class), [spec/threat-model.md](../../spec/threat-model.md), [schemas/statement.schema.json](../../schemas/statement.schema.json), [schemas/evidence.schema.json](../../schemas/evidence.schema.json)
- [research/drafts/registration-record.md](../../research/drafts/registration-record.md) (§4.1–§4.4, §5, §9, §10, §12) and [research/drafts/registration-fixtures/check_registration.py](../../research/drafts/registration-fixtures/check_registration.py)
- [test-vectors/commitment.json](../../test-vectors/commitment.json) and [examples/catalogue.json](../../examples/catalogue.json)
- [research/experiments/signing-interop/policy-results.json](../../research/experiments/signing-interop/policy-results.json), [run_policy.py](../../research/experiments/signing-interop/run_policy.py), and [signing-policy-results.md](../../research/lanes/signing-policy-results.md)

**Verdict: `changes required` (`M4.6` stays `open`).**
Found **2 blocking findings** (`CD-B1`, `CD-B2`) and **5 advisory findings** (`CD-A1`–`CD-A5`), all requiring explicit disposition before `M4.6` can be marked `met`.

---

## 1. Cryptographic and adversarial assessment

| Surface | Design mechanism | Assessment |
| --- | --- | --- |
| Domain & length framing | `SHA256("Traceweave-Catalogue-v0.1\x00" \|\| R[32] \|\| uint64be(len(C)) \|\| C)` and `SHA256("Traceweave-Possession-v1\x00" \|\| nonce[32] \|\| uint64be(len(A)) \|\| A)` | Sound construction when `len(nonce) == 32` is enforced: fixed-width domain tag + fixed 32-byte salt + fixed 8-byte big-endian length precede the payload, preventing domain confusion and length-boundary ambiguity. Verified `f4df04ab...c4a9` on `test-vectors/commitment.json` and `50` Go/Rust commitment outcomes + `4` framing counterchecks in `policy-results.json`. |
| Pre-disclosure hiding | Statement carries a fresh 256-bit `nonce` (`§4.2`); only `SHA256(sig)` leaves the machine to TSAs/calendars (`§5`, `§6.1`). Catalogue commitment uses separate private `R` (`spec/core.md`). | Pre-disclosure hiding holds against time services and observers **only if** `R` is independent of `predicate.nonce` (`CD-B2`) and producer OS CSPRNG entropy is sound (`CD-A3`). |
| Post-disclosure guessing / dictionary | Plain `subject.digest.sha256` and (once `nonce` is revealed in the statement) `possession[i].sha256` confirm candidate files (`§4.3`, `§5`). | Candidly documented: neither protects low-entropy artifacts/snippets from offline enumeration once the statement is disclosed. |
| Opening verification | `check_registration.py` (`check_link`) recomputes `catalogue_commitment` and `sha256(catalogue)` against `referenceCatalogueSha256`. | Missing `len(nonce) == 32` / `HEX64` / non-zero guard on `catalogueOpening.nonceHex` in `check_registration.py`, and missing prohibition on `catalogueOpening.nonceHex == predicate.nonce` (`CD-B2`). |
| Partial / selective disclosure | All-or-nothing catalogue opening (`spec/core.md`, `§4.4`, `§9`); multi-subject batching (`1..64` subjects under one statement, `§4.1`). | Opening reveals the entire catalogue (including all unkeyed fingerprints, `spec/catalogue-report.md` §3.7), and disclosing a multi-subject statement exposes all bundled `subject` digests (`CD-A2`). |
| Side-channel considerations | Not discussed in `spec/attestations.md`, `spec/core.md`, or `registration-record.md`. | Public commitment verification leaks nothing secret via final digest comparison (`R` and `C` are already supplied by the opener), whereas private key signing and CSPRNG nonce generation require standard constant-time/CSPRNG discipline (`CD-A5`). |

---

## 2. Findings and suggested dispositions

### Blocking

#### `CD-B1` — `sha256-salted-possession-v1` and disclosure/opening verification rules lack normative spec, schema, and promoted vector coverage
- **Severity:** `blocking`
- **Location:** [spec/attestations.md](../../spec/attestations.md), [spec/core.md](../../spec/core.md#private-catalogue-commitment), [test-vectors/commitment.json](../../test-vectors/commitment.json), [policy-results.json](../../research/experiments/signing-interop/policy-results.json), [registration-record.md](../../research/drafts/registration-record.md#43-possession-digest) (§4.3, §4.4, §9)
- **Detail:** `spec/core.md` and `schemas/evidence.schema.json` define only `sha256-salted-catalogue-v1` (`Traceweave-Catalogue-v0.1\x00`), and `spec/attestations.md` does not specify any commitment, nonce, possession, or opening-verification rules. Likewise, `test-vectors/commitment.json` holds a single `sha256-salted-catalogue-v1` vector, and `policy-results.json` (`run_policy.py`) exercises only `Traceweave-Catalogue-v0.1\x00`. `sha256-salted-possession-v1` (`Traceweave-Possession-v1\x00`) and `catalogueOpening` verification exist only in the unpromoted `registration-record.md` draft and `research/drafts/registration-fixtures/`.
- **Suggested disposition:** Promote the normative specification of `sha256-salted-possession-v1`, nonce generation/uniqueness rules, and `catalogueOpening` verification into `spec/core.md` / `spec/attestations.md` (and `schemas/`) alongside `M4.3`/`M4.5` promotion, add promoted test vectors for `sha256-salted-possession-v1` and negative opening cases to `test-vectors/`, and extend the Go/Rust commitment interop checks to `Traceweave-Possession-v1\x00` (or formally rescope `M4.6` if possession/registration remains outside M4).

#### `CD-B2` — `catalogueOpening.nonceHex` lacks 32-byte / `HEX64` / non-zero enforcement in the reference checker and is not prevented from reusing `predicate.nonce`
- **Severity:** `blocking`
- **Location:** [registration-record.md](../../research/drafts/registration-record.md#44-catalogue-commitment-optional) (§4.2, §4.4, §9), [check_registration.py](../../research/drafts/registration-fixtures/check_registration.py#L435-L436) (lines 435–436, 1288–1294)
- **Detail:**
  1. Unlike `tools/validate.py` (line 44: `if len(nonce) != 32: raise ValueError(...)`) and the Go/Rust drivers verified in `policy-results.json` (`invalid-nonce-length-{0,1,31,33,64}`), `check_registration.py`'s `catalogue_commitment(nonce, catalogue)` does not check `len(nonce) == 32`, and `check_link` calls `bytes.fromhex(opening["nonceHex"])` without validating `HEX64` or rejecting `"0" * 64`. Malformed hex triggers an unhandled `ValueError`, and an implementation omitting the 32-byte check allows bytes from an oversized `nonce` to collide across the `nonce || uint64be(len(C)) || C` boundary.
  2. Neither `registration-record.md` (§4.2, §4.4, §9) nor `check_registration.py` forbids setting the private catalogue commitment's `R` equal to the statement's `predicate.nonce`. Because `predicate.nonce` is disclosed in plaintext whenever the registration statement is shared (e.g., to verify `possession`), reusing `predicate.nonce` as `R` prematurely reveals `R` before any `catalogueOpening`, collapsing the salted catalogue commitment into an unsalted public-salt digest (`catalogue-unsalted` equivalent) and enabling offline catalogue confirmation attacks.
- **Suggested disposition:**
  1. Enforce `HEX64` (exact 32-byte lowercase hex) and reject `"0" * 64` (and `len(nonce) != 32`) on `catalogueOpening.nonceHex` in the specification and checker (returning a clean rejection code such as `catalogue-does-not-open` or `nonce-invalid`).
  2. Add an explicit normative rule in §4.4/§9 requiring `R` (`catalogueOpening.nonceHex`) to be drawn independently from `predicate.nonce` (never equal to `predicate.nonce` or any public test-vector nonce), and enforce `opening["nonceHex"] != statement["predicate"]["nonce"]` with a negative fixture.

---

### Advisory

#### `CD-A1` — Normative schema and field drift between `schemas/evidence.schema.json` / `spec/attestations.md` and `registration-record.md` §4
- **Severity:** `advisory`
- **Location:** [schemas/statement.schema.json](../../schemas/statement.schema.json), [schemas/evidence.schema.json](../../schemas/evidence.schema.json), [spec/attestations.md](../../spec/attestations.md), [registration-record.md](../../research/drafts/registration-record.md#4-the-registration-statement) (§4)
- **Detail:** `schemas/statement.schema.json` enforces `subject` `maxItems: 1` and `predicateType` `.../core.md#evidence-0.1.0-draft.1`, while `schemas/evidence.schema.json` requires `contentKind` in `["code", "text", "image", "audio", "binary", "other"]`, top-level `profile`, and required `catalogueCommitment` (no `nonce` or `possession`). By contrast, `registration-record.md` draft-5 allows `1..64` subjects, sets `contentKind` to `("text", "source-code", "image", "other")`, adds `nonce` and `possession`, and renames `catalogueCommitment` to optional `catalogue` containing `profile`. `spec/attestations.md` currently points only to `statement.schema.json`.
- **Suggested disposition:** Reconcile `schemas/` and `spec/attestations.md` (either deprecate/supersede `evidence.schema.json` `0.1.0-draft.1` or publish the `registration-draft-5` schemas alongside `M4.3`/`M4.5` promotion) and align `contentKind` values.

#### `CD-A2` — All-or-nothing disclosure and multi-subject correlation under `sha256-salted-catalogue-v1` and `1..64` subject batching
- **Severity:** `advisory`
- **Location:** [spec/core.md](../../spec/core.md#private-catalogue-commitment), [spec/catalogue-report.md](../../spec/catalogue-report.md#37-commitment-and-privacy-class), [registration-record.md](../../research/drafts/registration-record.md#41-subjects) (§4.1, §4.4, §5, §9), [check_registration.py](../../research/drafts/registration-fixtures/check_registration.py#L1285-L1295)
- **Detail:**
  1. Opening `catalogue` via `catalogueOpening` reveals the entire catalogue `C`—including every unrelated file's `sha256`, spans, and unkeyed winnowed fingerprints (`spec/catalogue-report.md` §3.7)—even when disputing a single file or region. Similarly, batching up to `64` subjects into one statement (`§4.1`, `§19.6`) reveals all bundled `subject` digests and filenames upon disclosing the statement for any single work, exposing any low-entropy bundled artifact to confirmation attacks (`§5`).
  2. In `check_registration.py` line 1293, `check_link` checks `sha(catalogue) == body["inputs"]["referenceCatalogueSha256"]` only, preventing a registrant whose registered catalogue is the `candidate` side of a comparison report from linking and opening it.
- **Suggested disposition:** Document in `§4.1` and `§5` that registrants requiring per-file selective disclosure should register one work/catalogue per statement rather than batching unrelated works (deferring per-entry Merkle commitments to a future `v2` scheme if needed), and clarify or generalize `report-link` §9 to support opening `candidateCatalogueSha256` when the linked role is `candidate`.

#### `CD-A3` — Signer binding of `possession[i]` relies on the enclosing signature; OS CSPRNG entropy is an uncheckable producer obligation
- **Severity:** `advisory`
- **Location:** [registration-record.md](../../research/drafts/registration-record.md#42-nonce) (§4.2, §4.3, §12)
- **Detail:** `possession[i]` hashes `("Traceweave-Possession-v1\x00" || nonce || L || A)` without the signer's public key, so key binding rests entirely on the DSSE signature and `§6.1` signature-target rules (already enforced). Separately, `§4.2` cross-record `nonce-reused` checks catch exact collisions across supplied records, but weak/predictable PRNG nonces cannot be detected at verification time and would silently defeat pre-disclosure hiding for low-entropy artifacts.
- **Suggested disposition:** State explicitly in `§4.3` that `possession[i]` binds to a key only through the enclosing verified DSSE signature, and specify OS CSPRNG APIs (no non-cryptographic fallback) in `§4.2`.

#### `CD-A4` — Canonicalization fragility on `C` and unstated maximum byte-length bounds in normative commitment specs
- **Severity:** `advisory`
- **Location:** [spec/core.md](../../spec/core.md#private-catalogue-commitment), [registration-record.md](../../research/drafts/registration-record.md#43-possession-digest) (§4.3–§4.4), [signing-policy-results.md](../../research/lanes/signing-policy-results.md)
- **Detail:** `policy-results.json` (`json-reserialization`, `catalogue-trailing-whitespace`) shows any re-serialization breaks `sha256-salted-catalogue-v1`, requiring verbatim retention of the committed bytes `C`. Additionally, while `run_policy.py` / `policy-results.json` enforce a `1 MiB` (`1,048,576`-byte) cap on `C` (`catalogue-resource-limit`), `spec/core.md` and `registration-record.md` specify `uint64be(L)` without stating a resource/memory cap for `C` or `A` during commitment verification.
- **Suggested disposition:** Document a bounded/streaming verification rule and explicit maximum `C`/`A` size limit in `spec/core.md` / `registration-record.md`, and note in `§14` step 4 that `C` must be retained as exact raw bytes (never re-serialized before opening).

#### `CD-A5` — Side-channel scope and `run_policy.py` vs native commitment boundary
- **Severity:** `advisory`
- **Location:** [spec/attestations.md](../../spec/attestations.md), [registration-record.md](../../research/drafts/registration-record.md#101-ed25519-verification-rule-set-a4) (§10.1), [run_policy.py](../../research/experiments/signing-interop/run_policy.py)
- **Detail:** Neither `spec/attestations.md` nor `registration-record.md` states which operations are timing-sensitive. Comparing public commitment digests during opening verification does not compare secret material (both `R` and `C` are supplied in the opening), whereas private Ed25519 signing, OS CSPRNG nonce generation, and any future hosted service checking secret credentials/openings require constant-time / side-channel-safe primitives. Note also that in `policy-results.json`, the `72` DSSE/JSON policy checks were orchestrated once in Python (`signing-policy-results.md`), whereas the `50` `sha256-salted-catalogue-v1` commitment checks were executed independently in Go and Rust.
- **Suggested disposition:** Add a short side-channel note to `spec/attestations.md` / `registration-record.md` distinguishing public commitment verification from secret-bearing signing/nonce generation (requiring constant-time Ed25519 signing), and keep independent Go/Rust commitment testing when adding `sha256-salted-possession-v1` vectors.

---

## 3. Gate `M4.6` status

- **Blocking findings:** `2` (`CD-B1`, `CD-B2`)
- **Advisory findings:** `5` (`CD-A1`–`CD-A5`)
- **Dispositions recorded:** `7 / 7` (`CD-B2` fixed pending reviewer confirmation; `CD-B1` and `CD-A1`–`CD-A5` deferred to owner-gated M4 normative promotion)
- **`M4.6` status in `ROADMAP.md`:** Remains **`open`** until `CD-B1` normative promotion is completed and the reviewer confirms `CD-B2`.

---

## 4. Dispositions

Recorded on `roadmap-v2` following the `CD-B2` fix:

| ID | Severity | Disposition | Target / Evidence |
| --- | --- | --- | --- |
| `CD-B1` | `blocking` | **Deferred to M4 normative promotion.** Promoting `sha256-salted-possession-v1`, `catalogueOpening` verification, and Go/Rust `Traceweave-Possession-v1\x00` interop vectors into `spec/` and `test-vectors/` requires the owner-gated M4 promotion alongside `M4.3`/`M4.5`. | `spec/core.md`, `spec/attestations.md`, `test-vectors/`, `research/experiments/signing-interop/` |
| `CD-B2` | `blocking` | **Fixed (awaiting reviewer confirmation).** Enforced 32-byte nonce length in `catalogue_commitment`, strict `HEX64` and non-zero validation (`nonce-invalid`), and `catalogueOpening.nonceHex != predicate.nonce` (`nonce-reused`) in `registration-record.md` (§4.4, §9) and `check_registration.py`, backed by 7 negative fixtures (`neg-opening-nonce-*`) and 3 wrong-implementation self-test cases. | `research/drafts/registration-record.md`, `research/drafts/registration-fixtures/` |
| `CD-A1` | `advisory` | **Deferred to M4 normative promotion.** Reconciling `schemas/statement.schema.json`, `schemas/evidence.schema.json`, and `spec/attestations.md` with `registration-draft-5` and `contentKind` values will happen alongside `M4.3`/`M4.5` promotion. | `schemas/`, `spec/attestations.md` |
| `CD-A2` | `advisory` | **Acknowledged / deferred to M4 normative promotion.** Per-file selective disclosure guidance (one work/catalogue per statement) and supporting `candidateCatalogueSha256` in `report-link` §9 will be addressed during normative promotion; per-entry Merkle commitments remain out of scope for `v1`. | `research/drafts/registration-record.md` (§4.1, §5, §9) |
| `CD-A3` | `advisory` | **Acknowledged / deferred to M4 normative promotion.** Explicitly stating that `possession[i]` binds to a key only through the enclosing DSSE signature (`§4.3`) and specifying OS CSPRNG APIs with no non-cryptographic fallback (`§4.2`) will be carried into the promoted normative spec. | `spec/attestations.md`, `research/drafts/registration-record.md` (§4.2, §4.3) |
| `CD-A4` | `advisory` | **Acknowledged / deferred to M4 normative promotion.** Verbatim byte retention for `C` (`§4.4`, `§14`) and explicit maximum `C`/`A` byte-length bounds (`1 MiB` as enforced in `run_policy.py`) will be codified in `spec/core.md` during normative promotion. | `spec/core.md`, `research/drafts/registration-record.md` (§4.4, §14) |
| `CD-A5` | `advisory` | **Acknowledged / deferred to M4 normative promotion.** Documenting the timing-sensitivity boundary (public commitment verification vs constant-time private signing and CSPRNG nonce generation) and maintaining independent Go/Rust commitment testing when `Traceweave-Possession-v1\x00` vectors are promoted will be completed in M4 promotion. | `spec/attestations.md`, `research/experiments/signing-interop/` |

---

## 5. Confirmation pass (`bd2f703`)

Spot-checked 2026-11-25 at local commit `bd2f703` on `roadmap-v2`:
- **Spec & checker ([registration-record.md](../../research/drafts/registration-record.md#44-catalogue-commitment-optional), [check_registration.py](../../research/drafts/registration-fixtures/check_registration.py#L1296-L1310)):** Verified `catalogue_commitment` and `possession_digest` enforce `len(nonce) == 32`, and `check_link` enforces `HEX64.fullmatch(nonce_hex)` and non-zero (`nonce-invalid`) as well as `nonce_hex != st["predicate"]["nonce"]` (`nonce-reused`).
- **Fixtures & self-tests ([build_fixtures.py](../../research/drafts/registration-fixtures/build_fixtures.py)):** Deterministic rebuild (`python3 -I research/drafts/registration-fixtures/build_fixtures.py`) leaves the working tree unchanged and produces `86` positive, `147` negative (including the `7` new `neg-opening-nonce-*` fixtures), and `44` auxiliary fixtures; `python3 -I research/drafts/registration-fixtures/check_registration.py` passes `86` positive fixtures, `147` negative fixtures, `46` wrong-implementation cases (including the `3` `CD-B2` cases), and `57/57` codes.
- **Verdict:** **`CD-B2` confirmed resolved.** `M4.6` remains **`open`** in [ROADMAP.md](../../ROADMAP.md) until `CD-B1` (and the deferred `CD-A1`–`CD-A5` items) are addressed by owner-gated M4 normative promotion.
