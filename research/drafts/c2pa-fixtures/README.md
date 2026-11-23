# Traceweave ↔ C2PA mapping fixtures (illustrative)

These fixtures belong to the [C2PA mapping draft](../c2pa-mapping.md) (roadmap gates C2PA.1–C2PA.3). They are research material, not test vectors, and they make **no compatibility claim**.

**What these are not.** The C2PA side of each fixture is CBOR/JUMBF written by hand in JSON diagnostic form. Nothing was serialized to CBOR or JUMBF, nothing was signed, and **no C2PA implementation produced or validated any fixture**. Each fixture carries the same notice, and the checker rejects a fixture that drops or changes it. C2PA.2 needs fixtures from a pinned open-source C2PA tool, so it stays open.

## Files

| Path | Content |
| --- | --- |
| `mapping-rules.json` | The mapping table of the draft in machine-readable form: for each fixture kind, the mapped fields (source pointer, target pointer, type, conversion) and the lossy, unmapped, opaque, conflicting and forbidden fields. It also holds the pinned soft-binding algorithm ids (79, from the list at `b445c12f`), the standard labels, the hash algorithms and the deprecated constructs of C2PA 2.5 |
| `fixtures/` | Six positive fixtures, f1–f6 (table in the draft, §8) |
| `negative/` | 18 broken fixtures. Each changes one thing in a positive fixture, and `expect.code` names the one failure it must produce |
| `build_fixtures.py` | Rebuilds both directories from committed Traceweave sources: entry `s0000000` of the `e-img-f-2` image catalogue, the `sum.go` reference catalogue of `go-function-in-host`, and `example-report.json`. It records each source file's SHA-256 |
| `check_fixtures.py` | The checker. Standard library only, Python 3.11 or later |

## Notation on the C2PA side

| CBOR | Written as |
| --- | --- |
| byte string | `"h'<lowercase hex>'"`, or `"'<text>'"` for bytes that are UTF-8 text (the report body) |
| text string | a JSON string |
| tag 0 date (`tdate`) | `"0(\"<RFC 3339 time>\")"` |
| float | a JSON number with a fraction (`512.0`); an integer there is a type error |
| hashed URI hash | the text `not computed: no JUMBF box was serialized` |
| claim signature | the text `absent: nothing was signed` |

Custom labels, `alg` ids and the report predicate type use the namespace `org.traceweave`, the reverse-domain form of the project domain `traceweave.org`. They are **proposed identifiers, not registered anywhere**: no algorithm-list entry exists for any of them, and nothing is published at the predicate URL. Fixtures declare such `alg` ids with `mapping.unregisteredAlg: true`.

## What the checker enforces

For every fixture:
- **Notice and wording:** the exact notice is present. No text outside the notice and `expect` matches the claim-word pattern (compatible, interoperable, compliant, conformant, certified, C2PA-ready). The C2PA version is the rules' version.
- **Mapped fields:** every mapped source field present in the fixture appears at its target pointer, with the right type and value under its conversion (`hex-to-bstr`, `jcs-bytes`, `text`, `tdate`, `same`, `prefix:…`, `pixel-rect`). `hex-to-bstr-whole-file` also refuses a hard binding with exclusions.
- **Declared losses:** every lossy, unmapped, opaque and conflicting rule that matches a source field is declared in `mapping`. A declared `carriedAt` must hold the source value. A declaration that is not a rule of its category is rejected, and every source leaf must be covered by some rule.
- **Forbidden content:** forbidden keys anywhere (`similarityScore`, `score`, `confidence` and others) and forbidden pointers.
- **C2PA side:** labels are standard or under the proposed `org.traceweave` namespace. Every assertion is referenced by the claim, and every reference resolves. There is exactly one hard binding, and its algorithm is a 12.1 hash. Deprecated constructs are refused (`url`, `scope.extent`, `c2pa.watermarked`). `c2pa.watermarked.bound` needs a soft binding. The report assertion goes in `gathered_assertions` unless the signer ran the comparison, and its body bytes hash to its `bodySha256`. Soft-binding `alg` values are registered or declared unregistered. The signature is absent.
- **in-toto side:** Statement v1 with one sha256 subject and the proposed predicate type; the body hashes to `bodySha256`; the manifest reference is well formed; and its `relation` is consistent with the hard binding.
- **Round trip:** the declared survivors and losses equal what the imported record actually contains. Nothing is invented, and every survivor comes from a mapped rule.
- **Drift:** every rule pointer appears in backticks in the mapping document, and each source file still has the SHA-256 recorded at build time.

Failure codes: `alg-unregistered-undeclared`, `assertion-missing`, `assertion-undeclared`, `attribution`, `body-digest-mismatch`, `claim-wording`, `conflict-undeclared`, `declaration-unknown`, `deprecated-construct`, `field-unruled`, `fixture-shape`, `forbidden-field`, `hard-binding-count`, `identity-conflation`, `intoto-shape`, `kind-unknown`, `label-namespace`, `lossy-undeclared`, `mapped-missing`, `notice-missing`, `opaque-undeclared`, `round-trip-invented`, `round-trip-misdeclared`, `round-trip-unsupported`, `signature-claimed`, `soft-as-hard`, `soft-binding-missing`, `source-drift`, `type-mismatch`, `unmapped-undeclared`, `value-mismatch`, `version-pin`, plus `doc-drift` for the whole run.

## Negative fixtures

| File | Must produce |
| --- | --- |
| `neg-lossy-dropped` | `lossy-undeclared`: PDQ quality silently dropped |
| `neg-compatibility-claim` | `claim-wording`: "C2PA-compatible" in the description |
| `neg-mapped-missing` | `mapped-missing` |
| `neg-type-text-not-bstr` | `type-mismatch`: hash written as text |
| `neg-value-changed` | `value-mismatch`: one hex digit differs |
| `neg-similarity-score` | `forbidden-field` |
| `neg-soft-as-hard` | `soft-as-hard`: the hard binding names a soft-binding algorithm |
| `neg-c2pa-namespace` | `label-namespace`, and `mapped-missing` as a consequence |
| `neg-deprecated-extent` | `deprecated-construct` |
| `neg-identity-same-bytes` | `identity-conflation` |
| `neg-body-digest` | `body-digest-mismatch` |
| `neg-watermark-no-binding` | `soft-binding-missing` |
| `neg-round-trip-misdeclared` | `round-trip-misdeclared` |
| `neg-conflict-undeclared` | `conflict-undeclared`: orientation basis |
| `neg-report-attributed` | `attribution` |
| `neg-alg-unregistered` | `alg-unregistered-undeclared` |
| `neg-signature-claimed` | `signature-claimed` |
| `neg-region-integer` | `type-mismatch`: integer region coordinate |

## Commands

From the repository root:

```sh
python3 -I research/drafts/c2pa-fixtures/build_fixtures.py   # rewrites fixtures/ and negative/
python3 -I research/drafts/c2pa-fixtures/check_fixtures.py   # exit 0 when every fixture behaves as expected
```

The checker exits 1 if any positive fixture fails, if any negative fixture is not rejected with exactly its expected codes, if a rule pointer is missing from the mapping document, or if fewer than 6 fixtures or 8 negatives are present. These scripts are not wired into `tools/validate.py` or CI.

## Limits

- The checker tests this draft's own rules. It does not test C2PA conformance, CBOR well-formedness, JUMBF layout or any signature.
- The JCS step covers the sources here only (ASCII strings, non-negative integers).
- The mark-detection record (f4) is invented; no Traceweave schema for it exists.
- The token-catalogue export (f6) shows a mapping that the draft recommends **against** (private catalogues, D6).
