# Draft-3 synthetic normalization conformance

Research-only companion to the [proposed draft-3 profile](../../drafts/extraction-profile-image-draft3.md). This directory is separate from the frozen `image-fingerprint/` experiment. It performs no downloads, image decoding, trim, DCT/hash generation, matching or full study. No natural images or corpora are used.

`arithmetic.py` implements the proposed equations using ordinary binary64 and exact integer sample accumulation. `oracle.py` separately implements elementary binary64 rounding with exact `Fraction` arithmetic and ties-to-even significand rounding; it never imports the implementation or Pillow and performs no native float arithmetic. It uses explicit coordinate passes rather than the implementation's transpose helper. These are two arithmetic approaches authored in one change, not two independent implementers. Review of both remains necessary.

`build_fixtures.py` records RGB bytes and oracle-computed grey, first-pass and final bytes in `fixtures.json`. Expected bytes are labelled computed, not hand-derived. Fifteen deliberately specified cases cover black/white/colour swatches, identity, width/height-only, noninteger downscale, pass-order inequality equality and vertical-first branch, wide aspect, edge overshoot, one-pixel sides and upscaling. Most RGB samples use the stated seedless modular polynomials in the builder; inputs are committed verbatim. Small arrays are post-trim stage inputs, not new accepted decoded-image classes. An aggregate coefficient-table digest checks bounds/weights too.

`check.py` recomputes every expected output through both approaches. It checks exact tie/primary-colour anchors and applies two deliberate incorrect resize implementations: reversed pass order and retaining unquantized intermediates until final-only rounding. Each mutation must differ on at least one fixture. `test_checker.py` injects each wrong implementation and requires the checker itself to fail; it also verifies byte-identical oracle regeneration. The checker also guards inherited frozen file digests and permits only the two documented extraction-config field changes. The reported 15 cases are not 15 independent population samples.

## Offline commands

With any existing Python 3.11+ (standard library only), from repository root:

```sh
python3 -B research/experiments/image-normalization-draft3/check.py
python3 -B -m unittest discover -s research/experiments/image-normalization-draft3 -p test_checker.py
```

To compare the **already installed** pinned Pillow target, set `PINNED_PYTHON` to the existing CPython 3.14 experiment virtualenv interpreter and `PILLOW_WHEEL` to its already provisioned `pillow-13.0.0-cp314-cp314-macosx_11_0_arm64.whl`. No install or fetch command is included. Both environment variables are caller-supplied paths; portable records contain neither path.

```sh
: "${PINNED_PYTHON:?Existing pinned experiment interpreter}"
: "${PILLOW_WHEEL:?Existing pinned Pillow wheel}"
"$PINNED_PYTHON" -B research/experiments/image-normalization-draft3/check.py \
  --pillow-wheel "$PILLOW_WHEEL" --report "$TMPDIR/image-normalization-comparison.json"
```

The wheel SHA-256 must be `d9b0a2bee3f3e03e9f29057aedb807dbf1e1d96ee1b9d0f422d9db6c8583271d`; the loaded `PIL/Image.py` and compiled `PIL/_imaging` bytes are checked against that wheel, not just its version string. Only its RGB-to-L and mode-L BICUBIC resize operations are called. It is a separate comparison target, never the expected-output oracle. Exit 1 means an observed mismatch or undetected mutation; the JSON report preserves differing-byte counts and the full Pillow final output, including mismatches. Missing/unpinned prerequisites fail setup rather than silently skipping a requested target comparison.

On macOS the recorded target run was additionally wrapped by `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'`. This bounded checker has no network code. No new network-denial claim about the frozen study is made.

Explicit regeneration (review changes; never regenerate from Pillow to hide a mismatch):

```sh
python3 -B research/experiments/image-normalization-draft3/build_fixtures.py
```

`primary-source-pins.json` records upstream source identities established by the preceding read-only investigation; runtime never fetches these URLs. `frozen-pins.json` records the base commit, inherited draft/protocol/config file hashes, and frozen experiment Git tree id. Verify preservation from Git as well:

```sh
git diff --exit-code 24bb4b8483dc86966cb7c8277130bb816b0c6b3f -- \
  research/drafts/extraction-profile-image.md research/drafts/image-experiment-protocol.md \
  research/experiments/image-fingerprint
```

## Recorded result

[comparison-results.json](comparison-results.json) records CPython 3.14.6, Darwin arm64, pinned Pillow wheel/loaded target identity and source/config/fixture hashes. All 15 cases agreed on grey, first-pass and final bytes. Coefficient tables agreed between arithmetic implementations. Both resize mutations were detected on `noninteger`, `order-equality`, `vertical-first`, `wide` and `edge` (5 witnesses each). No target mismatch was observed in this finite suite; no universal, cross-host, compiler, SDK or end-to-end normalization equivalence follows. Future mismatches must remain visible.

The frozen draft-2 configuration and `e-img-f-2` inputs/results are unchanged. Draft-3 has a new extraction identity; matching/core rules are inherited. This directory does not promote a normative profile, close IMGF.1/IMGF.5, or authorize broader experiment/evaluation work.

Validation on this change: ordinary and sandboxed pinned-target checks exited 0; the four checker self-tests passed; oracle fixture regeneration was byte-identical; repository `tools/validate.py`, `--links-all`, all 28 repository unit tests, hygiene and `git diff --check` passed. The frozen-path diff against the base was empty. These checks do not rerun the frozen image experiment.

## Exact grey half-tie follow-up

The `grey-half-tie` fixture is a constant 32×32 RGB array with pixel `(1,53,185)`. Independent integer arithmetic gives `19595*1 + 38470*53 + 7471*185 = 3440640 = 52*65536 + 32768`, exactly `52.5` before rounding. The specified half-up result is **53** (`0x35`); no resize pass changes that byte. The oracle, ordinary implementation and pinned Pillow all produce 1,024 copies of 53. A ties-to-even mutation produces **52** (`0x34`) and is detected at all 1,024 grey bytes; injecting that mutation also makes the checker fail with 1,024 final-byte differences. This explicit anchor does not rely on expected bytes copied from Pillow.

This addresses the missing exact-half-tie fixture identified by independent review `b3a3a2c99b52f7313a3e6b6a4ae10e5e96846755` of `fce78938e9fd7d80a7ddd2d06686a857bfc458d5`. That reviewer lacked upstream C source bytes for a fresh source-hash verification. The limitation remains: this follow-up acquires no upstream sources and makes no new source-verification claim. Frozen draft-2, the draft-3 extraction config and both arithmetic implementations are unchanged; only draft-3 fixtures/checker/evidence are extended.
