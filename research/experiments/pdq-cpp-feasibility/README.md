# Curated PDQ common-luma evidence

This package preserves a bounded historical comparison, not an IMGF.5 closure. Six declared integer-luminance arrays produced **32/48 exact C++ hashes and 6/6 exact quality values**; four inputs agreed across all eight variants. The constant-127 (quality 0) and low-contrast (quality 11) inputs each retain eight hash mismatches. Black (quality 0) agrees. Python port/vendor results agree for all six inputs, using shared arithmetic rather than an independent implementation.

The arrays bypass image decoding, luminance conversion, trimming and ISCC encoding. They do not cover the 30 vendor vectors or the full frozen synthetic study. The numeric cause remains unlocalized; differing floating-point precision is a hypothesis. IMGF.5 remains **OPEN**, with no negative-result designation or criterion change.

## What is published

The seven JSON reports, bridge, adapted runner and upstream licence are unchanged copies from the historical evidence package. The [provenance summary](provenance.md) distinguishes internal tree/subset proof from the privately retained commit-to-root proof. The raw upstream commit object is entirely omitted. The original package manifest is omitted because it describes a different package. [public-package-sha256.json](public-package-sha256.json) describes these actual public files; it provides consistency, not an authenticated signature.

Run the stdlib-only inspection without fetching, compiling or executing PDQ:

```sh
python -B research/experiments/pdq-cpp-feasibility/inspect_evidence.py
python -B -m unittest discover -s research/experiments/pdq-cpp-feasibility -p 'test_*.py' -v
```

Optional `--source PATH` and `--reference PATH` inspect already provisioned upstream and frozen Python export bytes against their reports; they neither fetch nor import them. No upstream source subset, compiled binary or original input files are bundled. `reproduce.py` is the unchanged adapted runner, statically checked and **unexecuted** in this packaging task; its presence is not proof of portable execution. See [validation scope](validation.md) and the [historical review summary](../../reviews/pdq-cpp-curated-public-summary.md). Independent review of this new curated package is pending.
