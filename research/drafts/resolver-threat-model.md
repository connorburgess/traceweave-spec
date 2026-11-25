# Resolver Threat Model (Draft)

Status: **research draft in progress, 2026-11-25.** Drafted for roadmap gate **RES.1** ([roadmap](../../ROADMAP.md#later-profiles-and-sequence)). **Not normative and not yet reviewed** (gate **RES.3** requires an independent review with every finding dispositioned; **RES.1** remains open until then). **No public resolver, lookup registry, or hosted signing service exists or is operated by the project.**

Inputs: [core](../../spec/core.md), [extraction contract](../../spec/extraction.md), [catalogue and report contract](../../spec/catalogue-report.md), [attestations](../../spec/attestations.md), [initial draft review](../../docs/reviews/initial-draft-review.md), [registration record draft-5](registration-record.md), [trust policy draft](trust-policy.md), [C2PA mapping draft](c2pa-mapping.md), and [image-mark finding aid draft](image-mark-finding-aid.md).

---

## 1. Standing Principle and System Boundary

### 1.1 Standing Principle: Public Registration and Remote Resolvers Stay Strictly Optional

> **Standing principle:** Public registration and remote resolvers stay **strictly optional**. Local offline verification and self-hosted static shelves **never** require a resolver.

Per [core](../../spec/core.md#privacy-defaults):
- Local extraction, catalogue construction, comparison (`extract -> catalogue -> compare -> report`), and registration verification MUST work with zero network access (`scripts/offline`, [trust policy §7](trust-policy.md#7-revocation-freshness-and-offline-first-evaluation)).
- No core profile or verification flow depends on a central lookup index, transparency log, or soft-binding resolver.
- Any future remote resolver, public directory, or hosted witness is an **opt-in extension** gated on this threat model (**RES.1**), pre-committed synthetic leakage measurements (**RES.2**), independent review (**RES.3**), and explicit owner authorization (**SK.5** / **RD3**).

### 1.2 Deployment Tiers and Trust Boundaries

| Tier | Mechanism | Network interaction | Resolver required? | Primary disclosure surface |
| --- | --- | --- | --- | --- |
| **T0 — Local offline (default)** | Local CLI / library / WASM (`WEB.2`); local catalogues stored outside checkouts (`M2.8`); locally retained DSSE bundles, TSA certificate chains, CRL/OCSP snapshots, and pinned Bitcoin header checkpoints | None (network-denied) | **No** | Local filesystem / operator host only |
| **T1 — Self-hosted static shelf** | Registrant prints a `tw1-` reference ([§9.1](registration-record.md#91-text-reference-normative-frozen-2026-11-24)) beside a static HTTPS URL they control, or publishes a release catalogue artifact | Explicit `GET <url>` of a static object | **No** | Host sees verifier IP, timestamp, `User-Agent`, and requested URL; bundle disclosure follows [§5](registration-record.md#5-what-publishing-each-value-reveals) |
| **T2 — Optional remote resolver (out of core scope)** | Interactive lookup service answering queries over `tw1-` / `statementSha256`, `subject.sha256`, `keySha256` / `keyid`, key-event streams, or fingerprint / prefix-bucket indices | Interactive query/response | **Yes (opt-in only)** | All 5 RES.1 threat classes below |

Note on existing hosted time services: obtaining RFC 3161 tokens or OpenTimestamps proofs ([registration design §17](registration-record.md#17-needs-the-owner)) sends only `SHA-256(raw signature bytes)` over a statement salted with a 256-bit `predicate.nonce` (or a further calendar nonce), and a hypothetical hosted A2A witness ([§19.3](registration-record.md#193-what-crosses-the-wire-and-the-privacy-exposure)) receives only that signature digest and offers **no public lookup by digest** ([§19.6](registration-record.md#196-abuse-and-mitigations)). Neither is a content or fingerprint resolver.

### 1.3 Assets and Protocol Objects Under Analysis

1. **Token / feature catalogues (`traceweave-catalogue-draft-2`)**: unkeyed 64-bit `sha256-first8-u64be` hashes ([extraction §7](../../spec/extraction.md#7-k-grams-and-hashing)), `kgramCount`, `partialWindow`, `tokenCount`, `byteLength`, `sha256`, opaque `id`, and UTF-8 byte `span` `[start, end)` per fingerprint ([catalogue contract §3.2, §3.7](../../spec/catalogue-report.md#37-commitment-and-privacy-class)). Image/media extensions add 256-bit PDQ or 64-bit ISCC Image-Code values ([C2PA mapping §1.2](c2pa-mapping.md#12-image-catalogue-entry--c2pa-fixture-f1-round-trip-f5)).
2. **Salted commitments (`sha256-salted-catalogue-v1`)**: `SHA256("Traceweave-Catalogue-v0.1\x00" || R || L || C)` with 32-byte OS-random `R` ([core](../../spec/core.md#private-catalogue-commitment)).
3. **Registration statements & `tw1-` references**: DSSE-wrapped `in-toto` Statement v1 carrying 1–64 `subject[].digest.sha256`, 256-bit `predicate.nonce`, `possession[]`, optional `catalogue` commitment, optional `claims.aiUse`, and `tw1-` (first 130 bits of `statementSha256` in Crockford base32 + 1 Luhn mod 32 check char; [§9.1](registration-record.md#91-text-reference-normative-frozen-2026-11-24)).
4. **Key identities & key events**: full 32-byte Ed25519 key digest (`keySha256`), 16-hex `keyid` hint, and signed time-stamped `rotated` / `retired` / `compromised` events ([§8](registration-record.md#8-key-identity-rotation-compromise-and-revocation-f3-b1b3-s1)).

---

## 2. Threat Model Summary Matrix

| Threat class | Adversary | Primary attack vector | Residual risk beyond crypto | Primary mitigations | RES.2 metric IDs |
| --- | --- | --- | --- | --- | --- |
| **1. Query leakage** | Honest-but-curious operator, log compromise, passive network observer | Logging unkeyed k-gram / prefix-bucket / digest / `tw1-` queries + IP/timing session correlation | Any remote query leaks existence, timing, origin, and multiplicity of interest | Local-only default (`T0`), static shelves (`T1`), batch/pad queries, no raw/fingerprints on registration wires | `M-QL-1`, `M-QL-2` |
| **2. Enumeration** | Unauthenticated or rate-limited external prober | Brute-forcing truncated `tw1-`, dictionary probing `subject.sha256`, scraping `keyid` / `keySha256` or sequential IDs | Any digest/key lookup oracle confirms guessed low-entropy files and links keys | No public digest/key lookup; require full 27-char `tw1-` or 256-bit `statementSha256`; per-work keys (`I0′`); uniform `not-found` | `M-EN-1`, `M-EN-2` |
| **3. Catalogue inference** | Semi-trusted peer, resolver operator, consortium insider | Inverting unkeyed `sha256-first8-u64be` via token k-gram rainbow tables; reading file structure from `span` / `byteLength` | Deterministic unkeyed hashes of low-entropy syntax are always dictionary-testable | Private-by-default catalogues (`M2.8`); salted commitments (`R`) until opening; omit spans/lengths from indices; bilateral keyed hashes (`KEYED.1`) | `M-CI-1`, `M-CI-2` |
| **4. Membership disclosure** | Adaptive oracle querier | Sending minimal `k + w - 1` (8-token) probes, sliding-window edits, or suppression/mode differentials to test corpus inclusion | A truthful match oracle inherently leaks membership of any attacker-chosen query `X` | No remote oracle over private corpora; query floors (`>> k+w-1`, `minRegionDistinctHashes >= 2`); omit seed coordinates; bilateral keyed catalogues | `M-MD-1`, `M-MD-2` |
| **5. Abuse** | Spammer, griefing competitor, DoS flooder, key thief / Sybil attacker | High-frequency k-gram index poisoning, max-seed/deep-JSON DoS, Sybil key-event floods, look-back compromise griefing, `tw1-` look-alikes | Anyone holding public text can register it; a thief with `K` inside `lookback` can dispute a recent rotation | Fail-closed parse/seed/depth caps; two-pass non-oscillating key events (`E1`); full 256-bit binding (`statementSha256`); caller quotas + no public lookup | `M-AB-1`, `M-AB-2` |

---

## 3. Systematic Threat Analysis

### 3.1 Query Leakage

#### Adversary model
- **Operator adversary ($\mathcal{A}_{\text{op}}$):** Honest-but-curious or subpoenaed resolver/host operator that logs every incoming query payload, response, timestamp, TLS fingerprint, and client network address.
- **Network observer ($\mathcal{A}_{\text{net}}$):** Passive observer (ISP, CDN edge, or compromised gateway) observing packet sizes, inter-arrival timing, SNI/DNS, and request bursts across resolver calls, static shelf fetches, and TSA/calendar requests.

#### Concrete attack vectors
1. **Unkeyed fingerprint dictionary testing by operator:** When a client queries a resolver with `sha256-first8-u64be` hashes (from `exact` or `normalized` channels), the operator gains the client's query hashes and can run offline dictionary matching against known repositories, boilerplate, or guessed snippets to recover what code or prose the client is investigating.
2. **Truncated hash / prefix-bucket intersection:** As noted in [initial draft review #2](../../docs/reviews/initial-draft-review.md) and [core](../../spec/core.md#privacy-defaults), sending 16–24-bit hash prefixes (e.g., to fetch "k-anonymous" buckets and filter locally) does not guarantee anonymity. A single file produces multiple winnowed fingerprints; intersecting the set of queried 16-bit or 24-bit prefixes across a single file (or across `exact` and `normalized` channels simultaneously) rapidly shrinks the candidate set to a unique artifact.
3. **Cross-query and multi-channel session correlation:** A client verifying a file or repository typically queries (a) multiple k-gram fingerprints, (b) `exact` and `normalized` hashes together, (c) `tw1-` bundle URLs, and (d) key-event or CRL/OCSP endpoints within a short time window. Even when `tw1-` carries no content or identity, correlating arrival times, source IP, TLS session tickets, and query cardinality reveals *which* works are being linked, the approximate token size of the queried file, and organizational review cadence.
4. **Static-shelf verification leakage (`T1`):** Fetching a registration bundle from a registrant-hosted URL next to a `tw1-` string reveals to that host *when* and from *which network* a specific `tw1-` registration is being verified ([registration design §9.1](registration-record.md#91-text-reference-normative-frozen-2026-11-24)).

#### Residual risk (not eliminable by cryptography alone)
- Any live network query reveals **participation, timing, client network identity (unless anonymized out-of-band), and query volume/multiplicity** to the contacted endpoint.
- No hashing or commitment scheme can hide a queried unkeyed k-gram or plain content `sha256` from the server if the server itself holds an index keyed by that exact digest. Even Private Information Retrieval (PIR) or Oblivious RAM (ORAM) cannot hide query occurrence and query count without dummy traffic and padded batches, and still leaves content-side confirmation risk if the server chooses what to return or logs side-channel size/timing.

#### Architectural mitigations
- **Local-first default (`T0`):** Keep extraction, cataloguing, comparison, and registration verification completely offline (`scripts/offline`, `WEB.2` zero-network assertion). Do not send fingerprints or artifact digests over the network during normal verification.
- **Static distribution over interactive query APIs (`T1`):** Distribute public release catalogues or verification bundles as immutable static files/archives (mirrored or fetched as a whole snapshot) rather than per-snippet query endpoints, decoupling verification reads from per-item lookup logs.
- **Wire hygiene on registration routes:** Enforce `content-on-wire` and `forbidden-field` ([registration design §19.3](registration-record.md#193-what-crosses-the-wire-and-the-privacy-exposure)): only `SHA-256(raw DSSE signature)` (salted by 256-bit `predicate.nonce`) may cross to time services or an optional witness.
- **If a future opt-in resolver profile is ever specified:** Require fixed-size padded batches or whole-bucket/shard downloads, prohibit raw IP/query retention in operator policy, forbid sending `exact` and `normalized` channel queries in unlinkable-intended single probes without batching, and document prefix-bucket intersection leakage explicitly without claiming *k*-anonymity.

#### Proposed RES.2 leakage metrics
- **`M-QL-1` (Bucket-intersection uniqueness rate):** Given a synthetic corpus of $N$ files and a prefix width $b \in \{16, 20, 24, 32, 64\}$ bits, the fraction of queried files (numerator: uniquely identified files; denominator: $N$ files) whose queried prefix set intersects to a singleton set (anonymity set size $1$), plus the median anonymity set size as a function of fingerprints queried per file.
- **`M-QL-2` (Cross-channel / multi-query session linkability):** Given $M$ mixed multi-file verification sessions in synthetic traffic traces, the adversary's precision/recall (and F1 over $\binom{Q}{2}$ query pairs) in clustering queries originating from the same source repository or comparison job using timing, channel pairing, and bucket co-occurrence.

---

### 3.2 Enumeration

#### Adversary model
- **External prober ($\mathcal{A}_{\text{enum}}$):** Unauthenticated or multi-account client issuing high-rate automated queries to discover unlisted works, confirm whether specific target files were ever registered, or harvest all records belonging to a registrant.

#### Concrete attack vectors
1. **Abbreviated or prefix `tw1-` probing:** A canonical `tw1-` reference encodes 130 bits of `statementSha256` (`26` Crockford base32 characters + `1` Luhn mod 32 check character), which resists blind brute force ($2^{130}$). However, if a resolver allows prefix queries, substring/wildcard search, or abbreviated 4+4 display matching (40 bits, [§9.1](registration-record.md#91-text-reference-normative-frozen-2026-11-24)), an adversary can enumerate valid references at feasible cost ($2^{40}$ or far less for short prefixes) or harvest metadata via autocomplete.
2. **Content-digest dictionary probing (`subject.sha256`):** If a resolver indexes registrations by `subject[].digest.sha256`, an adversary with candidate files (scraped open-source repositories, leaked drafts, configuration templates, or short parameterized snippets) submits `SHA-256(candidate)` to discover whether and when that file was registered and retrieve its bundle/public key ([registration design §5](registration-record.md#5-what-publishing-each-value-reveals)).
3. **Key-hint (`keyid`) and public-key enumeration:** A 16-hex `keyid` is only 64 bits and is explicitly a hint, not identity ([trust policy §3](trust-policy.md#3-zero-reliance-on-unverified-hints)). A resolver indexing by `keyid` or `keySha256` lets anyone who observes a single public key (from one disclosed registration, I1 posting, or I2 Fulcio log entry) enumerate **every** other registration and key event under that key—even works the registrant kept unlisted.
4. **Sequential index / log traversal:** Any public transparency log or resolver assigning monotonic `logIndex` or sequential URLs (`/records/1`, `/records/2`, …) lets an enumerator walk the entire population of registered digests and public keys in $O(N)$ requests.

#### Residual risk (not eliminable by cryptography alone)
- Any public oracle answering "is digest $H$ registered?" necessarily acts as a **confirmation oracle** for guessed low-entropy content (short files, templates, or known public files).
- Any directory indexed by signer public key links all works signed by that key once the key is known; signing key continuity (`I0`) and cross-work unlinkability (`I0′`) are fundamentally in tension.

#### Architectural mitigations
- **No public lookup by content digest or key:** Any future optional resolver MUST NOT expose public lookup by `subject.sha256`, `possession[].sha256`, `keyid`, or `keySha256` ([registration design §19.6](registration-record.md#196-abuse-and-mitigations)).
- **Exact full-reference lookup only:** If a static shelf or opt-in bundle store resolves `tw1-` references, lookup MUST require the full canonical 27-character `tw1-` (strict Crockford base32 + valid Luhn mod 32 check character, or full 256-bit `statementSha256`), with zero prefix matching, zero wildcard search, and zero listing/enumeration endpoints.
- **Unlinkable per-work keys (`I0′`):** Recommend `I0′` (fresh Ed25519 key per work, optionally linked later via a signed key list in a dispute) whenever cross-work correlation is undesired ([registration design §7](registration-record.md#7-signer-identity-options)).
- **Uniform response & rate limits:** Return identical error status/timing for syntactically valid unknown references and unlisted items; apply per-caller authentication and strict query budgets on any opt-in service.

#### Proposed RES.2 leakage metrics
- **`M-EN-1` (Dictionary confirmation yield):** Over a synthetic corpus of $N$ registered works mixed with $M$ unregistered distractors (stratified into high-entropy files vs low-entropy templates/snippets), the true-positive discovery rate (confirmed hits / $N$) and false-discovery rate under an attacker query budget $Q$ against (a) full `tw1-`, (b) $p$-character `tw1-` prefixes, and (c) `subject.sha256` lookup.
- **`M-EN-2` (Key-linkage exposure ratio):** Fraction of a synthetic multi-work registrant's portfolio (discovered works / total works) recoverable by an adversary starting from 1 disclosed bundle under key-policy `I0` vs `I0′` when querying a key-indexed vs `tw1-`-only endpoint.

---

### 3.3 Catalogue Inference

#### Adversary model
- **Catalogue-holding peer or resolver ($\mathcal{A}_{\text{cat}}$):** Any party that receives a `traceweave-catalogue-draft-2` file (or queries/indexes its hashes and metadata) and seeks to reconstruct source-code structure, token sequences, vendor dependencies, or programming language/profile details without holding the original source bytes.

#### Concrete attack vectors
1. **Structural reconstruction from spans and counts:** Every `ok` entry in `traceweave-catalogue-draft-2` exposes `byteLength`, `tokenCount`, per-channel `kgramCount`, `partialWindow`, and ordered fingerprints `{hash, position, span}` ([catalogue contract §3.2, §3.7](../../spec/catalogue-report.md#37-commitment-and-privacy-class)). Plotting consecutive `span` `[start, end)` intervals and gaps between winnowed positions leaks file byte size, average token density, large comment/whitespace gaps, and approximate function/block boundaries.
2. **Offline dictionary inversion of unkeyed k-grams:** Because `sha256-first8-u64be` is unkeyed and domain-separated only by public `(profile, profileVersion, channel, k)` ([extraction §7](../../spec/extraction.md#7-k-grams-and-hashing)), an adversary can precompute a lookup table over millions of common token $k$-grams (e.g., `k = 5`: `if err != nil {`, `for i := 0;`, `pub fn new ( )`, import blocks, license headers) and invert matched `exact` and `normalized` hashes directly back to literal token streams and structural skeletons.
3. **Profile, language, and dependency fingerprinting:** Observing `profile.id`, `extractionConfig.channels` (`["exact","normalized"]` vs `["exact","folded","skeleton"]`), `k`, `window`, and the intersection of catalogue hashes against public OSS/vendor catalogues identifies the exact language, toolchain profile, and third-party vendor libraries inside a private codebase—even when artifact `id`s are opaque.
4. **Shared-key consortium inversion:** As highlighted in [initial draft review #2](../../docs/reviews/initial-draft-review.md), replacing unkeyed SHA-256 with a single consortium-wide HMAC key does *not* stop dictionary inversion by any authorized participant holding that key.

#### Residual risk (not eliminable by cryptography alone)
- Any deterministic, unkeyed fingerprint scheme that allows independent third-party matching over identical inputs allows **offline guessing attacks** against low-entropy token sequences ($k$-grams from common idioms or small templates).
- Even if hashes are salted/keyed, structural metadata (`byteLength`, `tokenCount`, ordered `position` and `span` arrays) directly reflects artifact length and winnowing density if exposed in a shared index.

#### Architectural mitigations
- **Private-by-default catalogues (`M2.8`):** Treat catalogues with the same confidentiality as source code ([catalogue contract §3.7](../../spec/catalogue-report.md#37-commitment-and-privacy-class)); store outside source trees by default (`0` files written inside temporary checkouts).
- **Salted commitments before opening (`sha256-salted-catalogue-v1`):** Public or shared registration records store only the salted commitment (`R` = 32 fresh OS-random bytes independent of `predicate.nonce`, [registration design §4.4](registration-record.md#44-catalogue-commitment-optional)). Nothing about the catalogue leaks until `catalogueOpening` is explicitly disclosed.
- **Minimal index projection:** Any optional resolver index MUST strip `span`, `position`, `byteLength`, `tokenCount`, and path-like `id`s (enforce opaque `^[a-z0-9][a-z0-9._-]{0,63}$` labels).
- **Per-relationship keyed catalogues (`KEYED.1`):** For semi-trusted bilateral or opt-in remote indexing, evaluate per-relationship keyed hash selection/hashing (`KEYED.1`) rather than unkeyed or globally shared consortium keys.

#### Proposed RES.2 leakage metrics
- **`M-CI-1` (K-gram dictionary inversion rate):** On a synthetic benchmark of source/text catalogues extracted under shipped configs (`k=5, w=4`), the fraction of distinct fingerprints (inverted fingerprints / total distinct fingerprints in catalogue) recovered by an adversary holding a fixed public-corpus $k$-gram dictionary of size $D \in \{10^4, 10^5, 10^6\}$, reported separately for `exact` and `normalized` channels.
- **`M-CI-2` (Structural & dependency inference accuracy):** Error in estimating hidden `byteLength` / `tokenCount` from stripped fingerprint lists (MAE / $R^2$), plus precision/recall of identifying injected vendor/boilerplate modules (against denominator of total synthetic modules) from an unlabelled catalogue or stripped hash set.

---

### 3.4 Membership Disclosure

#### Adversary model
- **Adaptive oracle attacker ($\mathcal{A}_{\text{mem}}$):** An adversary allowed to submit chosen candidate files or short synthetic token sequences to a resolver (or request `compare` reports over attacker-supplied candidate catalogues) to determine whether a specific secret snippet, credential pattern, or proprietary file exists inside a private target corpus.

#### Concrete attack vectors
1. **Minimal-window (`k + w - 1`) probe oracle:** Winnowing guarantees that any unchanged run of at least $k + w - 1$ tokens in a channel produces at least one shared fingerprint under identical configuration ([extraction §8](../../spec/extraction.md#8-winnowing-selection)). Under shipped `k = 5, w = 4`, an attacker constructs a minimal 8-token file containing a suspected secret token sequence (or wraps a target snippet in neutral syntax) and queries the resolver. A single returned seed or match confirms that exact 8-token run exists in the indexed corpus.
2. **Adaptive sliding-window / binary-search expansion:** If the resolver returns matching counts, `distinctHashes`, region spans, or `candidate` vs `reference` match flags, the attacker probes variations of a known prefix (varying the $k$-th token over likely identifiers, literals, or keywords in `exact` vs `normalized` modes) to recover adjacent secret tokens one step at a time.
3. **Differential suppression & mode probing:** Submitting identical probes with and without a boilerplate/vendor `suppressionCatalogueSha256`, or comparing `exact` vs `normalized` responses, isolates private custom code from common idioms and reveals whether a suspect file matches with identifiers intact vs renamed.
4. **Whole-file `subject.sha256` / `possession` confirmation:** Querying a registration service by `subject.sha256` acts as a 1-bit exact membership oracle for any candidate file the attacker already holds ([registration design §5](registration-record.md#5-what-publishing-each-value-reveals)).

#### Residual risk (not eliminable by cryptography alone)
- **Fundamental oracle limit:** Any system that accurately answers whether an untrusted caller's input overlaps a private corpus leaks membership of the caller's chosen input. Neither encryption in transit nor salted storage prevents an adaptive caller from using the match response itself as a membership oracle, particularly when winnowing locality operates down to `k + w - 1 = 8` tokens.
- As stated in [core](../../spec/core.md#interpretation) and [extraction §12](../../spec/extraction.md#12-what-the-baseline-does-not-claim), even a genuine fingerprint overlap does **not** establish training membership, authorship, or infringement.

#### Architectural mitigations
- **No public membership oracle (`T0` default):** Comparisons run locally against catalogues the verifier already holds or has been explicitly given in a bilateral dispute (`M2.1`).
- **Minimum query evidence & suppression floors:** Any opt-in resolver MUST reject single-hash or minimal-window queries, enforcing `minQueryTokens >> k + w - 1`, requiring at least `minRegionDistinctHashes >= 2` (or higher policy floor) before returning a hit, and suppressing known boilerplate before scoring.
- **Coarse response surface & query budgets:** Never return `span` offsets, `position` indices, or exact `seedCount` over a remote oracle to untrusted queriers; enforce strict per-caller query budgets to block adaptive token-by-token binary search.
- **Per-relationship keyed hashing (`KEYED.1`):** If a corpus owner exposes a remote index to authorized partners, key the hash function per authorized relationship so third parties cannot construct valid oracle probes.

#### Proposed RES.2 leakage metrics
- **`M-MD-1` (Membership inference advantage vs probe length):** Across $N$ balanced positive (in-corpus) and negative (out-of-corpus) synthetic probes of token length $L \in \{8, 16, 32, 64, 128\}$ under shipped `(k=5, w=4)` and candidate `(k=8..12, w=8..16)` configs, measure the attacker's membership advantage $\text{Adv} = \text{TPR} - \text{FPR}$ (with explicit TP/FN/FP/TN denominators) with and without boilerplate suppression and minimum-distinct-hash thresholds.
- **`M-MD-2` (Adaptive extraction query count):** Median and worst-case number of adaptive oracle queries $Q$ (out of max budget $Q_{\max}$) required to confirm membership of a target function or recover a hidden token extension from an `exact`/`normalized` oracle response.

---

### 3.5 Abuse (Spam, Griefing, DoS, Sybil Key-Event & False Compromise Flooding)

#### Adversary model
- **Spammer / squatter ($\mathcal{A}_{\text{spam}}$):** Automated actor mass-registering scraped public files or flooding an index with synthetic registrations.
- **Griefer / DoS attacker ($\mathcal{A}_{\text{dos}}$):** Attacker crafting pathological catalogues, high-multiplicity k-gram floods, malformed deep JSON, or high-rate requests to force verifier abstentions (`seed-limit-exceeded`), truncate valid match lists (`maxRegionsPerMode`), or exhaust CPU/memory/storage.
- **Key thief / hostile collaborator ($\mathcal{A}_{\text{key}}$):** Actor holding a stolen old key `K` (or forging/flooding unsigned/untrusted key events) seeking to invalidate honest history, cause evaluation oscillation, or deceive verifiers via `tw1-` look-alikes.

#### Concrete attack vectors
1. **Scraped-corpus squatting & griefing:** An adversary scrapes public repositories or pasted text and registers them under its own key (`tw1-` squatting, [registration design §19.6](registration-record.md#196-abuse-and-mitigations)), then points to its records to harass creators or pollute a public directory.
2. **False-match / seed-explosion index poisoning:** An adversary injects catalogues packed with high-frequency valid k-grams (or boilerplate-adjacent repetitive tokens such as repeated `;` / common control-flow patterns) into a shared index. During comparison (`traceweave-seed-merge-draft-2`), cross-product seed generation ($\sum \text{occ}_{\text{ref}} \times \text{occ}_{\text{cand}}$) explodes past `maxSeedsPerMode` (`100,000` shipped; `10,000,000` ceiling, [catalogue contract §4, §5.4](../../spec/catalogue-report.md#54-seeds-and-the-seed-limit)), forcing `seed-limit-exceeded` abstentions, or fills `maxRegionsPerMode` (`1,000` shipped) so legitimate regions are truncated.
3. **Parser & resource-exhaustion DoS:** Submitting inputs just above `maxInputBytes` (8 MiB), configurations with `k > 16` or `window > 128` (`O(k·N)` hashing blowup, [extraction §10a](../../spec/extraction.md#10a-resource-bounds-and-complexity)), deeply nested JSON (`> 64` containers, [catalogue contract §3.6 step 1](../../spec/catalogue-report.md#36-validation-by-a-consumer)), duplicate JSON keys, or malformed Ed25519 points (`[8]A == identity` or `S >= L`, [trust policy §4.1](trust-policy.md#41-strict-signature-and-parsing-rules)) to crash or hang verifiers/resolvers.
4. **Sybil key-event flooding & oscillation attacks:** Flooding a key-event feed with thousands of unauthorized events (`ignored-unauthorized`), single-source/un-timestamped claims (`ignored-no-proved-time`), multi-signature wrapper masks (prepending a foreign signature to a valid event, [registration design §8](registration-record.md#8-key-identity-rotation-compromise-and-revocation-f3-b1b3-s1)), or crafted sequences intended to trigger non-terminating fixed-point loops (draft-4 E1 oscillation).
5. **Hostile / early-dated compromise griefing:** A thief who obtains an old key `K` (or a former collaborator) submits a time-stamped `compromised` report with an early claimed `Tc` to retroactively invalidate honest registrations, or files a `compromised` report within `compromiseLookbackSeconds` after the owner's honest rotation `K -> S` to permanently dispute `K -> S` (`I6` / RD18 trade-off, [registration design §8](registration-record.md#8-key-identity-rotation-compromise-and-revocation-f3-b1b3-s1)).
6. **`tw1-` equivocation & look-alike phishing:** A well-resourced adversary spends $\sim 2^{65}$ SHA-256 work to craft two statements sharing one 130-bit `tw1-` prefix (showing innocuous content to one verifier and disputed content to another), or $\sim 2^{40}$ work to match the first 4 + last 4 characters of a victim's `tw1-` alongside a spoofed "verify here" URL ([registration design §9.1](registration-record.md#91-text-reference-normative-frozen-2026-11-24)).

#### Residual risk (not eliminable by cryptography alone)
- **First to register is not first to create:** No cryptographic timestamp or signature stops someone who already possesses public text or code from registering it; deterrence relies on mandatory §11 / §19.5 non-authorship wording and the absence of a public accusation registry.
- **Look-back window trade-off (RD15):** If a thief compromises key `K` and files a time-stamped `compromised` event inside `compromiseLookbackSeconds` after an honest `K -> S` rotation, the rotation is permanently `disputed` (preventing silent hijacking if the thief was the one who rotated first), forcing recovery via pre-listed `recoveryKeys` or out-of-band verification.
- **Open-access quota bypass:** If any future public resolver allows unauthenticated or cheaply Sybil-created accounts, rate limits alone can be bypassed horizontally at operator cost.

#### Architectural mitigations
- **Local verification & verifier-owned trust policy:** Every verifier controls its own `trustedKeys`, `recoveryKeys`, `timeRoots`, and `suppressionCatalogueSha256` locally ([trust policy §2](trust-policy.md#2-policy-structure-and-fail-closed-validation)); external spam cannot enter a verifier's trust set or poison its local comparison.
- **Fail-closed bounds before cryptography:** Enforce `nesting depth <= 64`, strict JSON (no duplicate keys, no non-finite numbers), `k <= 16`, `window <= 128`, `maxInputBytes <= 8 MiB`, `maxSeedsPerMode <= 10^7`, `maxRegionsPerMode <= 10^5`, and cofactorless strict Ed25519 checks (`§10.1`).
- **Hardened key-event evaluation (`§8`):** Enforce single-signature key-event envelopes (`key-event-signatures`), identify events by `SHA-256(payload || signature)`, require quorum bounds `E` (`ignored-no-proved-time`), clamp compromise claims to `start = max(Tc, E - compromiseLookbackSeconds)`, and run the two-pass non-oscillating procedure (`E1`: Pass 1 standing, Pass 2 disputes with no feedback; a successor's report never disputes its own appointment).
- **Full 256-bit binding & strict `tw1-` display:** Bind machine records (`report-link`, C2PA `org.traceweave.registration-link`, IMG.5 `registrationLink`) to the full 256-bit `statementSha256` rather than `tw1-` alone; require tools to compare all 27 characters of `tw1-` and forbid abbreviated rendering or trusting remote "verify here" pages ([registration design §9.1](registration-record.md#91-text-reference-normative-frozen-2026-11-24)).
- **Hosted-service gating (`SK.5`) & caller quotas:** Any future hosted witness or resolver requires an accountable operator (`SK.5`), up-front caller authentication, idempotency keyed on `(caller, messageId)`, per-caller quotas, `REJECTED` refusals, and **no public digest lookup** ([§19.4, §19.6](registration-record.md#196-abuse-and-mitigations)).

#### Proposed RES.2 leakage / resilience metrics
- **`M-AB-1` (Index-poisoning abstention & truncation rate):** Under a synthetic candidate catalogue / index where $p \in \{1\%, 5\%, 10\%\}$ of entries are injected adversarial high-frequency / boilerplate-flooding entries, the fraction of legitimate positive comparisons (affected comparisons / total positive comparisons) degraded to `seed-limit-exceeded` abstention or losing their true-match region past `maxRegionsPerMode`.
- **`M-AB-2` (Parser / verification amplification factor):** Ratio of resolver/verifier CPU time and peak memory per input byte (and valid vs rejected byte ratio) across synthetic adversarial inputs: max-bound catalogues (`k=16, w=128, 8 MiB`), `depth=65` JSON, duplicate-key payloads, `S >= L` / small-order Ed25519 keys, and $N_{\text{ev}}$ Sybil `ignored-unauthorized` / `ignored-no-proved-time` key events.

---

## 4. Pre-Registration Summary for RES.2

Before any **RES.2** synthetic experiment is run, the protocol commit MUST freeze:

1. **Adversary query model $\mathcal{Q}(\mathcal{C}_{\text{priv}}, \mathcal{C}_{\text{bg}}, Q, D)$:**
   - **Target private corpus $\mathcal{C}_{\text{priv}}$:** synthetic Go/Rust/Python/text catalogues built strictly from existing committed synthetic fixtures/generators (no private or held-out evaluation code).
   - **Auxiliary background dictionary $\mathcal{C}_{\text{bg}}$:** size-$D$ public synthetic $k$-gram dictionary available to $\mathcal{A}$ offline.
   - **Oracle interface $O(q)$:** parameterized across the four candidate query surfaces to be compared against the local-only baseline:
     - $O_{\text{prefix}}(b)$: $b$-bit truncated hash prefix lookup ($b \in \{16, 20, 24, 32, 64\}$);
     - $O_{\text{fp}}$: unkeyed full 64-bit `sha256-first8-u64be` lookup with region/seed vs count-only responses;
     - $O_{\text{ref}}$: `tw1-` (full vs truncated prefix) and `subject.sha256` lookup;
     - $O_{\text{keyed}}$: per-relationship keyed hash lookup (`KEYED.1` candidate baseline).
   - **Query budget $Q$:** bounded per-run query count per adversary role ($\mathcal{A}_{\text{op}}$, $\mathcal{A}_{\text{enum}}$, $\mathcal{A}_{\text{cat}}$, $\mathcal{A}_{\text{mem}}$, $\mathcal{A}_{\text{dos}}$).

2. **Frozen metric table (all figures MUST report numerator and denominator):**

| ID | Threat class | Metric definition (numerator / denominator) |
| --- | --- | --- |
| `M-QL-1` | Query leakage | Uniquely isolated files (anonymity set $= 1$) / $N$ synthetic queried files at prefix width $b$; median anonymity set size |
| `M-QL-2` | Query leakage | Session-clustering F1 over $\binom{Q}{2}$ query pairs (correctly linked same-job query pairs / total same-job pairs & predicted pairs) |
| `M-EN-1` | Enumeration | Confirmed unlisted works / $N$ planted works (and false confirmations / $M$ distractors) at budget $Q$ |
| `M-EN-2` | Enumeration | Discovered registrant works / total registrant works starting from 1 disclosed bundle (`I0` vs `I0′`) |
| `M-CI-1` | Catalogue inference | Inverted distinct fingerprints / total distinct fingerprints in catalogue from size-$D$ dictionary (`exact` & `normalized`) |
| `M-CI-2` | Catalogue inference | Module-identification precision/recall (identified vendor modules / total synthetic modules) & size estimation MAE from stripped catalogues |
| `M-MD-1` | Membership disclosure | Membership advantage $\text{TPR} - \text{FPR}$ (TP / $N_{\text{pos}}$ minus FP / $N_{\text{neg}}$) across probe lengths $L \in \{8, 16, 32, 64, 128\}$ |
| `M-MD-2` | Membership disclosure | Queries $Q$ required to confirm/extend a target $L$-token passage / max budget $Q_{\max}$ (successes / trials) |
| `M-AB-1` | Abuse | Degraded legitimate comparisons (`seed-limit-exceeded` or true region truncated) / total positive comparisons at poison rate $p\%$ |
| `M-AB-2` | Abuse | Peak CPU ms / KiB input and peak RSS / input bytes across adversarial parse, seed, and Sybil key-event floods (rejected / total inputs) |

3. **Explicit non-goals:**
   - **RES.1–RES.3** evaluate leakage and abuse risks on synthetic catalogues; they do **not** authorize deploying a public resolver, choosing a hosted operator (**SK.5**), or turning on public logging (**RD3**).
   - Until **RES.1–RES.3** are met and **SK.5** is explicitly decided by the owner, the Traceweave specification operates exclusively under **Tier T0** (local offline) and optional **Tier T1** (registrant-chosen static shelves).
