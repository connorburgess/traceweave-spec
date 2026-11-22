# Draft catalogue and comparison-report contract: token-fingerprint baseline

Status: **draft for review, revision draft-2, 2026-11-22.** Roadmap item TW-03. Gates: [roadmap-v2](../../ROADMAP.md) M1.3 (catalogue and report schemas) and M2.6 (hand-derived matching vectors). This contract also fixes what I2 in the [implementation plan](implementation-repo-plan.md#milestones) must reproduce for M2.4 and M2.5. It builds on the reviewed [extraction contract](extraction-contract.md) and changes nothing in it.

This revision resolves the [clean-room review](catalogue-report-contract-review.md) Part 1 findings 1–10 and guesses G1–G6, plus the non-blocking additions of its confirmation pass (G7, invariance, cap and suppression-order vectors). Every disposition is in [§13](#13-review-dispositions). Draft-2 changes formats: catalogue `traceweave-catalogue-draft-2`, comparison `traceweave-seed-merge-draft-2`, report `traceweave-report-draft-2`. Draft-1 identifiers are no longer accepted.

This is research material, not a normative change. It does not modify [core](../../spec/core.md), [attestations](../../spec/attestations.md), [conformance](../../spec/conformance.md), `schemas/`, `profiles/` or `test-vectors/`. "MUST" describes what this draft proposes for an implementation claiming to follow it. The draft schemas and vectors are in [matching-vectors/](matching-vectors/README.md). Nothing here is a registered algorithm. No parameter is tuned or calibrated.

Every choice an implementation could otherwise make differently is fixed below. Decisions that change bytes are listed in [§11](#11-decisions) as "decided in draft, pending owner confirmation", with the reason. Questions still open are listed there too.

## 1. Pipeline and scope

```
extraction config bytes + artifact bytes  ──extract (extraction contract)──►  extraction results
extraction results + artifact ids         ──catalogue (§3)───────────────────►  catalogue bytes
reference + candidate (+ optional suppression) catalogue bytes + comparison config bytes ──compare (§5)──► body (§6)
body + provenance (§6.6)                  ──────────────────────────────────►  report document
```

Comparison reads **only** the catalogues and the comparison configuration. It never reads source text, so a report can be reproduced from the catalogues alone.

That is not the same as "comparing without disclosing code". The parties exchange catalogues, and a catalogue lets its holder test guessed code against it. The privacy class of each object is stated in [§3.7](#37-commitment-and-privacy-class) and [§6.7](#67-privacy-class-of-the-report).

**Outside this contract, by design:**
- **Candidate selection, indexing and ranking.** The comparison is exhaustive over the two catalogues it is given. Any index or ranking that chooses which artifacts to compare runs *before* the comparison, and its result is simply the candidate catalogue, whose digest the body records (`inputs.candidateCatalogueSha256`). The body has no rank, score or index field and no place to put one (§7). Information about how candidates were generated (exhaustive, or which index chose them) belongs in a **separate record keyed by `bodySha256`**. Coordinator decision: it is not a report field.
- **Origin, dependency and licence links.** These are not report fields. A separate record (for example an M2.7 review packet) refers to a report by its `bodySha256` and to a region by its region key (§5.5).
- **Also outside:** eligible-file selection (extraction OD-14), signing, trust, timestamps, resolver queries and keyed fingerprints.

## 2. What is taken from extraction

For each artifact, the catalogue uses these extraction contract §9 fields:
- the SHA-256 and byte length of the input;
- `status`;
- for errors, `error.code` and `error.offset`;
- `tokenCount`;
- per channel, `partialWindow` and the fingerprints (position, hash, span).

`kgramCount` is defined as `max(0, tokenCount − k + 1)` and is computed from `tokenCount`, because extraction §9 makes k-gram lists optional in production (G6). The catalogue uses no tokens, token text, k-gram lists, window selections or normalized values.

## 3. Catalogue record (`traceweave-catalogue-draft-2`)

Schema: [catalogue.schema.json](matching-vectors/catalogue.schema.json) (structure only). §3.3–§3.6 are part of the contract, and [check_matching.py](matching-vectors/check_matching.py) enforces them.

### 3.1 Fields

| Field | Content |
| --- | --- |
| `catalogueVersion` | `traceweave-catalogue-draft-2` |
| `profile` | `{configSha256, id, version}`: the core profile triple ([core](../../spec/core.md#claims-and-records)). It equals the extraction configuration's `profile` and `profileVersion`, and the SHA-256 of its exact bytes (extraction §10) |
| `extractionConfig` | The eight parsed values of the extraction configuration. Re-serialized in extraction §10 canonical form (fixed key order, final LF), they MUST hash to `profile.configSha256` |
| `artifacts` | One or more entries (§3.2) |

**One configuration per catalogue (G3).** Every artifact in a catalogue was extracted under the same extraction configuration bytes. A builder given artifacts extracted under different configurations MUST NOT produce a single catalogue. It produces one catalogue per configuration, or none.

### 3.2 Artifact entry

Every examined artifact gets an entry, including failures:

| `status` | Fields |
| --- | --- |
| `ok` | `byteLength`, `channels.exact` and `channels.normalized` (each `{fingerprints, kgramCount, partialWindow}`), `id`, `sha256`, `status`, `tokenCount` |
| `insufficient-tokens` | The same, with `kgramCount` 0, `partialWindow` false and `fingerprints` `[]` |
| `error` | `byteLength`, `error: {code, offset}`, `id`, `sha256`, `status`. No channels. `code` is a lexical or input code from the profile's closed list (extraction §4.8/§5.9) |

- **`unsupported-config` never appears in a catalogue (G4).** An extraction that fails with `unsupported-config` has no valid configuration to bind, so it yields no catalogue at all, and the schema's integer `offset` cannot hold its `null`.
- **`id`** is a caller-chosen opaque label matching `^[a-z0-9][a-z0-9._-]{0,63}$`, unique within the catalogue. Ids appear in reports, so a path-like id discloses the path.
- **`sha256`** is over the **original artifact bytes**. Two entries in one catalogue MUST NOT share a `sha256`.
- **A fingerprint** is `{hash, position, span}`: the 16-hex-digit hash, the k-gram position, and the k-gram's half-open UTF-8 byte span `[start, end)` (extraction §7).

### 3.3 Canonical serialization

The rules below apply to catalogue bytes and to report body bytes alike. Both are [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) (JCS) serializations, restricted so that every JCS implementation agrees:

1. Values are objects, arrays, strings, booleans and integers in `0 … 2⁵³ − 1`. There are no floats, negative numbers or `null`.
2. Every string consists of printable ASCII (U+0020–U+007E) other than `"` and `\`, so no escape sequence occurs. The schema patterns guarantee this for every field.
3. Object members are sorted by key in code-unit order (plain ASCII order here). There is no insignificant whitespace. Integers are plain decimal.
4. There is **no trailing newline**, and no byte-order mark.
5. **Fractions are raw counts and are never reduced (G1).** For example, `{"denominator":14,"numerator":14}` is never written as `1/1`. A zero denominator is written as `0`.
6. Arrays keep the order this contract gives them (§3.4, §6.5). No array is a set.

### 3.4 Ordering

- `artifacts` are sorted by `id`, compared as bytes, strictly increasing.
- `fingerprints` are sorted by `position`, strictly increasing. Equal hashes at different positions are all kept (extraction OD-16).

### 3.5 Not stored

The catalogue stores none of the following:
- source text, token text, token lists or normalized values;
- k-gram lists other than the selected fingerprints, and window selections;
- file paths, unless the caller chooses a path as `id`;
- timestamps, identities, licence or rights data, and signatures.

Every object has `additionalProperties: false`, so a catalogue with any extra field is malformed.

### 3.6 Validation by a consumer

Steps in order. The first failure decides the code:

1. **Strict JSON.** The bytes are UTF-8 and strict JSON, with no non-integer numbers and no constants. **Duplicate keys are detected during parsing, before any member is read**, so a catalogue with `catalogueVersion` twice is `malformed-catalogue` whatever the values (finding 6). The top level is an object with a string `catalogueVersion`. Otherwise: `malformed-catalogue`.
2. `catalogueVersion` is `traceweave-catalogue-draft-2`. Otherwise: `unsupported-catalogue`.
3. The schema holds. Otherwise: `malformed-catalogue`.
4. The canonical serialization (§3.3) equals the bytes exactly. Otherwise: `malformed-catalogue`.
5. `(profile.id, profile.version)` is implemented (here `go-tokens`/`draft-1` and `rust2024-tokens`/`draft-1`). Otherwise: `unsupported-profile`.
6. Semantic rules hold. Otherwise: `malformed-catalogue`.
   - **Binding.** `profile` matches `extractionConfig`, and `configSha256` is the digest of its canonical bytes. Ids are strictly ordered, and digests are unique.
   - **Error entries.** The code is in the profile's closed list. `byteLength > maxInputBytes` holds exactly when the code is `input-too-large`, which has offset 0. Any other offset is at most `byteLength`.
   - **Other entries.** `byteLength ≤ maxInputBytes`. `status` is `ok` exactly when `tokenCount ≥ k`. `kgramCount = max(0, tokenCount − k + 1)`. `partialWindow` is true exactly when `1 ≤ kgramCount < window`, and a partial window has exactly one fingerprint.
   - **Fingerprints.** Each position is below `kgramCount`, with `0 ≤ start ≤ end ≤ byteLength` (finding 9). The span may be empty: with k = 1, a Go inserted `;` k-gram has span `[e, e)`, and `e` can equal `byteLength`. Positions and span starts strictly increase, and span ends never decrease. When `kgramCount ≥ window`: consecutive positions differ by at most `window`, the first position is below `window`, the last is at least `kgramCount − window`, and the count lies between ⌈(m − w + 1)/w⌉ and m − w + 1.

Step 6 checks only that the fingerprints have the shape winnowing produces. Their *correctness* needs the sources, and is checked in the vectors by re-extraction.

### 3.7 Commitment and privacy class

The canonical bytes are the exact `C` of core's `sha256-salted-catalogue-v1` commitment.

**Privacy class: private.** The hashes are unkeyed (extraction §7), and short normalized token runs have little entropy. Anyone holding a catalogue can therefore:
- test guessed code against it;
- confirm a guessed whole file through `sha256`;
- read file structure from the spans.

Exchanging catalogues for a comparison discloses all of this to the other party. Handle a catalogue like source code ([core privacy defaults](../../spec/core.md#privacy-defaults)).

## 4. Comparison configuration

Exact shipped bytes ([comparison-config.json](matching-vectors/comparison-config.json), SHA-256 `39345e9c8de2b566d19943563326062a46edd38e429a4a96f169307b15147333`), one line ending in LF:

```
{"comparison":"traceweave-seed-merge-draft-2","modes":["exact","normalized"],"minRegionDistinctHashes":2,"mergeGap":4,"maxSeedsPerMode":100000,"maxRegionsPerMode":1000,"suppressionCatalogueSha256":"none"}
```

Validation, in order. Any failure is `unsupported-comparison-config`:

1. UTF-8 with exactly one line break, which is a final LF, and no CR.
2. Strict JSON. Duplicate keys are rejected during parsing, and non-integer numbers and constants are rejected.
3. A top-level object with exactly these seven keys in this order.
4. `comparison` is `traceweave-seed-merge-draft-2`, and `modes` is exactly `["exact","normalized"]`.
5. `minRegionDistinctHashes`, `mergeGap`, `maxSeedsPerMode` and `maxRegionsPerMode` are integers in 1 … 2³² − 1, written in decimal with no sign, leading zero or exponent.
6. `suppressionCatalogueSha256` is `"none"` or 64 lowercase hexadecimal digits.
7. Re-serialization reproduces the bytes.

[comparison-config-negative.json](matching-vectors/comparison-config-negative.json) lists 22 configurations that MUST be rejected.

**Parameters** (experimental; reports say `"parameterStatus": "experimental"`):

| Parameter | Meaning | Shipped |
| --- | --- | --- |
| `minRegionDistinctHashes` | Minimum evidence: distinct non-common hashes a region needs to be reportable (§5.6) | 2 |
| `mergeGap` | Largest reference-position gap that joins two seeds on one diagonal. Consecutive fingerprints inside an unchanged run are at most `window` apart (extraction §8) | 4 |
| `maxSeedsPerMode` | Above this many seeds, a mode abstains with `seed-limit-exceeded` (§5.4) | 100000 |
| `maxRegionsPerMode` | Regions listed per mode. The rest are counted, not listed (§5.7) | 1000 |
| `suppressionCatalogueSha256` | Digest of the boilerplate catalogue that defines common hashes, or `none` (§5.2) | `none` |

Binding the suppression catalogue's digest into the configuration means the configuration digest, which every report records, also identifies which common-code list was used.

## 5. Comparison algorithm (`traceweave-seed-merge-draft-2`)

### 5.1 Rejection order (report level)

The first failure produces a rejected body (§6.4):

1. The comparison configuration is invalid (§4): `unsupported-comparison-config`, side `comparison-config`.
2. The suppression binding does not hold: `suppression-catalogue-mismatch`, side `suppression`. It holds only in two cases:
   - the configuration says `none` and no suppression catalogue is supplied;
   - the configuration gives a digest and a suppression catalogue whose exact bytes have that SHA-256 is supplied.

   Configuration `none` with a supplied catalogue is therefore an explicit rejection. It is never silently ignored (`go-suppression-unexpected`). This check runs before any catalogue is parsed. It compares bytes only, so a malformed suppression catalogue with a wrong digest is a binding mismatch (`go-suppression-order-binding-before-validity`), and it takes precedence over a malformed reference (`go-suppression-order-binding-before-reference`).
3. The reference catalogue fails §3.6: its code, side `reference`.
4. The candidate catalogue fails §3.6: its code, side `candidate`.
5. The suppression catalogue, if supplied, fails §3.6: its code, side `suppression`.
6. The candidate's `(profile.id, profile.version)` differs from the reference's: `profile-mismatch`, side `candidate`. Then the same check for the suppression catalogue, side `suppression`.
7. The candidate's `profile.configSha256` differs from the reference's: `config-mismatch`, side `candidate`. Then the same check for the suppression catalogue, side `suppression`.

Steps 6 and 7 each run for both sides before the next step starts. A suppression profile mismatch is therefore reported ahead of a candidate configuration mismatch (`go-suppression-order-profile-before-config`), and within a step the candidate comes first (`go-suppression-order-candidate-config-first`, `go-suppression-order-candidate-validity-first`). A bound but malformed suppression catalogue is reported at step 5 (`go-suppression-order-malformed-bound`).

No fallback, re-extraction or cross-configuration comparison is attempted.

### 5.2 Common hashes (suppression)

For mode `exact` or `normalized`, a hash is **common** if and only if it occurs among the fingerprints, in that channel, of any `ok` artifact of the supplied suppression catalogue. Several occurrences make no difference. With no suppression catalogue, no hash is common.

Commonness does not depend on the reference or candidate catalogues. Adding or removing unrelated reference files cannot change any pair's outcome (finding 1). Vectors `go-invariance-three-references` and `go-invariance-plus-unrelated` have three ok reference files that share the copied loop, and the checker requires every pair common to both vectors to have an identical result. An implementation that still applied draft-1 document-frequency suppression would mark the loop's hashes common and fail them.

Suppression is **advisory and corpus-dependent**. It removes only the hashes that winnowing happened to select in the boilerplate catalogue's files, so a shared idiom whose k-grams were selected differently is not suppressed (§10). A match produced by boilerplate is expected behavior, not an error (`go-boilerplate-unsuppressed`).

### 5.3 Pairs

Every reference artifact is paired with every candidate artifact, ordered by (reference `id`, candidate `id`) as bytes. Rules in order:

1. Reference status `error`: the pair is `not-compared`, `reference-extraction-error`.
2. Candidate status `error`: `not-compared`, `candidate-extraction-error`.
3. Either side `insufficient-tokens`: `not-compared`, `insufficient-tokens` (abstention).
4. Otherwise `compared`, with §5.4–§5.9 run for mode `exact` on the exact channel and mode `normalized` on the normalized channel.

### 5.4 Seeds and the seed limit

A **seed** is a pair `(p, q)` such that reference fingerprint position `p` and candidate fingerprint position `q` have equal hashes. All such pairs are seeds: the full cross product of the occurrences of each hash. No seed is preferred or dropped. The diagonal of a seed is `q − p`.

`seedCount` is the number of seeds, Σ over shared hashes of (reference occurrences × candidate occurrences). It can be computed before any seed is enumerated:
- If `seedCount = 0`, the outcome is `no-shared-fingerprints`.
- If `seedCount > maxSeedsPerMode`, the mode abstains with `seed-limit-exceeded`. No regions are formed, `regions` is `[]` and all region counts are 0.
- Equality with the limit is allowed (`go-output-caps`).

Containment and similarity (§5.9) are always reported.

### 5.5 Regions and the region key

Group seeds by diagonal. Within a diagonal, sort by `p` and cut into maximal runs whose consecutive seeds satisfy `p_next − p ≤ mergeGap`. A gap of exactly `mergeGap` joins and `mergeGap + 1` splits (`rv-gap-equal`, `rv-gap-boundary`, `rv-gap-boundary-offset`). Each run is a candidate matched region. Seeds on different diagonals never merge.

Region fields:
- `seeds`: `[p, q]` pairs in increasing `p`;
- `referenceSpan` and `candidateSpan`: from the smallest start to the largest end of the region's fingerprint spans on that side, in UTF-8 bytes (`go-non-ascii-shift` shows a 28-byte, 12-code-point shift);
- `distinctHashes`: the number of distinct hashes among the seeds;
- `distinctCommonHashes`: how many of those are common.

Spans cover matched k-grams only. They are lower bounds on the copied extent, never widened from source.

Regions are ordered by their first seed `(p, q)`, which is unique.

**Region key:** `(reference id, candidate id, mode, first seed p, first seed q)`. It identifies a region within a report body for external records such as origin or review links. Together with `bodySha256`, it identifies a region globally.

**Only listed regions can be referenced.** A region cut by `maxRegionsPerMode` (§5.7) has no first seed in the body, so no external record can cite it by region key against that body, and a link to it fails any check that the key exists. To obtain such regions, a consumer re-runs the comparison with a larger `maxRegionsPerMode`. That is a different configuration with a different digest and a different body, so links then cite the new `bodySha256`.

### 5.6 Region status: minimum evidence counts distinct hashes

Let `evidence = distinctHashes − distinctCommonHashes`:
- `reportable` if `evidence ≥ minRegionDistinctHashes`;
- `below-minimum-evidence` if `1 ≤ evidence < minRegionDistinctHashes`;
- `common-only` if `evidence = 0`.

**Repeated occurrences of one hash count once** (finding 2). Periodic code such as `x++` repeated therefore never reaches `match` on one repeated hash (`go-repeated-hash-self`, `go-periodic-distinct`). A common hash reduces evidence even when other hashes in the region are not common (`rv-common-reduces-evidence`, `-2`).

### 5.7 Ambiguity and the output cap

Ambiguity is computed over **all** regions of the mode, before any cap. A reportable region is `ambiguous` when another reportable region uses any of its reference positions or any of its candidate positions. Overlapping spans without a shared position do not make a region ambiguous (`rv-span-overlap-disjoint-positions`). Non-reportable regions are never ambiguous.

The cap applies after ordering, ambiguity and counting:
- `regions` lists the first `maxRegionsPerMode` regions in §5.5 order;
- `truncatedRegions` is the number omitted;
- `regionCounts` (`reportable`, `belowMinimumEvidence`, `commonOnly`) counts every region, uncapped;
- the outcome is decided from all regions (`go-output-caps`, `go-output-caps-2`);
- a listed region keeps the `ambiguous` flag earned from a truncated partner (`go-cap-straddles-ambiguous`, `-mirror`).

**Completeness.** For a valid configuration and catalogues that pass §3.6, an implementation MUST emit a body. The work is bounded by `maxSeedsPerMode`. An implementation that cannot finish within those limits is non-conformant for that input. No conformance outcome is "failed outside the report".

### 5.8 Mode outcome

Evaluated in order:

1. `seedCount = 0`: `no-match` / `no-shared-fingerprints`.
2. `seedCount > maxSeedsPerMode`: `abstain` / `seed-limit-exceeded`.
3. At least one reportable region is not ambiguous: `match` / `match`. This holds even when other reportable regions are ambiguous (`rv-match-over-ambiguous`, `-mirror`).
4. Reportable regions exist and all are ambiguous: `abstain` / `ambiguous`. This ranks above weaker regions (`rv-ambiguous-over-below`, `-mirror`).
5. Some region is `below-minimum-evidence`: `no-match` / `below-minimum-evidence`. This ranks above `common-only` (`rv-below-over-common`, `-reversed`).
6. Otherwise: `no-match` / `common-only`.

`no-match` means insufficient matching evidence under these parameters ([core interpretation](../../spec/core.md#interpretation)). It does not mean that no reuse occurred.

### 5.9 Containment and similarity

These are computed per mode over **distinct hashes**, with common hashes included, and `sharedCommonDistinctHashes` reported beside them:
- `containment.candidateInReference` = |H_R ∩ H_C| / |H_C|;
- `containment.referenceInCandidate` = |H_R ∩ H_C| / |H_R|;
- `similarity.jaccard` = |H_R ∩ H_C| / |H_R ∪ H_C|.

Each is an integer pair of raw counts, never reduced (§3.3 rule 5). They are separate fields (M2.5): in `go-function-in-host`, reference-in-candidate containment is 14/14 while Jaccard is 14/39. They are overlap counts, not probabilities or scores.

## 6. Report (`traceweave-report-draft-2`)

Schema: [report.schema.json](matching-vectors/report.schema.json).

### 6.1 Document

A report document is `{"body": …, "provenance": …}`.
- The body is deterministic. Its canonical bytes (§3.3) and their SHA-256 (`bodySha256`) are what two runs or two implementations must reproduce (M2.4).
- The provenance block is excluded from that equality.

### 6.2 Body fields (G2: every name is fixed here)

| Field | Present | Content |
| --- | --- | --- |
| `reportVersion` | always | `traceweave-report-draft-2` |
| `resultKind` | always | `token-fingerprint-comparison` |
| `inputs` | always | `{candidateCatalogueSha256, comparisonConfigSha256, referenceCatalogueSha256, suppressionCatalogueSha256}`: SHA-256 of the exact bytes received. `suppressionCatalogueSha256` is `"none"` when no suppression catalogue was supplied |
| `status` | always | `compared` or `rejected` |
| `rejection` | rejected | `{class, code, side}` (§6.4) |
| `comparison` | compared | `{comparison, maxRegionsPerMode, maxSeedsPerMode, mergeGap, minRegionDistinctHashes, modes, parameterStatus, suppressionCatalogueSha256}`: the parsed configuration values plus `parameterStatus: "experimental"` |
| `suppression` | compared | `{"status":"none"}`, or `{"status":"supplied", "artifactCount": n, "distinctHashes": {"exact": n, "normalized": n}}`. The body thus states whether suppression could act, and over how many hashes. **`artifactCount` is the number of entries in the suppression catalogue, of every status (`ok`, `insufficient-tokens` and `error`)**, while `distinctHashes` counts the distinct fingerprint hashes of its `ok` entries only (G7, `go-suppression-artifact-count`) |
| `profile` | compared | The shared profile triple `{configSha256, id, version}` |
| `referenceArtifactCount`, `candidateArtifactCount` | compared | Catalogue sizes, including error and insufficient-tokens entries |
| `pairs` | compared | §5.3 order. Each pair has `reference` and `candidate` `{id, sha256}`, `status`, and either `outcome` (not-compared) or `modes: {exact, normalized}` |

### 6.3 Mode and region fields

**Mode:**
- `outcome {class, code}`;
- `seedCount`;
- `regionCounts {belowMinimumEvidence, commonOnly, reportable}`;
- `regions` (capped) and `truncatedRegions`;
- `containment {candidateInReference, referenceInCandidate}` and `similarity {jaccard}`, each `{denominator, numerator}`;
- `sharedCommonDistinctHashes`.

**Region:** `ambiguous`, `candidateSpan`, `distinctCommonHashes`, `distinctHashes`, `referenceSpan`, `seeds`, `status`.

### 6.4 Outcome classes and the closed code list

| Level | Class | Codes |
| --- | --- | --- |
| Report | `unsupported-input` | `unsupported-comparison-config` (side `comparison-config`); `malformed-catalogue`, `unsupported-catalogue`, `unsupported-profile` (side `reference`, `candidate` or `suppression`) |
| Report | `mismatch` | `profile-mismatch`, `config-mismatch` (side `candidate` or `suppression`); `suppression-catalogue-mismatch` (side `suppression`) |
| Pair | `unsupported-input` | `reference-extraction-error`, `candidate-extraction-error` |
| Pair | `abstain` | `insufficient-tokens` |
| Mode | `match` | `match` |
| Mode | `abstain` | `ambiguous`, `seed-limit-exceeded` |
| Mode | `no-match` | `no-shared-fingerprints`, `below-minimum-evidence`, `common-only` |

The list is closed. The schema pins every class, code and side combination.

### 6.5 Ordering

- Pairs follow §5.3.
- Regions follow §5.5, then the cap in §5.7.
- Seeds are in increasing `p`.
- `modes` in the configuration are `["exact","normalized"]`.
- Object keys are sorted by canonicalization.

### 6.6 Provenance block

| Field | Required | Content |
| --- | --- | --- |
| `bodySha256` | yes | Digest of the canonical body |
| `comparisonConfigSha256` | yes | Equal to `body.inputs.comparisonConfigSha256`. This is a convenience copy. Roadmap M2.4 checks the configuration digest in the body, where `inputs` is part of the canonical bytes |
| `implementation` | yes | `{commit, name, version}`. `commit` is 40 hex digits. `name` and `version` match `^[A-Za-z0-9._+-]{1,64}$` |
| `specCommit` | yes | 40 hex digits: the spec commit the implementation pins |
| `generatedAt` | no | `YYYY-MM-DDThh:mm:ssZ`, a claimed time only, like core's `recordedAt` |

The block has **no free-text field**. Draft-1's `note` is removed, and the `name`/`version` patterns cannot hold spaces, quotes, braces or operators, so provenance cannot carry source text (finding 5). It holds no signature and no trust or time result. [example-report.json](matching-vectors/example-report.json) shows the form with placeholder commits.

### 6.7 Privacy class of the report

**Private by default.** A body discloses:
- the digests of both catalogues and of every compared artifact, which confirm a guessed whole file;
- the artifact ids;
- the matched byte spans, which reveal structure and where matches sit;
- seed positions, and counts of shared and common hashes.

It contains no source text and no fingerprint hashes. Publishing a report is a separate disclosure decision, as for any record under core's privacy defaults.

## 7. Separation from other results

The body holds fingerprint comparison results only. `additionalProperties: false` makes each of the following a schema violation; the checker corruptions cover a rank field, an origin field, `ownership` and `signatureValid`:
- exact-subject digest verification, signature validity, signer trust, timestamp verification, rights or licence assessment ([core interpretation](../../spec/core.md#interpretation), [attestations](../../spec/attestations.md), ROADMAP TW-03);
- **index, rank or candidate-selection results**;
- **origin, dependency or licence links**.

Equal artifact digests are visible, but the body draws no conclusion from them. A signature over a report attests who produced it, not what the comparison means. A soft match MUST NOT be presented as an exact subject digest.

## 8. What the report must not claim

A report, and any rendering of one, MUST NOT state or imply any of the following:

- **Ownership, authorship, permission or infringement.** A region is a run of shared token fingerprints.
- **Ancestry or direction of copying.** `reference` and `candidate` are query roles. Boilerplate and independently written same-task code can match (`go-boilerplate-unsuppressed`, `go-independent-same-task`).
- **A calibrated false-alert rate, p-value, probability or confidence.** Any later rate must be calibrated over the complete search ([lane 07](../lanes/07-evidence-review.md)). The schema has no score field.
- **Absence of reuse** on `no-match`, or **a unique location** on `ambiguous`.
- **Scope-aware or semantic equivalence.** `go-shadowing` shows the normalized mode cannot tell a shadowed variable from a fresh one.
- **Suppression as a guarantee.** Suppression is advisory (§5.2).

A rendering of a `match` MUST show, for each reportable region, its `evidence` beside `minRegionDistinctHashes`. A region whose evidence equals the minimum MUST be described as **at the minimum**, so results at a margin of one are visible as such.

## 9. Hand checks

Each mode's expectation in the vectors carries a `derivation` label:
- `hand`: written from the inputs and this contract **before** the value was computed;
- `computed-then-reviewed`: written or corrected **after** a computed value had been seen.

A vector is `hand` only if every mode is `hand`, otherwise `mixed`. The README lists every `computed-then-reviewed` mode.

**`go-repeated-hash-self`, exact mode (hand, draft-2).** The input is `x++\n` four times, compared with itself. Exact fingerprints sit at positions 2 and 5 with one hash, `1d99e08d…` (extraction README).
- Seeds: (2,2), (2,5), (5,2), (5,5).
- Diagonal 0 holds (2,2) and (5,5), gap 3 ≤ 4: one region with 2 seeds but **1 distinct hash**, so it is below the minimum evidence.
- Diagonals +3 and −3 hold one seed each, also below the minimum.
- Ordered by first seed: `[[2,2],[5,5]]`, `[[2,5]]`, `[[5,2]]`. `seedCount` is 4, and the outcome is `below-minimum-evidence`.

Draft-1 said `match` here. The rule changed (§5.6), not the arithmetic.

**`go-repeated-hash-self`, normalized mode (computed-then-reviewed).** The seed lists were first seen in a computed result in draft-1, when my hand expectation had omitted this channel. Draft-1 §9 wrongly called them hand-derived; this revision corrects that.

**`rv-gap-boundary` (hand).**
- Reference fingerprints: (0, A), (3, X), (5, B).
- Candidate fingerprints: (0, A), (3, Y), (5, B).
- Seeds (0,0) and (5,5) share diagonal 0, with gap 5 = `mergeGap` + 1. That gives two regions of one distinct hash each, so the outcome is `below-minimum-evidence`.

## 10. Findings while building the vectors

1. **Suppression by reference-catalogue document frequency** (draft-1) let a pair's outcome depend on unrelated reference files. In draft-1 the hand expectation for `go-boilerplate-only` caught one case, and the reviewer measured that changing the threshold or dropping one reference made all three pairs match. Draft-2 binds an explicit boilerplate catalogue (§5.2). Suppression is still selection-dependent, and `go-boilerplate-suppressed` works because the boilerplate files share the idiom's contexts.
2. **Without suppression, boilerplate alone produces a normalized `match`** (`go-boilerplate-unsuppressed`). There are 2 reportable regions: the `err := x.f(y)` call shape and the err-check idiom. The vector is labelled demonstrative and `computed-then-reviewed`.
3. **Exact mode does not match the rename pairs.** Rust exact gives `below-minimum-evidence` from one shared return-type k-gram (`) - > i32 {`). With `minRegionDistinctHashes` 1 it would report a match on that k-gram alone.
4. **`go-shadowing` exact mode matches (1 of 2 regions reportable).** Normalized cannot distinguish shadowing at all.
5. **`go-independent-same-task`.** Independently written code for the same task shares two normalized k-grams, giving `below-minimum-evidence`: one fingerprint short of the minimum.
6. **My hand expectations were wrong several times**, and the computation was right each time:
   - draft-1: the normalized bounds in the duplicate and tie vectors, and the normalized outcome of `go-repeated-hash-self`;
   - draft-2: the byte count of the `go-non-ascii-shift` prefix, which I first counted as 25 bytes and 11 code points instead of 28 and 12.

   These modes are labelled `computed-then-reviewed`.

   Draft-2 adds 25 vectors, 13 of them synthetic, and changes the expectations of `go-repeated-hash-self` exact mode. Every other new or changed expectation passed on its first computation. The 12 vectors added after the confirmation pass also passed on their first computation. One vector, `go-suppression-config-mismatch`, was first built wrongly: its configuration named the wrong digest, so the digest check fired before the configuration check. The construction was fixed; the expectation was not changed.

## 11. Decisions

**Decided in draft, pending owner confirmation.** These follow the reviewer's recommendations, are encoded in the vectors, and change bytes or outcomes:

| ID | Decision | Reason |
| --- | --- | --- |
| OD-C1 | (a) No trailing newline on catalogue or body bytes | Plain RFC 8785, so off-the-shelf JCS libraries agree |
| OD-C2 | (a) Containment and similarity include common hashes, with `sharedCommonDistinctHashes` beside them. Raw counts, never reduced | Overlap is reported as observed; suppression affects evidence only |
| OD-C3 | (a) Same diagonal, gap ≤ `mergeGap`, no indels, for draft-2 | Simplest deterministic rule. Gap-tolerant chaining is a new comparison id |
| OD-C4 | (a) Parameters 2 / 4 / 100000 / 1000, frozen as experimental in the configuration digest | Hand-checkable. Tuning under TW-05 means new digests |
| OD-C5 | **(b)** An explicit boilerplate catalogue, bound by digest in the configuration and recorded in `inputs` and `suppression` | Outcome independent of unrelated reference files (finding 1) |
| OD-C6 | (a) Overlapping reportable regions are ambiguous both ways, one-to-many and many-to-one | Lane 07: enumerate, do not choose |
| OD-C7 | **(b)** Deterministic cap: `maxSeedsPerMode` gives `seed-limit-exceeded`, and `maxRegionsPerMode` truncates after ordering with uncapped counts | Bounded work and output, and no outcome outside the report (finding 7) |
| OD-C8 | (a) Opaque ids `[a-z0-9._-]`, up to 64 characters | No escaping, and paths are not forced into reports |
| OD-C9 | (a) Duplicate artifact bytes are forbidden within a catalogue | Counts stay honest |
| OD-C10 | (a) Copy the vectors into `test-vectors/` with `validate` running the checker, **after owner review** and after the vendor class is added | M2.6 requires `test-vectors/`. This lane does not touch it |
| OD-C11 | (a) Insufficient tokens is decided at pair level | Both channels share one token count |
| OD-C12 | Minimum evidence counts **distinct** non-common hashes (new, finding 2) | Periodic code cannot reach `match` on one hash |
| OD-C13 | Fractions are raw counts (new, finding 4) | Byte agreement |
| OD-C14 | Catalogue and report bodies are private by default, and provenance carries no free text (new, finding 5) | §3.7, §6.6, §6.7 |
| OD-C15 | Duplicate keys are rejected during parsing, before any member is read (new, finding 6) | Lenient parsers would otherwise choose different codes |
| OD-C16 | Empty fingerprint spans are allowed (`start ≤ end`) (new, finding 9) | k = 1 is a legal extraction configuration |

**Still open:**
- **OD-C17, parameter tuning** (TW-05). Each choice is a new configuration digest.
- **OD-C18, gap-tolerant region formation** (OD-C3 (b)/(c)) as a future comparison id. It needs its own tie rule and vectors.
- **OD-C19, the vendor/third-party control class** for M2.3. It depends on eligible-file selection (extraction OD-14, TW-01), which this contract does not define. Until it exists, the M2.6 gate claim is **not met**.
- **OD-C20, keyed fingerprints** (extraction OD-11) would change the privacy class in §3.7. A separate gate.

## 12. Requirement-to-check map

All checks are in [check_matching.py](matching-vectors/check_matching.py) unless noted.

| Requirement | Check |
| --- | --- |
| §3.1–§3.5: content, binding, canonical bytes, ordering, nothing extra | Every source-backed catalogue is rebuilt from extraction records and compared, and its digest is recomputed with the checker's own JCS writer. Synthetic catalogues must pass §3.6. Corruptions cover hash, span, order, source text, config digest and catalogue digest |
| §3.6: consumer order and rules, including duplicate keys first and the k = 1 empty span | Rule self-test, 24 cases: 23 single-defect catalogues plus one valid k = 1 catalogue, with no extraction records. Vectors `go-malformed-catalogue`, `go-duplicate-key-catalogue`, `go-unsupported-catalogue`, `go-unsupported-profile` |
| Extraction inputs | Hashes and selections are recomputed from tokens. Tokens are checked by `extraction-vectors/check_vectors.py`; the new inputs were also compared with go/scanner, proc-macro2 and rustc (README) |
| §4 | Shipped bytes and digest; 22 negatives; `go-unsupported-comparison-config` |
| §5 | Independent recomputation must equal every body. Two or more vectors are required per recognized situation: merge join at the gap and split at gap + 1; span overlap without a shared position; match over ambiguous; ambiguous over weaker; below-minimum over common-only; repeated hash in a region; mixed common region; truncation; seed limit; an ambiguous region listed while its partner is truncated. Wrong-implementation self-test: 24 variants (the reviewer's 13, 5 of my own, and the confirmation pass's 6) must each change at least one body. An invariance-group check covers adding an unrelated reference file |
| §6 | Schema interpreter and keyword audit; `bodySha256`; report rule layer for order, cap, counts, ambiguity and outcome; corruptions for outcome, class, side, rank, origin, ownership, signature, float and reduced fraction; provenance note, source text in the name, and provenance config digest |
| M1.3 | Required-field self-test: every single-field deletion in a catalogue, 3 compared bodies, 4 rejected bodies and the report document |
| M2.5 | A `large-host` vector with complete containment and partial Jaccard |
| Hand derivation | Codes, counts, seeds, ambiguity flags, excerpt bounds and byte shifts, with a `derivation` label per mode. A corruption that relabels a computed-then-reviewed mode as `hand` is rejected |

**Limits.** The checker and `build_vectors.py` share an author. The hand layer and the wrong-implementation variants reduce, but do not remove, the risk of a shared misreading. The reviewer's draft-1 clean-room program reproduced all 23 draft-1 bodies. No independent implementation of draft-2 exists yet.

## 13. Review dispositions

| Review item | Resolution |
| --- | --- |
| Finding 1 (suppression depends on unrelated files) | OD-C5 (b): an explicit boilerplate catalogue bound by digest (§4, §5.1, §5.2). The body records `inputs.suppressionCatalogueSha256` and the `suppression` block. Vectors `go-boilerplate-suppressed`, `go-suppression-digest-mismatch`, `go-suppression-missing`, `go-suppression-config-mismatch` and four synthetic suppression vectors |
| Finding 2 (evidence counted seeds) | §5.6 counts distinct hashes. `go-repeated-hash-self` now gives `below-minimum-evidence`. Second vector: `go-periodic-distinct` |
| Finding 3 (unpinned boundaries; single-vector rules) | Boundary vectors `rv-gap-boundary`, `rv-gap-boundary-offset`, `rv-gap-equal`, `rv-span-overlap-disjoint-positions`. Reference-side error and insufficient-tokens entries in `go-reference-side-failures`. Non-ASCII `go-non-ascii-shift`. Duplicate key `go-duplicate-key-catalogue`. Two or more vectors per situation, enforced by the checker. M2.2/M2.3 classes: Unicode, shadowing and independent-same-task added; vendor still open (OD-C19) |
| Finding 4 (fraction reduction) | §3.3 rule 5 and §5.9 |
| Finding 5 (privacy class, §1 overclaim, free-text provenance) | §1, §3.7, §6.6, §6.7. `note` removed, and `name`/`version` constrained |
| Finding 6 (lenient parsers) | §3.6 step 1 and §4 step 2. `go-duplicate-key-catalogue`; wrong-implementation variant N5 |
| Finding 7 (output size, failures outside the report) | §5.4, §5.7 completeness. `go-output-caps`, `go-output-caps-2` |
| Finding 8 (inaccurate own account) | §9 and §10 corrected. A per-mode `derivation` label. `go-boilerplate-unsuppressed` has a real expectation, labelled demonstrative and `computed-then-reviewed`. Suppression is advisory (§5.2), and margin-of-one is visible (§8) |
| Finding 9 (k = 1 span) | §3.6 allows `start ≤ end`; rule self-test case |
| Finding 10 / G2–G4 | §6.2 names every field. §3.1 requires one configuration per catalogue. §3.2 says `unsupported-config` yields no catalogue |
| G1 | §3.3 rule 5 |
| G5 | §5.7 and `rv-span-overlap-disjoint-positions` |
| G6 | §2 |
| M2.4 provenance config digest | Draft-2 first misstated M2.4 as checking provenance. M2.4 checks the body's `inputs.comparisonConfigSha256`. The provenance copy is kept as a convenience and must equal it (§6.6) |
| Part 3 item 1 (M2.9 index) | §1 and §7: no index or rank field. The candidate set is identified by `inputs.candidateCatalogueSha256`, and canonical id ordering makes input order irrelevant. Recording how candidates were generated (exhaustive, or a digest of the selected id set) is left to M2.9's own record; the body records only the resulting catalogue digest |
| Part 3 item 2 (M2.7 origin links) | §1, §5.5 region key and §7: origin links live in a separate record that references `bodySha256` and the region key |
| Parts 2 and 3, other items | Outside this lane's files (use-case plans, roadmap) |
| Confirmation pass G7 | §6.2 defines `artifactCount`. Vector `go-suppression-artifact-count` (ok, insufficient-tokens and error entries) |
| Confirmation (a): document frequency still applied | Invariance vectors (§5.2) and an invariance-group check in the checker |
| Confirmation (b): ambiguity among listed regions only | `go-cap-straddles-ambiguous`, `-mirror` (§5.7) |
| Confirmation (c): `none` plus a supplied catalogue | Decided as explicit `suppression-catalogue-mismatch` (§5.1); `go-suppression-unexpected` |
| Confirmation (d), (e): suppression check order | Six `go-suppression-order-*` vectors (§5.1) |
| Confirmation: region key and the cap | §5.5 |
| Confirmation: M2.4 sentence | §6.6 corrected |
