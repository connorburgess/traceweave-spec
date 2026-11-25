# Independent non-author promotion review: M4 registration, in-toto adapter, and `py-tokens` (`5facdd4`)

Reviewed 2026-11-25 on local `roadmap-v2` at commit `5facdd4` (preceded by `81a47e1`). I wrote none of the promoted specifications, profiles, schemas, vectors, or scripts in `5facdd4`.

**Verdict: `accept` (0 blocking defects).**
Core gates **M4.3** and **M4.6**, and later-profile gates **PY.1** and **PY.2**, all meet their `ROADMAP.md` criteria and may be marked **met**.

---

## 1. Promotion integrity (`research/promotion-map.md` & `schemas/record.schema.json`)

### 1.1 File moves, SHA-256 verification, and JSON diff audit

- **Move accounting:** `git diff-tree --no-commit-id --name-status -r 5facdd4` records **352** added (`A`), **352** deleted (`D`), and **29** modified (`M`) paths. The 352 `D`→`A` pairs match the 352 rows of `Promotion 2 — 2026-11-25` in [research/promotion-map.md](../promotion-map.md) 1-to-1 (`set()` symmetric difference on both old and new paths).
- **Digest verification:** Recomputing SHA-256 for every row against `81a47e1:<old>` and `5facdd4:<new>` yields **0 mismatches** (`63` byte-identical, `289` changed).
- **Registration fixture JSON audit (276 files):** Deep structural comparison of all 276 changed JSON files under `test-vectors/registration/` against their `81a47e1` drafts confirms **0 unexpected JSON diffs**. Every change falls exclusively into one of:
  1. `fixture.notice` updated from `research/drafts/registration-record.md` to `spec/registration-record.md`; or
  2. SHA-256 digests (`bundleSha256`, `object.inputs.keyEvents[]` digests and their lexicographic sort order across 15 verification-result files, etc.) deterministically recomputed from the notice-updated referenced JSON files.
- **in-toto adapter & Python vector JSONs:** All 4 `accept/` and 26 `reject/` JSON fixtures in `test-vectors/intoto-adapter/`, and `py.json`, `limits-py.json`, `config-py.json`, `config-py-limit16.json`, and `config-negative-python.json` in `test-vectors/extraction-python/`, are **byte-identical** to `81a47e1`.
- **Promoted Markdown & Python script audit (13 changed non-JSON files):** Word/line diffs of `spec/registration-record.md`, `spec/trust-policy.md`, `docs/decisions/timestamp-adapter-decision.md`, `profiles/python.md`, and the promoted READMEs/checkers/builders confirm only documented status-line updates, relative path updates, usage comments, `ROOT = HERE.parents[1]` / `parents[2]` depth adjustments, and the intentional `CD-A2`–`CD-A5` normative notes (`spec/registration-record.md` and `check_registration.py` `check_link` `candidateCatalogueSha256` support). No unintended normative drift was found.

### 1.2 `schemas/record.schema.json` audit

- Diff in `5facdd4`:
  1. Updated `description` from `"union of both profiles"` to `"union across registered token profiles"`.
  2. Updated `$defs.token.properties.class.pattern` from `"^[a-z]+$"` to `"^[a-z]+(?:-[a-z]+)*$"`.
  3. Added `"inconsistent-indentation"` and `"unmatched-dedent"` to `$defs.lexicalErrorResult.properties.error.properties.code.enum`.
- **No weakening of existing checks:** `^[a-z]+(?:-[a-z]+)*$` accepts all existing single-word lowercase classes (`^[a-z]+$`) and hyphenated Python classes (`fstring-start`, `fstring-middle`, `fstring-end`, `tstring-start`, `tstring-middle`, `tstring-end`), while continuing to reject empty strings, leading/trailing hyphens (`-start`, `start-`), consecutive hyphens (`fstring--start`), uppercase, digits, and underscores. Per-profile closed token-class and error-code lists remain enforced by `test-vectors/matching/check_matching.py`.
- **Validation:** Validating all **107** vectors in `test-vectors/extraction-python/py.json` and all **3** vectors in `limits-py.json` (wrapped as `traceweave-extraction-record-draft-1` records) against `schemas/record.schema.json` passes **110/110**, and `ContractTests.test_record_schema_accepts_python_token_classes_and_error_codes` passes in `unittest`.

