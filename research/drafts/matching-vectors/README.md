# Draft matching vectors (revision draft-2)

Status: draft for review, 2026-11-22. These vectors accompany the [catalogue and report contract](../catalogue-report-contract.md) (TW-03; roadmap-v2 gates M1.3 and M2.6), revised after the [clean-room review](../../reviews/catalogue-report-contract-review.md) and its confirmation pass. They are research fixtures, not files in `test-vectors/` or `schemas/`. They make no detection-accuracy claim, and every parameter is experimental. The M2.6 gate is **not met** yet: the vendor control class is missing (contract OD-C19), and the vectors are not in `test-vectors/` (OD-C10).

## Files

| File | Contents |
| --- | --- |
| `record.schema.json` | Draft schema of the canonical extraction record (contract §2a, amendment A1) |
| `records.json` | 29 expected records (bytes and SHA-256), 7 catalogues built from records (two from the text lane's `text-plain` records, one from an inline record whose hash was altered consistently, which a builder accepts), 6 refused builds |
| `catalogue.schema.json`, `report.schema.json` | Draft JSON Schema 2020-12 (draft-2). They use only the keywords `check_matching.py` interprets |
| `comparison-config.json` | Exact comparison configuration bytes (contract §4), SHA-256 `39345e9c…147333` |
| `comparison-config-negative.json` | 22 configurations that MUST be rejected |
| `extraction-go.json`, `extraction-rust.json` | 17 new synthetic inputs (15 Go, 2 Rust) in the [extraction vector](../extraction-vectors/README.md) format, with the shipped 1 MiB configurations |
| `matching.json` | 76 matching vectors |
| `behaviour-checklist.md` | A6, A7: 58 numbered behavioural conformance items (working-tree markers, override scope, exit statuses, location values, stdout, provenance, atomic writes and temporaries, symbolic links, per-platform default location, message hygiene), each an observable command outcome, for implementations to script |
| `comparison-config-bounds.json` | A5: 4 configurations above the seed and region bounds (MUST be rejected) and 4 at or just below them (MUST be accepted) |
| `config-three-channel-test.json`, `extraction-go-classes.json` | Amendment A3: the TEST-ONLY three-channel profile's configuration, and two Go inputs with equal class sequences |
| `comparison-config-negative-channels.json` | 5 channel-list configurations that MUST be rejected (A3; the text list was removed in A4 when `text-plain` was registered) |
| `example-report.json` | One report document (body plus provenance). The commits are placeholders |
| `check_matching.py` | Independent checker, standard library only |
| `build_vectors.py` | Generator for all of the above, holding the inputs and hand expectations. The checker does not use it |

## Vector format

Each entry in `matching.json` has:
- `id`, `tags`, `description`, and `derivation`: `hand`, or `mixed` when some mode is `computed-then-reviewed`;
- `comparisonConfig`: the shipped file, or `bytesBase64`;
- `reference`, `candidate` and, optionally, `suppression`, each with `sha256` and one of three forms:
  - **source-backed**: `artifacts` (catalogue `id` plus `source`, a reference to an extraction record that holds the input bytes and tokens) and `canonical`, the catalogue object;
  - **fabricated**: `artifacts` plus `bytesBase64` and a `fabricated` note, for the nine deliberately invalid catalogues (pretty-printed, wrong version, unsupported profile, duplicate key);
  - **synthetic**: `canonical` and a `synthetic` note, with no source bytes. These are winnowing-shaped catalogues for exact boundary and precedence cases. They must pass the contract §3.6 rules;
  - **`configOverride`** (optional; A6, Go lane C7). It is allowed only on a **source-backed canonical** side (one with `artifacts` and `canonical`, not synthetic, fabricated or `fromRecords`) whose artifacts are all extraction **errors**, so no fingerprint depends on the configuration. It is an object whose keys are a non-empty subset of `k`, `window`, `maxInputBytes`, each an integer within the extraction bounds (k ≤ 16, window ≤ 128, maxInputBytes ≤ 8,388,608). The catalogue is the one built from the listed sources with those values replacing the source configuration's, re-serialized in extraction §10 canonical form, and `profile.configSha256` is recomputed. Anything else (a string value, another key, an empty object, a value out of bounds, use on another kind of side) is a vector error, and `check_matching.py` rejects it. Used by `k1-extraction-bounds-at-bound`;
- `handExpectations`;
- `expectedReport`: `body` and `bodySha256`.

**Derivation labels.** Each mode of each hand expectation carries one:
- `hand`: written from the inputs and the contract **before** the value was computed;
- `computed-then-reviewed`: written or corrected after a computed value had been seen.

The `computed-then-reviewed` modes are:

| Vector | Mode | Why |
| --- | --- | --- |
| `go-duplicate-regions`, `go-tie-equal-candidate-span` | normalized | My draft-1 excerpt bounds were wrong: the erased function name extends the region to `func` |
| `go-repeated-hash-self` | normalized | Draft-1 hand expectation omitted this channel. The seed lists were first seen computed |
| `go-boilerplate-unsuppressed` | exact, normalized | Demonstrative vector. Values first seen in the draft-1 computation |
| `go-non-ascii-shift` | exact, normalized | I counted the prefix as 25 bytes and 11 code points; it is 28 and 12. Corrected with `len()` |

Two `hand` modes are deliberately **unconstrained** (`codeIn` lists every code): `go-shadowing` exact and `go-independent-same-task` normalized. Their outcomes depend on winnowing selection, so the computed value is recorded but not hand-predicted.

The checker rejects a corrupted copy that relabels a `computed-then-reviewed` mode as `hand`.

## Coverage

| Group | Vectors |
| --- | --- |
| Positive classes | `go-identical`, `rust-identical`; `go-function-in-host`, `rust-function-in-host` (M2.5: ref-in-cand 14/14 against Jaccard 14/39); `go-partial-copy`; `go-comments-whitespace`, `rust-comments-whitespace`; `go-renamed`, `rust-renamed` (normalized only); `go-shadowing`; `go-non-ascii-shift` (spans shift by 28 bytes, not 12 code points) |
| Controls | `go-no-overlap`; `go-independent-same-task`; `go-boilerplate-suppressed` (no match with the bound boilerplate catalogue); `go-boilerplate-unsuppressed` (demonstrative normalized match without it) |
| Pair-level | `go-insufficient-tokens`; `go-malformed-candidate`; `go-reference-side-failures` (reference error, reference insufficient-tokens, candidate error; precedence across 6 pairs) |
| Report-level rejections | `go-unsupported-comparison-config`; `go-malformed-catalogue`; `go-duplicate-key-catalogue`; `go-unsupported-catalogue`; `go-unsupported-profile`; `profile-mismatch`; `go-config-mismatch`; `go-suppression-digest-mismatch`; `go-suppression-missing`; `go-suppression-config-mismatch` |
| Duplicates and ties | `go-duplicate-regions`; `go-tie-equal-candidate-span`; `go-repeated-hash-self`; `go-periodic-distinct` |
| Merge boundary (synthetic) | `rv-gap-equal` (gap 4 joins); `rv-gap-boundary`, `rv-gap-boundary-offset` (gap 5 splits) |
| Ambiguity definition (synthetic) | `rv-span-overlap-disjoint-positions` (overlapping spans, no shared position, so not ambiguous) |
| Precedence (synthetic) | `rv-match-over-ambiguous`, `-mirror`; `rv-ambiguous-over-below`, `-mirror`; `rv-below-over-common`, `-reversed` |
| Suppression arithmetic (synthetic) | `rv-common-reduces-evidence`, `-2`, `-unsuppressed` |
| Channel lists (A3, TEST-ONLY profile `go-tokens-three-channel-test`, channels `exact`, `normalized`, `classes`) | `tc-rename` (exact no match; normalized and classes match), `tc-classes-only` (only `classes` matches), `tc-format-suppressed` (suppression per mode, three `distinctHashes` keys), `tc-mode-mismatch-three-on-two`, `tc-mode-mismatch-two-on-three` |
| Real `text-plain` (A4; records from `../extraction-vectors-text/records-text-plain.json`, modes `exact`, `folded`, `skeleton`, `minRegionDistinctHashes` 1, `mergeGap` 8) | `text-plain-three-modes`: identical and reflowed copies match in all three modes; the Cyrillic homoglyph variant matches only in `skeleton` (seed (7,7)); unrelated text shares nothing. Expectations derived by hand from the recorded fingerprints |
| I2 rulings (A5) | `k1-extraction-bounds-k17`, `k1-extraction-bounds-max-input` (out-of-bound `extractionConfig` with a correct digest: `malformed-catalogue`), `k1-extraction-bounds-at-bound` (k 16, window 128 accepted); `k3-lone-surrogate`, `k3-non-integer-number` (`malformed-catalogue` at step 1); `k4-depth-64` (within the limit: `unsupported-catalogue`), `k4-depth-65` (`malformed-catalogue`); `bounds-seeds-above`, `bounds-regions-above` (rejected), `bounds-at-limits` (accepted). In `records.json`: `cat-k2-text-plain-registered`, `cat-builder-hash-not-rederived`, `build-tokencount-mismatch`, `build-unregistered-profile`, `build-empty-artifact-list` |
| Caps | `go-output-caps`, `go-output-caps-2` (region truncation with uncapped counts; seed limit at and above the limit); `go-cap-straddles-ambiguous`, `-mirror` (a listed region stays ambiguous when its partner is truncated) |
| Invariance | `go-invariance-three-references`, `go-invariance-plus-unrelated` (3 ok references sharing the copied loop; adding an unrelated reference changes no pair; checked as an invariance group) |
| Suppression definition and order | `go-suppression-artifact-count` (artifactCount counts ok, insufficient and error entries: 3); `go-suppression-unexpected` (`none` plus a supplied catalogue is rejected); `go-suppression-order-binding-before-reference`, `-binding-before-validity`, `-malformed-bound`, `-candidate-validity-first`, `-candidate-config-first`, `-profile-before-config` |

Body digests and outcomes per vector are in `matching.json`. `build_vectors.py` prints a one-line summary per vector.

## Extraction records (amendment A1)

`records.json` holds one expected canonical record per case, derived from an existing extraction vector (or, for `unsupported-config`, from a `config-negative.json` entry with input `x := 1\n`). Each entry has `source`, the input as base64, **the extraction configuration named explicitly** (`configFile`, a path relative to `records.json`, or `configBase64` with the exact bytes for the two rejected configurations, which exist in no file), `configSha256` over those configuration bytes (equal to the record's own `configSha256`), `expectedRecordText` (the record bytes decoded as UTF-8, including the final LF) and `expectedRecordSha256`.

| Record | Case |
| --- | --- |
| `rec-go-ok`, `rec-go-ok-sum`, `rec-go-limit-exact`, `rec-rust-ok` | ok (Rust: quotes and backslashes escaped) |
| `rec-go-ok-unicode`, `rec-go-ok-raw-cr`, `rec-go-ok-vt` | raw UTF-8; `\r\n`; `\u000b` lowercase |
| `rec-go-insufficient`, `rec-go-empty` | insufficient-tokens (empty k-gram arrays) |
| `rec-go-lexical-error`, `rec-rust-lexical-error`, `rec-go-encoding-error` | lexical and encoding errors |
| `rec-go-over-limit`, `rec-go-over-limit-precedence` | input-too-large: `inputSha256`/`inputLength` null; both records are byte-identical |
| `rec-unsupported-config`, `rec-unsupported-config-2` | profile, version, input fields and offset null |
| `rec-3ch-*` (8) | A3: Go token streams re-derived under the TEST-ONLY three-channel profile (`rederivedFromTokens: true`); `classes` has `values` all `""`. The checker recomputes every channel block from the tokens itself |
| `rec-excl-semi-newlines`, `-semi-explicit`, `-ok-normalized-empty`, `-insufficient`, `-partial-window` | Amendment A2: TEST-ONLY profile `go-tokens-exclusion-test` from `../extraction-vectors/exclusion-rule.json` (extraction OD-23). The normalized channel starts with `tokenIndices`, and `values` lists kept tokens only; an `ok` record can have an empty normalized channel. Go and Rust records never carry `tokenIndices` |

`cataloguesFromRecords` builds the `go-reference-side-failures` reference catalogue and the `go-input-too-large` candidate catalogue from records (contract §3.8); both equal the `matching.json` catalogues byte for byte. A third, `cat-exclusion-test` (TEST-ONLY profile), equals the catalogue the checker rebuilds from `exclusion-rule.json`, and shows a normalized `kgramCount` below the exact one, including an `ok` entry with an empty normalized channel. `catalogueBuildRejections` lists three builds the builder must refuse.

**Against the current implementations** (2026-11-22, the M1.4 cross-check worktree: Rust `target/release/traceweave`, Go `traceweave-go` built into `$TMPDIR`): for all 16 records, both CLIs' `result` bytes equal the expected ones. After the envelope change in contract OD-C21 (Rust: replace the leading `"contract":…` member with `"recordVersion":…`, rename `inputBytes` to `inputLength`; Go: insert `"recordVersion":…` first) both equal all 16 records byte for byte. Neither implementation was modified.

**Text-plain records (A4).** `check_matching.py` validates all 60 frozen records of `../extraction-vectors-text/records-text-plain.json` (owned by the text lane): named configuration and digests, canonical bytes, schema, declared channel order, closed error codes, Q10 nulls, input digests, and all 1,023 k-gram hashes and window selections recomputed from the recorded values. How the `folded` and `skeleton` values are derived is checked by the text lane's own checker, not here.

## Checking

```
python3 -I research/drafts/matching-vectors/check_matching.py
python3 -I research/drafts/extraction-vectors/check_vectors.py \
    research/drafts/matching-vectors/extraction-go.json research/drafts/matching-vectors/extraction-rust.json
python3 -I research/drafts/matching-vectors/build_vectors.py   # regenerates every file byte for byte
```

`check_matching.py` output on 2026-11-22 (Python 3.14.6), with per-item lines omitted:

```
PASS matching.json: vectors=76 catalogues-rebuilt=112 synthetic-catalogues=30 fabricated-catalogues=15 pairs=71 regions=171 reportable=96 rejected-reports=27 comparison-config-negatives=22/22 + channel-list and bound negatives 9/9 rejected, bound positives accepted; example-report.json valid
  rule situations (vectors each, minimum 2): match-over-ambiguous=2, match-over-weaker=2, ambiguous-over-weaker=2, below-over-common=3, region-repeats-hash=4, mixed-common-region=2, merge-split-at-gap-plus-one=2, merge-join-at-gap=21, span-overlap-without-shared-position=3, truncated=4, seed-limit=2, ambiguity-before-cap=2
PASS corruption self-test: rejected 68/68
PASS catalogue rule self-test (no extraction records used): 42/42 as stated
PASS required-field self-test: 706/706 single-field deletions handled (required fields rejected, optional provenance field accepted)
PASS wrong-implementation self-test: rejected 33/33
PASS records-text-plain.json (text lane, external): 60/60 records valid, 1023 k-gram hashes recomputed from recorded values
PASS records.json: records=29 (null input fields: 4) catalogues-from-records=7 (2 equal to matching.json catalogues, 1 to a rebuild from extraction vectors, 1 from re-derived records, 1 from text-plain records) build-rejections=6
PASS record corruption self-test: rejected 55/55
```

**What the checker does.** For each vector it:
1. resolves extraction records and recomputes every k-gram hash, window selection and fingerprint from the tokens;
2. rebuilds source-backed catalogues, and checks synthetic ones against the §3.6 rules;
3. recomputes catalogue digests with its own RFC 8785 writer;
4. validates catalogues and bodies with its own interpreter for the schema keyword subset, after auditing that the schemas use nothing else, plus the contract's report rules;
5. recomputes the whole comparison from the catalogue bytes alone, requiring identical bodies and `bodySha256`;
6. checks hand expectations and derivation labels.

It then **recognizes rule situations from the bodies themselves**, not from tags, and requires each in at least two vectors.

**Corruption self-test** (68 corruptions, all rejected; A6 adds six malformed `configOverride` uses (a string value, an extra `hash` key, an unknown key, k 17, an empty object, use on a synthetic side); A5 adds the K3 and K4 rejections relabelled, an at-bound override moved out of bounds, and the at-limits vector relabelled rejected; A4 adds the `text-plain` skeleton match dropped and the folded mode dropped; A3 adds: a mode dropped from a pair, modes echo reordered, a suppression `distinctHashes` key missing, an extra mode on a Go pair, a mode mismatch relabelled, the test-only flag dropped; digests are refreshed so only the targeted layer is wrong):
- spans and regions: wrong span; reordered regions or pairs; missing or extra region; missing pair; removed seed;
- outcomes: wrong outcome code or class; exact match claimed for the rename pair; ambiguity cleared, or set on span overlap; region status downgraded; insufficient-tokens pair given an outcome; pair precedence swapped; wrong rejection code or side;
- counts: distinct count inflated; common count cleared; containment numerator wrong; fraction reduced; float similarity; truncated count wrong; region beyond the cap; seed limit not applied; seed count wrong;
- forbidden fields: `ownership`, `signatureValid`, `rank` (index) and `origin`;
- suppression: block dropped; digest not recorded; artifactCount counting ok entries only;
- caps and invariance: ambiguity cleared on a listed region whose partner is truncated; an outcome changed in one invariance vector;
- digests: wrong body digest, wrong catalogue digest;
- catalogue content: fingerprint hash, fingerprint span, unsorted artifacts, source text, config digest; synthetic fingerprint moved; non-canonical catalogue accepted;
- labels and expectations: hand excerpt violated; computed-then-reviewed mode relabelled `hand`; valid config listed as negative;
- provenance: free-text `note`; source text in `implementation.name`; config digest wrong.

Two corrupted files were also written to `$TMPDIR` and passed to the CLI. Both failed with exit 1:
- an extra seed `[5,5]` in the first `rv-gap-boundary` region (`seedCount below listed seeds`);
- `inputs.suppressionCatalogueSha256` set to `none` in `go-boilerplate-suppressed` (`comparison.suppressionCatalogueSha256 differs from inputs`).

**Record checks.** The checker has its own record writer (fixed key order, ECMAScript escaping). For every record it requires strict JSON, the record schema, byte equality with its own canonical re-serialization, and byte equality with the record it derives from the source vector (whose hashes it recomputes from tokens). It rebuilds the two catalogues from record bytes alone and runs the three refused builds. **Configuration rule.** The checker requires exactly one of `configFile`/`configBase64`, requires those bytes to equal the source vector's configuration, and requires `configSha256` to equal their digest and the record's `configSha256`. **Record corruption self-test** (55 cases, all rejected): A5 adds three wrong builders (one that re-derives hashes, one that skips the `tokenCount` check, one that builds only Go and Rust); A4 adds a wrong record in the text catalogue, and three in-memory corruptions of the text lane's records (a skeleton value changed, channels reordered, an error code outside the text list); A3 channels out of declared order; `classes` missing; `classes` without values; `values` in `exact`; an extra channel on a Go record; non-empty `classes` values; re-derivation undeclared; `tokenIndices` on a Go record; `tokenIndices` omitted, or after `values`, on an exclusion record; `values` including excluded tokens; exclusions ignored; normalized positions taken from the exact channel; wrong exclusion-catalogue digest; configuration not named; wrong configuration file; wrong configuration digest; `inputBytes` field name; extra `contract` key; missing `recordVersion`; envelope or result keys reordered; JCS-sorted keys; no final LF; CRLF; insignificant whitespace; non-ASCII escaped; uppercase hex escape; raw control character; unnecessary `\u0061` escape; non-null input digest, profile or offset for unsupported-config; non-null length for input-too-large; null offset for a lexical error; k-grams, window selections or values omitted; `inserted:false`; wrong or float `tokenCount`; duplicate key; wrong input digest; changed fingerprint hash; wrong record digest; wrong catalogue-from-records digest; a refused build made valid; input-too-large coverage dropped.

**Catalogue rule self-test** (42 cases, A6 adds report documents at depth 65 (rejected at step 1) and 64 (passes step 1) and a lone surrogate in a report body; A5 adds window 129, k 2³²−1 and a text contract on a Go catalogue; no extraction records, as a consumer has). It covers:
- ordering and identity: unsorted artifacts; duplicate id or digest;
- forbidden fields: source-text and token-list fields;
- binding: config digest; profile triple;
- fingerprint rules: unordered fingerprints; span beyond the input; inverted span; position beyond the k-gram count; wrong k-gram count; wrong partial-window flag; window gap; empty first window;
- status rules: insufficient entry with a fingerprint; error code outside the profile list; `unsupported-config` as an entry; error entry with channels;
- versions: unknown catalogue version (draft-1 now); unknown profile version;
- bytes: non-canonical bytes; duplicate `catalogueVersion` (rejected before the version is read);
- **a valid k = 1 catalogue with an empty span at end of input, which must be accepted**;
- A3: a valid three-channel catalogue (accepted), an entry missing `classes`, a wrong `classes` count, a configuration list that is not the profile's, and a Go entry with an extra channel (all rejected);
- A2: a Go entry whose normalized `kgramCount` differs from the exact one (rejected); on the TEST-ONLY exclusion profile, an `ok` entry with an empty normalized channel (accepted), a normalized `kgramCount` above the exact one (rejected), and the test-only profile treated as unsupported for comparison;
- A1: `input-too-large` with a length (rejected), a lexical error with a null digest (rejected), and `input-too-large` with null digest and length (accepted).

**Required-field self-test** (M1.3, 706 deletions). Each single-field deletion must be rejected, except `provenance.generatedAt`, which must be accepted. The instances are a catalogue with ok, insufficient and error entries, 3 compared bodies, 4 rejected bodies and the report document.

**Wrong-implementation self-test** (33 variants, all rejected; A5 adds K1 bounds ignored (2 vectors), K2 builder for extracted profiles only (5), K3 lone surrogate accepted (1), K4 no depth limit (1) and off-by-one depth (1), and comparison bounds ignored (2); A3 adds L1 modes hard-coded to exact/normalized, caught by 5 vectors; L2 a mode mismatch intersected instead of rejected, caught by 2; L3 modes echoed sorted, caught by 3). Each variant re-derives every body under one misreading. It is caught when any body or body digest differs. The first 13 are the reviewer's draft-1 variants:

| # | Variant | Caught by |
| --- | --- | --- |
| R1 | merge joins gap ≤ mergeGap + 1 | `rv-gap-boundary`, `rv-gap-boundary-offset` (the reviewer found draft-1 vectors **accepted** this) |
| R2 | ambiguity by span overlap | `rv-span-overlap-disjoint-positions`, `rv-match-over-ambiguous`, `-mirror` (draft-1 **accepted** this) |
| R3 | merge uses gap < mergeGap | 14 vectors |
| R4 | evidence `d > min` | 8 vectors |
| R5 | evidence counts seeds or occurrences, not distinct hashes (draft-2 form of the reviewer's per-occurrence counting) | `go-repeated-hash-self`, `go-periodic-distinct`, `go-output-caps`, `go-output-caps-2` |
| R6 | common set not taken from the bound suppression catalogue (draft-2 form) | 5 vectors |
| R7 | regions ordered by (diagonal, p) | 12 vectors |
| R8 | fractions reduced | 31 vectors |
| R9 | below-minimum-evidence ranked above ambiguous | `rv-ambiguous-over-below`, `-mirror` |
| R10 | first occurrence only | 10 vectors |
| R11 | containment excludes common hashes | 5 vectors |
| R12 | one-to-many counted as match | `go-duplicate-regions`, `rv-match-over-ambiguous`, `rv-ambiguous-over-below` |
| R13 | trailing LF on body bytes | all 47 |

The remaining five are new:
- N1: cap applied before ambiguity and counting;
- N2: counts taken after truncation;
- N3: seed limit tested as `≥`;
- N4: suppression digest not enforced;
- N5: duplicate keys resolved last-wins (caught by one vector, `go-duplicate-key-catalogue`).

The last six are the confirmation pass's cases (a)–(f). The reviewer reported that the draft-2 vectors accepted all six:

| Case | Variant | Caught by |
| --- | --- | --- |
| (a) | draft-1 reference document frequency (threshold 3) applied on top of the boilerplate catalogue | `go-invariance-three-references`, `go-invariance-plus-unrelated` |
| (b) | ambiguity computed only among listed regions | `go-cap-straddles-ambiguous`, `-mirror` |
| (c) | `none` plus a supplied catalogue silently ignored | `go-suppression-unexpected`, `go-suppression-order-binding-before-reference` |
| (d) | binding checked after catalogue validation | `go-suppression-order-binding-before-reference`, `-binding-before-validity` |
| (e) | suppression profile/config checks before the candidate's | `go-suppression-order-candidate-config-first` (one vector) |
| (f) | `artifactCount` counts ok entries only | `go-suppression-artifact-count` (one vector) |

These are re-implementations from the review's descriptions. The reviewer's `corrupt2.py` was not re-run.

The reviewer's own scripts (`variants.py`, `cleanroom.py` in their scratch directory) target draft-1 formats and cannot run against draft-2. The 13 variants above are re-implemented inside the checker.

**Other verification run on 2026-11-22.**
- `extraction-vectors/check_vectors.py` accepts both new extraction files, and the default run on the shipped extraction vectors still passes; those files were not modified.
- A scratch script reused `harness/crosscheck.py` functions:
  - go/scanner agrees token for token on all 15 Go inputs, including the non-ASCII ones (run before the confirmation-pass additions, which added no new inputs);
  - proc-macro2 agrees on both Rust inputs, and rustc 1.97.1 accepts them;
  - toolchains: go1.27.3 and rustc 1.97.1.
- The `jsonschema` library in `.venv` validated all 259 valid instances: 153 catalogues, 76 bodies, 29 records and the report document. It rejected 4 record corruptions (`inputBytes`, `contract` key, `inserted:false`, missing `kgrams`) in addition to the earlier body corruptions below. It rejected 8 structural corruptions: extra field, rank, origin, float, class/code mismatch, draft-1 region field, provenance note, and source text in the implementation name.

**What the checker cannot do.**
- It does not lex. Token streams rest on `check_vectors.py` and the toolchain comparison above.
- It shares an author with `build_vectors.py`.
- Synthetic and fabricated catalogues are checked for shape, digest and expected outcome, not rebuilt.
- No independent draft-2 implementation exists.
