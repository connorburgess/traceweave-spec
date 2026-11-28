# Retained six-input PDQ mismatch diagnosis

This is portable **evidence retention**, not a new study or replacement implementation. The previously accepted diagnosis localizes the retained six-input/one-host mismatches to DCT coefficient construction and binary32 product/accumulation rounding. Its specified binary32 path reconstructed all48 C++ hashes and12 T/B stage-byte comparisons; the independent reconstruction derived coefficients from the source formula rather than treating observed coefficients as an oracle. All1606 differing bit decisions are retained:1118 constant127,488 low-contrast. There is no tolerance or quality waiver.

The original baseline remains **32/48 exact hashes and6/6 exact qualities**, including all eight mismatching variants of each low-quality input. “48 reconstructed” is diagnostic recovery of recorded C++ results, not48/48 Python/C++ agreement. IMGF.5 stays **OPEN**, without negative-result status, criterion/count change or general parity. M3 HOLD and all WEB.6/runtime/other holds remain.

## Retained evidence and exact scope

| Artifact | Retention |
|---|---|
| [Revised author report](reports/author-report.md) | Labelled adaptation; original SHA-2562816c35b4ce7ace508170bb6f55a515fe4df60cec7a20d0d3603f66e30ebac95 |
| [Original independent review](reports/independent-review.md) | Labelled adaptation preserving adverse PDQ-D1 disposition and independent numeric finding |
| [Focused PDQ-D1 acceptance](reports/pdq-d1-addendum.md) | Labelled adaptation; supersedes only the report/generator correction condition |
| [Diagnosis](results/diagnosis.json), [mixed probes](results/mixed-probes.json), [stage-byte checks](results/bitwise-checks.json) | Exact original JSON bytes |
| [Independent results](results/independent-results.json), [D1 focused evidence](results/pdq-d1-addendum-evidence.json) | Exact original JSON bytes; earlier execution records, not measurements by this packaging task |
| [Selected-fields ledger](summary-ledger.json) | Labelled reduced projection with original source hashes; six input identities/dimensions and distinct denominators |
| [black](decisions/black.csv), [constant127](decisions/constant127.csv), [low-contrast](decisions/low-contrast.csv), [asymmetric](decisions/asymmetric.csv), [wide](decisions/wide.csv), [tall](decisions/tall.csv) | Six labelled CRLF-to-LF adaptations, including four header-only zero-decision files; fields/order/numeric text unchanged,1606 records total |
| [Prior comparison](../../experiments/pdq-cpp-feasibility/comparison.json), [source identities](../../experiments/pdq-cpp-feasibility/acquisition.json), [Python identities](../../experiments/pdq-cpp-feasibility/python-source.json) | Reused existing curated files, not duplicated |
| [Questions](source-records/questions.md), [D1 resolution](source-records/pdq-d1-resolution.md) | Exact historical declaration/correction records; original instrumentation patch is identity-only in the manifest, not a copied/altered patch |
| [prepare.py](source-records/prepare.py), [diagnose.py](source-records/diagnose.py), [mixed-probes.py](source-records/mixed-probes.py), [check-diagnosis.py](source-records/check-diagnosis.py) | Exact source records, retained for inspection only; original layout/dependencies absent here, unexecuted in retention |

[Retention manifest](retention-manifest.json) records every selected original/retained identity, adaptation and identity-only omission. Its packageFiles inventory covers actual package files except the manifest itself; this provides consistency, not a signature/authenticated execution proof. The revised original manifest SHA-256 is5b2db7762a4e7949b9ebb70fb1d40397bfff25a85a8af968ba7ea31541976b8e (413 original files/412 manifest entries); it is identified, not copied as a misleading public-package inventory. Hundreds of source/input/binary/array/log artifacts are omitted. Original artifact names inside adapted historical reports refer to that original package unless linked above; their mention does not assert public retention. No private attachment is needed to inspect retained result accounting, but the full numerical experiment is not self-contained here.

## PDQ-D1 and causal limits

Original report/generator flip masks were wrong: the retained adverse review remains visible. Revised flipx is **+B on odd row i, −B on even row i**; flipy is **+B on odd column j, −B on even column j**, neither transposes. Only those two literal rows changed in report/generator;409 other existing files were unchanged, one resolution note was added, and the manifest refreshed. No arithmetic output or implementation mask changed to fit the report. The addendum accepts exact revised report/package identities after the correction; it does not independently review this new portable retention package.

The observation is limited to black, constant127, low-contrast, asymmetric, wide and tall integer common-luma arrays, one retained arm64 host/compiler, unit blur windows, Apple clang21.0.0 and flags `-std=c++11 -O2 -fno-fast-math -ffp-contract=off`. Frozen export6f39e50f33026c9f1d9526c2a566d6a447219667 is one Python arithmetic reference; vendor/NumPy agreement is not two independent implementations. C++ subset label9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2 remains qualified by the [existing provenance boundary](../../experiments/pdq-cpp-feasibility/provenance.md): published internal tree/subset consistency does not reproduce commit-to-root binding. No raw upstream commit, signature/email metadata or alternate encoding is included.

No RGB/decoder/pre-resize, larger blur window/dimension, other host/flag, noninteger/full-frozen-set or30/1400 evidence is supplied. No threshold calibration, natural-image rate or universal exclusive cause follows. The previous curated package’s “unlocalized” wording is preserved as a historical snapshot; this accepted bounded successor supports only the current queue clarification.

## Static inspection and reproduction limits

```sh
python3 -B research/reviews/pdq-six-input-diagnosis/inspect_retention.py
```

This stdlib inspector reads files/JSON/CSV and checks identities/projections/counts. It never imports the numerical source records, compiles, fetches or runs PDQ. It checks retained accounting, not causal truth by re-executing DCT. [Reproduction commands and omissions](reproduction.md) distinguish original numerical reproduction prerequisites from portable static inspection. Retention involved no numerical rerun/build/native/browser/acquisition, no new dependencies and no rewrite/push. Original reports/review records remain unchanged privately. This package requires independent retention review before shared integration.