---

## 2. Gate verdicts

### 2.1 `M4.3` — **met**

> **Criterion ([ROADMAP.md](../../ROADMAP.md)):** "Negative cryptographic vectors (tampered payload, type or signature; untrusted key; malformed or duplicate-key payload; subject mismatch), each with a distinct reason code. `validate` checks them"

All required categories are present with distinct reason codes and verified by `tools/validate.py`:

| Required category | Promoted fixtures (`test-vectors/registration/` & `test-vectors/intoto-adapter/`) | Distinct reason code(s) |
| --- | --- | --- |
| Tampered payload | `registration/negative/neg-signature-invalid.json` (claimed time edited after signing); `registration/negative/neg-tsa-signature-invalid.json` (`genTime` edited after signing); `intoto-adapter/reject/reject-tampered-payload.json` | `signature-invalid`, `tsa-signature-invalid` |
| Tampered / wrong type | `registration/negative/neg-envelope-shape.json` (wrong DSSE `payloadType`), `neg-predicate-type.json`; `intoto-adapter/reject/reject-wrong-type.json`, `reject-wrong-dsse-payload-type.json`, `reject-wrong-predicate-type.json` | `envelope-shape`, `predicate-type`, `statement-type`, `dsse-payload-type` |
| Tampered / invalid signature | `registration/negative/neg-signature-invalid.json`, `neg-evidence-target-base64.json`, `neg-evidence-wrong-target.json` + Ed25519 `S >= L` / small-order / non-canonical self-tests in `check_registration.py`; `intoto-adapter/reject/reject-signature-over-base64.json` | `signature-invalid`, `evidence-wrong-target` |
| Untrusted key | `registration/negative/neg-trust-by-hint.json`, `neg-root-not-anchored.json`, `neg-key-event-two-signatures.json`; `intoto-adapter/reject/reject-untrusted-key.json` | `key-identity-by-hint`, `root-not-anchored`, `key-event-signatures`, `untrusted-signer` |
| Malformed / duplicate-key payload | `registration/negative/neg-duplicate-key.json`, `neg-statement-shape.json`, `neg-nonce-invalid.json`, `neg-opening-nonce-*` (6 malformed/zero cases); `intoto-adapter/reject/reject-duplicate-json-key.json`, `reject-invalid-base64.json`, `reject-missing-statement-field.json`, `reject-missing-predicate-field.json` | `duplicate-key`, `statement-shape`, `nonce-invalid`, `invalid-base64`, `missing-required-field` |
| Subject mismatch | `registration/negative/neg-subject-mismatch.json`, `neg-possession-mismatch.json`; `intoto-adapter/reject/reject-subject-digest-mismatch.json` | `subject-mismatch`, `possession-mismatch`, `subject-digest-mismatch` |

`check_registration.py` verifies **86** positive fixtures, **147** negative fixtures covering **57/57** codes, and **46** wrong-implementation self-tests; `check_intoto_adapter.py` verifies **4** accept fixtures, **26** reject fixtures covering **17/17** required reject codes, and self-tests. Both run inside `tools/validate.py` and exit `0`.

*(Non-blocking observation: `test-vectors/registration/README.md` line 150 correctly states `147` broken fixtures in `negative/`, while its Markdown table lists `146` rows—`neg-reference-jump-transposed` is present on disk and checked by `check_registration.py`, carried over from the pre-promotion draft.)*

---

### 2.2 `M4.6` — **met**

> **Criterion ([ROADMAP.md](../../ROADMAP.md)):** "Commitment/disclosure design reviewed by a named non-author. Report in `docs/reviews/`; every finding has a disposition"

Review report is committed at [docs/reviews/commitment-disclosure-review.md](../../docs/reviews/commitment-disclosure-review.md). All **2** blocking findings and **5** advisory findings have clean dispositions implemented in `5facdd4`:

