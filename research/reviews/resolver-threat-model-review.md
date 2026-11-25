# Independent non-author review: `resolver-threat-model.md` (`19cc1ca`)

Reviewed 2026-11-25 against commit `19cc1ca` on local branch `roadmap-v2`, evaluating [research/drafts/resolver-threat-model.md](../drafts/resolver-threat-model.md) against [ROADMAP.md](../../ROADMAP.md) (`RES.1`–`RES.3`), [spec/core.md](../../spec/core.md), [spec/extraction.md](../../spec/extraction.md), [spec/catalogue-report.md](../../spec/catalogue-report.md), [registration-record.md](../drafts/registration-record.md), [trust-policy.md](../drafts/trust-policy.md), [c2pa-mapping.md](../drafts/c2pa-mapping.md), [image-mark-finding-aid.md](../drafts/image-mark-finding-aid.md), and [initial-draft-review.md](../../docs/reviews/initial-draft-review.md). I wrote none of the reviewed document.

**Verdict: `revise before closing RES.1 / freezing RES.2`.**

The draft establishes a strong foundation: it covers all five required `RES.1` threat classes, enforces strict **T0/T1/T2** separation (keeping public registration and remote resolvers strictly optional), avoids premature security or *k*-anonymity promises, aligns accurately with wire/crypto primitives (`tw1-` 130-bit truncation, unkeyed `sha256-first8-u64be`, `sha256-salted-catalogue-v1`, E1 two-pass key events, and strict Ed25519/JSON bounds), and defines 10 judgment-free `RES.2` metrics. However, adversarial inspection surfaced **3 blocking findings** (`B1`–`B3`) and **5 advisory items** (`A1`–`A5`) that must be dispositioned before `RES.1` is marked met or `RES.2` synthetic measurements are frozen and executed. Per instructions, neither `resolver-threat-model.md` nor `ROADMAP.md` was modified, and `RES.1` / `RES.3` remain open.

---

## 1. Summary of Findings

### Blocking

