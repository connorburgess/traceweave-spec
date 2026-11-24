# Draft catalogue and comparison-report contract: token-fingerprint baseline

Status: experimental draft, normative for conformance of this draft version; decided-in-draft items confirmed by the owner's delegation on 2026-11-23.

Revision status (before promotion): **draft for review, revision draft-2 with amendments A1 (extraction record), A2 (normalized-stream exclusions), A3 (declared channel lists), A4 (registered text-plain and ts-tokens), A5 (I2 cross-check rulings), A6 (behavioural rulings), A7 (behavioural follow-ups), A8 (verified provenance stamp), A9 (fault-injection values), A10 (provenance by content), A11 (commit resolved once), A12 (private read-only export), A13 (gate closure), A14 (core-gates review), A15 (hand-written token streams), A16 (implementation rulings) and A17 (records over any body), 2026-11-24.** Roadmap item TW-03. Gates: [roadmap](../ROADMAP.md) M1.3 (catalogue and report schemas) and M2.6 (hand-derived matching vectors). This contract also fixes what I2 in the [implementation plan](../docs/implementation-repo-plan.md#milestones) must reproduce for M2.4 and M2.5. It builds on the reviewed [extraction contract](extraction.md) and changes nothing in it.

This revision resolves the [clean-room review](../research/reviews/catalogue-report-contract-review.md) Part 1 findings 1–10 and guesses G1–G6, plus the non-blocking additions of its confirmation pass (G7, invariance, cap and suppression-order vectors). Every disposition is in [§13](#13-review-dispositions). Draft-2 changes formats: catalogue `traceweave-catalogue-draft-2`, comparison `traceweave-seed-merge-draft-2`, report `traceweave-report-draft-2`. Draft-1 identifiers are no longer accepted.

**Amendment A1** (§2a, §3.8) fixes the single canonical extraction record `traceweave-extraction-record-draft-1`, which the extraction contract §9 and its Q10 leave to TW-03. It also brings `input-too-large` catalogue entries into line with Q10 (null input digest and length). **No existing catalogue or report byte changed.** All 59 earlier vectors are byte-identical, and catalogue, comparison and report identifiers stay at draft-2. The details and the one rule change are in §13, A1.

**Amendment A2** follows extraction OD-23 (normalized-stream exclusions): per-channel token counts n_C (§2, §3.6, §3.8) and an optional `tokenIndices` in the record's normalized channel (§2a), present only for profiles that declare exclusions. Go and Rust declare none, so **no Go/Rust record, catalogue or report byte changed**. Details are in §13, A2.

**Amendment A3** (§2b) replaces the hard-coded pair `exact`, `normalized` with **the profile's declared, ordered channel list** in records, catalogues, comparison modes and reports, as the [text-profile review](../research/reviews/extraction-profile-text-review.md) §4 recommends (no renaming). Go, Rust and TypeScript declare exactly `["exact","normalized"]`, so **no existing record, catalogue, report, digest or vector changed** (only the three schemas were extended). A synthetic TEST-ONLY three-channel profile pins the rule. Details are in §13, A3.

This document is normative for conformance of this draft version, as stated in its status line. "MUST" describes what this draft proposes for an implementation claiming to follow it. The draft schemas and vectors are in [matching/](../test-vectors/matching/README.md). Nothing here is a registered algorithm. No parameter is tuned or calibrated.

Every choice an implementation could otherwise make differently is fixed below. Decisions that change bytes are listed in [§11](#11-decisions) as "decided in draft, pending owner confirmation", with the reason. Questions still open are listed there too.

## 1. Pipeline and scope

```
extraction config bytes + artifact bytes  ──extract (extraction contract)──►  extraction results
extraction records (§2a) + config bytes + artifact ids ──catalogue (§3.8)──►  catalogue bytes
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
- per channel, `partialWindow` and the fingerprints (position, hash, span), and for the normalized channel of a profile that declares exclusions, `tokenIndices` (extraction §6, OD-23).

`kgramCount` is defined **per channel** as `max(0, n_C − k + 1)` (G6; extraction §6–§7). For the exact channel, n_C = `tokenCount`. For the normalized channel, n_C = `tokenCount` when the profile declares no `normalizedExclusions` (Go and Rust), and otherwise the number of kept tokens, which is the length of the record's `tokenIndices`. It is computed from these counts, not from k-gram lists, because extraction §9 makes k-gram lists optional in production. The catalogue uses no tokens, token text, k-gram lists, window selections or normalized values.

## 2a. Extraction record (`traceweave-extraction-record-draft-1`)

One extraction (configuration bytes + input bytes) produces one record. The record's canonical bytes are the **normative output of extraction** for conformance level 4: two implementations MUST emit identical record bytes for the same configuration and input bytes. Schema: [record.schema.json](../schemas/record.schema.json) (structure only). Vectors: [records.json](../test-vectors/matching/records.json).

**Envelope fields, in this order:**

| # | Key | Type | Value |
| --- | --- | --- | --- |
| 1 | `recordVersion` | string | `traceweave-extraction-record-draft-1` |
| 2 | `profile` | string or `null` | The configuration's `profile`; `null` for `unsupported-config` |
| 3 | `profileVersion` | string or `null` | The configuration's `profileVersion`; `null` for `unsupported-config` |
| 4 | `configSha256` | string | SHA-256 of the configuration bytes **as supplied** (even when they are rejected), 64 lowercase hex digits |
| 5 | `inputSha256` | string or `null` | SHA-256 of the input bytes; `null` for `unsupported-config` and `input-too-large` |
| 6 | `inputLength` | integer or `null` | Input length in bytes; `null` for `unsupported-config` and `input-too-large` |
| 7 | `result` | object | Below |

There is no `contract` key: the configuration's `contract` is bound through `configSha256`, and `recordVersion` identifies the record format. The name is `inputLength`, not `inputBytes`.

**`result`, in this order:**
- **Error** (`status` `"error"`): `{"status":"error","error":{"code":…,"offset":…}}`. `offset` is an integer, except `null` for `unsupported-config`; it is 0 for `input-too-large` (extraction §2, error offsets). `code` is from the profile's closed list (extraction §4.8/§5.9) or `unsupported-config`.
- **`ok` or `insufficient-tokens`**: `status`, `tokenCount`, `tokens`, `channels`.
  - Each token is `class`, `text`, `span`, then `inserted` (the literal `true`) **only** for Go inserted semicolons. `inserted` is never `false`.
  - `channels` holds the profile's channel list in order (§2b); for Go, Rust and TypeScript that is `exact` then `normalized`. The exact channel is `kgrams`, `windowSelections`, `partialWindow`, `fingerprints`. Every other channel (here `normalized`) is `tokenIndices` (**only** when the profile declares exclusions for that channel, extraction OD-23), then `values`, `kgrams`, `windowSelections`, `partialWindow`, `fingerprints`.
  - `values` lists the normalized values of the **kept** tokens only, in stream order. `tokenIndices` lists the ascending indices of the kept tokens in `tokens`. A profile without exclusions MUST NOT emit `tokenIndices`; for Go and Rust it is always absent and `values` has one entry per token. Normalized k-gram positions, `windowSelections` and fingerprint positions index the normalized stream; spans stay original bytes.
  - Each k-gram and fingerprint is `position`, `hash`, `span`.
  - k-gram lists, `windowSelections` and `values` are **always present** in the canonical record (empty arrays for `insufficient-tokens`). Extraction §9 calls them optional "in production output"; an implementation MAY offer other outputs, but only this record is canonical.

**Record vectors name their configuration.** A record is a function of (configuration bytes, input bytes), so every entry in `records.json` states its configuration explicitly: `configFile` (path relative to `records.json`) or `configBase64` (the exact bytes, for rejected configurations), plus `configSha256`, which must equal the digest of those bytes and the record's own `configSha256`. The configuration is never left implicit in a source vector.

These are exactly the extraction vectors' `result` objects (extraction §9 and the [vector README](../test-vectors/extraction/README.md)), so record vectors are derived from extraction vectors without new hand work.

**Canonical serialization:**
1. Objects use the key order given above, **not** sorted order. No other keys exist.
2. No insignificant whitespace. The record ends with **exactly one LF** (U+000A) and contains no other raw LF or CR.
3. Integers are plain decimal. `true`, `false` and `null` as in JSON. No floats.
4. Strings use the ECMAScript `JSON.stringify` (RFC 8785 §3.2.2.2) escaping:
   - `"` → `\"`, `\` → `\\`;
   - U+0008, U+0009, U+000A, U+000C, U+000D → `\b`, `\t`, `\n`, `\f`, `\r`;
   - every other code point below U+0020 → `\u00xx`, with **lowercase** hex;
   - **everything else is written as raw UTF-8**: non-ASCII, U+007F, U+2028/U+2029 and `/` are never escaped.
5. Token text is the input bytes at the token's span (extraction §3), so the record is valid UTF-8 even when the input is not: inputs that are not UTF-8 are errors and have no token text.

Records differ from catalogues and report bodies (sorted keys, no final LF, §3.3) because a record is a stream unit: it reproduces the layout both current implementations already emit for `result`, and its final LF makes records concatenable.

**Record streams and the CLI.** A sequence of records concatenated in input order is a valid JSON Lines stream, because each record is one line. That framing, the CLI's argument syntax, exit statuses and any `--pretty`/`--result-only` options are **not normative** (conformance: CLI names are optional interfaces). What is normative is (a) the bytes of each record and (b) the catalogue (§3), which is the persisted, committed artifact. **Unknown option values are errors** (A5; §6.8 B6): an implementation that offers options, environment settings or fault-injection hooks MUST reject an unknown value as a usage error (exit 2) rather than ignore it, so a typo can never silently disable a check. Records go to stdout only (§6.8 B7).

**Not in the record.** The configuration bytes themselves (bound by `configSha256`), the input bytes, file names, timestamps and implementation identity. A record carries the token text, so it is as private as the source (it is source text).

## 2b. Declared channel lists (amendment A3)

**Rule.** Every profile declares an ordered, non-empty list of channel names (`[a-z]+`, at most 8), its **channel list**. The first channel is always `exact` (the token's original bytes); each other channel is named by the profile and defines one value per token. The extraction configuration's `channels` MUST equal the profile's list (that is how the list is bound into `configSha256`). Everything downstream is defined over that list:

- **Record (§2a):** `channels` holds one block per listed channel, in list order. `exact` has no `values`; every other channel has `values` (and `tokenIndices` first if the profile declares exclusions for that channel, extraction OD-23).
- **Catalogue (§3):** each `ok`/`insufficient-tokens` entry holds one channel per listed channel; the keys equal `extractionConfig.channels`. The §3.6 counting rules apply per channel, with n_C = `tokenCount` unless the profile declares exclusions for that channel.
- **Comparison (§4, §5):** `modes` MUST equal the channel list of a profile the implementation supports, so it is validated before any catalogue is read; after the catalogues pass, `modes` MUST equal the compared catalogues' `extractionConfig.channels`, otherwise `mode-mismatch` (§5.1 step 8). Each mode runs on the channel of the same name (§5.3).
- **Report (§6):** `comparison.modes` echoes the list in order; each compared pair's `modes` and `suppression.distinctHashes` have exactly one key per mode.

**Declared lists:** `go-tokens`, `rust2024-tokens` and `ts-tokens`/`tsx-tokens` declare `["exact","normalized"]`. Their bytes are unchanged by A3. `text-plain` declares `["exact","folded","skeleton"]` and is registered (A4, §3.6 step 5). `text-plain`/`text-markdown` would declare `["exact","folded","skeleton"]` (§13, A3, for what the text profile must still say). The synthetic **TEST-ONLY** profile `go-tokens-three-channel-test`/`draft-1` declares `["exact","normalized","classes"]`: Go lexing, where `classes` gives every token the value `""`, so only the class sequence counts ([config-three-channel-test.json](../test-vectors/matching/config-three-channel-test.json)). It is accepted only for vectors flagged `testOnlyProfile` and is never a supported comparison profile.

**Not allowed:** a subset of a profile's channels as `modes` (e.g. `["exact"]`), or a reordered list. Both stay rejected at the configuration step, exactly as before A3 (`comparison-config-negative.json` is unchanged; five further negatives are in `comparison-config-negative-channels.json`). Comparing a subset is OD-C27.

## 3. Catalogue record (`traceweave-catalogue-draft-2`)

Schema: [catalogue.schema.json](../schemas/catalogue.schema.json) (structure only). §3.3–§3.6 are part of the contract, and [check_matching.py](../test-vectors/matching/check_matching.py) enforces them.

### 3.1 Fields

| Field | Content |
| --- | --- |
| `catalogueVersion` | `traceweave-catalogue-draft-2` |
| `profile` | `{configSha256, id, version}`: the core profile triple ([core](core.md#claims-and-records)). It equals the extraction configuration's `profile` and `profileVersion`, and the SHA-256 of its exact bytes (extraction §10) |
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

- **`input-too-large` entries** have offset 0 (extraction §2) and `sha256` `null` and `byteLength` `null`, because the input is not read past the limit (extraction Q10). This is the only place `null` appears in a catalogue. Such entries are excluded from the digest-uniqueness rule.
- **`unsupported-config` never appears in a catalogue (G4).** An extraction that fails with `unsupported-config` has no valid configuration to bind, so it yields no catalogue at all, and the schema's integer `offset` cannot hold its `null`.
- **`id`** is a caller-chosen opaque label matching `^[a-z0-9][a-z0-9._-]{0,63}$`, unique within the catalogue. Ids appear in reports, so a path-like id discloses the path.
- **`sha256`** is over the **original artifact bytes**. Two entries in one catalogue MUST NOT share a `sha256`.
- **A fingerprint** is `{hash, position, span}`: the 16-hex-digit hash, the k-gram position, and the k-gram's half-open UTF-8 byte span `[start, end)` (extraction §7).

### 3.3 Canonical serialization

The rules below apply to catalogue bytes and to report body bytes alike. Both are [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) (JCS) serializations, restricted so that every JCS implementation agrees:

1. Values are objects, arrays, strings, booleans and integers in `0 … 2⁵³ − 1`. There are no floats or negative numbers. `null` appears only where the schemas allow it: the `sha256` and `byteLength` of an `input-too-large` entry, and the `sha256` of a report artifact reference to such an entry.
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

1. **Strict JSON.** All of the following are decided at this step, **before any member (including `catalogueVersion`) is read**; any failure is `malformed-catalogue`:
   - the bytes are UTF-8;
   - **nesting depth** (A5, K4): at most **64** nested containers (objects and arrays), the top-level object counting as 1. Implementations count depth on the bytes or while parsing, never by unbounded recursion. A valid catalogue nests 8 deep, a report body 9 and a record 7, so the limit only bounds hostile input (`k4-depth-64` is within it and falls through to step 2; `k4-depth-65` is not);
   - strict JSON with no non-integer numbers (`1.0`, `1e3`) and no constants (`k3-non-integer-number`);
   - **duplicate keys** are detected during parsing, so a catalogue with `catalogueVersion` twice is `malformed-catalogue` whatever the values (finding 6);
   - **every key and string is a sequence of Unicode scalar values** (I-JSON, RFC 7493 §2.1; A5, K3): a lone surrogate escape such as `"\ud800"` is ill-formed, so `{"catalogueVersion":"\ud800"}` is `malformed-catalogue`, not `unsupported-catalogue` (`k3-lone-surrogate`);
   - the top level is an object with a string `catalogueVersion`.

   The same step-1 rules (depth 64, strict JSON, duplicate keys, scalar values) apply to comparison configurations (§4 step 2, outcome `unsupported-comparison-config`), to records (§2a; a record failing them is not canonical), and to report documents and bodies read back for validation (A6, B9: such a document is invalid, decided before schema validation).
2. `catalogueVersion` is `traceweave-catalogue-draft-2`. Otherwise: `unsupported-catalogue`.
3. The schema holds. Otherwise: `malformed-catalogue`.
4. The canonical serialization (§3.3) equals the bytes exactly. Otherwise: `malformed-catalogue`.
5. `(profile.id, profile.version)` is a **registered profile** (table below). Otherwise: `unsupported-profile`.

   | Profile / version | Contract | Zero-width tokens (A14) | Channel list (§2b) | Closed error codes (besides `unsupported-config`, which never enters a catalogue) |
   | --- | --- | --- | --- | --- |
   | `go-tokens` / `draft-1` | `traceweave-token-winnow-draft-1` | no | `exact`, `normalized` | `invalid-utf8`, `bom`, `nul`, `input-too-large`, `illegal-character`, `unterminated-comment`, `unterminated-literal`, `malformed-literal` |
   | `rust2024-tokens` / `draft-1` | `traceweave-token-winnow-draft-1` | no | `exact`, `normalized` | Go's list plus `isolated-cr`, `reserved-token`, `unbalanced-delimiter`, `non-nfc-identifier`, `malformed-identifier` |
   | `ts-tokens` / `draft-2` (A4; normalized excludes `punct` `;`, extraction OD-23) | `traceweave-token-winnow-draft-1` | no | `exact`, `normalized` | `invalid-utf8`, `bom`, `nul`, `input-too-large`, `illegal-character`, `unterminated-comment`, `unterminated-literal`, `malformed-literal`, `malformed-identifier`, `unbalanced-delimiter` ([TypeScript profile](../profiles/typescript.md)) |
   | `text-plain` / `draft-1` (A4) | `traceweave-text-winnow-draft-1` | no | `exact`, `folded`, `skeleton` | `invalid-utf8`, `nul`, `input-too-large` ([text profile](../profiles/text.md)) |
   | `py-tokens` / `draft-1` (A13; **specified, not implemented**: frozen at 58c25a9, no reference extractor yet) | `traceweave-token-winnow-draft-1` | **yes** (NEWLINE, INDENT, DEDENT) | `exact`, `normalized` (no `normalizedExclusions`) | `invalid-utf8`, `bom`, `nul`, `input-too-large`, `illegal-character`, `unterminated-literal`, `malformed-literal`, `unbalanced-delimiter`, `inconsistent-indentation`, `unmatched-dedent` ([Python profile draft](../research/drafts/extraction-profile-python.md)) |

   **Zero-width tokens** (A14, OD-C64 revised) is a declared property of the profile, not a property of a catalogue: a profile declares it when its extraction can emit a token whose span is empty. Today only `py-tokens` declares it. Go's inserted `;` is not zero-width in this sense: it starts at the end of the token before it, so at k ≥ 2 its k-gram spans are non-empty and distinct positions have distinct starts. A future profile that can emit zero-width tokens MUST declare it in its row; without the declaration the strict rules of step 6 apply.

   `tsx-tokens` and `text-markdown` are not registered: they are not frozen for stage 1. The TEST-ONLY profiles (`go-tokens-exclusion-test`, `go-tokens-three-channel-test`) are accepted only in vectors flagged as such and are never registered. Registering a profile adds lists to the set `modes` may name (§4 step 4); it changes no existing byte. **"Specified, not implemented"** (A13) means the profile is registered for everything that needs no lexer: catalogue validation, comparison and building from records (§3.8, K2) MUST accept it. Only extraction of that profile may be missing from an implementation, and the implementation documents that.
6. Semantic rules hold. Otherwise: `malformed-catalogue`.
   - **Binding.** `profile` matches `extractionConfig`, and `configSha256` is the digest of its canonical bytes. Ids are strictly ordered, and digests are unique.
   - **Extraction bounds and profile row** (A5, K1). `extractionConfig` MUST be a configuration a conforming extractor accepts: `k` ≤ 16, `window` ≤ 128, `maxInputBytes` ≤ 8,388,608 (extraction §10 step 5, §10a), `contract` equal to the profile's contract (§3.6 step 5 table) and `channels` equal to its channel list. A catalogue outside these is `malformed-catalogue` **even when its digest binding is correct**, because no conforming extractor could have produced it (`k1-extraction-bounds-k17` as reference, `k1-extraction-bounds-max-input` as candidate; `k1-extraction-bounds-at-bound` shows k 16, window 128 accepted).
   - **Error entries.** The code is in the profile's closed list. An `input-too-large` entry has `sha256` and `byteLength` `null` and offset 0 (A1; draft-2 before A1 required `byteLength > maxInputBytes`, which a Q10 record cannot supply). Every other error entry has a digest, `byteLength ≤ maxInputBytes` and offset at most `byteLength`.
   - **Other entries.** `byteLength ≤ maxInputBytes`. `status` is `ok` exactly when `tokenCount ≥ k` (the exact count decides status). Exact `kgramCount = max(0, tokenCount − k + 1)`. Normalized `kgramCount`: for a profile without exclusions it equals the exact `kgramCount`; for a profile that declares exclusions, n_N is not stored, so the rule is `0 ≤ kgramCount ≤` the exact `kgramCount`, and an `ok` entry may have an empty normalized channel (`kgramCount` 0, no fingerprints, `partialWindow` false). In each channel, `partialWindow` is true exactly when `1 ≤ kgramCount < window`, and a partial window has exactly one fingerprint.
   - **Fingerprints.** Each position is below `kgramCount`, with `0 ≤ start ≤ end ≤ byteLength` (finding 9). The span may be empty: with k = 1, a Go inserted `;` k-gram has span `[e, e)`, and `e` can equal `byteLength`. Positions strictly increase. The span rules depend on the profile's **zero-width tokens** property (step 5 table; A14, OD-C64 revised):
     - **Profile without zero-width tokens** (`go-tokens`, `rust2024-tokens`, `ts-tokens`, `text-plain`): an empty span is valid only at k = 1, and **span starts strictly increase**. Distinct positions of such a profile always start at distinct offsets, so a reused start or two identical spans at consecutive positions can only come from a broken extractor, and is `malformed-catalogue` (`go-w1-reused-span-start`, `go-w2-identical-spans`, `rust-w1-reused-span-start`, `rust-w2-identical-spans`, `go-empty-span-k5`).
     - **Profile with zero-width tokens** (`py-tokens`): **an empty span is valid at every k** (a k-gram made only of zero-width tokens has span `[n, n)`), and **span starts never decrease**: consecutive k-grams that start at zero-width tokens can share a start offset (`py-equal-starts`). A catalogue MUST store such a span unchanged, a report MUST carry any region span derived from it unchanged, and a consumer MUST NOT treat it as an error or drop it (`py-empty-span-self`, `rv-py-empty-span-region`).

     A13 relaxed the rule for every profile; the [core-gates review](../research/reviews/core-gates-m1-m2-review.md) §6 showed that this let a broken Go or Rust extractor through. A14 restores the strict rule for profiles without zero-width tokens. Neither change alters an existing byte or outcome: no earlier vector had a non-increasing start or an empty span at k > 1 outside `py-tokens`. When `kgramCount ≥ window`: consecutive positions differ by at most `window`, the first position is below `window`, the last is at least `kgramCount − window`, and the count lies between ⌈(m − w + 1)/w⌉ and m − w + 1.

   - **Span ends never decrease, for every profile** (A16, OD-C69; CG-Q3 / E7). For consecutive fingerprints, the later one's span end is at least the earlier one's. The A13 text stated it; A14's rewrite dropped the sentence, and both implementations had kept the rule. K-gram ends follow token order, so winnowing cannot produce a decreasing end, zero-width tokens included (`go-w3-decreasing-span-end`, `rust-w3-decreasing-span-end`, `rv-py-decreasing-span-end`: each `malformed-catalogue`).

Step 6 checks only that the fingerprints have the shape winnowing produces. Their *correctness* needs the sources, and is checked in the vectors by re-extraction.

### 3.7 Commitment and privacy class

The canonical bytes are the exact `C` of core's `sha256-salted-catalogue-v1` commitment.

**Privacy class: private.** The hashes are unkeyed (extraction §7), and short normalized token runs have little entropy. Anyone holding a catalogue can therefore:
- test guessed code against it;
- confirm a guessed whole file through `sha256`;
- read file structure from the spans.

Exchanging catalogues for a comparison discloses all of this to the other party. Handle a catalogue like source code ([core privacy defaults](core.md#privacy-defaults)).

### 3.8 Building a catalogue from records

Inputs: the extraction configuration bytes, and a list of `(id, record bytes)`. Output: the catalogue bytes, or a refusal. The builder:

1. Validates the configuration bytes (extraction §10) and requires **a registered profile (§3.6 step 5), whether or not the implementation extracts that profile** (A5, K2). The builder reads records only, so it needs no lexer: refusing to build `text-plain` records is non-conformant (`cat-text-plain`, `cat-k2-text-plain-registered`). TEST-ONLY profiles are refused outside flagged vectors (`build-unregistered-profile`). An empty artifact list is refused (`build-empty-artifact-list`).
2. For each record: validates it as a canonical record (§2a), and requires `configSha256` = SHA-256 of the configuration bytes and `profile`/`profileVersion` equal to the configuration's. An `unsupported-config` record is refused (it has no catalogue entry, §3.2). **Validation depth** (A5): canonical bytes (step-1 rules, key order, escaping, final LF), the record schema, the declared channel list and order, closed error codes, Q10 nulls, `tokenCount` = number of tokens, `tokenIndices` presence and range, and `values` length. The builder does **not** re-derive hashes or window selections and does not compare token text with input bytes, because it has no input: a record whose hash was changed consistently in `kgrams` and `fingerprints` is accepted (`cat-builder-hash-not-rederived`), while a wrong `tokenCount` is refused (`build-tokencount-mismatch`). Hash correctness is the extractor's conformance (level 4), checked against record vectors.
3. Maps each record to an entry:
   - `id` from the caller; `sha256` = `inputSha256`; `byteLength` = `inputLength` (both `null` only for `input-too-large`); `status` = `result.status`;
   - for errors, `error` = `result.error`;
   - otherwise `tokenCount`, and per channel `fingerprints` (each `{hash, position, span}` from the record's fingerprint), `kgramCount` = max(0, n_C − k + 1) with n_C = `tokenCount` for exact, and for normalized the length of `tokenIndices` when present, else `tokenCount`; and `partialWindow`.
4. Sorts entries by id, adds `catalogueVersion`, `extractionConfig` (the eight configuration values) and `profile`, and serializes per §3.3.

**A side given as extraction-vector sources of a profile the implementation does not extract** (A16, OD-C70; CG-Q2 / E6; today the `py-tokens` sides `extraction-py.json#…`). The runner builds each record by §2a from the vector: `configSha256` is the SHA-256 of the vector file's `configFile` bytes, `inputSha256` and `inputLength` are taken from the decoded `inputBase64`, and `result` is the vector's `result` unchanged. It then builds the catalogue by this section. The catalogue MUST equal the side's catalogue bytes. Extracting such a profile is still `unsupported-config`.

Any failure refuses the whole catalogue; the builder never drops a record silently. Tokens, token text, k-gram lists, window selections and normalized values are discarded (§3.5). Vectors: two catalogues built from records equal the corresponding `matching.json` catalogues byte for byte, and three refused builds (mixed configurations, an `unsupported-config` record, wrong configuration bytes).

## 4. Comparison configuration

Exact shipped bytes ([comparison-config.json](../test-vectors/matching/comparison-config.json), SHA-256 `39345e9c8de2b566d19943563326062a46edd38e429a4a96f169307b15147333`), one line ending in LF:

```
{"comparison":"traceweave-seed-merge-draft-2","modes":["exact","normalized"],"minRegionDistinctHashes":2,"mergeGap":4,"maxSeedsPerMode":100000,"maxRegionsPerMode":1000,"suppressionCatalogueSha256":"none"}
```

Validation, in order. Any failure is `unsupported-comparison-config`:

1. UTF-8 with exactly one line break, which is a final LF, and no CR.
2. Strict JSON. Duplicate keys are rejected during parsing, and non-integer numbers and constants are rejected.
3. A top-level object with exactly these seven keys in this order.
4. `comparison` is `traceweave-seed-merge-draft-2`, and `modes` equals the channel list of a profile the implementation supports (§2b). For every shipped vector outside the TEST-ONLY ones, that is exactly `["exact","normalized"]`.
5. `minRegionDistinctHashes`, `mergeGap`, `maxSeedsPerMode` and `maxRegionsPerMode` are integers in 1 … 2³² − 1, written in decimal with no sign, leading zero or exponent; in addition **`maxSeedsPerMode` ≤ 10,000,000 and `maxRegionsPerMode` ≤ 100,000** (A5, decided in draft, pending owner confirmation; OD-C33). Vectors: `bounds-seeds-above`, `bounds-regions-above` (rejected), `bounds-at-limits` (accepted), and [comparison-config-bounds.json](../test-vectors/matching/comparison-config-bounds.json) (4 negatives at bound + 1 and 2³² − 1, 4 positives at the bounds and one below).
6. `suppressionCatalogueSha256` is `"none"` or 64 lowercase hexadecimal digits.
7. Re-serialization reproduces the bytes.

[comparison-config-negative.json](../test-vectors/matching/comparison-config-negative.json) lists 22 configurations that MUST be rejected.

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

8. `modes` differs from the reference catalogue's `extractionConfig.channels` (both catalogues share it after step 7): `mode-mismatch`, class `mismatch`, side `comparison-config` (A3; `tc-mode-mismatch-three-on-two`, `tc-mode-mismatch-two-on-three`).

No fallback, re-extraction or cross-configuration comparison is attempted.

### 5.2 Common hashes (suppression)

For mode `exact` or `normalized`, a hash is **common** if and only if it occurs among the fingerprints, in that channel, of any `ok` artifact of the supplied suppression catalogue. Several occurrences make no difference. With no suppression catalogue, no hash is common.

Commonness does not depend on the reference or candidate catalogues. Adding or removing unrelated reference files cannot change any pair's outcome (finding 1). Vectors `go-invariance-three-references` and `go-invariance-plus-unrelated` have three ok reference files that share the copied loop, and the checker requires every pair common to both vectors to have an identical result. An implementation that still applied draft-1 document-frequency suppression would mark the loop's hashes common and fail them.

Suppression is **advisory and corpus-dependent**. It removes only the hashes that winnowing happened to select in the boilerplate catalogue's files, so a shared idiom whose k-grams were selected differently is not suppressed (§10). A match produced by boilerplate is expected behavior, not an error (`go-boilerplate-unsuppressed`).

**Vendored third-party code** (OD-C19, decided in draft, pending owner confirmation; A13). Vendored or dependency code needs no new catalogue field or artifact label. It is represented on two paths:
1. **Comparison: the vendor catalogue is the suppression catalogue.** The vendored files' catalogue, built like any other from the third-party sources, is bound by digest as the suppression catalogue (§4, §5.1). Its hashes are common. Vendored regions therefore stay **visible** in the report, listed with their counts and with status `common-only`, but they never count as evidence (`vendor-suppressed`). Without it they match like any copied code (`vendor-unsuppressed`). A vendor catalogue and a boilerplate catalogue can be one catalogue; this draft binds one suppression catalogue per comparison.
2. **Origin: a review packet** (§6.9) links the region to the dependency, naming the package and version, the upstream artifact digest and the digest of the archived licence text (`packet-vendored-dependency`, and `packet-vendored-common-only` for the suppressed region).

**What vendor suppression does and does not do** (A14, OD-C66, decided in draft, pending owner confirmation). Suppression acts **per hash, on every pair** of the comparison. It does not know which files are vendored; it only knows which hashes occur in the suppression catalogue. Two effects follow, and a reader of a suppressed comparison MUST take both into account:
- **Copies of vendor code in a project's own files are suppressed too.** Code copied from the vendored library into the project's own sources, under its own names, becomes `common-only` exactly like the vendored file (`vendor-copied-into-own-code`: `util.go` and `helpers.go` hold the library code; both modes `common-only`). The comparison cannot tell such reuse from vendoring.
- **Unrelated pairs that share code with the vendor files lose evidence.** A pair in which neither side is vendored, but which shares an idiom that also occurs in a vendor file, has those hashes suppressed. Its regions can become `common-only` and its outcome can change from `match` to `common-only` (`vendor-idiom-suppresses-pair`: the `go-identical` inputs, which match without suppression, are `common-only` in both modes once a vendor file with the same code is in the catalogue).

Suppression never hides a region: suppressed regions are listed with status `common-only`. **An operator sees the effect in the counts**: `suppression.distinctHashes` per mode (how many hashes the catalogue suppresses), `sharedCommonDistinctHashes` beside containment and similarity, `regionCounts.commonOnly` and each region's `distinctCommonHashes`. A pair with high containment whose `sharedCommonDistinctHashes` equals its shared count is a pair the catalogue silenced. The report cannot say which suppressed hashes came from vendor files and which from boilerplate files, because one suppression catalogue is bound per comparison.

**When vendor-derived reuse is the question** (whether a project copied vendor code into its own files, or whether a pair matches beyond vendor code), run a **companion comparison** on the same reference and candidate catalogues, either with no suppression catalogue (`suppressionCatalogueSha256` `none`) or with a narrower catalogue (boilerplate only, or only the vendor files known to be present unmodified), and read both reports. The companion has its own configuration digest and body, so the two results are never confused. In the vectors, `vendor-unsuppressed` and `go-identical` are the companions without the vendor catalogue for the two effects above: the same bytes match in both modes.

The alternative, a labelled reference-artifact class inside catalogues, was not chosen. It would add a field to every catalogue entry and put an origin claim inside the comparison inputs, which M2.7 keeps out of the report path. Eligible-file selection (whether vendored files are extracted at all) stays with TW-01 (extraction OD-14).

### 5.3 Pairs

Every reference artifact is paired with every candidate artifact, ordered by (reference `id`, candidate `id`) as bytes. Rules in order:

1. Reference status `error`: the pair is `not-compared`, `reference-extraction-error`.
2. Candidate status `error`: `not-compared`, `candidate-extraction-error`.
3. Either side `insufficient-tokens`: `not-compared`, `insufficient-tokens` (abstention).
4. Otherwise `compared`, with §5.4–§5.9 run once per mode, in `modes` order, each on the channel of the same name (§2b).

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

**Complexity** (A5, decided in draft, pending owner confirmation). Per compared pair and mode, with F_r and F_c fingerprints and S = `seedCount`:
- counting seeds (§5.4) is O(F_r + F_c) and is done before any seed is enumerated, so a mode above the limit costs only the count;
- enumeration, sorting and region formation are O(S log S) time and O(S) memory, S ≤ `maxSeedsPerMode` ≤ 10⁷ — linear in seeds up to the sort;
- the body lists at most `maxRegionsPerMode` ≤ 10⁵ regions per mode, whose seeds are bounded by S.
- **A report's total work is the sum over its pairs**, so it grows with (reference artifacts × candidate artifacts × modes). The bounds limit one mode of one pair, not a whole report; callers comparing large catalogues SHOULD split them.

Measured by the I2 cross-check (go-tokens k1 w1, periodic sources): 8 M seeds per mode took 1.9 s and 1.4 GiB (Rust) and 4.2 s and 3.1 GiB (Go); 72 M seeds took 7.6 GiB and 10.8 GiB. About 54 (Rust) and 77 (Go) bytes per seed, both modes counted. The largest catalogue within the extraction bounds (8.4 M fingerprints per channel, 7.0 × 10¹³ seeds) validates and abstains in both without enumerating.

### 5.8 Mode outcome

Evaluated in order:

1. `seedCount = 0`: `no-match` / `no-shared-fingerprints`.
2. `seedCount > maxSeedsPerMode`: `abstain` / `seed-limit-exceeded`.
3. At least one reportable region is not ambiguous: `match` / `match`. This holds even when other reportable regions are ambiguous (`rv-match-over-ambiguous`, `-mirror`).
4. Reportable regions exist and all are ambiguous: `abstain` / `ambiguous`. This ranks above weaker regions (`rv-ambiguous-over-below`, `-mirror`).
5. Some region is `below-minimum-evidence`: `no-match` / `below-minimum-evidence`. This ranks above `common-only` (`rv-below-over-common`, `-reversed`).
6. Otherwise: `no-match` / `common-only`.

`no-match` means insufficient matching evidence under these parameters ([core interpretation](core.md#interpretation)). It does not mean that no reuse occurred.

### 5.9 Containment and similarity

These are computed per mode over **distinct hashes**, with common hashes included, and `sharedCommonDistinctHashes` reported beside them:
- `containment.candidateInReference` = |H_R ∩ H_C| / |H_C|;
- `containment.referenceInCandidate` = |H_R ∩ H_C| / |H_R|;
- `similarity.jaccard` = |H_R ∩ H_C| / |H_R ∪ H_C|.

Each is an integer pair of raw counts, never reduced (§3.3 rule 5). They are separate fields (M2.5): in `go-function-in-host`, reference-in-candidate containment is 14/14 while Jaccard is 14/39. They are overlap counts, not probabilities or scores.

## 6. Report (`traceweave-report-draft-2`)

Schema: [report.schema.json](../schemas/report.schema.json).

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
| `pairs` | compared | §5.3 order. Each pair has `reference` and `candidate` `{id, sha256}` (`sha256` is `null` for an `input-too-large` entry), `status`, and either `outcome` (not-compared) or `modes: {exact, normalized}` |

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
| Report | `mismatch` | `profile-mismatch`, `config-mismatch` (side `candidate` or `suppression`); `suppression-catalogue-mismatch` (side `suppression`); `mode-mismatch` (side `comparison-config`, A3) |
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

**Dirty or unknown builds** (A5, M2.4; tightened by A6, B10). `implementation.commit` MUST describe the code that produced the body. It is **fixed at build time only**, from the version-control state of the tree being built. An implementation refuses to write a report document (exit 2) when its build had uncommitted changes, including documentation-only changes, or carries no build-time commit. Unstamped builds include an archive export, stamping disabled, and an interpreted or `go run` execution. Such builds MAY still write the body alone, which carries no provenance. **A commit supplied at run time is never accepted.** A5's allowance of an explicit commit for unstamped builds is withdrawn: the I2 behavioural run showed that an unstamped binary built from modified sources cannot tell itself from a clean archive build, so that allowance let provenance name a commit that does not describe the code. *Why refuse rather than add a `dirty` flag:* a flag would make provenance name a commit that does not describe the code, so M2.4's recheck could not pass, and it would add a field to a closed schema; refusing keeps every existing provenance byte and meaning.

**What M2.4 needs:** a document's `implementation.commit` equals the commit from which a clean, stamped build produced it. The recheck builds that commit from a clean clone, re-runs the comparison, and obtains the identical body and the same commit (checklist items 13 and 43). Dirty and unstamped builds produce no document (items 44 and 45).

**Report document bytes are not normative.** Both implementations write RFC 8785 of `{"body", "provenance"}`; a consumer MUST NOT hash or compare the document bytes, only `bodySha256` and the provenance fields.

The block has **no free-text field**. Draft-1's `note` is removed, and the `name`/`version` patterns cannot hold spaces, quotes, braces or operators, so provenance cannot carry source text (finding 5). It holds no signature and no trust or time result. [example-report.json](../test-vectors/matching/example-report.json) shows the form with placeholder commits.

**Private outputs** (A5, M2.8; made precise by A6, §6.8 B1–B7). The default private location for catalogues and reports is implementation-defined. An implementation MUST refuse (exit 2) to write private output to a directory inside a version-controlled working tree (B1), whether the directory was chosen by default, by environment variable or by option. The one exception is an explicit override naming exactly that directory (B2). Writes are atomic (temporary file then rename) with owner-only permissions. The refusal covers paths the implementation opens itself; stdout is the operator's destination (B7).

### 6.7 Privacy class of the report

**Private by default.** A body discloses:
- the digests of both catalogues and of every compared artifact, which confirm a guessed whole file;
- the artifact ids;
- the matched byte spans, which reveal structure and where matches sit;
- seed positions, and counts of shared and common hashes.

It contains no source text and no fingerprint hashes. Publishing a report is a separate disclosure decision, as for any record under core's privacy defaults.

### 6.8 Behavioural rules (A6, decided in draft, pending owner confirmation)

These rules come from the I2 behavioural run (77 scenarios across both CLIs, `xcheck/REPORT-I2.md` §3 on `merge-i2`). They bind any implementation that writes private output or report documents, or offers a command line. Vectors cannot pin them. The [behavioural conformance checklist](../test-vectors/matching/behaviour-checklist.md) turns each rule into numbered commands with observable outcomes (66 items).

- **B1 Working-tree markers.** A directory is inside a version-controlled working tree if it, or any ancestor up to the filesystem root, contains an entry named:
  - `.git` (directory or file: worktrees and submodules use a file);
  - `.hg`, `.svn`, `.jj`, `.bzr`, `_darcs`;
  - `.fslckout` or `_FOSSIL_` (Fossil).

  The nearest marker is enough. The check is made on the output file's directory after resolving relative paths and symbolic links. A directory that does not exist yet is checked through its nearest existing ancestor.
- **B2 Override scope.** The override applies only when it names **exactly** the output file's directory, compared after both paths are made absolute (relative paths resolve from the current directory) and symbolic links are resolved. An ancestor (including the working-tree root), a descendant, a sibling or the output file path itself is not an override; the write is refused.
- **B3 Exit statuses.** One status per refusal class:

  | Status | Class | Examples |
  | ---: | --- | --- |
  | 0 | A result was produced | a record of any status (including `unsupported-config`); a catalogue; a report body, compared or rejected; a validation verdict "valid"; a report document from a stamped, clean build |
  | 1 | Refused input | a refused catalogue build (§3.8: bad record, empty list, unregistered profile, mixed configurations); a validated file that is invalid (any catalogue, configuration, record or report code) |
  | 2 | Usage, environment, location, I/O or provenance | unknown option or option value; invalid or relative location value (B4); output inside a working tree (B1, B2); unreadable input or failed write; a report document refused for a dirty or unstamped build (B10) |

  A5's provenance refusal therefore exits 2 in both implementations (the Rust lane used 1).
- **B4 Location values** (refined by A7). Every environment variable or option that names a location and is meant to be absolute (`TRACEWEAVE_PRIVATE_DIR`, `XDG_DATA_HOME`, `HOME`, `LOCALAPPDATA`) is a usage error (exit 2) if it is relative. This deliberately differs from the XDG Base Directory specification, which says to ignore a relative value: an ignored value silently moves private output. **A variable is validated only when the implementation consults it to resolve an output location** (the default private location, B11). A run that does not resolve a default location ignores these variables, even when they are invalid. Examples: validation, a body or record written to stdout, or a write to an explicit output path (checklist items 49 and 50; item 34 is the consulted case). If the implementation needs `HOME` to resolve the default location and it is unset, that is exit 2. Output paths given as command arguments may be relative and resolve from the current directory (B2).
- **B5 Empty means unset.** An environment variable set to the empty string is treated exactly as if it were unset.
- **B6 Unknown values.** Unknown options, option values, and values of the environment or fault-injection variables that the implementation reads are usage errors (exit 2), never ignored (A5, OD-C38). Environment variables the implementation does not read are simply not read. Rejecting unknown variables is not required, so a stray variable that resembles a commit setting (for example `TRACEWEAVE_BUILD_COMMIT` or `TRACEWEAVE_IMPL_COMMIT` at run time) changes nothing (B10, item 54). Fault injection (A9) uses **one variable, `TRACEWEAVE_TEST_FAULT`, with exactly three values**, so one harness drives both implementations. Each applies to the next private-output write (B8):
  - `before-temp-open`: the write fails before the temporary file is created. Exit 2, no temporary, and any previous output byte-identical.
  - `after-partial-write`: after part of the content is written to the temporary file, the process **terminates itself with SIGKILL** (no cleanup runs). No exit status, at most one temporary file (mode 0600), and any previous output byte-identical.
  - `rename-fails`: the final rename fails after the temporary is complete. Exit 2, the temporary is removed, and any previous output byte-identical.

  Unset or empty (B5) means no fault. **Any other value, including another implementation's former names (`before-open`, `kill-after-partial`, `rename`), is a usage error, exit 2.** Implementations MAY omit the variable in release builds; when they read it, these names and outcomes are mandatory.
- **B7 Stdout.** `-` as an output **file** path means stdout, in every option that takes an output file path. `-` given to an option that names a **directory** (an override, a private-directory option) is a usage error, exit 2 (item 53). Stdout, and any shell redirection of it, is the operator's explicit destination and is not policed. Records are written to stdout only, so their destination, including a redirection into a working tree, is the operator's responsibility.
- **B8 Atomic writes and temporaries** (refined by A7). A write creates a temporary file **in the output file's directory**, named `.` + the output file name + `.tw-tmp-` + 1–32 implementation-chosen characters from `[A-Za-z0-9]`. For example, `.c.json.tw-tmp-3f9a1c` for `c.json`. The file is created exclusively (it must not already exist), with mode 0600 from creation; it is never widened. The implementation writes and flushes it, then renames it over the output path.
  - A failure that the process survives (exit 2) removes the temporary file, leaves any previous file at the output path byte-identical, and never leaves a partial file at that path.
  - A process killed during the write (for example by a fault hook's signal) can leave **one** temporary file. That file may hold part of a catalogue, so it is as private as the catalogue: hidden name, mode 0600, inside the private directory. Nothing is ever left at the output path itself.
  - **Cleanup:** before its own rename, the next write to the same output path MUST delete every file in that directory that matches `.` + output name + `.tw-tmp-*` and is owned by the current user. It never reads them. Temporaries of other output names are left alone (items 47 and 48).
- **B9 Depth and strictness for report documents.** The §3.6 step-1 rules (nesting depth 64, strict JSON, duplicate keys, Unicode scalar values) apply to report documents and bodies read back for validation, as they do to catalogues, configurations and records. A valid body nests 9 deep.
- **B10 Build-time commit only, and only when verified** (refined by A8). See §6.6: a stamped, clean build writes documents; every other build writes bodies only; a run-time commit is never accepted. A provenance commit is **valid only if the build itself verified both of the following** before recording it:
  1. **The version-control root is the root of the tree being built.** The repository whose commit is recorded must be the implementation's own repository. Its working-tree root (for example `git rev-parse --show-toplevel`) is the documented root of the implementation's source tree, the directory holding the implementation's top-level build manifest. Every source file compiled into the binary is a tracked path of that repository at the recorded commit, and none of them is ignored.
  2. **That tree is clean, by content** (A10). The content of **every file that can affect the build** equals the committed content at the recorded commit. That set includes:
     - every compiled source file;
     - build manifests and lock files;
     - build scripts;
     - vendored code;
     - embedded data;
     - toolchain configuration files inside the tree.

     The build verifies this by **comparing content**: for example, it hashes each file and compares it with the blob of the commit (`git hash-object` against `git ls-tree -r <commit>`), or it builds from a fresh export of the commit. It never relies on index or status flags alone. No file outside that committed set may be compiled or read by the build.
  3. **The build environment cannot substitute sources** (A10). Nothing outside the committed tree may redirect, replace, overlay or patch what is compiled: no environment variable, user or system configuration file, or tool wrapper. The verifying step either neutralizes such inputs (for example `GOENV=off` with `GOFLAGS` empty; `RUSTC_WRAPPER` and `RUSTFLAGS` unset; user-level `.cargo/config.toml` ignored) or refuses to stamp when any is present.

  4. **One commit, resolved once** (A11). The build resolves the commit to a full object id **once, at its start**. It takes everything it compiles and everything it compares (point 2) from that object id, never again from a ref, the index or the working tree. Repository state that changes during the build (refs moved or `HEAD` flipped, the index rewritten, working-tree files edited) must not be able to produce a stamped binary whose code differs from the recorded commit. The build is either **immune by construction** (for example, it compiles a fresh export of that object id into a private directory) or **refuses to stamp** when it detects any change (for example, it re-resolves `HEAD` and re-compares content after compiling, and gets a different answer) (item 65).

  5. **Private, read-only export, re-verified after compiling** (A12). The verifying build step compiles **only from a private export** of the resolved object id. The export lives in a directory created for this build, owned by the building user and not writable by anyone else (mode 0700 or stricter), and its files are made **read-only** before compilation starts. After compilation, the step **re-verifies the export by content** against the commit's blobs, as in point 2. If any file differs, or a file was added or removed, it refuses to stamp. An edit to the export between verification and compilation therefore cannot produce a stamped binary (item 66).

  **Known routes that defeat flag- or status-based checks.** These are examples; the principle above governs:
  - index flags `git update-index --assume-unchanged` and `--skip-worktree`, which hide edits from `git status` (review P1, both lanes);
  - replace refs and grafts (`refs/replace/`, `info/grafts`), which change what a commit id appears to contain;
  - `info/exclude` and `.gitignore` entries that hide an untracked or ignored file which is then compiled;
  - sparse checkout, which leaves committed files absent while status reports clean;
  - toolchain overlay, patch or wrapper configuration: Go `GOENV` files with `GOFLAGS=-overlay=…` (review P2) and `go.work`; Cargo `[patch]` or `paths` overrides in user-level or parent `.cargo/config.toml`, `RUSTC_WRAPPER`, and `build.rustflags`.

  **Out of scope.** A deliberately forged local build defeats any check that runs inside that build: hand-injected linker flags (`-ldflags -X` typed by the person building), a modified compiler or toolchain, an edited build script, or a patched binary. Also out of scope is **anything able to write the private build directory without the operating system recording it** (for example a privileged user, or a process running as the building user that edits the export and restores it before re-verification), alongside a modified toolchain. Provenance is **evidence about cooperative builds**, made so that an honest operator cannot produce a document whose commit does not describe the code by mistake or through ordinary tool state. It is **not a security boundary**. Binding a report to verified code against an adversarial builder needs signed build attestation, which is milestone M4.

  **A toolchain-provided stamp that cannot prove (1) and (2) is treated as unstamped.** An example is Go's `vcs.revision` and `vcs.modified` build information, which records neither the repository root nor whether the compiled files belong to that repository. An implementation whose toolchain cannot verify the root MUST inject the commit through a **documented build step that performs both checks** (for example a build script that runs them and then passes the commit with `-ldflags -X`, or a `build.rs` that runs them). Every other build, including the toolchain's plain build command, writes bodies only. This closes the Go lane's D5 case: an archive export unpacked into an **ignored** folder of another repository gets that repository's HEAD as a clean toolchain stamp, yet it is unstamped under this rule. An archive export unpacked anywhere is unstamped, ignored or not, because it is not the root of a repository (items 55, 59 and 60).
- **B11 Default private location per platform.** So that both implementations agree, the default private directory (used when no explicit output path and no `TRACEWEAVE_PRIVATE_DIR` are given) is:
  - **macOS:** `$HOME/Library/Application Support/traceweave/private`. `XDG_DATA_HOME` is **not consulted** on macOS.
  - **Linux and other Unix systems except macOS:** `$XDG_DATA_HOME/traceweave/private`, with `XDG_DATA_HOME` defaulting to `$HOME/.local/share` when unset or empty.
  - **Windows:** `%LOCALAPPDATA%\traceweave\private`. `XDG_DATA_HOME` is not consulted.

  `TRACEWEAVE_PRIVATE_DIR`, when set and non-empty, replaces the platform default on every platform. File names inside the private directory remain implementation-defined (items 36, 37 and 56).
- **B12 Error messages.** Messages (stderr, stdout, logs) MUST NOT echo strings taken from input content. That covers source or token text, record, catalogue, configuration or report values, and **key names**, including unknown keys. Messages may contain:
  - paths and artifact ids that the operator supplied on the command line;
  - the closed codes of this contract;
  - JSON paths built only from field names defined by the schemas;
  - byte offsets, depths and counts.

  An unknown field is reported as "unknown field" with its position or depth, not its name (items 57 and 58). The review of `merge-i2` found the Go lane echoing an unknown key name (F3).
- **B13 A symbolic link at the output file name.** The final rename replaces the link **itself**. The implementation never writes through it, so the link's former target is left byte-identical, and the result is a regular file at the output path. The working-tree check (B1, B2) applies to the output file's directory after resolving links. A link at the file name does not change which directory is checked (items 51 and 52).

### 6.9 Review packets: origin and dependency links (A13, roadmap M2.7)

UC-2 origin and dependency links live in a **separate record**, the review packet ([schemas/review-packet.schema.json](../schemas/review-packet.schema.json), `traceweave-review-packet-draft-2`; A14 replaced draft-1). It is never part of a report body, which has no origin field (§7; fixture `origin-inside-report`). A packet holds:
- `report.bodySha256`: the body it annotates;
- `region`: the region key of §5.5, `{referenceId, candidateId, mode, firstSeed}`. It MUST name a **listed** region of that body: a compared pair, one of its modes, and a region whose first seed equals `firstSeed`. A region cut by the cap cannot be referenced (§5.5). A key absent from the body is invalid (`region-key-absent`, `region-mode-absent`);
- `origin`, one of three kinds. Each names a `side` (`reference` or `candidate`) of the region's pair, the side the origin claim is about:
  - `own-origin`: `artifactSha256` and the `repositoryCommit` it comes from;
  - `vendored-dependency`: `vendoredArtifactSha256`, `package {name, version}`, `upstreamArtifactSha256` and `licence {textSha256}`;
  - `historical-copy`: `copyArtifactSha256`, `sourceArtifactSha256`, `sourceCommit` and `licence {textSha256}` in force at that commit.

**Binding to the region** (A14, OD-C67, decided in draft, pending owner confirmation). Every digest is the SHA-256 of an artifact's exact input bytes, the same value as the artifact's `sha256` in the catalogue and in the body's pair (§6.2). A validator holding only the body and the packet checks:
- the region key names a listed region of the body (above);
- the named side's digest is bound: `own-origin` `artifactSha256`, `vendored-dependency` `vendoredArtifactSha256` and `historical-copy` `copyArtifactSha256` MUST each equal the body pair's `<side>.sha256`. A packet re-pointed at another region keeps its old digest and fails (`vendored-repointed-p1b`, `vendored-digest-mismatch`, `own-origin-digest-mismatch`, `own-origin-wrong-side`, `historical-copy-digest-mismatch`);
- `historical-copy` `sourceArtifactSha256` MUST equal the digest of the **other** side of the pair: the packet asserts that the other side is the source of the copy, so the source is one of the compared artifacts (`historical-source-unbound`). Copying from a source outside the comparison is recorded by comparing against that source;
- the licence text digest names an archived text (below).

`upstreamArtifactSha256` **cannot** be checked from the body and the packet: it is the digest of the file in the upstream package archive, which is not a compared artifact. It is a **claim**, checkable only by someone holding the upstream archive (its file with that digest, in the package and version named). It equals `vendoredArtifactSha256` exactly when the vendored copy is unmodified. The fixtures use the upstream file's bytes from `vendor-unsuppressed` as the claimed upstream.

**No licence identifier** (A14). Draft-1 carried `licence.identifier` beside the text digest, and nothing checked one against the other, so an identifier contradicting the archived text validated (review P3). A14 removes the field: the archived text, named by `textSha256`, is the licence. Any identifier a reviewer derives from that text belongs to the rights review that cites the packet. A packet with an `identifier` is rejected by the schema (`licence-identifier-p3`).

**Rejection codes** (A16, OD-C71; CG-Q5 / E3). A validator reports the **first** failing check in this order, with this code:
1. `malformed-packet`: the bytes fail the §3.6 step 1 rules (strict JSON, duplicate keys, BOM, trailing data, depth), or the schema;
2. `body-unknown`: no body the validator holds has `report.bodySha256`;
3. `region-key-absent`: the pair `(referenceId, candidateId)` is absent or not compared;
4. `region-mode-absent`: the pair has no mode `mode`;
5. `region-key-absent`: no listed region of that mode has first seed `firstSeed`, which covers a non-first seed;
6. `side-digest-mismatch`: the named side's bound digest differs from the pair's;
7. `historical-source-unbound`;
8. `licence-text-unarchived`.

**A packet keyed to a body with no region at its key** (A17, OD-C75). A rejected body (§5.1) lists no pairs, so every region key is absent from it. A not-compared pair, and a mode that lists no region, are absent too. Each gives `region-key-absent` and never a failure of the validator (`body-kind-go-config-mismatch`, `body-kind-go-malformed-catalogue`, `body-kind-go-insufficient-tokens`, `body-kind-go-no-overlap`).

Each invalid fixture in `review-packets.json` carries its `code`. A schema failure may also report the member path, but never the name of an unknown member (B12). **A packet need not be RFC 8785 canonical** (CG-Q6): a strict-JSON packet that is valid is accepted in any key order and whitespace, because packets are validated, not hashed.

`licence.textSha256` is the SHA-256 of an **archived licence text** that the record's holder can produce. Fixtures archive synthetic placeholder texts under `test-vectors/matching/licence-texts/`. A packet has **no rights-verdict field**: no permitted or infringing flag, no licence-compatibility conclusion, no owner, no score and no free text. A rights review reaches its conclusion elsewhere and cites the packet. A "historical permitted copy" is therefore recorded as `historical-copy` with the licence then in force; whether it was permitted is not a field. Fixtures are in [review-packets.json](../test-vectors/matching/review-packets.json):
- 4 valid packets: own origin, vendored dependency, vendored and common-only, historical copy;
- 71 rejections (A17 added 4 for bodies with no region at the key): one per required field of each origin kind; region key or mode absent; a non-first seed; unknown body; the side-digest and source-digest bindings above (P1b among them); a licence identifier; a `permitted` flag inside `package`; an uppercase digest; an unarchived licence text; and forbidden fields;
- 1 report body with an origin field, which the report schema rejects.

### 6.10 Candidate-generation record (A13, roadmap M2.9)

Index ranking is not evidence. How the candidate catalogue was produced is recorded in a **separate record keyed by the body's `bodySha256`** ([schemas/candidate-generation.schema.json](../schemas/candidate-generation.schema.json), `traceweave-candidate-generation-draft-1`). It is never part of the body. The record holds:
- `report.bodySha256`;
- `candidateCatalogueSha256`, which MUST equal the body's `inputs.candidateCatalogueSha256`;
- `generation`: either `{"method":"exhaustive"}`, or `{"method":"selected", "selectedIdsSha256", "index": {name, version}}`. `selectedIdsSha256` is the SHA-256 of the RFC 8785 array of the selected candidate ids sorted by bytes, and MUST equal that digest computed over the candidate catalogue's ids.

**Rejection codes and the candidate catalogue** (A16, OD-C72; CG-Q7 / E4). The body records the candidate catalogue's digest but not its ids, so checking `selectedIdsSha256` needs the candidate catalogue bytes. A validator reports the first failing check, in this order:
1. `malformed-record`: step-1 rules or schema;
2. `body-unknown`;
3. `candidate-catalogue-mismatch`: `candidateCatalogueSha256` differs from the body's `inputs.candidateCatalogueSha256`, or from the SHA-256 of the supplied catalogue bytes;
4. `candidate-catalogue-unavailable`: a `selected` record and no candidate catalogue supplied. It is not validated, and so not accepted;
5. `selected-ids-mismatch`.

An `exhaustive` record needs no catalogue (`exhaustive-without-candidate-catalogue` in `validWithoutCandidateCatalogue`); new fixture `selected-without-candidate-catalogue` gives `candidate-catalogue-unavailable`.

**A supplied candidate catalogue, and records over any body** (A17, OD-C76; integration finding B3). This refines A16 and keeps its order:
- **Digest only.** Supplied candidate catalogue bytes are compared with the record and the body by the SHA-256 of their bytes alone. A digest that differs is `candidate-catalogue-mismatch`, for either method, and needs no parsing.
- **Parsed only for the id set.** The bytes are parsed only when a check needs their contents, which is a `selected` record's id set. Bytes that match the digest but fail §3.6 give the new code **`candidate-catalogue-invalid`**. The full order is: `malformed-record`, `body-unknown`, `candidate-catalogue-mismatch`, `candidate-catalogue-unavailable`, `candidate-catalogue-invalid`, `selected-ids-mismatch`.
- **Malformed record first.** A malformed record is `malformed-record` whatever catalogue is supplied. The catalogue is never read first, and a catalogue code never pre-empts a record code.
- **`exhaustive`.** An `exhaustive` record is never checked against catalogue contents. Supplying an invalid catalogue whose digest matches leaves it valid.
- **Any body.** A record annotates how the candidate catalogue was produced, whatever the comparison's outcome. It is validated the same way against a compared body, a body with not-compared pairs, or a rejected body (§5.1): the body supplies only `bodySha256` and `inputs.candidateCatalogueSha256`, which every body has. A record can therefore be valid for a rejected body.
- **Writers.** A record writer validates the candidate catalogue by §3.6 before writing a record of either method. It refuses an invalid catalogue with `candidate-catalogue-invalid` and writes nothing. Over a valid catalogue it writes the record whatever the comparison's outcome.

Fixtures: `bodyKindCases`, 22 cases over the three rejected-body vectors whose candidate side is a malformed catalogue (`go-malformed-catalogue`, `go-suppression-order-candidate-validity-first`, `k1-extraction-bounds-max-input`) and over `go-config-mismatch`. They cover a malformed record, an invalid catalogue, a withheld catalogue, wrong bytes, an exhaustive record with and without the invalid catalogue, a record re-keyed to another body, and a valid `selected` record for a rejected body. `writerCases` has 7 cases: 6 refusals and 1 record written over a valid catalogue for a rejected body.

**`exhaustive` is the producer's claim** (A14). The record holds no corpus, so a validator cannot tell an exhaustive run from a subset recorded as `exhaustive` (review C2). What it can check is the binding: the candidate catalogue digest and, for `selected`, the id-set digest. Whether the catalogue held the whole corpus is attested by whoever holds the corpus.

There is no rank, score or position field, in the record or in the body. Because the candidate catalogue is canonical (artifacts sorted by id, §3.4), **the same candidate set gives a byte-identical catalogue and body whatever retrieval path or order produced it**. A different set changes the candidate catalogue digest, `candidateArtifactCount` and the pairs. Fixtures are in [candidate-generation.json](../test-vectors/matching/candidate-generation.json):
- built on `text-plain-three-modes`, three retrieval paths (exhaustive, and two toy indexes returning the four documents in other orders) each give that vector's body byte for byte;
- one index selecting two documents gives a different catalogue, count and pairs;
- 7 invalid records: rank, scores, unknown method, missing digest, wrong id-set digest, catalogue mismatch, unknown body;
- 4 report bodies with rank, score, index or candidate-generation fields, which the report schema rejects.

### 6.11 Frozen M2.2 fixture manifest (A13)

[m22-fixture-manifest.json](../test-vectors/matching/m22-fixture-manifest.json) (SHA-256 `349bd14953082dcef95e00c40d22972a708654d270819ba7ae7366444dc7fb34`, pinned in `check_gates.py`; A14 re-froze it after adding `regionsListed`, A15 after adding `derivationRule`) names, for each UC-1 example-matrix row, its cases:

| Row | Positive cases | Companion cases |
| --- | --- | --- |
| exact | `go-identical`, `rust-identical` | none |
| formatted fragment in a large host | `go-formatted-fragment-in-host`, `go-function-in-host`, `go-comments-whitespace` | none |
| rename/shadowing | `go-renamed`, `go-shadowing`, `rust-renamed` | none |
| Unicode / repeated minima / tiny file | `go-non-ascii-shift-2` | `go-periodic-distinct` (deterministic handling of repeated equal minima), `go-insufficient-tokens` (abstention on a tiny file) |

Every positive case is `derivation: hand`. Each case lists its input digests and byte lengths, its catalogue and body digests, and the expected outcome and half-open UTF-8 byte spans of its regions per mode. **Positive cases list reportable regions only** (`regionsListed: "reportable"`); companion cases list every region (`"all"`). The two `below-minimum-evidence` regions of `go-shadowing` exact and `rust-renamed` exact are therefore not listed; the body digest still covers them (A14). `check_gates.py` recomputes the bodies and requires every span to match (56/56). An implementation passes M2.2 when it reproduces every digest and span (N/N).

**Reading the manifest** (A16, OD-C73; Q-B, CG-Q8, E5). The manifest is frozen by digest, so a checker first requires that digest. Then:
- **Mode entries.** Each `expectedSpans` entry names a pair, plus either a `mode` with its `outcome` or a `pairOutcome`. `outcome` is the mode's outcome **code** (§6.4), not its class. A `pairOutcome` entry has no mode and no `regions`; it is the pair's outcome code (for example `insufficient-tokens`).
- **`regions` is required on every mode entry** (`[]` when none is listed). A mode entry without it makes the manifest malformed; it is not an empty list. A checker reports the manifest as invalid and does not crash.
- **Order.** `regions` lists the body's regions of the listed kind (`reportable` for positive cases, all for companions) **in the body's canonical region order** (§6.5). They are compared **by position**: the k-th listed region equals the k-th such region of the body. A list in another order, or with a region missing or extra, fails even if every listed region exists. Set matching is non-conformant.
- **Artifacts.** Each artifact's `inputSha256` and `byteLength` equal the SHA-256 and length of its input bytes and the catalogue entry's `sha256` and `byteLength`.

Corruptions `manifest-regions-reordered-q-b` and `manifest-regions-key-dropped` in `check_gates.py` are rejected.

### 6.12 M2.3 control classes (A16, roadmap M2.3)

M2.3 asks for each control class in the report with its candidate count and denominator. The body has no class field: a class is a set of vectors. The membership and the counts are fixed here (A16, OD-C74; Q-A, CG-Q4, E2), and [m23-control-classes.json](../test-vectors/matching/m23-control-classes.json) gives the expected numbers.
- **Classes and tags**, in this order:
  - `independent-same-task`: tag `independent-same-task`;
  - `boilerplate`: tag `boilerplate`;
  - `vendor`: tag `vendor`, listed apart from boilerplate;
  - `unrelated`: tag `no-overlap`;
  - `malformed-unsupported`: tags `malformed-catalogue`, `malformed-candidate`, `unsupported-catalogue`, `unsupported-profile` and `unsupported-comparison-config`. The `*-mismatch` codes are not in it.
- **Membership.** A class holds the matching vectors labelled **`derivation: hand`** that carry one of its tags, in id byte order. A vector labelled `mixed` is not a member, because M2.3 rests on hand vectors only (§11). `go-boilerplate-unsuppressed` is therefore excluded, and is listed under `excludedNotHand`. A vector with tags of several classes is a member of each.
- **Per vector.** For a compared or partly compared body, `pairs` is the number of pairs the body lists, compared or not. `candidates` is the number of those pairs whose outcome code is `match` in at least one mode, and `candidatesByMode` gives the same count per mode. A rejected comparison (§5.1, body `status` `rejected`) lists no pair and is recorded as `rejected` with its code.
- **Per class.** `candidateCount` is the sum of `candidates`, and `denominator` is the sum of `pairs`. `rejectedComparisons` counts the rejected comparisons, which are **never part of the denominator**.

An implementation's M2.3 report MUST give these numbers. At this revision they are:

| Class | Members | Candidates / denominator | Rejected comparisons |
| --- | --- | --- | --- |
| independent-same-task | 1 | 0/1 | 0 |
| boilerplate | 1 | 0/2 | 0 |
| vendor | 4 | 1/10 | 0 |
| unrelated | 1 | 0/1 | 0 |
| malformed-unsupported | 23 | 1/10 | 20 |

`check_gates.py` recounts every number from its own recomputed bodies. Its corruptions include counting the `mixed` vector and adding rejected comparisons to the denominator, and both are rejected. M2.2 and M2.3 rest on `hand` vectors only (§11).

The baseline's normalized channel is not scope-aware (§8). For the shadowing case it is expected to match a shadowed and a fresh binding alike; the example matrix's "a scope-aware channel must distinguish shadowed bindings" applies to a future scope-aware profile, not to this baseline.

## 7. Separation from other results

The body holds fingerprint comparison results only. `additionalProperties: false` makes each of the following a schema violation; the checker corruptions cover a rank field, an origin field, `ownership` and `signatureValid`:
- exact-subject digest verification, signature validity, signer trust, timestamp verification, rights or licence assessment ([core interpretation](core.md#interpretation), [attestations](attestations.md), ROADMAP TW-03);
- **index, rank or candidate-selection results**;
- **origin, dependency or licence links**.

Equal artifact digests are visible, but the body draws no conclusion from them. A signature over a report attests who produced it, not what the comparison means. A soft match MUST NOT be presented as an exact subject digest.

## 8. What the report must not claim

A report, and any rendering of one, MUST NOT state or imply any of the following:

- **Ownership, authorship, permission or infringement.** A region is a run of shared token fingerprints.
- **Ancestry or direction of copying.** `reference` and `candidate` are query roles. Boilerplate and independently written same-task code can match (`go-boilerplate-unsuppressed`, `go-independent-same-task`).
- **A calibrated false-alert rate, p-value, probability or confidence.** Any later rate must be calibrated over the complete search ([lane 07](../research/lanes/07-evidence-review.md)). The schema has no score field.
- **Absence of reuse** on `no-match`, or **a unique location** on `ambiguous`.
- **Scope-aware or semantic equivalence.** `go-shadowing` shows the normalized mode cannot tell a shadowed variable from a fresh one.
- **Suppression as a guarantee.** Suppression is advisory (§5.2).
- **That a `common-only` region is vendor code, or that a suppressed pair is unrelated** (A14). A vendor suppression catalogue also suppresses vendor code copied into a project's own files and idioms that unrelated pairs share with the vendor files (§5.2; `vendor-copied-into-own-code`, `vendor-idiom-suppresses-pair`). Where that matters, the rendering points to a companion comparison without the vendor catalogue or with a narrower one, and shows the suppression counts.

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

**Amendment A1, decided in draft, pending owner confirmation:**

| ID | Decision | Reason |
| --- | --- | --- |
| OD-C21 | One record format `traceweave-extraction-record-draft-1`: envelope `recordVersion, profile, profileVersion, configSha256, inputSha256, inputLength, result`; no `contract` key; `inputLength` | Both implementations already agree on everything else; this is one key added (Go) or one renamed and one replaced (Rust) |
| OD-C22 | Fixed key order and a final LF for records; sorted keys and no LF for catalogues and bodies | Records are stream units and keep today's shared `result` layout; catalogues and bodies are hashed artifacts where JCS libraries help |
| OD-C23 | Record bytes and catalogue bytes are normative; record-stream framing and the CLI are not | Conformance names CLIs optional; record bytes are what level 4 compares |
| OD-C24 | k-gram lists, window selections and normalized values always present in the canonical record | One canonical form; a compact production output may exist but is not compared |
| OD-C25 | `input-too-large` catalogue entries carry `null` digest and length (A1) | Required by extraction Q10; no existing vector changes. Bumping the catalogue identifier would change all 124 catalogue digests and every body digest for a rule no previous vector exercised, so it is not bumped; the owner may decide otherwise |

**Amendment A3, decided in draft, pending owner confirmation:**

| ID | Decision | Reason |
| --- | --- | --- |
| OD-C26 | Channels are the profile's declared ordered list, `exact` first; records, catalogues, modes and reports follow it; `mode-mismatch` when `modes` ≠ the catalogues' list | Text-profile review §4 (no renaming); Go/Rust/TS bytes unchanged |
| OD-C27 | `modes` must equal a full declared list; subsets are not allowed in draft-2 | Allowing `["exact"]` would make an existing negative configuration valid and change `comparison-config-negative.json`. A subset (e.g. `["folded"]`) needs a new comparison identifier, which the owner may choose later |
| OD-C28 | The comparison identifier stays `traceweave-seed-merge-draft-2` | Every existing configuration keeps its meaning and bytes; the change only admits lists of other profiles, which no draft-2 configuration could name before |

**Amendment A5 (I2 cross-check rulings), decided in draft, pending owner confirmation:**

| ID | Question | Ruling | Vectors |
| --- | --- | --- | --- |
| OD-C29 (K1) | `extractionConfig` outside extraction bounds | `malformed-catalogue` at §3.6 step 6, even with a correct digest (Rust reading) | `k1-extraction-bounds-k17`, `-max-input`, `-at-bound`; rule self-test window 129, k 2³²−1, wrong contract |
| OD-C30 (K2) | Which profiles a record builder accepts | Every registered profile (Go reading) | `cat-text-plain`, `cat-k2-text-plain-registered`, `build-unregistered-profile` |
| OD-C31 (K3) | Lone surrogate / ill-formed strings | `malformed-catalogue` at step 1, before the version (Rust reading) | `k3-lone-surrogate`, `k3-non-integer-number` |
| OD-C32 (K4) | Nesting depth | At most 64 containers; deeper is `malformed-catalogue` at step 1 (both lanes adjust) | `k4-depth-64`, `k4-depth-65` |
| OD-C33 | Comparison bounds | `maxSeedsPerMode` ≤ 10⁷, `maxRegionsPerMode` ≤ 10⁵, plus the §5.7 complexity statement | `bounds-*`, `comparison-config-bounds.json` |
| OD-C34 | Builder validation depth | Structural and canonical, no hash re-derivation (§3.8 step 2) | `cat-builder-hash-not-rederived`, `build-tokencount-mismatch`, `build-empty-artifact-list` |
| OD-C35 | Provenance for dirty or unknown builds | Refuse the report document; body-only output allowed. The explicit-commit allowance was withdrawn by A6 (B10): the commit is fixed at build time only (§6.6) | checklist items 43–45 |
| OD-C36 | Report document bytes | Not normative (§6.6) | none |
| OD-C37 | Private output inside a checkout | Refused unless explicitly overridden; location otherwise implementation-defined (§6.6) | behavioral, no vector |
| OD-C38 | Unknown option or fault-injection values | Usage error (§2a) | behavioral, no vector |

**Amendment A6 (behavioural rulings), decided in draft, pending owner confirmation:** OD-C39 the working-tree marker list (B1); OD-C40 exact-directory override (B2); OD-C41 the exit-status table (B3); OD-C42 relative location values are errors wherever consulted, deviating from XDG (B4); OD-C43 empty means unset (B5); OD-C44 a shared fault variable name, SHOULD (B6); OD-C45 `-` is stdout and stdout is not policed (B7); OD-C46 step-1 rules for report documents (B9); OD-C47 build-time commit only, withdrawing A5's run-time allowance (B10). All follow the I2 report's recommendations; none was found wrong.

**Amendment A7 (behavioural follow-ups), decided in draft, pending owner confirmation:** OD-C48 temporary-file name pattern, mode 0600 and cleanup on the next write (B8); OD-C49 location variables validated only when consulted to resolve a default location (B4); OD-C50 a symbolic link at the output name is replaced, never written through (B13); OD-C51 `-` for a directory option is a usage error (B7); OD-C52 unread variables are simply not read (B6); OD-C53 an archive export unpacked inside another repository is unstamped (B10); OD-C54 the per-platform default private location, with XDG consulted only on non-macOS Unix (B11); OD-C55 messages never echo input content or key names (B12).

**Amendment A8 (verified provenance stamp), decided in draft, pending owner confirmation:** OD-C56 a provenance commit is valid only if the build verified that the version-control root is the implementation's own source root and that tree is clean; toolchain stamps that cannot prove this are unstamped, and such implementations inject the commit through a documented verifying build step (B10).

**Amendment A9 (fault-injection values), decided in draft, pending owner confirmation:** OD-C57 `TRACEWEAVE_TEST_FAULT` takes exactly `before-temp-open`, `after-partial-write` (SIGKILL after a partial write) or `rename-fails`; any other value is a usage error (B6). The Rust lane's names were adopted because they say where the fault occurs, and `after-partial-write` names the point rather than the mechanism.

**Amendment A10 (provenance by content), decided in draft, pending owner confirmation:** OD-C58 "clean" means that every file that can affect the build equals the committed content, verified by content comparison and never by index or status flags alone, and that the build environment cannot substitute sources; deliberately forged builds are out of scope, and signed attestation is M4 (B10).

**Amendment A11 (commit resolved once), decided in draft, pending owner confirmation:** OD-C59 the build resolves the commit to an object id once and takes everything it compiles and compares from that id; changes to refs, index or working tree during the build either cannot affect the stamped binary or make the build refuse (B10 point 4).

**Amendment A12 (private read-only export), decided in draft, pending owner confirmation:** OD-C60 the verifying build step compiles from a private, read-only export of the resolved object id and re-verifies that export by content after compiling; writers of the private build directory that the operating system does not record are out of scope, alongside a modified toolchain (B10 point 5).

**Amendment A13 (gate closure: vendor class, review packets, candidate generation, M2.2 manifest, py-tokens), decided in draft, pending owner confirmation:** OD-C19 vendored code is a vendor catalogue bound as the suppression catalogue, plus a review packet for its origin, not a catalogue field (§5.2); OD-C61 the review-packet record (§6.9); OD-C62 the candidate-generation record (§6.10); OD-C63 the frozen M2.2 manifest (§6.11); OD-C64 empty spans valid at every k for zero-width-token profiles, and span starts non-decreasing (§3.6); OD-C65 `py-tokens` registered as specified, not implemented (§3.6 step 5).

**Amendment A14 (core-gates review), decided in draft, pending owner confirmation:** OD-C64 revised: zero-width tokens are a declared profile property (only `py-tokens`); empty spans at every k and non-decreasing starts apply only to such profiles, and every other profile keeps strictly increasing starts and empty spans only at k = 1 (§3.6); OD-C66 the effects of vendor suppression (per hash, every pair: own-code copies and idiom-sharing pairs are suppressed), how they show in the counts, and the companion comparison as the remedy (§5.2, §8); OD-C67 review packet draft-2: a `side` and a bound digest per origin kind, the historical source bound to the other side, `upstreamArtifactSha256` a claim, and no licence identifier (§6.9); `exhaustive` stated as the producer's claim (§6.10); the M2.2 manifest lists reportable regions only for positive cases (§6.11).

**Amendment A15 (hand-written token streams, roadmap M2.6), decided in draft, pending owner confirmation:** OD-C68: the token streams of the 22 synthetic matching inputs are hand-written literals, and the builder's mini-lexer is only a cross-check that must agree; every matching and gate fixture file carries a `derivationRule` (the ROADMAP.md definition, then how it applies); `check_matching.py` fails a `hand` vector that rests on a lexical layer not labelled `hand`. Coordinator decision applying the hand-derivation ruling ([core-gates review](../research/reviews/core-gates-m1-m2-review.md) §11). No expected output changed: all 22 hand-written streams equal the earlier ones.

**Amendment A16 (implementation rulings after the core-gates differential), decided in draft, pending owner confirmation.** It changes no existing expected value: 3 vectors and 2 fixtures are added, and invalid fixtures gain a `code`. Its decisions:
- OD-C69: span ends never decrease, for every profile (§3.6).
- OD-C70: a side of a profile that is not extracted is built from its vectors' results as records (§3.8).
- OD-C71: common review-packet rejection codes, in checking order, and packets need not be canonical (§6.9).
- OD-C72: common candidate-generation codes; a `selected` record without its candidate catalogue is `candidate-catalogue-unavailable` (§6.10).
- OD-C73: reading the M2.2 manifest. `regions` is required, regions are compared positionally in canonical order, and `outcome` is a code (§6.11).
- OD-C74: M2.3 class membership by tag among `hand` vectors; rejected comparisons are counted apart from the pair denominator (§6.12).

**Amendment A17 (records over any body), decided in draft, pending owner confirmation:** OD-C75, a review packet keyed to a rejected body, a not-compared pair or a mode without regions is `region-key-absent` (§6.9). OD-C76, candidate-generation records: supplied catalogues are compared by digest, parsed only for a `selected` id set, invalid bytes are `candidate-catalogue-invalid`, a record is validated alike against any body kind, and a writer refuses an invalid candidate catalogue (§6.10). No existing expected value changes; fixtures are added.

**Implementation-defined** (A16; recorded, no rule):
- CG-Q1 / E1: whether the TEST-ONLY `exclusion-rule.json` vectors are run. Extraction §6 expects no implementation to support that profile, and "every vector" excludes its positives. Reproducing its rejections under `go-tokens` is allowed and not required.
- CG-Q9 / E8: which example the walkthrough uses. Both lanes use `go-function-in-host`, whose expected body digest is its `bodySha256`.
- CG-Q10: the index's notion of a candidate. M2.9 requires one index and two retrieval paths. A record names the selection only, never counts or ranks (§6.10).
- E9 needs no ruling (A14 already states that `exhaustive` is a claim). E10 is not a question about the contract: the divergence clears once both lanes implement A14.

**Derivation of the matching vectors** (M2.6). Exact count: **6 vectors `mixed`, 87 `hand`** (A16 added 3 `hand` rejection vectors); the 6 `mixed` vectors hold 8 modes labelled `computed-then-reviewed`. Since A15 every input token stream of a `hand` vector is hand-written: the frozen extraction vectors, the `extraction-py.json` copies, the text lane's records, the matching lane's 22 synthetic inputs (literals in `build_vectors.py`), or catalogues written as literals. Every vector carries a `derivation` label, and every mode of every hand expectation carries its own. **Five vectors cannot be claimed as hand-derived**, and stay `mixed`, because their values were seen computed before they were written down:
- `go-duplicate-regions` and `go-tie-equal-candidate-span` (normalized);
- `go-repeated-hash-self` (normalized);
- `go-boilerplate-unsuppressed` (both modes);
- `go-non-ascii-shift` (both modes).

They are not re-labelled: a re-derivation now would still follow the computation. A13 adds one more such mode: `py-empty-span-self` normalized, whose layout-only k-grams repeat, so it is ambiguous. No M2.2 positive case or M2.3 control class rests on a `mixed` vector:
- `go-non-ascii-shift-2` is a new, hand-derived Unicode vector;
- the vendor class (`vendor-suppressed`, `vendor-unsuppressed`, and A14's `vendor-copied-into-own-code`, `vendor-idiom-suppresses-pair`) is hand-derived. Its first input repeated a normalized 5-gram and failed the hand expectation, so the input was replaced and the expectation kept, as with the draft-1 boilerplate input (README).

**Still open:**
- **OD-C17, parameter tuning** (TW-05). Each choice is a new configuration digest.
- **OD-C18, gap-tolerant region formation** (OD-C3 (b)/(c)) as a future comparison id. It needs its own tie rule and vectors.
- **OD-C20, keyed fingerprints** (extraction OD-11) would change the privacy class in §3.7. A separate gate.

## 12. Requirement-to-check map

All checks are in [check_matching.py](../test-vectors/matching/check_matching.py) unless noted.

| Requirement | Check |
| --- | --- |
| §3.1–§3.5: content, binding, canonical bytes, ordering, nothing extra | Every source-backed catalogue is rebuilt from extraction records and compared, and its digest is recomputed with the checker's own JCS writer. Synthetic catalogues must pass §3.6. Corruptions cover hash, span, order, source text, config digest and catalogue digest |
| §3.6: consumer order and rules, including duplicate keys first and the k = 1 empty span | Rule self-test, 24 cases: 23 single-defect catalogues plus one valid k = 1 catalogue, with no extraction records. Vectors `go-malformed-catalogue`, `go-duplicate-key-catalogue`, `go-unsupported-catalogue`, `go-unsupported-profile` |
| Extraction inputs | Hashes and selections are recomputed from tokens. Tokens are checked by `extraction/check_vectors.py`; the new inputs were also compared with go/scanner, proc-macro2 and rustc (README) |
| §4 | Shipped bytes and digest; 22 negatives; `go-unsupported-comparison-config` |
| §5 | Independent recomputation must equal every body. Two or more vectors are required per recognized situation: merge join at the gap and split at gap + 1; span overlap without a shared position; match over ambiguous; ambiguous over weaker; below-minimum over common-only; repeated hash in a region; mixed common region; truncation; seed limit; an ambiguous region listed while its partner is truncated. Wrong-implementation self-test: 27 variants (the reviewer's 13, 5 of my own, the confirmation pass's 6, and 3 for channel lists: modes hard-coded to exact/normalized, a mode mismatch intersected instead of rejected, modes echoed sorted) must each change at least one body. An invariance-group check covers adding an unrelated reference file |
| §6 | Schema interpreter and keyword audit; `bodySha256`; report rule layer for order, cap, counts, ambiguity and outcome; corruptions for outcome, class, side, rank, origin, ownership, signature, float and reduced fraction; provenance note, source text in the name, and provenance config digest |
| M1.3 | Required-field self-test: every single-field deletion in a catalogue, 3 compared bodies, 4 rejected bodies and the report document |
| M2.5 | A `large-host` vector with complete containment and partial Jaccard |
| §2a record bytes | `records.json`: 16 records (ok, Unicode, CR, U+000B, insufficient, empty, lexical error, encoding error, input-too-large ×2, at-limit ok, unsupported-config ×2, Rust ok with quotes and backslashes, Rust error), each derived from an extraction vector and compared with the checker's own record writer; strict parse, schema and canonical round trip. Record corruption self-test, 48 cases (A3 adds: channels out of order, `classes` missing, `classes` without values, `values` in `exact`, an extra channel on a Go record, non-empty `classes` values, re-derivation undeclared), including an unnamed configuration, a wrong configuration file and a wrong configuration digest |
| §3.8 catalogue from records | Two catalogues built from records equal the `matching.json` catalogues; a TEST-ONLY exclusion-profile catalogue equals one rebuilt from `exclusion-rule.json`; three refused builds |
| A13 gates (§3.6, §5.2, §6.9–§6.11) | `check_gates.py` (run by `tools/validate.py`): M2.2 manifest frozen by digest, 11 cases, 56/56 spans recomputed; M2.7 review packets: 4 valid (3 origin kinds), 55 rejections (one per required field per kind, absent region key or mode, unknown body, digest and licence checks, forbidden verdict fields), 1 report body with an origin field rejected; M2.9: 3 retrieval paths give one body byte for byte, a subset changes catalogue, count and pairs, 7 invalid records, 4 report bodies with rank/score/index fields rejected; 13 gate corruptions rejected. `check_matching.py`: 7 new vectors; wrong implementations "strict span starts" and "empty span rejected" are caught |
| A14 review fixes (§3.6, §5.2, §6.9–§6.11) | `check_matching.py`: zero-width tokens a profile property (`py-tokens` only); 7 new vectors (5 span rejections for Go and Rust, 2 vendor-effect vectors); wrong implementation "relaxation global" (A13's rule applied to every profile) caught by 5 vectors. `check_gates.py`: review packet draft-2, 4 valid, 67 rejections (side and source bindings, P1b, P2, P3, P4, P6); manifest re-frozen with `regionsListed`; 18 gate corruptions rejected |
| A16 rulings (§3.6, §3.8, §6.9–§6.12) | `check_matching.py`: 3 span-end rejection vectors; wrong implementation "span ends unchecked" caught by 3 vectors. `check_gates.py`: packet and candidate-generation rejection codes compared with each fixture's `code`; `regions` required and compared by position; M2.3 class members and counts recounted from recomputed bodies; 30 gate corruptions rejected, among them Q-A (the `mixed` vector counted) and Q-B (regions reordered) |
| A3 channel lists (§2b) | 8 re-derived TEST-ONLY records checked against an independent re-derivation from the Go tokens; a three-channel catalogue from records; 5 `tc-*` matching vectors (rename: exact no match, normalized and classes match; classes-only match; per-mode suppression; two `mode-mismatch`); 5 channel-list negatives (6 at A3; A4 removed the text list when `text-plain` was registered); catalogue rules (missing channel, wrong `classes` count, config list ≠ profile list, extra channel on Go); report corruptions (mode dropped, modes reordered, suppression key missing, extra mode, flag dropped) |
| A2 normalized exclusions (§2, §2a, §3.6, §3.8) | Five records from `exclusion-rule.json` (`rec-excl-*`, TEST-ONLY profile `go-tokens-exclusion-test`); the checker recomputes the normalized stream from the declared exclusions. Record corruptions: `tokenIndices` on Go, omitted, after `values`, `values` including excluded tokens, exclusions ignored, normalized positions from exact. Catalogue rules: Go normalized `kgramCount` ≠ exact (rejected), exclusion profile with an empty normalized `ok` channel (accepted), normalized above exact (rejected), test-only profile unsupported for comparison |
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
| **A13** gate closure (coordinator task; roadmap M2.2, M2.3, M2.6, M2.7, M2.9 and the py-tokens follow-up) | §3.6 (empty spans at every k for zero-width tokens; starts non-decreasing; `py-tokens` registered as specified, not implemented), §5.2 (OD-C19 vendor class), §6.9 review packets, §6.10 candidate generation, §6.11 M2.2 manifest, derivation statement. New schemas `review-packet` and `candidate-generation`; new fixtures `m22-fixture-manifest.json`, `review-packets.json`, `candidate-generation.json`, `licence-texts/`; new checker `check_gates.py` run by `tools/validate.py`; 7 new matching vectors. Every earlier expected output byte-identical |
| **A14** [core-gates review](../research/reviews/core-gates-m1-m2-review.md) (catalogue/report side) | §6 OD-C64 unsound globally: §3.6 zero-width tokens as a declared profile property, strict starts and k = 1-only empty spans for every other profile; the reviewer's W1 and W2 as `go-`/`rust-w1-reused-span-start`, `go-`/`rust-w2-identical-spans`, plus `go-empty-span-k5`. §7 vendor effects: §5.2 and §8 text (OD-C66), `vendor-copied-into-own-code`, `vendor-idiom-suppresses-pair`; the reviewer's per-class reporting suggestion is not adopted (one catalogue per comparison stays), the companion comparison is the remedy. §7 M2.3: stated as an implementation report (§6.11). §8 P1b and the source digest: bound (OD-C67); P3: identifier removed; C2: `exhaustive` stated as a claim. §9: reportable regions only, manifest re-frozen. §10 M2.6 wording: M2.2/M2.3 rest on `hand` vectors only. Extraction-side findings (§2–§4) are not in this contract. Every earlier expected output byte-identical |
| **A15** core-gates review §11 (hand-derivation ruling; coordinator decision: fix, do not relabel) | The 22 synthetic inputs' token streams written by hand as literals (`HAND_TOKENS`); `lex()` kept as a cross-check that must agree (all 22 agree); one hand-written span start (`mv-go-host-formatted`, `spanStarts: hand`). `derivationRule` added to `matching.json`, the four matching extraction files, `extraction-py.json`, `records.json` (confirmation pass), `m22-fixture-manifest.json`, `review-packets.json` and `candidate-generation.json`; manifest re-frozen. `check_matching.py` fails a `hand` vector on a non-`hand` lexical layer (derivation self-test 8/8; the rule is required in every matching file with a derivation label); `check_gates.py` requires the rule text. The 6 `mixed` vectors keep their labels. Every record, catalogue, body and expected digest byte-identical |
| **A16** core-gates differential (integration report Q-A, Q-B, D1; lane questions CG-Q1–Q10, E1–E10) | Q-A: §6.12, class membership by tag among `hand` vectors, rejected comparisons outside the denominator, `m23-control-classes.json`. Q-B and CG-Q8 / E5 / D1: §6.11, positional comparison in canonical order, `regions` required. CG-Q3 / E7: §3.6, span ends never decrease, 3 vectors. CG-Q2 / E6: §3.8. CG-Q5 / E3 and CG-Q6: §6.9 codes, `code` on every invalid packet fixture. CG-Q7 / E4: §6.10 codes plus 2 fixtures. CG-Q1 / E1, CG-Q9 / E8 and CG-Q10 are implementation-defined (§11); E9 and E10 need no ruling. No existing expected value changed |
| **A17** integration finding B3 and a missing §6.9 fixture | §6.10: digest-only comparison of supplied catalogues; new code `candidate-catalogue-invalid` after `candidate-catalogue-unavailable` and before `selected-ids-mismatch`; `exhaustive` never parses the catalogue; records valid against any body kind; writers refuse an invalid candidate catalogue. 22 `bodyKindCases` and 7 `writerCases`. §6.9: 4 packets keyed to a rejected body (two rejection classes), a not-compared pair and a mode without regions, each `region-key-absent`. No existing expected value changed |
| **A12** private read-only export (post-i2 confirmation bcd649e: an edit to the private export between verification and compilation forged a document in both lanes) | §6.8 B10 point 5 and the extended out-of-scope statement; checklist item 66 (66 in total). No vector bytes changed |
| **A11** commit resolved once (the post-i2 confirmation's Go `HEAD`-race route, f9a71a6) | §6.8 B10 point 4; checklist item 65 (65 in total). Also fixed the remaining "6 channel-list negatives" mentions in §12 and the A3 row (the file has 5 since A4). No vector bytes changed |
| **A10** provenance by content (`research/reviews/implementation-merge-i2-review.md`, "Confirmation: post-i2", fad444d: P1 index flags hide edits in both CLIs; P2 a Go `GOENV` overlay swaps sources) | §6.8 B10 points 2 and 3 rewritten with the content principle, the known routes as examples, and the out-of-scope statement. Checklist items 62 (P1), 63 (P2) and 64 (generic routes) added, 64 in total. No vector bytes changed |
| **A9** fault-injection values (the two CLIs shared `TRACEWEAVE_TEST_FAULT` but used different values) | §6.8 B6: the three values above, their outcomes, and every other value a usage error. Checklist items 42, 46 and 47 reworded; item 61 added (61 in total). No vector bytes changed |
| **A8** verified provenance stamp (Go lane D5 on `i2-go`: an export unpacked into an ignored folder of another repository received that repository's HEAD as a clean stamp and wrote a document, exit 0) | §6.8 B10 rewritten: the build must verify the repository root and cleanliness, toolchain stamps that cannot are unstamped, and a documented verifying build step is required. Checklist item 55 reworded; items 59 (ignored folder) and 60 (plain toolchain build without the verifying step) added, 60 in total. No vector bytes changed |
| **A7** behavioural follow-ups (both lanes pass all 46 items; recorded ambiguities; `research/reviews/implementation-merge-i2-review.md` F3 and its spec nit) | §6.8 B4, B6, B7, B8, B10 refined; B11–B13 added. Checklist items 36, 37, 43 and 46 reworded and items 47–58 added (58 in total). §2b now says five channel negatives (the file has 5). No vector bytes changed |
| **A6** I2 behavioural rulings (`xcheck/REPORT-I2.md` §3 and §5 on `merge-i2`; Rust lane A5-Q1–Q3, Go lane C7–C9) | §6.8 B1–B10, §6.6 (commit fixed at build time; the A5 run-time allowance withdrawn after Go lane C8 showed the gap), §3.6 step 1 (report documents), §2a. Answers: A5-Q1 and C9 (exact-directory override), B2; A5-Q2 (records to stdout), B7; A5-Q3 (report depth), B9; C7 (`configOverride`), now documented in the [vectors README](../test-vectors/matching/README.md) and enforced by the checker; C8 (run-time commit), B10. New: [behaviour-checklist.md](../test-vectors/matching/behaviour-checklist.md) (46 items); checker: 6 `configOverride` corruptions and 3 report-document step-1 cases. **No vector bytes changed** |
| **A5** I2 cross-check (`xcheck/REPORT-I2.md` on `merge-i2`; Rust `i2-rust` 9bd3bbf, Go `i2-go` c1b105c) | K1–K4 and the other reconciled questions ruled as OD-C29–C38 (§3.6 steps 1 and 6, §3.8, §4 step 5, §5.7, §2a, §6.6). New vectors: 10 matching (`k1-*` 3, `k3-*` 2, `k4-*` 2, `bounds-*` 3), 2 catalogues from records (`cat-k2-text-plain-registered`, `cat-builder-hash-not-rederived`), 3 refused builds (`build-tokencount-mismatch`, `build-unregistered-profile`, `build-empty-artifact-list`), and `comparison-config-bounds.json` (8). Checker: step-1 depth and scalar-value checks for catalogues, configurations and records; K1 bounds; builder depth; 6 wrong-implementation variants (one per reading, plus an off-by-one depth and ignored bounds), 3 wrong builders, 4 corruptions, 3 rule cases. **No existing expected output changed**: every earlier vector, record, catalogue, report and digest is byte-identical, so no version bump |
| **A4** register `text-plain` and `ts-tokens` (coordinator; text profile frozen at commit 794f1fe, TypeScript profile frozen for stage 1) | §3.6 step 5 table (contract, channel list, closed error codes); §2b. `check_matching.py` validates all 60 frozen `text-plain` records from `extraction-text/records-text-plain.json`: named configuration and digests, canonical bytes, schema, declared channel order, closed codes, Q10 nulls, input digests, and all 1,023 k-gram hashes and window selections recomputed from the recorded values (the shared hashing layer; folding and skeleton derivations remain the text checker's). New: catalogue `cat-text-plain` from text records (ok, insufficient, `nul` error), matching vector `text-plain-three-modes` on real inputs (identical and reflowed copies match in all three modes; the Cyrillic homoglyph variant matches only in `skeleton`; unrelated shares nothing), with hand expectations derived from the recorded fingerprints; it uses `minRegionDistinctHashes` 1 (the homoglyph pair shares exactly one skeleton fingerprint) and `mergeGap` 8 (the text window). **Nothing in the text records contradicts A3**: all 60 have the §2a shape and the declared channel order. One A3 file changed: the negative `modes-text-list-unimplemented` was removed from `comparison-config-negative-channels.json`, because its stated reason (no text profile registered) no longer holds. Every other existing byte is identical |
| **A3** declared channel lists (coordinator, from the text-profile review §4, commit c6e8f2a) | §2b; §2a, §4 step 4, §5.1 step 8, §5.3 rule 4, §6.4. Schemas: channel and mode objects keyed by the declared list (`exact` required, other keys by `additionalProperties`), `extractionConfig.contract` enum gains `traceweave-text-winnow-draft-1`, channel lists are arrays, new code `mode-mismatch`. New: TEST-ONLY profile `go-tokens-three-channel-test` ([config](../test-vectors/matching/config-three-channel-test.json)), 8 re-derived records, 1 catalogue from records, 5 matching vectors (`tc-*`), 5 channel-list negatives (6 at A3; A4 removed the text list when `text-plain` was registered). Unchanged (checked byte for byte against the previous files): every existing record, catalogue, report body and digest, `comparison-config.json`, `comparison-config-negative.json`, `example-report.json`, `extraction-go.json`, `extraction-rust.json`. **What the shared extraction contract must say** (not edited here): §10 step 6 becomes "`channels` equals the profile's declared channel list; `exact` is first", §6–§8 run per listed channel with the channel name in the hash input (already so in §7), and §9 lists "per listed channel". **What the text profile must say:** it declares `["exact","folded","skeleton"]`; its records use the §2a shape (token `class` `word`, `tokenCount`, no per-token `folded`/`skeleton`, which are the channels' `values`); `text-markdown`'s `masked` needs a declared place in the record (proposed: after `tokens`, before `channels`), which A3 does not yet define; the catalogue profile list and error codes (`invalid-utf8`, `nul`, `input-too-large`) are added when a text profile is implemented |
| **A2** extraction OD-23 normalized-stream exclusions (commit c81be10) | §2 per-channel n_C; §2a normalized channel order (`tokenIndices` only with exclusions, then `values`, `kgrams`, `windowSelections`, `partialWindow`, `fingerprints`), `values` for kept tokens only; §3.6 normalized `kgramCount` rule; §3.8 per-channel `kgramCount`; `record.schema.json` (optional `tokenIndices`) and `catalogue.schema.json` (empty normalized channel allowed for `ok`, enforced per profile). §2a citation fixed: the `input-too-large` offset of 0 comes from extraction §2. Unchanged: every Go/Rust record, catalogue and report byte (checked against the previous files) |
| **A1** extraction record (coordinator, from the M1.4 cross-check REPORT and extraction Q10) | §2a, §3.8, OD-C21–C25. Changed: §3.2, §3.3 rule 1 and §3.6 for `input-too-large` entries (null digest and length instead of `byteLength > maxInputBytes`); `catalogue.schema.json` gains a `tooLargeArtifact` variant; `report.schema.json` allows a `null` artifact digest. New: `record.schema.json`, `records.json`, vector `go-input-too-large`. Unchanged: every byte of the 59 earlier vectors (catalogues, bodies, digests) and every identifier. Measured against the current CLIs: both emit `result` bytes identical to all 16 record vectors; after the OD-C21 envelope change (Rust: `contract` → `recordVersion` first, `inputBytes` → `inputLength`; Go: add `recordVersion` first) both equal all 16 records byte for byte |
| Confirmation pass G7 | §6.2 defines `artifactCount`. Vector `go-suppression-artifact-count` (ok, insufficient-tokens and error entries) |
| Confirmation (a): document frequency still applied | Invariance vectors (§5.2) and an invariance-group check in the checker |
| Confirmation (b): ambiguity among listed regions only | `go-cap-straddles-ambiguous`, `-mirror` (§5.7) |
| Confirmation (c): `none` plus a supplied catalogue | Decided as explicit `suppression-catalogue-mismatch` (§5.1); `go-suppression-unexpected` |
| Confirmation (d), (e): suppression check order | Six `go-suppression-order-*` vectors (§5.1) |
| Confirmation: region key and the cap | §5.5 |
| Confirmation: M2.4 sentence | §6.6 corrected |