| ID | Disposition & verified implementation in `5facdd4` |
| --- | --- |
| `CD-B1` | **Implemented.** `spec/core.md` (`#salted-possession-digest`, `#catalogue-opening-verification`) and `spec/attestations.md` normatively specify `sha256-salted-possession-v1` (`Traceweave-Possession-v1\x00`), independent OS CSPRNG nonce generation, and 4-step `catalogueOpening` verification, backed by promoted vectors in `test-vectors/registration/` and `test-vectors/intoto-adapter/` wired into `tools/validate.py`. |
| `CD-B2` | **Confirmed (`1b51807`) & promoted.** 32-byte `len(nonce) == 32` check in `catalogue_commitment` / `possession_digest`, strict `HEX64` + non-zero validation (`nonce-invalid`), and prohibition of `catalogueOpening.nonceHex == predicate.nonce` (`nonce-reused`) are codified in `spec/core.md` and `spec/registration-record.md` (§4.4, §9) and enforced by `test-vectors/registration/check_registration.py` with 7 `neg-opening-nonce-*` fixtures and 3 wrong-implementation self-test cases. |
| `CD-A1` | **Implemented.** `spec/attestations.md` reconciles both restricted in-toto Statement v1 / DSSE adapter forms side-by-side (`0.1.0-draft.1` minimal commitment via `schemas/statement.schema.json` + `schemas/evidence.schema.json` vs `traceweave-registration-draft-5` via `spec/registration-record.md` §4), both verified by `test-vectors/intoto-adapter/check_intoto_adapter.py`. |
| `CD-A2` | **Implemented.** `spec/core.md` and `spec/registration-record.md` (§4.1) document all-or-nothing disclosure and advise one work/catalogue per statement for per-work selective disclosure; `spec/core.md`, `spec/registration-record.md` (§9), and `test-vectors/registration/check_registration.py` (`check_link`) support opening `candidateCatalogueSha256` when all linked entries have `role: "candidate"`. |
| `CD-A3` | **Implemented.** `spec/core.md`, `spec/attestations.md`, and `spec/registration-record.md` (§4.2–§4.3) specify OS CSPRNG APIs with no non-cryptographic fallback and state that `possession[i]` binds to a key only through the enclosing verified DSSE signature. |
| `CD-A4` | **Implemented.** `spec/core.md` and `spec/registration-record.md` (§4.4, §14 step 4) require verbatim raw-byte retention of `C` without re-serialization and specify a bounded verification cap (`1 MiB` / `1,048,576` bytes for `C` in the M4 policy/harness, streaming/bounded hashing for `A`). |
| `CD-A5` | **Implemented.** `spec/attestations.md` and `spec/registration-record.md` (§10.1) document the side-channel boundary distinguishing public `catalogueOpening` digest comparisons from constant-time Ed25519 signing and OS CSPRNG nonce generation. |

---

### 2.3 `PY.1` — **met**

> **Criterion ([ROADMAP.md](../../ROADMAP.md)):** "The profile covers the M1.1 list plus Python layout: NEWLINE, INDENT and DEDENT as zero-width tokens; line continuation; string and f-string literals; encoding declarations. Generated and vendored exclusions are stated."

