# Historical reproduction commands and omitted prerequisites

This page is a labelled command summary from the accepted original `reproduce.sh`, not a new executed runner. Its original SHA-256 and size are in the [retention manifest](retention-manifest.json). The source records beside this page are exact original scripts in a different public layout; do not run them here or point them at retained evidence in place.

Portable static accounting is reproducible with:

```sh
python3 -B research/reviews/pdq-six-input-diagnosis/inspect_retention.py
```

Full numerical reproduction additionally needs a **fresh scratch copy of the complete accepted original package**, its omitted six input payloads/source subset/frozen Python export/trace dependencies, a matching provisioned CPython3.14.6 +NumPy2.5.5 +Pillow13.0.0 environment and existing Apple clang21.0.0. Verify the original report/manifest identities before use, including all412 original manifest entries. No acquisition/install is part of these commands. This public subset cannot reconstruct missing bytes from hashes or authenticate the upstream commit binding. The original compiler/host record and uncalibrated chronology are historical evidence, not guaranteed portable behavior.

In that fresh complete scratch copy, update only its copied workspace-path locator and existing interpreter selection for the scratch root. Never alter originals. `prepare.py` is a one-time constructor requiring its destination not already exist; the independent review regenerated instrumentation only after removing the copied destination in its own scratch. The observed instrumentation patch identity is a3569a2fd63fe3ee7c32351645a8ad0646c0b514b5cf05df72d57397db20c4fe. The following is the original command sequence with the private interpreter locator replaced by an explicit caller-supplied variable; all other command dimensions are retained:

```sh
# PWD must be the fresh complete original scratch package, not this public subset.
r="$PWD"
py="${PDQ_PYTHON:?select the existing pinned environment}"
deny() { /usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' "$@"; }
deny "$py" -B "$r/baseline-artifact/compare.py"
deny /usr/bin/clang++ --version
deny /usr/bin/clang++ -std=c++11 -O2 -fno-fast-math -ffp-contract=off -I "$r/instrumented-source" "$r/baseline-artifact/bridge.cpp" "$r/instrumented-source/pdq/cpp/hashing/pdqhashing.cpp" "$r/instrumented-source/pdq/cpp/hashing/torben.cpp" "$r/instrumented-source/pdq/cpp/downscaling/downscaling.cpp" -o "$r/pdq-instrumented"
deny "$py" -B "$r/diagnose.py"
deny "$py" -B "$r/mixed-probes.py"
deny "$py" -B "$r/check-diagnosis.py"
```

The historical launchers require bind EPERM before core execution. This is OS confinement evidence, not browser privacy or zero-request-attempt proof. Baseline32/48hash6/6quality, all48 diagnostic reconstructions and1606 decisions must keep separate meanings. Expected baseline binary ba757a0791cb4a6b5ab1d2493daddb325d04ba02bb52fb9b0a098441b42bcfeb and instrumented binary bcd50af99b5d6db87ae729988a9aaf2dad6cf51c38ec256c7606cec17572c262 are identity-only artifacts here; no execution or new compiler result is claimed.

The independent review’s separate scalar source-derived coefficient reconstruction is retained as [reported results](results/independent-results.json) and [labelled review](reports/independent-review.md). Its original checker identity is recorded but checker/source/array execution dependencies are omitted; the public static inspector does not substitute for it. Numerical reproduction remains subject to separate authorization and an adequate retained environment. No such run is authorized by this command summary, and none was performed during retention.
