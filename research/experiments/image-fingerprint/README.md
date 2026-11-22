# Image fingerprint experiment (E-IMG-F): harness, generator and dry tests

Research only. This directory holds the code for the frozen protocol [`e-img-f-1`](../../drafts/image-experiment-protocol.md), which tests the draft [still-image fingerprint profile](../../drafts/extraction-profile-image.md) (roadmap IMGF.1–IMGF.5). **The measured experiment has not been run.** Nothing in this directory is a result. Smoke runs use a seed range disjoint from the experiment and are labelled `SMOKE RUN - NOT A RESULT`.

Protocol digest (`e-img-f-1`, SHA-256 of [image-experiment-protocol.md](../../drafts/image-experiment-protocol.md) with its digest field set to 64 zeros): `b7e4856bdd1a2d4eaaea478f18bd0f8d197fd2349733e5f14a65e31130da9d07`

## Layout

| Path | What it is |
| --- | --- |
| `twimg/decode.py` | Shared decode stage (profile §3): Pillow, EXIF orientation, white alpha flattening, closed abstention codes |
| `twimg/pdq_np.py` | NumPy port of the vendored PDQ, bit-identical by construction and by test |
| `twimg/iscc_img.py` | iscc-sdk 0.9.7 normalization (tolerant trim, `L`, 32×32 BICUBIC) and the iscc-core 1.5.0 Image-Code v0 hash, with 8 dihedral variants |
| `twimg/generator.py` | Seeded synthetic image generator `traceweave-synth-draft-1` |
| `twimg/transforms.py` | The 12 frozen edits |
| `twimg/profile.py` | Extraction and matching configuration bytes, digests, environment pin check |
| `run_experiment.py` | Harness: `smoke`, `full` and `compare` modes; metrics, criteria and validity checks |
| `check_vectors.py` | IMGF.2 evidence: PDQ and ISCC against published reference outputs; writes `vectors/check-results.json` |
| `fetch_wheels.py`, `fetch_pdq_vectors.py` | The only online steps: pinned wheels, and the 30 ThreatExchange vector images |
| `vectors/pdq-reference.json` | The 30 vector files (git blob id and SHA-256) and the three vendor reference-output sets, transcribed by script with source line numbers |
| `vectors/check-results.json` | The committed output of `check_vectors.py` (IMGF.2 evidence; not an experiment result) |
| `vendor/threatexchange_pdq/` | ThreatExchange pure-Python PDQ, unmodified, BSD; see its [PROVENANCE.md](vendor/threatexchange_pdq/PROVENANCE.md) |
| `vendor/iscc-sdk-LICENSE.txt` | Apache-2.0 licence of iscc-sdk. `fill_transparency` (in `decode.py`) and `trim_tolerant` (in `iscc_img.py`) re-implement iscc-sdk 0.9.7 functions at commit `cc11f771e4efbf0a600f196c7e9155b529ad7598` with the same Pillow calls |
| `tests/test_harness.py` | 24 unit tests |
| `requirements-build.txt`, `requirements.txt` | Hash-locked pins |

Git-ignored: `.venv/`, `wheelhouse/`, `vectors/pdq-data/`, `out/`.

## Environment

The environment is CPython 3.14.6 (Homebrew) on macOS 26.4, Apple Silicon. Every file is pinned by SHA-256; see [requirements.txt](requirements.txt) and [requirements-build.txt](requirements-build.txt). The hashes are for macOS arm64 CPython 3.14 wheels, so the pins are platform-locked.

Licences were read from each file's metadata (`License-Expression`, `License` or classifiers) and, for data-url, from its `LICENSE` file:

| Package | Version | Licence | File |
| --- | --- | --- | --- |
| pillow | 13.0.0 | MIT-CMU (bundles libjpeg-turbo 3.2.0, zlib-ng 1.3.1 and others, each under its own licence in the wheel) | `pillow-13.0.0-cp314-cp314-macosx_11_0_arm64.whl` |
| numpy | 2.5.5 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | `numpy-2.5.5-cp314-cp314-macosx_14_0_arm64.whl` |
| iscc-core | 1.5.0 | Apache-2.0 | `iscc_core-1.5.0-cp314-cp314-macosx_11_0_arm64.whl` |
| annotated-types | 0.8.0 | MIT | py3 wheel |
| base58 | 2.1.1 | MIT | py3 wheel |
| bitarray | 3.12.4 | PSF-2.0 | cp314 arm64 wheel |
| blake3 | 1.0.11 | CC0-1.0 OR Apache-2.0 | cp314 arm64 wheel |
| data-url | 1.4.0 | MIT (licence file; no wheel exists, built locally from the pinned sdist) | `data_url-1.4.0.tar.gz` |
| jcs | 0.3.0 | Apache-2.0 | py3 wheel |
| loguru | 0.8.0 | MIT | py3 wheel |
| more-itertools | 11.2.1 | MIT | py3 wheel |
| pybase64 | 1.5.2 | BSD-2-Clause | cp314 arm64 wheel |
| pydantic | 2.14.4 | MIT | py3 wheel |
| pydantic-core | 2.50.5 | MIT | cp314 arm64 wheel |
| python-dotenv | 1.2.4 | BSD-3-Clause | py3 wheel |
| typing-extensions | 4.16.0 | PSF-2.0 | py3 wheel |
| typing-inspection | 0.4.5 | MIT | py3 wheel |
| uvarint | 1.2.0 | MIT (classifier; metadata licence field "UNKNOWN") | py3 wheel |
| xxhash | 4.1.0 | BSD-2-Clause | cp314 arm64 wheel |
| setuptools (build only) | 84.2.1 | MIT | py3 wheel |