Verified in [profiles/python.md](../../profiles/python.md):
- **M1.1 checklist (§15):** Maps all items from [profiles/code.md](../../profiles/code.md) "Before registering a profile" with 0 TBDs (grouping hash parameters, window sizes, and tie-breaking into one row).
- **Python layout (§4.4–§4.5):** `newline`, `indent`, and `dedent` defined as zero-width `[p, p)` tokens with empty text `""`, two-width (`col`, `alt`) indentation stack, form-feed reset, and end-of-input dedents.
- **Line continuation (§4.2):** Explicit `\` continuations and implicit bracket / replacement-field joining specified.
- **String and f-string literals (§5.3, §6):** Prefix rules, raw/triple strings, and full f-string / t-string mode machine specified.
- **Encoding declarations (§3.1):** PEP 263 comments treated as comments (no non-UTF-8 repair), UTF-8 alias selection rule (`PYOD-2`), and BOM/NUL rejection specified.
- **Generated and vendored exclusions (§2, §12, §15):** `.pyi` stubs, `.ipynb` notebooks, `.pyx`/`.pxd`/`.pxi` Cython, extensionless scripts, Python 2 metadata guidance, non-UTF-8/BOM selection exclusions, and `@generated` / `DO NOT EDIT` within the first 2,048 bytes are stated.

---

### 2.4 `PY.2` — **met**

> **Criterion ([ROADMAP.md](../../ROADMAP.md)):** "Hand-derived (definition) vectors cover the M1.2 classes plus the PY.1 classes, including a layout-only k-gram with an empty span (`py-empty-span-fingerprint`)."

Verified in [test-vectors/extraction-python/](../../test-vectors/extraction-python/README.md):
- **Counts & derivation:** `py.json` holds **107** vectors (`68` accepted, `39` errors), **107/107** labelled `derivation: "hand"` (streams hand-written in `harness/vector_sources.py`; arithmetic computed by `harness/build_vectors.py`; independently re-lexed by `pylex.py` and sort-based winnowing in `check_vectors.py`, plus byte-for-byte reproduction by independent Rust and Go implementations under `PY.3`). Every accepted vector has a valid `pairedRejection` error vector. `limits-py.json` adds **3** size-limit vectors, and `config-negative-python.json` holds **20** rejected configs.
- **Coverage:** All 7 M1.2 classes (empty, below `k+w-1`, Unicode, malformed, repeated, equal-minimum ties, CRLF/BOM) and all PY.1 classes (layout `newline`/`indent`/`dedent`, line continuations, strings/f-strings/t-strings, encoding declarations) are covered across all 17 token classes and 9 lexical error codes.
- **Empty-span fingerprint:** `py-empty-span-fingerprint` (`"if a:\n if b:\n  if c:\n   if d:\n    x"`) produces exact-channel fingerprint `{"position": 21, "hash": "14443fa60c4a7419", "span": [35, 35]}`, explicitly asserted by `check_vectors.py`.
- **`validate` integration:** `test-vectors/extraction-python/check_vectors.py` is wired into `tools/validate.py` (`32/32` mutation self-tests, `29/29` wrong-lexer self-tests) and exits `0`.

*(Non-blocking observation: `py.json` vectors carry `derivation: "hand"` per vector, while the derivation rule is stated in `README.md` / `harness/` rather than a top-level `derivationRule` JSON field; `py.json` bytes are intentionally kept frozen at `58c25a9` as pinned by `PY.3`.)*

---

## 3. Verification commands run

All checks executed cleanly on `5facdd4`:

- `.venv/bin/python tools/validate.py` → exit `0` (`PASS: draft schemas, synthetic examples, fixture digests, commitment and DSSE framing vectors, local links, promoted schemas and vector checkers`).
- `.venv/bin/python tools/validate.py --links-all` → exit `0` (`PASS: local Markdown links in every Markdown file`).
- `.venv/bin/python -m unittest discover -s tests -v` → exit `0` (`Ran 12 tests in 24.590s`, `OK`).
- `.venv/bin/python tools/check_hygiene.py` → exit `0` (`PASS: no home-directory paths, thread identifiers or AI-attribution trailers (tree)`).
- `.venv/bin/python test-vectors/registration/check_registration.py --verbose` → exit `0` (`86 positive fixtures, 147 negative fixtures, 46 wrong-implementation cases, 57 codes (57 exercised by a negative); all as expected`).
- `.venv/bin/python test-vectors/intoto-adapter/check_intoto_adapter.py --verbose` → exit `0` (`PASS in-toto adapter (M4.5): 4 accept, 26 reject, 17/17 reject codes covered, self-tests passed`).
- `.venv/bin/python test-vectors/extraction-python/check_vectors.py` → exit `0` (`107` `py.json`, `3` `limits-py.json`, `20/20` negative configs, `32/32` mutations, `29/29` wrong lexers).