1. **B1 (`M-AB-1` contradicts `traceweave-seed-merge-draft-2` pairwise `seedCount` / `maxRegionsPerMode` scope).**
   - *Where:* [§3.5 `M-AB-1`](../drafts/resolver-threat-model.md#L190) and [§4 metric table](../drafts/resolver-threat-model.md#L221).
   - *Issue:* `M-AB-1` proposes injecting $p \in \{1\%, 5\%, 10\%\}$ adversarial high-frequency / boilerplate-flooding entries into a synthetic candidate catalogue / index and measuring the fraction of legitimate positive comparisons degraded to `seed-limit-exceeded` or losing their true-match region past `maxRegionsPerMode`. Under [spec/catalogue-report.md §5.3–§5.7](../../spec/catalogue-report.md#54-seeds-and-the-seed-limit), `seedCount`, `seed-limit-exceeded`, and `maxRegionsPerMode` operate **strictly per `(reference artifact, candidate artifact, mode)` pair** ("The bounds limit one mode of one pair, not a whole report", §5.7). Adding $p\%$ separate adversarial entries to a `traceweave-catalogue-draft-2` candidate catalogue leaves every legitimate `(ref, legit_cand)` pair untouched (`0 / total positive comparisons` by construction).
   - *Required fix:* Specify the exact poisoning mechanism in both §3.5 and §4 before freezing `RES.2` — e.g.: (i) **within-artifact padding** (injecting adversarial high-frequency tokens into candidate artifacts themselves to force per-pair `seed-limit-exceeded` or early-position truncation past `maxRegionsPerMode`), (ii) a **T2 index query surface** with an explicit global per-query seed/region cap across returned hits, and/or (iii) **top-$K$ candidate-selection crowding** (measuring dropped legitimate candidates before comparison rather than `seed-limit-exceeded`).

2. **B2 (§3.4 membership-disclosure mitigation leaves `below-minimum-evidence` and `containment`/`similarity` single-hash side channels open).**
   - *Where:* [§3.4 Architectural mitigations](../drafts/resolver-threat-model.md#L150-L155).
   - *Issue:* §3.4 proposes mitigating minimal-window ($k + w - 1 = 8$ token) oracle probes by enforcing `minQueryTokens >> k + w - 1`, requiring `minRegionDistinctHashes >= 2` "before returning a hit", and suppressing `span`, `position`, and exact `seedCount` from remote responses. However, in [spec/catalogue-report.md §5.8, §5.9, and §6.3](../../spec/catalogue-report.md#58-mode-outcome), a single shared hash (`distinctHashes = 1 < 2`) still distinguishes `no-match` / `below-minimum-evidence` from `no-shared-fingerprints`, populates `regionCounts.belowMinimumEvidence = 1`, and yields non-zero `containment` (`1/|H_C|`) and `similarity.jaccard` numerators. Unless a T2 oracle explicitly collapses `below-minimum-evidence` and `common-only` into a uniform `no-match` and withholds `regionCounts` and `containment`/`similarity` numerators, `minRegionDistinctHashes >= 2` does not prevent single-hash 8-token membership probing. In addition, an attacker who knows one unsuppressed public/corpus 8-token snippet can pair it with a guessed 8-token secret within `mergeGap` (or anywhere in the probe for global distinct-hash floors) to clear both `minQueryTokens` and `minRegionDistinctHashes >= 2`.
   - *Required fix:* Extend §3.4's T2 response-surface mitigation to require collapsing `below-minimum-evidence` / `common-only` into an indistinguishable `no-match` and suppressing `regionCounts`, `containment`, and `similarity` fractions on untrusted T2 queries, and document the known-prefix padding residual risk against `minQueryTokens` + `minRegionDistinctHashes`.

3. **B3 (`M-EN-1` definition discrepancy between §3.2 "false-discovery rate" and §4 "false confirmations / $M$ distractors").**
   - *Where:* [§3.2 `M-EN-1`](../drafts/resolver-threat-model.md#L103) vs [§4 metric table](../drafts/resolver-threat-model.md#L215).
   - *Issue:* §3.2 defines `M-EN-1`'s error metric as `false-discovery rate` ($\text{FP} / (\text{TP} + \text{FP})$, which is $0/0$ undefined when $\text{TP} = \text{FP} = 0$, as expected on full `tw1-`), whereas §4 defines it as `false confirmations / M distractors` ($\text{FP} / M$, i.e., false-positive rate). Because `RES.2` requires freezing the metric and denominators prior to measurement, both sections must use the exact same definition.
   - *Required fix:* Align §3.2 with §4 on false-positive rate ($\text{FP} / M$ distractors), optionally noting FDR alongside only when $\text{TP} + \text{FP} > 0$.

---

### Advisory

- **A1 (`T1` release catalogue disclosure in §1.2):** Line 25 includes `"or publishes a release catalogue artifact"` under `T1`, while stating `"bundle disclosure follows §5"`. Registration bundle disclosure ([registration-record.md §5](../drafts/registration-record.md#5-what-publishing-each-value-reveals)) applies to statements/nonces/keys, whereas publishing a `traceweave-catalogue-draft-2` artifact exposes unkeyed `sha256-first8-u64be` hashes, `byteLength`, `tokenCount`, `position`, and `span` per [spec/catalogue-report.md §3.7](../../spec/catalogue-report.md#37-commitment-and-privacy-class) (analyzed in §3.3). Cross-reference `spec/catalogue-report.md §3.7` in the T1 row.
- **A2 (Incomplete pre-registration parameters for `M-QL-1` and `M-CI-2` in §4):**
  - `M-QL-1` in §3.1 specifies `"as a function of fingerprints queried per file"`, but §4 ([line 207](../drafts/resolver-threat-model.md#L207), [line 213](../drafts/resolver-threat-model.md#L213)) does not parameterize the per-file fingerprint query count $q$ in $\mathcal{Q}$.
  - `M-CI-2` ([line 131](../drafts/resolver-threat-model.md#L131), [line 218](../drafts/resolver-threat-model.md#L218)) specifies recall's denominator (`identified vendor modules / total synthetic modules`) but omits precision's denominator (`total predicted vendor modules`) and MAE's unit/denominator (`per file` in bytes / tokens).
- **A3 (`M-AB-2` conflates `8 MiB` input cap with catalogue byte size):** Line 191 writes `max-bound catalogues (k=16, w=128, 8 MiB)`. In [spec/extraction.md §10a](../../spec/extraction.md#10a-resource-bounds-and-complexity), `8 MiB` (`maxInputBytes`) bounds the source input, whereas the resulting `traceweave-catalogue-draft-2` JSON can be substantially larger (up to ~8.4M fingerprints per channel in [spec/catalogue-report.md §5.7](../../spec/catalogue-report.md#57-ambiguity-and-the-output-cap)). Reword to `max-bound inputs (k=16, w=128, maxInputBytes=8 MiB)`.
- **A4 (Explicit `RES.2` scope note for `text-plain` and PDQ/ISCC):** §1.3 lists 256-bit PDQ and 64-bit ISCC Image-Code values and §3.3 notes `text-plain` (`["exact","folded","skeleton"]`), while §4 scopes `M-CI-1` and `M-MD-1` to `(k=5, w=4)` and `exact`/`normalized` channels. State explicitly in §4 whether `RES.2` excludes PDQ/ISCC Hamming-radius resolver queries (e.g., C2PA `/matches/byBinding` in [c2pa-mapping.md §2.4](../drafts/c2pa-mapping.md#24-what-the-resolution-api-expects-c2)) and whether `text-plain` (`folded`/`skeleton`) is included alongside code profiles.
- **A5 (Minor phrasing on `tw1-` in §1.3 item 3):** Line 34 writes `"DSSE-wrapped in-toto Statement v1 carrying ..., and tw1-"`. Clarify that `tw1-` is computed externally from `statementSha256` ([registration-record.md §9.1](../drafts/registration-record.md#91-text-reference-normative-frozen-2026-11-24)), not carried as a field inside the statement.

---

## 2. Detailed Checklist Verification

### 2.1 Five Threat Classes (§3.1–§3.5)

| Threat class | Adversary model & attack vectors vs specs | Residual risk honesty | Mitigation soundness |
| --- | --- | --- | --- |
| **1. Query leakage (§3.1)** | Accurate ($\mathcal{A}_{\text{op}}$, $\mathcal{A}_{\text{net}}$, unkeyed `sha256-first8-u64be` dictionary testing, 16–24-bit prefix-bucket intersection across `exact`/`normalized`, cross-query/CRL/OCSP/bundle timing correlation, T1 static-shelf IP/timestamp exposure). | Honest: notes network queries inherently reveal participation, timing, network identity, and multiplicity; PIR/ORAM do not hide occurrence/count without padded batches/dummy traffic. | Sound: T0 offline default (`WEB.2`, `M2.8`), static snapshot distribution (`T1`), `content-on-wire` / `forbidden-field` hygiene, explicit ban on claiming *k*-anonymity. |
| **2. Enumeration (§3.2)** | Accurate (`tw1-` 26 Crockford base32 chars = 130 bits + 1 Luhn mod 32 check char = 27 chars; 4+4 display prefix at $2^{40}$ work; `subject.sha256` dictionary probing; 16-hex `keyid` hint vs 32-byte `keySha256` cross-work linking under `I0`; monotonic `logIndex` / sequential IDs). | Honest: confirms any digest oracle answers membership for low-entropy guesses; `I0` continuity vs `I0′` unlinkability tension stated clearly. | Sound: forbids public lookup by `subject.sha256`, `possession[].sha256`, `keyid`, or `keySha256`; mandates exact full 27-char `tw1-` or 256-bit `statementSha256`, uniform `not-found`, and `I0′` recommendation. |
| **3. Catalogue inference (§3.3)** | Accurate (`traceweave-catalogue-draft-2` exposes `byteLength`, `tokenCount`, per-channel `kgramCount`, `partialWindow`, `{hash, position, span}`; unkeyed `sha256-first8-u64be` domain-separated by `(profile, profileVersion, channel, k)`; profile/channel/dependency fingerprinting; consortium-wide HMAC inversion). | Honest: states deterministic unkeyed hashes of low-entropy syntax are always dictionary-testable; structural metadata leaks size/density even when hashes are keyed. | Sound: private-by-default storage (`M2.8`), `sha256-salted-catalogue-v1` with 32-byte OS-random `R` independent of `predicate.nonce`, index projection stripping spans/lengths/paths, bilateral `KEYED.1`. |
| **4. Membership disclosure (§3.4)** | Accurate (winnowing $k+w-1 = 8$ token locality under shipped `k=5, w=4`; adaptive sliding-window / $k$-th-token expansion; `suppressionCatalogueSha256` and `exact` vs `normalized` differential probing; `subject.sha256` confirmation). | Honest: explicitly states the fundamental oracle limit and preserves [spec/core.md#interpretation](../../spec/core.md#interpretation) non-authorship / non-infringement boundary. | **Gap (B2):** relies on `minRegionDistinctHashes >= 2` and hiding `span`/`position`/`seedCount` without collapsing `below-minimum-evidence` / `regionCounts` / `containment` fractions or addressing known-prefix padding. |
| **5. Abuse (§3.5)** | Accurate (`maxSeedsPerMode` 100k shipped / 10M ceiling, `maxRegionsPerMode` 1k shipped, $\sum \text{occ}_{\text{ref}} \times \text{occ}_{\text{cand}}$ seed explosion; `maxInputBytes` 8 MiB, `k <= 16`, `window <= 128`, depth 64, duplicate JSON keys, `[8]A == identity`, `S >= L`; `key-event-signatures` wrapper mask, `ignored-unauthorized`, `ignored-no-proved-time`, E1 oscillation, `compromiseLookbackSeconds` / RD18 / `I6` permanent dispute; $2^{65}$ `tw1-` equivocation & $2^{40}$ 4+4 look-alike phishing). | Honest: "first to register is not first to create"; look-back window trade-off (RD15); Sybil quota bypass on open-access endpoints. | Sound: local policy ownership, pre-crypto strict bounds, two-pass non-oscillating E1, full 256-bit `statementSha256` binding in machine records (`report-link`, `org.traceweave.registration-link`, `registrationLink`), `SK.5` + `(caller, messageId)` quotas. |

### 2.2 Optionality & No Premature Privacy/Security Promises (§1, §4)

- **T0 / T1 / T2 separation:** Verified across [§1.1–§1.2](../drafts/resolver-threat-model.md#L11-L29) and [§4.3](../drafts/resolver-threat-model.md#L224-L226). `T0` (local offline) and `T1` (registrant-chosen static HTTPS shelf) require no resolver; `T2` is explicitly out of core scope, opt-in only, and gated on `RES.1`–`RES.3`, `SK.5`, and `RD3`. Existing hosted time services (RFC 3161, OpenTimestamps) and hypothetical A2A witness routes receive only `SHA-256(raw DSSE signature)` over a 256-bit-nonced statement and offer no public digest lookup.
- **No premature promises:** Confirmed. No *k*-anonymity, zero-knowledge, unbreakable privacy, or detection-rate guarantees are claimed; residual cryptographic and metadata limits are stated explicitly for all five classes.

### 2.3 Pre-registered `RES.2` Metrics (`M-QL-1..2`, `M-EN-1..2`, `M-CI-1..2`, `M-MD-1..2`, `M-AB-1..2`)

All 10 metrics are free of judgment words and designed for synthetic corpus experiments, with the specific specification defects noted in **B1** (`M-AB-1` poisoning unit vs per-pair caps), **B3** (`M-EN-1` FDR vs FPR mismatch), and **A2** (`M-QL-1` per-file query slice parameter $q$; `M-CI-2` precision and MAE denominators).

---

## 3. Verification Commands Run

Executed on commit `19cc1ca` (and re-run after writing this review file):

| Command | Outcome | Observed output |
| --- | --- | --- |
| `.venv/bin/python tools/validate.py` | **PASS** (exit 0) | Draft schemas, synthetic examples, fixture digests, commitment/DSSE vectors, local links, promoted schemas, and vector checkers pass |
| `.venv/bin/python tools/validate.py --links-all` | **PASS** (exit 0) | Local Markdown links valid in every Markdown file |
| `.venv/bin/python -m unittest discover -s tests` | **PASS** (exit 0) | `Ran 11 tests in 13.449s` (`OK`) |
| `.venv/bin/python tools/check_hygiene.py` | **PASS** (exit 0) | No home-directory paths, thread identifiers, or AI-attribution trailers |

---

## 4. Confirmation pass (`9f50798`)

Re-checked 2026-11-25 against commit `9f50798` on local `roadmap-v2`.

**Verdict: `ready`** for **RES.1** (`RES.2` synthetic measurement and `RES.3` post-measurement review remain open).

- **B1 resolved ([§2](../drafts/resolver-threat-model.md#L47), [§3.5](../drafts/resolver-threat-model.md#L173-L197), [§4](../drafts/resolver-threat-model.md#L230)):** `traceweave-seed-merge-draft-2` pairwise `seedCount` / `maxRegionsPerMode` scope is explicitly distinguished from pre-comparison top-$K$ crowding and T2 global caps; `M-AB-1` splits cleanly into `M-AB-1a` (within-artifact padding) and `M-AB-1b` (top-$K$ candidate crowding & T2 global query cap), each with explicit numerators and denominators.
- **B2 resolved ([§2](../drafts/resolver-threat-model.md#L46), [§3.4](../drafts/resolver-threat-model.md#L142-L159), [§4](../drafts/resolver-threat-model.md#L213-L228)):** T2 oracle mitigations mandate collapsing `below-minimum-evidence`, `common-only`, and `no-shared-fingerprints` into an indistinguishable `no-match` and withholding `regionCounts`, `containment`, `similarity.jaccard`, `span`, `position`, and `seedCount`; known-prefix padding within `mergeGap` (or under global distinct-hash floors) is documented in attack vectors, residual risk, and `M-MD-1`.
- **B3 resolved ([§3.2](../drafts/resolver-threat-model.md#L103), [§4](../drafts/resolver-threat-model.md#L224)):** Standardized both sections on $\text{TPR} = \text{TP} / N$ and $\text{FPR} = \text{FP} / M$ distractors, restricting supplemental FDR to $\text{TP} + \text{FP} > 0$.
- **A1–A5 resolved:** `T1` cross-references [catalogue contract §3.7](../../spec/catalogue-report.md#37-commitment-and-privacy-class) (`§1.2`); `M-QL-1` freezes $q \in \{1, 2, 4, 8, \text{all}\}$ and `M-CI-2` defines precision, recall, and per-file MAE denominators (`§3.1`, `§3.3`, `§4`); `M-AB-2` clarifies `max-bound inputs (k=16, w=128, maxInputBytes=8 MiB)` (`§3.5`, `§4`); `§4` scopes `RES.2` to `go-tokens`, `rust2024-tokens`, `ts-tokens`, and `text-plain` (`folded`/`skeleton`) while excluding PDQ/ISCC Hamming-ball resolver queries pending a separate addendum; and `§1.3` clarifies `tw1-` is computed externally from `statementSha256`.
- **Re-run checks on `9f50798` + `ROADMAP.md` (`RES.1` met):** `tools/validate.py`, `tools/validate.py --links-all`, `unittest discover -s tests`, and `tools/check_hygiene.py` all passed (exit 0).