Vendored code is not installed from PyPI:
- ThreatExchange PDQ at `9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2`, BSD;
- re-implemented iscc-sdk functions, Apache-2.0.

The vector images are ThreatExchange `pdq/data` files at the same commit, BSD. They are fetched, not committed.

Only Pillow, NumPy and iscc-core are used directly. The other 16 packages are iscc-core's declared dependencies, imported when `iscc_core` loads. No model weights, datasets or real image sets are involved.

### Install (online once, then offline)

From this directory:

```sh
python3 fetch_wheels.py            # 20/20 pinned files into wheelhouse/ (curl, system TLS)
python3 fetch_pdq_vectors.py       # 30/30 vector images into vectors/pdq-data/
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/python -m pip install --no-index --find-links wheelhouse --require-hashes -r requirements-build.txt
.venv/bin/python -m pip install --no-index --find-links wheelhouse --require-hashes --no-build-isolation -r requirements.txt
```

`fetch_wheels.py` uses curl because, inside the agent sandbox used for this lane, pip's own TLS verification against the macOS trust store failed. Each file is matched to PyPI's published SHA-256 and checked again after download. pip then installs with `--require-hashes`.

## Dry tests (run 2026-11-22; not results)

```sh
.venv/bin/python check_vectors.py
.venv/bin/python -m unittest discover -s tests
.venv/bin/python run_experiment.py smoke --out out/smoke-a
.venv/bin/python run_experiment.py smoke --out out/smoke-b
.venv/bin/python run_experiment.py compare out/smoke-a out/smoke-b
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .venv/bin/python run_experiment.py smoke --out out/smoke-c --require-network-denied
.venv/bin/python run_experiment.py compare out/smoke-a out/smoke-c
```

Record of the last dry-test pass on the committed code is in the [dry-test record](#dry-test-record) below.

## Running the measured experiment

Do not run this until the protocol has been reviewed (protocol §13). From this directory, after the install:

```sh
SB='(version 1)(allow default)(deny network*)'
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python check_vectors.py
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python -m unittest discover -s tests
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python run_experiment.py full --require-network-denied --out out/full-1
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python run_experiment.py full --require-network-denied --out out/full-2
.venv/bin/python run_experiment.py compare out/full-1 out/full-2
```

`full` refuses to start unless the protocol digest, the environment pin, `vectors/check-results.json` and the network probe all hold. The roadmap's `scripts/offline` does not exist in this repository; `sandbox-exec` with `deny network*` stands in for it (protocol §8).

## Dry-test record

Run on 2026-11-22 on the committed code, before the protocol digest was recorded. Not a result.

| Check | Outcome |
| --- | --- |
| `fetch_wheels.py` in a fresh directory | 20/20 pinned files verified; byte-identical to the wheelhouse used for the install |
| `fetch_pdq_vectors.py` | 30/30 vector files verified (git blob id and SHA-256) |
| `pip install --no-index --require-hashes` | completed; `pip freeze` lists exactly the pinned versions (plus pip 26.1.2) |
| `check_vectors.py` | PDQ core port vs vendored 30/30. ISCC `data.json` 3/3, compiled and pure DCT. Published PDQ outputs: C++ 0/8 exact (max distance 8), Python README 4/12 (profile path) and 9/12 (thumbnail path), Python unit test 8/18 and 17/18; see profile §7 |
| Unit tests | 24/24 pass |
| Smoke runs a and b | each 108 queries, about 25 s, peak RSS about 0.67 GB; vendor cross-check 44/44; byte-identical; `resultsSha256` `57cb67b36fc6fe599539a3cd51bafaed5993ac5516ee35a9317fe5fba8b3e468` |
| Smoke run c under `sandbox-exec` deny-network | probe: bind and connect refused (errno 1); byte-identical to a; 23.3 s |
| Catalogue validation (C6) on smoke catalogues | no errors |

Running `sandbox-exec` needed the command to run outside the agent's own sandbox, which does not allow a nested sandbox profile.
